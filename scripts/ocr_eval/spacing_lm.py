"""Character n-gram space inserter for Gojri text (insert only: letters never change).

Idea (plans/RESEARCH-nastaliq-word-spacing.md): the OCR text often glues words, because the print has no clear gap.
A character n-gram model trained on word-spaced Gojri text scores a line with and without a space at each place.
A space is added where it raises the score by more than a bonus. Spaces that the OCR read are never removed, and no
letter is ever changed, added or dropped.

  lm = CharLM(order=5); lm.add(["آپ بھلا تے جگ بھلو", ...])        # lines of letters and single spaces, no marks
  out = insert_spaces(text, [lm_fli, lm_cards], [0.7, 0.3], bonus=2.0, where="nonjoin")

The decoder is exact for the model: the state is the last (order-1) characters, equal states are merged.
Letters are folded as in score_spacing.py (ك to ک, ه to ہ, ݨ to ݩ) so the training text and the scores agree.
"""
import collections
import math
import unicodedata

FOLD = str.maketrans({"ك": "ک", "ه": "ہ", "ݨ": "ݩ"})
NONJOIN = set("ادڈذرڑزژوےۓ")  # a space may follow these when the print shows no gap
BOS, EOS = "^", "$"


def letter_class(c):
    """'mark', 'space', 'skip' (punctuation, control) or 'letter'. Same classes as score_spacing.parse."""
    cat = unicodedata.category(c)
    if cat.startswith("M"):
        return "mark"
    if c.isspace():
        return "space"
    if cat[0] in "PC":
        return "skip"
    return "letter"


def words_line(text):
    """Text -> 'word word word': letters only (no marks, no punctuation), single spaces. Folded."""
    text = unicodedata.normalize("NFC", text).translate(FOLD)
    out, gap = [], False
    for c in text:
        k = letter_class(c)
        if k == "space":
            gap = True
        elif k == "letter":
            if gap and out and out[-1] != " ":
                out.append(" ")
            gap = False
            out.append(c)
    return "".join(out)


class CharLM:
    """Interpolated Witten-Bell character n-gram model over lines of letters and spaces."""

    def __init__(self, order):
        self.order = order
        self.cnt = [collections.defaultdict(collections.Counter) for _ in range(order)]  # cnt[k][context of k chars][next char]
        self.chars = set([EOS, " "])
        self.memo = {}

    def add(self, lines, weight=1.0):
        pad = BOS * (self.order - 1)
        for ln in lines:
            s = pad + ln + EOS
            self.chars.update(ln)
            for i in range(self.order - 1, len(s)):
                for k in range(self.order):
                    self.cnt[k][s[i - k:i]][s[i]] += weight
        self.memo = {}

    def prob(self, hist, c):
        """P(c | hist). hist: the last order-1 chars (padded with BOS at the line start)."""
        key = (hist, c)
        v = self.memo.get(key)
        if v is not None:
            return v
        p = 1.0 / (len(self.chars) + 1)
        for k in range(self.order):
            ctx = hist[len(hist) - k:] if k else ""
            d = self.cnt[k].get(ctx)
            if not d:
                break
            tot = sum(d.values())
            t = len(d)
            p = (d.get(c, 0.0) + t * p) / (tot + t)
        self.memo[key] = p
        return p


def mix_logp(lms, ws, hist, c):
    return math.log(sum(w * lm.prob(hist[len(hist) - (lm.order - 1):] if lm.order > 1 else "", c) for lm, w in zip(lms, ws)))


def parse_letters(text):
    """[(index in text, folded letter)] of the letter characters of text, and the set of letter numbers that follow a space."""
    text = unicodedata.normalize("NFC", text)
    if len(text) != len(text.translate(FOLD)):
        raise ValueError("folding changed the length")
    letters, after_space, gap = [], set(), False
    for i, c in enumerate(text):
        k = letter_class(c)
        if k == "space":
            gap = True
        elif k == "letter":
            if gap and letters:
                after_space.add(len(letters))
            gap = False
            letters.append((i, c.translate(FOLD)))
    return text, letters, after_space


def decide(letters, after_space, lms, ws, bonus, where="nonjoin"):
    """Return the set of letter numbers before which a space is inserted (never one that already has a space)."""
    order = max(lm.order for lm in lms)
    pad = BOS * (order - 1)
    states = {pad: (0.0, ())}
    for n, (_, ch) in enumerate(letters):
        new = {}
        have = n in after_space
        can = (not have) and n > 0 and (where == "any" or letters[n - 1][1] in NONJOIN)
        for hist, (sc, ins) in states.items():
            opts = []
            if have:
                opts.append((hist + " ", sc + mix_logp(lms, ws, hist, " "), ins))
            else:
                opts.append((hist, sc, ins))
                if can:
                    opts.append((hist + " ", sc + mix_logp(lms, ws, hist, " ") + bonus, ins + (n,)))
            for h, s, i in opts:
                s2 = s + mix_logp(lms, ws, h, ch)
                h2 = (h + ch)[-(order - 1):] if order > 1 else ""
                cur = new.get(h2)
                if cur is None or s2 > cur[0]:
                    new[h2] = (s2, i)
        states = new
    best = max(states.items(), key=lambda kv: kv[1][0] + mix_logp(lms, ws, kv[0], EOS))
    return set(best[1][1])


def insert_spaces(text, lms, ws, bonus, where="nonjoin"):
    """Add spaces to text (marks and punctuation kept). Returns the new text."""
    text, letters, after_space = parse_letters(text)
    if not letters:
        return text
    ins = decide(letters, after_space, lms, ws, bonus, where)
    at = {letters[n][0] for n in ins}
    out = []
    for i, c in enumerate(text):
        if i in at:
            out.append(" ")
        out.append(c)
    return "".join(out)
