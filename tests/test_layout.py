"""Unit tests for grid layout calculations."""

import pytest

from videos_multi_view.core.layout import Rect, calculate_layout, even, fit
from videos_multi_view.core.models import Layout, Output, Project, Video


def test_fit():
    bounds = Rect(0, 0, 1000, 1000)
    # 16:9 aspect
    r1 = fit(16 / 9, bounds)
    assert r1.width == 1000
    assert r1.height == 562  # even
    assert r1.y == even((1000 - 562) / 2)

    # 9:16 portrait aspect
    r2 = fit(9 / 16, bounds)
    assert r2.height == 1000
    assert r2.width == 562
    assert r2.x == even((1000 - 562) / 2)


def test_calculate_layout_empty():
    p = Project()
    assert calculate_layout(p) == []


@pytest.mark.parametrize(
    "count,expected_cols,expected_rows",
    [
        (1, 1, 1),
        (2, 2, 1),
        (3, 2, 2),
        (4, 2, 2),
        (5, 3, 2),
        (6, 3, 2),
        (9, 3, 3),
    ],
)
def test_calculate_layout_auto_grid(count, expected_cols, expected_rows):
    videos = [
        Video(
            path=f"v{i}.mp4",
            width=1920,
            height=1080,
            duration_ms=1000,
            fps=30.0,
            id=f"v{i}",
        )
        for i in range(count)
    ]
    p = Project(
        videos=videos,
        layout=Layout(columns=0, gap=10, margin=20),
        output=Output(width=1920, height=1080),
    )
    cells = calculate_layout(p)
    assert len(cells) == count

    # Verify bounds fit within output canvas
    for cell in cells:
        b = cell.bounds
        assert b.x >= 20
        assert b.y >= 20
        assert b.x + b.width <= 1920 - 20
        assert b.y + b.height <= 1080 - 20

        # Verify image fits within bounds
        img = cell.image
        assert img.x >= b.x
        assert img.y >= b.y
        assert img.x + img.width <= b.x + b.width
        assert img.y + img.height <= b.y + b.height


def test_calculate_layout_explicit_columns():
    videos = [
        Video(path=f"v{i}.mp4", width=640, height=480, duration_ms=1000, fps=30.0, id=f"v{i}")
        for i in range(4)
    ]
    # Set explicit columns = 1 (vertical stack)
    p = Project(videos=videos, layout=Layout(columns=1, gap=10, margin=10))
    cells = calculate_layout(p)
    assert len(cells) == 4
    for i in range(3):
        assert cells[i].bounds.y + cells[i].bounds.height + 10 == cells[i + 1].bounds.y


def test_calculate_layout_insufficient_space():
    videos = [
        Video(path="v1.mp4", width=640, height=480, duration_ms=1000, fps=30.0),
        Video(path="v2.mp4", width=640, height=480, duration_ms=1000, fps=30.0),
    ]
    # Margin too large for canvas
    p = Project(
        videos=videos,
        layout=Layout(margin=1000),
        output=Output(width=1920, height=1080),
    )
    with pytest.raises(ValueError, match="셀 공간이 부족합니다"):
        calculate_layout(p)
