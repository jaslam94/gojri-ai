# ASR performance check: Gojri Whisper-small

Date: 2026-11-23 and 2026-11-24. Model: `openai/whisper-small`, fine-tuned on Common Voice Scripted Speech 26.0, Gujari
(job `gojri-asr-whisper-2026-11-20-17-43-55-757`, details in `scripts/asr/README.md`).

This check trains nothing and uploads nothing. Audio, sentence text and per-clip predictions stay on the local PC.
Code is in `scripts/asr/perf_check/`.

## Result in short

| Question | Answer |
|---|---|
| Does the reported number reproduce from the saved predictions? | Yes: 22.66% word error (all), 23.38% (seen), 21.57% (unseen). |
| Does it reproduce from the model and the audio? | Yes, within 0.04 points: 22.62% (all). 615 of 623 clips give identical text. |
| What is in the errors? | About 10% of all errors are spacing only. About half of the sampled word substitutions are real errors. No empty or looping output. |
| Own-voice test | **Not done.** It needs JD to record sentences (step 6 below). |
| Safe claim | Word error near 22% on read-aloud Common Voice sentences from the same books as training. Nothing is shown for free speech. |

## What was run

| Item | Value |
|---|---|
| Hardware | Intel Core i7-1165G7 (4 cores, 8 threads), 15.7 GB RAM, Windows 10. No GPU: all runs used the CPU. |
| Software | Python 3.10.5, torch 2.14.1+cpu, torchaudio 2.11.1+cpu, transformers 4.46.3, jiwer 3.0.4, accelerate 1.1.1, numpy 1.26.4, soundfile 0.14.0 (the job used 0.12.1), gradio 6.17.3 (demo only) |
| Model files | `model.tar.gz` from S3 (425.6 MiB). The copy in `data/asr/output/` is byte-identical (same SHA-256). Weights are fp16 on disk; the run loads them as fp32. |
| Test data | The official `test.tsv` (623 clips) from the local Common Voice copy, with the speaker labels of `data/asr/splits/test.tsv`. The sentences equal the job's `test_predictions.tsv` for all 623 clips. The S3 test copy was not downloaded: it is the same files. |
| Decoding | Language `urdu`, task `transcribe`, `max_new_tokens=128`, greedy search, batch 16. Same as the job. |
| Scoring | The rule of the job, copied into `scripts/asr/perf_check/asrlib.py`: NFC, combining marks and punctuation removed, ك to ک, ي to ی, ه to ہ, ھ kept apart, spaces collapsed. Same rule on both sides. |
| Run time | 30 min for 623 clips on the CPU. |

## Step 3 and 4: the numbers reproduce

| Source | All (623) | Seen speakers (389) | Unseen speakers (234) | Character error (all) |
|---|---|---|---|---|
| Job `results.json` | 22.7% | 23.4% | 21.6% | 8.3% |
| Re-score of the saved predictions | 22.66% | 23.38% | 21.57% | 8.34% |
| New run on the audio | 22.62% | 23.34% | 21.51% | 8.33% |

The new run differs from the job on 8 of 623 clips. The likely cause is fp16 rounding of the saved weights. The
difference is 0.04 points.

Clip-level 95% intervals (bootstrap, 2,000 resamples, job predictions): all 21.0 to 24.4; seen 21.4 to 25.5; unseen
18.9 to 24.4. The intervals resample clips, not speakers or sentences, so they are too narrow. Treat them as a minimum.

## Step 5: error analysis

Counts on the job predictions (4,249 reference words): 764 substitutions, 126 deletions, 73 insertions, 963 errors.
218 of 623 clips have no error. 142 clips have three or more. The new run gives nearly the same counts (763, 125, 73).

### Empty or looping output

| Check | Count |
|---|---|
| Empty output | 0 |
| Same word three or more times in a row, or output longer than twice the reference plus 3 words | 0 |
| Output five or more words longer than the reference | 0 |

### The reference text has spacing noise

The Common Voice sentences contain stray spaces inside words, for example a reference `یو ہ` against the model output
`یوہ`. The test references hold 69 one-letter tokens. The model output holds 35.

| Measure | Value |
|---|---|
| Error groups where reference and output are the same letters without spaces | 49 groups, 98 errors (10.2% of 963) |
| Word error if those groups counted as correct | 20.36% |
| Character error with spaces ignored | 8.74% (a lower base, so a higher percentage; not comparable with 8.34%) |

Word error counts a space difference as a full word error. Real quality is a little better than 22.7% on this measure.

### The 20 most frequent word errors

All 20 occur 3 to 6 times. They are 8.3% of all errors; there are 842 distinct error pairs. A long tail, not a few
repeated faults. Kind: sub = substitution, del = reference word missing in output, ins = extra output word.

| # | Kind | Reference | Output | Times |
|---|---|---|---|---|
| 1 | del | ں | (none) | 6 |
| 2 | sub | یو | یوہ | 5 |
| 3 | del | ہ | (none) | 5 |
| 4 | sub | جی | جے | 5 |
| 5 | del | گیا | (none) | 5 |
| 6 | del | ر | (none) | 5 |
| 7 | del | ا | (none) | 5 |
| 8 | ins | (none) | کے | 4 |
| 9 | sub | بی | بھی | 4 |
| 10 | ins | (none) | تیر | 4 |
| 11 | sub | ایو | آیو | 4 |
| 12 | sub | ان | انھ | 4 |
| 13 | sub | ہوے | ہووے | 3 |
| 14 | sub | ڈیرا | ڈیرے | 3 |
| 15 | sub | کے | کا | 3 |
| 16 | sub | تیرو | و | 3 |
| 17 | del | کے | (none) | 3 |
| 18 | del | اس | (none) | 3 |
| 19 | ins | (none) | کہیو | 3 |
| 20 | ins | (none) | ما | 3 |

Rows 1, 3, 6 and 7 are the spacing noise: a one-letter reference "word" that the model wrote inside the neighbouring word.
Rows 2, 9, 11, 12 and 13 look like spelling variants.

### Spelling variant or real error

Automatic check on all 764 substitutions: 48 (6.3%) are equal after folding closely related letters (ں/ن, ے/ی, ھ and
similar); 277 (36.3%) differ by one letter; 439 (57.5%) differ more. The one-letter group mixes variants and true
misses, so it cannot answer the question alone.

Hand labels on a random sample of 50 substitutions (seed 20261123), with one label each:

| Label | Count | Meaning |
|---|---|---|
| Real error | 25 | Wrong word or wrong letters |
| Reference spacing | 11 | A space inside the reference word, or two reference words glued |
| Spelling variant | 7 | Same word, other accepted spelling (for example وخت and وقت, صحیح and سہی, جنازا and جنازہ) |
| Unclear | 7 | Word-final nasal or vowel, or ب and پ; cannot decide without the audio |

**These labels are from Claude, not from a native Gojri speaker. JD must check them.** The sample is small: 25 of 50 has a
95% interval of about 36% to 64%. The sample holds substitutions only, which are 79% of all errors. The file with the
labels is local (`D:\asr-check\analysis_job\sample50_labelled.tsv`) because it holds Common Voice sentence text.

### By speaker, clip length and group

| Group | Clips | Word error |
|---|---|---|
| S3 (seen) | 385 | 23.6% |
| S2 (unseen) | 101 | 22.6% |
| S6 (unseen) | 132 | 20.8% |
| S1 (seen) | 4 | 9.1% (too few clips) |
| S4 (unseen) | 1 | 0.0% (one clip) |
| Short clips (under 2.3 s) | 202 | 24.6% |
| Medium (2.3 to 3.2 s) | 212 | 22.0% |
| Long (3.2 s and more) | 209 | 22.3% |
| 1 to 5 reference words | 271 | 24.7% |
| 6 to 9 reference words | 224 | 20.5% |
| 10 or more reference words | 128 | 23.6% |

Short clips are a little worse. The pattern is weak. Speakers are close, and the speaker groups are very uneven (see limits).

### Run without a forced language

Whisper with no forced language, saved config cleared: all 623 outputs are identical to the Urdu-token run (22.62%).
The model writes the Urdu language token `<|ur|>` for every clip checked (6 clips by token, 623 by output). The question
is closed: the fine-tuned model always picks Urdu by itself. The zero-shot base model with no forced language was not run.

## Step 6: own-voice test (not done)

JD must do this step. Claude cannot record speech or correct Gojri text.

1. Record 10 to 20 short Gojri sentences, one file each (phone or microphone, wav or mp3). Use sentences that are not in
   Common Voice. Put the files in one local folder outside the repo, for example `D:\asr-check\own_voice`.
2. Transcribe:
   `D:\asr-check\venv\Scripts\python.exe scripts\asr\perf_check\transcribe.py --model D:\asr-check\extract\model --audio-dir D:\asr-check\own_voice --out D:\asr-check\own_pred.tsv`
3. Make the sheet: `python scripts\asr\perf_check\step6_ownvoice.py sheet --pred D:\asr-check\own_pred.tsv --out D:\asr-check\own_sheet.tsv`
4. Open the sheet. In the column `corrected_text`, write what you said. Write it yourself, do not copy the model output.
5. Score: `python scripts\asr\perf_check\step6_ownvoice.py score --sheet D:\asr-check\own_sheet.tsv --cv-sentences datasets\cv-corpus-26.0-2026-06-12\gju\validated.tsv`
   The score step flags any sentence that is also in Common Voice.

Treat the result as an anecdote. 10 to 20 sentences from one speaker cannot give a rate.

## Step 7: local demo

`scripts/asr/perf_check/demo_app.py` is a Gradio app (record or upload, shows the Nastaliq output). It starts on
`127.0.0.1:7860` only, with no share link, and answers HTTP 200. Claude did not test a recording through the page.
Run: `D:\asr-check\venv\Scripts\python.exe scripts\asr\perf_check\demo_app.py --model D:\asr-check\extract\model`.
Not deployed.

## Limits

- One run, one seed, one model. The check ran the saved model; it did not train again.
- Training used three speakers (S1, S3, S5). The seen-speaker number is nearly one person: S3 gives 385 of 389 clips.
- The unseen-speaker number rests on two people in practice: S2 (101 clips) and S6 (132 clips). S4 has one clip. So
  "three speakers never in training" is true, but one of them is a single clip.
- The test set is read-aloud text. Common Voice says its 3,854 sentences come from Gojri story books, folk tales,
  Islamic studies and course books (65.6% short stories). A model that fits these books can score well and still fail
  on everyday speech. The own-voice test and a test on free speech are the only ways to learn this.
- Training and test sentences share no exact sentence, but the same books and the same words. 8.3% of test word
  tokens never occur in training; 91.7% do. After normalisation, 4 of 623 test clips have the same text as a training
  clip (3 from S6, which is not in training; 1 from S3; this is noted in the status section of `CLAUDE.md`, 2026-11-23, and I did not recheck it). The result stands;
  the claim of no shared sentence holds for exact text only.
- There is no standard spelling and the references have spacing noise. Word error counts a valid variant or a space
  as a full error. This pushes the number up. It cannot be removed by any scoring rule without a native check.
- The special Gojri letters of the Common Voice datasheet (ل° and ن°, and the project letters ݨ and ڵ) do not occur in
  any training or test sentence. The model never writes them.
- The model uses the Urdu language token. It writes Urdu-style spelling for some Gojri words (for example وقت for وخت).
- Common Voice terms: the datasheet says CC0 and forbids determining the identity of speakers. It says nothing about
  releasing trained weights.
- Prior work: BaltiVoice (arXiv 2606.03504) reports 24.78% word error for Whisper-small on Balti (abstract, Table 3 and
  section 5.2 agree). The paper chose its best checkpoint on the same 538-utterance set it reports, so that number is
  optimistic. `CLAUDE.md` and `ROADMAP.md` said 26.74%; that figure is not in the paper and is now corrected. The
  Gojri test set here was not used to choose the checkpoint (the dev set was), so the two numbers are not the same kind.
  Languages, data and test sets differ, so do not compare them as a ranking.

## Decision list for JD

1. **Good enough to publish with the limits?** The evidence supports a baseline model card: about 22% word error on
   read-aloud Common Voice sentences, spacing noise included, with the limits above. It does not support any claim about
   free speech or real use. Do step 6 first, because it is the only evidence from a real voice outside Common Voice.
2. **Do Common Voice terms allow release of the weights?** Not answered here. The datasheet in the local copy says CC0
   and "do not determine the identity of speakers". It does not mention models. Read the dataset page on Mozilla Data
   Collective before any upload. If it is still unclear, ask Mozilla Data Collective in writing.
3. **Model card content:** base model; data and release; the split and the three training speakers; results with the
   seen and unseen groups and the intervals above; the Urdu language token; the spacing-noise note; the missing Gojri
   letters; the limits; the AI-use and accuracy notice used in the README and the other Hugging Face cards.
4. **Repository:** a model repo under `junaidaslam` on Hugging Face. An optional Space with the Gradio app. Both need
   JD's decision. Nothing was created or uploaded.

## Open items

- Step 6, own-voice recordings and corrections (JD).
- JD to confirm or change the 50 hand labels (Claude's labels, not a native speaker's).
- The zero-shot base model without a forced language was not run.
- Common Voice terms on model release (decision 2).
