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

## Data already collected (in this repo)
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

### Garbled text when copy-pasting from PDFs — CONFIRMED with direct inspection
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

### PDF collection triage — refined into 4 buckets (Aug 2026 automated scan)
Ran a finer script across all 92 PDFs, counting Arabic-Unicode-block characters vs
Private-Use-Area (PUA) characters vs Latin characters in sampled pages of each file:
- **4 files = "good text already"**: correct Arabic-block Unicode, no fix needed,
  just extract and clean. Includes `QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf` and
  its duplicate `javaidrahi-blog/gojri-quran-final-1010-1.pdf` (717 pages each — a
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

### Two distinct legacy encoding schemes (Aug 2026) — not one problem, two
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

### Duplicate PDFs — verified by file hash (Aug 2026), corrects an earlier undercount
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

### OCR pipeline plan (validated on 2 sample pages so far, not yet run at scale)
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
   entirely** — for OCR the output is a full page of transcribed text, and output
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
     settings (temperature=0, explicit max_tokens, no thinking — logged in
     `data/gold/ocr_runs_log.csv`). **Quality is not usable**: on `dict_alif`
     (dense dictionary layout) it substitutes a placeholder character in place of
     headwords it can't read, inconsistently (`ئ` in one run, `Ī` — not even a
     valid character in this script — in a rerun of the same page); on
     `gojri_adbiyaat` (poetry) whole phrases are wrong, not just diacritics, e.g.
     `وِچ چھوڑا کے عمر گزری، دتو تیں نہ کدے دیدار مِناں` (correct) came back as
     `ویچ ویڑھو کے عم گردی، ڑو تھیں یک کے دھار دھیال` — most words differ, not a
     near-miss. **Qwen3-VL** (a candidate cheap alternative, not in the original
     Haiku/Sonnet plan) was tested alongside and also failed, differently: mostly
     correct structure but frequent character-order corruption and word swaps
     (`الف` read as `فلف`). **Both ruled out for this project.** The one variable
     controlled for and eliminated as the cause: Gemini 3.6 Flash, given the exact
     same cropped images and prompt, transcribed both pages correctly — so this is
     a real capability gap on small/dense Nastaliq text for these two specific
     models, not a settings or input-quality issue. Full outputs kept for the
     record in `data/gold/transcriptions_archived/`. Sonnet 5 access turned out to
     be blocked behind an AWS Sales-gated request (full self-service agreement flow
     completed successfully, invocation still denied — a genuine Sales-only gate,
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

### The decode-table idea — highest-upside experiment, worth testing before bulk spend
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
    English prose, verified by font — plain Calibri/Arial, not Nastaliq).
- **New structural finding, not previously known**: 26 files (6,295 pages, ~43% of
  the OCR workload) are **two-page spreads**, a single PDF page containing both the
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
| Of which: two-page-spread layout (needs special handling) | 26 files | 6,295 |
| Tier 1 (dictionaries/glossaries, highest value) | 15 | 3,310 |

This revises the OCR cost estimate up slightly again (14,761 vs the earlier 14,550),
immaterial at this scale, but the tier-1 page count grew meaningfully (3,310 vs the
earlier rough sense of it) now that the Devanagari dictionary and rescued poetry
collections are correctly counted.

**Correction (Aug 2026):** the 717-page Quran translation is `broken_tounicode`,
not good text. Unique good-text pages are now **1,473** (4 files). Unique pages
that still need decode or OCR are **15,478**.

## Status
Stage 0 in progress (Aug 2026). Manifest is built. Gold-set Step 0.3 is done for
the working set of 12 vision-OCR pages (one `_gold.txt` each, first six
re-checked 2026-08-15). Score with `py -3 scripts/score_gold.py`. One-shot
bake-off: Gemini 3.6 Flash 17.3% pooled word error, Sonnet 4.6 21.9%. Composer
chat is lower error but is not a bulk pipeline. Dual-model agreement still
shares a wrong word on about 5% of agreed tokens. **Bulk vision OCR is paused:**
the user cannot review 15,478 pages, and 17% word error would poison the corpus.
OCR decode work is on branch `feat/decode-table`. Batool PUA table is in
`data/decode/batool_pua_seed.json` (160 codes). This Gojri-English
dictionary is one 498-page file (`Gojri-English-Dictionary.pdf`). Body
pages 25-498 have **zero unknown** Batool codes. Front pages 1-24 are
mostly English; 3 Batool codes on those pages are still unmapped.
`Concise_Gojri_English_Dictionary_by_Dr_R.pdf` is the same 24-page front
matter, not a second volume. Decode with
`py -3 scripts/decode_batool.py 1 498`. Neighbor rules make page 25 letter
forms match `dict_alif_gold.txt` (`آبلائے`, `نھیں`, `مهارو`, `ھُدرو`).
Output is local under `data/decode/out/` (gitignored). NOORIN seed is
`data/decode/noorin_pua_seed.json` (**2,149 keys, complete**). Book-wide census:
`py -3 scripts/census_noorin.py 1 169`. Unique keys 2,149; table covers all.
**Mapped instances 100.0%** (80,638). **Zero unknown keys** on pages 1–169.
Page 50 still has zero unknown keys. Decode with
`py -3 scripts/decode_noorin_flow.py` on PUA NOORIN books. Kahawat-Kosh
(`Kahawat-Kosh.pdf`, 169 pages) is the reference book for this table.
Transfer scan: `py -3 scripts/census_noorin_transfer.py` writes
`data/decode/noorin_transfer.csv`. On 44 primary PUA books: **17 books >=90%**
mapped instances (typical Anjumshanasi poetry/prose 95–97%), **1 book 87%**
(G-Kashmiri-Dictionary), **16 books <1%** (Javaid Rahi dict parts use
Latin-range NOORIN codes, not PUA `F0xx`), **10 books 0%** (legacy_8bit/TT*
fonts). Bulk decode for books >=87%:
`py -3 scripts/census_noorin_transfer.py --decode --min-pct 87` →
`data/decode/out/<slug>/`. Use `--skip-census --batch-size 1` to resume
without re-scanning; `--skip-existing` on `decode_noorin_flow.py` skips
pages already written. Progress file:
`data/decode/transfer_decode_progress.json`. **All 17 transferable books
decoded** (Aug 2026).
High-count
base fills include `عا`, `ٹا`, `تھو`, `چڑ`, `ش`, `گی`, `قد`, `لو`,
`نیا`/`دنیا`, `ہونو`, isolated `ز`, `خا`, `سے`, `ئیے`, `بی`, `پنے`,
isolated `خ`, isolated `چ`, `مند`, `ھو`, `سیا`, isolated `ف`, `تیر`,
`ینی`/`دینی`, `بنا`, `مصیبت`, `پیا`/`روپیا`, `بچو`/`بچوں`, `منہ`,
`یکھ`/`دیکھ کے`, `مد`/`مدد`, `ریب`/`غریب`, `بغیر`, `مید`/`امید`/`میدان`,
`رضی`/`غرضی`, `شش`/`کوشش`, `بند`, `کنڈ`, `بہا`, `گما`, `گیو`, `پے`,
`بھو`, `کیو`/`کیوں`, `رہنو`, `تھا`/`تھاں`, `سوچ`, `شو`, `پا`/`پار`,
`ضا`/`رضا`, `تک`, `مت`/`ہمت`, `مطلب`, `بھی`, `ع`/`غ`, isolated `ق`/`شوق`,
`لت`, `گئی`, `تھی`, `ج`, `بجھار`, `جلد`, `محنت`, `حد`, `سد`, `ض`, `گھی`, `ل`/`لیا`, `شکر`, `دشمن`, `بچ`/`بچا`, `ٹھنڈ`/`چھوڑ`, `لینo`, `سر`, `و`, `د`, `ر`, `نو`, `کن`, `کہیں`, `F0D7`+`F026`/`F027`→`در`, `ھ`/`ھیان`, `دے`, `پئی`, `طرح`, `س`, `طا`, `ہم`, `چ`, `ٹھ`, `تیا`, `ٹھا`/`اٹھا`, `سمجھ`, `ق`, `یر`, `جد`, `فی`. Neighbor rules:
`NOORIN13:F0A8` (ا+ے→س, ر+ے→ہ), `NOORIN08:F081` (ر+ے→empty, ل+ں→ا),
`NOORIN09:F051` (default ٹھنڈ; next F07D→چھوڑ),
`NOORIN04:F058` (default بچ; next F0C6→بچا),
`NOORIN12:F0E2` (next F07B→بال), `NOORIN12:F07B` (prev F0E2→وں; next F07D→گھڑے; next F02C→گھڑیں; else گھڑی),
`NOORIN12:F0BE` (next یار→لیا), `NOORIN14:F07A` (line-start ر; after گما→ن/نو; after کی→ہنڈ; after F031 before ،→ ہنڈی; after ر before د/کو→empty),
`NOORIN81:F0A2` (empty before F07A/ھ; حا+…→ضر ہ; بعد F022→ضرر ; 0 leftovers), `NOORIN14:F0F7` (joiner; 0 placeholders), `NOORIN10:F072` (after کی/کو→ہی; before F0F7→ا; after نے→اک; 0 placeholders),
`NOORIN04:F0DB` (0 decode placeholders: prior batch plus p154 F098+…→بیری; p128 F04A+…→ب; p22 F041+…→empty),
`NOORIN08:F04A` (next F0DB→سخت), `NOORIN01:F09D` (after NOORIN57:F05A before F041→و),
flat `NOORIN27:F098` (نیچی), `NOORIN17:F041` (کر), `NOORIN05:F035` (پکی),
`NOORIN34:F023` (context: after د/یا → شمنی or دشمنی), `NOORIN01:F099` (before F023 → د; after F063 → یا),
`NOORIN16:F023`/`NOORIN01:F07B`/`NOORIN81:F07B` (خواہ مخواہ: F81→خو, F07B↔F023→اہ, F023→مخو),
`NOORIN06:F05E` (after F032→ٹھو گاٹھوری; after F09F→ھو; سو/نا+کرن→ٹھو; F0D1/F0D1→empty; جوٹھو/جھوٹو/رٹھو/اٹھو/ٹھوڈی/ٹھوکرے جا; line-start before س→جھوٹو ا; line-start before :→ھو; after F065→ھوا; 0 leftovers),
`NOORIN12:F042`/`NOORIN57:F031` (F031 before F042→بو; F042 flat لیں),
`NOORIN82:F074` (after ھ→ویہ; after ۔/سا/و/ما/پ/د/نا or line-start→یہ; after ج→ی; 0 leftovers),
flat `NOORIN01:F09F` (ڈ), flat `NOORIN26:F032` (گا), flat `NOORIN89:F031` (نجھی),
flat `NOORIN14:F0B7` (ھ; د+ے→ھیان), flat `NOORIN18:F0A9` (پئی; after آپ→ اپنی), flat `NOORIN01:F062` (طرح), flat `NOORIN08:F053` (س before طرح),
`NOORIN82:F040` (after کھا→د/دے; after تے→دے; 0 leftovers), `NOORIN12:F076` (گھاٹو/گھا/گھ/گھائی/گھوڑو/ک; F05E after→ٹ; F0F0 after→empty; 0 leftovers),
flat `NOORIN81:F0A4` (طا), flat `NOORIN48:F0EB` (ہم), flat `NOORIN57:F024` (چ), flat `NOORIN57:F04A` (ٹھ),
flat `NOORIN82:F071` (ایک), flat `NOORIN63:F0F0` (من; prev F068 next *:F06A→ں), flat `NOORIN08:F06A` (اس; prev F083→سکو; prev F037→اسکو; prev+next F05A→اسکو), flat `NOORIN06:F06A` (اس),
flat `NOORIN16:F078` (میا), flat `NOORIN12:F043` (لیو), flat `NOORIN82:F087` (قا), `NOORIN83:F0DE` (empty joiner; next F02E→بل, F03E→پل, F04C→تل, F054→ٹل/اٹل after F05A),
flat `NOORIN81:F09C` (صد; next F063→یا; next F0B8→قہ), `NOORIN82:F09A` (کڑ; next F0EC→کڑی; next F07B→کھڑ), `NOORIN56:F0DF` (اصو/اصولی/اصولو/صورت/صور; F0E0/F0DF after→empty),
flat `NOORIN85:F0BB` (تیا), flat `NOORIN06:F056` (ٹھا; F051/F05A before→ا), flat `NOORIN52:F099` (سمجھ; F057 after→آ),
flat `NOORIN48:F0DE` (ق after F0D8; کھ+ل/ڑ/و by next), flat `NOORIN81:F061` (یر; F05A before→empty; F02C after→یںپ),
flat `NOORIN81:F05D` (جد; F068→ید; F09E→کہ; F07A after→جدو), flat `NOORIN08:F04A` (س; F0DB after→سخت), flat `NOORIN63:F0B0` (فی), flat `NOORIN56:F0DD` (صل; F05A before→اصل; F071 before→حاصل),
flat `NOORIN05:F056` (پھل after کو/گو; و after نا+کھا، comma+کی، گا، line-start),
flat `NOORIN01:F0A7` (ر), `NOORIN06:F06E` (و; prev F07D→لئے),
flat `NOORIN27:F076` (نقصان; prev F04A→پنو نقصان; F079 after→empty),
`NOORIN05:F06E` (تباہی after F084; تباہ+بر after F07B+ز; else تباہ; F084 after→empty),
flat `NOORIN81:F06C` (چر; next F0F0→چڑ; F02C after→یںپ; F021 after→بی),
flat `NOORIN44:F041` (لگنی), flat `NOORIN22:F0AA` (پہلا),
`NOORIN81:F0A7` (طر; after خا→تر خاطر; before طرح→دی), flat `NOORIN63:F0DD` (لم),
flat `NOORIN17:F0D2` (لحاظ; F070/F06F after→empty), flat `NOORIN15:F0C9` (لکھ),
flat `NOORIN81:F064` (جگ; F0E0 before→ے after ت/ج else empty),
`NOORIN08:F094` (ے/سنی after د; سنی before : or after گل; empty before سنائی), `NOORIN25:F05B` (بیگا before نی; بن/bنا/بیگا line-start; گ before نا/و), `NOORIN43:F092` (نین default; نیند after کی/اپنی; ا after ج before کر; F059 after→د), `NOORIN21:F053` (نے default; نبھا after پئی), `NOORIN08:F096` (سہارے/ھک/سہارہ/و; empty after سے), `NOORIN57:F076` (سڑ default; ر after کو; ھ in کتھ; empty before یار), `NOORIN17:F081` (ھی default; تھی after F026/در), `NOORIN08:F0E8` (ش/شیر/یر/ک/ر/وں by context; شیر proverbs), `NOORIN57:F021` (ب default; بی after ڈ/چر; ے/ی/س/ہ by prev; duplicate empty), `NOORIN25:F0A9` (ے after ک/کی/و; ی after نہ; بھی after ں; F079 after→empty), `NOORIN13:F0FA` (نماز after کے; اں after ریںپ; ے after کی; گ after (), `NOORIN01:F071` (empty joiner; ت after F0E7), `NOORIN81:F099` (ڑ/ڈ/د before ف; duplicate empty), `NOORIN09:F09A` (ے/بلا/ا/و by context), `NOORIN82:F02D` (ند after ر; ں after ما), `NOORIN54:F02A` (ے before ک; empty before رکھ after F07A/F03A/F0CF/F0A7), `NOORIN05:F061` (empty joiner; پیدا when F071/F081/F035 in window), flat `NOORIN56:F0CD` (empty joiner after دے), flat `NOORIN09:F0F9` (empty line-start joiner), `NOORIN01:F09D` (empty; F05A+F041→و; گھی→ڈال; F021→و), `NOORIN14:F0D7` (ے after اپنوروپ; نا+F021→ی; نا+F056→ں; empty before ں after ددھا), `NOORIN05:F0DF` (پھر/تنگ before کرنو; full-row F0F4 context via `base_keys_before_full_row`), `NOORIN57:F060` (empty; F077+F071→چن), `NOORIN43:F0C3` (و after ہون/کرن; empty before ۔), `NOORIN05:F051` (empty joiner; پھر; چ in وچ; و/ی context), `NOORIN19:F03E` (ب/پ/د/ھ/ہ/و/ں by colon context), `NOORIN82:F07E` (ق in حقدار/قرض; empty before بتا), `NOORIN29:F068` (ں after ما; ے after مدد; ی after مصیبت; else empty), `NOORIN61:F0CE` (دین before F07B; دے after comma; ے in دینیت دے; ھ in لتھ; ھیل in پھیلنو; F07B empty after F0CE), `NOORIN01:F05E` (empty joiner; ٹ after گھا in گھاٹ نہیں), `NOORIN08:F0F1` (ے/د/ دے by context; colon joiner), `NOORIN15:F02E` (empty joiner after پ in پنی/پے), `NOORIN10:F088` (ی in ایں/ساکھیء; عاء/اء titles; ب in بے; empty before کڑھا/شکر; F059 empty after non-ی F088), `NOORIN16:F08C` (ر after F07A in ترہ; else empty), `NOORIN67:F0F0` (flat empty joiner), `NOORIN04:F0EA` (ی in کوئی; ا in پراں; دھ in دھلاو; else empty), `NOORIN10:F0B4` (ہ line-start/after F043; ئ before F060 after کو/ئے; F060→ی helper), `NOORIN43:F042` (ا line-start; م after F0BB; else empty), `NOORIN89:F036` (ے before ۔ after F067/F0C8; else empty), `NOORIN12:F031` (ا before F056; else empty), `NOORIN05:F05E` (ا in با; ی in کسی; else empty), flat `NOORIN82:F0B5` (empty joiner), `NOORIN16:F07E` (ہ in رہے/رہے ہیں/کم رہ; ے after ں/ک; empty after comma/شرمسار; F021→ے helper), `NOORIN07:F0EC` (ے line-start/after یار; else empty), `NOORIN10:F028` (ے in کہنی/رکے; else empty), flat `NOORIN82:F037` (ی after ت before اچا; else empty), flat `NOORIN17:F05E` (empty before کد), flat `NOORIN13:F0C3` (empty joiner), flat `NOORIN81:F0AD` (empty after ک/د), flat `NOORIN08:F073` (empty before م/ہمت), `NOORIN10:F0D2` (و after ر before لا/د/گہنو; else empty), flat `NOORIN63:F0D3` (empty after لا), `NOORIN32:F061` (ی/ں/نی/ے line-end inflections), flat `NOORIN57:F073` (empty joiner), flat `NOORIN12:F0D6` (empty after ھ), flat `NOORIN18:F09E` (empty before پدے), flat `NOORIN81:F057` (empty in کور/بایار), flat `NOORIN07:F0ED` (empty joiner), `NOORIN12:F0BF` (ے after کر; else empty), flat `NOORIN89:F05A` (empty before ج/بی/F06F), flat `NOORIN10:F047` (empty joiner), `NOORIN14:F068` (ی/ں/ا before F0E8/نا/گلانی; else empty), `NOORIN11:F048` (ا/و before ں/ھ/ک; empty after مقامتو), `NOORIN15:F059` (ے after ھ; empty after سو), `NOORIN05:F063` (یر default; empty joiner; یر after F045/F056/F07D/F0F2), flat `NOORIN04:F0E9` (empty joiner), `NOORIN04:F0CE` (ں after سو), `NOORIN20:F06E` (و after :), `NOORIN63:F0F3` (د after ز/ر; else empty), `NOORIN57:F063` (ڑ after مو; و after ھ; else empty), `NOORIN81:F0B8` (ا in باں; ب in کثریب/بہونو/برباد; else empty), `NOORIN63:F0AF` (ی after طر/ما; else empty), flat `NOORIN15:F0F5` (ت before ھ), `NOORIN81:F02F` (وں/توں/ں/کی by context; else empty), `NOORIN59:F0EB` (after لا: ھ/ر/ہ/ب/آ by next; empty before ت), `NOORIN13:F052` (after غ: ر/ا/ت/ھ by next; empty after ع before ک), `NOORIN12:F041` (ر after ک before تو; else empty), `NOORIN57:F027` (ں after ما before کے; ر after : before ر; else empty), `NOORIN19:F034` (گ line-start before ین; ے after کو/کی before ین; ے after ں before نہ; else empty), `NOORIN08:F065` (ے in کالے; و in نالوں; ے after کر before نے; ت before F050; else empty), `NOORIN14:F091` (د after بھا; ے/و after ک by context; else empty), `NOORIN10:F05D` (ی in را before ک; else empty), `NOORIN56:F0FA` (ھ after د; ی after ت/: before ک; ر after کھ before ر; else empty), `NOORIN12:F06B` (پ after آپ before F07B; ے after کی before F085; ی after د before F07B; ے after ل before F061; else empty), flat `NOORIN63:F0BE` (empty joiner), `NOORIN12:F024` (ے after بھا before ،; else empty), `NOORIN09:F0E5` (ے after گھر/پلاء/کے; ن in بنائے; ر in رہے; ا in ڈرانی; else empty), `NOORIN32:F05F` (ئی after کو; ہ after کا before ھ; ت in سوتری; ں in آنیاں; ہم line-start; else empty), `NOORIN14:F0DC` (ے after د/مد; ے before ناداد after :), `NOORIN04:F0DA` (ی line-start; ئی after کو; ے/یا/ھ/ی/empty by context), `NOORIN04:F0B9` (گ in رنگ; ف in فردر; ا/ڑ/empty by context), `NOORIN08:F092` (ھ/ہ after د; empty after ناداد), `NOORIN21:F088` (و in ھو;اں/پ/ا/یو/empty by context), `NOORIN24:F02C` (ک/س; ا+ئ/ک+ی pairs), `NOORIN20:F082` (ش in بارش; ی/ڑ/ب/ے/و by context), `NOORIN21:F075` (ے/ؤ/ا/ز/و/ہ/ن/empty by context), `NOORIN51:F096` (ا before ت; ے in کیے; else empty), `NOORIN53:F036` (ی/ہ/ا in ایک/کہہ/کا), flat `NOORIN22:F041` (ھ after F08A), `NOORIN01:F0AF` (ز before ندگی; ہ before نگ; empty line-start before :), `NOORIN52:F0F2` (ب in پنجابر; پ before ڈر; ہ in کھاوہ; else empty), `NOORIN82:F0AD` (ا in مار; ی before یار; else empty), flat `NOORIN07:F086` (empty index marker), `NOORIN57:F06A` (ھ in تھکنو; د after : in د دینو; else empty), `NOORIN81:F0B2` (ئی in کوئی; ب in بشوں; ہ in بہش; else empty), `NOORIN81:F02E` (بل after F0DE; rule in F02E block), `NOORIN82:F0A6` (ہ/ت/کو/empty by context), `NOORIN81:F077` (ف in فر; ش/ح/شر in شرم/حرمت; else empty),
`NOORIN82:F038` (after ک→ھ/و or قبل ای→رنگ; after با/F0AF/ڈ/ڈر/د/ر/کا+مند→نگ; 0 leftovers),
`NOORIN29:F04F` (ہ after ر; ے after ک), `NOORIN15:F0CF` (و in وت/کیوں/مو; empty before لائکرننی), `NOORIN07:F0A7` (و/یں/ی/ح/ں/space by gloss), `NOORIN26:F0CF` (و in یاروں/ماوے; ں in آپوں; else empty), flat `NOORIN69:F085` (۔), `NOORIN23:F074` (اپ/ے by context), `NOORIN28:F0F1` (،/space joiner in glosses), `NOORIN35:F0C6` (ب/ے/ن/space by context), `NOORIN11:F051` (ے/space joiner), `NOORIN41:F032` (و/ے/ت by context),
flat `NOORIN06:F0E5` (ے), `NOORIN08:F03F` (ا/ے/و/space by colon context), `NOORIN30:F044` (ے after ک), `NOORIN81:F093` (ے after ر), `NOORIN19:F049` (ا/وں/ک/اں by proverb gloss), `NOORIN41:F0AF` (empty before ہون), flat `NOORIN31:F06F` (و), flat `NOORIN08:F0B0` (،), `NOORIN63:F0B5` (ٹ after مو), `NOORIN18:F02B` (ا line-start; empty in چھوک/ہتھک), `NOORIN26:F083` (و in جگوں/سبوں), `NOORIN09:F096` (space/comma joiner), `NOORIN50:F071` (ھ/ی/ے/space in Urdu gloss), flat `NOORIN04:F0AB` (ے), flat `NOORIN04:F0B6` (۔), `NOORIN04:F02A` (ے/ی by context), flat `NOORIN01:F032/F039/F031/F030` (empty English index markers), `NOORIN54:F0AB` (ے before ک),
flat `NOORIN24:F0D6` (ر in گوجر/ڈر), `NOORIN12:F0F4` (ر in گوجر/لاڑ; ڑ after ڈر), `NOORIN57:F062` (ی after ،; و after ک; ہ in رہ; empty joiner), `NOORIN11:F037` (ی in بھائی/گل; ے/ئ/ھ by context), `NOORIN16:F07D` (غ headers; ک/ڑ/ے by context), flat `NOORIN01:F0AD` (ے Urdu gloss), `NOORIN39:F0C6` (ل/پ/ن/ے by context), `NOORIN13:F033` (و/ے/empty joiner), `NOORIN15:F02B` (ڑ/ے by context), `NOORIN66:F04F` (اں in ماں; empty after کو),
flat `NOORIN74:F0A2` (ں), `NOORIN57:F05F` (کی/لارہنو/نہیں by next), `NOORIN04:F0B3` (زھز/ھ/پ by neighbor), `NOORIN11:F0A7` (ن/ں/نا), `NOORIN14:F045` (اک/ک/ے/ھ/ں/ر by context), `NOORIN01:F021` (ے joiner; empty after F057+F028), `NOORIN48:F0F6` (ے/ت/ں/ک/آ by prev), `NOORIN06:F029` (ھ/ر/ت/ی by context), `NOORIN10:F08F` (ریب; قد before F08A), `NOORIN56:F0DC` (فر/کر by next),
`NOORIN08:F06D` (ر/ہ/گ/ھ by context), `NOORIN76:F027` (ک/ر by neighbor), `NOORIN17:F0E1` (ے/ن/ف/ھ by context), flat `NOORIN61:F08C` (۔), `NOORIN06:F0E4` (ے/ھ/و after آپ), `NOORIN57:F042` (یر/دی/ال/ون), `NOORIN73:F0EE` (بول/ھ/ر/خ by next), `NOORIN16:F06E` (ما/کی after F0E7), `NOORIN22:F098` (ے/ب by context), `NOORIN57:F077` (و/ت/ع/ے),
`NOORIN41:F0B1` (ے/ر/ہ), flat `NOORIN82:F05E` (نا after F059), `NOORIN05:F0B7` (ک in رکقماز; ے in سیرے), `NOORIN57:F05E` (ت/ی/و/د/ا), `NOORIN05:F0EA` (ھ after F05A+F07A; empty line-start), `NOORIN13:F0E6` (ے/ی/ا), `NOORIN11:F06D` (ی/ھ/ے/ب/ں), `NOORIN57:F064` (ے/و after F0CE), `NOORIN15:F050` (ی/و/ا/ے/ن by next), `NOORIN05:F082` (ر/ی by neighbor),
`NOORIN17:F097` (ب in تباہی; ھ in رددھاچڑانو), `NOORIN08:F0BA` (ک/ر by neighbor), flat `NOORIN82:F095` (ن), `NOORIN76:F084` (و/ں), `NOORIN58:F0ED` (ل/ہ/empty), `NOORIN10:F029` (و/ے/ک), flat `NOORIN10:F0E2` (د in ددھاکر), `NOORIN17:F083` (ند/ک/ر), `NOORIN31:F083` (ہ/ں/ئ),
flat `NOORIN48:F0E9` (ش in خوش/خورش/فخور), `NOORIN16:F0B2` (د/ر/ڈ), `NOORIN05:F099` (ے/ا), `NOORIN19:F0C2` (ے/ر/د), `NOORIN13:F076` (ے after F08A/F09B), `NOORIN10:F0C9` (ں/ے), `NOORIN14:F033` (ر after F021), flat `NOORIN32:F085` (ب), `NOORIN63:F031` (ر/ز/ے), `NOORIN82:F041` (ل/ں/ہ),
`NOORIN51:F0EF` (م/ت/ی/و/ہ/ر), flat `NOORIN07:F051` (ے), flat `NOORIN08:F07C` (ے), flat `NOORIN10:F0CB` (ر in ڈرر/شرر), `NOORIN11:F030` (ے/ر/ن), `NOORIN11:F04F` (ا/ہ/ی), `NOORIN29:F05B` (ے/ت/ہ/ب), `NOORIN63:F0DE` (ے/ر), flat `NOORIN34:F024` (ق), flat `NOORIN83:F0CB` (۔),
`NOORIN05:F048` (رت/ے/: by context; 0 leftovers), `NOORIN14:F0B4` (ھ/ر/م; 0 leftovers),
`NOORIN25:F043`/`NOORIN41:F041`/`NOORIN56:F0CC`/`NOORIN09:F0BF`/`NOORIN82:F096`/`NOORIN13:F036`/`NOORIN04:F04F`/`NOORIN05:F06B` (batches 73; 0 leftovers each),
flat `NOORIN07:F0AA` (رے), `NOORIN11:F02B`/`NOORIN64:F0D8`/`NOORIN49:F061`/`NOORIN81:F054`/`NOORIN57:F03F`/`NOORIN22:F056`/`NOORIN05:F064`/`NOORIN10:F0F3`/`NOORIN25:F0EB` (batch 74; 0 leftovers),
flat `NOORIN19:F046` (ک), `NOORIN41:F09B`/`NOORIN13:F0BB`/`NOORIN38:F0BD`/`NOORIN06:F028`/`NOORIN07:F0DC`/`NOORIN06:F04C`/`NOORIN15:F0DB`/`NOORIN14:F099`/`NOORIN07:F068` (batch 75; 0 leftovers),
`NOORIN75:F084`/`NOORIN12:F0F9`/`NOORIN14:F02D`/`NOORIN32:F06C`/`NOORIN14:F039`/`NOORIN10:F0B7`/`NOORIN06:F07C`/`NOORIN04:F0B4`/`NOORIN26:F07B`/`NOORIN57:F0B7` (batch 76; 0 leftovers),
`NOORIN01:F03F`/`NOORIN10:F0BE`/`NOORIN26:F024`/`NOORIN10:F094`/`NOORIN01:F05F`/`NOORIN27:F04D`/`NOORIN82:F065`/`NOORIN16:F0C8`/`NOORIN15:F032`/`NOORIN08:F0E0` (batch 77; 0 leftovers),
flat `NOORIN49:F08D` (ک), `NOORIN23:F0F0`/`NOORIN70:F052`/`NOORIN26:F031`/`NOORIN17:F040`/`NOORIN15:F041`/`NOORIN06:F0C3`/`NOORIN72:F0B4`/`NOORIN10:F0C0`/`NOORIN14:F0E2` (batch 78; 0 leftovers),
flat `NOORIN81:F094` (ر), flat `NOORIN45:F096` (ں), `NOORIN01:F0A3`/`NOORIN37:F057`/`NOORIN18:F085`/`NOORIN10:F03D`/`NOORIN01:F036`/`NOORIN57:F057`/`NOORIN59:F0F5`/`NOORIN82:F069` (batch 79; 0 leftovers),
`NOORIN28:F0F8`/`NOORIN18:F076`/`NOORIN11:F097`/`NOORIN13:F0B1`/`NOORIN57:F058`/`NOORIN81:F072`/`NOORIN81:F081`/`NOORIN04:F0BE`/`NOORIN14:F0C4`/`NOORIN12:F0CB` (batch 80; 0 leftovers),
`NOORIN89:F07A` through `NOORIN12:F038` (batches 81–95; 105 keys, 7 per batch, n=4 each; 0 leftovers),
`NOORIN08:F04D` through `NOORIN82:F085` (batches 96–115; 120 keys, 6 per batch, n≤4 each; 0 leftovers),
`NOORIN30:F048` through `NOORIN14:F060` (batches 116–135; 140 keys, 7 per batch, n≤4 each; 0 leftovers),
`NOORIN11:F074` through `NOORIN85:F0B8` (batches 166–195; 150 keys, 5 per batch, n≤3 each; 0 leftovers),
`NOORIN30:F046` through `NOORIN89:F030` (batches 196–230; 175 keys, 5 per batch, n≤3 each; 0 leftovers),
`NOORIN09:F09D` through `NOORIN17:F0EB` (batches 136–165; 150 keys, 5 per batch, n≤4 each; 0 leftovers),
`NOORIN34:F023` (شمنی/دشمنی; patched), `NOORIN07:F0B8`/`NOORIN01:F06D`/`NOORIN15:F0D3`/`NOORIN04:F068`/`NOORIN16:F0A3`/`NOORIN16:F056`/`NOORIN11:F046`/`NOORIN11:F0DC`/`NOORIN56:F089` (batch 65; 0 leftovers),
`NOORIN15:F0D0`/`NOORIN10:F051`/`NOORIN05:F0E2`/`NOORIN13:F0E0`/`NOORIN14:F0BC`/`NOORIN07:F098`/`NOORIN03:F0F9`/`NOORIN13:F02B`/`NOORIN29:F0F8`/`NOORIN10:F0E7` (batch 66; 0 leftovers),
`NOORIN13:F024`/`NOORIN59:F0EC`/`NOORIN14:F07D` (کہ/لا patched)/`NOORIN36:F0D2`/`NOORIN81:F06E`/`NOORIN14:F02E`/`NOORIN41:F0AB`/`NOORIN05:F04D`/`NOORIN06:F090`/`NOORIN08:F032` (batch 67; 0 leftovers),
`NOORIN11:F0CE`/`NOORIN82:F0A5`/`NOORIN25:F05A`/`NOORIN15:F0C7`/`NOORIN72:F0A2`/`NOORIN05:F044`/`NOORIN06:F060`/`NOORIN22:F040`/`NOORIN15:F089`/`NOORIN12:F03F` (batch 68; 0 leftovers),
`NOORIN82:F0B4`/`NOORIN27:F095`/`NOORIN48:F0EF`/`NOORIN17:F03E`/`NOORIN10:F072` (patched)/`NOORIN01:F072`/`NOORIN81:F03A`/`NOORIN83:F0CD`/`NOORIN53:F0CC`/`NOORIN67:F028` (batch 69; 0 leftovers),
`NOORIN12:F0F2`/`NOORIN10:F0CF`/`NOORIN16:F0CB`/`NOORIN05:F059`/`NOORIN81:F0B0`/`NOORIN05:F0EF`/`NOORIN08:F043`/`NOORIN08:F0D1`/`NOORIN57:F040`/`NOORIN19:F054` (batch 70; 0 leftovers),
`NOORIN14:F078`/`NOORIN16:F0BE`/`NOORIN04:F07A`/`NOORIN29:F0C8`/`NOORIN15:F0E8`/`NOORIN07:F04B`/`NOORIN14:F0AF`/`NOORIN13:F0B6`/`NOORIN15:F027`/`NOORIN12:F0DC` (batch 71; 0 leftovers),
`NOORIN27:F028`/`NOORIN02:F073`/`NOORIN08:F090`/`NOORIN14:F084`/`NOORIN55:F0E5`/`NOORIN50:F0F4`/`NOORIN46:F037`/`NOORIN04:F0F7`/`NOORIN10:F0B8`/`NOORIN54:F0CB` (batch 72; 0 leftovers),
all unmapped `NOORIN86:*` overlays empty (nuqta). All `NOORIC`/`NOORIC01` overlays in Kahawat-Kosh map to empty (131 keys).
Dump with `py -3 scripts/dump_noorin_lines.py 50`. Do not mix with Batool.
Clean-text extract: `py -3 scripts/extract_clean_text.py` writes
`data/extracted/` (gitignored) plus `provenance.jsonl`. The FLI corpus
copy is real Gojri Unicode. Remaining `good_text` PDFs: 4 files, 1,473
pages (3 English Islamic studies; 1 Devanagari dictionary with mixed
GurbaniHindi Latin glosses). The Quran translation is **not** clean
Unicode. Scheme `broken_tounicode`. `get_text` on page 17 is unreadable
(Buhid / Latin-extended stand-ins for joining UrduTypesetting glyphs).
The extract folder was deleted. Next path for that book is a GID decode
table against the embedded `UrduTypesetting` subset (927 glyphs, no
cmap), or vision OCR. Javaid Rahi dictionary parts use NOORIN
with Latin-range codes, not PUA `F0xx`, so the Kahawat table does not
transfer (<1% on Javaid Rahi dict parts; Latin-range codes). Same-scheme
PUA transfer works on Anjumshanasi books: typical 95–97%, Aks-e-Jamal
92.8% book-wide. Full scan: `py -3 scripts/census_noorin_transfer.py`.
Decode PUA NOORIN books with
`py -3 scripts/decode_noorin_flow.py PDF START END` or bulk
`py -3 scripts/census_noorin_transfer.py --decode --min-pct 87`.
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
Direct-extraction pages were removed from the gold image folders. Step 0.4
(corpus layout / provenance) is still open. See `plans/STAGE-0.md`,
`data/gold/README.md`, and `LOG.md`.
