"""Experiment: attach PDF pesh/zer glyphs to OCR letters by x position. Scores against the speaker's marked cards."""
import difflib, json, sys, unicodedata, collections, math
from pathlib import Path
import numpy as np
import fitz
from PIL import Image
sys.path.insert(0, "D:/Code/VSCodeProjects/gojri-ai/scripts/ocr_eval")
import ocrlib as O
import ocr_kahawat as K

S = Path(r"D:/Code/VSCodeProjects/gojri-ai/data/ocr/pdfmarks-work")
ROOT = Path("D:/Code/VSCodeProjects/gojri-ai")
DPI = 200
PT2PX = DPI / 72
sample = json.load(open(ROOT / "data/ocr/kahawat-marks/sample.json", encoding="utf-8"))
marks = json.load(open(ROOT / "data/ocr/kahawat-marks/review_marks.json", encoding="utf-8"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import marks_table as MT


def _book_table():
    """{(font name, gid): seed entry} for the fonts saved in the work folder (dump_fonts.py), found by outline hash."""
    from fontTools.ttLib import TTFont
    seed = json.loads(MT.SEED.read_text(encoding="utf-8"))
    n2x = {k.split("|")[1]: v for k, v in json.load(open(S / "fonts/map_all.json")).items()}
    out = {}
    for name, x in n2x.items():
        if not name.startswith("NOORI"):
            continue
        tt = TTFont(S / f"fonts/x{x}.ttf")
        for gid in range(len(tt.getGlyphOrder())):
            try:
                h = MT.glyph_hash(tt, gid)
            except Exception:
                continue
            if h in seed:
                out[(name, gid)] = seed[h]
    return out


BOOK = _book_table()
TM = {0x64F: "pesh", 0x650: "zer"}
IMG_W, IMG_H = O.IMG_W, O.IMG_H


def read_aligned(utr, img):
    """Like UTRNet.read_conf, also x (px in img) of each emitted character."""
    torch = utr.torch
    im = img.convert("L").transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    w, h = im.size
    rw = IMG_W if math.ceil(IMG_H * w / h) > IMG_W else math.ceil(IMG_H * w / h)
    a = np.asarray(im.resize((rw, IMG_H), Image.Resampling.BICUBIC), dtype="float32") / 255.0
    t = torch.from_numpy((a - 0.5) / 0.5).unsqueeze(0)
    x = torch.zeros(1, IMG_H, IMG_W)
    x[:, :, :rw] = t
    if rw < IMG_W:
        x[:, :, rw:] = t[:, :, rw - 1].unsqueeze(2).expand(1, IMG_H, IMG_W - rw)
    with torch.no_grad():
        probs = utr.net(x.unsqueeze(0).to(utr.dev)).softmax(2)[0]
    am = probs.argmax(1).tolist()
    nfr = len(am)
    out, prev = [], 0
    # group consecutive frames of the same non-blank class into one emitted char: x = mean frame
    i = 0
    while i < nfr:
        k = am[i]
        j = i
        while j + 1 < nfr and am[j + 1] == k:
            j += 1
        if k != 0:
            fmid = (i + j) / 2 + 0.5  # in the 400 wide mirrored input; maps 1:1 to resized px
            xo = (rw - fmid) * w / rw
            out.append((utr.chars[k], xo))
        i = j + 1
    return out


def read_row_aligned(utr, row_img, ink):
    """Chunks of <= 11 x height, read right to left. Returns [(char, x in row_img px)] left to right in x."""
    h = row_img.height
    res = []
    for c0, c1 in O.split_chunks(ink, int(11 * h)):
        a = max(0, c0 - 2)
        crop = row_img.crop((a, 0, c1 + 2, h))
        for ch, x in read_aligned(utr, crop):
            res.append((ch, a + x))
    return sorted(res, key=lambda t: -t[1])


def base_letters(s):
    out = []
    for ch in s:
        if unicodedata.category(ch) == "Mn":
            continue
        if ch.isspace() or ch in ":۔،()-.":
            continue
        out.append(ch)
    s2 = "".join(out)
    return s2.replace("ك", "ک").replace("ه", "ہ").replace("ۃ", "ہ").replace("ي", "ی").replace("ى", "ی")


def truth_marks(idiom):
    """[(host index in base letters, type)] with host = the base letter before the mark."""
    res, n = [], 0
    for ch in idiom:
        if unicodedata.category(ch) == "Mn":
            if ord(ch) in TM and n > 0:
                res.append((n - 1, TM[ord(ch)]))
            continue
        if ch.isspace() or ch in ":۔،()-.":
            continue
        n += 1
    return res


def pdf_marks(page_idx, y_ranges_px=None):
    """[(type, x centre px, y px)] of the mark glyphs of page page_idx (0-based), at DPI. The trace lists a glyph twice.
    The small "v" (type nun) becomes nun_n or nun_l by the letter glyph under it; unknown host glyph: not returned."""
    tr = json.load(open(S / f"trace/p{page_idx}.json"))
    out, seen = [], set()
    chars = [(fn, gid, ox, oy, size) for fn, gid, uc, ox, oy, bb, size in tr]
    for fn, gid, ox, oy, size in chars:
        e = BOOK.get((fn, gid))
        if not e or e["type"] == "vhost":
            continue
        key = (fn, gid, ox, oy)
        if key in seen:
            continue
        seen.add(key)
        x_pt = ox + (e["xmin"] + e["xmax"]) / 2 * size
        t = e["type"]
        if t == "nun":
            h = MT.host_letter(chars, BOOK, x_pt, oy)
            if h is None:
                continue
            t = "nun_n" if h == "ن" else "nun_l"
        if e.get("kind") == "baked" and e.get("letter"):
            t = t + "|" + e["letter"]  # the glyph carries its own letter (دُ is one glyph): marks_insert can check the OCR letter
        out.append((t, x_pt * PT2PX, oy * PT2PX))
    return out


def main(cards):
    utr = O.UTRNet("D:/ocr-tools/utrnet", "D:/ocr-tools/weights/large.pth")
    doc = fitz.open(ROOT / "pdfs/anjumshanasi/Kahawat-Kosh.pdf")
    fb = K.book_line(doc, DPI, range(20, min(len(doc), 60), 4))
    results = []
    for cid in cards:
        c = sample[cid]
        m = marks[str(cid)]
        n = c["page"]
        gray, ln, pinfo, crops = K.page_setup(doc, n, DPI, fb)
        xb = ln[1] + 3
        right, y_off = crops[0], crops[2]
        ink_all = right < O.otsu(right)
        # OCR chars of every idiom row of the entry
        chars = []  # (char, x_page, row_index)
        rows = [(y_off + a0, y_off + b0) for a0, b0 in K.region_rows(right) if c["y0"] - 4 <= y_off + a0 < c["y1"] - 4]
        e = {"yr": rows}
        for ri, (ya, yb) in enumerate(rows):
            a, b = max(0, ya - y_off - 3), min(right.shape[0], yb - y_off + 3)
            img = Image.fromarray(right[a:b])
            for ch, x in read_row_aligned(utr, img, ink_all[a:b]):
                chars.append((ch, xb + x, ri))
        ocr_base = "".join(ch for ch, _, _ in chars if ch != " " and not unicodedata.category(ch).startswith("P"))
        # keep index map for the base letters only
        idx = [i for i, (ch, _, _) in enumerate(chars) if ch != " " and not unicodedata.category(ch).startswith("P") and unicodedata.category(ch) != "Mn"]
        ocr_letters = "".join(chars[i][0] for i in idx)
        ocr_letters_f = base_letters(ocr_letters)
        truth_idiom = m["idiom"]
        tletters = base_letters(truth_idiom)
        sm = difflib.SequenceMatcher(None, tletters, ocr_letters_f, autojunk=False)
        t2o = {}
        for blk in sm.get_matching_blocks():
            for d in range(blk.size):
                t2o[blk.a + d] = blk.b + d
        tm = truth_marks(truth_idiom)
        # PDF marks inside the entry's row y ranges
        pm_all = pdf_marks(n - 1, e["yr"])
        pm = []
        for t, xpx, ypx in pm_all:
            for ri, (ya, yb) in enumerate(e["yr"]):
                if ya - 14 <= ypx <= yb + 14 and xpx >= xb - 4:
                    pm.append((t, xpx, ri))
                    break
        results.append(dict(cid=cid, page=n, k=c["k"], truth=truth_idiom, ocr="".join(ch for ch, _, _ in chars), tm=tm, t2o=t2o, idx=idx,
                            chars=chars, pm=pm, tletters=tletters, oletters=ocr_letters_f))
        print(cid, "letters truth/ocr", len(tletters), len(ocr_letters_f), "matched", len(t2o), "truth marks", tm, "pdf marks", [(t, round(x)) for t, x, _ in pm], flush=True)
    json.dump(results, open(S / "align_results.json", "w"), ensure_ascii=False)
    return results


if __name__ == "__main__":
    ids = [int(a) for a in sys.argv[1:]] or [int(k) for k, v in marks.items() if v["m"] == "wrong"]
    main(ids)
