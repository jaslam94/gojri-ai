---
pretty_name: Gojri Devanagari-Nastaliq Lexicon
language:
  - gju
license: other
license_name: derivative-of-copyrighted-dictionary
license_link: LICENSE.md
task_categories:
  - translation
  - other
tags:
  - gojri
  - gujari
  - gju
  - nastaliq
  - perso-arabic
  - devanagari
  - dictionary
  - lexicon
  - low-resource
  - indo-aryan
  - orthography
  - script-conversion
size_categories:
  - 1K<n<10K
dataset_info:
  features:
    - name: entry_id
      dtype: string
    - name: page
      dtype: int32
    - name: line
      dtype: int32
    - name: devanagari
      dtype: string
    - name: roman
      dtype: string
    - name: nastaliq
      dtype: string
    - name: english_gloss
      dtype: string
    - name: quality
      dtype: string
configs:
  - config_name: default
    data_files:
      - split: train
        path: gojri_lexicon_final.tsv
  - config_name: human_verified
    data_files:
      - split: train
        path: gojri_lexicon_human_verified.tsv
---

# Gojri Devanagari-Nastaliq lexicon

A lexicon that maps Gojri headwords from Devanagari to Nastaliq (ISO 639-3: `gju`).

The language of this dataset is Gojri, not Urdu or Hindi. Each row maps a Devanagari headword from a published Gojri dictionary to its Gojri Nastaliq (Perso-Arabic) form. Optional Roman transliteration and a short English gloss come from the same source line.

## Source attribution

This lexicon is derived from headwords in:

> Anjum, Rafique, and Ruksana Sadiq. *Concise Gojri-English-Hindi Dictionary*.
> Educational Publishing House / J K Anjuman Taraqi Gojri Adab, New Delhi.
> ISBN 978-81-19225-29-3. Compilation: Prof. (Dr.) Rafique Anjum (D.Phil).
> Composition and vetting: Ms. Ruksana Sadiq (M.Phil). © All rights reserved
> by the original rights holders.

Local PDF file used for extraction:
`anjumshanasi/Gojri-Hindi-English-Dictionary.pdf` (458 pages; MD5 `dbcf6814f1b19a111f8bb3955e341b11` in the project manifest).

Cite both this dataset and the original dictionary in any publication or redistribution that uses these headwords. See [Citation](#citation) and [License](#license).

## Dataset files

| File | Rows | Description |
|------|-----:|-------------|
| `gojri_lexicon_final.tsv` | 1,862 | Full lexicon (default split) |
| `gojri_lexicon_human_verified.tsv` | 50 | Native-speaker verified subset |
| `LICENSE.md` | - | Derivative rights notice |
| `README.md` | - | Dataset card |

## Language

| Field | Value |
|-------|--------|
| Language | Gojri (Gujari) |
| ISO 639-3 | `gju` |
| Source script | Devanagari |
| Target script | Perso-Arabic Nastaliq |

Gojri is an Indo-Aryan language. It shares script and some vocabulary with Urdu, but it is a distinct language. Spellings in this lexicon follow Gojri print practice.

## Columns

| Column | Description |
|--------|-------------|
| `entry_id` | Stable ID, e.g. `p0019:L14` (source page and line) |
| `page` | Page number in the source PDF |
| `line` | Line number in the page extract |
| `devanagari` | Headword in Devanagari |
| `roman` | Optional Latin form from the dictionary |
| `nastaliq` | Gojri Nastaliq headword (main field) |
| `english_gloss` | Short English gloss snippet when present |
| `quality` | Trust tag |

### Quality tags

| `quality` | Count | Meaning |
|-----------|------:|---------|
| `human_verified` | 50 | Approved by a native Gojri speaker |
| `pass2_refined` | 299 | Refined in pass 2 |
| `pass1_kept` | 1,513 | Kept from pass 1 as correct Gojri Nastaliq |

50 rows are human-verified so far. Remaining rows are automated conversions and require spot-checking before training-critical use.

## How it was built

1. Extracted clean Unicode text from the Devanagari dictionary PDF.
2. Pass 1: Ran Aksharamukha `Devanagari -> Urdu` locally and removed short vowels.
3. Pass 2: Applied Gojri orthography rules:
   - Retained pass 1 when already correct.
   - Mapped न and ण to standard `ن` (U+0646) instead of `ݨ` (U+0768).
   - Preferred Gojri word-final `-و` endings where required.
   - Corrected Perso-Arabic etymology for Arabic and Persian loanwords.
4. Human verification: 50 seed entries (pages 19, 31, 167) were reviewed by a native Gojri speaker.
5. Initial heh (November 2026): the Gojri print writes a word that starts with /h/ with the two-eyed heh ھ (448 of 475 word-initial heh forms in the printed Gojri-English Dictionary text). Aksharamukha writes ہ there, so every Arabic-script word in `nastaliq` that started with ہ or ه now starts with ھ. This changed 112 words in 98 rows. Human-verified rows were not touched. `scripts/lexicon_initial_heh.py` in the project repository applies the rule.

The source PDF has no Nastaliq text. It holds Devanagari, Roman, English and Hindi only, so the `nastaliq` column is machine-made (rules and a language model) and only the 50 human-verified rows were checked by a speaker. Some rows are example phrases or sentence fragments from the dictionary, not single headwords.

## Versions

Tag `v1.0` is the October 2026 release. Tag `v2.0` (November 2026) starts every Arabic-script word in the `nastaliq` column with ھ where it started with ہ (112 words in 98 rows; see build step 5). Load a version with `load_dataset("junaidaslam/gojri-devanagari-nastaliq-lexicon", revision="v1.0")`.

Known verified correction: Devanagari `अंगणू` -> Nastaliq `انگنو` (not `انگݨو`).

Pipeline code is in the [gojri-ai](https://github.com/jaslam94/gojri-ai) repository (`scripts/dict_translit_*.py`, `prompts/devanagari_to_gojri_nastaliq_v1.txt`).

## Loading the dataset

```python
from datasets import load_dataset

ds = load_dataset("junaidaslam/gojri-devanagari-nastaliq-lexicon")
print(ds["train"][0])

# Verified subset only
gold = load_dataset(
    "junaidaslam/gojri-devanagari-nastaliq-lexicon",
    name="human_verified",
)
```

Direct TSV loading:

```python
from datasets import load_dataset

ds = load_dataset(
    "csv",
    data_files="gojri_lexicon_final.tsv",
    delimiter="\t",
)
```

## Intended use

- Devanagari to Nastaliq headword lookup for Gojri.
- Seed data for orthography and transliteration tools.
- Vocabulary verification for OCR and ASR systems.

## Limitations

- Contains headwords and brief glosses rather than full dictionary definitions.
- Includes single-letter alphabet entries from early dictionary pages.
- Most rows are not yet human-verified.
- Does not contain full page text or example sentences from the copyrighted book.

## License

See [`LICENSE.md`](LICENSE.md).

- The original dictionary remains copyright of the original rights holders (Anjum, Sadiq, Educational Publishing House, J K Anjuman Taraqi Gojri Adab).
- This release is a script-conversion derivative of headwords for language preservation and research.
- Users must retain attribution to the original authors and to this dataset.

## Citation

```bibtex
@dataset{gojri_devanagari_nastaliq_lexicon_2026,
  title     = {Gojri Devanagari-Nastaliq Lexicon},
  author    = {Aslam, Junaid},
  year      = {2026},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon},
  note      = {Script-conversion derivative of headwords from Anjum and Sadiq,
               Concise Gojri-English-Hindi Dictionary; 50 rows human-verified}
}
```

Original source dictionary:

```bibtex
@book{anjum_sadiq_gojri_dictionary,
  title     = {Concise Gojri-English-Hindi Dictionary},
  author    = {Anjum, Rafique and Sadiq, Ruksana},
  publisher = {Educational Publishing House / J K Anjuman Taraqi Gojri Adab},
  address   = {New Delhi},
  isbn      = {978-81-19225-29-3},
  note      = {Compilation by Prof. (Dr.) Rafique Anjum; composition and vetting
               by Ms. Ruksana Sadiq}
}
```

## Contributions

Contributions to correct `nastaliq` forms or add verified rows are welcome via issues or pull requests on GitHub.

## Contact

- Dataset maintainer: [junaidaslam](https://huggingface.co/junaidaslam)
- Repository: [jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai)
