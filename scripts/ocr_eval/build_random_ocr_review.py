"""Build a local page where the speaker checks the OCR letters, marks and spaces of RANDOM rows (not the 10 pages reviewed so far).

Why: the 178 rows of the first prose review sit on 10 pages (letters 0.97% wrong, marks 11 of 92 wrong against the speaker's text).
That is not a sample of the 716 pages. The 120 random rows of the language-tag page (`origin: new`, seeded, rows of 20 or more Arabic letters,
no Latin) come from all pages. Each card shows the printed row (embedded image) and the OCR text in an edit box. The result gives an
unbiased error rate for letters and marks, split by the speaker's language tag.
Cards use the same buttons and result format as build_prose_review.py (OK, Wrong, Unsure; error types), file review_random_marks.json.

Run: py -3 -X utf8 scripts/ocr_eval/build_random_ocr_review.py
Output: data/ocr/prose-words/random_ocr_review.html (holds book crops: keep it local).
"""
import base64
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_prose_review import CSS, JS  # noqa: E402

RUN = ROOT / "data/ocr/prose-aws-full2"
OUT = ROOT / "data/ocr/prose-words"
TAGS = ROOT / "data/reviews/prose-language/lang_tags_final_20261124.json"
NAMES = {"gju": "Gojri", "urd": "Urdu", "same": "same in both"}


def main():
    tags = json.loads(TAGS.read_text(encoding="utf-8"))
    sample = [r for r in json.loads((ROOT / "data/reviews/prose-language/lang_tag_sample.json").read_text(encoding="utf-8")) if r["origin"] == "new"]
    cards = []
    for r in sorted(sample, key=lambda r: (r["book"], r["page"], r["row"])):
        j = json.loads((RUN / r["book"] / "dpi300" / f"page_{r['page']:03d}.json").read_text(encoding="utf-8"))
        row = next(x for x in j["rows"] if x["row"] == r["row"])
        crop = RUN / r["book"] / "crops" / f"p{r['page']:03d}" / f"L{r['row']:02d}.png"
        img = base64.b64encode(crop.read_bytes()).decode()
        lang = NAMES.get(tags.get(r["key"], {}).get("tag"), "")
        cards.append(
            f'<section class="card" data-id="{html.escape(r["key"], quote=True)}">'
            f'<div class="meta">{html.escape(r["book"])} page {r["page"]} row {r["row"]} &middot; language tag: {lang}</div>'
            f'<img src="data:image/png;base64,{img}" alt="row crop">'
            f'<textarea rows="2" spellcheck="false">{html.escape(row["text"])}</textarea>'
            '<div><button data-m="ok">OK</button><button data-m="wrong">Wrong (I fixed the text)</button>'
            '<button data-m="unsure">Unsure</button> <span class="state"></span></div>'
            '<div><label class="t"><input type="checkbox" value="letters"> letters wrong</label>'
            '<label class="t"><input type="checkbox" value="marks"> marks wrong</label>'
            '<label class="t"><input type="checkbox" value="spaces"> spaces wrong</label>'
            '<label class="t"><input type="checkbox" value="crop"> crop cut or has other line</label></div></section>')
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Random OCR row check</title><style>{CSS}</style></head><body>'
            '<header><b>Random OCR rows</b> &middot; <span id="count"></span> '
            '<button id="dl">Download review_marks.json</button></header><main>'
            f'<p>{len(cards)} random rows from all pages of Banjara and Dil-Darya. Compare the picture with the text box. Click <b>OK</b> if the text is right. '
            'If not, correct the text in the box (keep the TAB between verse halves), tick what was wrong, then click <b>Wrong</b>. '
            'Judge letters, marks and spaces separately. Spaces follow meaning. Your work is saved in this browser; use Download when you stop.</p>'
            + "\n".join(cards) + '</main><script>const KEY="random_ocr_v1";' + JS + '</script></body></html>')
    (OUT / "random_ocr_review.html").write_text(page, encoding="utf-8")
    print(len(cards), "cards ->", OUT / "random_ocr_review.html")


if __name__ == "__main__":
    main()
