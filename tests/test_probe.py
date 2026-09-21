import pytest

from videos_multi_view.media.probe import ProbeJob, parse_probe, probe


@pytest.mark.integration
def test_probe_v1(media_factory):
    v = probe(str(media_factory(fps=24, audio=True, size="96x160")))
    assert (v.width, v.height, v.fps, v.has_audio) == (96, 160, 24, True)
    assert abs(v.duration_ms - 2000) < 100


@pytest.mark.integration
def test_probe_v2(media_factory):
    v = probe(str(media_factory(fps=30, size="160x96")))
    assert (v.width, v.height, v.fps, v.has_audio) == (160, 96, 30, False)


@pytest.mark.integration
def test_probe_job_async(qtbot, clip):
    job = ProbeJob(str(clip))
    with qtbot.waitSignal(job.succeeded, timeout=5000) as result:
        job.start()
    assert result.args[0].width == 160


@pytest.mark.parametrize("average", ["0/0", "N/A", None, "0", "nan"])
def test_unknown_fps_falls_back(average):
    v = parse_probe(
        "test.mp4",
        {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 160,
                    "height": 96,
                    "duration": "N/A",
                    "avg_frame_rate": average,
                    "r_frame_rate": "24000/1001",
                }
            ],
            "format": {"duration": "2"},
        },
    )
    assert abs(v.fps - 23.976) < 0.001
    assert v.duration_ms == 2000


@pytest.mark.parametrize("duration", ["0", "-1", "N/A", "nan", "inf", None])
def test_invalid_duration_is_rejected(duration):
    with pytest.raises(ValueError, match="길이"):
        parse_probe(
            "test.mp4",
            {
                "streams": [
                    {
                        "codec_type": "video",
                        "width": 160,
                        "height": 96,
                        "duration": duration,
                    }
                ]
            },
        )


def test_rotation_and_sar():
    v = parse_probe(
        "test.mp4",
        {
            "streams": [
                {
                    "codec_type": "video",
                    "width": 160,
                    "height": 96,
                    "duration": "2",
                    "sample_aspect_ratio": "2:1",
                    "side_data_list": [{"rotation": 90}],
                }
            ]
        },
    )
    assert v.display_aspect == pytest.approx(0.3)


@pytest.mark.integration
def test_corrupt_file(qtbot, tmp_path):
    path = tmp_path / "broken.mp4"
    path.write_bytes(b"not a video")
    job = ProbeJob(str(path))
    with qtbot.waitSignal(job.failed, timeout=5000):
        job.start()
