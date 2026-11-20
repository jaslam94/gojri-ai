# Gojri AI Project Roadmap

A living plan. It says where each stage stands, what we decided, and what comes next. `docs/TIMELINE.md` is the dated
summary of the work so far; `LOG.md` holds the detail; `CLAUDE.md` holds the current technical facts. This file was
rewritten on 2026-11-20. The August draft and its strategy reviews are in the git history.

## Where we are (November 2026)

| Stage | State |
|---|---|
| 0. Data hygiene and measurement | Done. Catalog, deduplication, triage, 12-page gold set, speaker review sets. |
| 1. Text extraction (OCR) | A working OCR path for clean printed Nastaliq. Three NOORIN books read in full: Kahawat-Kosh, Banjara, Dil-Darya (local, not published). Word spacing open. Not yet tested on an unseen book or on photographed scans. |
| 2. Speech recognition (ASR) | Not started. Data in hand. Unblocked. |
| 3. Language model and translation | Not started. Waits for more text. |
| 4. Publish and promote | Four datasets public on Hugging Face. Repository public. |

## Why this order

OCR feeds the other two stages: more clean Gojri text gives more sentences to record and more material to adapt a
language model. The link is strong for Stage 3 and weak for Stage 2. ASR needs audio paired with transcripts, and
the Common Voice data already has that. So Stage 2 does not have to wait for Stage 1. It is a known recipe (the
BaltiVoice project did the same for Balti with 16.8 hours) and the fastest route to a first demo.

## Stage 0: Data hygiene and measurement (done)

- **Catalog.** `data/manifest.csv` (`scripts/build_manifest.py`) lists all 92 PDFs with hash, duplicate group,
  encoding scheme, script, scope and tier. Duplicates: 18 files (3,662 pages) in 14 groups, found by file hash
  and, on 2026-11-20, by comparing every page image; all 18 were deleted from `pdfs/` and are flagged
  `removed_duplicate_nov2026` in the manifest. Unique pages: 19,725.
- **Triage by the script in the text, not by character counts.** This rescued Gojri poetry books in a legacy 8-bit
  encoding and the Devanagari Gojri-Hindi-English Dictionary, which a first count had marked as English. Seven files
  (4,192 pages) are English prose and out of scope.
- **Workload.** 14,060 unique pages need decode or OCR (bad text 12,907 and image-only 1,153). The Quran translation
  (717 pages) is in this number: its text layer is broken, not good text. Two-page spreads: 21 files, 5,168 pages,
  split at the centre with `scripts/split_spread.py`. Tier 1 (dictionaries and glossaries): 12 files, 3,007 pages.
- **Overlaps that stay.** Kept on purpose: three primer pairs are two editions of the same J&K board book (`gojri-books-iind` / `GUJJARS_GOJRI_KI_DOJI_KITAB`, `gojri-book-iiird` / `..._TEJI_KITAB`, `gojri-book-ivth` / `..._CHOTHI_KITAB`; 53 of 64, 23 of 33 and 24 of 33 pages identical); `Gojri-Adbiyaat.pdf` holds about 73% of the pages of `gojri-adab-ki-tariekh.pdf`, and 82 pages of `Gojri-Sheryaat.pdf`. The two Louk Warsti files share no page: they are Vol 1 (ا to س) and Vol 2 (ش to ی) of Javaid Rahi's
*Gujjar Qabila Ki Louk Warsti Dictionary*, now named `Gujjar_Qabila_Ki_Louk_Warsti_Dictionary_Vol1.pdf` and `..._Vol2.pdf`.
- **Measurement.** 12 gold pages (1,791 words) spanning the hard cases, and the speaker's review sets in
  `data/reviews/`. Every OCR decision since then was made against these.

## Stage 1: Text extraction (OCR)

### What we learned

- **Font-encoded PDFs cannot be read as text.** InPage-era Noori Nastaleeq fonts map glyphs to Private Use Area codes
  or to Latin letters, in more than one scheme.
- **Decode tables work for one simple font and fail for NOORIN.** The Batool table decodes the Gojri-English
  Dictionary (160 codes, speaker-checked). The NOORIN fonts are component fonts: a 2,149-key table gave 98.8% word
  error, and learning the clusters from text gave 79% to 100%. That path is closed.
- **One-shot vision models are too error-prone for unreviewed text.** Gemini 3.6 Flash 17.8% and Claude Sonnet 4.6
  22.6% word error on the gold pages. Bulk vision OCR stays paused.
- **UTRNet-Large reads clean Gojri Nastaliq well with no training.** 2.1% Arabic-letter error on the 200 reviewed
  dictionary lines (2.0% to 2.2% over five seeds). With SegNet script labels and Tesseract for English, the page
  pipeline reaches 3.7% on the 12 gold pages (a development number).
- **Short vowel marks come from the PDF itself** in the NOORIN books: separate mark glyphs, found by outline hash.
  Mark error fell from 67% to 14% on 30 checked Kahawat-Kosh cards. The table's glyphs appear in about 30 books.
- **Word spaces are the main open problem.** The PDF text layer has no space glyphs, and in tight prose the gap
  between words is as narrow as the gap inside words. A word-list splitter added more wrong spaces than right ones.
  The speaker ruled that spaces follow meaning, not the print.

### Next steps, in order

1. **Lock a test set.** About 20 new pages that no design step touches, from books the pipeline has not seen.
2. **Test on an unseen book and on photographed scans.** Report the result either way. The image-only books (1,153
   pages) need this before any bulk run.
3. **Word spacing.** First decide one labelling rule for the review truth (some reviewed rows keep glued words, while
   the 2026-11-16 ruling says spaces follow meaning). Then try a small space tagger trained on speaker-checked lines,
   or a speaker review of about 500 lines.
4. **Run the NOORIN books in tier order** with PDF marks (dictionaries and glossaries first, then literature, large
   volumes last), with speaker spot checks on a random sample of each book.
5. **Speaker review of the OCR text.** The text of four full books is in `data/ocr-output/`. Each page a speaker
   checks becomes test data and can later train the OCR.
6. **Publish** the text of books whose rights allow it, with the same credits as the PDF collection.

## Stage 2: Speech recognition (ASR)

Fine-tune Whisper on the Common Voice data, following the BaltiVoice recipe (Whisper-small, 16.8 hours, 26.74% word
error, down from 159% zero-shot). Expect a rough but usable first model.

- **Data:** Common Voice Scripted Speech 26.0, Gujari: 11,741 clips, 10.68 hours, 11,081 validated rows. The release
  page says 7 speakers; our count of `client_id` in `validated.tsv` finds 6. Kept locally, not in this repository.
- **First experiment:** Whisper-small baseline, word error on the Common Voice `test.tsv` split. Never train on it.
- **More data:** new recordings through the normal Common Voice flow (more speakers, past 15 to 20 hours). Sentences
  from the OCR'd books can be read aloud in future drives.
- **YouTube audio:** unlabeled, so it is not direct training data. Possible later uses: self-supervised pretraining or
  pseudo-labeling once a first model exists. Needs audio curation and a licensing check before any public use.

## Stage 3: Language model and translation

Adapt an existing Urdu-capable model to Gojri with transfer learning (for example LoRA), not training from scratch.

- **Decided order:** first a Gojri to Urdu/English translator; then, when quality and text volume allow, an assistant
  that speaks Gojri directly. A cascade (translate in, let an existing LLM answer, translate out) can bridge the gap.
- **Parallel data we have:** the Gojri-Urdu story file in the FLI corpus (`10-3 Stories with Urdu Translations`,
  paragraph-level), the Gojri-English Dictionary text (11,767 entry lines) and the lexicon (1,862 headwords).
- **More parallel data:** a strong LLM drafts translations guided by these real examples; the native speaker corrects
  them.
- **Evaluation:** hold out part of the real Gojri-Urdu pairs and never train on them.

## Stage 4: Publish and promote

- **Done:** four Hugging Face datasets (dictionary text, lexicon, OCR gold set, PDF collection with credits), the
  public code repository, and the machine OCR text of four books for review. Everything is non-commercial and carries
  an accuracy and AI-use notice.
- **Next:** a small demo (dictionary search, OCR on an uploaded page) and contact with FLI and Common Voice, to work
  with the people already active for Gojri.

## Parking lot

- **U+FFFF in the FLI corpus.** 82 broken characters in 4 of the 11 files (the folk stories, the poem and the
  Gojri-Urdu file), probably a lost Gojri mark. No published method or error rate exists for the corpus
  (`plans/RESEARCH-gojri-corpus-provenance.md`). A sample review page is built (`scripts/fli_review.py`); the
  speaker's check is pending. Fix before training on those files.
- **Overlapping books** (primer editions, Gojri-Adbiyaat): see Stage 0. When those books are read, skip the pages
  already read in the other copy.
- **Quran translation (717 pages).** Broken text layer. The glyph-id table is paused; page OCR is the likely path.
- **Orthography.** Gojri has no standard spelling. Rulings so far follow the print: word-initial ھ as printed, ك and
  ک equal, ه and ہ equal, ھ separate, ݨ and ڵ where the print shows the small "v", a space after ۔ and ،, word spaces
  by meaning. Before Stage 3, compare with the spelling of the Common Voice sentences and FLI's proposals, and keep
  one convention across the project.
- **PDF licensing.** The PDF collection is shared for research with per-file credits and a takedown contact. Ask the
  authors and publishers before any commercial or wider release.
- **Common Voice speaker count:** 7 on the release page, 6 in `validated.tsv`. Low stakes.

## Cross-cutting

- **Budget.** $150 AWS credit. The LOG estimates about $8 spent by 11 November and about $2.50 for the 19 November
  book run. The credit goes to short GPU runs on SageMaker (one `ml.g5.xlarge` at a time), not to vision APIs.
  Free notebooks (Colab, Kaggle) suit ASR training.
- **Measure first.** Every new method gets a score on the gold pages or a speaker-checked set before it touches
  corpus text. Report Arabic-letter error for OCR, with its conditions.
- **Learning.** Each stage is also a chance to learn the ideas behind it as they come up.
