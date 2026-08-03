"""
Stage 0, Step 0.1 + 0.2: build the single source of truth about every PDF.

Produces data/manifest.csv with one row per PDF: stats, hash-based duplicate
grouping, content category, legacy encoding scheme, script evidence, scope and
processing tier.

Read-only with respect to the PDF collection. Nothing is moved or deleted.
Re-runnable: just overwrites the manifest.
"""

import csv
import hashlib
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "PDFs"
OUT = ROOT / "data" / "manifest.csv"

# Fonts that indicate Perso-Arabic/Nastaliq typesetting. If a document embeds these,
# it is Gojri/Urdu content regardless of what its extracted characters look like,
# which is exactly the trap that previously mislabelled two poetry collections.
#
# NOTE: font-name matching alone is NOT sufficient. A whole family of these PDFs
# embeds subsetted fonts with obfuscated names (TT230t00, TT6A9t00, ...) that carry
# no hint of the script at all. Verified visually: kulyate_rana_fazal_hussan uses
# such fonts and is 494 pages of Gojri Nastaliq poetry. So classification falls back
# to "no known script found in the text -> it is some legacy encoding", which is
# robust to font naming.
NASTALIQ_FONT_HINTS = (
    "noorin", "noori", "nastaliq", "nastaleeq", "batool", "aseer", "sadaf",
    "unwan", "zakharif", "jameel", "alvi", "faiz", "urdu", "naskh", "arabic",
)

# Dictionaries/glossaries are the highest-value documents in the collection: each
# entry is already a translated pair, which is exactly what the Stage 3 translator
# needs. They are also mostly non-Gojri characters by their very nature, so they
# must never be excluded merely for "containing English".
PARALLEL_NAME_HINTS = ("dictionary", "kosh", "glossar", "lughat", "vocab")

# Common English function words, used to tell real English prose apart from
# Latin-range gibberish produced by legacy 8-bit font encodings.
ENGLISH_MARKERS = (
    " the ", " and ", " of ", " in ", " to ", " is ", " was ", " that ", " for ",
)

# Sampling: how many pages to inspect per document.
SAMPLE_PAGES = 10


def sample_page_indices(n_pages, k=SAMPLE_PAGES):
    """Evenly spread sample across the document, skipping the cover page."""
    if n_pages <= 0:
        return []
    if n_pages <= k:
        return list(range(n_pages))
    step = n_pages / float(k)
    idx = sorted({min(n_pages - 1, int(i * step)) for i in range(k)})
    # Drop page 0 when we can afford to: covers are unrepresentative.
    return idx[1:] if len(idx) > 1 else idx


def analyse(pdf_path):
    """Extract every fact we need about one PDF."""
    rec = {
        "pages": 0, "arabic": 0, "devanagari": 0, "pua": 0, "latin": 0,
        "total_chars": 0, "fonts": [], "text_sample": "", "error": "",
        "landscape": 0,
    }
    try:
        doc = fitz.open(pdf_path)
    except Exception as exc:
        rec["error"] = f"open_failed: {exc}"
        return rec

    rec["pages"] = len(doc)
    fonts = Counter()
    text_parts = []

    spread_votes = []
    for i in sample_page_indices(len(doc)):
        try:
            page = doc[i]
            for f in page.get_fonts(full=True):
                # index 3 is the base font name, e.g. "FNTSBS+NOORIN01,Bold"
                fonts[f[3]] += 1
            text = page.get_text()
            r = page.rect
            # A single portrait book page is taller than wide. A PDF page noticeably
            # WIDER than tall is evidence of a two-page spread scanned/exported as one
            # image (seen directly in kulyate_rana_fazal_hussan), which matters for
            # OCR: reading order and RTL column handling differ from a normal page.
            spread_votes.append(r.width > r.height * 1.15)
        except Exception:
            continue

        text_parts.append(text)
        for ch in text:
            if ch.isspace():
                continue
            cp = ord(ch)
            rec["total_chars"] += 1
            if 0x0600 <= cp <= 0x06FF or 0x0750 <= cp <= 0x077F:
                rec["arabic"] += 1
            elif 0x0900 <= cp <= 0x097F:
                rec["devanagari"] += 1
            elif 0xE000 <= cp <= 0xF8FF:
                rec["pua"] += 1
            elif ch.isascii() and ch.isalpha():
                rec["latin"] += 1

    doc.close()
    rec["fonts"] = [name for name, _ in fonts.most_common()]
    rec["text_sample"] = " ".join(text_parts)[:4000]
    rec["landscape"] = int(bool(spread_votes) and sum(spread_votes) > len(spread_votes) / 2)
    return rec


def has_nastaliq_font(fonts):
    joined = " ".join(fonts).lower()
    return any(hint in joined for hint in NASTALIQ_FONT_HINTS)


def looks_like_english(text):
    """Real English prose, as opposed to Latin-range gibberish from a legacy font."""
    lowered = " " + re.sub(r"\s+", " ", text.lower()) + " "
    hits = sum(1 for w in ENGLISH_MARKERS if w in lowered)
    return hits >= 3


def classify(rec):
    """Return (category, encoding_scheme, script_found, likely_english).

    Key principle learned the hard way: decide by WHAT SCRIPT THE TEXT IS IN, not by
    font names (which can be obfuscated) and not by "does it contain English"
    (which wrongly condemns bilingual dictionaries, our most valuable documents).
    """
    english = looks_like_english(rec["text_sample"])
    nastaliq_font = has_nastaliq_font(rec["fonts"])

    # Almost no extractable text at all -> the page is an image.
    if rec["total_chars"] < 30:
        return "image_only", "none", "none", 0

    # Real Perso-Arabic Unicode already present: nothing to fix.
    if rec["arabic"] > 20 and rec["arabic"] >= rec["pua"]:
        return "good_text", "clean_unicode", "perso_arabic", int(english)

    # Real Devanagari Unicode: also already correct, just a different script.
    # Gojri is written in Devanagari in parts of India, so this is genuine Gojri
    # source material, not a foreign language.
    if rec["devanagari"] > 20:
        return "good_text", "clean_unicode", "devanagari", int(english)

    # Glyphs mapped into the Unicode Private Use Area.
    if rec["pua"] > 20:
        return "bad_text", "pua", "legacy_encoded", int(english)

    # Nothing but Latin-range characters left. Two possibilities:
    #  (a) genuine English prose, or
    #  (b) Nastaliq typeset with a legacy 8-bit font, which extracts as gibberish.
    # Recognisable English function words are the discriminator, and this works
    # even when font names are obfuscated subsets like TT230t00.
    if english and not nastaliq_font:
        return "english_prose", "clean_unicode", "latin", 1

    return "bad_text", "legacy_8bit", "legacy_encoded", int(english)


def is_parallel_source(path_str):
    """Dictionaries/glossaries: each entry is already a translated pair."""
    return int(any(k in path_str.lower() for k in PARALLEL_NAME_HINTS))


def assign_tier(path_str, in_scope, parallel):
    """1 = dictionaries/glossaries, 2 = literature, 3 = large volumes, 9 = skip."""
    if not in_scope:
        return 9
    if parallel or "grammar" in path_str.lower():
        return 1
    return 2  # refined to tier 3 later, once page counts are known


def main():
    if not PDF_DIR.is_dir():
        sys.exit(f"PDF directory not found: {PDF_DIR}")

    pdfs = sorted(PDF_DIR.rglob("*.pdf"))
    print(f"Scanning {len(pdfs)} PDFs...")

    rows = []
    by_hash = defaultdict(list)

    for n, p in enumerate(pdfs, 1):
        rel = p.relative_to(PDF_DIR).as_posix()
        md5 = hashlib.md5(p.read_bytes()).hexdigest()
        rec = analyse(p)
        category, scheme, script_found, english = classify(rec)
        parallel = is_parallel_source(rel)

        # In scope = contains Gojri source material in ANY script.
        # Out of scope ONLY for English prose with no Gojri content at all.
        # A bilingual dictionary is mostly non-Gojri characters by definition and
        # is our single most valuable document type, so it stays in scope.
        in_scope = 0 if (category == "english_prose" and not parallel) else 1
        if rec["error"]:
            in_scope = 0

        row = {
            "path": rel,
            "size_mb": round(p.stat().st_size / 1e6, 2),
            "pages": rec["pages"],
            "md5": md5,
            "dup_group": "",
            "is_primary": 1,
            "category": category,
            "encoding_scheme": scheme,
            "script_found": script_found,
            "likely_english": english,
            "parallel_source": parallel,
            "needs_ocr": int(category in ("bad_text", "image_only")),
            "page_spread": rec["landscape"],
            "in_scope": in_scope,
            "tier": assign_tier(rel, in_scope, parallel),
            "arabic_chars": rec["arabic"],
            "devanagari_chars": rec["devanagari"],
            "pua_chars": rec["pua"],
            "latin_chars": rec["latin"],
            "fonts": "; ".join(rec["fonts"][:6]),
            "error": rec["error"],
        }
        rows.append(row)
        by_hash[md5].append(row)
        if n % 20 == 0:
            print(f"  ...{n}/{len(pdfs)}")

    # Mark duplicate groups. Keep the shortest path as primary: it is usually the
    # top-level copy rather than one nested inside a source-specific subfolder.
    gid = 0
    for md5, group in by_hash.items():
        if len(group) < 2:
            continue
        gid += 1
        group.sort(key=lambda r: (len(r["path"]), r["path"]))
        for i, r in enumerate(group):
            r["dup_group"] = f"D{gid:02d}"
            r["is_primary"] = 1 if i == 0 else 0

    # Promote genuinely large in-scope documents to tier 3 (do last, cheaply).
    for r in rows:
        if r["in_scope"] and r["tier"] == 2 and r["pages"] >= 100:
            r["tier"] = 3

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nWrote {OUT} ({len(rows)} rows)\n")
    summary(rows)


def summary(rows):
    def pages(pred):
        return sum(r["pages"] for r in rows if pred(r))

    primary = lambda r: r["is_primary"] == 1
    print("=" * 62)
    print("MANIFEST SUMMARY")
    print("=" * 62)
    print(f"Files: {len(rows)}   Total pages: {pages(lambda r: True)}")

    dup_rows = [r for r in rows if r["dup_group"]]
    groups = len({r["dup_group"] for r in dup_rows})
    wasted = pages(lambda r: r["is_primary"] == 0)
    print(f"Duplicate groups: {groups}  |  redundant copies: "
          f"{sum(1 for r in rows if not primary(r))}  |  wasted pages: {wasted}")

    print("\nBy category (deduped, primary copies only):")
    for cat in ("good_text", "bad_text", "image_only", "english_prose"):
        sel = lambda r, c=cat: primary(r) and r["category"] == c
        print(f"  {cat:14s} {sum(1 for r in rows if sel(r)):3d} files  "
              f"{pages(sel):6d} pages")

    print("\nBy script found (deduped, in-scope only):")
    for s in ("perso_arabic", "devanagari", "legacy_encoded", "none"):
        sel = lambda r, s=s: primary(r) and r["in_scope"] and r["script_found"] == s
        n = sum(1 for r in rows if sel(r))
        if n:
            print(f"  {s:15s} {n:3d} files  {pages(sel):6d} pages")

    needs_ocr = lambda r: primary(r) and r["in_scope"] == 1 and r["needs_ocr"] == 1
    print(f"\nPAGES NEEDING OCR (in-scope, deduped): {pages(needs_ocr)}")

    parallel = lambda r: primary(r) and r["parallel_source"] == 1 and r["in_scope"]
    print(f"PARALLEL/DICTIONARY SOURCES (tier 1, highest value): "
          f"{sum(1 for r in rows if parallel(r))} files, {pages(parallel)} pages")

    print("\nBy tier (in-scope, deduped):")
    for t in (1, 2, 3):
        sel = lambda r, t=t: primary(r) and r["in_scope"] == 1 and r["tier"] == t
        print(f"  tier {t}: {sum(1 for r in rows if sel(r)):3d} files  "
              f"{pages(sel):6d} pages")

    out = [r for r in rows if r["in_scope"] == 0]
    print(f"\nOut of scope ({len(out)} files, {sum(r['pages'] for r in out)} pages):")
    for r in out:
        print(f"  {r['path']}  ({r['category']}, pages={r['pages']})")


if __name__ == "__main__":
    main()
