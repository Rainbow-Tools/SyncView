from copy import deepcopy
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, Signal
from PySide6.QtGui import QImage, QPainter
from PySide6.QtMultimedia import QMediaPlayer

from videos_multi_view.application.controller import AppController
from videos_multi_view.application.storage import load_project
from videos_multi_view.core.layout import calculate_layout
from videos_multi_view.core.models import Label, Layout, Output, Project, Video
from videos_multi_view.media.player import SyncPlayer
from videos_multi_view.ui.main_window import MainWindow
from videos_multi_view.ui.renderer import DecorationRenderer, resolve_label_text


class FakeMediaPlayer:
    def __init__(self):
        self.pos = 100
        self.state = QMediaPlayer.PlaybackState.PausedState
        self.seeks = []
        self.starts = 0

    def position(self):
        return self.pos

    def setPosition(self, value):
        self.pos = value
        self.seeks.append(value)

    def playbackState(self):
        return self.state

    def play(self):
        self.starts += 1
        self.state = QMediaPlayer.PlaybackState.PlayingState

    def pause(self):
        self.state = QMediaPlayer.PlaybackState.PausedState


def playback():
    p = SyncPlayer()
    v = Video("test.mp4", 160, 96, 1000, 30)
    p._project = Project(videos=[v])
    p._duration = 1000
    fake = FakeMediaPlayer()
    p._players[v.id] = fake
    return p, v, fake


def test_seek_to_ended_clip_updates_position():
    p, v, fake = playback()
    p.seek(1000)
    assert fake.pos == 966
    p._players.clear()


def test_small_seek_during_play_is_not_ignored():
    p, v, fake = playback()
    p._is_playing = True
    fake.state = QMediaPlayer.PlaybackState.PlayingState
    p.seek(150)
    assert fake.pos == 150
    p._players.clear()


def test_clock_is_anchored(monkeypatch):
    import videos_multi_view.media.player as module

    now = [100.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    p, v, fake = playback()
    p.play()
    for i in range(1, 11):
        now[0] = 100 + i * 0.0254
        p._on_clock_tick()
    assert p.common_time == 254  # Per-tick rounding would give 250.
    p.pause()
    p._players.clear()


def test_automatic_corrections_allow_decoder_to_finish(monkeypatch):
    import videos_multi_view.media.player as module

    now = [100.0]
    monkeypatch.setattr(module.time, "monotonic", lambda: now[0])
    p, v, fake = playback()
    p._is_playing = True
    p._common_time = 500
    p._sync_all_players(False)
    fake.pos = 0  # Decoder still reports the old position while seeking.
    for tick in range(1, 9):
        now[0] = 100 + tick * 0.025
        p._sync_all_players(False)
    assert fake.seeks == [500]
    now[0] = 100.3
    p._sync_all_players(False)
    assert fake.seeks == [500, 500]
    p.seek(600)  # An explicit user seek must remain immediate.
    assert fake.seeks[-1] == 600
    p.pause()
    p._players.clear()


def test_design_does_not_seek_or_restart(monkeypatch):
    p, v, fake = playback()
    project = p._project
    p._sources[v.id] = v.path
    p.set_project(project)
    p.play()
    fake.seeks.clear()
    before = fake.starts
    v.label.text = "changed"
    project.layout.background = "#ff0000"
    p.set_project(project)
    assert fake.seeks == []
    assert fake.starts == before
    assert p.is_playing
    p.pause()
    p._players.clear()


def test_output_settings_persist_and_validate(qtbot, monkeypatch, tmp_path):
    from PySide6.QtWidgets import QMessageBox

    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Discard)
    w = MainWindow()
    qtbot.addWidget(w)
    w.settings_panel.combo_fps.setCurrentText("60")
    w.settings_panel.combo_encoder.setCurrentIndex(1)
    assert w.controller.is_dirty
    w.controller.save_project_file(tmp_path / "p.json")
    loaded = load_project(tmp_path / "p.json")
    assert loaded.output.fps == 60
    assert loaded.output.encoder == "h264_nvenc"
    w.controller.is_dirty = False


class FakeProbe(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()
    jobs = []

    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self.cancelled = False
        self.jobs.append(self)

    def start(self):
        pass

    def cancel(self):
        self.cancelled = True  # Finish later to emulate in-flight work.

    def complete(self):
        self.succeeded.emit(Video(self.path, 160, 96, 1000, 30, display_aspect=5 / 3))
        self.finished.emit()


@pytest.fixture
def controller(monkeypatch):
    import videos_multi_view.application.controller as module

    FakeProbe.jobs = []
    monkeypatch.setattr(module, "ProbeJob", FakeProbe)
    player = SyncPlayer()
    monkeypatch.setattr(player, "set_project", lambda project: None)
    ctl = AppController(player)
    yield ctl
    ctl.shutdown()
    ctl.deleteLater()
    player.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    FakeProbe.jobs.clear()


def test_old_probe_cannot_modify_new_project(controller, tmp_path):
    path = tmp_path / "a.mp4"
    path.touch()
    controller.add_video_files([str(path)])
    old = FakeProbe.jobs[0]
    controller.new_project()
    old.complete()
    assert old.cancelled
    assert controller.project.videos == []
    assert not controller._active_probe_jobs


def test_probe_order_dedup_and_concurrency(controller, tmp_path):
    paths = [tmp_path / f"{i}.mp4" for i in range(3)]
    for path in paths:
        path.touch()
    controller.add_video_files([str(p) for p in paths] + [str(paths[0])])
    assert len(FakeProbe.jobs) == 2
    FakeProbe.jobs[1].complete()
    assert controller.project.videos == []
    assert len(FakeProbe.jobs) == 3
    FakeProbe.jobs[2].complete()
    FakeProbe.jobs[0].complete()
    assert [Path(v.path).name for v in controller.project.videos] == ["0.mp4", "1.mp4", "2.mp4"]
    assert not controller._pending_paths


def test_relink_preserves_settings(controller, tmp_path):
    v = Video("missing.mp4", 64, 64, 3000, 24, offset_ms=100, label=Label(text="keep"))
    controller.project.videos.append(v)
    path = tmp_path / "new.mp4"
    path.touch()
    controller.relink_video(v.id, str(path))
    FakeProbe.jobs[0].complete()
    replacement = controller.project.videos[0]
    assert (replacement.id, replacement.label.text, replacement.offset_ms) == (v.id, "keep", 100)
    assert replacement.path == str(path)
    assert replacement.width == 160


def test_invalid_layout_keeps_previous_state(controller):
    controller.project.videos.append(Video("x.mp4", 160, 96, 1000, 30))
    original = deepcopy(controller.project.layout)
    controller.apply_settings("layout", (Layout(margin=9000), Output()))
    assert controller.project.layout == original


def test_long_label_stays_in_cell(qapp):
    v = Video("x.mp4", 160, 96, 1000, 30, label=Label(text="아주 긴 이름표 " * 30, size=20))
    p = Project(videos=[v], layout=Layout(margin=10), output=Output(width=320, height=240))
    cells = calculate_layout(p)
    renderer = DecorationRenderer(p, cells)
    image = renderer.image()
    bounds = cells[0].bounds
    for y in range(image.height()):
        for x in range(image.width()):
            if not (
                bounds.x <= x < bounds.x + bounds.width and bounds.y <= y < bounds.y + bounds.height
            ):
                assert image.pixelColor(x, y).alpha() == 0


def test_static_decoration_cache_and_time_clamp(qapp):
    v = Video("x.mp4", 160, 96, 1000, 30, label=Label(text="Static"))
    p = Project(videos=[v])
    renderer = DecorationRenderer(p, calculate_layout(p))
    image = QImage(1920, 1080, QImage.Format.Format_RGB32)
    painter = QPainter(image)
    renderer.draw(painter, 0)
    cached = renderer.labels[0].image.cacheKey()
    renderer.draw(painter, 500)
    assert renderer.labels[0].image.cacheKey() == cached
    painter.end()
    assert resolve_label_text("{timecode}", v, 3000) == "00:00.966"
