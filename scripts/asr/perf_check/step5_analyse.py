"""Step 5: error analysis of a predictions TSV (path, speaker, seen, reference, hypothesis).

Prints and writes (all to --outdir, local only, never commit): summary.json (numbers), top_errors.tsv, sample50.tsv
(50 random word substitutions for hand labelling), per_clip.tsv.
Word errors come from a jiwer alignment on the normalised text (same rule as the job).
Run: python step5_analyse.py --pred FILE --durations clip_durations.tsv --outdir DIR [--seed 20261123]
"""
import argparse
import collections
import csv
import json
import os
import random
import statistics
import unicodedata

import jiwer

from asrlib import group_scores, norm, read_tsv, scores

ap = argparse.ArgumentParser()
ap.add_argument("--pred", required=True)
ap.add_argument("--durations", required=True)
ap.add_argument("--outdir", required=True)
ap.add_argument("--seed", type=int, default=20261123)
args = ap.parse_args()
os.makedirs(args.outdir, exist_ok=True)

rows = read_tsv(args.pred)
dur = {r["clip"]: int(r["duration[ms]"]) / 1000 for r in read_tsv(args.durations)}
for r in rows:
    r["nref"], r["nhyp"] = norm(r["reference"]), norm(r["hypothesis"])
    r["sec"] = dur.get(r["path"], float("nan"))
rows = [r for r in rows if r["nref"]]

summary = {"clips": len(rows), "scores": group_scores(rows)}

# ---- alignment -------------------------------------------------------------------------------------------------
out = jiwer.process_words([r["nref"] for r in rows], [r["nhyp"] for r in rows])
summary["counts"] = {"substitutions": out.substitutions, "deletions": out.deletions, "insertions": out.insertions,
                     "hits": out.hits, "ref_words": out.substitutions + out.deletions + out.hits}
pairs = []  # (clip index, kind, ref word, hyp word)
for i, (al, r) in enumerate(zip(out.alignments, rows)):
    rw, hw = r["nref"].split(), r["nhyp"].split()
    for c in al:
        if c.type == "substitute":
            for k in range(c.ref_end_idx - c.ref_start_idx):
                pairs.append((i, "sub", rw[c.ref_start_idx + k], hw[c.hyp_start_idx + k]))
        elif c.type == "delete":
            pairs += [(i, "del", w, "") for w in rw[c.ref_start_idx:c.ref_end_idx]]
        elif c.type == "insert":
            pairs += [(i, "ins", "", w) for w in hw[c.hyp_start_idx:c.hyp_end_idx]]

freq = collections.Counter((k, a, b) for _, k, a, b in pairs)
top = freq.most_common(20)
summary["top20"] = [{"kind": k, "ref": a, "hyp": b, "n": n} for (k, a, b), n in top]
with open(os.path.join(args.outdir, "top_errors.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["kind", "ref", "hyp", "n"])
    for (k, a, b), n in freq.most_common(200):
        w.writerow([k, a, b, n])
errs = sum(freq.values())
summary["distinct_error_pairs"] = len(freq)
summary["top20_share_of_errors"] = round(100 * sum(n for _, n in top) / errs, 1)

# ---- automatic spelling-variant check -------------------------------------------------------------------------
STRONG = str.maketrans({"ں": "ن", "ے": "ی", "ۓ": "ی", "ۃ": "ہ", "ؤ": "و", "أ": "ا", "إ": "ا", "آ": "ا",
                        "ڵ": "ل", "ݨ": "ن", "ٹ": "ٹ"})


def strong(s):
    s = s.translate(STRONG).replace("ھ", "")
    return "".join(c for c in unicodedata.normalize("NFC", s) if not unicodedata.category(c).startswith("M"))


def edit1(a, b):
    return jiwer.cer([a], [b]) * len(a) <= 1.0 + 1e-9


def auto_class(a, b):
    if strong(a) == strong(b):
        return "fold-equal"
    return "near-1char" if len(a) >= 3 and edit1(a, b) else "other"


subs = [p for p in pairs if p[1] == "sub"]
ac = collections.Counter(auto_class(a, b) for _, _, a, b in subs)
summary["substitution_auto_class"] = dict(ac)

# ---- 50 random substitutions for hand labelling ----------------------------------------------------------------
rng = random.Random(args.seed)
pick = rng.sample(range(len(subs)), min(50, len(subs)))
with open(os.path.join(args.outdir, "sample50.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["id", "clip", "ref_word", "hyp_word", "auto_class", "ref_sentence", "hyp_sentence", "label", "note"])
    for n, j in enumerate(sorted(pick), 1):
        i, _, a, b = subs[j]
        w.writerow([n, rows[i]["path"], a, b, auto_class(a, b), rows[i]["nref"], rows[i]["nhyp"], "", ""])

# ---- per clip, by speaker, by length ---------------------------------------------------------------------------
per_clip = []
for r, al in zip(rows, out.alignments):
    s = sum(c.ref_end_idx - c.ref_start_idx for c in al if c.type == "substitute")
    d = sum(c.ref_end_idx - c.ref_start_idx for c in al if c.type == "delete")
    ins = sum(c.hyp_end_idx - c.hyp_start_idx for c in al if c.type == "insert")
    r["errors"] = s + d + ins
    per_clip.append([r["path"], r["speaker"], r["seen"], f"{r['sec']:.2f}", len(r["nref"].split()), len(r["nhyp"].split()),
                     r["errors"]])
with open(os.path.join(args.outdir, "per_clip.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["path", "speaker", "seen", "sec", "ref_words", "hyp_words", "errors"])
    w.writerows(per_clip)

summary["by_speaker"] = {sp: scores([r["reference"] for r in rows if r["speaker"] == sp],
                                    [r["hypothesis"] for r in rows if r["speaker"] == sp])
                         for sp in sorted({r["speaker"] for r in rows})}


def bucket(key, edges, labels):
    res = {}
    for lab, (lo, hi) in zip(labels, zip(edges[:-1], edges[1:])):
        sub = [r for r in rows if lo <= r[key] < hi]
        if sub:
            res[lab] = scores([r["reference"] for r in sub], [r["hypothesis"] for r in sub])
            res[lab]["median_" + key] = round(statistics.median(r[key] for r in sub), 2)
    return res


for r in rows:
    r["nwords"] = len(r["nref"].split())
secs = sorted(r["sec"] for r in rows)
q1, q2 = secs[len(secs) // 3], secs[2 * len(secs) // 3]
summary["by_duration"] = bucket("sec", [0, q1, q2, 1e9], [f"short (<{q1:.1f}s)", f"medium ({q1:.1f}-{q2:.1f}s)", f"long (>={q2:.1f}s)"])
summary["by_ref_words"] = bucket("nwords", [0, 6, 10, 1e9], ["1-5 words", "6-9 words", "10+ words"])

# ---- spacing-only errors ---------------------------------------------------------------------------------------
# A run of adjacent non-equal alignment chunks is "spacing only" when reference and hypothesis give the same letters
# once the spaces are removed (for example reference "یو ہ" against hypothesis "یوہ").
sp_err = sp_groups = tot_err = 0
for r, al in zip(rows, out.alignments):
    rw, hw = r["nref"].split(), r["nhyp"].split()
    grp = []
    for c in list(al) + [None]:
        if c is not None and c.type != "equal":
            grp.append(c)
            continue
        if grp:
            rs, re_ = grp[0].ref_start_idx, grp[-1].ref_end_idx
            hs, he = grp[0].hyp_start_idx, grp[-1].hyp_end_idx
            n_err = sum(max(g.ref_end_idx - g.ref_start_idx, g.hyp_end_idx - g.hyp_start_idx) if g.type == "substitute"
                        else (g.ref_end_idx - g.ref_start_idx) + (g.hyp_end_idx - g.hyp_start_idx) for g in grp)
            tot_err += n_err
            if "".join(rw[rs:re_]) == "".join(hw[hs:he]):
                sp_err += n_err
                sp_groups += 1
            grp = []
nref_words = summary["counts"]["ref_words"]
summary["spacing"] = {
    "spacing_only_error_groups": sp_groups, "errors_in_spacing_only_groups": sp_err, "all_errors": tot_err,
    "wer_if_spacing_only_groups_were_correct": round(100 * (tot_err - sp_err) / nref_words, 2),
    "single_letter_reference_tokens": sum(1 for r in rows for t in r["nref"].split() if len(t) == 1),
    "single_letter_hypothesis_tokens": sum(1 for r in rows for t in r["nhyp"].split() if len(t) == 1),
    "cer_ignoring_spaces": round(100 * jiwer.cer([r["nref"].replace(" ", "") for r in rows],
                                                 [r["nhyp"].replace(" ", "") for r in rows]), 2),
}

# ---- loops and empty output ------------------------------------------------------------------------------------


def looped(r):
    h = r["nhyp"].split()
    nr = r["nwords"]
    run = best = 1
    for a, b in zip(h, h[1:]):
        run = run + 1 if a == b else 1
        best = max(best, run)
    long_out = len(h) > 2 * nr + 3
    rep3 = best >= 3 and best > 2  # the same word three times in a row
    return long_out or rep3


summary["empty_output"] = sum(1 for r in rows if not r["nhyp"])
summary["loop_or_overlong_output"] = sum(1 for r in rows if looped(r))
summary["hyp_longer_than_ref_by_5+_words"] = sum(1 for r in rows if len(r["nhyp"].split()) - r["nwords"] >= 5)
summary["perfect_clips"] = sum(1 for r in rows if r["errors"] == 0)
summary["clips_with_3plus_errors"] = sum(1 for r in rows if r["errors"] >= 3)

with open(os.path.join(args.outdir, "summary.json"), "w", encoding="utf-8") as f:
    json.dump(summary, f, ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False, indent=1))
