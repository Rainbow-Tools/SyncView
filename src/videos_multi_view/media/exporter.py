"""Cancellable export. Rendering and pipe backpressure stay off the GUI thread."""

import os
import subprocess
from collections import deque
from copy import deepcopy
from math import ceil
from pathlib import Path
from threading import Event, Lock, Thread
from uuid import uuid4

from PySide6.QtCore import QObject, QThread, Signal

from videos_multi_view.core.layout import calculate_layout
from videos_multi_view.core.models import Project
from videos_multi_view.core.timeline import duration_ms, source_time_ms
from videos_multi_view.i18n import tr
from videos_multi_view.media.tools import executable
from videos_multi_view.ui.renderer import DecorationRenderer


def build_filter_complex(project: Project) -> tuple[str, bool]:
    cells = calculate_layout(project)
    length = duration_ms(project) / 1000
    fps = project.output.fps
    # MP4 is opaque; QColor's alpha-first notation must not be passed as FFmpeg RGBA.
    background = project.layout.background[-6:]
    filters = [
        f"color=c=0x{background}:s={project.output.width}x{project.output.height}"
        f":r={fps}:d={length:.6f}[base]"
    ]
    previous = "[base]"
    for i, (video, cell) in enumerate(zip(project.videos, cells, strict=True)):
        start = (source_time_ms(video, 0) or 0) / 1000
        delay = max(0, video.offset_ms) / 1000
        rect = cell.image
        # Normalize BEFORE trim; resample only after trimming the source interval.
        chain = (
            f"setpts=PTS-STARTPTS,trim=start={start:.6f}:end={video.duration_ms / 1000:.6f},"
            f"setpts=PTS-STARTPTS,scale={rect.width}:{rect.height},setsar=1,"
            f"tpad=stop_mode=clone:stop_duration={length:.6f},fps={fps},setpts=PTS+{delay:.6f}/TB"
        )
        filters.append(f"[{i}:v:0]{chain}[v{i}]")
        filters.append(
            f"{previous}[v{i}]overlay=x={rect.x}:y={rect.y}:eof_action=repeat"
            f":enable='gte(t,{delay:.6f})'[ov{i}]"
        )
        previous = f"[ov{i}]"
    filters.append(f"{previous}[{len(project.videos)}:v:0]overlay=0:0:format=auto:shortest=1[vout]")
    has_audio = False
    for i, video in enumerate(project.videos):
        if video.id == project.audio_id and video.has_audio:
            start = max(0, -video.offset_ms) / 1000
            delay = max(0, video.offset_ms)
            filters.append(
                f"[{i}:a:0]asetpts=PTS-STARTPTS,"
                f"atrim=start={start:.6f}:end={video.duration_ms / 1000:.6f},"
                f"asetpts=PTS-STARTPTS,adelay={delay}:all=1,"
                f"apad=whole_dur={length:.6f},atrim=duration={length:.6f}[aout]"
            )
            has_audio = True
            break
    return ";".join(filters), has_audio


class _ExportWorker(QThread):
    progress = Signal(float)

    def __init__(self, project: Project, target: Path, parent: QObject) -> None:
        super().__init__(parent)
        self.project, self.target = project, target
        self.cancel_event = Event()
        self.lock = Lock()
        self.process: subprocess.Popen | None = None
        self.error = ""
        self.cleanup_failed = False
        self.success = False

    def cancel(self) -> None:
        with self.lock:
            if self.success:
                return
            self.cancel_event.set()
            if self.process is not None and self.process.poll() is None:
                self.process.kill()

    def run(self) -> None:
        token = uuid4().hex
        temporary = self.target.with_name(f".{self.target.stem}_{token}.tmp.mp4")
        overlay = self.target.with_name(f".{self.target.stem}_{token}_dec.png")
        readers: list[Thread] = []
        errors: deque[str] = deque(maxlen=100)
        try:
            project = self.project
            project.validate()
            if not project.videos or duration_ms(project) <= 0:
                raise ValueError(tr("합성할 재생 구간이 없습니다."))
            for video in project.videos:
                source = Path(video.path)
                if source.resolve() == self.target or (
                    self.target.exists()
                    and source.exists()
                    and os.path.samefile(source, self.target)
                ):
                    raise ValueError(tr("출력 경로가 원본 영상 파일과 같습니다."))
                if not source.is_file():
                    raise ValueError(
                        tr("원본 파일을 다시 연결하세요: {value0}", value0=source.name)
                    )
            if not self.target.parent.is_dir():
                raise ValueError(tr("출력 폴더가 없습니다."))
            if self.target.is_dir():
                raise ValueError(tr("출력 위치가 파일이 아닌 폴더입니다."))
            renderer = DecorationRenderer(project, calculate_layout(project))
            args = ["-hide_banner", "-loglevel", "error", "-nostdin", "-y"]
            for video in project.videos:
                args += ["-i", video.path]
            if renderer.dynamic:
                args += [
                    "-f",
                    "rawvideo",
                    "-pixel_format",
                    "rgba",
                    "-video_size",
                    f"{project.output.width}x{project.output.height}",
                    "-framerate",
                    str(project.output.fps),
                    "-i",
                    "pipe:0",
                ]
            else:
                if not renderer.image().save(str(overlay)):
                    raise OSError(tr("이름표 이미지를 저장할 수 없습니다."))
                args += ["-loop", "1", "-framerate", str(project.output.fps), "-i", str(overlay)]
            graph, audio = build_filter_complex(project)
            args += ["-filter_complex", graph, "-map", "[vout]"]
            args += ["-map", "[aout]", "-c:a", "aac", "-b:a", "192k"] if audio else ["-an"]
            encoder = project.output.encoder
            args += ["-c:v", encoder, "-pix_fmt", "nv12" if encoder == "h264_qsv" else "yuv420p"]
            if encoder == "libx264":
                args += ["-crf", "18", "-preset", "medium"]
            length = duration_ms(project)
            args += [
                "-r",
                str(project.output.fps),
                "-t",
                f"{length / 1000:.6f}",
                "-movflags",
                "+faststart",
                "-progress",
                "pipe:1",
                str(temporary),
            ]
            with self.lock:
                if self.cancel_event.is_set():
                    return
                self.process = subprocess.Popen(
                    [executable("ffmpeg"), *args],
                    stdin=subprocess.PIPE if renderer.dynamic else subprocess.DEVNULL,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    bufsize=0,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
                )
            process = self.process

            def read_progress() -> None:
                for raw in process.stdout:
                    if raw.startswith(b"out_time_us="):
                        try:
                            self.progress.emit(
                                min(0.999, max(0, int(raw.split(b"=")[1]) / (length * 1000)))
                            )
                        except ValueError:
                            pass

            def read_errors() -> None:
                for raw in process.stderr:
                    errors.append(raw.decode("utf-8", "replace")[-2048:])

            readers = [Thread(target=read_progress), Thread(target=read_errors)]
            for reader in readers:
                reader.start()
            if renderer.dynamic:
                for frame in range(ceil(length * project.output.fps / 1000)):
                    if self.cancel_event.is_set():
                        break
                    image = renderer.image(round(frame * 1000 / project.output.fps))
                    remaining = image.constBits()
                    # Keep only the current image; OS pipe backpressure bounds the buffer.
                    while remaining and not self.cancel_event.is_set():
                        written = process.stdin.write(remaining)
                        if not written:
                            raise BrokenPipeError(tr("FFmpeg 입력 파이프가 닫혔습니다."))
                        remaining = remaining[written:]
                process.stdin.close()
            code = process.wait()
            for reader in readers:
                reader.join()
            with self.lock:
                if not self.cancel_event.is_set():
                    if code != 0 or not temporary.is_file():
                        raise RuntimeError("".join(errors) or tr("FFmpeg 인코딩이 실패했습니다."))
                    os.replace(temporary, self.target)
                    self.success = True
        except Exception as exc:
            self.error = "".join(errors) or str(exc)
        finally:
            with self.lock:
                if self.process is not None and self.process.poll() is None:
                    self.process.kill()
            if self.process is not None:
                self.process.wait()
                for reader in readers:
                    reader.join()
                for stream in (self.process.stdin, self.process.stdout, self.process.stderr):
                    if stream:
                        stream.close()
            for path in (temporary, overlay):
                try:
                    path.unlink(missing_ok=True)
                except OSError as exc:
                    self.cleanup_failed = True
                    self.error += tr(
                        "\n임시 파일 정리 실패: {value0}: {value1}", value0=path.name, value1=exc
                    )


class ExportJob(QObject):
    progress = Signal(float)
    succeeded = Signal(str)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(self, project: Project, target_path: Path, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.project = deepcopy(project)
        self.target_path = target_path.resolve()
        self._worker: _ExportWorker | None = None
        self._settled = False

    def start(self) -> None:
        if self._worker is not None or self._settled:
            return
        # Keep immediate validation errors observable, without launching a worker.
        try:
            self.project.validate()
            if any(Path(v.path).resolve() == self.target_path for v in self.project.videos):
                raise ValueError(tr("출력 경로가 원본 영상 파일과 같습니다."))
        except (ValueError, TypeError) as exc:
            self._settled = True
            self.failed.emit(str(exc))
            self.finished.emit()
            return
        self._worker = _ExportWorker(self.project, self.target_path, self)
        self._worker.progress.connect(self.progress.emit)
        self._worker.finished.connect(self._done)
        self._worker.start()

    def cancel(self) -> None:
        if self._worker is not None and not self._settled:
            self._worker.cancel()

    def _done(self) -> None:
        if self._settled:
            return
        self._settled = True
        worker = self._worker
        if worker.success:
            self.progress.emit(1.0)
            self.succeeded.emit(str(self.target_path))
        elif worker.cancel_event.is_set() and not worker.cleanup_failed:
            self.cancelled.emit()
        else:
            self.failed.emit(worker.error or tr("내보내기가 실패했습니다."))
        self.finished.emit()
        worker.deleteLater()
