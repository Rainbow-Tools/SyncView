"""Shared, bounded decoration cache for preview and export."""

from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QImage, QPainter, QPainterPath, QPen

from videos_multi_view.core.layout import Cell
from videos_multi_view.core.models import Project, Video
from videos_multi_view.core.timeline import format_time, source_time_ms
from videos_multi_view.i18n import tr


def resolve_label_text(text: str, video: Video, current_time_ms: int = 0) -> str:
    replacements = {
        "{filename}": Path(video.path).stem,
        "{timecode}": format_time(source_time_ms(video, current_time_ms) or 0),
        "{fps}": f"{video.fps:g}fps",
        "{resolution}": f"{video.width}x{video.height}",
        "{offset}": f"{video.offset_ms}ms",
    }
    for macro, value in replacements.items():
        text = text.replace(macro, value)
    return text


class _LabelCache:
    def __init__(self, video: Video, cell: Cell) -> None:
        self.video, self.cell = video, cell
        self.font = QFont(video.label.font_family or "Malgun Gothic")
        self.font.setPixelSize(video.label.size)
        self.font.setWeight(QFont.Weight.Medium)
        self.metrics = QFontMetricsF(self.font)
        self.dynamic = "{timecode}" in video.label.text
        self.template = resolve_label_text(
            video.label.text.replace("{timecode}", "\0"), video
        ).replace("\0", "{timecode}")
        self.text: str | None = None
        self.image = QImage()
        self.position = QPointF()

    def draw(self, painter: QPainter, current_time_ms: int) -> None:
        text = self.template
        if self.dynamic:
            text = text.replace(
                "{timecode}", format_time(source_time_ms(self.video, current_time_ms) or 0)
            )
        if text != self.text:
            self.text = text
            self._render(text)
        if not self.image.isNull():
            painter.drawImage(self.position, self.image)

    def _render(self, text: str) -> None:
        label, bounds = self.video.label, self.cell.bounds
        margin = max(6, round(label.size * 0.3))
        px, py = max(6, round(label.size * 0.35)), max(4, round(label.size * 0.25))
        available = bounds.width - 2 * margin - 2 * px
        height = min(round(self.metrics.height()) + 2 * py, bounds.height - 2 * margin)
        if available < 4 or height < 4:
            self.image = QImage()
            return
        text = self.metrics.elidedText(
            text.replace("\n", " "), Qt.TextElideMode.ElideRight, available
        )
        width = min(
            bounds.width - 2 * margin, int(self.metrics.horizontalAdvance(text) + 1) + 2 * px
        )
        self.image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        self.image.fill(Qt.GlobalColor.transparent)
        p = QPainter(self.image)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(label.background))
        radius = max(3.0, label.size * 0.15)
        p.drawRoundedRect(QRectF(0, 0, width, height), radius, radius)
        p.setFont(self.font)
        p.setPen(QColor(label.color))
        p.drawText(QPointF(px, py + self.metrics.ascent()), text)
        p.end()
        x = bounds.x + margin
        y = bounds.y + margin
        if label.position.endswith("right"):
            x = bounds.x + bounds.width - width - margin
        if label.position.startswith("bottom"):
            y = bounds.y + bounds.height - height - margin
        self.position = QPointF(x, y)


class DecorationRenderer:
    """Create on settings changes; reuse each frame. Only current label images are retained."""

    def __init__(self, project: Project, cells: list[Cell]) -> None:
        self.project, self.cells = project, cells
        self._is_overlay = project.overlay.enabled and len(project.videos) >= 2
        if self._is_overlay:
            self.labels = []
            self.dynamic = False
            self._border_path = QPainterPath()
            self._border_pen = QPen()
            return

        videos = {v.id: v for v in project.videos}
        self.labels = [
            _LabelCache(videos[cell.video_id], cell)
            for cell in cells
            if videos[cell.video_id].label.visible and videos[cell.video_id].label.text
        ]
        self.dynamic = any(label.dynamic for label in self.labels)
        layout = project.layout
        self._border_path = QPainterPath()
        self._border_pen = QPen(QColor(layout.border_color), layout.border_width)
        self._border_pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        if layout.border_visible and layout.border_width:
            half = layout.border_width / 2
            for cell in cells:
                b = cell.bounds
                self._border_path.addRect(
                    QRectF(b.x + half, b.y + half, b.width - 2 * half, b.height - 2 * half)
                )

    def draw(self, painter: QPainter, current_time_ms: int = 0) -> None:
        painter.save()
        if self._is_overlay:
            self._draw_overlay_badge(painter)
            painter.restore()
            return
        if not self._border_path.isEmpty():
            painter.setPen(self._border_pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(self._border_path)
        for label in self.labels:
            label.draw(painter, current_time_ms)
        painter.restore()

    def _draw_overlay_badge(self, painter: QPainter) -> None:
        overlay = self.project.overlay
        video_map = {v.id: v for v in self.project.videos}
        vid_a = video_map.get(overlay.base_video_id) or self.project.videos[0]
        candidates = [v for v in self.project.videos if v.id != vid_a.id]
        vid_b = (
            video_map.get(overlay.overlay_video_id)
            if overlay.overlay_video_id and overlay.overlay_video_id in video_map
            else (candidates[0] if candidates else None)
        )
        if not vid_b:
            return
        badge_font = QFont("Pretendard Variable", 10)
        badge_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(badge_font)
        method = overlay.method
        method_names = {
            "blend": f"투명도 블렌드 ({int(overlay.opacity * 100)}%)",
            "tint": "색상 틴트 비교",
            "difference": f"잔차 오류 맵 ({overlay.gain:.1f}x)",
        }
        text = f"⧉ 오버레이 비교: {method_names.get(method, method)}"
        name_a = Path(vid_a.path).stem
        name_b = Path(vid_b.path).stem
        subtext = f"{name_a} vs {name_b}"
        badge_w = max(260.0, QFontMetricsF(badge_font).horizontalAdvance(text) + 24.0)
        badge_rect = QRectF(12, 12, badge_w, 42)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 190))
        painter.drawRoundedRect(badge_rect, 6, 6)
        painter.setPen(QColor("#60A5FA"))
        painter.drawText(
            QRectF(badge_rect.x() + 10, badge_rect.y() + 4, badge_rect.width() - 20, 18),
            Qt.AlignmentFlag.AlignLeft,
            text,
        )
        small_font = QFont("Pretendard Variable", 8)
        painter.setFont(small_font)
        painter.setPen(QColor("#94A3B8"))
        painter.drawText(
            QRectF(badge_rect.x() + 10, badge_rect.y() + 23, badge_rect.width() - 20, 16),
            Qt.AlignmentFlag.AlignLeft,
            subtext,
        )

    def image(self, current_time_ms: int = 0) -> QImage:
        image = QImage(
            self.project.output.width, self.project.output.height, QImage.Format.Format_RGBA8888
        )
        if image.isNull():
            raise ValueError(tr("출력 이미지를 만들 메모리가 부족합니다."))
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.draw(painter, current_time_ms)
        painter.end()
        return image


def render_decorations(
    painter: QPainter,
    project: Project,
    cells: list[Cell],
    selected_video_id: str | None = None,
    current_time_ms: int = 0,
) -> None:
    """Compatibility entry point; animation should reuse DecorationRenderer."""
    DecorationRenderer(project, cells).draw(painter, current_time_ms)


def render_selection_highlight(
    painter: QPainter,
    cell: Cell,
    color: str = "#0078d4",
    width: float = 3.0,
) -> None:
    pen = QPen(QColor(color))
    pen.setWidthF(width)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    half = width / 2
    b = cell.bounds
    painter.drawRect(QRectF(b.x + half, b.y + half, b.width - width, b.height - width))
