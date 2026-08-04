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
