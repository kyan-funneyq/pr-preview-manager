"""Manage per-PR preview folders under <target>/pr-preview/."""

import argparse
import json
import os
import re
import shutil
import sys
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
    if not source.is_dir():
        raise ValidationError(f"source {source} is not a folder")
    if not (source / "index.html").is_file():
        raise ValidationError(f"source {source} has no index.html")
    return source


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
    dest = root / PREVIEW_DIR / f"pr-{pr}"
    manifest = read_manifest(root)
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    manifest[str(pr)] = {"sha": sha, "updated_at": datetime.now(UTC).isoformat(timespec="seconds")}
    write_manifest(root, manifest)
    return dest


def build_parser() -> Parser:
    parser = Parser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("prepare", help="add or replace one PR's preview")
    p.add_argument("--pr", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--target", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
        if args.command == "prepare":
            pr, sha = parse_pr(args.pr), parse_sha(args.sha)
            dest = prepare(args.target, pr, sha, check_source(args.source))
            print(f"prepare pr={pr} sha={sha} path={dest} result=ok")
    except ValidationError as exc:
        print(f"rejected: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # any unexpected failure maps to exit 2
        print(f"error: {exc!r}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
