# Gojri AI

Resources and measurements to bring Gojri into language technology: printed-text OCR first, then speech
recognition (ASR) and a Gojri language model.

Gojri (Gujari, ISO 639-3 `gju`) is an Indo-Aryan language of the Gujjar communities of Jammu and Kashmir, Himachal
Pradesh, Azad Kashmir, Gilgit-Baltistan, Hazara and eastern Afghanistan. India's 2011 census counted about 1.2 million
speakers. Gojri is not in NLLB-200, and in August 2026 we found no Gojri model on Hugging Face. Most Gojri books are
printed in Nastaliq script with InPage-era fonts, and their PDFs do not give usable Unicode text: the glyphs map to
Private Use Area codes or to Latin letters. This project measures that problem and builds tools and data around it.

## About this project

Gojri AI is a personal, non-profit project for research and language preservation. **It is not for commercial use**
(see [License](#license)).

**AI does much of the work.** AI coding agents (Claude Code and Cursor) wrote most of the code and of this
documentation under the maintainer's direction. AI models also made much of the data: Gemini corrected and audited
the dictionary text; Gemini, Claude and Cursor Composer drafted the gold transcriptions, and Claude drafted the locked
test pages; UTRNet and Tesseract read the book pages; transliteration rules and Gemini made the lexicon's Nastaliq.
The maintainer, a native Gojri speaker, checks samples and decides spelling questions, but **most machine text has
not been checked by a person**.

**Accuracy.** We check numbers against the data and record every correction in [`LOG.md`](LOG.md). Even so, figures,
statements and data can contain errors, inconsistencies or outdated values. Each number in these documents holds only
under the conditions stated with it; reproduce it before you rely on it.

**Help wanted.** We welcome corrections and contributions, above all from Gojri speakers who can review the machine
OCR text in [`data/ocr-output/`](data/ocr-output/README.md). Every checked page becomes test data and helps us improve
and fine-tune the OCR. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Status (November 2026)

| Area | State |
|---|---|
| Catalog of 92 collected PDFs | Done: 18 duplicate files (3,662 pages) found by file hash and by page content and removed; 19,725 unique pages; 14,060 pages that need decode or OCR. `data/manifest.csv` |
| OCR benchmark | Done: 12 gold pages (1,791 words) written and checked by a native speaker. `data/gold/` |
| Gojri-English dictionary text | Published: 474 pages, 11,767 entry lines, from a font decode table, a Gemini correction pass and a corrected table merge. 200 lines were checked by the speaker; the rest is machine text. |
| Devanagari to Nastaliq lexicon | Published: 1,862 headwords, 50 checked by the speaker. `data/lexicon/` |
| OCR for clean printed Nastaliq | Works on born-digital print: see the results below. Not yet tested on a second unseen book or on photographed scans. |
| Short vowel marks | Taken from the PDF text layer of the NOORIN-font books. Tested on four books; the mark glyphs appear in about 30 books of the collection. |
| Word spacing | Open. OCR letters are good, but word spaces in tight prose are often missing. |
| Machine OCR text for review | Published in `data/ocr-output/`: Kahawat-Kosh, Banjara, Dil-Darya and Gojri-Ghazal, mostly unchecked. |
| ASR and language model | Not started. 10.7 hours of Common Voice Gujari audio are available. |

The dated history is in [`docs/TIMELINE.md`](docs/TIMELINE.md). The full experiment journal is [`LOG.md`](LOG.md).

## Main results

All OCR scores below are **Arabic-letter error**: Levenshtein distance over the Arabic-script letters only, with
short vowel marks, spaces and Latin text left out, and ك=ک, ه=ہ, ݩ=ݨ treated as equal (ھ stays separate). We do not
report whole-line character error for the dictionary, because English is 87% of its characters and hides the Nastaliq
errors.

| Test | Result | Conditions | Details |
|---|---|---|---|
| UTRNet-Large, no training, on the Arabic parts of 200 random dictionary lines checked by the speaker | **2.1%** (seed 0); 2.0% to 2.2% over five seeds | Clean born-digital print. Arabic runs cut with the PDF's glyph boxes. 1,400 reference letters. | [`data/utrnet-test/`](data/utrnet-test/README.md) |
| Page pipeline (SegNet script labels, UTRNet for Arabic, Tesseract for English) on the 12 gold pages | **3.7%** (229 of 6,253 letters); English 6.6% | Development set: these pages guided the design. Seed 0, repeatable. Only one gold page is a dictionary page. | [`scripts/ocr_eval/`](scripts/ocr_eval/README.md) |
| One-shot vision models on the 12 gold pages, word error | Gemini 3.6 Flash 17.8%, Claude Sonnet 4.6 22.6% | One API call per page, fixed prompt. | [`data/gold/`](data/gold/README.md) |
| Short vowel marks from the PDF's own mark glyphs, 30 Kahawat-Kosh cards | Mark error 67% (UTRNet alone) to 14% | 36 marks checked by the speaker. | `LOG.md`, 2026-11-11 |
| Line-by-line OCR sheet, Kahawat-Kosh page 50 | 0.9% character error, 17.5% word error | 20 gold lines; nearly all word errors are spaces. | `LOG.md`, 2026-10-24 |

Statements that the data supports, and their limits:

- UTRNet-Large reads clean, short Nastaliq runs of this dictionary at about 2% letter error with no training. This is
  not comparable to scanned-page benchmarks.
- The page pipeline result (3.7%) is a development number. A locked test set and a second, unseen book are still
  needed.
- One-shot vision models make about 18% word errors on these pages. That is too high for corpus text without review.

## What did not work

Each failure has a stored output and a reason in `LOG.md`.

| Method | Result |
|---|---|
| Claude Haiku 4.5, Qwen3-VL (vision models, Aug 2026) | Haiku: placeholder characters and wrong phrases; Qwen3-VL: swapped letters and words. |
| Decode table for the NOORIN fonts (Aug 2026) | 98.8% word error even with full key coverage. Abandoned. |
| Learning the NOORIN glyph clusters from text (Oct 2026) | 79% to 100% held-out word error. Closed. |
| Our own CRNN line model, trained on synthetic and real lines | 33.4% Arabic-letter error. Ruled out. |
| Qaari-0.1 (Urdu VLM) | 186% on line crops, 174% on the gold pages (runaway text). |
| Three TrOCR Urdu models from Hugging Face | 102% to 662%. |
| Kraken with its Urdu model | Behind UTRNet on the Kahawat cards. |
| Full fine-tune of UTRNet on our labels | Damages the letters. Only an output-layer fine-tune kept them. |
| Word-list space splitter | Adds more wrong spaces than right ones. |

## Data

Published on Hugging Face (account [junaidaslam](https://huggingface.co/junaidaslam)):

| Dataset | Content |
|---|---|
| [gojri-english-dictionary](https://huggingface.co/datasets/junaidaslam/gojri-english-dictionary) | Text of the *Concise Gojri-English Dictionary* (Dr. M. R. Anjum Awan), CSV, JSONL and per-page TXT. CC BY-NC 4.0. |
| [gojri-devanagari-nastaliq-lexicon](https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon) | Gojri headwords in Devanagari and Nastaliq, with Roman and English glosses. |
| [gojri-nastaliq-ocr-gold](https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold) | The 12-page OCR benchmark: page images, gold text, model outputs. |
| [gojri-print-pdf-collection](https://huggingface.co/datasets/junaidaslam/gojri-print-pdf-collection) | The 64 unique in-scope print PDFs, with per-file credits, for non-commercial research. |

Third-party data that the project uses but does not re-host: the FLI Gojri Literature Corpus (Mozilla Data
Collective) and Common Voice Gujari 26.0. See [`datasets/README.md`](datasets/README.md).

## Repository map

| Path | Content |
|---|---|
| [`docs/TIMELINE.md`](docs/TIMELINE.md) | Dated summary of the work, findings and decisions. |
| [`LOG.md`](LOG.md) | Full experiment journal, in date order. |
| [`ROADMAP.md`](ROADMAP.md) | Stages of the project and what comes next. |
| [`scripts/`](scripts/README.md) | All code, indexed by project stage in `scripts/README.md`. |
| [`data/manifest.csv`](data/manifest.csv) | Catalog of the 92 PDFs: hash, duplicates, encoding, scope, tier. |
| [`data/gold/`](data/gold/README.md) | OCR gold set and bake-off results. |
| [`data/test-locked/`](data/test-locked/README.md) | Locked test set: 20 pages from 20 books that no design step used. |
| [`data/reviews/`](data/reviews/README.md) | Every check the native speaker made against the print (the test truth). |
| [`data/ocr-output/`](data/ocr-output/README.md) | Machine OCR text of four full books, for Gojri speakers to review. |
| [`data/dictionary/`](data/dictionary/README.md) | The card of the published dictionary text. |
| [`data/utrnet-test/`](data/utrnet-test/README.md) | UTRNet test on the 200 dictionary lines: method, results, error list, examples. |
| [`data/decode/`](data/decode/README.md) | Font decode tables (Batool, Quran glyph ids) and the PDF mark glyph table. |
| [`data/lexicon/`](data/lexicon/README.md) | The Devanagari to Nastaliq lexicon. |
| [`data/pdf-corpus/`](data/pdf-corpus/README.md) | Credits and rights notice for the PDF collection. |
| [`data/archive/`](data/archive/noorin-decode-spike/README.md) | Record of the abandoned NOORIN decode table. |
| [`plans/`](plans/) | Stage plans (historical) and research notes. |
| [`prompts/`](prompts/) | Versioned prompts for the vision-model and lexicon runs. |
| `CLAUDE.md`, `AGENTS.md` | Working briefs for the coding agents: current facts, rules and status. |
| [`CONTRIBUTING.md`](CONTRIBUTING.md), [`DATA-NOTICE.md`](DATA-NOTICE.md), [`LICENSE`](LICENSE) | How to help; rights for code and data; the code license. |

## Reproduce the scores

The two gold-page scorers need only Python 3 (standard library):

```
py -3 -X utf8 scripts/score_gold.py                       # word error of every model run on the 12 gold pages
py -3 -X utf8 scripts/ocr_eval/score_gold_letters.py      # Arabic-letter error of every run (add --latin for English)
```

The UTRNet test needs the UTRNet code and weights (non-commercial: CC BY-NC 4.0 in its LICENSE file, CC BY-NC-SA 4.0 in its README; not in this repository) and the dictionary PDF
from the PDF collection. The 200 line crops and the test truth are tracked in `data/reviews/dictionary-200-lines/`.
Steps: [`data/utrnet-test/README.md`](data/utrnet-test/README.md). Use `--seed` (default 0), because UTRNet keeps
its dropout on at inference; seed 0 gives 29 wrong letters of 1,400 (2.1%).

## Credits

- Dr. M. R. Anjum Awan: compiler of the *Concise Gojri-English Dictionary* (J&K Anjuman Taraqi Gojri Adab), the source of
  the dictionary text.
- Dr. Javaid Rahi: compiler and editor of many books in the collection (dictionaries, folklore, poetry).
- Prof. (Dr.) Rafique Anjum and Ms. Ruksana Sadiq: the Concise Gojri-English-Hindi Dictionary behind the lexicon.
- Forum for Language Initiatives (FLI): the Gojri Literature Corpus and Gojri orthography work.
- Mozilla Common Voice and the Gujari contributors.
- UTRNet: Abdur Rahman, Arjun Ghosh and Chetan Arora (ICDAR 2023).

All book content stays under the copyright of its authors and publishers.

## License

Non-commercial use only. Code and prompts: PolyForm Noncommercial License 1.0.0 ([`LICENSE`](LICENSE)). Project data:
CC BY-NC 4.0, except where a folder has its own license file. Book content stays with its authors and publishers.
Details and third-party terms: [`DATA-NOTICE.md`](DATA-NOTICE.md).

## Contributions and contact

Corrections, native-speaker checks, more gold pages and rights-cleared Gojri text are welcome through issues or pull
requests. See [`CONTRIBUTING.md`](CONTRIBUTING.md).

- GitHub: [jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai)
- Hugging Face: [junaidaslam](https://huggingface.co/junaidaslam)
