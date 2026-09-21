# Build from the repository root with: python -m PyInstaller VideoMultiView.spec
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files

root = Path(SPECPATH)
media = root / "vendor" / "ffmpeg"
for filename in ("ffmpeg.exe", "ffprobe.exe"):
    if not (media / filename).is_file():
        raise SystemExit("Run scripts/setup_ffmpeg.ps1 before building.")

a = Analysis(
    [str(root / "src/videos_multi_view/__main__.py")],
    pathex=[str(root / "src")],
    binaries=[(str(media / name), "vendor/ffmpeg") for name in ("ffmpeg.exe", "ffprobe.exe")],
    datas=collect_data_files("videos_multi_view")
    + [
        (str(media / "README.md"), "vendor/ffmpeg"),
        (str(media / "LICENSE"), "vendor/ffmpeg"),
    ],
    hiddenimports=["PySide6.QtMultimedia"],
    excludes=["pytest", "ruff"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SyncView",
    console=False,
    upx=False,
    icon=str(root / "src/videos_multi_view/assets/logo.ico"),
)
