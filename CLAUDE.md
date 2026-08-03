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
- **Never use em dashes (—) in responses.** Use normal sentence connectors and punctuation.
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
- `Gojri Language Corpus/`: 11 UTF-8 .txt files from the Mozilla Data Collective
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
- **`cv-corpus-26.0-2026-06-12/gju/`: the Common Voice "Scripted Speech 26.0 - Gujari"
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
- `PDFs/`: 92 PDF files, dictionaries, textbooks, poetry, folklore, a Quran
  translation, history volumes, etc. See the precise, hash-verified categorization
  and duplicate list further down (not repeated here to avoid two sources of truth).
- `PDFs/unlocked/`: contains one already-extracted .txt sample that reads as clean,
  correct Nastaliq Unicode (including bracketed image descriptions like
  `[لوگو: ...]`). **Resolved**: asked the user directly, this was not produced by
  running any AI/OCR tool ourselves, it's a file collected as-is from an online
  source that happened to already have clean text. It is *not* evidence that a
  vision pipeline was already tried on our own scans, that validation was done
  separately and directly (see OCR findings below).

## Key technical findings from research

### Garbled text when copy-pasting from PDFs — CONFIRMED with direct inspection
Verified directly (Aug 2026) using PyMuPDF against the actual files in `PDFs/`, not
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
  (401 pages) and `Revival-of-Islam.pdf` (116 pages), both under `PDFs/anjumshanasi/`.
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
   cleanup only, no OCR/vision needed. Notably this bucket already includes the
   717-page Quran translation, so that large volume needs zero transcription spend.
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
8. Since there's no independent ground truth to check accuracy against, quality
   control means the user (native speaker) spot-checking a sample of transcribed
   pages against the source images, not an automated accuracy score, and this check
   specifically needs to watch for confident-but-wrong text, not just typos.

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

**How it would work**: vision-transcribe a modest "training set" of pages, extract
the parallel (font, codepoint) sequence from the same pages, align the two, and
learn the mapping. Then apply the learned table to decode all remaining pages
deterministically at zero marginal cost.

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
  (see `cv-corpus-26.0-2026-06-12/gju/` above), close to but under that range, so
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

## Status
Stage 0 in progress (Aug 2026): manifest built and its classification errors caught
and fixed on the same day, before any bulk spend. Remaining Stage 0 work: build the
OCR gold set (Step 0.3) and finalize corpus/provenance conventions (Step 0.4). See
`plans/STAGE-0.md` for the full implementation plan and `ROADMAP.md` for the staged
project plan and parking lot.
