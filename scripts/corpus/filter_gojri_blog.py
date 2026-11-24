"""Keep the Gojri parts of the fetched blog posts (the blogs also hold Urdu).

Method: the blog HTML splits some poems into one-word lines, so single lines are not tagged. Consecutive lines of a post are joined into
chunks of at least CHUNK letters. Each chunk is tagged with the Gojri/Urdu tagger (scripts/ocr_eval/langid.py, character n-gram; about 97%
right on lines of 61 or more letters). A chunk with a score between -MARGIN and +MARGIN is "unsure". The tagger learned the FLI spelling, so
the output is a draft for the speaker's check (build_blog_lang_review.py), not truth.

Run: py -3 -X utf8 scripts/corpus/filter_gojri_blog.py
Reads datasets/gojri-blogs/*/posts.jsonl; writes datasets/gojri-blogs/chunks.jsonl (all chunks with tag and score) and gojri_only.jsonl
(chunks tagged gju, with post id, url, title, labels for credit). Output is gitignored.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/ocr_eval"))
import langid as G  # noqa: E402

CHUNK = 80
MARGIN = 0.05
BLOGS = ROOT / "datasets/gojri-blogs"


def chunks(text):
    cur, n = [], 0
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        cur.append(line)
        n += len(G.letters(line))
        if n >= CHUNK:
            yield cur
            cur, n = [], 0
    if cur:
        if n >= G.MIN_LETTERS:
            yield cur
        elif cur and n:
            yield cur


def main():
    T = G.Tagger().fit(G.load_units())
    allc, keep = [], []
    stats = {}
    for f in sorted(BLOGS.glob("*/posts.jsonl")):
        blog = f.parent.name
        for i, l in enumerate(open(f, encoding="utf-8")):
            p = json.loads(l)
            for j, c in enumerate(chunks(p["text"])):
                text = "\n".join(c)
                letters = G.letters(text)
                if len(letters) < G.MIN_LETTERS:
                    tag, sc = "short", 0.0
                else:
                    u = {"text": text, "letters": letters, "marker": G.has_marker(text)}
                    sc = T.score(u)
                    tag = "gju" if sc > MARGIN else ("urd" if sc < -MARGIN else "unsure")
                rec = {"blog": blog, "post": p["id"], "url": p["url"], "title": p["title"], "labels": p["labels"],
                       "published": p["published"], "chunk": j, "tag": tag, "score": round(sc, 3), "letters": len(letters),
                       "words": len(text.split()), "text": text}
                allc.append(rec)
                s = stats.setdefault(blog, {})
                s[tag] = s.get(tag, 0) + rec["words"]
                if tag == "gju":
                    keep.append(rec)
    for name, rows in (("chunks.jsonl", allc), ("gojri_only.jsonl", keep)):
        with open(BLOGS / name, "w", encoding="utf-8") as fo:
            for r in rows:
                fo.write(json.dumps(r, ensure_ascii=False) + "\n")
    for blog, s in stats.items():
        print(blog, "words by tag:", s)
    print("kept chunks:", len(keep), "words:", sum(r["words"] for r in keep))


if __name__ == "__main__":
    main()
