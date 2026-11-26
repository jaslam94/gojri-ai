"""Convert our Common Voice Gujari split to the parquet layout of the Omnilingual ASR training recipe.

Layout (workflows/dataprep/README.md in facebookresearch/omnilingual-asr):
  OUT/version=0/corpus=cv/split=<train|dev|test>/language=gju_Arab/part-00000.parquet
Columns: text (string), audio_bytes (list<int8>, flac at 16 kHz mono), audio_size (int64, samples at 16 kHz). row_group_size=100.
Also writes OUT/language_distribution_0.tsv (corpus, language, hours) and OUT/gojri_cv_gju26.yaml (the dataset card; DATA_PATH is
replaced by the job). The test split is written for scoring only; the recipe trains on `train` and validates on `dev`.

Text: NFC, punctuation removed, then every character the Omnilingual tokenizer cannot represent is dropped (with --tokenizer), spaces
collapsed. Checked 2026-11-26: 2.35% of the training label characters (short vowel marks damma, kasra, fatha, shadda, sukun, and a few
symbols) are unknown to `omniASR_tokenizer_v1`; kept in the labels they would become unknown tokens. The scorer removes marks on both sides,
so dropping them does not change the score.
Common Voice terms forbid re-hosting: keep OUT local or on private S3.

Run: py -3 -X utf8 scripts/asr/omni_ft/make_parquet.py OUT_DIR --tokenizer omniASR_tokenizer.model [--limit N]
Tokenizer file: https://dl.fbaipublicfiles.com/mms/omniASR_tokenizer.model (the 7B LLM uses omniASR_tokenizer_v7.model).
"""
import argparse
import csv
import io
import collections
import re
import unicodedata
from pathlib import Path

import librosa
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import sentencepiece as spm
import soundfile as sf

ROOT = Path(__file__).resolve().parents[3]
SPLITS = ROOT / "data/asr/splits"
CLIPS = ROOT / "datasets/cv-corpus-26.0-2026-06-12/gju/clips"
SR = 16000
LANG = "gju_Arab"


SP = None
DROPPED = collections.Counter()


def known(c):
    if c == " ":
        return True
    return SP.piece_to_id(c) != SP.unk_id() and SP.encode(c) != [SP.unk_id()]


def clean(s):
    s = unicodedata.normalize("NFC", s)
    s = "".join(c for c in s if not unicodedata.category(c).startswith("P"))
    if SP is not None:
        kept = []
        for c in s:
            if known(c):
                kept.append(c)
            else:
                DROPPED[c] += 1
        s = "".join(kept)
    return re.sub(r"\s+", " ", s).strip()


def flac_bytes(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != SR:
        x = librosa.resample(x, orig_sr=sr, target_sr=SR)
    buf = io.BytesIO()
    sf.write(buf, x, SR, format="FLAC", subtype="PCM_16")
    return buf.getvalue(), len(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--limit", type=int, default=0, help="clips per split (test runs)")
    ap.add_argument("--tokenizer", help="sentencepiece model of the Omnilingual tokenizer; drops unknown characters from the text")
    a = ap.parse_args()
    global SP
    if a.tokenizer:
        SP = spm.SentencePieceProcessor()
        SP.load(a.tokenizer)
    out = Path(a.out)
    hours = 0.0
    for split in ("train", "dev", "test"):
        rows = list(csv.DictReader(open(SPLITS / f"{split}.tsv", encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
        if a.limit:
            rows = rows[:a.limit]
        texts, blobs, sizes = [], [], []
        for r in rows:
            b, n = flac_bytes(str(CLIPS / r["path"]))
            texts.append(clean(r["sentence"]))
            blobs.append(np.frombuffer(b, dtype=np.int8))
            sizes.append(n)
        offsets = np.concatenate([[0], np.cumsum([len(b) for b in blobs])]).astype(np.int32)
        audio = pa.ListArray.from_arrays(pa.array(offsets), pa.array(np.concatenate(blobs), type=pa.int8()))
        table = pa.table({"text": pa.array(texts, pa.string()), "audio_bytes": audio, "audio_size": pa.array(sizes, pa.int64())})
        d = out / "version=0" / "corpus=cv" / f"split={split}" / f"language={LANG}"
        d.mkdir(parents=True, exist_ok=True)
        pq.write_table(table, d / "part-00000.parquet", row_group_size=100)
        h = sum(sizes) / 3600 / SR
        hours += h
        print(f"{split}: {len(rows)} clips, {h:.2f} h", flush=True)
    with open(out / "language_distribution_0.tsv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["corpus", "language", "hours"])
        w.writerow(["cv", LANG, hours])
    (out / "gojri_cv_gju26.yaml").write_text(
        "name: gojri_cv_gju26\ndataset_family: mixture_parquet_asr_dataset\ndataset_config:\n  data: DATA_PATH/version=0\n"
        "tokenizer_ref: omniASR_tokenizer_v1\n", encoding="utf-8")
    print("total hours", round(hours, 3), "->", out)
    if SP is not None:
        print("dropped characters:", {f"U+{ord(c):04X}": n for c, n in DROPPED.most_common()})


if __name__ == "__main__":
    main()
