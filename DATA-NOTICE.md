# Code and data rights

Gojri AI is a non-commercial project. **Nothing in this repository or in its published datasets may be used for
commercial purposes.** This file lists the terms for each part.

| Part | Terms |
|---|---|
| Code and prompts (`scripts/`, `prompts/`) | PolyForm Noncommercial License 1.0.0 (`LICENSE`). |
| `data/gold/` | OCR gold set: gold text and short page excerpts. Non-commercial. See `data/gold/LICENSE.md`. |
| `data/lexicon/` | Devanagari to Nastaliq lexicon, a derivative of a copyrighted dictionary. Non-commercial. See `data/lexicon/LICENSE.md`. |
| `data/pdf-corpus/` | Credits and rights notice for the PDF collection on Hugging Face. Non-commercial. See `data/pdf-corpus/LICENSE.md`. |
| `data/dictionary/` | The card of the published dictionary text. CC BY-NC 4.0, with credit to Dr. M. R. Anjum Awan, the author of the source dictionary. |
| All other project data (`data/manifest.csv`, `data/decode/`, `data/reviews/`, `data/utrnet-test/`, `data/ocr-output/`, `data/test-locked/`, `data/asr/`) | Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0). Credit "Gojri AI project". |

License history of the code: before commit `49a9002` (2026-11-20) the repository had no license file. That commit
added the MIT license. The same day the code moved to PolyForm Noncommercial 1.0.0, because the project is
non-commercial. Copies taken from commit `49a9002` to commit `e0def0b` keep the MIT terms.

Many data files quote lines from printed Gojri books (dictionary entries, proverbs, OCR text). That text stays under
the copyright of its authors and publishers. These terms give no right to reproduce the books.

## Book content

The source PDFs are not in this repository. Copyright of every book stays with its authors, editors and
publishers, mainly Dr. Javaid Rahi and Prof. (Dr.) Rafique Anjum. Per-file credits: `data/pdf-corpus/CREDITS.tsv`.
Authors or publishers who want a file removed can open an issue on GitHub.

## Published datasets

- `junaidaslam/gojri-english-dictionary`: CC BY-NC 4.0, with credit to Dr. M. R. Anjum Awan (*Concise Gojri-English Dictionary*).
- `junaidaslam/gojri-devanagari-nastaliq-lexicon`: non-commercial; see its `LICENSE.md`.
- `junaidaslam/gojri-nastaliq-ocr-gold`: non-commercial; see its `LICENSE.md`.
- `junaidaslam/gojri-print-pdf-collection`: non-commercial; see its `LICENSE.md` and `CREDITS.tsv`.

## Third-party data and tools (not in this repository)

| Item | Source and license | Note |
|---|---|---|
| Gojri Literature Corpus (FLI) | Mozilla Data Collective, CC BY-NC 4.0 | Download it from the source. See `datasets/README.md`. |
| Common Voice Gujari 26.0 | Mozilla Common Voice, CC0 with Common Voice terms | Download it from the source. Do not re-host it or try to identify speakers. |
| UTRNet code and weights | github.com/abdur75648/UTRNet-High-Resolution-Urdu-Text-Recognition. Non-commercial: its LICENSE file is CC BY-NC 4.0, its README says CC BY-NC-SA 4.0. | Scripts import it from a local clone. |
| Whisper (openai/whisper-small) | Apache 2.0 (model card on Hugging Face) | Downloaded by the ASR job. |
| Tesseract OCR | Apache 2.0 | Installed separately. |
| Kraken and its Urdu model | Apache 2.0 | Used only in one comparison script. |
| Noto Nastaliq Urdu font | SIL Open Font License | Used to render synthetic lines. Not in this repository. |
