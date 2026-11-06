"""SageMaker entry: Qaari-0.1-Urdu-OCR-VL-2B on the Arabic-run crops (GPU).

Input channel `runs` holds the PNG crops and manifest.json (made by
scripts/ocr_eval/dump_arabic_runs.py). Output goes to /opt/ml/model/qaari_out.jsonl,
one row per (crop, variant). Variants: raw crop, 2x upscale, 2x upscale on a padded
white canvas (the model was trained on larger text images, so size may matter).

Library versions are pinned in requirements.txt to the ones the adapter was made with.
The script stops if the adapter did not load (a plain Qwen2-VL would give void results).
"""
import json
import os
import time
from pathlib import Path

import torch
from peft import PeftModel
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

RUNS = Path(os.environ.get("SM_CHANNEL_RUNS", "/opt/ml/input/data/runs"))
OUT = Path(os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
BASE = "Qwen/Qwen2-VL-2B-Instruct"
ADAPTER = "oddadmix/Qaari-0.1-Urdu-OCR-VL-2B-Instruct"
PROMPT = ("Below is the image of one page of a document, as well as some raw textual content that was "
          "previously extracted for it. Just return the plain text representation of this document as if "
          "you were reading it naturally. Do not hallucinate.")  # exact prompt from the model card

model = Qwen2VLForConditionalGeneration.from_pretrained(BASE, torch_dtype=torch.bfloat16).to("cuda")
model = PeftModel.from_pretrained(model, ADAPTER)
lora_b = [p for n, p in model.named_parameters() if "lora_B" in n]
nonzero = sum(bool(p.abs().sum() > 0) for p in lora_b)
print(f"LoRA B tensors: {len(lora_b)}, non-zero: {nonzero}", flush=True)
assert lora_b and nonzero == len(lora_b), "adapter did not load, stop"
model = model.merge_and_unload().eval()
proc = AutoProcessor.from_pretrained(BASE)


def min_side(img, n=32):
    """Qwen2-VL needs both sides > 28 px: pad small crops with white."""
    if img.width >= n and img.height >= n:
        return img
    canvas = Image.new("RGB", (max(img.width, n), max(img.height, n)), "white")
    canvas.paste(img, ((canvas.width - img.width) // 2, (canvas.height - img.height) // 2))
    return canvas


def variants(img):
    img = min_side(img)
    yield "raw", img
    up = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
    yield "up2", up
    pad = 60
    canvas = Image.new("RGB", (up.width + 2 * pad, up.height + 2 * pad), "white")
    canvas.paste(up, (pad, pad))
    yield "up2pad", canvas


man = json.loads((RUNS / "manifest.json").read_text(encoding="utf-8"))
OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "qaari_out.jsonl").open("w", encoding="utf-8") as f:
    for i, m in enumerate(man):
        img = Image.open(RUNS / m["file"]).convert("RGB")
        for vname, vimg in variants(img):
            msgs = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
            text = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
            t = time.time()
            try:
                inp = proc(text=[text], images=[vimg], return_tensors="pt").to("cuda")
                with torch.no_grad():
                    ids = model.generate(**inp, max_new_tokens=100, do_sample=False)
                s = proc.batch_decode(ids[:, inp.input_ids.shape[1]:], skip_special_tokens=True)[0]
            except Exception as e:  # keep going, record the error
                s = f"[ERROR] {type(e).__name__}: {e}"
            f.write(json.dumps({**m, "variant": vname, "text": s, "sec": round(time.time() - t, 2)},
                               ensure_ascii=False) + "\n")
        f.flush()
        if i % 20 == 0:
            print(i, m["file"], s[:50], flush=True)
print("done", flush=True)
