"""SageMaker entry: train SegNet (script segmenter) on per-column labels of real dictionary lines.

Input channel `data`: seg_data.pkl.gz from scripts/ocr_eval/build_segmenter_data.py (trusted, own data).
Output: /opt/ml/model/segnet.pt (state dict), metrics.json (test column accuracy and confusion).
Augmentation: random width and height scale, brightness/contrast, noise, blur (to resemble scans).
"""
import argparse
import gzip
import json
import os
import pickle
import random
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from segnet import SegNet

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=int, default=14)
ap.add_argument("--bs", type=int, default=16)
ap.add_argument("--lr", type=float, default=2e-3)
ap.add_argument("--limit", type=int, default=0, help="smoke test on N train lines")
args = ap.parse_args()
torch.manual_seed(0); random.seed(0); np.random.seed(0)

DATA = Path(os.environ.get("SM_CHANNEL_DATA", "/opt/ml/input/data/data"))
OUT = Path(os.environ.get("SM_MODEL_DIR", "/opt/ml/model")); OUT.mkdir(parents=True, exist_ok=True)
items = pickle.load(gzip.open(next(DATA.glob("*.pkl.gz")), "rb"))
train = [d for d in items if d["split"] == "train"]
test = [d for d in items if d["split"] == "test"]
if args.limit:
    train, test = train[: args.limit], test[: max(8, args.limit // 4)]
print(len(train), "train lines,", len(test), "test lines", flush=True)
dev = "cuda" if torch.cuda.is_available() else "cpu"
H = 64


def augment(img, lab):
    """img (64, W) uint8 paper-white, lab (W,) -> float tensors; random scale, photometric noise."""
    x = torch.from_numpy(img).float()[None, None] / 255.0
    sw, sh = random.uniform(0.75, 1.3), random.uniform(0.8, 1.2)
    w2, h2 = max(16, int(x.shape[-1] * sw)), max(40, int(H * sh))
    x = F.interpolate(x, size=(h2, w2), mode="bilinear", align_corners=False)
    lab = torch.from_numpy(lab)[None, None].float()
    lab = F.interpolate(lab, size=w2, mode="nearest")[0, 0].long()
    if h2 >= H:
        t = (h2 - H) // 2
        x = x[:, :, t:t + H]
    else:
        pad = H - h2
        x = F.pad(x, (0, 0, pad // 2, pad - pad // 2), value=1.0)
    if random.random() < 0.4:
        x = F.avg_pool2d(x, 3, 1, 1)
    c, b = random.uniform(0.6, 1.2), random.uniform(-0.15, 0.15)
    x = ((x - 0.5) * c + 0.5 + b + torch.randn_like(x) * random.uniform(0, 0.06)).clamp(0, 1)
    return (x[0] - 0.5) / 0.5, lab


def plain(img, lab):
    x = torch.from_numpy(img).float()[None] / 255.0
    return (x - 0.5) / 0.5, torch.from_numpy(lab).long()


def batchify(pairs):
    w = max(p[0].shape[-1] for p in pairs)
    xs = torch.ones(len(pairs), 1, H, w)
    ys = torch.full((len(pairs), w), -100, dtype=torch.long)
    for i, (x, y) in enumerate(pairs):
        xs[i, :, :, :x.shape[-1]] = x
        ys[i, :len(y)] = y
    return xs.to(dev), ys.to(dev)


net = SegNet().to(dev)
opt = torch.optim.AdamW(net.parameters(), lr=args.lr, weight_decay=1e-4)
steps = args.epochs * ((len(train) + args.bs - 1) // args.bs)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr, total_steps=steps)
cnt = np.bincount(np.concatenate([d["lab"] for d in train]), minlength=3).astype("float64")
freq = cnt / cnt.sum()
wts = (freq.max() / freq) ** 0.5  # inverse square-root class frequency, most common class = 1
print("train column share gap/arabic/latin:", np.round(freq, 3).tolist(), "loss weights:", np.round(wts, 2).tolist(), flush=True)
lossf = torch.nn.CrossEntropyLoss(weight=torch.tensor(wts, dtype=torch.float32, device=dev), ignore_index=-100)


def evaluate():
    net.eval()
    cm = np.zeros((3, 3), dtype=np.int64)
    with torch.no_grad():
        for i in range(0, len(test), 8):
            x, y = batchify([plain(d["img"], d["lab"]) for d in test[i:i + 8]])
            p = net(x).argmax(1)
            m = y != -100
            for a in range(3):
                for b in range(3):
                    cm[a, b] += int(((y == a) & (p == b) & m).sum())
    net.train()
    return cm


t0 = time.time()
for ep in range(args.epochs):
    random.shuffle(train)
    tot = 0.0
    for i in range(0, len(train), args.bs):
        x, y = batchify([augment(d["img"], d["lab"]) for d in train[i:i + args.bs]])
        loss = lossf(net(x), y)
        opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        tot += float(loss) * len(y)
    cm = evaluate()
    acc = cm.trace() / cm.sum()
    nonblank = cm[1:, 1:]
    print(f"epoch {ep + 1}/{args.epochs} loss {tot / len(train):.4f} test column acc {100 * acc:.2f}% "
          f"arabic<->latin confusion {int(cm[1, 2] + cm[2, 1])} columns ({time.time() - t0:.0f}s)", flush=True)

cm = evaluate()
torch.save(net.state_dict(), OUT / "segnet.pt")
(OUT / "metrics.json").write_text(json.dumps({"confusion_rows_true_cols_pred_gap_arabic_latin": cm.tolist(),
                                              "test_column_accuracy": float(cm.trace() / cm.sum())}), encoding="utf-8")
print("saved", flush=True)
