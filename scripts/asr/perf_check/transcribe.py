"""Transcribe audio with the fine-tuned Whisper model (CPU or GPU). Same decoding as the SageMaker job:
language urdu, task transcribe, max_new_tokens 128, greedy search.

Two modes:
  --tsv FILE --clips DIR   rows with path, sentence, speaker (data/asr/splits/test.tsv); writes path, speaker, seen,
                           reference, hypothesis, seconds. --seen-speakers S1,S3 marks the training speakers.
  --audio-dir DIR          every audio file in DIR; writes file, hypothesis (own-voice test).
Run: python transcribe.py --model DIR --out FILE.tsv (--tsv ... --clips ... | --audio-dir ...) [--batch 16] [--limit N]
Output is local only: it holds Common Voice sentence text (tsv mode) or private recordings (audio-dir mode).
"""
import argparse
import csv
import os
import time

import numpy as np
import soundfile as sf
import torch
import torchaudio
from transformers import WhisperForConditionalGeneration, WhisperProcessor

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--tsv")
ap.add_argument("--clips")
ap.add_argument("--audio-dir")
ap.add_argument("--seen-speakers", default="S1,S3,S5")
ap.add_argument("--batch", type=int, default=16)
ap.add_argument("--limit", type=int, default=0)
ap.add_argument("--language", default="urdu", help="'none' = no forced language (Whisper detects it)")
ap.add_argument("--threads", type=int, default=0)
args = ap.parse_args()
if args.threads:
    torch.set_num_threads(args.threads)


def load_audio(path):
    x, sr = sf.read(path, dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    return x


if args.tsv:
    rows = list(csv.DictReader(open(args.tsv, encoding="utf-8", newline=""), delimiter="\t", quoting=csv.QUOTE_NONE))
    items = [(r["path"], os.path.join(args.clips, r["path"]), r) for r in rows]
else:
    names = sorted(f for f in os.listdir(args.audio_dir) if f.lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a")))
    items = [(n, os.path.join(args.audio_dir, n), {}) for n in names]
if args.limit:
    items = items[:args.limit]
seen = set(args.seen_speakers.split(","))

proc = WhisperProcessor.from_pretrained(args.model)
model = WhisperForConditionalGeneration.from_pretrained(args.model, torch_dtype=torch.float32).eval()
dev = "cuda" if torch.cuda.is_available() else "cpu"
model.to(dev)
print(f"{len(items)} clips on {dev}, {torch.get_num_threads()} threads, language={args.language}", flush=True)

kw = {"task": "transcribe", "max_new_tokens": 128}
if args.language != "none":
    kw["language"] = args.language
else:
    # The saved generation config pins language=urdu; clear it so Whisper detects the language per clip.
    model.generation_config.language = None
    model.generation_config.forced_decoder_ids = None

out = []
t0 = time.time()
with torch.no_grad():
    for i in range(0, len(items), args.batch):
        chunk = items[i:i + args.batch]
        feats = proc.feature_extractor([load_audio(p) for _, p, _ in chunk], sampling_rate=16000,
                                       return_tensors="pt").input_features.to(dev)
        ids = model.generate(feats, **kw)
        for (name, _, r), h in zip(chunk, proc.batch_decode(ids, skip_special_tokens=True)):
            row = {"path": name, "hypothesis": h}
            if r:
                row.update(speaker=r["speaker"], seen=int(r["speaker"] in seen), reference=r["sentence"])
            out.append(row)
        done = min(i + args.batch, len(items))
        print(f"{done}/{len(items)} {time.time() - t0:.0f}s", flush=True)

fields = ["path", "speaker", "seen", "reference", "hypothesis"] if args.tsv else ["path", "hypothesis"]
with open(args.out, "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(fields)
    for r in out:
        w.writerow([r[k] for k in fields])
print("wrote", args.out, f"in {(time.time() - t0) / 60:.1f} min")
