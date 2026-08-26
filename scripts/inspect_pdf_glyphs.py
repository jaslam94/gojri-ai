"""Read-only dump of (font, codepoint) sequences from a PDF page.

This is the first decode-table spike step: see what the PDF actually stores
before we try any mapping table.

Usage:
  py -3 scripts/inspect_pdf_glyphs.py pdfs/anjumshanasi/Gojri-English-Dictionary.pdf 25
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent


def classify_ord(o: int) -> str:
    if 0xE000 <= o <= 0xF8FF:
        return "pua"
    if 0x0600 <= o <= 0x06FF or 0x0750 <= o <= 0x077F or 0x08A0 <= o <= 0x08FF:
        return "arabic"
    if 0x0900 <= o <= 0x097F:
        return "devanagari"
    if 32 <= o < 127:
        return "ascii"
    if o == 0xFFFD:
        return "replacement"
    return "other"


def extract_chars(page: fitz.Page) -> list[dict]:
    data = page.get_text("rawdict", flags=0)
    out = []
    for block in data["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                font = span.get("font", "")
                size = span.get("size")
                for ch in span["chars"]:
                    c = ch["c"]
                    o = ord(c) if c else -1
                    x0, y0, x1, y1 = ch["bbox"]
                    out.append(
                        {
                            "font": font,
                            "size": size,
                            "char": c,
                            "ord": o,
                            "bucket": classify_ord(o),
                            "x": round(x0, 1),
                            "y": round(y0, 1),
                            "w": round(x1 - x0, 1),
                        }
                    )
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf")
    parser.add_argument("page", type=int, help="1-based page number")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    path = Path(args.pdf)
    if not path.is_absolute():
        path = ROOT / path
    doc = fitz.open(path)
    page = doc[args.page - 1]
    print(f"file: {path.relative_to(ROOT).as_posix()}")
    print(f"page: {args.page}  size: {page.rect}")
    print("fonts:")
    for item in page.get_fonts():
        xref, ext, ftype, name, encoding = item[0], item[1], item[2], item[3], item[5]
        obj = doc.xref_object(xref)
        has_tu = "/ToUnicode" in obj
        print(
            f"  {name:40} type={ftype} enc={encoding} "
            f"ToUnicode={has_tu} xref={xref}"
        )

    chars = extract_chars(page)
    print(f"\nextracted chars: {len(chars)}")
    print(f"unique (font, ord): {len({(c['font'], c['ord']) for c in chars})}")
    print("buckets:", dict(Counter(c["bucket"] for c in chars)))
    print("top fonts:", Counter(c["font"] for c in chars).most_common(8))
    print("top ords:", Counter(c["ord"] for c in chars).most_common(12))
    print(f"\nfirst {args.limit} glyphs (visual left-to-right, as stored):")
    for i, c in enumerate(chars[: args.limit], 1):
        print(
            f"{i:3} U+{c['ord']:04X} {c['char']!r:8} "
            f"{c['bucket']:11} {c['font']:28} x={c['x']:6} y={c['y']:6} w={c['w']:5}"
        )


if __name__ == "__main__":
    main()
