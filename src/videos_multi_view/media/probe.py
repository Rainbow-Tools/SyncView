"""Metadata parsing and a cancellable asynchronous ffprobe adapter."""

import json
from fractions import Fraction
from math import isfinite
from pathlib import Path

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

from videos_multi_view.core.models import Label, Video

from .tools import executable, run_tool

PROBE_ARGS = ["-v", "error", "-show_streams", "-show_format", "-of", "json"]


def _number(value: object) -> float:
    try:
        number = float(Fraction(str(value)))
        return number if isfinite(number) and number > 0 else 0
    except (ValueError, ZeroDivisionError, OverflowError):
        return 0


def parse_probe(path: str, data: dict) -> Video:
    streams = data.get("streams", [])
    stream = next(
        (
            s
            for s in streams
            if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")
        ),
        None,
    )
    if not stream:
        raise ValueError("재생 가능한 영상 트랙이 없습니다.")
    width, height = int(stream["width"]), int(stream["height"])
    duration = _number(stream.get("duration")) or _number(data.get("format", {}).get("duration"))
    fps = _number(stream.get("avg_frame_rate")) or _number(stream.get("r_frame_rate")) or 30.0
    if duration <= 0 or min(width, height) <= 0:
        raise ValueError("영상 길이 또는 크기를 확인할 수 없습니다.")
    rotation = int(float(stream.get("tags", {}).get("rotate", 0)))
    for side in stream.get("side_data_list", []):
        rotation = int(side.get("rotation", rotation))
    sar = _number(str(stream.get("sample_aspect_ratio", "1:1")).replace(":", "/")) or 1.0
    aspect = width / height * sar
    if abs(rotation) % 180 == 90:
        aspect = 1 / aspect
    return Video(
        path=str(Path(path).resolve()),
        width=width,
        height=height,
        duration_ms=max(1, round(duration * 1000)),
        fps=fps,
        has_audio=any(s.get("codec_type") == "audio" for s in streams),
        display_aspect=aspect,
        rotation=rotation,
        label=Label(text=Path(path).stem),
    )


def probe(path: str) -> Video:
    result = run_tool("ffprobe", [*PROBE_ARGS, path])
    return parse_probe(path, json.loads(result.stdout))


class ProbeJob(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, path: str, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.path = path
        self.process = QProcess(self)
        self.process.finished.connect(self._done)
        self.process.errorOccurred.connect(self._error)
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self._timeout)
        self.settled = False
        self._cancelled = False
        self._failure = ""

    def start(self) -> None:
        try:
            self.process.start(executable("ffprobe"), [*PROBE_ARGS, self.path])
            self.timer.start(30000)
        except OSError as exc:
            self._finish(str(exc))

    def cancel(self) -> None:
        if self.settled:
            return
        self._cancelled = True
        self.timer.stop()
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self._finish()
        else:
            self.process.kill()

    def _finish(self, message: str = "", video: Video | None = None) -> None:
        if self.settled:
            return
        self.settled = True
        self.timer.stop()
        if not self._cancelled:
            if message:
                self.failed.emit(f"{Path(self.path).name}: {message}")
            elif video is not None:
                self.succeeded.emit(video)
        self.finished.emit()

    def _timeout(self) -> None:
        self._failure = "영상 분석 시간이 초과되었습니다."
        self.process.kill()

    def _error(self, error: QProcess.ProcessError) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._finish(self.process.errorString())
        else:
            self._failure = self._failure or self.process.errorString()

    def _done(self, code: int, status: QProcess.ExitStatus) -> None:
        if self._cancelled:
            self._finish()
            return
        if code or status != QProcess.ExitStatus.NormalExit:
            self._finish(
                self._failure
                or bytes(self.process.readAllStandardError()).decode("utf-8", "replace")
            )
            return
        try:
            self._finish(
                video=parse_probe(
                    self.path, json.loads(bytes(self.process.readAllStandardOutput()))
                )
            )
        except (ValueError, KeyError, TypeError, ZeroDivisionError, OverflowError) as exc:
            self._finish(str(exc))
