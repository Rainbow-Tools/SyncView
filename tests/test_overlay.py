"""Unit tests for overlay video comparison mode."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPainter

from videos_multi_view.application.controller import AppController
from videos_multi_view.application.storage import load_project, save_project
from videos_multi_view.core.models import OverlayConfig, Project, Video
from videos_multi_view.media.exporter import build_filter_complex
from videos_multi_view.media.player import SyncPlayer
from videos_multi_view.ui.preview import PreviewCanvas
from videos_multi_view.ui.renderer import DecorationRenderer
from videos_multi_view.ui.settings_panel import SettingsPanel


def test_overlay_model_defaults_and_validation():
    proj = Project(
        videos=[
            Video(path="C:/v1.mp4", width=1920, height=1080, duration_ms=5000, fps=30.0),
            Video(path="C:/v2.mp4", width=1920, height=1080, duration_ms=5000, fps=30.0),
        ],
        overlay=OverlayConfig(
            enabled=True,
            method="blend",
            opacity=0.7,
            gain=2.5,
            tint_a="#FF0000",
            tint_b="#00FFFF",
        ),
    )
    proj.validate()
    assert proj.overlay.enabled is True
    assert proj.overlay.opacity == 0.7
    assert proj.overlay.diff_colormap == "grayscale"
    assert proj.overlay.diff_custom_color == "#00FF66"

    # Valid colormaps
    for cmap in ("grayscale", "heat", "jet", "green", "magenta", "custom"):
        ok_p = Project(
            videos=proj.videos,
            overlay=OverlayConfig(diff_colormap=cmap, diff_custom_color="#123456"),
        )
        ok_p.validate()

    # Invalid colormap
    with pytest.raises(ValueError, match="지원하지 않는 잔차 색상"):
        bad = Project(overlay=OverlayConfig(diff_colormap="invalid_cmap"))
        bad.validate()

    # Invalid custom color format
    with pytest.raises(ValueError, match="색상"):
        bad = Project(overlay=OverlayConfig(diff_custom_color="not_a_hex"))
        bad.validate()

    # Invalid method
    with pytest.raises(ValueError, match="지원하지 않는 오버레이"):
        bad = Project(overlay=OverlayConfig(method="unknown_method"))
        bad.validate()

    # Invalid opacity
    with pytest.raises(ValueError, match="투명도"):
        bad = Project(overlay=OverlayConfig(opacity=1.5))
        bad.validate()

    # Invalid gain
    with pytest.raises(ValueError, match="잔차 증폭"):
        bad = Project(overlay=OverlayConfig(gain=0.5))
        bad.validate()

    # Invalid tint color format
    with pytest.raises(ValueError, match="색상"):
        bad = Project(overlay=OverlayConfig(tint_a="red"))
        bad.validate()

    # Invalid video IDs
    with pytest.raises(ValueError, match="기준 영상"):
        bad = Project(overlay=OverlayConfig(base_video_id="non_existent_id"))
        bad.validate()


def test_overlay_storage_roundtrip(tmp_path: Path):
    v1_file = tmp_path / "v1.mp4"
    v2_file = tmp_path / "v2.mp4"
    v1_file.write_bytes(b"v1")
    v2_file.write_bytes(b"v2")

    v1 = Video(path=str(v1_file.resolve()), width=1920, height=1080, duration_ms=4000, fps=30.0)
    v2 = Video(path=str(v2_file.resolve()), width=1920, height=1080, duration_ms=4000, fps=30.0)

    proj = Project(
        videos=[v1, v2],
        overlay=OverlayConfig(
            enabled=True,
            base_video_id=v1.id,
            overlay_video_id=v2.id,
            method="difference",
            gain=5.0,
            diff_colormap="heat",
            diff_custom_color="#123456",
        ),
    )
    proj_path = tmp_path / "overlay_project.json"
    save_project(proj, proj_path)

    loaded = load_project(proj_path)
    assert loaded.overlay.enabled is True
    assert loaded.overlay.base_video_id == v1.id
    assert loaded.overlay.overlay_video_id == v2.id
    assert loaded.overlay.method == "difference"
    assert loaded.overlay.gain == 5.0
    assert loaded.overlay.diff_colormap == "heat"
    assert loaded.overlay.diff_custom_color == "#123456"


def test_overlay_filter_complex_export():
    v1 = Video(path="C:/v1.mp4", width=1920, height=1080, duration_ms=5000, fps=30.0)
    v2 = Video(path="C:/v2.mp4", width=1920, height=1080, duration_ms=5000, fps=30.0)

    # 1. Blend mode
    p_blend = Project(
        videos=[v1, v2],
        overlay=OverlayConfig(
            enabled=True,
            base_video_id=v1.id,
            overlay_video_id=v2.id,
            method="blend",
            opacity=0.6,
        ),
    )
    filtergraph, _ = build_filter_complex(p_blend)
    assert "blend=all_mode='normal':all_opacity=0.600" in filtergraph
    assert "[ov_composed]" in filtergraph

    # 2. Difference mode (all colormaps)
    for cmap, expected_token in (
        ("grayscale", "val*8.00"),
        ("heat", "clip(3*clip(val*8.00"),
        ("jet", "clip(4*clip(val*8.00"),
        ("green", "102/255"),
        ("magenta", "153/255"),
        ("custom", "val*8.00*0.000"),
    ):
        p_diff = Project(
            videos=[v1, v2],
            overlay=OverlayConfig(
                enabled=True,
                base_video_id=v1.id,
                overlay_video_id=v2.id,
                method="difference",
                gain=8.0,
                diff_colormap=cmap,
                diff_custom_color="#000000",
            ),
        )
        filtergraph, _ = build_filter_complex(p_diff)
        assert "blend=all_mode='difference'" in filtergraph
        assert expected_token in filtergraph
        assert "format=gray,format=rgb24" in filtergraph

    # 3. Tint mode
    p_tint = Project(
        videos=[v1, v2],
        overlay=OverlayConfig(
            enabled=True,
            base_video_id=v1.id,
            overlay_video_id=v2.id,
            method="tint",
            tint_a="#FF0000",
            tint_b="#00FFFF",
        ),
    )
    filtergraph, _ = build_filter_complex(p_tint)
    assert "colorchannelmixer" in filtergraph
    assert "blend=all_mode='addition'" in filtergraph


def test_overlay_controller_and_settings_panel(qtbot):
    player = SyncPlayer()
    controller = AppController(player)

    v1 = Video(path="C:/v1.mp4", width=1920, height=1080, duration_ms=4000, fps=30.0)
    v2 = Video(path="C:/v2.mp4", width=1920, height=1080, duration_ms=4000, fps=30.0)
    controller.project.videos = [v1, v2]

    panel = SettingsPanel()
    qtbot.addWidget(panel)
    panel.show()
    panel.set_project(controller.project)

    assert panel.chk_overlay.isEnabled() is True
    assert panel.combo_ov_base.count() == 2
    assert panel.combo_ov_target.count() == 2

    # Toggle overlay
    panel.chk_overlay.setChecked(True)
    assert panel.combo_ov_base.isEnabled() is True
    assert panel.combo_ov_target.isEnabled() is True

    # Check method switching visibility
    panel.combo_ov_method.setCurrentIndex(panel.combo_ov_method.findData("blend"))
    assert panel.row_opacity_widget.isVisible() is True
    assert panel.spin_ov_gain.isVisible() is False
    assert panel.combo_ov_tint.isVisible() is False

    panel.combo_ov_method.setCurrentIndex(panel.combo_ov_method.findData("difference"))
    assert panel.row_opacity_widget.isVisible() is False
    assert panel.spin_ov_gain.isVisible() is True
    assert panel.combo_diff_colormap.isVisible() is True
    assert panel.lbl_ov_diff_color.isVisible() is True
    assert panel.combo_ov_tint.isVisible() is False

    # Check custom diff color button visibility
    panel.combo_diff_colormap.setCurrentIndex(panel.combo_diff_colormap.findData("grayscale"))
    assert panel.btn_diff_color.isVisible() is False
    assert panel.lbl_diff_custom.isVisible() is False

    panel.combo_diff_colormap.setCurrentIndex(panel.combo_diff_colormap.findData("custom"))
    assert panel.btn_diff_color.isVisible() is True
    assert panel.lbl_diff_custom.isVisible() is True

    panel.combo_ov_method.setCurrentIndex(panel.combo_ov_method.findData("tint"))
    assert panel.row_opacity_widget.isVisible() is False
    assert panel.spin_ov_gain.isVisible() is False
    assert panel.combo_diff_colormap.isVisible() is False
    assert panel.btn_diff_color.isVisible() is False
    assert panel.combo_ov_tint.isVisible() is True

    # Test controller apply_settings for overlay with difference colormap
    new_ov = OverlayConfig(
        enabled=True,
        method="difference",
        gain=4.0,
        diff_colormap="heat",
        diff_custom_color="#00FF88",
    )
    controller.apply_settings("overlay", new_ov)
    assert controller.project.overlay.enabled is True
    assert controller.project.overlay.method == "difference"
    assert controller.project.overlay.diff_colormap == "heat"
    assert controller.project.overlay.diff_custom_color == "#00FF88"


def test_overlay_canvas_and_renderer_rendering(qtbot):
    player = SyncPlayer()
    canvas = PreviewCanvas(player)
    qtbot.addWidget(canvas)
    canvas.resize(800, 600)

    v1 = Video(path="C:/v1.mp4", width=1920, height=1080, duration_ms=4000, fps=30.0)
    v2 = Video(path="C:/v2.mp4", width=1920, height=1080, duration_ms=4000, fps=30.0)

    for method in ("blend", "tint", "difference"):
        proj = Project(
            videos=[v1, v2],
            overlay=OverlayConfig(
                enabled=True,
                base_video_id=v1.id,
                overlay_video_id=v2.id,
                method=method,
                opacity=0.5,
                gain=3.0,
            ),
        )
        canvas.set_project(proj)
        # Verify DecorationRenderer handles overlay mode
        renderer = DecorationRenderer(proj, [])
        img = renderer.image()
        assert not img.isNull()
        assert img.width() == 1920
        assert img.height() == 1080

        # Verify QPainter drawing canvas without exceptions
        test_img = QImage(800, 600, QImage.Format.Format_ARGB32_Premultiplied)
        test_img.fill(Qt.GlobalColor.black)
        p = QPainter(test_img)
        canvas._draw_overlay(p, 1000)
        p.end()

    # Test all difference colormaps in preview canvas
    for cmap in ("grayscale", "heat", "jet", "green", "magenta", "custom"):
        proj = Project(
            videos=[v1, v2],
            overlay=OverlayConfig(
                enabled=True,
                base_video_id=v1.id,
                overlay_video_id=v2.id,
                method="difference",
                gain=4.0,
                diff_colormap=cmap,
                diff_custom_color="#FF8800",
            ),
        )
        canvas.set_project(proj)
        test_img = QImage(800, 600, QImage.Format.Format_ARGB32_Premultiplied)
        test_img.fill(Qt.GlobalColor.black)
        p = QPainter(test_img)
        canvas._draw_overlay(p, 1000)
        p.end()
