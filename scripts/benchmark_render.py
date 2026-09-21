"""Compare paint paths using identical synthetic frames, output size and fonts."""

import argparse
import ctypes
import importlib.util
import json
import platform
import statistics
import time
from pathlib import Path

from PySide6.QtCore import QRectF
from PySide6.QtGui import QColor, QFontDatabase, QImage, QPainter
from PySide6.QtWidgets import QApplication

from videos_multi_view.core.layout import calculate_layout
from videos_multi_view.core.models import Label, Project, Video
from videos_multi_view.ui.renderer import DecorationRenderer


def working_set() -> int:
    if platform.system() != "Windows":
        return 0

    class Counters(ctypes.Structure):
        _fields_ = [("cb", ctypes.c_ulong), ("faults", ctypes.c_ulong)] + [
            (name, ctypes.c_size_t)
            for name in (
                "peak",
                "working",
                "paged_peak",
                "paged",
                "nonpaged_peak",
                "nonpaged",
                "page_peak",
                "page",
            )
        ]

    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    ctypes.windll.kernel32.GetCurrentProcess.restype = ctypes.c_void_p
    query = ctypes.windll.psapi.GetProcessMemoryInfo
    query.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters), ctypes.c_ulong]
    query.restype = ctypes.c_int
    if not query(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise ctypes.WinError()
    return counters.working


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--output", type=Path, default=Path("artifacts/render-benchmark.json"))
    args = parser.parse_args()
    app = QApplication([])
    font = Path("C:/Windows/Fonts/malgun.ttf")
    if font.is_file():
        QFontDatabase.addApplicationFont(str(font))
    old = None
    if args.baseline:
        spec = importlib.util.spec_from_file_location("baseline_renderer", args.baseline)
        old = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(old)
    result = {
        "os": platform.platform(),
        "python": platform.python_version(),
        "measurement": "1920x1080; cached synthetic frames, not decoding; 600 samples per path",
        "memory": "sampled process working set; both renderers coexist, not isolated allocations",
        "runs": [],
    }
    frame = QImage(320, 180, QImage.Format.Format_RGB32)
    frame.fill(QColor("#39495d"))
    for count in (2, 5, 9):
        project = Project(
            videos=[
                Video(
                    f"camera{i}.mp4",
                    320,
                    180,
                    10000,
                    30,
                    display_aspect=16 / 9,
                    label=Label(text=f"Camera {i + 1}", font_family="Malgun Gothic"),
                )
                for i in range(count)
            ]
        )
        project.layout.border_visible = True
        cells = calculate_layout(project)
        renderer = DecorationRenderer(project, cells)
        canvas = QImage(1920, 1080, QImage.Format.Format_RGB32)
        painter = QPainter(canvas)
        painter.setRenderHints(
            QPainter.RenderHint.Antialiasing | QPainter.RenderHint.SmoothPixmapTransform
        )
        modes = ["before", "after"] if old else ["after"]
        for scope in ("full_paint", "decorations"):
            samples = {mode: [] for mode in modes}
            cpu = {mode: 0.0 for mode in modes}
            peak = {mode: 0 for mode in modes}
            # Alternate order to reduce thermal/scheduling bias. First two batches warm caches.
            for batch in range(12):
                for mode in modes if batch % 2 else list(reversed(modes)):
                    cpu_start = time.process_time()
                    for _ in range(60):
                        started = time.perf_counter()
                        if scope == "full_paint":
                            painter.fillRect(canvas.rect(), QColor(project.layout.background))
                            for cell in cells:
                                r = cell.image
                                painter.drawImage(QRectF(r.x, r.y, r.width, r.height), frame)
                        if mode == "before":
                            old.render_decorations(painter, project, cells)
                        else:
                            renderer.draw(painter)
                        elapsed = (time.perf_counter() - started) * 1000
                        if batch >= 2:
                            samples[mode].append(elapsed)
                    if batch >= 2:
                        cpu[mode] += time.process_time() - cpu_start
                        peak[mode] = max(peak[mode], working_set())
            for mode in modes:
                result["runs"].append(
                    {
                        "videos": count,
                        "scope": scope,
                        "mode": mode,
                        "median_ms": round(statistics.median(samples[mode]), 3),
                        "p95_ms": round(sorted(samples[mode])[int(len(samples[mode]) * 0.95)], 3),
                        "cpu_ms_per_frame": round(cpu[mode] * 1000 / len(samples[mode]), 3),
                        "sampled_working_set_mib": round(peak[mode] / 1024**2, 1),
                    }
                )
        painter.end()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    app.quit()


if __name__ == "__main__":
    main()
