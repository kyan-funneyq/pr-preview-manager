"""Manage per-PR preview folders under <target>/pr-preview/."""

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

PREVIEW_DIR = "pr-preview"
MANIFEST = "previews.json"
PR_RE = re.compile(r"[1-9][0-9]*")
SHA_RE = re.compile(r"[0-9a-fA-F]{7,40}")


class ValidationError(Exception):
    """Input rejected before anything was written (exit 1)."""


class Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise ValidationError(message)


def parse_pr(value: str) -> int:
    if not PR_RE.fullmatch(value):
        raise ValidationError(f"PR must be a positive integer, got {value!r}")
    return int(value)


def parse_sha(value: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise ValidationError(f"SHA must be 7-40 hex characters, got {value!r}")
    return value


def check_source(source: Path) -> Path:
    if not source.is_dir() or source.is_symlink():
        raise ValidationError(f"source {source} is not a real folder")
    if not (source / "index.html").is_file():
        raise ValidationError(f"source {source} has no index.html")
    links = [p for p in source.rglob("*") if p.is_symlink()]
    if links:
        raise ValidationError(f"source contains symlinks: {links[0]}")
    return source


def preview_path(root: Path, pr: int) -> Path:
    """Return <root>/pr-preview/pr-<N>, rejecting anything that escapes pr-preview/."""
    base = root / PREVIEW_DIR
    if base.is_symlink():
        raise ValidationError(f"{base} is a symlink")
    dest = base / f"pr-{pr}"
    if dest.is_symlink() or not dest.resolve().is_relative_to(base.resolve()):
        raise ValidationError(f"{dest} resolves outside {base}")
    return dest


def read_manifest(root: Path) -> dict:
    path = root / PREVIEW_DIR / MANIFEST
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} is not a JSON object")
    return data


def write_manifest(root: Path, data: dict) -> None:
    path = root / PREVIEW_DIR / MANIFEST
    tmp = path.with_name(MANIFEST + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def prepare(root: Path, pr: int, sha: str, source: Path) -> Path:
    dest = preview_path(root, pr)
    manifest = read_manifest(root)  # last read-only step; a bad manifest exits 2 before any write
    dest.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".staging-pr-{pr}-", dir=dest.parent))
    try:
        new, old = staging / "new", staging / "old"
        shutil.copytree(source, new)
        if dest.exists():
            dest.rename(old)
        try:
            new.rename(dest)
        except OSError:
            if old.exists():
                old.rename(dest)  # restore the previous preview
            raise
        updated_at = datetime.now(UTC).isoformat(timespec="seconds")
        manifest[str(pr)] = {"sha": sha, "updated_at": updated_at}
        write_manifest(root, manifest)
    finally:
        shutil.rmtree(staging, ignore_errors=True)  # also deletes the old preview after a swap
    return dest


def remove(root: Path, pr: int) -> str:
    dest = preview_path(root, pr)
    manifest = read_manifest(root)
    if not dest.exists() and str(pr) not in manifest:
        return "absent"
    if dest.exists():
        shutil.rmtree(dest)
    manifest.pop(str(pr), None)
    write_manifest(root, manifest)
    return "removed"


def status(root: Path) -> list[str]:
    manifest = read_manifest(root)
    base = root / PREVIEW_DIR
    lines = []
    for pr, entry in sorted(manifest.items(), key=lambda kv: int(kv[0])):
        folder = "ok" if (base / f"pr-{pr}").is_dir() else "missing"
        lines.append(f"pr={pr} sha={entry['sha']} updated_at={entry['updated_at']} folder={folder}")
    if base.is_dir():
        for d in sorted(base.glob("pr-*")):
            if d.is_dir() and d.name.removeprefix("pr-") not in manifest:
                lines.append(f"{d.name} folder=untracked")
    return lines


def build_parser() -> Parser:
    parser = Parser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="add or replace one PR's preview")
    p.add_argument("--pr", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--target", type=Path, required=True)
    r = sub.add_parser("remove", help="delete one PR's preview and manifest entry")
    r.add_argument("--pr", required=True)
    r.add_argument("--target", type=Path, required=True)
    s = sub.add_parser("status", help="list previews in the manifest")
    s.add_argument("--target", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.command == "prepare":
            pr, sha = parse_pr(args.pr), parse_sha(args.sha)
            dest = prepare(args.target, pr, sha, check_source(args.source))
            print(f"prepare pr={pr} sha={sha} path={dest} result=ok")
        elif args.command == "remove":
            pr = parse_pr(args.pr)
            print(f"remove pr={pr} result={remove(args.target, pr)}")
        elif args.command == "status":
            lines = status(args.target)
            if lines:
                print("\n".join(lines))
            print(f"status previews={sum(line.startswith('pr=') for line in lines)} result=ok")
    except ValidationError as exc:
        print(f"rejected: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # any unexpected failure maps to exit 2
        print(f"error: {exc!r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
