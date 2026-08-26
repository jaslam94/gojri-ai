"""Measure Kahawat NOORIN table transfer onto other PUA PDFs.

Reads data/manifest.csv. Reports mapped instance % per book.
Skips Batool-font dictionaries (separate table).

  py -3 scripts/census_noorin_transfer.py
  py -3 scripts/census_noorin_transfer.py --decode --skip-census --min-pct 87 --batch-size 3
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.csv"
OUT_CSV = ROOT / "data" / "decode" / "noorin_transfer.csv"
PROGRESS_JSON = ROOT / "data" / "decode" / "transfer_decode_progress.json"
OUT_ROOT = ROOT / "data" / "decode" / "out"
PDF_DIR = ROOT / "pdfs"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from decode_noorin_flow import slug_from_pdf
from dump_noorin_lines import is_noorin, is_overlay_font, load_map, map_key

BATOOL_ONLY = {
    "anjumshanasi/Gojri-English-Dictionary.pdf",
    "Concise_Gojri_English_Dictionary_by_Dr_R.pdf",
}

SKIP_DECODE = {
    "anjumshanasi/Kahawat-Kosh.pdf",
}


def census_book(pdf: Path, pua: dict[str, str]) -> dict:
    doc = fitz.open(pdf)
    all_seen: set[str] = set()
    all_unk: set[str] = set()
    mapped_n = 0
    unk_n = 0
    for page in doc:
        try:
            data = page.get_text("rawdict", flags=0)
        except Exception:
            return {
                "pages": doc.page_count,
                "unique_keys": 0,
                "unknown_keys": 0,
                "mapped_n": 0,
                "unk_n": 0,
                "mapped_pct": 0.0,
                "error": "rawdict_failed",
            }
        for block in data.get("blocks", []):
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    font = span.get("font", "")
                    if not is_noorin(font):
                        continue
                    for ch in span["chars"]:
                        key = map_key(font, ord(ch["c"]))
                        all_seen.add(key)
                        if key not in pua:
                            all_unk.add(key)
                            unk_n += 1
                        else:
                            mapped_n += 1
    total = mapped_n + unk_n
    pct = (100.0 * mapped_n / total) if total else 0.0
    overlay_u = sum(
        1 for k in all_unk if is_overlay_font(k.split(":")[0])
    )
    return {
        "pages": doc.page_count,
        "unique_keys": len(all_seen),
        "unknown_keys": len(all_unk),
        "mapped_n": mapped_n,
        "unk_n": unk_n,
        "mapped_pct": round(pct, 1),
        "overlay_unknown": overlay_u,
        "error": "",
    }


def load_manifest_rows() -> list[dict]:
    with MANIFEST.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def page_count_done(slug: str) -> int:
    out = OUT_ROOT / slug
    if not out.is_dir():
        return 0
    return sum(1 for _ in out.glob("page-*.txt"))


def book_complete(slug: str, pages: int) -> bool:
    return page_count_done(slug) >= pages


def load_transfer_csv() -> list[dict]:
    with OUT_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def run_census(min_pct: float) -> list[dict]:
    pua = load_map()
    print(f"seed keys {len(pua)}")
    rows = load_manifest_rows()
    candidates = [
        r
        for r in rows
        if r.get("encoding_scheme") == "pua"
        and r.get("is_primary") == "1"
        and r.get("in_scope") == "1"
        and r.get("path", "") not in BATOOL_ONLY
    ]
    print(f"PUA books to scan: {len(candidates)}")
    print()

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out_rows: list[dict] = []

    for r in sorted(candidates, key=lambda x: x.get("path", "")):
        rel = r["path"]
        pdf = PDF_DIR / rel
        if not pdf.exists():
            print(f"SKIP missing {rel}")
            continue
        stats = census_book(pdf, pua)
        row = {
            "path": rel,
            "pages": stats["pages"],
            "tier": r.get("tier", ""),
            "unique_keys": stats["unique_keys"],
            "unknown_keys": stats["unknown_keys"],
            "mapped_instances": stats["mapped_n"],
            "unknown_instances": stats["unk_n"],
            "mapped_pct": stats["mapped_pct"],
            "overlay_unknown": stats.get("overlay_unknown", 0),
            "error": stats.get("error", ""),
        }
        out_rows.append(row)
        flag = ""
        if stats["mapped_pct"] >= 90:
            flag = " GOOD"
        elif stats["mapped_pct"] >= 50:
            flag = " PARTIAL"
        elif stats["mapped_pct"] > 0:
            flag = " LOW"
        else:
            flag = " NONE"
        print(
            f"{stats['mapped_pct']:5.1f}%  p{stats['pages']:4}  "
            f"unk {stats['unknown_keys']:4}/{stats['unique_keys']:4}  "
            f"{rel}{flag}"
        )

    fieldnames = list(out_rows[0].keys()) if out_rows else []
    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(out_rows)
    print()
    print(f"wrote {OUT_CSV.relative_to(ROOT).as_posix()}")

    good = sum(1 for r in out_rows if float(r["mapped_pct"]) >= 90)
    partial = sum(1 for r in out_rows if 50 <= float(r["mapped_pct"]) < 90)
    low = sum(1 for r in out_rows if 0 < float(r["mapped_pct"]) < 50)
    none = sum(1 for r in out_rows if float(r["mapped_pct"]) == 0)
    print(f"summary: {good} >=90%, {partial} 50-89%, {low} 1-49%, {none} 0%")
    return out_rows


def decode_queue_from_rows(rows: list[dict], min_pct: float) -> list[tuple[str, int, float, str]]:
    queue: list[tuple[str, int, float, str]] = []
    for row in rows:
        rel = row["path"]
        pct = float(row["mapped_pct"])
        pages = int(row["pages"])
        if pct <= min_pct or row.get("error") or rel in SKIP_DECODE:
            continue
        slug = slug_from_pdf(PDF_DIR / rel)
        queue.append((rel, pages, pct, slug))
    return queue


def save_progress(queue: list, batch_done: list[dict]) -> None:
    PROGRESS_JSON.parent.mkdir(parents=True, exist_ok=True)
    status = []
    for rel, pages, pct, slug in queue:
        done = page_count_done(slug)
        status.append(
            {
                "path": rel,
                "slug": slug,
                "pages": pages,
                "pages_done": done,
                "complete": done >= pages,
                "mapped_pct": pct,
            }
        )
    payload = {
        "updated": datetime.now(timezone.utc).isoformat(),
        "books": status,
        "last_batch": batch_done,
    }
    PROGRESS_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def decode_books(
    queue: list[tuple[str, int, float, str]],
    batch_size: int,
    skip_existing: bool,
) -> list[dict]:
    incomplete = [
        item for item in queue if not book_complete(item[3], item[1])
    ]
    if not incomplete:
        print("all books in queue are already complete")
        return []

    batch = incomplete[:batch_size]
    print(f"batch: {len(batch)} book(s), {len(incomplete)} still incomplete")
    batch_done: list[dict] = []

    for rel, pages, pct, slug in batch:
        done_before = page_count_done(slug)
        pdf_arg = f"pdfs/{rel}"
        print(f"decode {rel} ({done_before}/{pages} pages, {pct}%)")
        cmd = [
            sys.executable,
            str(ROOT / "scripts/decode_noorin_flow.py"),
            pdf_arg,
            "1",
            str(pages),
        ]
        if skip_existing:
            cmd.append("--skip-existing")
        subprocess.run(cmd, cwd=ROOT, check=True)
        done_after = page_count_done(slug)
        batch_done.append(
            {
                "path": rel,
                "slug": slug,
                "pages": pages,
                "pages_before": done_before,
                "pages_after": done_after,
                "complete": done_after >= pages,
            }
        )
        print(f"  -> {slug}: {done_after}/{pages}")

    save_progress(queue, batch_done)
    print(f"progress -> {PROGRESS_JSON.relative_to(ROOT).as_posix()}")
    remaining = sum(1 for item in queue if not book_complete(item[3], item[1]))
    print(f"remaining incomplete books: {remaining}")
    return batch_done


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--decode",
        action="store_true",
        help="decode books from queue (use with --skip-census after first census)",
    )
    ap.add_argument(
        "--skip-census",
        action="store_true",
        help="read noorin_transfer.csv instead of re-scanning all PDFs",
    )
    ap.add_argument(
        "--min-pct",
        type=float,
        default=87.0,
        help="minimum mapped_pct to decode (default 87)",
    )
    ap.add_argument(
        "--batch-size",
        type=int,
        default=1,
        help="max incomplete books to decode per run (default 1)",
    )
    ap.add_argument(
        "--no-skip-existing",
        action="store_true",
        help="re-decode pages even if page-NNNN.txt already exists",
    )
    args = ap.parse_args()

    if args.skip_census:
        if not OUT_CSV.is_file():
            raise SystemExit(f"missing {OUT_CSV}; run census first")
        out_rows = load_transfer_csv()
        print(f"loaded {len(out_rows)} rows from {OUT_CSV.name}")
    else:
        out_rows = run_census(args.min_pct)

    if not args.decode:
        queue = decode_queue_from_rows(out_rows, args.min_pct)
        print(f"decode queue ({args.min_pct}%+): {len(queue)} books")
        for rel, pages, pct, slug in queue:
            done = page_count_done(slug)
            mark = "DONE" if done >= pages else f"{done}/{pages}"
            print(f"  {mark:8} {pct:5.1f}%  {rel}")
        print()
        print(
            "resume: py -3 scripts/census_noorin_transfer.py "
            "--decode --skip-census --min-pct 87 --batch-size 1"
        )
        return

    queue = decode_queue_from_rows(out_rows, args.min_pct)
    decode_books(
        queue,
        batch_size=max(1, args.batch_size),
        skip_existing=not args.no_skip_existing,
    )


if __name__ == "__main__":
    main()
