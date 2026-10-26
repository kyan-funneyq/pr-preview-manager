"""Render site/ into an output folder, filling in {{PR}} and {{SHA}}."""

import argparse
import shutil
import sys
from pathlib import Path

SITE_DIR = Path(__file__).resolve().parent.parent / "site"
TEXT_SUFFIXES = {".html", ".css"}


def build(pr: int, sha: str, out: Path, site: Path = SITE_DIR) -> None:
    shutil.copytree(site, out, dirs_exist_ok=True)
    for path in out.rglob("*"):
        if path.suffix in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8")
            text = text.replace("{{PR}}", str(pr)).replace("{{SHA}}", sha)
            path.write_text(text, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr", type=int, required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    if args.out.exists() and any(args.out.iterdir()):
        print(f"error: output folder {args.out} is not empty", file=sys.stderr)
        return 1
    build(args.pr, args.sha, args.out)
    print(f"build pr={args.pr} sha={args.sha} out={args.out} result=ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
