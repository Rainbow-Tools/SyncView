import re
from dataclasses import dataclass, field
from math import isfinite
from uuid import uuid4

from videos_multi_view.i18n import tr

POSITIONS = ("top-left", "top-right", "bottom-left", "bottom-right")


@dataclass
class Label:
    text: str = ""
    visible: bool = True
    position: str = "bottom-left"
    size: int = 28
    color: str = "#ffffff"
    background: str = "#b3000000"
    font_family: str = ""


@dataclass
class Video:
    path: str
    width: int
    height: int
    duration_ms: int
    fps: float
    has_audio: bool = False
    display_aspect: float = 1.0
    rotation: int = 0
    id: str = field(default_factory=lambda: uuid4().hex)
    offset_ms: int = 0
    label: Label = field(default_factory=Label)


@dataclass
class Layout:
    columns: int = 0
    gap: int = 8
    margin: int = 16
    background: str = "#15191f"
    border_visible: bool = False
    border_width: int = 2
    border_color: str = "#ffffff"


VALID_ENCODERS = ("libx264", "h264_nvenc", "h264_qsv")
OVERLAY_METHODS = ("blend", "tint", "difference")
DIFF_COLORMAPS = ("grayscale", "heat", "jet", "green", "magenta", "custom")


@dataclass
class OverlayConfig:
    enabled: bool = False
    base_video_id: str | None = None
    overlay_video_id: str | None = None
    method: str = "blend"
    opacity: float = 0.5
    gain: float = 1.0
    tint_a: str = "#FF0000"
    tint_b: str = "#00FFFF"
    diff_colormap: str = "grayscale"
    diff_custom_color: str = "#00FF66"


@dataclass
class Output:
    width: int = 1920
    height: int = 1080
    fps: int = 30
    encoder: str = "libx264"


@dataclass
class Project:
    videos: list[Video] = field(default_factory=list)
    layout: Layout = field(default_factory=Layout)
    output: Output = field(default_factory=Output)
    overlay: OverlayConfig = field(default_factory=OverlayConfig)
    audio_id: str | None = None
    version: int = 1

    def validate(self) -> None:
        if self.version != 1:
            raise ValueError(tr("지원하지 않는 프로젝트 버전입니다."))
        for value in (self.output.width, self.output.height):
            if type(value) is not int or not 2 <= value <= 16384 or value % 2:
                raise ValueError(tr("출력 크기는 2~16384 사이의 짝수여야 합니다."))
        if self.output.fps not in (24, 30, 60):
            raise ValueError(tr("출력 FPS는 24, 30, 60 중 하나여야 합니다."))
        if self.output.encoder not in VALID_ENCODERS:
            raise ValueError(tr("지원하지 않는 인코더입니다."))
        for value in (self.layout.columns, self.layout.gap, self.layout.margin):
            if type(value) is not int or value < 0:
                raise ValueError(tr("열 수, 간격, 여백은 음수가 될 수 없습니다."))
        if not 0 <= self.layout.border_width <= 100:
            raise ValueError(tr("테두리 두께는 0~100 사이여야 합니다."))
        colors = [self.layout.background, self.layout.border_color]
        ids = set()
        for video in self.videos:
            if not isinstance(video.path, str) or not video.path:
                raise ValueError(tr("영상 경로가 비어 있습니다."))
            if not isinstance(video.id, str) or not video.id or video.id in ids:
                raise ValueError(tr("영상 ID가 비어 있거나 중복되었습니다."))
            ids.add(video.id)
            if video.width <= 0 or video.height <= 0 or video.duration_ms <= 0:
                raise ValueError(tr("영상 크기 또는 길이가 올바르지 않습니다."))
            if not isfinite(video.fps) or video.fps <= 0:
                raise ValueError(tr("영상 FPS가 올바르지 않습니다."))
            if not isfinite(video.display_aspect) or video.display_aspect <= 0:
                raise ValueError(tr("영상 표시 비율이 올바르지 않습니다."))
            if type(video.offset_ms) is not int:
                raise ValueError(tr("오프셋은 밀리초 정수여야 합니다."))
            if video.offset_ms + video.duration_ms <= 0:
                raise ValueError(tr("오프셋이 영상 전체 길이를 건너뜁니다."))
            if video.label.position not in POSITIONS or not 8 <= video.label.size <= 200:
                raise ValueError(tr("이름표 위치 또는 크기가 올바르지 않습니다."))
            if not isinstance(video.label.text, str):
                raise ValueError(tr("이름표는 문자열이어야 합니다."))
            if not isinstance(video.label.font_family, str):
                raise ValueError(tr("이름표 글꼴은 문자열이어야 합니다."))
            colors += [video.label.color, video.label.background]
        if self.audio_id is not None and self.audio_id not in ids:
            raise ValueError(tr("선택한 오디오 영상이 없습니다."))
        if self.overlay.method not in OVERLAY_METHODS:
            raise ValueError(tr("지원하지 않는 오버레이 비교 방식입니다."))
        if self.overlay.diff_colormap not in DIFF_COLORMAPS:
            raise ValueError(tr("지원하지 않는 잔차 색상입니다."))
        if not (0.0 <= self.overlay.opacity <= 1.0):
            raise ValueError(tr("투명도는 0.0과 1.0 사이여야 합니다."))
        if not (1.0 <= self.overlay.gain <= 50.0):
            raise ValueError(tr("잔차 증폭 배율은 1.0과 50.0 사이여야 합니다."))
        colors += [self.overlay.tint_a, self.overlay.tint_b, self.overlay.diff_custom_color]
        if self.overlay.base_video_id is not None and self.overlay.base_video_id not in ids:
            raise ValueError(tr("선택한 기준 영상이 없습니다."))
        if self.overlay.overlay_video_id is not None and self.overlay.overlay_video_id not in ids:
            raise ValueError(tr("선택한 비교 영상이 없습니다."))
        for color in colors:
            if not isinstance(color, str) or not re.fullmatch(
                r"#[0-9a-fA-F]{6}([0-9a-fA-F]{2})?", color
            ):
                raise ValueError(tr("색상은 #RRGGBB 또는 #AARRGGBB 형식이어야 합니다."))
