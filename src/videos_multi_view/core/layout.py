from dataclasses import dataclass
from math import ceil, sqrt

from videos_multi_view.i18n import tr

from .models import Project


@dataclass(frozen=True)
class Rect:
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True)
class Cell:
    video_id: str
    bounds: Rect
    image: Rect


def even(value: float) -> int:
    return int(value) // 2 * 2


def fit(aspect: float, bounds: Rect) -> Rect:
    width = min(bounds.width, even(bounds.height * aspect))
    height = min(bounds.height, even(bounds.width / aspect))
    width, height = max(2, even(width)), max(2, even(height))
    return Rect(
        bounds.x + even((bounds.width - width) / 2),
        bounds.y + even((bounds.height - height) / 2),
        width,
        height,
    )


def calculate_layout(project: Project) -> list[Cell]:
    count = len(project.videos)
    if not count:
        return []
    spec, output = project.layout, project.output
    columns = spec.columns or ceil(sqrt(count))
    rows = ceil(count / columns)
    margin, gap = even(spec.margin), even(spec.gap)
    width = even((output.width - 2 * margin - gap * (columns - 1)) / columns)
    height = even((output.height - 2 * margin - gap * (rows - 1)) / rows)
    inset = even(spec.border_width + 1) if spec.border_visible else 0
    if min(width, height) < 4 + 2 * inset:
        raise ValueError(tr("셀 공간이 부족합니다. 열 수, 간격 또는 여백을 줄이세요."))
    cells = []
    for index, video in enumerate(project.videos):
        x = margin + index % columns * (width + gap)
        y = margin + index // columns * (height + gap)
        bounds = Rect(x, y, width, height)
        inner = Rect(x + inset, y + inset, width - 2 * inset, height - 2 * inset)
        cells.append(Cell(video.id, bounds, fit(video.display_aspect, inner)))
    return cells
