"""Summarize an exported review file (Export JSON button in data/review/index.html).

  py -3 -X utf8 scripts/review/summarize_review.py path/to/gojri_review_marks_*.json
  py -3 -X utf8 scripts/review/summarize_review.py marks.json --out data/review/summary.md

Writes Markdown. The console cannot print Arabic script, so use --out and read the file.
Letter changes treat ݨ (U+0768) and ݩ (U+0769) as one letter. Spelling is not normalised.
"""

from __future__ import annotations

import argparse
import difflib
import json
import math
import sys
from collections import Counter
from pathlib import Path

SAME_LETTER = {"ݩ": "ݨ"}


def norm(s: str) -> str:
    return "".join(SAME_LETTER.get(c, c) for c in s)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    a = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, (c - a) / d), min(1.0, (c + a) / d)


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def rate_line(name: str, k: int, n: int) -> str:
    lo, hi = wilson(k, n)
    return f"- {name}: {k} of {n} = {pct(k / n if n else 0)} (95% CI {pct(lo)} to {pct(hi)})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("marks")
    ap.add_argument("--out")
    args = ap.parse_args()
    d = json.loads(Path(args.marks).read_text(encoding="utf-8"))

    lines = d.get("lines", [])
    ok = [x for x in lines if "ok" in x["marks"]]
    crop = [x for x in lines if "crop" in x["marks"] and "ok" not in x["marks"]]
    wrong = [x for x in lines if x not in ok and x not in crop]
    n = len(ok) + len(wrong)
    out = ["# Dictionary review summary", "", "## Line sample", ""]
    out.append(f"Reviewed {len(lines)} lines. Bad crop (left out of the rate): {len(crop)}.")
    out.append("")
    out.append(rate_line("Any error", len(wrong), n))
    out.append(rate_line("Wrong letters", sum("letters" in x["marks"] for x in wrong), n))
    out.append(rate_line("Wrong spacing", sum("spacing" in x["marks"] for x in wrong), n))
    if not wrong and n >= 30:
        out.append(f"- Rule of three: 0 errors in {n} lines, so the error rate is probably below {pct(3 / n)}.")
    causes = Counter(x.get("cause") or "unknown" for x in wrong)
    out.append(
        f"- Source of the errors: raw decode also wrong {causes['raw_wrong']} (table or decode rule), "
        f"raw decode right {causes['raw_right']} (Pass 2 broke it), unknown {causes['unknown']}."
    )

    confusions: Counter = Counter()
    for x in wrong:
        if not x.get("fix"):
            continue
        a, b = norm(x["label"]), norm(x["fix"])
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if op != "equal":
                confusions[(a[i1:i2], b[j1:j2])] += 1
    if confusions:
        out += ["", "Most common changes (label to your fix):", ""]
        out += [f"- `{a or '(nothing)'}` to `{b or '(nothing)'}`: {c}" for (a, b), c in confusions.most_common(25)]

    out += ["", "## Table check", ""]
    table = d.get("table", [])
    cnt = Counter(t["mark"] for t in table)
    out.append(f"Right {cnt['right']}, wrong {cnt['wrong']}, unsure {cnt['unsure']}, not checked {160 - len(table)}.")
    for t in table:
        if t["mark"] in ("wrong", "unsure"):
            out.append(
                f"- {t['code']} {t['mark']}: table says `{t['table_output']}`, "
                f"your letters `{t.get('fix', '')}`. Used {t['uses']} times on {t['pages']} pages. {t.get('note', '')}"
            )

    text = "\n".join(out) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print("wrote", args.out)
    else:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        print(text)


if __name__ == "__main__":
    main()
