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

# Gojri print PDF collection

A research collection of Gojri (ISO 639-3: `gju`) print PDFs, including dictionaries, poetry, folklore, textbooks, and historical works.

This collection provides source material for OCR evaluation, lexicon building, and text corpus development for Gojri language technology.

## Rights and copyright

The files in this collection are third-party published books. Copyright remains with the original authors, editors, and publishers. This repository serves as a research mirror for language technology development.

- Read [`LICENSE.md`](LICENSE.md) and [`CREDITS.tsv`](CREDITS.tsv) before using these files.
- Credit the authors and publishers listed for each file.
- Do not use these files for commercial republication.
- Authors or publishers requesting removal or re-licensing of a file can open an issue on the [gojri-ai](https://github.com/jaslam94/gojri-ai) repository or contact the maintainer.

## Contents

- PDF files under `pdfs/` (matching paths in the project manifest).
- `CREDITS.tsv`: File metadata including path, page count, scope, credits, notes, and MD5 hashes.
- `LICENSE.md`: Usage terms and copyright notice.

Only primary unique files are included. Exact duplicate files identified by MD5 hash were removed during project triage.

## Credits

Principal author and editor credits across this collection include:

- Dr. Javaid Rahi (editor and compiler of Gojri dictionaries, folklore anthologies, and poetry collections)
- Prof. (Dr.) Rafique Anjum and co-authors (dictionary and Anjum Shanasi publications)
- Additional authors and publishers listed in `CREDITS.tsv` and on printed title pages

Refer to `CREDITS.tsv` for per-file credit details.

## Related resources

- Digitized dictionary: [gojri-english-dictionary](https://huggingface.co/datasets/junaidaslam/gojri-english-dictionary)
- Lexicon: [gojri-devanagari-nastaliq-lexicon](https://huggingface.co/datasets/junaidaslam/gojri-devanagari-nastaliq-lexicon)
- OCR gold set: [gojri-nastaliq-ocr-gold](https://huggingface.co/datasets/junaidaslam/gojri-nastaliq-ocr-gold)
- Project repository: [jaslam94/gojri-ai](https://github.com/jaslam94/gojri-ai)

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

Cite the individual source book when referencing specific content from this collection.

## Contributions

Corrections to metadata or title-page credits are welcome via GitHub issues.
