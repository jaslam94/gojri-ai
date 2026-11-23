# Machine OCR output for review

This folder holds the text that our OCR pipeline produced for four full books. **It is machine output and a person has
not checked it**, except for the small samples in the table below. We publish it so that Gojri speakers can find and
correct errors. Every correction helps us measure the OCR and improve it.

## Contents

| Folder | Book (source PDF file name) | Pages | Run |
|---|---|---|---|
| `kahawat-kosh/entries.tsv` | `anjumshanasi/Kahawat-Kosh.pdf` (proverbs) | 2,383 entries on 151 pages | `kahawat-pdfmarks-v2`, 2026-11-15 |
| `banjara/page_NNN.txt` | `anjumshanasi/Banjara.pdf` | 496 | `prose-aws-full2`, 2026-11-19 |
| `dil-darya/page_NNN.txt` | `anjumshanasi/Dil-Darya.pdf` | 220 | `prose-aws-full2`, 2026-11-19 |
| `gojri-ghazal/page_NNN.txt` | `anjumshanasi/Gojri-Ghazal.pdf` | 209 | `ghazal-full`, 2026-11-20 (seeded) |

Banjara and Dil-Darya are code-mixed: much of their text is Urdu, with Gojri words in the same sentence. Do not count it as
pure Gojri without a language tag per line.

`NNN` and `pdf_page` are PDF page numbers (1-based), not the numbers printed on the pages. In the page files, one
row is one printed line; a TAB separates the two halves of a verse line, and the book name and page number at the top
of a page are a header row. The books are not in this repository. Get each one from its original source (credits: `data/pdf-corpus/CREDITS.tsv`).
Made by `scripts/ocr_eval/export_ocr_output.py` from the local run folders.

How the text was made: UTRNet-Large reads each line from the page image; the short vowel marks, the takhallus sign and
the small "v" of ݨ and ڵ come from the PDF's own mark glyphs (`scripts/ocr_eval/pdf_marks/`).

## How good it is (measured on checked samples only)

| Book | Checked sample | Result |
|---|---|---|
| Kahawat-Kosh | 60 cards checked by the speaker (`data/reviews/kahawat-*`) | Letter error 2.1% (first 30) and 1.2% (second 30); short vowel marks wrong 3 of 36 and 1 of 69 |
| Banjara, Dil-Darya | 178 rows on 10 pages (`data/reviews/prose-banjara-dildarya/`) | Letter error 0.8%; marks wrong 12.0% of 117; 152 space edits on 1,522 spaces |
| Gojri-Ghazal | Gold page 40 (`data/gold/`) | Letter error 1.4%; 11 of 11 readable marks right |

The rest is not checked. Known problems: **word spaces** (words run together in tight prose, and some words split);
marks on letters that the OCR misread; headers and page numbers read as text; Gojri-Ghazal shows 402 takhallus signs,
which is more than expected and may include ornaments.

## How to review

1. Open the book PDF at the page you want to check, and the matching `page_NNN.txt` (or the rows of `entries.tsv`).
2. Compare line by line. Write letters and marks as printed; put word spaces where the meaning has a word break;
   ك and ک, and ه and ہ, count as the same letter; ھ is a separate letter.
3. Send the correction: open an issue on [GitHub](https://github.com/jaslam94/gojri-ai/issues) with the book, the PDF
   page, the line, the OCR text and the correct text, or send a pull request that edits the file. See
   [`CONTRIBUTING.md`](../../CONTRIBUTING.md).

Checked corrections go into `data/reviews/` and become test data for the OCR.

## Terms

The books stay under the copyright of their authors and publishers (credit lines in `data/pdf-corpus/CREDITS.tsv`).
This text is shared for non-commercial research, review and language preservation only, under the terms in
[`DATA-NOTICE.md`](../../DATA-NOTICE.md). Authors or publishers who want a book removed can open an issue.
