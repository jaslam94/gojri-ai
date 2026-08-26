"""Extract already-correct Unicode from good-text PDFs and copy the FLI corpus.

Writes page files, one concatenated book file, and a provenance JSONL.
Output is local under data/extracted/ (gitignored). Re-run overwrites.

  py -3 scripts/extract_clean_text.py
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "pdfs"
MANIFEST = ROOT / "data" / "manifest.csv"
FLI_DIR = ROOT / "datasets" / "Gojri Language Corpus"
OUT = ROOT / "data" / "extracted"
PROV = OUT / "provenance.jsonl"


def slug_from_path(rel: str) -> str:
    name = Path(rel).stem
    name = re.sub(r"[^\w]+", "-", name, flags=re.ASCII)
    return name.strip("-").lower() or "book"


def garbage_ratio(text: str) -> float:
    n = 0
    bad = 0
    for ch in text:
        if ch.isspace():
            continue
        n += 1
        cp = ord(ch)
        if cp in (0xFFFD, 0xFFFF):
            bad += 1
        elif not ch.isascii() and not (
            0x0600 <= cp <= 0x06FF
            or 0x0750 <= cp <= 0x077F
            or 0x0900 <= cp <= 0x097F
            or 0xFB50 <= cp <= 0xFDFF
            or 0xFE70 <= cp <= 0xFEFF
        ):
            bad += 1
    return (bad / n) if n else 0.0


def extract_pdf(rel: str, script_found: str) -> dict:
    src = PDF_DIR / rel
    slug = slug_from_path(rel)
    dest = OUT / "clean-pdf" / slug
    dest.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(src)
    pages = []
    book_parts = []
    for i, page in enumerate(doc, start=1):
        text = page.get_text("text")
        if not text.endswith("\n"):
            text += "\n"
        page_path = dest / f"page-{i:04d}.txt"
        page_path.write_text(text, encoding="utf-8")
        pages.append(page_path)
        book_parts.append(text.rstrip("\n"))
    doc.close()
    sample = "\n".join(
        book_parts[min(5, len(book_parts) - 1) : min(15, len(book_parts))]
    )
    ratio = garbage_ratio(sample)
    if ratio > 0.08:
        shutil.rmtree(dest)
        rec = {
            "source": f"pdfs/{rel}",
            "method": "pymupdf_get_text",
            "encoding_scheme": "broken_tounicode",
            "script_found": script_found,
            "pages": len(pages),
            "skipped": 1,
            "garbage_ratio": round(ratio, 3),
            "note": "ToUnicode is broken. Direct extract discarded.",
        }
        print(
            f"SKIPPED {rel} (garbage_ratio={ratio:.3f}; "
            "broken ToUnicode, extract deleted)"
        )
        return rec
    book_path = dest / "book.txt"
    book_path.write_text("\n\n".join(book_parts) + "\n", encoding="utf-8")
    chars = sum(len(p.read_text(encoding="utf-8")) for p in pages)
    rec = {
        "source": f"pdfs/{rel}",
        "method": "pymupdf_get_text",
        "encoding_scheme": "clean_unicode",
        "script_found": script_found,
        "pages": len(pages),
        "chars": chars,
        "out_dir": dest.relative_to(ROOT).as_posix(),
        "book": book_path.relative_to(ROOT).as_posix(),
    }
    print(
        f"extracted {rel} -> {dest.relative_to(ROOT).as_posix()} "
        f"({len(pages)} pages, {chars} chars)"
    )
    return rec


def copy_fli() -> list[dict]:
    dest = OUT / "fli-corpus"
    dest.mkdir(parents=True, exist_ok=True)
    recs = []
    for src in sorted(FLI_DIR.glob("*.txt")):
        text = src.read_text(encoding="utf-8")
        n_ffff = text.count("\uffff")
        out = dest / src.name
        shutil.copy2(src, out)
        rec = {
            "source": src.relative_to(ROOT).as_posix(),
            "method": "copy_utf8",
            "encoding_scheme": "clean_unicode",
            "script_found": "perso_arabic",
            "pages": 1,
            "chars": len(text),
            "words": len(text.split()),
            "u_ffff": n_ffff,
            "out_file": out.relative_to(ROOT).as_posix(),
        }
        recs.append(rec)
        print(
            f"copied {src.name} ({rec['words']} words, U+FFFF={n_ffff})"
        )
    return recs


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not PDF_DIR.is_dir():
        sys.exit(f"PDF directory not found: {PDF_DIR}")
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
    targets = [
        r
        for r in rows
        if int(r["is_primary"])
        and int(r["in_scope"])
        and r["category"] == "good_text"
        and r["encoding_scheme"] == "clean_unicode"
    ]
    if not targets:
        sys.exit("no clean-unicode primary PDFs in the manifest")
    OUT.mkdir(parents=True, exist_ok=True)
    recs = []
    recs.extend(copy_fli())
    for r in targets:
        recs.append(extract_pdf(r["path"], r["script_found"]))
    PROV.write_text(
        "".join(json.dumps(rec, ensure_ascii=False) + "\n" for rec in recs),
        encoding="utf-8",
    )
    print(f"wrote {PROV.relative_to(ROOT).as_posix()} ({len(recs)} records)")


if __name__ == "__main__":
    main()
