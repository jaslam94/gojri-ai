"""Build the ASR train / dev / test split from Common Voice Scripted Speech 26.0, Gujari, and stage it on S3.

The official Common Voice split puts one speaker in train.tsv (3,207 clips, 2.9 h), none in dev.tsv, and five in
test.tsv (623 clips). With six speakers in all, most validated clips sit outside the official split. This split:
  test  = the official test.tsv (623 clips, 5 speakers).
  pool  = every validated clip whose sentence is not a test sentence (sentence-disjoint from test).
  dev   = all recordings of a random 5% of the pool sentences (seed 20261120), for checkpoint choice.
  train = the rest of the pool.
Two test speakers also read training sentences; the other three never appear in training. Report both groups.

Writes (local, gitignored): data/asr/splits/{train,dev,test}.tsv with path, sentence, speaker.
Writes (tracked): data/asr/split_clips.tsv with path, split, speaker only (no sentence text, no client id), so the
split can be rebuilt from a Common Voice download. Speaker labels S1..S6 follow the sorted client ids.
--upload copies the needed clips and the three TSV files to s3://$GOJRI_BUCKET/asr/cv-gju-26/ (private; Common Voice
terms forbid public re-hosting).
Run: py -3 -X utf8 scripts/asr/prepare_cv_split.py [--upload]
"""
import argparse
import csv
import os
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CV = ROOT / "datasets" / "cv-corpus-26.0-2026-06-12" / "gju"
OUT = ROOT / "data" / "asr"
SEED = 20261120


def read(name):
    return list(csv.DictReader(open(CV / name, encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--upload", action="store_true")
    args = ap.parse_args()
    val, test = read("validated.tsv"), read("test.tsv")
    ids = sorted({r["client_id"] for r in val + test})
    spk = {c: f"S{i + 1}" for i, c in enumerate(ids)}
    test_sent, test_path = {r["sentence"] for r in test}, {r["path"] for r in test}
    pool = [r for r in val if r["sentence"] not in test_sent and r["path"] not in test_path]
    sents = sorted({r["sentence"] for r in pool})
    rng = random.Random(SEED)
    dev_sent = set(rng.sample(sents, round(0.05 * len(sents))))
    split = {"train": [r for r in pool if r["sentence"] not in dev_sent],
             "dev": [r for r in pool if r["sentence"] in dev_sent], "test": test}
    (OUT / "splits").mkdir(parents=True, exist_ok=True)
    for name, rows in split.items():
        with open(OUT / "splits" / f"{name}.tsv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, delimiter="\t", lineterminator="\n")
            w.writerow(["path", "sentence", "speaker"])
            w.writerows([r["path"], r["sentence"], spk[r["client_id"]]] for r in rows)
        print(name, len(rows), "clips,", len({r["client_id"] for r in rows}), "speakers")
    with open(OUT / "split_clips.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["path", "split", "speaker"])
        for name, rows in split.items():
            w.writerows([r["path"], name, spk[r["client_id"]]] for r in sorted(rows, key=lambda r: r["path"]))
    if args.upload:
        import boto3
        s3 = boto3.client("s3")
        bucket = os.environ.get("GOJRI_BUCKET", "gojri-ai-sagemaker-data")
        pre = "asr/cv-gju-26/"
        for name in split:
            s3.upload_file(str(OUT / "splits" / f"{name}.tsv"), bucket, pre + f"{name}.tsv")
        clips = sorted({r["path"] for rows in split.values() for r in rows})
        with ThreadPoolExecutor(16) as ex:
            list(ex.map(lambda c: s3.upload_file(str(CV / "clips" / c), bucket, pre + "clips/" + c), clips))
        print("uploaded", len(clips), "clips to", f"s3://{bucket}/{pre}")


if __name__ == "__main__":
    main()
