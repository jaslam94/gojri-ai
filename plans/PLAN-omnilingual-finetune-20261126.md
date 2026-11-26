# Plan: fine-tune Meta Omnilingual ASR on Common Voice Gujari (2026-11-26)

Goal: score below the zero-shot Omnilingual LLM-7B (9.9% word error) on the 623 Common Voice test clips, with the same scorer.
Then test on a recording from outside Common Voice (the speaker will make one).
Marks: VERIFIED = read in the repository `facebookresearch/omnilingual-asr` or in our files this session. MY ARITHMETIC = computed from verified numbers, not tested. UNKNOWN = not checked.

## What the repository gives us (VERIFIED)
- A training recipe for fairseq2: `python -m workflows.recipes.wav2vec2.asr $OUTPUT_DIR --config-file <yaml>`. It lives in the repository, not in the pip package, so the job must clone the repository.
- `configs/llm-finetune.yaml` trains an LLM model from an LLM checkpoint. Its defaults: model `omniASR_LLM_1B`, tokenizer `omniASR_tokenizer_v1`, learning rate 5e-05, FSDP data parallelism, bfloat16, gradient accumulation 4, 20,000 steps, `max_audio_len` 320,000 samples (20 s at 16 kHz).
- Meta's README says its own CTC fine-tunes used 32 GPUs (300M), 64 (1B) and 96 (3B). Our data is far smaller; the settings must be re-chosen on a smoke test.
- Data format: parquet, partitioned `version=0/corpus=<name>/split=<train|dev|test>/language=<code>/part-*.parquet`, `row_group_size=100`. Columns: `text` (string), `audio_bytes` (list of int8; flac or ogg, 16 kHz mono), `audio_size` (samples), `corpus`, `split`, `language` (`gju_Arab`).
- A summary TSV (`dataset_summary_path`): columns `corpus`, `language`, `hours` (hours = sum of `audio_size` / 3600 / 16,000), written by `compute_stats` in `workflows/dataprep/hf_dataset_ingestion_example.py`.
- A dataset card (YAML asset): `name`, `dataset_family: mixture_parquet_asr_dataset`, `dataset_config: {data: <path to version=0>}`, `tokenizer_ref`.
- Tokenizers: `omniASR_tokenizer_v1` for the first-version models except the 7B LLM; `omniASR_tokenizer_v1_variant7` for the 7B LLM architecture (README table).

## Model sizes (VERIFIED, README table)
| Model | Parameters | Download (FP32) |
|---|---|---|
| LLM-300M | 1,627,603,584 | 6.1 GiB |
| LLM-1B | 2,275,710,592 | 8.5 GiB |
| LLM-3B | 4,376,679,040 | 17.0 GiB |
| LLM-7B | 7,801,041,536 | 30.0 GiB |

For comparison (Hugging Face model pages): Whisper-small 241,734,912; Whisper-medium 763,857,920; Whisper-large-v3 1,543,490,560. Omnilingual LLM-7B has about 5.1 times the parameters of Whisper-large-v3 and 10.2 times those of Whisper-medium (MY ARITHMETIC).

## GPU memory (MY ARITHMETIC, not tested)
Full fine-tuning with fp32 master weights, gradients and AdamW needs about 16 bytes per parameter before activations: LLM-1B about 36 GB, LLM-3B about 70 GB, LLM-7B about 125 GB.
- `ml.g5.xlarge`, `2xlarge`, `4xlarge`: one 24 GB GPU. Not enough for any of these.
- `ml.g5.12xlarge`: four 24 GB GPUs (96 GB), quota 1 (VERIFIED in Service Quotas). FSDP can shard LLM-1B comfortably; LLM-3B is tight; LLM-7B does not fit.
- `ml.g5.48xlarge` quota is 0. Other large types: UNKNOWN.
So LLM-1B is the first target. LLM-7B needs a larger instance or a parameter-efficient method; whether the recipe supports LoRA is UNKNOWN.
Price of `ml.g5.12xlarge` is not in our bill yet (rates so far: `g5.xlarge` $1.41, `2xlarge` $1.52, `4xlarge` $2.03 per hour). Check the price before launching.

## Steps
1. **Data (local, free).** `scripts/asr/omni_ft/make_parquet.py` converts `data/asr/splits/{train,dev,test}.tsv` (9,041 / 475 / 623 clips; the test split is for scoring only) to the parquet layout with `corpus=cv`, `language=gju_Arab`, flac at 16 kHz mono, plus the summary TSV and the dataset card. Text: NFC, punctuation removed, short vowel marks kept (the scorer removes marks on both sides, so they do not change the score).
2. **Upload** the parquet folder to private S3 (`s3://gojri-ai-sagemaker-data/asr/omni-ft/`). Common Voice terms forbid re-hosting; private S3 is the same practice as the Whisper runs.
3. **Smoke test** on `ml.g5.12xlarge`: LLM-1B, about 50 steps on a small subset. Measures memory, speed per step and whether the recipe runs end to end. Writes errors to the output folder (the AWS user cannot read job logs).
4. **Real run**: LLM-1B on all of train. Steps, batch size and learning rate are set after the smoke test; no number is promised here.
5. **Score** the checkpoint with the same scorer on the 623 test clips, as `scripts/asr/sm_omni/omni_entry.py` does for zero-shot models.
6. **Compare** with the same-size zero-shot model (LLM-1B: 13.4%) to measure the gain from fine-tuning, and with LLM-7B zero-shot (9.9%) to decide whether to scale up.

## Risks
- Only 3 training speakers and book-style text; the model may learn the sentence pool. The unseen-speaker split in the score guards speakers, not text.
- Meta may have trained on these public clips (not checked), so the zero-shot baseline and the gain from fine-tuning are both unclear until a recording from outside Common Voice is scored.
- fairseq2 0.6 needs the CUDA 12.8 build of PyTorch 2.8.0; the SageMaker image ships the CUDA 12.9 build. `omni_entry.py` already reinstalls it.
- Our first fine-tune may run into recipe details only the smoke test shows (checkpoint format, asset card for a local checkpoint). Each failure of that kind costs a short job.

## Decisions needed
- Spend limit for the `ml.g5.12xlarge` smoke test and the first run.
- Label text: keep short vowel marks (proposed) or strip them.
