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

The test set shares no sentence with training. Two test speakers (S1, S3, 389 clips) also read training sentences; three
(S2, S4, S6, 234 clips) never appear in training. Results are reported for both groups; the unseen-speaker number is
the honest one. `data/asr/split_clips.tsv` (tracked) lists clip, split and speaker label, so the split can be rebuilt
from a Common Voice download.

## Files

| File | What it does |
|---|---|
| `prepare_cv_split.py` | Builds the split from the local Common Voice copy; `--upload` stages it on private S3. |
| `launch_whisper.py` | Starts the SageMaker job (`ml.g5.xlarge`, hard time cap). Needs `SAGEMAKER_ROLE_ARN`. |
| `sm_whisper/sm_whisper_entry.py` | The job: zero-shot Whisper score, fine-tune, score again; writes `results.json`, `test_predictions.tsv` and the model. |

Scoring: word error (WER) and character error (CER) after one normalisation on both sides (NFC, combining marks and
punctuation removed, ك=ک, ي=ی, ه=ہ, ھ separate). Whisper has no Gojri token; the Urdu token is used.
