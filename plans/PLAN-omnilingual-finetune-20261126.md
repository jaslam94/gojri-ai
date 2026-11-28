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
Billed price (read 2026-11-28): `ml.g5.12xlarge` $7.09 per hour (`g5.xlarge` $1.41, `2xlarge` $1.52, `4xlarge` $2.03). The fine-tune cost $25.93 in all: the real run 9,363 s ($18.44), the four smoke tests 3,803 s ($7.49).

## Steps
1. **Data (local, free).** `scripts/asr/omni_ft/make_parquet.py` converts `data/asr/splits/{train,dev,test}.tsv` (9,041 / 475 / 623 clips; the test split is for scoring only) to the parquet layout with `corpus=cv`, `language=gju_Arab`, flac at 16 kHz mono, plus the summary TSV and the dataset card. Text: NFC, punctuation removed, short vowel marks kept (the scorer removes marks on both sides, so they do not change the score).
2. **Upload** the parquet folder to private S3 (`s3://gojri-ai-sagemaker-data/asr/omni-ft/`). Common Voice terms forbid re-hosting; private S3 is the same practice as the Whisper runs.
3. **Smoke test** on `ml.g5.12xlarge`: LLM-1B, about 50 steps on a small subset. Measures memory, speed per step and whether the recipe runs end to end. Writes errors to the output folder (the AWS user cannot read job logs).
4. **Real run**: LLM-1B on all of train. Steps, batch size and learning rate are set after the smoke test; no number is promised here.
5. **Score** the checkpoint with the same scorer on the 623 test clips, as `scripts/asr/sm_omni/omni_entry.py` does for zero-shot models.
6. **Compare** with the same-size zero-shot model (LLM-1B: 13.4%) to measure the gain from fine-tuning, and with LLM-7B zero-shot (9.9%) to decide whether to scale up.

## Risks
- Only 3 training speakers and book-style text; the model may learn the sentence pool. The unseen-speaker split in the score guards speakers, not text.
- Meta may have trained on these clips, so the zero-shot baseline and the gain from fine-tuning are both unclear until a recording from outside Common Voice is scored. (Checked 2026-11-28: the paper's Common Voice v22 holds no Gujari, which first appears in 23.0; its other sources are not ruled out. See `scripts/asr/README.md`.)
- fairseq2 0.6 needs the CUDA 12.8 build of PyTorch 2.8.0; the SageMaker image ships the CUDA 12.9 build. `omni_entry.py` already reinstalls it.
- Our first fine-tune may run into recipe details only the smoke test shows (checkpoint format, asset card for a local checkpoint). Each failure of that kind costs a short job.

## Status (2026-11-26) and changes made while building
Decided by the speaker: Omnilingual is the base for now; spend is approved; LLM-1B first.
- **Label text: marks stripped, not kept.** Check of `omniASR_tokenizer_v1` against our labels: 2.35% of the label characters (damma, kasra, fatha, shadda, sukun, tatweel and a few symbols) are unknown to it (253,849 characters checked in the training labels). `make_parquet.py --tokenizer` now drops every character the tokenizer cannot represent. Dropped over all splits: U+064F 3,546; U+0650 1,741; U+064E 1,290; U+FDFA 37; U+0640 27; U+0651 18; U+0656 12; U+0652 3; U+060E 3. The scorer removes marks on both sides, so the score is not affected, except for the 37 U+FDFA and 27 tatweel characters, which the model cannot write. After filtering: 0 unknown characters, 0 empty labels. Data: train 9,041 clips (8.20 h), dev 475 (0.43 h), test 623 (0.52 h).
- **No validation inside training.** The recipe validates by gathering the full model on every GPU (`summon_full_parameters`). On 22 GB cards this ran out of memory (smoke test 1, rank 3, at step 10; peak active memory in training was 20.02 GiB of 22.06). fairseq2 also validates once at the end of training whenever a validation reader exists, so the config sets `dataset.valid_split: null` (the recipe builds no validator then; checked in `recipe.py` at tag 0.2.0) and `regime.score_metric: null`. The job scores every saved checkpoint on dev itself with our scorer and picks the lowest dev word error.
- **Micro-batch size.** Halving it (10 s of audio per GPU, accumulation 8) did not lower peak memory (19.64 GiB) and doubled the step time (33.7 s against 18.1 s per step; the 4 GPUs share no fast link, so each extra micro-batch costs a parameter gather). Kept: 20 s per GPU (320,000 samples), accumulation 4, `PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True`.
- **Checkpoint choice.** fairseq2 stores the validation score so that higher is better (negated word error). With our own dev scoring this no longer matters; recorded here because a first version of the job picked the lowest stored score, which would have been the worst checkpoint.
- **Checkpoints reload.** fairseq2 writes `step_N/model/pp_00/tp_00/sdp_XX.pt` shards and reshards them when a card with `base: <model card>` and `checkpoint: <dir>` is loaded (smoke test 4: both checkpoints loaded and scored).
- **Smoke tests (all `ml.g5.12xlarge`).** 1: ran 10 steps, out of memory in validation. 2: checkpoints saved, crash in the end-of-training validation. 3: clean training (exit code 0, 20 steps in 403 s), scoring failed on a Python path problem (editable install invisible to the running interpreter). 4: whole chain passed; on 32 clips only (a pipeline check, not a result): dev word error 11.32% at step 10, 8.96% at step 20; test 13.92% for the step-20 checkpoint.
- **Real run.** Job `gojri-asr-omni-ft-1b-2026-11-26-12-33-47-861`: LLM-1B, learning rate 5e-05, 400 steps (about 4 passes over the training data), checkpoint every 80 steps, checkpoints uploaded to private S3 (`asr/omni-ft/out/<job>/`). Result file: `data/asr/results_omniasr_finetune-1b_2026-11-26.json`.
- **Result.** Test word error 12.52% (character error 4.06%; seen speakers 12.82%, unseen 12.06%); the same model without training: 13.37%. Dev word error by checkpoint: 13.95 (80), 13.49 (160), 13.80 (240), 13.58 (320), 13.03 (400, chosen). Training loss 0.187 to 0.005. Gain over no training: 0.85 points; LLM-7B without training (9.86%) is still better. Conclusion: with this data, full fine-tuning of the 1B model adds little; the bottleneck is data variety (3,852 sentences, 3 training speakers), not steps.

## Decisions still open
- Whether to scale up (LLM-3B needs about 70 GB for full fine-tuning by the estimate above; LLM-7B does not fit on `ml.g5.12xlarge`) after the LLM-1B result.
