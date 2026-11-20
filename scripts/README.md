# Scripts index

Every script in this folder, grouped by the stage of the project it belongs to. Paths stay as they are, because
`LOG.md` and the dataset cards refer to them. Run all scripts from the repository root with `py -3 -X utf8 <script>`.

Status words: **current** (in use), **done** (its output exists; kept to show how it was made), **paused** (work
stopped, may resume), **ruled out** (the method failed; kept as evidence).

Third-party tools that some scripts need are not in this repository: the UTRNet code and weights (set `UTRNET_REPO`
and `UTRNET_WEIGHTS`), Tesseract 5, and for SageMaker runs the environment variable `SAGEMAKER_ROLE_ARN`. See
`DATA-NOTICE.md`.

## 1. Catalog of the PDF collection (Aug 2026, done)

| Script | What it does |
|---|---|
| `build_manifest.py` | Builds `data/manifest.csv`: one row per PDF with hash, duplicate group, category, encoding scheme, script, scope and tier. Read-only on the PDFs. |
| `inspect_pdf_glyphs.py` | Dumps the (font, codepoint) sequence of one PDF page. |
| `extract_clean_text.py` | Extracts text from the PDFs that already hold correct Unicode (the Devanagari dictionary). |
| `build_pdf_credits.py` | Builds `data/pdf-corpus/CREDITS.tsv` from the manifest. |
| `split_spread.py` | Splits a two-page-spread page image at its centre into the right and the left page. |

## 2. OCR gold set and the vision-model bake-off (Aug 2026, done)

| Script | What it does |
|---|---|
| `build_gold_candidates.py` | Renders the gold-set candidate pages. |
| `build_locked_test.py` | **Current.** Drew and froze the locked test set in `data/test-locked/` (20 pages from 20 unseen books). Run once only; it refuses to redraw. |
| `crop_gold_images.py` | Crops gold page images to their content box. |
| `ocr_test_common.py` | Shared prompt, file naming and run log for the model tests. |
| `gemini_ocr_test.py`, `bedrock_ocr_test.py` | Transcribe a gold page with Gemini 3.6 Flash, or with a model on AWS Bedrock (Claude Haiku 4.5, Claude Sonnet 4.6, Qwen3-VL, Kimi K2.5, Llama 4 Maverick, Pixtral Large). |
| `score_gold.py` | **Current.** Word error of every `*_original.txt` run against `<page>_gold.txt`. Standard library only. |
| `update_bakeoff_csv.py` | **Current.** Rewrites `data/gold/bakeoff_results.csv` from `score_gold.py`. Run after any gold edit. |

## 3. Font decode tables (Aug to Oct 2026)

| Script | What it does |
|---|---|
| `census_batool.py`, `dump_batool_lines.py`, `crop_unknown_batool.py`, `decode_batool.py` | Batool font table for `Gojri-English-Dictionary.pdf` (done): count codes, dump lines, crop unknown codes, decode pages. Table: `data/decode/batool_pua_seed.json`. |
| `score_batool_gold.py` | Scores the Batool decode of page 25 against the `dict_alif` gold page. |
| `batool_pass2_gemini.py`, `batool_pass2_audit.py` | Pass 2 (Gemini with the page image) and the image-against-text audit for all 474 body pages (done). |
| `build_dictionary_release.py` | **Current.** Builds the Hugging Face release of the dictionary text (`data/release/`, gitignored). |
| `census_quran.py`, `dump_quran_gids.py`, `crop_quran_gids.py`, `decode_quran.py` | Quran glyph-id table (paused). Table: `data/decode/quran_gid_seed.json`. |

The NOORIN decode-table scripts were removed when that path failed (Aug 2026). See
`data/archive/noorin-decode-spike/README.md`.

## 4. Devanagari to Nastaliq lexicon (Sep to Nov 2026, done)

| Script | What it does |
|---|---|
| `dict_translit_common.py` | Shared helpers. |
| `dict_translit_pass1.py` | Pass 1: Devanagari headwords to a Nastaliq draft with Aksharamukha rules. |
| `dict_translit_pass2.py` | Pass 2: refines the draft with Gemini. |
| `dict_translit_verify_batch.py` | Builds a batch of rows for the speaker to check. |
| `lexicon_initial_heh.py` | Writes ھ at the start of Gojri words (the speaker's rule of Nov 2026). |

## 5. Speaker review tools

| Script | What it does |
|---|---|
| `review/build_review.py`, `review/review_template.html`, `review/summarize_review.py` | The dictionary review page (200 lines and 160 font codes) and its summary. See `review/README.md`. Results: `data/reviews/dictionary-200-lines/`. |
| `fli_review.py` | Sample review page for the FLI literature corpus, and its text defect rate. |

## 6. Synthetic data and our own line model (Nov 2026, ruled out)

All in `synth/`. Our CRNN reads the Arabic-script letters of the 200 reviewed lines at 33.4% error, so it is not
used. The label tools are still current.

| Script | What it does |
|---|---|
| `synth/synth_generate.py`, `synth/synth_aug.py`, `synth/synth_preview.py` | Render Gojri text into Nastaliq line images, add scan damage, preview a sample. |
| `synth/mine_batool_pairs.py` | Cuts real-print line crops from the dictionary PDF and pairs them with labels. |
| `synth/merge_decode_letters.py`, `synth/make_clean_labels.py` | **Current.** Rebuild the real-print labels from the corrected font table, and write the training label files. |
| `synth/ocr_train.py`, `synth/sagemaker_launch.py`, `synth/sm_entry.py` | CRNN-CTC trainer and its SageMaker launch (ruled out). |
| `synth/build_utrnet_runs.py` | Cuts the Arabic-script runs out of the dictionary lines for the UTRNet fine-tune. |

## 7. OCR model search and the page pipeline (Nov 2026, current)

In `ocr_eval/`. Full results: `ocr_eval/README.md`.

| Script | What it does |
|---|---|
| `utrnet_arabic_eval.py` | **Current.** UTRNet-Large, zero-shot, on the Arabic runs of the 200 reviewed lines (2.1%; use `--seed`). |
| `utrnet_latin_eval.py` | UTRNet on the English parts of the same lines (it cannot read them). |
| `ocr_eval/ocrlib.py` | Shared reader code: UTRNet, Tesseract, row and run helpers. |
| `ocr_eval/ocr_page.py` | **Current.** The page pipeline: rows, SegNet script runs, UTRNet for Arabic, Tesseract for English. |
| `ocr_eval/score_gold_letters.py` | **Current.** Arabic-letter error of every run on the 12 gold pages. Standard library only. |
| `ocr_eval/utrnet_gold.py` | UTRNet alone on the gold pages with a simple line splitter. |
| `ocr_eval/build_segmenter_data.py`, `ocr_eval/sm_seg/`, `ocr_eval/launch_segnet.py` | Build per-column script labels and train SegNet on SageMaker. |
| `ocr_eval/dump_script_chunks.py`, `ocr_eval/eval_script_tesseract.py`, `ocr_eval/eval_line_reader.py` | Script detection tests and the mixed-script line reader test. |
| `ocr_eval/dump_arabic_runs.py`, `ocr_eval/score_qaari.py`, `ocr_eval/sm_qaari/`, `ocr_eval/launch_qaari*.py`, `ocr_eval/sm_trocr/`, `ocr_eval/launch_trocr.py` | Qaari and three TrOCR Urdu models on the same crops and pages (ruled out). |
| `ocr_eval/kraken_compare.py` | Kraken with its Urdu model against UTRNet on the Kahawat cards (behind UTRNet). |
| `ocr_eval/finetune_utrnet.py`, `ocr_eval/launch_finetune.py`, `ocr_eval/sm_finetune_entry.py`, `ocr_eval/launch_sweep.py`, `ocr_eval/sm_sweep_entry.py` | UTRNet fine-tune for short vowel marks (only the output layer helped; replaced by the PDF mark method). |
| `ocr_eval/restore_marks.py` | Restores marks from a marked word list (small gain; not used). |

## 8. Book OCR, PDF marks and word spacing (Nov 2026, current)

| Script | What it does |
|---|---|
| `ocr_eval/ocr_kahawat.py`, `ocr_eval/launch_ocr_pdf.py`, `ocr_eval/sm_ocr_entry.py`, `ocr_eval/english_spans.py` | Kahawat-Kosh (two columns) OCR, with Tesseract for its English notes. |
| `ocr_eval/ocr_prose_pages.py`, `ocr_eval/launch_prose_pages.py`, `ocr_eval/sm_prose_entry.py` | Single-column prose and poetry OCR; `--pdf-marks` adds the PDF's own mark glyphs. |
| `ocr_eval/pdf_marks/` | Short vowel marks, takhallus and the small "v" taken from the PDF text layer by glyph outline hash. See `ocr_eval/pdf_marks/README.md`. Table: `data/decode/noori_marks_seed.json`. |
| `ocr_eval/build_kahawat_review.py`, `ocr_eval/score_marks.py` | Kahawat review cards for the speaker, and the mark score against them. |
| `ocr_eval/build_prose_review.py`, `ocr_eval/score_prose_review.py` | Prose review cards, and letter, mark and space error against them. |
| `ocr_eval/build_spacing_review.py`, `ocr_eval/space_fix.py`, `ocr_eval/space_review.py` | Word spacing: a review page, a word-list splitter (it adds more wrong spaces than right ones), and an accept/reject page for its proposals. |

## 9. Speech recognition baseline (Nov 2026, current)

In `asr/`. See `asr/README.md`.

| Script | What it does |
|---|---|
| `asr/prepare_cv_split.py` | Common Voice Gujari split (sentence-disjoint from the official test set) and private S3 staging. |
| `asr/launch_whisper.py`, `asr/sm_whisper/` | Whisper-small fine-tune and scoring as one SageMaker job. |

`ocr_eval/requirements.txt` lists the packages for the SageMaker jobs (PyMuPDF, Pillow, NumPy, SciPy).
