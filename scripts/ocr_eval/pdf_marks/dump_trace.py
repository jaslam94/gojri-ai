import fitz, json, sys
S = r"D:/Code/VSCodeProjects/gojri-ai/data/ocr/pdfmarks-work"
doc = fitz.open("pdfs/anjumshanasi/Kahawat-Kosh.pdf")
for p in map(int, sys.argv[1:]):
    out = []
    for s in doc[p].get_texttrace():
        for ch in s["chars"]:
            out.append([s["font"].split("+")[-1], ch[1], ch[0], round(ch[2][0],2), round(ch[2][1],2), [round(v,2) for v in ch[3]], round(s["size"],3)])
    json.dump(out, open(f"{S}/trace/p{p}.json", "w"))
