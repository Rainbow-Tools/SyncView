import os
import shutil
import subprocess
import sys
from pathlib import Path

from videos_multi_view.i18n import tr


def resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[3]


def executable(name: str) -> str:
    suffix = ".exe" if os.name == "nt" else ""
    bundled = resource_root() / "vendor" / "ffmpeg" / (name + suffix)
    if bundled.is_file():
        return str(bundled)
    if not getattr(sys, "frozen", False):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError(
        tr("{value0} 실행 파일이 없습니다. vendor/ffmpeg를 확인하세요.", value0=name)
    )


def run_tool(name: str, args: list[str], timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        [executable(name), *args],
        capture_output=True,
        timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        check=True,
    )
