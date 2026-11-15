# Dump glyph traces (dump_trace.py) and embedded fonts (dump_fonts.py) of every page of Kahawat-Kosh.pdf, 8 pages per process
# (pymupdf crashes after many get_texttrace calls in one process). Run from the repo root: bash scripts/ocr_eval/pdf_marks/dump_all.sh
D=scripts/ocr_eval/pdf_marks
for script in dump_trace.py dump_fonts.py; do
  p=0
  while [ $p -lt 169 ]; do
    pages=""; n=0
    while [ $n -lt 8 ] && [ $p -lt 169 ]; do pages="$pages $p"; p=$((p+1)); n=$((n+1)); done
    py -3 -X utf8 $D/$script $pages || echo "fail $script: $pages"
  done
done
ls data/ocr/pdfmarks-work/trace | wc -l; ls data/ocr/pdfmarks-work/fonts | grep -c ttf
