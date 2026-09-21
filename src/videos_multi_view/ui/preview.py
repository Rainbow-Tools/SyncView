"""Composite preview canvas maintaining aspect ratio with interactive selection."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import QWidget

from videos_multi_view.core.layout import Cell, Rect, calculate_layout, fit
from videos_multi_view.core.models import Project
from videos_multi_view.media.player import SyncPlayer
from videos_multi_view.ui.renderer import DecorationRenderer, render_selection_highlight


class PreviewCanvas(QWidget):
    """Widget displaying the composite multi-view video canvas."""

    video_selected = Signal(str)
    solo_changed = Signal(object)

    def __init__(self, player: SyncPlayer, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.player = player
        self.player.frame_updated.connect(self.update)

        self._project = Project()
        self._cells: list[Cell] = []
        self._selected_video_id: str | None = None
        self._solo_video_id: str | None = None
        self._video_map = {}
        self._draw_cells = []
        self._renderer = DecorationRenderer(self._project, [])

        self.setMinimumSize(320, 180)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    def set_project(self, project: Project, selected_video_id: str | None = None) -> None:
        self._project = project
        self._selected_video_id = selected_video_id
        if self._solo_video_id and not any(v.id == self._solo_video_id for v in project.videos):
            self._solo_video_id = None
            self.solo_changed.emit(None)
        try:
            self._cells = calculate_layout(project)
        except ValueError:
            self._cells = []
        self._video_map = {v.id: v for v in project.videos}
        self._rebuild_renderer()
        self.update()

    def _rebuild_renderer(self) -> None:
        self._draw_cells = self._cells
        if self._solo_video_id in self._video_map:
            video = self._video_map[self._solo_video_id]
            output = self._project.output
            bounds = Rect(0, 0, output.width, output.height)
            self._draw_cells = [Cell(video.id, bounds, fit(video.display_aspect, bounds))]
        self._renderer = DecorationRenderer(self._project, self._draw_cells)

    def set_selected_video(self, video_id: str | None) -> None:
        if self._selected_video_id != video_id:
            self._selected_video_id = video_id
            self.update()

    def _compute_canvas_rect(self) -> tuple[QRectF, float]:
        """Compute the letterboxed/pillarboxed canvas rectangle and scale factor."""
        w, h = self.width(), self.height()
        out_w, out_h = self._project.output.width, self._project.output.height
        if out_w <= 0 or out_h <= 0 or w <= 0 or h <= 0:
            return QRectF(0, 0, w, h), 1.0

        scale = min(w / out_w, h / out_h)
        target_w = out_w * scale
        target_h = out_h * scale
        x = (w - target_w) / 2.0
        y = (h - target_h) / 2.0
        return QRectF(x, y, target_w, target_h), scale

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        # 1. Fill widget workspace background
        painter.fillRect(self.rect(), QColor("#090D16"))

        canvas_rect, scale = self._compute_canvas_rect()
        if scale <= 0:
            return

        # 2. Fill canvas background
        bg_color = QColor(self._project.layout.background)
        bg_color.setAlpha(255)  # MP4 has an opaque canvas; only decorations use alpha.
        painter.fillRect(canvas_rect, bg_color)

        # 3. Draw video frames and decorations in canvas coordinates
        painter.save()
        painter.translate(canvas_rect.topLeft())
        painter.scale(scale, scale)

        common_t = self.player.common_time
        video_map = self._video_map
        cells_to_draw = self._draw_cells

        for cell in cells_to_draw:
            video = video_map.get(cell.video_id)
            if not video:
                continue
            frame = self.player.get_frame(video, common_t)
            if frame is not None and not frame.isNull():
                img_rect = QRectF(
                    cell.image.x,
                    cell.image.y,
                    cell.image.width,
                    cell.image.height,
                )
                painter.drawImage(img_rect, frame)

        # Draw borders and labels with dynamic macros
        self._renderer.draw(painter, common_t)

        # Draw selection highlight
        if self._selected_video_id and not self._solo_video_id:
            for cell in cells_to_draw:
                if cell.video_id == self._selected_video_id:
                    render_selection_highlight(painter, cell)
                    break

        if self._solo_video_id:
            badge_font = QFont("Pretendard", 10)
            badge_font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(badge_font)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(0, 0, 0, 180))
            painter.drawRoundedRect(QRectF(12, 12, 210, 28), 4, 4)
            painter.setPen(QColor("#60A5FA"))
            painter.drawText(
                QRectF(12, 12, 210, 28),
                Qt.AlignmentFlag.AlignCenter,
                "솔로 뷰 (더블클릭하여 복귀)",
            )

        painter.restore()

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        canvas_rect, scale = self._compute_canvas_rect()
        pos = event.position()
        if not canvas_rect.contains(pos) or scale <= 0:
            super().mousePressEvent(event)
            return

        cx = (pos.x() - canvas_rect.x()) / scale
        cy = (pos.y() - canvas_rect.y()) / scale

        for cell in self._cells:
            b = cell.bounds
            if b.x <= cx <= b.x + b.width and b.y <= cy <= b.y + b.height:
                self.video_selected.emit(cell.video_id)
                return

        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            super().mouseDoubleClickEvent(event)
            return

        if self._solo_video_id is not None:
            self._solo_video_id = None
            self._rebuild_renderer()
            self.solo_changed.emit(None)
            self.update()
            return

        canvas_rect, scale = self._compute_canvas_rect()
        pos = event.position()
        if not canvas_rect.contains(pos) or scale <= 0:
            super().mouseDoubleClickEvent(event)
            return

        cx = (pos.x() - canvas_rect.x()) / scale
        cy = (pos.y() - canvas_rect.y()) / scale

        for cell in self._cells:
            b = cell.bounds
            if b.x <= cx <= b.x + b.width and b.y <= cy <= b.y + b.height:
                self._solo_video_id = cell.video_id
                self._rebuild_renderer()
                self.solo_changed.emit(cell.video_id)
                self.video_selected.emit(cell.video_id)
                self.update()
                return

        super().mouseDoubleClickEvent(event)
