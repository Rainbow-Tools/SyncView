"""UI tests using pytest-qt."""

import pytest
from PySide6.QtWidgets import QMessageBox

from videos_multi_view.core.models import Video
from videos_multi_view.ui.main_window import MainWindow


@pytest.fixture(autouse=True)
def no_modal_dialogs(monkeypatch):
    """Prevent QMessageBox modals from blocking test teardown."""
    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Discard
    )


def test_main_window_init(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert "SyncView" in window.windowTitle()
    assert window.video_list_panel.list_widget.count() == 0
    assert window.settings_panel.spin_width.value() == 1920
    assert window.settings_panel.spin_height.value() == 1080
    assert not window.settings_panel.video_group.isEnabled()
    assert window.status_progress is not None


def test_main_window_add_and_select_video(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    v1 = Video(
        path="C:/videos/test1.mp4",
        width=1280,
        height=720,
        duration_ms=5000,
        fps=30.0,
        has_audio=True,
    )
    v2 = Video(
        path="C:/videos/test2.mp4",
        width=1920,
        height=1080,
        duration_ms=8000,
        fps=60.0,
        has_audio=False,
    )

    window.controller.project.videos.extend([v1, v2])
    window.controller.select_video(v1.id)
    window.controller._notify_state_changed()

    # Verify list count
    assert window.video_list_panel.list_widget.count() == 2

    # Verify selected video
    assert window.settings_panel.video_group.isEnabled()
    assert window.settings_panel.edit_label_text.text() == v1.label.text
    assert window.settings_panel.combo_label_font.currentFont().family() != ""

    # Change font
    window.settings_panel.combo_label_font.setCurrentText("Arial")
    assert v1.label.font_family == "Arial"

    # Reorder
    window.video_list_panel.move_video_requested.emit(v1.id, 1)
    assert window.controller.project.videos[0].id == v2.id
    assert window.controller.project.videos[1].id == v1.id

    # Remove
    window.video_list_panel.remove_video_requested.emit(v2.id)
    assert len(window.controller.project.videos) == 1
    assert window.controller.project.videos[0].id == v1.id


def test_main_window_timeline_scrub(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    v = Video(path="C:/videos/test.mp4", width=640, height=480, duration_ms=10000, fps=30.0)
    window.controller.project.videos.append(v)
    window.controller._notify_state_changed()

    assert window.timeline_bar.slider.maximum() == 10000

    # Seek
    window.timeline_bar.slider.setValue(4500)
    window.timeline_bar._on_slider_released()
    assert window.player.common_time == 4500
    assert "00:04.500" in window.timeline_bar.lbl_time.text()


def test_main_window_dirty_and_help(qtbot, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(
        QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Discard
    )

    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.controller.is_dirty

    # Modifying state sets dirty
    v = Video(path="C:/videos/test.mp4", width=640, height=480, duration_ms=1000, fps=30.0)
    window.controller.project.videos.append(v)
    window.controller._notify_state_changed()

    assert window.controller.is_dirty
    assert window.windowTitle().startswith("*")

    # Help dialog test
    from videos_multi_view.ui.help_dialog import HelpDialog

    dlg = HelpDialog(initial_tab=0)
    qtbot.addWidget(dlg)
    assert dlg.list_topics.count() > 0

    window.controller.is_dirty = False


def test_main_window_responsive_toggles_and_help_text(qtbot):
    from videos_multi_view.ui.help_dialog import HELP_SECTIONS

    # 1. Verify manual has no emojis and has correct resolution / filename format
    forbidden_emojis = ["🚀", "⏱️", "📐", "🏷️", "🔍", "🎬", "⌨️"]
    for title, html in HELP_SECTIONS:
        for emoji in forbidden_emojis:
            assert emoji not in title, f"Emoji {emoji} found in title: {title}"
            assert emoji not in html, f"Emoji {emoji} found in content of {title}"

    # Verify resolution example uses 'x' rather than multiplication symbol
    assert "1920x1080" in HELP_SECTIONS[3][1]
    assert "Front_Camera" in HELP_SECTIONS[3][1]
    assert len(HELP_SECTIONS) == 9
    assert "GPLv3" in HELP_SECTIONS[8][1]
    assert "LGPLv3" in HELP_SECTIONS[8][1]

    # 2. Verify UI responsive toggles
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Left panel toggle
    assert window.video_list_panel.isVisible()
    window.btn_toggle_left.setChecked(False)
    assert not window.video_list_panel.isVisible()
    assert not window.act_view_left.isChecked()
    window.act_view_left.setChecked(True)
    assert window.video_list_panel.isVisible()
    assert window.btn_toggle_left.isChecked()

    # Right panel toggle
    assert window.settings_panel.isVisible()
    window.btn_toggle_right.setChecked(False)
    assert not window.settings_panel.isVisible()
    assert not window.act_view_right.isChecked()
    window.act_view_right.setChecked(True)
    assert window.settings_panel.isVisible()
    assert window.btn_toggle_right.isChecked()

    # Maximize toggle
    window.btn_toggle_maximize.setChecked(True)
    assert not window.video_list_panel.isVisible()
    assert not window.settings_panel.isVisible()
    assert window.act_view_max.isChecked()
    window.btn_toggle_maximize.setChecked(False)
    assert window.video_list_panel.isVisible()
    assert window.settings_panel.isVisible()

    # Status label check
    assert "0개 영상" in window.lbl_view_status.text()
    v = Video(path="C:/videos/sample.mp4", width=1280, height=720, duration_ms=2000, fps=30.0)
    window.controller.project.videos.append(v)
    window.controller._notify_state_changed()
    assert "1개 영상" in window.lbl_view_status.text()

    # Solo view status label check
    window.preview_canvas.solo_changed.emit(v.id)
    assert "솔로 뷰: sample.mp4" in window.lbl_view_status.text()
    window.preview_canvas.solo_changed.emit(None)
    assert "1개 영상" in window.lbl_view_status.text()
