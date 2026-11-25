"""SageMaker entry: fine-tune Whisper on Common Voice Gujari and score it (zero-shot baseline, then fine-tuned).

Channel `data` = s3://$GOJRI_BUCKET/asr/cv-gju-26/ (train.tsv, dev.tsv, test.tsv with path, sentence, speaker; clips/).
Whisper has no Gojri token; the Urdu token is used (same script, close vocabulary).
Scores (word error, WER; character error, CER) use one normalisation on both sides: NFC, short-vowel and other
combining marks removed, punctuation removed, ك=ک, ي=ی, ه=ہ folded (ھ stays separate), spaces collapsed.
The test set is reported overall, for speakers who also read training sentences ("seen"), and for speakers who never
appear in training ("unseen"). Output in /opt/ml/model: results.json, test_predictions.tsv, and the best model (fp16).
"""
import argparse
import csv
import json
import os
import re
import time
import unicodedata

import jiwer
import numpy as np
import soundfile as sf
import torch
import torchaudio
from transformers import (Seq2SeqTrainer, Seq2SeqTrainingArguments, WhisperForConditionalGeneration,
                          WhisperProcessor)

ap = argparse.ArgumentParser()
ap.add_argument("--model", default="openai/whisper-small")
ap.add_argument("--max-steps", type=int, default=2500)
ap.add_argument("--lr", type=float, default=1e-5)
ap.add_argument("--warmup", type=int, default=300)
ap.add_argument("--batch", type=int, default=16, help="per-step batch; effective batch = batch x grad-accum")
ap.add_argument("--grad-accum", type=int, default=1)
ap.add_argument("--grad-ckpt", type=int, default=0, help="1 = gradient checkpointing (less GPU memory, slower; for medium and larger)")
ap.add_argument("--eval-every", type=int, default=500)
ap.add_argument("--limit-train", type=int, default=0)
ap.add_argument("--limit-eval", type=int, default=0, help="cap on dev and test clips (smoke test only)")
ap.add_argument("--seed", type=int, default=0)
args = ap.parse_args()

DATA = os.environ.get("SM_CHANNEL_DATA", "data")
OUT = os.environ.get("SM_MODEL_DIR", "out")
os.makedirs(OUT, exist_ok=True)
torch.manual_seed(args.seed)
np.random.seed(args.seed)


def read(name, limit=0):
    rows = list(csv.DictReader(open(os.path.join(DATA, name), encoding="utf-8"), delimiter="\t", quoting=csv.QUOTE_NONE))
    return rows[:limit] if limit else rows


train, dev, test = read("train.tsv", args.limit_train), read("dev.tsv", args.limit_eval), read("test.tsv", args.limit_eval)
seen = {r["speaker"] for r in train}
print(f"train {len(train)} dev {len(dev)} test {len(test)}; training speakers {sorted(seen)}", flush=True)

FOLD = str.maketrans({"ك": "ک", "ي": "ی", "ه": "ہ"})


def norm(s):
    s = unicodedata.normalize("NFC", s)
    s = "".join(c for c in s if not unicodedata.category(c).startswith(("M", "P")))
    return re.sub(r"\s+", " ", s.translate(FOLD)).strip()


def scores(refs, hyps):
    pairs = [(norm(r), norm(h)) for r, h in zip(refs, hyps) if norm(r)]
    rr, hh = [p[0] for p in pairs], [p[1] for p in pairs]
    return {"wer": round(100 * jiwer.wer(rr, hh), 2), "cer": round(100 * jiwer.cer(rr, hh), 2), "n": len(pairs)}


def audio(path):
    x, sr = sf.read(os.path.join(DATA, "clips", path), dtype="float32")
    if x.ndim > 1:
        x = x.mean(axis=1)
    if sr != 16000:
        x = torchaudio.functional.resample(torch.from_numpy(x), sr, 16000).numpy()
    return x


proc = WhisperProcessor.from_pretrained(args.model, language="urdu", task="transcribe")
model = WhisperForConditionalGeneration.from_pretrained(args.model)
model.generation_config.language = "urdu"
model.generation_config.task = "transcribe"
model.generation_config.forced_decoder_ids = None
if args.grad_ckpt:
    model.config.use_cache = False  # the cache and gradient checkpointing do not mix during training
dev_ = "cuda" if torch.cuda.is_available() else "cpu"


class DS(torch.utils.data.Dataset):
    def __init__(self, rows):
        self.rows = rows

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        return {"audio": audio(r["path"]), "text": r["sentence"]}


def collate(batch):
    feats = proc.feature_extractor([b["audio"] for b in batch], sampling_rate=16000, return_tensors="pt").input_features
    lab = proc.tokenizer([b["text"] for b in batch], padding=True, return_tensors="pt")
    labels = lab.input_ids.masked_fill(lab.attention_mask.ne(1), -100)
    if (labels[:, 0] == model.config.decoder_start_token_id).all():
        labels = labels[:, 1:]
    return {"input_features": feats, "labels": labels}


@torch.no_grad()
def transcribe(rows, m):
    m.eval().to(dev_)
    hyps = []
    for i in range(0, len(rows), args.batch):
        chunk = rows[i:i + args.batch]
        feats = proc.feature_extractor([audio(r["path"]) for r in chunk], sampling_rate=16000,
                                       return_tensors="pt").input_features.to(dev_)
        if dev_ == "cuda":
            feats = feats.half() if next(m.parameters()).dtype == torch.float16 else feats
        ids = m.generate(feats, language="urdu", task="transcribe", max_new_tokens=128)
        hyps += proc.batch_decode(ids, skip_special_tokens=True)
    return hyps


def report(rows, hyps):
    refs = [r["sentence"] for r in rows]
    out = {"all": scores(refs, hyps)}
    for name, keep in (("seen_speakers", lambda r: r["speaker"] in seen), ("unseen_speakers", lambda r: r["speaker"] not in seen)):
        idx = [i for i, r in enumerate(rows) if keep(r)]
        if idx:
            out[name] = scores([refs[i] for i in idx], [hyps[i] for i in idx])
    return out


t0 = time.time()
results = {"model": args.model, "args": vars(args), "split": {"train": len(train), "dev": len(dev), "test": len(test)},
           "training_speakers": sorted(seen)}
results["zero_shot_test"] = report(test, transcribe(test, model))
print("zero-shot test:", results["zero_shot_test"], flush=True)


def compute_metrics(pred):
    ids = np.where(pred.predictions != -100, pred.predictions, proc.tokenizer.pad_token_id)
    lab = np.where(pred.label_ids != -100, pred.label_ids, proc.tokenizer.pad_token_id)
    return scores(proc.batch_decode(lab, skip_special_tokens=True), proc.batch_decode(ids, skip_special_tokens=True))


targs = Seq2SeqTrainingArguments(
    output_dir="/tmp/ckpt", per_device_train_batch_size=args.batch, per_device_eval_batch_size=args.batch,
    learning_rate=args.lr, warmup_steps=args.warmup, max_steps=args.max_steps, fp16=dev_ == "cuda",
    gradient_accumulation_steps=args.grad_accum, gradient_checkpointing=bool(args.grad_ckpt),
    eval_strategy="steps", eval_steps=args.eval_every, save_steps=args.eval_every, save_total_limit=2,
    load_best_model_at_end=True, metric_for_best_model="wer", greater_is_better=False, predict_with_generate=True,
    generation_max_length=128, logging_steps=50, report_to=[], remove_unused_columns=False,
    dataloader_num_workers=4, seed=args.seed)
trainer = Seq2SeqTrainer(model=model, args=targs, train_dataset=DS(train), eval_dataset=DS(dev), data_collator=collate,
                         compute_metrics=compute_metrics, tokenizer=proc.feature_extractor)
trainer.train()
results["dev_history"] = [h for h in trainer.state.log_history if "eval_wer" in h]
best = trainer.model
best.config.use_cache = True
hyps = transcribe(test, best)
results["fine_tuned_test"] = report(test, hyps)
results["minutes"] = round((time.time() - t0) / 60, 1)
print("fine-tuned test:", results["fine_tuned_test"], flush=True)
with open(os.path.join(OUT, "results.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=1)
with open(os.path.join(OUT, "test_predictions.tsv"), "w", encoding="utf-8", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["path", "speaker", "seen", "reference", "hypothesis"])
    for r, h in zip(test, hyps):
        w.writerow([r["path"], r["speaker"], int(r["speaker"] in seen), r["sentence"], h])
best.half().save_pretrained(os.path.join(OUT, "model"), safe_serialization=True)
proc.save_pretrained(os.path.join(OUT, "model"))
print("done in", results["minutes"], "min", flush=True)
