"""Pass 1: Devanagari headwords → Nastaliq draft via Aksharamukha.

Usage:
    py -3 scripts/dict_translit_pass1.py              # all pages
    py -3 scripts/dict_translit_pass1.py --page 19    # one page (pilot)
    py -3 scripts/dict_translit_pass1.py --page 19 31 49
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dict_translit_common import TRANSLIT_DIR, collect_entries, write_tsv, aksharamukha_to_urdu

OUT = TRANSLIT_DIR / "pass1_aksharamukha.tsv"


def main() -> None:
    p = argparse.ArgumentParser(description="Dictionary pass 1: Aksharamukha Devanagari → Urdu")
    p.add_argument("--page", type=int, action="append", dest="pages", help="limit to page number(s)")
    args = p.parse_args()

    entries = collect_entries(args.pages)
    if not entries:
        print("No Devanagari headwords found. Check data/extracted/.../page-*.txt exists.")
        sys.exit(1)

    for row in entries:
        row["nastaliq_pass1"] = aksharamukha_to_urdu(row["devanagari"])

    write_tsv(OUT, entries)
    pages = sorted({r["page"] for r in entries})
    print(f"Wrote {len(entries)} entries from {len(pages)} page(s) to {OUT}")
    print("Sample:")
    for row in entries[:5]:
        print(f"  {row['devanagari']} ({row['roman']}) -> {row['nastaliq_pass1']}")


if __name__ == "__main__":
    main()
