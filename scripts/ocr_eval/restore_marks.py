"""Restore dropped short-vowel marks (pesh, zer, and so on) in OCR text from a marked Gojri word list.

UTRNet reads the letters well but leaves out many marks. A mark is part of how a Gojri word is spelled, so a word list with
marks can put them back. Rule: for each OCR word that has no mark, look up its bare letters (marks removed, ك=ک, ه=ہ) in the
list; if the list spells that bare word with marks in at least --min-share of its marked-or-unmarked uses, copy the marks
onto the OCR letters (same letter count, so the OCR letters never change). A word that already carries a mark is left alone.

Word list: the Arabic-script words of data/synth/real_pairs/labels_merged_clean.jsonl (11,126 dictionary lines, marks from
the decoded font codes) plus labels_review_test.jsonl (the 200 lines the speaker checked).

Test (30 marked Kahawat cards): py -3 -X utf8 scripts/ocr_eval/restore_marks.py --score data/ocr/kahawat-gpu7/score_marks.json
"""
import argparse
import collections
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MARK = re.compile("[ً-ٰٟۖ-ۭ]")
FOLD = str.maketrans({"ك": "ک", "ه": "ہ", "ۃ": "ہ", "ي": "ی", "ى": "ی"})


def split_marks(word):
    """[(letter, marks)] for a word: marks attach to the letter before them."""
    out = []
    for ch in unicodedata.normalize("NFC", word):
        if MARK.match(ch) and out:
            out[-1][1] += ch
        else:
            out.append([ch, ""])
    return [(a, b) for a, b in out]


def bare(word):
    return "".join(a for a, _ in split_marks(word)).translate(FOLD)


def build_wordlist(paths):
    forms = collections.defaultdict(collections.Counter)  # bare -> Counter(marks tuple)
    for p in paths:
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            for tok in re.findall(r"[؀-ۿ]+", r.get("text_fix") or r["text"]):
                sm = split_marks(tok)
                letters = [a for a, _ in sm if re.match(r"[ؠ-يٮ-ۓەۮ-ۿ]", a)]
                if len(letters) != len(sm) or len(sm) < 2:
                    continue
                forms[bare(tok)][tuple(b for _, b in sm)] += 1
    return forms


def restore(text, forms, min_share=0.7, min_count=1):
    out = []
    for tok in re.split(r"(\s+)", text):
        if not tok.strip() or MARK.search(tok) or not re.fullmatch(r"[؀-ۿ]+", tok):
            out.append(tok)
            continue
        sm = split_marks(tok)
        c = forms.get(bare(tok))
        if not c or len(sm) < 2:
            out.append(tok)
            continue
        best, n = c.most_common(1)[0]
        total = sum(c.values())
        if len(best) != len(sm) or not any(best) or n < min_count or n / total < min_share:
            out.append(tok)
            continue
        out.append("".join(a + m for (a, _), m in zip(sm, best)))
    return "".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", required=True, help="score_marks.json of a Kahawat run")
    ap.add_argument("--min-share", type=float, nargs="+", default=[0.5, 0.7, 0.9])
    args = ap.parse_args()
    base = ROOT / "data" / "synth" / "real_pairs"
    forms = build_wordlist([base / "labels_merged_clean.jsonl", base / "labels_review_test.jsonl"])
    print("word list:", len(forms), "bare words;", sum(1 for c in forms.values() if any(any(k) for k in c)), "with marks")
    rows = [r for r in json.loads(Path(args.score).read_text(encoding="utf-8")) if r["ocr"] is not None]
    marks_of = lambda s: "".join(MARK.findall(unicodedata.normalize("NFC", s)))  # noqa: E731
    nm = sum(len(marks_of(r["trimmed"])) for r in rows)
    print(f"fields {len(rows)}, marks in truth {nm}, baseline mark errors {sum(r['mark_ed'] for r in rows)}")
    for ms in args.min_share:
        err = ins = good = exact_marks = 0
        for r in rows:
            new = restore(r["ocr"], forms, ms)
            e = O.ed(marks_of(r["trimmed"]), marks_of(new))
            err += e
            exact_marks += e == 0
            assert O.arabic(new) == O.arabic(r["ocr"]), "letters changed"
        print(f"min share {ms}: mark errors {err} of {nm} ({100 * err / nm:.0f}%), fields with exact marks {exact_marks} of {len(rows)}")


if __name__ == "__main__":
    main()
