"""Left panel for video list management, reordering, and drag-and-drop."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from videos_multi_view.core.models import Video
from videos_multi_view.core.timeline import format_time
from videos_multi_view.i18n import tr
from videos_multi_view.ui.translation import bind


class VideoListPanel(QWidget):
    """Panel managing video items, additions, deletions, and ordering."""

    add_files_requested = Signal(list)  # list[str] paths
    remove_video_requested = Signal(str)  # video_id
    move_video_requested = Signal(str, int)  # video_id, direction (-1 up, +1 down)
    video_selected = Signal(str)  # video_id
    relink_requested = Signal(str, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._videos: list[Video] = []
        self._selected_id: str | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header
        self.title_label = bind(QLabel(), "영상 목록 (0)")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #60A5FA;")
        layout.addWidget(self.title_label)

        # List Widget
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_widget.currentRowChanged.connect(self._on_row_changed)
        layout.addWidget(self.list_widget)

        # Control Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(4)

        self.btn_add = bind(QPushButton(), "추가")
        self.btn_add.clicked.connect(self._on_add_clicked)
        btn_layout.addWidget(self.btn_add)

        self.btn_up = QPushButton("▲")
        bind(self.btn_up, "위로", setter="setToolTip")
        self.btn_up.setMaximumWidth(36)
        self.btn_up.clicked.connect(self._on_up_clicked)
        btn_layout.addWidget(self.btn_up)

        self.btn_down = QPushButton("▼")
        bind(self.btn_down, "아래로", setter="setToolTip")
        self.btn_down.setMaximumWidth(36)
        self.btn_down.clicked.connect(self._on_down_clicked)
        btn_layout.addWidget(self.btn_down)

        self.btn_delete = bind(QPushButton(), "삭제")
        self.btn_delete.clicked.connect(self._on_delete_clicked)
        btn_layout.addWidget(self.btn_delete)

        layout.addLayout(btn_layout)
        self.btn_relink = bind(QPushButton(), "원본 다시 연결…")
        self.btn_relink.clicked.connect(self._on_relink_clicked)
        layout.addWidget(self.btn_relink)

        # Status & Error Banner
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #94A3B8; font-size: 11px;")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self._update_buttons()

    def set_videos(self, videos: list[Video], selected_id: str | None = None) -> None:
        self._videos = list(videos)
        self._selected_id = selected_id
        bind(self.title_label, "영상 목록 ({value0})", setter="setText", value0=len(self._videos))

        self.list_widget.blockSignals(True)
        self.list_widget.clear()

        selected_row = -1
        for idx, video in enumerate(self._videos):
            name = video.label.text or Path(video.path).name
            dur_str = format_time(video.duration_ms)
            audio_str = tr("오디오 있음" if video.has_audio else "무음")
            details = f"{video.width}×{video.height} | {video.fps:.1f}fps | {dur_str} | {audio_str}"
            text = f"{idx + 1}. {name}\n   {details}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, video.id)
            self.list_widget.addItem(item)

            if video.id == selected_id:
                selected_row = idx

        if selected_row >= 0:
            self.list_widget.setCurrentRow(selected_row)
        else:
            self.list_widget.clearSelection()

        self.list_widget.blockSignals(False)
        self._update_buttons()

    def set_selected_video(self, video_id: str | None) -> None:
        self._selected_id = video_id
        self.list_widget.blockSignals(True)
        for row in range(self.list_widget.count()):
            item = self.list_widget.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == video_id:
                self.list_widget.setCurrentRow(row)
                break
        else:
            self.list_widget.clearSelection()
        self.list_widget.blockSignals(False)
        self._update_buttons()

    def retranslate(self) -> None:
        scroll = self.list_widget.verticalScrollBar().value()
        self.set_videos(self._videos, self._selected_id)
        self.list_widget.verticalScrollBar().setValue(scroll)

    def set_status(self, text: str, is_error: bool = False) -> None:
        color = "#F87171" if is_error else "#94A3B8"
        self.status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.status_label.setText(text)

    def _on_row_changed(self, row: int) -> None:
        if 0 <= row < len(self._videos):
            vid_id = self._videos[row].id
            self._selected_id = vid_id
            self.video_selected.emit(vid_id)
        else:
            self._selected_id = None
        self._update_buttons()

    def _on_add_clicked(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr("동영상 추가"),
            "",
            tr("동영상 파일 (*.mp4 *.mkv *.mov *.avi *.webm);;모든 파일 (*.*)"),
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if paths:
            self.add_files_requested.emit(paths)

    def _on_delete_clicked(self) -> None:
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._videos):
            self.remove_video_requested.emit(self._videos[row].id)

    def _on_up_clicked(self) -> None:
        row = self.list_widget.currentRow()
        if row > 0:
            self.move_video_requested.emit(self._videos[row].id, -1)

    def _on_relink_clicked(self) -> None:
        if self._selected_id:
            path, _ = QFileDialog.getOpenFileName(
                self,
                tr("원본 영상 다시 연결"),
                "",
                tr("영상 (*.*)"),
                options=QFileDialog.Option.DontUseNativeDialog,
            )
            if path:
                self.relink_requested.emit(self._selected_id, path)

    def _on_down_clicked(self) -> None:
        row = self.list_widget.currentRow()
        if 0 <= row < len(self._videos) - 1:
            self.move_video_requested.emit(self._videos[row].id, 1)

    def _update_buttons(self) -> None:
        row = self.list_widget.currentRow()
        has_sel = 0 <= row < len(self._videos)
        self.btn_delete.setEnabled(has_sel)
        self.btn_relink.setEnabled(has_sel)
        self.btn_up.setEnabled(has_sel and row > 0)
        self.btn_down.setEnabled(has_sel and row < len(self._videos) - 1)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        paths = [url.toLocalFile() for url in urls if url.isLocalFile()]
        if paths:
            self.add_files_requested.emit(paths)
