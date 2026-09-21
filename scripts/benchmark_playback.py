"""Measure decoded-frame timestamps against the common clock (Windows/Qt backend)."""

import argparse
import json
import os
import statistics
import time
from pathlib import Path
from uuid import uuid4

from benchmark_render import working_set
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from videos_multi_view.core.models import Project
from videos_multi_view.core.timeline import source_time_ms
from videos_multi_view.media.player import SyncPlayer
from videos_multi_view.media.probe import probe
from videos_multi_view.media.tools import run_tool


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/playback-benchmark.json"))
    parser.add_argument("--counts", type=int, nargs="+", choices=[2, 5, 9], default=[2, 5, 9])
    parser.add_argument("--software-decode", action="store_true")
    args = parser.parse_args()
    if args.software_decode:
        os.environ["QT_FFMPEG_DECODING_HW_DEVICE_TYPES"] = ","
    args.output.parent.mkdir(parents=True, exist_ok=True)
    clip = args.output.parent / f"synthetic-{uuid4().hex}.mp4"
    run_tool(
        "ffmpeg",
        [
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc2=size=320x180:rate=30:duration=15",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(clip),
        ],
    )
    app = QApplication([])
    results = []
    for count in args.counts:
        project = Project(videos=[probe(str(clip)) for _ in range(count)])
        player = SyncPlayer()
        player.set_project(project)
        player.play()
        ready_deadline = time.perf_counter() + 10
        while len(player._frames) < count and time.perf_counter() < ready_deadline:
            QTest.qWait(50)
        player.seek(0)
        if not player.is_playing:
            player.play()
        errors, spreads = [], []
        cpu, wall = time.process_time(), time.perf_counter()
        peak, frames = 0, 0
        try:
            while time.perf_counter() - wall < 5:
                QTest.qWait(50)
                if player.common_time < 1000:
                    continue  # Exclude decoder startup.
                offsets = []
                for video in project.videos:
                    frame = player._sinks[video.id].videoFrame()
                    if frame.isValid() and frame.startTime() >= 0:
                        delta = frame.startTime() / 1000 - source_time_ms(video, player.common_time)
                        errors.append(abs(delta))
                        offsets.append(delta)
                if len(offsets) == count:
                    spreads.append(max(offsets) - min(offsets))
                peak = max(peak, working_set())
            frames = len(player._frames)
            results.append(
                {
                    "videos": count,
                    "frames_loaded": frames,
                    "samples": len(errors),
                    "median_frame_error_ms": round(statistics.median(errors), 1)
                    if errors
                    else None,
                    "p95_frame_error_ms": round(sorted(errors)[int(len(errors) * 0.95)], 1)
                    if errors
                    else None,
                    "max_frame_error_ms": round(max(errors), 1) if errors else None,
                    "max_between_videos_ms": round(max(spreads), 1) if spreads else None,
                    "cpu_percent_one_core": round(
                        100 * (time.process_time() - cpu) / (time.perf_counter() - wall), 1
                    ),
                    "peak_working_set_mib": round(peak / 1024**2, 1),
                }
            )
        finally:
            player.cleanup()
            QTest.qWait(100)
    clip.unlink()
    result = {
        "input": "320x180 H.264 30fps, 15s pattern; same source with independent decoders",
        "method": "Frame PTS vs common clock; 50ms samples, first 1s discarded; no UI painting",
        "hardware_device_types": os.environ.get("QT_FFMPEG_DECODING_HW_DEVICE_TYPES", "auto"),
        "results": results,
    }
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    app.quit()


if __name__ == "__main__":
    main()
