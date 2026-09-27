---
pretty_name: Gojri Print PDF Collection
language:
  - gju
license: other
license_name: third-party-print-corpus
license_link: LICENSE.md
task_categories:
  - other
tags:
  - gojri
  - gujari
  - gju
  - nastaliq
  - pdf
  - corpus
  - low-resource
  - language-preservation
size_categories:
  - n<1K
---

# Gojri Print PDF Collection

A local research collection of **Gojri** (گوجری, ISO 639-3: `gju`) print PDFs:
dictionaries, poetry, folklore, textbooks, and related books. Shared so others
can help grow text and speech resources for Gojri.

This project aims to build **Gojri ASR** and a **Gojri LLM**, in the same spirit
as community Pashto work such as **Katib** (speech recognition) and **Qehwa**
(language model). The work is experimental. It is done for the love of the
language and for fairer representation in AI and NLP. The maintainer is a
software engineer who learns by intuition and experiment; one purpose of this
collection is to learn the domain while growing usable Gojri data.
Contributions are welcome.

## Important rights note

Most files here are **third-party published books**. Copyright stays with the
original authors, editors, and publishers. This dataset is a research mirror for
language technology, not a claim of ownership.

**Please:**

1. Read [`LICENSE.md`](LICENSE.md) and [`CREDITS.tsv`](CREDITS.tsv).
2. Credit the people named for each file.
3. Do not treat this as permission for commercial republication of the books.
4. If you are an author or publisher and want a file removed or relicensed,
   open an issue on [gojri-ai](https://github.com/jaslam94/gojri-ai) or contact
   the maintainer.

## What is included

- PDF files under `pdfs/` (same relative paths as in the project manifest)
- `CREDITS.tsv` — one row per file: path, pages, scope, credits, notes, MD5
- This README and LICENSE

Only primary copies that still exist locally are uploaded. Exact duplicates from
the original collection were already dropped via MD5 in the project manifest.
Some English-only history volumes were marked out of scope earlier and may be
absent.

## Credits (high level)

Many volumes in this set are connected to work by:

- **Dr. Javaid Rahi** (editor/compiler of numerous Gojri dictionaries, folklore,
  and poetry collections)
- **Prof. (Dr.) Rafique Anjum** and collaborators (including dictionary and
  related Anjum Shanasi publications)
- Other authors and publishers named on individual title pages

Per-file credits and notes are in **`CREDITS.tsv`**. Always prefer the printed
title page when it is more precise than our short credit line.

## How this helps

These PDFs support OCR experiments, lexicon growth, and future Gojri text
corpora for ASR and LLM training. Companion public releases:

- Lexicon: https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon
- OCR gold set: https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold
- Code and notes: https://github.com/jaslam94/gojri-ai

## Citation

```bibtex
@dataset{gojri_print_pdf_collection_2026,
  title     = {Gojri Print PDF Collection},
  author    = {Aslam, Junaid},
  year      = {2026},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/junaidaslam/gojri-print-pdf-collection},
  note      = {Research mirror of third-party Gojri print PDFs; see CREDITS.tsv}
}
```

Also cite the original book for any specific volume you use.

## Contributions

If you have rights-cleared Gojri books, better title-page credits, or want to
help with OCR and corpus work, please get in touch via GitHub issues. Speakers,
students, and researchers are all welcome.
