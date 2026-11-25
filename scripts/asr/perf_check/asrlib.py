"""Shared scoring and audio code for the ASR performance check.

The normalisation and the scores are a copy of scripts/asr/sm_whisper/sm_whisper_entry.py (norm, scores), so the
numbers here are comparable with the SageMaker job. Keep the two in step.
"""
import csv
import re
import unicodedata

import jiwer

FOLD = str.maketrans({"ك": "ک", "ي": "ی", "ه": "ہ"})


def norm(s):
    s = unicodedata.normalize("NFC", s)
    s = "".join(c for c in s if not unicodedata.category(c).startswith(("M", "P")))
    return re.sub(r"\s+", " ", s.translate(FOLD)).strip()


def scores(refs, hyps):
    pairs = [(norm(r), norm(h)) for r, h in zip(refs, hyps) if norm(r)]
    rr, hh = [p[0] for p in pairs], [p[1] for p in pairs]
    return {"wer": round(100 * jiwer.wer(rr, hh), 2), "cer": round(100 * jiwer.cer(rr, hh), 2), "n": len(pairs)}


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE))


def write_tsv(path, rows, fields):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(fields)
        for r in rows:
            w.writerow([r[k] for k in fields])


def group_scores(rows):
    """rows: dicts with reference, hypothesis, speaker, seen. Returns overall, seen and unseen scores."""
    out = {"all": scores([r["reference"] for r in rows], [r["hypothesis"] for r in rows])}
    for name, flag in (("seen", "1"), ("unseen", "0")):
        sub = [r for r in rows if str(r["seen"]) == flag]
        if sub:
            out[name] = scores([r["reference"] for r in sub], [r["hypothesis"] for r in sub])
    return out
