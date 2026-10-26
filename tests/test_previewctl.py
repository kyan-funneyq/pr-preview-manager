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


# --- Phase 3: isolation, update, remove, rejection without side effects (AC3-AC5) ---


@pytest.fixture
def two_previews(tmp_path, make_source) -> Path:
    root = tmp_path / "root"
    v1 = make_source("v1", body="<p>pr one</p>")
    v2 = make_source("v2", body="<p>pr two</p>")
    assert run("prepare", "--pr", 1, "--sha", "aaaaaaa", "--source", v1, "--target", root) == 0
    assert run("prepare", "--pr", 2, "--sha", "bbbbbbb", "--source", v2, "--target", root) == 0
    return root


def test_update_one_leaves_other_identical(two_previews, make_source):
    root = two_previews
    pr2_before = tree_hash(root / "pr-preview" / "pr-2")
    entry2 = manifest(root)["2"]
    v1b = make_source("v1b", body="<p>pr one, updated</p>")

    assert run("prepare", "--pr", 1, "--sha", "ccccccc", "--source", v1b, "--target", root) == 0

    assert tree_hash(root / "pr-preview" / "pr-2") == pr2_before
    assert manifest(root)["2"] == entry2


def test_update_replaces_files_and_sha(tmp_path, make_source):
    root = tmp_path / "root"
    v1 = make_source("v1", body="old")
    (v1 / "old.txt").write_text("stale", encoding="utf-8")
    assert run("prepare", "--pr", 1, "--sha", "aaaaaaa", "--source", v1, "--target", root) == 0
    v2 = make_source("v2", body="new")

    assert run("prepare", "--pr", 1, "--sha", "ccccccc", "--source", v2, "--target", root) == 0

    preview = root / "pr-preview" / "pr-1"
    assert not (preview / "old.txt").exists()
    assert (preview / "index.html").read_text(encoding="utf-8") == "new"
    assert manifest(root)["1"]["sha"] == "ccccccc"
    assert not list((root / "pr-preview").glob(".staging-*"))


def test_remove_leaves_other(two_previews):
    root = two_previews
    pr2_before = tree_hash(root / "pr-preview" / "pr-2")
    entry2 = manifest(root)["2"]

    assert run("remove", "--pr", 1, "--target", root) == 0

    assert not (root / "pr-preview" / "pr-1").exists()
    assert "1" not in manifest(root)
    assert tree_hash(root / "pr-preview" / "pr-2") == pr2_before
    assert manifest(root)["2"] == entry2


def test_remove_missing_succeeds(two_previews, capsys):
    root = two_previews
    before = tree_hash(root)

    assert run("remove", "--pr", 99, "--target", root) == 0

    assert "remove pr=99 result=absent" in capsys.readouterr().out
    assert tree_hash(root) == before


def prepare_args(root: Path, source: Path, pr: str = "3", sha: str = "ccccccc") -> list:
    return ["prepare", "--pr", pr, "--sha", sha, "--source", source, "--target", root]


def _source_missing(tmp_path, root, make_source):
    return prepare_args(root, tmp_path / "does-not-exist")


def _source_no_index(tmp_path, root, make_source):
    src = tmp_path / "no-index"
    src.mkdir()
    (src / "page.html").write_text("x", encoding="utf-8")
    return prepare_args(root, src)


def _source_has_symlink(tmp_path, root, make_source):
    src = make_source("leaky")
    secret = tmp_path / "secret.txt"
    secret.write_text("do not publish", encoding="utf-8")
    os.symlink(secret, src / "leak.txt")
    return prepare_args(root, src)


def _source_is_symlink(tmp_path, root, make_source):
    link = tmp_path / "linked-src"
    os.symlink(make_source("real-src"), link)
    return prepare_args(root, link)


def _preview_folder_symlink_outside(tmp_path, root, make_source):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("outside the root", encoding="utf-8")
    os.symlink(outside, root / "pr-preview" / "pr-3")
    return prepare_args(root, make_source("new"))


INVALID_CASES = {
    "pr-zero": lambda t, r, m: prepare_args(r, m("new"), pr="0"),
    "pr-negative": lambda t, r, m: prepare_args(r, m("new"), pr="-1"),
    "pr-not-a-number": lambda t, r, m: prepare_args(r, m("new"), pr="abc"),
    "sha-too-short": lambda t, r, m: prepare_args(r, m("new"), sha="abc12"),
    "sha-not-hex": lambda t, r, m: prepare_args(r, m("new"), sha="zzzzzzz"),
    "sha-too-long": lambda t, r, m: prepare_args(r, m("new"), sha="a" * 41),
    "source-missing": _source_missing,
    "source-no-index": _source_no_index,
    "source-has-symlink": _source_has_symlink,
    "source-is-symlink": _source_is_symlink,
    "preview-folder-symlink-outside": _preview_folder_symlink_outside,
}


@pytest.mark.parametrize("case", INVALID_CASES)
def test_invalid_input_changes_nothing(tmp_path, two_previews, make_source, case):
    args = INVALID_CASES[case](tmp_path, two_previews, make_source)
    # Hash everything under tmp_path: the preview root and any folder outside it.
    before = tree_hash(tmp_path)

    assert run(*args) == 1

    assert tree_hash(tmp_path) == before


def test_symlinked_preview_dir_rejected(tmp_path, make_source):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "keep.txt").write_text("outside the root", encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    os.symlink(outside, root / "pr-preview")
    src = make_source("new")
    before = tree_hash(tmp_path)

    assert run(*prepare_args(root, src, pr="1")) == 1
    assert run("remove", "--pr", 1, "--target", root) == 1

    assert tree_hash(tmp_path) == before


def test_swap_failure_restores_old(two_previews, make_source, monkeypatch):
    root = two_previews
    v1b = make_source("v1b", body="new")
    before = tree_hash(root)
    real_rename = Path.rename

    def failing_rename(self, target):
        if self.name == "new":
            raise OSError("simulated rename failure")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", failing_rename)
    assert run("prepare", "--pr", 1, "--sha", "ccccccc", "--source", v1b, "--target", root) == 2
    monkeypatch.undo()

    assert tree_hash(root) == before


def test_malformed_manifest_exits_2(two_previews, make_source):
    root = two_previews
    (root / "pr-preview" / "previews.json").write_text("[]", encoding="utf-8")
    src = make_source("new")
    before = tree_hash(root)

    assert run(*prepare_args(root, src)) == 2

    assert tree_hash(root) == before


def test_status_lists_previews(two_previews, capsys):
    capsys.readouterr()

    assert run("status", "--target", two_previews) == 0

    out = capsys.readouterr().out
    assert "pr=1 sha=aaaaaaa" in out
    assert "pr=2 sha=bbbbbbb" in out
    assert "status previews=2 result=ok" in out


def test_status_flags_untracked_folder(two_previews, capsys):
    (two_previews / "pr-preview" / "pr-9").mkdir()
    capsys.readouterr()

    assert run("status", "--target", two_previews) == 0

    assert "pr-9 folder=untracked" in capsys.readouterr().out


def test_prepare_logs_one_line(tmp_path, make_source, capsys):
    src = make_source("src")
    root = tmp_path / "root"

    assert run("prepare", "--pr", 1, "--sha", "a1b2c3d", "--source", src, "--target", root) == 0

    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 1
    assert lines[0].startswith("prepare pr=1 sha=a1b2c3d ")
