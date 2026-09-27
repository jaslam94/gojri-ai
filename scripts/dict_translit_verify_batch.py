"""Build a human verification batch from pass-1 transliteration.

Usage:
    py -3 scripts/dict_translit_verify_batch.py --pages 19 31 167 --limit 50
    py -3 scripts/dict_translit_verify_batch.py --pages 19 --out pass_verify_page19.tsv
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dict_translit_common import TRANSLIT_DIR, read_tsv, write_tsv

ROOT = Path(__file__).resolve().parent.parent
PASS1 = TRANSLIT_DIR / "pass1_aksharamukha.tsv"
PASS2 = TRANSLIT_DIR / "pass2_gemini.tsv"

VERIFY_FIELDS = [
    "entry_id",
    "page",
    "line",
    "devanagari",
    "roman",
    "raw_line",
    "nastaliq_pass1",
    "nastaliq_pass2",
    "nastaliq_verified",
    "verify_status",
    "verify_notes",
]


def main() -> None:
    p = argparse.ArgumentParser(description="Build a verification batch TSV from pass 1")
    p.add_argument("--pages", type=int, nargs="+", required=True, help="page number(s), in order")
    p.add_argument("--limit", type=int, default=0, help="max rows (0 = all from selected pages)")
    p.add_argument(
        "--out",
        type=str,
        default="",
        help="output filename under translit/ (default: pass_verify_batch.tsv)",
    )
    args = p.parse_args()

    if not PASS1.exists():
        print(f"Missing {PASS1}. Run dict_translit_pass1.py first.")
        sys.exit(1)

    rows = read_tsv(PASS1)
    pass2_by_id: dict[str, str] = {}
    if PASS2.exists():
        for row in read_tsv(PASS2):
            if row.get("nastaliq_pass2"):
                pass2_by_id[row["entry_id"]] = row["nastaliq_pass2"]

    wanted = [str(pg) for pg in args.pages]
    picked: list[dict] = []
    for page in wanted:
        page_rows = [r for r in rows if r["page"] == page]
        if not page_rows:
            print(f"Warning: no entries on page {page}")
        picked.extend(page_rows)
        if args.limit and len(picked) >= args.limit:
            picked = picked[: args.limit]
            break

    if not picked:
        print("No entries matched.")
        sys.exit(1)

    for row in picked:
        row["nastaliq_pass2"] = pass2_by_id.get(row["entry_id"], row.get("nastaliq_pass2") or "")
        row["nastaliq_verified"] = ""
        row["verify_status"] = "pending"
        row["verify_notes"] = ""

    out_name = args.out or "pass_verify_batch.tsv"
    out_path = TRANSLIT_DIR / out_name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        import csv

        w = csv.DictWriter(f, fieldnames=VERIFY_FIELDS, delimiter="\t", extrasaction="ignore")
        w.writeheader()
        w.writerows(picked)

    print(f"Wrote {len(picked)} rows to {out_path.relative_to(ROOT)}")
    by_page: dict[str, int] = {}
    for row in picked:
        by_page[row["page"]] = by_page.get(row["page"], 0) + 1
    for page in wanted:
        if page in by_page:
            print(f"  page {page}: {by_page[page]} entries")


if __name__ == "__main__":
    main()
