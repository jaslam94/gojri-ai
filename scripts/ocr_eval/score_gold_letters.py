"""Arabic-letter error of every OCR run on the gold pages (spaces, Latin and short vowels ignored).

Same normalisation as scripts/utrnet_arabic_eval.py: NFC, short-vowel marks removed, only Arabic and
Arabic Supplement characters kept (U+0750-077F holds ݨ), ك=ک, ه=ہ and ݩ=ݨ folded (ھ stays
separate). Before 2026-11-20 the supplement was left out, so ݨ counted as an English character. Error = Levenshtein distance of the whole page
string / number of gold letters. Add --latin to score the English (non-Arabic, non-space) characters instead.
Run: py -3 -X utf8 scripts/ocr_eval/score_gold_letters.py [--latin] [run tags...]
"""
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRANS = ROOT / "data" / "gold" / "transcriptions"
MARKS = re.compile(r"[ً-ٰٟۖ-ۭؐ-ؚ]")
ARAB = re.compile(r"[؀-ۿݐ-ݿ]")  # Arabic and Arabic Supplement (the supplement holds ݨ, Gojri retroflex noon)
FOLD = str.maketrans({"ك": "ک", "ه": "ہ", "ݩ": "ݨ"})
SKIP = re.compile(r"^\[.*\]$")


def arabic(s):
    return "".join(ARAB.findall(MARKS.sub("", unicodedata.normalize("NFC", s)))).translate(FOLD)


LATIN_MODE = "--latin" in sys.argv
if LATIN_MODE:
    sys.argv.remove("--latin")


def latin(s):
    """Non-Arabic, non-space characters (English words, digits, brackets), case kept."""
    s = MARKS.sub("", unicodedata.normalize("NFC", s))
    return "".join(c for c in s if not ARAB.match(c) and not c.isspace())


def prep(path):
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip() and not SKIP.match(l.strip())]
    return latin(" ".join(lines)) if LATIN_MODE else arabic(" ".join(lines))


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
