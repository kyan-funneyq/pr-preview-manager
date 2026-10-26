import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import previewctl

REPO_ROOT = Path(__file__).resolve().parent.parent


def tree_hash(root: Path) -> str:
    """Hash every path, file content and symlink target under root."""
    h = hashlib.sha256()
    for p in sorted(root.rglob("*")):
        h.update(p.relative_to(root).as_posix().encode())
        if p.is_symlink():
            h.update(b"link:" + os.readlink(p).encode())
        elif p.is_file():
            h.update(p.read_bytes())
    return h.hexdigest()


@pytest.fixture
def make_source(tmp_path):
    def _make(name: str, body: str = "hello") -> Path:
        d = tmp_path / name
        d.mkdir()
        (d / "index.html").write_text(body, encoding="utf-8")
        return d

    return _make


def run(*args) -> int:
    return previewctl.main([str(a) for a in args])


def manifest(root: Path) -> dict:
    return json.loads((root / "pr-preview" / "previews.json").read_text(encoding="utf-8"))


def test_prepare_creates_preview_and_manifest(tmp_path, make_source):
    root = tmp_path / "root"
    src = make_source("src", body="<p>pr one</p>")

    assert run("prepare", "--pr", 1, "--sha", "a1b2c3d", "--source", src, "--target", root) == 0

    index = root / "pr-preview" / "pr-1" / "index.html"
    assert index.read_text(encoding="utf-8") == "<p>pr one</p>"
    assert manifest(root)["1"]["sha"] == "a1b2c3d"


@pytest.mark.parametrize("pr", ["0", "-1", "abc", "1.5"])
def test_rejects_bad_pr(tmp_path, make_source, pr):
    root = tmp_path / "root"
    src = make_source("src")

    assert run("prepare", "--pr", pr, "--sha", "a1b2c3d", "--source", src, "--target", root) == 1
    assert not (root / "pr-preview").exists()


@pytest.mark.parametrize("sha", ["abc12", "zzzzzzz", "a" * 41])
def test_rejects_bad_sha(tmp_path, make_source, sha):
    root = tmp_path / "root"
    src = make_source("src")

    assert run("prepare", "--pr", 1, "--sha", sha, "--source", src, "--target", root) == 1
    assert not (root / "pr-preview").exists()


def test_rejects_missing_index(tmp_path):
    root = tmp_path / "root"
    src = tmp_path / "src"
    src.mkdir()

    assert run("prepare", "--pr", 1, "--sha", "a1b2c3d", "--source", src, "--target", root) == 1
    assert not (root / "pr-preview").exists()


def test_cli_entrypoint_exit_code(tmp_path, make_source):
    src = make_source("src")
    cmd = [
        sys.executable, str(REPO_ROOT / "src" / "previewctl.py"), "prepare",
        "--pr", "abc", "--sha", "a1b2c3d", "--source", str(src), "--target", str(tmp_path / "root"),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    assert result.returncode == 1
    assert "rejected:" in result.stderr
