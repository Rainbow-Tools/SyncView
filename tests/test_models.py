"""Unit tests for core data models and validation."""

import pytest

from videos_multi_view.core.models import Label, Layout, Output, Project, Video


def test_default_models():
    proj = Project()
    assert proj.version == 1
    assert proj.output.width == 1920
    assert proj.output.height == 1080
    assert proj.output.fps == 30
    assert proj.output.encoder == "libx264"
    assert proj.layout.columns == 0
    assert proj.layout.gap == 8
    assert proj.layout.margin == 16
    assert proj.layout.background == "#15191f"
    assert not proj.layout.border_visible
    assert proj.layout.border_width == 2
    assert proj.layout.border_color == "#ffffff"
    assert proj.audio_id is None
    assert proj.videos == []
    proj.validate()


def test_video_model():
    vid = Video(
        path="C:/videos/sample.mp4",
        width=1920,
        height=1080,
        duration_ms=5000,
        fps=30.0,
        has_audio=True,
    )
    assert vid.display_aspect == 1.0
    assert vid.offset_ms == 0
    assert vid.label.text == ""
    assert vid.label.position == "bottom-left"
    assert vid.label.font_family == ""


def test_project_validation_output():
    # Odd width or height
    p1 = Project(output=Output(width=1921, height=1080, fps=30))
    with pytest.raises(ValueError, match="짝수"):
        p1.validate()

    # Invalid FPS
    p2 = Project(output=Output(width=1920, height=1080, fps=25))
    with pytest.raises(ValueError, match="출력 FPS"):
        p2.validate()

    # Invalid encoder
    p_enc = Project(output=Output(encoder="invalid_enc"))
    with pytest.raises(ValueError, match="인코더"):
        p_enc.validate()

    # Version mismatch
    p3 = Project(version=2)
    with pytest.raises(ValueError, match="버전"):
        p3.validate()


def test_project_validation_layout():
    # Negative values
    p1 = Project(layout=Layout(columns=-1))
    with pytest.raises(ValueError, match="음수"):
        p1.validate()

    # Invalid border width
    p2 = Project(layout=Layout(border_width=101))
    with pytest.raises(ValueError, match="테두리 두께"):
        p2.validate()

    # Invalid color hex
    p3 = Project(layout=Layout(background="invalid"))
    with pytest.raises(ValueError, match="색상"):
        p3.validate()


def test_project_validation_videos():
    v1 = Video(path="v1.mp4", width=640, height=480, duration_ms=1000, fps=30.0, id="v1")
    v2 = Video(
        path="v2.mp4", width=640, height=480, duration_ms=1000, fps=30.0, id="v1"
    )  # duplicate id

    p = Project(videos=[v1, v2])
    with pytest.raises(ValueError, match="중복"):
        p.validate()

    # Offset exceeds negative duration
    v3 = Video(path="v3.mp4", width=640, height=480, duration_ms=1000, fps=30.0, offset_ms=-1000)
    p3 = Project(videos=[v3])
    with pytest.raises(ValueError, match="건너뜁니다"):
        p3.validate()

    # Invalid audio_id
    v4 = Video(path="v4.mp4", width=640, height=480, duration_ms=1000, fps=30.0, id="v4")
    p4 = Project(videos=[v4], audio_id="unknown_id")
    with pytest.raises(ValueError, match="오디오"):
        p4.validate()

    # Invalid label position
    v5 = Video(
        path="v5.mp4",
        width=640,
        height=480,
        duration_ms=1000,
        fps=30.0,
        label=Label(position="center"),
    )
    p5 = Project(videos=[v5])
    with pytest.raises(ValueError, match="이름표 위치"):
        p5.validate()

    # Invalid label font_family
    v6 = Video(
        path="v6.mp4",
        width=640,
        height=480,
        duration_ms=1000,
        fps=30.0,
        label=Label(font_family=123),  # type: ignore
    )
    p6 = Project(videos=[v6])
    with pytest.raises(ValueError, match="이름표 글꼴"):
        p6.validate()
