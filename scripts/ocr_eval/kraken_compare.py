"""Compare Kraken (Printed Urdu Base Model) with UTRNet-Large on the Kahawat-Kosh cards a Gojri speaker has marked.

Same page pipeline for both readers (rule detection, row cut, chunk cut, pairing in ocr_kahawat.py); only the line
reader changes. Truth: a card marked OK keeps its OCR text, a card marked Wrong takes the speaker's fixed text,
Unsure cards are skipped. Cards are matched to entries by PDF page and the y of the entry's first idiom row.

UTRNet text comes from the finished run in --utr-dir (same rows, no CPU re-run). Kraken is run here.
Needs Kraken 7 (pip install --target D:/ocr-tools/kraken-pkgs kraken) and the model file urdu_best.mlmodel
(https://zenodo.org/records/14585602, Apache 2.0). Run with PYTHONPATH=D:/ocr-tools/kraken-pkgs.

Metrics (per field: idiom or meaning), all on the Arabic-script letters only:
  letter error  = edit distance of the base letters (spaces, marks, punctuation removed; ك/ک, ه/ہ, ي/ی merged) / truth letters
  space errors  = word breaks missing / extra, counted on the letters both texts share (Wrong cards only: on OK cards
                  the speaker did not check spaces)
  mark errors   = edit distance of the diacritic strings (zer, zabar, pesh, shadda, and so on) / marks in the truth
Run: py -3 -X utf8 scripts/ocr_eval/kraken_compare.py --marks <review_marks.json> --sample <old sample.json>
        --utr-dir data/ocr/kahawat-gpu3 --out data/ocr/kraken-test
"""
import argparse
import difflib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import fitz
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402
import ocr_kahawat as K  # noqa: E402

MODEL = os.environ.get("KRAKEN_MODEL", r"D:\ocr-tools\kraken-model\urdu_best.mlmodel")
MARKS = re.compile("[\u064b-\u065f\u0670\u06d6-\u06ed]")
MERGE = str.maketrans({"ك": "ک", "ه": "ہ", "ي": "ی", "ى": "ی", "ۃ": "ہ"})


class KrakenReader:
    """Same read_conf(img) -> (text, confidence) interface as O.UTRNet, so ocr_kahawat.ocr_page can use it."""

    def __init__(self, path, mode="bbox"):
        from kraken.lib import models
        self.net = models.load_any(path)
        self.mode = mode

    def read_conf(self, img):
        from kraken.containers import BBoxLine, BaselineLine, Segmentation
        from kraken.rpred import rpred
        im = img.convert("L")
        w, h = im.size
        if self.mode == "bbox":
            line = BBoxLine(id="l", bbox=(0, 0, w, h), text_direction="horizontal-rl")
            seg = Segmentation(type="bbox", imagename="x", text_direction="horizontal-rl", script_detection=False, lines=[line])
        else:
            # a white margin keeps the line polygon inside the image (without it every line failed in Kraken 7.1.1)
            from PIL import ImageOps
            im = ImageOps.expand(im, border=12, fill=255)
            w, h = im.size
            line = BaselineLine(id="l", baseline=[(12, h // 2), (w - 12, h // 2)],
                                boundary=[(2, 2), (w - 2, 2), (w - 2, h - 2), (2, h - 2)], base_dir="R")
            seg = Segmentation(type="baselines", imagename="x", text_direction="horizontal-rl", script_detection=False, lines=[line])
        recs = list(rpred(self.net, im, seg))
        if not recs:
            return "", 0.0
        c = recs[0].confidences
        return recs[0].prediction, (float(sum(c) / len(c)) if len(c) else 0.0)


def norm(s):
    return unicodedata.normalize("NFC", s).translate(MERGE)


def base(s):
    """Arabic-script base letters only (no spaces, marks, punctuation, Latin, digits)."""
    return "".join(ch for ch in norm(s) if "\u0600" <= ch <= "\u06ff" and not MARKS.match(ch) and ch.isalpha() and ch != "ـ")


def marks_of(s):
    return "".join(ch for ch in norm(s) if MARKS.match(ch))


def breaks(s):
    """(letters, set of letter indexes after which the text has a space)."""
    letters, brk, i = [], set(), 0
    for ch in norm(s):
        if "\u0600" <= ch <= "\u06ff" and not MARKS.match(ch) and ch.isalpha() and ch != "ـ":
            letters.append(ch)
            i += 1
        elif ch == " " and i:
            brk.add(i)
    return "".join(letters), brk


def space_errors(truth, ocr):
    """(missing, extra, truth_breaks) on the letters both texts share, found by aligning the two letter strings."""
    lt, bt = breaks(truth)
    lo, bo = breaks(ocr)
    sm = difflib.SequenceMatcher(None, lt, lo, autojunk=False)
    missing = extra = total = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag != "equal":
            continue
        for k in range(i2 - i1):
            ti, oi = i1 + k + 1, j1 + k + 1
            if ti >= len(lt) or oi >= len(lo):
                continue  # the end of the text is not a break
            t, o = ti in bt, oi in bo
            total += t
            missing += t and not o
            extra += o and not t
    return missing, extra, total


def entries_of(info):
    return info.get("entries", []) if info.get("kind") == "entries" else []


def match(entries, y, idiom):
    """The entry whose first idiom row is closest to y (within 14 px) and whose idiom looks like the card's idiom."""
    best = None
    for e in entries:
        d = abs(e["y"] - y)
        if d <= 14 and (best is None or d < best[0]):
            best = (d, e)
    return best[1] if best else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--marks", required=True)
    ap.add_argument("--sample", required=True)
    ap.add_argument("--utr-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--modes", nargs="*", default=["bbox", "baseline"])
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--pdf", default=str(K.PDF))
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    sample = json.loads(Path(args.sample).read_text(encoding="utf-8"))
    marks = json.loads(Path(args.marks).read_text(encoding="utf-8"))
    cards = []
    for i, m in marks.items():
        s = sample[int(i)]
        if m["m"] == "unsure":
            continue
        truth = (m["idiom"], m["meaning"]) if m["m"] == "wrong" else (s["idiom"], s["meaning"])
        cards.append({"id": int(i), "page": s["page"], "y0": s["y0"], "mark": m["m"], "truth": truth, "old": (s["idiom"], s["meaning"])})
    pages = sorted({c["page"] for c in cards})
    print(len(cards), "cards on", len(pages), "pages", flush=True)
    doc = fitz.open(args.pdf)
    fallback = K.book_line(doc, args.dpi, range(20, min(len(doc), 60), 4))
    runs = {"utrnet": {}}
    for p in pages:
        runs["utrnet"][p] = json.loads((Path(args.utr_dir) / f"page_{p:03d}.json").read_text(encoding="utf-8"))
    for mode in args.modes:
        reader = KrakenReader(MODEL, mode)
        cache = out / f"kraken_{mode}.json"
        if cache.exists():
            runs["kraken_" + mode] = {int(k): v for k, v in json.loads(cache.read_text(encoding="utf-8")).items()}
            continue
        t0 = time.time()
        res = {}
        for p in pages:
            res[p] = K.ocr_page(reader, doc, p, args.dpi, fallback)
            print(mode, "page", p, res[p]["kind"], round(time.time() - t0), "s", flush=True)
        cache.write_text(json.dumps(res, ensure_ascii=False), encoding="utf-8")
        runs["kraken_" + mode] = res
    rows = []
    for name, run in runs.items():
        for c in cards:
            ents = entries_of(run[c["page"]])
            e = match(ents, c["y0"], c["old"][0])
            for fi, field in enumerate(("idiom", "meaning")):
                truth = c["truth"][fi]
                ocr = e[field] if e else None
                r = {"engine": name, "card": c["id"], "page": c["page"], "field": field, "mark": c["mark"], "truth": truth, "ocr": ocr}
                if ocr is not None:
                    bt, bo = base(truth), base(ocr)
                    r.update(n_letters=len(bt), letter_ed=O.ed(bt, bo), n_marks=len(marks_of(truth)),
                             mark_ed=O.ed(marks_of(truth), marks_of(ocr)))
                    if c["mark"] == "wrong":
                        r["sp_missing"], r["sp_extra"], r["sp_total"] = space_errors(truth, ocr)
                rows.append(r)
    (out / "rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\nengine            fields  unmatched  letters  letter-err  marks  mark-err  breaks  missing  extra")
    for name in runs:
        rs = [r for r in rows if r["engine"] == name]
        ok = [r for r in rs if r["ocr"] is not None]
        nl = sum(r["n_letters"] for r in ok)
        le = sum(r["letter_ed"] for r in ok)
        nm = sum(r["n_marks"] for r in ok)
        me = sum(r["mark_ed"] for r in ok)
        sp = [r for r in ok if "sp_total" in r]
        print(f"{name:16}  {len(rs):6}  {len(rs) - len(ok):9}  {nl:7}  {100 * le / max(nl, 1):9.1f}%  {nm:5}  {100 * me / max(nm, 1):7.1f}%  "
              f"{sum(r['sp_total'] for r in sp):6}  {sum(r['sp_missing'] for r in sp):7}  {sum(r['sp_extra'] for r in sp):5}")


if __name__ == "__main__":
    main()
