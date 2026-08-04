# Handoff: Run the real OCR test batch via AWS Bedrock

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
List is in `data/gold/candidates.csv`. Of the 14 images there:
- **12 need this test** (`check_type == vision_ocr`): `dict_alif`, `kahawat_kosh`,
  `gojri_adbiyaat`, `gojri_ghazal`, `mahatma_gandhi`, `kulyate_spread_a_right`,
  `kulyate_spread_b_left`, `nazir_spread_a_right`, `nazir_spread_b_left`,
  `louk_warsti`, `shingar_textbook`, `primer_pehli`.
- **2 do NOT need this test** (`check_type == direct_extraction`): `hindi_dict`,
  `quran_translation`. These are already correct Unicode text pulled directly from
  the PDF, not vision OCR candidates. Skip them.

Images are at `data/gold/images/{id}.png`, already rendered at the correct zoom
level (zoom 2 — do not re-render at a different zoom, zoom 3 was tested and
confirmed to waste tokens for no quality gain, see `CLAUDE.md`).

**Ignore any `*_gemini_3.6_flash.txt`, `*_sonnet_5_original.txt`, or
`*_sonnet_5_corrected.txt` / `*_corrected.txt` files already sitting next to
`dict_alif` and `gojri_adbiyaat`.** Those were produced with an earlier, less
complete version of the prompt before this session's guardrail additions. They are
not representative of what v1 will produce and should not be treated as already-done
work. Regenerate both of those two pages fresh under v1 like the other 10.

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
- No quality scoring yet (character error rate against the gold set) — the user is
  still hand-correcting the gold set's draft transcriptions. That comparison happens
  once corrections are done; don't build a scorer as part of this task unless asked.
- No bulk run across the full PDF collection. This is 12 pages only.
- No decision-making about which model to use for the bulk run — that's a
  conversation to have with the user once real cost and (later) real quality numbers
  exist for both.

## Report back
Once done: the 24 output files, the CSV of token usage, and the extrapolated cost
for both models against the real 14,550-page workload. Flag anything that
surprised you (unexpected errors, wildly different token counts between models,
truncated output, etc.) rather than silently working around it.
