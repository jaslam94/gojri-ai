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
