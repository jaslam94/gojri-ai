# Experiment Log

A dated, running journal of what we try, what we find, and why we made each call.
`CLAUDE.md` holds the accumulated *current state* of project knowledge (decisions,
findings, status); this file is the *story* of how we got there, kept mainly so you
can track your own learning as we go. New AI/ML terms get a one-line explanation the
first time they show up, then get added to the Glossary at the bottom.

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
