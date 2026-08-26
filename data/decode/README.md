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

The table key is `(font family, code)`, not the code alone. The same `U+F08A`
in Batool is not the same letter as `U+F08A` in `NOORIN85`.

## How we build a table

1. Extract glyphs with `scripts/inspect_pdf_glyphs.py`.
2. Group a page into lines, read Nastaliq right-to-left.
3. Align that code sequence with the gold Unicode for the same page.
4. Record confident pairs in `data/decode/*.json`.
5. Apply the table to another page of the same font+scheme and score against
   gold (`scripts/score_gold.py`).

Image-only PDFs have no codes. They stay out of this path.

## Seed

`batool_pua_seed.json` holds the Batool PUA table (160 codes). This
dictionary has 160 unique Batool codes on pages 25-498. All are mapped.
The PDF is 498 pages in total (Dr. M. R. Anjum Awan). The 24-page
`Concise_Gojri_English_Dictionary_by_Dr_R.pdf` is the same front matter,
not a second volume. Javaid Rahi dictionary parts use NOORIN. Do not
decode them with this table.

The decoder attaches pesh, zair, and other combining marks to the nearest
host letter. It also applies neighbor rules so `آبلائے`, `نھیں`, `مهارو`,
and `ھُدرو` match gold.

```
py -3 scripts/dump_batool_lines.py 28
py -3 scripts/census_batool.py 25 498
py -3 scripts/decode_batool.py 1 498
```

Decoded pages are written to `data/decode/out/` (gitignored). Do not copy
this table onto NOORIN or TT* fonts.

## NOORIN seed (Kahawat-Kosh)

`noorin_pua_seed.json` is a separate table (**2,149 keys, complete** on
Kahawat-Kosh pages 1–169). Key is `FONT:CODE`. Neighbor rules live in
`scripts/dump_noorin_lines.py` (context-dependent joiners and ligatures).

Decode Kahawat-Kosh (two columns) with `py -3 scripts/decode_noorin.py 1 169`.
Decode other single-flow PUA NOORIN books with
`py -3 scripts/decode_noorin_flow.py PDF START END`.

Transfer scan across the manifest:

```
py -3 scripts/census_noorin_transfer.py
py -3 scripts/census_noorin_transfer.py --skip-census --min-pct 87
py -3 scripts/census_noorin_transfer.py --decode --skip-census --min-pct 87 --batch-size 1
```

Results: `data/decode/noorin_transfer.csv`,
`data/decode/transfer_decode_progress.json`. Decoded pages:
`data/decode/out/<slug>/` (gitignored).

**Transfer (Aug 2026):** 17 Anjumshanasi books decode at 87–97% with this
table (typical 95–97%). `Aks-e-Jamal.pdf` is 92.8% book-wide. Javaid Rahi
dictionary parts stay below 1%: those NOORIN fonts emit Latin-range codes
(`00D4`, not `F0xx`). That is a separate scheme. Do not copy this table
onto Batool.

```
py -3 scripts/dump_noorin_lines.py 50
py -3 scripts/census_noorin.py 1 169
py -3 scripts/decode_noorin.py 1 169
py -3 scripts/census_noorin.py 1 121 pdfs/anjumshanasi/Aks-e-Jamal.pdf
py -3 scripts/decode_noorin_flow.py pdfs/anjumshanasi/Aks-e-Jamal.pdf 1 121 --skip-existing
```

## Quran GID seed (broken ToUnicode)

`quran_gid_seed.json` is a separate table (551 keys). Key is
`FONT:GID` from `get_texttrace`. Do not copy it onto Batool or
NOORIN. Isolated letters often already have good ToUnicode.
Joining bodies often do not. Zero-width Arabic letters are
nuqta overlays; `scripts/dump_quran_gids.py` names the next
host glyph from that ToUnicode value.

`rawdict` crashes on this PDF. Census and decode run in short
child processes.

```
py -3 scripts/dump_quran_gids.py 17
py -3 scripts/census_quran.py 1 717 --write-seed
py -3 scripts/decode_quran.py 1 717
```

Decoded pages are local under
`data/decode/out/quranic-translation-gojri/` (gitignored).
Book census: 976 unique keep keys, 84.5% of table instances.
The Gojri bismillah line on page 16 is the first check page.

