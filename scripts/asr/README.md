# ASR baseline: Whisper on Common Voice Gujari

Data: Common Voice Scripted Speech 26.0, Gujari (CC0; Common Voice terms forbid re-hosting, so the audio and the
sentence text stay out of this repository and on private S3 only).

## The split

The official split has one training speaker (3,207 clips, 2.9 h), an empty dev set and five test speakers. To use the
other validated clips, `prepare_cv_split.py` keeps the official `test.tsv` and trains on every validated clip whose
sentence is not a test sentence:

| Split | Clips | Speakers |
|---|---|---|
| train | 9,041 | S1, S3, S5 |
| dev (5% of the training sentences, seed 20261120) | 475 | S1, S3, S5 |
| test (official) | 623 | S1 (4), S2 (101), S3 (385), S4 (1), S6 (132) |

The test set shares no identical sentence with training. After the scorer's normalisation, 4 of the 623 test clips (0.6%)
have the same text as a training clip: 3 from S6 (not in training) and 1 from S3. Two test speakers (S1, S3, 389 clips) also read training sentences; three
(S2, S4, S6, 234 clips) never appear in training. Results are reported for both groups; the unseen-speaker number is
the honest one. `data/asr/split_clips.tsv` (tracked) lists clip, split and speaker label, so the split can be rebuilt
from a Common Voice download.

## Results (2026-11-20)

Job `gojri-asr-whisper-2026-11-20-17-43-55-757` (`ml.g5.xlarge`, 2,248 billable seconds): Whisper-small, 2,500 steps,
batch 16, learning rate 1e-5, warm-up 300, dev check every 500 steps; the best dev checkpoint (step 1,500, dev word
error 18.9%) was kept.

| Test set | Clips | Word error | Character error |
|---|---|---|---|
| No fine-tune (zero-shot, Urdu token) | 623 | 73.8% | 33.2% |
| Fine-tuned, all | 623 | **22.7%** | 8.3% |
| Fine-tuned, speakers seen in training (S1, S3) | 389 | 23.4% | 8.5% |
| Fine-tuned, speakers never in training (S2, S4, S6) | 234 | 21.6% | 8.1% |

Dev word error by step: 23.2% (500), 20.9% (1,000), 18.9% (1,500), 19.3% (2,000), 20.8% (2,500). One run, one seed.
The numbers come from `results.json` of the job (copy: `data/asr/results_whisper-small_2026-11-20.json`); the
per-clip predictions hold Common Voice sentence text and stay local.

## Whisper-medium (2026-11-25)

Job `gojri-asr-whisper-medium-2026-11-25-13-46-21-607` (`ml.g5.xlarge`, 8,539 billable seconds, about $3.4 by the cost of the earlier jobs): same data,
split and scorer as the small run. Whisper-medium (769M), batch 8 x 2 accumulation (effective 16), gradient checkpointing,
learning rate 1e-5, warm-up 300, 2,500 steps, dev check every 250; the best dev checkpoint (step 1,750, dev word error 15.4%)
was kept. One run, one seed.

| Test set | Clips | Word error small | Word error medium | Character error small | Character error medium |
|---|---|---|---|---|---|
| No fine-tune (zero-shot, Urdu token) | 623 | 73.8% | 72.7% | 33.2% | 34.6% |
| Fine-tuned, all | 623 | 22.7% | **18.3%** | 8.3% | **6.9%** |
| Fine-tuned, speakers seen in training (S1, S3) | 389 | 23.4% | 18.2% | 8.5% | 6.4% |
| Fine-tuned, speakers never in training (S2, S4, S6) | 234 | 21.6% | 18.5% | 8.1% | 7.6% |

Dev word error by step: 27.1% (250), 18.7% (500), 19.0% (750), 18.4% (1,000), 18.4% (1,250), 18.2% (1,500), 15.4% (1,750),
17.0% (2,000), 15.9% (2,250), 15.6% (2,500). The curve is noisy and was still near its low at the end; small had its best
point at 1,500 and got worse after. Results file: `data/asr/results_whisper-medium_2026-11-25.json`.

## Meta Omnilingual ASR, zero-shot (2026-11-25)

No training on our data. Same 623 test clips and same scorer. Language tag `gju_Arab` (Gojri, Arabic script) where the model takes one.
Code: `launch_omni.py`, `sm_omni/omni_entry.py`. Result file: `data/asr/results_omniasr_zero-shot_2026-11-25.json`. Predictions stay local (they hold Common Voice text).

| Model | Word error | Character error | Seen speakers | Unseen speakers |
|---|---|---|---|---|
| Omnilingual LLM-300M (`gju_Arab`) | 14.9% | 5.4% | 15.5% | 14.1% |
| Omnilingual LLM-1B (`gju_Arab`) | 13.4% | 4.6% | 13.8% | 12.7% |
| Omnilingual LLM-3B (`gju_Arab`) | 12.2% | 4.2% | 12.8% | 11.2% |
| **Omnilingual LLM-7B (`gju_Arab`)** | **9.9%** | **3.15%** | 10.0% | 9.6% |
| Omnilingual LLM-7B (`urd_Arab`, control) | 10.5% | 3.4% | 10.8% | 10.0% |
| Omnilingual LLM-7B (no language tag) | 9.9% | 3.1% | 10.0% | 9.6% |
| Omnilingual CTC-1B | 42.4% | 14.1% | 43.2% | 41.1% |
| (Whisper-small, fine-tuned) | 22.7% | 8.3% | 23.4% | 21.6% |
| (Whisper-medium, fine-tuned) | 18.3% | 6.9% | 18.2% | 18.5% |

Error falls with size. The language tag changes little (7B: 9.9% with `gju_Arab` or no tag, 10.5% with the Urdu tag). The CTC model is poor on Gojri.
**Limit:** Meta may have trained on these public Common Voice clips; I could not check. Treat the numbers as an upper bound on quality until a recording that no
dataset holds (a speaker's own voice) is scored. Jobs: 17-57-37 (300M, 1B; the 3B step ran out of host memory on `ml.g5.xlarge`) and 18-32-10 (`ml.g5.4xlarge`, 64 GB).
Versions: the PyPI release names the cards `omniASR_*` and `omniASR_*_v2`; the `_v2` names were not known inside the job, so only the first versions were tested.

## Files

| File | What it does |
|---|---|
| `prepare_cv_split.py` | Builds the split from the local Common Voice copy; `--upload` stages it on private S3. |
| `launch_whisper.py` | Starts the SageMaker job (`ml.g5.xlarge`, hard time cap). Needs `SAGEMAKER_ROLE_ARN`. |
| `launch_omni.py` / `sm_omni/omni_entry.py` | Zero-shot test of Omnilingual ASR on the test set (SageMaker, PyTorch 2.8; reinstalls the CUDA 12.8 build of torch that fairseq2 needs; writes errors to `results.json`). |
| `launch_omni_ft.py` / `sm_omni_ft/omni_ft_entry.py` | Fine-tunes Omnilingual ASR (LLM family) with Meta's recipe on `ml.g5.12xlarge` (4 x A10G), scores every saved checkpoint on dev with our scorer, then the best one on test. Checkpoints go to private S3. |
| `omni_ft/make_parquet.py` | Converts our split (train, dev, test) to the parquet layout of the Omnilingual training recipe (flac 16 kHz, text, sample count) plus summary TSV and dataset card. Plan: `plans/PLAN-omnilingual-finetune-20261126.md`. |
| `transcribe.py` | Runs the trained model on your own audio (any format, CPU only). Needs the unpacked `model.tar.gz` of the job and `pip install transformers torch av numpy`. |
| `sm_whisper/sm_whisper_entry.py` | The job: zero-shot Whisper score, fine-tune, score again; writes `results.json`, `test_predictions.tsv` and the model. |

Scoring: word error (WER) and character error (CER) after one normalisation on both sides (NFC, combining marks and
punctuation removed, ك=ک, ي=ی, ه=ہ, ھ separate). Whisper has no Gojri token; the Urdu token is used.
