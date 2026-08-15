# Gojri AI Project Roadmap (draft, for discussion)

This is a draft, not a locked plan. Each stage has open questions we should settle
together before building. See `CLAUDE.md` for the research and technical findings
behind these decisions.

## The big picture: why this order

The three goals (OCR, ASR, fine-tuned model) aren't independent. Text extraction
(OCR) feeds the other two: more clean Gojri text means more sentences to read aloud
for voice data, and more raw material to teach a language model. So even though you
have voice data sitting ready to use right now, it makes sense to unlock the text
first, since it multiplies the value of everything after it.

**Honest caveat on that ordering (added in strategy review):** the "OCR feeds
everything" claim is strong for Stage 3 (the translator genuinely needs the text)
but weak for Stage 2. ASR fine-tuning needs audio paired with transcripts, and we
already have that; OCR text only helps ASR *indirectly and later*, by supplying new
sentences for humans to read aloud in future recording drives. Stage 2 is therefore
fully unblocked today and is the fastest route to a first working artifact. Two
defensible orderings:
- **OCR-first (current plan)**: tackles the bottleneck for the most valuable goal,
  but the first visible result is further away.
- **ASR-in-parallel**: run the Whisper fine-tune early, because it is largely a
  known-recipe exercise (BaltiVoice) on data already in hand, and it produces a
  demoable win plus early hands-on ML learning while OCR grinds through 14,550 pages.
Recommendation: keep OCR as the primary track, but do not serialize Stage 2 behind
it. Stage 2 has no real dependency on Stage 1 and is the better first *learning*
project.

## Two gaps found in strategy review (address before/inside Stage 0)

**1. There is no evaluation plan, and without one we are flying blind.**
Every stage currently ends with "the user spot-checks quality," which is subjective
and unrepeatable. We cannot tell whether Haiku is good enough, whether the decode
table beats vision transcription, or whether model v2 is better than v1, because
there is nothing to measure against. Fix, and it belongs in Stage 0 because it must
exist *before* the things it measures:
- **OCR gold set**: pick ~20-30 pages spanning the different document types (PUA
  scheme, ASCII scheme, image-only, dictionary layout, poetry layout). The user
  hand-corrects those to perfectly accurate text, once, as one
  `transcriptions/<page>/<page>_gold.txt` per page. That becomes the permanent
  yardstick for every OCR method we try, measured by character or word error rate.
- **ASR eval set**: already exists, Common Voice ships a `test.tsv` split. Just do
  not train on it.
- **Translation eval set**: hold out a portion of the real Gojri-Urdu pairs from
  `10-3 Stories with Urdu Translations.txt` and never train on them.
This is a modest amount of human work that makes every later decision evidence-based
instead of a matter of opinion.

**2. "Process all 14,550 pages" is an unexamined assumption.**
Nobody has asked what the last 10,000 pages are actually worth. Rough order of
magnitude: 14,550 pages is perhaps 4-5 million words, which is a real corpus for
adapting a model but still small by LLM standards, and its value is very unevenly
distributed (dictionaries and parallel text are worth far more per page than a
seventh volume of prose). Treat full-corpus processing as a *decision to revisit*,
not a commitment: process in value-ordered tiers, and after each tier ask whether the
next one still earns its cost. This pairs with the tiering already defined in Stage 1.

## Stage 0: Data hygiene (small, do this first)
- De-duplicate the 92 PDFs. Verified by file hash (not just filename matching, which
  had already been shown to miss things), **7 exact-duplicate groups found**,
  wasting 2,244 pages total: the 281-page Javaid Rahi dictionary (3 copies, not 2),
  the 717-page Quran translation (2 copies), the 410-page `Gojri_lok_kahani` folklore
  collection (2 copies, not previously known about), the 275-page `gojri-history`
  volume (2 copies, not previously known about), plus three smaller
  `gojri-dictionary-by-dr-javaid-rahi-*` duplicates (169, 110, and 1 page). Full list
  with exact filenames in `CLAUDE.md`. Keep one copy of each, drop the rest, before
  anything else. Caveat: hash matching only catches byte-identical files, a
  re-scanned copy of the same book wouldn't be caught this way, so this is "no exact
  duplicates missed," not "guaranteed no duplicate content at all."
- Decide where data lives long-term: local folders are fine for now, but we should
  pick a plan for backup and later for public release (Hugging Face has a free
  "dataset repo" hosting model made for exactly this).
- Licensing: the Mozilla text corpus is explicitly CC-BY-NC-4.0 (non-commercial,
  credit FLI). The PDF collection (Javaid Rahi and others) was freely available
  online with no known restriction, but "no known restriction" isn't the same as an
  explicit license. Fine to proceed with for research/preservation/learning now;
  before Stage 4 (public release of anything derived from this material), worth a
  sanity check with the sources, and defaulting any public release to
  non-commercial terms, matching the strictest license already in the mix.
- **Re-triage the 11 "unclear" files individually, do not bulk-judge them.** Strategy
  review caught a real error here: these were previously assumed to be English-language
  books, but inspection showed the bucket is mixed. `gojri-kalam-israel-asar` and
  `gojri-kalam-_gulam_sarwar_rana` are **Gojri poetry collections** (they use NOORIN
  Nastaliq fonts) that merely *extract* as Latin gibberish because of a second
  encoding scheme, and they were nearly discarded. Meanwhile `the-gujjars-vol-1/3/4/5/6`
  really are English prose (verified: Calibri font, readable English). Check each file
  by its embedded font names, not by character statistics.
- **Build the OCR gold set** (see "Two gaps" above): hand-corrected pages
  spanning document types, to serve as the permanent yardstick for OCR quality.
  **Progress (Aug 2026):** working set is 12 vision pages with `_gold.txt`.
  Bake-off scored. Bulk vision OCR paused. Decode-table spike is next.
  This is the single highest-value piece of human effort in the whole project, because
  every later OCR decision depends on being able to measure.
- Output of this stage: a deduped, correctly-triaged file list, sorted into the
  priority order used to kick off Stage 1 (see tiers below), plus the gold evaluation
  set, so Stage 1 starts on the highest-value material with a way to measure results.

## Stage 1: Text extraction (OCR)
Turn the in-scope PDFs into clean Unicode Gojri text. Vision transcription was
the first validated path (render page, ask a vision model). **Aug 2026:** the
gold-set bake-off showed one-shot vision error is too high to run unreviewed,
so bulk vision OCR is paused. The decode-table spike is the next experiment
for font-encoded pages. Image-only pages still need vision later.

Confirmed breakdown after inspection: 4 files already have good text (no work
needed, and this bucket includes the huge 717-page Quran translation, so that
volume costs nothing to process), 59 have the font-encoding problem, 18 are
image-only, and 11 look like they may not even be Gojri-script material (mostly
English-language books about Gujjars, need a relevance check, see parking lot
below). **Precise, hash-verified page count for the real workload (bad-text +
image-only, after removing exact duplicates): 14,550 pages.** This corrects an
earlier rougher estimate that undercounted the total.

**Processing order, highest value first, not just "start at file 1":**
1. **Dictionaries and glossaries first**: `Gojri-English-Dictionary.pdf`,
   `Concise_Gojri_English_Dictionary_by_Dr_R.pdf`, the `gojri-dictionary-by-dr-
   javaid-rahi-*` parts, `Kahawat-Kosh.pdf` (proverbs). A bilingual dictionary entry
   is already a translated pair (Gojri word <-> English/Urdu meaning), so this is
   structured, directly-usable parallel data for Stage 3, arguably more valuable per
   page than ordinary prose. `Gojri-Hindi-English-Dictionary.pdf` needs a quick check
   first, since it sampled as pure Latin script, it may already be a romanized
   dictionary rather than one using Nastaliq script, which would mean it needs no
   vision transcription at all, just direct text extraction.
2. **General literature next** (stories, poetry, folklore, the bulk of the 59+18
   files): good general-purpose corpus material. Worth specifically watching for more
   documents structured like the parallel-translation file already found in the
   Mozilla corpus (Gojri passage immediately followed by a labeled Urdu translation),
   since those are rare and valuable if any exist in this pile too.
3. **Large volumes last**: confirmed these four actually need vision transcription
   (unlike the Quran translation, which is "good text already" and needs no OCR at
   all, it doesn't belong in this processing order): `Gojri_lok_kahani.pdf` (410
   pages, font-encoding problem), `gojri-history.pdf` (275 pages, font-encoding
   problem), `Gujjar_Qabila_Ki_Louk_Warsti_Dictionary.pdf` (202 pages, image-only),
   `LOK_VIRSO_Gojri_The_Folk_Lore_of_Gujjar.pdf` (117 pages, image-only). High page
   count relative to tier 1's value, worth doing but not first, and worth sampling
   a few pages before committing to all of them.
- Small test batch first (one full short book from tier 1 or 2), you review quality,
  before scaling up further.
- **Test batch must include a model comparison, not just a quality check**: the one
  successful transcription we've seen so far used this conversation's own
  (Sonnet-class) vision reading, not the cheaper Haiku model the budget estimate
  assumed. Haiku's real quality on Nastaliq is untested. The test batch should run
  the same pages through Haiku and Sonnet (and optionally Tesseract, a free
  traditional OCR engine, as a zero-cost baseline, though it's expected to do
  noticeably worse on Nastaliq specifically) so the model choice for the full run is
  based on real comparison, not assumption.
- You (native speaker) spot-check a sample of pages for accuracy, watching
  specifically for confident-sounding but wrong text, a known risk with LLM-based
  OCR (it can fluently guess a plausible word instead of accurately failing on an
  unclear one), not just typos.
- Output: a much bigger, cleaner Gojri text corpus than the ~60K words we started
  with, likely the single highest-leverage thing we can produce early on.
- **Cost estimate, corrected again in strategy review** (the previous "~$44 Haiku /
  ~$175 Sonnet" figures were wrong: they counted only input tokens and ignored output
  tokens, which for OCR are a full page of text billed at ~5x the input rate).
  Using measured image sizes (~2,530 image tokens/page) plus ~1,200 output tokens:
  **Haiku ≈ $100, Sonnet ≈ $377** across 14,550 pages. Haiku would eat two thirds of
  the entire AWS credit; Sonnet-for-everything is unaffordable. Implications:
  - Cost control is a primary design constraint, not a detail.
  - A hybrid is likely: cheap model for bulk, expensive model only for the
    highest-value tier-1 dictionaries or for pages flagged as uncertain.
  - **Free optimization already found**: render pages at zoom 2, not zoom 3. Both
    downscale to the same size on the model's side, so zoom 3 pays identical tokens
    for no benefit.
- **Run the decode-table spike before committing bulk spend.** The font-encoded PDFs
  are a deterministic substitution cipher, not noise; a census found only ~2,022
  unique glyph shapes, with the top 432 covering 90% of all text. If we can learn
  that mapping from a small vision-transcribed sample, the largest cost bucket
  (13,269 pages) decodes for free, deterministically, with zero hallucination risk.
  It is a research bet with real risks (right-to-left alignment, ligature-to-multi-
  character mapping, multiple tables needed for the multiple encoding schemes), so
  timebox it, but the payoff is asymmetric: success saves ~$90 and removes the
  biggest quality risk, failure costs a day and we fall back to the already-validated
  vision approach. Full analysis in `CLAUDE.md`. **Status (Aug 2026):** gold-set
  bake-off completed; bulk vision OCR paused. This spike is now the next OCR
  experiment, not a side bet after a Gemini bulk run.

## Stage 2: Speech recognition (ASR)
Fine-tune an open speech-recognition model (Whisper) on the existing Gojri audio,
following the same recipe used for Balti (a very similar, already solved case):
expect a rough but usable result, not something polished.

- **Confirmed locally present**: `datasets/cv-corpus-26.0-2026-06-12/gju/`, 11,741 clips,
  10.68 hours, 11,081 validated rows. Speaker count has a small discrepancy worth
  knowing about: the online dataset page says 7 speakers, our own direct check
  found 6 unique speakers in the validated set (parking lot).
- Contribute more recordings via Mozilla Common Voice's normal recording flow to grow
  past 6-7 speakers and past ~11 hours (both speaker diversity and total hours matter,
  and we're just under the ~15-20 hours the research literature suggests for a solid
  result).
- Sentences from the newly OCR'd books (Stage 1) can become new material to read
  aloud for more recordings, this is where the two stages start reinforcing each
  other.
- Can run in parallel with Stage 1 since the audio data already exists; doesn't have
  to wait.
- **YouTube audio (user suggestion, Aug 2026)**: real potential source of more Gojri
  speech, but a different kind of data than Common Voice, worth planning for
  correctly rather than treating as more of the same. It comes with no transcript
  (unlabeled), so it can't directly become more Whisper fine-tuning pairs the way
  Common Voice data can. Realistic use: unlabeled/self-supervised pretraining to help
  the model learn Gojri's sound patterns before fine-tuning on the labeled set, a
  standard low-resource-speech technique, or a later pseudo-labeling loop once a
  first model exists. Also needs audio quality curation (background noise, music,
  cross-talk) and a licensing check before any public use, YouTube content isn't
  CC0 like Common Voice. Planned as a Stage 2 enhancement once the core fine-tuning
  is working, not a Stage 0/1 priority.

## Stage 3: Fine-tuned language model
Adapt an existing Urdu-capable model toward Gojri (translation, basic generation),
using transfer learning rather than training from scratch, since our data will still
be small by LLM standards even after Stage 1.

- We're not starting from nothing on parallel data: `10-3 Stories with Urdu
  Translations.txt` (already in the Mozilla text corpus) has several real
  Gojri-to-Urdu story/poem pairs with explicit translations, and Stage 1's
  dictionaries will add structured word-level pairs. Both are small, but they're
  real, verified examples, not guesses, which makes them useful as few-shot examples
  to show a strong LLM the correct style and conventions when it drafts translations
  of the rest of the (larger) monolingual corpus.
- The realistic path to more parallel data: use a strong LLM to draft translations of
  Stage 1's Gojri text, guided by the real examples above, and have you correct them
  as the native speaker. This is real, valuable work you're uniquely positioned to
  do, and a good place for you to learn how "human-in-the-loop" data creation works
  in practice.
- **Decided:** two goals, in sequence rather than at once:
  1. A **Gojri <-> Urdu/English translator** first. This is the more tractable goal
     given our data, and it's the natural stepping stone to goal 2: once translation
     works, a "cascade" approach (translate Gojri input to Urdu/English, let a
     capable existing LLM handle the actual conversation, translate the reply back
     to Gojri) can get us most of the way to a conversational assistant without
     needing to natively train a full Gojri chat model from scratch.
  2. A **conversational assistant that speaks Gojri directly**, once real
     translation quality and text volume support it. This needs meaningfully more
     data than translation alone (a chatbot needs to handle open-ended requests, not
     just convert sentences), so it's the longer-term goal, not the starting point.

## Stage 4: Publish and promote
Once something works, even roughly:
- Publish datasets and models on Hugging Face (the standard place for this, and
  where the Balti project published theirs).
- Consider reaching out to FLI (already doing serious Gojri documentation work) and
  Common Voice, rather than working in isolation from people already active in this
  space.
- A small public demo (type or speak Gojri, see it transcribed/translated) is a good
  way to make the work visible and invite more community data contribution.

## Parking lot (known issues, deliberately deferred)
Things we've noticed but agreed not to solve right now, tracked here so they don't
get lost:
- **Broken character in the text corpus**: 82 occurrences of an invalid Unicode
  "non-character" found in 4 of the 11 Mozilla corpus files (the folk stories/poems
  and the Urdu-translation file), likely a lost Gojri-specific diacritic mark that
  standard Urdu doesn't use. Needs investigating and fixing before those 4 files are
  used for real training, not blocking anything right now.
- **11 "unclear" PDFs — RESOLVED (Aug 2026, Stage 0 execution)**: rebuilt the
  manifest classifying by script-in-text instead of English-word-counting. Result: 6
  files (~1,290 pages) were genuine Gojri content in a third legacy encoding scheme
  and are now correctly in scope; `Gojri-Hindi-English-Dictionary.pdf` (458 pages) is
  Devanagari, not English, and is likely the single most valuable document in the
  collection; only 7 files (4,192 pages) are genuinely out-of-scope English prose.
  Full detail in `CLAUDE.md`.
- **Two-page-spread PDFs — RESOLVED (Aug 2026)**: 26 files, 6,295 pages, have a
  single PDF page containing two physical book pages side by side. Decision: split
  each into two images at the exact geometric horizontal center, implemented in
  `scripts/split_spread.py`. Verified this is safe, not just convenient: measured
  the whitespace gap across 6 files x 3 pages each, exact center always fell inside
  a contiguous white gutter, worst-case margin 61px on a 1684px-wide page (~3.6%).
  Also verified visually on a real page: both halves render with their full
  decorative border intact, no text clipped. Reading order confirmed correct in the
  same test: since these are right-to-left books, the RIGHT half is the earlier page
  and LEFT half is the later page, confirmed by the visible printed page number
  appearing on the left half only. As a side benefit, splitting also roughly doubles
  each page's effective resolution after Claude's automatic image downscaling
  (previously the two pages shared one downscaled image), which should help accuracy
  too, not just reading order.
- **Orthography/normalization is still unowned and it is a cross-stage risk**: if
  OCR output, the existing Mozilla corpus, and the Common Voice transcripts each use
  different spelling conventions for the same Gojri words, Stage 3 training data will
  be inconsistent and the model will learn noise. Worth an early look at what
  conventions the Common Voice sentences actually use, since those are already
  human-curated, and adopting one convention project-wide.
- **PDF licensing verification**: proceeding now on "freely available, no known
  restriction," revisit properly with sources before Stage 4 public release.
- **Common Voice speaker count discrepancy**: online dataset page says 7 speakers,
  our own direct check of `validated.tsv` found 6. Low stakes, but flagged rather
  than silently picking one number.
- **Possible near-duplicate PDFs not caught by hashing**: the 7 confirmed duplicate
  groups are exact byte-for-byte matches only. A re-scanned or differently-exported
  copy of the same book could still be hiding in the collection undetected. Worth a
  lighter content-similarity pass at some point, not urgent.
- **YouTube audio licensing**: fine for private research use, needs a real check
  before any public release of models/data derived from it.

## Cross-cutting things to keep deciding as we go
- **Orthography**: Gojri has no single standard spelling. FLI has proposed one. We
  should probably follow an existing standard rather than invent our own, to stay
  compatible with future community work.
- **Budget**: $150 AWS credit is small. Best used for OCR transcription (Stage 1) and
  later light hosting, not for training runs, free platforms like Google Colab are
  better for the fine-tuning experimentation itself.
- **Learning goal**: each stage is also a chance to actually learn the underlying
  AI/ML ideas (what fine-tuning is, what a tokenizer is, what WER means, etc.) as we
  hit them, not all at once up front.

## Status
**Strategy review (Opus, Aug 2026) complete.** Verdict: the overall five-stage shape
holds up and is sound, but the review found one wrong number, one wrong conclusion,
and two missing pieces, all now fixed above:
- **Wrong number**: OCR cost was understated ~2x by ignoring output tokens.
  Corrected to Haiku ≈ $100 / Sonnet ≈ $377, which makes budget a primary constraint.
- **Wrong conclusion**: the 11 "unclear" PDFs were assumed to be English books; two
  are actually Gojri poetry collections that were nearly discarded.
- **Missing**: no evaluation/gold-standard sets existed anywhere in the plan, so no
  decision could have been made on evidence. Now a Stage 0 deliverable.
- **Missing**: no cost-control strategy. Now includes the decode-table spike (a
  potentially free, deterministic alternative for the largest page bucket) and the
  free zoom-2 rendering fix.
Also newly documented: the collection contains **two distinct legacy encoding
schemes**, not one, which explains the misclassification and shapes any decode work.
Next: per-stage implementation plans, starting with Stage 0.

### Prior third-pass notes (retained)
Corrected two real mistakes from the second pass:
the page-count/cost estimate was based on an undercount (now hash-verified: 14,550
pages actually need paid transcription, not the rough ~18,000-total figure used
before), and 2 of the 7 exact-duplicate PDF groups had gone completely unnoticed
(the 410-page `Gojri_lok_kahani` and 275-page `gojri-history` volumes). Also added
the YouTube ASR consideration and resolved the `pdfs/unlocked/` open question. Model
choice for OCR was flagged as a real budget decision requiring a gold-set test.
That test (Aug 2026) puts Gemini 3.6 Flash ahead of Sonnet 4.6 on one-shot word
error (17.3% vs 21.9%). Haiku 4.5 is shelved. Bulk vision OCR is paused. Next OCR
work is the decode-table spike. Stage 0 execution (dedup using the
verified list, relevance check on the 11 unclear files, confirm priority order),
then detailed per-stage implementation plans, starting with Stage 1's test batch.
