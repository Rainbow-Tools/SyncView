"""Project actions, validated updates and bounded background-job lifetimes."""

from collections import deque
from copy import deepcopy
from dataclasses import fields
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from videos_multi_view.application.storage import load_project, save_project
from videos_multi_view.core.layout import calculate_layout
from videos_multi_view.core.models import Project, Video
from videos_multi_view.i18n import tr
from videos_multi_view.media.exporter import ExportJob
from videos_multi_view.media.player import SyncPlayer
from videos_multi_view.media.probe import ProbeJob


class AppController(QObject):
    project_changed = Signal(object)
    video_selected = Signal(object)
    probe_status_updated = Signal(str, bool)
    probe_progress = Signal(int, int)
    export_progress = Signal(float)
    export_succeeded = Signal(str)
    export_failed = Signal(str)
    export_cancelled = Signal()
    dirty_changed = Signal(bool)
    idle = Signal()

    def __init__(self, player: SyncPlayer, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.player = player
        self.project = Project()
        self.current_project_path: Path | None = None
        self.selected_video_id: str | None = None
        self.is_dirty = False
        self._active_probe_jobs: list[ProbeJob] = []
        self._queue: deque[tuple[int, str, str | None]] = deque()
        self._results: dict[int, tuple[str, str | None, Video | None]] = {}
        self._pending_paths: set[str] = set()
        self._generation = 0
        self._probe_total = self._probe_completed = self._next_result = 0
        self._current_export_job: ExportJob | None = None
        self._closing = False

    @property
    def busy(self) -> bool:
        return bool(self._active_probe_jobs or self._current_export_job)

    def _cancel_probes(self) -> None:
        self._generation += 1
        self._queue.clear()
        self._results.clear()
        self._pending_paths.clear()
        self._probe_total = self._probe_completed = self._next_result = 0
        for job in list(self._active_probe_jobs):
            job.cancel()
        self.probe_progress.emit(0, 0)

    def shutdown(self) -> None:
        self._closing = True
        self._cancel_probes()
        self.cancel_export()
        self.player.cleanup()
        self._check_idle()

    def _check_idle(self) -> None:
        if self._closing and not self.busy:
            self.idle.emit()

    def _replace_project(self, project: Project, path: Path | None) -> None:
        self._cancel_probes()
        self.player.cleanup()
        self.project = project
        self.current_project_path = path
        self.selected_video_id = project.videos[0].id if project.videos else None
        self.is_dirty = False
        self.dirty_changed.emit(False)
        self.player.set_project(project)
        self.project_changed.emit(project)
        self.video_selected.emit(self.selected_video_id)

    def new_project(self) -> None:
        self._replace_project(Project(), None)

    def load_project_file(self, path: Path) -> list[str]:
        loaded = load_project(path)
        self._replace_project(loaded, path.resolve())
        return [v.path for v in loaded.videos if not Path(v.path).is_file()]

    def save_project_file(self, path: Path) -> None:
        save_project(self.project, path)
        self.current_project_path = path.resolve()
        self.is_dirty = False
        self.dirty_changed.emit(False)

    def add_video_files(self, paths: list[str]) -> None:
        for path in paths:
            self._enqueue(path)
        self._pump_probes()

    def relink_video(self, video_id: str, path: str) -> None:
        if any(v.id == video_id for v in self.project.videos):
            self._enqueue(path, video_id)
            self._pump_probes()

    def _enqueue(self, path: str, relink_id: str | None = None) -> None:
        source = Path(path).resolve()
        canonical = str(source).casefold()
        if not source.is_file():
            self.probe_status_updated.emit(
                tr("파일을 찾을 수 없습니다: {value0}", value0=source.name), True
            )
            return
        if canonical in self._pending_paths or (
            relink_id is None and any(Path(v.path).resolve() == source for v in self.project.videos)
        ):
            self.probe_status_updated.emit(
                tr("이미 추가 중이거나 추가된 영상입니다: {value0}", value0=source.name), False
            )
            return
        self._pending_paths.add(canonical)
        self._queue.append((self._probe_total, str(source), relink_id))
        self._probe_total += 1
        self.probe_progress.emit(self._probe_completed, self._probe_total)

    def _pump_probes(self) -> None:
        while self._queue and len(self._active_probe_jobs) < 2 and not self._closing:
            index, path, relink = self._queue.popleft()
            job = ProbeJob(path, self)
            self._active_probe_jobs.append(job)
            generation = self._generation
            result: list[Video] = []

            def success(video: Video, bucket=result) -> None:
                bucket.append(video)

            def failure(message: str, epoch=generation) -> None:
                if epoch == self._generation:
                    self.probe_status_updated.emit(message, True)

            def finished(
                j=job, idx=index, source=path, target=relink, epoch=generation, bucket=result
            ) -> None:
                if j in self._active_probe_jobs:
                    self._active_probe_jobs.remove(j)
                j.deleteLater()
                if epoch == self._generation and not self._closing:
                    self._results[idx] = (source, target, bucket[0] if bucket else None)
                    self._probe_completed += 1
                    self._drain_results()
                    self.probe_progress.emit(self._probe_completed, self._probe_total)
                self._pump_probes()
                self._check_idle()

            job.succeeded.connect(success)
            job.failed.connect(failure)
            job.finished.connect(finished)
            job.start()

    def _drain_results(self) -> None:
        changed = False
        while self._next_result in self._results:
            source, target, video = self._results.pop(self._next_result)
            self._next_result += 1
            self._pending_paths.discard(source.casefold())
            if video is None:
                continue
            if target:
                original = next((v for v in self.project.videos if v.id == target), None)
                if original is None:
                    continue
                video.id, video.label, video.offset_ms = (
                    original.id,
                    original.label,
                    original.offset_ms,
                )
                if video.duration_ms + video.offset_ms <= 0:
                    self.probe_status_updated.emit(tr("교체 영상이 오프셋보다 짧습니다."), True)
                    continue
                self.project.videos[self.project.videos.index(original)] = video
            else:
                self.project.videos.append(video)
            self.selected_video_id = self.selected_video_id or video.id
            changed = True
            self.probe_status_updated.emit(
                tr("추가/연결 완료: {value0}", value0=Path(video.path).name), False
            )
        if changed:
            self._notify_state_changed()

    def remove_video(self, video_id: str) -> None:
        self.project.videos[:] = [v for v in self.project.videos if v.id != video_id]
        if self.project.audio_id == video_id:
            self.project.audio_id = None
        if self.selected_video_id == video_id:
            self.selected_video_id = self.project.videos[0].id if self.project.videos else None
        self._notify_state_changed()

    def move_video(self, video_id: str, direction: int) -> None:
        index = next((i for i, v in enumerate(self.project.videos) if v.id == video_id), -1)
        other = index + direction
        if index >= 0 and 0 <= other < len(self.project.videos):
            self.project.videos[index], self.project.videos[other] = (
                self.project.videos[other],
                self.project.videos[index],
            )
            self._notify_state_changed()

    def select_video(self, video_id: str | None) -> None:
        if self.selected_video_id != video_id:
            self.selected_video_id = video_id
            self.video_selected.emit(video_id)

    def apply_settings(self, kind: str, value: object) -> None:
        candidate = deepcopy(self.project)
        try:
            if kind == "video":
                idx = next(i for i, v in enumerate(candidate.videos) if v.id == value.id)
                candidate.videos[idx] = value
            elif kind == "layout":
                candidate.layout, candidate.output = value
            elif kind == "output":
                candidate.output = value
            elif kind == "overlay":
                candidate.overlay = value
            candidate.validate()
            calculate_layout(candidate)
        except (ValueError, TypeError, StopIteration) as exc:
            self.probe_status_updated.emit(str(exc), True)
            self.project_changed.emit(self.project)
            return
        if kind == "video":
            original = self.project.videos[idx]
            for field in fields(Video):
                setattr(original, field.name, getattr(value, field.name))
        elif kind == "overlay":
            self.project.overlay = candidate.overlay
        else:
            self.project.layout, self.project.output = candidate.layout, candidate.output
        self._notify_state_changed()

    def update_layout(self) -> None:
        self._notify_state_changed()

    def update_video_settings(self, video_id: str) -> None:
        self._notify_state_changed()

    def update_overlay_settings(self) -> None:
        self._notify_state_changed()

    def set_audio_source(self, audio_id: str | None) -> None:
        self.project.audio_id = audio_id
        self._notify_state_changed()

    def _notify_state_changed(self) -> None:
        try:
            self.project.validate()
            calculate_layout(self.project)
        except (ValueError, TypeError) as exc:
            self.probe_status_updated.emit(str(exc), True)
        self.is_dirty = True
        self.dirty_changed.emit(True)
        self.player.set_project(self.project)
        self.project_changed.emit(self.project)
        self.video_selected.emit(self.selected_video_id)

    def start_export(self, target_path: Path, fps: int | None = None) -> None:
        if self._current_export_job:
            self.export_failed.emit(tr("이미 다른 내보내기 작업이 진행 중입니다."))
            return
        if self.current_project_path and target_path.resolve() == self.current_project_path:
            self.export_failed.emit(tr("프로젝트 파일을 영상으로 덮어쓸 수 없습니다."))
            return
        snapshot = deepcopy(self.project)
        if fps is not None:
            snapshot.output.fps = fps
        job = ExportJob(snapshot, target_path, self)
        self._current_export_job = job
        job.progress.connect(self.export_progress.emit)
        job.succeeded.connect(self.export_succeeded.emit)
        job.failed.connect(self.export_failed.emit)
        job.cancelled.connect(self.export_cancelled.emit)

        def finished() -> None:
            self._current_export_job = None
            job.deleteLater()
            self._check_idle()

        job.finished.connect(finished)
        job.start()

    def cancel_export(self) -> None:
        if self._current_export_job:
            self._current_export_job.cancel()
