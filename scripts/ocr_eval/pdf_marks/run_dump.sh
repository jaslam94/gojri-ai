S="D:/Code/VSCodeProjects/gojri-ai/data/ocr/pdfmarks-work"
PAGES=$(py -3 -c "import json;print(' '.join(str(p) for p in sorted({c['page']-1 for c in json.load(open('data/ocr/kahawat-marks/sample.json',encoding='utf-8'))})))")
set -- $PAGES
while [ $# -gt 0 ]; do
  chunk=""; n=0
  while [ $n -lt 8 ] && [ $# -gt 0 ]; do chunk="$chunk $1"; shift; n=$((n+1)); done
  py -3 -X utf8 $S/dump_trace.py $chunk || echo "fail: $chunk"
done
ls $S/trace | wc -l
