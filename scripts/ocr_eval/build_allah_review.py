"""Local page for the 5 Kahawat-Kosh fields that the word-glyph check flagged (word_glyph_flags.json).

The PDF draws the shadda glyph of اللّٰہ in each of these fields, but the OCR text has no اللہ (it reads اللدئےتے, اللنے, عبیدالل, اللران, الللی).
Each card shows the printed row (rendered straight from the PDF at 300 dpi) and the OCR text in an edit box. The speaker corrects the text and clicks OK or Wrong.
Ruling 2026-11-23: اللہ keeps its shadda as printed (اللّٰہ).

Run: py -3 -X utf8 scripts/ocr_eval/build_allah_review.py [--run data/ocr/kahawat-final3]
Output: data/ocr/kahawat-final3/allah_review.html (holds book crops: keep it local). The page downloads review_marks.json.
"""
import argparse
import base64
import html
import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_prose_review import CSS, JS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(ROOT / "data/ocr/kahawat-final3"))
    a = ap.parse_args()
    run = Path(a.run)
    flags = json.loads((ROOT / "data/ocr/kahawat-final2/word_glyph_flags.json").read_text(encoding="utf-8"))
    doc = fitz.open(ROOT / "pdfs/anjumshanasi/Kahawat-Kosh.pdf")
    cards = []
    for f in flags:
        j = json.loads((run / f"page_{f['page']:03d}.json").read_text(encoding="utf-8"))
        e = j["entries"][f["entry"]]  # the flag counts entries from 0
        text = e[f["field"]]
        assert text == f["text"], (f["page"], f["entry"])
        rows = e["yr"] if f["field"] == "idiom" else e["yl"]
        page = doc[f["page"] - 1]
        lo, hi = (215, page.rect.width) if f["field"] == "idiom" else (0, 215)
        imgs = ""
        for ya, yb in rows:
            clip = fitz.Rect(lo, ya * 72 / 200 - 3, hi, yb * 72 / 200 + 3)
            png = page.get_pixmap(clip=clip, dpi=300).tobytes("png")
            imgs += f'<img src="data:image/png;base64,{base64.b64encode(png).decode()}" alt="row">'
        key = f"{f['page']}|{f['entry']}|{f['field']}"
        cards.append(
            f'<section class="card" data-id="{html.escape(key, quote=True)}">'
            f'<div class="meta">PDF page {f["page"]}, entry {f["entry"] + 1}, {f["field"]}</div>{imgs}'
            f'<textarea rows="2" spellcheck="false">{html.escape(text)}</textarea>'
            '<div><button data-m="ok">OK</button><button data-m="wrong">Wrong (I fixed the text)</button>'
            '<button data-m="unsure">Unsure</button> <span class="state"></span></div></section>')
    page_html = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                 f'<title>Allah word check</title><style>{CSS}</style></head><body>'
                 '<header><b>اللہ check</b> &middot; <span id="count"></span> <button id="dl">Download review_marks.json</button></header><main>'
                 f'<p>{len(cards)} fields. The PDF has the glyph of the word اللّٰہ in each, but the OCR text does not show it. Compare the picture with the text box, '
                 'write the right text (اللہ keeps its shadda, اللّٰہ), then click <b>Wrong</b>. Click <b>OK</b> if the text is already right.</p>'
                 + "\n".join(cards) + '</main><script>const KEY="allah_check_v1";' + JS + '</script></body></html>')
    (run / "allah_review.html").write_text(page_html, encoding="utf-8")
    print(len(cards), "cards ->", run / "allah_review.html")


if __name__ == "__main__":
    main()
