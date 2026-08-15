"""Score gold-set OCR originals against <page>_gold.txt.

Word error ignores spacing around : ، ۔ and skips illustration/photo/blank
bracket lines. Prints a table plus classified substitution samples.

Run: py -3 scripts/score_gold.py
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANS = ROOT / "data" / "gold" / "transcriptions"

DIACRITICS = re.compile(r"[\u064B-\u065F\u0670\u06D6-\u06ED\u08E4-\u08FF]")
HONORIFIC = re.compile(r"[\u0610-\u0615]")
HEH = str.maketrans({"ہ": "H", "ھ": "H", "ه": "H"})
EAST_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")

SKIP_LINE = re.compile(
    r"^\[(illustration|photo|blank|badge|footer|stamp|handwritten|oval|logo)[:\]]",
    re.I,
)

PAGES = [
    "dict_alif",
    "gojri_adbiyaat",
    "gojri_ghazal",
    "kahawat_kosh",
    "kulyate_spread_a_right",
    "kulyate_spread_b_left",
    "mahatma_gandhi",
    "nazir_spread_a_right",
    "nazir_spread_b_left",
    "shingar_textbook",
    "louk_warsti",
    "primer_pehli",
]


def tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFC", text)
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if SKIP_LINE.match(s) or (s.startswith("[") and s.endswith("]")):
            continue
        lines.append(s)
    text = " ".join(lines)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\s+([:،۔,])", r"\1", text)
    text = re.sub(r"([:،۔,])\s+", r"\1 ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.split() if text else []


def align(ref: list[str], hyp: list[str]) -> list[tuple[str, str | None, str | None]]:
    n, m = len(ref), len(hyp)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    bt = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0] = i
        bt[i][0] = "del"
    for j in range(1, m + 1):
        dp[0][j] = j
        bt[0][j] = "ins"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if ref[i - 1] == hyp[j - 1] else 1
            choices = (
                (dp[i - 1][j] + 1, "del"),
                (dp[i][j - 1] + 1, "ins"),
                (dp[i - 1][j - 1] + cost, "eq" if cost == 0 else "sub"),
            )
            dp[i][j], bt[i][j] = min(choices, key=lambda x: x[0])
    ops = []
    i, j = n, m
    while i > 0 or j > 0:
        op = bt[i][j]
        if op == "eq" or op == "sub":
            ops.append((op, ref[i - 1], hyp[j - 1]))
            i -= 1
            j -= 1
        elif op == "del":
            ops.append(("del", ref[i - 1], None))
            i -= 1
        else:
            ops.append(("ins", None, hyp[j - 1]))
            j -= 1
    ops.reverse()
    return ops


def strip_dia(s: str) -> str:
    return DIACRITICS.sub("", s)


def classify_sub(g: str, h: str) -> str:
    if strip_dia(g) == strip_dia(h):
        return "diacritic"
    g_h, h_h = HONORIFIC.sub("", g), HONORIFIC.sub("", h)
    if strip_dia(g_h) == strip_dia(h_h):
        return "honorific"
    if strip_dia(g.translate(HEH)) == strip_dia(h.translate(HEH)):
        return "heh"
    if g.translate(EAST_DIGITS) == h.translate(EAST_DIGITS) and g != h:
        return "digit_system"
    g_alnum = re.sub(r"[^\w\u0600-\u06FF]", "", g, flags=re.UNICODE)
    h_alnum = re.sub(r"[^\w\u0600-\u06FF]", "", h, flags=re.UNICODE)
    if g_alnum and g_alnum == h_alnum:
        return "punct_other"
    return "letter_or_word"


def merge_splits(ops: list[tuple[str, str | None, str | None]]) -> list[tuple]:
    """Collapse insert/delete runs that concatenate to the other side."""
    merged = []
    i = 0
    while i < len(ops):
        op, g, h = ops[i]
        if op == "del":
            dels = [g]
            j = i + 1
            while j < len(ops) and ops[j][0] == "del":
                dels.append(ops[j][1])
                j += 1
            ins = []
            k = j
            while k < len(ops) and ops[k][0] == "ins":
                ins.append(ops[k][2])
                k += 1
            if ins and "".join(dels) == "".join(ins):
                merged.append(("split_join", " ".join(dels), " ".join(ins)))
                i = k
                continue
        if op == "ins":
            ins = [h]
            j = i + 1
            while j < len(ops) and ops[j][0] == "ins":
                ins.append(ops[j][2])
                j += 1
            dels = []
            k = j
            while k < len(ops) and ops[k][0] == "del":
                dels.append(ops[k][1])
                k += 1
            if dels and "".join(dels) == "".join(ins):
                merged.append(("split_join", " ".join(dels), " ".join(ins)))
                i = k
                continue
        merged.append((op, g, h))
        i += 1
    return merged


def discover_originals(page: str) -> list[Path]:
    folder = TRANS / page
    return sorted(p for p in folder.glob(f"{page}_*_original.txt"))


def tag_from_name(page: str, path: Path) -> str:
    stem = path.stem
    rest = stem[len(page) + 1 :]
    if rest.endswith("_original"):
        rest = rest[: -len("_original")]
    return rest


def score_pair(gold: list[str], hyp: list[str]) -> dict:
    raw_ops = align(gold, hyp)
    ops = merge_splits(raw_ops)
    cats = Counter()
    samples = defaultdict(list)
    errors = 0
    for item in ops:
        op = item[0]
        if op == "eq":
            continue
        errors += 1
        if op == "del":
            cat = "missing"
            pair = (item[1], "")
        elif op == "ins":
            cat = "extra"
            pair = ("", item[2])
        elif op == "split_join":
            cat = "split_join"
            pair = (item[1], item[2])
        else:
            cat = classify_sub(item[1], item[2])
            pair = (item[1], item[2])
        cats[cat] += 1
        if len(samples[cat]) < 8:
            samples[cat].append(pair)
    n = len(gold)
    return {
        "gold_words": n,
        "hyp_words": len(hyp),
        "errors": errors,
        "wer": (100.0 * errors / n) if n else 0.0,
        "cats": dict(cats),
        "samples": {k: v for k, v in samples.items()},
    }


def main() -> None:
    import sys

    sys.stdout.reconfigure(encoding="utf-8")
    rows = []
    print("page | run | gold | err | WER | categories")
    print("-" * 100)
    for page in PAGES:
        gold_path = TRANS / page / f"{page}_gold.txt"
        gold = tokens(gold_path.read_text(encoding="utf-8"))
        for path in discover_originals(page):
            tag = tag_from_name(page, path)
            hyp = tokens(path.read_text(encoding="utf-8"))
            rec = score_pair(gold, hyp)
            rec["page"] = page
            rec["tag"] = tag
            rows.append(rec)
            cat_s = " ".join(f"{k}={v}" for k, v in sorted(rec["cats"].items()))
            print(
                f"{page:24} {tag:28} {rec['gold_words']:4} "
                f"{rec['errors']:4} {rec['wer']:5.1f}%  {cat_s}"
            )

    print("\n=== samples by model family (active runs) ===")
    families = {
        "composer": lambda t: t.startswith("composer"),
        "gemini": lambda t: t.startswith("gemini"),
        "sonnet_4.6": lambda t: t.startswith("sonnet_4.6"),
        "sonnet_5_cc": lambda t: t.startswith("sonnet_5_cc"),
    }
    for fam, pred in families.items():
        fam_cats = Counter()
        fam_samples = defaultdict(list)
        n_err = 0
        n_gold = 0
        n_pages = 0
        for rec in rows:
            if not pred(rec["tag"]):
                continue
            n_pages += 1
            n_err += rec["errors"]
            n_gold += rec["gold_words"]
            for k, v in rec["cats"].items():
                fam_cats[k] += v
            for k, pairs in rec["samples"].items():
                for p in pairs:
                    if len(fam_samples[k]) < 12:
                        fam_samples[k].append((rec["page"], rec["tag"], p[0], p[1]))
        wer = 100.0 * n_err / n_gold if n_gold else 0
        print(f"\n{fam}: runs={n_pages} pooled_WER={wer:.1f}% errors={n_err}/{n_gold}")
        print("  " + " ".join(f"{k}={v}" for k, v in fam_cats.most_common()))
        for cat, items in fam_samples.items():
            print(f"  [{cat}]")
            for page, tag, a, b in items[:6]:
                print(f"    {page}/{tag}: {a!r} -> {b!r}")

    # Primary API comparison: latest prompt per page (v2 if present else v1)
    print("\n=== primary one-shot API (latest prompt per page) ===")
    for fam_prefix in ("gemini_3.6_flash", "sonnet_4.6"):
        total_e = total_g = 0
        for page in PAGES:
            cands = [r for r in rows if r["page"] == page and r["tag"].startswith(fam_prefix)]
            if not cands:
                continue
            cands.sort(key=lambda r: ("v2" in r["tag"], r["tag"]))
            rec = cands[-1]
            total_e += rec["errors"]
            total_g += rec["gold_words"]
            print(f"  {page:24} {rec['tag']:28} {rec['wer']:5.1f}%")
        print(f"  TOTAL {fam_prefix:20} {100.0*total_e/total_g:5.1f}%  ({total_e}/{total_g})\n")

    print("=== composer v1 (chat, not one-shot) ===")
    total_e = total_g = 0
    for rec in rows:
        if rec["tag"] == "composer_v1":
            total_e += rec["errors"]
            total_g += rec["gold_words"]
            print(f"  {rec['page']:24} {rec['wer']:5.1f}%")
    print(f"  TOTAL composer_v1          {100.0*total_e/total_g:5.1f}%  ({total_e}/{total_g})")


if __name__ == "__main__":
    main()
