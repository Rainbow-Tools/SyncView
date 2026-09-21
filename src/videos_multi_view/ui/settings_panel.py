"""Right panel for grid, canvas, selected video decoration, and export settings."""

from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFontComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from videos_multi_view.core.models import POSITIONS, Project, Video


class ColorButton(QPushButton):
    """Button showing a color swatch and opening a QColorDialog when clicked."""

    color_changed = Signal(str)

    def __init__(self, color_hex: str = "#ffffff", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._color = color_hex
        self.clicked.connect(self._choose_color)
        self._update_style()

    @property
    def color(self) -> str:
        return self._color

    def set_color(self, color_hex: str) -> None:
        self._color = color_hex
        self._update_style()

    def _update_style(self) -> None:
        self.setText(self._color)
        c = QColor(self._color)
        # Choose text color (white or black) based on luminance
        lum = 0.299 * c.red() + 0.587 * c.green() + 0.114 * c.blue()
        text_col = "#ffffff" if lum < 128 else "#000000"
        self.setStyleSheet(
            f"background-color: {c.name()}; color: {text_col}; "
            "font-family: monospace; font-weight: bold;"
        )

    def _choose_color(self) -> None:
        c = QColorDialog.getColor(
            QColor(self._color),
            self,
            "색상 선택",
            QColorDialog.ColorDialogOption.ShowAlphaChannel,
        )
        if c.isValid():
            # Format as #AARRGGBB if alpha < 255, else #RRGGBB
            if c.alpha() < 255:
                hex_str = f"#{c.alpha():02x}{c.red():02x}{c.green():02x}{c.blue():02x}"
            else:
                hex_str = c.name()
            self.set_color(hex_str)
            self.color_changed.emit(hex_str)


class SettingsPanel(QWidget):
    """Inspector panel for canvas layout, video properties, and export controls."""

    layout_updated = Signal()
    settings_requested = Signal(str, object)
    video_updated = Signal(str)  # video_id
    export_requested = Signal(Path, int, str)  # target_path, fps, encoder
    export_cancelled = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._project = Project()
        self._selected_video: Video | None = None
        self._blocking = False

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # 1. Canvas & Grid Settings Group
        grid_group = QGroupBox("그리드 설정")
        grid_form = QFormLayout(grid_group)

        # Output resolution
        res_layout = QHBoxLayout()
        self.spin_width = QSpinBox()
        self.spin_width.setRange(320, 7680)
        self.spin_width.setSingleStep(2)
        self.spin_width.setValue(1920)
        self.spin_width.valueChanged.connect(self._on_canvas_dim_changed)
        res_layout.addWidget(self.spin_width)
        res_layout.addWidget(QLabel("×"))
        self.spin_height = QSpinBox()
        self.spin_height.setRange(240, 4320)
        self.spin_height.setSingleStep(2)
        self.spin_height.setValue(1080)
        self.spin_height.valueChanged.connect(self._on_canvas_dim_changed)
        res_layout.addWidget(self.spin_height)
        grid_form.addRow("해상도", res_layout)

        # Columns
        self.spin_columns = QSpinBox()
        self.spin_columns.setRange(0, 9)
        self.spin_columns.setSpecialValueText("자동")
        self.spin_columns.valueChanged.connect(self._on_layout_changed)
        grid_form.addRow("열 수", self.spin_columns)

        # Gap and Margin
        self.spin_gap = QSpinBox()
        self.spin_gap.setRange(0, 100)
        self.spin_gap.setSingleStep(2)
        self.spin_gap.setValue(8)
        self.spin_gap.valueChanged.connect(self._on_layout_changed)
        grid_form.addRow("간격", self.spin_gap)

        self.spin_margin = QSpinBox()
        self.spin_margin.setRange(0, 200)
        self.spin_margin.setSingleStep(2)
        self.spin_margin.setValue(16)
        self.spin_margin.valueChanged.connect(self._on_layout_changed)
        grid_form.addRow("여백", self.spin_margin)

        # Background color
        self.btn_bg_color = ColorButton("#15191f")
        self.btn_bg_color.color_changed.connect(self._on_layout_changed)
        grid_form.addRow("배경색", self.btn_bg_color)

        # Border
        self.chk_border = QCheckBox("테두리")
        self.chk_border.toggled.connect(self._on_layout_changed)
        grid_form.addRow("", self.chk_border)

        self.spin_border_w = QSpinBox()
        self.spin_border_w.setRange(1, 50)
        self.spin_border_w.setValue(2)
        self.spin_border_w.valueChanged.connect(self._on_layout_changed)
        grid_form.addRow("두께", self.spin_border_w)

        self.btn_border_color = ColorButton("#ffffff")
        self.btn_border_color.color_changed.connect(self._on_layout_changed)
        grid_form.addRow("색상", self.btn_border_color)

        layout.addWidget(grid_group)

        # 2. Selected Video & Label Settings Group
        self.video_group = QGroupBox("영상 설정")
        vid_form = QFormLayout(self.video_group)

        self.spin_offset = QSpinBox()
        self.spin_offset.setRange(-600000, 600000)
        self.spin_offset.setSingleStep(100)
        self.spin_offset.setSuffix(" ms")
        self.spin_offset.valueChanged.connect(self._on_video_changed)
        vid_form.addRow("오프셋", self.spin_offset)

        self.edit_label_text = QLineEdit()
        self.edit_label_text.setPlaceholderText("이름표 문구 ({filename}, {timecode} 등)")
        self.edit_label_text.setToolTip(
            "지원 매크로: {filename}, {timecode}, {fps}, {resolution}, {offset}"
        )
        self.edit_label_text.textChanged.connect(self._on_video_changed)
        vid_form.addRow("이름표", self.edit_label_text)

        self.chk_label_vis = QCheckBox("표시")
        self.chk_label_vis.toggled.connect(self._on_video_changed)
        vid_form.addRow("", self.chk_label_vis)

        self.combo_label_pos = QComboBox()
        self.combo_label_pos.addItems(list(POSITIONS))
        self.combo_label_pos.currentTextChanged.connect(self._on_video_changed)
        vid_form.addRow("위치", self.combo_label_pos)

        self.combo_label_font = QFontComboBox()
        self.combo_label_font.currentFontChanged.connect(self._on_video_changed)
        vid_form.addRow("글꼴", self.combo_label_font)

        self.spin_label_size = QSpinBox()
        self.spin_label_size.setRange(8, 120)
        self.spin_label_size.setValue(28)
        self.spin_label_size.valueChanged.connect(self._on_video_changed)
        vid_form.addRow("크기", self.spin_label_size)

        self.btn_label_color = ColorButton("#ffffff")
        self.btn_label_color.color_changed.connect(self._on_video_changed)
        vid_form.addRow("색상", self.btn_label_color)

        self.btn_label_bg = ColorButton("#b3000000")
        self.btn_label_bg.color_changed.connect(self._on_video_changed)
        vid_form.addRow("배경", self.btn_label_bg)

        layout.addWidget(self.video_group)

        # 3. Export Settings Group
        export_group = QGroupBox("내보내기")
        export_layout = QVBoxLayout(export_group)

        exp_form = QFormLayout()
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["24", "30", "60"])
        self.combo_fps.setCurrentText("30")
        self.combo_fps.currentIndexChanged.connect(self._on_output_changed)
        exp_form.addRow("FPS", self.combo_fps)

        self.combo_encoder = QComboBox()
        self.combo_encoder.addItem("CPU (libx264 - 기본)", "libx264")
        self.combo_encoder.addItem("NVIDIA GPU (h264_nvenc)", "h264_nvenc")
        self.combo_encoder.addItem("Intel GPU (h264_qsv)", "h264_qsv")
        self.combo_encoder.currentIndexChanged.connect(self._on_output_changed)
        exp_form.addRow("인코더", self.combo_encoder)

        path_layout = QHBoxLayout()
        self.edit_export_path = QLineEdit()
        self.edit_export_path.setPlaceholderText("저장할 MP4 경로...")
        path_layout.addWidget(self.edit_export_path)
        self.btn_browse_export = QPushButton("찾기")
        self.btn_browse_export.clicked.connect(self._on_browse_export)
        path_layout.addWidget(self.btn_browse_export)
        exp_form.addRow("경로", path_layout)

        export_layout.addLayout(exp_form)

        btn_exp_layout = QHBoxLayout()
        self.btn_export = QPushButton("내보내기")
        self.btn_export.setObjectName("primaryButton")
        self.btn_export.clicked.connect(self._on_export_clicked)
        btn_exp_layout.addWidget(self.btn_export)

        self.btn_cancel_export = QPushButton("취소")
        self.btn_cancel_export.setEnabled(False)
        self.btn_cancel_export.clicked.connect(self.export_cancelled.emit)
        btn_exp_layout.addWidget(self.btn_cancel_export)

        export_layout.addLayout(btn_exp_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        export_layout.addWidget(self.progress_bar)

        self.export_status_label = QLabel("")
        self.export_status_label.setStyleSheet("font-size: 11px;")
        self.export_status_label.setWordWrap(True)
        export_layout.addWidget(self.export_status_label)

        layout.addWidget(export_group)
        layout.addStretch()

        scroll.setWidget(container)
        outer_layout.addWidget(scroll)

        self._update_video_group_state()

    def set_project(self, project: Project, selected_video_id: str | None = None) -> None:
        self._blocking = True
        self._project = project

        self.spin_width.setValue(project.output.width)
        self.spin_height.setValue(project.output.height)
        self.combo_fps.setCurrentText(str(project.output.fps))
        idx = self.combo_encoder.findData(project.output.encoder)
        if idx >= 0:
            self.combo_encoder.setCurrentIndex(idx)

        lay = project.layout
        self.spin_columns.setValue(lay.columns)
        self.spin_gap.setValue(lay.gap)
        self.spin_margin.setValue(lay.margin)
        self.btn_bg_color.set_color(lay.background)
        self.chk_border.setChecked(lay.border_visible)
        self.spin_border_w.setValue(lay.border_width)
        self.btn_border_color.set_color(lay.border_color)

        self.set_selected_video(selected_video_id)
        self._blocking = False

    def set_selected_video(self, video_id: str | None) -> None:
        self._blocking = True
        self._selected_video = next((v for v in self._project.videos if v.id == video_id), None)
        self._update_video_group_state()

        if self._selected_video:
            v = self._selected_video
            self.spin_offset.setValue(v.offset_ms)
            self.edit_label_text.setText(v.label.text)
            self.chk_label_vis.setChecked(v.label.visible)
            self.combo_label_pos.setCurrentText(v.label.position)
            self.spin_label_size.setValue(v.label.size)
            self.btn_label_color.set_color(v.label.color)
            self.btn_label_bg.set_color(v.label.background)
            if v.label.font_family:
                self.combo_label_font.setCurrentFont(QFont(v.label.font_family))
            else:
                self.combo_label_font.setCurrentFont(QFont("Pretendard"))

        self._blocking = False

    def _update_video_group_state(self) -> None:
        has_sel = self._selected_video is not None
        self.video_group.setEnabled(has_sel)
        if has_sel:
            name = self._selected_video.label.text or Path(self._selected_video.path).stem
            self.video_group.setTitle(f"영상 설정: {name}")
        else:
            self.video_group.setTitle("영상 설정 (선택 없음)")

    def _on_canvas_dim_changed(self) -> None:
        if self._blocking:
            return
        # Ensure even numbers
        w = self.spin_width.value() // 2 * 2
        h = self.spin_height.value() // 2 * 2
        output = deepcopy(self._project.output)
        output.width, output.height = w, h
        self.settings_requested.emit("layout", (deepcopy(self._project.layout), output))

    def _on_layout_changed(self) -> None:
        if self._blocking:
            return
        lay = deepcopy(self._project.layout)
        lay.columns = self.spin_columns.value()
        lay.gap = self.spin_gap.value()
        lay.margin = self.spin_margin.value()
        lay.background = self.btn_bg_color.color
        lay.border_visible = self.chk_border.isChecked()
        lay.border_width = self.spin_border_w.value()
        lay.border_color = self.btn_border_color.color
        self.settings_requested.emit("layout", (lay, deepcopy(self._project.output)))

    def _on_video_changed(self) -> None:
        if self._blocking or not self._selected_video:
            return
        v = deepcopy(self._selected_video)
        v.offset_ms = self.spin_offset.value()
        v.label.text = self.edit_label_text.text()
        v.label.visible = self.chk_label_vis.isChecked()
        v.label.position = self.combo_label_pos.currentText()
        v.label.size = self.spin_label_size.value()
        v.label.color = self.btn_label_color.color
        v.label.background = self.btn_label_bg.color
        v.label.font_family = self.combo_label_font.currentFont().family()
        self.settings_requested.emit("video", v)

    def _on_output_changed(self) -> None:
        if self._blocking or not hasattr(self, "combo_encoder"):
            return
        output = deepcopy(self._project.output)
        output.fps = int(self.combo_fps.currentText())
        output.encoder = self.combo_encoder.currentData() or "libx264"
        self.settings_requested.emit("output", output)

    def _on_browse_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "MP4 저장 경로 선택",
            self.edit_export_path.text() or "output.mp4",
            "MP4 영상 (*.mp4)",
        )
        if path:
            self.edit_export_path.setText(path)

    def _on_export_clicked(self) -> None:
        path_str = self.edit_export_path.text().strip()
        if not path_str:
            self._on_browse_export()
            path_str = self.edit_export_path.text().strip()
            if not path_str:
                return

        fps = int(self.combo_fps.currentText())
        encoder = self.combo_encoder.currentData() or "libx264"
        self.export_requested.emit(Path(path_str), fps, encoder)

    def set_exporting_state(self, exporting: bool) -> None:
        self.btn_export.setEnabled(not exporting)
        self.btn_cancel_export.setEnabled(exporting)
        self.progress_bar.setVisible(exporting)
        if exporting:
            self.progress_bar.setValue(0)
            self.export_status_label.setText("인코딩 중...")

    def update_export_progress(self, progress: float) -> None:
        self.progress_bar.setValue(int(progress * 100))

    def set_export_status(self, text: str, is_error: bool = False) -> None:
        color = "#F87171" if is_error else "#60A5FA"
        self.export_status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        self.export_status_label.setText(text)
