# Gojri AI Project Roadmap

A living plan. It says where each stage stands, what we decided, and what comes next. `docs/TIMELINE.md` is the dated
summary of the work so far; `LOG.md` holds the detail; `CLAUDE.md` holds the current technical facts. This file was
rewritten on 2026-11-20. The August draft and its strategy reviews are in the git history.

## Where we are (November 2026)

| Stage | State |
|---|---|
| 0. Data hygiene and measurement | Done. Catalog, deduplication, triage, 12-page gold set, speaker review sets. |
| 1. Text extraction (OCR) | A working OCR path for clean printed Nastaliq. Four NOORIN books read in full (Kahawat-Kosh, Banjara, Dil-Darya, Gojri-Ghazal); the machine text is in `data/ocr-output/` for review. On 120 random checked rows of two books: letters 0.60%, marks 5.6%, 173 of 1,314 spaces missing. Word spacing is partly solved for short Gojri idioms, not for prose or verse. Not yet tested on an unseen book or on photographed scans. |
| 2. Speech recognition (ASR) | Best system: Meta Omnilingual ASR LLM-7B with no training on our data, 9.9% word error on the Common Voice test set. Our best fine-tunes: Omnilingual LLM-1B 12.5%, Whisper-medium 18.3%. A test on recordings from outside Common Voice is built and waits for the speaker's recordings. |
| 3. Language model and translation | Not started. Waits for more text. |
| 4. Publish and promote | Three datasets public on Hugging Face (the PDF collection is private). Repository public. |

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
  Mark error fell from 67% to 8% (3 of 36) on 30 checked Kahawat-Kosh cards. The table's glyphs appear in about 30 books.
- **Word spaces are the main open problem.** The PDF text layer has no space glyphs, and in tight prose the gap
  between words is as narrow as the gap inside words. The speaker ruled that spaces follow meaning, not the print.
  Against the speaker's 200 Kahawat-Kosh cards (2026-11-21) the OCR text misses 232 of 759 spaces, 205 of them after
  a non-joining letter. The word-list splitter adds 101 spaces at margin 4, 86 of them right. On 66 splits it proposed in Banjara and
  Dil-Darya, 66 of 72 added spaces were right (the speaker's review of 2026-11-21). An earlier test
  against rows that kept glued words found it adding more wrong spaces than right ones; the two tests differ in
  truth and in book.
  On 2026-11-23 a character n-gram space inserter cut space errors on 100 locked Kahawat-Kosh cards from 116 to 52
  (precision 90.9%, recall 95.0%). On 55 checked Banjara and Dil-Darya cards it added 32 right and 35 wrong spaces;
  52 of those 55 cards sit on rows that the speaker later tagged Urdu. A first Gojri-or-Urdu line tagger reaches 78.4%
  on group cross-validation (97.5% on lines of 61 or more letters, 51.1% on short idioms).
- **The speaker's checks of 24 to 26 November** show that the two models do not carry over to these books. The tagger
  scores 76.1% on 255 prose rows, below "always Gojri" (88.6%). Urdu is about 5% of random rows. On 98 random rows the
  space model adds 209 spaces, 122 of them right (58%); with a limit to tokens of 8 letters or more, 52 of 67 (78%),
  but it then finds only 34% of the missing spaces. On 106 verse-row cards it added 79 right and 49 wrong spaces.
- **A pesh over ک reads as گ.** The PDF draws a different glyph for a true گُ, so the fix needs no model
  (`scripts/ocr_eval/pdf_marks/gaf_fix.py`). Random-row letter error 0.6% to 0.5%, a small test.

### Next steps, in order

1. **Finish the Kahawat-Kosh release.** The release table is built (2,383 entries). The speaker checks the 36 flagged
   fields. Then update `data/ocr-output/` with the fixed run.
2. **Score the locked test set.** The 20 pages are built (`data/test-locked/`, from books no design step touched). The
   speaker's gold text is pending. Then run the page pipeline once, with no tuning, and publish the number.
3. **Test on an unseen book and on photographed scans.** Report the result either way. The image-only books (1,153
   pages) need this before any bulk run.
4. **Word spacing.** The rule is decided (spaces follow meaning). The n-gram inserter works on idioms. It is not good
   enough for prose or verse, and a line language tag does not fix cuts in Urdu words inside Gojri rows. It needs more
   Gojri text with correct spaces, or another method. The speaker's 170 marked cards and 120 random rows are the test
   data. The spaces of the 200 dictionary lines wait for the speaker's check.
5. **Run the NOORIN books in tier order** with PDF marks (dictionaries and glossaries first, then literature, large
   volumes last), with speaker spot checks on a random sample of each book. Check the mark and گ glyph ids per book.
6. **Speaker review of the OCR text.** The text of four full books is in `data/ocr-output/`. Each page a speaker
   checks becomes test data and can later train the OCR.
7. **Publish** the text of books whose rights allow it, with a credit to the source book (`data/pdf-corpus/CREDITS.tsv`).

## Stage 2: Speech recognition (ASR)

### Data

Common Voice Scripted Speech, Gujari: 11,741 clips, 10.67 to 10.68 hours, 11,081 validated rows, 3,852 validated
sentences. We hold release 26.0, kept locally. The release page says 7 speakers; our count of `client_id` in
`validated.tsv` finds 6. Release 27.0 has the same clips and hours (checked 2026-11-28), so a newer download adds no
data. Our split: train 9,041 clips (3 speakers), dev 475, test 623 (the official test set). See `scripts/asr/README.md`.

### What we learned (all on the 623 test clips, one scorer)

| Model | Trained on our data | Word error | Unseen speakers |
|---|---|---|---|
| Omnilingual LLM-7B | no | **9.9%** | 9.6% |
| Omnilingual LLM-3B | no | 12.2% | 11.2% |
| Omnilingual LLM-1B | yes | 12.5% | 12.1% |
| Omnilingual LLM-1B | no | 13.4% | 12.7% |
| Omnilingual LLM-300M | no | 14.9% | 14.1% |
| Whisper-medium | yes | 18.3% | 18.5% |
| Whisper-small | yes | 22.7% | 21.6% |
| Omnilingual CTC-1B | no | 42.4% | 41.1% |

- A model that already knows Gojri beats our fine-tunes of a model that does not (Whisper has no Gojri token).
- Fine-tuning LLM-1B gained 0.85 points. Training loss fell to near zero while dev error stayed near 13%. The limit is
  the small sentence pool and three training voices, not the number of steps.
- The test set is read-aloud book text. Nothing here measures everyday or free speech.
- Overlap with Meta's training data (checked 2026-11-28): the paper names Common Voice v22, and Gujari first appears in
  23.0. Meta's released corpus has no Gujari. Other training sources of the paper are not ruled out.

### Next steps, in order

1. **Own-voice test (ready).** The speaker records 20 to 30 own sentences that are not in Common Voice and types the
   text before seeing any model output. `scripts/asr/voice_test.py` scores LLM-7B, LLM-1B and the fine-tuned LLM-1B.
   About 15 to 20 minutes and about $0.50 on AWS.
2. **A better real-voice test set.** Everyday speech from two or more other Gojri speakers, transcribed by a speaker.
   Agree on consent and a license before recording. Keep it for testing only.
3. **Decide the base model** from steps 1 and 2. If the 7B model holds, it is the Gojri baseline and the next work is
   around it (transcript drafts for new audio, a demo). If its error is much higher on new voices, new data comes first.
4. **More varied training data**, because more steps will not help:
   - New speakers and new sentences through Common Voice. Common Voice takes only public-domain (CC0) sentences, so own
     sentences are usable and text from the books is not, unless the rights holder agrees.
   - Free speech: record it, let the best model draft the text, and let a speaker correct it. Check this on a small
     sample first, to see that correcting is faster than typing.
   - YouTube audio is unlabeled and needs curation and a licensing check before any use.
5. **Then fine-tune again** with the new data. Open technical items: fine-tune LLM-3B (about 70 GB of GPU memory by
   estimate); find a parameter-efficient method for the 7B model (whether Meta's recipe supports one is unknown); score
   the `_v2` model cards, which are not tested. Whisper large-v3 with LoRA is built and has low priority.
6. **Publish** a short report and, if wanted, a demo. Read the Common Voice terms before releasing any weights trained
   on that data.

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

- **Done:** three public Hugging Face datasets (dictionary text, lexicon, OCR gold set), the public code repository,
  and the machine OCR text of four books for review. The PDF collection is private since 2026-11-23. Everything is
  non-commercial and carries an accuracy and AI-use notice.
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
- **PDF licensing.** The PDF collection on Hugging Face stays private. The project shares only derived text, with a
  credit to the source book.
- **Common Voice speaker count:** 7 on the release page, 6 in `validated.tsv`. Low stakes.

## Cross-cutting

- **Budget.** $150 AWS credit. Cost Explorer (credits excluded), read 2026-11-28: gross usage $57.12 from July to date (SageMaker $50.15, Bedrock $6.48, S3 $0.37, Cost Explorer itself $0.11). No data for 27 and 28 November yet; the most recent days can lag. SageMaker training rates from the bill: `ml.g5.xlarge` $1.41 per hour,
  `ml.g5.2xlarge` $1.52, `ml.g5.4xlarge` $2.03, `ml.g5.12xlarge` $7.09. Quotas are one job per instance type, so jobs of different types can run
  together. The credit goes to GPU runs on SageMaker, not to vision APIs. Private S3
  storage: 29.6 GB on 2026-11-28, 18.2 GB of it two fine-tune checkpoints.
- **Measure first.** Every new method gets a score on the gold pages or a speaker-checked set before it touches
  corpus text. Report Arabic-letter error for OCR, with its conditions.
- **Learning.** Each stage is also a chance to learn the ideas behind it as they come up.
