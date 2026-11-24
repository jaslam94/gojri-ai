"""Build a page of the spaces that the character n-gram inserter (spacing_lm.py) adds to the prose OCR rows, for the speaker to check.

Why: the prose review (183 rows, 2026-11-16) came before the ruling "spaces follow meaning", so its truth keeps some glued
words, and scoring the model against it overcounts wrong spaces (score_prose_spacing.py, check A). The speaker judges the model's
own proposals instead, as he did for the old splitter (space_review.py).
Cards: every glued OCR token of the reviewed rows where the model adds a space, except tokens that are already among the 66
split cards, and tokens whose added spaces already appear in the speaker's own row text.
  py -3 -X utf8 scripts/ocr_eval/space_review_model.py   writes data/ocr/prose-words/model_space_review.html and model_space_cards.json
  py -3 -X utf8 scripts/ocr_eval/space_review_model.py --gojri-only   second page (2026-11-24): only cards that the speaker has not checked
    and that sit on rows he tagged Gojri (data/reviews/prose-language/lang_tags_final_20261124.json); writes model_space_review_gju.html
"""
import argparse
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_prose_spacing as P  # noqa: E402
import score_spacing as SS  # noqa: E402


def tokens_with_splits(ocr, new):
    """[(ocr token, token with the model's spaces, first letter index of the token in the row)]. Insert only, so the pieces line up."""
    out, nt, letters = [], new.split(), 0
    j = 0
    for tok in ocr.split():
        parts, got = [], ""
        bare = "".join(SS.parse(tok)[0])
        while j < len(nt) and "".join(SS.parse(got)[0]) != bare:
            parts.append(nt[j])
            got += nt[j]
            j += 1
        assert "".join(SS.parse(got)[0]) == bare, (tok, parts)
        n = len(SS.parse(tok)[0])
        if len(parts) > 1:
            out.append((tok, " ".join(parts), letters))
        letters += n
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gojri-only", action="store_true")
    args = ap.parse_args()
    model = P.build_model()
    rev = json.loads((P.R / "prose-banjara-dildarya/review_marks.json").read_text(encoding="utf-8"))
    done = {(c["row"], c["token"]) for c in json.loads((P.R / "prose-word-splits/splits_20261121.json").read_text(encoding="utf-8"))}
    cards, skipped_known, skipped_agreed = [], 0, 0
    for k, x in rev.items():
        if x["m"] == "unsure":
            continue
        ocr = P.punct(x["ocr"])
        if re.search(r"[0-9A-Za-z]", ocr) or len(SS.parse(ocr)[0]) < 4:
            continue
        new = P.add_spaces(ocr, model)
        truth = P.punct(x["text"] if x["m"] == "wrong" else x["ocr"])
        tl, _, ts = SS.parse(truth)
        ol, _, os_ = SS.parse(ocr)
        for tok, split, start in tokens_with_splits(ocr, new):
            core = tok.strip("۔،:؛؟!()-")
            if (k, core) in done or (k, tok) in done:
                skipped_known += 1
                continue
            added = {start + i for i in SS.parse(split)[2]}
            if ol == tl and added <= ts:
                skipped_agreed += 1
                continue
            cards.append({"id": f"{k}|{tok}|{start}", "row": k, "token": tok, "proposal": split, "context": ocr})
    out = ROOT / "data/ocr/prose-words"
    suffix = ""
    if args.gojri_only:
        tags = json.loads((ROOT / "data/reviews/prose-language/lang_tags_final_20261124.json").read_text(encoding="utf-8"))
        done_ids = {k for k, v in json.loads((ROOT / "data/reviews/prose-model-space/model_space_20261123.json").read_text(encoding="utf-8")).items() if v.get("m")}
        cards = [c for c in cards if c["id"] not in done_ids and tags.get(c["row"], {}).get("tag") == "gju"]
        suffix = "_gju"
    (out / f"model_space_cards{suffix}.json").write_text(json.dumps(cards, ensure_ascii=False, indent=1), encoding="utf-8")
    rows = "".join(
        f'<section class="c" data-id="{html.escape(c["id"])}"><div class="m">{html.escape(c["row"])}</div>'
        f'<div class="w">{html.escape(c["token"])} &rarr; <b>{html.escape(c["proposal"])}</b></div><div class="l">{html.escape(c["context"])}</div>'
        f'<div class="f">Right split: <input class="t" dir="rtl" value="{html.escape(c["proposal"])}"></div>'
        '<button data-m="accept">Accept</button><button data-m="reject">Reject</button><span class="s"></span></section>'
        for c in cards)
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>Model space check</title><style>body{font:16px system-ui;margin:0 auto;max-width:900px;padding:12px;background:#fafafa;color:#111}'
            '@media(prefers-color-scheme:dark){body{background:#161616;color:#eee}.c{background:#222!important}}'
            '.c{background:#fff;border:1px solid #888;border-radius:8px;padding:8px;margin:8px 0}.w,.l{direction:rtl;text-align:right;font:26px "Noto Nastaliq Urdu",serif;line-height:1.9}'
            '.l{font-size:18px;opacity:.7}.m{font-size:12px;opacity:.7}.c.accept{border-color:#1b7f3b}.c.reject{border-color:#b3261e}button{font:inherit;margin-right:8px;padding:4px 12px}.t{font:22px "Noto Nastaliq Urdu",serif;width:60%;direction:rtl;margin:4px 0 8px}.f{font-size:13px;opacity:.8}</style></head><body>'
            f'<h3>Model space check ({len(cards)} cards)</h3><p>The arrow shows the glued word and the spaces the model adds. Spaces follow meaning (ruling 2026-11-16). '
            'Accept if every space the model adds is right (more spaces may still be missing). Reject if it cuts a word wrongly. '
            'If the right split is different, or more spaces are missing, write the right words in the box.</p>'
            '<button id="dl">Download model_space_review' + suffix + '.json</button>' + rows +
            '<script>const KEY="model_space_v1' + suffix + '",KF="model_space_v1' + suffix + '_text";let m={},x={};try{m=JSON.parse(localStorage.getItem(KEY)||"{}");x=JSON.parse(localStorage.getItem(KF)||"{}")}catch(e){}'
            'document.querySelectorAll(".c").forEach(c=>{const id=c.dataset.id;const t=c.querySelector(".t");if(x[id])t.value=x[id];t.oninput=()=>{x[id]=t.value;try{localStorage.setItem(KF,JSON.stringify(x))}catch(e){}};const p=()=>{c.classList.remove("accept","reject");if(m[id]){c.classList.add(m[id]);c.querySelector(".s").textContent=m[id]}};'
            'c.querySelectorAll("button").forEach(b=>b.onclick=()=>{m[id]=b.dataset.m;try{localStorage.setItem(KEY,JSON.stringify(m))}catch(e){}p()});p()});'
            'document.getElementById("dl").onclick=()=>{const o={};document.querySelectorAll(".c").forEach(c=>{const id=c.dataset.id;if(m[id]||x[id])o[id]={m:m[id]||"",text:x[id]||c.querySelector(".t").defaultValue}});const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([JSON.stringify(o,null,1)],{type:"application/json"}));a.download="model_space_review' + suffix + '.json";a.click()};'
            '</script></body></html>')
    (out / f"model_space_review{suffix}.html").write_text(page, encoding="utf-8")
    print(len(cards), "cards;", skipped_known, "tokens skipped (already among the 66 split cards);", skipped_agreed, "skipped (the speaker's row text already has these spaces)")


if __name__ == "__main__":
    main()
