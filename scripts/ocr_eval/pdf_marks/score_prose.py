import json, sys, difflib
sys.path.insert(0,"scripts/ocr_eval/pdf_marks"); sys.path.insert(0,"scripts/ocr_eval")
from placed import pairs
gold=open("./data/gold/transcriptions/gojri_ghazal/gojri_ghazal_gold.txt",encoding="utf-8").read()
res=json.load(open(sys.argv[1],encoding="utf-8"))
names={"\u064f":"pesh","\u0650":"zer","\u064e":"zabar","\u0651":"shadda","\u064b":"tanwin","\u0652":"sukun"}
t=pairs(gold)
for k,v in {"UTRNet alone":"\n".join(r["raw"] for r in res["rows"]), "PDF marks":"\n".join(r["text"] for r in res["rows"])}.items():
    o=pairs(v)
    sm=difflib.SequenceMatcher(None,"".join(a for a,_ in t),"".join(a for a,_ in o),autojunk=False)
    m={}
    for b in sm.get_matching_blocks():
        for d in range(b.size): m[b.a+d]=b.b+d
    inv={j:i for i,j in m.items()}
    ok=miss=other=extra=skip=0; det=[]
    for i,(c,mk) in enumerate(t):
        if not mk: continue
        if i not in m: skip+=1; continue
        got=o[m[i]][1]
        if got==mk: ok+=1
        elif not got: miss+=1; det.append(("missing",c,names.get(mk,mk)))
        else: other+=1; det.append(("other",c,names.get(mk,mk),names.get(got,got)))
    for j,(c,mk) in enumerate(o):
        if mk and j in inv and not t[inv[j]][1]: extra+=1; det.append(("EXTRA",c,[names.get(x,x) for x in mk]))
    print(f"{k}: truth marks {sum(1 for _,x in t if x)} | right {ok}, missing {miss}, other {other}, extra {extra}, on unread letters {skip}"); print("   ",det)
