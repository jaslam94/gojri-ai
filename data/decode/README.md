# Decode tables (font encoding → Unicode)

These PDFs are not `.INP` InPage files. Public InPage-to-Unicode tools
(KamalAbdali, ltrc/inPageToUnicode, `inpage-format`) read InPage documents.
They do not read our exported PDFs. We take the *idea* (a lookup table), not
their file parsers.

## What the PDFs store

- **Batool / NOORIN (PUA scheme):** Type0 `Identity-H` fonts. A ToUnicode map
  exists, but it maps glyph IDs to Private Use Area codes (`U+F0xx`), not to
  Arabic letters. Copy-paste is therefore garbage by design.
- **TT* subset fonts (legacy 8-bit):** many small fonts, WinAnsi, almost no
  ToUnicode. Extracted text looks like Latin letters.
- English on mixed pages (Arial / Times) is already real Unicode. Leave it.

The table key is `(font family, code)`, not the code alone. The same `U+F0xx`
in Batool is not the same letter as in `NOORIN85`.

Image-only PDFs have no codes. They stay out of this path.

## NOORIN path — abandoned (Aug 2026)

We built a 2,149-key PUA table on Kahawat-Kosh and bulk-decoded 17 books.
Census reported 100% key coverage, but decoded text failed validation
(**98.8% word error** on page 28 vs OCR ground truth). Key coverage does not
mean correct Unicode.

**Do not use NOORIN decode for corpus text.** Scripts, seeds, and local
decode output were removed. Summary:
`data/archive/noorin-decode-spike/README.md`.

**Corpus path for font-encoded PDFs: vision OCR** (Gemini 3.6 Flash scored
best on the gold set).

## Batool seed (paused)

`batool_pua_seed.json` holds a Batool PUA table (160 codes) for
`Gojri-English-Dictionary.pdf`. Not validated at book scale. Do not use
decode output for corpus until scored on gold.

```
py -3 scripts/dump_batool_lines.py 28
py -3 scripts/census_batool.py 25 498
py -3 scripts/decode_batool.py 1 498
```

Decoded pages would go under `data/decode/out/` (gitignored). Do not mix
Batool with NOORIN or TT* fonts.

## Quran GID seed (paused)

`quran_gid_seed.json` is a separate table (570 keys). Key is
`FONT:GID` from `get_texttrace`. Do not copy it onto Batool.
`rawdict` crashes on this PDF.

```
py -3 scripts/dump_quran_gids.py 17
py -3 scripts/census_quran.py 1 717 --write-seed
py -3 scripts/decode_quran.py 1 717
```

Not validated at book scale. Prefer vision OCR for the Quran translation PDF.
