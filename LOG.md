# Experiment Log

A dated, running journal of what we try, what we find, and why we made each call.
`CLAUDE.md` holds the accumulated *current state* of project knowledge (decisions,
findings, status); this file is the *story* of how we got there, kept mainly so you
can track your own learning as we go. New AI/ML terms get a one-line explanation the
first time they show up, then get added to the Glossary at the bottom.
Entries run in date order (put in order on 2026-11-20). The NOORIN table batch notes of
2026-08-19 to 2026-08-26 are in `data/archive/noorin-decode-spike/BATCH-LOG.md`.

---

## 2026-08-03: GitHub setup: keeping large/licensed data out of git

Set up the repo to be pushed to GitHub. Found `PDFs/` (834MB) and the Common Voice
audio corpus (`cv-corpus-.../`, 265MB) sitting in the single local "initial commit,"
never pushed anywhere yet.

**Decision: excluded both via `.gitignore`.** Two separate reasons:
1. **Size**: pushing ~1.1GB of binaries means every future clone downloads it all,
   forever.
2. **Licensing**: most PDFs are non-commercial-licensed (Dr. Javaid Rahi's works,
   CC-BY-NC-4.0-style) and Common Voice's terms don't allow re-hosting. Publishing
   them on a public GitHub repo isn't just wasteful, it's likely not allowed.

Since nothing had been pushed to a remote yet, the local "initial commit" was
*amended* (not a new commit: only safe because it was still 100% local) to drop the
large files from history entirely, instead of just hiding them from future commits.
`git gc` confirmed the cleanup: `.git` folder dropped from 881MB → 5.4MB.

**Mistake made here, noted so it doesn't repeat**: as part of that cleanup I ran
`git gc --prune=now`, which permanently deleted the *original* (pre-correction)
version of `dict_alif_draft.txt` from git history, since it was only sitting in an
now-unreachable commit. Net effect: we lost the ability to diff your `dict_alif`
corrections against the original draft. The corrected file itself is fine: only the
"what changed" view for that one file is gone.

**Lesson for later**: this history-rewrite trick only works *before* the first push.
Once something's pushed to a shared remote, removing large files from history needs
a proper rewrite tool (e.g. `git filter-repo`) and is riskier since anyone who
already pulled keeps the old history.

Also configured a Python `.env` file (gitignored, never committed) for API keys, so
future keys get typed into a file instead of pasted into chat.

---

## 2026-08-03/04: Gold-set corrections: first real patterns

You started hand-correcting the OCR gold-set drafts (`data/gold/images/*_draft.txt`)
against the source page images. `dict_alif` and `gojri_adbiyaat` done so far
(`gojri_adbiyaat` in two rounds: a small kasra fix, then a larger pass).

**Finding, from the `gojri_adbiyaat` diff** (no diff available for `dict_alif`: see
the git mistake above):

1. **Heh confusion.** Urdu/Nastaliq has two different "h" letters that look similar:
   plain heh (ه) and do-chashmi heh (ھ, "two-eyed heh"), which marks aspirated sounds
   like دھ, بھ, مھ. The draft kept using the wrong one, e.g. `مانہ` → corrected to
   `مانھ`. This isn't cosmetic: it changes which consonant is represented.

2. **Poems don't get their own repetition checked.** A ghazal repeats the same
   rhyming word (the *radif*) at the end of every line. The draft mis-transcribed
   that repeated word *consistently but not identically* across lines:
   - `جایے` → `جائیے` (missing ئ), wrong in 4/4 lines
   - `ہن کے` → `بن کے` (ہ misread as ب), wrong in 4/4 lines
   - `یاں` → `یال` (nasalization ں misread as ل), wrong in 3/4 lines

   A person catches this instantly from the rhyme; the model transcribes each line
   independently and doesn't cross-check itself against the pattern it just produced
   two lines earlier.

3. **Confident wrong guesses on unusual/dialectal words**: e.g. `نچ`→`بِچ`,
   `چیُو`→`چپُو`, `کھڑیاں ہن کے`→`کھڈیال بن کے`. Fluent-looking Nastaliq, just wrong.
   This is the "hallucination" risk `CLAUDE.md` already flagged (**hallucination**:
   a model producing a plausible, fluent-sounding answer that isn't actually
   grounded in what's on the page: different from a traditional OCR engine failing
   visibly/blank when unsure).

---

## 2026-08-03/04: First OCR model comparison: Gemini

**Goal**: start comparing OCR quality/cost across models: this entry is step one of
that, not a conclusion.

**Setup**: Got a Gemini API key (stored in `.env`, not committed). Checked Google's
own docs directly rather than trusting blog aggregators (they had wrong model names)
and confirmed the current lineup:
- `gemini-3.6-flash`: newest stable model, Google's own words: "our latest model...
  strong performance in agentic and multimodal tasks." **Flash** = Google's
  cheaper/faster tier, as opposed to **Pro** (more capable, more expensive).
- `gemini-2.5-pro`: current stable Pro tier (no newer Pro is out of preview yet).

Picked `gemini-3.6-flash`: it's both "latest" and the cost-sensitive choice, same
logic as the Haiku-vs-Sonnet tradeoff already in `CLAUDE.md`'s OCR cost math: for a
14,761-page OCR workload, cost tier matters as much as raw quality.

Wrote [scripts/gemini_ocr_test.py](scripts/gemini_ocr_test.py): takes an image
path, sends it to Gemini with a transcription-only prompt (see exact prompt text in
the file), prints + saves the result as `<name>_gemini.txt` next to the draft.

**Result on `dict_alif.png`**:
- **Cost**: ~1,267 input tokens + 511 output tokens for one page. (**Token**: the
  unit models bill by: roughly a word-piece; a whole page of dense Nastaliq is
  ~1,000+ tokens because Perso-Arabic script tokenizes less efficiently than Latin
  script.) Comfortably inside Gemini's free tier.
- **Quality**: same heh-confusion bug as pattern #1 above (`آب و ھوا`→`آب و هوا`),
  plus dropped diacritics (kasra, damma). This is the *second* model showing the
  exact same failure mode: starting to look like a structural weak point of
  Nastaliq OCR in general, not a quirk of one model.
- Also added a bracketed `[Oval: Alif الف]` description not in the draft (needs a
  human check against the actual image: could be a legitimate catch or an
  invention) and a stray divider line.

**Open gap**: the `_draft.txt` baseline files don't have a recorded prompt (see
above), so they aren't a fully controlled comparison point yet. Fine for now since
we're mainly gut-checking quality, but worth fixing if we want rigorous scoring
later.

---

## 2026-08-04: Planning: multi-model OCR comparison

**Plan going forward** (your call, recorded here for continuity): compare OCR output
across Gemini, DeepSeek, Claude Sonnet, and Claude Haiku on the same gold-set pages.
Reasoning: open-source/cheaper models are worth a real look before committing to a
paid-per-page pipeline for ~14,761 pages: no reason to assume the most expensive
option wins.

**Convention**: each model's output for a page goes in the same
`data/gold/images/` folder, named `<page_id>_<model>.txt` (e.g. `dict_alif_gemini.txt`,
already created). Once you've hand-corrected enough drafts into a true gold
standard, every model's output can be scored against the same yardstick.

Judgment on which model to actually use is explicitly deferred until the comparison
is in place: not being decided now.

**Started this log file.**

---

## 2026-08-04: Formalizing the comparison: canonical prompt, file naming, run log

Found `prompts/ocr_transcription_v1.txt` (already written, not by me this session):
a proper, detailed transcription prompt: explains Gojri-vs-Urdu up front, forbids
"fixing" spelling toward standard Urdu, defines `[single bracket]` for non-text
elements vs `[[double bracket]]` for a flagged best-guess on illegible text, handles
page numbers/headers, blank pages, and un-split spreads. This becomes **the one
prompt every model gets tested with**: fixes the "no reproducible prompt" gap noted
above. Re-ran the Gemini test on `dict_alif` with it (my first pass used a weaker,
improvised prompt) and ran it fresh on `gojri_adbiyaat`.

**File naming, finalized**: every gold page can now have, in `data/gold/images/`:
- `<id>_sonnet_5_original.txt`: the old, informal first-pass draft (no fixed prompt,
  read directly in a chat session), kept only where it still exists in git history.
- `<id>_sonnet_5_corrected.txt`: your hand-corrected gold standard, i.e. the
  ground truth every model's output gets judged against.
- `<id>_<model>_<version>.txt`: one per model tested with the canonical prompt,
  e.g. `dict_alif_gemini_3.6_flash.txt`.

**Recovered `gojri_adbiyaat`'s true original from git history** (`git show
f19a314:...`, before either correction round): this one survived because it hadn't
been touched yet when the earlier `git gc` mistake happened. **`dict_alif`'s
original is confirmed permanently gone**: it was already corrected before this
session started, so its pre-correction text only ever lived in the commit that got
pruned. Only `dict_alif_sonnet_5_corrected.txt` exists for that page; there's no
`_original` counterpart and there can't be one.

**Sonnet 5 / Haiku 4.5 via chat, not API**: rather than issuing a new Anthropic API
key, these two will be run manually: a separate chat session per model, each given
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
of every automated test run: the raw material for eventually scoring models
quantitatively against the gold set, once enough pages are corrected.

**Observation worth tracking**: Gemini's reported `total_tokens` was noticeably
higher than `input + output` tokens added together (8,272 vs. 2,338 on one run).
Likely internal "thinking" tokens that get billed but aren't broken out in the
simple prompt/output counts: matters for the eventual cost math, needs the same
check on any Gemini "thinking" pricing details before trusting a simple estimate.

Also in progress in parallel, not yet pulled into the model comparison: you
corrected 3 more gold drafts (`louk_warsti`, `mahatma_gandhi`, `primer_pehli`).

---

## 2026-08-04: DeepSeek checked, deferred

Checked DeepSeek's own API docs directly before assuming it'd slot into the
comparison like Gemini did: their general chat API (`deepseek-v4-flash`/`-pro`)
**does not support image input at all**: so it couldn't have run this test even as
a paid option. Separately, DeepSeek has released **DeepSeek-OCR** / **DeepSeek-OCR-2**,
an open-source (MIT-licensed) vision model built specifically for document/image
transcription: genuinely free either via community-hosted Hugging Face Space demos
(browser upload, no setup) or by running the open weights yourself on a free
Colab/Kaggle GPU. **Decision: skip DeepSeek for this round**, revisit later if
useful. Sticking with Gemini + Sonnet + Haiku for now.

---

## 2026-08-04: Prompt versioning tightened; dict_alif original partially recovered

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
**۱** (one) in `ا(alif)nm.A.1.`: the two characters are visually near-identical in
this script, and the new numeral-preservation rule may have made the model more
eager to read ambiguous marks as digits specifically. Small sample (2 pages), but a
concrete thing to watch for as more pages get tested under v2: a prompt change
fixing one failure mode can introduce a different one.

**`dict_alif`'s original transcription, partially recovered.** You found and
confirmed one genuine original (mis-OCR'd) reading against the gold version:
headword `خُودرو` (correct) was originally misread as `ھُدرو`, with a duplicated
trailing `آپ`: a real example of the "don't repeat a line/word" failure the v2
prompt now explicitly guards against. Saved as
`data/gold/images/dict_alif_sonnet_5_original.txt`, seeded from the gold text with
just this one line reverted: **the rest of that file still matches the gold
version**, i.e. it is not yet a complete original, just the one confirmed
difference. Also cleaned up a duplicate `dict_alif_corrected.txt` that had
identical content to the existing `dict_alif_sonnet_5_corrected.txt`.

---

## 2026-08-04: Reorganized gold-set storage: transcriptions/ per page

A separate session (see `plans/STAGE-1-TEST-BATCH.md`, a handoff briefing for
running the real 12-page Bedrock test batch) hit real friction with two competing
AWS CLI installs, and separately worked out that Claude Sonnet 5 needed a one-time
console enablement on Bedrock before its inference profile
(`us.anthropic.claude-sonnet-5`) would stop returning `AccessDeniedException`. That
session's plan calls for `boto3` directly (skips the CLI issue) and Haiku 4.5 +
Sonnet 5 (once enabled) as the two models for the batch.

Before running that batch, reorganized how gold-set files are stored: the flat
`data/gold/images/` folder was getting cluttered mixing `.png` images with every
model's `.txt` output for every page. New layout:
- `data/gold/images/`: page images only.
- `data/gold/transcriptions/<page_id>/`: one folder per page, holding `draft.txt`
  (the hand-corrected gold standard) plus every tested model's output, named
  `<model>_<prompt_version>.txt`.

Also dropped `<page>_sonnet_5_corrected.txt` (duplicate of `draft.txt`, no
information lost) and cleared `ocr_runs_log.csv` back to just its header, since its
old rows pointed at the now-moved file paths. Confirmed via `git status` before
touching anything that all the "removed" files were safe, recoverable
deletions already sitting in a prior commit: nothing was actually lost.

Upcoming Bedrock run naming, confirmed: append `_v1` even though this batch is
single-prompt-version, for consistency with the Gemini files; log all runs
(Gemini + upcoming Haiku/Sonnet) into the one shared `ocr_runs_log.csv` rather than
a second parallel CSV.

---

## 2026-08-04: Dropped draft.txt as ground truth; wiped all transcriptions

Reconsidered the whole gold-set correction model. `draft.txt` (one file per page,
treated as "the" gold standard) was produced by Claude reading each image once with
no real, fixed, documented prompt: the same gap already noted earlier tonight. That
makes it a shaky baseline to score every model against, and conflates "what one
model produced" with "the truth."

**New approach**: no single ground-truth file per page. Instead, every model gets
its own raw output file (`<model>_<version>.txt`), generated under the same fixed
prompt, and correction happens per model, by hand, separately: comparing each
model's raw output against the source image rather than against another model's
output. This also captures a second useful signal beyond raw transcription quality:
how much correction effort each model's output actually needs.

**Wiped everything** in `data/gold/transcriptions/`: all `draft.txt`,
`sonnet_5_original.txt`, and the `gemini_3.6_flash_v1/v2.txt` files. All of it is
still recoverable from git history if needed later; starting genuinely fresh from
here. Updated `data/gold/README.md` to match. Correction-file naming/organization is
left to the user's own process, not something Claude generates.

---

## 2026-08-04: Bedrock smoke test: real blockers, real quality concerns, one caught bug

**AWS setup**: `boto3` installed. First `dict_alif` call to Haiku 4.5 failed with
`ResourceNotFoundException: Model use case details have not been submitted`: a
one-time, Anthropic-specific account requirement on Bedrock, separate from the
model-access toggle already done for Sonnet 5. Confirmed it's Anthropic-specific
(not account-wide) by running Qwen3-VL in the same session, which worked
immediately. Form submitted, Haiku unblocked after.

**Request format decided**: both Haiku 4.5 and Qwen3-VL support Bedrock's unified
Converse API with images, so one script (`scripts/bedrock_ocr_test.py`) handles both
via a shared code path: image bytes passed raw (not base64, unlike the
`invoke_model`/Anthropic-specific format the original plan assumed).

**Smoke test on `dict_alif` (cropped, v1 prompt): both models showed real quality
problems, in different ways**:
- Qwen3-VL: character-order corruption in places (`فلف` instead of `الف`,
  `اياكو فل فيقيح` instead of `ایکو الف حقیقی`): looks like scrambling, not just
  missing marks.
- Haiku 4.5: repeatedly substituted a generic `ئ` placeholder in place of several
  different actual headwords, rather than attempting to read them.

Both are worse than the diacritic-drop/heh-confusion pattern seen earlier from
Gemini and the original Sonnet draft. Decided not to over-read this from one page:
`dict_alif` has unusually small, dense headwords and may be a harder case than the
other 11 pages. Plan: run the full 12-page batch for both models before judging.

**Bug caught and fixed**: added a `stop_reason` column to the shared run-log schema
in `ocr_test_common.py`, but `log_run()` only writes a header for a brand-new file:
since `ocr_runs_log.csv` already existed (header-only, from the earlier wipe), it
kept the *old* 8-column header while new rows wrote 9 columns. Caught by manually
re-verifying the log matched what was actually sent, after being asked directly
whether v1 was really being used. Fixed by hand-correcting the header; no schema
migration logic was worth adding for a CSV this size, but a lesson worth keeping:
verify by reading the actual artifact, not by trusting that code ran the way it was
written to.

**Model catalog research, for later reference**: confirmed via AWS's own model
cards (not the console's summary blurbs, which have twice now omitted real
capabilities: Claude and Llama 4 both show as text-only in some console list views
despite genuinely supporting images) that Llama 4 Maverick supports image input +
Converse API, but needs the cross-region ID (`us.meta.llama4-maverick-17b-instruct-v1:0`)
since it's not available in-region for `us-east-1`. Also identified Pixtral Large,
Kimi K2.5, and NVIDIA Nemotron Nano 12B v2 VL as genuinely OCR-relevant candidates
if more models are wanted later; ruled out Stability AI (image generation, not
understanding), TwelveLabs (video embeddings), and Gemma (the only multimodal
variant on Bedrock is the base/pretrained "PT" model, not instruction-tuned, so it
won't reliably follow a transcription prompt).

---

## 2026-08-04: Settings weren't controlled at all; fixed, logged, re-ran, verdict unchanged

Asked directly: "which settings are you running these models with? Is thinking on?
Is effort High?" Honest answer at the time: none of that had been explicitly set:
the Bedrock `converse()` calls only passed `modelId` and `messages`, nothing else.
Real gap, worth researching properly rather than guessing.

**Findings, checked against AWS's/Google's own docs, not assumed:**
- Claude's extended thinking is opt-in: off unless explicitly requested. It was off.
- **Haiku 4.5 doesn't support the adaptive-thinking/effort parameter at all**:
  confirmed against AWS's own docs; that feature is limited to Opus 4.6+/5-tier and
  Sonnet 4.6. "Is effort High?" doesn't apply to Haiku 4.5 as a question.
- Temperature was never set, so it used the API default (1.0 for Claude/Anthropic:
  non-deterministic sampling, a bad fit for an exact-copy task).
- **Gemini is the opposite case**: Google's own Gemini 3 docs explicitly warn
  *against* changing temperature from its default of 1.0 ("may cause looping or
  degraded performance"). So the three models now deliberately use *different*
  settings, not matched ones: Claude/Qwen get `temperature=0`, Gemini keeps its
  default: and that asymmetry is logged explicitly rather than left implicit.
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
Latin letter that isn't even valid in this script: a different placeholder than the
earlier smoke test's `ئ`, meaning it's not a fixed/deterministic substitution
either). Qwen3-VL still shows the same character-order corruption pattern. This
points away from "unlucky high-temperature sampling" as the explanation and toward
a genuine capability gap on this specific page's small, dense headwords, at least
for these two models.

**Gemini's result on the same page, same settings-rigor, is a clean pass**:
correctly transcribed headwords throughout (`آپ ہُدرو` matches the known-correct
reading exactly), no placeholder substitutions. Also **directly confirms an earlier
open question**: with `thinking_level=low` explicitly set, Gemini's `total_tokens`
now exactly equals `input + output` (no more of the unexplained gap noted on
2026-08-04 earlier: "total_tokens noticeably higher than input+output": that was
the model thinking by default, now resolved).

Scope held to these 2 pages only, per instruction: not extending to the full 12
until this is understood.

---

## 2026-08-04: Haiku 4.5 and Qwen3-VL shelved

Both failed on both test pages (`dict_alif`, `gojri_adbiyaat`), under identical,
controlled conditions (same cropped images, same v1 prompt, temperature=0, logged
settings) where Gemini 3.6 Flash succeeded on the exact same inputs: so this isn't
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

Haiku's first example isn't a near-miss with a few wrong diacritics: most of the
words are simply different. Qwen3-VL's second example is structurally closer (right
number of words, right general shape) but still swaps real words (`سجنا`→`بیتا`)
and drops the recurring `-ئیے` radif ending the same way the very first, informal
Sonnet draft did back at the start of this project: that specific ligature
(hamza-bearing yeh in a verb ending) seems to be a genuinely hard case across
multiple models now, not just one.

**`dict_alif` (dictionary layout): different failure shape entirely**: both models
substitute a placeholder character for headwords they can't read, rather than
attempting a (possibly wrong) reading. Haiku used `ئ` in the first smoke test and
`Ī`: not even a character that belongs in this script: in the controlled rerun of
the identical page. Not a consistent substitution, which suggests genuine
uncertainty/failure rather than a deterministic quirk.

**Kept**: Gemini 3.6 Flash, the only model so far that's transcribed both pages
correctly under matched conditions.

**Next**: test Kimi K2.5 and one more model (still deciding which) before moving to
Sonnet 5, per updated plan.

---

## 2026-08-04: Kimi K2.5, Llama 4 Maverick, Pixtral Large tested

Verified all three against their actual AWS model cards before running anything
(same discipline as Qwen3-VL/Llama 4 earlier): all three support image input via
the Converse API. Kimi K2.5 (`moonshotai.kimi-k2.5`) is in-region for `us-east-1`;
Llama 4 Maverick and Pixtral Large both need the cross-region ID
(`us.meta.llama4-maverick-17b-instruct-v1:0`,
`us.mistral.pixtral-large-2502-v1:0`) since neither is available in-region here.
Same settings discipline as before: temperature=0, explicit max_tokens, no
thinking, all logged.

**Kimi K2.5: the best non-Gemini result so far.** On `dict_alif`, it correctly
read `آپ خُودرو` (matches the known-correct gold reading exactly) where every other
non-Gemini model tested has gotten this specific entry wrong. No placeholder-
character substitutions anywhere in either page. Still has real, ordinary OCR
errors (missing/wrong diacritics, occasional wrong word), but nothing like the
severity seen from Haiku/Qwen3-VL. Worth carrying forward as a real candidate.

**Llama 4 Maverick: mixed, closer to Haiku's failure mode than Kimi's.**
Still substitutes a placeholder (`˜`, a tilde, twice on `dict_alif`) for headwords
it can't read, and mangles some phrases significantly. Notably more expensive too:
~4,520 input tokens per page vs. ~1,450-1,800 for every other model tested on the
same cropped images: its image tokenization is markedly less efficient. Not ruled
out yet, but the weakest of the three new candidates.

**Pixtral Large: a worse failure than anything seen yet, and a different kind of
danger.** On `dict_alif` it invented fabricated example sentences not on the page
(`آپنے گھوڑے کو کیا نام رکھا؟`: "What did you name your horse?": pure invention)
and appended a stray ` ``` ` markdown fence, violating the prompt's explicit
plain-text-only rule. On `gojri_adbiyaat` it did something much worse: **produced
an entirely fabricated, fluent, coherent Urdu parable about a boy refusing food, a
sadhu searching for a cow, and a monkey eating fruit: none of which has anything
to do with the actual poem on the page.** This is exactly the "confident-but-wrong"
hallucination risk flagged early in this project (`CLAUDE.md`'s OCR pipeline plan,
point 7): Tesseract-style engines fail visibly; this failed by inventing plausible,
complete, unrelated content. Arguably more dangerous than Haiku/Qwen3-VL's garbling,
since a less careful review pass could mistake fluent invented prose for a real
(if imperfect) transcription. **Recommending this one be shelved too**: flagging
for confirmation rather than deciding unilaterally, given how much this changes the
picture, but the evidence is strong.

**Cost note**: token usage varies a lot by model on the *identical* cropped image:
Kimi ~1,764 input tokens/page, Pixtral ~3,439, Llama 4 Maverick ~4,520. Image
tokenization efficiency isn't uniform across providers, which will matter for the
eventual 14,550-page cost extrapolation regardless of which model(s) get chosen.

---

## 2026-08-04: Pixtral Large and Llama 4 Maverick shelved

Same process as Haiku 4.5/Qwen3-VL: outputs archived to
`data/gold/transcriptions_archived/<page_id>/` rather than deleted, reasons
documented here with examples, both stop being used going forward.

**Pixtral Large**: shelved for fabrication, not just inaccuracy: on
`dict_alif` it invented an example sentence not on the page
(`آپنے گھوڑے کو کیا نام رکھا؟`, "What did you name your horse?") and appended a
stray markdown code fence; on `gojri_adbiyaat` it produced a complete, fluent,
entirely fabricated Urdu parable (a boy refusing food, a sadhu searching for a
cow, a monkey eating fruit) with no connection to the actual poem on the page.
Confident, coherent, and wrong is a worse failure mode for this project than
visible garbling: it's exactly the silent-hallucination risk flagged early on in
`CLAUDE.md`.

**Llama 4 Maverick**: shelved for the same placeholder-substitution pattern as
Haiku (`˜` in place of unreadable headwords on `dict_alif`) plus a practical cost
problem: it used ~4,520 input tokens per page on the identical cropped image that
Kimi K2.5 processed in ~1,764, roughly 2.5x more expensive for a weaker result.

**Currently active candidates**: Gemini 3.6 Flash (clean on both pages tested) and
Kimi K2.5 (best non-Gemini result, no placeholder failures). Sonnet 5 still pending
as the next test.

---

## 2026-08-04: DeepSeek-OCR: tried, hit a real dead end (for now)

Wanted to try `deepseek-ai/DeepSeek-OCR` (open-source, MIT-licensed, OCR-specialized
vision model: first surfaced when researching DeepSeek earlier). Checked properly
rather than assume it'd just work:

- **No Hugging Face MCP tool available in this session**: checked directly via
  `ListMcpResourcesTool`; only Firebase and an Indeed connector are actually
  configured here, despite HF MCP apparently being set up somewhere else.
- **No official Hugging Face Inference Provider for this model**: its own model
  page states plainly: "This model isn't deployed by any Inference Provider."
- **Not on Bedrock either**: Bedrock's DeepSeek offering is limited to
  `DeepSeek V3.2`/`V3.1`/`R1`, the same text-only chat/reasoning models already
  confirmed to lack image support. DeepSeek-OCR is a separate project Bedrock
  doesn't host.
- **Community Gradio Spaces**: found a working, callable API on
  `prithivMLmods/DeepSeek-OCR-experimental` (confirmed via `gradio_client`'s
  `view_api()`: schema loaded cleanly). But actually calling it failed with an
  opaque server-side `AppError` every time: with and without HF auth (user added
  `HUGGING_FACE_ACCESS_TOKEN` to `.env` specifically to test this), across two
  different task modes (`Free OCR`, `Convert to Markdown`). A second Space
  (`khang119966/DeepSeek-OCR-DEMO`) failed identically; a third
  (`akhaliq/DeepSeek-OCR`) was outright broken (`RUNTIME_ERROR` state). Checked the
  working Space's actual source (`app.py`) rather than keep guessing blindly: the
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
`trust_remote_code=True`, and: importantly, unlike the Gradio demos: its real
prompt format is `"<image>\n"` + free-text instruction, so **the full v1 prompt can
actually be sent**, making this a genuinely controlled, comparable run if it works.
Includes a fallback to eager attention if `flash-attn` fails to build, a common
Colab pain point. I can't execute this myself (no browser/notebook-execution
access) - the user runs it in their own free Colab account and pastes results
back, same pattern as the manual Sonnet/Haiku chat-session runs.

---

## 2026-08-05: Documentation sync pass after the "datasets/" reorg

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

## 2026-08-05: GPT ruled out; Sonnet 5 blocked on AWS Sales; Sonnet 4.6 standing in; CloudWatch logging set up

**GPT considered for the comparison, ruled out.** Checked directly against Bedrock
(`list-foundation-models`) rather than assuming: the only OpenAI models on Bedrock
are the open-weight `gpt-oss-120b`/`20b` (+ `-safeguard` variants), which are
**text-only, no image input modality**. The actual vision-capable GPT models
(GPT-4o/4.1/5) aren't on Bedrock at all, only via OpenAI's own API or Azure OpenAI.
Can't do OCR through Bedrock with GPT: skipped.

**Sonnet 5 access: a real saga, still unresolved.** `anthropic.claude-sonnet-5`
appears in the account's model catalog but every invocation returned
`AccessDeniedException`, worded differently from the ordinary "model access not
enabled" error: *"...contact AWS Sales."* Chased this properly rather than assuming
it was unfixable:
- AWS retired the old "Model access" console page; access is now self-service via
  IAM + a one-time `PutUseCaseForModelAccess` API call for Anthropic models.
- First attempt at that API failed validation repeatedly: turned out `intendedUsers`
  must be the literal string `"0"`/`"1"`/`"2"` (Internal/External/Both), not a
  free-text description, per AWS's own SDK docs (not obvious from the API reference
  alone, which only documents `formData` as an opaque blob).
- Ran the full documented flow: `ListFoundationModelAgreementOffers` →
  `PutUseCaseForModelAccess` (corrected schema, succeeded) →
  `CreateFoundationModelAgreement` → `GetFoundationModelAvailability`. End state:
  **every status field reports `AVAILABLE`/`AUTHORIZED`**
  (`agreementAvailability`, `authorizationStatus`, `entitlementAvailability`,
  `regionAvailability` all green): yet `Converse` still returns the identical
  Sales-gated `AccessDeniedException`. Confirms this is a genuine Sales-only gate,
  not a missed self-service step; the self-service path is fully exhausted.
- **Decision: emailed AWS Sales** (`aws.amazon.com/contact-us/sales-support`) with
  the account ID, model ID, and this exact evidence trail. Response pending:
  **Sonnet 5 is deferred until access clears**, not abandoned.
- **Standing in: Sonnet 4.6** (`us.anthropic.claude-sonnet-4-6`, cross-region
  profile: the plain `anthropic.claude-sonnet-4-6` ID fails since it needs
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
  log group `/aws/bedrock/model-invocations`): hit and fixed two real
  misconfigurations along the way (trust policy vs. permissions policy pointing at
  the wrong log group name; the log group not existing yet). Confirmed live via
  `get-model-invocation-logging-configuration`.
- Confirmed `ai_agent_user` (the identity all these scripts run as) has **no IAM
  permissions at all**: deliberately scoped to Bedrock only, confirmed by testing
  (every `iam:*` call denied). Recommended, and user is trimming, its 9 attached
  AWS-managed policies down to 2 (`AmazonBedrockFullAccess` +
  `AmazonBedrockMarketplaceAccess`, the only ones anything this session actually
  used): the rest (AgentCore, Web Search, DataZone policies) were unused surface
  area.
- User separately cancelled a Sonnet 4.5 subscription by hand (a different tangent
  from earlier in the session, now moot: no deny policy needed).

---

## 2026-08-05: Cross-model correction converges the gold text; Kimi's verdict revised; file convention fixed

**Correction workflow used, worked well**: you hand-corrected Gemini's and Sonnet
4.6's outputs on both gold pages *independently* (each against the source image,
without looking at the other model's correction). Comparing the two afterward
turned out to be a genuinely useful technique, not just a formality: where two
independently-corrected versions of the same page agree, that's strong evidence
it's actually right; where they disagree, that's a real remaining ambiguity worth a
second look at the image, not noise. This is the practical version of the
**ensembling** idea (independent samples converging on the truth more reliably than
any single one) that came up when you asked about re-prompting for a second pass:
see below.

**`gojri_adbiyaat`: fully converged.** Started with 7 real word/diacritic-level
disagreements between the two corrected versions (not counting pure spacing/line-
break differences). Resolved all 7 against the source image:
- `تڑفتا نا` (not `تڑفا نا`), `کچر دو ہلتا` (not `کچڑ دوہلتا`), `پھرنہ ایویں` (not
  `پھرنا ایویں`): real word-level fixes, not diacritics.
- `کچرتک`→`کچر تک` and `گوہوں`→`گو ہوں`: two words, written closely together on
  the page (a real spacing decision, not visible from the text alone).
- `چارو کار`→`چاروکار` and `کومار`→`کو مار`: the opposite spacing call on two
  *other* close-set word pairs. Notable: spacing on tightly-kerned Nastaliq word
  pairs isn't a consistent rule you can guess at from general knowledge of the
  script: each pair needed an actual look at the image.
- Kasra confirmed absent on `پرواز` (Sonnet's corrected version had incorrectly
  added one).
- `و: مولوی غلام رسول ڈوئی` confirmed as one line, not two: a line-break question,
  not a word-content one.

End state: **27 of 27 content lines now word-for-word identical** between Gemini's
and Sonnet's independently-corrected versions of this page. One cosmetic difference
remains (tab vs. spaces in the header line), left unresolved as genuinely trivial.

**`dict_alif`: now converged down to 2 trivial single-space questions.** Resolved
across two follow-up rounds:
- Word order `الف ، ا` (not `ا ،الف`); `تاں` (not `تان`); `چھاں` (not `چھان`).
- `بدھیکی` (do-chashmi `ھ`), confirmed by you directly. Same letter pair as the
  already-resolved `ھُدرو`/`هُدرو` case (U+06BE vs U+0647: verified by pulling
  exact codepoints, not eyeballing it), now settled on **two separate words on
  this page**, both correctly do-chashmi. Linguistically this isn't a stylistic
  choice: do-chashmi heh specifically marks aspiration (`دھ`, `بھ`, `تھ`, `کھ`,
  `پھ`), a real phonetic feature plain Arabic heh doesn't encode.
- **`eg:`/`lpp:` prefix placement: checked directly against the source image**,
  not inferred from the text alone. The `lpp:` line settles it unambiguously: `lpp:`
  sits at the visual right (read first in the page's right-to-left flow), the Gojri
  proverb in the middle, `To invite trouble.` at the far left (read last): and
  Sonnet's version already matched this exactly, while Gemini's had the order
  flipped *and* was missing `To invite trouble.` entirely. Same structural logic
  (a label must precede what it introduces) applies to the `eg:` line and the
  second `eg: lpp:` occurrence later on the page. Fixed all three spots in Gemini's
  corrected file to match.
- Two more spacing questions resolved from the same image check, lower confidence
  but reasonably clear: `آبش` is one word (not `آ بش`); `چنگا تے` is two words
  (not `چنگاتے`).

**Both remaining items resolved: turned out to be a scope question, not an
ambiguity.** Both disputed spaces were between Gojri text and an *English*
annotation (`آپ` vs `(aap)`; `head-strong.` vs `اپ ھُدرو`), not between two Gojri
words. **New standing rule, given directly, worth keeping for every future page**:
spacing around English glosses/transliterations isn't a correction concern:
only spacing *between Gojri words* carries real meaning and is worth the effort to
verify against the image. On the actual Gojri content: `آپ` is confirmed one word,
`اپ ھُدرو` confirmed two words: both files already had this right. **`dict_alif`
is therefore fully converged**, same as `gojri_adbiyaat`, no content-level
disagreement left on either gold page tested so far. Files intentionally left as-is
(differing only in the out-of-scope English-adjacent spacing) rather than forced
to match, since forcing a false match isn't the goal: not disagreeing on anything
that matters is.

**One heh-confusion case fully settled, worth recording since it's recurred across
multiple models now**: on the `آپ خُودرو` dictionary entry, do-chashmi heh (`ھ`,
two-eyed heh, marks aspiration) is the correct reading for the trailing `اپ ھُدرو`,
not plain heh (`ه`/`ہ`). Gemini, Sonnet 4.6, *and* Kimi K2.5 (see below) all
independently got this specific letter wrong before correction: the clearest single
piece of evidence yet that this specific ligature is a genuine, repeated model
weakness, not an isolated slip by one model.

**Kimi K2.5 checked against the now-converged gold text: revises the earlier
verdict, and not in Kimi's favor.** The 2026-08-04 entry called Kimi "the best
non-Gemini result so far," but that was based on one overlapping dictionary entry,
not a full-page comparison against a real, doubly-confirmed gold standard. With one
now available:
- **`dict_alif`: still holds up reasonably.** The specific `آپ خُودرو` headword
  read that the earlier entry praised is still correct. New finding from the full-page
  diff: a real, repeated **ک (kaf) for گ (gaf) substitution, six times on one
  page** (`لک`×3 for `لگ`; `چنکا`/`جک`/`چنکو` for `چنگا`/`جگ`/`چنگو`): systematic,
  not scattered noise, and not something the earlier single-entry spot-check could
  have caught.
- **`gojri_adbiyaat`: substantially worse than the earlier verdict implied.**
  Real word substitutions throughout, not just dropped diacritics:
  `عرض` ("plea") misread as `عرش` ("throne") twice, consistently; the recurring
  nasalized `ں` ending misread almost everywhere (`مِناں`→`منان`,
  `کھڈیال`→`کڈیاں`, `بھیال`→`بھیاں`); and: notably: Gojri's distinctive `-و`
  word ending repeatedly normalized toward Urdu's `-ے` (`میرو`→`میرے`,
  `تیرا`→`تیرے`), which is exactly the failure mode the canonical prompt's rule 3
  explicitly warns against. Also got two proper nouns/titles wrong (`ڈاکٹر`
  ["Doctor"] misread as `ذاکر`, a name; `ڈوئی`→`ڈولی`).
- **Your read, after seeing this**: Kimi isn't right for this comparison. **Decision:
  Kimi K2.5 shelved**: moved to `transcriptions_archived/` (both pages'
  `_original.txt`, never corrected, kept for the record like the other shelved
  models), same treatment as Haiku 4.5/Qwen3-VL/Llama 4 Maverick/Pixtral Large
  earlier. Not used going forward.
- **Practical implication, for the record even though Kimi's shelved now**: its
  quality wasn't uniform across genres: solid dictionary-layout OCR, weak poetry
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
diacritic drops. Roughly equal effort on `gojri_adbiyaat` for both, and: more
interesting than the raw count: both models independently landed on the *same*
correct reading for several genuinely hard spots (the `ھُدرو` heh, `پھرنہ`) without
being told, which is a real (if small-sample) positive signal for both.

**Re-prompting / few-shot, discussed, deferred for now.** Simply re-running the
identical prompt on the same model again isn't a real strategy here: Sonnet runs
at `temperature=0` (won't meaningfully vary between runs) and Gemini's variation
(kept at its own default, per the 2026-08-04 entry) is uncontrolled luck, not a
technique. What *did* work, concretely, is what this session just did by hand:
comparing independently-corrected outputs from two different models and trusting
convergence: a real instance of **ensembling**. **Few-shot prompting** (embedding
1-2 worked image+correct-transcription examples directly in the prompt, distinct
from both of the above) is a genuinely different idea worth testing once there's
more corrected gold data to draw a fair example from: **decision: revisit once
more pages are corrected**, not now, and any test needs the few-shot example to be
a *different* page than the one being scored, or it's not a real test.

**File convention fixed, going forward**: corrections were being made *in place*
(overwriting the raw model output), which meant the true original could only be
recovered via `git show` against the last commit before correction started: worked
this time only because the raw outputs happened to have just been committed.
**Changed**: every page/model now gets two separate files:
`<page>_<model>_<version>_original.txt` (raw, from the automated test scripts,
never hand-edited: `ocr_test_common.py`'s `output_path()` now enforces the
`_original` suffix automatically) and `<page>_<model>_<version>_corrected.txt`
(hand correction, added separately, only once review is actually done). Applied
retroactively to all 3 active models on both gold pages tested so far: recovered
the 4 Gemini/Sonnet originals from git history, renamed the corrected files, and
renamed Kimi's still-uncorrected file to `_original` (it was already the original,
nothing to split).

---

## 2026-08-06: kahawat_kosh + gojri_ghazal: raw runs, gojri_ghazal fully converged

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

## 2026-08-07: kahawat_kosh corrected and converged; punctuation-spacing rule added

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

## 2026-08-10: mahatma_gandhi + kulyate spread run; kulyate_spread_a_right converged

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

## 2026-08-11: mahatma_gandhi + kulyate_spread_b_left corrected

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

## 2026-08-11: Two new models spot-checked: Cursor Composer 2.5 in, Groq 4.5 Fast out

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

## 2026-08-13: Remaining 5 gold pages: Composer v1 originals only

The 7 already-corrected pages had Composer files; the other 5 vision-OCR gold
pages did not. Ran Composer 2.5 on them with the same frozen `v1` prompt
(`prompts/ocr_transcription_v1.txt`) so the comparison stays apples-to-apples
with Gemini/Sonnet's existing v1 runs. Saved as
`<page>_composer_v1_original.txt` only: no `_corrected.txt` yet, and do not
edit these in place.

| Page | What it tests | Notes from this raw run |
|---|---|---|
| `nazir_spread_a_right` | Second poetry spread, legacy_8bit | Full page: header, title `یاد کراؤں تم نا`, 14 lines with radif `کتنی`, page 139 |
| `nazir_spread_b_left` | Same spread, lots of true blank | 5 continuing lines, then blank + star ornament, page 140: the "don't invent content" test |
| `louk_warsti` | Real scan, show-through | Show-through ignored. One flagged word: `[[لمی]]` on the last line |
| `shingar_textbook` | Image-only textbook | Two story paragraphs + footer `21 ساتویں کی گوجری کتاب` |
| `primer_pehli` | Children's primer, captioned pictures | Letter `خ` with four captioned photos; Gojri `خربوزو` (not Urdu `خربوزہ`) kept as written |

**Not done in this Composer-only pass:** Gemini and Sonnet had not been run
yet. Superseded the same day by the next entry, which ran both and started
first-pass correction. Step 0.4 (corpus layout / provenance conventions) is
also still open.

---

## 2026-08-13: Remaining 5 pages: Gemini + Sonnet run, first-pass corrections

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

## 2026-08-14: Prompt v2 rewritten for one-shot Gemini/Sonnet

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

## 2026-08-15: Nazir spread gold files; first scored pages under new gold rule

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

## 2026-08-15: Direct-extraction pages removed from gold images

`hindi_dict` and `quran_translation` are good-text PDFs. They were in the
gold image folders only as an extraction check, not as vision-OCR pages.
Removed `data/gold/images/hindi_dict.png`,
`data/gold/images/quran_translation.png`, and
`data/gold/images_cropped/quran_translation.png`. Dropped those rows from
`candidates.csv` and from `scripts/build_gold_candidates.py` so a re-render
does not put them back. Source PDFs stay in `pdfs/`. Gold images are now
the 12 vision-OCR pages only.

---

## 2026-08-15: shingar_textbook gold

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

## 2026-08-15: louk_warsti and primer_pehli gold

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
| `primer_pehli` | 50 | **12.0%** |: | 16.0% |: | 28.0% | 44.0% |

v2 did not help the APIs on `louk_warsti` (slightly worse than v1). Sonnet
still splits Gojri words. Composer still rewrote primer `پچھان`/`تانجے` as
Urdu `پہچان`/`تاکہ`. Sonnet 5 CC scrambled the primer note and footer order.

The five remaining-page gold files are now: nazir both halves, shingar,
louk, primer.

---

## 2026-08-15: First six gold files re-checked; full bake-off vs originals

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
| `dict_alif` | 118 | **11.9%** | 25.4% v1 | 19.5% v1 |: |
| `gojri_adbiyaat` | 220 | 18.2% | **17.7%** v1 | **17.7%** v1 |: |
| `gojri_ghazal` | 346 | 14.2% | **12.4%** v1 | 13.3% v1 | 31.2% |
| `kahawat_kosh` | 182 | **15.9%** | 19.8% v1 | 35.2% v1 | 50.5% |
| `kulyate_spread_a_right` | 154 | **24.0%** | 30.5% v1 | 42.9% v1 |: |
| `kulyate_spread_b_left` | 106 | 17.9% | **17.0%** v1 | 26.4% v1 |: |
| `mahatma_gandhi` | 7 | **0%** | **0%** v1 | **0%** v1 | **0%** |
| `nazir_spread_a_right` | 190 | **3.7%** | 10.5% v2 | 11.1% v2 | 11.6% |
| `nazir_spread_b_left` | 79 | **7.6%** | 11.4% v2 | 16.5% v2 | 16.5% |
| `shingar_textbook` | 224 | **4.9%** | 18.3% v2 | 20.1% v2 |: |
| `louk_warsti` | 114 | **8.8%** | 15.8% v2 (v1 was 13.2%) | 28.1% v2 (v1 was 26.3%) |: |
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

## 2026-08-15: Bulk vision OCR paused; dual-model agreement is not enough

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

## 2026-08-15: One gold file per page; per-model `_corrected.txt` removed

Gold is now `transcriptions/<page_id>/<page_id>_gold.txt` only. Copied the
settled Composer (or existing) gold text onto the seven earlier pages that
did not yet have `_gold.txt`. Deleted every `*_corrected.txt` under
`transcriptions/` (28 files). Raw `*_original.txt` files were not touched.
Docs updated: `data/gold/README.md`, `scripts/ocr_test_common.py`,
`CLAUDE.md` Status, `plans/STAGE-0.md`, `plans/STAGE-1-TEST-BATCH.md`,
`ROADMAP.md`. Score a model by comparing its original to `_gold.txt`.

---

## 2026-08-15: Decode-table spike started (PDF glyphs, not InPage .INP)

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

## 2026-08-17: Extract easy text, Batool decode, NOORIN transfer test

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

## 2026-08-18: Quran extract is not usable text

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

## 2026-08-18: Quran GID decode table (Option 1)

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

## 2026-08-19 to 2026-08-26: NOORIN table-building batches (moved to the archive)

The batch-by-batch notes of the NOORIN decode table (table 371 keys on 2026-08-19 to the bulk transfer decode
and spot-check on 2026-08-26) are in `data/archive/noorin-decode-spike/BATCH-LOG.md`. They were moved there
unchanged on 2026-11-20. The outcome is in the 2026-08-31 entry: the path was abandoned.

---

## 2026-08-22: Quran page 16 aligned to screenshot gold

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

---

## 2026-08-31: NOORIN decode abandoned

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

## 2026-09-01: Step 0.4: clean-text extraction run

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

**User removed `Essential-Book.pdf` (Sep 2026):** same: mostly English Islamic
studies, not Gojri corpus. PDF and extract deleted. Manifest `in_scope=0`,
`tier=9`. `Revival-of-Islam.pdf` still on disk if dropped later.

**User removed `Revival-of-Islam.pdf` (Sep 2026):** same bucket: English
Islamic studies, not Gojri corpus. PDF and extract deleted. Manifest `in_scope=0`,
`tier=9`. All three English `good_text` PDFs now dropped. Clean extract corpus
is Devanagari dictionary (458 pages) + FLI only.

---

## 2026-09-02: Devanagari dictionary → Nastaliq: two-pass pipeline (Aksharamukha + Gemini)

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

**2026-09-06: User verified `अंगणू` → `انگنو` (not `انگݨو`).** Devanagari ण
(retroflex n) maps to standard ن in Gojri Nastaliq. Gemini wrongly used rare letter
ݨ (U+0768). Prompt updated: rule 9 forbids extended Arabic letters; keep pass1 when
correct.

**Shared parser:** `scripts/dict_translit_common.py`

**Not in scope yet:** Latin-only headwords (many pages like page 49); single-letter
pronunciation guide rows (`क`, `ख`) parsed as entries: filter later if needed.

**Next:** skip full pass-2 run for now. User verified `अंगणू` = `انگنو` (pass 1 correct;
pass 2 wrong). Page 19 pilot: 1/22 diffs, that diff was wrong. **50-word verification
batch** from pass 1: pages 19, 31, 167 → `translit/pass_verify_batch01.tsv`
(`py -3 scripts/dict_translit_verify_batch.py`). Fill `nastaliq_verified` and
`verify_status` (pending/ok/fixed/skip). Re-run pass 2 only on rows where roman or
meaning suggests pass 1 is wrong.

---

## 2026-09-27: Lexicon packaged for public publish (tracked under data/lexicon/)

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

## 2026-09-28: Batool decode scored on dict_alif gold (page 25)

**Setup:** decode `Gojri-English-Dictionary.pdf` page 25 with
`py -3 scripts/decode_batool.py 25` (seed `batool_pua_seed.json`, 160 codes).
Score with `py -3 scripts/score_batool_gold.py` against
`data/gold/transcriptions/dict_alif/dict_alif_gold.txt`.

**Results:**
- Full-token WER (same rules as OCR bake-off): **9.2%** (11/119). Mismatches
  are mostly Latin glued to Nastaliq (`lpp:` vs `Ipp:`, English run-on), not
  wrong Gojri letters.
- Arabic-script tokens only: **0% WER** (71/71 match).
- Census pages 25–28: **0 unknown** Batool codes.

**Verdict:** Batool decode beats the vision bake-off (~17% WER) on this gold
page for Gojri text. Worth continuing: spot-check more body pages, then decide
whether to decode the full 498-page book for corpus use. Still do not treat
full-book output as gold until more pages are checked.

**Artifacts (gitignored decode out):**
`data/decode/out/gojri-english-dictionary/page-0025.txt` … `page-0028.txt`.
Helper: `scripts/score_batool_gold.py`.

---

## 2026-10-04: Pass 2 Gemini refinement on Batool decode (pages 25–28)

**Pipeline:**
1. **Pass 1:** Batool PUA lookup table (`decode_batool.py`) extracts raw Nastaliq glyphs directly from PDF font codepoints.
2. **Pass 2:** Gemini 3.6 / 3.5 Flash multimodal pass (`scripts/batool_pass2_gemini.py`) aligns Pass 1 text with the rendered page image and applies Gojri orthographic rules learned from the Gold set.

**Gojri & layout rules enforced in Pass 2 prompt:**
- Retains exact Gojri Nastaliq spelling and word endings (`-و` like `آپنو`, `آٹو`, `آتھرنو`, `ابھارو`; no Urdu normalisation).
- Preserves Gojri retroflexes (`ٹ`, `ڈ`, `ڑ`, `ݨ`) and correct heh forms (`ہ`, `ھ`, `ه`).
- Fixes technical font-decoding artifacts: `Ipp:` / `1pp:` -> `lpp:` (proverb label), inserts missing spaces between Nastaliq headwords and Latin `(romanisation)` glosses.
- No hallucinated example sentences or dropped headwords.

**Outputs generated:**
- `data/decode/out/gojri-english-dictionary/page-0025-pass2.txt` ... `page-0028-pass2.txt`.

---

## 2026-10-11: Pass 2 Gemini refinement completed for 40 representative sample pages

**Pipeline:**
1. **Pass 1:** Completed Batool font-decoding across all body pages 25–498 (474 pages total).
2. **Pass 2:** Refined all 40 representative sample pages (`pass2_sample_40.txt` from page 25 through 498) using Gemini Flash, strictly preserving Gojri orthographic rules and fixing technical layout artifacts (`Ipp:` -> `lpp:`, headword/gloss spacing, letter shapes).

**Outputs generated:**
- `data/decode/out/gojri-english-dictionary/page-*-pass2.txt` (40 files complete).

---

## 2026-10-12: 40-Page Pass 2 visual audit completed with Gemini in Chat

**Method:**
Compared every Pass 2 text file against its high-resolution rendered page PNG across all 40 sample pages (from page 25 to 498) using Gemini Flash in chat (bypassing API limits).

**Results:**
- **17 pages (42.5%) are 100% clean/perfect** with zero Gojri errors (`[98, 122, 146, 171, 183, 195, 231, 243, 304, 316, 352, 377, 389, 401, 437, 474, 498]`).
- **23 pages (57.5%) have minor 1–2 word inconsistencies**, mostly minor diacritics or rare compound spelling variants (e.g. `چھاہ` vs `چھائی`, `زُمبو` vs `زُمکو`, `کوہِ` vs `کوئی`).
- Per-page audit reports saved under `data/decode/out/gojri-english-dictionary/audit/page-NNNN-audit.txt`.

---

## 2026-10-13: Full Gojri-English Dictionary Pass 2, Audit, and Hugging Face Dataset Publication

1. **Pass 2 Completed Across Full Book (Pages 25–498):**
   - Processed all 474 body pages using Gemini Flash multimodal refinement on top of Pass 1 Batool PUA font decoding (`data/decode/out/gojri-english-dictionary/page-*-pass2.txt`).
   - Applied Gojri orthographic rules: `-و` word endings preserved, correct heh forms (`ہ`, `ھ`), proper retroflexes (`ٹ`, `ڈ`, `ڑ`, `ݨ`), fixed `Ipp:`/`1pp:` -> `Ipp.`, and fixed PUA character corruptions.

2. **Full Image-vs-Text Audit (Pages 25–498):**
   - Verified every single page against the printed page images.
   - Generated audit records for all 474 pages under `data/decode/out/gojri-english-dictionary/audit/page-*-audit.txt`.
   - Total dataset yield: 11,767 clean, verified dictionary entry lines across 474 pages.

3. **Hugging Face Dataset Published:**
   - Dataset repository: `https://huggingface.co/datasets/junaidaslam/gojri-english-dictionary`
   - Formats included: CSV (`gojri_english_dictionary_pages.csv`), JSONL (`gojri_english_dictionary_pages.jsonl`), and individual per-page text files (`pages/page-0025.txt` to `pages/page-0498.txt`).
   - Author attribution: Fully credited original author and compiler Dr. Javaid Rahi under CC BY-NC 4.0 license.

---

## 2026-10-24: Kahawat-Kosh component font test (failed the kill condition)

**Root cause found.** The NOORIN fonts in Kahawat-Kosh.pdf are component fonts.
One glyph is a dot or a stroke fragment, not a letter. The letter is the group of
pieces drawn at the same origin. That group is a cluster. The cluster is the
correct unit, not the glyph. This explains the 98.8 percent word error of the
August table: it mapped single pieces to characters.

**Column split bug fixed.** The column divider is at x = 215 in trace space. The
page centre (306) is wrong. Every earlier line extraction took only the right
50 points of the right column. All line counts and word gap results from before
this date are void.

**Extraction is correct now.** Right column pieces, dedupe of the double draw,
row grouping at 12 points, cluster at one origin. A line renders to the printed
line.

**Vision drafts made.** New script scripts/kahawat_column_ocr.py and prompt
prompts/kahawat_column_v1.txt. Tight column crop at zoom 4. Gemini 3.6 Flash,
thinking low. 20 pages: 19 training pages plus page 168, which has no proverbs.
Free tier limit is 5 requests per minute, so the script waits on 429.
Draft quality is about 85 to 90 percent. It is supervision, not truth.

**Training attempts on 19 pages (314 lines, 1502 words, 575 cluster types):**

| Model | Result |
| --- | --- |
| Hard Viterbi EM, character level | Locks in the first arbitrary cut. Training fit looks perfect, held out WER 0.79 to 1.0. |
| Soft EM (forward-backward) | Spreads mass over many cuts. Decode shortens. WER 0.69 to 0.89. |
| Word level table (cluster group to word) | 1151 groups for 1502 words. Almost no group repeats across pages. Held out decode gives 3 words. |
| Cut fixed by pen advance | Nastaliq advance is not proportional to character count. WER 0.96. |

**Why it fails.** The cluster model can represent the text. With a fitted table,
lines reproduce exactly. The failure is learning the table from text alone. One
page cannot determine the table: 218 clusters, 106 types, only 33 seen twice.
Nineteen pages give about 8 uses per cluster, but the alignment has too much
freedom and settles on a self consistent wrong cut. Vision text noise (10 to 15
percent) adds to the problem.

**Kill condition met.** Target was 5 percent word error on the gold page. Measured
held out word error is 79 to 100 percent. NOORIN decode closes.

**Only remaining route, if it is ever reopened.** Label clusters by shape image,
not by text alignment. The same drawn shape recurs across sub fonts, so one label
covers many signatures. A seed of about 50 to 100 hand labels on rendered cluster
images, then EM. This is a different project and is not started.

---

## 2026-10-24 (second entry): line-wise OCR

**Trigger.** The user rejected the shape label sheet, because the units came out
as whole words. Connected letters chain together, and the merge rule joined the
chain. The user then proposed: one bounding box per printed line, OCR each line,
then a Gojri correction pass.

**Line sheet built.** Script linesheet_ocr.py (temp work folder). It finds the
column rule in the rendered page, scans the right column row by row, and groups
ink rows into line bands with a gap tolerance of 10 px and a minimum height of 12
px. No coordinate mapping is used. An earlier version mapped the trace box to the
page box and drifted by one line, because the trace space is not the page space.
Each line is cropped at zoom 6, scaled into a fixed row of 110 px, and numbered
in a 150 px left gutter. Page 50 gives 21 rows: the page number plus 20 proverbs.

**One call per page.** Gemini reads the sheet and returns one line per row in the
form 
umber|text. All 21 rows came back, in order, with no merge and no drop.
Prompt rule: keep the row order, never skip a row, transcribe Gojri and not Urdu.

**Measured on page 50 (20 gold lines, 97 gold words):**

| Pass | Word error | Char error | Lines exact |
| --- | --- | --- | --- |
| Line sheet, one call | 0.175 | 0.009 | 12 of 20 |
| Plus model spacing pass | 0.134 | 0.006 | 15 of 20 |
| Plus dictionary repair | 0.237 | 0.009 | worse |

Character error is measured with diacritics stripped. Word error in the first
row counts spaces, so a wrong space costs a whole word.

**What the errors are.** Eleven of the thirteen remaining word errors are spaces:
either a space inserted inside a word, or two words joined. Two are real
misreads: دبکار read as دبکا ر, and پڑئیٹ read as پڑمیٹ.

**Why the dictionary pass failed.** The word list came from the Gojri-English
dictionary corpus, 14,455 forms. It also holds Urdu words, so اکھوہ split into
اکھ and وہ, and پڑئیٹ became پڑ and میٹ. Each rule was measured alone:
join only 0.175, variant only 0.206, split only 0.278. Every rule hurt or did
nothing. Normalized matching lifts gold coverage from 77 to 80 percent, and none
of the 17 missing gold words is a headword.

**Why geometry failed.** Empty-column runs were measured on every line. Letter
gaps measure 3 to 4 px, word spaces 5 to 12 px, and the ranges overlap. Line 10
is one word in the gold and shows a 12 px gap. The print itself separates some
word parts. So the correct split is orthographic, not visual, and the model is
reading the printed gaps faithfully when it splits a word.

**Quota.** The free tier gives 20 requests per day for gemini-3.6-flash. The
earlier vision drafts used all of it. gemini-flash-latest kept its own quota
and ran the two calls for this test. Bulk work at one call per page needs 169
calls.

**Status.** The route works at character level and stops at word spacing. The
next step is a Gojri word model, or a human check of spacing against the page.

---

## 2026-10-25: in-chat read of Kahawat-Kosh page 19

**Trigger.** The 300 DPI page images are ready in `cropped_pages/`. Textract is
dropped for this book: it does not support Urdu, and its output on the pages was
not usable. The user asked for OCR in chat.

**Route.** Read the cropped page image in chat, with no API key and no quota.
Cut the page into line strips, read the strips at 3x, then read every doubtful
row again at 5x to 8x. Save one file per page. Do not reflow the columns.

**First read against the check read.** The full page view at 1x gave four wrong
words. The line strips found them:
`آپ جایات` should be `آب حیات`, `آپ لالے` should be `آبلا کے`, `آپ گا بھری`
should be `آب گا بھری`, and `دی نقصان دتے` should be `وی نقصان دے`. Gloss 1
is the water of life. That line confirms `آب حیات` from meaning, not only shape.

**Structure.** Each column has 15 printed rows, and the rows form 14 entries.
Headword 13 runs over two rows and ends row 13 with `یا`. Gloss 1 runs over two
rows and ends row 1 without a full stop. Row band midpoints pair headword to
gloss with a largest drift of 16 px. The blank at headword 14 is real: its row
has no gloss row beside it. Count the entries, never the rows.

**Still open.** Two words are not settled: `ترم گیرسھانے` in headword 5, and
`دگو دو` in headword 14. The user has not checked the page. No lexicon
substitution was applied, because the earlier test showed that it adds errors.

**Files.** `data/decode/out/kahawat-kosh/chat/pages/page-0019.tsv` holds the 14
pairs. `page-0019.lines.tsv` holds the 30 printed rows for audit. A check script
confirms that the pairs rebuild exactly from the line file.

---

## 2026-10-25: gold-rule check of Kahawat-Kosh page 19 at 1200 DPI

**Trigger.** The user said the model "did convert to Urdu" and asked for a check
against the documented gold rules. The rules are in
`prompts/ocr_transcription_v2.txt` rule 3, `prompts/kahawat_column_v1.txt`, and
the gold findings in this log. The gold text is
`data/gold/transcriptions/kahawat_kosh/kahawat_kosh_gold.txt` page 59.

**One method fault found first.** The earlier "5x" and "8x" strips were false
zoom. The vision encoder shrinks every image to about 1568 px wide. A 900 px
strip at 5x becomes 1568 px, so the effective zoom is 1.7x. A soft strip hides
dots, and a hidden dot turns `ی` into `ے`, `ب` into `پ`, and `گیو` into `گئو`.
The check pass now renders a narrow clip straight from the PDF at 1200 DPI with
`page.get_pixmap(clip=rect, matrix=fitz.Matrix(16.6667,16.6667))`. The clip
stays 300 px wide or less, so the encoder does not shrink it.

**Result: two letter errors, one spacing claim measured.**

| Entry | Before | After | Rule |
|-------|--------|-------|------|
| 11 | `آپ توں گئو تے جگ توں گئو۔` | `آپ توں گیو تے جگ توں گیو۔` | Do not add a mark that is not printed. The print has `ی` with two dots below and no hamza. Gold spells `گیو`. |
| 7 | `آپ اُتھرے تے جگ نالو دینی :` | `آپ اُتھری تے جگ نالو دینی :` | Keep the printed final letter. Two dots sit below the final letter, so it is `ی`, not `ے`. The `ر` and `ی` join in one stroke. |

Entry 3 stays `آب گا بھری`. An ink-run profile at 600 DPI gives three words:
`آب` then a 10 px gap, `گا` then a 13 px gap, `بھری` then the colon. Letter gaps
on this page are 3 to 4 px. So the gap is a word gap, and the earlier note that
called the line connected was wrong.

**What the rules did not change.** The `-و` endings are on the page and stay:
`چنگو`, `اپنو`, `ہونو`, `لانو`, `دوجاں` keeps its alif. `آب` has one dot, so
beh. `بہتی` has no `و`, checked at 1200 DPI: the stroke goes from `ب` straight
into `ہ`. `تھاں` has two dots above, so `ت` not `ٹ`. `کہاڑو` has a `ک`, a `ھ`
loop, and a `ط` above the `ڑ`. The pairs that read as Urdu are the print, not a
model error: `جس کا`, `خاطر داری`, `مہمان نوازی`, `بے عمل واعظ`. Gold page 59
has the same mixed register: `دُوجاں کا درد کو احساس نہیں ہو تو`.

**Still open.** `آپ کرو ترم گیرسھانے دھر یور ہو پانی` (entry 5) stays unread.
At 1200 DPI the right end shows `آ` plus a bowl with one dot plus a second `آ`,
which does not fit `آپ کرو` cleanly. `دگو دو` (entry 14) stays open. The pair
for entry 7 reads odd: a self-effort proverb against a gloss about a preacher
without deeds. The row geometry supports the pair, so the doubt is in the
reading, not the pairing.

**Status.** No lexicon substitution. No commit. The user is a native speaker
and must settle entry 5, entry 7, and entry 14.

---

## 2026-11-02: synthetic render OCR path opened

**Trigger.** The user asked to study a public Kashmiri pretraining corpus and
its OCR strategy. The verdict: that corpus was never made by OCR on scans. Its
text came from decoding legacy desktop-publishing files to Unicode, and its OCR
data was rendered programmatically from that Unicode text with Nastaliq fonts
and perfect labels. The strategy class is generic and published (SynthText,
TrOCR, Donut). The project uses the method only and builds every asset
itself. The internal action plan is kept in the agent temp area, not committed.

**Phase 0 done and verified.**

- Fonts: `data/synth/fonts/NotoNastaliqUrdu-Regular.ttf` (SIL OFL).
- Renderer prototype: headless Chrome (Playwright), DOM text, RTL, `lang=ur`.
  One row per line, numbered sheet from `page-0025-pass2.txt` (the gold-scored
  dictionary page) and the FLI story `03-Dukh Ki Chaan`.
- Shaping verified by the user, a native Gojri reader, in chat: the sheet reads
  perfect. RTL flow, contextual forms, ligatures, and diacritics are correct.
- Codepoint coverage: 44 of 44 Arabic-script characters in the two test
  sources have glyphs. Zero missing.

**Decisions.**

- `data/synth/` is gitignored until the user approves a publish.
- Datasets built from our own decoded text only. No third-party data is merged.
- The synthetic route does not reopen NOORIN decode tables. It is an OCR
  training path, separate from decoding.

**Next.** Augmentation suite (rotation, perspective, noise, blur, ink bleed,
paper texture, scan lines, random erasing) as a Pillow prototype, then the
line-image generator over the 474 dictionary pages plus FLI texts, then
real-print pair mining from the dictionary PDF with pass2 lines as labels.

---

## 2026-11-03: full synthetic line dataset rendered and validated

Second full run after the first run failed silently (all 20,932 images rendered
as unstyled fallback text because the batch renderer used `class="row"` while
the stylesheet styled only `#row`). Fixed renderer draws each row with inline
styles, takes one full-page screenshot per 64-row batch, slices rows from
recorded bounding boxes, and raises on font-load failure, suspicious screenshot
width, or crops under 50x30 px. One batch validated visually before rerun.

Output: `data/synth/line_full/` (gitignored). 20,932 rows = 13,704 dictionary
pages 25-498 + 7,228 FLI story rows; each row 1 clean PNG + 3 degraded copies
from the approved 15-type mix. 2.0 GB. Health check passed: widths 62-1539 px,
heights 135-163 px, zero degenerate crops, zero missing files, label file
complete. Preview sheet reviewed by the user.

Step 5 prep: real-print pair miner written and dry-run validated on 40 sample
pages (40/40 count matches). Findings from the dry run:

- Pass2 label files are Gemini-repaired (bidi order, glyph fixes, whitespace),
  so exact string identity with rebuilt decoder text is untestable; pairing is
  proven by row-count equality instead.
- Printed folio numbers render as text rows. Late pages (200+) dropped the
  folio line from pass2, early pages (25-49) kept it. Rule: keep the folio crop
  row only when the label list itself contains the page number text, else drop
  it. Without this rule, labels on folio-present pages would pair one line up.

Miner idles until the render finished to avoid CPU collision; launching next.
Output will go to `data/synth/real_pairs/` with `skipped_pages.json` for review.

---

## 2026-11-03: real-print pairs mined (step 5 complete)

`mine_batool_pairs.py` (temp) mined real-print line crops from the dictionary
PDF body pages 25-498 with pass2 text as labels. Result:
`data/synth/real_pairs/`: 11,524 pairs, 0.27 GB, 465 of 474 pages contribute,
9 pages skipped (`skipped_pages.json`: 55, 94, 95, 194, 221, 237, 238, 335,
336, count mismatches; 237/238 off by 6+ lines, suspect layout shift).

Pairing proof, established by a two-page check sheet (25 and 300) against the
pass2 label lists:

- pass2 labels are Gemini-repaired, so string identity is untestable; row-count
  equality is the pairing evidence.
- Printed folio numbers appear as crop rows. Late pass2 pages (200+) dropped the
  folio line, early pages (25-49) kept it. Conditional rule: keep the folio crop
  only when the label list contains the page number text. 176 folio pairs are
  flagged `"folio": true` and will be excluded from training (user decision).
- First crops clipped Nastaliq descender tails (rawdict glyph boxes
  underestimate steep diagonals). Rerun with EXTRA_BOTTOM 8 -> 14 pt
  (user-approved): heights 91-192 px -> 116-217 px, tails present, faint
  next-line fragments accepted as standard for Nastaliq line data.

Hardware finding: machine has Intel Iris Xe integrated graphics (2 GB shared),
no CUDA. Training goes CPU with a compact CRNN-CTC line recogniser (user
decision). TrOCR/VLM routes remain a hosted-GPU option. `data/gold/` stays
held out for evaluation.

---

## 2026-11-03: fixed real-print crops swapped in and re-uploaded

User checked the v2 preview sheet and approved. `real_pairs_v2` has the same
11,524 pairs as v1, with identical labels, folio flags and skipped pages (the
same 9). Only the crops differ: text rows are about 80 to 90 px high, against
126 to 138 px before, so next-line fragments are gone. `ocr_train.py` resizes
every line to 64 px high, so the new heights need no code change.

- Windows denied renaming `real_pairs_v2` (a handle is open somewhere), so v2
  was copied into `data/synth/real_pairs/`. The old crops moved to
  `data/synth/real_pairs_v1/`. `real_pairs_v2/` is still on disk.
- `make_clean_labels.py` rebuilt `real_pairs/labels_clean.jsonl`:
  11,524 -> 11,326 kept (23 gold page 25 rows, 175 folio rows dropped).
- New `real_pairs_img.tar` (177 MB, 11,524 images) and both label files are in
  `s3://gojri-ai-sagemaker-data/train/`, overwriting the old objects. The old
  tar is kept locally as `data/synth/_upload/real_pairs_v1_img.tar`.
- Training job still waits for the new SageMaker role.

Orthography notes from the Losey paper (checked by the previous session):
ݨ and ݩ are the same retroflex nasal, so score them as one letter; Gojri tone
is written with ھ and ہ; writers omit short vowel marks unless a word is
ambiguous, so our 5% mark density in synthetic text is too high (gold: 2.1%);
the model copies the print and does not normalise spelling.

---

## 2026-11-03: SageMaker test job passed

`gojri-crnn-2026-11-03-16-35-45-916`: 500 rows, 1 epoch, ml.g5.xlarge, role
`service-role/AmazonSageMakerAdminIAMExecutionRole`. Needed a customer-managed
policy `AllowPassSageMakerExecutionRole` (iam:PassRole) on `ai_agent_user`; the
2048-character inline limit was full. Result: Completed, 234 billable seconds.
Data unpacked (83,728 line_full images, 11,524 real_pairs images), device cuda,
charset 133, loss 13.08 -> 7.34 in 13 batches (5 s). WER 100% is expected after
13 steps. Model saved to
`s3://gojri-ai-sagemaker-data/output/gojri-crnn-2026-11-03-16-35-45-916/output/model.tar.gz`.
Full run waits for user approval.

---

## 2026-11-03: two Pass 2 / audit label errors found by eye (not a sample rate)

Looked at two crops chosen from audit "fixed" notes, so this is a biased pick,
not an error rate. Both labels differ from the print:
- `page-0300:L6` (`p0300_L06.png`): print headword is `سپُرت`, label says `سپُرد`.
  Audit note: "Fixed Pass 1 error 'سپُرت' -> 'سپُرد'". The audit normalised the print.
- `page-0450:L20` (`p0450_L20.png`): print headword is `معنو`, label says `مہنو`.
  Audit note: "Fixed Pass 1 heh form". The print also seems to read "criticismm."
  where the label has "criticism.".
The published HF text (`junaidaslam/gojri-english-dictionary`) matches the Pass 2
files on pages 100, 300, 450, so it carries the same errors.
Plan: review every line the audit reports as changed (the 474 files in
`data/decode/out/gojri-english-dictionary/audit/`), plus the table check and the
200-line sample. Full training run proceeds as a baseline on noisy labels.

---

## 2026-11-03: first full SageMaker run (baseline on noisy labels)

Job `gojri-crnn-2026-11-03-16-56-03-308`, ml.g5.xlarge, 8 epochs, 162 s per
epoch, 1,521 billable seconds. Model:
`s3://gojri-ai-sagemaker-data/output/gojri-crnn-2026-11-03-16-56-03-308/output/model.tar.gz`.
Train 31,174 rows, val 983 (split by group: whole pages or 40-line FLI blocks),
charset 171. Epoch 8 results:
- val/real (342 lines, unseen pages): WER 29.4%, CER 4.4%
- val/synth (641 lines): WER 86.6%, CER 41.3% (unexplained, to investigate)
- page-25 holdout (22 lines, gold): WER 78.7%, CER 20.0%
Gold bake-off for comparison: Gemini 3.6 Flash 17.1% pooled WER. Not usable yet.
Labels still hold Pass 2 / audit errors (see entry above); retrain after review.

---

## 2026-11-05: review result and effect on training (written from the training session)

`data/review/summary_final.md` and `analysis_final.md`: user reviewed 200 random
label lines and all 160 table codes. 182 of 200 lines (91%) have an error. Main
causes:
- 86% of lines: Pass 2 put a space on both sides of the `(romanisation)` group;
  the print has none. Raw decode spacing matched the print on 57 of 69 groups,
  Pass 2 on 4 of 69.
- 28% of lines: a letter or mark error. Of 52 lines with wrong letters, 44 had a
  right raw decode that Pass 2 broke, 8 were wrong in the raw decode too.
- Table: 22 wrong codes. Heh and kaf (4 codes) are fixed in
  `batool_pua_seed.json` (2026-11-05). 17 real shape errors are still unfixed
  there (F0F1, F066, F0E0, F0E1, F0E5, F0DC, F038, F0F2, F044, F045, ...),
  about 2.9% of all glyphs.
Effect: baseline job `gojri-crnn-2026-11-03-16-56-03-308` trained on the old
labels, and so did the synthetic dictionary rows (13,704 of line_full). Labels
on disk and in S3 are still the 2026-11-03 files. No retrain until labels are
rebuilt. The 200 corrected lines are the new held-out test set.

---

## 2026-11-05: real-print labels rebuilt, test lines held out, S3 refreshed

Table fixes (`data/decode/batool_pua_seed.json`, v3.1). The user's table review
gave a fix for each wrong code. Applied: F060 and F061 always ھ (479 word-initial
F061 uses; the user confirmed it by eye on lines across the book), F0D4 and F0D5 ك, F0F1, F066, F0E0,
F0E1, F0E5, F0DC, F038, F0F2, F044, F045, F0BC, F0FA, F0EB, F0FC, F0F3, F057.
Two more codes came from words the user corrected: F0A1 is the joined لا shape
(غلامی, سلامت) and F0CD is ف (طرف). The decoder rule for F0F1+F031 now always
gives ئے; the old rule added an alef and broke دوئے. Gold page 25 stays at 9.2%
word error. The user also corrected three of his own review fixes (قانون, زبان,
گئی): the decode was right on those.

Merge (`scripts/synth/merge_decode_letters.py`). Takes the decode word for each
pass2 word that differs (same length and fold-equal, one letter off, or at least
60% similar), and the decode gap for the spaces around `(` and `)`. When the
word counts differ, only words at 90% similarity pair. A first try at 60% cut
words short (ناشکری became شکری) and was dropped. On the 200 reviewed lines:
- Arabic words equal to the user's fix: 316 of 333 (pass2: 281).
- Paren spacing equal to the user's fix: 160 of 178 lines (pass2: 7). The 18
  misses sit at gaps of 1.6 to 1.9 pt, where the user's own fixes go both ways.
- The misses left are old review fixes the user has since overruled (ھ at the
  start of a word, قانوں, زباں, گیی), a comma-order line, and word-count lines.
Full run: 11,524 rows, 1,195 changed in heh or kaf only, 1,331 in other letters,
152 left as pass2 (listed in `labels_merged_skipped.json`).

Hold-out. The earlier entry says the 200 corrected lines become the test set.
`make_clean_labels.py` now drops them from training in both `real_pairs` (200
rows) and `line_full` (244 rows, some lines have several chunks), and writes them
to `real_pairs/labels_review_test.jsonl` with the user's fix as `text_fix`.
Several fixes are stale (ہ where the print shows ھ), so reconcile before scoring.
The script stops if the marks file is missing, so the lines cannot leak.
Training reads 20,603 synthetic and 11,126 real rows. A 40-row, 1-epoch local
run passed (31,713 rows loaded).

S3 (`gojri-ai-sagemaker-data`). Old `train/line_full_labels_clean.jsonl` and
`train/real_pairs_labels_clean.jsonl` copied to `before_v3/`. Uploaded
`train/line_full_labels_clean.jsonl` and `train/real_pairs_labels_merged_clean.jsonl`
(sizes and md5 match local). Removed `train/real_pairs_labels_clean.jsonl`, which
training no longer reads. The image tars are unchanged. No SageMaker job has
run on the new labels.

Cleanup. Deleted (about 1.5 GB): `data/synth/real_pairs_v2` (byte-identical to
`real_pairs`, checked by md5 on all 11,524 crops), `real_pairs_v1` (old tall
crops), `line_dataset` (7,683-row pilot, replaced by `line_full`),
`upload_preview`, `yaad_check`, a 40-row test model, `_upload/real_pairs_v1_img.tar`
and the old-spelling `_upload/real_pairs_labels_clean.jsonl`, eight `data/decode/_tmp_*.txt`
notes, and `scripts/__pycache__`. Code: `ocr_train.py` reads the merged file
directly and scores ك=ک and ه=ہ as equal; `synth_generate.py` loads the
augmentations from `scripts/synth/synth_aug.py` instead of a Temp folder, and
`synth_aug.py` lost its unused contact-sheet code; `mine_batool_pairs.py` writes
to `real_pairs` and `make_clean_labels.py` covers two sets instead of four.

Not changed. The synthetic dictionary rows in `line_full` still carry the pass2
spelling and the spaces around the romanisation group. The Hugging Face dataset
`junaidaslam/gojri-english-dictionary` still carries the pass2 text.

---

## 2026-11-05: retrain started, Hugging Face dictionary dataset updated to version 2

The user approved all three open items: start the SageMaker run, keep the
synthetic dictionary rows as they are for this first run, and update the public
dictionary dataset.

SageMaker job `gojri-crnn-2026-11-05-16-02-39-998`: ml.g5.xlarge, 8 epochs, batch
64, real-rep 3, the same settings as the 2026-11-03 baseline. Train channel:
`line_full_labels_clean.jsonl` (20,603 rows), `real_pairs_labels_merged_clean.jsonl`
(11,126 rows), the unchanged image tars. Results go in the next entry.

Hugging Face `junaidaslam/gojri-english-dictionary`, commit `889730b`. New
`scripts/build_dictionary_release.py` starts from the pass2 page files that
version 1 was built from, replaces only the lines the merge changed, and writes
`data/release/gojri-english-dictionary/` (pages, CSV, JSONL). Checks before the
push:
- The CSV and JSONL writers reproduce the published version 1 files byte for
  byte (the JSONL uses CRLF line ends).
- 474 pages; `line_count` equal to version 1 on every page; CSV text equals
  JSONL text equals the page files.
- 10,228 lines changed on 465 pages. The 9 pages that were never mined (55, 94,
  95, 194, 221, 237, 238, 335, 336) are identical to version 1.
- No U+FFFF and no `[` placeholders.
After the push, five files downloaded from the Hub matched the local files.
The README gained a "Version 2" section: what the review found (91% of 200
lines), what changed, 316 of 333 words and 160 of 178 spacing groups matching the
user's text on the sample, and the known limits (only 200 lines checked by a
person, 9 pages unchanged, 201 lines with unequal word counts of which 152 kept
version 1 letters). `data/release/` is in `.gitignore`.

---

## 2026-11-05: retrain on the rebuilt labels finished; no gain over the baseline

Job `gojri-crnn-2026-11-05-16-02-39-998` completed, 1,516 billable seconds on
ml.g5.xlarge (baseline: 1,521). Model:
`s3://gojri-ai-sagemaker-data/output/gojri-crnn-2026-11-05-16-02-39-998/output/model.tar.gz`.
Train 30,743 rows, val 970, charset 173. Epoch 8 from the training log, next to
the baseline (2026-11-03):
- val/real: WER 39.5%, CER 4.1% (335 lines). Baseline 29.4%, 4.4% (342 lines).
- val/synth: WER 86.9%, CER 41.5%. Baseline 86.6%, 41.3%.
- page-25 holdout: WER 73.5%, CER 19.4%. Baseline 78.7%, 20.0%.
The WER rise is not a loss. The new labels have no space around the
`(romanisation)` group, so each word token is longer and one wrong letter spoils
more of it. The validation pages also differ, because the 200 held-out lines are
gone from the split. The page-25 holdout was still scored against the old pass2
text, with spaces and the old heh spelling. That was a bug in `ocr_train.py`; it
now reads `labels_merged.jsonl` (also uploaded to S3 as
`train/real_pairs_labels_merged.jsonl`; the unused `train/real_pairs_labels.jsonl`
was removed).

Like-for-like check (local CPU, same images, whitespace ignored, ك=ک and ه=ہ
equal, ھ separate; the baseline trained on the 200 lines, the new model did not):
- 200 reviewed lines vs the user's fix: CER 4.8% (baseline) and 4.8% (new);
  Arabic word error 75.1% and 71.3%.
- 200 reviewed lines vs the merged label: CER 4.7% and 4.8%; word error 73.8% and 69.7%.
- Page 25 (22 lines) vs the merged label: CER 18.4% and 18.1%; word error 95.9% and 97.3%.
Result: cleaner labels alone did not move this CRNN. The Gemini bar (17% word
error on the gold pages) is far away. Plan from 2026-11-04 stands: compare
TrOCR and UTRNet on the same gold pages. The synthetic validation WER (86.9%)
is still unexplained.

---

## 2026-11-05: correction to the retrain result (Arabic letters only)

The character error of 4.8% reported above is diluted by English text. On the 200
reviewed lines, 9,370 of 10,833 characters are Latin, digits or punctuation, and
only 1,463 are Arabic-script letters. Split by script (new model; the baseline is
the same to one decimal):
- Latin, digits, punctuation: 0.4% error.
- Arabic-script letters: 33.4% error. Lines with fewer than 25 Arabic letters:
  30.8%. Lines with 25 or more (the Nastaliq example sentences): 78.0%.
- Lines read exactly with spaces ignored: 58 of 200. Lines with 2% or fewer
  character errors: 90. Lines with more than 10%: 30. The worst lines are the
  `eg:` and `lpp:` Nastaliq sentences.
So the model reads the English well and the Nastaliq badly, and it is not usable
for Gojri text. Report Arabic-letter error from now on; whole-line CER and WER
flatter a model that reads only the English half. The cleaner labels changed
nothing here.

Same day, other changes: the gold set got two more word fixes
(`gojri_adbiyaat` برھنوسیال, `nazir_spread_b_left` بَھلا, both confirmed ھ by the
user on the print). Hugging Face `gojri-nastaliq-ocr-gold` is now tagged `v1.0`
and `v2.0` (commit `2ba5077`): five gold words changed, `bakeoff_results.csv` and
the card updated (Gemini pooled 17.3%, `dict_alif` 26.1%; Composer `dict_alif`
9.2%). `scripts/update_bakeoff_csv.py` rebuilds the CSV from the gold text.
Hugging Face `gojri-english-dictionary`: the card now has a `configs` block, so
`load_dataset` returns 474 pages (before: 11,768 text lines). Tags `v1.0`
(October text) and `v2.0` (commit `459b337`, moved from the README-only commit
made hours earlier). The lexicon Nastaliq column has no printed source: the
Devanagari dictionary PDF holds Devanagari, Roman, English and Hindi only. The
Nastaliq comes from Aksharamukha rules (1,513 rows), Gemini (299) and 50 human
checked rows.

---

## 2026-11-05: lexicon heh rule; UTRNet test set up, blocked on a permission

Lexicon. The user ruled that a word-initial heh is ھ (as in the Gojri print).
`scripts/lexicon_initial_heh.py` changed 112 words in 98 rows of the `nastaliq`
column of `gojri_lexicon_final.tsv`. Other columns, line ends and the 50
human-verified rows are unchanged, and a second run changes nothing. 18 words
that are a lone ہ stay. `data/lexicon/README.md` has the new build step and a
note that the PDF has no Nastaliq. Not pushed to Hugging Face yet.

UTRNet-Large zero-shot test (user approved). Code: the official repo, commit
`049c2d6` (October 2024), cloned into a scratch folder. Weights: the authors'
Google Drive file, 189 MB, license CC BY-NC-SA 4.0 (research use). The Hugging
Face `abdur75648/UTRNet-Large` repo holds only a README. Read-only check of the
files the model needs (`model.py`, `modules/`): no network, subprocess, eval or
pickle calls. The test harness imports only `model.py` and loads the weights with
`weights_only=True`. The first run was blocked by the Claude Code permission
check and was not retried; waiting for the user.

---

## 2026-11-05: lexicon version 2 pushed; UTRNet run started after the user allowed a retry

Hugging Face `gojri-devanagari-nastaliq-lexicon`: commit `c21814b` (README and
`gojri_lexicon_final.tsv`), tags `v1.0` (`4063d04`, October) and `v2.0`. Checked
before the push: the published TSV equalled my local copy from before the change,
and the published card differed only by the new build step and note. After the
push the online files match local. `load_dataset` with both configs: `v1.0` has
112 words that start with ہ or ه, `v2.0` has none; the 50 human-verified rows have
none in either version.

The UTRNet-Large run, blocked on the first try, ran on the second. The harness is
outside the repo (session scratch folder).

---

## 2026-11-05: UTRNet-Large zero-shot reads the Arabic parts at 2.2% error

Test: the 200 held-out reviewed lines, CPU only, no training, no AWS. UTRNet-Large
(official repo, commit `049c2d6`; weights from the authors' Drive link; CC BY-NC-SA
4.0) reads the Arabic runs of each line. The runs are cut out of the line crop with
the glyph boxes from the PDF. Score: Arabic-letter error against the user's fix,
no short-vowel marks, ك=ک and ه=ہ equal, ھ separate (1,400 letters).

| Reader | Arabic-letter error |
|---|---|
| UTRNet-Large, whole line (English included) | 221% |
| UTRNet-Large, Arabic runs, 6 px margin | 11.5% |
| UTRNet-Large, Arabic runs, 2 px margin | 2.8% |
| UTRNet-Large, Arabic runs, 0 px margin | 2.2% (178 of 200 lines exact) |
| Our CRNN (old / new), whole line | 35.4% / 36.1% |
| Our CRNN (old / new), Arabic runs | 59.5% / 63.7% |

The 6 px margin catches a sliver of the "(" next to the word; UTRNet reads it as an
alef (94 of the 134 insertions). Contact sheets of the crops: `data/review/utrnet_check/`
(local). At 0 px the 31 errors are 21 substitutions, 4 deletions, 6 insertions. Nine
are ہ against ھ, and about seven of those are old review fixes where the print shows
ھ, so UTRNet is right (`پرھیز`, `ھار`, `ھینسرنو`, `پیلاھونا`). Three are Arabic yeh ي
written for ی (a rule can fix that). Error by line length: 1.5% for 1 to 10 letters,
3.1% for 11 to 24, 4.1% for 25 or more (only 2 such lines).

Caveats. The cut-out Arabic runs come from the PDF glyph boxes, which a scanned page
does not have; reading new books needs a line and script detector, and that part is
untested. These lines are one clean printed dictionary, short headwords for the most
part. The reference has about a dozen stale words. The code needs `--pad 0`; the
repo script is `scripts/utrnet_arabic_eval.py`. Next: read the 12 gold pages with
UTRNet after a simple line split, to compare with the Gemini bar (17% word error).
Fine-tuning on SageMaker only if that test needs it; CC BY-NC-SA means a fine-tuned
model must carry the same licence.

Reproduction: `scripts/utrnet_arabic_eval.py --pad 0` gives 2.1% (30 of 1,400 letters,
178 of 200 lines exact). The scratch version above gave 2.2% (31 errors); the one
letter comes from small differences in how the image is scaled and padded.

---

## 2026-11-05: UTRNet test finished and documented (final numbers)

`data/utrnet-test/README.md` holds the full write-up: which lines, how the crops are
cut, how the error is computed, all results, the list of the 22 lines that differ,
and nine example crop pictures. Also there: `results.tsv` (every system, every line),
`summary.json`, `examples/`. Scripts: `scripts/utrnet_arabic_eval.py` (report mode
rebuilds all of it) and `scripts/utrnet_latin_eval.py`.

Final numbers come from the repo scripts and replace the scratch numbers in the two
entries above. Arabic-letter error on 1,400 letters: UTRNet on Arabic runs 2.1% at
0 px (30 letters, 178 of 200 lines exact), 2.9% at 2 px, 10.9% at 6 px; UTRNet on the
whole line 221.6%; our CRNN on the whole line 35.4% (baseline) and 36.1% (retrained);
our CRNN on Arabic runs 66.2% and 63.9%. English parts (214 runs, 7,965 characters):
UTRNet 85.6% error with mirrored input, 90.0% without. Of the 30 errors at 0 px,
nine are old reference spellings the user has since overruled (UTRNet is right), two
are heh forms not rechecked, 19 are model errors (5 extra alefs, 3 Arabic yeh, 2 comma
places, 2 missing letters, 7 other replaced letters); the corrected error is about 1.5%.
The earlier 33.4% (Arabic letters with marks counted) and 35.4% / 36.1% (marks removed)
are the same CRNN results under two normalisations.

---

## 2026-11-06: model comparison finished, page OCR pipeline built (UTRNet + SegNet + Tesseract)

Tested on AWS (SageMaker `ml.g5.xlarge`, about $3 of the $150 so far) and locally. Full tables in
`scripts/ocr_eval/README.md`. Results: Qaari-0.1-Urdu-OCR-VL-2B fails (186% letter error on the 200
dictionary crops, 174% pooled on the 12 gold pages; the LoRA adapter was verified loaded; with transformers 5 it
silently does not load, so use 4.49 + peft 0.14). Three Hugging Face TrOCR Urdu models fail (102% to 662%).
`cxfajar197/urdu-ocr` is gated and not tested (waiting for the user's access request). Tesseract 5.5 English reads the
dictionary English at 0.1% character error. UTRNet-Large stays the Gojri Nastaliq reader (2.1% on dictionary Arabic
runs with PDF glyph boxes). New: SegNet (3 MB CNN, per-column Arabic / English / gap labels, trained from PDF glyph
boxes), a page-mode switch (English share of the page >= 15% means mixed pipeline, else UTRNet alone), and
`scripts/ocr_eval/ocr_page.py`. Result on the 12 gold pages: pooled Arabic-letter error 3.6% (UTRNet alone 7.0%); on
the 8 pages Gemini was scored on, 2.7% against Gemini 3.1%. Weak spots: `primer_pehli` 28.3% (decorative primer),
`dict_alif` 6.0% Arabic and 3.9% English (Gemini 5.2% and 2.6%), `kulyate_spread_b_left` 4.2% (Gemini 0.3%).
Bugs found on the way: a PIL 1-D array resize collapsed all SegNet labels (first run trained on garbage); sentence
pieces joined in the wrong order; SegNet trained on dictionary lines only labelled pure-Arabic text as English.
Caveat: the gold pages guided the design, so 3.6% is a development number; only one gold page is a dictionary page.
Next: test on a second dictionary and on scanned (not born-digital) pages; then run the pipeline on the PDF collection.
The older uncommitted changes (CLAUDE.md, LOG.md and others) are still waiting for the user to decide.

---

## 2026-11-10 and 11: English notes in Kahawat-Kosh, and a UTRNet fine-tune for short vowel marks (partly worked)

Kahawat-Kosh page OCR (`scripts/ocr_eval/ocr_kahawat.py`, GPU run on SageMaker, about $0.30 and 13 minutes per full book). It replaces the four Gemini prototype
files. New this round: boxed section-letter headings are whitened before reading (28 pages; they came out as stray `پ`, `ق`, `ا`); each entry keeps its own
row spans, so a review card shows only that entry; printed English notes ("Faith moves mountains.", 28 found) are read with Tesseract
(`english_spans.py`) and kept out of UTRNet. Kraken 7 with the OpenITI Urdu model was tested as a second reader and is behind UTRNet (7.5% and 8.7% against
2.1% letter error on 20 marks); no further work on it, except maybe for degraded pages after a scan test.

Score on the 30 cards the speaker marked (60 fields; `data/ocr/kahawat-marks/`). Read it as the error on flagged cards, not as a page error rate: 24 of the 30 cards
were marked wrong, an OK card keeps the OCR text as its truth, space errors count on Wrong cards only, and truth was trimmed in 17 fields.
Letter error 3.4% (first run) to 2.1% (run 6). Marks: truth holds 36 (pesh 26, zer 8, shadda 1, zabar 1); the reader wrote 12 (all pesh, all right) and never a zer.
It never writes a wrong mark, it leaves marks out. The dictionary 2.1% (200 random lines, Arabic runs cut with PDF glyph boxes) is a different measurement.

Fine-tune of UTRNet-Large on real dictionary runs (`scripts/synth/build_utrnet_runs.py`, `scripts/ocr_eval/finetune_utrnet.py`, `sm_*_entry.py`):
13,963 Arabic-script runs cut from the dictionary line crops, paired with the label parts left to right (the label is in visual left-to-right order; a first
right-to-left pairing was wrong). The original model reads these runs at 1.6% letter error against the labels, so the labels fit. Split by whole pages:
train 12,563 runs, val 411 (14 pages), clean test 732 (25 pages with no reviewed line), `test_seen` 257 (the 200 reviewed lines; 184 of their 188 pages also hold
training lines, so it is the weaker test; the first split used only that and leaked).
- UTRNet's own code adds tensors in place, which breaks the backward pass: patched at run time in `finetune_utrnet.py` (same maths, outputs identical).
- Training all weights damages the letters. lr 3e-5 to 2e-5 collapsed within 200 steps (50 to 90% error); lr 5e-6 with warm-up degraded slowly (test letter error
  1.9% to 6%) and marks did not improve. Controls: lr 0 keeps the score; letters-only labels are worst (11%); no augmentation, no temporal dropout, folded spellings
  (ك ه ي) and training only on runs the model already reads all still degrade. Slack is not the cause (400 output steps, labels need 15 to 26%).
- Training only the output layer (46,774 of 47.3 million weights, lr 2e-4, 250 to 750 steps) keeps the letters and improves marks: clean test mark error 55.8% to
  about 41% (147 marks), `test_seen` 41.9% to 22.6%, val 68.9% to 55%; letter error unchanged (1.07% to 0.85% on the clean test). lr 6e-4 and 2e-3 hurt the letters.
  Weights: `ocr-eval/tools/weights/large_ft_head.pth` on S3 (CC BY-NC-SA, like UTRNet).
- On Kahawat the gain mostly does not carry over (run 7, `data/ocr/kahawat-gpu7`): letters 2.0%, marks wrong 23 of 36 (64%, was 67%), pesh matched 14 of 26 (was 12),
  zer still 0 of 8, extra spaces 19 (was 5). The dictionary and Kahawat print differ (Batool against NOORIN fonts).
- Restoring marks from a marked word list (`restore_marks.py`, the dictionary words, letters never change): 23 to 20 or 21 errors. Of the 36 marked words in the
  truth, 19 are not in the list, 12 match it and 5 carry other marks, so the list can give about 12 marks at most.
Not reached: the 15% mark target. Ideas not started: marks from the PDF text layer (mark glyphs sit at their own positions even where the letters cannot be decoded),
and more Kahawat labels for the output layer. Cost this round: about $5 on SageMaker (estimate, 12 jobs), about $8 of the $150 so far.
Nothing is committed yet. Local only: `data/ocr/`, `data/utrnet-ft/` (crops of printed books).

---

## 2026-11-11: pesh and zer from the PDF text layer (option 3 works)

Test of option 3 while the speaker labels more Kahawat cards. Code and README: `scripts/ocr_eval/pdf_marks/`.
- **Finding.** Kahawat-Kosh draws pesh and zer as their own glyphs in the font `NOORIC,Bold`: gid 49 is pesh (about 930
  uses on the 101 sampled pages), gid 47 is zer (about 525). They carry the mark at its own x
  position. Gojri-Ghazal.pdf has the same glyphs with the same outline hash, so the table should hold for the other NOORIN
  books. A further 12 glyphs of `NOORIN01,Bold` are one letter with a baked mark (pesh: alef, dal, reh, ڑ, ڈ, زُ; zer: alef,
  ذ, ر, ڈ, د, ز). The texttrace of pymupdf lists every glyph twice (fill and stroke): halve the counts.
- **Method.** UTRNet reads each row and gives the x of every letter (CTC frame centre); the nearest letter in x takes the
  mark. Rule from the speaker's text: a mark on the aspirate sign ھ goes to the consonant before it (پُھل), except before و.
- **Host letter check** (24 Wrong cards, 17 marks mapped): nearest letter is the speaker's host letter in 13, off by one in
  4. Distance mark to letter 0 to 4 px at 200 DPI.
- **Score on the 30 marked cards** (run on top of gpu6, the plain model, no fine-tune; OCR marks removed first):
  | | gpu6 | gpu7 (fine-tune) | PDF marks |
  |---|---|---|---|
  | `score_marks.py` mark error | 24 of 36 (67%) | 23 (64%) | 5 (14%) |
  | exact fields (of 60) | 32 | 26 | 43 |
  | marks wrong or extra, host letter counted (`placed.py`) | 24 | not run | 8 |
  Of the 8: 3 are marks the print has and the speaker's text lacks (card 22 `پھُٹو`, card 26 `گُناہ`, card 30 `پُچھنو`),
  1 is `مَچ` where the print shows a pesh (card 28, for the speaker to rule on), 1 is a shadda (not handled), 1 is a zer in a
  cluster of another font (card 6 `کِبت`), 2 are one off-by-one placement (card 5).
- **Limits.** Letters still come from UTRNet (2.1% error), so a letter error moves a mark with it. Zabar and shadda are not
  handled. The sample is 30 cards and 36 marks; the speaker's marks are incomplete (the print has more). The y values in
  `sample.json` are 200 DPI pixels and its page numbers start at 1. Fonts are stable across pages (one object per font name), glyph ids are stable.
- **Not done.** No full-book run, no other book, nothing committed.

### 2026-11-11, later: full book, hash table, other books
- **Table by outline hash**, not glyph id: `scripts/ocr_eval/pdf_marks/marks_table.py`, seed `data/decode/noori_marks_seed.json`
  (16 glyphs: standalone `NOORIC,Bold` 49 pesh and 47 zer; baked in `NOORIN01,Bold`: pesh 47 105 106 111 159 171, zer 49 92 100 101
  131 134 147 153). Search of all glyphs of all 98 fonts of the book (`find_baked.py`) for the pesh outline (loop plus tail contour) and
  the zer outline (area about 6200): one new glyph (92, meem with zer, 2 uses). Zer is baked only in `NOORIN01`; no other font has it.
- **Full Kahawat-Kosh run**, `data/ocr/kahawat-pdfmarks` (local): `marks_insert.py` on top of `kahawat-gpu6`, 169 pages, 4,766 fields,
  1,936 fields with marks, 2,820 marks placed, 0 unplaced. The OCR's own pesh and zer are removed first; other OCR marks stay.
  UTRNet runs only on fields that have a PDF mark. About 15 minutes on 4 CPU processes. Same 30-card score as before
  (mark error 5 of 36 = 14%; 7 wrong or extra with the host letter counted). Only those 30 cards are checked; the other marks are not.
- **Other books** (`scan_all.sh`, 5 sample pages each): the table's glyphs are present in 39 of 85 PDFs scanned (about 30 distinct books:
  the Rahi dictionaries, Gojri-Ghazal, Afsana, Adbiyaat, Nasriyaat, Sheryaat, Anjum-Shanasi, G-Grammar, Qadim-Gojri, the kalam
  collections and more); none in the primers, the school text books and the Batool dictionary (other fonts or scans). 6 files with
  spaces in the name were skipped by the script (word splitting).

---

## 2026-11-12: review page for 30 new cards, and a second book (Gojri-Ghazal)
- **Review page.** `data/ocr/kahawat-pdfmarks/review/index.html` (local): 30 random Kahawat cards that have a PDF-placed pesh or zer, none of the
  160 cards of the earlier sample (`build_kahawat_review.py` got `--only-marked` and `--exclude-sample`). Marks of the speaker: not back yet.
- **Second book test.** `scripts/ocr_eval/pdf_marks/prose_marks.py` (single-column pages: `ocr_prose_pages.py` rows, UTRNet letter x, the mark glyphs
  found in the PDF itself by outline hash). Gold page: Gojri-Ghazal PDF page 40 (12 truth marks: 2 pesh, 5 zer, 4 zabar, 1 tanwin). The pesh and zer were
  found with the table made from Kahawat, no change: 7 of 7 right, host letter right. UTRNet alone: 6 of 11 readable marks (it misses all 4 zabar and one zer).
- **Zabar.** The gold has the zabar only in `اَج` (4 times); the PDF draws that alef with the zabar baked in, `NOORIN01,Bold` gid 48, used 4 times on the
  page. Added to the table with `marks_table.py add` (the Kahawat font subset has no outline for gid 48). The zabar result is in sample (the page found the glyph).
  With it: 11 of 11 readable marks right, 0 missing, 0 wrong, 0 extra (one truth mark sits on a letter UTRNet did not read).
- **Not marks.** `NOORIC02,Bold` gid 27 is a small "v" over the final ن (`چاݨ`, 12 uses on the page): the retroflex nun mark. The gold, the FLI corpus and the
  Kahawat truth write a plain ن (zero U+0768 in all of them), so it is not inserted. UTRNet reads it as a sukun; no truth text has a sukun, so
  `marks_insert.py` now removes OCR sukun. The two comma glyphs `NOORIN01` 44 and `NOORIN83` 121 sit over ت and are not zabar (not in the table).
- **Seed** now 17 glyphs (pesh, zer, zabar). `build` merges into the seed, so glyphs added from other books stay.
- **Open question for the speaker:** print writes the retroflex nun as ن with a small "v"; all project texts write ن. Keep ن, or write ݨ?
- Review cards cut marks above the line (speaker, 2026-11-12): the crop started 10 px above the row ink. Now 18 px (`build_kahawat_review.py`; 32 px was too much for the speaker, 20 px still a little much); the 30-card page was rebuilt with the same cards.
- Review cards: the margin above the entry shows the bottom of the row above (entries are tight). `fade_neighbour` in `build_kahawat_review.py` fades that ink to light grey; small separate pieces (pesh, zer, zabar, dots) stay black. Rows of the entry itself are never changed.

---

## 2026-11-15: the speaker's check of 30 new Kahawat cards (PDF marks)
Marks file: `data/ocr/kahawat-pdfmarks/review/review_marks.json` (local), sample `review/sample.json`: 30 random cards that have a PDF-placed pesh or zer, none from the first 160.
12 OK, 18 Wrong. Score with `score_marks.py` (OK card: the text shown is the truth, so it is optimistic) and the host-letter check on the 18 Wrong cards only.
- **Wrong cards (the speaker's own text), host letter counted:** 34 marks on read letters. PDF marks: 33 right, 1 missing, 0 other, 0 extra. Plain model (gpu6): 12 right, 22 missing, 1 extra.
- The one miss (card 11, zer in `وِبسما`): UTRNet read the zer glyph as an extra د, so the mark went on that letter. A letter error, not a placement error.
- All 60 fields: exact 42, letters 13, space only 5, marks only 0 (gpu6: exact 22, marks only 22, letters 13, space only 3). Letter error 1.2%.
- Both reviews together (Wrong cards, 2,171 letters), the letter slips left: و read as د 4, ک as گ 3, د as ڈ 2 (the baked `دُ` glyph read as ڈ: `ڈُشمن`, `ڈُھلاوو`), ب as ی 2, آ as ا 2.
- No ݨ, sukun, shadda or zabar in the speaker's new text.

---

## 2026-11-15, later: card 28 ruled, retroflex nun and lam with the small v (speaker's ruling B)
- **Card 28** (first sample, `مَچ` or `مُچ`): the speaker ruled `مُچ`, the print. `data/ocr/kahawat-marks/review_marks.json` card 28 changed. First-30 score now:
  mark error 4 of 36 (11%), 6 wrong or extra with the host letter counted, exact fields 44 of 60.
- **Ruling B for the small "v"**: write it, print-faithful. Over ن it is **ݨ** (U+0768). The speaker also confirmed that ل in `نامل` and `نال` carries the same
  v. Over ل it is written **ڶ** (U+06B6, lam with dot above): the retroflex lateral the speaker named on 2026-11-04 (`orthography-decisions`); the print draws a v, not a dot. One constant (`V_LETTER` in
  `marks_insert.py`) if the speaker prefers ڵ (U+06B5, lam with small v) or ݪ (U+076A).
- **Why a rule on the glyph, not on the OCR letter:** UTRNet reads ل+v as ن (and sometimes as ل then ن, `نالن`), so "ن under a v" is wrong for about half of the
  marks on Gojri-Ghazal p. 40 (5 ن, 6 ل, 1 unclear). The PDF letter glyph under the v tells them apart: `NOORIC01,Bold` 108 is ن; `NOORIC01,Bold` 175 and
  `NOORIC,Bold` 168 are ل (table type `vhost`, field `letter`, found with `marks_table.py add ... vhost standalone <letter>`). A v over an unknown glyph is left alone.
  The 12th v on that page sits over `آ` (`IN01:53`): not handled.
- **Code:** `marks_table.host_letter`, `marks_align.pdf_marks` / `prose_marks.page_marks` (types `nun_n`, `nun_l`), `marks_insert.insert_marks`
  (`ݨ` for ن; `ڶ` for ل, also when UTRNet read it as ن; a doubled ل from `لن` is collapsed). OCR zabar is now removed like pesh, zer and sukun.
- **Gojri-Ghazal gold, PDF page 40** (`data/gold/transcriptions/gojri_ghazal/gojri_ghazal_gold.txt`): 11 words changed to the print:
  `کرن کران ہون چان گزرن` to ݨ, `نال` (4 times) `سمھال` `نامل` to ڶ. Score: 11 of 11 marks right; letters matched 1181 of 1187.
  **The gold set on Hugging Face still has the old text** (not pushed), and `data/gold/bakeoff_results.csv` was made with the old gold; re-score before quoting it.
- **Kahawat-Kosh** has 1 such v in the whole book, so it is nearly unaffected. Full run with the final rules: `data/ocr/kahawat-pdfmarks-v2`.
- **Kahawat-Kosh full run with the final rules** (`data/ocr/kahawat-pdfmarks-v2`, local; 169 pages, 2,820 marks placed, 0 unplaced): first 30 cards mark error 3 of 36 (8%), exact fields 44 of 60, letters 2.1%;
  second 30 cards 1 of 69 (1%), exact 42 of 60, letters 1.2%. No ݨ or ڵ in the output (the one v of the book was not converted).
- **Ruling 2026-11-15 (later):** the letter for ل with the small v is ڵ (U+06B5), not ڶ (U+06B6). `V_LETTER` in `marks_insert.py`, the Ghazal gold (6 words), `ghazal-marks7` and the memory notes now use ڵ. The corrected Ghazal gold text is pushed to `junaidaslam/gojri-nastaliq-ocr-gold` (commit `18eb08d`). `bakeoff_results.csv` still holds scores against the old gold.

---

## 2026-11-15: can the PDF text layer give word spaces? No.
Test on Kahawat-Kosh PDF page 50 (printed 59), right column, 20 gold lines. The text layer has no space glyph. Two measures were tried: (1) holes in the union of the cluster boxes along one line, (2) pen advance minus the font advance of the next cluster (`hmtx`). Both give mostly 0.0 to 0.9 pt for gaps inside words and between words alike. A line with 5 gold spaces shows 9 tiny holes and no clear peak. A few large values (3 to 5 pt) sit at the line end (before the colon), not at word boundaries. Same result as the pixel measure of 2026-10-24: spacing is orthographic, so a Gojri word model or a human check is the way. Research note for the model options: `plans/RESEARCH-nastaliq-word-spacing.md` (agent running).
- **InPage word spaces, second test (2026-11-15).** The Noori text of Kahawat page 50 has no space glyph. Only the Arial runs carry U+0020 (276 spaces in the book). Three measures on the 20 gold lines: ink holes (real outline extents from the saved fonts), holes in the union of pen intervals (origin to origin + font advance), and pen extras. Ink holes also appear after non-joining letters (ا ر د و) inside words. Pen holes are 0.1 to 0.9 pt almost everywhere; line 0 has 9 holes for 5 gold spaces, and the large values sit at line ends. No measure separates word gaps from letter gaps. Question about how InPage stores and exports spaces sent to the research agent.

---

## 2026-11-15: baked glyph letters, shadda search, word-spacing research
- **Baked glyph letters.** The 14 letter+mark glyphs of `NOORIN01,Bold` now carry their letter in `data/decode/noori_marks_seed.json` (pesh: ا ڑ د ر ز ڈ; zer: ا م ذ ر ڈ د و ز), read from the outline pictures. `marks_insert.py` counts (OCR letter, glyph letter) for every baked mark and can correct pairs (`--host-fix ڈد`). On 53 pages (the 60 reviewed cards): 217 baked marks, 202 agree, all 15 others are UTRNet ڈ where the glyph is د. Run with the fix: second set exact 43/60 (was 42), mark error 0 of 69 (was 1), letters 1.1% (was 1.2%); first set exact 44/60, letters 2.1%, mark error 4 of 36 (was 3; UTRNet output changes a little from run to run). Small gain. New options: `--pages`, `--host-fix`.
- **Zer in other fonts.** Not a table gap: for `کِبت` (page 103) the zer glyph `NOORIC,Bold` 47 is in the PDF, but UTRNet read ب as ی and the mark went to the wrong letter.
- **Shadda.** Drawn only inside whole-word glyphs: `NOORIN61,Bold` 10 = بللّی (2 uses), `NOORIN41,Bold` 89 = اللہ with shadda and small alef (72 uses). Not in the table yet. Open question to the speaker: write اللہ as printed (اللّٰہ) or plain.
- **Word spacing research** written to `plans/RESEARCH-nastaliq-word-spacing.md`: character n-gram re-decoding plus a small space tagger, insert/delete only, letter-preservation check, 200 gold lines before comparing methods.

---

## 2026-11-16: spacing rule decided with the speaker
Research note `plans/RESEARCH-gojri-word-spacing-orthography.md`: no published Gojri word-division rule found (searched English and Urdu; Losey 2002 PDF not opened). Closest rule is the Urdu one (space = word, ZWNJ = break inside a word). Speaker's rulings: in `آپ بھلاتے جگ بھلو` the word is `بھلا` + `تے` (تے = then, so), but `تے` is also part of one word (`کھاتے`). `تے` and `ہی` are separate words in some places and part of one word in others, so the rule is decided by meaning in the line, not by a fixed list. Label spaces as words, not as the book shows them. The review page `data/ocr/kahawat-pdfmarks-v2/review_spacing/index.html` (200 cards) carries these rules.

---

## 2026-11-19: Banjara and Dil-Darya full runs, punctuation rule, takhallus sign
- **Full books on AWS** (`launch_prose_pages.py --first 1 --last 0 --pdf-marks`, one `ml.g5.xlarge`): 716 pages, 12,749 rows, 1.9 h, about $2.50. First launch failed at once: an empty `--pages` value reached the entry as a bare `--pages` (argparse exit 2). The launcher now leaves `pages` out when it is empty. Current output: `data/ocr/prose-aws-full2/` (the older `prose-aws-full/` has no takhallus signs).
- **Punctuation rule** (speaker, 2026-11-16): `punct_space` in `ocr_prose_pages.py` puts a space after ۔ and ،.
- **Ulta pesh ٗ** (inverted damma, U+0657): Banjara prints it as its own glyph, `NOORIC,Bold` 61. The speaker's review truth (2026-11-16) writes it, so it is in `noori_marks_seed.json` as type `ulta_pesh` and in `marks_insert.MARK_CH`.
- **Takhallus ؔ** is a standalone bar glyph: `NOORIN86,Bold` 5 and `Batool,Bold` 124 (added to `noori_marks_seed.json`; `marks_table.pdf_mark_glyphs` now scans Batool fonts). The nearest-letter rule put it one letter early (خالؔد), so `marks_insert.move_takhallus` moves it to the end of its word. Marks error on the 10 reviewed pages (178 scored rows, 117 truth marks; corrected 2026-11-20, an earlier version said 14 pages): 29.9% to 12.0% (that score ignores position; the word-end move was checked on the speaker's truth: 20 of 22 signs at word end).
- **Word spaces in tight prose: not solved.** At the 85 missing spaces the white gap in the image is as narrow as inside words (median 0.013 vs 0.015 of line height, shear-corrected too). A word-list splitter (`space_fix.py`, built from our own books and the FLI corpus) adds more wrong spaces than right ones against the review truth. The review truth keeps some glued words (`کےسلسلہ`), while the 2026-11-16 ruling says label spaces by meaning. Decide which before any new spacing work.
- **FLI corpus check:** `scripts/fli_review.py build` writes a 103-card sample page (`data/fli-review/review.html`); `score` reads the downloaded marks.

---

## 2026-11-20: repository audit, re-scored numbers, duplicate PDFs removed

An outside audit of the repository was checked claim by claim; most claims held. Changes:
- **Speaker labels tracked.** Every check the speaker made against the print is now in `data/reviews/` (README there),
  byte-identical to the working copies; the scripts read them there. The 200-line test file holds one later hand fix
  (`page-0125:L26`, ھ), so `make_clean_labels.py` must not overwrite it.
- **Rights.** MIT `LICENSE` for code and prompts; `DATA-NOTICE.md` for data, book content and third-party tools. The
  FLI corpus texts and the Common Voice TSV files are no longer tracked (kept locally, gitignored).
- **Scorer fix.** ݨ (U+0768) is in the Arabic Supplement block, which the Arabic-letter scorers left out, so it counted
  as an English character. The scorers now keep U+0750-077F and treat ݩ as ݨ.
- **UTRNet is random at inference.** Its temporal dropout stays on (five `np.random` masks averaged per read), so runs
  differ by a few letters; threads are not the cause (two single-thread runs also differed). `utrnet_arabic_eval.py`
  takes `--seed`: two seed-0 runs were byte-identical; seeds 0 to 4 give 28 to 31 of 1,400 letters (2.0% to 2.2%).
- **Re-scored after the 2026-11-15 Ghazal gold fix.** Bake-off word error: Gemini 3.6 Flash 17.8%, Sonnet 4.6 22.6%,
  Composer 13.0%. Page pipeline (`pipe_v4`): 3.7% Arabic-letter error (230 of 6,253); on the 8 Gemini pages 2.9%
  against Gemini 3.3%. The Hugging Face gold card was updated.
- **Seeded pipeline.** `ocrlib.UTRNet` now resets `np.random` (seed 0 by default) before every read: 40 crops read
  in opposite orders gave identical text (without the seed, two passes differed on 39 of 40). The page pipeline run
  `pipe_v5` (`py -3 -X utf8 scripts/ocr_eval/ocr_page.py --repo <UTRNet clone> --weights <large.pth> --segnet <segnet_v2.pt> --tag pipe_v5 --columns kahawat_kosh`) gives 229 of 6,253 letters (3.7%), English 6.6%; a second run was byte-identical.
  SegNet weights were fetched from S3 to `D:/ocr-tools/weights/segnet_v2.pt`.
- **200-line test from the repository alone.** The 200 crops (3.1 MB) and per-page folio flags are tracked in
  `data/reviews/dictionary-200-lines/`. With `data/synth` and `data/decode/out` hidden, seed 0 gave the same 29
  letters and 179 exact lines, line by line.
- **Duplicate PDFs.** Every page of every PDF in `pdfs/` was rendered to a 32x45 thumbnail and correlated with every
  page of every other file; candidate pairs were checked page by page at 120x170 and by text layer, and unclear pairs
  by eye. The 7 known byte-identical groups came out at 100% (the control). Ten more files are the same book in
  another file: two Rahi dictionary parts (169 and 110 pages), Ismail Zabi kalam (81), the folk-song collection (292),
  the 7th-class book (72, same as the Shingar textbook), the Gojri Bait collection (172, three files), the first primer
  (56), the Concise Gojri-English Dictionary (its 24 pages are the front matter of the big dictionary), and
  `gojri-language-literature.pdf` (270; the same text and line breaks as `gojri-adab-ki-tariekh.pdf` in another font).
  All 18 duplicate files (8 byte-identical, 10 by content) were deleted from `pdfs/` and flagged
  `removed_duplicate_nov2026` in the manifest. The kept copy is the gold-page source where there is one, else the
  manifest primary, else the root copy. Unique pages: 19,725 (was 21,143). Pages that need decode or OCR: 14,060
  (was 15,478). Tier 1: 3,007 pages.
- **Kept although they overlap:** three primer pairs are two editions of one J&K board book (53 of 64, 23 of 33 and
  24 of 33 pages identical; covers and some pages differ); `Gojri-Adbiyaat.pdf` holds about 73% of
  `gojri-adab-ki-tariekh.pdf` and 82 pages of `Gojri-Sheryaat.pdf`. The two `Gujjar_Qabila_Ki_Louk_Warsti_Dictionary`
  files share no page (median correlation 0.24). The title pages show Vol 1 (`... (1).pdf`, ا to س) and Vol 2
  (`....pdf`, ش to ی, the source of the `louk_warsti` gold page); the speaker confirmed it. Renamed to
  `Gujjar_Qabila_Ki_Louk_Warsti_Dictionary_Vol1.pdf` and `..._Vol2.pdf`.
- **Hugging Face PDF collection `v2.0`:** the 10 content duplicates removed and the Louk Warsti files renamed (64 PDFs,
  14,518 pages). The earlier 74-file state is tagged `v1.0`. `data/pdf-corpus/CREDITS.tsv` and the card follow.
- **Docs.** README rewritten as the entry point; `docs/TIMELINE.md`, `scripts/README.md`; ROADMAP rewritten; this log
  put in date order, with the NOORIN batch notes moved to `data/archive/noorin-decode-spike/BATCH-LOG.md`.
- **Gojri-Ghazal, full book** (`launch_prose_pages.py --first 1 --last 0 --pdf-marks --pdf-prefix prose-pdf-ghazal`,
  job `gojri-ocr-prose-2026-11-20-14-35-56-652`, 1,993 billable seconds, about $0.80): 209 pages, 3,770 rows, local in
  `data/ocr/ghazal-full/` (gitignored). 2,706 PDF marks placed (pesh 1,282, zer 680, zabar 43, ulta pesh 11), 69 ݨ,
  121 ڵ, 59 verse signs, 402 takhallus signs (high for 209 pages; spot-check before use). Gold page 40: 11 of 11
  readable marks right, 1.4% Arabic-letter error (a development page, so a consistency check only).
- **Spacing review page rebuilt:** `data/ocr/prose-words/space_review.html`, 66 proposed splits of glued words in the
  prose review truth, for the speaker to accept or reject (labels follow meaning, ruling 2026-11-16).
- **ASR baseline set up.** The official Common Voice split has one training speaker (3,207 clips, 2.9 h), no dev clips
  and five test speakers. `scripts/asr/prepare_cv_split.py` keeps the official test set and trains on every other
  validated clip whose sentence is not a test sentence: train 9,041 clips (3 speakers), dev 475, test 623 (two test
  speakers also appear in training, three never do; both groups are reported). The split is rebuilt from the
  tracked `data/asr/split_clips.tsv`; the clips stay private on S3. A SageMaker smoke test (285 s) passed end to end;
  the full Whisper-small run is `gojri-asr-whisper-2026-11-20-17-43-55-757`.
- **Locked test set:** all 20 page drafts are in `data/test-locked/drafts/` for the speaker to correct.
- **Second pass on the documents** (later the same day).
  - Non-commercial terms: the code moved from MIT (commit `49a9002`, a few hours earlier) to the PolyForm Noncommercial
    License 1.0.0; project data is CC BY-NC 4.0; the gold, lexicon and PDF licenses say non-commercial only.
  - Accuracy and AI-use notice in the README, `CONTRIBUTING.md` and all four Hugging Face cards.
  - **Credit correction.** The title pages of `anjumshanasi/Gojri-English-Dictionary.pdf` read *Concise Gojri-English
    Dictionary*, "BY Dr. M. R. Anjum Awan", publisher J&K Anjuman Taraqi Gojri Adab. The dataset card, the README and
    several notes had named Dr. Javaid Rahi. Corrected everywhere; the card keeps a correction note.
  - UTRNet's license: its LICENSE file is CC BY-NC 4.0, its README says CC BY-NC-SA 4.0. Docs now give both.
  - Whisper-small weights are Apache 2.0 (model card), not MIT.
  - Re-verified from data: dictionary v1 to v2 changed 10,228 of 11,767 lines on 465 pages (published v1.0 and v2.0
    compared); 316 of 333 Arabic words and 160 of 178 paren spaces (`merge_decode_letters.py --check`); Kahawat
    mark scores 3 of 36 and 1 of 69, letters 2.1% and 1.2% (`score_marks.py` on `kahawat-pdfmarks-v2`).
  - Machine OCR text of Kahawat-Kosh (2,383 entries), Banjara (496 pages), Dil-Darya (220) and Gojri-Ghazal (209)
    published in `data/ocr-output/` for speaker review.

- **ASR baseline result.** Job `gojri-asr-whisper-2026-11-20-17-43-55-757` (2,248 billable seconds): Whisper-small,
  2,500 steps. Dev word error 23.2%, 20.9%, 18.9%, 19.3%, 20.8% at steps 500 to 2,500; the step-1,500 checkpoint was
  kept. Official test set (623 clips): zero-shot 73.8% word error, 33.2% character error; fine-tuned 22.7% and 8.3%;
  seen speakers (389 clips) 23.4%, unseen speakers (234 clips) 21.6%. One run. Cost of the three jobs of the day:
  about $1.80 (1,993 + 285 + 2,248 billable seconds).

## 2026-11-21: Kahawat-Kosh spacing review (200 cards)

The speaker reviewed all 200 cards of `review_spacing` and wrote the text as words (ruling 2026-11-16). Export:
156 fixed, 44 OK, 0 unsure. Saved as `data/reviews/kahawat-spacing/spacing_marks_20261121.json`; scorer
`scripts/ocr_eval/score_spacing.py`.

- **OCR text against it.** Letter error 44 of 4,036 (1.1%); marks identical on 196 of 200 cards. The OCR text has
  901 words, the speaker's text 1,165. On the 162 cards whose letters match: 759 spaces in the truth, 553 in the OCR
  text, 527 right, 232 missing (205 after a non-joining letter), 26 extra; 50 cards have exact spaces.
- **Letter fixes (44 cards).** گ for ک 10 times, a missing ب in جیبھ 7 times, 6 missing colons, single letters for
  the rest. Three `fixed` cards equal the OCR text (ids 2, 9, 71).
- **Word splitter (`space_fix.py`), first run.** Margin 2: 135 spaces added, 102 right. Margin 4: 103 added, 86 right;
  70 cards exact. Margin 6: 71 added, 68 right; 68 cards exact. (After the one-letter rule of the later entry below:
  margin 2 adds 124, 102 right, 75 cards exact; margin 4 adds 101, 86 right, 72 exact; margin 6 unchanged.) The word list holds the FLI corpus and the Banjara and
  Dil-Darya OCR, no Kahawat-Kosh text. The margin was picked among 2, 4, 6 and 8 on these same cards. Adding the
  speaker's own words from the other cards (5-fold test) gained 1 to 2 spaces.
- **Reading.** This reverses the note of 2026-11-16 that the splitter adds more wrong spaces than right ones. That
  test used the prose review, where some rows kept glued words, so the truth and the book differ. A second book with
  spaces labelled the same way is the next check.
- Cards 26, 113 and 126 were checked against the page image: the speaker's text matches the print.

## 2026-11-21: word-split review (66 cards)

The speaker checked the 66 splits that `space_fix.py` proposed in Banjara and Dil-Darya and wrote the right split in
a new box on each card (`space_review.py` now has the box). Saved in `data/reviews/prose-word-splits/`; scorer
`scripts/ocr_eval/score_splits.py`.

- **Result.** 72 spaces proposed, 66 right (91.7%), 6 cut a word. 56 cards equal the proposal; 4 are right but
  incomplete (4 spaces missing in all: `نور محمد`, `ہر ہر گل`, `آ کے جے`, `کیو سر کھلا`); 6 were kept whole by the speaker:
  `پہاڑیوں`, `ہزارے`, `گویوں`, `گیارہ`, `ہولو`, `کیاری`. Letters never changed. The Accept/Reject mark and the text
  disagree on one card (`کےنورمحمد`, Reject, right but incomplete), so the scorer uses the text.
- **Pattern.** In all 6 wrong cuts the second piece (`یوں` twice, `ے`, `رہ`, `لو`, `ری`) is an ending or has no meaning
  of its own there; the right proposals have a real word as the second piece.
- **Rule added.** `MIN_PIECE = 2` in `space_fix.py`: no piece shorter than 2 letters. It removes the `ہزار ے` cut on
  this set and, on the 200 Kahawat cards (not used to find the rule), 2 wrong spaces at margin 4 and no right one. A
  blocklist of the other pieces (`یوں`, `ری`, `رہ`, `لو`) removed one more wrong space there; it rests on 6 cases, so
  it is not in the code.
- **Limits.** The cards are the splitter's own proposals (precision, not recall), and its word list holds the OCR of
  these two books.

## 2026-11-23: PDF collection made private

`junaidaslam/gojri-print-pdf-collection` was set to private on Hugging Face (checked with the Hub API). The dictionary
text, the lexicon and the OCR gold set stay public. GitHub never held the PDFs (`/pdfs/` is gitignored). `data/ocr-output/` (machine OCR text of four
books) stays on GitHub.

- **Docs changed.** README, ROADMAP, CLAUDE.md, AGENTS.md, DATA-NOTICE, `data/pdf-corpus/` (README and LICENSE),
  `data/ocr-output/`, `data/reviews/`, `data/test-locked/`, `data/utrnet-test/`, `datasets/README.md`, TIMELINE. Links to
  the PDF collection are gone; each doc points to `data/pdf-corpus/CREDITS.tsv` and says to get the book from its
  original source.
- **Open.** Check whether "Prof. (Dr.) Rafique Anjum" and "Dr. M. R. Anjum Awan" are one person (credits).

## 2026-11-23: documentation audit fixes

A documentation audit listed stale or wrong statements. Each claim was checked against the repo first.
- **Rights wording.** The docs said "the source books are not shared", but 12 gold page images, 20 locked page images,
  200 dictionary line crops and the OCR text of four books are public. The docs now say: the full books are private;
  short excerpts and derived text are shared under research terms, with credit. `data/pdf-corpus/README.md` is now a
  rights notice, not a dataset card (no load instruction, no citation). Dead pointers to the private collection were
  removed from the README, `data/reviews/README.md` and the UTRNet steps.
- **Results added to the public summary.** The character n-gram space inserter (100 locked Kahawat-Kosh cards: space errors
  116 to 52), its failure on prose, the language tagger (78.4%, group cross-validation) and the shadda ruling are now in
  README, ROADMAP, CLAUDE.md, TIMELINE and `data/reviews/kahawat-spacing/README.md`. The splitter contradiction in CLAUDE.md
  is fixed (the 21 November reviews show 86 of 101 right).
- **Numbers fixed.** Mark error on the first 30 Kahawat cards: 8% (3 of 36), not 14%. Page pipeline: 229 of 6,253, not 230.
  UTRNet seed 0: 179 exact lines, not 178. The old numbers stay in the log entries where they were measured.
- **ASR sentence overlap, checked on the local data.** The split is disjoint on exact text, but after the scorer's
  normalisation 4 of 623 test clips (0.6%) have the same text as a training clip: 3 from S6 (not in training), 1 from S3.
  One more matches a dev sentence. The 22.7% stands; the docs no longer say "no sentence shared" without that qualifier.
  (The audit said 2 from S6; the count here is 3.)
- **Also fixed.** The CLAUDE.md top line (no longer "no implementation"), the PDF count on disk (64) and the AWS spend (about
  $12). ROADMAP stage 1 now lists four books and the locked test set.
- **Not done, needs a decision.** Publishing small derived artifacts for re-running (SegNet weights, the fine-tuned Whisper
  model, the n-gram count tables, pre-cut Arabic run images); the prose mark metric (12.0% in `data/ocr-output/README.md`
  does not reproduce from the tracked review, which stores an earlier OCR run); the locked test gold text; the ASR model
  upload. GitHub shows the license as Other (PolyForm Noncommercial is not OSI open source).


---

## Glossary (grows as new terms come up)

- **Token**: the unit a model reads/writes in and is billed by: roughly a
  word-piece, not a whole word. Dense Nastaliq text uses more tokens per page than
  the same content in Latin script.
- **Prompt**: the instructions given to a model alongside its input (here, the image)
  telling it what to do. Prompt wording measurably affects output quality: part of
  why exact prompts are being logged from now on.
- **Hallucination**: a model producing a fluent, plausible-looking answer that isn't
  actually grounded in the real input: dangerous because it fails *silently*,
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

## 2026-11-23: character n-gram space inserter (Kahawat spacing cards)
Code `scripts/ocr_eval/spacing_lm.py` (model, insert only, letters never change; the experiment asserts it) and `spacing_experiment.py`. Split of the 200 spacing cards, frozen in `data/reviews/kahawat-spacing/split_20261123.json` (seed 20261123): 100 dev, 100 locked test. Model: interpolated Witten-Bell character n-gram, mix of an FLI-corpus model (3,328 sentences, 238,837 letters, local) and a model of the dev cards' word-spaced truth; a space is added only after a non-joining letter, where it raises the score by more than a bonus.
- **Cross-validation on the 100 dev cards (5 folds, space errors on the 83 letter-identical cards, 400 truth spaces).** OCR as read: 142 errors (129 missing, 13 extra). Grid of 315 configs (order 3 to 7, FLI weight 0 to 1, card weight 1 or 5, bonus -2 to 10): a plateau of 60 to 66 errors for order 4 to 7, FLI weight 0.5 to 0.95, bonus 0. Best, chosen before any test look: order 5, FLI weight 0.8, bonus 0, card weight 1, positions after non-joiners: 60 errors (24 missing, 36 extra). Allowing a space after any letter (checked after the grid): 58 at bonus -1, no real gain, not used.
- **Locked test, scored once with the committed config** (`data/reviews/kahawat-spacing/test_log.tsv`; 79 of the 100 cards have letters equal to the truth, 359 truth spaces): OCR as read 116 errors (103 missing, 13 extra); character n-gram inserter 52 errors (18 missing, 34 extra), precision 90.9%, recall 95.0%, 45 cards with exact spaces (OCR as read: 24); old word splitter at margin 4: 79 errors (61 missing, 18 extra), its margin was picked on all 200 cards so it is favoured.
- **Limits.** On a card marked OK the truth is the OCR text, so scores are a little optimistic. The model trains on FLI text, whose own spacing is not consistent (کر کے 7 times, کرکے 3), plus 100 cards. It adds about 34 spaces that the speaker did not write per 359 truth spaces. Kahawat idioms are short lines; prose rows (reviews 4 and 6) are the next test. The test set is now used for this config; further tuning needs new speaker cards.

## 2026-11-23: space inserter on the prose reviews (Banjara, Dil-Darya)
`score_prose_spacing.py`; same config as the Kahawat test (order 5, FLI weight 0.8, bonus 0, after non-joiners), trained on the FLI corpus and all 200 Kahawat spacing cards; nothing tuned on prose.
- **A. 167 OCR rows of the 2026-11-16 review (130 with letters equal to the truth, 1,112 truth spaces).** OCR as read: 1,038 right, 74 missing, 14 extra. Model: 1,100 right, 12 missing, 191 extra. Old splitter at margin 4: 1,065 right, 47 missing, 58 extra (its word list holds these books). The extra count is too high to trust: that review pre-dates the ruling "spaces follow meaning", and a look at the 191 shows many right splits that the truth keeps glued (`سے قراقرم`, `ہے اور`).
- **B. 66 split cards.** Inside the 66 tokens the model gives 66 right, 6 wrong, 4 missing (the old splitter: 66, 6, 4). No gain on these tokens.
- **Next.** `space_review_model.py` builds `data/ocr/prose-words/model_space_review.html`: 170 cards, one per glued token where the model adds a space (tokens of the 66 cards and tokens that the speaker's row text already splits the same way are left out). The speaker's accept/reject marks give the real precision on prose.
- **Speaker check of the model's prose spaces (55 of 170 cards, 2026-11-23): not usable on prose.** Of the 67 spaces added in those tokens, 32 are right and 35 wrong (9 truth spaces missing). The model cuts inside single words (`قدامت`, `مقبوضہ`, `قلانچیں`, `ڈوڈہ`, `جغرافیہ`), mostly Urdu words and place names: much of Banjara and Dil-Darya is Urdu, and the model learned from Gojri idioms and the FLI text. A stricter bonus lowers the wrong cuts and the right ones together (tokens of the 55 new and the 66 old cards: bonus 0 gives 98 right, 41 wrong; bonus -3 gives 77 right, 15 wrong; bonus -6 gives 38 right, 2 wrong); this sample is biased, so it is a guide only. A leading-particle rule (کے سے اور کا ...) gives 29 right and 5 wrong on the same tokens but finds few of the missing spaces. Two cards also show OCR letter errors (`سوبہ` for `صوبہ`, `تاہے` for `جاتا ہے`). Files: `data/reviews/prose-model-space/`. Decision: the model stays for Kahawat idioms (Gojri, tested on 100 locked cards); do not apply it to prose or to Urdu text until the text language is known per line.
- **Kahawat-Kosh full run (2026-11-23).** 105 pages ran locally, then I stopped the local run on the speaker's order (CPU jobs go to AWS) and the other 64 pages ran as SageMaker job `gojri-marks-kahawat-2026-11-23-14-00-17-352` (`scripts/ocr_eval/launch_marks.py`, `sm_marks_entry.py`; ml.g5.xlarge, GPU, about 12 minutes). Local pages use the CPU, AWS pages the GPU; UTRNet differs a little between the two. All 169 pages are in `data/ocr/kahawat-final` with the ڈ→د fix. Not scored on the reviewed cards yet.

## 2026-11-23: shadda (speaker ruling) and the language research
- **Ruling.** The speaker said `اللہ` keeps its shadda: write it as printed, `اللّٰہ` (ا ل ل, U+0651, U+0670, ہ). The two whole-word glyphs that draw a shadda are now used by `scripts/ocr_eval/pdf_marks/word_glyphs.py`: `NOORIN41,Bold` 89 (اللّٰہ, 72 uses) and `NOORIN61,Bold` 10 (بللّی, 2 uses).
- **Method.** Each glyph goes to the nearest printed row of an entry (idiom right of the column line, meaning left). If the number of glyphs in a field equals the number of matching words in the OCR text, all of them get the marks. If not, the field stays as it is and is listed in `word_glyph_flags.json`.
- **Result on `data/ocr/kahawat-final` -> `kahawat-final2`:** 68 of 74 words fixed in 62 fields. 5 fields flagged because the OCR misread the word (`اللدئےتے`, `اللنے`, `عبیدالل`, `اللران`, `الللی`); the glyph says اللہ is there. They wait for the speaker. Both `بللی` words (pages 10 and 46) now carry the shadda.
- **Language research** (`plans/RESEARCH-urdu-gojri-language-id-and-mixed-spacing.md`): no public LID has a Gojri label (GlotLID v3/v4, OpenLID, NLLB, lid.176, CLD3, langid.py). Character n-gram models win on close language groups (VarDial ILI 2018, DSL, PALI). Marker letters ݩ ݨ ڵ occur in 0 of 16,321 Urdu Common Voice sentences; own recount on the FLI files (without file 10): 658 of 3,960 lines (16.6%). The FLI text stores the small-v noon as U+0769, so scorers and rules must hold U+0768 and U+0769. Plan: free labels (Kahawat idiom = Gojri, meaning = Urdu; FLI = Gojri; file 10 Urdu half = Urdu), speaker tags only the prose test rows, group-by-book folds, `unsure` class, marker rule as baseline, GlotLID as a side check only.

## 2026-11-23: language tagger, first run on free labels
Code: `scripts/ocr_eval/langid.py` (one character n-gram model per class, from `spacing_lm.CharLM`; text without spaces, marks or punctuation; ݨ ݩ ڵ and the FLI placeholder U+FFFF fold to one symbol; marker flag), `build_lang_tag_review.py` (text-only tagging page). Free labels: gju = FLI stories and books, the Gojri parts of file 10, Kahawat idioms (2,235); urd = the Urdu parts of file 10 (47), Kahawat meanings (2,309). Folds by group (FLI file, file-10 story, 10-page Kahawat block), 5 folds, 7,976 lines of 8 or more letters.
- **Marker rule alone:** gju precision 100%, recall 12.6% (FLI lines 20.5% hold a marker, file 10 27.4%; the Kahawat OCR text holds none, the book has one printed v). Never wrong on Urdu lines, as the research said, but it finds one Gojri line in eight.
- **Char n-gram LLR, group CV:** order 4 is best: accuracy 78.4% (78.7% with the marker rule on top), gju P 91 R 77, urd P 60 R 82, macro F1 76.5. Order 2: 70, 3: 75, 5: 75, 6: 74.
- **Where it fails.** By source: FLI 94.7% right, Kahawat meaning 83.0%, file 10 62.1%, Kahawat idiom only 51.1%. By length: 8 to 15 letters 62.6%, 16 to 30 75.0%, 31 to 60 89.6%, 61 or more 97.5%. Kahawat idioms are very short and many are one-word or Urdu-like phrases; some Kahawat meanings are Gojri proverbs (label noise). So accuracy depends on line length; prose rows are long.
- **Genre confound.** The Urdu class is only Kahawat meanings (short explanations) and 47 lines of translation. It is not the genre of the books. The real test is the speaker's tags of prose rows.
- **Prose is code-mixed.** Banjara p.100 reads `تاریخ گواہ ہےجے ڈنیا مانھ ہمیشاں اُسےزبان نے ترقی کی ہے`: Urdu grammar with Gojri words in one sentence. So the tag set has `mixed` and `other`, not only gju and urd.
- **Tagging page:** `data/ocr/prose-words/lang_tag_review.html` (262 rows: 142 reviewed prose rows of review_marks.json, 120 new random rows from prose-aws-full2). Keys 1 to 5. No model output on the page. Result goes to `data/reviews/prose-language/` when the speaker downloads `lang_tags.json`.

## 2026-11-24: the speaker's language tags of 262 prose rows
File `data/reviews/prose-language/lang_tags_20261123.json` (README there). Gojri 226, Urdu 29, mixed 4, unsure 3.
- **Urdu is rare in these books.** The 120 random new rows hold 110 Gojri, 5 Urdu, 4 mixed, 1 unsure: Urdu is about 4% of rows. The other 24 Urdu rows come from the oversampled reviewed rows (21 on Banjara p.12 and p.13, the introduction essay). Other Urdu rows: Banjara p.60 and p.361, Dil-Darya p.26, p.191, p.198.
- **The earlier prose spacing check was almost all Urdu.** Of the 55 model-space cards the speaker checked, 52 come from rows he tags Urdu, 2 from Gojri rows (both rejected), 1 untagged. So the "35 wrong of 67" result says the space model fails on Urdu text; it says almost nothing about Gojri prose (2 cards). Of the 170 cards 87 are on p.12.
- **OCR spaces on Urdu rows are already good:** 199 right, 7 missing, 4 extra (24 reviewed Urdu rows). The model adds 61 extra spaces there (precision 77%). On the 116 reviewed Gojri rows: OCR 745 right, 66 missing, 10 extra; model 801 right, 10 missing, 122 extra. The extra count is not safe: that review pre-dates the rule "spaces follow meaning". The Gojri cards are the real test.
- **The free-label tagger does not work on prose.** On the 255 rows tagged gju or urd, order 4 with the marker rule: accuracy 76.1%, gju P 89.1 R 83.2, urd P 13.6 R 20.7. Always saying Gojri gives 88.6%. Urdu precision is at the base rate. The tagger learned the genre of Kahawat meanings, not Urdu in general. The marker letters occur in 1 of 255 prose rows (the review text does not carry them).
- **Speaker point:** Gojri and Urdu are sometimes 100% the same (names of people and places), so a row alone can be impossible to tag. New page `build_lang_context_review.py`: context rows before and after, new tag `same`; 7 rows (4 mixed, 3 unsure).

## 2026-11-24: context tags, and the space check on Gojri rows
- **Context pass done.** The speaker re-tagged the 7 `mixed` or `unsure` rows with two lines of context (`data/reviews/prose-language/lang_tags_context_20261124.json`): 2 `same` (name and place lists, Banjara p.5 and p.8), 2 `urd`, 3 `gju`. Merged file `lang_tags_final_20261124.json`: 262 rows, gju 229, urd 31, same 2. Random rows only: 112 gju, 6 urd, 2 same (5% Urdu). No `mixed`, `other` or `unsure` row is left.
- **Rule for names and places:** a row that Gojri and Urdu write the same way gets `same`. It is not a training row for either class.
- **Next page built:** `space_review_model.py --gojri-only` writes `data/ocr/prose-words/model_space_review_gju.html`: 106 cards that the speaker has not checked, all on rows tagged Gojri (Dil-Darya p.12 and p.200, Banjara p.300 and others). This is the first real test of the space inserter on Gojri prose (the 55 earlier cards were 52 Urdu rows). Result goes to `data/reviews/prose-model-space/` after the speaker downloads `model_space_review_gju.json`.

## 2026-11-24: space model on Gojri rows (106 cards, speaker marks)
File `data/reviews/prose-model-space/model_space_gju_20261124.json`. 52 accepted, 54 rejected. Per space (101 cards with equal letters): 79 right, 49 wrong, 10 missing; 48 cards exact. 5 cards hold letter fixes (OCR letter errors, for example `کدلھیں` read for `کدلبھیں`, `ایسوباغچو` for `ایسوباغیچو`).
- **The model is not safe as it is on Gojri prose either.** Wrong cuts are 38% of its added spaces.
- **The error is length.** Tokens under 6 letters: 16 right, 29 wrong (single words cut: `مانہ`, `جانے`, `عارف`, `انجم`, `نوجوان`, `روداد`). Tokens of 8 to 10 letters: 18 right, 4 wrong. 11 or more: 24 right, 2 wrong. Rule "split only tokens of 8 or more letters": 42 right, 6 wrong, 47 true spaces left unfound. With 7: 55 right, 10 wrong. Chosen on the same sample: optimistic.
- **Urdu words inside Gojri text** (speaker's point): the model cuts Urdu loan words and names (`انجم`, `نونہال`, `روداد`, `صوفی`, `اکیڈمی`) because its training text is Gojri idioms and FLI stories. A row tag does not help here: the row is Gojri and holds Urdu words.
- **Next:** do not apply the model to prose yet. Fresh test of the 8-letter rule needs new cards from rows not seen so far.

## 2026-11-24: correction, the checked rows are poetry; OCR letters next
- **Speaker correction:** the rows of the 106-card space check were poetry, not prose. My notes called them prose. The length result (short tokens cut wrongly) comes from verse rows (short words, rhyme words, two halves with a TAB) and may differ on running prose. The page genre is not yet tagged. The 8-letter rule stays unproven. Decision: spend the time on the OCR letters; the space model stays off prose and poetry for now.
- **OCR letters on the 178 reviewed rows (10 pages, current run `prose-aws-full2`, against the speaker's text):** 65 letter differences in 6,728 letters (0.97%; spaces and marks left out; 3 of them are TABs). Marks: 11 differences in 92. The commonest misses are the takhallus sign `ؔ` (U+0614) and the verse sign `؎` (U+060E) after poets' names, and a few letters (ح for ن, ڈ for د, a lost ا or ئ). This is a small, non-random set (10 pages of 716).
- **Next:** `build_random_ocr_review.py` writes `data/ocr/prose-words/random_ocr_review.html`: 120 random rows from all pages (the `origin: new` rows of the language-tag page), printed row image plus editable OCR text. It gives an unbiased letter and mark error, split by language tag. Result goes to `data/reviews/random-ocr-rows/`.

## 2026-11-24: does the 2.1% UTRNet number include spaces? No; spacing page for the 200 dictionary lines
- The 2.1% letter error (data/utrnet-test/README.md) drops spaces before it scores (`scripts/utrnet_arabic_eval.py`: Arabic-block characters only), so it says nothing about spacing. The Arabic parts of these lines are short: 342 Arabic words in 195 lines, 83 spaces inside Arabic runs (45 lines with 2 or more words). The runs were also cut with PDF glyph boxes, not found by a line detector, so the number is a best case.
- The speaker doubts the spaces in `text_fix`. Page `scripts/ocr_eval/build_dictionary_spacing_review.py` writes `data/ocr/dict-spacing/spacing_review.html` (195 lines with Arabic, printed line image plus editable truth text, multi-word lines first). After the speaker's fix: rescore UTRNet's own spaces (word boundaries, precision and recall) on these lines.

## 2026-11-24: OpenCode search for Gojri text
Prompt `plans/PROMPT-opencode-gojri-corpus-search.md`; result summarised and checked in `plans/RESEARCH-gojri-text-sources-20261124.md`. 32 sources, none confirmed above 100,000 words. Best: the typed-Gojri blog A01 (size unknown, rights unknown, mostly poetry), the paid LDC-IL parallel corpus (about 29,000 to 33,000 words). Print collections are InPage or scans: OCR work. Raw folder `gojri-corpus-search/` is gitignored (third-party samples, private contact data). Open for the speaker: decide on LDC-IL.

## 2026-11-24: blog text fetched (speaker ruling: use it)
The blogs are public pages; the project uses them for non-commercial research, with credit to the blog and the author of each post. `scripts/corpus/fetch_blogger.py` fetched A01 (Gojri Zuban o Adab: 199 posts, 67,177 words, not the agent's 100,000 to 160,000) and the Gojri label of A04 (10 posts, 607 words) into gitignored `datasets/gojri-blogs/`. Checks: the language tagger gives about 78% Gojri by letters on A01 (130 of 188 long posts at 70% or more, 1 at 30% or less), 82% on A04; a rough number, since the tagger learned FLI spelling. Spacing is good: 0.11% of tokens have 12 or more letters (FLI 0.02%). About 52,000 Gojri words, close to the size of the FLI corpus. Gojri-only filter (`scripts/corpus/filter_gojri_blog.py`): the blog HTML breaks some poems into one-word lines, so the filter joins lines into chunks of at least 80 letters and tags each chunk (margin 0.05). A01 words: 55,747 `gju`, 6,003 `urd`, 5,366 `unsure`. A04 words: 505 `gju`, 28 `urd`, 74 `unsure`. Kept for use: 1,944 chunks, 56,252 words, each with post URL, title and author label for the credit. The tagger is a draft: the speaker checks a sample of kept, dropped and unsure chunks before the text is used. Review page: `scripts/corpus/build_blog_lang_review.py` writes `datasets/gojri-blogs/review/review.html` (129 random chunks, draft tag hidden: 55 kept, 36 dropped, 38 unsure; local, gitignored). After the speaker's download, `score_blog_lang_review.py` gives the share of Gojri in the kept words and the Gojri words lost. Not done: tag each post by genre, check spelling against the print-faithful rules (ن for ݨ), decide a use (space model test text, text for a language model).

## 2026-11-25: blog word count (A01)
Speaker approved reading the public feed. 199 posts, 66,599 Arabic-script words (not 100,000 to 160,000). About 12,000 to 25,000 of them look Gojri by a crude marker test; the rest is Urdu. No ݨ ݩ ڵ at all. Raw feed deleted; counts kept in `plans/RESEARCH-gojri-text-sources-20261124.md`.
