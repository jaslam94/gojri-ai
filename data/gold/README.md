# OCR Gold Set

Twelve carefully checked Gojri Nastaliq page images for OCR experiments.

This work is experimental. It exists because Gojri deserves better support in
AI and NLP. The maintainer is a software engineer who learns by intuition and
experiment; this gold set is also practice in the OCR and NLP domain.
Contributions are welcome.

**Published copy:**
https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold

## Layout (this repo)

- `images_cropped/` — images used for OCR tests (preferred)
- `images/` — uncropped renders (local comparison only)
- `transcriptions/<page_id>/`
  - `*_gold.txt` — ground truth
  - `*_original.txt` — raw model outputs
- `transcriptions_archived/` — shelved models (not in the public bake-off)
- `candidates.csv` — page metadata
- `bakeoff_results.csv` — word error rates from the comparison
- `ocr_runs_log.csv` — local API cost log (not published)

## Bake-off (pooled word error)

| Setup | WER | Role |
|-------|----:|------|
| Gemini 3.6 Flash (one-shot API) | **17.1%** | Best one-shot API here |
| Claude Sonnet 4.6 (one-shot API) | 22.0% | Comparison |
| Composer 2.5 (chat) | 12.6% | Draft helper; not a bulk API |

Bulk vision OCR stays paused until quality is good enough without checking every page.

Score with:

```bash
py -3 scripts/score_gold.py
```

See `LOG.md` for the full experiment story.
