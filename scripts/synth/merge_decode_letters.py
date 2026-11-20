"""Rebuild the real-print labels from the table decode and the pass2 text.

The pass2 labels (Gemini-repaired) get spelling and spacing wrong against the
print. The decode table follows the print by glyph code (user rulings
2026-11-04 and 2026-11-05). For each printed line this script:
  1. decodes the line with the table (same pairing rule as mine_batool_pairs),
  2. replaces a pass2 Arabic-script word with the decode word when they differ
     only in heh/kaf letters, in one letter, or are at least 60% similar
     (less similar means a reordered word, not a spelling),
  3. when the word counts differ, pairs words only at 90% similarity; unpaired
     words keep the pass2 spelling,
  4. copies the space before "(" and after ")" from the decode gap.

Output: data/synth/real_pairs/labels_merged.jsonl (all lines, with the old text
in `text_pass2`) and labels_merged_skipped.json (no decode, or no word changed
on a line with unequal word counts). Source label files stay untouched.

Run: py -3 -X utf8 scripts/synth/merge_decode_letters.py [--check]
--check scores the merge against the 200 reviewed lines and writes nothing.
"""
import json
import re
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "synth"))
from dump_batool_lines import fmt_line, load_map  # noqa: E402
from mine_batool_pairs import cluster_rows_full, page_chars_full  # noqa: E402

PDF = ROOT / "pdfs" / "anjumshanasi" / "Gojri-English-Dictionary.pdf"
PASS2 = ROOT / "data" / "decode" / "out" / "gojri-english-dictionary"
SRC = ROOT / "data" / "synth" / "real_pairs" / "labels.jsonl"
OUT = ROOT / "data" / "synth" / "real_pairs" / "labels_merged.jsonl"
SKIP = ROOT / "data" / "synth" / "real_pairs" / "labels_merged_skipped.json"
MARKS = ROOT / "data" / "reviews" / "dictionary-200-lines" / "marks_final_20261104.json"

AR_RUN = re.compile(r"[؀-ۿݐ-ݿ]+")
HEH_KAF = set("هہھكک")
FOLD = {"ك": "ک", "ه": "ہ", "ھ": "ہ"}  # merge: any heh/kaf form
SCORE_FOLD = {"ك": "ک", "ه": "ہ"}  # scoring: ك=ک and ه=ہ; ھ stays apart


def fold(s, table=FOLD):
    return "".join(table.get(c, c) for c in s)


MIN_ALIGNED = 0.9  # unequal word counts: only near-identical words pair (0.6 cut words short)
MIN_SIMILAR = 0.6  # a decode word that differs more than this from its label word is a reorder, not a spelling


def take_decode_word(w, d):
    """True when the decode word d should replace the label word w."""
    if w == d or "[" in d:
        return False
    if len(w) == len(d) and fold(w) == fold(d):
        return True  # heh/kaf letters only
    if len(w) == len(d) and sum(a != b for a, b in zip(w, d)) <= 1:
        return True  # one wrong letter, also for short words (اں vs ان)
    return SequenceMatcher(None, w, d).ratio() >= MIN_SIMILAR


def similarity(w, d):
    if fold(w) == fold(d):
        return 1.0
    if len(w) == len(d) and sum(a != b for a, b in zip(w, d)) <= 1:
        return 0.9
    return SequenceMatcher(None, w, d).ratio()


def pair_words(lw, dw):
    """For each label word, the decode word it matches, or None.

    Equal counts pair in order. Unequal counts (the decode split or joined a
    word) pair by dynamic programming: only pairs with similarity >= MIN_ALIGNED
    count, and the best total wins. Unpaired label words stay as they are.
    """
    if len(lw) == len(dw):
        return list(dw), False
    n, m = len(lw), len(dw)
    best = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            sim = similarity(lw[i - 1], dw[j - 1])
            take = best[i - 1][j - 1] + sim if sim >= MIN_ALIGNED else -1.0
            best[i][j] = max(best[i - 1][j], best[i][j - 1], take)
    out = [None] * n
    i, j = n, m
    while i > 0 and j > 0:
        sim = similarity(lw[i - 1], dw[j - 1])
        if sim >= MIN_ALIGNED and abs(best[i][j] - (best[i - 1][j - 1] + sim)) < 1e-9:
            out[i - 1] = dw[j - 1]
            i, j = i - 1, j - 1
        elif best[i][j] == best[i - 1][j]:
            i -= 1
        else:
            j -= 1
    return out, True


def merge_line(label, decoded):
    """Return (merged_label, status, aligned).

    Status: ok (only heh/kaf letters changed) | letters (another letter changed)
    | no_change | no_decode. aligned is True when the word counts differed and
    the words were paired by similarity.
    """
    if not decoded:
        return label, "no_decode", False
    lw = list(AR_RUN.finditer(label))
    dw = [m.group() for m in AR_RUN.finditer(decoded)]
    pairs, aligned = pair_words([m.group() for m in lw], dw)
    out, pos, status = [], 0, "no_change"
    for m, d in zip(lw, pairs):
        w = m.group()
        out.append(label[pos:m.start()])
        pos = m.end()
        if d is not None and take_decode_word(w, d):
            out.append(d)
            if not (len(w) == len(d) and fold(w) == fold(d)):
                status = "letters"
            elif status == "no_change":
                status = "ok"
        else:
            out.append(w)
    out.append(label[pos:])
    return "".join(out), status, aligned


def paren_gaps(s):
    """(space before '(', space after ')') for the first (...) group, or None."""
    i = s.find("(")
    j = s.find(")", i + 1) if i >= 0 else -1
    if i < 0 or j < 0:
        return None
    return (i > 0 and s[i - 1] == " ", j + 1 < len(s) and s[j + 1] == " ")


def fix_paren_spacing(label, decoded):
    """Copy the space before '(' and after ')' from the decode (print geometry).

    Gemini put a space on both sides of the transliteration group on 175 of 177
    reviewed lines. The print has none on 143 of 177. The decode matches the
    print on 57 of 69 lines, so its gap is the better guide.
    """
    want = paren_gaps(decoded) if decoded else None
    i = label.find("(")
    j = label.find(")", i + 1) if i >= 0 else -1
    if want is None or i < 0 or j < 0:
        return label, "no_paren"
    head = label[:i].rstrip(" ")
    tail = label[j + 1:].lstrip(" ")
    new = head + (" " if want[0] and head else "") + label[i:j + 1] + (" " if want[1] and tail else "") + tail
    return new, ("changed" if new != label else "same")


def page_decodes(doc, page_1idx, labels, pua_map):
    """Decoded text per kept row, using the same rule as mine_batool_pairs."""
    rows = cluster_rows_full(page_chars_full(doc[page_1idx - 1]))
    texts = [re.sub(r"\s+", " ", fmt_line(bb["chars"], pua_map, wrap_batool=False)).strip()
             for _y, bb in rows]
    keep_folio = str(page_1idx) in labels
    kept = [t for t in texts if t and (keep_folio or t != str(page_1idx))]
    return kept if len(kept) == len(labels) else None


def pass2_labels(page_1idx):
    p = PASS2 / f"page-{page_1idx:04d}-pass2.txt"
    lines = [re.sub(r"\s+", " ", ln).strip()
             for ln in unicodedata.normalize("NFC", p.read_text(encoding="utf-8")).splitlines()]
    return [ln for ln in lines if ln]


def words_of(s):
    return [fold(w, SCORE_FOLD) for w in AR_RUN.findall(unicodedata.normalize("NFC", s))]


def hk_seq(s):
    return fold("".join(c for c in s if c in HEH_KAF), SCORE_FOLD)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    check = "--check" in sys.argv
    pua_map = load_map()
    doc = fitz.open(PDF)
    rows = [json.loads(ln) for ln in SRC.open(encoding="utf-8")]
    if check:
        marks = {x["page_line"]: x for x in json.loads(MARKS.read_text(encoding="utf-8"))["lines"]}
        rows = [r for r in rows if r["page_line"] in marks]
    pages = sorted({int(r["page_line"][5:9]) for r in rows})
    dec = {}
    for p in pages:
        dec[p] = page_decodes(doc, p, pass2_labels(p), pua_map)
    merged, skipped, stats = [], [], {}
    for r in rows:
        p = int(r["page_line"][5:9])
        k = int(r["page_line"].split(":L")[1])
        d = dec[p][k - 1] if dec.get(p) else None
        text, status, aligned = merge_line(r["text"], d)
        text, paren = fix_paren_spacing(text, d)
        if aligned:
            stats["aligned"] = stats.get("aligned", 0) + 1
        stats[status] = stats.get(status, 0) + 1
        stats["paren_" + paren] = stats.get("paren_" + paren, 0) + 1
        if status == "no_decode" or (aligned and status == "no_change"):
            skipped.append({"page_line": r["page_line"], "status": status})
        merged.append({**r, "text": text, "text_pass2": r["text"], "merge": status,
                       "aligned": aligned, "paren": paren})
    print("status:", stats)
    if check:
        score(merged, marks)
        return
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in merged) + "\n", encoding="utf-8")
    SKIP.write_text(json.dumps(skipped, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(merged)} rows to {OUT}, skipped {len(skipped)}")


def score(merged, marks):
    """Compare the heh/kaf letter sequence with the user's fix, line by line."""
    wp = wm = wn = lp = lm = 0
    for r in merged:
        truth = marks[r["page_line"]].get("fix") or marks[r["page_line"]]["label"]
        a, b, c = (words_of(x) for x in (r["text_pass2"], r["text"], truth))
        if len(a) == len(b) == len(c):
            wn += len(c)
            wp += sum(u == w for u, w in zip(a, c))
            wm += sum(u == w for u, w in zip(b, c))
            lp += a == c
            lm += b == c
    print(f"Arabic words equal to user fix (lines with the same word count, {wn} words): "
          f"pass2 {wp}, merged {wm}; whole lines: pass2 {lp}, merged {lm}")
    n = old_ok = new_ok = fixed = broke = 0
    bad = []
    for r in merged:
        truth = marks[r["page_line"]].get("fix") or marks[r["page_line"]]["label"]
        t = hk_seq(truth)
        o, m = hk_seq(r["text_pass2"]), hk_seq(r["text"])
        n += 1
        old_ok += o == t
        new_ok += m == t
        fixed += o != t and m == t
        broke += o == t and m != t
        if m != t:
            bad.append((r["page_line"], r["merge"], o, m, t))
    print(f"lines {n} | heh/kaf letters match user fix: pass2 {old_ok}, merged {new_ok}")
    print(f"merge fixed {fixed} lines, broke {broke} lines")
    pn = po = pm = pboth = 0
    pbad = []
    for r in merged:
        truth = marks[r["page_line"]].get("fix") or marks[r["page_line"]]["label"]
        t, o, m = paren_gaps(truth), paren_gaps(r["text_pass2"]), paren_gaps(r["text"])
        if t is None:
            continue
        pn += 1
        po += o == t
        pm += m == t
        if m != t:
            pbad.append((r["page_line"], r["paren"], o, m, t))
    print(f"paren spacing matches user fix on {pn} lines: pass2 {po}, merged {pm}")
    for b in pbad[:25]:
        print(" ", *b)
    for b in bad[:40]:
        print(" ", *b)


if __name__ == "__main__":
    main()
