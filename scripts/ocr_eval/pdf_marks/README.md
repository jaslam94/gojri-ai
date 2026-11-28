# Short vowel marks from the PDF text layer (experiment, 2026-11-11)

Idea: the NOORIN PDFs draw pesh and zer as their own glyphs, at their own x position, even where the letters cannot be
decoded. Read the letters with UTRNet (with the x position of every letter), take the mark glyphs from the PDF, and put
each mark after the letter nearest to it in x.

Glyph ids (identical in `Kahawat-Kosh.pdf` and `Gojri-Ghazal.pdf`, same outline hash):
- `NOORIC,Bold` gid 49 = pesh, gid 47 = zer (standalone, ink centred on the glyph origin).
- `NOORIN01,Bold` letter+mark glyphs: pesh 47 (alef), 105, 106 (dal), 111 (reh), 159, 171; zer 49, 100, 101, 131, 134, 153.
- Not yet found: zer inside longer cluster glyphs of other fonts, zabar, shadda.

Order (all paths are under `data/ocr/pdfmarks-work`, local only):
1. `bash scripts/ocr_eval/pdf_marks/dump_all.sh` (from the repo root): `dump_trace.py` and `dump_fonts.py` for every page,
   8 pages per process (pymupdf crashes after many `get_texttrace` calls in one process).
2. `py -3 -X utf8 marks_insert.py --cards 0 1 2 ... --out <run folder>` : reads the idiom and meaning rows with UTRNet
   (needs the UTRNet clone and weights: environment variables `UTRNET_REPO` and `UTRNET_WEIGHTS`, default `local/ocr-tools` (untracked, inside the repository)), inserts the marks into the entries of `data/ocr/kahawat-gpu6`.
3. `py -3 -X utf8 ../score_marks.py --marks ... --sample ... --ocr-dir <run folder>` and `placed.py <run folder>` (which also
   counts the host letter).
`marks_align.py` is the first check (nearest letter vs the speaker's host letter). `glyphrender.py` draws glyph outlines.

## Full book and other books (2026-11-11, later)
- `dump_all.sh` dumps traces and fonts of the whole book. `marks_table.py build|scan` makes and tests the table by outline hash
  (`data/decode/noori_marks_seed.json`). `find_baked.py` searches all glyphs for more pesh and zer outlines.
- Whole book: `py -3 -X utf8 scripts/ocr_eval/pdf_marks/marks_insert.py --first 1 --last 169 --threads 2 --out data/ocr/kahawat-pdfmarks`
  (run four ranges in parallel). Without `--cards` it processes every entry; fields without PDF marks are not read by UTRNet.
- `scan_all.sh` lists which PDFs of the collection use the table's glyphs (word splitting skips file names with spaces).

## Single-column books (2026-11-12)
`prose_marks.py --pdf <pdf> --pages N ... --out <folder>` reads single-column pages (prose, poetry) with UTRNet letter positions and the PDF's own mark glyphs
(found by outline hash, no per-book dump needed). Test: Gojri-Ghazal page 40 against its gold text, 11 of 11 readable marks right.
`marks_table.py add <pdf> <page 0-based> <font> <gid> <type> <kind>` puts a new glyph into the table (used for the zabar glyph, `NOORIN01,Bold` 48).
The gold-page check is `scripts/ocr_eval/pdf_marks/score_prose.py <page json>` (run from the repo root).

## The small "v" (2026-11-15)
Print draws a small v over ن (ݨ) and over ل (ڵ) in Gojri-Ghazal (6 and 6 on p. 40); Kahawat-Kosh has one in the whole book. The v is `NOORIC02,Bold` 27 (type `nun`).
The letter under it comes from the letter glyph (table type `vhost` with a `letter` field):
`marks_table.py add pdfs/anjumshanasi/Gojri-Ghazal.pdf 39 NOORIC01,Bold 175 vhost standalone ل` (also 108 = ن, and `NOORIC,Bold` 168 = ل).
`build` keeps glyphs added with `add`. New books may have other host glyphs: a v over an unknown glyph is not converted. Check with the gold page.

## گ read for ک under a pesh (2026-11-26)
A pesh over ک looks like the second stroke of گ, so UTRNet reads گُ for کُ (random rows: 10 گُ outputs, 3 right; examples `کُن`, `کُجھ`, `کُڑتو`).
A word list cannot decide: `گرو` and `کرو` are both common. The PDF can: a true گُ has the glyph `NOORIC,Bold` 60 beside the pesh glyph `NOORIC,Bold` 49
(within 5 pt in x, 14 pt in y). Count: true گُ 8 of 8 have it, true کُ 0 of 7 (one more row unclear). `gaf_fix.py` applies the row rule (see its docstring):
no glyph 60 at any pesh in the row and enough pesh glyphs: every گُ becomes کُ. Only text changes.
Whole Banjara and Dil-Darya run: 482 rows have گُ; 229 rows change (246 letters), 241 stay, 3 are ambiguous, 9 have too few pesh glyphs.
On the 14 labeled rows that carry گُ or کُ: 6 fixed, 0 broken, 1 row unchanged (truth is ٹ, not a گ/ک case). Random-row letter error 0.6% to 0.5%.
The rule was found on the first 10 cases and confirmed on 8 older ones; it is a small test. Other books may use other glyph ids: check before use.
Output goes to a new run folder (`data/ocr/prose-gaffix`, local); the original run is not changed.

### Kahawat-Kosh (2026-11-26)
`gaf_fix.py kahawat --run data/ocr/kahawat-final2 --out data/ocr/kahawat-final3 --trace-dir <dir>`. The book is alphabetical, which gives labels without the speaker:
OCR گُ at the start of an idiom on pages 120 to 130 (the ک section) must be کُ: 14 of 14 have no glyph 60. On pages 132 to 137 (the گ section) it is گُ: 8 of 8 have glyph 60.
Run: 125 fields with گُ, 88 changed (94 letters: `کُتی`, `کُتا`, `کُجھ`, `کُھلا`, `بالکُل`, `کُوڑ`), 37 kept (`گڑ`, `گناہ`, `گذریو`, `گجر`, `گنگا`), 0 unclear.
Reviewed cards (60 fields per review file): first-30 unchanged (letter error 2.1%), second-30 1.1% to 0.9% (card 12 `گُبا` is now `کُبا`); mark error unchanged (2 of 36, 2 of 69).
Not caught: a `ک` read as `گ` when the pesh went to another letter (second-30 card 14, `گمہا` for `کُمہا`).
