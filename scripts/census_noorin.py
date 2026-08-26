"""Count mapped vs unknown NOORIN keys on a PUA PDF.

Key is FONT:CODE. Do not use the Batool table.

  py -3 scripts/census_noorin.py 50 50
  py -3 scripts/census_noorin.py 1 169
  py -3 scripts/census_noorin.py 1 20 pdfs/gojri-dictionary-by-dr-javaid-rahi-3.pdf
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "decode" / "noorin_pua_seed.json"
PDF = ROOT / "pdfs/anjumshanasi/Kahawat-Kosh.pdf"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_noorin_lines import is_noorin, is_overlay_font, map_key


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    pua = json.loads(SEED.read_text(encoding="utf-8")).get("map", {})
    start, end = 50, 50
    pdf = PDF
    if len(sys.argv) >= 3:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    if len(sys.argv) >= 4:
        pdf = Path(sys.argv[3])
        if not pdf.is_absolute():
            pdf = ROOT / pdf
    print(f"pdf {pdf.relative_to(ROOT).as_posix() if pdf.is_relative_to(ROOT) else pdf}")
    print(f"table size {len(pua)}")
    print("page unique mapped unknown inst_unk")
    all_seen: set[str] = set()
    all_unk: set[str] = set()
    unk_inst: Counter[str] = Counter()
    first_page: dict[str, int] = {}
    mapped_n = 0
    unk_n = 0
    doc = fitz.open(pdf)
    end = min(end, doc.page_count)
    for page_1idx in range(start, end + 1):
        seen: set[str] = set()
        unk: set[str] = set()
        page_unk_n = 0
        data = doc[page_1idx - 1].get_text("rawdict", flags=0)
        for block in data["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    font = span.get("font", "")
                    if not is_noorin(font):
                        continue
                    for ch in span["chars"]:
                        key = map_key(font, ord(ch["c"]))
                        seen.add(key)
                        all_seen.add(key)
                        if key not in pua:
                            unk.add(key)
                            all_unk.add(key)
                            unk_inst[key] += 1
                            page_unk_n += 1
                            unk_n += 1
                            first_page.setdefault(key, page_1idx)
                        else:
                            mapped_n += 1
        print(
            f"{page_1idx:3} {len(seen):3} {len(seen) - len(unk):3} "
            f"{len(unk):3} {page_unk_n:5}"
        )
    total = mapped_n + unk_n
    pct = (100.0 * mapped_n / total) if total else 0.0
    print(
        f"pages {start}-{end} unique keys {len(all_seen)} "
        f"still unknown {len(all_unk)}"
    )
    print(
        f"instances mapped {mapped_n} unknown {unk_n} "
        f"mapped_pct {pct:.1f}"
    )
    overlay_n = sum(
        n for k, n in unk_inst.items() if is_overlay_font(k.split(":")[0])
    )
    overlay_u = sum(
        1 for k in all_unk if is_overlay_font(k.split(":")[0])
    )
    print(f"unknown overlay unique {overlay_u} instances {overlay_n}")
    once = sum(1 for n in unk_inst.values() if n == 1)
    twice = sum(1 for n in unk_inst.values() if n == 2)
    print(f"unknown appear once {once} twice {twice}")
    print("top unknown keys (instances, first page)")
    for key, n in unk_inst.most_common(40):
        kind = "overlay" if is_overlay_font(key.split(":")[0]) else "base"
        print(f"{n:5} p{first_page[key]:03d} {kind:7} {key}")


if __name__ == "__main__":
    main()
