"""Export the machine OCR text of the full-book runs to data/ocr-output/ (tracked) for speakers to review.

Text only; page images and line crops stay local. Page numbers are PDF page numbers (1-based), as in the source PDFs
(file names in data/pdf-corpus/CREDITS.tsv), not the numbers printed on the pages.
  kahawat-kosh/entries.tsv           from data/ocr/kahawat-pdfmarks-v2/page_NNN.json (one row per proverb entry)
  banjara/, dil-darya/               from data/ocr/prose-aws-full2/<book>/dpi300/page_NNN.txt
  gojri-ghazal/                      from data/ocr/ghazal-full/Gojri-Ghazal/dpi300/page_NNN.txt
Run: py -3 -X utf8 scripts/ocr_eval/export_ocr_output.py
"""
import csv
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OCR = ROOT / "data" / "ocr"
OUT = ROOT / "data" / "ocr-output"

TEXT_RUNS = {
    "banjara": OCR / "prose-aws-full2" / "Banjara" / "dpi300",
    "dil-darya": OCR / "prose-aws-full2" / "Dil-Darya" / "dpi300",
    "gojri-ghazal": OCR / "ghazal-full" / "Gojri-Ghazal" / "dpi300",
}


def main():
    for name, src in TEXT_RUNS.items():
        dst = OUT / name
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True)
        files = sorted(src.glob("page_*.txt"))
        for f in files:
            text = f.read_text(encoding="utf-8").replace("\r\n", "\n")
            (dst / f.name).write_text(text, encoding="utf-8")
        print(name, len(files), "pages")
    dst = OUT / "kahawat-kosh"
    dst.mkdir(parents=True, exist_ok=True)
    rows = []
    for f in sorted((OCR / "kahawat-pdfmarks-v2").glob("page_*.json")):
        j = json.loads(f.read_text(encoding="utf-8"))
        for k, e in enumerate(j.get("entries", []), 1):
            rows.append([j["page"], k, e.get("idiom", ""), e.get("meaning", "")])
    with open(dst / "entries.tsv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["pdf_page", "entry", "idiom", "meaning"])
        w.writerows(rows)
    print("kahawat-kosh", len(rows), "entries on", len({r[0] for r in rows}), "pages")


if __name__ == "__main__":
    main()
