from math import ceil

from .models import Project, Video


def duration_ms(project: Project) -> int:
    return max([0] + [v.offset_ms + v.duration_ms for v in project.videos])


def source_time_ms(video: Video, common_ms: int) -> int | None:
    """None means the clip has not started; ended clips retain their last frame."""
    source = common_ms - video.offset_ms
    if source < 0:
        return None
    last = max(0, video.duration_ms - max(1, ceil(1000 / video.fps)))
    return min(source, last)


def is_active(video: Video, common_ms: int) -> bool:
    return video.offset_ms <= common_ms < video.offset_ms + video.duration_ms


def format_time(milliseconds: int) -> str:
    seconds, ms = divmod(max(0, milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02}:{seconds:02}.{ms:03}"
