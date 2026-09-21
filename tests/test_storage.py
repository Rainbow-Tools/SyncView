"""Unit tests for project serialization and deserialization."""

from pathlib import Path

import pytest

from videos_multi_view.application.storage import load_project, save_project
from videos_multi_view.core.models import Label, Layout, Output, Project, Video


def test_save_and_load_project(tmp_path: Path):
    video_file = tmp_path / "video1.mp4"
    video_file.write_bytes(b"dummy")

    proj = Project(
        videos=[
            Video(
                path=str(video_file.resolve()),
                width=1920,
                height=1080,
                duration_ms=5000,
                fps=30.0,
                has_audio=True,
                offset_ms=1000,
                label=Label(text="테스트 영상", position="top-right", size=32),
            )
        ],
        layout=Layout(columns=1, gap=12, border_visible=True, border_width=4),
        output=Output(width=1280, height=720, fps=60),
    )

    proj_file = tmp_path / "subdir" / "proj.json"
    proj_file.parent.mkdir()

    save_project(proj, proj_file)
    assert proj_file.is_file()

    loaded = load_project(proj_file)
    assert loaded.version == 1
    assert loaded.output.width == 1280
    assert loaded.output.height == 720
    assert loaded.output.fps == 60
    assert loaded.layout.columns == 1
    assert loaded.layout.border_visible
    assert loaded.layout.border_width == 4
    assert len(loaded.videos) == 1

    lv = loaded.videos[0]
    assert Path(lv.path).resolve() == video_file.resolve()
    assert lv.offset_ms == 1000
    assert lv.label.text == "테스트 영상"
    assert lv.label.position == "top-right"
    assert lv.label.size == 32


def test_save_cannot_overwrite_source_video(tmp_path: Path):
    video_file = tmp_path / "video1.mp4"
    video_file.write_bytes(b"dummy")

    proj = Project(
        videos=[
            Video(
                path=str(video_file.resolve()),
                width=640,
                height=480,
                duration_ms=1000,
                fps=30.0,
            )
        ]
    )

    with pytest.raises(ValueError, match="원본 영상을 프로젝트 파일로 덮어쓸 수 없습니다"):
        save_project(proj, video_file)


def test_load_invalid_version(tmp_path: Path):
    proj_file = tmp_path / "bad_version.json"
    proj_file.write_text('{"version": 99, "videos": [], "layout": {}, "output": {}}')
    with pytest.raises(ValueError, match="지원하지 않는 프로젝트 버전"):
        load_project(proj_file)


def test_load_malformed_json(tmp_path: Path):
    proj_file = tmp_path / "malformed.json"
    proj_file.write_text('{"broken json": ')
    with pytest.raises(ValueError):
        load_project(proj_file)
