"""Unit tests for timeline calculations and formatting."""

from videos_multi_view.core.models import Project, Video
from videos_multi_view.core.timeline import duration_ms, format_time, is_active, source_time_ms


def test_timeline_duration():
    p = Project()
    assert duration_ms(p) == 0

    v1 = Video(path="v1.mp4", width=640, height=480, duration_ms=5000, fps=30.0, offset_ms=1000)
    v2 = Video(path="v2.mp4", width=640, height=480, duration_ms=8000, fps=30.0, offset_ms=-1000)
    p.videos = [v1, v2]
    # v1 ends at 1000 + 5000 = 6000
    # v2 ends at -1000 + 8000 = 7000
    assert duration_ms(p) == 7000


def test_source_time_ms():
    vid = Video(path="v.mp4", width=640, height=480, duration_ms=5000, fps=25.0, offset_ms=2000)
    # 25 fps -> 1000 / 25 = 40ms frame time. Last frame = 5000 - 40 = 4960ms

    # Before start
    assert source_time_ms(vid, 1000) is None
    assert source_time_ms(vid, 1999) is None

    # At start
    assert source_time_ms(vid, 2000) == 0

    # During playback
    assert source_time_ms(vid, 3500) == 1500

    # Ended clip retains last frame
    assert source_time_ms(vid, 7000) == 4960
    assert source_time_ms(vid, 10000) == 4960


def test_source_time_negative_offset():
    vid = Video(path="v.mp4", width=640, height=480, duration_ms=5000, fps=30.0, offset_ms=-1500)
    # At common_ms=0, source is 1500
    assert source_time_ms(vid, 0) == 1500
    assert source_time_ms(vid, 1000) == 2500


def test_is_active():
    vid = Video(path="v.mp4", width=640, height=480, duration_ms=4000, fps=30.0, offset_ms=1000)
    # Active interval: [1000, 5000)
    assert not is_active(vid, 999)
    assert is_active(vid, 1000)
    assert is_active(vid, 4999)
    assert not is_active(vid, 5000)


def test_format_time():
    assert format_time(0) == "00:00.000"
    assert format_time(500) == "00:00.500"
    assert format_time(61234) == "01:01.234"
    assert format_time(3661050) == "61:01.050"
