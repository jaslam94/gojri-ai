"""Shared pieces of the Gojri OCR pipeline: UTRNet-Large reader, Tesseract English reader, line and span helpers.

Import with: sys.path.insert(0, "scripts/ocr_eval"); import ocrlib
UTRNet code and weights are third party (non-commercial: CC BY-NC 4.0 in its LICENSE file, CC BY-NC-SA 4.0 in its README); only model.py and modules/ are imported from the clone.
"""
import io
import math
import os
import re
import subprocess
import sys
import unicodedata
from argparse import Namespace
from pathlib import Path

import numpy as np
from PIL import Image

# Local UTRNet clone and weights (third party, non-commercial license, not in this repo).
# Set UTRNET_REPO and UTRNET_WEIGHTS to use another location.
_LOCAL_TOOLS = Path(__file__).resolve().parents[2] / "local" / "ocr-tools"  # untracked folder inside the repository
UTRNET_REPO = os.environ.get("UTRNET_REPO", str(_LOCAL_TOOLS / "utrnet"))
UTRNET_WEIGHTS = os.environ.get("UTRNET_WEIGHTS", str(_LOCAL_TOOLS / "weights" / "large.pth"))

TESS = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
IMG_H, IMG_W = 32, 400
MARKS = re.compile(r"[ً-ٰٟۖ-ۭؐ-ؚ]")
ARAB = re.compile(r"[؀-ۿ]")
FOLD = str.maketrans({"ك": "ک", "ه": "ہ"})


def arabic(s):
    """Arabic-letter normalisation used by every score in this project (see utrnet_arabic_eval.py)."""
    return "".join(ARAB.findall(MARKS.sub("", unicodedata.normalize("NFC", s)))).translate(FOLD)


def latin(s):
    """Non-Arabic, non-space characters of a mixed line (English words, digits, brackets)."""
    s = MARKS.sub("", unicodedata.normalize("NFC", s))
    return "".join(c for c in s if not ARAB.match(c) and not c.isspace())


def ed(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


class UTRNet:
    """UTRNet-Large reader. UTRNet keeps its temporal dropout on at inference: each read averages five random masks
    drawn with np.random (modules/dropout_layer.py), so unseeded reads of one crop can differ. With `seed` (default 0)
    np.random is reset before every read, so a crop always gives the same text, whatever the reading order or the
    process. seed=None keeps the old random behaviour."""

    def __init__(self, repo, weights, seed=0):
        import torch
        self.torch = torch
        self.seed = seed
        sys.path.insert(0, str(repo))
        from model import Model  # noqa: E402
        glyphs = "".join(s.strip("\n") for s in open(Path(repo) / "UrduGlyphs.txt", encoding="utf-8")) + " "
        self.chars = ["[CTCblank]"] + list(glyphs)
        self.dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # GPU on SageMaker, CPU on this PC
        opt = Namespace(FeatureExtraction="HRNet", SequenceModeling="DBiLSTM", Prediction="CTC", imgH=IMG_H, imgW=IMG_W,
                        num_fiducial=20, input_channel=1, output_channel=32, hidden_size=256, batch_max_length=100,
                        rgb=False, device=self.dev, character=glyphs, num_class=len(self.chars))
        self.net = Model(opt)
        state = torch.load(weights, map_location="cpu", weights_only=True)
        self.net.load_state_dict({k.removeprefix("module."): v for k, v in state.items()})
        self.net.to(self.dev).eval()

    def read(self, img):
        """One line chunk: grey, mirrored, 32 px high, padded to 400 px, scaled to [-1, 1]."""
        return self.read_conf(img)[0]

    def read_conf(self, img):
        """Like read, also returns a confidence in 0..1: mean softmax peak of the frames that emit a character."""
        torch = self.torch
        img = img.convert("L").transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        w, h = img.size
        rw = IMG_W if math.ceil(IMG_H * w / h) > IMG_W else math.ceil(IMG_H * w / h)
        a = np.asarray(img.resize((rw, IMG_H), Image.Resampling.BICUBIC), dtype="float32") / 255.0
        t = torch.from_numpy((a - 0.5) / 0.5).unsqueeze(0)
        x = torch.zeros(1, IMG_H, IMG_W)
        x[:, :, :rw] = t
        if rw < IMG_W:
            x[:, :, rw:] = t[:, :, rw - 1].unsqueeze(2).expand(1, IMG_H, IMG_W - rw)
        if self.seed is not None:
            np.random.seed(self.seed)  # fixes the five dropout masks of this read
        with torch.no_grad():
            probs = self.net(x.unsqueeze(0).to(self.dev)).softmax(2)[0]
        peak, am = probs.max(1)
        idx, peaks = am.tolist(), peak.tolist()
        out, confs, prev = [], [], 0
        for k, pk in zip(idx, peaks):
            if k != 0 and k != prev:
                out.append(self.chars[k])
                confs.append(pk)
            prev = k
        return "".join(out), (sum(confs) / len(confs) if confs else 0.0)


def tesseract_words(img, pad=12):
    """English Tesseract on one line image. Returns [(x0, x1, conf, text)] in image pixels (left to right)."""
    g = img.convert("L")
    canvas = Image.new("L", (g.width + 2 * pad, g.height + 2 * pad), 255)
    canvas.paste(g, (pad, pad))
    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    p = subprocess.run([TESS, "stdin", "stdout", "--psm", "7", "-l", "eng", "tsv"], input=buf.getvalue(),
                       capture_output=True, timeout=60)
    words = []
    for ln in p.stdout.decode("utf-8", "replace").splitlines()[1:]:
        r = ln.split("\t")
        if len(r) >= 12 and r[0] == "5" and r[11].strip():
            x0 = int(r[6]) - pad
            words.append((max(0, x0), min(img.width, x0 + int(r[8])), float(r[10]), r[11]))
    return sorted(words)


def runs_of(mask):
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            out.append((start, i))
            start = None
    if start is not None:
        out.append((start, len(mask)))
    return out


def otsu(g):
    hist = np.bincount(g.ravel(), minlength=256).astype("float64")
    total, sum_all = g.size, (np.arange(256) * hist).sum()
    best, thr, wb, sb = 0.0, 128, 0.0, 0.0
    for t in range(256):
        wb += hist[t]
        if wb == 0 or wb == total:
            continue
        sb += t * hist[t]
        mb, mf = sb / wb, (sum_all - sb) / (total - wb)
        v = wb * (total - wb) * (mb - mf) ** 2
        if v > best:
            best, thr = v, t
    return thr


def split_chunks(ink_row, max_w):
    """Cut an ink mask (rows x cols) into x-ranges no wider than max_w, at the widest white gaps."""
    cols = ink_row.sum(axis=0) > 0
    xs = np.where(cols)[0]
    if len(xs) == 0:
        return []
    x0, x1 = xs[0], xs[-1] + 1
    gaps = [(a + x0, b + x0) for a, b in runs_of(~cols[x0:x1])]
    chunks, start = [], x0
    while x1 - start > max_w:
        lim = start + max_w
        cand = [g for g in gaps if g[0] > start + max_w * 0.4 and g[1] <= lim + 2]
        if not cand:
            cand = [(lim - 1, lim)]
        g = max(cand, key=lambda t: t[1] - t[0])
        chunks.append((start, g[0]))
        start = g[1]
    chunks.append((start, x1))
    return [c for c in chunks if c[1] - c[0] >= 6]


def is_latin_word(conf, text):
    """Word-level test: a real English-looking token. Short junk from Arabic-script areas fails it."""
    s = text.replace(" ", "")
    ascii_ok = sum(ch.isascii() and (ch.isalnum() or ch in "().;:,-'/&") for ch in s)
    return len(s) >= 3 and ascii_ok / max(1, len(s)) >= 0.8 and conf >= 30


def tesseract_text(img, pad=12):
    """English Tesseract text for one Latin crop (single line, --psm 7)."""
    g = img.convert("L")
    canvas = Image.new("L", (g.width + 2 * pad, g.height + 2 * pad), 255)
    canvas.paste(g, (pad, pad))
    buf = io.BytesIO()
    canvas.save(buf, "PNG")
    p = subprocess.run([TESS, "stdin", "stdout", "--psm", "7", "-l", "eng"], input=buf.getvalue(),
                       capture_output=True, timeout=60)
    return p.stdout.decode("utf-8", "replace").strip()


def split_rows(ink, valley=True):
    """Text rows of a page: horizontal ink profile gaps; rows taller than 1.6 x median are split at their ink valley."""
    prof = ink.sum(axis=1).astype("float32")
    thr = max(2.0, 0.02 * prof.max())
    merged = []
    for a, b in runs_of(prof > thr):
        if merged and a - merged[-1][1] < 3:
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    rows = [(a, b) for a, b in merged if b - a >= 8]
    if valley and len(rows) >= 4:
        med = float(np.median([b - a for a, b in rows]))
        smooth = np.convolve(prof, np.ones(5) / 5, mode="same")
        out, stack = [], list(reversed(rows))
        while stack:
            a, b = stack.pop()
            if b - a > 1.6 * med and b - a >= 16:
                lo, hi = a + int(0.35 * (b - a)), a + int(0.65 * (b - a))
                cut = lo + int(np.argmin(smooth[lo:hi]))
                stack += [(cut, b), (a, cut)]
            else:
                out.append((a, b))
        rows = out
    return rows


class LineReader:
    """Mixed-script line reader: SegNet finds Arabic and Latin runs, UTRNet reads Arabic, Tesseract reads Latin.

    read(img) -> list of (class, x0, x1, text) left to right; class 1 = Arabic, 2 = Latin.
    Consecutive spans of one script are one run (a long Arabic sentence has wide word gaps but reads as one
    right-to-left unit); chunks of a run are joined right to left.
    """

    def __init__(self, utrnet, segnet_path, segnet_dir, max_aspect=11.0, min_letters=3):
        import torch
        sys.path.insert(0, str(segnet_dir))
        from segnet import SegNet, spans_from_logits
        self.torch, self.spans_from_logits, self.utr, self.max_aspect = torch, spans_from_logits, utrnet, max_aspect
        self.min_letters = min_letters
        self.seg = SegNet()
        self.seg.load_state_dict(torch.load(segnet_path, map_location="cpu", weights_only=True))
        self.seg.eval()

    def read(self, img):
        torch = self.torch
        h, w = img.height, img.width
        s = 64 / h
        g64 = img.convert("L").resize((max(8, round(w * s)), 64), Image.Resampling.BICUBIC)
        x = (torch.from_numpy(np.asarray(g64, dtype="float32") / 255.0)[None, None] - 0.5) / 0.5
        with torch.no_grad():
            logits = self.seg(x)[0]
        runs = []
        for c, a, b in self.spans_from_logits(logits):
            a, b = int(a / s), min(w, int(b / s) + 1)
            if runs and runs[-1][0] == c:
                runs[-1] = (c, runs[-1][1], b)
            else:
                runs.append((c, a, b))
        gray = np.asarray(img.convert("L"))
        ink = gray < otsu(gray)
        # An English run is kept only if Tesseract returns English-looking text; otherwise it was a mislabelled
        # Arabic stretch (typical on pure-Arabic pages): it becomes Arabic and merges with its neighbours.
        eng = {}
        checked = []
        for c, a, b in runs:
            if c == 2:
                t = tesseract_text(img.crop((max(0, a - 2), 0, min(w, b + 2), h)))
                if not looks_english(t, self.min_letters):
                    c = 1
                else:
                    eng[(a, b)] = t
            if checked and checked[-1][0] == c:
                checked[-1] = (c, checked[-1][1], b)
            else:
                checked.append((c, a, b))
        runs = checked
        out = []
        for c, a, b in runs:
            a, b = max(0, a - 2), min(w, b + 2)
            if c == 1:
                parts = [(c0, self.utr.read(img.crop((a + max(0, c0 - 2), 0, a + c1 + 2, h))))
                         for c0, c1 in split_chunks(ink[:, a:b], int(self.max_aspect * h))]
                out.append((1, a, b, " ".join(t for _, t in sorted(parts, key=lambda p: -p[0]))))
            else:
                out.append((2, a, b, eng.get((a + 2 if a > 0 else a, min(w, b - 2) if b < w else b)) or tesseract_text(img.crop((a, 0, b, h)))))
        return out


def looks_english(t, min_letters=6):
    """True if Tesseract text for a run looks like real English: enough ASCII letters, almost all characters ASCII."""
    s = t.replace(" ", "")
    if len(s) < 4:
        return False
    letters = sum(ch.isascii() and ch.isalpha() for ch in s)
    ascii_ok = sum(ch.isascii() and (ch.isalnum() or ch in "().;:,-'/&") for ch in s)
    return letters >= min_letters and ascii_ok / len(s) >= 0.85


def _line_runs(reader, img):
    """SegNet runs for one line image: [(class, x0, x1)] in image pixels, same-script neighbours merged."""
    torch = reader.torch
    h, w = img.height, img.width
    s = 64 / h
    g64 = img.convert("L").resize((max(8, round(w * s)), 64), Image.Resampling.BICUBIC)
    x = (torch.from_numpy(np.asarray(g64, dtype="float32") / 255.0)[None, None] - 0.5) / 0.5
    with torch.no_grad():
        logits = reader.seg(x)[0]
    runs = []
    for c, a, b in reader.spans_from_logits(logits):
        a, b = int(a / s), min(w, int(b / s) + 1)
        if runs and runs[-1][0] == c:
            runs[-1] = (c, runs[-1][1], b)
        else:
            runs.append((c, a, b))
    return runs


def english_width(reader, img, min_letters=6):
    """(English run width, total run width) of a line: SegNet English runs that Tesseract confirms with >= min_letters
    letters. Used to decide whether a page is a mixed-script page (dictionary) or pure Arabic."""
    h, w = img.height, img.width
    eng = tot = 0
    for c, a, b in _line_runs(reader, img):
        tot += b - a
        if c == 2 and looks_english(tesseract_text(img.crop((max(0, a - 2), 0, min(w, b + 2), h))), min_letters):
            eng += b - a
    return eng, tot


def read_arabic_only(reader, img):
    """Whole line as one right-to-left Arabic unit (UTRNet only): for pages without English."""
    h = img.height
    gray = np.asarray(img.convert("L"))
    ink = gray < otsu(gray)
    parts = [(c0, reader.utr.read(img.crop((max(0, c0 - 2), 0, c1 + 2, h))))
             for c0, c1 in split_chunks(ink, int(reader.max_aspect * h))]
    return " ".join(t for _, t in sorted(parts, key=lambda p: -p[0]))
