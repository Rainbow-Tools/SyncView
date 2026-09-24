"""Composite preview canvas maintaining aspect ratio with interactive selection."""

from PySide6.QtCore import QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QImage,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    qRgb,
)
from PySide6.QtWidgets import QWidget

from videos_multi_view.core.layout import Cell, Rect, calculate_layout, fit
from videos_multi_view.core.models import Project
from videos_multi_view.i18n import tr
from videos_multi_view.media.player import SyncPlayer
from videos_multi_view.ui.renderer import DecorationRenderer, render_selection_highlight


def _generate_diff_color_table(colormap: str, gain: float, custom_hex: str) -> list[int]:
    """Precompute a 256-entry QRgb color table for difference colormaps."""
    table: list[int] = [0] * 256
    custom_c = QColor(custom_hex)
    cr, cg, cb = custom_c.red(), custom_c.green(), custom_c.blue()

    for d in range(256):
        v = min(255, max(0, int(d * gain)))
        norm = v / 255.0

        if colormap == "heat":
            # Black -> Red -> Orange -> Yellow -> White
            r = int(min(1.0, max(0.0, 3.0 * norm)) * 255)
            g = int(min(1.0, max(0.0, 3.0 * norm - 1.0)) * 255)
            b = int(min(1.0, max(0.0, 3.0 * norm - 2.0)) * 255)
            table[d] = qRgb(r, g, b)
        elif colormap == "jet":
            # Black -> Blue -> Cyan -> Green -> Orange -> Red
            factor = min(1.0, max(0.0, norm * 10.0))
            r = int(min(1.0, max(0.0, 4.0 * norm - 2.0)) * 255)
            g = int(min(1.0, max(0.0, 1.5 - abs(3.0 * norm - 1.5))) * 255)
            b = int(min(1.0, max(0.0, 2.0 - 4.0 * norm)) * factor * 255)
            table[d] = qRgb(r, g, b)
        elif colormap == "green":
            # Neon Green: Black -> (0, 255, 102)
            table[d] = qRgb(0, v, int(v * 102 / 255))
        elif colormap == "magenta":
            # Neon Magenta: Black -> (255, 0, 153)
            table[d] = qRgb(v, 0, int(v * 153 / 255))
        elif colormap == "custom":
            # Custom Color: Black -> (cr, cg, cb)
            table[d] = qRgb(int(v * cr / 255), int(v * cg / 255), int(v * cb / 255))
        else:
            # grayscale (default)
            table[d] = qRgb(v, v, v)

    return table


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
        self._buf_tint_a: QImage | None = None
        self._buf_tint_b: QImage | None = None
        self._buf_diff: QImage | None = None
        self._diff_lut_cache_key: tuple[str, float, str] | None = None
        self._diff_color_table: list[int] = []

        self.setMinimumSize(320, 180)
        self.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)

    def _get_overlay_buffer(self, name: str, w: int, h: int) -> QImage:
        buf = getattr(self, name, None)
        if buf is None or buf.width() != w or buf.height() != h:
            buf = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
            setattr(self, name, buf)
        buf.fill(Qt.GlobalColor.black)
        return buf

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

        if (
            self._project.overlay.enabled
            and len(self._project.videos) >= 2
            and not self._solo_video_id
        ):
            self._draw_overlay(painter, common_t)
        else:
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
                badge_font = QFont("Pretendard Variable", 10)
                badge_font.setWeight(QFont.Weight.DemiBold)
                painter.setFont(badge_font)
                text = tr("솔로 뷰 (더블클릭하여 복귀)")
                badge = QRectF(
                    12, 12, max(210, QFontMetricsF(badge_font).horizontalAdvance(text) + 24), 28
                )
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(0, 0, 0, 180))
                painter.drawRoundedRect(badge, 4, 4)
                painter.setPen(QColor("#60A5FA"))
                painter.drawText(
                    badge,
                    Qt.AlignmentFlag.AlignCenter,
                    text,
                )

        painter.restore()

    def _draw_overlay(self, painter: QPainter, common_t: int) -> None:
        out_w = self._project.output.width
        out_h = self._project.output.height
        bounds = Rect(0, 0, out_w, out_h)
        video_map = self._video_map
        overlay = self._project.overlay

        vid_a = video_map.get(overlay.base_video_id) or self._project.videos[0]
        candidates = [v for v in self._project.videos if v.id != vid_a.id]
        vid_b = (
            video_map.get(overlay.overlay_video_id)
            if overlay.overlay_video_id and overlay.overlay_video_id in video_map
            else (candidates[0] if candidates else None)
        )
        if not vid_b:
            return

        rect_a = fit(vid_a.display_aspect, bounds)
        target_rect = QRectF(rect_a.x, rect_a.y, rect_a.width, rect_a.height)

        frame_a = self.player.get_frame(vid_a, common_t)
        frame_b = self.player.get_frame(vid_b, common_t)

        method = overlay.method
        has_both = (
            frame_a is not None
            and not frame_a.isNull()
            and frame_b is not None
            and not frame_b.isNull()
        )
        if has_both:
            if method == "blend":
                painter.drawImage(target_rect, frame_a)
                painter.save()
                painter.setOpacity(overlay.opacity)
                painter.drawImage(target_rect, frame_b)
                painter.restore()
            elif method == "tint":
                w_int = max(1, int(target_rect.width()))
                h_int = max(1, int(target_rect.height()))
                tinted_a = self._get_overlay_buffer("_buf_tint_a", w_int, h_int)
                pa = QPainter(tinted_a)
                pa.drawImage(tinted_a.rect(), frame_a)
                pa.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
                pa.fillRect(tinted_a.rect(), QColor(overlay.tint_a))
                pa.end()

                tinted_b = self._get_overlay_buffer("_buf_tint_b", w_int, h_int)
                pb = QPainter(tinted_b)
                pb.drawImage(tinted_b.rect(), frame_b)
                pb.setCompositionMode(QPainter.CompositionMode.CompositionMode_Multiply)
                pb.fillRect(tinted_b.rect(), QColor(overlay.tint_b))
                pb.end()

                painter.save()
                painter.drawImage(target_rect, tinted_a)
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Plus)
                painter.drawImage(target_rect, tinted_b)
                painter.restore()
            elif method == "difference":
                w_int = max(1, int(target_rect.width()))
                h_int = max(1, int(target_rect.height()))
                diff_img = self._get_overlay_buffer("_buf_diff", w_int, h_int)
                pd = QPainter(diff_img)
                pd.drawImage(diff_img.rect(), frame_a)
                pd.setCompositionMode(QPainter.CompositionMode.CompositionMode_Difference)
                pd.drawImage(diff_img.rect(), frame_b)
                pd.end()

                gain = max(1.0, float(overlay.gain))
                colormap = overlay.diff_colormap
                custom_hex = overlay.diff_custom_color

                cache_key = (colormap, gain, custom_hex)
                if self._diff_lut_cache_key != cache_key or not self._diff_color_table:
                    self._diff_color_table = _generate_diff_color_table(colormap, gain, custom_hex)
                    self._diff_lut_cache_key = cache_key

                gray = diff_img.convertToFormat(QImage.Format.Format_Grayscale8)
                indexed = QImage(
                    gray.constBits(),
                    gray.width(),
                    gray.height(),
                    gray.bytesPerLine(),
                    QImage.Format.Format_Indexed8,
                )
                indexed.setColorTable(self._diff_color_table)
                painter.drawImage(target_rect, indexed)
        elif frame_a is not None and not frame_a.isNull():
            painter.drawImage(target_rect, frame_a)
        elif frame_b is not None and not frame_b.isNull():
            painter.drawImage(target_rect, frame_b)

        # Draw overlay info badge via shared renderer
        self._renderer.draw(painter, common_t)

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
