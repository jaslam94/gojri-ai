"""Score the character n-gram space inserter (spacing_lm.py) on the speaker's prose reviews (Banjara, Dil-Darya).

Model: the config chosen on the Kahawat dev cards (data/reviews/kahawat-spacing/chosen_config_20261123.json), trained on the
FLI corpus and the word-spaced truth of ALL 200 Kahawat spacing cards (the prose rows are a different book, so nothing leaks).
No setting is tuned here.

Two checks:
 A. The 183 OCR rows of review_marks.json. Truth = the speaker's text (marked wrong) or the OCR text (marked ok). Caution: this
    review was made before the ruling "spaces follow meaning" (2026-11-16 and 2026-11-19), so some truth rows keep glued words.
    The count of "extra" spaces is therefore too high, and the missing count is the safer number.
 B. The 66 split cards (splits_20261121.json): the speaker's right split of a glued token. The spaces the model adds inside that
    token are compared with the speaker's text. These tokens were chosen by the old splitter, so this compares on the same tokens.
Run: py -3 -X utf8 scripts/ocr_eval/score_prose_spacing.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_spacing as SS  # noqa: E402
import space_fix as S  # noqa: E402
import spacing_experiment as E  # noqa: E402
import spacing_lm as L  # noqa: E402

CFG = json.loads((ROOT / "data/reviews/kahawat-spacing/chosen_config_20261123.json").read_text(encoding="utf-8"))
R = ROOT / "data/reviews"


def punct(s):
    return re.sub(r"([۔،])(?=[^\s۔،])", r"\1 ", s)


def build_model():
    lm_fli = L.CharLM(CFG["order"])
    lm_fli.add(E.fli_lines())
    lm_c = L.CharLM(CFG["order"])
    lm_c.add([L.words_line(c["truth"]) for c in SS.load()], weight=CFG["wcards"])
    return [lm_fli, lm_c], [CFG["lam"], 1.0 - CFG["lam"]]


def add_spaces(text, model):
    lms, ws = model
    return L.insert_spaces(text, lms, ws, CFG["bonus"], CFG["where"])


def count(pairs):
    """pairs: [(truth text, ocr text, new text)] -> counts on the letter-identical pairs."""
    import collections
    sp = collections.Counter()
    for truth, ocr, new in pairs:
        tl, _, ts = SS.parse(truth)
        ol, _, os_ = SS.parse(ocr)
        nl, _, ns = SS.parse(new)
        assert nl == ol and os_ <= ns, "the inserter changed a letter or removed a space"
        if ol != tl:
            sp["rows_letters_differ"] += 1
            continue
        sp["rows"] += 1
        sp["truth"] += len(ts)
        for name, got in (("ocr", os_), ("new", ns)):
            sp[name + "_hit"] += len(ts & got)
            sp[name + "_missing"] += len(ts - got)
            sp[name + "_extra"] += len(got - ts)
    return sp


def line(sp, name):
    h, m, e = sp[name + "_hit"], sp[name + "_missing"], sp[name + "_extra"]
    p = h / (h + e) if h + e else 0
    r = h / sp["truth"] if sp["truth"] else 0
    return f"{name}: right {h}, missing {m}, extra {e}, errors {m + e}; precision {100 * p:.1f}%, recall {100 * r:.1f}%"


def main():
    model = build_model()
    rev = json.loads((R / "prose-banjara-dildarya/review_marks.json").read_text(encoding="utf-8"))
    pairs, skipped = [], 0
    for k, x in rev.items():
        if x["m"] == "unsure":
            continue
        ocr = punct(x["ocr"])
        if re.search(r"[0-9A-Za-z]", ocr) or len(SS.parse(ocr)[0]) < 4:
            skipped += 1
            continue
        truth = punct(x["text"] if x["m"] == "wrong" else x["ocr"])
        pairs.append((truth, ocr, add_spaces(ocr, model)))
    sp = count(pairs)
    print(f"A. prose rows: {len(pairs)} rows used ({skipped} skipped: digits, Latin or too short); {sp['rows']} with letters equal to the truth; truth has {sp['truth']} spaces")
    print("   " + line(sp, "ocr"))
    print("   " + line(sp, "new"))
    v = SS.vocab()
    sp2 = count([(t, o, S.fix_line(o, v, 4.0)) for t, o, _ in pairs])
    print("   splitter margin 4 (its word list holds these very books, so it is favoured): " + line(sp2, "new").replace("new:", ""))

    cards = json.loads((R / "prose-word-splits/splits_20261121.json").read_text(encoding="utf-8"))
    tot = {"truth": 0, "right": 0, "wrong": 0, "missing": 0, "tokens": 0}
    bad = []
    for c in cards:
        row = punct(c["context"])
        new = add_spaces(row, model)
        tok = c["token"]
        # find the token in the row by its letters, then read the spaces the model put inside it
        rl, _, rsp = SS.parse(row)
        nl, _, nsp = SS.parse(new)
        tl, _, tsp = SS.parse(tok)
        tt, _, ttruth = SS.parse(c["text"])
        assert tl == tt
        start = rl.find(tl)
        if start < 0:
            continue
        inside = {i - start for i in nsp if start < i < start + len(tl)}
        orig_in = {i - start for i in rsp if start < i < start + len(tl)}
        tot["tokens"] += 1
        tot["truth"] += len(ttruth)
        tot["right"] += len(inside & ttruth)
        tot["wrong"] += len(inside - ttruth)
        tot["missing"] += len(ttruth - inside)
        if inside - ttruth:
            bad.append((tok, c["text"], new))
    print(f"B. 66 split cards: {tot['tokens']} tokens found; truth spaces {tot['truth']}; model: right {tot['right']}, wrong {tot['wrong']}, missing {tot['missing']}")
    print("   old splitter on these cards (score_splits.py, 2026-11-21): proposed 72, right 66, wrong 6, missing 4")
    for b in bad:
        print("   wrong cut:", b[0], "| truth:", b[1])


if __name__ == "__main__":
    main()
