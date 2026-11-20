# Code and data rights

The MIT license in `LICENSE` covers the code and prompts of this project (`scripts/`, `prompts/`). It does not cover
the data, the book text, or third-party tools. This file lists what applies to each part.

## Data made by this project, in this repository

| Path | Terms |
|---|---|
| `data/gold/` | OCR gold set: gold transcriptions and short page excerpts. See `data/gold/LICENSE.md`. |
| `data/lexicon/` | Devanagari to Nastaliq lexicon, a derivative of a copyrighted dictionary. See `data/lexicon/LICENSE.md`. |
| `data/pdf-corpus/` | Credits and the rights notice for the PDF mirror on Hugging Face. See `data/pdf-corpus/LICENSE.md`. |
| `data/manifest.csv`, `data/decode/`, `data/reviews/`, `data/utrnet-test/` | Catalog, font decode tables, speaker review labels, test results. Shared for research, education and language preservation. Cite this project. |

Some of these files quote short lines from printed Gojri books (for example dictionary entries, proverbs and OCR
rows). That text stays under the copyright of its authors and publishers. This repository gives no right to
reproduce the books.

## Book content

The source PDFs are not in this repository. Copyright of every book stays with its authors, editors and
publishers, mainly Dr. Javaid Rahi and Prof. (Dr.) Rafique Anjum. Per-file credits: `data/pdf-corpus/CREDITS.tsv`.

## Published datasets

Each dataset on Hugging Face carries its own license in its card:

- `junaidaslam/gojri-english-dictionary`: CC BY-NC 4.0, with credit to Dr. Javaid Rahi.
- `junaidaslam/gojri-devanagari-nastaliq-lexicon`: see its `LICENSE.md`.
- `junaidaslam/gojri-nastaliq-ocr-gold`: see its `LICENSE.md`.
- `junaidaslam/gojri-print-pdf-collection`: see its `LICENSE.md` and `CREDITS.tsv`.

## Third-party data and tools (not in this repository)

| Item | Source and license | Note |
|---|---|---|
| Gojri Literature Corpus (FLI) | Mozilla Data Collective, CC BY-NC 4.0 | Download it from the source. See `datasets/README.md`. |
| Common Voice Gujari 26.0 | Mozilla Common Voice, CC0 with Common Voice terms | Download it from the source. Do not re-host it or try to identify speakers. |
| UTRNet code and weights | github.com/abdur75648/UTRNet-High-Resolution-Urdu-Text-Recognition, CC BY-NC-SA 4.0 | Scripts import it from a local clone. Non-commercial use only. |
| Tesseract OCR | Apache 2.0 | Installed separately. |
| Kraken and its Urdu model | Apache 2.0 | Used only in one comparison script. |
| Noto Nastaliq Urdu font | SIL Open Font License | Used to render synthetic lines. Not in this repository. |

A result that depends on UTRNet (for example `scripts/ocr_eval/ocr_page.py`) can be used only under the
non-commercial terms of UTRNet, even though our own code is MIT.
