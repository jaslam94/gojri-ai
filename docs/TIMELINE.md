# Project timeline

A short, dated record of what the project did, what it found and what it decided, August to November 2026. Each
line points to the `LOG.md` entry of that date, which holds the detail. Numbers are as reported at the time, unless a
later correction is noted.

## August 2026: the collection and the measurement

- **3 Aug.** Repository started. The 92 collected PDFs turn out to be mostly unreadable as text: InPage-era Noori
  Nastaleeq fonts map glyphs to Private Use Area codes or to Latin letters.
- **3 to 5 Aug.** First vision-model tests on two pages. Claude Haiku 4.5 and Qwen3-VL fail on dense Nastaliq. Llama 4
  Maverick and Pixtral Large are shelved, DeepSeek-OCR has no usable path, GPT is ruled out, Sonnet 5 access is blocked.
  Gemini 3.6 Flash and Claude Sonnet 4.6 stay as candidates.
- **By 3 Aug (Stage 0).** `data/manifest.csv` catalogs all 92 PDFs by hash: 7 exact-duplicate groups (2,244 duplicate
  pages), 21,143 unique pages, 15,478 pages that need decode or OCR. The catalog rescues Gojri books that a first
  character count had marked as English, and finds the Devanagari Gojri-Hindi-English dictionary.
- **3 to 15 Aug.** Twelve gold pages are written and corrected by the native speaker: the OCR benchmark.
- **15 Aug.** Bake-off on the 12 gold pages: one-shot Gemini 3.6 Flash 17.3% word error, Sonnet 4.6 21.9%. Decision:
  **bulk vision OCR is paused.** 17% error cannot go into a corpus without review, and nobody can review 15,000 pages.
- **15 to 31 Aug.** Decode-table attempt for the NOORIN fonts: a 2,149-key table with full key coverage still gives
  98.8% word error. **Abandoned on 31 Aug.** Summary: `data/archive/noorin-decode-spike/README.md`.
- **17 to 22 Aug.** The Batool font of the Gojri-English Dictionary decodes cleanly. The Quran translation, first
  classed as good text, has a broken text layer; a glyph-id table is started and then paused.

## September 2026: first public releases

- **1 to 2 Sep.** Clean text extracted from the Devanagari dictionary. Devanagari to Nastaliq lexicon built in two
  passes (rules, then Gemini), with 50 rows checked by the speaker.
- **27 Sep.** Repository made public. Published on Hugging Face: the lexicon, the OCR gold set and the PDF research
  collection (with per-file credits).
- **28 Sep.** Batool decode scored on the `dict_alif` gold page: 0% word error on the Arabic-script words.

## October 2026: the dictionary corpus and the NOORIN books

- **4 to 13 Oct.** Gemini Pass 2 and an image-against-text audit on all 474 body pages of the Gojri-English Dictionary.
  **13 Oct:** the dictionary text (11,767 entry lines) is published on Hugging Face.
- **24 Oct.** Second, fair test of a NOORIN decode on Kahawat-Kosh: the learning methods give 79% to 100% held-out word
  error. The path stays closed. A line-by-line OCR sheet reaches 0.9% character error but 17.5% word error, almost all
  of it in word spaces.
- **25 Oct.** Method for reading in chat: narrow crops at high zoom, because the vision model shrinks wide images.

## November 2026: an OCR pipeline that works

- **2 to 3 Nov.** Synthetic training data: 20,932 rendered Nastaliq lines. 11,524 real-print line pairs cut from the
  dictionary PDF. A small CRNN line model trained on SageMaker.
- **4 to 5 Nov.** The speaker reviews 200 random dictionary lines and all 160 font codes. 91% of the lines had an
  error, mostly spacing. The font table is corrected (22 codes), the labels are rebuilt, and the dictionary dataset
  version 2 is published (10,228 lines changed). Lexicon version 2: word-initial heh written as ھ.
- **5 Nov.** Our CRNN reads Arabic-script letters at 33.4% error: ruled out. **UTRNet-Large, with no training, reads
  the Arabic runs of the 200 lines at 2.1% letter error.**
- **6 Nov.** Model search closed. Qaari and three TrOCR Urdu models fail. Tesseract reads the English at 0.1%. A page
  pipeline (SegNet script labels, UTRNet for Arabic, Tesseract for English) reaches 3.6% Arabic-letter error on the 12
  gold pages (3.7% after the 15 Nov gold correction).
- **10 to 11 Nov.** Kahawat-Kosh page OCR. Kraken is tested and is behind UTRNet. A UTRNet fine-tune for short vowel
  marks helps only on the dictionary print.
- **11 to 12 Nov.** **Short vowel marks from the PDF itself:** the NOORIN books draw pesh and zer as separate glyphs,
  found by outline hash and placed on the nearest letter. Mark error on 30 checked cards falls from 67% to 14%. The
  same glyphs appear in about 30 books of the collection. Gojri-Ghazal gold page: 11 of 11 readable marks right.
- **15 Nov.** The speaker checks 30 more cards (33 of 34 marks right on the wrong cards). Ruling: write the small "v"
  of the print, ݨ over ن and ڵ over ل. The Ghazal gold page is corrected to match the print. Test: the PDF text layer
  holds no word spaces.
- **16 Nov.** Word spacing rule: spaces follow meaning, not the print. A space follows ۔ and ،.
- **17 Nov.** Research note on how the FLI literature corpus was made: no method and no error rate are published.
- **19 Nov.** Full OCR runs of Banjara and Dil-Darya (716 pages, about $2.50 on AWS). The takhallus sign and the
  inverted pesh are added to the mark table; marks error on 10 checked pages falls from 29.9% to 12.0%. Word spacing
  in tight prose is still not solved.
- **20 Nov.** Repository audit and cleanup:
  - The speaker's review labels are now tracked in `data/reviews/`.
  - Licenses: the code first got the MIT license, then the same day the PolyForm Noncommercial License 1.0.0;
    project data is CC BY-NC 4.0. The project is non-commercial.
  - Credit correction: the digitized dictionary is the *Concise Gojri-English Dictionary* by Dr. M. R. Anjum Awan
    (title pages), not a work of Dr. Javaid Rahi as the published card had said.
  - The machine OCR text of four full books is published in `data/ocr-output/` for Gojri speakers to review, with
    an accuracy and AI-use notice in every public document.
  - Third-party datasets are no longer tracked.
  - Scorer fix: ݨ now counts as an Arabic letter.
  - The UTRNet test now takes a fixed seed, because UTRNet's dropout stays on at inference.
  - Re-scored numbers: bake-off 17.8%, 22.6% and 13.0%; pipeline 3.7%; UTRNet 2.1% (2.0% to 2.2% over five seeds).
  - Duplicate PDFs removed. Every page of every PDF was compared by image, not only by file hash. Besides the 8
    byte-identical copies, 10 more files turned out to be the same book in another file. All 18 were deleted from
    `pdfs/` and flagged in the manifest. Unique pages: 19,725; pages that need decode or OCR: 14,060. The Hugging Face
    PDF collection drops the same duplicates in version 2.0 (64 PDFs).

- **20 Nov (ASR).** First speech recognition baseline: Whisper-small fine-tuned on Common Voice Gujari (9,041 clips,
  3 speakers) reaches 22.7% word error on the official test set, from 73.8% without fine-tuning; 21.6% for speakers
  not in training.

- **21 Nov (word spacing).** The speaker reviewed 200 Kahawat-Kosh cards and wrote the text as words. The OCR text
  misses 232 of 759 spaces (letter error 1.1%); the word-list splitter adds 101 spaces, 86 of them right, and closes about a third of the gap (see
  `data/reviews/kahawat-spacing/README.md`).

- **21 Nov (word splits).** The speaker checked 66 splits that the word-list splitter proposed in Banjara and
  Dil-Darya: 66 of 72 added spaces were right, 6 cut a word. The splitter now never cuts a piece shorter than 2 letters.

- **23 Nov (rights).** The Hugging Face PDF collection is private, because the project has no written permission to
  redistribute the books. The text datasets stay public with a credit to the source book. The docs now say that the
  books are not shared.

- **23 Nov (spacing model, language ID).** A character n-gram space inserter cut space errors on 100 locked
  Kahawat-Kosh cards from 116 to 52 (precision 90.9%, recall 95.0%). On Banjara and Dil-Darya prose, which is largely
  Urdu, it added 32 right and 35 wrong spaces. A first Gojri-or-Urdu line tagger reaches 78.4% on group
  cross-validation (51.1% on short idioms, 97.5% on lines of 61 or more letters). The `اللہ` shadda is now kept as
  printed.

## Not started yet

A Gojri language model. See `ROADMAP.md`.
