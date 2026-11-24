"""Fetch posts of a public Blogger blog through its Atom/JSON feed.

Polite: one request every 2 seconds, a plain User-Agent, only the feed that
robots.txt allows. Output goes to a gitignored folder (third-party text).

Usage:
  py -3 -X utf8 scripts/corpus/fetch_blogger.py BLOG_URL OUT_DIR [--label LABEL]

Writes OUT_DIR/posts.jsonl (one post per line: id, url, title, published,
labels, text) and OUT_DIR/summary.txt.
"""
import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

UA = "gojri-research-fetch/1.0 (non-commercial language research)"
BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "blockquote"}


class Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
        if tag in BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def html_to_text(h):
    p = Text()
    p.feed(h)
    t = "".join(p.out).replace("\xa0", " ")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return "\n".join(l.strip() for l in t.split("\n")).strip()


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("blog")
    ap.add_argument("out")
    ap.add_argument("--label")
    ap.add_argument("--page", type=int, default=25)
    a = ap.parse_args()
    base = a.blog.rstrip("/") + "/feeds/posts/default"
    if a.label:
        base += "/-/" + urllib.parse.quote(a.label)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    start, n, words = 1, 0, 0
    with open(out / "posts.jsonl", "w", encoding="utf-8") as f:
        while True:
            d = get(f"{base}?alt=json&max-results={a.page}&start-index={start}")
            entries = d["feed"].get("entry", [])
            if not entries:
                break
            for e in entries:
                html = (e.get("content") or e.get("summary") or {}).get("$t", "")
                text = html_to_text(html)
                link = next((l["href"] for l in e.get("link", []) if l.get("rel") == "alternate"), "")
                rec = {
                    "id": e["id"]["$t"],
                    "url": link,
                    "title": e["title"]["$t"],
                    "published": e["published"]["$t"],
                    "labels": [c["term"] for c in e.get("category", [])],
                    "text": text,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
                words += len(text.split())
            print(f"fetched {n} posts, {words} words", flush=True)
            start += len(entries)
            time.sleep(2)
    (out / "summary.txt").write_text(f"{a.blog}\nlabel: {a.label}\nposts: {n}\nwords: {words}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
