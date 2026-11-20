---
annotations_creators:
- machine-generated
- expert-generated
configs:
- config_name: default
  data_files:
  - split: train
    path: gojri_english_dictionary_pages.csv
language:
- gju
- en
language_bcp47:
- gju
- en-US
license: cc-by-nc-4.0
multilinguality:
- bilingual
pretty_name: Gojri-English Dictionary Text Corpus
size_categories:
- 10K<n<100K
source_datasets:
- original
tags:
- gojri
- dictionary
- ocr
- nlp
- low-resource-languages
- unicode-text
task_categories:
- translation
- text-retrieval
---

# Gojri-English dictionary text corpus

## Dataset summary

Digitized text of the printed *Concise Gojri-English Dictionary* by Dr. M. R. Anjum Awan. The dataset covers 474 body pages (pages 25 to 498) and includes 11,767 dictionary entry lines. Each line contains a Gojri headword in Perso-Arabic (Nastaliq) script, a Latin transliteration, a part-of-speech tag and an English definition.

## Author and source credits

- Compilation and composition: Dr. M. R. Anjum Awan (as printed on the title pages)
- Computational editing: Shabir Ahmad
- Publisher: J&K Anjuman Taraqi Gojri Adab
- Source work: *Concise Gojri-English Dictionary* (498 PDF pages)
- Language: Gojri (ISO 639-3: `gju`) and English (`en`)
- Digitization: Gojri AI project

All original content rights remain with the author and the publisher.

**Correction (November 2026):** earlier versions of this card named Dr. Javaid Rahi as the author. That was wrong. The title pages of the book name Dr. M. R. Anjum Awan.

## Digitization pipeline

The PDF uses the Batool font, which maps Nastaliq glyphs to Private Use Area (PUA) Unicode code points, so copied text is unreadable symbols.

The text was made in four steps:

1. Font decoding: a table of the 160 Batool PUA codes maps them to Unicode Arabic letters.
2. Multimodal refinement: Gemini Flash read the decoded text together with the page image and fixed marks, letter order and formatting.
3. Image audit: Gemini compared the text of every page with the page image and listed the problems it found.
4. Table merge (version 2, November 2026): A native Gojri speaker checked all 160 font codes and 200 random lines against the printed pages, and the font table was corrected. Each line was then compared with the corrected font decode. Where a word differed, the decode spelling replaced the Gemini spelling. The spaces around the `(transliteration)` group come from the gaps measured in the PDF.

## Version 2 (November 2026)

Version 1 (October 2026) is tagged `v1.0` and this version is tagged `v2.0`. Load a version with `load_dataset("junaidaslam/gojri-english-dictionary", revision="v1.0")`. In `v1.0`, `load_dataset` returns one row per text line with a single `text` column. From `v2.0` it returns one row per page with the four fields listed below. The speaker found errors in 91% of the 200 sampled lines. The most common error was spacing: Gemini put a space on both sides of the transliteration group, and the print has none on most lines. Next came heh and kaf spelling, then a few wrong letters. Version 2 changes 10,228 of the 11,767 lines, on 465 pages.

On the 200 sampled lines, 316 of 333 Arabic words now equal the speaker's final text (version 1: 281). The space before and after the transliteration group matches on 160 of 178 lines (version 1: 7).

The spelling follows the print. The two-eyed heh ھ at the start of a word is as printed. ك and ک are the same letter, and the text keeps the shape the print shows. Gojri has no agreed spelling, so the same word can appear in more than one form.

Known limits:

- Only the 200 sampled lines were checked by a person. The rest was not.
- Pages 55, 94, 95, 194, 221, 237, 238, 335 and 336 are unchanged from version 1.
- On 201 lines the Gemini text and the decode split words differently. Only close word pairs were updated there, and 152 of those lines kept their version 1 letters.
- On 18 of the 178 sampled lines with a transliteration group, the space before or after it still differs from the speaker's text.

## Dataset structure

The dataset is available in CSV, JSONL, and plain text formats:

- `gojri_english_dictionary_pages.csv`: Main tabular dataset file.
- `gojri_english_dictionary_pages.jsonl`: Line-delimited JSON file.
- `pages/`: Individual text files for each page (`page-0025.txt` to `page-0498.txt`).

### Data fields

- `page_number` (int): Page number in the printed dictionary (25 to 498; the same as the PDF page number).
- `page_file` (string): Filename of the page text file.
- `line_count` (int): Number of entry lines on the page.
- `text` (string): Full text of the page (version 2).

## Quick start

Load the dataset with the Hugging Face `datasets` library:

```python
from datasets import load_dataset

dataset = load_dataset("junaidaslam/gojri-english-dictionary")
print(dataset["train"][0])
```

## Accuracy, AI use and terms

- This dataset comes from a personal, non-profit project. Use it for non-commercial purposes only.
- AI did most of the work: a font decode table, Gemini for correction and audit, and AI coding agents for the scripts. A native Gojri speaker checked 200 of the 11,767 lines and all 160 font codes. The rest is machine text.
- We check our figures against the data, but errors and inconsistencies can remain. Please report them. Corrections and reviews by Gojri speakers are very welcome: [github.com/jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai) (see `CONTRIBUTING.md`).

## Licensing

This dataset is released under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

- Non-commercial use only: research, education, language preservation and language technology development.
- Attribution: credit Dr. M. R. Anjum Awan as the author of the source dictionary and the Gojri AI project for the digitized text.
