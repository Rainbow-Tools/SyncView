"""Bottom control bar with common playback controls, scrubber, and audio selection."""

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QWidget,
)

from videos_multi_view.core.models import Project
from videos_multi_view.core.timeline import duration_ms, format_time


class TimelineBar(QWidget):
    """Controls for master playback, scrubber slider, time display, and audio track selection."""

    play_pause_requested = Signal()
    stop_requested = Signal()
    seek_requested = Signal(int)  # milliseconds
    audio_selected = Signal(object)  # str | None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project = Project()
        self._duration_ms = 0
        self._current_time_ms = 0
        self._is_user_scrubbing = False
        self._blocking_audio = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Play/Pause and Stop buttons
        self.btn_play = QPushButton("▶ 재생")
        self.btn_play.setMinimumWidth(80)
        self.btn_play.clicked.connect(self.play_pause_requested.emit)
        layout.addWidget(self.btn_play)

        self.btn_stop = QPushButton("⏹ 정지")
        self.btn_stop.clicked.connect(self.stop_requested.emit)
        layout.addWidget(self.btn_stop)

        # Scrubber slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 0)
        self.slider.sliderPressed.connect(self._on_slider_pressed)
        self.slider.sliderMoved.connect(self._on_slider_moved)
        self.slider.sliderReleased.connect(self._on_slider_released)
        layout.addWidget(self.slider, stretch=1)

        # Time label
        self.lbl_time = QLabel("00:00.000 / 00:00.000")
        self.lbl_time.setStyleSheet("font-family: monospace; font-size: 12px;")
        layout.addWidget(self.lbl_time)

        # Audio source selection
        layout.addWidget(QLabel("오디오:"))
        self.combo_audio = QComboBox()
        self.combo_audio.setMinimumWidth(150)
        self.combo_audio.currentIndexChanged.connect(self._on_audio_changed)
        layout.addWidget(self.combo_audio)

    def set_project(self, project: Project) -> None:
        self._project = project
        self._duration_ms = duration_ms(project)
        self.slider.setRange(0, self._duration_ms)

        self._update_time_label()
        self._populate_audio_sources()

    def set_position(self, position_ms: int) -> None:
        self._current_time_ms = position_ms
        if not self._is_user_scrubbing:
            self.slider.setValue(position_ms)
        self._update_time_label()

    def set_playback_state(self, is_playing: bool) -> None:
        self.btn_play.setText("⏸ 일시정지" if is_playing else "▶ 재생")

    def _update_time_label(self) -> None:
        curr = format_time(self._current_time_ms)
        total = format_time(self._duration_ms)
        self.lbl_time.setText(f"{curr} / {total}")

    def _populate_audio_sources(self) -> None:
        self._blocking_audio = True
        self.combo_audio.clear()

        # Default item: None (Mute)
        self.combo_audio.addItem("무음 (기본)", None)

        selected_index = 0
        for idx, video in enumerate(self._project.videos):
            name = video.label.text or Path(video.path).stem
            tag = "" if video.has_audio else " (오디오 없음)"
            label = f"{idx + 1}. {name}{tag}"
            self.combo_audio.addItem(label, video.id)
            if video.id == self._project.audio_id:
                selected_index = idx + 1

        self.combo_audio.setCurrentIndex(selected_index)
        self._blocking_audio = False

    def _on_audio_changed(self, index: int) -> None:
        if self._blocking_audio:
            return
        audio_id = self.combo_audio.currentData()
        self._project.audio_id = audio_id
        self.audio_selected.emit(audio_id)

    def _on_slider_pressed(self) -> None:
        self._is_user_scrubbing = True

    def _on_slider_moved(self, value: int) -> None:
        self._current_time_ms = value
        self._update_time_label()
        self.seek_requested.emit(value)

    def _on_slider_released(self) -> None:
        self._is_user_scrubbing = False
        self.seek_requested.emit(self.slider.value())
