"""SageMaker entry: Qaari-0.1-Urdu-OCR-VL-2B on whole page images (its intended input).

Input channel `pages` holds the gold page PNGs (data/gold/images_cropped). Output:
/opt/ml/model/qaari_pages.jsonl, one row per page (greedy decoding, up to 1500 new tokens, model-card prompt).
Stops if the LoRA adapter did not load.
"""
import json
import os
import time
from pathlib import Path

import torch
from peft import PeftModel
from PIL import Image
from transformers import AutoProcessor, Qwen2VLForConditionalGeneration

PAGES = Path(os.environ.get("SM_CHANNEL_PAGES", "/opt/ml/input/data/pages"))
OUT = Path(os.environ.get("SM_MODEL_DIR", "/opt/ml/model"))
BASE = "Qwen/Qwen2-VL-2B-Instruct"
ADAPTER = "oddadmix/Qaari-0.1-Urdu-OCR-VL-2B-Instruct"
PROMPT = ("Below is the image of one page of a document, as well as some raw textual content that was "
          "previously extracted for it. Just return the plain text representation of this document as if "
          "you were reading it naturally. Do not hallucinate.")

model = Qwen2VLForConditionalGeneration.from_pretrained(BASE, torch_dtype=torch.bfloat16).to("cuda")
model = PeftModel.from_pretrained(model, ADAPTER)
lora_b = [p for n, p in model.named_parameters() if "lora_B" in n]
nonzero = sum(bool(p.abs().sum() > 0) for p in lora_b)
print(f"LoRA B tensors: {len(lora_b)}, non-zero: {nonzero}", flush=True)
assert lora_b and nonzero == len(lora_b), "adapter did not load, stop"
model = model.merge_and_unload().eval()
proc = AutoProcessor.from_pretrained(BASE)

OUT.mkdir(parents=True, exist_ok=True)
with (OUT / "qaari_pages.jsonl").open("w", encoding="utf-8") as f:
    for p in sorted(PAGES.glob("*.png")):
        img = Image.open(p).convert("RGB")
        msgs = [{"role": "user", "content": [{"type": "image"}, {"type": "text", "text": PROMPT}]}]
        text = proc.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)
        t = time.time()
        try:
            inp = proc(text=[text], images=[img], return_tensors="pt").to("cuda")
            with torch.no_grad():
                ids = model.generate(**inp, max_new_tokens=1500, do_sample=False)
            s = proc.batch_decode(ids[:, inp.input_ids.shape[1]:], skip_special_tokens=True)[0]
        except Exception as e:
            s = f"[ERROR] {type(e).__name__}: {e}"
        f.write(json.dumps({"page": p.stem, "text": s, "sec": round(time.time() - t, 1)}, ensure_ascii=False) + "\n")
        f.flush()
        print(p.stem, round(time.time() - t, 1), len(s), flush=True)
print("done", flush=True)
