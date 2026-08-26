"""Count mapped vs unknown Batool PUA codes on dictionary pages.

  py -3 scripts/census_batool.py
  py -3 scripts/census_batool.py 25 80
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "decode" / "batool_pua_seed.json"
PDF = ROOT / "pdfs/anjumshanasi/Gojri-English-Dictionary.pdf"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    pua = json.loads(SEED.read_text(encoding="utf-8"))["map"]
    doc = fitz.open(PDF)
    print(f"table size {len(pua)}")
    print("page unique mapped unknown")
    all_seen: set[str] = set()
    all_unk: set[str] = set()
    start, end = 25, 40
    if len(sys.argv) >= 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    for page_1idx in range(start, end + 1):
        seen: set[str] = set()
        unk: set[str] = set()
        page = doc[page_1idx - 1]
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
                        seen.add(key)
                        all_seen.add(key)
                        if key not in pua:
                            unk.add(key)
                            all_unk.add(key)
        print(
            f"{page_1idx:3} {len(seen):3} {len(seen) - len(unk):3} "
            f"{len(unk):3} {' '.join(sorted(unk))}"
        )
    print(
        f"pages {start}-{end} unique Batool {len(all_seen)} "
        f"still unknown {len(all_unk)} {' '.join(sorted(all_unk))}"
    )


if __name__ == "__main__":
    main()
