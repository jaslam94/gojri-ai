"""Score a crop run (SageMaker output jsonl from the Qaari or TrOCR job) against the 200 reviewed dictionary lines.
Output rows are grouped by whichever of model / image / decode / variant they contain.

Same metric as scripts/utrnet_arabic_eval.py: NFC, short-vowel marks removed, only Arabic-block characters
kept, ك=ک and ه=ہ folded (ھ separate); Levenshtein distance summed over lines / reference letters.
The crops of one line are joined left to right (idx order), as in the UTRNet test. The UTRNet column comes
from data/utrnet-test/results.tsv, so both systems are scored on identical references.

Run: py -3 -X utf8 scripts/ocr_eval/score_qaari.py <qaari_out.jsonl>
"""
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MARKS = re.compile(r"[ً-ٰٟۖ-ۭؐ-ؚ]")
ARAB = re.compile(r"[؀-ۿ]")
FOLD = str.maketrans({"ك": "ک", "ه": "ہ"})


def arabic(s):
    return "".join(ARAB.findall(MARKS.sub("", unicodedata.normalize("NFC", s)))).translate(FOLD)


def ed(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


rows = list(csv.DictReader((ROOT / "data/utrnet-test/results.tsv").open(encoding="utf-8"), delimiter="\t"))
ref = {r["page_line"]: r["reference_arabic"] for r in rows}
systems = {"utrnet_pad0": {r["page_line"]: r["utrnet_pad0"] for r in rows}}

by = defaultdict(lambda: defaultdict(list))
for line in Path(sys.argv[1]).open(encoding="utf-8"):
    d = json.loads(line)
    if "error" in d:
        print("model failed:", d["model"], d["error"][:150])
        continue
    key = "_".join(str(d[k]).split("/")[-1] for k in ("model", "image", "decode", "variant") if k in d)
    by[key][d["page_line"]].append((d["idx"], d["text"]))
for v, lines in by.items():
    systems[v] = {k: " ".join(t for _, t in sorted(x)) for k, x in lines.items()}

print(f"{'system':44s} {'errors':>7s} {'letters':>8s} {'error':>7s} {'exact':>6s}")
for name, out in systems.items():
    e = n = x = 0
    for k, r in ref.items():
        d = ed(r, arabic(out.get(k, "")))
        e, n, x = e + d, n + len(r), x + (d == 0)
    print(f"{name:44s} {e:7d} {n:8d} {100 * e / n:6.1f}% {x:6d}")
