# Handoff: Run the real OCR test batch via AWS Bedrock

> **Status update (2026-08-15): gold scoring is in place. Bulk vision OCR is
> paused.** Haiku 4.5 and the other cheap vision models were tested and shelved
> (`LOG.md`). Best one-shot API on the 12-page gold set is Gemini 3.6 Flash
> (17.3% WER) vs Sonnet 4.6 (21.9%). That is not good enough to run unreviewed
> on 14,761 pages. Next OCR experiment is the decode-table spike. Score with
> `py -3 scripts/score_gold.py`. Output path is
> `transcriptions/<page>/<page>_<model>_<version>_original.txt`. Do not write
> `_corrected.txt`. Early rows in `ocr_runs_log.csv` still point at archived
> filenames; the files themselves live under `transcriptions_archived/`.
>
> **Status update (2026-08-05): this plan has been executed and substantially
> extended since it was written. Read `LOG.md`'s 2026-08-04/05 entries for the full,
> current picture before acting on anything below** — several specifics here are now
> stale:
> - Images actually used are `data/gold/images_cropped/{id}.png`, not
>   `data/gold/images/{id}.png` — cropping margins cut image tokens ~60% on the
>   densest pages, with originals kept for comparison. `data/gold/candidates.csv`
>   now points at the cropped versions.
> - Output files are named `{id}_{model}_{version}_original.txt` under
>   `data/gold/transcriptions/<page_id>/`, not `data/gold/images/{id}_{model}.txt`.
> - Every call now logs exact temperature/max_tokens/thinking settings to
>   `data/gold/ocr_runs_log.csv`, not just token counts - settings were found to be
>   completely unconfigured in the first pass, which mattered.
> - The model roster grew well beyond Haiku/Sonnet: Gemini 3.6 Flash is the
>   current default one-shot candidate; Kimi K2.5, Haiku 4.5, Qwen3-VL, Llama 4
>   Maverick, and Pixtral Large were tested and shelved (reasons in `LOG.md`).
>   Sonnet 5 on Bedrock is still Sales-gated. DeepSeek-OCR has no working free
>   API path found so far.
> - Gold is one `<page>_gold.txt` per folder. See `data/gold/README.md`.
>
> The sections below are kept for historical/methodology reference (the AWS
> Bedrock setup notes, request-format background, and cost-math framing are still
> accurate) but don't follow the specific file paths/names here without
> cross-checking `LOG.md` first.

This is a self-contained briefing for a fresh Claude session that will execute what
this session only prepared. Read this file plus the four referenced below, and you
have everything needed to run the task without re-deriving anything.

## Read these first
- `CLAUDE.md` — full project context and research findings
- `ROADMAP.md` — staged plan; Stage 1 is OCR, this task is part of it
- `plans/STAGE-0.md` — the gold-set-building plan this task follows on from
- `data/gold/README.md` — what the gold set is and how it's organized

## The task
Send each of 12 gold-set page images through AWS Bedrock using **both** Claude
Haiku 4.5 and a Sonnet-tier model, with the finalized transcription prompt, and
capture the real output text plus real token usage for each. This replaces
estimated OCR cost numbers with measured ones, and gives the user (a native Gojri
speaker, currently hand-correcting the gold set) real model outputs to judge quality
against, once corrections are done.

This is NOT the full 14,550-page Stage 1 run. It's a 12-page test batch to decide
whether Haiku is good enough, or whether a hybrid/Sonnet approach is needed, before
any bulk spend happens.

## The prompt
Use `prompts/ocr_transcription_v1.txt` **verbatim**, as the text content sent
alongside each image. Do not paraphrase or shorten it — it encodes multiple
hard-won corrections (numeral preservation, spread/column reading order, the
Gojri-vs-Urdu normalization warning, etc.), each backed by a real example found in
this project. Read it before running anything so you understand why each rule
exists.

## The images to process
List is in `data/gold/candidates.csv`. All 12 images there need this test
(`check_type == vision_ocr`): `dict_alif`, `kahawat_kosh`, `gojri_adbiyaat`,
`gojri_ghazal`, `mahatma_gandhi`, `kulyate_spread_a_right`,
`kulyate_spread_b_left`, `nazir_spread_a_right`, `nazir_spread_b_left`,
`louk_warsti`, `shingar_textbook`, `primer_pehli`. Direct-extraction pages
(`hindi_dict`, `quran_translation`) are not in the gold image folders.

Images for OCR calls are at `data/gold/images_cropped/{id}.png` (zoom 2).
`data/gold/images/` is the uncropped render, for comparison only.

**Ignore leftover `*_corrected.txt` names in old notes.** Gold is now one
`<page_id>_gold.txt` per folder. Raw model output is `*_original.txt` only.

## AWS Bedrock setup (already verified working this session)
- **Region: `us-east-1`.**
- Credentials are already configured on this machine (`aws configure` was run with
  a fresh IAM user, `ai_agent_user`, account `342374576774`, policy
  `AmazonBedrockFullAccess`). If running on the same machine/user profile, no
  further AWS setup is needed. If not, credentials need to be reconfigured.
- **Use `boto3` directly in Python rather than shelling out to the `aws` CLI.**
  This machine has two AWS CLI installs at different versions/paths (a PATH-order
  quirk, harmless but annoying), and boto3 sidesteps that entirely. Confirm boto3
  is installed (`py -3 -m pip show boto3`), install if not.
- **Use the `bedrock-runtime` client, not `bedrock`.** `bedrock` is for
  control-plane calls like listing models; `bedrock-runtime` is for actually
  invoking one, method `invoke_model`.
- **Model IDs must be inference-profile IDs, not bare model IDs**, for on-demand
  invocation of current-generation models. Verified working:
  - Haiku 4.5: `us.anthropic.claude-haiku-4-5-20251001-v1:0`
  - Sonnet: `us.anthropic.claude-sonnet-4-5-20250929-v1:0` (or
    `us.anthropic.claude-sonnet-4-6`, also confirmed working)
  - **Does NOT work yet**: `us.anthropic.claude-sonnet-5` — returns
    `AccessDeniedException`, not enabled for this account (likely needs a one-time
    console visit per Bedrock's new "first Anthropic invocation" flow). Not worth
    chasing for this task, the 4.5/4.6 Sonnet models are a perfectly good stand-in
    for a "capable, pricier tier" comparison point.
  - A bare model ID like `anthropic.claude-haiku-4-5-20251001-v1:0` (no `us.`
    prefix) fails with `ValidationException` telling you to use an inference
    profile instead — that error is expected and means "use the `us.` ID."

## Request format
Bedrock's Anthropic models use the standard Anthropic Messages API shape, just
invoked differently. Body needs `anthropic_version: "bedrock-2023-05-31"`:

```json
{
  "anthropic_version": "bedrock-2023-05-31",
  "max_tokens": 4096,
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "<base64 PNG bytes>"}},
        {"type": "text", "text": "<the full contents of prompts/ocr_transcription_v1.txt>"}
      ]
    }
  ]
}
```

`max_tokens: 4096` is a reasonable ceiling — dense pages transcribe to roughly
1,000-1,500 tokens per the earlier estimate in `CLAUDE.md`, but leave headroom.

A minimal text-only call was already tested and confirmed working this session
(Haiku 4.5 and Sonnet 4.5/4.6 both returned clean responses with real `usage`
data). Image calls haven't been tested yet — that's this task.

## What to capture, per image, per model
The response JSON has a `usage` field: `input_tokens`, `output_tokens` (plus some
cache fields you can ignore for this). **Capture and log these, they are the whole
point of this exercise** — the earlier cost estimates in `CLAUDE.md`/`ROADMAP.md`
were already corrected once after being found to undercount by ~2x (they'd ignored
output tokens entirely), so getting real numbers here matters.

For each of the 12 images x 2 models (24 calls total):
1. Save the transcription text to `data/gold/images/{id}_{model_short_name}.txt`
   (e.g. `dict_alif_haiku_4.5.txt`, `dict_alif_sonnet_4.5.txt`).
2. Log `id, model, input_tokens, output_tokens` to a CSV, e.g.
   `data/gold/api_test_results.csv`.

## After the calls: cost extrapolation
Once you have real per-page token counts for both models, extrapolate to the real
Stage 1 workload (14,550 pages needing OCR, see `CLAUDE.md` for how that figure was
derived) using current Bedrock pricing for Haiku 4.5 and the Sonnet model you used.
Look up current pricing rather than reusing the older per-million-token figures
already in `CLAUDE.md`, since those were themselves estimates pending this exact
verification. Report the corrected total for both models.

## What this task does NOT include
- No quality scoring in that original test-batch task. Gold is now
  `transcriptions/<page>/<page>_gold.txt`. Score `*_original.txt` against it
  with `py -3 scripts/score_gold.py`. Provisional bulk model from that score:
  Gemini 3.6 Flash. Sonnet 4.6 is not the default.
- No bulk run across the full PDF collection. This is 12 pages only.
- No decision-making about which model to use for the bulk run was in the
  original 12-page Bedrock task. The   2026-08-15 gold bake-off now gives a
  ranking (Gemini 3.6 Flash best one-shot) and a stop: bulk vision OCR is paused.
  Next is the decode-table spike, scored on the same gold pages.

## Report back
Once done: the 24 output files, the CSV of token usage, and the extrapolated cost
for both models against the real 14,550-page workload. Flag anything that
surprised you (unexpected errors, wildly different token counts between models,
truncated output, etc.) rather than silently working around it.
