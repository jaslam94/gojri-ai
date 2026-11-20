"""Put back the word spaces that UTRNet misses in tight prose.

Print gives no visible gap after a letter that does not join to the next one (ا د ڈ ذ ر ڑ ز ژ و ے), so UTRNet reads
"کےسلسلہ" for "کے سلسلہ". Of 80 missing spaces in the speaker's review, 71 follow such a letter. The fix cuts only there.
A glued token is split when the pieces are known words and the split beats the whole token by a margin (Norvig style
word segmentation over a word list built from our own books). No new letters are ever made; only spaces are added.

Build the word list:  vocab = build_vocab(files, skip=...)   Use:  fixed = fix_line(text, vocab)
"""
import collections
import glob
import json
import math
import re
import unicodedata

NONJOIN = set("ادڈذرڑزژوےۓ")  # a space may follow these (no visible gap in print)
PUNCT = "۔،:؛؟!()[]{}\"'-.,؎"
UNK = -13.0  # log probability of an unseen piece
UNK_LEN = 1.5  # extra penalty per letter of an unseen piece
MARGIN = 2.0  # the split must beat the whole token by this much (log units)
MAX_PIECES = 4


def strip_marks(s):
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def words_of(text):
    out = []
    for w in re.split(r"[\s\t]+", text):
        w = strip_marks(w).strip(PUNCT)
        if len(w) >= 1 and not re.search(r"[0-9A-Za-z]", w):
            out.append(w)
    return out


class Vocab:
    def __init__(self, counter):
        self.c = counter
        self.n = sum(counter.values())

    def lp(self, w):
        k = self.c.get(w, 0)
        if k:
            return math.log(k / self.n)
        return UNK - UNK_LEN * len(w)


def build_vocab(texts):
    c = collections.Counter()
    for t in texts:
        c.update(words_of(t))
    return Vocab(c)


def split_token(tok, v, margin=MARGIN):
    """tok: a space-free run with marks. Returns the run with spaces added, or tok."""
    bare = strip_marks(tok)
    if len(bare) < 4 or re.search(r"[0-9A-Za-z]", bare):
        return tok
    # allowed cut points in `bare` indexes: after a non-joiner, at least 1 letter on each side
    cuts = [i for i in range(1, len(bare)) if bare[i - 1] in NONJOIN]
    if not cuts:
        return tok
    best = {0: (0.0, [])}
    pts = [0] + cuts + [len(bare)]
    for j in range(1, len(pts)):
        cand = None
        for i in range(j):
            if i not in best:
                continue
            if len(best[i][1]) + 1 > MAX_PIECES:
                continue
            sc = best[i][0] + v.lp(bare[pts[i]:pts[j]])
            if cand is None or sc > cand[0]:
                cand = (sc, best[i][1] + [pts[i]])
        if cand:
            best[j] = cand
    sc, starts = best[len(pts) - 1]
    whole = v.lp(bare)
    if len(starts) <= 1 or sc <= whole + margin:
        return tok
    cutset = set(starts[1:])
    out, n = [], 0
    for ch in tok:
        if unicodedata.category(ch) != "Mn":
            if n in cutset:
                out.append(" ")
            n += 1
        out.append(ch)
    return "".join(out)


def fix_line(text, v, margin=MARGIN):
    """Add spaces inside every space-free run of a text line (tabs kept)."""
    parts = re.split(r"(\s+)", text)
    out = []
    for p in parts:
        if not p or p.isspace():
            out.append(p)
            continue
        # keep leading/trailing punctuation outside the run
        m = re.match(rf"^([{re.escape(PUNCT)}]*)(.*?)([{re.escape(PUNCT)}]*)$", p, re.S)
        a, mid, b = m.group(1), m.group(2), m.group(3)
        out.append(a + split_token(mid, v, margin) + b)
    return "".join(out)
