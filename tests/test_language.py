"""Language changes must affect presentation, never media or saved project values."""

import ast
from copy import deepcopy
from pathlib import Path
from string import Formatter

import pytest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QDialogButtonBox

from videos_multi_view.application.language import LanguageManager
from videos_multi_view.application.storage import load_project, save_project
from videos_multi_view.core.models import Label, Project, Video
from videos_multi_view.i18n import set_language, tr
from videos_multi_view.media.exporter import ExportJob, _ExportWorker
from videos_multi_view.translations import ENGLISH
from videos_multi_view.ui.help_content import ENGLISH_HELP_SECTIONS, HELP_SECTIONS
from videos_multi_view.ui.help_dialog import HelpDialog
from videos_multi_view.ui.main_window import MainWindow


@pytest.mark.parametrize("locale, expected", [("ko-KR", "ko"), ("en-US", "en"), ("de-DE", "en")])
def test_first_launch_and_persistence(qapp, tmp_path, locale, expected):
    path = str(tmp_path / "language.ini")
    settings = QSettings(path, QSettings.Format.IniFormat)
    manager = LanguageManager(settings=settings, system_language=locale)
    assert manager.current == expected
    manager.select("en")
    reopened = LanguageManager(
        settings=QSettings(path, QSettings.Format.IniFormat), system_language="ko-KR"
    )
    assert reopened.current == "en"
    # An override for this launch must not overwrite the persisted preference.
    reopened.select("ko", persist=False)
    assert settings.value("ui/language") == "en"


def test_unknown_preference_uses_system_fallback(qapp, tmp_path):
    settings = QSettings(str(tmp_path / "invalid.ini"), QSettings.Format.IniFormat)
    settings.setValue("ui/language", {"invalid": True})
    manager = LanguageManager(settings=settings, system_language="ko-KR")
    assert manager.current == "ko"
    with pytest.raises(ValueError, match="Unsupported language"):
        manager.select("fr")
    assert manager.current == "ko"


def test_standard_dialog_buttons_follow_language(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.languages.select("ko")
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel, window)
    cancel = buttons.button(QDialogButtonBox.StandardButton.Cancel)
    assert cancel.text() == "취소"
    window.languages.select("en")
    qtbot.waitUntil(lambda: cancel.text() == "Cancel")


def test_live_language_preserves_project_playback_and_edits(qtbot, tmp_path, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)
    video = Video(
        str((tmp_path / "한글 경로/추가.mp4").resolve()),
        640,
        360,
        10000,
        30,
        has_audio=True,
        label=Label(text="추가 {filename} / 내보내기", position="top-right"),
    )
    project = window.controller.project
    project.videos.append(video)
    project.audio_id = video.id
    project.output.encoder = "h264_qsv"
    project.output.fps = 60
    window.controller.select_video(video.id)
    window.controller._notify_state_changed()
    window.controller.is_dirty = False
    window.player.seek(1500)
    window.player.play()
    window.settings_panel.edit_export_path.setText("C:/출력/추가.mp4")
    original = deepcopy(project)

    def unexpected(*args):
        pytest.fail("Language change reset playback/project state")

    monkeypatch.setattr(window.player, "set_project", unexpected)
    monkeypatch.setattr(window.player, "seek", unexpected)
    window.language_actions["en"].trigger()
    assert window.video_list_panel.btn_add.text() == "Add"
    assert window.settings_panel.btn_export.text() == "Export"
    assert window.timeline_bar.btn_play.text() == "⏸ Pause"
    assert "Multiview grid" in window.lbl_view_status.text()
    assert window.windowTitle() == "New project - SyncView"
    assert window.player.is_playing
    assert window.player.common_time >= 1500
    assert not window.controller.is_dirty
    assert project == original
    assert window.controller.selected_video_id == video.id
    assert window.settings_panel.edit_label_text.text() == video.label.text
    assert window.settings_panel.edit_export_path.text() == "C:/출력/추가.mp4"
    assert window.settings_panel.combo_label_pos.currentData() == "top-right"
    assert window.settings_panel.combo_label_pos.currentText() == "Top right"
    assert window.settings_panel.combo_encoder.currentData() == "h264_qsv"
    assert window.timeline_bar.combo_audio.currentData() == video.id

    path = tmp_path / "project.json"
    save_project(project, path)
    assert load_project(path) == original
    window.language_actions["ko"].trigger()
    assert window.video_list_panel.btn_add.text() == "추가"
    assert window.settings_panel.combo_label_pos.currentText() == "오른쪽 위"
    assert project == original
    window.player.pause()


def test_help_and_export_progress_retranslate(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    dialog = HelpDialog(initial_tab=3, parent=window)
    qtbot.addWidget(dialog)
    window._on_export_progress(0.42)
    window.languages.select("en")
    assert window.status_progress.value() == 42
    assert window.status_bar.currentMessage() == "Exporting... 42%"
    assert dialog.list_topics.currentRow() == 3
    assert "Label macros" in dialog.list_topics.currentItem().text()
    assert "{timecode}" in dialog.browser.toPlainText()
    assert "Source filename" in dialog.browser.toPlainText()
    for index in range(8):
        dialog.list_topics.setCurrentRow(index)
        assert not any(
            "가" <= ch <= "힣"
            for ch in dialog.browser.toPlainText().replace("언어", "").replace("한국어", "")
        )
    window._on_export_cancelled()
    window.languages.select("ko")
    assert window.settings_panel.export_status_label.text() == "취소됨"
    assert window.status_bar.currentMessage() == "내보내기 취소됨"


def test_translated_validation_and_macros():
    set_language("en")
    project = Project()
    project.output.width = 321
    with pytest.raises(ValueError, match="Output dimensions"):
        project.validate()
    assert "{filename}" in tr("이름표 문구 ({filename}, {timecode} 등)")
    assert tr("파일을 찾을 수 없습니다: {value0}", value0="추가 {fps}.mp4") == (
        "File not found: 추가 {fps}.mp4"
    )


def test_cleanup_failure_stays_failure_across_language_change(qtbot, tmp_path):
    job = ExportJob(Project(), tmp_path / "output.mp4")
    worker = _ExportWorker(job.project, job.target_path, job)
    job._worker = worker
    worker.cancel_event.set()
    worker.cleanup_failed = True
    worker.error = "임시 파일 정리 실패: output.tmp.mp4"
    set_language("en")
    signals = []
    job.failed.connect(lambda _: signals.append("failed"))
    job.cancelled.connect(lambda: signals.append("cancelled"))
    job.finished.connect(lambda: signals.append("finished"))
    job._done()
    job._done()
    assert signals == ["failed", "finished"]


def test_catalog_covers_message_calls_and_preserves_placeholders():
    formatter = Formatter()

    def fields(text):
        return {field for _, field, _, _ in formatter.parse(text) if field}

    for source, translated in ENGLISH.items():
        assert fields(source) == fields(translated), source
    for path in Path("src/videos_multi_view").rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            index = {"tr": 0, "bind": 1}.get(node.func.id)
            if index is None or len(node.args) <= index:
                continue
            value = node.args[index]
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                assert value.value in ENGLISH, (path, value.value)
    assert len(ENGLISH_HELP_SECTIONS) == len(HELP_SECTIONS) == 8
