"""Crop first occurrence of unknown Batool codes on a page.

  py -3 scripts/crop_unknown_batool.py 27
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "decode" / "batool_pua_seed.json"
PDF = ROOT / "pdfs/anjumshanasi/Gojri-English-Dictionary.pdf"
OUT = ROOT / "data" / "decode" / "_glyph_crops"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    page_1idx = int(sys.argv[1])
    pua = json.loads(SEED.read_text(encoding="utf-8"))["map"]
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)
    page = doc[page_1idx - 1]
    zoom = 6
    first: dict[str, tuple[float, float, float, float]] = {}
    data = page.get_text("rawdict", flags=0)
    for block in data["blocks"]:
        if block.get("type") != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                if "Batool" not in span.get("font", ""):
                    continue
                for ch in span["chars"]:
                    key = f"{ord(ch['c']):04X}"
                    if key in pua or key in first:
                        continue
                    first[key] = ch["bbox"]
    pad = 1.5
    print("unknown", sorted(first))
    for key, (x0, y0, x1, y1) in sorted(first.items()):
        clip = fitz.Rect(x0 - pad, y0 - pad, x1 + pad, y1 + pad)
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), clip=clip, alpha=False)
        path = OUT / f"p{page_1idx}_{key}.png"
        pix.save(str(path))
        print("wrote", path.name)


if __name__ == "__main__":
    main()
