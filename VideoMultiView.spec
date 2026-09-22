# Build from the repository root with: python -m PyInstaller VideoMultiView.spec
import os
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files
from PySide6.QtCore import QLibraryInfo

root = Path(SPECPATH)
media = root / "vendor" / "ffmpeg"
mode = os.environ.get("SYNCVIEW_BUILD_MODE", "onefile")
if mode not in ("onefile", "onedir"):
    raise SystemExit("SYNCVIEW_BUILD_MODE must be onefile or onedir.")
qt_translation = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)) / "qtbase_ko.qm"
if not qt_translation.is_file():
    raise SystemExit("The PySide6 Korean Qt translation is missing. Reinstall the pinned dependencies.")
for filename in ("ffmpeg.exe", "ffprobe.exe"):
    if not (media / filename).is_file():
        raise SystemExit("Run scripts/setup_ffmpeg.ps1 before building.")

a = Analysis(
    [str(root / "src/videos_multi_view/__main__.py")],
    pathex=[str(root / "src")],
    binaries=[(str(media / name), "vendor/ffmpeg") for name in ("ffmpeg.exe", "ffprobe.exe")],
    datas=collect_data_files("videos_multi_view")
    + [
        (str(root / "LICENSE"), "."),
        (str(root / "THIRD_PARTY_NOTICES.md"), "."),
        (str(root / "licenses"), "licenses"),
        (str(root / "docs" / "LICENSING.md"), "docs"),
        (str(qt_translation), "PySide6/translations"),
        (str(media / "README.md"), "vendor/ffmpeg"),
        (str(media / "LICENSE"), "vendor/ffmpeg"),
    ],
    hiddenimports=["PySide6.QtMultimedia"],
    excludes=["pytest", "ruff"],
)
# Qt's default plugin collection includes this GPL-only module. This Widgets
# application does not use it; remove both the plugin and its library.
a.binaries = [entry for entry in a.binaries if "virtualkeyboard" not in entry[0].lower()]
pyz = PYZ(a.pure)
options = dict(
    name="SyncView",
    console=False,
    upx=False,
    icon=str(root / "src/videos_multi_view/assets/logo.ico"),
)
if mode == "onedir":
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, **options)
    collect = COLLECT(exe, a.binaries, a.datas, name="SyncView", upx=False)
else:
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], **options)
