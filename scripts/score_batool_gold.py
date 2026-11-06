"""Score Batool decode of page 25 against dict_alif gold."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from score_gold import align, classify_sub, tokens

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "data/gold/transcriptions/dict_alif/dict_alif_gold.txt"
HYP = ROOT / "data/decode/out/gojri-english-dictionary/page-0025.txt"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    gold = GOLD.read_text(encoding="utf-8")
    hyp = HYP.read_text(encoding="utf-8")
    # Gold file starts with page number / header lines; keep scoring consistent
    # with score_gold tokenization (skips bracket lines).
    ref = tokens(gold)
    hyp_toks = tokens(hyp)
    ops = align(ref, hyp_toks)
    n_ref = len(ref)
    errs = sum(1 for op, _, _ in ops if op != "eq")
    wer = errs / n_ref if n_ref else 0.0
    print(f"ref_tokens={n_ref} hyp_tokens={len(hyp_toks)}")
    print(f"errors={errs} WER={wer:.1%}")
    print()
    print("--- first 40 mismatches ---")
    shown = 0
    for op, g, h in ops:
        if op == "eq":
            continue
        kind = classify_sub(g or "", h or "") if op == "sub" else op
        print(f"  {op:3} [{kind}] gold={g!r} hyp={h!r}")
        shown += 1
        if shown >= 40:
            break
    print()
    print("--- hyp preview (first 25 lines) ---")
    for i, line in enumerate(hyp.splitlines()[:25], 1):
        print(f"{i:2}| {line}")


if __name__ == "__main__":
    main()
