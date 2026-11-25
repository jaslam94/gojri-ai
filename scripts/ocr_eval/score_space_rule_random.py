"""Test the character n-gram space inserter on the 120 RANDOM prose rows that the speaker fixed (random_ocr_review.html).

Why: the "8 letters or more" rule was picked on the 106 Gojri poetry cards, so it is only a guess. These rows are random, were never used to pick it,
and the speaker's text box is the truth. Rows where the OCR letters differ from the truth letters are skipped (their spaces cannot be aligned).
Same rules as space_review_model.py: punctuation rule on both sides, insert only, a proposal is right when every space it adds is in the truth.

Run: py -3 -X utf8 scripts/ocr_eval/score_space_rule_random.py [marks.json]
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_prose_spacing as P  # noqa: E402
import score_spacing as SS  # noqa: E402
from space_review_model import tokens_with_splits  # noqa: E402

MARKS = ROOT / "data/reviews/random-ocr-rows/review_marks_20261126.json"
TAGS = ROOT / "data/reviews/prose-language/lang_tags_final_20261124.json"


def main():
    marks = json.loads(Path(sys.argv[1] if len(sys.argv) > 1 else MARKS).read_text(encoding="utf-8"))
    tags = json.loads(TAGS.read_text(encoding="utf-8"))
    model = P.build_model()
    rows = skipped = 0
    missing_total = extra_total = truth_sp = 0
    props = []  # (tag, token letters, right, n spaces added, n added right)
    found = collections.Counter()  # missing truth spaces found, by token length bucket
    for k, v in marks.items():
        ocr, truth = P.punct(v["ocr"]), P.punct(v["text"])
        tl, _, ts = SS.parse(truth)
        ol, _, os_ = SS.parse(ocr)
        if ol != tl:
            skipped += 1
            continue
        rows += 1
        truth_sp += len(ts)
        missing_total += len(ts - os_)
        extra_total += len(os_ - ts)
        new = P.add_spaces(ocr, model)
        for tok, split, start in tokens_with_splits(ocr, new):
            added = {start + i for i in SS.parse(split)[2]}
            n = len(SS.parse(tok)[0])
            ok = added <= ts
            props.append((tags[k]["tag"], n, ok, len(added), len(added & ts)))
    print(f"rows scored {rows}, skipped (letters differ) {skipped}")
    print(f"truth spaces {truth_sp}, missing in OCR {missing_total}, extra in OCR {extra_total}")
    def rule(name, f):
        sel = [p for p in props if f(p)]
        ad = sum(p[3] for p in sel)
        adr = sum(p[4] for p in sel)
        print(f"{name:28s} proposals {len(sel):3d}, right {sum(p[2] for p in sel):3d}, wrong {sum(not p[2] for p in sel):3d} | "
              f"spaces added {ad:3d}, right {adr:3d}, found {100 * adr / max(missing_total, 1):4.1f}% of the missing spaces")
    rule("model, all tokens", lambda p: True)
    for t in (6, 8, 10, 12):
        rule(f"model, token {t}+ letters", lambda p, t=t: p[1] >= t)
    rule("model, Gojri rows only", lambda p: p[0] == "gju")
    rule("model 8+, Gojri rows only", lambda p: p[0] == "gju" and p[1] >= 8)
    print("by token length (all proposals):")
    for lo, hi in ((0, 5), (6, 7), (8, 10), (11, 99)):
        sel = [p for p in props if lo <= p[1] <= hi]
        print(f"  {lo}-{hi} letters: {len(sel)} proposals, {sum(p[2] for p in sel)} right")


if __name__ == "__main__":
    main()
