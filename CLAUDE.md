# Gojri AI Project

## Goal
Build OCR, ASR (speech-to-text), and a fine-tuned language model for Gojri (گوجری),
an under-resourced language, to help bring it into the AI/LLM space. Long-term
mission: language preservation and promotion of Gojri in AI.

Project is in the **research and planning phase**. No implementation has started.
We research, discuss, and agree on a roadmap together before writing pipeline code.

## Who I'm working with
- Not an AI/ML expert; basic conceptual understanding only. Explain things in simple,
  plain terms. Teach concepts as we go, this is a learning opportunity for the user.
- Native Gojri speaker, native Urdu speaker, fluent English. A Gujjar. Can label data,
  verify translations, judge dialect/quality issues, and correct model output.
- **Never use em dashes in responses.** Use commas, periods, or conjunctions.
- Write English in ASD-STE100 Simplified Technical English: one meaning per word,
  active voice, simple tenses, short sentences. No preambles, pleasantries, or
  filler. Cursor agents also follow `AGENTS.md`.
- Prefers to research and discuss deeply before jumping to implementation.

## Resources available
- $150 USD in free AWS credits.

## The language: Gojri / Gujari (ISO 639-3: gju)
- Indo-Aryan language spoken by Gujjar communities across Jammu & Kashmir, Himachal
  Pradesh (India), Azad Kashmir, Gilgit-Baltistan, Hazara, KP (Pakistan), and eastern
  Afghanistan (~18,580 speakers there per 2015 estimate). India's 2011 census recorded
  ~1.2 million Gojri speakers nationally.
- No standardized orthography yet. SIL/Forum for Language Initiatives (FLI) has
  published research on this ("Writing Gojri" paper) covering dialect variation and
  the difficulty of representing Gojri tone in writing.
- Script varies by region: Nastaliq/Perso-Arabic in Pakistan and Indian-administered
  Kashmir; Devanagari in some Indian states (Himachal Pradesh, Gujarat, etc.).
- Shares script and vocabulary with Urdu, but is grammatically and phonologically its
  own language (distinct morphology, tone system), not a dialect of Urdu.
- Classified as endangered/vulnerable; essentially absent from mainstream NLP:
  not in NLLB-200's language set, no confirmed presence in major LLM training data,
  no dedicated models found on Hugging Face as of this research (Aug 2026).

## Existing ecosystem / prior art (important, avoid duplicating work)
- **Forum for Language Initiatives (FLI)**: the main organization already doing Gojri
  language documentation. Curated the text corpus dataset below, published SIL Global
  orthography research, and maintains a live online **Gojri Dictionary** at
  webonary.org/gojri.
- **Dr. Javaid Rahi**: prolific compiler/editor of Gojri dictionaries, folklore,
  poetry anthologies, and translated works (many of the project's PDFs are his work).
- **BaltiVoice** (arXiv 2606.03504): near-identical precedent project for Balti, another
  Nastaliq-script minority language from Gilgit-Baltistan, Pakistan. Built a 16.8-hour
  Common Voice-derived corpus, fine-tuned Whisper-small (WER 26.74%, down from 159%
  zero-shot), published dataset + model + demo on Hugging Face. This is a solid
  template to follow for the ASR piece.

## Data already collected (local; third-party data is not tracked in git)
- `datasets/Gojri Language Corpus/`: 11 UTF-8 .txt files from the Mozilla Data Collective
  "Gojri Literature Corpus" dataset, curated by FLI. Actually read the content (Aug
  2026), not just file names, confirming word count (~60,814 words) matches the
  dataset's reported ~60,821 tokens, so this is verified as the right/complete data
  despite an earlier, less reliable "117.97 KB" size figure pulled from a page
  summary (that number tracked something else, likely a compressed size, not a
  content gap; text is clean, correct Unicode Nastaliq throughout, no font-encoding
  problems like the PDFs have).
  - Genres: a religious biography (`01-Seerat Nabi Arbi`, 28K words, the bulk of the
    corpus), an Islamic Q&A book (`07-Maharo Deen`, 11.6K words), several short
    children's stories/folktales, one poem.
  - **`10-3 Stories with Urdu Translations - 1306.txt` is a genuine Gojri<->Urdu
    parallel corpus**: several short Gojri stories/poems, each immediately followed
    by an explicit `ترجمہ` (translation) section in Urdu. Alignment is at the
    story/paragraph level, not sentence level, but this is real, valuable seed data
    for the Stage 3 translator goal, more directly useful than the monolingual text.
  - **Data quality issue found**: 82 occurrences of U+FFFF (a reserved Unicode
    "non-character", never valid in real text) scattered through the corpus,
    concentrated entirely in 4 of the 11 files (`08-Shaal Kaka Ko Poot`,
    `09-Rasheed Ko Ghoro`, `10-3 Stories with Urdu Translations`,
    `11-Saeen Kaka Ki Bakri`), zero occurrences in the other 7. Likely explanation:
    Gojri needs diacritic marks beyond standard Urdu's alphabet (SIL's orthography
    research flags this, e.g. for nasalization/retroflex sounds), and these 4 files
    (the more colloquial folk stories/poems) probably used such a mark that didn't
    survive whatever process produced this corpus, while the more formal religious/
    Q&A texts in the other 7 files may not have needed it. Needs investigating (check
    against an original source if one exists) before using these 4 files as
    training-quality data.
  License: CC-BY-NC-4.0 (non-commercial only, attribution required).
- **`datasets/cv-corpus-26.0-2026-06-12/gju/`: the Common Voice "Scripted Speech 26.0 - Gujari"
  dataset, confirmed present locally** (verified Aug 2026, not just referenced from
  the dataset page as earlier noted). Standard Common Voice layout
  (`clips/`, `train.tsv`, `dev.tsv`, `test.tsv`, `validated.tsv`, etc.).
  Directly verified by reading the files: 11,741 audio clips, 10.68 total hours
  (`clip_durations.tsv`), 11,081 validated rows. **Speaker count discrepancy**: the
  online dataset page reports 7 speakers, but our own count of unique `client_id`
  values in `validated.tsv` found only **6**. Minor, but noted rather than silently
  picking one number, likely the 7th speaker's clips live only in `other.tsv` or
  `invalidated.tsv`, not confirmed. Gender field is 'unknown' for all validated rows
  in this release, so gender-based diversity can't be assessed from the data itself.
  License: CC0 (public domain, no re-hosting/speaker-identification per terms).
- `pdfs/`: 92 PDF files, dictionaries, textbooks, poetry, folklore, a Quran
  translation, history volumes, etc. See the precise, hash-verified categorization
  and duplicate list further down (not repeated here to avoid two sources of truth).
- `pdfs/unlocked/`: contains one already-extracted .txt sample that reads as clean,
  correct Nastaliq Unicode (including bracketed image descriptions like
  `[لوگو: ...]`). **Resolved**: asked the user directly, this was not produced by
  running any AI/OCR tool ourselves, it's a file collected as-is from an online
  source that happened to already have clean text. It is *not* evidence that a
  vision pipeline was already tried on our own scans, that validation was done
  separately and directly (see OCR findings below).

## Key technical findings from research

### Garbled text when copy-pasting from PDFs (CONFIRMED with direct inspection)
Verified directly (Aug 2026) using PyMuPDF against the actual files in `pdfs/`, not
just literature research. Root cause confirmed: most of these PDFs embed Nastaliq
text using **Noori Nastaleeq**, the Nastaliq font family bundled with InPage (the
desktop publishing software used for nearly all Urdu/Nastaliq print production for
decades). Noori Nastaleeq splits Nastaliq's huge number of letter-connection shapes
across ~80+ separate numbered sub-fonts (we found font names like `NOORIN01` through
`NOORIN86`, `Batool`, `BatoolBold`, `Aseer`, `Sadaf`, `Unwan` across the corpus, all
`Identity-H` encoded). Each glyph is mapped to a Unicode **Private Use Area** code
point (e.g. `U+F05D`) instead of a real Arabic-script character, so pulling "text"
out of these PDFs literally cannot produce correct Unicode without a font-specific
PUA-to-Unicode remapping table.
- Survey of first 3 pages across all 92 PDFs found dozens of these numbered fonts in
  wide use, confirming this is the dominant pattern across the collection, not a
  one-off.
- This is a well-known, solved problem in the Urdu NLP/publishing world (Noori
  Nastaleeq was the de facto standard font for two decades), so mapping tables and
  open-source converters already exist, e.g. `KamalAbdali/InpageToUnicode` on GitHub.
  Next step is to test one of these converters (or build a small custom PUA map for
  the specific fonts we see) against a real sample page and confirm it reproduces
  correct Gojri/Urdu text.
- Some PDFs may need a different approach: `GOJRI_TEXT_BOOK_Series_SHINGAR_for_class.pdf`
  (14.7 MB) has **no extractable text at all** (pdftotext returns ~0 characters across
  72 pages), confirming it's a pure scanned-image PDF needing real OCR, not a
  font-remapping fix. Both problem types exist in the collection and need separate
  handling.

### OCR for scanned Nastaliq pages
- Nastaliq is much harder to OCR than Naskh (the straighter script Arabic/Urdu is
  often printed in) because letters are diagonal, cursive, and heavily
  context-dependent. This is still an active research problem (LREC 2026 papers on it).
- **UTRNet** (arXiv 2306.15782, open source): current state-of-the-art hybrid CNN-RNN
  model for printed Urdu OCR, with real (UTRSet-Real) and synthetic training sets, and
  a scanned-document line-detection benchmark (UrduDoc). Performs reasonably on Naskh,
  struggles more on Nastaliq specifically.
- **Tested and confirmed (Aug 2026)**: rendered a page from the font-encoded
  dictionary (`anjumshanasi/Gojri-English-Dictionary.pdf`, page 25) and a page from
  the "no text layer" school textbook (`GOJRI_TEXT_BOOK_Series_SHINGAR_for_class.pdf`,
  page 21) to PNG images and read them directly with Claude's vision. Both were
  transcribed accurately and fluently in both cases, since these are all
  born-digital/typeset pages (clean vector-quality text, gradients, design elements),
  not photographs of physical worn books, which is a much easier case for OCR than a
  camera scan of an old book would be. This means a vision-LLM-based transcription
  pipeline (render page to image, ask a vision model to transcribe) is a promising
  and validated first strategy for **both** problem types in this collection, since
  it bypasses the broken font encoding and the missing text layer at the same time.
  Caveat: only tested on 2 pages from 2 files so far; true photographed/degraded
  scans (if any exist in the 92 PDFs) may behave worse and haven't been tested yet.
- Practical implication for AWS credit: Claude (and other vision LLMs) is available
  through AWS Bedrock, so bulk page-by-page transcription of the PDF collection is a
  concrete, budget-appropriate use of the $150 credit.
- **In-chat reading method (Oct 2026)**: read line strips at 3x instead of the full
  page, then re-read each doubtful row. On Kahawat-Kosh page 19 this corrected four
  words that the 1x view got wrong (`آب حیات` for `آپ جایات`, among others). It also
  showed that one proverb can run over two printed rows. Count entries by sentence,
  not by row. Page 19 output is in `data/decode/out/kahawat-kosh/chat/pages/`. No
  page has a human check yet.
- **Narrow-crop rule (Oct 2026)**: a "5x" or "8x" strip is false zoom. The vision
  encoder shrinks any image to about 1568 px wide, so a wide strip keeps only about
  2x. Dots stay soft and letters merge. Read narrow clips only: 300 native px wide or
  less, final size 1500 px or less. For the sharpest check, render the clip straight
  from the PDF at 1200 DPI (`page.get_pixmap(clip=rect, matrix=fitz.Matrix(16.6667,
  16.6667))`). At that zoom the gold rules become testable: final `-و` vs `-ے`,
  printed madda, `ک` vs `گ`, `ب` vs `پ`, `ت` vs `ٹ`, and the heh forms. Word gaps
  are 5 to 13 px at 600 DPI; letter gaps are 3 to 4 px. Measure the gap, do not
  judge it by eye.

### PDF collection triage: refined into 4 buckets (Aug 2026 automated scan)
Ran a finer script across all 92 PDFs, counting Arabic-Unicode-block characters vs
Private-Use-Area (PUA) characters vs Latin characters in sampled pages of each file:
- **4 files = "good text already"**: correct Arabic-block Unicode, no fix needed,
  just extract and clean. Includes `QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf` and
its duplicate `javaidrahi-blog/gojri-quran-final-1010-1.pdf` (717 pages each, a
huge chunk of total page count, and duplicated), plus `ABC-Islamic-Studies.pdf`
  (401 pages) and `Revival-of-Islam.pdf` (116 pages), both under `pdfs/anjumshanasi/`.
  **Correction (Aug 2026):** the Quran file is not clean Unicode. Direct extract
  of page 17 (and the rest) is unreadable. UrduTypesetting ToUnicode maps many
  joining glyphs to unrelated BMP codepoints (Buhid, Latin-extended, IPA). The
  file is now `bad_text` / `broken_tounicode`. The 717 unique pages need a GID
  decode table or vision OCR. `get_text` output was deleted.
- **59 files = "bad text" (Problem 1, PUA font-encoding)**: needs vision
  transcription (see below).
- **18 files = "image only" (Problem 2, no text layer)**: needs vision transcription
  too. Overlaps with, but is a slightly refined version of, the earlier 19-file count.
- **11 files = "unclear/mixed"**: sampled pages show Latin-range characters with
  ~zero Arabic or PUA. **An earlier reading of this bucket was wrong and nearly cost
  us real data** (see "Two encoding schemes" below): it assumed these were all
  English-language books. Direct inspection proved the bucket is actually two very
  different things:
  - **Genuinely English books, likely out of scope**: `the-gujjars-vol-1/3/4/5/6`
    (verified: Calibri font, plainly readable English prose about Gujjar history),
    `Islam-in-the-Modern-World.pdf`, `Revisiting-Islam.pdf`.
  - **Real Gojri content that was nearly discarded by mistake**:
    `gojri-kalam-israel-asar_-ed-dr-javaid-rahi.pdf` and
    `gojri-kalam-_gulam_sarwar_rana_ed-javaid-rahi.pdf` (verified: these use
    **NOORIN Nastaliq fonts**, i.e. they are Gojri poetry collections, "kalam" =
    poetry, whose text merely extracts as Latin-range garbage because of the second
    encoding scheme below). `MAHATMA_GANDHI_Tasweeran_Sangh_Kahani_by.pdf` and
    `Gojri-Hindi-English-Dictionary.pdf` are also in this bucket and need the same
    individual check rather than a bulk assumption.
  Lesson: bucket membership must be confirmed per file by looking at embedded font
  names, not inferred from character-range statistics alone.

### Two distinct legacy encoding schemes (Aug 2026): not one problem, two
An important refinement to the "font-encoding problem" framing. The broken PDFs do
not all use the same broken encoding. Verified by inspecting embedded fonts and raw
extracted codepoints:
1. **PUA scheme**: glyphs mapped into the Unicode Private Use Area (`U+F0xx`), e.g.
   `Gojri-English-Dictionary.pdf` (Batool font), `Gojri-Ghazal.pdf`,
   `Kahawat-Kosh.pdf` (NOORIN* fonts). Extracted text looks like ``.
2. **ASCII/8-bit legacy scheme**: glyphs mapped into the ordinary Latin/ASCII range,
   e.g. `Gojri_lok_kahani.pdf`, `javaidrahi-blog/gojri-history.pdf`, and the two
   `gojri-kalam-*` poetry collections above. Extracted text looks like
   `c r # g S Z q` or `~ # Q # ֻzZ`, i.e. meaningless Latin letters and punctuation.
Notably the **same NOORIN font family appears under both schemes** in different
files, so the scheme is a property of how each PDF was exported, not of the font.
Consequences:
- Any character-range-based classifier that counts only PUA will systematically
  misjudge scheme-2 files (this is exactly what happened above).
- A decode-table approach would need a separate table per (font, scheme), not one
  universal table.
- The vision-transcription approach is unaffected: it reads the rendered page image,
  so it handles both schemes identically without caring which is which. This is a
  point in favor of vision transcription as the safe default.

### Duplicate PDFs: verified by file hash (Aug 2026), corrects an earlier undercount
Ran MD5 hashing across all 92 files (byte-for-byte comparison, not just filename
pattern-matching, since filename matching alone had already been shown to miss
things). Found **7 exact-duplicate groups**, two of which were not previously known
about at all:
| Duplicated content | Copies | Pages each | Pages wasted |
|---|---|---|---|
| `GOJRI_DICTIONARY_by_Dr_JAVAID_RAHI_Part (2).pdf` / `gojri-dictionary-by-dr-javaid-rahi-1-281-1.pdf` (both locations) | **3x** | 281 | 562 |
| `GOJRI_LOK_KAHANI_by_Dr_Javaid_Rahi_A_col.pdf` / `Gojri_lok_kahani.pdf` | 2x | 410 | 410 |
| `QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf` / `javaidrahi-blog/gojri-quran-final-1010-1.pdf` | 2x | 717 | 717 |
| `gojri-dictionary-by-dr-javaid-rahi-3.pdf` (both locations) | 2x | 169 | 169 |
| `javaidrahi-blog/gojri-history.pdf` / `javaidrahi-blog/gojri-history1.pdf` | 2x | 275 | 275 |
| `gojri-dictionary-by-dr-javaid-rahi-part-05.pdf` (both locations) | 2x | 110 | 110 |
| `gojri-dictionary-by-dr-javaid-rahi-01.pdf` (both locations) | 2x | 1 | 1 |

Total: **2,244 duplicate pages** that should not be paid for or double-counted.
Caveat: MD5 hashing only catches byte-identical files. A re-scanned or re-exported
copy of the same book with even one different byte would not be caught by this
method and could still be sitting in the collection undetected; this is a "no exact
duplicates missed" guarantee, not a "no duplicate content at all" guarantee.

### Precise page counts by category (Aug 2026, corrects the earlier rough ~18,000 estimate)
The earlier "~18,000 total pages" figure was an undercount, it excluded the 11
"unclear" files' pages entirely and used a rougher method. Recomputed properly:

| Category | Pages (before dedup) | Pages (after removing exact dupes) |
|---|---|---|
| Good text already (4 files) | 1,951 | 1,234 |
| Bad text / PUA font issue (59 files) | 14,795 | 13,269 |
| Image only (18 files) | 1,282 | 1,281 |
| Unclear / probably not Gojri (11 files) | 5,359 | 5,359 (no dupes found in this bucket) |
| **Total (all 92 files)** | **23,387** | **21,143** |

**The number that actually drives cost is pages needing paid vision transcription**
(bad-text + image-only, deduped, excluding "good text" which needs no OCR and
"unclear" which is pending a relevance decision): **14,550 pages.** This is the real
number Stage 1's cost estimate should be built on.

### OCR pipeline plan (historical, Aug 2026; superseded, see Status)
1. "Good text already" files: extract directly (e.g. PyMuPDF `get_text`), light
   cleanup only, no OCR/vision needed. **Do not include the Quran translation.**
   Its ToUnicode CMap is broken (`broken_tounicode`). Direct extract is garbage.
2. "Bad text" and "image only" files (77 files, 14,550 pages after dedup, the real
   workload): render each page to a PNG (already proven with PyMuPDF, e.g. 3x zoom
   matrix), then send the image to a vision-capable LLM with a transcription-only
   prompt (transcribe exactly what's on the page, preserve line breaks, don't
   translate, flag uncertain words).
3. "Unclear" files (5,359 pages): manual relevance check first, decide in/out before
   spending transcription budget on them, this alone is a meaningful chunk of pages
   to potentially exclude entirely.
4. **Cost math, corrected twice, now based on measured values** (supersedes both the
   earlier "~tens of dollars" and the "~$44 Haiku / ~$175 Sonnet" figures, **both of
   which were wrong because they counted only input tokens and ignored output tokens
entirely: for OCR the output is a full page of transcribed text, and output
tokens bill at ~5x the input rate, so omitting them understated cost by ~2x):
   - Measured, not assumed: a rendered page at zoom 2 is ~1211x1568 px, which after
     Claude's automatic downscaling is **~2,530 image tokens per page**.
   - **Free optimization found: rendering at zoom 3 is wasted money.** Both zoom 2 and
     zoom 3 downscale to the identical ~1211x1568, so zoom 3 costs the same tokens
     while producing a larger intermediate file. Render at zoom 2.
   - Output: a dense Nastaliq page is very roughly ~1,000-1,500 tokens (Perso-Arabic
     script tokenizes inefficiently). Assume ~1,200.
   - Resulting estimate across the 14,550-page workload:
     **Haiku ≈ $100, Sonnet ≈ $377.**
   - This changes the strategic picture materially: Haiku now consumes ~2/3 of the
     entire $150 credit, and Sonnet-for-everything is simply unaffordable. Cost
     control is therefore a first-class design constraint, not a footnote, and the
     decode-table spike below is worth real effort before committing spend.
   - These are still estimates on the output-token side. The Stage 1 test batch must
     capture **actual** billed input/output tokens per page and revise again.
5. **Important correction**: the successful 2-page test transcription was done using
   this conversation's own vision reading (a larger, Sonnet-class model), not a
   verified test of Haiku specifically. Haiku's actual quality on Nastaliq is
   currently untested. Before committing to a model for the bulk run, the Stage 1
   test batch must directly A/B compare Haiku vs Sonnet output on the same pages
   (and optionally Tesseract, see below, as a free zero-cost baseline) so the
   cost/quality tradeoff is based on evidence, not assumption.
   - **Resolved (Aug 2026, Stage 1 test batch)**: Haiku 4.5 tested directly via AWS
     Bedrock on 2 real gold-set pages (`dict_alif`, `gojri_adbiyaat`), controlled
settings (temperature=0, explicit max_tokens, no thinking, logged in
`data/gold/ocr_runs_log.csv`). **Quality is not usable**: on `dict_alif`
(dense dictionary layout) it substitutes a placeholder character in place of
headwords it can't read, inconsistently (`ئ` in one run, `Ī`, not even a
valid character in this script, in a rerun of the same page); on
`gojri_adbiyaat` (poetry) whole phrases are wrong, not just diacritics, e.g.
`وِچ چھوڑا کے عمر گزری، دتو تیں نہ کدے دیدار مِناں` (correct) came back as
`ویچ ویڑھو کے عم گردی، ڑو تھیں یک کے دھار دھیال` (most words differ, not a
near-miss). **Qwen3-VL** (a candidate cheap alternative, not in the original
Haiku/Sonnet plan) was tested alongside and also failed, differently: mostly
correct structure but frequent character-order corruption and word swaps
(`الف` read as `فلف`). **Both ruled out for this project.** The one variable
controlled for and eliminated as the cause: Gemini 3.6 Flash, given the exact
same cropped images and prompt, transcribed both pages correctly, so this is
a real capability gap on small/dense Nastaliq text for these two specific
models, not a settings or input-quality issue. Full outputs kept for the
record in `data/gold/transcriptions_archived/`. Sonnet 5 access turned out to
be blocked behind an AWS Sales-gated request (full self-service agreement flow
completed successfully, invocation still denied, a genuine Sales-only gate,
not a missed step; a request is in with AWS Sales, response pending). **Sonnet
4.6 is standing in as the active Claude candidate** until that clears, tested
against Gemini's and Kimi K2.5's cost/quality bar on both gold pages, per
`LOG.md`.
6. **Tesseract (traditional OCR) considered as an alternative/baseline**: free and
   runs locally, but is a pattern-matching engine with no language understanding, it
   cannot use surrounding context to resolve ambiguous cursive strokes the way a
   vision LLM can, and even purpose-built modern Urdu OCR research models (UTRNet)
   report Nastaliq as their weakest case, Tesseract (older, more generic) would
   likely do worse still. Realistic role: a free, deterministic baseline to compare
   against in the test batch, not the primary strategy.
7. **Hallucination risk specific to vision-LLM OCR** (does not apply to Tesseract):
   an LLM can produce a fluent, plausible-looking word that isn't actually what's on
   the page, since it's completing patterns rather than only matching shapes.
   Tesseract fails visibly (garbled/blank) when unsure; an LLM can fail silently and
   confidently. This is exactly why step 8 (human spot-checking) isn't optional.
8. The 12-page gold set is now that independent ground truth for scoring. It is
   not a substitute for checking bulk output. Vision-LLM OCR can still fail
   silently, so bulk vision transcription stays paused until a method (decode
   table, or a much better model) beats gold without needing a person on every
   page.

### The decode-table idea: highest-upside experiment, worth testing before bulk spend
**Premise**: the broken PDFs are not random noise, they are a *deterministic
substitution cipher*. Each (font, codepoint) pair always renders as the same Nastaliq
ligature. If we can recover that mapping, we can decode pages for free, instantly,
and with zero hallucination risk, instead of paying per page forever.

**Feasibility evidence gathered (Aug 2026), encouraging but not conclusive:**
- Glyph census over 4 font-encoded books (40 pages each): **2,022 unique (font,
  codepoint) pairs** total, and the distribution is steeply concentrated. The **top
  432 glyphs cover 90%** of all glyph instances; the top 1,587 cover 99%. A table of
  low thousands of entries is very tractable.
- Font-encoded pages carry ~540 glyphs/page, so vision-transcribing even ~30-50 pages
  yields tens of thousands of glyph instances to align against.
- No ready-made public mapping table for these specific NOORIN/Batool fonts was
  found in searching, so this would mean building one, not downloading one.

**How it would work**: extract the (font, codepoint) sequence from font-encoded
pages, align it against known Unicode (the gold pages first, then any later
trusted text), and learn the mapping. Then apply the table to remaining pages
at zero marginal cost. Kashmiri InPage-to-Unicode work (KS-LIT-3M / KS-PRET-5M)
is the closest public neighbour: mapping table first, not vision per page.

The original sketch used extra vision-transcribed pages as the parallel text.
Gold pages already give a small, trusted parallel. That is the first alignment
set to try.

**Honest risks, this is a research bet not a sure thing:**
- Alignment is the hard part: right-to-left text, one glyph mapping to a *sequence*
  of Unicode characters (these are ligatures, not letters), and uncertain word/space
  boundaries.
- Requires a separate table per (font, scheme), and we confirmed at least two schemes
  exist, so it is several tables, not one.
- Rare glyphs in the long tail may never get enough examples to learn confidently,
  so a hybrid (decode what's confident, vision-transcribe pages with too many unknown
  glyphs) is the realistic end state.
- Does nothing for the 1,281 genuinely image-only pages, which still need vision.

**Why it is still worth a timeboxed spike**: if it works even partially, it converts
the largest cost bucket (13,269 font-encoded pages) from ~$90 of billed, hallucination-
prone output into free, deterministic, verifiable output, and leaves the AWS credit
available for the rest of the project. If it fails, we lose a day and fall back to
vision transcription, which is already validated. Asymmetric payoff, so test it
before committing bulk spend, not after.

**Outcome (Aug 2026): NOORIN spike failed validation and is abandoned.** We built
a 2,149-key table on Kahawat-Kosh with 100% census key coverage, but decoded text
was wrong: page 28 **98.8% word error** vs OCR ground truth, page 59 gold **98.9%**
word error. Key coverage does not mean correct Unicode. All NOORIN scripts, seeds,
and decode output were removed. Summary: `data/archive/noorin-decode-spike/README.md`.
**Corpus path for font-encoded PDFs is vision OCR**, not glyph decode. Batool and
Quran GID decode remain in the repo but are paused and not validated at book scale.

### ASR (speech recognition)
- Fine-tuning OpenAI Whisper is the standard low-resource approach. Literature
  (BaltiVoice and others) suggests roughly 15-20 hours of labeled audio gives a usable,
  if imperfect, fine-tuned model; we have 10.68 hours validated for Gojri locally
  (see `datasets/cv-corpus-26.0-2026-06-12/gju/` above), close to but under that range, so
  more contributed recordings would meaningfully help.
  More Gojri voice data can be added directly through Mozilla Common Voice's normal
  contribution flow (record/validate sentences in the app), which feeds back into
  future Mozilla Data Collective releases.
- LoRA/adapter fine-tuning and "support language" transfer (borrowing strength from a
  related higher-resource language, e.g. Urdu/Punjabi/Hindi) are proven techniques to
  get more out of small datasets.
- AWS Transcribe does not appear to support Urdu or Gojri as a built-in ASR language,
  so the practical path is self-managed fine-tuning (e.g. via SageMaker or any GPU
  box), not an AWS managed ASR product.
- **YouTube audio considered as an additional source (Aug 2026, user suggestion)**:
  there's likely a meaningful amount of spoken Gojri content on YouTube. Important
  distinction from the Common Voice data: YouTube audio comes with no transcript
  (YouTube's auto-captions don't support Gojri and would likely mis-transcribe it as
  Urdu-ish text if attempted), so it's *unlabeled* audio, not directly usable as
  Whisper fine-tuning pairs the way Common Voice data is. Realistic uses:
  (a) self-supervised/unlabeled pretraining to help a model learn Gojri's general
  sound patterns before fine-tuning on the smaller labeled set, a standard low-resource
  speech technique, or (b) a future pseudo-labeling loop (use an already fine-tuned
  model to auto-transcribe it, human corrects/filters). Also needs real curation
  (background music, cross-talk, multiple speakers common on YouTube vs. Common
  Voice's clean single-speaker scripted reads) and a licensing check before any
  public use, since YouTube content isn't contributed under CC0 the way Common Voice
  is. Treated as a Stage 2 enhancement to plan for, not a Stage 0 priority.

### LLM / translation
- No foundation model has real Gojri knowledge; it's not in NLLB-200's language list
  and not meaningfully present in LLM pretraining data.
- Because Gojri shares script and a lot of vocabulary with Urdu, and grammar overlap
  with Punjabi/Hindi/Rajasthani, the realistic path is transfer learning from an
  Urdu-capable base model (e.g. open Urdu LLMs like Alif or UrduLLaMA, or
  multilingual models like NLLB/XLM-R), fine-tuned/adapted on Gojri data with LoRA,
  rather than training from scratch.
- Current text corpus (~60K tokens) is far too small for pretraining, but is useful
  as: a bilingual glossary/parallel-data seed, an evaluation set, or seed data for
  synthetic data generation (using a strong LLM to draft Gojri-Urdu pairs, which the
  user then verifies/corrects as a native speaker, human-in-the-loop).
- AWS Bedrock fine-tuning is billed per training token plus a provisioned-throughput
  hosting cost (~$24/hr on-demand equivalent), which is expensive for a $150 budget.
  Free-tier compute (Colab/Kaggle GPUs) or SageMaker spot instances are likely better
  for experimentation; AWS credit is probably better spent on storage/hosting/light
  inference than on training runs.

## Stage 0 execution log (Aug 2026)

`scripts/build_manifest.py` builds `data/manifest.csv`, one row per PDF with hash,
duplicate group, category, encoding scheme, script found, scope, and tier. Re-run it
any time; it's read-only against the PDF collection.

**It caught real errors on the first run, which is exactly why Step 0.1 (build a
verifiable manifest) came before any bulk processing:**
- Initial classification, which only counted PUA characters, misjudged the 11
  "unclear" files as mostly English. Rebuilding classification around "what script
  is actually in the text" instead of "does English appear" found:
  - **A third legacy encoding scheme** (`legacy_8bit`): fonts with obfuscated subset
    names like `TT230t00` that carry no hint of the script. Verified visually by
    rendering a page: `kulyate_rana_fazal_hussan_ed-dr-javaid-rah.pdf` (494 pages) is
    genuine Gojri Nastaliq poetry that would have been silently dropped. 6 files,
    ~1,290 pages total rescued this way (the two `gojri-kalam-*` files plus
    `gojri-_kuliyat-e-qasam_shamim`, `guldasta_kalami_sheikh_ul_aalam`,
    `kulyate_rana_fazal_hussan`, `MAHATMA_GANDHI_Tasweeran_Sangh_Kahani_by`).
  - **`Gojri-Hindi-English-Dictionary.pdf` (458 pages) is in Devanagari, not
    English**, verified visually: real Gojri headwords in Devanagari with English
    and Hindi glosses. This was nearly excluded entirely; it is arguably the single
    most valuable document in the collection (a three-way aligned dictionary).
    Devanagari needed its own detection range (U+0900-097F), it isn't Arabic-block
    and isn't PUA, so the original classifier had no bucket for it at all.
  - Genuinely out of scope, confirmed: `Islam-in-the-Modern-World.pdf`,
    `Revisiting-Islam.pdf`, and the five `the-gujjars-vol-*` history volumes (real
    English prose, verified by font: plain Calibri/Arial, not Nastaliq).
- **New structural finding, not previously known**: 25 unique files (5,885 pages, 38% of
  the 15,478-page workload as counted before the Nov 2026 dedupe; now 21 files, 5,168 pages) are **two-page spreads**, a single PDF page containing both the
  left and right physical book pages side by side (page width notably exceeds
  height). Detected by checking rendered page aspect ratio. Concentrated entirely in
  `javaidrahi-blog/`. This matters for Stage 1: fed to a vision model unmodified,
  reading order would likely get scrambled (which column is "first" in a
  right-to-left book is not obvious from geometry alone). **Resolved**: build
  `scripts/split_spread.py`, splits at the exact geometric center. Verified safe
  (not just convenient) across 6 files x 3 pages each: center always lands in a
  contiguous white gutter, worst-case margin 61px on a ~1684px-wide page. Verified
  visually too: both halves keep their full decorative border, nothing clipped, and
  the right-half-first / left-half-second reading order was confirmed correct
  against the visible printed page number on the left half. Bonus: splitting also
  roughly doubles each half's effective resolution after the vision model's
  automatic downscaling, since the two pages no longer share one downscaled image.

**Final, verified numbers after fixing classification (reconciles exactly: 2,190 +
13,480 + 1,281 + 4,192 = 21,143, matching the independently-computed deduped total)**:
| Category | Files | Pages |
|---|---|---|
| Good text already (incl. 1 Devanagari dictionary) | 5 | 2,190 |
| Bad text (needs vision transcription) | 55 | 13,480 |
| Image only (needs vision transcription) | 17 | 1,281 |
| Genuinely out of scope (English prose) | 7 | 4,192 |
| **Pages needing paid OCR** | | **14,761** |
| Of which: two-page-spread layout (needs special handling) | 26 files (Aug count) | 6,295 |
| Tier 1 (dictionaries/glossaries, highest value) | 15 | 3,310 |

This revises the OCR cost estimate up slightly again (14,761 vs the earlier 14,550),
immaterial at this scale, but the tier-1 page count grew meaningfully (3,310 vs the
earlier rough sense of it) now that the Devanagari dictionary and rescued poetry
collections are correctly counted.

**Correction (Aug 2026):** the 717-page Quran translation is `broken_tounicode`,
not good text. Unique good-text pages are now **1,473** (4 files). Unique pages
that still need decode or OCR are **15,478**.

**Duplicates removed (2026-11-20).** Hashing misses re-exported copies, so every page of every PDF was compared
by image (thumbnail correlation, then a page-by-page check at higher resolution, plus the text layer where one
exists). 18 files were deleted from `pdfs/`: the 8 byte-identical copies and 10 content duplicates (same pages in
another file). Their manifest rows stay, flagged `removed_duplicate_nov2026` with `is_primary=0` and a `dup_group`
(D01 to D14) that names the kept copy. Current figures: 64 PDFs on disk; 3,662 duplicate pages; 19,725 unique
pages; **14,060** pages need decode or OCR (bad text 12,907, image-only 1,153); spreads 21 files, 5,168 pages; Tier 1
12 files, 3,007 pages. Kept on purpose: three primer pairs are two editions of the same J&K board book (`gojri-books-iind` / `GUJJARS_GOJRI_KI_DOJI_KITAB`, `gojri-book-iiird` / `..._TEJI_KITAB`, `gojri-book-ivth` / `..._CHOTHI_KITAB`; 53 of 64, 23 of 33 and 24 of 33 pages identical); `Gojri-Adbiyaat.pdf` holds about 73% of the pages of `gojri-adab-ki-tariekh.pdf`, and 82 pages of `Gojri-Sheryaat.pdf`. The two Louk Warsti files share no page: they are Vol 1 (ا to س) and Vol 2 (ش to ی) of Javaid Rahi's
*Gujjar Qabila Ki Louk Warsti Dictionary*, now named `Gujjar_Qabila_Ki_Louk_Warsti_Dictionary_Vol1.pdf` and `..._Vol2.pdf`. The manifest now holds hand-set flags (September and November removals):
do not rebuild it blindly with `scripts/build_manifest.py`.

## Status
Newest first. The dated history is in `docs/TIMELINE.md`; the plan is in `ROADMAP.md`.

**Second pass (2026-11-20, later).** Code license is PolyForm Noncommercial 1.0.0 and project data CC BY-NC 4.0: the
project is non-commercial. Every public document carries an accuracy and AI-use notice (README "About this
project", `CONTRIBUTING.md`, the four Hugging Face cards). The dictionary source is the *Concise Gojri-English
Dictionary* by Dr. M. R. Anjum Awan; the card had wrongly named Dr. Javaid Rahi. UTRNet's license: its LICENSE file
says CC BY-NC 4.0, its README CC BY-NC-SA 4.0. Machine OCR text of four books is in `data/ocr-output/` for speaker
review (`scripts/ocr_eval/export_ocr_output.py`). Gojri-Ghazal was read in full (`data/ocr/ghazal-full/`, local).
The locked test set (`data/test-locked/`) has 20 drafts waiting for the speaker. ASR baseline (`scripts/asr/`):
Whisper-small fine-tuned on 9,041 Common Voice clips (3 speakers), 22.7% word error on the official test set
(73.8% zero-shot; 21.6% for unseen speakers); best dev checkpoint at step 1,500 of 2,500.

**Repository audit (2026-11-20).** The speaker's review labels are tracked in `data/reviews/` (README there); the
scripts read them from there, and `labels_review_test.jsonl` there holds one later hand fix (`page-0125:L26`).
Third-party datasets (FLI corpus, Common Voice) are no longer tracked. Code is PolyForm Noncommercial 1.0.0 (`LICENSE`; MIT for a few hours on 2026-11-20); project data is CC BY-NC 4.0;
terms in `DATA-NOTICE.md`. Nothing may be used commercially. Index of all scripts: `scripts/README.md`. Scorers now count ݨ (U+0768, Arabic Supplement) as an
Arabic letter. UTRNet keeps its temporal dropout on at inference, so `scripts/utrnet_arabic_eval.py` takes `--seed`
(default 0), and `ocrlib.UTRNet` resets the seed before every read; report UTRNet numbers with the seed. 18 duplicate PDFs (8 byte-identical, 10 same
book in another file) were deleted from `pdfs/` after a page-image comparison; the workload is now 14,060 pages.

**Book OCR, PDF marks and word spacing (2026-11-10 to 2026-11-19).**
- PDF mark glyphs: the NOORIN books draw pesh, zer, zabar, ulta pesh, the takhallus sign and the small "v" as their
  own glyphs. Table `data/decode/noori_marks_seed.json` (24 glyphs, keyed by outline hash); code and method
  `scripts/ocr_eval/pdf_marks/`. Each mark goes to the nearest UTRNet letter. On 30 Kahawat-Kosh cards mark error
  fell from 67% to 14%. The glyphs appear in about 30 books of the collection.
- Full local runs (gitignored `data/ocr/`): Kahawat-Kosh (169 pages, `kahawat-pdfmarks-v2`), Banjara and Dil-Darya
  (716 pages, `prose-aws-full2`). On the 10 reviewed prose pages (`data/reviews/prose-banjara-dildarya/`): letters
  0.8%, marks 12.0%.
- Speaker rulings: ݨ over ن and ڵ over ل where the print shows the small "v"; a space after ۔ and ،; word spaces
  follow meaning, not the print.
- Spacing review (2026-11-21): 200 Kahawat-Kosh cards written as words by the speaker, in `data/reviews/kahawat-spacing/`.
  The OCR text misses 232 of 759 spaces (205 after a non-joining letter); `space_fix.py` adds 101 spaces at margin 4,
  86 right. Score with `scripts/ocr_eval/score_spacing.py`. Split review (`data/reviews/prose-word-splits/`, 66 cards
  from Banjara and Dil-Darya): 66 of 72 proposed spaces right, 6 cut a word; `score_splits.py`. `space_fix.py` now
  never cuts a piece shorter than 2 letters (`MIN_PIECE`).
- Word spacing is not solved: the PDF text layer has no space glyphs, and gaps in tight prose are as narrow inside
  words as between them. `scripts/ocr_eval/space_fix.py` adds more wrong spaces than right ones. First decide one
  labelling rule for the review truth (some reviewed rows keep glued words).
- A UTRNet output-layer fine-tune for marks helped on the dictionary print only; the PDF mark method replaced it.
  Kraken is behind UTRNet.

**OCR model search done (2026-11-06).** Details: `scripts/ocr_eval/README.md`. UTRNet-Large is the Gojri Nastaliq reader
(2.1% letter error on dictionary Arabic runs, 2.0% to 2.2% over five seeds; its dropout is random at inference). Qaari-0.1 and three Hugging Face TrOCR Urdu models fail and are ruled out.
`cxfajar197/urdu-ocr` is gated (the user must request access) and untested. Tesseract 5.5 (installed at
`C:\Program Files\Tesseract-OCR`) reads English at 0.1% character error. Page pipeline `scripts/ocr_eval/ocr_page.py`
(SegNet per-column script labels, page-mode switch, UTRNet for Arabic, Tesseract for English): 3.7% pooled Arabic-letter
error on the 12 gold pages, 2.9% against Gemini 3.3% on the 8 pages Gemini was scored on (rescored
2026-11-20 on the corrected Ghazal gold; the seeded run `pipe_v5` gives the same 3.7%, 229 of 6,253, repeatable). A development number: the
gold pages guided the design, only one is a dictionary page, SegNet knows one dictionary's layout. UTRNet code and
weights live outside the repo (`D:\ocr-tools`; non-commercial: CC BY-NC 4.0 in its LICENSE file, CC BY-NC-SA 4.0 in its README); SegNet weights are on S3
(`ocr-eval/models/segnet_v2.pt`). SageMaker GPU runs: one `ml.g5.xlarge` at a time; the role ARN comes from the
environment variable `SAGEMAKER_ROLE_ARN` and never goes into the repo.

Stage 0 done (Aug 2026). Manifest is built. Gold-set Step 0.3 is done for
the working set of 12 vision-OCR pages (one `_gold.txt` each, first six
re-checked 2026-08-15). Score with `py -3 scripts/score_gold.py`. One-shot
bake-off: Gemini 3.6 Flash 17.8% pooled word error, Sonnet 4.6 22.6% (after the gold fixes of Nov 2026). Composer
chat is lower error but is not a bulk pipeline. Dual-model agreement still
shares a wrong word on about 5% of agreed tokens. **Bulk vision OCR is paused:**
the user cannot review 14,060 pages, and 17% word error would poison the corpus.

**NOORIN decode-table path abandoned (Aug 2026).** See
`data/archive/noorin-decode-spike/README.md`. Do not rebuild NOORIN tables.

**NOORIN component font test re-closed (Oct 2026).** One fair test was run on
`Kahawat-Kosh.pdf` before the speech work. Findings: the NOORIN fonts are
component fonts, so the unit is the cluster (all pieces at one origin), not the
glyph. The column divider is x = 215, not the page centre; earlier line data was
a 50 point slice and is void. Nineteen pages of vision drafts were made
(`data/decode/out/kahawat-kosh/vision/`, raw, about 85 to 90 percent correct,
not truth). Every learning model failed to recover the cluster table from text
alone: hard EM locks the first cut, soft EM spreads, the word level table has no
cross page reuse, and the pen advance is not proportional to characters. Held
out word error is 79 to 100 percent against a 5 percent target. The kill
condition is met and the path is closed. Only a shape image labelling route
(hand labels on rendered clusters, then EM) could reopen it. Journal:
`LOG.md`, 2026-10-24.

**NOORIN line-wise OCR works; word spacing is the open gap (Oct 2026).** The
user proposed a third route: cut the right column into one image row per printed
line, number each row, then run OCR. The sheet goes to Gemini in one call. Every
row returns in order, so the model cannot merge or drop a line. Measured on page
50 against the 20 gold lines: character error 0.9 percent, word error 17.5
percent, 12 of 20 lines exact. The word errors are almost all spaces. A repair
pass with the dictionary word list made the score worse, because that list is
Urdu heavy and holds Urdu words that split Gojri words. A second model pass that
restores only spaces reached 13.4 percent word error, but it changed letters on
two lines. Printed letter gaps measure 3 to 4 px and word spaces 5 to 12 px, so
geometry cannot split words either. The print itself has wide gaps inside some
words. A Gojri word model or a human check of spacing is the remaining work.
Prototype: `linesheet_ocr.py` in the temp work folder. Sheet:
`data/decode/out/kahawat-kosh/linesheet_img/`.

**Batool decode + Pass 2 Gemini + Full Audit (Oct 2026):** PUA table in
`data/decode/batool_pua_seed.json` (160 codes) for
`Gojri-English-Dictionary.pdf` (498 pages). Body pages 25-498: zero
unknown Batool codes on census. Front 1-24 mostly English; 3 unmapped
codes. `Concise_Gojri_English_Dictionary_by_Dr_R.pdf` is the same front
matter. **Gold score (page 25 / dict_alif):** full-token WER 9.2%
(Latin spacing / `lpp`↔`Ipp`); Arabic-token WER **0%**.
**Two-pass pipeline built and executed across full book:** Multimodal Pass 2
(Gemini Flash with Gojri orthographic rules: `-و` endings, correct heh forms,
fixed `Ipp:`, headword-gloss spacing) completed for **all 474 body pages**
(pages 25-498) under `data/decode/out/gojri-english-dictionary/page-*-pass2.txt`.
**Image-vs-Text Audit completed across all 474 pages:** Every page audited and
documented in `data/decode/out/gojri-english-dictionary/audit/page-*-audit.txt`.
Total entries: 11,767 dictionary lines across 474 pages.

**Synthetic OCR data opened (Nov 2026).** Decoded Gojri Unicode text renders
into Nastaliq line images as OCR training data: headless Chrome drawing with
Noto Nastaliq Urdu, device scale 2 (HD), and for each row one clean image plus
3 degraded copies from an approved 15-type scan-damage mix. Output stays
gitignored under `data/synth/`. Full set `data/synth/line_full/`: 20,932
rows (13,704 dictionary pass2 lines + 7,228 FLI story lines), 2.0 GB,
health-checked. The 7,683-row pilot set was deleted in Nov 2026. Real-print
pairs from the dictionary PDF land in `data/synth/real_pairs/`: tight
per-line crops at about 300 DPI, pairing by row-count
equality with a conditional folio-drop rule. Mined complete (Nov 2026): 11,524
pairs from 465 of 474 pages, folio crops flagged `folio: true` and excluded
from training, descender tails fixed with a 14 pt bottom pad. A compact CRNN-CTC
line model was trained on them (CPU, then SageMaker); it was ruled out (see below).

**Real-print labels rebuilt (Nov 2026).** The pass2 labels were wrong against
the print. The user reviewed 200 random lines and all 160 table codes: 91% of
lines had an error, mostly spaces around the `(romanisation)` group, then
heh, kaf and a few wrong glyph codes. The fix has three parts.
- **Table v3.1** (`data/decode/batool_pua_seed.json`): 22 codes corrected by the
  user's rulings. F060 and F061 are always ھ. F0D4 and F0D5 are ك. F0A1 is the
  joined لا shape, F0CD is ف, and F0F1+F031 is ئے with no extra alef.
- **Merge** (`scripts/synth/merge_decode_letters.py`): takes the decode spelling
  for each word that differs from pass2, and the decode gap for the spaces
  around `(` and `)`. On the 200 reviewed lines, 316 of 333 Arabic words equal
  the user's fix (pass2: 281). Paren spacing matches on 160 of 178 lines (pass2: 7).
  All remaining misses are old review fixes that the user has since overruled,
  or lines where the word counts differ.
- **Clean step** (`scripts/synth/make_clean_labels.py`): writes
  `real_pairs/labels_merged_clean.jsonl` (11,126 rows) for training. The 200
  reviewed lines stay out of training, in both the real and the synthetic rows,
  and are kept in `data/reviews/dictionary-200-lines/labels_review_test.jsonl`
  (tracked) with the user's fix as the test truth. Some of those fixes are stale (ہ where the print shows ھ), so
  reconcile them before scoring.
The synthetic dictionary rows in `line_full` still show the pass2 spelling and
the spaces around the `(romanisation)` group. They match their own images but
not the print. The S3 bucket `gojri-ai-sagemaker-data` holds the new labels under
`train/`; the old ones are under `before_v3/`. The retrain on them (job
`gojri-crnn-2026-11-05-16-02-39-998`) gave no gain. On the 200 reviewed lines the
model reads Latin text with 0.4% error but Arabic-script letters with 33.4% error (78% on
long Nastaliq sentences), for the old and the new model alike. It is not usable for Gojri text.
Whole-line CER (4.8%) hides this because English is 87% of the characters, so report
Arabic-letter error. **UTRNet-Large, zero-shot, reads the Arabic runs of the same 200 lines at 2.1%
error** (seed 0: 29 letters, 179 lines exact; 2.0% to 2.2% over seeds 0 to 4; 10.9% with a 6 px margin that caught a "("). It needs only the CPU. On the
English parts of the same lines it makes 86% errors, so it needs an Arabic/English split first. The
cut-out runs came from PDF glyph boxes, so reading scanned pages still needs a line and script
detector. Method, tables, error list and example crops: `data/utrnet-test/README.md`; code:
`scripts/utrnet_arabic_eval.py`, `scripts/utrnet_latin_eval.py`. The 12 gold-page run followed on 2026-11-06
(see the OCR model search paragraph).

**Hugging Face Dataset Published (Oct 2026):**
`https://huggingface.co/datasets/junaidaslam/gojri-english-dictionary`.
Complete digitized text corpus (CSV, JSONL, per-page TXT). The source is the *Concise Gojri-English Dictionary* by
Dr. M. R. Anjum Awan (title pages); the card wrongly named Dr. Javaid Rahi until the correction of 2026-11-20.
**Version 2 published 2026-11-05** (commit `889730b`): text rebuilt from the
corrected font table, 10,228 of 11,767 lines changed on 465 pages; the README has
a "Version 2" section with the numbers and known limits. Version 1 stays in the
repo history. Rebuild with `py -3 -X utf8 scripts/build_dictionary_release.py`
(writes `data/release/`, gitignored), then push the folder in one commit.

The Quran GID table is `data/decode/quran_gid_seed.json` (570 keys).
Key is `FONT:GID` from `get_texttrace`. Zero-width Arabic letters
are nuqta overlays; the decoder names the next host glyph.
Do not copy this table onto Batool or NOORIN. Decode with
`py -3 scripts/decode_quran.py 1 717`. Output is
`data/decode/out/quranic-translation-gojri/` (gitignored).
Book census pages 1-717: 976 unique keep keys, 84.5% of table
instances, plus nuqta GIDs that are not stored as letters.
Page 16 Gojri lines 1-3 and 6-7 now follow the user screenshot
gold (`جہڑو`, `مہربان`, `واسطے`, `پالنہار`, `رستو`). Verses 4-5
still mix in one cluster. Arabic ayahs still have placeholders.
`rawdict` crashes on this PDF. Do not use `get_text`.
`AGENTS.md` is the Cursor agent brief; it points at this file for project
facts.
Direct-extraction pages were removed from the gold image folders. **Step 0.4
run (Sep 2026):** `py -3 scripts/extract_clean_text.py` wrote
`data/extracted/` (gitignored) and `provenance.jsonl`: the
Devanagari `Gojri-Hindi-English-Dictionary.pdf` (458 pages). Several English
`good_text` / history PDFs were removed from scope by the user (Sep 2026);
see `data/manifest.csv` error notes. FLI literature texts stay only under
`datasets/Gojri Language Corpus/` (not duplicated under `data/extracted/`).

**Devanagari → Gojri Nastaliq lexicon (Sep 2026):** tracked deliverable in
`data/lexicon/`: `gojri_lexicon_final.tsv` (1,862 headwords) plus
`gojri_lexicon_human_verified.tsv` (50 speaker-checked rows). Dataset card and
Hugging Face upload steps: `data/lexicon/README.md`, `data/lexicon/PUBLISH.md`.
Published: `https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon`.
Pipeline: `scripts/dict_translit_*.py`, `prompts/devanagari_to_gojri_nastaliq_v1.txt`.
The source PDF has no Nastaliq text; the Nastaliq column is machine-made (Aksharamukha rules,
Gemini, 50 human-checked rows). Nov 2026: the user ruled that a word-initial heh is ھ, as the
Gojri print writes it (448 of 475 initial heh forms in the dictionary text), so
`scripts/lexicon_initial_heh.py` changed 112 words in 98 rows of `gojri_lexicon_final.tsv`.
Pushed 2026-11-05 as tag `v2.0` (commit `c21814b`); `v1.0` is the October text.

**OCR gold set published (Sep 2026):** cropped images, gold text, and bake-off
results (Gemini 3.6 Flash 17.1% pooled WER vs Sonnet 4.6 22.0%; Composer chat
12.6% as a non-API baseline). After the gold fixes of Nov 2026 (heh forms, Ghazal ڵ and ݨ): Gemini 17.8%,
Sonnet 22.6%, Composer 13.0%.
`https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold`.
See `data/gold/README.md` and `data/gold/bakeoff_results.csv`.

**PDF research mirror (Sep 2026):** in-scope print PDFs with per-file credits on
Hugging Face (`junaidaslam/gojri-print-pdf-collection`). Version `v2.0` (2026-11-20): 64 unique PDFs, 14,518
pages, after the content dedupe; `v1.0` is the 74-file original. See
`data/pdf-corpus/CREDITS.tsv` and `LICENSE.md`. Original book copyright remains
with authors/publishers.

**Local third-party datasets:** documented in `datasets/README.md` (FLI literature
via Mozilla Data Collective; Common Voice Gujari). Kept locally and gitignored
(untracked on 2026-11-20); never re-published.

**Project aim:** Gojri ASR and Gojri LLM (same spirit as Pashto Katib / Qehwa).

See `docs/TIMELINE.md`, `ROADMAP.md`, `data/gold/README.md`, and `LOG.md`.
