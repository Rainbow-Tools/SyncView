"""Right panel for grid, canvas, selected video decoration, and export settings."""

from copy import deepcopy
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
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
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from videos_multi_view.core.models import POSITIONS, Project, Video
from videos_multi_view.i18n import tr
from videos_multi_view.ui.translation import bind

POSITION_LABELS = ("왼쪽 위", "오른쪽 위", "왼쪽 아래", "오른쪽 아래")


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
            tr("색상 선택"),
            QColorDialog.ColorDialogOption.ShowAlphaChannel
            | QColorDialog.ColorDialogOption.DontUseNativeDialog,
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
        grid_group = bind(QGroupBox(), "그리드 설정", setter="setTitle")
        grid_form = QFormLayout(grid_group)
        grid_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

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
        grid_form.addRow(bind(QLabel(), "해상도"), res_layout)

        # Columns
        self.spin_columns = QSpinBox()
        self.spin_columns.setRange(0, 9)
        bind(self.spin_columns, "자동", setter="setSpecialValueText")
        self.spin_columns.valueChanged.connect(self._on_layout_changed)
        grid_form.addRow(bind(QLabel(), "열 수"), self.spin_columns)

        # Gap and Margin
        self.spin_gap = QSpinBox()
        self.spin_gap.setRange(0, 100)
        self.spin_gap.setSingleStep(2)
        self.spin_gap.setValue(8)
        self.spin_gap.valueChanged.connect(self._on_layout_changed)
        grid_form.addRow(bind(QLabel(), "간격"), self.spin_gap)

        self.spin_margin = QSpinBox()
        self.spin_margin.setRange(0, 200)
        self.spin_margin.setSingleStep(2)
        self.spin_margin.setValue(16)
        self.spin_margin.valueChanged.connect(self._on_layout_changed)
        grid_form.addRow(bind(QLabel(), "여백"), self.spin_margin)

        # Background color
        self.btn_bg_color = ColorButton("#15191f")
        self.btn_bg_color.color_changed.connect(self._on_layout_changed)
        grid_form.addRow(bind(QLabel(), "배경색"), self.btn_bg_color)

        # Border
        self.chk_border = bind(QCheckBox(), "테두리")
        self.chk_border.toggled.connect(self._on_layout_changed)
        grid_form.addRow("", self.chk_border)

        self.spin_border_w = QSpinBox()
        self.spin_border_w.setRange(1, 50)
        self.spin_border_w.setValue(2)
        self.spin_border_w.valueChanged.connect(self._on_layout_changed)
        grid_form.addRow(bind(QLabel(), "두께"), self.spin_border_w)

        self.btn_border_color = ColorButton("#ffffff")
        self.btn_border_color.color_changed.connect(self._on_layout_changed)
        grid_form.addRow(bind(QLabel(), "색상"), self.btn_border_color)

        layout.addWidget(grid_group)

        # 2. Overlay Comparison Settings Group
        self.overlay_group = bind(QGroupBox(), "오버레이 비교", setter="setTitle")
        ov_form = QFormLayout(self.overlay_group)
        ov_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        self.chk_overlay = bind(QCheckBox(), "오버레이 비교 모드 활성화")
        self.chk_overlay.toggled.connect(self._on_overlay_toggled)
        ov_form.addRow("", self.chk_overlay)

        self.combo_ov_base = QComboBox()
        self.combo_ov_base.currentIndexChanged.connect(self._on_overlay_changed)
        self.lbl_ov_base = bind(QLabel(), "기준 영상 (A)")
        ov_form.addRow(self.lbl_ov_base, self.combo_ov_base)

        self.combo_ov_target = QComboBox()
        self.combo_ov_target.currentIndexChanged.connect(self._on_overlay_changed)
        self.lbl_ov_target = bind(QLabel(), "비교 영상 (B)")
        ov_form.addRow(self.lbl_ov_target, self.combo_ov_target)

        self.combo_ov_method = QComboBox()
        self.combo_ov_method.addItem(tr("투명도 블렌드 (Alpha Blend)"), "blend")
        self.combo_ov_method.addItem(tr("색상 틴트 비교 (Red / Cyan)"), "tint")
        self.combo_ov_method.addItem(tr("잔차 오류 맵 (Difference)"), "difference")
        self.combo_ov_method.currentIndexChanged.connect(self._on_overlay_method_changed)
        self.lbl_ov_method = bind(QLabel(), "비교 방식")
        ov_form.addRow(self.lbl_ov_method, self.combo_ov_method)

        self.row_opacity_widget = QWidget()
        row_op_lay = QHBoxLayout(self.row_opacity_widget)
        row_op_lay.setContentsMargins(0, 0, 0, 0)
        self.slider_ov_opacity = QSlider(Qt.Orientation.Horizontal)
        self.slider_ov_opacity.setRange(0, 100)
        self.slider_ov_opacity.setValue(50)
        self.spin_ov_opacity = QSpinBox()
        self.spin_ov_opacity.setRange(0, 100)
        self.spin_ov_opacity.setSuffix("%")
        self.spin_ov_opacity.setValue(50)
        self.slider_ov_opacity.valueChanged.connect(self.spin_ov_opacity.setValue)
        self.spin_ov_opacity.valueChanged.connect(self.slider_ov_opacity.setValue)
        self.spin_ov_opacity.valueChanged.connect(self._on_overlay_changed)
        row_op_lay.addWidget(self.slider_ov_opacity, stretch=1)
        row_op_lay.addWidget(self.spin_ov_opacity)
        self.lbl_ov_opacity = bind(QLabel(), "투명도 (B)")
        ov_form.addRow(self.lbl_ov_opacity, self.row_opacity_widget)

        self.spin_ov_gain = QDoubleSpinBox()
        self.spin_ov_gain.setRange(1.0, 50.0)
        self.spin_ov_gain.setSingleStep(1.0)
        self.spin_ov_gain.setValue(1.0)
        self.spin_ov_gain.setSuffix("x")
        self.spin_ov_gain.valueChanged.connect(self._on_overlay_changed)
        self.lbl_ov_gain = bind(QLabel(), "잔차 증폭")
        ov_form.addRow(self.lbl_ov_gain, self.spin_ov_gain)

        self.combo_diff_colormap = QComboBox()
        self.combo_diff_colormap.addItem(tr("흑백 (기본)"), "grayscale")
        self.combo_diff_colormap.addItem(tr("히트맵 (Heatmap)"), "heat")
        self.combo_diff_colormap.addItem(tr("레인보우 (Jet)"), "jet")
        self.combo_diff_colormap.addItem(tr("네온 그린"), "green")
        self.combo_diff_colormap.addItem(tr("네온 마젠타"), "magenta")
        self.combo_diff_colormap.addItem(tr("사용자 지정"), "custom")
        self.combo_diff_colormap.currentIndexChanged.connect(self._on_diff_colormap_changed)
        self.lbl_ov_diff_color = bind(QLabel(), "잔차 색상")
        ov_form.addRow(self.lbl_ov_diff_color, self.combo_diff_colormap)

        self.btn_diff_color = ColorButton("#00FF66")
        self.btn_diff_color.color_changed.connect(self._on_overlay_changed)
        self.lbl_diff_custom = bind(QLabel(), "지정 색상")
        ov_form.addRow(self.lbl_diff_custom, self.btn_diff_color)

        self.combo_ov_tint = QComboBox()
        self.combo_ov_tint.addItem(tr("Red / Cyan (기본)"), ("#FF0000", "#00FFFF"))
        self.combo_ov_tint.addItem(tr("Green / Magenta"), ("#00FF00", "#FF00FF"))
        self.combo_ov_tint.addItem(tr("Blue / Yellow"), ("#0000FF", "#FFFF00"))
        self.combo_ov_tint.currentIndexChanged.connect(self._on_overlay_changed)
        self.lbl_ov_tint = bind(QLabel(), "틴트 배색")
        ov_form.addRow(self.lbl_ov_tint, self.combo_ov_tint)

        layout.addWidget(self.overlay_group)

        # 2. Selected Video & Label Settings Group
        self.video_group = bind(QGroupBox(), "영상 설정", setter="setTitle")
        vid_form = QFormLayout(self.video_group)
        vid_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)

        self.spin_offset = QSpinBox()
        self.spin_offset.setRange(-600000, 600000)
        self.spin_offset.setSingleStep(100)
        self.spin_offset.setSuffix(" ms")
        self.spin_offset.valueChanged.connect(self._on_video_changed)
        vid_form.addRow(bind(QLabel(), "오프셋"), self.spin_offset)

        self.edit_label_text = QLineEdit()
        bind(
            self.edit_label_text,
            "이름표 문구 ({filename}, {timecode} 등)",
            setter="setPlaceholderText",
        )
        bind(
            self.edit_label_text,
            "지원 매크로: {filename}, {timecode}, {fps}, {resolution}, {offset}",
            setter="setToolTip",
        )
        self.edit_label_text.textChanged.connect(self._on_video_changed)
        vid_form.addRow(bind(QLabel(), "이름표"), self.edit_label_text)

        self.chk_label_vis = bind(QCheckBox(), "표시")
        self.chk_label_vis.toggled.connect(self._on_video_changed)
        vid_form.addRow("", self.chk_label_vis)

        self.combo_label_pos = QComboBox()
        for code, label in zip(POSITIONS, POSITION_LABELS, strict=True):
            self.combo_label_pos.addItem(tr(label), code)
        self.combo_label_pos.currentIndexChanged.connect(self._on_video_changed)
        vid_form.addRow(bind(QLabel(), "위치"), self.combo_label_pos)

        self.combo_label_font = QFontComboBox()
        self.combo_label_font.currentFontChanged.connect(self._on_video_changed)
        vid_form.addRow(bind(QLabel(), "글꼴"), self.combo_label_font)

        self.spin_label_size = QSpinBox()
        self.spin_label_size.setRange(8, 120)
        self.spin_label_size.setValue(28)
        self.spin_label_size.valueChanged.connect(self._on_video_changed)
        vid_form.addRow(bind(QLabel(), "크기"), self.spin_label_size)

        self.btn_label_color = ColorButton("#ffffff")
        self.btn_label_color.color_changed.connect(self._on_video_changed)
        vid_form.addRow(bind(QLabel(), "색상"), self.btn_label_color)

        self.btn_label_bg = ColorButton("#b3000000")
        self.btn_label_bg.color_changed.connect(self._on_video_changed)
        vid_form.addRow(bind(QLabel(), "배경"), self.btn_label_bg)

        layout.addWidget(self.video_group)

        # 3. Export Settings Group
        export_group = bind(QGroupBox(), "내보내기", setter="setTitle")
        export_layout = QVBoxLayout(export_group)

        exp_form = QFormLayout()
        exp_form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        self.combo_fps = QComboBox()
        self.combo_fps.addItems(["24", "30", "60"])
        self.combo_fps.setCurrentText("30")
        self.combo_fps.currentIndexChanged.connect(self._on_output_changed)
        exp_form.addRow("FPS", self.combo_fps)

        self.combo_encoder = QComboBox()
        self.combo_encoder.addItem(tr("CPU (libx264 - 기본)"), "libx264")
        self.combo_encoder.addItem("NVIDIA GPU (h264_nvenc)", "h264_nvenc")
        self.combo_encoder.addItem("Intel GPU (h264_qsv)", "h264_qsv")
        self.combo_encoder.currentIndexChanged.connect(self._on_output_changed)
        exp_form.addRow(bind(QLabel(), "인코더"), self.combo_encoder)

        path_layout = QHBoxLayout()
        self.edit_export_path = QLineEdit()
        bind(self.edit_export_path, "저장할 MP4 경로...", setter="setPlaceholderText")
        path_layout.addWidget(self.edit_export_path)
        self.btn_browse_export = bind(QPushButton(), "찾기")
        self.btn_browse_export.clicked.connect(self._on_browse_export)
        path_layout.addWidget(self.btn_browse_export)
        exp_form.addRow(bind(QLabel(), "경로"), path_layout)

        export_layout.addLayout(exp_form)

        btn_exp_layout = QHBoxLayout()
        self.btn_export = bind(QPushButton(), "내보내기")
        self.btn_export.setObjectName("primaryButton")
        self.btn_export.clicked.connect(self._on_export_clicked)
        btn_exp_layout.addWidget(self.btn_export)

        self.btn_cancel_export = bind(QPushButton(), "취소")
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

        # Update overlay controls
        ov = project.overlay
        self.chk_overlay.setChecked(ov.enabled)
        self.chk_overlay.setEnabled(len(project.videos) >= 2)

        with QSignalBlocker(self.combo_ov_base), QSignalBlocker(self.combo_ov_target):
            self.combo_ov_base.clear()
            self.combo_ov_target.clear()
            for v in project.videos:
                name = v.label.text or Path(v.path).stem
                self.combo_ov_base.addItem(name, v.id)
                self.combo_ov_target.addItem(name, v.id)

            if ov.base_video_id:
                idx_b = self.combo_ov_base.findData(ov.base_video_id)
                if idx_b >= 0:
                    self.combo_ov_base.setCurrentIndex(idx_b)
            elif len(project.videos) >= 1:
                self.combo_ov_base.setCurrentIndex(0)

            if ov.overlay_video_id:
                idx_t = self.combo_ov_target.findData(ov.overlay_video_id)
                if idx_t >= 0:
                    self.combo_ov_target.setCurrentIndex(idx_t)
            elif len(project.videos) >= 2:
                self.combo_ov_target.setCurrentIndex(1)

        idx_m = self.combo_ov_method.findData(ov.method)
        if idx_m >= 0:
            self.combo_ov_method.setCurrentIndex(idx_m)

        self.slider_ov_opacity.setValue(int(ov.opacity * 100))
        self.spin_ov_opacity.setValue(int(ov.opacity * 100))
        self.spin_ov_gain.setValue(ov.gain)

        idx_dc = self.combo_diff_colormap.findData(ov.diff_colormap)
        if idx_dc >= 0:
            self.combo_diff_colormap.setCurrentIndex(idx_dc)
        self.btn_diff_color.set_color(ov.diff_custom_color)

        for i in range(self.combo_ov_tint.count()):
            pair = self.combo_ov_tint.itemData(i)
            if pair and pair[0] == ov.tint_a and pair[1] == ov.tint_b:
                self.combo_ov_tint.setCurrentIndex(i)
                break

        self._update_overlay_group_visibility()

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
            self.combo_label_pos.setCurrentIndex(self.combo_label_pos.findData(v.label.position))
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
            bind(self.video_group, "영상 설정: {value0}", setter="setTitle", value0=name)
        else:
            bind(self.video_group, "영상 설정 (선택 없음)", setter="setTitle")

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
        v.label.position = self.combo_label_pos.currentData()
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

    def _update_overlay_group_visibility(self) -> None:
        enabled = self.chk_overlay.isChecked()
        self.combo_ov_base.setEnabled(enabled)
        self.combo_ov_target.setEnabled(enabled)
        self.combo_ov_method.setEnabled(enabled)
        method = self.combo_ov_method.currentData() or "blend"
        is_blend = enabled and (method == "blend")
        is_diff = enabled and (method == "difference")
        is_tint = enabled and (method == "tint")

        is_custom_diff = is_diff and (self.combo_diff_colormap.currentData() == "custom")
        self.row_opacity_widget.setVisible(is_blend)
        self.lbl_ov_opacity.setVisible(is_blend)
        self.spin_ov_gain.setVisible(is_diff)
        self.lbl_ov_gain.setVisible(is_diff)
        self.lbl_ov_diff_color.setVisible(is_diff)
        self.combo_diff_colormap.setVisible(is_diff)
        self.lbl_diff_custom.setVisible(is_custom_diff)
        self.btn_diff_color.setVisible(is_custom_diff)
        self.combo_ov_tint.setVisible(is_tint)
        self.lbl_ov_tint.setVisible(is_tint)

    def _on_overlay_toggled(self, checked: bool) -> None:
        self._update_overlay_group_visibility()
        self._on_overlay_changed()

    def _on_overlay_method_changed(self) -> None:
        self._update_overlay_group_visibility()
        self._on_overlay_changed()

    def _on_diff_colormap_changed(self) -> None:
        self._update_overlay_group_visibility()
        self._on_overlay_changed()

    def _on_overlay_changed(self) -> None:
        if self._blocking:
            return
        overlay = deepcopy(self._project.overlay)
        overlay.enabled = self.chk_overlay.isChecked()
        overlay.base_video_id = self.combo_ov_base.currentData()
        overlay.overlay_video_id = self.combo_ov_target.currentData()
        overlay.method = self.combo_ov_method.currentData() or "blend"
        overlay.opacity = self.spin_ov_opacity.value() / 100.0
        overlay.gain = self.spin_ov_gain.value()
        overlay.diff_colormap = self.combo_diff_colormap.currentData() or "grayscale"
        overlay.diff_custom_color = self.btn_diff_color.color
        tint_pair = self.combo_ov_tint.currentData()
        if tint_pair:
            overlay.tint_a, overlay.tint_b = tint_pair
        self.settings_requested.emit("overlay", overlay)

    def set_overlay_enabled(self, enabled: bool) -> None:
        self.chk_overlay.setChecked(enabled)

    def retranslate(self) -> None:
        with QSignalBlocker(self.combo_label_pos), QSignalBlocker(self.combo_encoder):
            for index, source in enumerate(POSITION_LABELS):
                self.combo_label_pos.setItemText(index, tr(source))
            self.combo_encoder.setItemText(0, tr("CPU (libx264 - 기본)"))
        with (
            QSignalBlocker(self.combo_ov_method),
            QSignalBlocker(self.combo_ov_tint),
            QSignalBlocker(self.combo_diff_colormap),
        ):
            self.combo_ov_method.setItemText(0, tr("투명도 블렌드 (Alpha Blend)"))
            self.combo_ov_method.setItemText(1, tr("색상 틴트 비교 (Red / Cyan)"))
            self.combo_ov_method.setItemText(2, tr("잔차 오류 맵 (Difference)"))
            self.combo_ov_tint.setItemText(0, tr("Red / Cyan (기본)"))
            self.combo_ov_tint.setItemText(1, tr("Green / Magenta"))
            self.combo_ov_tint.setItemText(2, tr("Blue / Yellow"))
            self.combo_diff_colormap.setItemText(0, tr("흑백 (기본)"))
            self.combo_diff_colormap.setItemText(1, tr("히트맵 (Heatmap)"))
            self.combo_diff_colormap.setItemText(2, tr("레인보우 (Jet)"))
            self.combo_diff_colormap.setItemText(3, tr("네온 그린"))
            self.combo_diff_colormap.setItemText(4, tr("네온 마젠타"))
            self.combo_diff_colormap.setItemText(5, tr("사용자 지정"))

    def _on_browse_export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr("MP4 저장 경로 선택"),
            self.edit_export_path.text() or "output.mp4",
            tr("MP4 영상 (*.mp4)"),
            options=QFileDialog.Option.DontUseNativeDialog,
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
            bind(self.export_status_label, "인코딩 중...", setter="setText")

    def update_export_progress(self, progress: float) -> None:
        self.progress_bar.setValue(int(progress * 100))

    def set_export_status(self, source: str, is_error: bool = False, **values: object) -> None:
        color = "#F87171" if is_error else "#60A5FA"
        self.export_status_label.setStyleSheet(f"color: {color}; font-size: 11px;")
        bind(self.export_status_label, source, **values)
