# Speech recognition (ASR) on Common Voice Gujari

## Where we are (2026-11-28)

All rows: the same 623 test clips and the same scorer. One run and one seed per fine-tune.

| Model | Trained on our data | Word error | Character error | Unseen speakers, word error |
|---|---|---|---|---|
| **Omnilingual LLM-7B** | no | **9.9%** | **3.15%** | **9.6%** |
| Omnilingual LLM-3B | no | 12.2% | 4.2% | 11.2% |
| Omnilingual LLM-1B | yes | 12.5% | 4.1% | 12.1% |
| Omnilingual LLM-1B | no | 13.4% | 4.6% | 12.7% |
| Omnilingual LLM-300M | no | 14.9% | 5.4% | 14.1% |
| Whisper-medium | yes | 18.3% | 6.9% | 18.5% |
| Whisper-small | yes | 22.7% | 8.3% | 21.6% |
| Omnilingual CTC-1B | no | 42.4% | 14.1% | 41.1% |

The test set is read-aloud book text. A test on recordings that no dataset holds is ready and not yet run (see "Own-voice
test").

## Overlap with Meta's training data (checked 2026-11-28)

- Meta's paper (arXiv 2511.09690v1, section 3.3.1) lists **Common Voice v22** among its training datasets.
- Common Voice 22.0 has no Gujari. It first appears in **23.0** (September 2025). Checked in Mozilla's release metadata
  (`common-voice/cv-dataset`, `datasets/scripted-speech/`).
- Meta's released corpus `facebook/omnilingual-asr-corpus` has no `gju` folder.
- **Still open:** the paper also trains on a Common Voice speech fund (Open Multilingual Speech Fund), on internal data
  and on licensed data. We read no data source for Gujari in it, and no general removal of test clips from training. We
  did not read its full per-language appendix. So the test clips are not proven unseen.
- The same metadata lists 11,741 Gujari clips in releases 23.0, 26.0 and 27.0. Release 27.0 has the same clips, hours
  and validated sentences as our 26.0: there is no new Common Voice data to add.

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
**Limit:** overlap with Meta's training data is not ruled out (see the overlap section above). Treat the numbers as an upper bound on quality until a recording that no
dataset holds (a speaker's own voice) is scored. Jobs: 17-57-37 (300M, 1B; the 3B step ran out of host memory on `ml.g5.xlarge`) and 18-32-10 (`ml.g5.4xlarge`, 64 GB).
Versions: the PyPI release names the cards `omniASR_*` and `omniASR_*_v2`; the `_v2` names were not known inside the job, so only the first versions were tested.

## Omnilingual LLM-1B fine-tuned on our data (2026-11-26)

Job `gojri-asr-omni-ft-1b-2026-11-26-12-33-47-861` (`ml.g5.12xlarge`, 4 x A10G; 9,363 billable seconds, $18.44 at the billed $7.09 per hour; with the four smoke tests $25.93). Meta's own recipe (tag 0.2.0, fairseq2 0.6.0), learning rate 5e-05,
400 steps, checkpoint every 80 steps. Training saw 33,746 examples (3.73 passes over the 9,041 clips, 30.7 hours of audio), 17.4 seconds per step.
Labels: our sentences without punctuation and without the characters the tokenizer cannot write (short vowel marks and a few symbols; the scorer ignores marks).
Code: `launch_omni_ft.py`, `sm_omni_ft/omni_ft_entry.py`, `omni_ft/make_parquet.py`. Result file: `data/asr/results_omniasr_finetune-1b_2026-11-26.json`.

Dev word error by saved checkpoint (475 clips, our scorer): 13.95% (step 80), 13.49% (160), 13.80% (240), 13.58% (320), **13.03% (400, chosen)**.
The training loss fell from 0.187 (step 10) to 0.005 (step 400) while the dev error moved by less than one point.

| Test set (623 clips) | Word error | Character error | Seen speakers | Unseen speakers |
|---|---|---|---|---|
| **LLM-1B fine-tuned (step 400)** | **12.5%** | 4.06% | 12.8% | 12.1% |
| LLM-1B, no training | 13.4% | 4.6% | 13.8% | 12.7% |
| LLM-7B, no training | 9.9% | 3.15% | 10.0% | 9.6% |
| Whisper-medium, fine-tuned | 18.3% | 6.9% | 18.2% | 18.5% |

Fine-tuning gained 0.85 points of word error (6% fewer errors) over the same model without training. The fine-tuned 1B model is 5.8 points better than fine-tuned Whisper-medium and
2.7 points worse than the 7B model with no training. One run, one seed.
Error analysis on the saved predictions (local, not published): the 7B model with no training makes 419 word errors in 4,249 words (306 substitutions, 66 deletions, 47 insertions), 391 of 623 sentences
are exactly right; the fine-tuned 1B model makes 532 (414, 70, 48), 336 sentences exactly right. Of the eight most frequent word substitutions of the 7B model, most are spelling variants of one word (for example `ان` and `انھ`, `بی` and `بھی`,
`اتوں` and `اتو`); I did not classify all of them. Gojri has no standard spelling, so part of the error comes from the reference text.
Why the gain is small, as far as the numbers show: the training loss went to nearly zero, so the model fits the 3,852 book sentences, while the dev sentences are new text. More steps on this data are
unlikely to help; more varied text and speakers would. The 7B model does not fit full fine-tuning on this machine (about 125 GB by the estimate in the plan; the machine has 96 GB).

## Whisper large-v3 with LoRA (built, not run)

`sm_whisper_entry.py --lora 1` trains small adapter layers on a frozen large-v3 model, so it fits one 24 GB GPU. The
first smoke test crashed in the dev check (a number format mismatch); the fix is in. The second smoke test ran the whole
chain, including the merge and the save of the model; its scores were not read. The full run is not started.

## Own-voice test (ready, 2026-11-28)

`voice_test.py` scores Omnilingual LLM-7B, LLM-1B and the fine-tuned LLM-1B (checkpoint step 400 on private S3) on your
own recordings. Run from the repository root:

1. Write 20 to 30 short Gojri sentences that are not in Common Voice. Record one file per sentence (`01.m4a`, `02.m4a`,
   ...), each under 40 seconds, into `local/voice-test/audio/`.
2. `py -3 -X utf8 scripts/asr/voice_test.py sheet` makes `local/voice-test/sheet.tsv`. Type what you said **before** you
   see any model output.
3. `py -3 -X utf8 scripts/asr/voice_test.py launch` (needs `SAGEMAKER_ROLE_ARN`; `ml.g5.4xlarge`).
4. `... voice_test.py fetch <job name>`, then `... voice_test.py score` (`--show` prints every sentence).

Smoke test on 4 Common Voice clips (job `gojri-asr-voice-2026-11-28-07-09-54-865`, 817 billable seconds, about $0.46 at
$2.03 per hour): 12 of 12 outputs identical to the earlier jobs. This checks the pipeline; it is not a result. A few
sentences from one speaker will be a strong hint, not an error rate.

## Whisper-small error check (2026-11-23 to 2026-11-24)

`docs/asr_performance_check.md`: the score reproduces from the saved model and audio; about 10% of the word errors are
spacing only; Claude labelled 50 sampled substitutions and the speaker has not checked the labels.

## Files

| File | What it does |
|---|---|
| `prepare_cv_split.py` | Builds the split from the local Common Voice copy; `--upload` stages it on private S3. |
| `launch_whisper.py` | Starts the SageMaker job (`ml.g5.xlarge`, hard time cap). Needs `SAGEMAKER_ROLE_ARN`. |
| `launch_omni.py` / `sm_omni/omni_entry.py` | Zero-shot test of Omnilingual ASR on the test set (SageMaker, PyTorch 2.8; reinstalls the CUDA 12.8 build of torch that fairseq2 needs; writes errors to `results.json`). |
| `launch_omni_ft.py` / `sm_omni_ft/omni_ft_entry.py` | Fine-tunes Omnilingual ASR (LLM family) with Meta's recipe on `ml.g5.12xlarge` (4 x A10G), scores every saved checkpoint on dev with our scorer, then the best one on test. Checkpoints go to private S3. |
| `omni_ft/make_parquet.py` | Converts our split (train, dev, test) to the parquet layout of the Omnilingual training recipe (flac 16 kHz, text, sample count) plus summary TSV and dataset card. Plan: `plans/PLAN-omnilingual-finetune-20261126.md`. |
| `voice_test.py` / `sm_voice/voice_entry.py` | Own-voice test: makes the sheet for the speaker's text, runs the fine-tuned and zero-shot Omnilingual models on the recordings (SageMaker `ml.g5.4xlarge`), downloads the outputs and scores each model. Files stay in `local/voice-test/`. |
| `perf_check/asrlib.py` | Scoring shared by the local checks (a copy of the job's rules). |
| `perf_check/transcribe.py`, `step3_rescore.py`, `step5_analyse.py` | Whisper-small check: run the saved model on the CPU, re-score the saved predictions, analyse the errors. |
| `perf_check/build_label_review.py` | Page where the speaker checks the 50 hand-labelled errors, and the comparison with the draft labels. |
| `perf_check/step6_ownvoice.py`, `demo_app.py` | Own-voice sheet and score for Whisper-small; local Gradio demo (not deployed). |
| `transcribe.py` | Runs the trained model on your own audio (any format, CPU only). Needs the unpacked `model.tar.gz` of the job and `pip install transformers torch av numpy`. |
| `sm_whisper/sm_whisper_entry.py` | The job: zero-shot Whisper score, fine-tune, score again; writes `results.json`, `test_predictions.tsv` and the model. |

Scoring: word error (WER) and character error (CER) after one normalisation on both sides (NFC, combining marks and
punctuation removed, ك=ک, ي=ی, ه=ہ, ھ separate). Whisper has no Gojri token; the Urdu token is used.
