"""Decode Batool-PUA PDF pages to Unicode text files.

  py -3 scripts/decode_batool.py 25
  py -3 scripts/decode_batool.py 25 40
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_batool_lines import (
    ROOT,
    cluster_rows,
    fmt_line,
    load_map,
    page_chars,
)

PDF = ROOT / "pdfs/anjumshanasi/Gojri-English-Dictionary.pdf"
OUT = ROOT / "data" / "decode" / "out" / "gojri-english-dictionary"


def decode_page(page: fitz.Page, pua_map: dict[str, str]) -> str:
    rows = cluster_rows(page_chars(page))
    lines = []
    for _y, chars in rows:
        text = fmt_line(chars, pua_map, wrap_batool=False).strip()
        if text:
            lines.append(text)
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("usage: py -3 scripts/decode_batool.py START [END]")
        sys.exit(2)
    start = int(sys.argv[1])
    end = int(sys.argv[2]) if len(sys.argv) > 2 else start
    pua_map = load_map()
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    end = min(end, doc.page_count)
    for page_1idx in range(start, end + 1):
        text = decode_page(doc[page_1idx - 1], pua_map)
        path = OUT / f"page-{page_1idx:04d}.txt"
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(ROOT).as_posix()} ({len(text)} chars)")


if __name__ == "__main__":
    main()
