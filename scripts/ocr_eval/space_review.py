"""Build a page of proposed word splits for the speaker to accept or reject (spaces follow meaning, ruling 2026-11-19).

The splitter (space_fix.py) runs over the OCR text of the reviewed rows. Every token it would split becomes one card:
"glued token -> split token". The speaker marks Accept or Reject. The result tunes the splitter and shows its real precision.
Vocabulary: FLI corpus words plus all OCR words of the full runs, words seen at least 3 times; margin 4.0.
  py -3 -X utf8 scripts/ocr_eval/space_review.py   writes data/ocr/prose-words/space_review.html
"""
import glob
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import space_fix as S  # noqa: E402

MINC, MARGIN = 3, 4.0


def punct(s):
    return re.sub(r"([۔،])(?=[^\s۔،])", r"\1 ", s)


def main():
    texts = [open(f, encoding="utf-8").read().replace("\uffff", "") for f in glob.glob(str(ROOT / "datasets/Gojri Language Corpus/*.txt"))]
    for jf in glob.glob(str(ROOT / "data/ocr/prose-aws-full2/*/dpi300/page_*.json")):
        texts += [r["text"] for r in json.load(open(jf, encoding="utf-8"))["rows"]]
    v = S.build_vocab(texts)
    v.c = {w: c for w, c in v.c.items() if c >= MINC}
    v.n = sum(v.c.values())
    rev = json.load(open(ROOT / "data/ocr/prose-words/review_marks.json", encoding="utf-8"))
    seen, cards = set(), []
    for k, x in rev.items():
        if x["m"] == "unsure":
            continue
        line = punct(x["text"] if x["m"] == "wrong" else x["ocr"])
        for tok in line.split():
            core = tok.strip(S.PUNCT)
            new = S.split_token(core, v, MARGIN) if core else core
            if new != core and (tok, new) not in seen:
                seen.add((tok, new))
                cards.append((k, tok, tok.replace(core, new), line))
    rows = "".join(
        f'<section class="c" data-id="{html.escape(k + "|" + t)}"><div class="m">{html.escape(k)}</div>'
        f'<div class="w">{html.escape(t)} &rarr; <b>{html.escape(n)}</b></div><div class="l">{html.escape(l)}</div>'
        '<button data-m="accept">Accept</button><button data-m="reject">Reject</button><span class="s"></span></section>'
        for k, t, n, l in cards)
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Word split check</title><style>body{font:16px system-ui;margin:0 auto;max-width:900px;padding:12px;background:#fafafa;color:#111}'
            '@media(prefers-color-scheme:dark){body{background:#161616;color:#eee}.c{background:#222!important}}'
            '.c{background:#fff;border:1px solid #888;border-radius:8px;padding:8px;margin:8px 0}.w,.l{direction:rtl;text-align:right;font:26px "Noto Nastaliq Urdu",serif;line-height:1.9}'
            '.l{font-size:18px;opacity:.7}.m{font-size:12px;opacity:.7}.c.accept{border-color:#1b7f3b}.c.reject{border-color:#b3261e}button{font:inherit;margin-right:8px;padding:4px 12px}</style></head><body>'
            f'<h3>Word split check ({len(cards)} cards)</h3><p>Accept if the split gives two or more real words. Reject if it cuts a word.</p>'
            '<button id="dl">Download space_review.json</button>' + rows +
            '<script>const KEY="space_review_v1";let m={};try{m=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}'
            'document.querySelectorAll(".c").forEach(c=>{const id=c.dataset.id;const p=()=>{c.classList.remove("accept","reject");if(m[id]){c.classList.add(m[id]);c.querySelector(".s").textContent=m[id]}};'
            'c.querySelectorAll("button").forEach(b=>b.onclick=()=>{m[id]=b.dataset.m;try{localStorage.setItem(KEY,JSON.stringify(m))}catch(e){}p()});p()});'
            'document.getElementById("dl").onclick=()=>{const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(m,null,1)],{type:"application/json"}));a.download="space_review.json";a.click()};'
            '</script></body></html>')
    out = ROOT / "data/ocr/prose-words/space_review.html"
    out.write_text(page, encoding="utf-8")
    print("wrote", out, len(cards), "cards")


if __name__ == "__main__":
    main()
