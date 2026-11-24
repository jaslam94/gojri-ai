"""Page for the speaker to check (and fix) the word spaces of the Arabic-script parts in the 200 reviewed dictionary lines.

Why: the 2.1% letter error of UTRNet-Large on these lines (data/utrnet-test/README.md) drops spaces before it scores, so it says nothing
about spacing. The truth text of the 200 lines (`text_fix`) holds only 83 spaces inside Arabic runs (342 Arabic words in 195 lines), and the speaker
doubts that those spaces were marked with care. Cards: the 195 lines that hold Arabic letters, lines with 2 or more Arabic words first.
Each card shows the printed line (embedded image) and the truth text in an edit box. Spaces follow meaning; the English part needs no check.
The result file review_marks.json uses the same layout as the other review pages (OK, Wrong, Unsure; "ocr" = the old truth, "text" = the new one).

Run: py -3 -X utf8 scripts/ocr_eval/build_dictionary_spacing_review.py
Output: data/ocr/dict-spacing/spacing_review.html (holds book crops: keep it local).
"""
import base64
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_prose_review import CSS, JS  # noqa: E402

SRC = ROOT / "data/reviews/dictionary-200-lines"
OUT = ROOT / "data/ocr/dict-spacing"
AR = r"[؀-ۿݐ-ݿ]"


def n_arabic_words(t):
    runs = re.findall(AR + r"[؀-ۿݐ-ݿ\s،۔]*", t)
    return sum(len(re.findall(AR + "+", x)) for x in runs)


def main():
    rows = [json.loads(l) for l in (SRC / "labels_review_test.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    rows = [r for r in rows if n_arabic_words(r["text_fix"]) > 0]
    rows.sort(key=lambda r: (n_arabic_words(r["text_fix"]) < 2, r["page_line"]))
    cards = []
    for r in rows:
        img = base64.b64encode((SRC / r["image"]).read_bytes()).decode()
        nw = n_arabic_words(r["text_fix"])
        cards.append(
            f'<section class="card" data-id="{html.escape(r["page_line"], quote=True)}">'
            f'<div class="meta">{html.escape(r["page_line"])} &middot; {nw} Arabic word{"s" if nw != 1 else ""}</div>'
            f'<img src="data:image/png;base64,{img}" alt="printed line">'
            f'<textarea rows="2" spellcheck="false">{html.escape(r["text_fix"])}</textarea>'
            '<div><button data-m="ok">OK</button><button data-m="wrong">Wrong (I fixed the text)</button>'
            '<button data-m="unsure">Unsure</button> <span class="state"></span></div>'
            '<div><label class="t"><input type="checkbox" value="spaces"> spaces wrong</label>'
            '<label class="t"><input type="checkbox" value="letters"> letters wrong</label>'
            '<label class="t"><input type="checkbox" value="marks"> marks wrong</label></div></section>')
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Dictionary spacing check</title><style>{CSS}</style></head><body>'
            '<header><b>Dictionary lines: word spaces</b> &middot; <span id="count"></span> '
            '<button id="dl">Download review_marks.json</button></header><main>'
            f'<p>{len(cards)} lines with Arabic-script text. The first {sum(n_arabic_words(r["text_fix"]) > 1 for r in rows)} hold two or more Arabic words. '
            'Compare the picture with the box. Fix the <b>word spaces</b> of the Arabic-script parts (spaces follow meaning; a space after the comma and after the end sign). '
            'You may fix letters too. The English part needs no check. Click <b>OK</b> if all is right, or fix the text and click <b>Wrong</b>. '
            'Your work is saved in this browser; use Download when you stop.</p>'
            + "\n".join(cards) + '</main><script>const KEY="dict_spacing_v1";' + JS + '</script></body></html>')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "spacing_review.html").write_text(page, encoding="utf-8")
    print(len(cards), "cards ->", OUT / "spacing_review.html")


if __name__ == "__main__":
    main()
