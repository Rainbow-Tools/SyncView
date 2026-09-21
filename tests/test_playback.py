"""Exercise real Qt decoders as well as the controller's fake-player regressions."""

from copy import deepcopy
from pathlib import Path

import pytest

from videos_multi_view.core.models import Project
from videos_multi_view.media.player import SyncPlayer
from videos_multi_view.media.probe import probe

pytestmark = pytest.mark.integration


def color(player, video):
    image = player.get_frame(video, player.common_time)
    return image.pixelColor(image.width() // 2, image.height() // 2) if image else None


def test_real_seek_before_start_and_past_end(qtbot, clip):
    video = probe(str(clip))
    video.offset_ms = 500
    player = SyncPlayer()
    try:
        player.set_project(Project(videos=[video]))
        player.play()
        qtbot.waitUntil(lambda: video.id in player._frames, timeout=8000)
        player.pause()
        player.seek(800)
        qtbot.waitUntil(
            lambda: color(player, video) is not None and color(player, video).red() > 200
        )
        player.seek(2500)
        qtbot.waitUntil(lambda: color(player, video).blue() > 200, timeout=5000)
        player.seek(0)
        assert player.get_frame(video, 0) is None
    finally:
        player.cleanup()


def test_real_relink_replaces_decoder(qtbot, media_factory):
    video = probe(str(media_factory()))
    replacement_path = media_factory(name="replacement")
    player = SyncPlayer()
    try:
        project = Project(videos=[video])
        player.set_project(project)
        old = player._players[video.id]
        player.play()
        qtbot.waitUntil(lambda: video.id in player._frames, timeout=8000)
        updated = deepcopy(project)
        updated.videos[0].path = str(replacement_path)
        player.set_project(updated)
        assert player._players[video.id] is not old
        assert Path(player._players[video.id].source().toLocalFile()) == replacement_path
        qtbot.waitUntil(lambda: video.id in player._frames, timeout=8000)
    finally:
        player.cleanup()


def test_paused_project_loads_preview_frames(qtbot, clip):
    videos = [probe(str(clip)) for _ in range(2)]
    player = SyncPlayer()
    try:
        player.set_project(Project(videos=videos))
        qtbot.waitUntil(lambda: len(player._frames) == 2, timeout=8000)
        assert not player.is_playing
        assert player.common_time == 0
    finally:
        player.cleanup()
