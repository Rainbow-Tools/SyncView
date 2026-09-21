"""Verify encoded frames and lifecycle, not just command strings."""

from array import array
from statistics import mean

import pytest
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage

from videos_multi_view.core.models import Layout, Output, Project
from videos_multi_view.media.exporter import ExportJob
from videos_multi_view.media.probe import probe
from videos_multi_view.media.tools import run_tool

pytestmark = pytest.mark.integration


def export(qtbot, project, path):
    job = ExportJob(project, path)
    errors = []
    job.failed.connect(errors.append)
    try:
        with qtbot.waitSignal(job.finished, timeout=30000):
            job.start()
    finally:
        if not job._settled:
            with qtbot.waitSignal(job.finished, timeout=5000):
                job.cancel()
    assert not errors, errors
    assert path.is_file()
    return job


def rgb(path, at, x=80, y=48, width=160):
    result = run_tool(
        "ffmpeg",
        [
            "-v",
            "error",
            "-ss",
            str(at),
            "-i",
            str(path),
            "-frames:v",
            "1",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "pipe:1",
        ],
    )
    index = (y * width + x) * 3
    return tuple(result.stdout[index : index + 3])


def test_export_job_success(qtbot, tmp_path, media_factory):
    v1 = probe(str(media_factory(audio=True, fps=24)))
    v2 = probe(str(media_factory(size="96x160", fps=30)))
    target = tmp_path / "export_output.mp4"
    project = Project(
        videos=[v1, v2],
        layout=Layout(border_visible=True, border_width=4),
        output=Output(width=320, height=240, fps=30),
        audio_id=v1.id,
    )
    export(qtbot, project, target)
    result = probe(str(target))
    assert (result.width, result.height, result.fps) == (320, 240, 30)
    assert abs(result.duration_ms - 2000) <= 34
    assert result.has_audio


def test_export_job_cancel(qtbot, tmp_path, clip):
    target = tmp_path / "existing.mp4"
    target.write_bytes(b"original output")
    v = probe(str(clip))
    v.label.text = "{timecode}"
    v.offset_ms = 60000
    job = ExportJob(Project(videos=[v]), target)
    counts = []
    job.finished.connect(lambda: counts.append("finished"))
    with qtbot.waitSignal(job.cancelled, timeout=10000):
        job.start()
        QTimer.singleShot(100, job.cancel)
    assert counts == ["finished"]
    assert target.read_bytes() == b"original output"
    assert not list(tmp_path.glob(".*_dec.png"))
    assert not list(tmp_path.glob(".*.tmp.mp4"))


def test_export_target_same_as_input(qapp, clip):
    v = probe(str(clip))
    job = ExportJob(Project(videos=[v]), clip)
    messages = []
    job.failed.connect(messages.append)
    job.start()
    assert len(messages) == 1
    assert "원본 영상" in messages[0]


@pytest.mark.parametrize(
    "offset,at,expected",
    [
        (1000, 0.5, "black"),
        (1000, 1.2, "red"),
        (1000, 2.2, "blue"),
        (-1000, 0.2, "blue"),
        (0, 0.2, "red"),
        (1000, 1 + 29 / 30, "red"),
        (1000, 2 + 1 / 30, "blue"),
        (-1999, 0, "blue"),
    ],
)
def test_actual_offset_frames(qtbot, tmp_path, clip, offset, at, expected):
    v = probe(str(clip))
    v.offset_ms, v.label.visible = offset, False
    p = Project(
        videos=[v],
        layout=Layout(gap=0, margin=0, background="#000000"),
        output=Output(width=160, height=96),
    )
    target = tmp_path / "offset.mp4"
    export(qtbot, p, target)
    red, green, blue = rgb(target, at)
    if expected == "red":
        assert red > 220 and blue < 20
    elif expected == "blue":
        assert blue > 220 and red < 20
    else:
        assert max(red, green, blue) < 10


def test_dynamic_label_matches_shared_renderer(qtbot, tmp_path, clip):
    from PySide6.QtGui import QColor, QPainter

    from videos_multi_view.core.layout import calculate_layout
    from videos_multi_view.ui.renderer import DecorationRenderer

    v = probe(str(clip))
    v.label.text, v.label.size = "{timecode}", 12
    p = Project(videos=[v], layout=Layout(gap=0, margin=0), output=Output(width=160, height=96))
    target = tmp_path / "dynamic.mp4"
    export(qtbot, p, target)
    patches = []
    for at in (0.2, 0.7):
        image_path = tmp_path / f"{at}.png"
        run_tool(
            "ffmpeg",
            ["-v", "error", "-ss", str(at), "-i", str(target), "-frames:v", "1", str(image_path)],
        )
        actual = QImage(str(image_path))
        expected = QImage(160, 96, QImage.Format.Format_RGB32)
        expected.fill(QColor("red"))
        painter = QPainter(expected)
        DecorationRenderer(p, calculate_layout(p)).draw(painter, round(at * 1000))
        painter.end()
        differences = [
            abs(actual.pixelColor(x, y).red() - expected.pixelColor(x, y).red())
            for y in range(50, 90)
            for x in range(8, 145)
        ]
        assert mean(differences) < 12
        patches.append(bytes(actual.constBits()))
    assert patches[0] != patches[1]


@pytest.mark.parametrize("offset", [500, -500])
def test_last_frame_and_audio_padding(qtbot, tmp_path, media_factory, offset):
    short = probe(str(media_factory(audio=True)))
    long = probe(str(media_factory(duration=3)))
    short.offset_ms = offset
    short.label.visible = long.label.visible = False
    p = Project(
        videos=[short, long],
        audio_id=short.id,
        layout=Layout(gap=0, margin=0),
        output=Output(width=320, height=96),
    )
    target = tmp_path / "hold.mp4"
    export(qtbot, p, target)
    assert rgb(target, 2.8, width=320)[2] > 220
    raw = run_tool(
        "ffmpeg",
        [
            "-v",
            "error",
            "-i",
            str(target),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "8000",
            "-f",
            "f32le",
            "pipe:1",
        ],
    ).stdout
    samples = array("f", raw)

    def energy(start, end):
        return mean(s * s for s in samples[int(start * 8000) : int(end * 8000)])

    if offset > 0:
        assert energy(0.05, 0.35) < 0.00001
    else:
        assert energy(0.05, 0.35) > 0.0001
        assert energy(1.7, 1.9) < 0.00001
    assert energy(0.7, 1.0) > 0.0001
    assert energy(2.7, 2.9) < 0.00001


def test_export_failure_preserves_existing(qtbot, tmp_path, clip):
    v = probe(str(clip))
    v.path = str(tmp_path / "missing.mp4")
    target = tmp_path / "keep.mp4"
    target.write_bytes(b"keep")
    job = ExportJob(Project(videos=[v]), target)
    with qtbot.waitSignal(job.failed, timeout=5000):
        job.start()
    assert target.read_bytes() == b"keep"


def test_output_replace_failure(qtbot, tmp_path, clip, monkeypatch):
    import videos_multi_view.media.exporter as module

    def fail(*args):
        raise PermissionError("test locked destination")

    monkeypatch.setattr(module.os, "replace", fail)
    v = probe(str(clip))
    target = tmp_path / "locked.mp4"
    target.write_bytes(b"keep")
    job = ExportJob(Project(videos=[v], output=Output(width=160, height=96)), target)
    with qtbot.waitSignal(job.failed, timeout=10000) as result:
        job.start()
    assert "locked destination" in result.args[0]
    assert target.read_bytes() == b"keep"
    assert not list(tmp_path.glob(".*.tmp.mp4"))


@pytest.mark.parametrize("count", [1, 3, 5, 9])
def test_grid_export(qtbot, tmp_path, clip, count):
    from videos_multi_view.core.layout import calculate_layout

    videos = [probe(str(clip)) for _ in range(count)]
    for video in videos:
        video.label.visible = False
    project = Project(videos=videos, output=Output(width=480, height=270))
    target = tmp_path / "grid.mp4"
    export(qtbot, project, target)
    for cell in calculate_layout(project):
        bounds = cell.image
        red, _, blue = rgb(
            target, 0.2, bounds.x + bounds.width // 2, bounds.y + bounds.height // 2, 480
        )
        assert red > 220 and blue < 20


def test_rotation_is_applied_to_encoded_frames(qtbot, tmp_path, clip):
    patterned, rotated, target = [tmp_path / name for name in ("pattern.mp4", "rot.mp4", "out.mp4")]
    run_tool(
        "ffmpeg",
        [
            "-v",
            "error",
            "-i",
            str(clip),
            "-an",
            "-vf",
            "drawbox=x=80:y=0:w=80:h=96:color=blue:t=fill",
            str(patterned),
        ],
    )
    run_tool(
        "ffmpeg",
        [
            "-v",
            "error",
            "-display_rotation:v:0",
            "90",
            "-i",
            str(patterned),
            "-c",
            "copy",
            str(rotated),
        ],
    )
    video = probe(str(rotated))
    assert video.display_aspect == pytest.approx(96 / 160)
    video.label.visible = False
    project = Project(videos=[video], layout=Layout(margin=0), output=Output(width=160, height=160))
    export(qtbot, project, target)
    top, bottom = rgb(target, 0.2, 80, 40), rgb(target, 0.2, 80, 120)
    assert {
        "red" if color[0] > 200 else "blue" if color[2] > 200 else "other"
        for color in (top, bottom)
    } == {"red", "blue"}
