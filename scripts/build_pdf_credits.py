"""Build CREDITS.tsv for PDF corpus publish from data/manifest.csv."""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "data" / "manifest.csv"
PDF_DIR = ROOT / "pdfs"
OUT = ROOT / "data" / "pdf-corpus"


def credits_for(path: str, name: str) -> tuple[str, str]:
    low = f"{path} {name}".lower()
    credit: list[str] = []
    notes: list[str] = []
    folder = str(Path(path).parent).replace("\\", "/")

    if any(x in low for x in ("javaidrahi", "javaid_rahi", "rahi")):
        credit.append("Dr. Javaid Rahi (editor/compiler on many volumes in this set)")
    if any(x in low for x in ("anjum", "rafiq", "rafique")):
        credit.append(
            "Prof. (Dr.) Rafique Anjum / Anjum Shanasi-linked publications where applicable"
        )
    if "ruksana" in low or "sadiq" in low:
        credit.append("Ms. Ruksana Sadiq (where credited on the title page)")
    if folder == "anjumshanasi":
        notes.append("Local folder: anjumshanasi/")
    if folder == "javaidrahi-blog":
        notes.append("Local folder: javaidrahi-blog/")
    if any(x in low for x in ("dictionary", "kosh", "lughat")):
        notes.append("Dictionary / glossary volume")
    if "quran" in low:
        notes.append("Quranic translation volume")
    if "textbook" in low or "kitab" in low or "pehli" in low or "shingar" in low:
        notes.append("Textbook / primer material")
    if not credit:
        credit.append(
            "Original author(s) and publisher as printed in the book; check the title page"
        )
    return "; ".join(credit), "; ".join(notes)


def main() -> None:
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
    out_rows = []
    for r in rows:
        if r.get("is_primary") != "1":
            continue
        path = r["path"].replace("\\", "/")
        src = PDF_DIR / path
        if not src.exists():
            continue
        name = Path(path).name
        credits, notes = credits_for(path, name)
        err = (r.get("error") or "").strip()
        if err:
            notes = f"{notes}; {err}" if notes else err
        out_rows.append(
            {
                "filename": name,
                "relative_path": path,
                "pages": r.get("pages", ""),
                "size_mb": r.get("size_mb", ""),
                "category": r.get("category", ""),
                "script_found": r.get("script_found", ""),
                "scope": "in_scope" if r.get("in_scope") == "1" else "out_of_scope",
                "credits": credits,
                "notes": notes,
                "md5": r.get("md5", ""),
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    fields = list(out_rows[0].keys())
    dest = OUT / "CREDITS.tsv"
    with dest.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t")
        w.writeheader()
        w.writerows(out_rows)
    print(f"wrote {dest} ({len(out_rows)} files)")
    print("in_scope", sum(1 for x in out_rows if x["scope"] == "in_scope"))
    print("out_of_scope", sum(1 for x in out_rows if x["scope"] == "out_of_scope"))


if __name__ == "__main__":
    main()
