"""Explicit opt-in bundle smoke verification; never runs during normal startup."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from videos_multi_view.media.tools import executable

if TYPE_CHECKING:
    from videos_multi_view.ui.main_window import MainWindow


def verify_application(
    app: QApplication, window: MainWindow, project: Path, destination: Path
) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    font = Path("C:/Windows/Fonts/malgun.ttf")
    if font.is_file():
        QFontDatabase.addApplicationFont(str(font))
    report = {"frozen": bool(getattr(sys, "frozen", False)), "python": sys.version.split()[0]}
    try:
        window.controller.load_project_file(project)
    except Exception as exc:
        report["error"] = str(exc)
        (destination / "verification.json").write_text(json.dumps(report), encoding="utf-8")
        QTimer.singleShot(0, lambda: app.exit(1))
        return
    window.resize(1280, 800)
    window.show()
    # Avoid user-facing modal dialogs in this opt-in automation path.
    window.controller.export_succeeded.disconnect(window._on_export_succeeded)
    window.controller.export_failed.disconnect(window._on_export_failed)
    window.controller.export_cancelled.disconnect(window._on_export_cancelled)
    window.controller.is_dirty = False
    timer = QTimer(window)
    timer.setSingleShot(True)
    finished = False

    def finish(error: str = "") -> None:
        nonlocal finished
        if finished:
            return
        finished = True
        timer.stop()
        report["error"] = error
        (destination / "verification.json").write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        window.controller.is_dirty = False
        window.controller.idle.connect(lambda: app.exit(1 if error else 0))
        window.controller.shutdown()

    def export() -> None:
        if finished:
            return
        report["frame_count"] = len(window.player._frames)
        report["video_count"] = len(window.controller.project.videos)
        if report["frame_count"] != report["video_count"]:
            # A cold bundle/decoder start can exceed the initial 1.5 seconds.
            # Keep decoding until frames arrive; the overall timer still bounds the check.
            QTimer.singleShot(100, export)
            return
        window.player.pause()
        report["ffmpeg"] = executable("ffmpeg")
        report["ffprobe"] = executable("ffprobe")
        if report["frozen"]:
            bundle = Path(sys._MEIPASS)
            if not all(Path(report[name]).is_relative_to(bundle) for name in ("ffmpeg", "ffprobe")):
                finish("Media executables are not bundled.")
                return
        window.grab().save(str(destination / "preview.png"))
        window.controller.start_export(destination / "composite.mp4")

    window.controller.export_succeeded.connect(lambda _: finish())
    window.controller.export_failed.connect(finish)
    timer.timeout.connect(lambda: finish("Verification timed out."))
    timer.start(120000)
    window.player.play()
    QTimer.singleShot(1500, export)
