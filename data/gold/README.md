---
pretty_name: Gojri Nastaliq OCR Gold Set
language:
  - gju
license: other
license_name: research-excerpt-benchmark
license_link: LICENSE.md
task_categories:
  - image-to-text
  - other
tags:
  - gojri
  - gujari
  - gju
  - nastaliq
  - ocr
  - gold-standard
  - benchmark
  - low-resource
  - indo-aryan
size_categories:
  - n<1K
configs:
  - config_name: default
    data_files:
      - split: train
        path: candidates.csv
---

# Gojri Nastaliq OCR gold set

A 12-page benchmark for reading Gojri (ISO 639-3: `gju`) in Nastaliq script from page images.

This benchmark provides evaluation pages and ground truth transcriptions to test and compare OCR pipelines on printed Gojri text.

## Dataset contents

| Path | Description |
|------|-------------|
| `images_cropped/` | 12 cropped page images used for OCR evaluations |
| `transcriptions/<page_id>/<page_id>_gold.txt` | Human-checked ground truth text |
| `transcriptions/.../*_gemini_3.6_flash_*_original.txt` | Gemini 3.6 Flash one-shot API output |
| `transcriptions/.../*_sonnet_4.6_*_original.txt` | Claude Sonnet 4.6 one-shot API output |
| `transcriptions/.../*_composer_v1_original.txt` | Composer chat baseline output |
| `candidates.csv` | Page IDs, source PDF names, and notes |
| `bakeoff_results.csv` | Evaluated word error rates |

## Bake-off summary

Results pooled over 12 pages (1,791 ground-truth words):

| Model / pipeline | Pooled word error rate | Notes |
|------------------|-----------------------:|-------|
| Gemini 3.6 Flash (one-shot API) | 17.8% | Lowest error rate among tested one-shot APIs |
| Claude Sonnet 4.6 (one-shot API) | 22.6% | Tested via AWS Bedrock |
| Composer 2.5 (chat) | 13.0% | Interactive chat baseline, not an API run |

Heh forms count as different letters in the scorer: a plain heh (ہ), the Arabic heh (ه) and the two-eyed heh (ھ) do not match each other.

## Versions

- `v1.0`: the first release (September 2026).
- `v2.0` (November 2026): five words in three gold files change from ه to ھ after checking the printed pages: `dict_alif` (ھور, ھوا, مھارو), `gojri_adbiyaat` (برھنوسیال) and `nazir_spread_b_left` (بَھلا). Gemini 3.6 Flash pooled word error moves from 17.1% to 17.3%, and its `dict_alif` score from 23.5% to 26.1%. Composer `dict_alif` moves from 10.1% to 9.2%. Other scores do not change.
- Ghazal correction (15 November 2026): eleven words in `gojri_ghazal` now follow the small "v" that the print draws over ل and ن. Six words take ڵ (for example نال to ناڵ) and five take ݨ (for example کرن to کرݨ). The models wrote the plain letters, so every page score on `gojri_ghazal` rises: Gemini 12.4% to 14.7%, Sonnet 13.3% to 16.5%, Composer 14.2% to 16.5%. Pooled: Gemini 17.3% to 17.8%, Sonnet 22.0% to 22.6%, Composer 12.6% to 13.0%.

Bulk vision OCR remains paused because an error rate of 17% without human verification introduces too many errors into corpus text.

You can evaluate models locally using `scripts/score_gold.py` in the [gojri-ai](https://github.com/jaslam94/gojri-ai) repository.

## Page selection

| Page ID | Content type |
|---------|--------------|
| `dict_alif` | Dictionary layout with mixed Nastaliq and English |
| `kahawat_kosh` | Two-column proverb layout |
| `gojri_adbiyaat` | Dense literary prose |
| `gojri_ghazal` | Essay and literary layout |
| `mahatma_gandhi` | Illustration with caption |
| `kulyate_spread_*` | Split two-page spread poetry |
| `nazir_spread_*` | Split two-page spread poetry |
| `louk_warsti` | Scanned page with paper show-through |
| `shingar_textbook` | Scanned school textbook page |
| `primer_pehli` | Children's primer page |

Source pages are drawn from Gojri print PDFs (dictionaries, poetry, textbooks, and folklore). Full books are not included in this evaluation set.

## Usage

Load the dataset with the Hugging Face `datasets` library:

```python
from datasets import load_dataset

ds = load_dataset("junaidaslam/gojri-nastaliq-ocr-gold")
print(ds["train"][0])
```

## License and rights

See [`LICENSE.md`](LICENSE.md).

Gold transcriptions and benchmark files are shared for research and language technology development. Page images are short excerpts from printed Gojri books. Original book copyright remains with the authors and publishers.

## Citation

```bibtex
@dataset{gojri_nastaliq_ocr_gold_2026,
  title     = {Gojri Nastaliq OCR Gold Set},
  author    = {Aslam, Junaid},
  year      = {2026},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold},
  note      = {12-page experimental OCR benchmark for Gojri Nastaliq}
}
```

## Related resources

- Lexicon: [gojri-devanagari-nastaliq-lexicon](https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon)
- Project repository: [jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai)

## Contributions

Corrections to ground truth text and additional checked pages are welcome via issues or pull requests on GitHub.
