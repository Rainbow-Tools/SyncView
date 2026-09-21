"""Main application window assembling video list, preview canvas, settings, and timeline."""

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QKeyEvent, QKeySequence
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from videos_multi_view import __version__
from videos_multi_view.application.controller import AppController
from videos_multi_view.media.player import SyncPlayer
from videos_multi_view.media.tools import resource_root
from videos_multi_view.ui.help_dialog import HelpDialog
from videos_multi_view.ui.preview import PreviewCanvas
from videos_multi_view.ui.settings_panel import SettingsPanel
from videos_multi_view.ui.timeline_bar import TimelineBar
from videos_multi_view.ui.video_list import VideoListPanel


class MainWindow(QMainWindow):
    """Main window coordinating UI panels, menu actions, and media playback."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("SyncView")
        self.resize(1360, 840)

        # Set App Icon
        icon_path = resource_root() / "assets" / "logo.png"
        if not icon_path.is_file():
            icon_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Core components
        self.player = SyncPlayer(self)
        self.controller = AppController(self.player, self)

        # UI Widgets
        self.preview_canvas = PreviewCanvas(self.player)
        self.video_list_panel = VideoListPanel()
        self.settings_panel = SettingsPanel()
        self.timeline_bar = TimelineBar()

        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

        # Initialize with empty project
        self.controller.new_project()

    def _setup_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Center container with responsive control bar
        center_container = QWidget()
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(2)

        # Slim view header toolbar for toggling sidebars
        view_header = QWidget()
        view_header.setObjectName("viewHeader")
        header_layout = QHBoxLayout(view_header)
        header_layout.setContentsMargins(4, 2, 4, 2)
        header_layout.setSpacing(6)

        self.btn_toggle_left = QPushButton("◧ 영상 목록")
        self.btn_toggle_left.setObjectName("toggleButton")
        self.btn_toggle_left.setCheckable(True)
        self.btn_toggle_left.setChecked(True)
        self.btn_toggle_left.setToolTip("영상 목록 패널 접기 / 펼치기 (Ctrl+1)")
        self.btn_toggle_left.toggled.connect(self._on_toggle_left_panel)
        header_layout.addWidget(self.btn_toggle_left)

        self.lbl_view_status = QLabel("멀티뷰 그리드 (0개 영상)")
        self.lbl_view_status.setObjectName("viewStatusLabel")
        header_layout.addWidget(self.lbl_view_status)

        header_layout.addStretch()

        self.btn_toggle_maximize = QPushButton("⛶ 최대화")
        self.btn_toggle_maximize.setObjectName("toggleButton")
        self.btn_toggle_maximize.setCheckable(True)
        self.btn_toggle_maximize.setChecked(False)
        self.btn_toggle_maximize.setToolTip("미리보기 전체화면 모드 (F11)")
        self.btn_toggle_maximize.toggled.connect(self._on_toggle_maximize)
        header_layout.addWidget(self.btn_toggle_maximize)

        self.btn_toggle_right = QPushButton("설정 ◨")
        self.btn_toggle_right.setObjectName("toggleButton")
        self.btn_toggle_right.setCheckable(True)
        self.btn_toggle_right.setChecked(True)
        self.btn_toggle_right.setToolTip("설정 패널 접기 / 펼치기 (Ctrl+2)")
        self.btn_toggle_right.toggled.connect(self._on_toggle_right_panel)
        header_layout.addWidget(self.btn_toggle_right)

        center_layout.addWidget(view_header)
        center_layout.addWidget(self.preview_canvas, stretch=1)

        # Splitter: Left (List), Center (Preview), Right (Settings)
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.video_list_panel)
        self.splitter.addWidget(center_container)
        self.splitter.addWidget(self.settings_panel)

        # Initial sizes
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setStretchFactor(2, 0)
        self.splitter.setSizes([260, 800, 300])

        main_layout.addWidget(self.splitter, stretch=1)
        main_layout.addWidget(self.timeline_bar)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("준비")

        # Permanent progress bar for background tasks (probe, export)
        self.status_progress = QProgressBar()
        self.status_progress.setFixedSize(140, 14)
        self.status_progress.setVisible(False)
        self.status_bar.addPermanentWidget(self.status_progress)

    def _setup_menu(self) -> None:
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("파일(&F)")

        act_new = QAction("새 프로젝트(&N)", self)
        act_new.setShortcut(QKeySequence.StandardKey.New)
        act_new.triggered.connect(self._on_new_project)
        file_menu.addAction(act_new)

        act_open = QAction("열기(&O)...", self)
        act_open.setShortcut(QKeySequence.StandardKey.Open)
        act_open.triggered.connect(self._on_open_project)
        file_menu.addAction(act_open)

        act_save = QAction("저장(&S)", self)
        act_save.setShortcut(QKeySequence.StandardKey.Save)
        act_save.triggered.connect(self._on_save_project)
        file_menu.addAction(act_save)

        act_save_as = QAction("다른 이름으로 저장(&A)...", self)
        act_save_as.setShortcut(QKeySequence.StandardKey.SaveAs)
        act_save_as.triggered.connect(self._on_save_project_as)
        file_menu.addAction(act_save_as)

        file_menu.addSeparator()

        act_exit = QAction("종료(&X)", self)
        act_exit.setShortcut(QKeySequence.StandardKey.Quit)
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # View menu
        view_menu = menubar.addMenu("보기(&V)")

        self.act_view_left = QAction("영상 목록 패널(&L)", self, checkable=True)
        self.act_view_left.setChecked(True)
        self.act_view_left.setShortcut(QKeySequence("Ctrl+1"))
        self.act_view_left.toggled.connect(self.btn_toggle_left.setChecked)
        view_menu.addAction(self.act_view_left)

        self.act_view_right = QAction("설정 패널(&S)", self, checkable=True)
        self.act_view_right.setChecked(True)
        self.act_view_right.setShortcut(QKeySequence("Ctrl+2"))
        self.act_view_right.toggled.connect(self.btn_toggle_right.setChecked)
        view_menu.addAction(self.act_view_right)

        view_menu.addSeparator()

        self.act_view_max = QAction("전체화면 미리보기(&F)", self, checkable=True)
        self.act_view_max.setChecked(False)
        self.act_view_max.setShortcut(QKeySequence("F11"))
        self.act_view_max.toggled.connect(self.btn_toggle_maximize.setChecked)
        view_menu.addAction(self.act_view_max)

        # Help menu
        help_menu = menubar.addMenu("도움말(&H)")

        act_help = QAction("사용 설명서(&H)...", self)
        act_help.setShortcut(QKeySequence(Qt.Key.Key_F1))
        act_help.triggered.connect(lambda: self._on_show_help(0))
        help_menu.addAction(act_help)

        act_shortcuts = QAction("키보드 단축키 안내(&K)...", self)
        act_shortcuts.triggered.connect(lambda: self._on_show_help(6))
        help_menu.addAction(act_shortcuts)

        act_licenses = QAction("오픈소스 라이선스 고지(&L)...", self)
        act_licenses.triggered.connect(lambda: self._on_show_help(7))
        help_menu.addAction(act_licenses)

        help_menu.addSeparator()

        act_about = QAction("SyncView 정보(&A)...", self)
        act_about.triggered.connect(self._on_about)
        help_menu.addAction(act_about)

    def _on_toggle_left_panel(self, checked: bool) -> None:
        self.video_list_panel.setVisible(checked)
        self.btn_toggle_left.setText("◧ 영상 목록" if checked else "▢ 영상 목록")
        if self.act_view_left.isChecked() != checked:
            self.act_view_left.setChecked(checked)

    def _on_toggle_right_panel(self, checked: bool) -> None:
        self.settings_panel.setVisible(checked)
        self.btn_toggle_right.setText("설정 ◨" if checked else "설정 ▢")
        if self.act_view_right.isChecked() != checked:
            self.act_view_right.setChecked(checked)

    def _on_toggle_maximize(self, checked: bool) -> None:
        if checked:
            self._saved_left_vis = self.video_list_panel.isVisible()
            self._saved_right_vis = self.settings_panel.isVisible()
            self.btn_toggle_left.setChecked(False)
            self.btn_toggle_right.setChecked(False)
            self.btn_toggle_maximize.setText("⛶ 축소")
        else:
            self.btn_toggle_left.setChecked(getattr(self, "_saved_left_vis", True))
            self.btn_toggle_right.setChecked(getattr(self, "_saved_right_vis", True))
            self.btn_toggle_maximize.setText("⛶ 최대화")
        if self.act_view_max.isChecked() != checked:
            self.act_view_max.setChecked(checked)

    def _connect_signals(self) -> None:
        # Video list panel
        self.video_list_panel.add_files_requested.connect(self.controller.add_video_files)
        self.video_list_panel.remove_video_requested.connect(self.controller.remove_video)
        self.video_list_panel.move_video_requested.connect(self.controller.move_video)
        self.video_list_panel.video_selected.connect(self.controller.select_video)
        self.video_list_panel.relink_requested.connect(self.controller.relink_video)

        # Preview canvas
        self.preview_canvas.video_selected.connect(self.controller.select_video)
        self.preview_canvas.solo_changed.connect(self._on_solo_changed)

        # Settings panel
        self.settings_panel.layout_updated.connect(self.controller.update_layout)
        self.settings_panel.settings_requested.connect(self.controller.apply_settings)
        self.settings_panel.video_updated.connect(self.controller.update_video_settings)
        self.settings_panel.export_requested.connect(self._on_export_requested)
        self.settings_panel.export_cancelled.connect(self.controller.cancel_export)

        # Timeline bar
        self.timeline_bar.play_pause_requested.connect(self.player.toggle_play_pause)
        self.timeline_bar.stop_requested.connect(self.player.stop)
        self.timeline_bar.seek_requested.connect(self.player.seek)
        self.timeline_bar.audio_selected.connect(self.controller.set_audio_source)

        # Player
        self.player.position_changed.connect(self.timeline_bar.set_position)
        self.player.error.connect(lambda message: self.video_list_panel.set_status(message, True))
        self.player.playback_state_changed.connect(self.timeline_bar.set_playback_state)

        # Controller
        self.controller.project_changed.connect(self._on_project_changed)
        self.controller.video_selected.connect(self._on_video_selected)
        self.controller.probe_status_updated.connect(self.video_list_panel.set_status)
        self.controller.probe_progress.connect(self._on_probe_progress)
        self.controller.export_progress.connect(self._on_export_progress)
        self.controller.export_succeeded.connect(self._on_export_succeeded)
        self.controller.export_failed.connect(self._on_export_failed)
        self.controller.export_cancelled.connect(self._on_export_cancelled)
        self.controller.dirty_changed.connect(self._update_window_title)

    def _update_window_title(self, is_dirty: bool = False) -> None:
        name = (
            self.controller.current_project_path.name
            if self.controller.current_project_path
            else "새 프로젝트"
        )
        prefix = "* " if is_dirty else ""
        self.setWindowTitle(f"{prefix}{name} - SyncView")

    def _on_probe_progress(self, completed: int, total: int) -> None:
        if total > 0 and completed < total:
            self.status_progress.setVisible(True)
            self.status_progress.setRange(0, total)
            self.status_progress.setValue(completed)
            self.status_bar.showMessage(f"영상 분석 중... ({completed}/{total})")
        else:
            self.status_progress.setVisible(False)

    def _on_export_progress(self, progress: float) -> None:
        self.settings_panel.update_export_progress(progress)
        pct = int(progress * 100)
        self.status_progress.setVisible(True)
        self.status_progress.setRange(0, 100)
        self.status_progress.setValue(pct)
        self.status_bar.showMessage(f"내보내는 중... {pct}%")

    def _on_project_changed(self, project) -> None:
        sel_id = self.controller.selected_video_id
        self.preview_canvas.set_project(project, sel_id)
        self.video_list_panel.set_videos(project.videos, sel_id)
        self.settings_panel.set_project(project, sel_id)
        self.timeline_bar.set_project(project)
        self._update_view_status(self.preview_canvas._solo_video_id)

    def _on_solo_changed(self, video_id: str | None) -> None:
        self._update_view_status(video_id)

    def _update_view_status(self, solo_id: str | None = None) -> None:
        project = self.controller.project
        if solo_id:
            video = next((v for v in project.videos if v.id == solo_id), None)
            name = Path(video.path).name if video else "영상"
            self.lbl_view_status.setText(f"솔로 뷰: {name} (더블클릭하여 복귀)")
        else:
            self.lbl_view_status.setText(f"멀티뷰 그리드 ({len(project.videos)}개 영상)")

    def _on_video_selected(self, video_id: str | None) -> None:
        self.preview_canvas.set_selected_video(video_id)
        self.video_list_panel.set_selected_video(video_id)
        self.settings_panel.set_selected_video(video_id)

    def _on_export_requested(self, target_path: Path, fps: int, encoder: str = "libx264") -> None:
        if target_path.exists():
            res = QMessageBox.question(
                self,
                "파일 덮어쓰기 확인",
                f"'{target_path.name}' 파일이 이미 존재합니다.\n덮어쓰시겠습니까?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if res != QMessageBox.StandardButton.Yes:
                return

        self.settings_panel.set_exporting_state(True)
        self.status_progress.setVisible(True)
        self.status_progress.setValue(0)
        self.status_bar.showMessage(f"내보내는 중: {target_path.name}")
        self.controller.start_export(target_path, fps)

    def _on_export_succeeded(self, output_path: str) -> None:
        self.settings_panel.set_exporting_state(False)
        self.settings_panel.set_export_status("완료", is_error=False)
        self.status_progress.setVisible(False)
        self.status_bar.showMessage(f"완료: {output_path}")
        QMessageBox.information(self, "완료", f"내보내기 완료:\n{output_path}")

    def _on_export_failed(self, error_msg: str) -> None:
        self.settings_panel.set_exporting_state(False)
        self.settings_panel.set_export_status(f"실패: {error_msg}", is_error=True)
        self.status_progress.setVisible(False)
        self.status_bar.showMessage("내보내기 실패")
        QMessageBox.critical(self, "오류", f"내보내기 실패:\n{error_msg}")

    def _on_export_cancelled(self) -> None:
        self.settings_panel.set_exporting_state(False)
        self.settings_panel.set_export_status("취소됨", is_error=False)
        self.status_progress.setVisible(False)
        self.status_bar.showMessage("내보내기 취소됨")

    def _on_new_project(self) -> None:
        if not self._check_discard_changes():
            return
        self.controller.new_project()
        self.status_bar.showMessage("새 프로젝트")

    def _on_open_project(self) -> None:
        if not self._check_discard_changes():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "프로젝트 열기",
            "",
            "SyncView 프로젝트 (*.json);;모든 파일 (*.*)",
        )
        if not path:
            return
        try:
            missing = self.controller.load_project_file(Path(path))
            if missing:
                missing_str = "\n".join(f"- {p}" for p in missing)
                QMessageBox.warning(
                    self,
                    "영상 파일 누락",
                    f"다음 원본 파일이 없습니다:\n{missing_str}",
                )
            self.status_bar.showMessage(f"로드됨: {Path(path).name}")
        except Exception as exc:
            QMessageBox.critical(self, "오류", str(exc))

    def _on_save_project(self) -> bool:
        if self.controller.current_project_path:
            try:
                self.controller.save_project_file(self.controller.current_project_path)
                self.status_bar.showMessage(f"저장됨: {self.controller.current_project_path.name}")
                return True
            except Exception as exc:
                QMessageBox.critical(self, "오류", str(exc))
                return False
        else:
            return self._on_save_project_as()

    def _on_save_project_as(self) -> bool:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "프로젝트 저장",
            "project.json",
            "SyncView 프로젝트 (*.json)",
        )
        if path:
            try:
                self.controller.save_project_file(Path(path))
                self.status_bar.showMessage(f"저장됨: {Path(path).name}")
                return True
            except Exception as exc:
                QMessageBox.critical(self, "오류", str(exc))
                return False
        return False

    def _on_show_help(self, tab_index: int = 0) -> None:
        dlg = HelpDialog(initial_tab=tab_index, parent=self)
        dlg.exec()

    def _on_about(self) -> None:
        QMessageBox.about(
            self,
            "SyncView 정보",
            f"<h3>SyncView v{__version__}</h3>"
            "<p>로컬 동영상 멀티뷰 동기 재생 및 MP4 합성 도구</p>"
            "<p>단축키: <code>F1</code> 키를 눌러 상세 설명서를 확인하세요.</p>"
            "<hr style='border: none; border-top: 1px solid #1E293B;'>"
            "<p><b>오픈소스 라이선스 안내:</b><br>"
            "SyncView는 <b>FFmpeg (GPLv3)</b>, <b>PySide6/Qt 6 (LGPLv3)</b>, "
            "<b>Python (PSFL)</b>, <b>Pretendard (OFL)</b> 등의<br>"
            "오픈소스 소프트웨어를 포함하거나 활용합니다.<br>"
            "자세한 고지는 <b>[도움말] &gt; [오픈소스 라이선스 고지]</b>에서 "
            "확인하실 수 있습니다.</p>",
        )

    def _on_sync_marker(self) -> None:
        sel_id = self.controller.selected_video_id
        if not sel_id:
            return
        video = next((v for v in self.controller.project.videos if v.id == sel_id), None)
        if video:
            video.offset_ms = self.player.common_time
            self.controller.update_video_settings(video.id)
            name = video.label.text or Path(video.path).stem
            self.status_bar.showMessage(f"씽크 설정: {name} (오프셋: {video.offset_ms}ms)")

    def _check_discard_changes(self) -> bool:
        if not self.controller.is_dirty:
            return True
        res = QMessageBox.question(
            self,
            "저장되지 않은 변경사항",
            "현재 프로젝트에 저장되지 않은 변경사항이 있습니다.\n저장하시겠습니까?",
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save,
        )
        if res == QMessageBox.StandardButton.Save:
            return self._on_save_project()
        elif res == QMessageBox.StandardButton.Discard:
            return True
        return False

    def keyPressEvent(self, event: QKeyEvent) -> None:
        key = event.key()
        mod = event.modifiers()

        # Space: Play/Pause toggle
        if key == Qt.Key.Key_Space:
            self.player.toggle_play_pause()
            event.accept()
            return

        # Left / Right: Frame scrub (100ms or 1000ms with Shift)
        step = 1000 if mod & Qt.KeyboardModifier.ShiftModifier else 100
        if key == Qt.Key.Key_Left:
            self.player.seek(max(0, self.player.common_time - step))
            event.accept()
            return
        elif key == Qt.Key.Key_Right:
            self.player.seek(self.player.common_time + step)
            event.accept()
            return

        # Home: Go to start
        if key == Qt.Key.Key_Home:
            self.player.seek(0)
            event.accept()
            return

        # M: Sync Marker at current playhead
        if key == Qt.Key.Key_M:
            self._on_sync_marker()
            event.accept()
            return

        # Delete: Remove selected video
        if key == Qt.Key.Key_Delete:
            if self.controller.selected_video_id:
                self.controller.remove_video(self.controller.selected_video_id)
                event.accept()
                return

        super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:
        if getattr(self, "_closing", False):
            if self.controller.busy:
                event.ignore()
            else:
                event.accept()
            return
        if not self._check_discard_changes():
            event.ignore()
            return
        self._closing = True
        if self.controller.busy:
            event.ignore()
            self.setEnabled(False)
            self.controller.idle.connect(self.close)
            self.controller.shutdown()
        else:
            self.controller.shutdown()
            event.accept()
