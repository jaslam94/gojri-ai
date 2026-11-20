"""Draw and freeze the locked OCR test set: 20 pages, one per book, from books no design step has used.

Run once: py -3 -X utf8 scripts/build_locked_test.py
Writes data/test-locked/pages.tsv (the frozen list, with the MD5 of each source PDF) and data/test-locked/images/
(one 150 DPI grayscale page image each, for the speaker who writes the gold text). It refuses to overwrite an
existing list: the set is drawn once and then never changed.

Strata (seed 20261120, one page per book, page drawn from 15% to 90% of the book, blank or picture-only pages
redrawn): 4 unseen dictionaries and glossaries, 5 single-page NOORIN books, 4 two-page-spread NOORIN books (one half,
right or left at random), 3 legacy 8-bit poetry books, 4 image-only scans. A page is usable when its ink share lies
between half and three times the median of 15 evenly spaced pages of its book (no blank or picture-only pages).
"""
import csv
import hashlib
import random
import sys
from pathlib import Path

import fitz
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "test-locked"
SEED = 20261120

# Books that a design step has used: the gold-page sources, the books whose pages the speaker reviewed, the special
# Quran case, and books that overlap a gold book (Gojri-Adbiyaat) by many pages.
SEEN = {
    "GOJRI_TEXT_BOOK_Series_SHINGAR_for_class.pdf", "GUJJARS_GOJRI_KI_PEHLI_KITAB_Gojri_Prime.pdf",
    "Gujjar_Qabila_Ki_Louk_Warsti_Dictionary_Vol2.pdf", "MAHATMA_GANDHI_Tasweeran_Sangh_Kahani_by.pdf",
    "anjumshanasi/Gojri-Adbiyaat.pdf", "anjumshanasi/Gojri-English-Dictionary.pdf", "anjumshanasi/Gojri-Ghazal.pdf",
    "anjumshanasi/Kahawat-Kosh.pdf", "javaidrahi-blog/gojri-kalam-e-nazir-ahmad-nazir-nazir-ed-by-dr-javaid-rahi.pdf",
    "javaidrahi-blog/kulyate_rana_fazal_hussan_ed-dr-javaid-rah.pdf", "anjumshanasi/Banjara.pdf",
    "anjumshanasi/Dil-Darya.pdf", "QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf",
    "javaidrahi-blog/gojri-adab-ki-tariekh.pdf", "anjumshanasi/Gojri-Sheryaat.pdf",
    "gojri-dictionary-by-dr-javaid-rahi-01.pdf",  # one page only
}
STRATA = [("dictionary", 4), ("noorin_single", 5), ("noorin_spread", 4), ("legacy_8bit", 3), ("image_only", 4)]


def stratum(r):
    if r["category"] == "image_only":
        return "image_only"
    if r["encoding_scheme"] == "legacy_8bit":
        return "legacy_8bit"
    if r["tier"] == "1":
        return "dictionary"
    return "noorin_spread" if r["page_spread"] == "1" else "noorin_single"


def ink_share(page, half):
    pix = page.get_pixmap(matrix=fitz.Matrix(50 / 72, 50 / 72), colorspace=fitz.csGRAY, alpha=False)
    a = np.asarray(Image.frombytes("L", (pix.width, pix.height), pix.samples))
    if half != "full":
        m = a.shape[1] // 2
        a = a[:, m:] if half == "right" else a[:, :m]
    return float((a < 128).mean())


def main():
    if (OUT / "pages.tsv").exists():
        sys.exit("data/test-locked/pages.tsv exists: the locked set is drawn once and never redrawn.")
    rows = [r for r in csv.DictReader(open(ROOT / "data/manifest.csv", encoding="utf-8-sig"))
            if r["is_primary"] == "1" and r["in_scope"] == "1" and r["needs_ocr"] == "1"
            and (ROOT / "pdfs" / r["path"]).exists() and r["path"] not in SEEN]
    rng = random.Random(SEED)
    picked = []
    for name, k in STRATA:
        pool = sorted((r for r in rows if stratum(r) == name), key=lambda r: r["path"])
        for r in rng.sample(pool, k):
            doc = fitz.open(ROOT / "pdfs" / r["path"])
            n = doc.page_count
            probe = [ink_share(doc[int(i)], "right" if r["page_spread"] == "1" else "full")
                     for i in np.linspace(int(n * 0.15), int(n * 0.90) - 1, 15).astype(int)]
            med = float(np.median(probe))
            for _ in range(50):
                p = rng.randint(int(n * 0.15) + 1, max(int(n * 0.15) + 1, int(n * 0.90)))
                half = rng.choice(["right", "left"]) if r["page_spread"] == "1" else "full"
                s = ink_share(doc[p - 1], half)
                if 0.5 * med <= s <= 3 * med:
                    break
            else:
                sys.exit(f"no usable page in {r['path']}")
            md5 = hashlib.md5((ROOT / "pdfs" / r["path"]).read_bytes()).hexdigest()
            picked.append({"id": f"T{len(picked) + 1:02d}", "stratum": name, "pdf": r["path"], "pdf_md5": md5,
                           "page": p, "half": half, "ink_share": round(s, 3)})
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "images").mkdir(exist_ok=True)
    for t in picked:
        page = fitz.open(ROOT / "pdfs" / t["pdf"])[t["page"] - 1]
        clip = page.rect
        if t["half"] != "full":
            m = (clip.x0 + clip.x1) / 2
            clip = fitz.Rect(m, clip.y0, clip.x1, clip.y1) if t["half"] == "right" else fitz.Rect(clip.x0, clip.y0, m, clip.y1)
        pix = page.get_pixmap(matrix=fitz.Matrix(150 / 72, 150 / 72), clip=clip, colorspace=fitz.csGRAY, alpha=False)
        pix.save(str(OUT / "images" / f"{t['id']}.png"))
    with open(OUT / "pages.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(picked[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(picked)
    for t in picked:
        print(t["id"], t["stratum"], t["page"], t["half"], t["pdf"])


if __name__ == "__main__":
    main()
