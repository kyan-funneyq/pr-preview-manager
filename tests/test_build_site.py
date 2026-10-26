from pathlib import Path

import build_site


def test_fills_placeholders(tmp_path: Path) -> None:
    out = tmp_path / "out"

    assert build_site.main(["--pr", "7", "--sha", "abcdef1", "--out", str(out)]) == 0

    index = (out / "index.html").read_text(encoding="utf-8")
    assert "#7" in index
    assert "abcdef1" in index
    for path in out.rglob("*"):
        if path.suffix in {".html", ".css"}:
            assert "{{" not in path.read_text(encoding="utf-8"), path


def test_refuses_non_empty_out(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    keep = out / "keep.txt"
    keep.write_text("do not touch", encoding="utf-8")

    assert build_site.main(["--pr", "7", "--sha", "abcdef1", "--out", str(out)]) == 1

    assert keep.read_text(encoding="utf-8") == "do not touch"
    assert not (out / "index.html").exists()
