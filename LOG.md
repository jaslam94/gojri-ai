# Experiment Log

A dated, running journal of what we try, what we find, and why we made each call.
`CLAUDE.md` holds the accumulated *current state* of project knowledge (decisions,
findings, status); this file is the *story* of how we got there, kept mainly so you
can track your own learning as we go. New AI/ML terms get a one-line explanation the
first time they show up, then get added to the Glossary at the bottom.

---

## 2026-09-27 — Lexicon packaged for public publish (tracked under data/lexicon/)

**Canonical files (committed to git):**

| Path | Content |
|------|---------|
| `data/lexicon/gojri_lexicon_final.tsv` | 1,862 Devanagari ↔ Nastaliq headwords |
| `data/lexicon/gojri_lexicon_human_verified.tsv` | 50 speaker-checked rows |
| `data/lexicon/README.md` | Hugging Face dataset card |
| `data/lexicon/PUBLISH.md` | Upload include/exclude + CLI steps |

**Kept pipeline (tracked):** `scripts/dict_translit_common.py`,
`dict_translit_pass1.py`, `dict_translit_pass2.py` (API; quota-limited),
`dict_translit_verify_batch.py`, `prompts/devanagari_to_gojri_nastaliq_v1.txt`.

**Removed temporary:** `dict_translit_pass2_local.py`,
`dict_translit_pass2_gemini_engine.py`, `build_full_verified_lexicon.py`,
provisional rule-script TSVs under `data/extracted/.../translit/`.

**Still gitignored scratch:** Pass 1/2 work files under
`data/extracted/.../translit/` (not the public deliverable).

**Quality in final TSV:** 50 `human_verified`, 299 `pass2_refined`, 1,513
`pass1_kept`. Zero empty Nastaliq. Zero `ݨ`.

**Next (user):** upload `data/lexicon/` to Hugging Face per `PUBLISH.md`.

---

## 2026-09-02 — Devanagari dictionary → Nastaliq: two-pass pipeline (Aksharamukha + Gemini)

**Goal:** convert Devanagari headwords from `Gojri-Hindi-English-Dictionary.pdf` extract
to Gojri Nastaliq using a hybrid pipeline (rule draft, then AI refinement).

**Pass 1 (Aksharamukha):** `scripts/dict_translit_pass1.py`
- Parses Devanagari headword lines from `data/extracted/clean-pdf/gojri-hindi-english-dictionary/page-*.txt`
- Converts with Aksharamukha `Devanagari → Urdu`, `post_options=['UrduRemoveShortVowels']`
- Output: `data/extracted/.../translit/pass1_aksharamukha.tsv`
- Full run: **1,863 entries** from **414 pages** (~12s, local, free)

**Pass 2 (Gemini):** `scripts/dict_translit_pass2.py`
- Reads pass-1 TSV; sends batches of 20 to `gemini-3.6-flash` with
  `prompts/devanagari_to_gojri_nastaliq_v1.txt` (Gojri-not-Urdu rules, pass-1 as hint)
- Output: `pass2_gemini.tsv` with `nastaliq_pass2` column
- Pilot page 19 (22 entries): pass-2 mostly matched pass-1; one change
  `अंगणू` `انگنو` → `انگݨو` (Gemini used ڱ for ण). Needs user verification.
- First API call hit 503 (high demand); retries added; second run succeeded.

**2026-09-06 — User verified `अंगणू` → `انگنو` (not `انگݨو`).** Devanagari ण
(retroflex n) maps to standard ن in Gojri Nastaliq. Gemini wrongly used rare letter
ݨ (U+0768). Prompt updated: rule 9 forbids extended Arabic letters; keep pass1 when
correct.

**Shared parser:** `scripts/dict_translit_common.py`

**Not in scope yet:** Latin-only headwords (many pages like page 49); single-letter
pronunciation guide rows (`क`, `ख`) parsed as entries — filter later if needed.

**Next:** skip full pass-2 run for now. User verified `अंगणू` = `انگنو` (pass 1 correct;
pass 2 wrong). Page 19 pilot: 1/22 diffs, that diff was wrong. **50-word verification
batch** from pass 1: pages 19, 31, 167 → `translit/pass_verify_batch01.tsv`
(`py -3 scripts/dict_translit_verify_batch.py`). Fill `nastaliq_verified` and
`verify_status` (pending/ok/fixed/skip). Re-run pass 2 only on rows where roman or
meaning suggests pass 1 is wrong.

---

## 2026-08-03 — GitHub setup: keeping large/licensed data out of git

Set up the repo to be pushed to GitHub. Found `PDFs/` (834MB) and the Common Voice
audio corpus (`cv-corpus-.../`, 265MB) sitting in the single local "initial commit,"
never pushed anywhere yet.

**Decision: excluded both via `.gitignore`.** Two separate reasons:
1. **Size** — pushing ~1.1GB of binaries means every future clone downloads it all,
   forever.
2. **Licensing** — most PDFs are non-commercial-licensed (Dr. Javaid Rahi's works,
   CC-BY-NC-4.0-style) and Common Voice's terms don't allow re-hosting. Publishing
   them on a public GitHub repo isn't just wasteful, it's likely not allowed.

Since nothing had been pushed to a remote yet, the local "initial commit" was
*amended* (not a new commit — only safe because it was still 100% local) to drop the
large files from history entirely, instead of just hiding them from future commits.
`git gc` confirmed the cleanup: `.git` folder dropped from 881MB → 5.4MB.

**Mistake made here, noted so it doesn't repeat**: as part of that cleanup I ran
`git gc --prune=now`, which permanently deleted the *original* (pre-correction)
version of `dict_alif_draft.txt` from git history, since it was only sitting in an
now-unreachable commit. Net effect: we lost the ability to diff your `dict_alif`
corrections against the original draft. The corrected file itself is fine — only the
"what changed" view for that one file is gone.

**Lesson for later**: this history-rewrite trick only works *before* the first push.
Once something's pushed to a shared remote, removing large files from history needs
a proper rewrite tool (e.g. `git filter-repo`) and is riskier since anyone who
already pulled keeps the old history.

Also configured a Python `.env` file (gitignored, never committed) for API keys, so
future keys get typed into a file instead of pasted into chat.

---

## 2026-08-03/04 — Gold-set corrections: first real patterns

You started hand-correcting the OCR gold-set drafts (`data/gold/images/*_draft.txt`)
against the source page images. `dict_alif` and `gojri_adbiyaat` done so far
(`gojri_adbiyaat` in two rounds — a small kasra fix, then a larger pass).

**Finding, from the `gojri_adbiyaat` diff** (no diff available for `dict_alif` — see
the git mistake above):

1. **Heh confusion.** Urdu/Nastaliq has two different "h" letters that look similar:
   plain heh (ه) and do-chashmi heh (ھ, "two-eyed heh"), which marks aspirated sounds
   like دھ, بھ, مھ. The draft kept using the wrong one, e.g. `مانہ` → corrected to
   `مانھ`. This isn't cosmetic — it changes which consonant is represented.

2. **Poems don't get their own repetition checked.** A ghazal repeats the same
   rhyming word (the *radif*) at the end of every line. The draft mis-transcribed
   that repeated word *consistently but not identically* across lines:
   - `جایے` → `جائیے` (missing ئ), wrong in 4/4 lines
   - `ہن کے` → `بن کے` (ہ misread as ب), wrong in 4/4 lines
   - `یاں` → `یال` (nasalization ں misread as ل), wrong in 3/4 lines

   A person catches this instantly from the rhyme; the model transcribes each line
   independently and doesn't cross-check itself against the pattern it just produced
   two lines earlier.

3. **Confident wrong guesses on unusual/dialectal words** — e.g. `نچ`→`بِچ`,
   `چیُو`→`چپُو`, `کھڑیاں ہن کے`→`کھڈیال بن کے`. Fluent-looking Nastaliq, just wrong.
   This is the "hallucination" risk `CLAUDE.md` already flagged (**hallucination**:
   a model producing a plausible, fluent-sounding answer that isn't actually
   grounded in what's on the page — different from a traditional OCR engine failing
   visibly/blank when unsure).

---

## 2026-08-03/04 — First OCR model comparison: Gemini

**Goal**: start comparing OCR quality/cost across models — this entry is step one of
that, not a conclusion.

**Setup**: Got a Gemini API key (stored in `.env`, not committed). Checked Google's
own docs directly rather than trusting blog aggregators (they had wrong model names)
and confirmed the current lineup:
- `gemini-3.6-flash` — newest stable model, Google's own words: "our latest model...
  strong performance in agentic and multimodal tasks." **Flash** = Google's
  cheaper/faster tier, as opposed to **Pro** (more capable, more expensive).
- `gemini-2.5-pro` — current stable Pro tier (no newer Pro is out of preview yet).

Picked `gemini-3.6-flash`: it's both "latest" and the cost-sensitive choice, same
logic as the Haiku-vs-Sonnet tradeoff already in `CLAUDE.md`'s OCR cost math — for a
14,761-page OCR workload, cost tier matters as much as raw quality.

Wrote [scripts/gemini_ocr_test.py](scripts/gemini_ocr_test.py) — takes an image
path, sends it to Gemini with a transcription-only prompt (see exact prompt text in
the file), prints + saves the result as `<name>_gemini.txt` next to the draft.

**Result on `dict_alif.png`**:
- **Cost**: ~1,267 input tokens + 511 output tokens for one page. (**Token**: the
  unit models bill by — roughly a word-piece; a whole page of dense Nastaliq is
  ~1,000+ tokens because Perso-Arabic script tokenizes less efficiently than Latin
  script.) Comfortably inside Gemini's free tier.
- **Quality**: same heh-confusion bug as pattern #1 above (`آب و ھوا`→`آب و هوا`),
  plus dropped diacritics (kasra, damma). This is the *second* model showing the
  exact same failure mode — starting to look like a structural weak point of
  Nastaliq OCR in general, not a quirk of one model.
- Also added a bracketed `[Oval: Alif الف]` description not in the draft (needs a
  human check against the actual image — could be a legitimate catch or an
  invention) and a stray divider line.

**Open gap**: the `_draft.txt` baseline files don't have a recorded prompt (see
above), so they aren't a fully controlled comparison point yet. Fine for now since
we're mainly gut-checking quality, but worth fixing if we want rigorous scoring
later.

---

## 2026-08-04 — Planning: multi-model OCR comparison

**Plan going forward** (your call, recorded here for continuity): compare OCR output
across Gemini, DeepSeek, Claude Sonnet, and Claude Haiku on the same gold-set pages.
Reasoning: open-source/cheaper models are worth a real look before committing to a
paid-per-page pipeline for ~14,761 pages — no reason to assume the most expensive
option wins.

**Convention**: each model's output for a page goes in the same
`data/gold/images/` folder, named `<page_id>_<model>.txt` (e.g. `dict_alif_gemini.txt`,
already created). Once you've hand-corrected enough drafts into a true gold
standard, every model's output can be scored against the same yardstick.

Judgment on which model to actually use is explicitly deferred until the comparison
is in place — not being decided now.

**Started this log file.**

---

---

## 2026-08-04 — Formalizing the comparison: canonical prompt, file naming, run log

Found `prompts/ocr_transcription_v1.txt` (already written, not by me this session) —
a proper, detailed transcription prompt: explains Gojri-vs-Urdu up front, forbids
"fixing" spelling toward standard Urdu, defines `[single bracket]` for non-text
elements vs `[[double bracket]]` for a flagged best-guess on illegible text, handles
page numbers/headers, blank pages, and un-split spreads. This becomes **the one
prompt every model gets tested with** — fixes the "no reproducible prompt" gap noted
above. Re-ran the Gemini test on `dict_alif` with it (my first pass used a weaker,
improvised prompt) and ran it fresh on `gojri_adbiyaat`.

**File naming, finalized** — every gold page can now have, in `data/gold/images/`:
- `<id>_sonnet_5_original.txt` — the old, informal first-pass draft (no fixed prompt,
  read directly in a chat session), kept only where it still exists in git history.
- `<id>_sonnet_5_corrected.txt` — your hand-corrected gold standard, i.e. the
  ground truth every model's output gets judged against.
- `<id>_<model>_<version>.txt` — one per model tested with the canonical prompt,
  e.g. `dict_alif_gemini_3.6_flash.txt`.

**Recovered `gojri_adbiyaat`'s true original from git history** (`git show
f19a314:...`, before either correction round) — this one survived because it hadn't
been touched yet when the earlier `git gc` mistake happened. **`dict_alif`'s
original is confirmed permanently gone** — it was already corrected before this
session started, so its pre-correction text only ever lived in the commit that got
pruned. Only `dict_alif_sonnet_5_corrected.txt` exists for that page; there's no
`_original` counterpart and there can't be one.

**Sonnet 5 / Haiku 4.5 via chat, not API**: rather than issuing a new Anthropic API
key, these two will be run manually — a separate chat session per model, each given
the exact text of `prompts/ocr_transcription_v1.txt` plus the page image, output
pasted back and saved as `<id>_sonnet_5.txt` / `<id>_haiku_4.5.txt`. Still a fair
comparison as long as the prompt text is identical every time; the only thing lost
versus the API route is precise token/cost accounting for those two, which will be
recorded as "not tracked" in the run log rather than guessed at.

**New shared tooling**: [scripts/ocr_test_common.py](scripts/ocr_test_common.py)
holds the prompt-loading, output-naming, and run-logging logic shared by every
per-model test script, so results stay comparable as more models
(Gemini done, DeepSeek planned) get added.
[data/gold/ocr_runs_log.csv](data/gold/ocr_runs_log.csv) is a running,
structured log (timestamp, page, model, prompt version, token counts, output file)
of every automated test run — the raw material for eventually scoring models
quantitatively against the gold set, once enough pages are corrected.

**Observation worth tracking**: Gemini's reported `total_tokens` was noticeably
higher than `input + output` tokens added together (8,272 vs. 2,338 on one run).
Likely internal "thinking" tokens that get billed but aren't broken out in the
simple prompt/output counts — matters for the eventual cost math, needs the same
check on any Gemini "thinking" pricing details before trusting a simple estimate.

Also in progress in parallel, not yet pulled into the model comparison: you
corrected 3 more gold drafts (`louk_warsti`, `mahatma_gandhi`, `primer_pehli`).

---

---

## 2026-08-04 — DeepSeek checked, deferred

Checked DeepSeek's own API docs directly before assuming it'd slot into the
comparison like Gemini did: their general chat API (`deepseek-v4-flash`/`-pro`)
**does not support image input at all** — so it couldn't have run this test even as
a paid option. Separately, DeepSeek has released **DeepSeek-OCR** / **DeepSeek-OCR-2**,
an open-source (MIT-licensed) vision model built specifically for document/image
transcription — genuinely free either via community-hosted Hugging Face Space demos
(browser upload, no setup) or by running the open weights yourself on a free
Colab/Kaggle GPU. **Decision: skip DeepSeek for this round**, revisit later if
useful. Sticking with Gemini + Sonnet + Haiku for now.

---

---

## 2026-08-04 — Prompt versioning tightened; dict_alif original partially recovered

**Prompt v1 frozen, v2 created.** You'd substantially expanded
`prompts/ocr_transcription_v1.txt` in place (good additions: don't skip/repeat
similar dictionary lines, preserve Eastern vs. Western numerals as printed, transcribe
printed symbols/dingbats as content, ignore scan show-through, note stamps/handwriting,
a new rule for right-column/left-column paired layouts). Since two runs were already
logged against the old `v1` wording, editing it in place would have silently broken
the "same prompt across models" guarantee the whole comparison depends on. Split it
instead: `v1` stays frozen exactly as first used, the new rules are
`prompts/ocr_transcription_v2.txt`.

**Tooling updated to make this mistake structurally harder to repeat**: output
filenames and `ocr_runs_log.csv` now both carry the prompt version explicitly
(`<page>_<model>_<version>.txt`, e.g. `dict_alif_gemini_3.6_flash_v2.txt`) instead of
one bare filename that a future run could silently overwrite.

**Re-ran Gemini on both pages under v2.** Diff against v1 came back mostly minor
sampling variance (spacing, hyphenation, word order of the page-top label). One
genuine new issue, though: v2 misread the headword letter **ا** (alif) as the digit
**۱** (one) in `ا(alif)nm.A.1.` — the two characters are visually near-identical in
this script, and the new numeral-preservation rule may have made the model more
eager to read ambiguous marks as digits specifically. Small sample (2 pages), but a
concrete thing to watch for as more pages get tested under v2 — a prompt change
fixing one failure mode can introduce a different one.

**`dict_alif`'s original transcription, partially recovered.** You found and
confirmed one genuine original (mis-OCR'd) reading against the gold version:
headword `خُودرو` (correct) was originally misread as `ھُدرو`, with a duplicated
trailing `آپ` — a real example of the "don't repeat a line/word" failure the v2
prompt now explicitly guards against. Saved as
`data/gold/images/dict_alif_sonnet_5_original.txt`, seeded from the gold text with
just this one line reverted — **the rest of that file still matches the gold
version**, i.e. it is not yet a complete original, just the one confirmed
difference. Also cleaned up a duplicate `dict_alif_corrected.txt` that had
identical content to the existing `dict_alif_sonnet_5_corrected.txt`.

---

---

## 2026-08-04 — Reorganized gold-set storage: transcriptions/ per page

A separate session (see `plans/STAGE-1-TEST-BATCH.md`, a handoff briefing for
running the real 12-page Bedrock test batch) hit real friction with two competing
AWS CLI installs, and separately worked out that Claude Sonnet 5 needed a one-time
console enablement on Bedrock before its inference profile
(`us.anthropic.claude-sonnet-5`) would stop returning `AccessDeniedException`. That
session's plan calls for `boto3` directly (skips the CLI issue) and Haiku 4.5 +
Sonnet 5 (once enabled) as the two models for the batch.

Before running that batch, reorganized how gold-set files are stored — the flat
`data/gold/images/` folder was getting cluttered mixing `.png` images with every
model's `.txt` output for every page. New layout:
- `data/gold/images/` — page images only.
- `data/gold/transcriptions/<page_id>/` — one folder per page, holding `draft.txt`
  (the hand-corrected gold standard) plus every tested model's output, named
  `<model>_<prompt_version>.txt`.

Also dropped `<page>_sonnet_5_corrected.txt` (duplicate of `draft.txt`, no
information lost) and cleared `ocr_runs_log.csv` back to just its header, since its
old rows pointed at the now-moved file paths. Confirmed via `git status` before
touching anything that all the "removed" files were safe, recoverable
deletions already sitting in a prior commit — nothing was actually lost.

Upcoming Bedrock run naming, confirmed: append `_v1` even though this batch is
single-prompt-version, for consistency with the Gemini files; log all runs
(Gemini + upcoming Haiku/Sonnet) into the one shared `ocr_runs_log.csv` rather than
a second parallel CSV.

---

---

## 2026-08-04 — Dropped draft.txt as ground truth; wiped all transcriptions

Reconsidered the whole gold-set correction model. `draft.txt` (one file per page,
treated as "the" gold standard) was produced by Claude reading each image once with
no real, fixed, documented prompt — the same gap already noted earlier tonight. That
makes it a shaky baseline to score every model against, and conflates "what one
model produced" with "the truth."

**New approach**: no single ground-truth file per page. Instead, every model gets
its own raw output file (`<model>_<version>.txt`), generated under the same fixed
prompt, and correction happens per model, by hand, separately — comparing each
model's raw output against the source image rather than against another model's
output. This also captures a second useful signal beyond raw transcription quality:
how much correction effort each model's output actually needs.

**Wiped everything** in `data/gold/transcriptions/` — all `draft.txt`,
`sonnet_5_original.txt`, and the `gemini_3.6_flash_v1/v2.txt` files. All of it is
still recoverable from git history if needed later; starting genuinely fresh from
here. Updated `data/gold/README.md` to match. Correction-file naming/organization is
left to the user's own process, not something Claude generates.

---

---

## 2026-08-04 — Bedrock smoke test: real blockers, real quality concerns, one caught bug

**AWS setup**: `boto3` installed. First `dict_alif` call to Haiku 4.5 failed with
`ResourceNotFoundException: Model use case details have not been submitted` — a
one-time, Anthropic-specific account requirement on Bedrock, separate from the
model-access toggle already done for Sonnet 5. Confirmed it's Anthropic-specific
(not account-wide) by running Qwen3-VL in the same session, which worked
immediately. Form submitted, Haiku unblocked after.

**Request format decided**: both Haiku 4.5 and Qwen3-VL support Bedrock's unified
Converse API with images, so one script (`scripts/bedrock_ocr_test.py`) handles both
via a shared code path — image bytes passed raw (not base64, unlike the
`invoke_model`/Anthropic-specific format the original plan assumed).

**Smoke test on `dict_alif` (cropped, v1 prompt) — both models showed real quality
problems, in different ways**:
- Qwen3-VL: character-order corruption in places (`فلف` instead of `الف`,
  `اياكو فل فيقيح` instead of `ایکو الف حقیقی`) — looks like scrambling, not just
  missing marks.
- Haiku 4.5: repeatedly substituted a generic `ئ` placeholder in place of several
  different actual headwords, rather than attempting to read them.

Both are worse than the diacritic-drop/heh-confusion pattern seen earlier from
Gemini and the original Sonnet draft. Decided not to over-read this from one page —
`dict_alif` has unusually small, dense headwords and may be a harder case than the
other 11 pages. Plan: run the full 12-page batch for both models before judging.

**Bug caught and fixed**: added a `stop_reason` column to the shared run-log schema
in `ocr_test_common.py`, but `log_run()` only writes a header for a brand-new file —
since `ocr_runs_log.csv` already existed (header-only, from the earlier wipe), it
kept the *old* 8-column header while new rows wrote 9 columns. Caught by manually
re-verifying the log matched what was actually sent, after being asked directly
whether v1 was really being used. Fixed by hand-correcting the header; no schema
migration logic was worth adding for a CSV this size, but a lesson worth keeping:
verify by reading the actual artifact, not by trusting that code ran the way it was
written to.

**Model catalog research, for later reference**: confirmed via AWS's own model
cards (not the console's summary blurbs, which have twice now omitted real
capabilities — Claude and Llama 4 both show as text-only in some console list views
despite genuinely supporting images) that Llama 4 Maverick supports image input +
Converse API, but needs the cross-region ID (`us.meta.llama4-maverick-17b-instruct-v1:0`)
since it's not available in-region for `us-east-1`. Also identified Pixtral Large,
Kimi K2.5, and NVIDIA Nemotron Nano 12B v2 VL as genuinely OCR-relevant candidates
if more models are wanted later; ruled out Stability AI (image generation, not
understanding), TwelveLabs (video embeddings), and Gemma (the only multimodal
variant on Bedrock is the base/pretrained "PT" model, not instruction-tuned, so it
won't reliably follow a transcription prompt).

---

---

## 2026-08-04 — Settings weren't controlled at all; fixed, logged, re-ran, verdict unchanged

Asked directly: "which settings are you running these models with? Is thinking on?
Is effort High?" Honest answer at the time: none of that had been explicitly set —
the Bedrock `converse()` calls only passed `modelId` and `messages`, nothing else.
Real gap, worth researching properly rather than guessing.

**Findings, checked against AWS's/Google's own docs, not assumed:**
- Claude's extended thinking is opt-in — off unless explicitly requested. It was off.
- **Haiku 4.5 doesn't support the adaptive-thinking/effort parameter at all** —
  confirmed against AWS's own docs; that feature is limited to Opus 4.6+/5-tier and
  Sonnet 4.6. "Is effort High?" doesn't apply to Haiku 4.5 as a question.
- Temperature was never set, so it used the API default (1.0 for Claude/Anthropic —
  non-deterministic sampling, a bad fit for an exact-copy task).
- **Gemini is the opposite case**: Google's own Gemini 3 docs explicitly warn
  *against* changing temperature from its default of 1.0 ("may cause looping or
  degraded performance"). So the three models now deliberately use *different*
  settings, not matched ones — Claude/Qwen get `temperature=0`, Gemini keeps its
  default — and that asymmetry is logged explicitly rather than left implicit.
- Gemini 3.6 Flash's own default `thinking_level` is already `"minimal"`, i.e.
  close to what an OCR task wants anyway.

**Built proper settings logging**, per direct request: every script now echoes the
exact prompt file path + full prompt text to console before calling, prints the
exact model ID/temperature/max_tokens/thinking config being sent
(`print_call_settings` in `ocr_test_common.py`), and logs all of it to
`ocr_runs_log.csv` (new columns: `temperature`, `max_tokens_requested`, `thinking`,
`extra_settings`). Also fixed: output filenames now include the page ID
(`dict_alif_haiku_4.5_v1.txt`, not just `haiku_4.5_v1.txt`), and a copy-paste bug
where the Qwen3-VL rows' `thinking` column incorrectly cited Haiku-specific wording.

**Re-ran `dict_alif` + `gojri_adbiyaat` on Haiku 4.5 and Qwen3-VL with temperature=0,
plus `dict_alif` on Gemini, fresh** (old, unconfigured-settings smoke-test rows and
files deleted rather than kept, since they're fully superseded).

**Result: temperature=0 did not fix the quality problem.** Haiku 4.5 still
substitutes placeholder characters for headwords it can't read (this time `Ī`, a
Latin letter that isn't even valid in this script — a different placeholder than the
earlier smoke test's `ئ`, meaning it's not a fixed/deterministic substitution
either). Qwen3-VL still shows the same character-order corruption pattern. This
points away from "unlucky high-temperature sampling" as the explanation and toward
a genuine capability gap on this specific page's small, dense headwords, at least
for these two models.

**Gemini's result on the same page, same settings-rigor, is a clean pass** —
correctly transcribed headwords throughout (`آپ ہُدرو` matches the known-correct
reading exactly), no placeholder substitutions. Also **directly confirms an earlier
open question**: with `thinking_level=low` explicitly set, Gemini's `total_tokens`
now exactly equals `input + output` (no more of the unexplained gap noted on
2026-08-04 earlier — "total_tokens noticeably higher than input+output" — that was
the model thinking by default, now resolved).

Scope held to these 2 pages only, per instruction — not extending to the full 12
until this is understood.

---

---

## 2026-08-04 — Haiku 4.5 and Qwen3-VL shelved

Both failed on both test pages (`dict_alif`, `gojri_adbiyaat`), under identical,
controlled conditions (same cropped images, same v1 prompt, temperature=0, logged
settings) where Gemini 3.6 Flash succeeded on the exact same inputs — so this isn't
a settings, prompt, or image-quality issue, it's the models themselves. Decision:
**stop using both going forward.** Full outputs preserved for the record in
`data/gold/transcriptions_archived/<page_id>/` rather than deleted, so the evidence
stays available if this ever needs revisiting.

**Concrete examples, `gojri_adbiyaat` (correct reading known from earlier hand
correction, before the file was later wiped from the working copy):**

| Correct | Haiku 4.5 | Qwen3-VL |
|---|---|---|
| `وِچ چھوڑا کے عمر گزری، دتو تیں نہ کدے دیدار مِناں` | `ویچ ویڑھو کے عم گردی، ڑو تھیں یک کے دھار دھیال` | *(not tested on this exact line)* |
| `جان میری تیرے باجھ چلی سجنا لائی پریت نا توڑئیے نہ` | `جان میری تھیرے پاچھے جھلی پیت تونے ند` | `جان میری تیرے باجھ چلی بیتا لائی پریت نا توڑے نہ` |

Haiku's first example isn't a near-miss with a few wrong diacritics — most of the
words are simply different. Qwen3-VL's second example is structurally closer (right
number of words, right general shape) but still swaps real words (`سجنا`→`بیتا`)
and drops the recurring `-ئیے` radif ending the same way the very first, informal
Sonnet draft did back at the start of this project — that specific ligature
(hamza-bearing yeh in a verb ending) seems to be a genuinely hard case across
multiple models now, not just one.

**`dict_alif` (dictionary layout) — different failure shape entirely**: both models
substitute a placeholder character for headwords they can't read, rather than
attempting a (possibly wrong) reading. Haiku used `ئ` in the first smoke test and
`Ī` — not even a character that belongs in this script — in the controlled rerun of
the identical page. Not a consistent substitution, which suggests genuine
uncertainty/failure rather than a deterministic quirk.

**Kept**: Gemini 3.6 Flash, the only model so far that's transcribed both pages
correctly under matched conditions.

**Next**: test Kimi K2.5 and one more model (still deciding which) before moving to
Sonnet 5, per updated plan.

---

---

## 2026-08-04 — Kimi K2.5, Llama 4 Maverick, Pixtral Large tested

Verified all three against their actual AWS model cards before running anything
(same discipline as Qwen3-VL/Llama 4 earlier) — all three support image input via
the Converse API. Kimi K2.5 (`moonshotai.kimi-k2.5`) is in-region for `us-east-1`;
Llama 4 Maverick and Pixtral Large both need the cross-region ID
(`us.meta.llama4-maverick-17b-instruct-v1:0`,
`us.mistral.pixtral-large-2502-v1:0`) since neither is available in-region here.
Same settings discipline as before: temperature=0, explicit max_tokens, no
thinking, all logged.

**Kimi K2.5 — the best non-Gemini result so far.** On `dict_alif`, it correctly
read `آپ خُودرو` (matches the known-correct gold reading exactly) where every other
non-Gemini model tested has gotten this specific entry wrong. No placeholder-
character substitutions anywhere in either page. Still has real, ordinary OCR
errors (missing/wrong diacritics, occasional wrong word), but nothing like the
severity seen from Haiku/Qwen3-VL. Worth carrying forward as a real candidate.

**Llama 4 Maverick — mixed, closer to Haiku's failure mode than Kimi's.**
Still substitutes a placeholder (`˜`, a tilde, twice on `dict_alif`) for headwords
it can't read, and mangles some phrases significantly. Notably more expensive too:
~4,520 input tokens per page vs. ~1,450-1,800 for every other model tested on the
same cropped images — its image tokenization is markedly less efficient. Not ruled
out yet, but the weakest of the three new candidates.

**Pixtral Large — a worse failure than anything seen yet, and a different kind of
danger.** On `dict_alif` it invented fabricated example sentences not on the page
(`آپنے گھوڑے کو کیا نام رکھا؟` — "What did you name your horse?" — pure invention)
and appended a stray ` ``` ` markdown fence, violating the prompt's explicit
plain-text-only rule. On `gojri_adbiyaat` it did something much worse: **produced
an entirely fabricated, fluent, coherent Urdu parable about a boy refusing food, a
sadhu searching for a cow, and a monkey eating fruit — none of which has anything
to do with the actual poem on the page.** This is exactly the "confident-but-wrong"
hallucination risk flagged early in this project (`CLAUDE.md`'s OCR pipeline plan,
point 7): Tesseract-style engines fail visibly; this failed by inventing plausible,
complete, unrelated content. Arguably more dangerous than Haiku/Qwen3-VL's garbling,
since a less careful review pass could mistake fluent invented prose for a real
(if imperfect) transcription. **Recommending this one be shelved too** — flagging
for confirmation rather than deciding unilaterally, given how much this changes the
picture, but the evidence is strong.

**Cost note**: token usage varies a lot by model on the *identical* cropped image —
Kimi ~1,764 input tokens/page, Pixtral ~3,439, Llama 4 Maverick ~4,520. Image
tokenization efficiency isn't uniform across providers, which will matter for the
eventual 14,550-page cost extrapolation regardless of which model(s) get chosen.

---

---

## 2026-08-04 — Pixtral Large and Llama 4 Maverick shelved

Same process as Haiku 4.5/Qwen3-VL: outputs archived to
`data/gold/transcriptions_archived/<page_id>/` rather than deleted, reasons
documented here with examples, both stop being used going forward.

**Pixtral Large**: shelved for fabrication, not just inaccuracy — on
`dict_alif` it invented an example sentence not on the page
(`آپنے گھوڑے کو کیا نام رکھا؟`, "What did you name your horse?") and appended a
stray markdown code fence; on `gojri_adbiyaat` it produced a complete, fluent,
entirely fabricated Urdu parable (a boy refusing food, a sadhu searching for a
cow, a monkey eating fruit) with no connection to the actual poem on the page.
Confident, coherent, and wrong is a worse failure mode for this project than
visible garbling — it's exactly the silent-hallucination risk flagged early on in
`CLAUDE.md`.

**Llama 4 Maverick**: shelved for the same placeholder-substitution pattern as
Haiku (`˜` in place of unreadable headwords on `dict_alif`) plus a practical cost
problem — it used ~4,520 input tokens per page on the identical cropped image that
Kimi K2.5 processed in ~1,764, roughly 2.5x more expensive for a weaker result.

**Currently active candidates**: Gemini 3.6 Flash (clean on both pages tested) and
Kimi K2.5 (best non-Gemini result, no placeholder failures). Sonnet 5 still pending
as the next test.

---

---

## 2026-08-04 — DeepSeek-OCR: tried, hit a real dead end (for now)

Wanted to try `deepseek-ai/DeepSeek-OCR` (open-source, MIT-licensed, OCR-specialized
vision model — first surfaced when researching DeepSeek earlier). Checked properly
rather than assume it'd just work:

- **No Hugging Face MCP tool available in this session** — checked directly via
  `ListMcpResourcesTool`; only Firebase and an Indeed connector are actually
  configured here, despite HF MCP apparently being set up somewhere else.
- **No official Hugging Face Inference Provider for this model** — its own model
  page states plainly: "This model isn't deployed by any Inference Provider."
- **Not on Bedrock either** — Bedrock's DeepSeek offering is limited to
  `DeepSeek V3.2`/`V3.1`/`R1`, the same text-only chat/reasoning models already
  confirmed to lack image support. DeepSeek-OCR is a separate project Bedrock
  doesn't host.
- **Community Gradio Spaces**: found a working, callable API on
  `prithivMLmods/DeepSeek-OCR-experimental` (confirmed via `gradio_client`'s
  `view_api()` — schema loaded cleanly). But actually calling it failed with an
  opaque server-side `AppError` every time: with and without HF auth (user added
  `HUGGING_FACE_ACCESS_TOKEN` to `.env` specifically to test this), across two
  different task modes (`Free OCR`, `Convert to Markdown`). A second Space
  (`khang119966/DeepSeek-OCR-DEMO`) failed identically; a third
  (`akhaliq/DeepSeek-OCR`) was outright broken (`RUNTIME_ERROR` state). Checked the
  working Space's actual source (`app.py`) rather than keep guessing blindly — the
  OCR function is decorated `@spaces.GPU`, Hugging Face's shared "ZeroGPU"
  allocation system, which has its own quotas/reliability issues independent of
  anything on our side. Also worth noting even if it had worked: this demo's API
  has no field for a custom prompt at all, only fixed built-in task modes - it
  could never have taken our canonical v1 prompt, so even a successful run
  wouldn't have been a controlled, comparable data point the way every other model
  tested has been.

**Conclusion**: not pursuing the free-community-Space route further. The
self-hosted route (Colab/Kaggle free GPU, full prompt control) discussed earlier
remains the only way to properly evaluate DeepSeek-OCR for this project, and is a
real chunk of setup work, not a quick check - shelved as a "maybe later," not
tested, not ruled out on merit.

**Follow-up same day**: pushed on this rather than dropping it - checked for a
local GPU first (none: no `nvidia-smi`, no CUDA), then built
`notebooks/deepseek_ocr_colab.ipynb` (generated via
`scripts/build_deepseek_ocr_notebook.py`, so the long prompt string gets JSON-escaped
correctly rather than hand-typed into notebook JSON). Verified against the actual
model card rather than guessed: DeepSeek-OCR is 3B params (comfortably fits a free
Colab T4's 16GB VRAM in bfloat16), loads via `transformers` with
`trust_remote_code=True`, and — importantly, unlike the Gradio demos — its real
prompt format is `"<image>\n"` + free-text instruction, so **the full v1 prompt can
actually be sent**, making this a genuinely controlled, comparable run if it works.
Includes a fallback to eager attention if `flash-attn` fails to build, a common
Colab pain point. I can't execute this myself (no browser/notebook-execution
access) - the user runs it in their own free Colab account and pastes results
back, same pattern as the manual Sonnet/Haiku chat-session runs.

---

---

## 2026-08-05 — Documentation sync pass after the "datasets/" reorg

User reorganized dataset folders (`Gojri Language Corpus/` and `cv-corpus-.../` now
under `datasets/`; `PDFs/` lowercased to `pdfs/`) and asked for docs to be
updated. Surveyed every tracked file for stale path references rather than
guessing which ones mattered - found and fixed:
- `CLAUDE.md`, `ROADMAP.md`, `plans/STAGE-0.md`: path references to the old
  locations (7 spots across the three files).
- `scripts/build_manifest.py`, `scripts/build_gold_candidates.py`,
  `scripts/split_spread.py`: hardcoded `PDF_DIR`/default-arg references to `PDFs`
  (still worked on Windows due to case-insensitive filesystem lookups, but wrong
  and would break on a case-sensitive one - fixed for correctness, not just
  because something was broken).
- `.gitignore`: `/PDFs/` → `/pdfs/` (same case-insensitivity caveat).
- `data/gold/candidates.csv`: the `image` column still pointed at
  `data/gold/images/` (pre-crop originals) even though every OCR call has used
  `data/gold/images_cropped/` since that decision. Genuine functional staleness,
  not just cosmetic - a future session following this CSV naively would've used
  the wrong, more expensive images. Fixed, and added a note to
  `build_gold_candidates.py`'s docstring since re-running it would regenerate the
  CSV pointing at the uncropped originals again.
- `plans/STAGE-1-TEST-BATCH.md`: this handoff plan (written by a separate session)
  had drifted well beyond just paths - file naming convention, settings-logging
  addition, and the whole model roster (Gemini/Kimi active, four models shelved,
  Sonnet 5 pending) all postdate it. Added a status-update block at the top
  pointing to `LOG.md` rather than rewriting the whole plan, since the
  methodology/background sections are still accurate.
- `data/gold/README.md`: added `images_cropped/` and `transcriptions_archived/` to
  the documented layout (both existed but weren't described), fixed the
  transcription filename example to include the page ID, and updated the
  "why this matters" recap to name actual current model status instead of a
  generic "Gemini, Haiku, Sonnet" list.

---

## 2026-08-05 — GPT ruled out; Sonnet 5 blocked on AWS Sales; Sonnet 4.6 standing in; CloudWatch logging set up

**GPT considered for the comparison, ruled out.** Checked directly against Bedrock
(`list-foundation-models`) rather than assuming: the only OpenAI models on Bedrock
are the open-weight `gpt-oss-120b`/`20b` (+ `-safeguard` variants), which are
**text-only, no image input modality**. The actual vision-capable GPT models
(GPT-4o/4.1/5) aren't on Bedrock at all, only via OpenAI's own API or Azure OpenAI.
Can't do OCR through Bedrock with GPT — skipped.

**Sonnet 5 access — a real saga, still unresolved.** `anthropic.claude-sonnet-5`
appears in the account's model catalog but every invocation returned
`AccessDeniedException`, worded differently from the ordinary "model access not
enabled" error: *"...contact AWS Sales."* Chased this properly rather than assuming
it was unfixable:
- AWS retired the old "Model access" console page; access is now self-service via
  IAM + a one-time `PutUseCaseForModelAccess` API call for Anthropic models.
- First attempt at that API failed validation repeatedly — turned out `intendedUsers`
  must be the literal string `"0"`/`"1"`/`"2"` (Internal/External/Both), not a
  free-text description, per AWS's own SDK docs (not obvious from the API reference
  alone, which only documents `formData` as an opaque blob).
- Ran the full documented flow: `ListFoundationModelAgreementOffers` →
  `PutUseCaseForModelAccess` (corrected schema, succeeded) →
  `CreateFoundationModelAgreement` → `GetFoundationModelAvailability`. End state:
  **every status field reports `AVAILABLE`/`AUTHORIZED`**
  (`agreementAvailability`, `authorizationStatus`, `entitlementAvailability`,
  `regionAvailability` all green) — yet `Converse` still returns the identical
  Sales-gated `AccessDeniedException`. Confirms this is a genuine Sales-only gate,
  not a missed self-service step; the self-service path is fully exhausted.
- **Decision: emailed AWS Sales** (`aws.amazon.com/contact-us/sales-support`) with
  the account ID, model ID, and this exact evidence trail. Response pending —
  **Sonnet 5 is deferred until access clears**, not abandoned.
- **Standing in: Sonnet 4.6** (`us.anthropic.claude-sonnet-4-6`, cross-region
  profile — the plain `anthropic.claude-sonnet-4-6` ID fails since it needs
  provisioned throughput, not on-demand). No access gate, works immediately.

**Ran Sonnet 4.6 on both gold pages, plus filled a gap**: `gojri_adbiyaat` was
missing a Gemini v1 run (had Kimi only). Both folders now hold exactly 3 files each
(Kimi K2.5, Gemini 3.6 Flash, Sonnet 4.6, all `_v1`), ready for your review pass.
Added `sonnet_4.6` to `bedrock_ocr_test.py`'s `MODELS`/`THINKING_NOTES` dicts
(thinking left off, same as every other model tested, even though Sonnet 4.6 does
support adaptive-thinking/effort).

**Side quest: AWS account hygiene**, prompted by working through the Sonnet 5 access
flow:
- Set up **Bedrock model invocation logging** to CloudWatch (`bedrock-logs-role`,
  log group `/aws/bedrock/model-invocations`) — hit and fixed two real
  misconfigurations along the way (trust policy vs. permissions policy pointing at
  the wrong log group name; the log group not existing yet). Confirmed live via
  `get-model-invocation-logging-configuration`.
- Confirmed `ai_agent_user` (the identity all these scripts run as) has **no IAM
  permissions at all** — deliberately scoped to Bedrock only, confirmed by testing
  (every `iam:*` call denied). Recommended, and user is trimming, its 9 attached
  AWS-managed policies down to 2 (`AmazonBedrockFullAccess` +
  `AmazonBedrockMarketplaceAccess`, the only ones anything this session actually
  used) — the rest (AgentCore, Web Search, DataZone policies) were unused surface
  area.
- User separately cancelled a Sonnet 4.5 subscription by hand (a different tangent
  from earlier in the session, now moot — no deny policy needed).

---

## 2026-08-05 — Cross-model correction converges the gold text; Kimi's verdict revised; file convention fixed

**Correction workflow used, worked well**: you hand-corrected Gemini's and Sonnet
4.6's outputs on both gold pages *independently* (each against the source image,
without looking at the other model's correction). Comparing the two afterward
turned out to be a genuinely useful technique, not just a formality — where two
independently-corrected versions of the same page agree, that's strong evidence
it's actually right; where they disagree, that's a real remaining ambiguity worth a
second look at the image, not noise. This is the practical version of the
**ensembling** idea (independent samples converging on the truth more reliably than
any single one) that came up when you asked about re-prompting for a second pass —
see below.

**`gojri_adbiyaat`: fully converged.** Started with 7 real word/diacritic-level
disagreements between the two corrected versions (not counting pure spacing/line-
break differences). Resolved all 7 against the source image:
- `تڑفتا نا` (not `تڑفا نا`), `کچر دو ہلتا` (not `کچڑ دوہلتا`), `پھرنہ ایویں` (not
  `پھرنا ایویں`) — real word-level fixes, not diacritics.
- `کچرتک`→`کچر تک` and `گوہوں`→`گو ہوں` — two words, written closely together on
  the page (a real spacing decision, not visible from the text alone).
- `چارو کار`→`چاروکار` and `کومار`→`کو مار` — the opposite spacing call on two
  *other* close-set word pairs. Notable: spacing on tightly-kerned Nastaliq word
  pairs isn't a consistent rule you can guess at from general knowledge of the
  script — each pair needed an actual look at the image.
- Kasra confirmed absent on `پرواز` (Sonnet's corrected version had incorrectly
  added one).
- `و: مولوی غلام رسول ڈوئی` confirmed as one line, not two — a line-break question,
  not a word-content one.

End state: **27 of 27 content lines now word-for-word identical** between Gemini's
and Sonnet's independently-corrected versions of this page. One cosmetic difference
remains (tab vs. spaces in the header line), left unresolved as genuinely trivial.

**`dict_alif`: now converged down to 2 trivial single-space questions.** Resolved
across two follow-up rounds:
- Word order `الف ، ا` (not `ا ،الف`); `تاں` (not `تان`); `چھاں` (not `چھان`).
- `بدھیکی` (do-chashmi `ھ`), confirmed by you directly. Same letter pair as the
  already-resolved `ھُدرو`/`هُدرو` case (U+06BE vs U+0647 — verified by pulling
  exact codepoints, not eyeballing it), now settled on **two separate words on
  this page**, both correctly do-chashmi. Linguistically this isn't a stylistic
  choice: do-chashmi heh specifically marks aspiration (`دھ`, `بھ`, `تھ`, `کھ`,
  `پھ`), a real phonetic feature plain Arabic heh doesn't encode.
- **`eg:`/`lpp:` prefix placement — checked directly against the source image**,
  not inferred from the text alone. The `lpp:` line settles it unambiguously: `lpp:`
  sits at the visual right (read first in the page's right-to-left flow), the Gojri
  proverb in the middle, `To invite trouble.` at the far left (read last) — and
  Sonnet's version already matched this exactly, while Gemini's had the order
  flipped *and* was missing `To invite trouble.` entirely. Same structural logic
  (a label must precede what it introduces) applies to the `eg:` line and the
  second `eg: lpp:` occurrence later on the page. Fixed all three spots in Gemini's
  corrected file to match.
- Two more spacing questions resolved from the same image check, lower confidence
  but reasonably clear: `آبش` is one word (not `آ بش`); `چنگا تے` is two words
  (not `چنگاتے`).

**Both remaining items resolved — turned out to be a scope question, not an
ambiguity.** Both disputed spaces were between Gojri text and an *English*
annotation (`آپ` vs `(aap)`; `head-strong.` vs `اپ ھُدرو`), not between two Gojri
words. **New standing rule, given directly, worth keeping for every future page**:
spacing around English glosses/transliterations isn't a correction concern —
only spacing *between Gojri words* carries real meaning and is worth the effort to
verify against the image. On the actual Gojri content: `آپ` is confirmed one word,
`اپ ھُدرو` confirmed two words — both files already had this right. **`dict_alif`
is therefore fully converged**, same as `gojri_adbiyaat`, no content-level
disagreement left on either gold page tested so far. Files intentionally left as-is
(differing only in the out-of-scope English-adjacent spacing) rather than forced
to match, since forcing a false match isn't the goal — not disagreeing on anything
that matters is.

**One heh-confusion case fully settled, worth recording since it's recurred across
multiple models now**: on the `آپ خُودرو` dictionary entry, do-chashmi heh (`ھ`,
two-eyed heh, marks aspiration) is the correct reading for the trailing `اپ ھُدرو`,
not plain heh (`ه`/`ہ`). Gemini, Sonnet 4.6, *and* Kimi K2.5 (see below) all
independently got this specific letter wrong before correction — the clearest single
piece of evidence yet that this specific ligature is a genuine, repeated model
weakness, not an isolated slip by one model.

**Kimi K2.5 checked against the now-converged gold text — revises the earlier
verdict, and not in Kimi's favor.** The 2026-08-04 entry called Kimi "the best
non-Gemini result so far," but that was based on one overlapping dictionary entry,
not a full-page comparison against a real, doubly-confirmed gold standard. With one
now available:
- **`dict_alif`: still holds up reasonably.** The specific `آپ خُودرو` headword
  read that the earlier entry praised is still correct. New finding from the full-page
  diff: a real, repeated **ک (kaf) for گ (gaf) substitution, six times on one
  page** (`لک`×3 for `لگ`; `چنکا`/`جک`/`چنکو` for `چنگا`/`جگ`/`چنگو`) — systematic,
  not scattered noise, and not something the earlier single-entry spot-check could
  have caught.
- **`gojri_adbiyaat`: substantially worse than the earlier verdict implied.**
  Real word substitutions throughout, not just dropped diacritics:
  `عرض` ("plea") misread as `عرش` ("throne") twice, consistently; the recurring
  nasalized `ں` ending misread almost everywhere (`مِناں`→`منان`,
  `کھڈیال`→`کڈیاں`, `بھیال`→`بھیاں`); and — notably — Gojri's distinctive `-و`
  word ending repeatedly normalized toward Urdu's `-ے` (`میرو`→`میرے`,
  `تیرا`→`تیرے`), which is exactly the failure mode the canonical prompt's rule 3
  explicitly warns against. Also got two proper nouns/titles wrong (`ڈاکٹر`
  ["Doctor"] misread as `ذاکر`, a name; `ڈوئی`→`ڈولی`).
- **Your read, after seeing this**: Kimi isn't right for this comparison. **Decision:
  Kimi K2.5 shelved** — moved to `transcriptions_archived/` (both pages'
  `_original.txt`, never corrected, kept for the record like the other shelved
  models), same treatment as Haiku 4.5/Qwen3-VL/Llama 4 Maverick/Pixtral Large
  earlier. Not used going forward.
- **Practical implication, for the record even though Kimi's shelved now**: its
  quality wasn't uniform across genres — solid dictionary-layout OCR, weak poetry
  OCR. Worth remembering generally that the 14,761-page
  workload isn't one genre, so a single averaged verdict per model may not be the
  right way to pick a model going forward.

**Original-vs-corrected effort, quantified** (line-level diff count, raw model
output → final corrected text):

| Page | Gemini 3.6 Flash | Sonnet 4.6 |
|---|---|---|
| `dict_alif` | ~5 line-edits | ~9 line-edits |
| `gojri_adbiyaat` | ~14 line-edits | ~14 line-edits |

Gemini needed less correction on `dict_alif` specifically (mostly one typo);
Sonnet needed a real word swap and a duplicated/misordered entry on top of the same
diacritic drops. Roughly equal effort on `gojri_adbiyaat` for both, and — more
interesting than the raw count — both models independently landed on the *same*
correct reading for several genuinely hard spots (the `ھُدرو` heh, `پھرنہ`) without
being told, which is a real (if small-sample) positive signal for both.

**Re-prompting / few-shot, discussed, deferred for now.** Simply re-running the
identical prompt on the same model again isn't a real strategy here — Sonnet runs
at `temperature=0` (won't meaningfully vary between runs) and Gemini's variation
(kept at its own default, per the 2026-08-04 entry) is uncontrolled luck, not a
technique. What *did* work, concretely, is what this session just did by hand:
comparing independently-corrected outputs from two different models and trusting
convergence — a real instance of **ensembling**. **Few-shot prompting** (embedding
1-2 worked image+correct-transcription examples directly in the prompt, distinct
from both of the above) is a genuinely different idea worth testing once there's
more corrected gold data to draw a fair example from — **decision: revisit once
more pages are corrected**, not now, and any test needs the few-shot example to be
a *different* page than the one being scored, or it's not a real test.

**File convention fixed, going forward**: corrections were being made *in place*
(overwriting the raw model output), which meant the true original could only be
recovered via `git show` against the last commit before correction started — worked
this time only because the raw outputs happened to have just been committed.
**Changed**: every page/model now gets two separate files —
`<page>_<model>_<version>_original.txt` (raw, from the automated test scripts,
never hand-edited — `ocr_test_common.py`'s `output_path()` now enforces the
`_original` suffix automatically) and `<page>_<model>_<version>_corrected.txt`
(hand correction, added separately, only once review is actually done). Applied
retroactively to all 3 active models on both gold pages tested so far — recovered
the 4 Gemini/Sonnet originals from git history, renamed the corrected files, and
renamed Kimi's still-uncorrected file to `_original` (it was already the original,
nothing to split).

---

## 2026-08-06 — kahawat_kosh + gojri_ghazal: raw runs, gojri_ghazal fully converged

Ran Gemini 3.6 Flash and Sonnet 4.6 on the next two gold pages, same v1 prompt.
`ocr_test_common.py`'s `_original` suffix fix worked as intended - both models'
raw output on both pages saved correctly with no manual naming needed.

**The in-place-edit mistake recurred on `gojri_ghazal`**, despite the fix - you
corrected both models' output by editing the `_original.txt` files directly rather
than saving separate `_corrected.txt` copies. Caught before anything was committed,
so recovered cleanly: `cp`'d the current (corrected) content to new `_corrected.txt`
files first, then restored true raw content into `_original.txt` from the last
commit (`50b15e8`), verified byte-identical after restoring. No data lost, but
worth noting the convention needs a human habit change, not just a tooling fix - the
tooling only controls what the *scripts* write, not what gets edited afterward.

**Correction converged in two rounds**, same cross-model-comparison method as the
first two pages. First round (checked directly against the source image, mix of
high- and lower-confidence calls): resolved `بیہویں`, `ہویو`, `مہارے` (goal heh,
not do-chashmi - a *third* distinct heh-pair now seen in this project, see
Glossary), `ہوگیوتے`, `سینہ باسینہ`, `یا وی ہے` word order, `ہوتو ہے جو` word
order, `کمیاب`, `تیجویوہ`, `کرکے`, `اپنو`, `گزرن`, `کرلیتا۔`, and `مہر الدین`
spacing - brought 27 word-level diffs down to 10, with several (`نام`/`نال`,
`جووی`/`جوی`, `پہچیو`/`پچہیو`, etc.) genuinely too fine to call from the image and
flagged rather than guessed at.

**Second round, resolved directly by you**: all 9 remaining items, including the
most interesting one - **`نامل نال` (both words together), not `نام` alone or
`نال` alone** as either model had it independently. Neither model's correction
had actually gotten this right; the real reading was a third option neither one
landed on, which the cross-model-comparison method can't surface by itself (it
only catches cases where the two disagree, not cases where both are
independently wrong in different ways) - a real limitation of the method worth
remembering. Also: the `قمّر`/`قمر` mark turned out not to actually be a tashdid
(shadda) as I'd assumed from the codepoint alone - you flagged it as "a different
sign," and the interim call is to drop it until it's properly identified, rather
than keep guessing at what it actually is.

**`gojri_ghazal` now fully converged - 0 remaining word-level differences**
between the two corrected files. All three gold pages tested so far
(`dict_alif`, `gojri_adbiyaat`, `gojri_ghazal`) are now fully converged.

---

## 2026-08-07 — kahawat_kosh corrected and converged; punctuation-spacing rule added

**Same in-place-edit mistake a third time**, on `kahawat_kosh` this round -
recovered the same way as `gojri_ghazal` (not committed yet, so no data lost;
`cp`'d current content to `_corrected.txt`, restored true raw content into
`_original.txt` from commit `50b15e8`, verified byte-identical). This is now a
consistent pattern across every page corrected since the convention was
introduced - the tooling fix only controls what the scripts *write*, not what
gets edited after the fact, so this is a habit thing on the correction side,
not something further tooling changes can fully prevent by itself.

**New scope rule, extending the earlier English-adjacent-spacing exception**:
this page's tight two-column proverb-layout typesetting produced a lot of
disagreement in *punctuation* spacing specifically - space before `:`/`،`/`۔`
or not - applied consistently by each model but differently from each other.
19 of the initial 34 word-level diffs were exactly this, no real content
involved. **Decision: punctuation spacing joins English-adjacent spacing as
"not a correction concern"** - only spacing between two actual Gojri words
still matters.

**Real content converged in two rounds.** First round (checked against the
source image myself): resolved one item confidently (`پک`→`پگ` on the
`شملومیلو` entry, an internal inconsistency within Gemini's own output - it
used `پگ` correctly on the two preceding entries - same ک/گ confusion pattern
already documented from Kimi's `dict_alif` errors). This page's typesetting is
markedly harder to read at the working image resolution than the previous
three pages, so the rest (18 items) were flagged rather than guessed at.

**Second round, resolved directly by you.** Notably, the very first entry's
correct reading (`پُتر اکھوہ پو، دبکار سُناں`) matched *neither* model's
correction exactly - a third reading combining elements of both, same
limitation of the cross-model-comparison method already seen on
`gojri_ghazal`'s `نامل نال` case: convergence between two models is useful
evidence, but it isn't a proof, and doesn't catch a case where both are wrong
in different ways. You also distinguished between "is right" (certain) and
"seems right" (best guess) when answering - worth preserving that distinction
here rather than flattening it, since a few of the accepted readings
(`بھاراو`, `پرسیوپرسے ہونو`, `چلاکی`'s counterpart entries, `پروڑو`,
`شملو میلو`) are lower-confidence calls, not fully verified against the
source the way the "is right" ones are.

**`kahawat_kosh` now fully converged** (0 real remaining differences, only the
now-exempted punctuation spacing). All 4 gold pages tested so far (`dict_alif`,
`gojri_adbiyaat`, `gojri_ghazal`, `kahawat_kosh`) are fully converged between
Gemini 3.6 Flash and Sonnet 4.6.

---

## 2026-08-10 — mahatma_gandhi + kulyate spread run; kulyate_spread_a_right converged

**Ran both models on the next two pages**: `mahatma_gandhi` (illustration +
caption test) and the `kulyate_spread` two-page spread (`_a_right` + `_b_left`,
one logical page, two image files). Two things worth flagging from the raw
outputs, before any correction:
- **`kulyate_spread_a_right`: the two models transcribed different amounts of
  content.** Gemini produced 5 stanzas, Sonnet only 4 - missing the opening
  stanza entirely. Resolved during correction: the extra stanza is real: both
  corrected files now include it.
- **`mahatma_gandhi`: Gemini's illustration description echoed the prompt's own
  example almost verbatim** (prompt example: "a man handing cloth to a kneeling
  boy, others looking on"; Gemini's output: "...handing cloth to a kneeling
  person"). Flagged as worth checking against the image directly before
  trusting it - possible prompt-echo rather than genuine description. Not yet
  resolved - `mahatma_gandhi` correction is still pending.

**In-place-edit mistake happened a fourth time**, on `kulyate_spread_a_right` -
same recovery approach as before, but this time the raw output had never been
committed to git at all (caught the same session it was generated), so
`git show` wasn't available. **Recovered from the conversation's own tool
output instead** - the exact raw text was still visible earlier in the
session, so it was reconstructed from that rather than lost. Sanity-checked the
reconstruction against the logged token/word counts before trusting it. This
mistake has now recurred on every single page corrected since the
`_original`/`_corrected` convention was introduced - worth treating as an
expected step to check for, not a one-off.

**Real finding, not a disagreement**: neither model's raw output included the
page's title/attribution header (`کُلیاتِ رانا فضل حسین` / `تالیف: ڈاکٹر جاوید
راہی`) at all - both models missed it outright, and it was added fresh during
correction. A case where cross-model comparison couldn't have caught the gap,
since both models failed identically.

**Correction converged in three short rounds** (image check by me, then two
rounds of direct answers, distinguishing certain from best-guess as before).
One fix worth noting: `راہی` vs `راہھی` - Sonnet's version had two different
heh characters back to back on the well-documented author name **Dr. Javaid
Rahi** (this project's most-cited compiler, per `CLAUDE.md`) - resolved
confidently without needing the image, since the correct spelling of a known
real name isn't genuinely ambiguous. Also settled: the title/attribution
header is one line with the two phrases at opposite ends (not two lines, not
literally pipe-separated - `|` was Sonnet's own invented separator, not
something printed on the page, so replaced with plain spacing instead in both
files) - a layout detail cross-model agreement alone couldn't have surfaced.

**`kulyate_spread_a_right` now fully converged.** `kulyate_spread_b_left` and
`mahatma_gandhi` still have raw output only, correction pending.

---

## 2026-08-11 — mahatma_gandhi + kulyate_spread_b_left corrected

**In-place-edit mistake, fifth recurrence** - same as every page since the
convention was introduced. This time both files were already committed, so
recovery was simplest yet: `git show HEAD:path` directly, no history
archaeology needed. Confirmed by `git diff --stat` showing zero difference
after restoring.

**`kulyate_spread_b_left` converged in two short rounds.** One fix applied
without needing the image at all: `راہی`, not `راتھی` - the same author name
(Dr. Javaid Rahi) already settled with high confidence on the facing page
(`kulyate_spread_a_right`); Gemini already had it right in this file's own
header too, so this was purely an internal-consistency call. The header
line-format question (one line, phrases at opposite ends, no literal `|`)
was also already settled on the facing page - same book, same layout,
applied directly rather than re-asked. Two genuine remaining items resolved
by you (`جِندڑی` not `چندری`, `دِیا` not `دیا` - the diacritic one) plus
`وچھوڑیئے` not `وچھوڑیے`. **Fully converged.**

**`mahatma_gandhi`: an interesting non-convergence, resolved differently than
usual.** The two models' illustration descriptions never became identical,
and that's the right outcome here, not a gap. Gemini's original raw output
("...handing cloth to a kneeling person") and Sonnet's corrected version
("...a child reaching up, a woman in a dupatta, others seated and standing")
both got **independently confirmed as true** against the actual image -
they're just describing different real details of the same scene, not
disagreeing about it. This also resolves the earlier worry (2026-08-10 entry)
that Gemini's description might have been echoing the prompt's own example
text rather than genuinely describing the page - it wasn't; the detail is
real. Gemini's file needed zero edits and is legitimately "reviewed and
correct as originally written," not an overlooked file - first time that's
happened in this comparison. **Lesson for the eventual cross-page analysis**:
"the two models' corrected outputs disagree" isn't always a defect signal for
free-text description tasks (unlike exact transcription) - sometimes it just
means two true, non-exhaustive descriptions of the same thing, and forcing
them to match would make one artificially less complete, not more accurate.

**6 of 12 gold pages now fully corrected and converged**: `dict_alif`,
`gojri_adbiyaat`, `gojri_ghazal`, `kahawat_kosh`, `kulyate_spread_a_right`,
`kulyate_spread_b_left` (+ `mahatma_gandhi`, converged in substance if not in
exact wording, for the reason above).

---

## 2026-08-11 — Two new models spot-checked: Cursor Composer 2.5 in, Groq 4.5 Fast out

**Groq 4.5 Fast tested via pasted output on 2 pages, ruled out.** Word-level
diff against gold: 38.6% error rate on `gojri_adbiyaat`, 31.9% on
`gojri_ghazal` - roughly 3-4x worse than Gemini/Sonnet. More important than
the raw rate: the *kind* of errors. Confidently wrong on proper names,
repeatedly, with zero hedging - `نذیر`→`ندیم`, `قمر`→`فقر` (twice),
`راجوروی`→`راجوردی` (twice), and most notably the poem's actual signed
author `لعل حسین پرواز` came back as `فضل حسین پرواز` - "Rana Fazal Hussain"
being a real, *different* author's name that appears elsewhere in this exact
corpus (the `kulyate_spread` pages), which reads like possible cross-
contamination rather than a reading error. Also: Eastern/Persian numerals
(`۴۰`) came back as Arabic-Indic (`٢٠`, and wrong besides - misread 40 as
20), a page header's reading order was reversed, typographic quotes were
flattened to straight ASCII ones, and the `[[uncertain]]` bracket convention
was used zero times despite being by far the least accurate output of any
model tested - the opposite of what you'd want from the model most often
wrong. **Decision: not pursued further**, no correction done, no files added
- the pasted-output route doesn't fit the project's file/logging convention
anyway, and the quality gap was decisive enough not to need it.

**Cursor Composer 2.5**: first checked via pasted output (2 pages), looked
competitive; then a full file-based run appeared across all 7 corrected
pages, added directly to the transcriptions folders as `_composer_v1_original.txt`.
**Caught before trusting it**: the file version is a materially different,
more diacritic-careful run than what was pasted earlier - not the same data.
The pasted-text analysis is superseded by the file-based one below.

**Fair comparison, file-based, punctuation-spacing normalized out (same
exemption already applied to Gemini/Sonnet), `mahatma_gandhi` excluded as
non-comparable (free-text description, not exact transcription):**

| Page | gold words | Composer | Gemini (raw) | Sonnet (raw) |
|---|---|---|---|---|
| `dict_alif` | 108 | **15** | 31 | 21 |
| `gojri_adbiyaat` | 204 | 34 | **32** | 32 |
| `gojri_ghazal` | 322 | 52 | 40 | **29** |
| `kahawat_kosh` | 140 | **30** | 32 | 60 |
| `kulyate_spread_a_right` | 152 | **37** | 46 | 66 |
| `kulyate_spread_b_left` | 104 | 18 | **17** | 28 |
| **Total / rate** | 1030 | **186 (18.1%)** | 198 (19.2%) | 236 (22.9%) |

Composer wins outright on 3 of 6 pages and edges out both established
candidates in aggregate error rate. Its errors are the same *category* as
Gemini/Sonnet's raw output - diacritic drops, tight-word-pair spacing, the
occasional known-hard word - never Groq's garbling or invented proper names.
It uses `[[uncertain]]` brackets appropriately on genuinely hard spots (e.g.
`[[پچھّیو]]` on `gojri_ghazal`, the same word every model tested has
struggled with in some form). **One real pattern worth watching, not yet
confirmed as systematic**: `آج` appeared 3 times on `gojri_ghazal` where gold
has `اَج` - the same "normalizing toward standard Urdu instead of Gojri's own
spelling" failure mode already documented for Kimi's `-و`/`-ے` endings,
worth checking on more pages before calling it a real tendency.

**All 7 pages corrected**, following the established convention. Since these
are the *same physical pages* already cross-validated to a converged gold
text (2 independent models + direct image checks on disputed spots), Composer's
`_corrected.txt` for the 6 exact-transcription pages was set to match that
same verified text exactly - there's one true transcription per page, and
forcing an independent third "correction" pass would just re-derive the same
answer through more effort, not a different one. Verified byte-identical to
each page's gold file before committing, and confirmed the raw
`_composer_v1_original.txt` files were never touched. `mahatma_gandhi`
handled differently, consistent with how it's been treated throughout: checked
the actual image directly rather than copy an existing description, since
Composer's raw output described real, verifiable details (bare-chested man,
white dhoti, mud-walled room) but never identified the subject as **Mahatma
Gandhi** specifically, despite that being confirmed true earlier. Minimal
correction applied - added the identification, kept Composer's own otherwise-
accurate phrasing rather than overwriting it with Gemini's or Sonnet's wording.

**Practical note, no cost data for Composer or Groq**: both were produced
outside the project's metered scripts (Composer via Cursor IDE directly, Groq
via pasted output), so neither has token/pricing data in `ocr_runs_log.csv`
the way every Bedrock/Gemini call does. If Composer stays in the active
comparison, that's a real gap before it can be scored on cost the way
Gemini/Sonnet can.

---

## 2026-08-13 — Remaining 5 gold pages: Composer v1 originals only

The 7 already-corrected pages had Composer files; the other 5 vision-OCR gold
pages did not. Ran Composer 2.5 on them with the same frozen `v1` prompt
(`prompts/ocr_transcription_v1.txt`) so the comparison stays apples-to-apples
with Gemini/Sonnet's existing v1 runs. Saved as
`<page>_composer_v1_original.txt` only — no `_corrected.txt` yet, and do not
edit these in place.

| Page | What it tests | Notes from this raw run |
|---|---|---|
| `nazir_spread_a_right` | Second poetry spread, legacy_8bit | Full page: header, title `یاد کراؤں تم نا`, 14 lines with radif `کتنی`, page 139 |
| `nazir_spread_b_left` | Same spread, lots of true blank | 5 continuing lines, then blank + star ornament, page 140 — the "don't invent content" test |
| `louk_warsti` | Real scan, show-through | Show-through ignored. One flagged word: `[[لمی]]` on the last line |
| `shingar_textbook` | Image-only textbook | Two story paragraphs + footer `21 ساتویں کی گوجری کتاب` |
| `primer_pehli` | Children's primer, captioned pictures | Letter `خ` with four captioned photos; Gojri `خربوزو` (not Urdu `خربوزہ`) kept as written |

**Not done in this Composer-only pass:** Gemini and Sonnet had not been run
yet. Superseded the same day by the next entry, which ran both and started
first-pass correction. Step 0.4 (corpus layout / provenance conventions) is
also still open.

---

## 2026-08-13 — Remaining 5 pages: Gemini + Sonnet run, first-pass corrections

Same day as the Composer-only originals above. Ran Gemini 3.6 Flash and
Sonnet 4.6 on all 5 remaining images via the metered scripts (`v1` prompt,
cropped images), then first-pass corrected all three models against
`data/gold/images_cropped/`. Raw `_original.txt` files were never edited.
Logged in `ocr_runs_log.csv` (2026-08-13T15:21–15:23 UTC).

This is **first-pass, not fully converged**. Remaining items below need a
native-speaker image check, same as the earlier pages. Convergence between
models is evidence, not proof.

### What the models did, page by page

**`nazir_spread_a_right` (page 139, poetry, radif `کتنی`).** Header is one
line, opposite ends, no invented `|`. Author is `ڈاکٹر جاوید راہی`. Footer
has no comma between `آرٹ` and `کلچر` (unlike the kulyate books, which do).
Sonnet garbled the header (`نذمیر`, `راتی`). Gemini split the header onto
two lines. Composer got the header layout right. Applied first-pass:
`تھارا`, `جمالؔ`, `بدھائی`, `بُزرگی`, `چاننی`, `ازمائی` (plain alif, not
`آزمائی`), `ہم نا سُن` then `ہم ناں سُن کے`, `انھاں وِچ`, `جرگا`, `لالچ`,
`پھسائی`.

**`nazir_spread_b_left` (page 140, the blank-space test).** All three models
passed: 5 continuing lines, then blank, then a star ornament, page 140, same
footer. Nobody invented body text in the empty region. Applied: `بڈیائی`,
`کرامتاں`, `بگائی`, `کول`, `پھسائی`, `نذیرؔ سکو`. Gemini invented
`ہڈیائی`/`بگوائی`; Sonnet `بُدیائی`/`کون`/`بھسائی`. Composer was closest
and was the only one to mark the takhallus on `نذیرؔ`.

**`louk_warsti` (page 99, real scan, show-through).** All three ignored the
bleed-through, which is the point of this page. Heading `م` then
`ماترے : دوجی ماں`. Applied: `جہڑی اس را ہے۔`, `اُس گی` / `لڑکاں گی`,
`میٹرا`, `وے لڑکا`, `تھو دے`, `نا جائز`, `اسنو`, `ور لمی`, `کرلاوے`.
Composer flagged `[[لمی]]`. Gemini/Sonnet both used `گی`; Composer used `کی`.

**`shingar_textbook` (page 21, image-only textbook).** Two story paragraphs
plus a designed footer. Sonnet garbled the opening (`جیرا نگی`, duplicated
`تم`) and dropped `پکو` before `یقین ہے`. Gemini's body was usable; its
footer was scrambled (`سمتیں`, wrong order). Composer was closest on the
body. Applied footer: `21 ستویں کی گوجری کتاب` (Gojri `ستویں`, not Urdu
`ساتویں`) and `دی جموں اینڈ کشمیر سٹیٹ بورڈ آف سکول ایجوکیشن`. Kept
`ٹھگ گی آواز` (all three models) pending image confirmation of `گی` vs `کی`.

**`primer_pehli` (page 16, letter `خ`).** Captioned photos, not paragraphs.
Labels: `خرگوش`, `خچّر` (shadda on che), `خربوزو` (Gojri `-و`, not Urdu
`خربوزہ`), `خوبانی`. Note starts `نوٹ: اُپر دِتی وی شکلاں کی پچھان...`.
Footer uses Western `16`, not Eastern `١٦` (Sonnet used Eastern).
Illustration descriptions stay per-model, same rule as `mahatma_gandhi`.

**Composer Urdu-normalization, now seen twice not once.** On this primer
page Composer wrote `تاکہ` and `پہچان` where the page has Gojri `تانجے` and
`پچھان`. That is the same "normalize toward standard Urdu" tendency first
flagged as `آج` vs gold `اَج` on `gojri_ghazal`. No longer a one-off. Gemini
had `اَپر` (zabar) where the page has `اُپر` (pesh), a related diacritic
swap. First-pass gold uses `تانجے`, `پچھان`, `اُپر`, and `کنّی کنّی`
(shadda on noon; Composer/Sonnet had `کئی کئی`, Gemini `کتني کتنی`).

### Remaining items for native-speaker image check

Do not treat these pages as converged until these are answered against the
image, not by majority vote:

1. `nazir_a`: `جمالؔ` vs `جمالؑ`
2. `nazir_a`: `ازمائی` vs `آزمائی`
3. `nazir_a` line 8 vs 9: `ہم نا سُن` / `ہم ناں سُن` (plain noon vs noon-ghunna, and whether the two lines match)
4. `nazir_b`: `سکو` vs `سِکو`
5. `nazir_b`: is the takhallus mark on the last-line `نذیرؔ` (Composer yes, Gemini/Sonnet no)
6. `louk`: `کی` vs `گی` (`اُس گی زنانی`, `لڑکاں گی`)
7. `louk`: `میترا` vs `میٹرا`
8. `louk`: `اسنو` vs `اسو`
9. `shingar`: `ٹھگ گی آواز` vs `ٹھگ کی آواز`
10. `shingar`: `دِتو` vs `دِتّو`; `ہووے` vs `ہوے`; `لے سکتو` vs `لے سکو`
11. `primer`: confirm `کنّی کنّی` (vs `کئی کئی` / `کتني کتنی`)

Once those are settled, make all three `_corrected.txt` files byte-identical
on the exact-transcription pages (primer illustration notes may still differ)
and then the 12-page cross-model analysis can run.

Composer still has no cost/token rows in `ocr_runs_log.csv`. Sonnet 5 still
Sales-gated. Step 0.4 still open.

---

## 2026-08-14 — Prompt v2 rewritten for one-shot Gemini/Sonnet

The earlier `prompts/ocr_transcription_v2.txt` (2026-08-04) was deleted on
purpose. It had useful layout rules (no skip/repeat on dictionary lines,
numerals as printed, show-through, two-column pairs) but the gold-set work
since then showed failure modes v1 never named, and the old numeral rule
once pushed Gemini to read headword alif as digit `۱`.

New v2 is still one-shot. Second pass the same day, before any Gemini/Sonnet
re-run: the first draft had put gold-set answers into the prompt itself
(`خربوزو`, `پچھان`, `تانجے`, `اَج`, `لڑکا`/`لیو دے`, Western `16` vs
Eastern `١٦`, and the primer/mahatma illustration examples). That would have
contaminated the pages we are about to score. Those strings are gone. The
rules stay as patterns: do not rewrite Gojri as Urdu; keep pesh/kasra/zabar/
shadda/noon-ghunna as printed; the three heh letters; honorific marks; word
spacing from the visible gap; letter `ا` is not digit `۱`; headers as one
line with no invented `|`; banner footers; captions on pictures are text;
poetry refrain is a check against the image, not a reason to force two lines
identical. Also restored: no invented sentences, no placeholder letters,
kaf vs gaf, labelled-picture reading order, names letter-by-letter.
`scripts/ocr_test_common.py` already defaults to `v2`.

Gemini and Sonnet v1 originals were removed on `nazir_spread_*`,
`shingar_textbook`, and `primer_pehli` so those pages can be re-run under
this prompt only. `louk_warsti` still has v1 Gemini/Sonnet originals.
Composer v1 files were left in place (chat pipeline, not this prompt bump).

---

## 2026-08-15 — Nazir spread gold files; first scored pages under new gold rule

There is no `nazir_spread_a_left`. The left half is `nazir_spread_b_left`.

You image-checked both halves. Gold is now one file per page:
`nazir_spread_a_right_gold.txt` and `nazir_spread_b_left_gold.txt`, copied
from your edits to the Composer `_corrected.txt` files (those corrected
copies remain as the working notes you edited).

Your gold fixes vs the assistant first-pass: header takhallus `نذیرؔ`;
`جمالؔ` confirmed (mark on `ل`); `بِچ` not `وِچ`; `جِرگا`; and on the
left half, diacritics the first-pass had dropped (`مِلے`, `کَدھ`, `بَهلا`,
`کُھو`, `سُچی`, `سِکو`). Composer v1 original already had `سِکو`; the
first-pass "correction" had removed the kasra. That is why this spread's
first-pass looked worse than the earlier converged pages.

Word error vs gold (whitespace collapsed, punctuation spacing ignored,
`[[...]]` unwrapped, `[blank]`/`[illustration]` lines not counted):

| Page | gold words | Composer v1 | Gemini v2 API | Sonnet 4.6 v2 API | Sonnet 5 CC v2 |
|---|---|---|---|---|---|
| `nazir_spread_a_right` | 190 | **3.7%** | 10.5% | 11.1% | 11.6% |
| `nazir_spread_b_left` | 79 | **7.6%** | 11.4% | 16.5% | 16.5% |

Composer v1 is chat-with-notes, v1 prompt. Gemini/Sonnet 4.6 are one-shot
API, v2 prompt. Sonnet 5 CC is chat-with-notes, v2 prompt, and this
session may have seen LOG words. Do not read the table as a fair four-way
model rank.

---

## 2026-08-15 — Direct-extraction pages removed from gold images

`hindi_dict` and `quran_translation` are good-text PDFs. They were in the
gold image folders only as an extraction check, not as vision-OCR pages.
Removed `data/gold/images/hindi_dict.png`,
`data/gold/images/quran_translation.png`, and
`data/gold/images_cropped/quran_translation.png`. Dropped those rows from
`candidates.csv` and from `scripts/build_gold_candidates.py` so a re-render
does not put them back. Source PDFs stay in `pdfs/`. Gold images are now
the 12 vision-OCR pages only.

---

## 2026-08-15 — shingar_textbook gold

You image-checked `shingar_textbook_composer_v1_corrected.txt`. Gold is
`shingar_textbook_gold.txt`. Fixes vs the assistant first-pass: `مِناں`,
`سمجھ گے` / `لاہ گے` / `ہو گے` (not `کے`), `دِتی` / `چِر` / `ہوے` (not
`ہووے`), footer `ستمیں` not `ستویں`. `ٹھگ گی آواز` stays `گی`.

Word error vs gold (same rules as nazir). No Sonnet 5 CC file: that chat
skipped this page.

| Page | gold words | Composer v1 | Gemini v2 API | Sonnet 4.6 v2 API |
|---|---|---|---|---|
| `shingar_textbook` | 224 | **4.9%** | 18.3% | 20.1% |

Both APIs put the footer in `[badge:]` / `[footer ...]` notes, so those
words were missing from the scored text. Composer kept the footer as
printed text and was closer on body spelling, but still wrote Urdu-ish
`ساتویں` for gold `ستمیں`.

---

## 2026-08-15 — louk_warsti and primer_pehli gold

You had already image-checked both Composer `_corrected.txt` files. They
were not copied to `_gold.txt` until now. Gold is
`louk_warsti_gold.txt` and `primer_pehli_gold.txt`.

Louk vs first-pass: `اسو` not `اسنو`; `تُوں` with pesh; `لمّی` with shadda.
`گی` and `میٹرا` stay as you had them.

Primer vs first-pass: `بُھوم` (pesh). Labels stay `خربوزو`, `خچّر`,
`پچھان`, `تانجے`, `کنّی کنّی`. Picture notes are not scored.

Word error vs gold (same rules; picture lines skipped):

| Page | gold words | Composer v1 | Gemini v1 | Gemini v2 API | Sonnet 4.6 v1 | Sonnet 4.6 v2 API | Sonnet 5 CC v2 |
|---|---|---|---|---|---|---|---|
| `louk_warsti` | 114 | **8.8%** | 13.2% | 15.8% | 26.3% | 28.1% | (skipped) |
| `primer_pehli` | 50 | **12.0%** | — | 16.0% | — | 28.0% | 44.0% |

v2 did not help the APIs on `louk_warsti` (slightly worse than v1). Sonnet
still splits Gojri words. Composer still rewrote primer `پچھان`/`تانجے` as
Urdu `پہچان`/`تاکہ`. Sonnet 5 CC scrambled the primer note and footer order.

The five remaining-page gold files are now: nazir both halves, shingar,
louk, primer.

---

## 2026-08-15 — First six gold files re-checked; full bake-off vs originals

You re-checked `_gold.txt` for `dict_alif`, `gojri_adbiyaat`, `gojri_ghazal`,
`kahawat_kosh`, `kulyate_spread_a_right`, and `kulyate_spread_b_left` against
the cropped images. Main gold edits vs the earlier Composer-corrected copies:
takhallus `ؔ` on poet and compiler names; kasra on `آبِش` and `وِچ`;
`نحس` not `نخس`; `ڈاہڈی`; `کجھ` / `مھارے` / `جے وہ خود` on the ghazal
essay; proverb word joins (`پڑدورکھنو`, `لاڑلو پُوت`). Gold is yours. The
earlier log note that used `مہارے` (goal heh) is superseded on this page by
`مھارے` in gold.

Then scored every active `*_original.txt` against current gold with
`scripts/score_gold.py`. Rules: collapse whitespace; ignore spacing around
`: ، ۔`; unwrap `[[...]]`; skip whole lines that are only a bracket note
(`[illustration:]`, `[photo:]`, `[badge:]`, `[blank]`, and similar). That last
rule means a footer wrapped in `[badge:]` counts as **missing printed text**,
which is the correct penalty.

**Fairness (do not skip this).** Composer 2.5 and Sonnet 5 Claude Code are
chat runs with project notes and extra looks. Gemini 3.6 Flash and Sonnet 4.6
are one-shot API. Prompt is mixed: first six API pages are v1; nazir, shingar,
louk, primer are v2 (louk still also has v1). Sonnet 5 CC covers only 6 of 12
pages and this chat may have seen gold words. Chat WER is a quality ceiling,
not a bulk-pipeline rank.

**Word error, latest prompt per page for APIs (1790 gold words across 12 pages):**

| Page | gold words | Composer v1 chat | Gemini latest API | Sonnet 4.6 latest API | Sonnet 5 CC |
|---|---|---|---|---|---|
| `dict_alif` | 118 | **11.9%** | 25.4% v1 | 19.5% v1 | — |
| `gojri_adbiyaat` | 220 | 18.2% | **17.7%** v1 | **17.7%** v1 | — |
| `gojri_ghazal` | 346 | 14.2% | **12.4%** v1 | 13.3% v1 | 31.2% |
| `kahawat_kosh` | 182 | **15.9%** | 19.8% v1 | 35.2% v1 | 50.5% |
| `kulyate_spread_a_right` | 154 | **24.0%** | 30.5% v1 | 42.9% v1 | — |
| `kulyate_spread_b_left` | 106 | 17.9% | **17.0%** v1 | 26.4% v1 | — |
| `mahatma_gandhi` | 7 | **0%** | **0%** v1 | **0%** v1 | **0%** |
| `nazir_spread_a_right` | 190 | **3.7%** | 10.5% v2 | 11.1% v2 | 11.6% |
| `nazir_spread_b_left` | 79 | **7.6%** | 11.4% v2 | 16.5% v2 | 16.5% |
| `shingar_textbook` | 224 | **4.9%** | 18.3% v2 | 20.1% v2 | — |
| `louk_warsti` | 114 | **8.8%** | 15.8% v2 (v1 was 13.2%) | 28.1% v2 (v1 was 26.3%) | — |
| `primer_pehli` | 50 | **12.0%** | 16.0% v2 | 30.0% v2 | 44.0% |
| **Pooled** | **1790** | **12.7% chat** | **17.3% one-shot** | **21.9% one-shot** | 30.1% on 6 pages only |

Gemini 3.6 Flash is the best **one-shot API** on this gold set. It wins or ties
Sonnet 4.6 on 11 of 12 pages. Sonnet 4.6 wins only `dict_alif`. Composer chat
is still lower error on most pages, but that setup is not the bulk job.

**Where each model is strong**

- **Gemini 3.6 Flash (one-shot):** Best scalable reading of dense essay
  (`gojri_ghazal` 12.4%, beats Composer on that page). Keeps two-column proverb
  pairs in row order. On `kulyate_spread_b_left` almost all remaining error is
  dropped diacritics (16 of 18 errors), not wrong letters. Primer labels
  `خربوزو` stay Gojri; caption text is kept. Illustration pages: printed
  caption and page number match gold; it does not invent body text.
- **Sonnet 4.6 (one-shot):** Slightly better than Gemini on the mixed
  Nastaliq+English dictionary page. Honorifics and some diacritics appear when
  it does not split the line. Does not invent a second story on
  `mahatma_gandhi`.
- **Composer 2.5 (chat):** Lowest pooled WER. Reads banner footers as real
  text (`ستمیں کی گوجری کتاب`), not `[badge:]`. Fewest missing words (8 vs
  Gemini 50 / Sonnet 86 on the latest-API mix). Strong on nazir and shingar
  body spelling. Useful as a **gold-draft** helper, not as the paid bulk model.
- **Sonnet 5 Claude Code (chat):** Usable on nazir (11.6% / 16.5%), close to
  Sonnet 4.6 API. Not usable as evidence for bulk Sonnet 5: incomplete set,
  possible gold leak, 31%+ on the ghazal essay and 44% on the primer.

**Where each model lacks**

- **All models:** Drop takhallus `ؔ` on names unless a human already pushed
  them (Composer still dropped most of them in the raw original). Drop pesh /
  kasra / zabar / shadda on poetry. Confuse the three heh letters on a few
  words (`هور` / `ھدرو` / `بَهلا`). Dictionary mixed-script lines inflate WER
  because English glosses glue to Gojri tokens.
- **Gemini:** Mixes RTL order on some dictionary `eg:` / `lpp:` lines and
  drops the English tail (`To invite trouble`). Puts shingar footer inside
  `[badge:]` and writes Urdu `ساتویں` for gold `ستمیں`. Primer still
  Urdu-normalizes `پچھان` → `پہچان` and splits `تانجے`. v2 did not help
  `louk_warsti` (worse than v1).
- **Sonnet 4.6:** Splits Gojri words (`پر سیو`, `چَھٹنا` pieces, primer
  `تا نَجے`). Highest missing-word count: on `kulyate_spread_a_right` it
  skipped the header and the first stanza (35 missing words). Worst on
  two-column `kahawat_kosh` (35.2%): letter errors plus extra split tokens.
  Footer still wrapped as `[footer ... badge]`. Primer puts `خ` only inside an
  illustration note and writes `کئی کئی` for `کنّی کنّی`.
- **Composer:** Rewrites Gojri toward Urdu on the primer (`پہچان`, `تاکہ`,
  `کئی کئی`). Still misses `ؔ`. Extra tokens on dictionary lines from
  different wrapping, not from a second invented paragraph.
- **Sonnet 5 CC:** Reverses primer footer order. Scrambles the primer note
  (`پچھان اُنجے تانئے` / `تا نئچے`). Large deletions on `gojri_ghazal` and
  `kahawat_kosh`.

**Prompt v2 vs v1:** On `louk_warsti`, the only page with both API versions
kept, v2 is slightly worse for both Gemini and Sonnet. Do not treat the longer
prompt as a proven win. Do not bake gold-page answers into a v3 prompt.

**Provisional bulk choice:** Gemini 3.6 Flash, cropped images, current v2
prompt until a v3 trial is scored. Keep Sonnet 4.6 off the default path
(higher error and higher Bedrock cost). Composer remains the gold-draft
tool. Human spot-check is still required, especially dictionaries, two-column
pages, and poetry diacritics. Re-run Gemini/Sonnet v2 on the six v1-only pages
before claiming a prompt-controlled 12-page API rank.

---

## 2026-08-15 — Bulk vision OCR paused; dual-model agreement is not enough

You are not confident in Gemini for bulk work and cannot review 14,761 pages.
That constraint stands. 17.3% one-shot word error would poison a preservation
corpus if accepted unreviewed.

Gemini vs Sonnet 4.6 on gold (independent alignment of each hyp to gold): they
write the same token on 77.6% of gold words. Of those agreements, 5.0% are
still wrong (69 of 1,389). Shared fluent mistakes (dropped `ؔ`, Urdu-like
spelling, missing marks) are the silent failure. The other 22.4% of words
disagree and would still need a person. Poetry spreads are worse (about 12–15%
of agreements wrong). Dual-model filtering cuts work. It does not remove it.

**Decision:** pause bulk vision OCR. Keep the 12 gold pages as the yardstick.
Next OCR experiment is the decode-table spike on font-encoded PDFs. Image-only
pages (~1,281) still need vision later. Usable text that does not wait on OCR:
FLI corpus, good-text PDFs (including the Quran translation), Common Voice.

Closest public neighbours: BaltiVoice (ASR gold split, not OCR);
UTRNet/UTRSet-Real (11k human-labelled Urdu lines); Kashmiri InPage-to-Unicode
then KS-LIT-3M / KS-PRET-5M (mapping table, not vision per page); Sindhi and
IndicPhotoOCR gold sets are mostly synthetic lines or scene-text photos.

---

## 2026-08-15 — One gold file per page; per-model `_corrected.txt` removed

Gold is now `transcriptions/<page_id>/<page_id>_gold.txt` only. Copied the
settled Composer (or existing) gold text onto the seven earlier pages that
did not yet have `_gold.txt`. Deleted every `*_corrected.txt` under
`transcriptions/` (28 files). Raw `*_original.txt` files were not touched.
Docs updated: `data/gold/README.md`, `scripts/ocr_test_common.py`,
`CLAUDE.md` Status, `plans/STAGE-0.md`, `plans/STAGE-1-TEST-BATCH.md`,
`ROADMAP.md`. Score a model by comparing its original to `_gold.txt`.

---

## Glossary (grows as new terms come up)

- **Token**: the unit a model reads/writes in and is billed by — roughly a
  word-piece, not a whole word. Dense Nastaliq text uses more tokens per page than
  the same content in Latin script.
- **Prompt**: the instructions given to a model alongside its input (here, the image)
  telling it what to do. Prompt wording measurably affects output quality — part of
  why exact prompts are being logged from now on.
- **Hallucination**: a model producing a fluent, plausible-looking answer that isn't
  actually grounded in the real input — dangerous because it fails *silently*,
  unlike a traditional OCR engine which tends to fail visibly (blank/garbled) when
  unsure.
- **Flash vs. Pro (Gemini), Haiku vs. Sonnet (Claude)**: within one model family,
  vendors offer a faster/cheaper tier and a slower/more-capable tier. For a
  large-page-count OCR job, the cheaper tier is usually the right starting point
  since cost scales with every page.
- **Radif**: in Urdu/Gojri ghazal poetry, a word or phrase that repeats identically
  at the end of every line/couplet. Relevant to OCR because it's a built-in
  consistency check a model isn't currently using.
- **The three heh letters**: Nastaliq/Urdu script has three visually-similar but
  distinct heh characters, all real, separate letters, not stylistic variants:
  plain Arabic heh (`ه`, U+0647, borrowed from Arabic, no special meaning in
  Urdu/Gojri), goal heh (`ہ`, U+06C1, the ordinary standalone Urdu heh, e.g. in
  `وہ`/`یہ`/`ہے`), and do-chashmi heh (`ھ`, U+06BE, "two-eyed heh," marks
  aspiration - what turns `د` into `دھ`, `ب` into `بھ`, etc.). All three have shown
  up as genuine correction disputes across the gold-set pages so far - worth
  checking the exact codepoint, not just eyeballing similar-looking glyphs.
- **Gold set**: a small set of pages whose text a human has already confirmed
  against the image. Used only to score OCR methods (word error / character
  error), never as training data. Ours is 12 vision-OCR pages.
- **Word error rate (WER)**: share of words that are wrong, missing, or extra
  compared with gold, after light punctuation-spacing normalisation. 17% WER
  means about 17 of every 100 gold words do not match.
- **Decode table**: a lookup from each (font, codepoint) pair in a
  font-encoded PDF to the real Unicode letters that glyph represents. If the
  table is right, decoding is free and does not hallucinate.

---

## 2026-08-15 — Decode-table spike started (PDF glyphs, not InPage .INP)

Public converters target `.INP` files. Our books are already PDFs. Inspected
two gold pages with `scripts/inspect_pdf_glyphs.py`.

`Gojri-English-Dictionary.pdf` p.25 (Batool): Type0 Identity-H, ToUnicode
present but CID→PUA (`<0040> <F05D>`), not Arabic. 236 Batool glyphs, **58
unique codes**. English is real Arial/Times. Repeating gold word `الف` is
PUA sequence `F05D F0D6 F0CC` in RTL order. Seed map in
`data/decode/batool_pua_seed.json`: ا ل ف ، آ ب.

`Kahawat-Kosh.pdf` p.50: many `NOORIN*` subfonts, almost all PUA, 188 unique
(font, code) pairs on one page. Same PUA number in Batool vs NOORIN is not
the same letter. Table key must include the font.

`kulyate` spread: dozens of `TT*t00` WinAnsi fonts, almost no ToUnicode.
Third table family (legacy 8-bit), not Batool/NOORIN.

Grew the Batool table on `feat/decode-table`. All **58 unique codes** on
dictionary page 25 now have a Unicode value. Dump with
`py -3 scripts/dump_batool_lines.py`. Cluster rows by y (~14px). Insert a
word space when the RTL x-gap is above ~1px. Remaining mismatches vs
`dict_alif` gold: kasra/pesh sort before the host letter; `نہیں` vs gold
`نھیں`; `آبلاے` vs `آبلائے`; `مهارو` heh family.

Grew the same table from page 26 (13 new codes from English glosses) and
page 27 (ڈ ذ ز س ڑ ی). Census of pages 25-40: 117 unique Batool codes,
77 mapped. Pages 25-26 unknown=0. Page 27 leftover: F024 F07C F0D7 F0EB.

Agent brief: added `AGENTS.md` (writing rules plus a pointer to
`CLAUDE.md`) and `.cursor/rules/writing-ste100.mdc`.

Pages 25-80 of the Gojri-English dictionary now decode with **zero**
unknown Batool codes. Table size **160**. Full book (pages 25-498): 160
unique Batool codes, **zero leftover**. Wrote Unicode text with
`py -3 scripts/decode_batool.py 25 498` into `data/decode/out/`
(gitignored). Remaining issues vs gold: heh family, some ligature and
suffix alef placements. Combining marks now attach to the nearest letter.

Decoder now attaches combining marks (`ِ ُ ً ّ ٓ ٰ`) to the nearest host
letter by x, then emits letter-then-mark. Page 25 gold matches
`آبِش`, `آپ بِیتی`, `آپ خُودرو`, `دھُپ`. Rebuilt all 474 page files.

Second pass vs `dict_alif_gold.txt` (user gold, page 25). User confirmed
`آبلائے`, `نھیں`, `مهارو`, `اپ ھُدرو`, and `مار کے`. Decoder now uses
neighbor rules (not a 1:1 JSON split): F0F1+F031 → `ائے`; F060 after ن
before ی → `ھ`; F060 after م before ا → `ه`; F061 before د → `ھ`.
`مار کے` already had the space. Gold `مارکے` on that line was aligned to
`مار کے`. Page 25 letter forms now match gold. Leftover: Latin `Ipp` vs
gold `lpp`, and layout spaces.

Started a separate NOORIN table for `Kahawat-Kosh.pdf` (gold
`kahawat_kosh`, PDF page 50). Key is `FONT:CODE`. Page has 185 unique
keys. Blind gold-gap fill is unsafe: frequent codes must not take a
value from one row only. Unique ligatures that hold: `پرسیو` (F0B1),
`پگ بٹانی` (`بٹا`+`نی`), `پلا`/`چھوڑ`, `پلو پکڑنو`. Table is 70 keys.
115 letter keys still unknown. Decode line `پلوپکڑنو` now matches gold
letters. `پتر` still reads `وتر` until F0E2 nuqta attaches. Gold phrase
`دبکار سُناں` is ink on the page; those letters are not extra PUA codes
in the text layer (16 base glyphs on that row). Next: map the remaining
115 keys one ligature at a time. Do not mix fonts.

The Anjum Awan Gojri-English dictionary is one 498-page PDF, not 900.
`Concise_Gojri_English_Dictionary_by_Dr_R.pdf` (24 pages) is the same
front matter (same 97 Batool codes, same 3 unknowns). Decoded pages 1-24
of the 498-page file so the out folder covers the whole book. Front
matter leftover Batool codes: F0B3 F0EA F0FE. Javaid Rahi dictionary
parts (about 1,180 pages after keeping unique files) use NOORIN. The
Hindi-English dictionary (458 pages) is already clean Unicode.

Second pass of that inventory (manifest vs 92 PDFs on disk, live open of
the dictionary files). File buckets hold: 5 good Unicode, 55
font-encoded, 17 image-only, 7 English out of scope. Hash duplicates:
7 groups, 8 extra copies. Correction: the two 169-page Rahi PDFs are
re-exports of one part (text matches, MD5 differs). The two 110-page
Rahi PDFs are the same case. Unique Rahi dictionary *content* is about
902 pages (1+281+169+110+341), all NOORIN. Concise 24-page PDF: 21,000
Latin letters match pages 1-24 of the 498-page book exactly; files are
not the same bytes (Helvetica vs Arial). Two Louk Warsti 202-page files
are both image-only and not hash duplicates. `legacy_8bit` = 9 files,
1,886 pages; two of those still name NOORIN fonts but extract as
Latin-range text.

NOORIN page 50: overlays now join only the nearest row (they used to
join every row within 18px, so the next line's dots sat on `پتر`).
F0E2 with nearby NOORIN86 is `پ`. Decode of that headword is
`پرایاپتراکھوہرو` (`پتر` is correct; the PDF still has an extra `ر`
before the final `و`). Unique last-line maps: `شملو` `میلو`. Table 72
keys. 113 letter keys still unknown. Did not map frequent codes
(`F08A`, `F025`) from one row.

Grew unique maps: `ب` (F024, two sites), `دھا` (F04A), `نو` (F052),
`پک` (F03C). `پگبدھانی` now matches gold. `پڑ…نو` ends with `نو`.
Table 76 keys. About 109 letter keys still unknown. Frequent codes
still untouched.

NOORIN page 50 continued. Table is now 93 keys, 92 unknown letter keys
left. New maps that hold on every checked use: `ریںپ` (F02C), `بڈ`
(F025, two sites), `یری` (F06B), `رسے` (F0D0, three sites), `د` (F08A,
narrow 4.4px, 12 sites), `ینو` (F065, two `دینو` ends), `نہ` `لگن`
`ھیں` `پدے` `فارسی` `تے` `بیچیں` `تیل` `رایو` `لا` `وستی`.
Full Gojri matches: `پریںپانینہلگندینو`, `پگبٹانی`, `پگبدھانی`,
`پلوپکڑنو`. `پگبڈیری` is right; `F07E` still sits before `شملو`.
Did not map `F083` (votes split `ہ` vs a whole leftover phrase).
Did not map `F07E` as `ی` (it broke `بدتمیزی`). Dump:
`py -3 scripts/dump_noorin_lines.py 50`.

NOORIN page 50: every one of the 185 page keys is now in
`noorin_pua_seed.json`. `F083` uses a neighbor rule (`ہو` before `نی`,
`ہون` before `و`). Lines that match gold letters: `پریںپانینہلگندینو`,
`پگبٹانی`, `پگبدھانی`, `پگبڈیری شملومیلو`, `پلوپکڑنو`,
`پرسیوپرسےہونو`, `تھکجانو،`, `کسےکوعیبچھپانو`, `ڈرکنالنسجانو`.
Frequent keys `F04B` `اپنی`, `F063` `یار`, `F068` `ڑ` are majority
maps and still put the wrong letters on some other lines. Next: split
those three by neighbor rules, then decode the rest of Kahawat.

Neighbor rules added in `dump_noorin_lines.py`. `F04B`: `منا` before
`نی`, empty before `گہنو`, else `اپنی`. `F063`: `یار` after `بڈ`, `بت`
between two `ر`, `یا` after `ھ`, empty before `د`. `F068`: skip after
`چھوڑ` or `جوڑن`. Gold page 50 checks: `پربت` start, `منا نی`,
`پلاچھوڑ کے`, `جوڑن و`, `بڈیار`. Decoded all 169 Kahawat pages to
`data/decode/out/kahawat-kosh/`. Pages 161-169 are empty. 159 pages
still have unmapped keys (~24k tokens). The page-50 table is not a
full-book table.

Book-wide NOORIN census (`census_noorin.py 1 169`): 2,149 unique keys,
185 in the table, 1,964 unknown. Instances: 56,567 mapped, 24,071
unknown (70.1% mapped). Overlay unknown: 170 keys, 5,848 instances.
Top unknown keys by count: `NOORIN63:F0E2` 727, `NOORIC:F028` 542,
`NOORIN48:F0EC` 388, `NOORIN81:F021` 370, `NOORIN56:F0CE` 317. Top 40
unknown keys cover 34.6% of leftover instances. Top 160 cover 61.8%.
The long tail is large. Next fill should start with high-count base
keys, not a blind empty-map of every new NOORIC mark.

Unmapped unique keys in Kahawat: 1,964. Of those, 618 appear once
(594 base, 24 overlay), 267 appear twice. Public InPage-to-Unicode
tables (KamalAbdali, `inpage-format` `0x04 XX` maps, Kashmiri KS-LIT
converters) read `.INP` files. They map about 110 logical letters, not
the 80+ NOORIN ligature fonts in these PDFs. No public
`FONT:CODE` → Unicode table for NOORIN01–NOORIN86 PUA was found.
Desktop NOORIN TTFs exist on font sites with their own character maps.
Those maps are not the PDF Identity-H PUA codes. Do not paste an
InPage table onto this seed.

Grew the table from Kahawat page 51 (next to gold). Six maps:
`NOORIN05:F041` پلے, `NOORIN25:F0BA` پنجا, `NOORIN63:F0E2` ما,
`NOORIN01:F029` `(`, `NOORIN01:F028` `)`, `NOORIC:F028` empty.
Table 191 keys. Instances mapped 72.4% (was 70.1%). Unknown keys
1,958. Page 51 now reads `پلے` and `پنجاںماںنہپنجارماں` (`ہ` in
`پنجاہ` is still the old `ر` map). Did not map `F073` or `F021`
(same key, more than one letter). Re-decoded pages 1-169.

Next leftover batch: `NOORIN48:F0EC` is `ے` (388 uses; after `ک`/`ھ`
it makes `کے`/`ھے`). Neighbor rules: `F07B` is `ہ` between `پنجا` and
`ما` (`پنجاہماں` on page 51). `F021` is `با` only before `د`. `F033`
is `ن` only before `ے`. Did not give `F021` or `F0CE` a default map.
Table 192 keys. Instances mapped 72.9%.

`F021` split: default `با` (same 4.9px beh+alif shape). Before `ے`:
`ب` at word start (`بے`), empty after `س`/`کی` (`سے` on page 5,
`رسےکو`). Word-start `باڑ` `بال` `باد` hold. `باو` still sits where
`باپ` is wanted (next letter is `و`). Table 193 keys. Mapped 73.3%.
Re-decoded pages 1-169. Next leftover base key is `F0CE` (317).

`F0CE` is `سو` (9.5px seen+waw). Checks: `سو کرن`, `سونا` (`سو`+`نا`),
`سوں`. `اسوپکڑنو` keeps the `و` (`آس` would need `س` only).
`سورلنہیں` is near `سوال نہیں`. Table 194 keys. Mapped 73.7%.
Re-decoded pages 1-169. Next leftovers are mostly NOORIC overlays.

`F075` is a long `ک` form (11–13px), not `NOORIN01:F067`. Word crops
read `لوک`, `اک`, `رکھ`. Nuqta/NOORIN86 → `گ` (37 of 247). Page 8 now
shows `رکھ`. `پوکرد` still appears because `F0DF` stays `پو` (headers
look like `لوک`). `رککو` is `ک` plus a following `کو` ligature. Did
not empty-map `NOORIC:F038` / `F0F6` / `F0B2`: tight crops mixed in
neighbor letters. Table 195 keys. Mapped 74.0%. Re-decoded 1-169.
Next high-count base key is `F033` (242; `ن` only before `ے` so far).

`F033` is `کھا` (10.9px kaf + do-chashmi-he + alif). Tight crops match.
Page 28: `نہیں کھاتو`. `رکھاں` is likely `اکھاں` if `F05A` is `ا` on
those lines. The old `ن` before `ے` rule was wrong (`کھائے`, not
`کرنے`). No `گھا` split: nuqta crops still look like `کھا`. Table 196
keys. Mapped 74.3%. Re-decoded 1-169. Next high-count base key is
`NOORIN81:F040` (229).

`F040` is `تا` (6.8px te+alif). All 229 carry NOORIN86 dots. Word crops
`ہوتا` `آتا` `کھاتا` `کرتا`. Before `ں` (91) this is `تاں`. Page 13
shows `آپتاں`. Table 197 keys. Mapped 74.6%. Re-decoded 1-169. Next
high-count base key is `NOORIN83:F0D9` (196). Overlays still lead the
leftovers (`NOORIC:F038` 249).

`F0D9` is gol-he `ہ` (3.2px). It sits before `NOORIN82:F043` 180 times.
That pair is `ہر`. Mapped `F043` as long `ر` (8.9px) in the same step.
Checks: `ہرکوئے`, `ہرکسے`, `با ہر کرنے`. `F044` looks like `ز` (`ہزار`),
`F045` like `ڑ` (`گوہڑا`). Not mapped yet. Table 199 keys. Mapped
75.1%. Re-decoded 1-169. Next high-count base keys are `F0CD` and
`F082` (178 each). Overlays still lead (`F038` 249).

`F044` is `زا` (6 uses, all `ہزار`). `F045` is `ڑ` (10 uses, all after
`ہ`). Page 6: `ہزارکر`. Page 21: `ہڑ`. Table 201 keys. Mapped 75.1%.
Re-decoded 1-169. Next high-count base keys are `NOORIN63:F0CD` and
`NOORIN81:F082` (178 each).

`F082` is `سا`. `F0F1` is `مو`. `F05B` is isolated `ب`. `F0E0` is
bari-ye `ے` (`آپے`). `F0CD`+`F060` is `گوج` (`گو` + `ج`). Table 207
keys. Mapped 76.2%. Re-decoded 1-169.

Next leftover base batch, mapped only where crop plus neighbors hold:
`F0C9` `گل` (`کی گل کرنی`, `گل بات`); `F079` `گھر` (`کے گھر آپ`);
`F025` `گر` (`گر پدے`); `F03B` thin `ا` (`اک`, `دھاں`); `F04E` wide
final `و` (`ہونو`, `بننو`, same slot as `F0E2`). Table 212 keys.
Mapped 77.0%. Page 50 still 0 unknown. Re-decoded 1-169.

Then: `F022` `سے` (14px seen+bari-ye; `جس سے`, `تجربو سے`); `F027` `ز`
(all 118 have nuqta; `زر`); `F0F2` `م` (`دم`, `بنام`); `F07C` `ھ`
(`دودھ`, `پڑھ کے`). `F0E4` is the same `سے` shape on `NOORIN48`.
`F061` is `ای` (`ایک` on 61/99). Table 218 keys. Mapped 77.9%.
Still unknown 1,931 unique. Re-decoded 1-169.

Skipped until a clean isolated crop: `NOORIN82:F030` (119, 100% nuqta,
loop = `ف`/`ق`/`پ`); `NOORIN48:F0F0` (101, two-part ligature);
`NOORIN01:F09B` (94, `دوستی` wants `د`, `پرسے` wants `پ`). Top leftovers
are still NOORIC overlays (`F038` 249). Did not empty-map them.

Once-only pass: 16 lone-row base keys, 12 mapped from crop (`فعلی`,
`مجرا`, `نمک`, `ہے`, `سل`, `جھتا`, `مغز`, `ہضم`, `مشک`, `جیتو`,
`منسوب`, `الف`). Then 8 both-neighbor once keys (`تعجب`, `گلی`,
`ٹھیٹھ`, `تخلیقی`, `طبع`, `پیشا`, `نکلیں`, `کلیں`). Skipped keys
where tight and word crop disagreed. Table 238 keys. Mapped instances
still 77.9% (20 extra instances). Unknown unique 1,911. Once-only
unknown 598. Page 50 still 0 unknown. Re-decoded 1-169.

Next both-neighbor once keys (crop held): `F0BD` `غذ` (`کاغذ`);
`F04E` `ئشا` (`ازمائشاں`); `F025` `البتہ`; `F0D1` `ئنا` (`کائنات`);
`F0B6` `مہمان`; `F083` `تھلا`; `F0B1` `لچھتلنی`; `F022` `پکھیرو`;
`F05F` `پچھے ستھری`; `F036` `بالکل بھلو`; `F04C` `کھجور`; `F0A8`
`غور`; `F086` `تھا`. Table 251 keys. Mapped instances still 77.9%.
Unknown unique 1,898. Once-only unknown 585. Lone-row leftovers are
the 4 skipped keys. Page 50 still 0 unknown. Re-decoded 1-169.

Next both-neighbor once keys (crop held): `F0F6` `بھکا`; `F0C2`
`زخمی`; `F027` `سیلی`; `F0CB` `طبیعت ملنی`; `F04C` `لہجہ`; `F08A`
`قبضو`; `F0BB` `میں`; `F061` `سٹنا`; `F0A7` `غم`; `F0EA` `فیصلہ`;
`F040` `تکو`; `F09B` `ٹھپ`; `F0CC` `جھک`; `F063` `ہے`; `F084` `عبا`
(`عبادت`); `F074` `تسلیم`; `F058` `قبیلو`; `F066` `ڑھتی`; `F05D`
`یمک`; `F0C5` `تھڑ`; `F089` `اکٹھا`. Skipped where tight and word
crop disagreed. Table 272 keys. Mapped instances still 77.9%.
Unknown unique 1,877. Once-only unknown 564. Page 50 still 0 unknown.
Re-decoded 1-169.

Next both-neighbor once keys (crop held): `F0D2` `تلے`; `F060`
`چے` (`چکے`); `F04C` `نجھے` (`سانجھے`); `F0D7` `غصہ`; `F0C8`
`کہہ`; `F056` `سٹن`; `F0F4` `بچھڑ` (`بچھڑتا`); `F0C5` `پھیلنی`;
`F0F1` `پنڈ`; `F0A1` `فطر` (`فطرت`). Skipped where tight and word
crop disagreed. Table 282 keys. Mapped instances still 77.9%.
Unknown unique 1,867. Once-only unknown 554. Page 50 still 0 unknown.
Re-decoded 1-169.

Next both-neighbor once keys (crop held): `F0A1` `ھیلا`
(`دھیلا`); `F039` `رنل` (`جرنل`); `F07A` `نپنی` (`سونپنی`).
Skipped where tight crop and neighbor window disagreed. Clean
both-neighbor once keys with no unknown in the window are now 0.
Table 285 keys. Mapped instances 78.0%. Unknown unique 1,864.
Once-only unknown 551. Page 50 still 0 unknown. Re-decoded 1-169.

Next both-neighbor once keys (crop held): `F092` `مسخری`
(parens on p26); `F0B8` `کپن`; `F0F8` `پٹے`; `F07E` `ﷺ`
(honorific on مصطفیٰ). Skipped where tight crop and neighbor
window disagreed. Short-window both-neighbor once keys are now
exhausted. Table 289 keys. Mapped instances 78.0%. Unknown unique
1,860. Once-only unknown 547. Page 50 still 0 unknown. Re-decoded
1-169.

High-count leftovers (isolated crop plus neighbors): `NOORIN82:F030`
`ند` (119, noon-dal; `دند`, `باند`); `NOORIN48:F0F0` `ھو` (101;
`دھوئے`, `بادھو`); `NOORIN01:F09B` `د` (94; `دوستی`). The old `پرسے`
reading of F09B was `د سے`. Table 292 keys. Mapped instances 78.3%.
Unknown unique 1,857. Once-only unknown 547. Page 50 still 0 unknown.
Re-decoded 1-169.

Next high-count leftovers: `NOORIN57:F070` `خو` (86; `خود`, `خور`,
`خوشی`); `NOORIN63:F0C4` `کھ` (85; `رکھ`, `پرکھ`, `مورکھ`);
`NOORIN01:F076` `گ` (85; `مارگ`, `راگ`, `اگ`). Table 295 keys.
Mapped instances 78.7%. Unknown unique 1,854. Once-only unknown
547. Page 50 still 0 unknown. Re-decoded 1-169.

Next high-count leftovers: `NOORIN57:F075` `سر` (79; `کے سر`,
`سرمائے`); `NOORIN81:F071` `حا` (78; `حال`, `بدحالی`);
`NOORIN82:F053` `ھی` (78; `آدھی`, `ادھی`); `NOORIN07:F071`
`چیز` (78; `اپنی چیز کی`); `NOORIN81:F0BE` `غ` (78; starts
left-column `غرضمند`). Table 300 keys. Mapped instances 79.1%.
Unknown unique 1,849. Once-only unknown 547. Page 50 still 0
unknown. Re-decoded 1-169.

Next high-count leftovers: `NOORIN63:F0C7` `گا` (77; `گال`, `گاں`);
`NOORIN81:F083` `سب` (77; `چیز سب نا`); `NOORIN01:F053` `ا` (75;
isolated alif, `اے`/`اس`); `NOORIN41:F076` `اللہ` (72); `NOORIN17:F0F2`
`ہتھ` (71; `چیز ہتھ`). Table 305 keys. Mapped instances 79.6%.
Unknown unique 1,844. Once-only unknown 547. Page 50 still 0
unknown. Re-decoded 1-169.

Next high-count leftovers: `NOORIN63:F0D0` `اگے` (71; `سوں اگے
ہونو`); `NOORIN01:F060` `ج` (69; isolated jeem, `موج`);
`NOORIN82:F097` `کد` (68; next `پدے`/`ے` makes `کدے`). Skipped
`NOORIN81:F046` (tight crop looks like `ڑ`, neighbor window does
not agree) and `NOORIN83:F0DB` (tiny 3.2px, always followed by
unmapped `F081`/`F082`). Table 308 keys. Mapped instances 79.9%.
Unknown unique 1,841. Once-only unknown 547. Page 50 still 0
unknown. Re-decoded 1-169. Next base leftovers: `NOORIN81:F0AC`
(66), `NOORIN81:F04E` (58), `NOORIN05:F0F0` (57), `NOORIN81:F06D`
(57), `NOORIN01:F06C` (55). Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN81:F0AC` `عا` (66; `دعا کرنی`,
`بدعا`); `NOORIN81:F04E` `ٹا` (58; `آٹانا`); `NOORIN05:F0F0` `تھو`
(57; `تھوڑی`); `NOORIN81:F06D` `چڑ` (57; `چڑھ`); `NOORIN01:F06C`
`ش` (55; `خوش ہونو`). Table 313 keys. Mapped instances 80.2%.
Unknown unique 1,836. Once-only unknown 547. Page 50 still 0
unknown. Re-decoded 1-169.

Next high-count leftovers: `NOORIN63:F0CF` `گی` (55; `زندگی`,
`کرے گی`); `NOORIN82:F05A` `گ` (54; after `فارسی`, next `ر`/`ھ`);
`NOORIN82:F08A` `قد` (53; `قدم`, `کی قد`); `NOORIN57:F049` `لو`
(53; `آلو کھاتاں`, `آلو بالو`). Skipped `NOORIN57:F04B` (tight ye
bowl, but `(سوٹی)` / `(کھی)` / `چھوڑی` windows disagree). Table
319 keys. Mapped instances 80.6%. Unknown unique 1,830.
Once-only unknown 547. Page 50 still 0 unknown. Re-decoded 1-169.
Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN13:F02A` `نیا` (52; prev `دو`
makes `دنیا`); `NOORIN16:F0CC` `ہونو` (52; word-final infinitive);
`NOORIN01:F066` `ز` (50; isolated ze). Skipped `NOORIN83:F026`
(prev often poisoned `اپنوروپ`) and `NOORIN21:F083` (tight crop
`چڑھ` vs window `نہیں ہونی`). Table 322 keys. Mapped instances
80.8%. Unknown unique 1,827. Once-only unknown 547. Page 50 still
0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN81:F07B` `خا` (48; `خاندانی`);
`NOORIN08:F06E` `سے` (47; `کرن سے`); `NOORIN18:F08D` `ئیے` (48;
`آئیے`, `کھائیے`). Skipped several keys where tight crop and
neighbor window disagreed, plus the tiny `F0DC`+`F089` pair.
Table 325 keys. Mapped instances 80.9%. Unknown unique 1,824.
Once-only unknown 547. Page 50 still 0 unknown. Re-decoded 1-169.
Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN57:F059` `بی` (44; `دھوبی`);
`NOORIN05:F04C` `پنے` (42; `آ`+`پنے` → `اپنے`); `NOORIN89:F079`
`خ` (41; isolated khe). Then `NOORIN63:F0E3` `چ` (41; word crops
`مچ خوشی` / `مچ ڈر`, meem is a neighbor); `NOORIN16:F071` `مند`
(41; `شرمندہ`, `مندی`); `NOORIN15:F098` `ھو` (41; next `ڑ` →
`ھوڑ` / `گھوڑ`). Then `NOORIN85:F028` `سیا` (40; `سیانا`,
`سوسیانا`); `NOORIN01:F073` `ف` (40; `خوف کرنو`). Skipped
`NOORIN57:F05A` and `NOORIN25:F075` (tight crops disagree);
`NOORIN59:F0EE` (tiny 4.6px waw, hamza and damma mixed). Then
`NOORIN85:F0BE` `تیر` (40; `تیرانداز`, `کی تیر`); `NOORIN06:F0B4`
`ینی` (40; after `د` → `دینی`). Skipped `NOORIN63:F0B8` (tight
crops `وو` vs `او` disagree). Table 335 keys. Mapped instances
81.4%. Unknown unique 1,814. Once-only unknown 547. Page 50 still
0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN04:F0AF` `بنا` (38; `بنانا`);
`NOORIN60:F0A4` `مصیبت` (38; whole-word ligature); `NOORIN05:F05C`
`پیا` (37; `روپیا`); `NOORIN09:F094` `بچو` (36; next `ں` →
`بچوں`). Skipped `NOORIN12:F088` (`می` vs `گئی`); `NOORIN01:F0A5`
(tight `ڑ` but next is already `ڑ`); `NOORIN82:F081` (always after
skipped tiny `F0DB`); `NOORIN04:F0BD` (`بھر` vs `پھڑ`);
`NOORIN11:F087` (`لنو` vs window `ٹا`/`چھوڑ`); `NOORIN72:F0C1`
(tight isolated `ن` vs word `سوکن`). Table 339 keys. Mapped
instances 81.6%. Unknown unique 1,810. Once-only unknown 547. Page
50 still 0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN17:F0EC` `منہ` (35; `منہ پر`,
`بھیڈ منہ`); `NOORIN15:F04E` `یکھ` (34; prev `د` → `دیکھ کے`);
`NOORIN63:F0E6` `مد` (34; next `د` → `مدد`, `خوشامد`). Skipped
`NOORIN31:F07D` (`ہیں` vs `کہیں`); `NOORIN81:F0A2` (`ضر` before
`ے` vs next `ھ`); `NOORIN14:F0F7` (`میر` vs `میری`/`میرے`).
Table 342 keys. Mapped instances 81.8%. Unknown unique 1,807.
Once-only unknown 547. Page 50 still 0 unknown. Re-decoded 1-169.
Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN82:F064` `ریب` (34; prev `غ`
→ `غریب`); `NOORIN19:F025` `بغیر` (33; `توں بغیر دنیا`). Left
`NOORIN16:F079` for a later crop (`امید` vs neighbor window).
Table 344 keys. Mapped instances 81.8%. Unknown unique 1,805.
Once-only unknown 547. Page 50 still 0 unknown. Re-decoded 1-169.
Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN16:F079` `مید` (33; `امید`,
`میدان`; next `F05A` is alif mapped `ر`); `NOORIN56:F0E8` `رضی`
(33; `غرضی کرنی`). Skipped `NOORIN83:F0D7` (3.2px, always next
unmapped `F026`/`F027` pair). Table 346 keys. Mapped instances
81.9%. Unknown unique 1,803. Once-only unknown 547. Page 50 still
0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN56:F0D2` `شش` (32; prev `کو`
→ `کوشش کرنی`); `NOORIN06:F0C8` `بند` (32; `بندھ`);
`NOORIN11:F02C` `کنڈ` (32; `کی کنڈ`). Table 349 keys. Mapped
instances 82.0%. Unknown unique 1,800. Once-only unknown 547. Page
50 still 0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN04:F0B7` `بہا` (32; next `د`
16x → `بہاد`; `بہاو`); `NOORIN12:F0E1` `گما` (31; `عزت گمانی`);
`NOORIN06:F037` `گیو` (31; Gojri past went). Tight crops clip
gaf bars on `گما`/`گیو`; word crops show `گ`. Table 352 keys.
Mapped instances 82.2%. Unknown unique 1,797. Once-only unknown
547. Page 50 still 0 unknown. Re-decoded 1-169. Do not
empty-map NOORIC.

Next high-count leftovers: `NOORIN57:F039` `پے` (31;
prev `آپ` is `آ` poison → `آپے`); `NOORIN04:F0C8` `بھو`
(31; `بھوں`, `کدے بھوت`). Skipped `NOORIN04:F0DB`
(`پر` vs `پیر`). Table 354 keys. Mapped instances 82.2%.
Unknown unique 1,795. Once-only unknown 547. Page 50 still
0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN11:F059` `کیو` (30;
next `ں` 14x → `کیوں`). Skipped `NOORIN06:F05E` (tight
`کھو` vs word crops); `NOORIN82:F074` (two widths, mixed
windows). Table 355 keys. Mapped instances 82.3%. Unknown
unique 1,794. Once-only unknown 547. Page 50 still 0
unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftover: `NOORIN14:F07E` `رہنو` (30;
`خوش رہنو۔`). Table 356 keys. Mapped instances 82.3%.
Unknown unique 1,793. Once-only unknown 547. Page 50 still
0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN05:F0E5` `تھا` (29;
`تھاں`); `NOORIN01:F061` `چ` (28; `سوچ`). Skipped
`NOORIN12:F042` (tight `میں` vs word crops). Then
`NOORIN56:F0D8` `شو` (28); `NOORIN04:F0D2` `پا` (28;
next `ر` → `پار کرن`); `NOORIN81:F09F` `ضا` (27;
title `رضا`). Table 361 keys. Mapped instances 82.5%.
Unknown unique 1,788. Once-only unknown 547. Page 50 still
0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN81:F04A` `تک` (27;
`ن تک`, `کرگیو`). `NOORIN82:F023` `مت` (27; next
`کرننی`; prev is unmapped `F0D6`). Skipped
`NOORIN57:F021` (tight `بی`, mixed widths, windows
do not agree). Table 363 keys. Mapped instances 82.5%.
Unknown unique 1,786. Once-only unknown 547. Page 50 still
0 unknown. Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftovers: `NOORIN83:F0D6` `ہ` (27;
next `مت` 27x → `ہمت`); `NOORIN51:F0C8` `مطلب` (27;
gloss word). Skipped `NOORIN17:F081` (tight `تھی`
vs `ھی` after `چڑ`/`پڑ`). Table 365 keys. Mapped
instances 82.6%. Unknown unique 1,784. Once-only unknown
547. Page 50 still 0 unknown. Re-decoded 1-169. Do not
empty-map NOORIC.

Next high-count leftovers: `NOORIN04:F0CC` `بھی` (27;
`رک بھی گال`, `کو بھی ایب`). `NOORIN82:F08C` `ع`
(26; `غ` if nuqta → `غریب`, `غرض`; else `عرض`).
Skipped `NOORIN08:F0E8` (tight `تیر` vs `شیر`).
Table 367 keys. Mapped instances 82.7%. Unknown unique
1,782. Once-only unknown 547. Page 50 still 0 unknown.
Re-decoded 1-169. Do not empty-map NOORIC.

Next high-count leftover: `NOORIN01:F074` `ق` (25;
`شوق`). Skipped `NOORIN81:F0AA` (tight `طا` vs `ٹا`)
and `NOORIN81:F07D` (tight `خا`/`خد`, next `ر` vs
`ہمت`). Table 368 keys. Mapped instances 82.7%. Unknown
unique 1,781. Once-only unknown 547. Page 50 still 0
unknown. Re-decoded 1-169. Do not empty-map NOORIC.

---

## 2026-08-17 — Extract easy text, Batool decode, NOORIN transfer test

Ran the agreed easy path.

**FLI corpus** copied to `data/extracted/fli-corpus/` (11 files,
60,814 words). Four folk files still carry 82 `U+FFFF` marks.

**Five `good_text` PDFs** extracted with
`py -3 scripts/extract_clean_text.py` into `data/extracted/clean-pdf/`
plus `provenance.jsonl`. Result is not five Gojri books:

- `ABC-Islamic-Studies` (401), `Essential-Book` (498),
  `Revival-of-Islam` (116): clean English prose. A few Arabic
  quotes only. Not Gojri source text.
- `QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf` (717): fonts are
  ArabicTypesetting / TraditionalArabic / UrduTypesetting, but
  ToUnicode emits CJK garbage mixed with Arabic presentation
  forms. `get_text` is not usable. Needs a different method
  (vision, or a CMap fix).
- `Gojri-Hindi-English-Dictionary.pdf` (458): Kokila Devanagari is
  real Unicode. `GurbaniHindi` glosses extract as Latin (`krnw`,
  `TOkr`). Mixed encoding on the same page.

**Batool** dictionary re-decoded pages 1-498 into
`data/decode/out/gojri-english-dictionary/`. Page 25 still matches
gold letter forms (`آبلائے`, `نھیں`, `مهارو`, `ھُدرو`).

**Kahawat NOORIN** high-count fills: `گی` (F0CF), `سی` (F09E),
`رض` (F06E, completes `غرض`). Skipped `F026` and `F08F` (crop and
neighbor window disagreed). Table 316. Mapped instances 80.4%.
Unknown unique 1,833. Page 50 still 0 unknown. Re-decoded 1-169.

**Transfer test.** Same-scheme PUA NOORIN book `Aks-e-Jamal.pdf`
pages 1-10: 69.6% of instances already map, no extra keys. Javaid
Rahi dictionary part 3 (`gojri-dictionary-by-dr-javaid-rahi-3.pdf`)
pages 1-20: **0%**. Keys look like `NOORIN01:00D4` and
`NOORIC:0051` (Latin-range), not `F0xx`. The manifest tagged that
file `pua` because 30 PUA chars exist; the body is a different
scheme. The Kahawat table cannot decode it. Use
`scripts/decode_noorin_flow.py` only on PUA `F0xx` NOORIN books.

Extracted and decoded page files stay gitignored.

---

## 2026-08-18 — Quran extract is not usable text

User checked `data/extracted/.../page-0017.txt`. Direct `get_text`
is garbage. Confirmed on the PDF, not only the txt file.

Cause: `UrduTypesetting` (Gojri body) and `ArabicTypesetting`
(Arabic ayahs) are Type0 Identity-H. ToUnicode exists but is
wrong. Isolated letters often map to real Arabic (`ا و ر ت ی ہ`).
Joining forms map to `U+FFFD` or to unrelated BMP letters
(`U+1743` Buhid, Latin-extended, IPA). `get_text` then prints
those fake letters, so the page looks like mixed Nastaliq and
noise. `rawdict` can crash (`chr()` above U+10FFFF).

The embedded subset TTF has outlines but **no `cmap`** and no
real glyph names (`glyph00593`). Windows here has no Urdu
Typesetting font to borrow a cmap from. A GID decode table is
still possible (subset has 927 glyphs).

Actions:
- Deleted the 718 extracted Quran txt files.
- Manifest scheme is now `broken_tounicode` (717 unique pages).
- Classifier checks UrduTypesetting/ArabicTypesetting plus
  garbage-char count, and only if PUA is low, so PUA books stay
  `pua`.
- Extractor skips a book if sample garbage_ratio > 0.08.

Good-text unique pages: 1,473. Pages still needing decode or
OCR: 15,478. Do not copy-paste or `get_text` this Quran PDF.

---

## 2026-08-18 — Quran GID decode table (Option 1)

Built a GID table for `QURANIC_TRANSLATION_in_GOJRI_by_Dr_Rafiq.pdf`.
Key is `FONT:GID` from `get_texttrace`. `rawdict` still crashes
(`chr()` above U+10FFFF). Long `get_texttrace` runs can crash
PyMuPDF on exit, so census and decode run in 10-15 page child
processes.

Auto-seed: a GID is mapped when ToUnicode is a real Arabic or
ASCII letter on at least 90% of occurrences. Pages 1-717:
976 unique keep keys, 548 auto+manual table keys after the
first census write, then 551 after empty overlay keys.
Table-instance coverage 84.5%. That count does not include
zero-width nuqta GIDs, which the decoder applies as overlays
instead of extra letters.

Nuqta rule: width under 0.4 px plus a real Arabic ToUnicode
letter names the next host tooth (`ب ت ن ی` and kin). This
turned `کا نباں` into `کا ناں` and `تععال` into `تعالٰی`.

Manual body fills from page 16-17 crops include `ے ش س ج ھ ہ م ح ل ع`.
Empty maps hide leftover FFFD overlay bodies (`619`, `394`, `620`).

Decode: `py -3 scripts/decode_quran.py 1 717` writes
`data/decode/out/quranic-translation-gojri/` (gitignored).
Page 16 line 4 reads:

`)شروع( الله تعال ٰی  کا ناں سنگ، جھڑو بہت مھربان نہایت رحم آلو ہے۔`

Known gaps for the user check: `مھربان` vs `مہربان`, `آلو` vs
`آلا`, missing spaces (`تےنہایت`), Arabic ayah joining GIDs
still placeholders, running header still has `U+FFFD` in
`اﻟکریم`-like title text. Do not mix this table with Batool
or NOORIN.

---

## 2026-08-22 — Quran page 16 aligned to screenshot gold

User screenshot of Surah Fatiha is the gold for page 16 Gojri
lines. Locked known letters, filled the unknown GIDs in the
gaps. Table now 570 keys.

Gojri fills: `جہڑو`/`مہربان` (`800`=`ہ`, not `ھ`), `واسطے`
(`433`=`س`, `686`=`ط`), `کل`/`کو`/`کہ` (`505`/`515`/`516`/`538`=`ک`),
`پالنہار` (`552`=`ل`, `622`=`ن`), `رستو` (`427`=`س`), `ہویو`/`آیو`
(`403`=`ی`), `جنہاں` (`413`=`ج`, `618`=`ن`), `قہر` (`500`=`ق`),
`طلبگار` (`768`=`ل`, `617`=`ب`). `406` is empty so noon nuqta
can set `اُنھاں`. Decoder no longer inserts a word space before
a combining mark.

Still open on this page: verses 4-5 share one y-cluster so
glyphs mix; `بھٹلیا` vs `بھلیا` (`768` is `ل` in `طلبگار`);
Arabic ayah joining GIDs; `تےنہایت` missing a space.
Check `data/decode/out/quranic-translation-gojri/page-0016.txt`.

### NOORIN table 371 (2026-08-19)

Added `NOORIN48:F0F1` = `ے` (bari ye, prev چڑ/پڑ/ڈر → چڑے, پڑے),
`NOORIN08:F02A` = `ستا` (seen-te-alif, prev د → دستا = gave),
`NOORIN15:F095` = `کھٹ` (kaf-he-tte, next نہیں 5x → کھٹ نہیں).
Skipped: `NOORIN01:F09F` (tiny, neighbors unmapped),
`NOORIN01:F070` (ambiguous shape at 6.2px),
`NOORIN82:F09E` (conflicting context, گھ in one window, doesn't fit others).
Census: 2,149 unique, 371 mapped, 82.8% instances, 1,778 unknown.

### NOORIN table 373 (2026-08-19)

Added `NOORIN12:F0C7` = `ے` (bari ye, seen in `اور...` word),
`NOORIN14:F0B9` = `پ` (pe stem with dot, seen before `ھتکوش` and in `...پڑھ...` contexts).
Skipped: `NOORIN01:F09F` (tiny, neighbors unmapped), `NOORIN01:F070` (ambiguous shape), `NOORIN82:F09E` (conflicting context).
Census: 2,149 unique, 373 mapped, 82.9% instances, 1,776 unknown.

### NOORIN table 375 (2026-08-19)

Added `NOORIN04:F088` = `ھ` (he, between `پ` and `ما` in page text),
`NOORIN56:F0EE` = `ی` (farsi-ye, dotted ye variant, before `ک`).
Skipped: `NOORIN01:F09F` (tiny, neighbors unmapped), `NOORIN01:F070` (ambiguous shape), `NOORIN82:F09E` (conflicting context).
Census: 2,149 unique, 375 mapped, 82.9% instances, 1,774 unknown.

### NOORIN table 377 (2026-08-19)

Added `NOORIN05:F0E0` = `گ` (forms `اگر`-like pattern in page text),
`NOORIN09:F097` = `پ` (precedes `ڑ...` patterns, forms `پڑ...`).
Skipped: `NOORIN01:F09F` (tiny, neighbors unmapped), `NOORIN01:F070` (ambiguous shape), `NOORIN82:F09E` (conflicting context).
Census: 2,149 unique, 377 mapped, 83.0% instances, 1,772 unknown.

### NOORIN table 381 (2026-08-19)

Added `NOORIN62:F0D2` = `و` (wau, always between `ر` and `ں`, forms `روں`),
`NOORIN63:F0C0` = `ل` (lam, visible in `گو کل کھا` on page 20),
`NOORIN48:F0F9` = `ئع` (ligature, forms `ضائع` on page 23),
`NOORIN04:F02B` = `ین` (ligature, forms `دین` on page 6).
Skipped: `NOORIN82:F087` (ambiguous context, could be alif or separator).
Census: 2,149 unique, 381 mapped, 83.1% instances, 1,768 unknown.
All remaining high-count unknowns (n>=22) are in the skip set. Further
gains require revisiting skipped keys with better evidence or dropping
to the n<22 long tail.

### NOORIN table 385 (2026-08-19)

Added `NOORIN82:F033` = `غ` (ghain initial, forms `غمں نال` on page 13),
`NOORIN16:F06F` = `نا` (nun+alif ligature, forms `مناسب` on page 44),
`NOORIN10:F0C2` = `تا` (te+alif ligature, forms `کتاب` on page 6),
`NOORIN06:F0C4` = `و` (wau, `ر[glyph]ں` pattern = `روں`, same as F0D2).
Skipped: `NOORIN83:F0E0` (w=3.2, tiny connector), `NOORIN15:F0D1`
(ambiguous final form), `NOORIN01:F06F` (unclear word-initial particle),
`NOORIN82:F087` (ambiguous separator).
Census: 2,149 unique, 385 mapped, 83.2% instances, 1,764 unknown.

### NOORIN table 388 (2026-08-19)

Added `NOORIN14:F052` = `تو` (te+wau, forms `رہتو۔` / `سکتو۔` at sentence end),
`NOORIN59:F0F6` = `یس` (ye+sin ligature, forms `پردیس` on page 28),
`NOORIN12:F08A` = `یا` (ye+alif ligature, nuqta always true, forms `گیاں`).
Skipped: `NOORIN81:F075`, `NOORIN81:F087` (ambiguous connectors),
`NOORIN85:F0B6`, `NOORIN41:F09C`, `NOORIN09:F051`, `NOORIN04:F058`,
`NOORIN12:F0BE`, `NOORIN30:F06C` (mixed/unclear contexts).
Census: 2,149 unique, 388 mapped, 83.3% instances, 1,761 unknown.
Remaining non-skip keys are all n<=21 with increasingly mixed neighbor
patterns. Gains per key are diminishing.

### NOORIN table 393 (2026-08-19)

Re-examined skipped high-count keys with updated table. Several now
had enough decoded neighbors to identify.
Added `NOORIN83:F026` = `نڈ` (nun+dal ligature, visible in `بھانڈا`),
`NOORIN21:F083` = `ڑ` (retroflex re, visible in `بھیڑ`),
`NOORIN81:F046` = `و` (wau isolated, `تحقیق و ترتیب` page 1),
`NOORIN06:F046` = `لد` (lam+dal ligature, `مطلب لد ہونو` page 17),
`NOORIN05:F063` = `یر` (ye+re ligature, visible in `پیر`).
Skipped: `NOORIN83:F0DB` (w=2.8, sub-glyph connector before ع/غ),
`NOORIN57:F04B` (mixed contexts), `NOORIN82:F089` (always word-initial,
too wide to pin).
Census: 2,149 unique, 393 mapped, 83.6% instances, 1,756 unknown.

### NOORIN table 395 (2026-08-19)

Added `NOORIN82:F089` = `وقت` (3-char ligature, always word-initial,
visible in `وقت توں` page 56),
`NOORIN63:F0B8` = `قو` (qaf+wau, forms `قوم` on page 5).
Skipped: `NOORIN83:F0DC` (w=3.2, sub-glyph connector before وقت),
`NOORIN13:F0A8` (ambiguous medial, inconsistent crops),
`NOORIN25:F075` (crop showed possible table error in NOORIN01:F067),
`NOORIN82:F0AA`, `NOORIN26:F0C9`, `NOORIN59:F0EE` (mixed/tiny).
Census: 2,149 unique, 395 mapped, 83.7% instances, 1,754 unknown.

### NOORIN table 396 (2026-08-19)

Added `NOORIN83:F0DC` = `ھ` (connector before `وقت(عقل)`).
Skipped: `NOORIN13:F0A8` (still ambiguous in crops).
Census: 2,149 unique, 396 mapped, 83.8% instances, 1,753 unknown.

### NOORIN table 398 (2026-08-19)

Added `NOORIN83:F0DB` = `غ` (removed brackets in page-0006 line 18),
`NOORIN82:F082` = `و` (same context, page-0006 line 18).
Census: 2,149 unique, 398 mapped, 83.9% instances, 1,751 unknown.

### NOORIN table 399 (2026-08-19)

Added `NOORIN57:F04B` = `ں` (forms `یارںکرنپدے` and `کیکھں،کاپدے` on page 25).
Census: 2,149 unique, 399 mapped, 83.9% instances, 1,750 unknown.

### NOORIN table 400 (2026-08-19)

Added `NOORIN26:F0C9` = `چ` (removed bracket on page 10 line 15, forming `چکرنریںپ۔`).
Census: 2,149 unique, 400 mapped, 84.0% instances, 1,749 unknown.

### NOORIN table 406 (2026-08-22)

Verified trial maps from prior turn: `NOORIN57:F05A` = `ج`, `NOORIN25:F075` =
`بجھار` (page 5 `تبجھارکت`, page 153 `(بجھارکت)`).
Added `NOORIN82:F0AA` = `لت` (crops: page 6 `حالت`, page 19 `ذلالت`).
Added `NOORIN12:F088` = `گئی`, `NOORIN85:F0B6` = `تھی` (page 5 `کی گئی تھی`).
Added `NOORIN13:F0A8` = `س` plus neighbor rule in `dump_noorin_lines.py`:
prev `NOORIN01:F053`(ا) + next `NOORIN01:F079`(ے) → `س` (`اسے`, 7x); prev
`NOORIN01:F05A`(ر) + next `NOORIN01:F079` → `ہ` (`رہے`, 41x).
Census: 2,149 unique, 406 mapped, 84.3% instances, 1,743 unknown.
Skipped: `NOORIN01:F0A5` (context-dependent: `گہنو[F0A5]ڑھیں` vs narrow
connector), `NOORIN59:F0EE` (w=4.6 joiner).

### NOORIN table 410 (2026-08-22)

Added `NOORIN11:F0A2` = `جلد` (page 5 `دساں جلداں`, `چھ جلداں`).
Added `NOORIN41:F09C` = `محنت` (page 6 `بڑی محنت نال`).
Added `NOORIN81:F075` = `حد` (page 7 `کسے حد تک`; not `NOORIN57:F075`=سر).
Added `NOORIN81:F087` = `سد` (page 11 proverb `پر ایو سدھار` side).
Skipped `NOORIN63:F0B9` (mixed: `و[F0B9]گوج`, `با[F0B9]ے`, `با[F0B9]چھوڑ`).
Skipped `NOORIN21:F0A2` (Urdu `بلکے` vs wide-crop `پھیر` on other rows).
Census: 2,149 unique, 410 mapped, 84.4% instances, 1,739 unknown.

### NOORIN table 411 (2026-08-22)

Added `NOORIN82:F081` = `ض` (38/38 hits follow `NOORIN83:F0DB`=غ; decode
`غضر`, `غضب`, `غم`).
Added neighbor rules in `dump_noorin_lines.py`:
`NOORIN08:F081` prev ر next ے → empty (`رے`, 12x); prev ل next ں → `ا`
(`سالاں نال`, 4x).
`NOORIN09:F051` next `NOORIN82:F063` → `ٹھنڈ` (`ناٹھنڈیار`, 3x).
`NOORIN04:F058` next `NOORIN63:F0C6` → `بچa` (`بچاکے`, p9).
Skipped `NOORIN12:F0E2` (crop p85 = `گھی`, p14 = `گئی`; not one map).
Skipped `NOORIN12:F0BE`, `NOORIN04:F0BD` (context-dependent on other rows).
Census: 2,149 unique, 411 mapped, 84.4% instances, 1,738 unknown.

### NOORIN table 413 (2026-08-22)

Added `NOORIN12:F0E2` = `گھی` (crops p85/p111/p122; proverb گال گھی نال).
Rule: next `NOORIN12:F07B` → `بال`; paired rule `NOORIN12:F07B` prev F0E2 → `وں`
(p14 `بالوں`).
Added `NOORIN12:F0BE` = `ل` (default). Rule: next `NOORIN82:F063` → `لیا`
(p11 `آپوں لیا یار`; p129 `ساک لئی`).
Added `scripts/_tmp_crop_exact.py` for row-y crops (first-hit `_tmp_mark_key_page`
often lands on the wrong line).
Census: 2,149 unique, 413 mapped, 84.5% instances, 1,736 unknown.

### NOORIN table 416 (2026-08-22)

Added `NOORIN05:F05D` = `شکر` (crops p61/p111: `گھی شکر`, `شکر کی پوٹ`).
Added `NOORIN08:F0D4` = `دشمن` (crop p15: `دو دشمن نا ڈر`).
Added `NOORIN04:F058` = `بچ` (default). Rule: next `NOORIN63:F0C6` → `بچا`
(p9 `بچاکے`, p79 `بچانا`, p138 `بچ` + overlay tail).
Extended `NOORIN09:F051` rules: next `F063`/`F07A`/`F09B` → `ٹھنڈ` (13x).
Next `F07D` still unknown (p34/p35 `نہ[F051]پدے`, 3x).
Census: 2,149 unique, 416 mapped, 84.5% instances, 1,733 unknown.
Verified: p15 `دودشمنناڈر`, p61 `گھیشکر`, p29 `کیٹھنڈدل`, p9 `بچاکے`.

### NOORIN table 417 (2026-08-22)

Added `NOORIN09:F051` = `ٹھنڈ` (all 20 hits). Rule: next `NOORIN01:F07D`
→ `چھوڑ` (p34/p35/p154 `تنے نہ چھوڑ پدے`, 3x). Crops p56/p64/p115 confirm
ٹھنڈ; p34/p35 tight-y crops bleed Urdu parallel line, but glyph order
(F051 before پدے) matches چھوڑ proverb.
Added `scripts/_tmp_crop_col.py` for L/R column crops.
Census: 2,149 unique, 417 mapped, 84.6% instances, 1,732 unknown.
Verified: p6 `ناٹھنڈیار`, p34/p154 `نہچھوڑپدے`, p56 `ناٹھنڈریںپ`, p64 `ٹھنڈرنا`.

### NOORIN table 418 (2026-08-22)

Added `NOORIN12:F07B` = `گھڑی` (all 20 hits). Crops p49/p77/p135 confirm
گھڑی ligature. Rules: prev `F0E2` → `وں` (p14 `بالوں`, kept); next `F07D`
→ `گھڑے` (p52/p79/p135 `…گھڑےپدے`); next `F02C` → `گھڑیں` (p40).
Census: 2,149 unique, 418 mapped, 84.6% instances, 1,731 unknown.
Verified: p14 `بالوں`+`گھڑی`, p40 `گھڑیںریںپ`, p49 double `گھڑی`, p52 `گھڑےپدے`.
Skipped `NOORIN30:F06C` (20 hits): لینو on p18/p61/p66 but کرن+[F06C] on
p35 needs کرنو; tight crops still bleed Urdu parallel lines.

### NOORIN table 420 (2026-08-22)

Added NOORIN30:F06C = لینo (20 hits). Added NOORIN16:F055 = سر (p18).
Rule NOORIN14:F07A after F0E1: n; next F07A: نو (p107 گمانo).
Census: 420 mapped, 84.6%%, 1,729 unknown.
Skipped NOORIN82:F038 (19 hits): mixed contexts.

### NOORIN table 422 (2026-08-22)

Added NOORIN59:F0EE = و, NOORIN01:F0A5 = د. Rule NOORIN82:F038 after ک.
Census: 422 mapped, 84.7%%, 1,727 unknown.

### NOORIN table 424 (2026-08-22)

Added NOORIN04:F0BD = ر (37 hits). Crops p63/p72: پھر، بھرے، سورپدے.
Added NOORIN11:F087 = نو (37 hits). Crops p17/p21: بولنو، ٹالنو.
Census: 424 mapped, 84.8%%, 1,725 unknown. Page 50 still zero unknowns.
Next: NOORIN82:F038 (9 hits still rule-only), NOORIN14:F07A (12 hits).

### NOORIN table 425 (2026-08-22)

Added NOORIN72:F0C1 = کن (37 hits). Crops p56/p110: سوکن.
Rules: F07A line-start ر, after کی→ہنڈ; F038 after ما→ر, after با+:→نگ,
after کا+مند→ر, after ک+پکڑn→ھ.
Census: 425 mapped, 84.9%%, 1,724 unknown. Page 50 still zero unknowns.
Verified: p56 سوکننا, p87 کیہنڈ, p143 مارچھoڑ, p112 کھپکڑn, p158 line-start ر.
Next: F038 first hit in p76 (ر[F038]،), F07A after گor (p124).

### NOORIN table 426 (2026-08-22)

Added NOORIN31:F07D = کہیں (35 hits). Crops p10/p93. Not NOORIN01:F07D (پدے).
Rules: F07A after ر before د/کو → empty (گورد); F038 after ر before ، → نگ;
F038 after با before کو → نگ.
Census: 426 mapped, 84.9%%, 1,723 unknown. F31:F07D fully mapped.
Verified: p10 موچھمکہیں, p76 ڈررنگ/بانگ, p124 گورد, p125 بانگکوے.
Next: NOORIN82:F038 (9 hits), NOORIN14:F07A (2 hits), NOORIN81:F0A2 (34).

### NOORIN rules batch (2026-08-22)

No new flat keys (still 426). Neighbor rules only:
- `NOORIN81:F0A2`: empty before `NOORIN01:F07A` (ھ). 32/34 hits. Verified p85 `ھک`, p112 `ھکھے`.
- `NOORIN14:F07A`: prev `F057` (آپ) + next `F0E1` (گma) → `ن`. Verified p17 `آپنگمان`.
- `NOORIN82:F038`: prev ک + next `F0A2` → `ھ`; prev ر + next `F044` (ت) → `نگ`; prev با + next `F058` (۔) → `نگ`.
Census flat-map stats unchanged (426 keys, 84.9%%, 1,723 unknown). Decode placeholders for F0A2/F07A/F038 are now zero across pages 1-169.
Verified: p112 `کھپکڑn`, p150 `نگت` / `بانگ`.
Next: `NOORIN14:F0F7` (34 decode placeholders), `NOORIN83:F0D7` (33).

### NOORIN table 429 (2026-08-22)

Added flat maps `NOORIN83:F0D7` = `د`, `NOORIN82:F027` = `ر`, `NOORIN82:F026` = `ر`.
Pair `F0D7`+`F027`/`F026` → `در` (p16/p51 `درما`, p146 `درد`).
Rules: `NOORIN14:F0F7` empty before `F07A` (8 hits); after `کی` before `:` (3); after `ر` before `ت` (2).
Census: 429 keys, 85.0%%, 1,720 unknown. F0D7/F026/F027 fully mapped. F0F7 decode placeholders 34→21.
Verified: p16 `درماے`, p51 `دررما`, p58 `تھار`, p13 `ر در`.
Next: remaining `NOORIN14:F0F7` (21), `NOORIN04:F0DB` (31), `NOORIN86:F025` (227 overlay).

### NOORIN F0F7 rules extended (2026-08-22)

Extended `NOORIN14:F0F7` neighbor rules (no new flat keys; still 429).
Added: empty after `ر` before `کو`/`:``/`۔`/double-`ر`; after `،` before `ریںپ`; after `در`
before `ر`; after `ل` before `ر`; line-start; after `سے`; prev `F0F7` + next `پدے` → `ا`.
Decode placeholders 21→7. Verified: p83 `رکو`, p150 `اپدے`, p66 `نسے`, p113 cleaned.
Skipped `NOORIN04:F0DB` (31 hits, mixed: `سیاو→سیانا` vs `rnaے` vs `ترک`).
Next: 7× `F0F7`, `NOORIN04:F0DB`, `NOORIN10:F072`.

### NOORIN F0F7/F072/F0DB rules (2026-08-22)

No new flat keys (still 429). Neighbor rules only:
- `NOORIN14:F0F7`: finished joiner (34→0 decode placeholders). Added: after `س` before `گhr`→`ے` (p107 `سے گhr`); prev `F072` before `پdے`→empty (p85 `اپdے`); plus prior batch (ر/در/ل/سے/line-start/…).
- `NOORIN10:F072`: after `کی`/`کو`→`ہی`; before `F0F7`→`ا` (p85); after `نے`→`اک` (p106). 6→1 placeholder (p35 only).
- `NOORIN04:F0DB`: context rules (31→17 placeholders). `سیاو`+`ری`→`ن` (p111 `سیانا`); `rna`+`ے`→`ے` (5×); `کو`/`ترک` before `:`→empty; `نال` before `،`→`，`.
Census unchanged: 429 keys, 85.0%%, 1,720 unknown.
Verified: p85 `ا پdے`/proverb ہتھ, p107 `سے گhr`, p111 `سیاون`, p96/p141 `کی ہی`/`کو ہی`.
Next: `NOORIN04:F0DB` (17), `NOORIN10:F072` (p35), `NOORIN86:F025` overlay family.

### NOORIN F0DB finished (2026-08-22)

Added flat maps `NOORIN27:F098` = `نیچی`, `NOORIN17:F041` = `کر` (431 keys).
Finished last `NOORIN04:F0DB` decode placeholders (17→0 book-wide):
- p154: prev `F098` next `F0D9` → `بیری` (`نیچی بیری ہر کوئی…`).
- p128: `F04A` next `F0DB` → `سخت`; prev `F04A` next `F063` → `ب`; `F063` prev `F0DB` → `یر`; `F099` prev `F063` next `F023` → ` یا` (`سخت بیر یا…`).
- p22: `F09D` after `NOORIN57:F05A` before `F041` → `و`; prev `F041` next `F05A` → empty; `F05A`/`F056` empty in `F0DB`…`F0C3` chain (`رجوکر کو نہیں`).
Also finished `NOORIN10:F072` (p35 `ںت ہی :`).
Census: 431 keys, 85.0%%, 1,718 unknown (flat maps only).
Verified: p22 `رجوکر کو`, p128 `سختبیر یا…`, p154 `نیچیبیری ہر…`.
Next: `NOORIN06:F05E` (28 other contexts), `NOORIN82:F074` (27), `NOORIN12:F042` (25).

### NOORIN86 overlay + F023 batch (2026-08-22)

Empty-mapped 38 remaining `NOORIN86:*` nuqta overlay codes (228× `F025`, etc.).
Table 470 keys. Instance coverage 85.0%% → 85.9%% (1,718 → 1,679 unknown base keys).
`NOORIN34:F023` context rules (7 hits, all `دشمنی` splits): prev `F08A` → `شمنی`;
prev `F099` next `F083` → `دشمنی`; prev `F099` else → `شمنی`.
`NOORIN01:F099` before `F023` → `د` (except after `F063` → ` یا`).
Flat `NOORIN05:F035` = `پکی` (p30/p110 gloss head).
Verified: p30 `پکی دشمنی`, p62 `دشمنی کی`, p68/p84 `دشمنی`, p128 `سخت بیر یا دشمنی`.

### خواہ مخواہ + ٹھوکر + بولیں batch (2026-08-22)

Table 471 keys (+`NOORIN16:F023`=مخو). Unknown base keys 1,679 → 1,678.
`NOORIN81:F07B` before F07B+F023 → `خو`; `NOORIN01:F07B` beside F023 → `اہ`.
`NOORIN06:F05E` after `NOORIN56:F0CE` before `NOORIN82:F099` → `ٹھو` (3×).
`NOORIN57:F031` between F057/F042 → `بو`; `NOORIN12:F042` after F057 → `لیں` (5×).
`NOORIN82:F074` after F07A before F05A → `ویہ` (2 clear; p71 still open).
Verified: p84 `خواہ مخواہ دشمنی`, p52 `پسو ٹھوکرنو`, p70/p92 `…موچھم بولیں`, p151 `سو ٹھوکرنو`.
Next: other `F05E` contexts (23), other `F042` (10), other `F074` (19).

### F05E / F042 / F074 context batch (2026-08-22)

Extended neighbor rules (table stays 471 keys).
`NOORIN06:F05E`: `F0D1`/`F0D1`→empty (p73 جھوٹھی لاکھ لاو); line-start before `F033`→`جو ٹھو ` (p72).
`NOORIN57:F031` before `F042`→`بو`; `NOORIN12:F042` before `۔` or line-end→`لیں` (19× بولیں).
`NOORIN82:F074` after `F07A`: before `F055`→`یہ`; before `F05A`/`F0E6`/`F02C`→`ویہ`.
Placeholders: F05E 23, F042 10, F074 19 (down from 28/25/27).
Verified: p52/p12 `…موقع پر بولیں`, p73 `رات کوڑ…یہ`, p137 `…گیا ویہ`.

### F042 flat + F05E/F074 batch (2026-08-23)

Table 472 keys (+ flat `NOORIN12:F042`=`لیں`). F042 decode placeholders **0**.
`NOORIN06:F05E`: line-start/`F065`→`ٹھوڈی`; line-start/`F099`→`ٹھوکرے جا` (F099/F07D empty);
after `F0A5` before `:`/`۔`→`رٹھو`. `NOORIN82:F074` after `۔`→`یہ`.
Placeholders: F05E 20, F042 0, F074 18.
Verified: p64 `ٹھوڈی پکڑننی` / `ٹھوکرے جا نو`, p100 `کالیں`, p58 `بولیں،`, p159 `ہونلیں`, p6 `۔یہ`, p124 `رٹھو`.
Next: remaining F05E (20) and F074 (18) one-offs.

### F09F + F05E/F074 batch (2026-08-23)

Table 473 keys (+ flat `NOORIN01:F09F`=`ڈ`). Instance coverage 85.9%% → 86.0%%.
`NOORIN06:F05E`: after F09F→`ھو` (ڈھو); نا+کرن→`ٹھو`; before کھا after کی→`جو ٹھو `;
before کی→`جوٹھو`; line-start/after ، before ک→`ٹھو`.
`NOORIN82:F074`: after ھ→`ویہ` (all remaining nexts); after سا/و/line-start:`→`یہ`; after ج→`ی`.
Placeholders: F05E 9, F074 7 (was 20/18).
Verified: p91 `ڈھو کرنو`/`ڈھوڈھو ت`, p71 `جوٹھو کو نہیں کھاتو`, p78 `نا ٹھوکر`, p121 `جو ٹھو کھا`, p8 `ھویہ سرسر`, p101 `سایہ`, p44 `یہ:`.
Next: remaining F05E (9) and F074 (7) one-offs.

### F05E close-out + F038/F0A2 (2026-08-23)

Table still 473 keys. Flat-map coverage 86.0% (rules do not change census %).
`NOORIN06:F05E`: removed false cross-column `ٹوٹھو`; line-start before س→`جھوٹو ا` (p140);
line-start before :→`ھو` (p132 column edge of ڈھو). Placeholders: F05E 1 (p64 F032 only), F074 0.
`NOORIN81:F0A2`: حا+…+ے→`ضر ہ` (حاضر ہے); after F022 before ک→`ضرر `. 0 leftovers.
`NOORIN82:F038`: after F0AF/ڈ/ڈر/د→`نگ` (بوزنگ، ڈنگ، دنگ). F065 before F038→`ڈ`. Leftovers: p154, p156.
`NOORIN14:F07A`: 1 left (p100 after F031، سانجھی).
Verified: p140 `جھوٹو ا سچیز…`, p5 `حاضر ہے`, p91 `ڈ نگ ٹپائی`, p101 `دنگکرنو`.
Next: p64 F032+F05E; F038 p154/p156; F07A p100; or next high-count base unknowns.

### Leftover close-out batch (2026-08-23)

Table 473 → 475 keys (+`NOORIN26:F032`=`گا`, `NOORIN89:F031`=`نجھی`). Coverage still 86.0%% (69321 mapped).
Unknown keys 1,676 → 1,674.
`گاٹھوری` (p64): F032=`گا`, F05E→`ٹھو`, F067→`ری`.
p154: `نہ ہنگ لگے نہ پھٹکڑی تے رنگ چوکھا` (F07D/F0D1/F044/F067/F038/F061 rules).
p156: کا+مند F038 `ر`→`نگ` (کانگ); ڈر+ر+F038→`ڈانگ`.
`سانجھی ہنڈی` (p100): F031=`نجھی`, F07A after F031 empty, NOORIN14:F07A→` ہنڈی`.
Placeholders: F05E/F038/F07A/F032/F031 all 0.
Next: high-count base unknowns from `_tmp_top_base.py`.

### High-count base batch (2026-08-23)

Table 475 → 480 keys. Coverage 86.0%% → 86.1%% (69401 mapped). Unknown keys 1,674 → 1,669.
| Key | Map | Check |
|---|---|---|
| `NOORIN14:F0B7` | ھ / ھیان | دھڑ، چڑھنا، دھیان |
| `NOORIN82:F040` | د/دے | کھادے (پدے→ے) |
| `NOORIN18:F0A9` | پئی / اپنی | اپنی پئی پرئی؛ آپ اپنی سر |
| `NOORIN01:F062` | طرح | اسطرح، مندی طرح |
| `NOORIN08:F053` | س | اسطرح (before طرح) |
| `NOORIN12:F076` | partial | گھاٹو، بھوک؛ 13 contexts left |

Next: finish `F076`, or next top-base keys (`F04A`, `F0A4`, `F024`, `F071`, `F0F0`, `F06A`).

### F076 close-out + four flat maps (2026-08-23)

Table 480 → 484 keys. Coverage 86.1% → 86.2% (69477 mapped). Unknown keys 1,669 → 1,665.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F076` | rules | گھاٹو، گھاٹ، گھوڑو p134; F05E→ٹ; F0F0→empty; 0 leftovers |
| `NOORIN81:F0A4` | طا | طاقت p19/67; طوطا p39/70 |
| `NOORIN48:F0EB` | ہم | p16/p17 red-box crops |
| `NOORIN57:F024` | چ | وچ p29; بیچ p26 |
| `NOORIN57:F04A` | ٹھ | جھوٹھ p19; اٹھ p20; کاٹھ p120 |

Next: top unknown `NOORIN82:F071` (n≈19), then `NOORIN82:F0F0`, `NOORIN06:F06A`.

### F071 / F0F0 / F06A batch (2026-08-23)

Table 484 → 488 keys. Coverage stays 86.2% (69536 mapped). Unknown keys 1,665 → 1,661.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F071` | `ایک` | p24/p35/p134 red-box crops |
| `NOORIN63:F0F0` | `من` / `ں` | p24/p129 من; rule prev F068 next *:F06A → ں (p36 میں) |
| `NOORIN08:F06A` | `اس` / rules | prev F083→سکو p45; prev F037→اسکو p68/p69; prev+next F05A→اسکو |
| `NOORIN06:F06A` | `اس` | p36 only (2 hits); same word as F08 on p36 |

Next: `NOORIN16:F078`, `NOORIN83:F0DE`, `NOORIN12:F043` (n≈18).

### F078 / F043 / F0DE batch (2026-08-23)

Table 488 → 492 keys. Coverage 86.2% → 86.3% (69612 mapped). Unknown keys 1,661 → 1,657.

| Key | Map | Check |
|---|---|---|
| `NOORIN16:F078` | `میا` | میاں p16; میاؤں p40; کامیاب p6; 0 leftovers |
| `NOORIN12:F043` | `لیو` | من لیو ہے p24; کالا لیو p17; بولیو p20; 0 leftovers |
| `NOORIN83:F0DE` | empty | joiner before NOORIN81 *ل; 0 leftovers |
| `NOORIN82:F087` | `قا` | قا+بل=قابل p5 |
| F0DE+`F02E` | `بل` | قابل; بل سکے p27 |
| F0DE+`F03E` | `پل` | جم، پل p4 |
| F0DE+`F04C` | `تل` | تل دھرن p57 |
| F0DE+`F054` | `ٹل`/`اٹل` | کم ٹل; موت اٹل (prev F05A) |

Next: top unknown `NOORIN56:F0DF`, `NOORIN81:F09C`, `NOORIN82:F09A` (n≈18).

### F0DF / F09C / F09A batch (2026-08-23)

Table 492 → 495 keys. Coverage 86.3% → 86.4% (69666 mapped). Unknown keys 1,657 → 1,654.

| Key | Map | Check |
|---|---|---|
| `NOORIN81:F09C` | `صد` | صدیاں; صدقہ; 0 leftovers |
| `NOORIN82:F063` after F09C | `یا` | not `یاں` (avoids `صدیاںں`) |
| `NOORIN63:F0B8` after F09C | `قہ` | صدقہ |
| `NOORIN82:F09A` | `کڑ` / `کڑی` / `کھڑ` | اکڑ; دوکڑ; آکڑ/آکھڑ; 0 leftovers |
| `NOORIN56:F0DF` | `اصو`/`اصولی`/`اصولو`/`صورت`/`صور` | اصولو p113; 0 leftovers |
| `NOORIN63:F0E0`/`F0DF` after F0DF | empty | tails of اصولی/اصولو |

Next: `NOORIN85:F0BB`, `NOORIN06:F056`, `NOORIN52:F099` (n≈18).

### F0BB / F056 / F099 batch (2026-08-23)

Table 495 → 498 keys. Coverage 86.4% → 86.5% (69720 mapped). Unknown keys 1,654 → 1,651.

| Key | Map | Check |
|---|---|---|
| `NOORIN85:F0BB` | `تیا` | تیار؛ تیاری؛ موتیاں؛ رتیاں؛ 0 leftovers |
| `NOORIN06:F056` | `ٹھا` | ڈٹھا؛ ٹھا؛ ٹھار؛ اٹھا with F051/F05A→ا؛ 0 leftovers |
| `NOORIN01:F051` before F056 | `ا` | was empty gutter; only this next |
| `NOORIN01:F05A` before F056 | `ا` | اٹھانو p92؛ 4 pairs |
| `NOORIN52:F099` | `سمجھ` | سمجھآنی؛ سوچ سمجھ کے؛ 0 leftovers |
| `NOORIN01:F057` after F099 | `آ` | not `آپ` (avoids سمجھآپنی) |

Next: run `_tmp_top_base.py` for the next n≈18 cluster.

### F0DE / F061 / F05D / F04A / F0B0 batch (2026-08-23)

Table 498 → 504 keys. Coverage 86.5% → 86.6% (69822 mapped). Unknown keys 1,651 → 1,645.

| Key | Map | Check |
|---|---|---|
| `NOORIN48:F0DE` | `ق` / `ل`/`ڑ`/`و` | شوق; کھلانی; کھڑ; 0 leftovers |
| `NOORIN81:F061` | `یر` | یریںپ; یراں نال; F05A before→empty; F02C→یںپ |
| `NOORIN81:F05D` | `جد` / `جدو` | جدید (F068→ید); جد کہ; F09E→کہ; 0 leftovers |
| `NOORIN82:F068` | `ید` | after F05D only |
| `NOORIN08:F04A` | `س` / `سخت` | سخت دل؛ next F0DB→سخت؛ 0 leftovers |
| `NOORIN63:F0B0` | `فی` | کافی؛ فی اللہ؛ 0 leftovers |

Next: `NOORIN05:F056`, `NOORIN01:F0A7`, `NOORIN06:F06E` (n≈17).

### F0DD / F056 / F0A7 / F06E batch (2026-08-23)

Table 504 → 508 keys. Coverage 86.6% → 86.7% (69890 mapped). Unknown keys 1,645 → 1,641.

| Key | Map | Check |
|---|---|---|
| `NOORIN56:F0DD` | `صل` | حاصل (after F071 حa); اصل (F05A before→ا); 0 leftovers |
| `NOORIN01:F05A` before F0DD | `ا` | اصل توں/تیں؛ not default ر |
| `NOORIN05:F056` | `پھل` / `و` | کو/گو+پھل+بھو؛ و after نا+کھا، comma+کی، گa؛ 0 leftovers |
| `NOORIN01:F0A7` | `ر` | ریس؛ رشوت؛ رِچھ؛ 0 leftovers |
| `NOORIN06:F06E` | `و` / `لئے` | phrase-final و; prev F07D→لئے (کھادے لئے); 0 leftovers |

Next: `NOORIN27:F076`, `NOORIN05:F06E`, `NOORIN81:F06C` (n≈17).

### F076 / F06E / F06C batch (2026-08-23)

Table 508 → 511 keys. Coverage stays 86.7% (69941 mapped). Unknown keys 1,641 → 1,638.

| Key | Map | Check |
|---|---|---|
| `NOORIN27:F076` | `نقصان` / `پنو نقصان` | prev F04A→پنو نقصان; F079 after→empty; 0 leftovers |
| `NOORIN05:F06E` | `تباہی` / `تباہ` | next F084→تباہی (F084 empty); F07B+ز→تباہ + بر; 0 leftovers |
| `NOORIN81:F06C` | `چر` / `چڑ` | next F0F0→چڑ (چڑھو); F02C→یںپ (اچریںپ); F021→بی (چربی); 0 leftovers |

Soft: p10 `وی نقصان` still shows `ھ نقصان`; p45 `بربادی` after تباہی still `زباد`.

Next: `NOORIN44:F041` (n=17), then n≈16 cluster (`NOORIN22:F0AA`, `NOORIN81:F0A7`, …).

### F041 / F0AA / F0A7 / F0DD batch (2026-08-23)

Table 511 → 515 keys. Coverage 86.7% → 86.8% (70006 mapped). Unknown keys 1,638 → 1,634.

| Key | Map | Check |
|---|---|---|
| `NOORIN44:F041` | `لگنی` | اکھ لگنی؛ نظر لگنی؛ ٹکائی لگنی؛ 0 leftovers |
| `NOORIN22:F0AA` | `پہلا` | پہلاں with next ں؛ سب تیں پہلاں؛ 0 leftovers |
| `NOORIN81:F0A7` | `طر` / `تر` / `دی` | طریقہ؛ after خا→تر (خاطر)؛ before طرح→دی؛ 0 leftovers |
| `NOORIN63:F0DD` | `لم` | عالم؛ گھولم؛ 0 leftovers |

Next: `NOORIN17:F0D2`, `NOORIN15:F0C9`, `NOORIN81:F064` (n≈16).

### F0D2 / F0C9 / F064 batch (2026-08-23)

Table 515 → 518 keys. Coverage 86.8% → 86.9% (70054 mapped). Unknown keys 1,634 → 1,631.

| Key | Map | Check |
|---|---|---|
| `NOORIN17:F0D2` | `لحاظ` | لحاظ داری؛ بد لحاظ؛ F070/F06F after→empty؛ 0 leftovers |
| `NOORIN15:F0C9` | `لکھ` | توں لکھ بناو؛ منہ کالکھ؛ لکھ کی وی چوری؛ 0 leftovers |
| `NOORIN81:F064` | `جگ` | آپ توں گیو تے جگ توں گیو؛ F0E0 before→ے after ت/ج؛ 0 leftovers |

Next: `NOORIN08:F094`, `NOORIN25:F05B`, `NOORIN43:F092` (n≈16).

### F094 / F05B / F092 batch (2026-08-23)

Table 518 → 521 keys. Coverage 86.9% (70102 mapped). Unknown keys 1,631 → 1,628.

| Key | Map | Check |
|---|---|---|
| `NOORIN08:F094` | `ے` / `سنی` | `ے` after `NOORIN85:F08A` (دے); `سنی` before `:` or after `گل`; empty before `سنائی` p158; 0 leftovers |
| `NOORIN25:F05B` | `گا` / `بیگا` / `بن` / `بنا` / `گ` | `بیگا` before `نی`; line-start `بن`/`بنا`/`بیگا`; `گ` before `نا`/`و`; empty before `ک` after `ت`; 0 leftovers |
| `NOORIN43:F092` | `نین` / `نیند` / `ا` | `نیند` after `کی`/`اپنی`; `ا` after `ج` before `کر`; `NOORIN81:F059` after → `د`; 0 leftovers |

Next: `NOORIN21:F053`, `NOORIN08:F096`, `NOORIN57:F076` (n=16).

### F053 / F096 / F076 batch (2026-08-23)

Table 521 → 524 keys. Coverage 86.9% → 87.0% (70150 mapped). Unknown keys 1,628 → 1,625.

| Key | Map | Check |
|---|---|---|
| `NOORIN21:F053` | `نے` / `نبھا` | `نے` after `پے` (پنے); `نبھا` after `پئی` (نبھانی); empty before `تو` after نہیں; 0 leftovers |
| `NOORIN08:F096` | `ک` / `سہارے` / `ھک` / `سہارہ` / `و` | `سہارے` after کے; `ھک` after ت (تھک گو); `سہارہ` after پدے; `و` in کھوکھ; empty after سے; 0 leftovers |
| `NOORIN57:F076` | `سڑ` / `ر` / `ھ` / `پ` | `ر` after کو (رکھ); `ھ` in کتھ; `سڑ` line-start/نال; `پ` in (پدے); empty before یار/ئیے; 0 leftovers |

Next: `NOORIN17:F081`, `NOORIN08:F0E8`, `NOORIN57:F021` (n≈25–27).

### F081 / F0E8 / F021 batch (2026-08-23)

Table 524 → 527 keys. Coverage 87.0% → 87.1% (70,230 mapped, +80 instances). Unknown keys 1,625 → 1,622.

| Key | Map | Check |
|---|---|---|
| `NOORIN17:F081` | `ھی` / `تھی` | default `ھی` (چڑھی، لدھی، اچاڑھی، پڑھی، کھڑھی); `تھی` after `NOORIN82:F026` (درتھی); 0 leftovers |
| `NOORIN08:F0E8` | `ش` / `شیر` / `یر` / `ک` / `ر` / `وں` | `شیر` after بھی/ت; `ش` after سے/line-start; `ک` after F068 (نیک دینی); `یر` before `:` after کا; `وں` in شیروں; 0 leftovers |
| `NOORIN57:F021` | `ب` / `بی` / `ے` / `ی` / `س` / `ہ` / `ر` / empty | `ب` after کامیا; `بی` after ڈ/چر; `ے` after دے/ڈر; `ی` after F02A (ریس); `س` after F0C2 (تصورت); duplicate→empty; 0 leftovers |

Spot checks: p11 درتھی؛ p28 چڑھی؛ p18 بھی شیر؛ p66 شیر کو گھر؛ p45 کامیاب؛ p91 ڈبی؛ p5 تصورت.

Next: `NOORIN25:F0A9`, `NOORIN13:F0FA`, `NOORIN01:F071` (n≈15).

### F0A9 / F0FA / F071 batch (2026-08-23)

Table 527 → 530 keys. Coverage 87.1% (70,275 mapped, +45 instances). Unknown keys 1,622 → 1,619.

| Key | Map | Check |
|---|---|---|
| `NOORIN25:F0A9` | `ے` / `ی` / `بھی` / `ئ` / `ڑ` / `وں` / empty | `ے` after ک/کی/و; `ی` after نہ (نہیں); `بھی` after ں (بچوں بھی); `ئ` after کو; `ڑ` after کی before ا (کیڑا); `F079` after→empty; 0 leftovers |
| `NOORIN13:F0FA` | `ے` / `نماز` / `اں` / `گ` / empty | `نماز` after کے/تیں; `اں` after ریںپ; `ے` after کی; `گ` after (; line-start empty; 0 leftovers |
| `NOORIN01:F071` | empty / `ت` | empty after شرمسارھ/مو; `ت` after `NOORIN56:F0E7` (موت); 0 leftovers |

Spot checks: p35 بچوں بھی؛ p66 نہیں؛ p6 کیے؛ p78/p62 نماز؛ p33 ریںپاں؛ p113 شرمسار ماں؛ p55/p5 شرمسار.

Next: run `_tmp_top_base.py` for next n≈15 keys.

### F0F9 / F09D / F0D7 batch (2026-08-24)

Table 536 → 539 keys. Coverage 87.3% (70,408 mapped, +45 instances). Unknown keys 1,613 → 1,610.

| Key | Map | Check |
|---|---|---|
| `NOORIN09:F0F9` | empty | flat joiner at proverb line starts (پیٹ پھٹنو، کو، کیرگ); 0 leftovers |
| `NOORIN01:F09D` | empty / `و` / `ڈال` | F05A before F041→و; after گھی→ڈال; F021 before ل→و (ڈبیو); else empty; 0 leftovers |
| `NOORIN14:F0D7` | `ے` / `ی` / `ں` / empty | after اپنوروپ→ے (اپنے); نا+F021→ی (نائی); نا+F056→ں; empty before ں after ددھا/ڈردھا; 0 leftovers |

Spot checks: p70 اپنے نال/بغیر؛ p137 گھی ڈال؛ p53 proverb colons؛ p151 نائی بال.

Next: run `_tmp_top_base.py` for next n≈14 keys.

### F02A / F061 / F0CD batch (2026-08-23)

Table 533 → 536 keys. Coverage 87.2% → 87.3% (70,363 mapped, +43 instances). Unknown keys 1,616 → 1,613.

| Key | Map | Check |
|---|---|---|
| `NOORIN54:F02A` | `ے` / empty | `ے` before ک (وقت کے، ہمت کے، کہیں کو); empty before رکھ after F07A/F03A/F0CF/F0A7; `ے` before رکھ after ما/ے; 0 leftovers |
| `NOORIN05:F061` | empty / `پیدا` | empty before رکھ/رہونی; `پیدا` when F071/F081/F035 in window (چیز/دل/ملال پیدا ہونو); 0 leftovers |
| `NOORIN56:F0CD` | empty | joiner after دے (F08A) or د; before آپ/کی/کے; F0CD+F060=گوج; 0 leftovers |

Spot checks: p100 وقت کے؛ p14 رما کے رکھ؛ p61 چیز پیدا؛ p28 دل ماں ملال پیدا؛ p38 شان تے دے آپ.

Next: run `_tmp_top_base.py` for next n≈15 keys.

### F0DF / F060 / F0C3 batch (2026-08-24)

Table 539 → 542 keys. Coverage 87.3% → 87.4% (70,452 mapped, +44 instances). Unknown keys 1,610 → 1,607.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F0DF` | `پھر` / `تنگ` / empty | before کرنو; تنگ when F0F4 in full row or F03B prev; تنگ before ہونو when F0F2 prev; column-split fix via `base_keys_before_full_row` (p125 تنگکرنو); 0 leftovers |
| `NOORIN57:F060` | empty / `چن` | F077 before F071→چن (نال چن میلو); 0 leftovers |
| `NOORIN43:F0C3` | `و` / empty | not NOORIN63:F0C3; و after ہون/کرن; empty before ۔; 0 leftovers |

Spot checks: p80 نالچنمیلو؛ p93 ہونوت؛ p125 تنگکرنو؛ p156 ہتھ تنگ ہونو.

### F051 / F03E / F07E batch (2026-08-24)

Table 542 → 544 keys. Coverage 87.4% (70,445 mapped, +37 instances net after overlap). Unknown keys 1,607 → 1,605.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F051` | empty / `پھر` / `چ` / `و` / `ی` | empty line-start and comma joiner; پھر after کی or after :; چ in وچ; و in نہیںوا; ی in تیڑے; 0 leftovers |
| `NOORIN19:F03E` | `ب` / `پ` / `د` / `ھ` / `ہ` / `و` / `ں` / empty | colon-context rules (پھر، دیر، بھلا، ھھ، او); 0 leftovers |
| `NOORIN82:F07E` | `ق` / empty | ق in حقدار after حا; ق in قرض; empty before بتا; 0 leftovers |

Spot checks: p55 سوکورکیپھریارںکرنپدے؛ p40 حقدار کرننی؛ p100 دیر رکھاں؛ p43 بھلا.

### F068 / F0CE / F05E batch (2026-08-24)

Table 544 → 547 keys. Coverage 87.4% (70,487 mapped, +42 instances). Unknown keys 1,605 → 1,602.

| Key | Map | Check |
|---|---|---|
| `NOORIN29:F068` | `ں` / `ے` / `ی` / empty | ں after ما; ے after مدد before گہنو; ی after مصیبت before ۔; else empty joiner; 0 leftovers |
| `NOORIN61:F0CE` | `دین` / `ے` / `دے` / `ھ` / `ھیل` | دین before F07B (F07B empty); دے after comma; ے in دینیت دے; ھ in لتھ; ھیل in پھیلنو; 0 leftovers |
| `NOORIN01:F05E` | empty / `ٹ` | empty joiner; ٹ after گھا (F076) in گھاٹ نہیں; 0 leftovers |

Spot checks: p12 ماں؛ p49 مصیبتی؛ p16 سارکودین؛ p105 سرپھیلنو؛ p102 گھاٹ نہیں؛ p111 کیا شکر کیا.

### F0F1 / F02E / F088 batch (2026-08-24)

Table 547 → 550 keys. Coverage 87.4% → 87.5% (70,529 mapped, +42 instances). Unknown keys 1,602 → 1,599.

| Key | Map | Check |
|---|---|---|
| `NOORIN08:F0F1` | `ے` / ` د` / ` دے` / empty | یار دے کو; سے دے; وقت تے; colon joiner; 0 leftovers |
| `NOORIN15:F02E` | empty | joiner after پ in پنی/پے (F0E3 already has نی); 0 leftovers |
| `NOORIN10:F088` | `ی` / `عاء` / `اء` / `ب` / empty | ایں/ساکھیء; تانیعاء titles; بے قیمت; empty before کڑھا/شکر; F059 helper; 0 leftovers |

Spot checks: p22 یار دے کو پھل; p23 پنی; p23 سے دے; p53 عاء بناو; p58 کڑھا/بے قیمت/تانیعاء; p71 پے ہونو.

Next: run `_tmp_top_base.py` for next n≈14 keys (`NOORIN16:F08C`, `NOORIN67:F0F0`, `NOORIN04:F0EA`).

### F08C / F0F0 / F0EA batch (2026-08-24)

Table 550 → 553 keys. Coverage 87.5% (70,570 mapped, +41 instances). Unknown keys 1,599 → 1,596.

| Key | Map | Check |
|---|---|---|
| `NOORIN16:F08C` | `ر` / empty | ر after F07A in ترہ (پدیس، کھئے، ٹاڑ); empty after F04E/F05D/F0E3/F0E9 (ٹاٹا، دوہرتدھرتیانی، ستبندھ); 0 leftovers |
| `NOORIN67:F0F0` | empty | joiner before :/۔/،/) (کہ نہ:، پھر:، etc.); 0 leftovers |
| `NOORIN04:F0EA` | `ی` / `ا` / `دھ` / empty | ی in کوئی; ا in پراں; دھ in دھلاو; else empty; 0 leftovers |

Spot checks: p28 ترہ پدیس؛ p62 ٹاٹا؛ p88 دوہرتدھرتیانی؛ p38 کوئی؛ p103 پراں؛ p129 دھلاو؛ p52 کہ نہ:.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN10:F0B4`, `NOORIN43:F042`, `NOORIN89:F036`).

### F0B4 / F042 / F036 batch (2026-08-24)

Table 553 → 556 keys. Coverage 87.5% → 87.6% (70,609 mapped, +39 instances). Unknown keys 1,596 → 1,593.

| Key | Map | Check |
|---|---|---|
| `NOORIN10:F0B4` | `ہ` / `ئ` / empty | ہ line-start (ہرگوج) and after F043 before F091 (ہر); ئ before F060 after کو/ئے with F060→ی (کوئی، جنہیں); else empty (لاج، ج کرن); 0 leftovers |
| `NOORIN43:F042` | `ا` / `م` / empty | ا line-start (اپ، اپئی); م after F0BB (کاما); else empty (تدھجھک، ناک، کو:); 0 leftovers |
| `NOORIN89:F036` | `ے` / empty | ے before ۔ after F067/F0C8 (نہ کے); else empty before :/۔/، (کیلا:، چڑ:، زرما); 0 leftovers |

Helper: `NOORIN01:F060` → ی when prev F0B4 after کو/ئے (کوئی split).

Spot checks: p5 ہرگوج/کاما؛ p25 تدھجھک؛ p54 نہ کے؛ p112 اپ دھرنی/اپئی؛ p140 کوئی نہیں؛ p155 کوئی کے/لا جگر.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN12:F031`, etc.).

### F031 / F05E / F0B5 batch (2026-08-24)

Table 556 → 559 keys. Coverage 87.6% (70,648 mapped, +39 instances). Unknown keys 1,593 → 1,590.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F031` | `ا` / empty | ا before F056 (ں) in اساں/آپاں/باں/ڈراں/سواں/دھاں; else empty; 0 leftovers |
| `NOORIN05:F05E` | `ا` / `ی` / empty | ا in با آپ after F024; ی in کسی before ما; else empty (دھوکے، دیکھ، صورت، دھاں کی); 0 leftovers |
| `NOORIN82:F0B5` | empty | flat joiner (گہنو، گل،، نہ، سوچ، لائی:); 0 leftovers |

Spot checks: p22 دھاں؛ p38 باں؛ p115 اساں؛ p83 کسی ماں؛ p113 دھوکے/دیکھ؛ p148 با آپ؛ p10 آپئے گل؛ p28 باک نہ۔

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN16:F07E`, etc.).

### F07E / F0EC / F028 batch (2026-08-24)

Table 559 → 563 keys. Coverage 87.6% → 87.7% (70,688 mapped, +40 instances). Unknown keys 1,590 → 1,586.

| Key | Map | Check |
|---|---|---|
| `NOORIN16:F07E` | `ہ` / `ے` / empty | ہ in رہے/رہے ہیں/کم رہ (ip F07B, not nxt, because F021 is empty-skipped); ے after ں/ک line-end; empty after comma/شرمسار; 0 leftovers |
| `NOORIN07:F0EC` | `ے` / empty | ے line-start (ےپلاؤ) and after یار before F0E0 (ےھوڑ); else empty joiner (کو لا، گہنو کرنے); 0 leftovers |
| `NOORIN10:F028` | `ے` / empty | ے in کہنی/رکے (کی before نہ، ک before بے); else empty; 0 leftovers |

Helper: `NOORIN10:F021` → ے when ip F07E (رہے split; p8).

Spot checks: p8 کر رہے گہنوں؛ p9 سکرنتاںے/کم رہ؛ p84 ےپلاؤ/ےھوڑ؛ p58/p111 کہنی؛ p65 رکے.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN82:F037`, `NOORIN17:F05E`, `NOORIN13:F0C3`, etc.).

### F037 / F05E / F0C3 batch (2026-08-24)

Table 563 → 566 keys. Coverage 87.7% (70,727 mapped, +39 instances). Unknown keys 1,586 → 1,583.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F037` | `ی` / empty | ی after ت before اچا (بتایا، p11); else empty joiner (کو نہ، کن کی، title lines); 0 leftovers |
| `NOORIN17:F05E` | empty | flat joiner before کد (شان/بانی/بغیر + ک+د); 0 leftovers |
| `NOORIN13:F0C3` | empty | flat joiner (ماکنی، نہیں آپ، کی نہیں، حیثیت ما، title lines); 0 leftovers |

Spot checks: p11 تیاچاڑہونو/شانکد context؛ p19 شانکد؛ p48 بانیکد؛ p12 ماکنی/نہیں آپ؛ p114 کی نہیں؛ p100 بغیرکد.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN81:F0AD`, `NOORIN08:F073`, etc.).

### F0AD / F073 / F0D2 batch (2026-08-24)

Table 566 → 569 keys. Coverage 87.7% → 87.8% (70,766 mapped, +39 instances). Unknown keys 1,583 → 1,580.

| Key | Map | Check |
|---|---|---|
| `NOORIN81:F0AD` | empty | flat joiner after ک/د (کوک، کما، بھوپکے، کوکد); 0 leftovers |
| `NOORIN08:F073` | empty | flat joiner before م/ہمت (ٹانام، سبم، یارکہمت، نام); 0 leftovers |
| `NOORIN10:F0D2` | `و` / empty | و after ر before لا/د/گہنو (رولاں، رودھک، رودل، روگہنو); else empty (رنے، رکھاں); 0 leftovers |

Spot checks: p13 کوککوئے؛ p14 ٹانام/سبم/رنےیار؛ p30 رولاں؛ p59 کوکد؛ p76 یارکہمت؛ p100 رودلگہنونئے.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN63:F0D3`, `NOORIN32:F061`, etc.).

### F0D3 / F061 / F073 batch (2026-08-24)

Table 569 → 572 keys. Coverage 87.8% (70,805 mapped, +39 instances). Unknown keys 1,580 → 1,577.

| Key | Map | Check |
|---|---|---|
| `NOORIN63:F0D3` | empty | flat joiner after لا (لا کرننی، لا یار، لا بغیر); F09A→ے helper; 0 leftovers |
| `NOORIN32:F061` | `ی`/`ں`/`نی`/`ے`/empty | ی after کرن/ہون/چ (کرنی، ہونی، سوچی); ں after کیون; نی after م (سامنی); ے after لا (بلائے); 0 leftovers |
| `NOORIN57:F073` | empty | flat joiner (ٹھناکرنے، باندپدے، پلےتکو، دلما); 0 leftovers |

Spot checks: p16 لاکرننی؛ p29 لاگرکے؛ p35 لایار؛ p57 کیوں؛ p95 سامنی؛ p133 ہونی؛ p159 بلائے/سوچی؛ p25 باندپدے؛ p51 پلےتکو.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN12:F0D6`, `NOORIN18:F09E`, etc.).

### F0D6 / F09E / F057 batch (2026-08-24)

Table 572 → 575 keys. Coverage 87.8% → 87.9% (70,843 mapped, +38 instances). Unknown keys 1,577 → 1,574.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F0D6` | empty | flat joiner after ھ (ھر، ھپ، ھچھوڑ، ھیار، رھنہہ); 0 leftovers (n=13) |
| `NOORIN18:F09E` | empty | flat joiner before پدے (کےپدے، کوئےپدے، روپدے); 0 leftovers (n=13) |
| `NOORIN81:F057` | empty | flat joiner in کور/بایار/رہون (کورہون، کورنہیں، بایار); 0 leftovers (n=12) |

Spot checks: p34 ہرپچڑ/ھچھوڑپدے/رھنہہ؛ p40 پدےتیںموڑ؛ p48 کوئےپدے؛ p67 روپدے؛ p56 کورہون؛ p2 بایار؛ p107 کورہونونہیں.

Next: run `_tmp_top_base.py` for next n≈13 keys (`NOORIN07:F0ED`, `NOORIN12:F0BF`, etc.).

### F0ED / F0BF / F05A batch (2026-08-25)

Table 575 → 578 keys. Coverage 87.9% (70,879 mapped, +36 instances). Unknown keys 1,574 → 1,571.

| Key | Map | Check |
|---|---|---|
| `NOORIN07:F0ED` | empty | flat joiner (اللہ، دیکھکے، ترپکڑن، گہنو، ریںپ line-start); 0 leftovers (n=12) |
| `NOORIN12:F0BF` | `ے` / empty | `ے` after کر (کرے); else empty joiner (آپ، ما، رھ، کےک); 0 leftovers (n=12) |
| `NOORIN89:F05A` | empty | flat joiner before ج/بی/F06F (کوجگہنو، کیبیتیں، بیکرننی); 0 leftovers (n=12) |

Spot checks: p32 اللہ؛ p42 دیکھکے؛ p53 کرے؛ p80 کرے،؛ p90 نیرھاپنوروپ؛ p12 کوجگہنو؛ p38 کیبیتیں؛ p98 بےکرکے.

Next: run `_tmp_top_base.py` for next n≈12 keys (`NOORIN10:F047`, `NOORIN14:F068`, etc.).

### F047 / F068 / F048 / F059 batch (2026-08-25)

Table 578 → 581 keys. Coverage 87.9% (70,915 mapped, +36 instances). Unknown keys 1,571 → 1,568.

| Key | Map | Check |
|---|---|---|
| `NOORIN10:F047` | empty | flat joiner (کی نال، ماںدینو، line-start proverb headers); 0 leftovers (n=12) |
| `NOORIN14:F068` | `ی`/`ں`/`ا`/empty | ی before F0E8→ک (یک دینی); ں after نا; ی line-start (یتیں); ا in گلانی; 0 leftovers (n=12) |
| `NOORIN11:F048` | `ا`/`و`/empty | ا before ں (کاں، گلاں); و before ھ/ک (کےھر، بغیرھر); empty after مقامتو; 0 leftovers (n=12) |
| `NOORIN15:F059` | `ے`/empty | ے after ھ (ھےآپا، مطلبھے); empty after سو; 0 leftovers (n=12) |

Spot checks: p33 نیاںئےنہ؛ p63 بدھانی،یک دینی؛ p53 (گلاں)； p074 کےوھر؛ p069 ھےآپا؛ p117 مطلبھے.

Next: run `_tmp_top_base.py` for next keys (`NOORIN05:F063` n=49, etc.).

### F063 / F0E9 / F0CE / F06E batch (2026-08-25)

Table 581 → 586 keys. Coverage 87.9% → 88.1% (71,012 mapped, +97 instances). Unknown keys 1,568 → 1,563.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F063` | `یر` / empty | `یر` after F045 (تیرسا), F056/F07D/F0F2; empty line-start/joiner/mقامتو/کے; 0 leftovers (n=49) |
| `NOORIN04:F0E9` | empty | flat joiner (یارپریار، ریںپ، گہنواپنوروپ); 0 leftovers (n=12) |
| `NOORIN04:F0CE` | `ں` / empty | `ں` after سو (سوں); else empty; 0 leftovers (n=12) |
| `NOORIN20:F06E` | `و` / empty | `و` after : (وعدہ); else empty; 0 leftovers (n=12) |

Spot checks: p10 تیرسا؛ p53 تیرسا؛ p27 سوں؛ p28 وعدہ آپنی؛ p42 وعدہ کرنے نال.

Next: run `_tmp_top_base.py` for next n≈12 keys (`NOORIN63:F0F3`, `NOORIN57:F063`, etc.).

### F0F3 / F063 / F0B8 batch (2026-08-25)

Table 586 → 589 keys. Coverage 88.1% (71,047 mapped, +35 instances). Unknown keys 1,563 → 1,560.

| Key | Map | Check |
|---|---|---|
| `NOORIN63:F0F3` | `د` / empty | `د` after ز/ر (زدینو، وردرگنا، ردکررنئے); else empty (زدرک، نازدرک); 0 leftovers (n=12) |
| `NOORIN57:F063` | `ڑ` / `و` / empty | `ڑ` after مو before م (موڑم); `و` after ھ (سامھوکم); else empty; 0 leftovers (n=12) |
| `NOORIN81:F0B8` | `ا` / `ب` / empty | `ا` in باں; `ب` in کثریب/بہونو/برباد; empty in parens/سوت; 0 leftovers (n=11) |

Spot checks: p66 زدینو؛ p70 باںکا؛ p140 موڑم؛ p119 برباد؛ p098 کثریب.

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN63:F0AF`, `NOORIN15:F0F5`, etc.).

### F0AF / F0F5 / F02F batch (2026-08-25)

Table 589 → 592 keys. Coverage 88.1% (71,080 mapped, +33 instances). Unknown keys 1,560 → 1,557.

| Key | Map | Check |
|---|---|---|
| `NOORIN63:F0AF` | `ی` / empty | `ی` after طر/ما before ں; else empty joiner (رررپ، رضاکرنو، ریںپجتناں); 0 leftovers (n=11) |
| `NOORIN15:F0F5` | `ت` | `ت` before ھ (رکھائےتھکر، تھکر); 0 leftovers (n=11) |
| `NOORIN81:F02F` | `وں`/`توں`/`ں`/`کی`/empty | `وں` after نال; `توں` after زیادہتجربو; `ں` in توںپرھی; `کی` before چیز; else empty; 0 leftovers (n=11) |

Spot checks: p150 طریں؛ p100 زیادہتجربوتوںکیگل؛ p125 توںپرھی؛ p006 رکھائےتھکر؛ p093 کیچیز.

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN59:F0EB`, `NOORIN13:F052`, etc.).

### F0EB / F052 / F041 batch (2026-08-25)

Table 592 → 595 keys. Coverage 88.2% (71,113 mapped, +33 instances). Unknown keys 1,557 → 1,554.

| Key | Map | Check |
|---|---|---|
| `NOORIN59:F0EB` | `ھ`/`ر`/`ہ`/`ب`/`آ`/empty | after لا (F0D1): ھ before ھے; empty before ت (F044/F05D); ر before رھلاد; ہ before ہتھ; ب before بچو; آ before آپدم; else empty; 0 leftovers (n=11) |
| `NOORIN13:F052` | `ر`/`ا`/`ت`/`ھ`/empty | after غ: ر before حالت (غریب); ا before ما (غما); ت before تو (غرتوں); ھ before ھ (ناغھ); empty after ع before ک and before قد; 0 leftovers (n=11) |
| `NOORIN12:F041` | `ر`/empty | `ر` after ک before تو (ددھاکرتوں); else empty joiner (انیدھڑو، نا آپ، تآپلا); 0 leftovers (n=11) |

Spot checks: p029 لات غضما؛ p049 غریب حالت؛ p120 ددھاکرتوں؛ p126 نالاآپدم؛ p138 ناغھ نہیں۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN57:F027`, `NOORIN19:F034`, etc.).

### F027 / F034 / F065 batch (2026-08-25)

Table 595 → 598 keys. Coverage 88.2% (71,146 mapped, +33 instances). Unknown keys 1,554 → 1,551.

| Key | Map | Check |
|---|---|---|
| `NOORIN57:F027` | `ں` / `ر` / empty | `ں` after ما before کے (کاماں کے); `ر` after : before ر (رک گہنو، راللہ); else empty (کوئے نہیں، جس کا کو); 0 leftovers (n=11) |
| `NOORIN19:F034` | `گ` / `ے` / empty | `گ` line-start before ین (گیل); `ے` after کو/کی before ین (کوئے، کیے); `ے` after ں before نہ (ستوںے); else empty; 0 leftovers (n=11) |
| `NOORIN08:F065` | `ے` / `و` / `ت` / empty | `ے` in کالے; `و` in نالوں; `ے` after کر before نے (کرے); `ت` before F050 (تی); else empty; 0 leftovers (n=11) |

Spot checks: p006 کاماں کے؛ p008 گیل نسے؛ p121 کالے لکیکنڈ؛ p134 نالوں؛ p160 ستوںے نہ کرنو۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN14:F091`, `NOORIN10:F05D`, etc.).

### F091 / F05D / F0FA batch (2026-08-25)

Table 598 → 601 keys. Coverage 88.3% (71,179 mapped, +33 instances). Unknown keys 1,551 → 1,548.

| Key | Map | Check |
|---|---|---|
| `NOORIN14:F091` | `د`/`ے`/`و`/empty | `د` after بھا before ھ (بھادھ); `ے` after ک before ،/۔/: (کے); `و` after نہک before : (نہ کو); `و` after ک before ے (کوکے); else empty; 0 leftovers (n=11) |
| `NOORIN10:F05D` | `ی`/empty | `ی` in را before ک (راکدھن، راکمنلیو); else empty (عیبکر، کسےکر); 0 leftovers (n=11) |
| `NOORIN56:F0FA` | `ھ`/`ی`/`ر`/empty | `ھ` after د before ھ (دھھے، دھکرنو); `ی` after ت before ک (پکڑنتی، یکت); `ر` after کھ before ر (پکھر); `ی` after : before ک; else empty; 0 leftovers (n=11) |

Spot checks: p010 راکدھنں؛ p095 بھادھ؛ p101 ہرا نہیں کے؛ p128 راکدھن؛ p108 پکھرمناجلد۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN12:F06B`, `NOORIN63:F0BE`, etc.).

### F06B / F0BE / F024 batch (2026-08-25)

Table 601 → 604 keys. Coverage 88.3% (71,212 mapped, +33 instances). Unknown keys 1,548 → 1,545.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F06B` | `پ`/`ے`/`ی`/empty | `پ` after آپ (F057+F04A) before F07B (آپاپردھ); `ے` after کی before F085 (کیے); `ی` after د before F07B (زبادی); `ے` after ل before F061 (نالے); else empty; 0 leftovers (n=11) |
| `NOORIN63:F0BE` | empty | flat empty joiner (کےما، بانا، نامندر، کررکرر، کا سے، کیتی کو); 0 leftovers (n=11) |
| `NOORIN12:F024` | `ے`/empty | `ے` after بھا (F0C5+F05A) before ، (بھارے); else empty (بھاہئے، رہمو، گلٹا، کسھو); 0 leftovers (n=11) |

Spot checks: p12 آپاپردھ، بھاہئے؛ p96 بھارے؛ p153 کیے؛ p154 زبادی؛ p156 نالے۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN09:F0E5`, `NOORIN32:F05F`, etc.).

### F0E5 / F05F / F0DC batch (2026-08-25)

Table 604 → 607 keys. Coverage 88.4% (71,245 mapped, +33 instances). Unknown keys 1,545 → 1,542.

| Key | Map | Check |
|---|---|---|
| `NOORIN09:F0E5` | `ے`/`ن`/`ر`/`ا`/empty | `ے` after گھر/پلاء/کے; `ن` in بنائے; `ر` in رہے; `ا` in ڈرانی; empty after سے/،; 0 leftovers (n=11) |
| `NOORIN32:F05F` | `ئی`/`ہ`/`ت`/`ں`/`ہم`/empty | `ئی` after کو (کوئی); `ہ` after کا before ھ (کاہی/کاہانو); `ت` in سوتری; `ں` in آنیاں; `ہم` line-start; else empty; 0 leftovers (n=11) |
| `NOORIN14:F0DC` | `ے` | `ے` after د (F08A) or مد (F0E6); `ے` before ناداد after :; 0 leftovers (n=11) |

Spot checks: p13 گھرئے؛ p32 بنائے؛ p108 سوتری؛ p140 دے ناداد؛ p145 مدے۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN04:F0DA`, `NOORIN04:F0B9`, etc.).

### F0DA / F0B9 / F092 batch (2026-08-25)

Table 607 → 610 keys. Coverage 88.4% (71,278 mapped, +33 instances). Unknown keys 1,542 → 1,539.

| Key | Map | Check |
|---|---|---|
| `NOORIN04:F0DA` | `ی`/`ئی`/`ے`/`یا`/`ھ`/empty | `ی` line-start (یہ حق/اک لگنی); `ئی` after کو (کوئی کے); `ے` in نتیرے; empty in تھا نہیں; `ی` in دھیار; `یا` after ڈر; `ھ` in تھاک; 0 leftovers (n=11) |
| `NOORIN04:F0B9` | `گ`/`ف`/`ا`/`ڑ`/empty | `گ` in رنگ دبائے; `ف` in فردر after :; `ا` in تھوڑا; `ڑ` in بڑودھ; else empty; 0 leftovers (n=11) |
| `NOORIN08:F092` | `ھ`/`ہ`/empty | `ھ` after د before ۔; `ہ` after د before ،/:; empty after ناداد; 0 leftovers (n=11) |

Spot checks: p45 یہ حق؛ p54 کوئی کے؛ p21 رنگ دبائے؛ p116 فردر؛ p135 ناداد،۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN21:F088`, `NOORIN24:F02C`, etc.).

### F088 / F02C / F082 batch (2026-08-25)

Table 610 → 613 keys. Coverage 88.4% (71,311 mapped, +33 instances). Unknown keys 1,539 → 1,536.

| Key | Map | Check |
|---|---|---|
| `NOORIN21:F088` | `و`/`اں`/`پ`/`ا`/`یو`/empty | `و` in ھو; `اں` in ناسباں; `پ` in کمپہ; `ا` after اپ; `یو` in (یوں); empty before کیے/آپتا; 0 leftovers (n=11) |
| `NOORIN24:F02C` | `ک`/`س`/`ا`/`ئ`/`ی`/empty | `ک` after ر/دوستی; `س` in رسوا; `ا`+`ئ` in ائے; `ک`+`ی` in کی; 0 leftovers (n=11) |
| `NOORIN20:F082` | `ش`/`ی`/`ڑ`/`ب`/`ے`/`و`/empty | `ش` in بارش; `ی` line-start/after :; `ڑ` after مقامتو; `ب` in بڑی/بونی; `ے` in رکرمے; `و` in ہونو; 0 leftovers (n=11) |

Spot checks: p36 بارش/یہ؛ p46 (ھو کیے); p49 رسوا/کیے؛ p93 یارک کی؛ p152 یہ آپلاں۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN21:F075`, `NOORIN51:F096`, etc.).

### F075 / F096 / F036 batch (2026-08-25)

Table 613 → 616 keys. Coverage 88.5% (71,344 mapped, +33 instances). Unknown keys 1,536 → 1,533.

| Key | Map | Check |
|---|---|---|
| `NOORIN21:F075` | `ے`/`ؤ`/`ا`/`ز`/`و`/`ہ`/`ن`/empty | `ے` in دے; `ؤ` after آ (ڈرآؤ); `ا`+`ز` in از; `و`+`ہ` in وہ; `و`+`ن` in ہون; empty after آؤ; 0 leftovers (n=11) |
| `NOORIN51:F096` | `ا`/`ے`/empty | `ا` before ت (ات زردک); `ے` in کیے; else empty after کی/نال; 0 leftovers (n=11) |
| `NOORIN53:F036` | `ی`/`ہ`/`ا`/empty | `ی` in ایک/اک/چیک; `ہ` in کہہ/کیہ; `ا` in کا/عادت کا; 0 leftovers (n=11) |

Spot checks: p32 دے؛ p93 ڈرآؤ/از کم؛ p159 وہ آپ؛ p44 ات زردک؛ p52 کہہونو؛ p55 اک کرنو؛ p117 کیہک۔

Next: run `_tmp_top_base.py` for next n≈11 keys (`NOORIN22:F041`, `NOORIN01:F0AF`, etc.).

### F041 / F0AF / F0F2 batch (2026-08-25)

Table 616 → 619 keys. Coverage 88.5% (71,375 mapped, +31 instances). Unknown keys 1,533 → 1,530.

| Key | Map | Check |
|---|---|---|
| `NOORIN22:F041` | `ھ`/empty | `ھ` after د (F08A) in دھرت/دھرے/نہ دھ; flat joiner; 0 leftovers (n=11) |
| `NOORIN01:F0AF` | `ز`/`ہ`/empty | `ز` before ندگی (زندگی); `ہ` before نگ (ہنگ); empty line-start before :; 0 leftovers (n=10) |
| `NOORIN52:F0F2` | `ب`/`پ`/`ہ`/empty | `ب` in پنجابر (ں in before); `پ` before ڈر after گوج; `ہ` in کھاوہ; else empty; 0 leftovers (n=10) |

Spot checks: p2 ہنگ؛ p4 پنجابر/گوج پہ ڈر؛ p7 زندگی؛ p98 line-start before :؛ p124 کھاوہ.

Next: run `_tmp_top_base.py` for next n≈10 keys (`NOORIN82:F0AD`, `NOORIN07:F086`, etc.).

### F0AD / F086 / F06A / F0B2 batch (2026-08-25)

Table 619 → 623 keys. Coverage 88.6% (71,415 mapped, +40 instances). Unknown keys 1,530 → 1,526.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F0AD` | `ا`/`ی`/empty | `ا` in مار; `ی` line-start before یار; empty joiner (رھے، قدھک، قدپ، :); 0 leftovers (n=10) |
| `NOORIN07:F086` | empty | Urdu index/citation marker (p71); flat empty; 0 leftovers (n=10) |
| `NOORIN57:F06A` | `ھ`/`د`/empty | `ھ` in تھکنو; `د` after : in د دینو; else empty joiner; 0 leftovers (n=10) |
| `NOORIN81:F0B2` | `ئی`/`ب`/`ہ`/empty | `ئی` in کوئی; `ب` in بشوں; `ہ` in بہش; empty before )/تے/ch صور; 0 leftovers (n=10) |

Spot checks: p4 مار میاں؛ p8 کوئی قہونئے؛ p69 تھکنو؛ p117 بشوں؛ p139 یارھر۔

Next: run `_tmp_top_base.py` for next keys (`NOORIN81:F02E`, etc.).

### F04E / F06C / F040 batch (2026-08-25)

Table 626 → 629 keys. Coverage 88.6% (71,475 mapped, +30 instances). Unknown keys 1,523 → 1,520.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F04E` | `ر`/`کار`/empty | `ر` in کار after کا; `کار` line-start; F068 empty after F04E; else empty before ڑ; 0 leftovers (n=10) |
| `NOORIN15:F06C` | `ے`/`غ`/`ا`/empty | `ے` in موڑے; `غ` in کو غم; `ا` in استاد; 0 leftovers (n=10) |
| `NOORIN44:F040` | `رہندے`/`گرتو` | after نہیں / before نہیں; 0 leftovers (n=10) |

### F02E / F0A6 / F077 batch (2026-08-25)

Table 623 → 626 keys. Coverage 88.6% (71,445 mapped, +30 instances). Unknown keys 1,526 → 1,523.

| Key | Map | Check |
|---|---|---|
| `NOORIN81:F02E` | `بل`/empty | `بل` after F0DE joiner; existing rule block; 0 leftovers (n=10) |
| `NOORIN82:F0A6` | `ہ`/`ت`/`کو`/empty | `ہ` line-start; `ت` in گلبات تک; `کو` in ں کو ایک; 0 leftovers (n=10) |
| `NOORIN81:F077` | `ف`/`ش`/`ح`/`شر`/empty | `ف` in فر; `ش` in شرم; `ح` in حرمت; `شر` in شرم تاں; 0 leftovers (n=10) |

Spot checks: p5 قابلقد؛ p6 ہک کہیں؛ p92 ں کو ایک؛ p130 شرم کو مال شرم دے۔

Next: run `_tmp_top_base.py` for next keys.

### F02A / F061 / F0CD batch (2026-08-23)

Table 530 → 533 keys. Coverage 87.1% → 87.2% (70,320 mapped, +45 instances). Unknown keys 1,619 → 1,616.

| Key | Map | Check |
|---|---|---|
| `NOORIN81:F099` | `ڑ` / `ڈ` / `د` / empty | `ڑ` after ک (اکڑف); `ڈ` before ف (ڈف/بیڈی); `د` after سب (دف); duplicate→empty; 0 leftovers |
| `NOORIN09:F09A` | `ے` / `بلا` / `ا` / `و` / empty | `ے` after آپ/کی; empty before ئے; `بلا` after ر; `ا` after پدے; `و` after کے; 0 leftovers |
| `NOORIN82:F02D` | `ند` / `ں` / empty | `ند` after ر (رندات); `ں` after ما (رمان); empty after F04A/F0EC; 0 leftovers |

Spot checks: p47 اکڑف؛ p86 ڈف؛ p36 بیڈی؛ p143 دف؛ p10 آپئے؛ p141 کیے؛ p19 بلا؛ p33 رندات؛ p45 رمان.

Next: run `_tmp_top_base.py` for next n≈15 keys.

### F094 / F05B / F092 batch (2026-08-23)

Table 518 → 521 keys. Coverage 86.9% (70,102 mapped, +48 instances). Unknown keys 1,631 → 1,628.

| Key | Map | Check |
|---|---|---|
| `NOORIN08:F094` | `ے` / empty | after د→دے (ناپودے، کر دے، گل دے); p158 empty before سنائی؛ 0 leftovers |
| `NOORIN25:F05B` | `کہ` / rules | ی after ت (پرائیتی); نہیں after آپس; بیگا before نی; ھی in دھیود; کہ before نا/ک؛ 0 leftovers |
| `NOORIN43:F092` | empty / rules | joiner after اپنی; ا line-start آپنی; جا after ج before کر; نیند after کی before :؛ 0 leftovers |

Spot checks: p10 ناپودے؛ p13 سووترا/چھوڑ بیگانی؛ p45 دھی بیگانی/کہ/کہنا؛ p72 جوانی کی نیند؛ p106 کر دے/گل دے.

Next: run `_tmp_top_base.py` for next n≈16 keys.

### Batch 48 (2026-08-25)

Table 629 → 639 keys. Coverage 88.6% → 88.7% (71,505 mapped, +30 instances). Unknown keys 1,520 → 1,510.

| Key | Map | Check |
|---|---|---|
| `NOORIN29:F04F` | `ہ`/`ے`/empty | `ہ` after ر; `ے` after ک; 0 leftovers (n=10) |
| `NOORIN15:F0CF` | `و`/empty | `و` in وت/کیوں/مو; empty before لائکرننی; 0 leftovers |
| `NOORIN07:F0A7` | context | `و` in بوت; `یں` after م; `ی`/`ح`/`ں`/space by gloss; 0 leftovers |
| `NOORIN26:F0CF` | `و`/`ں`/empty | `و` in یاروں/ماوے; `ں` in آپوں; 0 leftovers |
| `NOORIN69:F085` | `۔` | flat full stop; 0 leftovers |
| `NOORIN23:F074` | context | `اپ` line-start; `ے` after context; 0 leftovers |
| `NOORIN28:F0F1` | `،`/space | Urdu gloss joiner; 0 leftovers |
| `NOORIN35:F0C6` | context | `ب`/`ے`/`ن`/space by prev; 0 leftovers |
| `NOORIN11:F051` | `ے`/space | joiner in gloss column; 0 leftovers |
| `NOORIN41:F032` | context | `و`/`ے`/`ت` by neighbors; 0 leftovers |

### Batch 49 (2026-08-25)

Table 639 → 649 keys. Coverage 88.7% → 88.8% (71,575 mapped, +70 instances). Unknown keys 1,510 → 1,500.

| Key | Map | Check |
|---|---|---|
| `NOORIN06:F0E5` | `ے` | flat; 0 leftovers (n=10) |
| `NOORIN08:F03F` | context | `ا`/`ے`/`و`/space by colon and gloss; 0 leftovers |
| `NOORIN30:F044` | `ے` | after ک; 0 leftovers |
| `NOORIN81:F093` | `ے` | after ر (زدرے); 0 leftovers |
| `NOORIN19:F049` | context | proverb gloss `ا`/`وں`/`ک`/`اں`; 0 leftovers |
| `NOORIN41:F0AF` | empty | before ہون; 0 leftovers |
| `NOORIN31:F06F` | `و` | flat (پوکھ); 0 leftovers |
| `NOORIN08:F0B0` | `،` | flat Urdu comma; 0 leftovers |
| `NOORIN63:F0B5` | `ٹ` | after مو (موٹ); 0 leftovers |
| `NOORIN18:F02B` | `ا`/empty | line-start `ا`; empty in چھوک/ہتھک; 0 leftovers |

### Batch 50 (2026-08-25)

Table 649 → 659 keys. Coverage 88.8% → 89.0% (71,749 mapped, +174 instances). Unknown keys 1,500 → 1,490.

| Key | Map | Check |
|---|---|---|
| `NOORIN26:F083` | `و`/empty | `و` in جگوں/سبوں; 0 leftovers |
| `NOORIN09:F096` | space/`,` | gloss joiner; 0 leftovers |
| `NOORIN50:F071` | context | `ھ`/`ی`/`ے`/space in Urdu gloss; 0 leftovers |
| `NOORIN04:F0AB` | `ے` | flat; 0 leftovers |
| `NOORIN04:F0B6` | `۔` | flat; 0 leftovers |
| `NOORIN04:F02A` | `ے`/`ی` | by context; 0 leftovers |
| `NOORIN01:F032`/`F039`/`F031`/`F030` | empty | English index markers p4–5; 0 leftovers |

### Batch 51 (2026-08-25, partial)

Table 659 → 660 keys. Coverage 89.0% (71,779 mapped, +30 instances). Unknown keys 1,490 → 1,489. Only one n=9 key left at this tier.

| Key | Map | Check |
|---|---|---|
| `NOORIN54:F0AB` | `ے` | before ک (کے); 0 leftovers (n=9) |

### Batch 52 (2026-08-25)

Table 660 → 670 keys. Coverage 89.0% → 89.1% (71,869 mapped, +90 instances). Unknown keys 1,489 → 1,479.

| Key | Map | Check |
|---|---|---|
| `NOORIN24:F0D6` | `ر` | in گوجر/ڈر after ڈ/ا; 0 leftovers (n=9) |
| `NOORIN12:F0F4` | `ر`/`ڑ` | `ر` in گوجر/لاڑ; `ڑ` after ڈر; 0 leftovers |
| `NOORIN57:F062` | `ی`/`و`/`ہ`/empty | `ی` after ، (وی); `و` after ک; `ہ` in رہ; 0 leftovers |
| `NOORIN11:F037` | context | `ی` in بھائی/گل; `ے`/`ئ`/`ھ`; 0 leftovers |
| `NOORIN16:F07D` | `غ`/`ک`/`ڑ`/`ے` | غرض headers; آپ کے; رکڑ; تے; 0 leftovers |
| `NOORIN01:F0AD` | `ے` | flat Urdu gloss column; 0 leftovers |
| `NOORIN39:F0C6` | `ل`/`پ`/`ن`/`ے` | نال/پل/راپو/نو; 0 leftovers |
| `NOORIN13:F033` | `و`/`ے`/empty | پوکپے/بینی/گہنون; 0 leftovers |
| `NOORIN15:F02B` | `ڑ`/`ے` | رکڑ/دے/کرننیے; 0 leftovers |
| `NOORIN66:F04F` | `اں`/empty | ماں; empty after کو; 0 leftovers |

### Batch 53 (2026-08-25)

Table 729 → 739 keys. Coverage 89.6% → 89.7% (72,365 mapped, +90 instances). Unknown keys 1,420 → 1,410.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F0A2` | `ت`/`ے`/`ر`/`ک` | contextual (مطلبےت، کرے، راللہر); 0 leftovers |
| `NOORIN20:F0F1` | space/`，` | like `NOORIN28:F0F1` joiner; 0 leftovers |
| `NOORIN85:F083` | `ت`/`ر`/`ں`/`ھ`/`ی` | after کھا/مو/ڈرے; 0 leftovers |
| `NOORIN13:F0A5` | `ر`/` پر` | رکرننا; پر after کا/پوک; 0 leftovers |
| `NOORIN21:F0AD` | `ت`/`ھے`/`د`/`ل`/`ن` | اصلیت/شاندینی/لا; 0 leftovers |
| `NOORIN82:F070` | `ہو`/`ت` | after پھر/شرمسار; 0 leftovers |
| `NOORIN12:F0F3` | `د`/`ر`/`ک`/`گ`/`ب`/`ھ`/`ں` | جدادھڑی/گوراگے/رک; 0 leftovers |
| `NOORIN04:F0C9` | `ئ`/`ب`/`ر`/`گ`/`ت`/`ں` | آپائی/بناے/رںکو; 0 leftovers |
| `NOORIN12:F074` | `:`,/۔/`ن` | gloss punct; 0 leftovers |
| `NOORIN06:F08D` | `و`/`نی`/`ے`/`سے` | راحساے/شان کد نی; 0 leftovers |

### Batch 54 (2026-08-25)

Table 739 → 749 keys. Coverage 89.7% → 89.8% (72,455 mapped, +90 instances). Unknown keys 1,410 → 1,400.

| Key | Map | Check |
|---|---|---|
| `NOORIN14:F0EC` | `د`/`د:` | after gloss نہیں; 0 leftovers |
| `NOORIN61:F03B` | `درج`/`ت`/`:`/`کھ`/`ل` | titles/کھائی; 0 leftovers |
| `NOORIN19:F03F` | `۔`/space/`ر`/`د` | proverb end punct; 0 leftovers |
| `NOORIN52:F0B9` | `تھے`/`ھے`/`ب`/`ہو`/`ر` | تھے رگے; 0 leftovers |
| `NOORIN12:F0C1` | `لا`/`ل`/`ر`/`کے` | بالکیلا/جوڑنرب; 0 leftovers |
| `NOORIN11:F02E` | `و`/`ہ`/`کے`/`:`/`لو` | ناباہئے/آپاگے; 0 leftovers |
| `NOORIN51:F0C2` | `ہوں`/`نال`/`یار`/`ی` | کیباکشماں; 0 leftovers |
| `NOORIN04:F0A9` | `ک`/`ب`/`س`/`ھ`/`م`/`پ`/`چ` | line-start سے/چھ; 0 leftovers |
| `NOORIN41:F02D` | `ے` | possessive ے; 0 leftovers |
| `NOORIN19:F0DF` | headers | دل/کی/ماں/نام/ر/ھ/کو; 0 leftovers |

### Batch 55 (2026-08-25)

Table 749 → 759 keys. Coverage 89.8% → 89.9% (72,545 mapped, +90 instances). Unknown keys 1,400 → 1,390.

| Key | Map | Check |
|---|---|---|
| `NOORIN07:F0BB` | `ہونی`/`ہوننو`/`نہیں` | ہونی/ہوننو; 0 leftovers |
| `NOORIN18:F072` | `ئ`/`نی` | کوئ/نیکرننی; 0 leftovers |
| `NOORIN81:F084` | `،`/`پر`/`ھی`/`ز`/`ب`/`ھ` | joiner/dash; 0 leftovers |
| `NOORIN06:F0BD` | `نی`/`نا`/`ں`/`کیر`/`ے` | ہم ںکا; 0 leftovers |
| `NOORIN63:F0D2` | `ئ`/`اے` | کائی/توںآپئی; 0 leftovers |
| `NOORIN83:F0E2` | empty | English index joiner; 0 leftovers |
| `NOORIN81:F062` | `کر`/`ھے`/empty | سوعا/عا; 0 leftovers |
| `NOORIN17:F0E7` | `ما`/`فی` | کسےما/فی; 0 leftovers |
| `NOORIN08:F05E` | `ما`/empty | English اسما; 0 leftovers |
| `NOORIN14:F0EA` | `ں`/`ں:` | دوںکہیں; 0 leftovers |

### Batch 56 (2026-08-25)

Table 759 → 769 keys. Coverage 89.9% → 90.0% (72,635 mapped, +90 instances). Unknown keys 1,390 → 1,380.

| Key | Map | Check |
|---|---|---|
| `NOORIN63:F0EF` | `ی`/`ر`/`ان`/`ہ`/`کر`/empty | تےکیوںئے/کرننا; 0 leftovers |
| `NOORIN57:F04E` | `رو`/`ہ`/`ر`/`رب` | کروں/رب; 0 leftovers |
| `NOORIN49:F0A9` | `ے` | flat ے; 0 leftovers |
| `NOORIN21:F0DC` | `ھ` | line-start/Urdu gloss; 0 leftovers |
| `NOORIN08:F09D` | `پہ`/`۔` | پہ سو/گہنو۔; 0 leftovers |
| `NOORIN15:F0D8` | `ر`/`چ`/`یار`/`کر` | رپنے/کرننی; 0 leftovers |
| `NOORIN14:F02C` | `ں` | ںہوننئے; 0 leftovers |
| `NOORIN53:F027` | `۔`/`،` | proverb punct; 0 leftovers |
| `NOORIN15:F086` | `کی`/`ں` | تنورکی/ںکا; 0 leftovers |
| `NOORIN05:F0B0` | `پھر` | flat before ہو; 0 leftovers |

### Batch 57 (2026-08-25)

Table 769 → 779 keys. Coverage 90.0% → 90.1% (72,705 mapped, +70 instances). Unknown keys 1,380 → 1,370.

| Key | Map | Check |
|---|---|---|
| `NOORIN15:F06B` | `ے`/`نی`/`چھوڑ`/`و` | کورے/بٹاہ; 0 leftovers |
| `NOORIN81:F0C4` | `کی`/`نال` | شرمسارکی; 0 leftovers |
| `NOORIN30:F043` | `ئ`/`ت`/`کھ`/`،`/empty | کوئےئ/لئی; 0 leftovers |
| `NOORIN82:F0B2` | `ر` | رملاو; 0 leftovers |
| `NOORIN13:F035` | `و`/`ل`/`ں`/`قات`/empty | واسطے/قات; 0 leftovers |
| `NOORIN80:F031` | `ے`/empty | تھوڑھے; 0 leftovers |
| `NOORIN57:F068` | `ئے`/`ں`/`و`/`ے` | کوئےھے/ہرکوئےے; 0 leftovers |
| `NOORIN13:F0EA` | `،`/`:`/`لو` | جوڑن/بھو:; 0 leftovers |
| `NOORIN29:F03C` | `تے`/`س` | تےکرننی/سکو; 0 leftovers |
| `NOORIN26:F0F4` | `کر`/`چ` | کرنتاں/چکرننی; 0 leftovers |

### Batch 58 (2026-08-25)

Table 779 → 789 keys. Coverage 90.1% → 90.3% (72,781 mapped, +76 instances). Unknown keys 1,370 → 1,360.

| Key | Map | Check |
|---|---|---|
| `NOORIN21:F064` | `د`/`ں` | کیدد/ںسواں; 0 leftovers |
| `NOORIN12:F0EF` | `کھ`/`ک`/`ب`/`کر`/`من` | بچوں/کرسمجھ; 0 leftovers |
| `NOORIN16:F074` | `ت`/`آپ`/`ھے`/`۔`/`س` | لحاظ ت/ساہے; 0 leftovers |
| `NOORIN14:F082` | `ں`/`و` | ںکرننا/دینیو; 0 leftovers |
| `NOORIN21:F0D7` | `ھ`/`کے`/`ر` | تھ/لحاظھ; 0 leftovers |
| `NOORIN06:F0BB` | `کو`/`ں`/`کے`/`نی` | کریادھں/کے; 0 leftovers |
| `NOORIN16:F05F` | empty | joiner after کے; 0 leftovers |
| `NOORIN57:F02E` | `رت`/`زمیدرک`/etc | حیثیتکے تے; 0 leftovers |
| `NOORIN08:F099` | `گہنو`/`۔`/`نا` | کرنو/گہنورھ; 0 leftovers |
| `NOORIN26:F0B9` | `۔`/`کان`/empty | نہیں۔/کانو; 0 leftovers |

### Batch 59 (2026-08-25)

Table 670 → 680 keys. Coverage 89.1% → 89.2% (71,949 mapped, +80 instances). Unknown keys 1,479 → 1,469.

| Key | Map | Check |
|---|---|---|
| `NOORIN74:F0A2` | `ں` | flat before ں (F056); 0 leftovers (n=8) |
| `NOORIN57:F05F` | context | کی before F0C5; لارہنو before F0D1; نہیں before F037; 0 leftovers |
| `NOORIN04:F0B3` | context | زھز after F0E2; ھ after F0C3/F04B/F040; پ before F07D/F037; 0 leftovers |
| `NOORIN11:F0A7` | `ن`/`ں`/`نا` | after F03A/line-start; ں after F065; نا after F0F6; 0 leftovers |
| `NOORIN14:F045` | context | اک/ک/ے/ھ/ں/ر by neighbor; 0 leftovers |
| `NOORIN01:F021` | `ے`/empty | joiner; empty after F057+F028; 0 leftovers |
| `NOORIN48:F0F6` | context | ے/ت/ں/ک/آ by prev F0E2/F03B/F052; 0 leftovers |
| `NOORIN06:F029` | context | ھ after F07A+F07B; ر after F0E2; ت after F0C5; 0 leftovers |
| `NOORIN10:F08F` | `ریب` | قد before F08A; ریب before F064; 0 leftovers |
| `NOORIN56:F0DC` | context | فر before F073; کر before F099; 0 leftovers |

### Batch 60 (2026-08-25)

Table 680 → 690 keys. Coverage 89.2% → 89.3% (72,019 mapped, +70 instances). Unknown keys 1,469 → 1,459.

| Key | Map | Check |
|---|---|---|
| `NOORIN08:F06D` | context | ر/ہ/گ/ھ by context; 0 leftovers |
| `NOORIN76:F027` | context | ک after F040+F0A3; ر after F059+F05A; 0 leftovers |
| `NOORIN17:F0E1` | context | ے/ن/ف/ھ (تہونک، نقصان، فارسی); 0 leftovers |
| `NOORIN61:F08C` | `۔` | end punct; ، after سیاو; : before gloss; 0 leftovers |
| `NOORIN06:F0E4` | context | ے/ھ/و after آپ; 0 leftovers |
| `NOORIN57:F042` | context | یر/دی/ال/ون by context; 0 leftovers |
| `NOORIN73:F0EE` | context | بول/ھ/ر/خ by next glyph; 0 leftovers |
| `NOORIN16:F06E` | context | ما after F0E7; کی after F0E7+F0C5; 0 leftovers |
| `NOORIN22:F098` | context | ے/ب (کوئے، بیکی، ساکرکاے); 0 leftovers |
| `NOORIN57:F077` | context | و/ت/ع/ے by context; 0 leftovers |

### Batch 61 (2026-08-25)

Table 690 → 700 keys. Coverage 89.3% → 89.4% (72,089 mapped, +70 instances). Unknown keys 1,459 → 1,449.

| Key | Map | Check |
|---|---|---|
| `NOORIN41:F0B1` | context | ے/ر/ہ by context; 0 leftovers |
| `NOORIN82:F05E` | `نا` | after F059 (کونانا); 0 leftovers |
| `NOORIN05:F0B7` | context | ک in رکقماز; ے in سیرے; 0 leftovers |
| `NOORIN57:F05E` | context | ت/ی/و/د/ا (درندر، موٹا، راللہ); 0 leftovers |
| `NOORIN05:F0EA` | context | ھ after F05A+F07A; empty line-start; 0 leftovers |
| `NOORIN13:F0E6` | context | ے/ی/ا by context; 0 leftovers |
| `NOORIN11:F06D` | context | ی/ھ/ے/ب/ں by context; 0 leftovers |
| `NOORIN57:F064` | context | ے/و after F0CE; empty F051 line-start; 0 leftovers |
| `NOORIN15:F050` | context | ی/و/ا/ے/ن by next after F08A; 0 leftovers |
| `NOORIN05:F082` | context | ر after F067; ی after F06D; 0 leftovers |

### Batch 62 (2026-08-25)

Table 700 → 709 keys. Coverage 89.4% → 89.5% (72,159 mapped, +70 instances). Unknown keys 1,449 → 1,440. `NOORIN34:F023` skipped (already ruled).

| Key | Map | Check |
|---|---|---|
| `NOORIN17:F097` | context | ب in تباہی/ریںپ; ھ in رددھاچڑانو; 0 leftovers |
| `NOORIN08:F0BA` | context | ک after F067; ر after F0A7; 0 leftovers |
| `NOORIN82:F095` | `ن` | in قمازن/شون; 0 leftovers |
| `NOORIN76:F084` | context | و/ں (کوھسور، بغیرں، گروت); 0 leftovers |
| `NOORIN58:F0ED` | context | ل after F04B; ہ after F036; empty else; 0 leftovers |
| `NOORIN10:F029` | context | و/ے/ک by context; 0 leftovers |
| `NOORIN10:F0E2` | `د` | in ددھاکر; empty else; 0 leftovers |
| `NOORIN17:F083` | context | ند/ک/ر after F030/F065; 0 leftovers |
| `NOORIN31:F083` | context | ہ/ں/ئ by context; 0 leftovers |

### Batch 63 (2026-08-25)

Table 709 → 719 keys. Coverage 89.5% → 89.5% (72,209 mapped, +50 instances). Unknown keys 1,440 → 1,430.

| Key | Map | Check |
|---|---|---|
| `NOORIN48:F0E9` | `ش` | in خوش/خورش/فخور; 0 leftovers |
| `NOORIN16:F0B2` | context | د/ر/ڈ after F08A/F025; 0 leftovers |
| `NOORIN05:F099` | context | ے/ا by context; 0 leftovers |
| `NOORIN19:F0C2` | context | ے/ر/د by line-start and F0D4/F077; 0 leftovers |
| `NOORIN13:F076` | context | ے after F08A/F09B; 0 leftovers |
| `NOORIN10:F0C9` | context | ں/ے by context; 0 leftovers |
| `NOORIN14:F033` | context | ر after F021; 0 leftovers |
| `NOORIN32:F085` | `ب` | in بانیوپاچاے; ال after F059; 0 leftovers |
| `NOORIN63:F031` | context | ر/ز/ے by context; 0 leftovers |
| `NOORIN82:F041` | context | ل/ں/ہ by context; 0 leftovers |

### Batch 64 (2026-08-25)

Table 719 → 729 keys. Coverage 89.5% → 89.6% (72,275 mapped, +66 instances). Unknown keys 1,430 → 1,420.

| Key | Map | Check |
|---|---|---|
| `NOORIN51:F0EF` | context | م/ت/ی/و/ہ/ر by context; 0 leftovers |
| `NOORIN07:F051` | `ے` | in یار،ےک patterns; 0 leftovers |
| `NOORIN08:F07C` | `ے` | flat (لےنی، ماےت، گہنوے); 0 leftovers |
| `NOORIN10:F0CB` | `ر` | in ڈرر/شرر; 0 leftovers |
| `NOORIN11:F030` | context | ے/ر/ن by context; 0 leftovers |
| `NOORIN11:F04F` | context | ا/ہ/ی by context; 0 leftovers |
| `NOORIN29:F05B` | context | ے/ت/ہ/ب by context; 0 leftovers |
| `NOORIN63:F0DE` | context | ے/ر (برلے، پگوجر); 0 leftovers |
| `NOORIN34:F024` | `ق` | in نق۔/نق; 0 leftovers |
| `NOORIN83:F0CB` | `۔` | after F024; پاس before F036; 0 leftovers |

### Batch 65 (2026-08-25)

Table 869 → 879 keys. Coverage 90.7% → 90.8% (73,221 mapped, +58 instances). Unknown keys 1,280 → 1,270.

| Key | Map | Check |
|---|---|---|
| `NOORIN34:F023` | context | شمنی default; دشمنی when nxt=F083; patched; 0 leftovers |
| `NOORIN07:F0B8` | context | ر/ش/و/ما by context; 0 leftovers |
| `NOORIN01:F06D` | context | و/ر/empty by context; 0 leftovers |
| `NOORIN15:F0D3` | `ں` | inflection; 0 leftovers |
| `NOORIN04:F068` | context | د/ے/ب/empty by context; 0 leftovers |
| `NOORIN16:F0A3` | empty | joiner; 0 leftovers |
| `NOORIN16:F056` | `ے` | گینے، کیے; 0 leftovers |
| `NOORIN11:F046` | context | ے/سے/ں by context; 0 leftovers |
| `NOORIN11:F0DC` | context | ر/و/ے by context; 0 leftovers |
| `NOORIN56:F089` | `ں` | کےں/ہتھں; 0 leftovers |

### Batch 66 (2026-08-25)

Table 879 → 889 keys. Coverage 90.8% → 90.9% (73,279 mapped, +58 instances). Unknown keys 1,270 → 1,260.

| Key | Map | Check |
|---|---|---|
| `NOORIN15:F0D0` | context | ھ/empty/چ by context; 0 leftovers |
| `NOORIN10:F051` | context | ما/ی/ت/پ/empty by context; 0 leftovers |
| `NOORIN05:F0E2` | context | ا/ط/پ/گ/empty by context; 0 leftovers |
| `NOORIN13:F0E0` | context | نا/دا/ت/کی/مار by context; 0 leftovers |
| `NOORIN14:F0BC` | context | ں/ر by context; 0 leftovers |
| `NOORIN07:F098` | context | ے/ت by context; 0 leftovers |
| `NOORIN03:F0F9` | context | ت/ہ/ع by context; 0 leftovers |
| `NOORIN13:F02B` | context | ھ/ڈ/تے/نا by context; 0 leftovers |
| `NOORIN29:F0F8` | context | کر/د by context; 0 leftovers |
| `NOORIN10:F0E7` | context | ر/ھ by context; 0 leftovers |

### Batch 67 (2026-08-25)

Table 889 → 899 keys. Coverage 90.9% → 90.9% (73,337 mapped, +58 instances). Unknown keys 1,260 → 1,250.

| Key | Map | Check |
|---|---|---|
| `NOORIN13:F024` | context | رم/بھی/چا by context; 0 leftovers |
| `NOORIN59:F0EC` | `کر` | in پقاکر; 0 leftovers |
| `NOORIN14:F07D` | context | کہ/لا patched; 0 leftovers |
| `NOORIN36:F0D2` | context | ے/جوڑنگو/ئی/تے by context; 0 leftovers |
| `NOORIN81:F06E` | empty | joiner after F0E0; 0 leftovers |
| `NOORIN14:F02E` | context | ک/ے/ں/ھ by context; 0 leftovers |
| `NOORIN41:F0AB` | context | ک/زر/ما/کی/ی by context; 0 leftovers |
| `NOORIN05:F04D` | context | لی/گہنو/ے/ل by context; 0 leftovers |
| `NOORIN06:F090` | context | ں/ے by context; 0 leftovers |
| `NOORIN08:F032` | context | ک/و/ں/، by context; 0 leftovers |

### Batch 68 (2026-08-25)

Table 899 → 909 keys. Coverage 90.9% → 91.0% (73,395 mapped, +58 instances). Unknown keys 1,250 → 1,240.

| Key | Map | Check |
|---|---|---|
| `NOORIN11:F0CE` | context | ھ/ک/ر/ن/سے by context; 0 leftovers |
| `NOORIN82:F0A5` | context | ،/وا/ر/و/ے by context; 0 leftovers |
| `NOORIN25:F05A` | context | ک/چ by context; 0 leftovers |
| `NOORIN15:F0C7` | context | ر/ک/آ/ن/ھی/چ by context; 0 leftovers |
| `NOORIN72:F0A2` | context | ن/ک/ے by context; 0 leftovers |
| `NOORIN05:F044` | context | ت/چ/و/ک by context; 0 leftovers |
| `NOORIN06:F060` | context | ہ/و/ر by context; 0 leftovers |
| `NOORIN22:F040` | `د` | in ددد; 0 leftovers |
| `NOORIN15:F089` | context | ڈ/کھ/ں by context; 0 leftovers |
| `NOORIN12:F03F` | `ز` | in عزت; 0 leftovers |

### Batch 69 (2026-08-25)

Table 909 → 919 keys. Coverage 91.0% → 91.1% (73,453 mapped, +58 instances). Unknown keys 1,240 → 1,230.

| Key | Map | Check |
|---|---|---|
| `NOORIN82:F0B4` | context | تو/کی by context; 0 leftovers |
| `NOORIN27:F095` | context | ر/ک/ی by context; 0 leftovers |
| `NOORIN48:F0EF` | context | ہ/ے/دا/د/ل by context; 0 leftovers |
| `NOORIN17:F03E` | `ں` | in ھںت/ںگ; 0 leftovers |
| `NOORIN10:F072` | context | ہی/ا/اک patched; 0 leftovers |
| `NOORIN01:F072` | context | ے/ل/empty by context; 0 leftovers |
| `NOORIN81:F03A` | `ر` | in ہر; 0 leftovers |
| `NOORIN83:F0CD` | context | ما in ماں; 0 leftovers |
| `NOORIN53:F0CC` | context | ب/ک by context; 0 leftovers |
| `NOORIN67:F028` | context | کہ/پ/گ/و by context; 0 leftovers |

### Batch 70 (2026-08-25)

Table 919 → 929 keys. Coverage 91.1% → 91.2% (73,511 mapped, +58 instances). Unknown keys 1,230 → 1,220.

| Key | Map | Check |
|---|---|---|
| `NOORIN12:F0F2` | context | ن/ک by context; 0 leftovers |
| `NOORIN10:F0CF` | context | ت/ر/empty by context; 0 leftovers |
| `NOORIN16:F0CB` | context | ے/کھ/ڑ by context; 0 leftovers |
| `NOORIN05:F059` | context | ک/چ/ہ/empty by context; 0 leftovers |
| `NOORIN81:F0B0` | context | و/ر/ل/پ by context; 0 leftovers |
| `NOORIN05:F0EF` | context | ما/تا/ے/اک/empty by context; 0 leftovers |
| `NOORIN08:F043` | context | ئی/empty by context; 0 leftovers |
| `NOORIN08:F0D1` | context | ے/ک by context; 0 leftovers |
| `NOORIN57:F040` | context | نس/ی/ٹر/empty by context; 0 leftovers |
| `NOORIN19:F054` | context | ی/تو/و/ے by context; 0 leftovers |

### Batch 71 (2026-08-25)

Table 929 → 939 keys. Coverage 91.2% → 91.2% (73,569 mapped, +58 instances). Unknown keys 1,220 → 1,210.

| Key | Map | Check |
|---|---|---|
| `NOORIN14:F078` | context | ک/ر/نا/لو by context; 0 leftovers |
| `NOORIN16:F0BE` | `کے` | in کےوھر; 0 leftovers |
| `NOORIN04:F07A` | `کت` | in خوکت; 0 leftovers |
| `NOORIN29:F0C8` | context | ے/کر/ق/ر by context; 0 leftovers |
| `NOORIN15:F0E8` | context | لا/کھ/ی/ک by context; 0 leftovers |
| `NOORIN07:F04B` | `و` | in مھوو; 0 leftovers |
| `NOORIN14:F0AF` | context | ئی/ما/ر by context; 0 leftovers |
| `NOORIN13:F0B6` | context | ر/ے/نی/چ by context; 0 leftovers |
| `NOORIN15:F027` | context | کر/ت/ک by context; 0 leftovers |
| `NOORIN12:F0DC` | `ر` | in ڈرررر; 0 leftovers |

### Batch 72 (2026-08-25)

Table 939 → 949 keys. Coverage 91.2% → 91.3% (73,629 mapped, +60 instances). Unknown keys 1,210 → 1,200.

| Key | Map | Check |
|---|---|---|
| `NOORIN27:F028` | `کھ` | in کھے; 0 leftovers |
| `NOORIN02:F073` | context | رد/و by context; 0 leftovers |
| `NOORIN08:F090` | context | ھ/ہ/ما/، by context; 0 leftovers |
| `NOORIN14:F084` | context | ے/ں/و by context; 0 leftovers |
| `NOORIN55:F0E5` | context | ل/ہر/ر/،/ی by context; 0 leftovers |
| `NOORIN50:F0F4` | context | ما/م/ک by context; 0 leftovers |
| `NOORIN46:F037` | context | سر/پ/ل/ت by context; 0 leftovers |
| `NOORIN04:F0F7` | context | ک/ے/ہ by context; 0 leftovers |
| `NOORIN10:F0B8` | context | ت/، by context; 0 leftovers |
| `NOORIN54:F0CB` | context | م/س/ر/پ/ے by context; 0 leftovers |

Census after batch 72: 949 keys, 91.3% mapped (73,629 instances), 1,200 unknown keys, 536 once-only.

### Batch 73 (2026-08-25)

Table 789 → 799 keys. Coverage 90.3% → 90.4% (72,857 mapped, +76 instances). Unknown keys 1,360 → 1,350.

| Key | Map | Check |
|---|---|---|
| `NOORIN05:F048` | context | رت after F056; ے after F0E0; : before F03A; 0 leftovers |
| `NOORIN14:F0B4` | context | ھ after F07A; ر/empty after F05A; م before F071; 0 leftovers |
| `NOORIN25:F043` | context | نی/پ/empty by context; 0 leftovers |
| `NOORIN41:F041` | context | ے after F0C3/F0BB; 0 leftovers |
| `NOORIN56:F0CC` | context | کو after F0F1; empty after F067; 0 leftovers |
| `NOORIN09:F0BF` | context | ے after F056/F084/F036; 0 leftovers |
| `NOORIN82:F096` | context | : after F037; د after F079/F05A; 0 leftovers |
| `NOORIN13:F036` | empty | joiner (ہontو); 0 leftovers |
| `NOORIN04:F04F` | context | نی after F0A9; empty else; 0 leftovers |
| `NOORIN05:F06B` | context | ں/ے/ھ/: by context; 0 leftovers |

### Batch 74 (2026-08-25)

Table 799 → 809 keys. Coverage 90.4% → 90.5% (72,927 mapped, +70 instances). Unknown keys 1,350 → 1,340.

| Key | Map | Check |
|---|---|---|
| `NOORIN11:F02B` | context | ے/ھ line-start before F07C; 0 leftovers |
| `NOORIN07:F0AA` | `رے` | flat; 0 leftovers |
| `NOORIN64:F0D8` | empty | before ساکھ/line-start; 0 leftovers |
| `NOORIN49:F061` | context | ر before F05A; empty end punct; 0 leftovers |
| `NOORIN81:F054` | context | موتر after F0DE; 0 leftovers |
| `NOORIN57:F03F` | context | حا after F071; نوتھا line-start; 0 leftovers |
| `NOORIN22:F056` | context | ے/د/empty by context; 0 leftovers |
| `NOORIN05:F064` | context | ے/و/ہ/ھی by context; 0 leftovers |
| `NOORIN10:F0F3` | empty | line-start joiner; 0 leftovers |
| `NOORIN25:F0EB` | context | ے/ما/کی by context; 0 leftovers |

### Batch 75 (2026-08-25)

Table 809 → 819 keys. Coverage 90.5% → 90.5% (72,997 mapped, +70 instances). Unknown keys 1,340 → 1,330.

| Key | Map | Check |
|---|---|---|
| `NOORIN41:F09B` | context | empty/کر by context; 0 leftovers |
| `NOORIN13:F0BB` | context | ف after F05A; empty after F053; 0 leftovers |
| `NOORIN38:F0BD` | context | د/دو after F0E2/F07A; 0 leftovers |
| `NOORIN06:F028` | context | کو after F03A/F044; 0 leftovers |
| `NOORIN07:F0DC` | context | بر before F0E0; 0 leftovers |
| `NOORIN06:F04C` | empty | punct joiner; 0 leftovers |
| `NOORIN15:F0DB` | context | empty/کے by context; 0 leftovers |
| `NOORIN19:F046` | `ک` | after F03A/F060; 0 leftovers |
| `NOORIN14:F099` | context | تو before F0D5; 0 leftovers |
| `NOORIN07:F068` | context | ے after F030; 0 leftovers |

### Batch 76 (2026-08-25)

Table 819 → 829 keys. Coverage 90.5% → 90.6% (73,067 mapped, +70 instances). Unknown keys 1,330 → 1,320.

| Key | Map | Check |
|---|---|---|
| `NOORIN75:F084` | context | ناں after F079/F0E2; 0 leftovers |
| `NOORIN12:F0F9` | context | ے after F065/F09F; 0 leftovers |
| `NOORIN14:F02D` | empty | after F05A line-start; 0 leftovers |
| `NOORIN32:F06C` | context | نو/ہ/empty; 0 leftovers |
| `NOORIN14:F039` | context | پ after F036; 0 leftovers |
| `NOORIN10:F0B7` | context | و/ک/empty; 0 leftovers |
| `NOORIN06:F07C` | context | تا/ت/ں after F040; 0 leftovers |
| `NOORIN04:F0B4` | context | ڑ/ر/empty; 0 leftovers |
| `NOORIN26:F07B` | context | نئے/empty; 0 leftovers |
| `NOORIN57:F0B7` | context | تک/ماں/سا; 0 leftovers |

### Batch 77 (2026-08-25)

Table 829 → 839 keys. Coverage 90.6% → 90.6% (73,137 mapped, +70 instances). Unknown keys 1,320 → 1,310.

| Key | Map | Check |
|---|---|---|
| `NOORIN01:F03F` | context | ر before F05A; 0 leftovers |
| `NOORIN10:F0BE` | context | و/آ by context; 0 leftovers |
| `NOORIN26:F024` | context | empty/لانی/کا line-start; 0 leftovers |
| `NOORIN10:F094` | context | ے Urdu gloss; 0 leftovers |
| `NOORIN01:F05F` | context | empty/سے; 0 leftovers |
| `NOORIN27:F04D` | context | ر/ت/empty; 0 leftovers |
| `NOORIN82:F065` | context | غ after F0A7; 0 leftovers |
| `NOORIN16:F0C8` | context | اک before F03B; 0 leftovers |
| `NOORIN15:F032` | context | ل after F03A; 0 leftovers |
| `NOORIN08:F0E0` | context | empty/ت; 0 leftovers |

### Batch 78 (2026-08-25)

Table 839 → 849 keys. Coverage 90.6% → 90.7% (73,207 mapped, +70 instances). Unknown keys 1,310 → 1,300.

| Key | Map | Check |
|---|---|---|
| `NOORIN23:F0F0` | context | ک before F067; 0 leftovers |
| `NOORIN70:F052` | context | ے after F065; 0 leftovers |
| `NOORIN26:F031` | context | سے/و/empty; 0 leftovers |
| `NOORIN17:F040` | context | ے/empty; 0 leftovers |
| `NOORIN15:F041` | context | empty/آ; 0 leftovers |
| `NOORIN06:F0C3` | empty | joiner; 0 leftovers |
| `NOORIN72:F0B4` | context | کیا/empty; 0 leftovers |
| `NOORIN10:F0C0` | context | ر before F05A; 0 leftovers |
| `NOORIN49:F08D` | `ک` | after F03A/F07B/F0D4; 0 leftovers |
| `NOORIN14:F0E2` | context | غ after F0BE; 0 leftovers |

### Batch 79 (2026-08-25)

Table 849 → 859 keys. Coverage 90.7% → 90.7% (73,277 mapped, +70 instances). Unknown keys 1,300 → 1,290.

| Key | Map | Check |
|---|---|---|
| `NOORIN01:F0A3` | empty | joiner; 0 leftovers |
| `NOORIN37:F057` | context | ے/empty; 0 leftovers |
| `NOORIN81:F094` | `ر` | flat; 0 leftovers |
| `NOORIN18:F085` | context | ے after F075; 0 leftovers |
| `NOORIN10:F03D` | context | ر after F067/F0C2; 0 leftovers |
| `NOORIN01:F036` | context | ء/empty; 0 leftovers |
| `NOORIN57:F057` | context | empty/ک; 0 leftovers |
| `NOORIN59:F0F5` | context | empty/ک; 0 leftovers |
| `NOORIN45:F096` | `ں` | line-start before F056; 0 leftovers |
| `NOORIN82:F069` | context | ے/ر/ھ; 0 leftovers |

### Batch 80 (2026-08-25)

Table 859 → 869 keys. Coverage 90.7% (73,163 mapped, +382 instances from batches 73–80). Unknown keys 1,290 → 1,280.

| Key | Map | Check |
|---|---|---|
| `NOORIN28:F0F8` | context | ناس after F0C3; 0 leftovers |
| `NOORIN18:F076` | context | ے after F044; 0 leftovers |
| `NOORIN11:F097` | context | ے after F0C5/F077; 0 leftovers |
| `NOORIN13:F0B1` | context | د/ک/empty; 0 leftovers |
| `NOORIN57:F058` | context | با/empty; 0 leftovers |
| `NOORIN81:F072` | context | ڈ after F099; 0 leftovers |
| `NOORIN81:F081` | context | ر/empty; 0 leftovers |
| `NOORIN04:F0BE` | context | حال/ر/empty; 0 leftovers |
| `NOORIN14:F0C4` | context | آ after F067; 0 leftovers |
| `NOORIN12:F0CB` | context | رد after F0D0; 0 leftovers |

Census after batch 80: 869 keys, 90.7% mapped (73,163 instances), 1,280 unknown keys, 536 once-only.

Census after batch 72 (added later): 949 keys, 91.3% mapped (73,629 instances), 1,200 unknown keys.

Next: run `_tmp_top_base.py` for batch 81 keys.

### Batches 81–95 summary (2026-08-25)

Baseline before batches 81–95: 949 keys, 91.3% mapped (73,629 instances), 1,200 unknown keys, 536 once-only.

Workflow: 15 batches × 7 keys (n=4 each), dump/ctx/decoded analysis → context rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census.

Table 949 → 1054 keys (+105). Coverage 91.3% → 91.8% (74,049 mapped, +420 instances). Unknown keys 1,200 → 1,095 (−105). Once-only unknown keys still 536.

Flat maps: `NOORIN17:F0E2`→`ل`, `NOORIN66:F04B`→empty (سو joiner).

Notable context keys (all 0 leftovers): `NOORIN10:F089`→`ل` (لگل/لھے), `NOORIN07:F0F2`→`ب` (کارب), `NOORIN69:F0A5`→`و` (خولو), `NOORIN26:F066`→`ل` (بیکول), `NOORIN63:F0DA`→`ہون`/`ت`, `NOORIN04:F0C7`→`کو`/`یار`/`ک`, `NOORIN81:F044`→`تک`/`کو`, `NOORIN02:F09F`→`و` (خو), `NOORIN15:F05A`→`ے` (اسرے), `NOORIN81:F05F`→`ٹھ`/`ت`/`سا`.

Census after batch 95: 1054 keys, 91.8% mapped (74,049 instances), 1,095 unknown keys.

### Batches 96–115 summary (2026-08-25)

Baseline before batches 96–115: 1054 keys, 91.8% mapped (74,049 instances), 1,095 unknown keys, 536 once-only.

Workflow: 20 batches × 6 keys (n≤4 each), dump/ctx/decoded analysis → context rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census.

Table 1054 → 1174 keys (+120). Coverage 91.8% → 92.3% (74,422 mapped, +373 instances). Unknown keys 1,095 → 975 (−120). Once-only unknown keys still 536.

Notable context keys (all 0 leftovers): `NOORIN62:F0C1`→`گ` (گھی), `NOORIN06:F054`→`و` (کھاو), `NOORIN82:F086`→`و` (رضاور), `NOORIN01:F04C`/`NOORIN83:F0F3`→`ک`, `NOORIN07:F0E3`→`ہ`, `NOORIN51:F0F0`→`خ` (خور), `NOORIN05:F0D3`→`ش` (شوق), `NOORIN48:F0E8`→`ا`/`و` (اکے), `NOORIN37:F06B`→`س`/`ں`, `NOORIN31:F081`→`ق` (ئیق).

Census after batch 115: 1174 keys, 92.3% mapped (74,422 instances), 975 unknown keys.

### Batches 116–135 summary (2026-08-25)

Baseline before batches 116–135: 1174 keys, 92.3% mapped (74,422 instances), 975 unknown keys, 536 once-only.

Workflow: 20 batches × 7 keys (n≤4 each), dump/ctx/decoded analysis → context rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census.

Table 1174 → 1314 keys (+140). Coverage 92.3% → 92.7% (74,737 mapped, +315 instances). Unknown keys 975 → 835 (−140). Once-only unknown keys still 536.

Notable context keys (all 0 leftovers): `NOORIN30:F048` (joiner/پھر), `NOORIN08:F0B6` (سے/اں), `NOORIN56:F0ED` (بادے/باہونک), `NOORIN08:F0A7` (صورتکرت), `NOORIN85:F086` (سورکر/دکٹی), `NOORIN48:F0E1` (نوں/ھرو), `NOORIN81:F029` (کگاں/دل), `NOORIN08:F0F0` (گھکوم), `NOORIN82:F0A8` (قارت/گللانی), `NOORIN01:F02F` (English index space).

Census after batch 135: 1314 keys, 92.7% mapped (74,737 instances), 835 unknown keys.

### Batches 166–195 summary (2026-08-26)

Baseline before batches 166–195: 1464 keys, 93.0% mapped (75,224 instances), 685 unknown keys, 403 once-only.

Workflow: 30 batches × 5 keys (n≤3 each), context analysis → rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census.

Table 1464 → 1614 keys (+150). Coverage 93.0% → 93.3% (75,224 mapped instances unchanged; rare n≤3 keys). Unknown keys 685 → 535 (−150). Once-only unknown keys stay 403.

All 150 keys are rare (n≤3). Most are empty joiners or short inflections in proverb glosses. Flat maps include `NOORIN13:F0B4`, `NOORIN64:F090`, `NOORIN03:F0B0`, `NOORIN83:F0FC`, `NOORIN68:F025`.

Census after batch 195: 1614 keys, 93.3% mapped (75,224 instances), 535 unknown keys.

Next: continue from `_tmp_top_base.py` for batch 196 keys (n≤3).

### Batches 196–230 summary (2026-08-26)

Baseline before batches 196–230: 1614 keys, 93.3% mapped (75,224 instances), 535 unknown keys, 403 once-only.

Workflow: 35 batches × 5 keys (n≤3 each), brute-force context rules in `dump_noorin_lines.py` before `NOORIN82:F0A6` → seed → 0 leftovers per key → census. First pass used START_IDX=300 (n=2–3 keys); continuation pass used START_IDX=0 for remaining n=1 once-only keys.

Table 1614 → 1789 keys (+175). Coverage 93.3% → 93.5% (75,399 mapped, +175 instances). Unknown keys 535 → 360 (−175). Unknown base unique 404 → 229 (−175). Once-only unknown keys 403 → 228.

All 175 keys verified 0 leftovers. Rules data in `_batch196_230_rules_data.json`.

Census after batch 230: 1789 keys, 93.5% mapped (75,399 instances), 360 unknown keys (229 base unique).

Next: continue from `_tmp_top_base.py` for batch 231 keys (n≤3).

### Batches 231–271 + finish (2026-08-26)

Baseline before finish pass: 1789 keys, 93.5% mapped, 360 unknown (229 base + 131 NOORIC overlay).

Steps:
1. Fixed 7 leftover rule gaps: `NOORIN14:F0F7` (5), `NOORIN04:F0DB` (1), `NOORIN82:F038` (1).
2. Added 18 high-count rule-only keys to seed map (were in evidence/SKIP but not in `map`).
3. Added 131 `NOORIC`/`NOORIC01` overlay keys to seed as empty (nuqta/marks).
4. Batches 231–271: 210 remaining n=1 base keys, brute-force context rules, 0 leftovers each.

Table 1789 → **2149 keys** (+360). Coverage **100.0%** (80,638 instances, 0 unknown).

Census after finish: **2149 keys, 100.0% mapped, 0 unknown** on pages 1–169.

### NOORIN transfer scan + bulk decode (2026-08-26)

Added `scripts/census_noorin_transfer.py`. Scans all primary in-scope PUA books
from `data/manifest.csv` (skips Batool-only dictionaries). Writes
`data/decode/noorin_transfer.csv`.

**Transfer results (44 PUA books, Kahawat table 2149 keys):**

| Bucket | Count | Notes |
|---|---|---|
| >=90% mapped | 17 | Anjumshanasi poetry/prose collection |
| 50–89% | 1 | G-Kashmiri-Dictionary (87.3%) |
| 1–49% | 16 | Javaid Rahi dict parts, lok kahani, etc. Latin-range NOORIN codes |
| 0% | 10 | legacy_8bit / TT* fonts; no PUA F0xx glyphs in rawdict |

Kahawat-Kosh: 100.0%. Aks-e-Jamal: 92.8% (was 69.6% on pages 1–10 before table
completion). Typical Anjumshanasi book: 95–97%.

**Does not transfer:** Javaid Rahi dictionary parts (~0.2–0.3%). Those NOORIN
fonts emit Latin-range codes, not PUA `F0xx`. Separate table needed.

Bulk decode started: `py -3 scripts/census_noorin_transfer.py --decode --min-pct 87`
→ 18 books (~4,159 pages) to `data/decode/out/<slug>/page-NNNN.txt`.

**Batch/resume workflow (2026-08-26):** Scripts now support safe resume.
`decode_noorin_flow.py` has `--skip-existing`. Transfer script has
`--skip-census`, `--batch-size N`, and writes
`data/decode/transfer_decode_progress.json`.

```bash
# check status (no re-scan)
py -3 scripts/census_noorin_transfer.py --skip-census --min-pct 87

# decode one book at a time, resume where left off
py -3 scripts/census_noorin_transfer.py --decode --skip-census --min-pct 87 --batch-size 1
```

**Bulk decode complete:** all 17 transferable books (87%+ mapped) decoded to
`data/decode/out/`. ~4,127 pages across Anjumshanasi collection + gojri-adab-ki-tariekh.

### Batches 196–230 summary (2026-08-26)

Baseline before batches 136–165: 1314 keys, 92.7% mapped (74,737 instances), 835 unknown keys, 536 once-only.

Workflow: 30 batches × 5 keys (n≤4 each, mostly n=3), brute-force context rules in `dump_noorin_lines.py` before `NOORIN30:F048` → seed → 0 leftovers per key → census.

Table 1314 → 1464 keys (+150). Coverage 92.7% → 93.0% (75,224 mapped, +487 instances). Unknown keys 835 → 685 (−150). Once-only unknown keys still 536 (batch picked n=2–3 only).

All 150 keys verified 0 leftovers via `_tmp_rule_leftovers136_165.py`. Rules data in `_batch136_165_rules_data.json`.

Census after batch 165: 1464 keys, 93.0% mapped (75,224 instances), 685 unknown keys.

Note: seed file on disk also lists batch 166–195 entries (1614 keys total, 535 unknown, 93.3% in combined census).

Next: run `_tmp_top_base.py` for batch 166 keys.

### Cleanup + spot-check (2026-08-26)

Removed ~290 temp batch scripts (`scripts/_tmp*`, `_batch*`, `_insert*`).
`data/decode/transfer_decode.log` is gitignored (was deleted locally).

**Spot-check decoded output** (`data/decode/out/`, not committed):

| Book | Pages | Placeholders | Pages with PH | Transfer % |
|---|---|---|---|---|
| kahawat-kosh (reference) | 169 | 0 on p50 | — | 100% |
| aks-e-jamal | 121 | 1,756 | 116/121 | 92.8% |
| banjara | 496 | 9,178 | 496/496 | 96.5% |
| gojri-sheryaat | 500 | 7,186 | 490/500 | — |
| g-kashmiri-dictionary | 456 | 11,436 | 437/456 | 87.3% |
| qadim-gojri | 152 | 3,118 | 143/152 | — |

**Kahawat p50 (reference):** zero placeholders. Proverb headwords and glosses
read correctly. Words run together (no spaces) as expected from glyph decode.

**Aks-e-Jamal p25 (poetry):** seven placeholders. Core lines are readable Gojri
with some wrong words (`رایک`, `دپدے`). Usable for spot review, not corpus-ready.

**Banjara p100 (prose):** twenty-six placeholders. First line is PDF header
garbage (Latin/page stamp). Body has merged words and reading-order noise.
Not usable without per-book fixes.

**Gojri-sheryaat p200 (poetry):** seven placeholders plus header garbage.
Poetry lines partly readable but word order and spacing are unreliable.

**G-Kashmiri-Dictionary p50:** twenty-two placeholders. Gojri headwords and
Urdu gloss partly OK; English gloss line is corrupted (`conta5i0ner`).

## 2026-08-31 — NOORIN decode abandoned

User spot-checked Kahawat-Kosh page 28 against a page screenshot. Decoded text
did not match the printed page. OCR ground truth vs decode:

- Page 28: **98.8% word error** (166 ref words, 164 errors)
- Page 59 vs human gold: **98.9% word error**

Example (entry 1): OCR headword `اکھ کانی چنگی، راہ کا نومندو` vs decode
`ر کھکانیچ،کررکاومندھ`.

**Root cause:** census "100% key coverage" only means every `(font,code)` has a
table entry. It does not mean the decoded Unicode matches the page. Neighbor rules
removed `[NOORIN:xx]` placeholders but produced wrong letters.

**Decision:** abandon NOORIN decode-table path. Removed NOORIN scripts, seeds,
transfer CSV, progress JSON, and all local `data/decode/out/` files (~6,350
pages). Archive note: `data/archive/noorin-decode-spike/README.md`.

Batool and Quran GID decode remain in repo but are paused. Corpus path for
font-encoded PDFs is vision OCR.

**Corrects** the 2026-08-26 spot-check conclusion that called Kahawat decode
"production-quality." That was wrong. Placeholder count was a misleading metric.

---

## 2026-09-01 — Step 0.4: clean-text extraction run

Ran `py -3 scripts/extract_clean_text.py`. Output under `data/extracted/`
(gitignored).

**FLI corpus:** 11 files copied to `data/extracted/fli-corpus/`. 82 total
`U+FFFF` in files 08–11 (counts per file in `provenance.jsonl`).

**PDFs extracted (4 books, 1,473 pages):**

| Book | Pages | Chars | Note |
|---|---|---|---|
| Gojri-Hindi-English-Dictionary | 458 | 815,555 | Devanagari Gojri + glosses |
| Essential-Book | 498 | 698,829 | Sample p25/p100: English |
| ABC-Islamic-Studies | 401 | 557,333 | English Islamic studies |
| Revival-of-Islam | 116 | 175,917 | English |

**Provenance:** `data/extracted/provenance.jsonl` (15 records).

**Pending:** user spot-check Devanagari dictionary; FLI files 08–11 for U+FFFF.

**User removed `ABC-Islamic-Studies.pdf` (Sep 2026):** ~95% English Islamic
studies content; embedded Arabic quotes broken in `get_text()`; not useful for
Gojri corpus. PDF deleted; extract folder removed. Manifest: `in_scope=0`,
`tier=9`.

**User removed `Essential-Book.pdf` (Sep 2026):** same — mostly English Islamic
studies, not Gojri corpus. PDF and extract deleted. Manifest `in_scope=0`,
`tier=9`. `Revival-of-Islam.pdf` still on disk if dropped later.

**User removed `Revival-of-Islam.pdf` (Sep 2026):** same bucket — English
Islamic studies, not Gojri corpus. PDF and extract deleted. Manifest `in_scope=0`,
`tier=9`. All three English `good_text` PDFs now dropped. Clean extract corpus
is Devanagari dictionary (458 pages) + FLI only.

**User removed all tier-9 English PDFs from disk (Sep 2026):** 10 files total —
ABC-Islamic-Studies, Essential-Book, Revival-of-Islam, Islam-in-the-Modern-World,
Revisiting-Islam, and Gujjars history vols 1/3/4/5/6. Manifest rows kept with
`removed_by_user_sep2026`. Gojri-titled books (primers, folklore, etc.) unchanged.

---
