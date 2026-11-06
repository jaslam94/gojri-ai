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

## NOORIN path: abandoned (Aug 2026)

We built a 2,149-key PUA table on Kahawat-Kosh and bulk-decoded 17 books.
Census reported 100% key coverage, but decoded text failed validation
(**98.8% word error** on page 28 vs OCR ground truth). Key coverage does not
mean correct Unicode.

**Do not use NOORIN decode for corpus text.** Scripts, seeds, and local
decode output were removed. Summary:
`data/archive/noorin-decode-spike/README.md`.

**Corpus path for font-encoded PDFs: vision OCR** (Gemini 3.6 Flash scored
best on the gold set).

## Batool seed (active)

`batool_pua_seed.json` holds the Batool PUA table (160 codes) for
`Gojri-English-Dictionary.pdf`. **Page 25 vs dict_alif gold:** full-token WER
9.2% (mostly Latin spacing); Arabic-token WER 0%.

**Review and fixes (Nov 2026).** The user checked all 160 codes and 200 random
lines against the print. 22 codes changed (table v3.1), by these rulings:
- F060 and F061 are always ھ, even at the start of a word (479 word-initial
  uses in the book). Context rules for them were removed.
- F0D4 and F0D5 are ك. F0D2 and F0D3 are ک. Both are the same letter, so
  scoring treats ك=ک and ه=ہ as equal. ھ stays a separate letter.
- F0A1 is the joined لا shape and F0CD is a plain final ف.
- F0F1+F031 is ئے with no extra alef (`دوئے`). The old rule added one.
- F0FA, F0EB and F0FC are combining marks (U+0614, U+0611, U+0657).
- F023 stays empty (blank after ﷺ).

On the 192 reviewed lines where the word counts match, the decode equals the
user's fix on 180 lines. Pass2 equals it on 152. Some of the 12 misses are old
fixes that the user has since overruled.

The training labels come from `scripts/synth/merge_decode_letters.py`, which
merges this decode with the pass2 text. See `CLAUDE.md` and `LOG.md`.

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
