# Contributing

Gojri AI welcomes corrections and contributions, most of all from people who speak and read Gojri. The project is
non-commercial. By contributing you agree that your contribution is shared under the project's terms
(`LICENSE` for code, `DATA-NOTICE.md` for data).

## Ways to help

1. **Review machine OCR text.** `data/ocr-output/` holds the OCR text of four full books, mostly unchecked. Compare
   a page with the printed page and send the corrections. Each checked page becomes test data and helps us improve
   and fine-tune the OCR. Instructions: [`data/ocr-output/README.md`](data/ocr-output/README.md).
2. **Report an error in the documents or the data.** A number, a statement or a transcription may be wrong. Open an
   issue with the file, the line, what is wrong, and your evidence.
3. **Check published text.** The dictionary text, the lexicon and the gold pages (links in [`README.md`](README.md))
   were made with AI help and only partly checked by a person.
4. **Share Gojri text or speech** that you have the right to share, or record and validate Gujari sentences on
   [Mozilla Common Voice](https://commonvoice.mozilla.org/).
5. **Improve the code.** Pull requests are welcome. Say what you changed and how you tested it.

## Rules for Gojri text corrections

- Write letters and marks as printed.
- Put word spaces where the meaning has a word break, even where the print runs words together.
- ك and ک, and ه and ہ, count as the same letter. ھ is a separate letter.
- Write ݨ and ڵ where the print shows a small "v" over ن or ل.
- Put a space after ۔ and ،.
- Keep one printed line per row; a TAB separates the two halves of a verse line.
- Use `[...]` to describe a picture or ornament, and `[[...]]` only for a word you cannot read.

## How to send

- **Issue:** [github.com/jaslam94/gojri-ai/issues](https://github.com/jaslam94/gojri-ai/issues). For a text
  correction give the book, the PDF page, the line, the current text and the correct text.
- **Pull request:** edit the file directly. Keep one book per pull request.

Do not include personal data about other people. Authors or publishers who want a book removed can open an issue.
