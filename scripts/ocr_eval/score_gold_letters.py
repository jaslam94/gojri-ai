"""Arabic-letter error of every OCR run on the gold pages (spaces, Latin and short vowels ignored).

Same normalisation as scripts/utrnet_arabic_eval.py: NFC, short-vowel marks removed, only Arabic-block
characters kept, ك=ک and ه=ہ folded (ھ stays separate). Error = Levenshtein distance of the whole page
string / number of gold letters. Run: py -3 -X utf8 scripts/ocr_eval/score_gold_letters.py
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRANS = ROOT / "data" / "gold" / "transcriptions"
MARKS = re.compile(r"[ً-ٰٟۖ-ۭؐ-ؚ]")
ARAB = re.compile(r"[؀-ۿ]")
FOLD = str.maketrans({"ك": "ک", "ه": "ہ"})
SKIP = re.compile(r"^\[.*\]$")


def arabic(s):
    return "".join(ARAB.findall(MARKS.sub("", unicodedata.normalize("NFC", s)))).translate(FOLD)


def prep(path):
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not SKIP.match(l.strip())]
    return arabic(" ".join(lines))


def ed(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


tags = sys.argv[1:]
tot = {}
print(f"{'page':26s} {'run':26s} {'gold':>5s} {'err':>5s} {'CER':>7s}")
for d in sorted(p for p in TRANS.iterdir() if p.is_dir()):
    gold_file = d / f"{d.name}_gold.txt"
    if not gold_file.exists():
        continue
    gold = prep(gold_file)
    for f in sorted(d.glob(f"{d.name}_*_original.txt")):
        tag = f.stem[len(d.name) + 1:-len("_original")]
        if tags and tag not in tags:
            continue
        e = ed(gold, prep(f))
        t = tot.setdefault(tag, [0, 0])
        t[0] += e
        t[1] += len(gold)
        print(f"{d.name:26s} {tag:26s} {len(gold):5d} {e:5d} {100 * e / len(gold):6.1f}%")
print()
for tag, (e, n) in tot.items():
    print(f"POOLED {tag:26s} {e}/{n} = {100 * e / n:.1f}%")
