from pathlib import Path

import pytest

from videos_multi_view.media.probe import probe


@pytest.mark.local_assets
def test_private_inputs(request):
    if not request.config.getoption("--local-assets"):
        pytest.skip("Use --local-assets for optional private inputs")
    paths = list(Path("test_assets").glob("*.mp4"))
    if not paths:
        pytest.skip("No private input videos available")
    for path in paths:
        video = probe(str(path.resolve()))
        assert video.width > 0 and video.height > 0
        assert video.duration_ms > 0
