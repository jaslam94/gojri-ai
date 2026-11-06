"""SageMaker entry: TrOCR-style Urdu models (VisionEncoderDecoder) on the Arabic-run crops.

Input channel `runs` holds the PNG crops and manifest.json (scripts/ocr_eval/dump_arabic_runs.py).
For each model, each crop is read in 2 image forms x 2 decoding settings:
  image:  raw        the crop as is (the processor squeezes it to 384 x 384, as in TrOCR training)
          padsq      the crop centred on a white square, so letter shapes keep their proportions
  decode: card       beam search 5, repetition_penalty 3.0 (setting recommended by the model cards)
          plain      greedy, no penalty (a repetition penalty of 3.0 can remove genuine repeated letters)
Output: /opt/ml/model/trocr_out.jsonl, one row per (model, crop, image, decode).
Models load with use_safetensors=True only (no pickle files are executed).
"""
import argparse
import json
import os
import time
from pathlib import Path

import torch
from PIL import Image
from transformers import AutoTokenizer, TrOCRProcessor, VisionEncoderDecoderModel, ViTImageProcessor

ap = argparse.ArgumentParser()
ap.add_argument("--models", required=True, help="comma-separated Hugging Face repo ids")
args = ap.parse_args()

RUNS = Path(os.environ.get("SM_CHANNEL_RUNS", "/opt/ml/input/data/runs"))
OUT = Path(os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
OUT.mkdir(parents=True, exist_ok=True)
man = json.loads((RUNS / "manifest.json").read_text(encoding="utf-8"))


def padsq(img):
    s = max(img.width, img.height) + 16
    c = Image.new("RGB", (s, s), "white")
    c.paste(img, ((s - img.width) // 2, (s - img.height) // 2))
    return c


DECODE = {
    "card": dict(max_length=128, num_beams=5, repetition_penalty=3.0, length_penalty=1.5, early_stopping=False),
    "plain": dict(max_length=128, num_beams=1, do_sample=False),
}

with (OUT / "trocr_out.jsonl").open("w", encoding="utf-8") as f:
    for repo in [m.strip() for m in args.models.split(",") if m.strip()]:
        t0 = time.time()
        try:
            model = VisionEncoderDecoderModel.from_pretrained(repo, use_safetensors=True).to("cuda").eval()
            try:
                proc = TrOCRProcessor.from_pretrained(repo)
                tok, imgproc = proc.tokenizer, proc.image_processor
            except Exception:  # repo without preprocessor_config.json: standard TrOCR image setup, tokenizer from repo
                tok = AutoTokenizer.from_pretrained(repo)
                imgproc = ViTImageProcessor(size={"height": 384, "width": 384}, image_mean=[0.5] * 3,
                                            image_std=[0.5] * 3, resample=2)
                print(repo, "using hand-built ViTImageProcessor (384, mean/std 0.5), as in its processor_config.json",
                      flush=True)
        except Exception as e:
            f.write(json.dumps({"model": repo, "error": f"load failed: {type(e).__name__}: {e}"}) + "\n")
            print(repo, "LOAD FAILED", e, flush=True)
            continue
        print(repo, "loaded", round(time.time() - t0), "s", flush=True)
        for m in man:
            img = Image.open(RUNS / m["file"]).convert("RGB")
            for iname, im in (("raw", img), ("padsq", padsq(img))):
                pv = imgproc(im, return_tensors="pt").pixel_values.to("cuda")
                for dname, kw in DECODE.items():
                    t = time.time()
                    try:
                        with torch.no_grad():
                            ids = model.generate(pv, **kw)
                        s = tok.batch_decode(ids, skip_special_tokens=True)[0]
                    except Exception as e:
                        s = f"[ERROR] {type(e).__name__}: {e}"
                    f.write(json.dumps({"model": repo, **m, "image": iname, "decode": dname, "text": s,
                                        "sec": round(time.time() - t, 3)}, ensure_ascii=False) + "\n")
        f.flush()
        print(repo, "done", round(time.time() - t0), "s", flush=True)
        del model
        torch.cuda.empty_cache()
print("all done", flush=True)
