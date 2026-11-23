"""Sample check of the FLI Gojri Literature Corpus (datasets/Gojri Language Corpus/): build a review page, then score it.

There is no scan of the source books, so a speaker can only judge the text itself: is a letter wrong, a mark lost, a word
split or joined, a character broken (U+FFFF)? The result is a text defect rate from a random sample, not an OCR error rate
against the print. State it that way.

  py -3 -X utf8 scripts/fli_review.py build [--per-file 10] [--seed 7]    writes data/fli-review/sample.json and review.html
  py -3 -X utf8 scripts/fli_review.py score <review_marks.json>            word error rate and line defect rate by file, overall

Sampling: per-file stratified (the same number of lines from each of the 11 files), lines of at least 3 words; a line longer
than 60 words is cut to a random window of 40 words. The overall rate weights each file by its word count.
U+FFFF cannot be drawn in a text box, so it is shown as the token ⟦FFFF⟧ and turned back when scoring.
"""
import argparse
import hashlib
import html
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "datasets" / "Gojri Language Corpus"
OUT = ROOT / "data" / "fli-review"
TOKEN = "⟦FFFF⟧"

CSS = '''
:root{--bg:#fafafa;--fg:#1a1a1a;--card:#fff;--line:#d8d8d8;--ok:#1b7f3b;--bad:#b3261e;--un:#8a6d00}
@media (prefers-color-scheme:dark){:root{--bg:#161616;--fg:#eee;--card:#222;--line:#444;--ok:#5ad17b;--bad:#ff8a80;--un:#e6c34d}}
body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.4 system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;z-index:5}
main{max-width:1000px;margin:0 auto;padding:12px 16px 80px}
.card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:10px;margin:10px 0}
.meta{font-size:12px;opacity:.75}
textarea{width:100%;box-sizing:border-box;direction:rtl;text-align:right;font:26px "Noto Nastaliq Urdu","Jameel Noori Nastaleeq",serif;
 line-height:1.9;padding:6px;margin:6px 0;background:var(--bg);color:var(--fg);border:1px solid var(--line);border-radius:4px;resize:vertical}
button{font:inherit;padding:5px 12px;margin-right:8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);cursor:pointer}
label.t{font-size:13px;margin-right:12px;opacity:.9}
.card.ok{border-color:var(--ok)}.card.wrong{border-color:var(--bad)}.card.unsure{border-color:var(--un)}
.state{font-size:13px}
.orig{direction:rtl;text-align:right;font:22px "Noto Nastaliq Urdu","Jameel Noori Nastaleeq",serif;line-height:1.9;padding:6px 8px;margin:6px 0;border:1px dashed var(--line);border-radius:4px;opacity:.85;white-space:pre-wrap}
.orig mark{background:var(--bad);color:#fff;padding:0 3px;border-radius:3px}
.lbl{font-size:12px;opacity:.7}
'''

JS = '''
let marks={};
try{marks=JSON.parse(localStorage.getItem(KEY)||"{}")}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(marks))}catch(e){}count()}
function count(){const v=Object.values(marks);document.getElementById("count").textContent=
 v.length+" of "+document.querySelectorAll(".card").length+" marked (OK "+v.filter(x=>x.m=="ok").length+", wrong "+v.filter(x=>x.m=="wrong").length+", unsure "+v.filter(x=>x.m=="unsure").length+")"}
document.querySelectorAll(".card").forEach(c=>{const id=c.dataset.id;const ta=c.querySelector("textarea");const ocr=ta.value;
 const types=()=>[...c.querySelectorAll("input[type=checkbox]:checked")].map(x=>x.value);
 const paint=()=>{const m=marks[id];c.classList.remove("ok","wrong","unsure");if(m){c.classList.add(m.m);c.querySelector(".state").textContent=m.m;
  ta.value=m.text;c.querySelectorAll("input[type=checkbox]").forEach(x=>x.checked=(m.types||[]).includes(x.value))}};
 c.querySelectorAll("button").forEach(b=>b.onclick=()=>{marks[id]={m:b.dataset.m,ocr:ocr,text:ta.value,types:types()};save();paint()});paint()});
document.getElementById("dl").onclick=()=>{const blob=new Blob([JSON.stringify(marks,null,1)],{type:"application/json"});
 const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="fli_review_marks.json";a.click()};
count();
'''


def sample(per_file, seed):
    rng = random.Random(seed)
    rows, words = [], {}
    for f in sorted(CORPUS.glob("*.txt")):
        text = f.read_text(encoding="utf-8")
        lines = [l.strip() for l in text.split("\n") if len(l.split()) >= 3]
        words[f.name] = len(text.split())
        for n in sorted(rng.sample(range(len(lines)), min(per_file, len(lines)))):
            ws = lines[n].split()
            if len(ws) > 60:
                a = rng.randrange(0, len(ws) - 40)
                ws = ws[a:a + 40]
            rows.append({"id": f"{f.name}|{n}", "file": f.name, "line": n, "text": " ".join(ws).replace("￿", TOKEN)})
    return rows, words


def build(args):
    rows, words = sample(args.per_file, args.seed)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "sample.json").write_text(json.dumps({"rows": rows, "words": words}, ensure_ascii=False, indent=1), encoding="utf-8")
    cards = []
    for r in rows:
        cards.append(
            f'<section class="card" data-id="{html.escape(r["id"], quote=True)}">'
            f'<div class="meta">{html.escape(r["file"])} line {r["line"]}</div>'
            '<div class="lbl">Original (as in the corpus file, read only)</div>'
            f'<div class="orig">{html.escape(r["text"]).replace(TOKEN, "<mark>" + TOKEN + "</mark>")}</div>'
            '<div class="lbl">Your text (edit here)</div>'
            f'<textarea rows="{r["text"].count(chr(10)) + 3}" spellcheck="false">{html.escape(r["text"])}</textarea>'
            '<div><button data-m="ok">OK</button><button data-m="wrong">Wrong (I fixed the text)</button>'
            '<button data-m="unsure">Unsure</button> <span class="state"></span></div>'
            '<div><label class="t"><input type="checkbox" value="letters"> letters</label>'
            '<label class="t"><input type="checkbox" value="marks"> marks</label>'
            '<label class="t"><input type="checkbox" value="spaces"> spaces</label>'
            f'<label class="t"><input type="checkbox" value="broken"> broken character ({TOKEN})</label></div>'
            '</section>')
    key = "fli_review_" + hashlib.md5(json.dumps([r["id"] for r in rows]).encode()).hexdigest()[:8]
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>FLI corpus check</title><style>{CSS}</style></head><body>'
            '<header><b>FLI Gojri Literature Corpus: sample check</b> &middot; <span id="count"></span> '
            '<button id="dl">Download fli_review_marks.json</button></header><main>'
            '<p>Each card is a random line from the corpus. The top box shows the original and never changes. Read it. Click <b>OK</b> if the text is right. If not, correct the text in the lower box, '
            f'tick what was wrong, then click <b>Wrong</b>. {TOKEN} marks a broken character in the file: type the letter or mark that belongs there '
            '(or leave the token if you do not know). Your work is saved in this browser; use Download when you stop.</p>'
            + "\n".join(cards) + f'</main><script>const KEY="{key}";{JS}</script></body></html>')
    (OUT / "review.html").write_text(page, encoding="utf-8")
    print("wrote", OUT / "review.html", len(rows), "cards from", len(words), "files")


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def score(args):
    marks = json.loads(Path(args.marks).read_text(encoding="utf-8"))
    meta = json.loads((OUT / "sample.json").read_text(encoding="utf-8"))
    file_of = {r["id"]: r["file"] for r in meta["rows"]}
    per = {}
    for cid, v in marks.items():
        if v["m"] == "unsure" or cid not in file_of:
            continue
        truth = v["text"] if v["m"] == "wrong" else v["ocr"]
        d = per.setdefault(file_of[cid], {"lines": 0, "wrong": 0, "words": 0, "word_err": 0, "broken": 0})
        d["lines"] += 1
        d["wrong"] += v["m"] == "wrong"
        a, b = v["ocr"].split(), truth.split()
        d["words"] += len(a)
        d["word_err"] += edit_distance(a, b)
        d["broken"] += TOKEN in v["ocr"]
    print(f"{'file':44} lines wrong  words word_err%  lines_with_FFFF")
    tw = te = 0.0
    for f in sorted(per):
        d = per[f]
        rate = d["word_err"] / max(d["words"], 1)
        n = meta["words"][f]
        tw += n
        te += rate * n
        print(f"{f[:44]:44} {d['lines']:5} {d['wrong']:5} {d['words']:6} {100 * rate:8.1f}%  {d['broken']}")
    if tw:
        print(f"overall word error (files weighted by their word count): {100 * te / tw:.1f}%   [{len(per)} files, {sum(d['lines'] for d in per.values())} lines]")
    print("This is a text defect rate from a sample. It is not an OCR error rate against the print.")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--per-file", type=int, default=10)
    b.add_argument("--seed", type=int, default=7)
    s = sub.add_parser("score")
    s.add_argument("marks")
    a = ap.parse_args()
    (build if a.cmd == "build" else score)(a)


if __name__ == "__main__":
    sys.exit(main())
