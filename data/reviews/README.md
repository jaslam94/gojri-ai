# Speaker reviews (human labels)

This folder holds every check that a native Gojri speaker made against the printed page. These files are the ground
truth for the tests in this repository. They are small, they cannot be made again without the speaker, and the
scripts read them from here.

The source books are not in this repository (credits: `data/pdf-corpus/CREDITS.tsv`). Get each one from its original
source. This folder holds text and labels, plus the 200 dictionary line crops in `dictionary-200-lines/img/`.

Earlier working copies live in gitignored folders (`data/review/`, `data/ocr/`, `data/synth/real_pairs/`). The files
here are the reference copies. If a working copy differs, this folder is right.

## dictionary-200-lines/

Book: *Concise Gojri-English Dictionary* (Dr. M. R. Anjum Awan), `anjumshanasi/Gojri-English-Dictionary.pdf`, body pages 25 to 498.

| File | What it is |
|---|---|
| `marks_final_20261104.json` | The speaker's export from the review page (`scripts/review/`), 2026-11-04. `table`: all 160 Batool font codes, each marked right (137), wrong (22) or unsure (1), with the fix. `lines`: 200 random lines (one per equal part of the book, seed 20261103), each with the label shown, the raw decode, the error types and the speaker's fix. |
| `labels_review_test.jsonl` | The 200-line test set: one row per line with the crop name and `text_fix` (the speaker's text). Built by `scripts/synth/make_clean_labels.py` from the export. One later hand fix: `page-0125:L26` has ھ (checked against the print on 2026-11-06), where the export still has ه. |
| `summary_final.md`, `analysis_final.md`, `analysis_followup.md` | Error rates and analysis of the review (91% of lines had an error, mostly spacing). |
| `img/` | The 200 line crops (about 300 DPI, 3.1 MB), cut from the PDF by `scripts/synth/mine_batool_pairs.py`. |
| `folio_pages.json` | Per test page: does the entry numbering keep the printed page-number line. Made from the local Pass 2 text, so the test needs no local files. |

Read by: `scripts/utrnet_arabic_eval.py`, `scripts/utrnet_latin_eval.py`, `scripts/synth/make_clean_labels.py`,
`scripts/synth/merge_decode_letters.py`, `scripts/synth/build_utrnet_runs.py` and several scripts in `scripts/ocr_eval/`.

With `img/` and `folio_pages.json` the 200-line UTRNet test runs from this repository, the dictionary PDF (get it from
its original source) and the UTRNet code and weights. Checked on 2026-11-20 with the local work folders hidden: seed 0
gives the same 29 wrong letters and 179 exact lines, line by line.

Known limit: a dozen fixes use spellings that the speaker ruled differently later (for example ہ where the print
shows ھ). See `data/utrnet-test/README.md`.

## kahawat-first-30/

Book: *Kahawat-Kosh* (proverbs, two columns). 30 cards (ids 0 to 29 of `sample.json`, which lists 160 drawn cards).
Each card is one proverb and its meaning. Marked 2026-11-11: 24 wrong (with the speaker's text), 6 OK. Card 28 (key
`27`) was changed on 2026-11-15 by the speaker's ruling `مُچ` (the print).

Read by: `scripts/ocr_eval/score_marks.py`, `scripts/ocr_eval/pdf_marks/marks_align.py`,
`scripts/ocr_eval/build_spacing_review.py` (to skip these cards).

## kahawat-second-30/

Book: *Kahawat-Kosh*. 30 new random cards that have a PDF-placed pesh or zer, none from the first 160. Marked
2026-11-15: 18 wrong, 12 OK. See `LOG.md`, 2026-11-15.

## kahawat-spacing/

Book: *Kahawat-Kosh*. 200 random idioms with the speaker's text written as words (spaces follow meaning). Marked
2026-11-21: 156 fixed, 44 OK, 0 unsure. See `kahawat-spacing/README.md` for the files and scores.

Read by: `scripts/ocr_eval/score_spacing.py`.

## kahawat-allah/

Book: *Kahawat-Kosh*. The 5 fields where the PDF draws اللّٰہ and the OCR text did not read it. Marked 2026-11-26: all 5
wrong, with the speaker's text.

Read by: `scripts/ocr_eval/apply_allah_fixes.py`.

## prose-language/

Books: *Banjara* and *Dil-Darya*. The speaker's language tag of 262 rows (final: 229 Gojri, 31 Urdu, 2 the same in both).
See `prose-language/README.md`.

## prose-model-space/

Books: *Banjara* and *Dil-Darya*. All 170 glued tokens where the character n-gram space inserter proposes spaces, with the
speaker's right spaces. Marked in three passes (2026-11-23 to 2026-11-25); the last pass shows the printed row on each
card: 71 accepted, 99 rejected. See `prose-model-space/README.md`.

## prose-word-splits/

Books: *Banjara* and *Dil-Darya*. 66 glued tokens that the word splitter proposed to split, with the speaker's right split
for each. Marked 2026-11-21: 59 Accept, 7 Reject. See `prose-word-splits/README.md`.

Read by: `scripts/ocr_eval/score_splits.py`.

## prose-banjara-dildarya/

Books: *Banjara* (pages 12, 60, 150, 300, 450) and *Dil-Darya* (pages 12, 50, 100, 150, 200). 183 OCR rows, keys
`book|page|row`. Marked 2026-11-16: 106 wrong, 72 OK, 5 unsure. Each row holds the OCR text, the speaker's text and
the error types (letters, marks, spaces, crop).

Read by: `scripts/ocr_eval/score_prose_review.py`, `scripts/ocr_eval/space_review.py`.

## random-ocr-rows/

Books: *Banjara* and *Dil-Darya*. 120 random rows from all pages, each with the speaker's text (2026-11-26). The least
biased OCR measure on these books. See `random-ocr-rows/README.md`.

Read by: `scripts/ocr_eval/score_space_rule_random.py`.

## How to read the scores

On an OK card the text that the page showed counts as the truth. A check by eye can miss a small error, so scores
on OK cards are optimistic. Report scores on these sets as "error on speaker-checked rows", not as a page error rate.
