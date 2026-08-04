"""
Stage 0, Step 0.3: render the OCR gold-set candidate pages.

Picks specific pages across every hard case found during triage, renders them to
PNG at zoom 2 (the resolution level already decided on, since zoom 3 wastes tokens
for no quality gain), and writes data/gold/candidates.csv describing each one.

This does NOT transcribe anything - that's the per-model test scripts
(gemini_ocr_test.py, bedrock_ocr_test.py), which write into
data/gold/transcriptions/<page_id>/, not this script.

Note: after this script runs, scripts/crop_gold_images.py crops the rendered pages
(cuts image tokens substantially on pages with large blank margins) into
data/gold/images_cropped/, which is what OCR test calls actually use. Re-running
this script regenerates candidates.csv pointing at the uncropped data/gold/images/
originals again - re-point the "image" column at images_cropped/ afterward (or
re-run crop_gold_images.py, which doesn't touch candidates.csv itself).
"""

import csv
import sys
from pathlib import Path

import fitz

sys.path.insert(0, str(Path(__file__).resolve().parent))
from split_spread import render_spread_halves

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "pdfs"
OUT_DIR = ROOT / "data" / "gold" / "images"
CANDIDATES_CSV = ROOT / "data" / "gold" / "candidates.csv"

# (id, relative pdf path, 1-indexed page number, is_spread, note)
# Page numbers chosen by hand after checking each book's page count, aiming for
# content-rich interior pages rather than covers/front matter.
CANDIDATES = [
    ("dict_alif", "anjumshanasi/Gojri-English-Dictionary.pdf", 25, False,
     "PUA scheme, tier1 dictionary, mixed Nastaliq+English on one page"),
    ("kahawat_kosh", "anjumshanasi/Kahawat-Kosh.pdf", 50, False,
     "PUA scheme, tier1, proverb-dictionary layout"),
    ("gojri_adbiyaat", "anjumshanasi/Gojri-Adbiyaat.pdf", 200, False,
     "PUA scheme, tier3, general literary prose"),
    ("gojri_ghazal", "anjumshanasi/Gojri-Ghazal.pdf", 40, False,
     "PUA scheme, tier3, poetry layout (single page, not a spread)"),
    ("mahatma_gandhi", "MAHATMA_GANDHI_Tasweeran_Sangh_Kahani_by.pdf", 30, False,
     "legacy_8bit scheme, the one non-spread example of this scheme"),
    ("kulyate_spread", "javaidrahi-blog/kulyate_rana_fazal_hussan_ed-dr-javaid-rah.pdf", 61, True,
     "legacy_8bit scheme, two-page spread, poetry (previously validated)"),
    ("nazir_spread", "javaidrahi-blog/gojri-kalam-e-nazir-ahmad-nazir-nazir-ed-by-dr-javaid-rahi.pdf", 70, True,
     "legacy_8bit scheme, two-page spread, second example for cross-check"),
    ("louk_warsti", "Gujjar_Qabila_Ki_Louk_Warsti_Dictionary.pdf", 100, False,
     "image_only, tier1, folklore dictionary, no text layer at all"),
    ("shingar_textbook", "GOJRI_TEXT_BOOK_Series_SHINGAR_for_class.pdf", 21, False,
     "image_only, tier2, school textbook (previously validated)"),
    ("primer_pehli", "GUJJARS_GOJRI_KI_PEHLI_KITAB_Gojri_Prime.pdf", 20, False,
     "image_only, tier2, children's primer, likely simpler/larger typography"),
    ("hindi_dict", "anjumshanasi/Gojri-Hindi-English-Dictionary.pdf", 81, False,
     "good_text, Devanagari script -- tests direct EXTRACTION fidelity, not vision OCR"),
    ("quran_translation", "QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf", 100, False,
     "good_text, Perso-Arabic -- tests direct EXTRACTION fidelity, not vision OCR"),
]


def render_page(pdf_rel, page_num_1idx, out_stem):
    doc = fitz.open(PDF_DIR / pdf_rel)
    idx = page_num_1idx - 1
    if idx >= len(doc):
        idx = len(doc) // 2
    page = doc[idx]
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
    out_path = OUT_DIR / f"{out_stem}.png"
    pix.save(out_path)
    real_page = idx + 1
    doc.close()
    return out_path, real_page


def extract_direct_text(pdf_rel, page_num_1idx):
    """For good_text files: pull out what's already there, for the extraction check."""
    doc = fitz.open(PDF_DIR / pdf_rel)
    idx = min(page_num_1idx - 1, len(doc) - 1)
    text = doc[idx].get_text()
    doc.close()
    return text


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for cid, pdf_rel, page_num, is_spread, note in CANDIDATES:
        full_path = PDF_DIR / pdf_rel
        if not full_path.exists():
            print(f"MISSING FILE, skipping: {pdf_rel}")
            continue

        if is_spread:
            idx = page_num - 1
            right_path, left_path = render_spread_halves(
                str(full_path), idx, zoom=2, out_dir=OUT_DIR)
            for half_id, path in ((f"{cid}_a_right", right_path),
                                   (f"{cid}_b_left", left_path)):
                # Rename to the friendly candidate id: split_spread.py names files
                # after the source PDF, which would otherwise mismatch the id-based
                # naming every other candidate uses (and the draft .txt files below).
                renamed = path.with_name(f"{half_id}.png")
                path.replace(renamed)
                rows.append({
                    "id": half_id, "source_pdf": pdf_rel, "page_1idx": page_num,
                    "image": renamed.relative_to(ROOT).as_posix(),
                    "note": note, "check_type": "vision_ocr",
                })
            print(f"[spread] {cid}: {pdf_rel} p{page_num} -> 2 images")
        else:
            path, real_page = render_page(pdf_rel, page_num, cid)
            check_type = "direct_extraction" if cid in ("hindi_dict", "quran_translation") else "vision_ocr"
            rows.append({
                "id": cid, "source_pdf": pdf_rel, "page_1idx": real_page,
                "image": path.relative_to(ROOT).as_posix(),
                "note": note, "check_type": check_type,
            })
            print(f"[single] {cid}: {pdf_rel} p{real_page} -> {path.name}")

    with open(CANDIDATES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"\n{len(rows)} images written to {OUT_DIR}")
    print(f"Candidate manifest: {CANDIDATES_CSV}")


if __name__ == "__main__":
    main()
