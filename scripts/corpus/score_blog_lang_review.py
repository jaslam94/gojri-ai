"""Score the Gojri-only filter against the speaker's marks.

Input: the marks file the review page downloads (blog_lang_tags.json: card id -> gju|urd|same|mixed|unsure) and
datasets/gojri-blogs/review/sample.json (the draft tag of each card).
Output: a table draft tag x speaker tag, then (stratified by the draft tag, weighted by words in the whole blog) the estimated
share of the kept words that are Gojri, and the Gojri words lost in the dropped and unsure parts.

Run: py -3 -X utf8 scripts/corpus/score_blog_lang_review.py path/to/blog_lang_tags.json [--blog gojrizubanoadab]
"""
import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BLOGS = ROOT / "datasets/gojri-blogs"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("marks")
    ap.add_argument("--blog", default="gojrizubanoadab")
    a = ap.parse_args()
    marks = json.loads(Path(a.marks).read_text(encoding="utf-8"))
    sample = json.loads((BLOGS / "review/sample.json").read_text(encoding="utf-8"))
    rows = [s for s in sample if s["blog"] == a.blog and str(s["id"]) in marks]
    tab = defaultdict(Counter)
    for s in rows:
        tab[s["draft"]][marks[str(s["id"])]] += 1
    cols = ["gju", "urd", "same", "mixed", "unsure"]
    print(f"{'draft':8}" + "".join(f"{c:>8}" for c in cols) + f"{'n':>6}")
    for d in ("gju", "urd", "unsure"):
        print(f"{d:8}" + "".join(f"{tab[d][c]:>8}" for c in cols) + f"{sum(tab[d].values()):>6}")
    words = Counter()
    for l in open(BLOGS / "chunks.jsonl", encoding="utf-8"):
        r = json.loads(l)
        if r["blog"] == a.blog:
            words[r["tag"]] += r["words"]
    est = Counter()
    for d, c in tab.items():
        n = sum(c.values())
        if not n:
            continue
        for m, k in c.items():
            est[(d, m)] = words[d] * k / n
    kept = words["gju"]
    good = est[("gju", "gju")] + est[("gju", "same")]
    print(f"\nwords in the whole blog by draft tag: {dict(words)}")
    print(f"kept (draft gju): {kept}; estimated Gojri or same-in-both: {good:.0f} ({100 * good / kept:.1f}%)")
    print(f"estimated Urdu words kept by mistake: {est[('gju', 'urd')]:.0f}")
    lost = est[("urd", "gju")] + est[("unsure", "gju")]
    print(f"estimated Gojri words outside the kept set: {lost:.0f} (from urd {est[('urd', 'gju')]:.0f}, unsure {est[('unsure', 'gju')]:.0f})")
    total = good + lost
    if total:
        print(f"filter recall on Gojri words: {100 * good / total:.1f}%")


if __name__ == "__main__":
    main()
