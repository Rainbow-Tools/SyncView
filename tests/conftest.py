from pathlib import Path

import pytest
from PySide6.QtGui import QFontDatabase

from videos_multi_view.media.tools import executable, run_tool


def pytest_addoption(parser):
    parser.addoption("--local-assets", action="store_true", help="Verify private local videos too")


@pytest.fixture(scope="session", autouse=True)
def test_fonts(qapp):
    # Qt's offscreen plugin does not discover Windows system fonts automatically.
    path = Path("C:/Windows/Fonts/malgun.ttf")
    if path.is_file():
        QFontDatabase.addApplicationFont(str(path))


@pytest.fixture
def media_factory(tmp_path):
    """Generate small, redistributable test inputs without private test_assets."""
    try:
        executable("ffmpeg")
    except FileNotFoundError:
        pytest.skip("FFmpeg integration tools are not installed")
    serial = 0

    def make(name="테스트 영상", fps=30, size="160x96", audio=False, duration=2):
        nonlocal serial
        serial += 1
        target = tmp_path / f"{name} {serial}.mp4"
        args = [
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            f"color=red:s={size}:r={fps}:d=1",
            "-f",
            "lavfi",
            "-i",
            f"color=blue:s={size}:r={fps}:d={max(1, duration - 1)}",
        ]
        if audio:
            args += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={duration}"]
        args += [
            "-filter_complex",
            "[0:v][1:v]concat=n=2:v=1:a=0[v]",
            "-map",
            "[v]",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
        ]
        if audio:
            args += ["-map", "2:a", "-c:a", "aac"]
        args += ["-t", str(duration), str(target)]
        run_tool("ffmpeg", args)
        return target

    return make


@pytest.fixture
def clip(media_factory) -> Path:
    return media_factory(audio=True)
