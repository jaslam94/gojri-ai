# Dictionary review tool

Builds a local page for a Gojri speaker to check the Batool dictionary text.
Output goes to `data/review/` (gitignored). The build only reads from
`data/synth/real_pairs/`, `data/decode/` and the PDF.

## Build and open

```
py -3 -X utf8 scripts/review/build_review.py
```

Then open `data/review/index.html` in Chrome or Edge. No server is needed.
`--skip-table` rebuilds the line sample and the page only. `--seed` changes the
sample (default 20261103). The sample list is saved in `data/review/line_sample.json`.

## The two checks

1. Table check. One card per Batool code (160), most used first. Each card shows
   the shape from the PDF, the table output, and up to 8 example words. Marks:
   right, wrong (type the right letters), unsure.
2. Line sample. 200 lines from `real_pairs/labels_clean.jsonl` (the old pass2 labels).
   `make_clean_labels.py` no longer writes that file; keep it so the sample can be
   rebuilt. The book is cut into 200 equal
   strata in page order and one line is drawn from each. Marks: OK, wrong letters,
   wrong spacing, bad crop, plus a fix box.

Marks save in the browser (`localStorage`). Use Export JSON to keep a copy.
Import JSON restores one.

## Read the result

The Results tab shows the error rate with a 95% Wilson interval. For a file
export:

```
py -3 -X utf8 scripts/review/summarize_review.py marks.json --out data/review/summary.md
```

## Notes

- The scan decodes every page with a traced copy of the production decoder. The build
  asserts that it gives the same text as `decode_batool_run` on every run.
- Glyph boxes come from `rawdict`. `get_texttrace` gives the same boxes (checked on
  40 pages, largest difference 0.04 pt), but this PyMuPDF build crashes after about
  55 `get_texttrace` calls in one process.
- The raw decode shown under a line is the `page-NNNN.txt` line with the same number.
  It appears only when the raw and Pass 2 files have the same line count (79 of 200).
