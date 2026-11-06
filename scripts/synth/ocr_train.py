"""CRNN-CTC line-OCR trainer for Gojri (CPU first).

Data (cleaned label files, see make_clean_labels.py):
  data/synth/line_full/labels_clean.jsonl   synthetic, clean + 3 degraded copies
  data/synth/real_pairs/labels_merged_clean.jsonl  real print crops from the dictionary PDF

Each epoch sees every unique line once. A synthetic line shows one random copy
of its 4 images. Real lines repeat --real-rep times, so print is not drowned out.

Validation groups: one dictionary page (synthetic and real rows share the key)
or one block of 40 FLI lines. A group is never split between train and val.
Held-out check: the 23 real crops of page 25 (gold page dict_alif). They never
train. This is a dictionary-only check, not a poetry check. The 200 lines the
user reviewed are also kept out of training (make_clean_labels.py).

Run from the repo root:
  py -3 -X utf8 scripts/synth/ocr_train.py --limit 300 --epochs 2   correctness run
  py -3 -X utf8 scripts/synth/ocr_train.py                           full run
"""
import argparse
import json
import math
import os
import random
import re
import time
import unicodedata
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, Dataset

ROOT = Path(__file__).resolve().parent.parent.parent
SYNTH = Path(os.environ.get("GOJRI_SYNTH", ROOT / "data" / "synth"))
OUT_DIR = Path(os.environ.get("SM_MODEL_DIR", SYNTH / "ocr_model"))
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

IMG_H = 64
MAX_W = 1400
TIME_DIV = 4  # CNN shrinks width by 4, so T = width // 4
BLANK = 0


def norm(t):
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", t).strip())


def group_key(r):
    pl = r["page_line"]
    head, _, line = pl.rpartition(":")
    if r["source_tag"] in ("dictionary", "batool_print"):
        return head.replace("-pass2", "")
    return f"{head}#{int(line.lstrip('L') or 0) // 40}"


def needs_steps(text):
    """CTC needs one step per char, plus one more per repeated neighbour."""
    return len(text) + sum(1 for a, b in zip(text, text[1:]) if a == b)


def load_rows(real_rep):
    rows, dropped = [], 0
    for name, real in (("line_full", False), ("real_pairs", True)):
        base = SYNTH / name
        for line in (base / ("labels_merged_clean.jsonl" if real else "labels_clean.jsonl")).open(encoding="utf-8"):
            r = json.loads(line)
            text = norm(r["text"])
            nw = max(16, min(MAX_W, int(r["width_px"] * IMG_H / r["height_px"])))
            if not text or nw // TIME_DIV < needs_steps(text):
                dropped += 1
                continue
            imgs = [base / r["image"]]
            if not real:
                imgs += [base / r["image"].replace(".png", f"_v{i}.png") for i in (1, 2, 3)]
            rows.append({"imgs": imgs, "text": text, "group": group_key(r),
                         "src": "real" if real else "synth", "rep": real_rep if real else 1})
    return rows, dropped


def holdout_rows():
    """Real crops of gold page 25 with the merged labels. Not in labels_merged_clean.jsonl, so never trained on."""
    base = SYNTH / "real_pairs"
    out = []
    for line in (base / "labels_merged.jsonl").open(encoding="utf-8"):
        r = json.loads(line)
        if r["page_line"].startswith("page-0025:") and not r.get("folio"):
            out.append({"imgs": [base / r["image"]], "text": norm(r["text"]),
                        "group": "page-0025", "src": "real", "rep": 1})
    return out


class Charset:
    def __init__(self, texts):
        chars = sorted({c for t in texts for c in t})
        self.chars = ["<blank>"] + chars
        self.idx = {c: i for i, c in enumerate(self.chars)}

    def encode(self, t):
        return [self.idx[c] for c in t if c in self.idx]

    def decode(self, seq):
        out, prev = [], BLANK
        for s in seq:
            if s != prev and s != BLANK:
                out.append(self.chars[s])
            prev = s
        return "".join(out)


class LineDS(Dataset):
    def __init__(self, rows, cs, train):
        self.rows, self.cs, self.train = rows, cs, train

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        p = random.choice(r["imgs"]) if self.train else r["imgs"][0]
        im = Image.open(p).convert("L")
        w, h = im.size
        nw = max(16, min(MAX_W, int(w * IMG_H / h)))
        im = im.resize((nw, IMG_H), Image.LANCZOS)
        a = 1.0 - np.asarray(im, dtype="float32") / 255.0  # ink = 1, paper = 0
        lab = torch.tensor(self.cs.encode(r["text"]), dtype=torch.long)
        return torch.from_numpy(a), nw, lab, r["text"], r["src"]


def collate(batch):
    W = max(math.ceil(b[1] / 8) * 8 for b in batch)
    x = torch.zeros(len(batch), 1, IMG_H, W)
    for i, b in enumerate(batch):
        x[i, 0, :, :b[1]] = b[0]
    widths = torch.tensor([b[1] // TIME_DIV for b in batch], dtype=torch.long)
    labs = [b[2] for b in batch]
    lab_lens = torch.tensor([len(l) for l in labs], dtype=torch.long)
    return x, widths, torch.cat(labs), lab_lens, [b[3] for b in batch], [b[4] for b in batch]


class CRNN(nn.Module):
    def __init__(self, n_classes):
        super().__init__()

        def blk(i, o, pool):
            return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.BatchNorm2d(o),
                                 nn.ReLU(), nn.MaxPool2d(pool), nn.Dropout2d(0.1))
        self.cnn = nn.Sequential(
            blk(1, 32, (2, 2)),     # 64 -> 32 high, width / 2
            blk(32, 64, (2, 2)),    # 32 -> 16 high, width / 4
            blk(64, 128, (2, 1)),   # 16 -> 8 high
            blk(128, 128, (2, 1)),  # 8 -> 4 high
        )
        self.rnn = nn.LSTM(128 * 4, 192, num_layers=2, bidirectional=True, batch_first=True)
        self.fc = nn.Linear(384, n_classes)

    def forward(self, x):
        f = self.cnn(x)                                  # B, C, 4, T
        b, c, h, t = f.shape
        f = f.permute(0, 3, 1, 2).reshape(b, t, c * h)   # B, T, C*H
        o, _ = self.rnn(f)
        return F.log_softmax(self.fc(o), dim=2).permute(1, 0, 2)  # T, B, classes (CTC order)


def edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1]


SCORE_FOLD = str.maketrans({"ك": "ک", "ه": "ہ"})  # ك=ک, ه=ہ; ھ stays apart


def score(refs, hyps):
    we = wn = ce = cn = 0
    for r, h in zip(refs, hyps):
        r, h = r.translate(SCORE_FOLD), h.translate(SCORE_FOLD)
        we += edit_distance(r.split(), h.split())
        wn += len(r.split())
        ce += edit_distance(r, h)
        cn += len(r)
    return 100.0 * we / max(1, wn), 100.0 * ce / max(1, cn)


@torch.no_grad()
def evaluate(net, cs, rows, bs):
    if not rows:
        return {}
    net.eval()
    ld = DataLoader(LineDS(rows, cs, False), batch_size=bs, collate_fn=collate)
    refs = {"real": [], "synth": []}
    hyps = {"real": [], "synth": []}
    for x, _w, _l, _ll, texts, srcs in ld:
        best = net(x.to(DEVICE)).argmax(2).permute(1, 0).cpu()  # B, T
        for seq, t, s in zip(best.tolist(), texts, srcs):
            refs[s].append(t)
            hyps[s].append(cs.decode(seq))
    out = {}
    for s in refs:
        if refs[s]:
            wer, cer = score(refs[s], hyps[s])
            out[s] = (wer, cer, len(refs[s]), refs[s][0], hyps[s][0])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0, help="use only N random rows (test run)")
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--bs", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--real-rep", type=int, default=3)
    ap.add_argument("--workers", type=int, default=2)
    args = ap.parse_args()

    torch.manual_seed(7)
    random.seed(7)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows, dropped = load_rows(args.real_rep)
    print(f"torch {torch.__version__} | device {DEVICE} | threads {torch.get_num_threads()} | "
          f"rows {len(rows)} (dropped {dropped} too short for CTC)", flush=True)
    if args.limit:
        random.shuffle(rows)
        rows = rows[:args.limit]

    groups = sorted({r["group"] for r in rows})
    random.Random(11).shuffle(groups)
    val_groups = set(groups[:max(2, len(groups) // 30)])
    train = [r for r in rows if r["group"] not in val_groups]
    val = [r for r in rows if r["group"] in val_groups]
    hold = holdout_rows()
    cs = Charset([r["text"] for r in train])
    unseen = {c for r in val + hold for c in r["text"]} - set(cs.chars)
    print(f"train {len(train)} | val {len(val)} | page-25 holdout {len(hold)} | "
          f"charset {len(cs.chars)} | val chars unseen in train: {len(unseen)}", flush=True)

    epoch_rows = [r for r in train for _ in range(r["rep"])]
    ld = DataLoader(LineDS(epoch_rows, cs, True), batch_size=args.bs, shuffle=True,
                    collate_fn=collate, num_workers=args.workers, drop_last=True,
                    persistent_workers=args.workers > 0)
    net = CRNN(len(cs.chars)).to(DEVICE)
    opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=args.lr,
                                                total_steps=args.epochs * len(ld))
    ctc = nn.CTCLoss(blank=BLANK, zero_infinity=True)

    for ep in range(1, args.epochs + 1):
        net.train()
        t0, tot, n = time.time(), 0.0, 0
        for bi, (x, in_len, tgt, tgt_len, _t, _s) in enumerate(ld):
            logp = net(x.to(DEVICE))
            in_len = in_len.clamp(max=logp.size(0))
            loss = ctc(logp, tgt, in_len, tgt_len)
            opt.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(net.parameters(), 5.0)
            opt.step()
            sched.step()
            tot += loss.item()
            n += 1
            if bi % 50 == 0:
                print(f"ep{ep} {bi}/{len(ld)} loss {tot / n:.3f} "
                      f"{(bi + 1) / (time.time() - t0):.2f} batch/s", flush=True)
        for name, rs in (("val", val), ("page25", hold)):
            for s, (wer, cer, cnt, ref, hyp) in evaluate(net, cs, rs, args.bs).items():
                print(f"== ep{ep} {name}/{s}: WER {wer:.1f}% CER {cer:.1f}% ({cnt} lines)", flush=True)
                if name == "page25":
                    print(f"   ref: {ref}\n   hyp: {hyp}", flush=True)
        torch.save({"state": net.state_dict(), "chars": cs.chars, "img_h": IMG_H,
                    "epoch": ep}, OUT_DIR / "crnn_last.pt")
        print(f"epoch {ep} done in {time.time() - t0:.0f}s, loss {tot / n:.3f}", flush=True)


if __name__ == "__main__":
    main()
