# ASR model candidates for Gojri (2026-11-25)

Goal: find a better base than Whisper-small (22.7% word error, 21.6% on unseen speakers). Optimisation comes later.
Marks: VERIFIED = I opened the source in this session. MEMORY = from my own knowledge, not checked today.

## Run now
**Whisper-medium** (769M parameters), same data and split as the small baseline, so the two scores compare directly.
Job `gojri-asr-whisper-medium-2026-11-25-13-46-21-607`, `ml.g5.xlarge`, batch 8 x 2 accumulation (effective 16),
gradient checkpointing, lr 1e-5, 2,500 steps, dev check every 250, hard cap 5 hours.
**Result: 18.33% word error** on the 623 test clips (small: 22.7%); unseen speakers 18.5% (small 21.6%); character error 6.9% (8.3%). Size alone gave about 4 points. Details: `scripts/asr/README.md`.

## Candidates, best lead first
| # | Model | Size | Why it may beat Whisper-small | Open question |
|---|---|---|---|---|
| 1 | **Meta Omnilingual ASR** | 300M to 7B | VERIFIED: its language list (`lang_ids.py` in the facebookresearch/omnilingual-asr repo) contains `gju_Arab` (Gojri, Arabic script) and `urd_Arab`. The model may already know Gojri. Model cards for the 3B and 7B LLM versions show license Apache-2.0 (VERIFIED). | How much Gojri audio it saw. Runs on fairseq2 (Linux). Fine-tuning recipes may be limited (one repo note says so for one variant; not checked). First step: zero-shot score on our 623 test clips. |
| 2 | **Whisper large-v3** | 1.55B (MEMORY) | Best Whisper for Urdu. Same recipe as now. | Needs LoRA or 8-bit optimiser to fit one 24 GB GPU, or a larger instance. |
| 3 | **Whisper large-v3-turbo** | 809M (MEMORY) | Close to large-v3 quality with a small decoder. Trains about like medium. | Fine-tuning reports are fewer. |
| 4 | **w2v-BERT 2.0 + CTC head** | 600M (MEMORY) | Hugging Face blog reports quality similar to Whisper-large-v3 on Mongolian after fine-tuning, with much less compute (VERIFIED as a claim of the blog). A 2025 African-language benchmark says Whisper gains plateau earlier than W2v-BERT and XLS-R as labelled data grows (VERIFIED as a claim of the paper). | Needs a character vocabulary and no built-in language model. Best when we have more data. |
| 5 | **AI4Bharat IndicConformer 600M** | 600M | VERIFIED: 22 Indian languages, includes Dogri (`doi`), a neighbour of Gojri; MIT license; also Urdu and Kashmiri models. | Gojri itself is not in the list. NeMo toolchain. |
| 6 | **Meta MMS 1B** | 1B | Covers 1,100+ languages. VERIFIED: the vocabulary has 1,198 keys and no `gju` key. | Not a lead unless an adapter is trained. Its license is CC BY-NC (MEMORY). |
| 7 | **Seamless M4T v2 large** | 2.3B (MEMORY) | Supports Urdu. | Heavy; CC BY-NC (MEMORY); little reason to prefer it over 1 to 4. |

## Results so far (all on the 623 test clips, one scorer)
| Model | Training on our data | Word error | Character error |
|---|---|---|---|
| Whisper-small | fine-tuned | 22.7% | 8.3% |
| Whisper-medium | fine-tuned | 18.3% | 6.9% |
| Omnilingual LLM-300M, `gju_Arab` | none | 14.9% | 5.4% |
| Omnilingual LLM-1B | none | 13.4% | 4.6% |
| Omnilingual LLM-3B | none | 12.2% | 4.2% |
| **Omnilingual LLM-7B** | none | **9.9%** | **3.15%** |
| Omnilingual CTC-1B | none | 42.4% | 14.1% |
| Omnilingual LLM-1B, fine-tuned on our data (400 steps) | fine-tuned | 12.5% | 4.06% |

Source: `data/asr/results_whisper-medium_2026-11-25.json`, `data/asr/results_omniasr_zero-shot_2026-11-25.json`. Open risk: Meta may have trained on these public Common Voice clips (not checked).
Whisper large-v3 (LoRA) is smoke-tested, not run: Omnilingual-7B already scores below what Whisper-medium reached.

## Order I suggest
1. Whisper-medium result (running). It tells us what size alone gives.
2. Omnilingual ASR zero-shot on the 623 test clips (inference only, cheap). If it already reads Gojri, fine-tune it.
3. Whisper large-v3 with LoRA, same split.
4. w2v-BERT 2.0 with CTC when we have more voices.

## Limits that hold for every model
- Only 3 training speakers. More voices help more than a bigger model.
- Test text comes from a small book pool (3,854 sentences). A real-voice test is still needed.
- Use the same split and the same scorer (`scripts/asr/sm_whisper/sm_whisper_entry.py`) for every model.
