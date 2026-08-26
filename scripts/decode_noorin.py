"""Decode Kahawat-Kosh NOORIN pages to Unicode text.

  py -3 scripts/decode_noorin.py 50
  py -3 scripts/decode_noorin.py 50 60
"""

from __future__ import annotations

import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_noorin_lines import (
    COL_SPLIT,
    PDF,
    ROOT,
    attach_overlays,
    cluster_rows,
    fmt_run,
    is_noorin,
    is_overlay_font,
    load_map,
    page_chars,
)

OUT = ROOT / "data" / "decode" / "out" / "kahawat-kosh"


def decode_page(page: fitz.Page, pua_map: dict[str, str]) -> str:
    chars = page_chars(page)
    noorin = [c for c in chars if is_noorin(c[3])]
    base = [c for c in noorin if not is_overlay_font(c[3])]
    overlays = [c for c in noorin if is_overlay_font(c[3])]
    rows = cluster_rows(base)
    attached = attach_overlays(rows, overlays)
    lines = []
    for (_y, _row), row_all in zip(rows, attached):
        left = [c for c in row_all if c[1] < COL_SPLIT]
        right = [c for c in row_all if c[1] >= COL_SPLIT]
        gojri = fmt_run(right, pua_map, row_all).strip() if right else ""
        urdu = fmt_run(left, pua_map, row_all).strip() if left else ""
        if not gojri and not urdu:
            continue
        if gojri and urdu:
            lines.append(f"{gojri}\t{urdu}")
        else:
            lines.append(gojri or urdu)
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print("usage: py -3 scripts/decode_noorin.py START [END]")
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
