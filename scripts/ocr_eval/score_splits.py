"""Score the word splitter (space_fix.py) against the speaker's 66 split cards (space_review.py).

Each card holds one glued token of the Banjara or Dil-Darya OCR and the speaker's text for it (spaces follow meaning).
A card's truth is the speaker's text; the Accept/Reject mark is not used, because the text decides (a proposal that adds
only right spaces but misses one was marked Reject once). Per card, the splitter's spaces are compared with the truth
by letter position (marks ignored). Letters never change.
Run: py -3 -X utf8 scripts/ocr_eval/score_splits.py [--margin 4] [--min-piece 1 2]
The word list needs the local FLI corpus and the full-book OCR runs, as in score_spacing.py.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_spacing as SS  # noqa: E402
import space_fix as S  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--margin", type=float, default=4.0)
    ap.add_argument("--min-piece", type=int, nargs="*", default=[1, 2])
    a = ap.parse_args()
    cards = json.loads((ROOT / "data/reviews/prose-word-splits/splits_20261121.json").read_text(encoding="utf-8"))
    v = SS.vocab()
    print(f"{len(cards)} cards; margin {a.margin}")
    for mp in a.min_piece:
        S.MIN_PIECE = mp
        n = right = wrong = missing = split = 0
        for c in cards:
            tl, _, ts = SS.parse(c["text"])
            out = S.split_token(c["token"].strip(S.PUNCT), v, a.margin)
            _, _, ps = SS.parse(out)
            n += len(ts)
            right += len(ps & ts)
            wrong += len(ps - ts)
            missing += len(ts - ps)
            split += out != c["token"].strip(S.PUNCT)
        print(f"min piece {mp}: tokens split {split}; spaces added {right + wrong}, right {right}, wrong {wrong}; truth has {n}, still missing {missing}")


if __name__ == "__main__":
    main()
