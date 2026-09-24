"""Playback synchronized to an anchored monotonic clock."""

import time

from PySide6.QtCore import QObject, Qt, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer, QVideoSink

from videos_multi_view.core.models import Project, Video
from videos_multi_view.core.timeline import duration_ms, is_active, source_time_ms


class SyncPlayer(QObject):
    frame_updated = Signal()
    position_changed = Signal(int)
    duration_changed = Signal(int)
    playback_state_changed = Signal(bool)
    finished = Signal()
    error = Signal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._project = Project()
        self._players: dict[str, QMediaPlayer] = {}
        self._audio_outputs: dict[str, QAudioOutput] = {}
        self._sinks: dict[str, QVideoSink] = {}
        self._frames: dict[str, QImage] = {}
        self._sources: dict[str, str] = {}
        self._phases: dict[str, str] = {}
        self._last_correction: dict[str, float] = {}
        self._signature: tuple = ()
        self._common_time = 0
        self._duration = 0
        self._is_playing = False
        self._anchor_time = 0.0
        self._anchor_position = 0
        self._clock_timer = QTimer(self)
        self._clock_timer.setInterval(25)
        self._clock_timer.timeout.connect(self._on_clock_tick)

    @property
    def is_playing(self) -> bool:
        return self._is_playing

    @property
    def common_time(self) -> int:
        return self._common_time

    def set_project(self, project: Project) -> None:
        signature = tuple(
            sorted((v.id, v.path, v.offset_ms, v.duration_ms, v.fps) for v in project.videos)
        )
        changed = signature != self._signature
        self._project = project
        self._signature = signature
        self._duration = duration_ms(project)
        ids = {v.id for v in project.videos}
        for key in list(self._players):
            if key not in ids:
                self._remove_player(key)
        for video in project.videos:
            if video.id in self._players and self._sources.get(video.id) != video.path:
                self._remove_player(video.id)
            if video.id not in self._players:
                self._create_player(video)
        if changed:
            self.duration_changed.emit(self._duration)
            self.seek(min(self._common_time, self._duration))
        else:
            self._update_audio_selection()

    def _create_player(self, video: Video) -> None:
        player, audio, sink = QMediaPlayer(self), QAudioOutput(self), QVideoSink(self)
        audio.setMuted(True)
        player.setAudioOutput(audio)
        player.setVideoSink(sink)
        key = video.id
        self._players[key], self._audio_outputs[key], self._sinks[key] = player, audio, sink
        self._sources[key] = video.path
        sink.setProperty("video_id", key)
        player.setProperty("video_id", key)
        sink.videoFrameChanged.connect(self._on_frame, Qt.ConnectionType.QueuedConnection)
        player.mediaStatusChanged.connect(self._on_media_status)
        player.errorOccurred.connect(self._on_error)
        player.setSource(QUrl.fromLocalFile(video.path))

    @Slot()
    def _on_frame(self) -> None:
        sink = self.sender()
        if sink is None:
            return
        key = sink.property("video_id")
        if self._sinks.get(key) is not sink:
            return  # Ignore queued notifications from a removed or replaced source.
        frame = sink.videoFrame()
        if frame.isValid():
            image = frame.toImage()
            if not image.isNull():
                self._frames[key] = image
                self.frame_updated.emit()

    @Slot(QMediaPlayer.MediaStatus)
    def _on_media_status(self, status: QMediaPlayer.MediaStatus) -> None:
        player = self.sender()
        if player is None or status != QMediaPlayer.MediaStatus.LoadedMedia:
            return
        key = player.property("video_id")
        if self._players.get(key) is player:
            video = next((v for v in self._project.videos if v.id == key), None)
            if video is not None:
                self._sync_player(video, True)

    @Slot(QMediaPlayer.Error, str)
    def _on_error(self, error: QMediaPlayer.Error, message: str) -> None:
        player = self.sender()
        if player is not None:
            key = player.property("video_id")
            if self._players.get(key) is player:
                video = next((v for v in self._project.videos if v.id == key), None)
                self.error.emit(f"{video.label.text if video else key}: {message}")

    def _remove_player(self, key: str) -> None:
        sink = self._sinks.pop(key, None)
        if sink:
            sink.videoFrameChanged.disconnect()
        player = self._players.pop(key, None)
        if player:
            player.mediaStatusChanged.disconnect()
            player.errorOccurred.disconnect()
            player.stop()
            player.setSource(QUrl())
            player.setVideoSink(None)
            player.setAudioOutput(None)
            player.deleteLater()
        audio = self._audio_outputs.pop(key, None)
        if audio:
            audio.deleteLater()
        if sink:
            sink.deleteLater()
        self._frames.pop(key, None)
        self._sources.pop(key, None)
        self._phases.pop(key, None)
        self._last_correction.pop(key, None)

    def _anchor(self) -> None:
        self._anchor_position = self._common_time
        self._anchor_time = time.monotonic()

    def play(self) -> None:
        if self._duration <= 0 or self._is_playing:
            return
        if self._common_time >= self._duration:
            self.seek(0)
        self._is_playing = True
        self._anchor()
        self._sync_all_players(True)
        self._clock_timer.start()
        self.playback_state_changed.emit(True)

    def pause(self) -> None:
        if self._is_playing:
            self._common_time = min(
                self._duration,
                self._anchor_position + round((time.monotonic() - self._anchor_time) * 1000),
            )
        self._is_playing = False
        self._clock_timer.stop()
        for player in self._players.values():
            if hasattr(player, "setPlaybackRate"):
                player.setPlaybackRate(1.0)
            player.pause()
        self._update_audio_selection()
        self.position_changed.emit(self._common_time)
        self.playback_state_changed.emit(False)

    def toggle_play_pause(self) -> None:
        self.pause() if self._is_playing else self.play()

    def stop(self) -> None:
        self.pause()
        self.seek(0)

    def seek(self, common_time_ms: int) -> None:
        self._common_time = max(0, min(common_time_ms, self._duration))
        self._anchor()
        self._sync_all_players(True)
        self.position_changed.emit(self._common_time)
        self.frame_updated.emit()

    def _on_clock_tick(self) -> None:
        if not self._is_playing:
            return
        self._common_time = min(
            self._duration,
            self._anchor_position + round((time.monotonic() - self._anchor_time) * 1000),
        )
        self._sync_all_players(False)
        self.position_changed.emit(self._common_time)
        self.frame_updated.emit()  # Update timecodes even while visible frames freeze.
        if self._common_time >= self._duration:
            self.pause()
            self.finished.emit()

    def _sync_all_players(self, is_seeking: bool) -> None:
        for video in self._project.videos:
            self._sync_player(video, is_seeking)
        self._update_audio_selection()

    def _sync_player(self, video: Video, is_seeking: bool) -> None:
        player = self._players.get(video.id)
        if player is None:
            return
        source = source_time_ms(video, self._common_time)
        active = is_active(video, self._common_time)
        phase = "before" if source is None else "active" if active else "ended"
        transition = self._phases.get(video.id) != phase
        self._phases[video.id] = phase
        position = source or 0
        now = time.monotonic()
        # Let a decoder finish an asynchronous seek before issuing another correction.
        correction_due = now - self._last_correction.get(video.id, 0) >= 0.25
        drift = position - player.position()
        if (
            is_seeking
            or transition
            or (active and self._is_playing and correction_due and abs(drift) > 400)
        ):
            self._last_correction[video.id] = now
            player.setPosition(position)
            if hasattr(player, "setPlaybackRate"):
                player.setPlaybackRate(1.0)
        elif active and self._is_playing:
            # Soft sync: micro-adjust playback rate without flushing decoders
            if hasattr(player, "setPlaybackRate"):
                if drift > 80:
                    player.setPlaybackRate(1.05)
                elif drift < -80:
                    player.setPlaybackRate(0.95)
                else:
                    player.setPlaybackRate(1.0)
        else:
            if hasattr(player, "setPlaybackRate"):
                player.setPlaybackRate(1.0)
        playing = active and self._is_playing
        state = player.playbackState()
        if playing and state != QMediaPlayer.PlaybackState.PlayingState:
            player.play()
        elif not playing and state != QMediaPlayer.PlaybackState.PausedState:
            player.pause()

    def _update_audio_selection(self) -> None:
        for video in self._project.videos:
            audio = self._audio_outputs.get(video.id)
            if audio:
                muted = not (
                    self._is_playing
                    and video.id == self._project.audio_id
                    and is_active(video, self._common_time)
                )
                if audio.isMuted() != muted:
                    audio.setMuted(muted)

    def get_frame(self, video: Video, common_time_ms: int) -> QImage | None:
        if source_time_ms(video, common_time_ms) is None:
            return None
        return self._frames.get(video.id)

    def cleanup(self) -> None:
        self.pause()
        for key in list(self._players):
            self._remove_player(key)
        self._common_time = self._duration = 0
        self._signature = ()
        self._project = Project()
        self.position_changed.emit(0)
