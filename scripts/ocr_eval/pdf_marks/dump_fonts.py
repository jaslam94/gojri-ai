import fitz, json, sys, os
from pathlib import Path
S = str(Path(__file__).resolve().parents[3] / "data/ocr/pdfmarks-work")
doc = fitz.open("pdfs/anjumshanasi/Kahawat-Kosh.pdf")
m = {}
for p in map(int, sys.argv[1:]):
    for f in doc[p].get_fonts(full=True):
        name = f[3].split("+")[-1]
        m[f"{p}|{name}"] = f[0]
        fp = f"{S}/fonts/x{f[0]}.ttf"
        if not os.path.exists(fp):
            try: open(fp, "wb").write(doc.extract_font(f[0])[3])
            except Exception as e: pass
json.dump(m, open(f"{S}/fonts/map_{sys.argv[1]}.json", "w"))
