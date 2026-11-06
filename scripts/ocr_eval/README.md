# OCR model comparison scripts

Scripts that compare Nastaliq OCR models on Gojri text. The 200-line test set is the 200 dictionary lines the
user reviewed. The reference text for it is `text_fix` in `data/synth/real_pairs/labels_review_test.jsonl`
(gitignored, copied into `data/utrnet-test/results.tsv`).

| Script | What it does |
|---|---|
| `dump_arabic_runs.py` | Cuts the Arabic-script parts of the 200 lines into PNG crops, using glyph boxes from the PDF. Needs the dictionary PDF and `scripts/synth/`. |
| `score_qaari.py` | Scores a Qaari output file against the 200 reference lines, next to UTRNet (same metric as `scripts/utrnet_arabic_eval.py`). |
| `sm_qaari/qaari_entry.py`, `launch_qaari.py` | Run Qaari on the crops as one SageMaker training job (`ml.g5.xlarge`). The job stops if the LoRA adapter did not load. |
| `score_gold_letters.py` | Arabic-letter error of every `*_original.txt` OCR run on the 12 gold pages. Spaces, Latin letters and short vowels are ignored. |

The launch scripts need the environment variable `SAGEMAKER_ROLE_ARN`. Do not commit it.

## Results so far (2026-11-06)

Arabic-letter error on the 200 lines (1,400 reference letters):

| System | Input | Error |
|---|---|---|
| UTRNet-Large | Arabic runs | 2.1% (29 letters, 178 lines exact) |
| Qaari-0.1-Urdu-OCR-VL-2B | Arabic runs, 2x scale on white canvas | 185.9% (46 lines exact) |
| Qaari | Arabic runs, raw crop | 198.5% |
| Qaari | Arabic runs, 2x scale | 212.3% |

Qaari writes sensible text for many short words. On 31 of 200 lines it runs away into long repeated text.
Those lines cause 2,230 of the 2,602 errors. On the other 169 lines it still makes 31.3% errors.
Qaari is a page-level model (trained on synthetic Urdu news pages), so line crops are not its intended input.
It must be checked on whole pages before it is ruled out. Adapter loading was verified in the job
(the library version must match: transformers 4.49 with peft 0.14, see `sm_qaari/requirements.txt`;
with transformers 5 the adapter silently does not load).

UTRNet on the 12 gold pages with a simple line splitter is not committed yet (the splitter is a first version).
