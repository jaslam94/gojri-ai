import json, sys, difflib, re, unicodedata
sys.path.insert(0, "D:/Code/VSCodeProjects/gojri-ai/scripts/ocr_eval")
from kraken_compare import base, MARKS, norm
def pairs(s):
    out = []   # [(letter, marks)]
    for ch in norm(s):
        if MARKS.match(ch):
            if out: out[-1][1] += ch
        elif "\u0600" <= ch <= "\u06ff" and ch.isalpha() and ch != "ـ":
            out.append([ch, ""])
    return out
def score(path, verbose=False):
    rows = json.load(open(path + "/score_marks.json", encoding="utf-8"))
    tot = wrong = 0; det = []
    for r in rows:
        if r.get("trimmed") is None or r["ocr"] is None: continue
        t, o = pairs(r["trimmed"]), pairs(r["ocr"])
        sm = difflib.SequenceMatcher(None, "".join(a for a, _ in t), "".join(a for a, _ in o), autojunk=False)
        m = {}
        for b in sm.get_matching_blocks():
            for d in range(b.size): m[b.a + d] = b.b + d
        for i, (ch, mk) in enumerate(t):
            if mk:
                tot += 1
                if i in m and o[m[i]][1] == mk: continue
                if i not in m: continue   # letter not read: not a placement error
                wrong += 1; det.append((r["card"], r["field"], ch, mk, o[m[i]][1]))
        # marks in ours that truth lacks
        inv = {v: k for k, v in m.items()}
        for j, (ch, mk) in enumerate(o):
            if mk and j in inv and not t[inv[j]][1]:
                wrong += 1; det.append((r["card"], r["field"], "EXTRA", ch, mk))
    return tot, wrong, det
if __name__ == "__main__":
    for p in sys.argv[1:]:
        tot, wrong, det = score(p)
        print(p.split("/")[-1], "truth marks on read letters", tot, "wrong or extra", wrong)
        for d in det: print("  ", d)
