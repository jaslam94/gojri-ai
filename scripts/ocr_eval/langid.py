"""Gojri (gju) versus Urdu (urd) line tagger: free-label data, marker rule, character n-gram class models, group cross-validation.

Why: the space model and the corpus must know the language of each line (plans/RESEARCH-urdu-gojri-language-id-and-mixed-spacing.md).
No public language-ID model has a Gojri label, so we train our own. Method (the research: char n-grams win on close languages with
little data): one character n-gram model per class (the CharLM of spacing_lm.py), score = log P(line | gju) - log P(line | urd),
per letter. Spaces are removed from the text on purpose: OCR spacing differs from the FLI spacing, and the model must not learn
"spacing style" as language. Marks and punctuation are removed. The small-v letters (ݨ U+0768, ݩ U+0769, ڵ U+06B5) and the FLI
placeholder U+FFFF (a lost ݨ or ڵ) are folded to one symbol, and a flag says whether a line holds one.

Free labels (no speaker work):
  gju: FLI stories and books (files 01-09, 11), the gju parts of file 10, the Kahawat-Kosh idioms.
  urd: the Urdu parts of file 10 (after each "ترجمہ"), the Kahawat-Kosh meanings (mostly Urdu; some may be Gojri: label noise).
Groups for cross-validation (a story and its translation, an idiom and its meaning stay together): FLI file, file-10 story,
Kahawat page block of 10 pages.

Run: py -3 -X utf8 scripts/ocr_eval/langid.py cv
"""
import collections
import glob
import json
import math
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import spacing_lm as L  # noqa: E402

FLI = ROOT / "datasets/Gojri Language Corpus"
KAHAWAT = ROOT / "data/ocr/kahawat-final2"
V_CHARS = set("ݨݩڵ￿")      # small-v noon (U+0768, U+0769), lam with v (U+06B5), FLI placeholder of a lost one
V = "ݩ"                          # the one symbol they fold to
FOLD = str.maketrans({"ك": "ک", "ه": "ہ", "ۃ": "ہ", "ي": "ی", "ى": "ی", "ݨ": V, "ڵ": V, "￿": V})
MIN_LETTERS = 8


def has_marker(raw):
    return any(c in V_CHARS for c in raw)


def letters(raw):
    """Raw text -> letters only (Arabic-script letters, folded, no spaces, marks, punctuation, digits, Latin)."""
    s = unicodedata.normalize("NFC", raw).translate(FOLD)
    return "".join(c for c in s if (c == V or "؀" <= c <= "ۿ" or "ݐ" <= c <= "ݿ") and unicodedata.category(c) not in ("Mn", "Nd", "Po", "Pd", "Ps", "Pe", "Cf", "Sk", "Sm"))


def fli_units():
    out = []
    for f in sorted(glob.glob(str(FLI / "*.txt"))):
        name = Path(f).name
        num = name[:2]
        text = Path(f).read_text(encoding="utf-8")
        if num == "10":
            out += file10_units(text)
            continue
        for s in re.split(r"[۔؟!\n]+", text):
            out.append({"text": s, "label": "gju", "group": "fli-" + num, "source": "fli"})
    return out


def file10_units(text):
    """File 10: four stories. Lines after a 'ترجمہ' line (and the Urdu title lines of story D) are Urdu; the rest is Gojri."""
    lines = text.split("\n")
    # story starts: lines 0, 17, 35, 58 of the file as read on 2026-11-23 (titles with a number or a story name)
    starts = {0: "A", 17: "B", 35: "C", 58: "D"}
    urdu = {16, 33, 46, 66, 68, 69}
    skip = {14, 15, 30, 32, 43, 45, 67}     # author lines and the 'ترجمہ' headings
    out, grp = [], "A"
    for i, ln in enumerate(lines):
        grp = starts.get(i, grp)
        if i in skip or not ln.strip():
            continue
        lab = "urd" if i in urdu else "gju"
        for s in re.split(r"[۔؟!]+", ln):
            out.append({"text": s, "label": lab, "group": "f10-" + grp, "source": "file10"})
    return out


def kahawat_units(folder=KAHAWAT):
    out = []
    for f in sorted(Path(folder).glob("page_*.json")):
        info = json.loads(f.read_text(encoding="utf-8"))
        if info.get("kind") != "entries":
            continue
        n = int(f.stem.split("_")[1])
        g = f"kk-{n // 10:02d}"
        for e in info["entries"]:
            out.append({"text": e["idiom"], "label": "gju", "group": g, "source": "kahawat-idiom"})
            out.append({"text": e["meaning"], "label": "urd", "group": g, "source": "kahawat-meaning"})
    return out


def load_units():
    units = fli_units() + kahawat_units()
    keep = []
    for u in units:
        u["letters"] = letters(u["text"])
        u["marker"] = has_marker(u["text"])
        if len(u["letters"]) >= MIN_LETTERS:
            keep.append(u)
    return keep


class ClassLM:
    """Character n-gram model of one class over unspaced letters (the CharLM of spacing_lm.py)."""

    def __init__(self, order):
        self.lm = L.CharLM(order)
        self.order = order

    def fit(self, lines):
        self.lm.add(lines)

    def logp(self, line):
        o = self.order
        s = L.BOS * (o - 1) + line + L.EOS
        tot = 0.0
        for i in range(o - 1, len(s)):
            tot += math.log(self.lm.prob(s[i - (o - 1):i], s[i]))
        return tot


class Tagger:
    def __init__(self, order=4, marker_override=True):
        self.order = order
        self.marker_override = marker_override

    def fit(self, units):
        self.m = {c: ClassLM(self.order) for c in ("gju", "urd")}
        for c, lm in self.m.items():
            lm.fit([u["letters"] for u in units if u["label"] == c])
        # make both models know every character, so that the score is on the same alphabet
        chars = set().union(*(lm.lm.chars for lm in self.m.values()))
        for lm in self.m.values():
            lm.lm.chars = set(chars)
        return self

    def score(self, u):
        """Per letter log-likelihood ratio gju - urd. Positive = Gojri."""
        s = u["letters"]
        return (self.m["gju"].logp(s) - self.m["urd"].logp(s)) / (len(s) + 1)

    def tag(self, u, thr=0.0):
        if self.marker_override and u["marker"]:
            return "gju"
        return "gju" if self.score(u) > thr else "urd"


def fold_groups(units, k=5):
    sizes = collections.Counter(u["group"] for u in units)
    folds = [[] for _ in range(k)]
    load = [0] * k
    for g, n in sorted(sizes.items(), key=lambda t: (-t[1], t[0])):
        i = load.index(min(load))
        folds[i].append(g)
        load[i] += n
    return folds


def prf(conf, cls):
    tp = conf[(cls, cls)]
    fp = sum(v for (t, p), v in conf.items() if p == cls and t != cls)
    fn = sum(v for (t, p), v in conf.items() if t == cls and p != cls)
    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    f = 2 * p * r / (p + r) if p + r else 0
    return p, r, f


def report(name, conf):
    n = sum(conf.values())
    acc = sum(v for (t, p), v in conf.items() if t == p) / n
    pg, rg, fg = prf(conf, "gju")
    pu, ru, fu = prf(conf, "urd")
    print(f"{name:34s} n {n}  acc {100 * acc:5.1f}  gju P {100 * pg:5.1f} R {100 * rg:5.1f}  urd P {100 * pu:5.1f} R {100 * ru:5.1f}  macro F1 {50 * (fg + fu):5.1f}  [gju->urd {conf[('gju', 'urd')]}, urd->gju {conf[('urd', 'gju')]}]")


def cmd_cv():
    units = load_units()
    c = collections.Counter((u["source"], u["label"]) for u in units)
    print("units", len(units), dict(c))
    print("marker share:", {s: f"{100 * sum(u['marker'] for u in units if u['source'] == s) / max(1, sum(1 for u in units if u['source'] == s)):.1f}%" for s in sorted({u['source'] for u in units})})
    folds = fold_groups(units)
    print("folds:", [len(f) for f in folds], "groups")
    # baseline: marker rule alone
    conf = collections.Counter((u["label"], "gju" if u["marker"] else "urd") for u in units)
    report("marker rule alone", conf)
    for order in (2, 3, 4, 5, 6):
        for override in (False, True):
            conf = collections.Counter()
            for held in folds:
                hs = set(held)
                tr = [u for u in units if u["group"] not in hs]
                te = [u for u in units if u["group"] in hs]
                t = Tagger(order, override).fit(tr)
                for u in te:
                    conf[(u["label"], t.tag(u))] += 1
            report(f"char {order}-gram LLR" + (" + marker rule" if override else ""), conf)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cv":
        cmd_cv()
    else:
        sys.exit(__doc__)
