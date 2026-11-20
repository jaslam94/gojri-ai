# Locked OCR test set

Twenty book pages that no design step of this project has used. The OCR pipeline was designed and tuned on the 12
pages in `data/gold/`, so its score there (3.7% Arabic-letter error) is a development number. This set gives the
honest number for books the pipeline has not seen.

Drawn on 2026-11-20 by `scripts/build_locked_test.py` (seed 20261120). The script refuses to redraw the set.

## Contents

| Path | What it is |
|---|---|
| `pages.tsv` | The frozen list: id, stratum, source PDF, MD5 of the PDF, page (1-based), half (`right`, `left` or `full`; a two-page spread gives one half), ink share. |
| `images/Txx.png` | Each test page at 150 DPI, grayscale, for the speaker who writes the gold text. |
| `drafts/Txx_draft.txt` | A first reading of each page by Claude (in chat, page crops at about 200 DPI), for the speaker to correct. Not our OCR pipeline. `[[...]]` marks a word the reader was unsure of; `[...]` describes a non-text element. |
| `gold/Txx_gold.txt` | The gold text: the draft as corrected by the native speaker. Not written yet. |

One page per book, 20 books, in five strata: 4 dictionaries and glossaries, 5 single-page NOORIN-font books, 4
two-page-spread NOORIN-font books, 3 legacy 8-bit poetry books, 4 image-only scans. Pages come from 15% to 90% of each
book; blank and picture-only pages were redrawn. Left out on purpose: every gold-page source, the books whose pages the
speaker reviewed (Banjara, Dil-Darya), the Quran translation, and two books that share many pages with a gold book.
The PDFs are in the public collection `junaidaslam/gojri-print-pdf-collection` (version `v2.0`).

To correct the drafts: `py -3 -X utf8 scripts/build_test_gold_page.py build`, open `data/test-locked/review.html`,
correct and mark each page Done, download `test_gold.json`, then `... build_test_gold_page.py apply <file>`.

## Rules

1. No design step uses these pages: no tuning, no threshold choice, no prompt choice, no look at OCR output for them.
2. The gold text is written before any OCR output for these pages is seen.
3. A score is taken only at a milestone, with a committed version of the code, and every score is added to the log
   below, good or bad. Never delete a row.
4. If a page turns out unusable (for example a wrong half), record it in the log and keep the page in the list.

## Score log

| Date | System and commit | Arabic-letter error | Notes |
|---|---|---|---|
| | | | No score yet: the gold text is not written. |

Page notes: T05 (*Kaash*, page 40) is an Urdu poem, not Gojri; it stays in the set as a Nastaliq page (rule 4).
T11 mixes a Gojri quatrain, an Urdu footnote and an Arabic verse.
