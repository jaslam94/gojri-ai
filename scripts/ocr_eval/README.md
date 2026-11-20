# OCR model comparison scripts

Scripts that compare Nastaliq OCR models on Gojri text. The 200-line test set is the 200 dictionary lines the
user reviewed. The reference text for it is `text_fix` in `data/reviews/dictionary-200-lines/labels_review_test.jsonl`
(tracked; also copied into `data/utrnet-test/results.tsv`).

| Script | What it does |
|---|---|
| `dump_arabic_runs.py` | Cuts the Arabic-script parts of the 200 lines into PNG crops, using glyph boxes from the PDF. Needs the dictionary PDF and `scripts/synth/`. |
| `score_qaari.py` | Scores a Qaari output file against the 200 reference lines, next to UTRNet (same metric as `scripts/utrnet_arabic_eval.py`). |
| `sm_qaari/qaari_entry.py`, `launch_qaari.py` | Run Qaari on the crops as one SageMaker training job (`ml.g5.xlarge`). The job stops if the LoRA adapter did not load. |
| `sm_qaari/qaari_pages_entry.py`, `launch_qaari_pages.py` | Run Qaari on whole gold pages (its intended input) as one SageMaker job. |
| `sm_trocr/trocr_entry.py`, `launch_trocr.py` | Run TrOCR-style Urdu models from Hugging Face on the crops (safetensors only; 2 image forms x 2 decoding settings). |
| `utrnet_gold.py` | UTRNet-Large on the 12 gold pages with a line splitter that uses only the page image (no PDF glyph boxes). Needs the UTRNet clone and weights (see `scripts/utrnet_arabic_eval.py`). |
| `dump_script_chunks.py` | Cuts labeled Arabic-script and Latin chunks from real dictionary lines (truth from PDF glyph boxes). |
| `eval_script_tesseract.py` | Tests Tesseract (English) as a script detector and as an English reader on those chunks. |
| `ocrlib.py` | Shared pieces: UTRNet reader, Tesseract reader, row and chunk splitting, `LineReader`, page-mode helpers. |
| `build_segmenter_data.py`, `sm_seg/`, `launch_segnet.py` | Build per-column script labels (Arabic / English / gap) from PDF glyph boxes and train SegNet on SageMaker. |
| `eval_line_reader.py` | Mixed-script line reader on the 200 dictionary lines without PDF glyph boxes (`--segnet` for SegNet). |
| `ocr_page.py` | The full page pipeline (see below). |
| `score_gold_letters.py` | Arabic-letter error of every `*_original.txt` OCR run on the 12 gold pages. Spaces, Latin letters and short vowels are ignored. |

The launch scripts need the environment variable `SAGEMAKER_ROLE_ARN`. Do not commit it.

## Results so far (2026-11-06)

Arabic-letter error on the 200 lines (1,400 reference letters):

| System | Input | Error |
|---|---|---|
| UTRNet-Large | Arabic runs | 2.1% (29 letters, 178 lines exact) |
| Qaari-0.1-Urdu-OCR-VL-2B | Arabic runs, 2x scale on white canvas | 185.9% (46 lines exact) |
| Qaari | Arabic runs, raw crop | 198.5% |
| Qaari | Arabic runs, 2x scale | 212.3% |

Qaari writes sensible text for many short words. On 31 of 200 lines it runs away into long repeated text.
Those lines cause 2,230 of the 2,602 errors. On the other 169 lines it still makes 31.3% errors.
Qaari is a page-level model (trained on synthetic Urdu news pages), so line crops are not its intended input.
It also fails on whole pages (see the gold pages section). Adapter loading was verified in each job
(the library version must match: transformers 4.49 with peft 0.14, see `sm_qaari/requirements.txt`;
with transformers 5 the adapter silently does not load).

### Other crop models (200 lines, same 1,400 letters)

| Model | Best of 4 settings | Exact lines |
|---|---|---|
| `qandeelasim13/urdu-ocr-trocr-si26` | 102.4% | 5 |
| `Khurram123/urdu-poetry-trocr-iqbal` | 662.0% | 5 |
| `Khurram123/urdu-poetry-trocr` | 594.2% | 5 |

Settings: crop as is or centred on a white square; the model card's beam search with repetition penalty 3.0 or plain greedy.
None is usable. `cxfajar197/urdu-ocr` is gated on Hugging Face and not tested yet (waiting for access).

## Gold pages (12 pages, Arabic-letter error of the whole page, spaces and Latin ignored)

Splitter v1 cuts rows at empty ink gaps. v2 (`--valley`) also splits any row taller than 1.6 x the median row height
at its ink valley (touching Nastaliq lines). The 1.6 value was fixed in advance and run once.
Command: `py -3 -X utf8 scripts/ocr_eval/utrnet_gold.py --repo <UTRNet clone> --weights <large.pth> --valley --tag utrnet_v2 --columns kahawat_kosh`.
Outputs are `data/gold/transcriptions/<page>/<page>_utrnet_v1_original.txt` (and `_v2_`, `_qaari_v1_`).

| Page | UTRNet v1 | UTRNet v2 | Qaari (page) | Gemini 3.6 Flash |
|---|---|---|---|---|
| dict_alif (English mixed in) | 100.4% | 99.6% | 718.1% | 5.2% |
| gojri_adbiyaat | 9.2% | 3.2% | 37.9% | 2.8% |
| gojri_ghazal | 1.3% | 1.2% | 37.6% | 1.6% |
| kahawat_kosh (2 columns) | 0.9% | 0.7% | 170.6% | 2.7% |
| kulyate_spread_a_right | 10.5% | 6.2% | 199.5% | 9.0% |
| kulyate_spread_b_left | 15.7% | 3.9% | 332.2% | 0.3% |
| louk_warsti | 1.3% | 1.0% | 335.9% | 1.3% |
| mahatma_gandhi (21 letters) | 4.8% | 0.0% | 28.6% | 0.0% |
| nazir_spread_a_right | 1.7% | 1.3% | 37.1% | not scored |
| nazir_spread_b_left | 2.0% | 2.0% | 481.2% | not scored |
| primer_pehli | 34.3% | 26.5% | 895.8% | not scored |
| shingar_textbook | 5.9% | 6.0% | 33.7% | not scored |
| **Pooled, 12 pages** | **9.2%** | **7.0%** | **174.2%** | |

Without `dict_alif` (English) and `primer_pehli` (decorative primer), UTRNet v2 pools to about 2.8%.
On the 8 pages that Gemini was scored on, UTRNet v1 pools to 10.6% and Gemini to 3.1%.
Qaari writes Urdu-like text with invented words and loops until the token limit on dense pages. It is not usable for Gojri.

## Summary of the model search (2026-11-06)

UTRNet-Large is the only tested model that reads Gojri Nastaliq well (2.1% on dictionary Arabic runs, 2.8% on the
10 clean gold pages). It cannot read English (85.6% error on English runs), and its page score depends on the line
splitter. Next step: a script detector that sends Arabic runs to UTRNet and English runs to an English reader.

## Script detector, first test (2026-11-06)

Data: 3,457 chunks from 1,500 real dictionary lines (1,863 Arabic-script, 1,594 Latin). The chunk edges come from
the PDF glyph boxes, so this tests the classifier only, not the finding of edges on a scanned page.
Tesseract 5.5 (English, `--psm 7`) is already installed on the machine (`C:\Program Files\Tesseract-OCR`).

- English reading: character error 0.1% (16 of 12,931 characters) on 300 Latin chunks.
- Confidence alone (mean word confidence >= 70 means Latin): 93.2% accuracy on a balanced sample of 600; 92.4% on a
  second sample of 800. Confidence is low for correctly read lines full of dictionary punctuation such as `(tarhi)nf:Stiffness;rigidity`.
- Rule "Latin if Tesseract returns at least 15 characters, or confidence >= 80": chosen on sample A (99.3%), then
  98.8% on sample B (8 Arabic chunks called Latin, 2 Latin chunks called Arabic out of 800). The two samples are
  random draws from the same 3,457 chunks and can overlap, so B is not fully independent.

Open problem: on a scanned page the script boundaries inside a line are not known. A complete pipeline must find them
(for example from Tesseract word boxes) before chunks reach UTRNet.

## Full page pipeline (2026-11-06)

`ocr_page.py`: rows from the page image, then a page-level mode, then the readers.
1. SegNet (3 MB CNN) labels every pixel column of a text line as gap, Arabic script or English. It was trained on
   10,112 lines: 6,612 real dictionary lines (labels from PDF glyph boxes, only pages without a reviewed line) and
   3,500 synthetic pure-Arabic story lines. Test (200 reviewed lines): 99.24% of columns right; 22 Arabic columns
   called English and 96 English columns called Arabic, of about 19,000 and 134,000.
2. Page mode: SegNet English runs are checked with Tesseract (at least 6 English letters). If confirmed English covers
   at least 15% of the text width the page is `mixed`, else `arabic`. Measured shares: `dict_alif` 75.6%, every other
   gold page 2.7% or less.
3. `arabic` mode: each row is read by UTRNet alone (chunks of at most 11 x row height, joined right to left).
   `mixed` mode: SegNet runs, Arabic runs by UTRNet, English runs by Tesseract; run text is written left to right.
   An English run that Tesseract cannot confirm (3 or more letters) becomes Arabic.

SegNet weights: `s3://gojri-ai-sagemaker-data/ocr-eval/models/segnet_v2.pt` (not in the repo).

| Test | Arabic-letter error | English character error |
|---|---|---|
| 200 dictionary lines, SegNet v1, no PDF glyph boxes (UTRNet with PDF boxes: 2.1%) | 2.3% (32 of 1,400; 173 lines exact) | 0.7% (61 of 9,370) |
| 12 gold pages, first try (Tesseract word boxes) | not scored (200-line version: 90.6% Arabic, 38.0% English) | |
| 12 gold pages, SegNet v1 on every page | 29.8% pooled | 40.3% |
| 12 gold pages, SegNet v2 on every page | 28.6% pooled | 31.9% |
| **12 gold pages, final (page mode)** | **3.6% pooled (222 of 6,253)** | 6.7% pooled (only `dict_alif` has English: 3.9%) |
| 12 gold pages, UTRNet alone (v2 splitter) | 7.0% | |
| 8 gold pages Gemini was scored on: final pipeline / Gemini 3.6 Flash | 2.7% / 3.1% | `dict_alif`: 3.9% / 2.6% |

Final per page (Arabic-letter error): dict_alif 6.0%, gojri_adbiyaat 3.3%, gojri_ghazal 1.2%, kahawat_kosh 0.9%,
kulyate_spread_a_right 5.7%, kulyate_spread_b_left 4.2%, louk_warsti 0.8%, mahatma_gandhi 0.0%,
nazir_spread_a_right 1.4%, nazir_spread_b_left 2.0%, primer_pehli 28.3%, shingar_textbook 5.9%.
Gemini is better on `kulyate_spread_b_left` (0.3%) and `dict_alif` (5.2% Arabic, 2.6% English).

What went wrong on the way, and the lessons:
- A first training run used labels that a PIL call had collapsed to one value per line (a 1-D array became a 1 pixel wide
  image). The net learned nothing. Always look at label shares and one overlay before training.
- Joining the pieces of one right-to-left sentence from left to right gave many order errors. Consecutive spans of one
  script are one run.
- SegNet trained on dictionary lines only labelled 3% to 25% of each pure-Arabic row as English. Adding synthetic
  pure-Arabic lines did not fix it. Tesseract confirmation of English runs and the page-level mode did.

Caveats: the gold pages guided these design steps (the span merge, the 6-letter check, the page mode), so 3.6% is a
development number. The mode threshold (15%) lies in an empty gap between the measured shares, but only one gold page
is a dictionary page. SegNet knows one dictionary's layout and font. The English reader depends on page resolution
(gold images are about 700 px wide). A new book needs a fresh test before any claim.
