"""Decode a single-flow NOORIN-PUA PDF (not Kahawat two-column).

Uses the Kahawat NOORIN table. Unknown glyphs stay as [FONT:CODE].
Latin / already-Unicode spans stay as-is. Do not use the Batool table.

  py -3 scripts/decode_noorin_flow.py pdfs/anjumshanasi/Aks-e-Jamal.pdf 1 10
  py -3 scripts/decode_noorin_flow.py pdfs/anjumshanasi/Aks-e-Jamal.pdf 1 169 --skip-existing
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dump_noorin_lines import (
    ROOT,
    attach_overlays,
    cluster_rows,
    fmt_run,
    is_noorin,
    is_overlay_font,
    load_map,
    page_chars,
)

OUT_ROOT = ROOT / "data" / "decode" / "out"


def slug_from_pdf(pdf: Path) -> str:
    return pdf.stem.lower().replace(" ", "-")


def fmt_latin(chars: list) -> str:
    run = sorted(chars, key=lambda t: t[1])
    return "".join(chr(o) for _y, _x0, _x1, _font, o in run)


def join_other(rows: list[tuple[float, list]], other: list) -> list[tuple[list, list]]:
    """Each Latin/other glyph joins the nearest NOORIN row by y."""
    out = [list(row) for _y, row in rows]
    extra = [[] for _ in rows]
    if not rows:
        return [([], list(other))] if other else []
    ys = [y for y, _row in rows]
    for item in other:
        best_i = min(range(len(ys)), key=lambda i: abs(item[0] - ys[i]))
        extra[best_i].append(item)
    return list(zip(out, extra))


def decode_page(page: fitz.Page, pua_map: dict[str, str]) -> str:
    chars = page_chars(page)
    noorin = [c for c in chars if is_noorin(c[3])]
    other = [c for c in chars if not is_noorin(c[3])]
    base = [c for c in noorin if not is_overlay_font(c[3])]
    overlays = [c for c in noorin if is_overlay_font(c[3])]
    rows = cluster_rows(base)
    attached = attach_overlays(rows, overlays)
    mixed = join_other(list(zip([y for y, _ in rows], attached)), other)
    lines = []
    for noorin_row, latin_row in mixed:
        gojri = fmt_run(noorin_row, pua_map).strip() if noorin_row else ""
        latin = fmt_latin(latin_row).strip() if latin_row else ""
        if gojri and latin:
            lines.append(f"{gojri}\t{latin}")
        elif gojri or latin:
            lines.append(gojri or latin)
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Decode a NOORIN PUA PDF page range.")
    ap.add_argument("pdf", help="path to PDF")
    ap.add_argument("start", nargs="?", type=int, default=1)
    ap.add_argument("end", nargs="?", type=int)
    ap.add_argument("slug", nargs="?", help="output folder name under data/decode/out/")
    ap.add_argument(
        "--skip-existing",
        action="store_true",
        help="skip pages that already have page-NNNN.txt output",
    )
    args = ap.parse_args()

    pdf = Path(args.pdf)
    if not pdf.is_absolute():
        pdf = ROOT / pdf
    start = args.start
    end = args.end if args.end is not None else start
    slug = args.slug if args.slug else slug_from_pdf(pdf)
    out = OUT_ROOT / slug
    pua_map = load_map()
    out.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(pdf)
    end = min(end, doc.page_count)
    wrote = 0
    skipped = 0
    for page_1idx in range(start, end + 1):
        path = out / f"page-{page_1idx:04d}.txt"
        if args.skip_existing and path.exists():
            skipped += 1
            continue
        text = decode_page(doc[page_1idx - 1], pua_map)
        path.write_text(text, encoding="utf-8")
        wrote += 1
        print(f"wrote {path.relative_to(ROOT).as_posix()} ({len(text)} chars)")
    print(f"done {slug}: wrote {wrote}, skipped {skipped}, pages {start}-{end}")


if __name__ == "__main__":
    main()
