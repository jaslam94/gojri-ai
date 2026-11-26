"""Local page for the Kahawat-Kosh fields that look wrong by simple rules, before the release (the speaker fixes them).

Rules (per field of the run, text as in the release before spacing):
  idiom:   text after the last colon that is not a (bracket note); digits; confidence below 0.85
  meaning: digits; confidence below 0.85
Real English glosses in the print (Out of sight, out of mind) are not flagged. Each card shows the printed rows rendered from the PDF at 300 dpi
and the text in an edit box; the speaker corrects the text and clicks OK or Wrong (same buttons and file as the other review pages: review_marks.json).
Key `page|entry|field`, entry counted from 0.

Run: py -3 -X utf8 scripts/ocr_eval/build_release_outliers.py [--run data/ocr/kahawat-final3]
Output: <run>/release_outliers.html and release_outliers_keys.json (local; the page holds book crops).
"""
import argparse
import base64
import glob
import html
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_prose_review import CSS, JS  # noqa: E402

DIG = re.compile(r"[0-9۰-۹]")


def why(field, text, conf):
    out = []
    if field == "idiom":
        i = text.rfind(":")
        tail = text[i + 1:].strip() if i >= 0 else ""
        if tail and not re.fullmatch(r"\(.*\)", tail):
            out.append("text after the colon")
    if DIG.search(text):
        out.append("digits")
    if conf < 0.85:
        out.append(f"confidence {conf:.2f}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=str(ROOT / "data/ocr/kahawat-final3"))
    a = ap.parse_args()
    run = Path(a.run)
    doc = fitz.open(ROOT / "pdfs/anjumshanasi/Kahawat-Kosh.pdf")
    cards, keys = [], []
    for fn in sorted(glob.glob(str(run / "page_*.json"))):
        j = json.loads(Path(fn).read_text(encoding="utf-8"))
        for ei, e in enumerate(j.get("entries", [])):
            for field, rows, lo, hi, ckey in (("idiom", e.get("yr") or [], 215, None, "idiom_conf"), ("meaning", e.get("yl") or [], 0, 215, "meaning_conf")):
                text = e.get(field, "")
                reasons = why(field, text, float(e.get(ckey, 1)))
                if not reasons:
                    continue
                page = doc[j["page"] - 1]
                imgs = ""
                for ya, yb in rows:
                    clip = fitz.Rect(lo, ya * 72 / 200 - 3, hi or page.rect.width, yb * 72 / 200 + 3)
                    imgs += f'<img src="data:image/png;base64,{base64.b64encode(page.get_pixmap(clip=clip, dpi=300).tobytes("png")).decode()}" alt="row">'
                key = f"{j['page']}|{ei}|{field}"
                keys.append({"key": key, "reasons": reasons})
                cards.append(
                    f'<section class="card" data-id="{html.escape(key, quote=True)}">'
                    f'<div class="meta">PDF page {j["page"]}, entry {ei + 1}, {field} &middot; flagged: {html.escape(", ".join(reasons))}</div>{imgs}'
                    f'<textarea rows="2" spellcheck="false">{html.escape(text)}</textarea>'
                    '<div><button data-m="ok">OK</button><button data-m="wrong">Wrong (I fixed the text)</button>'
                    '<button data-m="unsure">Unsure</button> <span class="state"></span></div></section>')
    page_html = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
                 f'<title>Kahawat release outliers</title><style>{CSS}</style></head><body>'
                 '<header><b>Kahawat: fields to check</b> &middot; <span id="count"></span> <button id="dl">Download review_marks.json</button></header><main>'
                 f'<p>{len(cards)} fields that look wrong by simple rules (digits, text after the colon, low confidence). Compare the picture with the text box. '
                 'If the text is wrong, write the right text (keep what the print shows, including English glosses) and click <b>Wrong</b>. Click <b>OK</b> if it is right. '
                 'Remove stray digits that are not in the print.</p>' + "\n".join(cards) + '</main><script>const KEY="kahawat_outliers_v1";' + JS + '</script></body></html>')
    (run / "release_outliers.html").write_text(page_html, encoding="utf-8")
    (run / "release_outliers_keys.json").write_text(json.dumps(keys, ensure_ascii=False, indent=1), encoding="utf-8")
    print(len(cards), "cards ->", run / "release_outliers.html")


if __name__ == "__main__":
    main()
