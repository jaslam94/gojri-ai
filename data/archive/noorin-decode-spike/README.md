# NOORIN PUA decode spike (abandoned Aug 2026)

## What we tried

Font-encoded PDFs store Nastaliq as PUA codes (`U+F0xx`) in NOORIN/Batool
fonts. We built a lookup table from Kahawat-Kosh (`Kahawat-Kosh.pdf`, 169
pages): 2,149 `(font, code)` keys, neighbor rules in Python, transfer to 17
other Anjumshanasi books.

## Why we stopped

**Census key coverage is not text quality.** Census reported 100% mapped keys on
Kahawat-Kosh. Decoded text still failed against real page content.

| Check | Result |
|---|---|
| Kahawat page 28 vs OCR ground truth | **98.8% word error** |
| Kahawat page 59 vs human gold | **98.9% word error** |
| User spot-check page 28 | Headword `اکھ کانی چنگی` decoded as `ر کھکانیچ` |

The spike produced plausible glyph sequences with no `[NOORIN:xx]` placeholders
on many pages, but the Unicode output was wrong. Not usable for a text corpus.

## What was removed

- `scripts/census_noorin*.py`, `decode_noorin*.py`, `dump_noorin_lines.py`
- `data/decode/noorin_pua_seed.json`, `noorin_transfer.csv`,
  `transfer_decode_progress.json`
- All local output under `data/decode/out/` from this path (~6,350 page files)

## Corpus path forward

Vision OCR on rendered PDF pages (Gemini 3.6 Flash scored best on the gold set).
See `LOG.md` entry **2026-08-31 — NOORIN decode abandoned**.

Batool and Quran GID decode scripts remain in the repo but are **paused** and
not validated at book scale.
