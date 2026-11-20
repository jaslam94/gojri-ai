"""Experiment: put PDF pesh/zer glyphs into an OCR run's idiom text, by x position. Writes a run folder for score_marks.py."""
import argparse, difflib, json, re, shutil, sys, unicodedata, collections
from pathlib import Path
import numpy as np
import fitz
from PIL import Image
sys.path.insert(0, "D:/Code/VSCodeProjects/gojri-ai/scripts/ocr_eval")
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import ocrlib as O
import ocr_kahawat as K
import marks_align as A
from score_marks import best_entry
from kraken_compare import base

ROOT = A.ROOT
ASPIRATE_RULE = True
PUNCT = ":۔،()-."
V_LETTER = {"nun_n": "ݨ", "nun_l": "ڵ"}  # ݨ (U+0768) for ن+v and ڵ (U+06B5) for ل+v: the speaker's letters (ruling B, 2026-11-15; ڵ ruled by the speaker 2026-11-15, replacing ڶ U+06B6)
HOST_STATS = collections.Counter()   # (OCR letter, glyph letter) of every baked mark that sat on an OCR letter
HOST_FIX = set()   # (OCR letter, glyph letter) pairs that are corrected; set in main from --host-fix, empty = only count
MARK_CH = {"pesh": "ُ", "zer": "ِ", "zabar": "َ", "ulta_pesh": "ٗ", "takhallus": "ؔ"}  # ulta_pesh = inverted damma U+0657 (NOORIC,Bold 61 in Banjara; user truth 2026-11-16)


def is_letter(ch):
    return not (unicodedata.category(ch) == "Mn" or ch.isspace() or ch in PUNCT or unicodedata.category(ch).startswith("P"))


def fold(s):
    return s.replace("ك", "ک").replace("ه", "ہ").replace("ۃ", "ہ").replace("ي", "ی").replace("ى", "ی")


TAKH = "ؔ"  # U+0614, the pen-name sign: the speaker writes it after the last letter of the name (انجمؔ), the print has the bar above it


def move_takhallus(text):
    """Put each takhallus sign after the last letter of its word. The nearest-letter rule puts it one letter early (خالؔد for
    خالدؔ), because the bar sits above and to the right of the final letter. A word is a run without space or tab; trailing
    punctuation stays outside. Only the position of the sign changes."""
    out = []
    for tok in re.split(r"(\s+)", text):
        if TAKH not in tok or tok.isspace():
            out.append(tok)
            continue
        core = tok.rstrip(PUNCT + "()")
        tail = tok[len(core):]
        base = core.replace(TAKH, "")
        out.append(base + TAKH + tail if base else tok)
    return "".join(out)


def insert_marks(text, chars, idx, pm, keep_ocr_marks):
    """text: entry idiom; chars: aligned OCR chars [(ch, x, row)]; idx: indices of letter chars; pm: [(type, x, row)]."""
    t_letters = [i for i, ch in enumerate(text) if is_letter(ch)]
    tl = fold("".join(text[i] for i in t_letters))
    ol = fold("".join(chars[i][0] for i in idx))
    sm = difflib.SequenceMatcher(None, ol, tl, autojunk=False)
    o2t = {}
    for blk in sm.get_matching_blocks():
        for d in range(blk.size):
            o2t[blk.a + d] = blk.b + d
    add = collections.defaultdict(list)  # text letter number -> [mark chars]
    vdrop = set()  # text letter numbers dropped: UTRNet read one ل with a v as two letters, ل then ن (نالن for ناڵ)
    hostfix = {}  # text letter number -> the letter of the baked glyph that replaces the OCR letter
    vmark = {}   # text letter number -> the letter with the small v (ݨ or ڵ) that replaces ن or ل
    for t, xpx, ri in pm:
        t, _, host = t.partition("|")  # host: the letter of a baked glyph (letter and mark in one glyph), or ""
        cand = sorted((abs(chars[i][1] - xpx), j) for j, i in enumerate(idx) if chars[i][2] == ri)
        if not cand:
            continue
        j = cand[0][1]
        if t in ("nun_n", "nun_l"):
            # the "v" sits over the letter. Over ن it makes ݨ; over ل it makes ڵ. UTRNet reads ل+v as ن, so for ل either letter is taken.
            ok = ("ن",) if t == "nun_n" else ("ن", "ل")
            for jj in [j] + [k for k in (j - 1, j + 1) if 0 <= k < len(idx)]:
                if chars[idx[jj]][0] in ok and chars[idx[jj]][2] == ri and jj in o2t:
                    vmark[o2t[jj]] = V_LETTER[t]
                    if t == "nun_l" and chars[idx[jj]][0] == "ن" and jj > 0 and chars[idx[jj - 1]][0] == "ل" and chars[idx[jj - 1]][2] == ri                             and jj - 1 in o2t and o2t[jj - 1] + 1 == o2t[jj]:
                        vdrop.add(o2t[jj - 1])
                    break
            continue
        if host and chars[idx[j]][2] == ri and j in o2t:
            ol = chars[idx[j]][0]
            HOST_STATS[(ol, host)] += 1
            if ol != host and (ol, host) in HOST_FIX:
                hostfix[o2t[j]] = host   # UTRNet read the baked letter wrong (دُ as ڈ): take the letter of the glyph
        # aspirate sign: the speaker writes the mark on the consonant before it (پُھل), except before a و (دھُواں)
        if not host and ASPIRATE_RULE and chars[idx[j]][0] == "ھ" and j > 0 and chars[idx[j - 1]][2] == chars[idx[j]][2] and chars[idx[j - 1]][0] not in "ھ"                 and not (j + 1 < len(idx) and chars[idx[j + 1]][0] == "و"):
            j -= 1
        if j in o2t:
            add[o2t[j]].append(MARK_CH[t])
    out, n = [], -1
    for ch in text:
        if ch in "َُِْ" and not keep_ocr_marks:  # no sukun in the project texts (UTRNet reads the retroflex-nun mark as one); its own zabar is wrong in all 5 cases of Kahawat (the PDF zabar glyph is used)
            continue
        if is_letter(ch):
            n += 1
            if n in vdrop and ch == "ل":
                continue
            out.append(vmark.get(n, ch) if ch in "نل" else hostfix.get(n, ch))
        else:
            out.append(ch)
        if is_letter(ch):
            for m in add.pop(n, []):
                if m not in "".join(out[-3:]):
                    out.append(m)
    return move_takhallus("".join(out)), sum(len(v) for v in add.values())


def field_marks(allm, rows, lo, hi):
    """[(type, x, row index)] of the PDF marks that lie in x range lo..hi and in the y range of one of the rows."""
    pm = []
    for t, xpx, ypx in allm:
        if not (lo <= xpx <= hi):
            continue
        for ri, (ya, yb) in enumerate(rows):
            if ya - 14 <= ypx <= yb + 14:
                pm.append((t, xpx, ri))
                break
    return pm


def main():
    ap = argparse.ArgumentParser(description="Put the PDF pesh/zer glyphs into the entries of an OCR run (all pages, or --cards).")
    ap.add_argument("--base", default=str(ROOT / "data/ocr/kahawat-gpu6"), help="OCR run folder (page_NNN.json with yr/yl rows)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-ocr-marks", action="store_true")
    ap.add_argument("--cards", nargs="*", type=int, help="only the pages of these cards of the marked sample, and only their entries")
    ap.add_argument("--first", type=int, default=1)
    ap.add_argument("--last", type=int, default=169)
    ap.add_argument("--threads", type=int, default=0)
    ap.add_argument("--pages", type=int, nargs="+", help="only these pages (instead of --first..--last)")
    ap.add_argument("--host-fix", nargs="*", default=[], help="pairs OCR-letter+glyph-letter to correct, e.g. ڈد (UTRNet ڈ, glyph د)")
    a = ap.parse_args()
    HOST_FIX.update((p[0], p[1]) for p in a.host_fix)
    if a.threads:
        import torch
        torch.set_num_threads(a.threads)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    utr = O.UTRNet("D:/ocr-tools/utrnet", "D:/ocr-tools/weights/large.pth")
    doc = fitz.open(ROOT / "pdfs/anjumshanasi/Kahawat-Kosh.pdf")
    fb = K.book_line(doc, A.DPI, range(20, min(len(doc), 60), 4))
    stats = collections.Counter()
    jobs = {}  # page -> list of entries to process (None = all)
    if a.cards:
        for cid in a.cards:
            c = A.sample[cid]
            info = json.load(open(Path(a.base) / f"page_{c['page']:03d}.json", encoding="utf-8"))
            e, _ = best_entry(info["entries"], c["idiom"], c["meaning"])
            jobs.setdefault(c["page"], []).append(info["entries"].index(e) if e is not None else None)
    else:
        jobs = {n: None for n in (a.pages or range(a.first, a.last + 1))}
    for n, only in sorted(jobs.items()):
        f = Path(a.base) / f"page_{n:03d}.json"
        if not f.exists():
            continue
        info = json.load(open(f, encoding="utf-8"))
        if info.get("kind") != "entries":
            (out / f.name).write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
            continue
        allm = A.pdf_marks(n - 1)
        gray, ln, pinfo, crops = K.page_setup(doc, n, A.DPI, fb)
        xa, xb0 = ln[0], ln[1]
        y_off = crops[2]
        for ei, e in enumerate(info["entries"]):
            if only is not None and ei not in only:
                continue
            for field, rowkey, crop, x_off, lo, hi in (("idiom", "yr", crops[0], xb0 + 3, xb0 - 1, 10**6), ("meaning", "yl", crops[1], 0, -10**6, xa + 1)):
                rows = e.get(rowkey) or []
                pm = field_marks(allm, rows, lo, hi)
                stats["fields"] += 1
                new = e[field]
                if pm:
                    ink_all = crop < O.otsu(crop)
                    chars = []
                    for ri, (ya, yb) in enumerate(rows):
                        r0, r1 = max(0, ya - y_off - 3), min(crop.shape[0], yb - y_off + 3)
                        for ch, x in A.read_row_aligned(utr, Image.fromarray(crop[r0:r1]), ink_all[r0:r1]):
                            chars.append((ch, x_off + x, ri))
                    idx = [i for i, (ch, _, _) in enumerate(chars) if is_letter(ch) and ch != " "]
                    new, left = insert_marks(e[field], chars, idx, pm, a.keep_ocr_marks)
                    stats["pdf marks"] += len(pm)
                    stats["unplaced"] += left
                    stats["fields with marks"] += 1
                elif not a.keep_ocr_marks:
                    new = e[field].replace("ُ", "").replace("ِ", "").replace("ْ", "").replace("َ", "")
                if new != e[field]:
                    e[field + "_old"] = e[field]
                    e[field] = new
        (out / f.name).write_text(json.dumps(info, ensure_ascii=False), encoding="utf-8")
        print("page", n, dict(stats), flush=True)
    tag = f"{a.first}_{a.last}" if not a.pages else f"p{a.pages[0]}_{len(a.pages)}"
    (out / f"stats_{tag}.json").write_text(json.dumps(dict(stats)), encoding="utf-8")
    (out / f"host_stats_{tag}.json").write_text(json.dumps({o + g: n for (o, g), n in HOST_STATS.items()}, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
