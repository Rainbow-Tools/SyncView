"""Package a local portable candidate; publishing a release is a separate action."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def package_portable(root: Path) -> Path:
    bundle = root / "dist/portable/SyncView"
    if not (bundle / "SyncView.exe").is_file():
        raise FileNotFoundError("Build the onedir application before packaging.")
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(root / name, bundle / name)
    shutil.copytree(root / "licenses", bundle / "licenses", dirs_exist_ok=True)
    shutil.copy2(root / "docs/QUICKSTART.md", bundle / "START_HERE.md")
    (bundle / "docs").mkdir(exist_ok=True)
    shutil.copy2(root / "docs/LICENSING.md", bundle / "docs/LICENSING.md")
    (bundle / "vendor/ffmpeg").mkdir(parents=True, exist_ok=True)
    for name in ("LICENSE", "README.md"):
        shutil.copy2(root / "vendor/ffmpeg" / name, bundle / "vendor/ffmpeg" / name)
    (bundle / "Software decoding.cmd").write_text(
        '@echo off\nstart "" "%~dp0SyncView.exe" --software-decode\n', encoding="ascii"
    )

    # Include the application's buildable source snapshot, not private media or caches.
    source_files = {
        root / name
        for name in (
            "pyproject.toml",
            "constraints.txt",
            "VideoMultiView.spec",
            "LICENSE",
            "THIRD_PARTY_NOTICES.md",
            "README.md",
            "README.en.md",
            "AGENTS.md",
            ".gitignore",
        )
    }
    for directory, suffixes in (
        ("src/videos_multi_view", {".py", ".png", ".ico"}),
        ("tests", {".py"}),
        ("scripts", {".py", ".ps1"}),
        ("docs", {".md", ".png"}),
        ("licenses", {".txt", ".md"}),
    ):
        source_files.update(
            path
            for path in (root / directory).rglob("*")
            if path.is_file() and path.suffix in suffixes and "__pycache__" not in path.parts
        )
    source_files.update((root / "vendor/ffmpeg/LICENSE", root / "vendor/ffmpeg/README.md"))
    with ZipFile(bundle / "SyncView-source.zip", "w", ZIP_DEFLATED) as archive:
        for path in sorted(source_files):
            archive.write(path, path.relative_to(root).as_posix())

    revision = None
    dirty = None
    if shutil.which("git"):
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True
        )
        if result.returncode == 0:
            revision = result.stdout.strip()
            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=root,
                capture_output=True,
                text=True,
                check=True,
            )
            dirty = bool(status.stdout.strip())
    config = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = {
        "name": "SyncView",
        "version": config["project"]["version"],
        "revision": revision,
        "working_tree_modified": dirty,
        "python": sys.version.split()[0],
        "languages": ["ko", "en"],
        "binary_license_review_complete": False,
        "source_scope": "Application source only; external corresponding sources still required.",
        "files": {
            path.relative_to(bundle).as_posix(): sha256(path)
            for path in sorted(bundle.rglob("*"))
            if path.is_file() and path.name != "build-info.json"
        },
    }
    (bundle / "build-info.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    target = root / "dist/SyncView-windows-x64-portable.zip"
    temporary = target.with_suffix(".zip.tmp")
    try:
        with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
            for path in sorted(bundle.rglob("*")):
                if path.is_file():
                    archive.write(path, "SyncView/" + path.relative_to(bundle).as_posix())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    target.with_suffix(".zip.sha256").write_text(
        f"{sha256(target)}  {target.name}\n", encoding="ascii"
    )
    return target


if __name__ == "__main__":
    print(package_portable(Path(__file__).resolve().parents[1]))
