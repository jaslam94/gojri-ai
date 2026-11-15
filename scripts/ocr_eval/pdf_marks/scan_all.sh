# Which PDFs of the collection use the mark glyphs of the table? 5 sample pages per PDF. Run from the repo root.
for f in $(find pdfs -name "*.pdf" | sort); do
  timeout 300 py -3 -X utf8 scripts/ocr_eval/pdf_marks/marks_table.py scan "$f" 2>&1 | tail -1 | cut -c1-200
done
