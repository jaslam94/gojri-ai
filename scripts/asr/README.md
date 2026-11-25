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

## Files

| File | What it does |
|---|---|
| `prepare_cv_split.py` | Builds the split from the local Common Voice copy; `--upload` stages it on private S3. |
| `launch_whisper.py` | Starts the SageMaker job (`ml.g5.xlarge`, hard time cap). Needs `SAGEMAKER_ROLE_ARN`. |
| `transcribe.py` | Runs the trained model on your own audio (any format, CPU only). Needs the unpacked `model.tar.gz` of the job and `pip install transformers torch av numpy`. |
| `sm_whisper/sm_whisper_entry.py` | The job: zero-shot Whisper score, fine-tune, score again; writes `results.json`, `test_predictions.tsv` and the model. |

Scoring: word error (WER) and character error (CER) after one normalisation on both sides (NFC, combining marks and
punctuation removed, ك=ک, ي=ی, ه=ہ, ھ separate). Whisper has no Gojri token; the Urdu token is used.
