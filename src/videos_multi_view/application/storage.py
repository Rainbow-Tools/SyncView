import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from videos_multi_view.core.layout import calculate_layout
from videos_multi_view.core.models import Label, Layout, Output, OverlayConfig, Project, Video
from videos_multi_view.i18n import tr


def save_project(project: Project, path: Path) -> None:
    project.validate()
    calculate_layout(project)
    path = path.resolve()
    if any(Path(v.path).resolve() == path for v in project.videos):
        raise ValueError(tr("원본 영상을 프로젝트 파일로 덮어쓸 수 없습니다."))
    data = asdict(project)
    for item in data["videos"]:
        try:
            item["path"] = os.path.relpath(item["path"], path.parent)
        except ValueError:
            item["path"] = str(Path(item["path"]).resolve())
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, suffix=".tmp", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary:
            temporary.unlink(missing_ok=True)


def load_project(path: Path) -> Project:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("version") != 1:
            raise ValueError(tr("지원하지 않는 프로젝트 버전입니다."))
        videos = []
        for item in data["videos"]:
            item = dict(item)
            item["label"] = Label(**item["label"])
            source = Path(item["path"])
            item["path"] = str((path.parent / source).resolve())
            videos.append(Video(**item))
        overlay_data = data.get("overlay")
        overlay = OverlayConfig(**overlay_data) if overlay_data else OverlayConfig()
        project = Project(
            videos=videos,
            layout=Layout(**data["layout"]),
            output=Output(**data["output"]),
            overlay=overlay,
            audio_id=data.get("audio_id"),
            version=data["version"],
        )
        project.validate()
        calculate_layout(project)
        return project
    except (KeyError, TypeError, AttributeError, OverflowError) as exc:
        raise ValueError(tr("프로젝트 파일의 구조가 올바르지 않습니다.")) from exc
