"""Write ھ (do chashmi heh) at the start of Gojri words in the lexicon.

The Gojri print writes a word that starts with /h/ with ھ: 448 of 475
word-initial heh forms in the Gojri-English Dictionary text (user ruling,
2026-11-05). Aksharamukha maps Devanagari ह to ہ, so the lexicon had ہ there.
This changes the first letter of every Arabic-script word in the `nastaliq`
column from ہ (U+06C1) or ه (U+0647) to ھ (U+06BE). Rows tagged
`human_verified` are not touched. Other columns and line ends stay as they are.
The script can run twice with the same result.

Run: py -3 -X utf8 scripts/lexicon_initial_heh.py [--dry-run]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TSV = ROOT / "data" / "lexicon" / "gojri_lexicon_final.tsv"
NASTALIQ, QUALITY = 5, 7  # column positions in the TSV
MARKS = "ً-ٰٟ"
WORD_START = re.compile(rf"(?<![؀-ۿ])([{MARKS}]*)[ہه](?=[؀-ۿ])")


def main():
    raw = TSV.read_bytes().decode("utf-8")
    lines = raw.split("\n")
    changed_rows = changed_words = 0
    for i, line in enumerate(lines[1:], 1):
        cols = line.rstrip("\r").split("\t")
        if len(cols) <= QUALITY or cols[QUALITY] == "human_verified":
            continue
        new, n = WORD_START.subn(lambda m: m.group(1) + "ھ", cols[NASTALIQ])
        if n:
            cols[NASTALIQ] = new
            lines[i] = "\t".join(cols) + ("\r" if line.endswith("\r") else "")
            changed_rows += 1
            changed_words += n
    print(f"{changed_words} words changed in {changed_rows} rows")
    if "--dry-run" not in sys.argv:
        TSV.write_bytes("\n".join(lines).encode("utf-8"))


if __name__ == "__main__":
    main()
