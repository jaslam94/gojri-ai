"""Build a local HTML review page for ocr_prose_pages.py output: each row shows its clean crop and the OCR text.

Run: py -3 -X utf8 scripts/ocr_eval/build_prose_review.py --root data/ocr/prose-words --dpi 300
Writes <root>/review.html. Open it in a browser. The text is right to left; verse lines hold two halves split by a TAB.
Rows flagged "touch" (two lines touch, the crop may lack a piece) or "header" are marked. Judge the three things
separately: letters, marks, spaces.
"""
import argparse
import html
import json
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--dpi", type=int, default=300)
    args = ap.parse_args()
    root = Path(args.root)
    out = ['<meta charset="utf-8"><style>body{font:16px sans-serif;max-width:1100px;margin:auto}'
           '.r{display:flex;gap:16px;align-items:center;border-bottom:1px solid #ccc;padding:4px 0}'
           '.r img{max-width:520px;height:auto;flex:none;border:1px solid #eee}'
           '.t{direction:rtl;font:26px "Noto Nastaliq Urdu","Jameel Noori Nastaleeq",serif;white-space:pre-wrap;flex:1;text-align:right}'
           '.f{font-size:12px;color:#b00;direction:ltr}h2{margin-top:32px}</style>']
    for book in sorted(p for p in root.iterdir() if p.is_dir()):
        for jf in sorted((book / f"dpi{args.dpi}").glob("page_*.json")):
            j = json.loads(jf.read_text(encoding="utf-8"))
            out.append(f"<h2>{html.escape(book.name)} page {j['page']} "
                       f"(word mode {j['word_mode']}, gaps {html.escape(json.dumps(j['gaps']))})</h2>")
            for r in j["rows"]:
                if not r["text"]:
                    continue
                img = f"{book.name}/crops/p{j['page']:03d}/L{r['row']:02d}.png"
                fl = " ".join(r["flags"])
                out.append(f'<div class="r"><div class="t">{html.escape(r["text"])}</div>'
                           f'<div><img src="{img}"><div class="f">row {r["row"]} {html.escape(fl)}</div></div></div>')
    (root / "review.html").write_text("\n".join(out), encoding="utf-8")
    print("wrote", root / "review.html")


if __name__ == "__main__":
    main()
