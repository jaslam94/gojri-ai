"""Score the OCR text of Kahawat-Kosh idioms against the speaker's spacing review (build_spacing_review.py).

Truth of a card: the speaker's text (marked "fixed") or the OCR text (marked "ok"). "unsure" cards are skipped.
Spaces follow meaning (ruling 2026-11-16), so the OCR text, which often glues words, is compared with that truth.
Three errors, scored apart (same folds as score_prose_review.py): letters (marks, spaces, punctuation removed),
marks (the mark sequence), and spaces. Space errors are counted only on cards whose letters match, so a letter
fix does not shift the positions. A space "position" is the index of the letter that follows it; punctuation and
marks are ignored, so the punctuation rule does not matter here.

Run:  py -3 -X utf8 scripts/ocr_eval/score_spacing.py
      py -3 -X utf8 scripts/ocr_eval/score_spacing.py --fix 4     also scores the word splitter space_fix.py (margin 4)
--fix needs the local word list sources (FLI corpus and the full-book OCR runs), as space_review.py does.
"""
import argparse
import collections
import glob
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import space_fix as S  # noqa: E402

D = ROOT / "data/reviews/kahawat-spacing"
SAME = str.maketrans({"ك": "ک", "ه": "ہ", "ݨ": "ݩ"})


def parse(text):
    """Return (letters, marks, spaces): letters as a string, marks as a string, spaces as a set of letter indexes."""
    text = unicodedata.normalize("NFC", text).translate(SAME)
    letters, marks, spaces, gap = [], [], set(), False
    for c in text:
        cat = unicodedata.category(c)
        if cat.startswith("M"):
            marks.append(c)
        elif c.isspace():
            gap = True
        elif cat[0] in "PC":
            continue
        else:
            if gap and letters:
                spaces.add(len(letters))
            gap = False
            letters.append(c)
    return "".join(letters), "".join(marks), spaces


def edit(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


def load():
    rev = json.loads((D / "spacing_marks_20261121.json").read_text(encoding="utf-8"))
    smp = json.loads((D / "sample.json").read_text(encoding="utf-8"))
    out = []
    for i, c in enumerate(smp):
        r = rev.get(str(i))
        if r and r["m"] != "unsure":
            out.append({"id": i, "page": c["page"], "ocr": c["text"], "truth": r["text"] if r["m"] == "fixed" else c["text"], "m": r["m"]})
    return out


def vocab():
    texts = [open(f, encoding="utf-8").read().replace("\uffff", "") for f in glob.glob(str(ROOT / "datasets/Gojri Language Corpus/*.txt"))]
    for jf in glob.glob(str(ROOT / "data/ocr/prose-aws-full2/*/dpi300/page_*.json")):
        texts += [r["text"] for r in json.load(open(jf, encoding="utf-8"))["rows"]]
    v = S.build_vocab(texts)
    v.c = {w: c for w, c in v.c.items() if c >= 3}
    v.n = sum(v.c.values())
    return v


def score(cards, key, label):
    n = len(cards)
    exact = letters_ok = marks_ok = 0
    err = tot = 0
    sp = collections.Counter()
    for c in cards:
        tl, tm, ts = parse(c["truth"])
        ol, om, os_ = parse(c[key])
        d = edit(ol, tl)
        err += d
        tot += len(tl)
        marks_ok += om == tm
        if ol == tl:
            letters_ok += 1
            sp["lines"] += 1
            sp["truth"] += len(ts)
            sp["ocr"] += len(os_)
            sp["hit"] += len(ts & os_)
            sp["missing"] += len(ts - os_)
            sp["extra"] += len(os_ - ts)
            sp["lines_exact"] += ts == os_
            sp["missing_after_nonjoiner"] += sum(1 for i in ts - os_ if tl[i - 1] in S.NONJOIN)
            exact += ts == os_ and om == tm
    print(f"== {label}: {n} cards")
    print(f"letter error {err}/{tot} = {100 * err / tot:.1f}%; cards with identical letters {letters_ok}; identical marks {marks_ok}")
    if sp["lines"]:
        p = sp["hit"] / sp["ocr"] if sp["ocr"] else 0
        r = sp["hit"] / sp["truth"]
        print(f"spaces on the {sp['lines']} letter-identical cards: truth {sp['truth']}, text {sp['ocr']}; hit {sp['hit']}, missing {sp['missing']} "
              f"(after a non-joining letter {sp['missing_after_nonjoiner']}), extra {sp['extra']}; precision {100 * p:.1f}%, recall {100 * r:.1f}%; "
              f"cards with exact spaces {sp['lines_exact']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", type=float, nargs="*", help="also score space_fix.py at these margins")
    a = ap.parse_args()
    cards = load()
    print(collections.Counter(c["m"] for c in cards))
    score(cards, "ocr", "OCR text as read")
    if a.fix:
        v = vocab()
        for mg in a.fix:
            for c in cards:
                c["fix"] = S.fix_line(re.sub(r"([۔،])(?=[^\s۔،])", r"\1 ", c["ocr"]), v, mg)
            score(cards, "fix", f"OCR text + word splitter, margin {mg}")


if __name__ == "__main__":
    main()
