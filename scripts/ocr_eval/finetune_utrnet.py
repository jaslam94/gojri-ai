"""Fine-tune UTRNet-Large on Gojri Arabic-script runs (real dictionary print), mainly to teach it the short vowel marks.

Why: zero-shot UTRNet reads Gojri letters well (2.1% error on dictionary runs) but writes only some of the marks
(pesh ُ about half, zer ِ never), because its Urdu training text has few marks. See LOG.md, 2026-11-10.

Data: the folder made by scripts/synth/build_utrnet_runs.py: img/*.png and train.tsv, val.tsv, test.tsv, test_seen.tsv
(file, label, left margin px, right margin px, page_line). test.tsv holds whole held-out pages (the clean test); test_seen.tsv holds runs
of the 200 reviewed lines (their pages also hold training lines, so it is the weaker test). Neither is ever trained on.
Training keeps a random 0 to 3 px of the margin around each run (the margin is cut fully for val and test).

Steps: (1) read every train run with the unchanged model and drop runs whose label is far from the read (pairing mistakes,
default: more than 40% letter error); (2) report zero-shot val and test scores; (3) fine-tune with Adam and a cosine
learning rate, CTC loss, light augmentation (scale, blur, contrast, noise); (4) after each epoch report val and test scores
and keep the weights with the lowest val error.

Scores (per set): letter error on base letters (marks, spaces, punctuation removed; ك=ک, ه=ہ), mark error (edit distance
of the mark strings / marks in the truth), full error (letters and marks together, spaces removed), exact runs.

Run (GPU strongly advised): py -3 -X utf8 scripts/ocr_eval/finetune_utrnet.py --repo D:/ocr-tools/utrnet
    --weights D:/ocr-tools/weights/large.pth --data data/utrnet-ft --out data/utrnet-ft/run1 [--epochs 6]
UTRNet code and weights are third party (CC BY-NC-SA 4.0): the fine-tuned weights stay non-commercial and share-alike.
"""
import argparse
import json
import math
import random
import re
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageEnhance, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ocrlib as O  # noqa: E402

IMG_H, IMG_W = O.IMG_H, O.IMG_W
MARKS = re.compile("[\u064b-\u065f\u0670\u06d6-\u06ed]")


def patch_hrnet():
    """UTRNet's HRNet adds tensors in place (x += ...), which breaks the backward pass. Same maths, out of place (including the in-place side effect on the stream list that later streams read).
    The third-party files stay unchanged; the weights and the outputs do not change."""
    from modules.cnn import hrnet as H

    def basic(self, x):
        return self.relu(self.conv(x) + x)

    def bottleneck(self, x):
        identity = self.downsampling(x) if self.downsampling else x
        return self.relu(self.conv(x) + identity)

    def hrblock(self, x_list):
        par = [self.parallel_conv_lists[i](x_list[i]) for i in range(self.index)]
        final = []
        for i in range(self.index if self.last_stage else self.index + 1):
            if i == self.index:
                x = 0
                for t, m in zip(par, self.down_conv_lists[-1]):
                    x = x + m(t)
            else:
                x = par[i]
                if i != self.index - 1:
                    up = 0
                    for t, m in zip(par[i + 1:], self.up_conv_lists[i]):
                        up = up + m(t)
                    x = x + up
                if i != 0:
                    down = 0
                    for t, m in zip(par[:i], self.down_conv_lists[i - 1]):
                        down = down + m(t)
                    x = x + down
                par[i] = x  # the original adds in place, so the later streams read this sum (before the ReLU), not the old value
            final.append(self.relu(x))
        return final

    H.BasicBlock.forward, H.Bottleneck.forward, H.HRBlock.forward = basic, bottleneck, hrblock


FOLD_LABELS = False  # set by --fold: write the spellings that look the same in print as the letters UTRNet already knows
FOLD2 = str.maketrans({"ك": "ک", "ه": "ہ", "ۃ": "ہ", "ي": "ی", "ى": "ی"})


def norm_label(s, charset):
    s = unicodedata.normalize("NFC", s)
    if FOLD_LABELS:
        s = s.translate(FOLD2)
    return "".join(ch for ch in s if ch in charset)


def marks_of(s):
    return "".join(MARKS.findall(unicodedata.normalize("NFC", s)))


def letters_of(s):
    return O.arabic(s)


def full_of(s):
    return "".join(unicodedata.normalize("NFC", s).split()).translate(O.FOLD)


def load_tsv(path):
    rows = []
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            f = line.split("\t")
            if len(f) >= 4:
                rows.append({"file": f[0], "label": f[1], "lm": int(f[2]), "rm": int(f[3]), "pl": f[4] if len(f) > 4 else ""})
    return rows


class Runs(torch.utils.data.Dataset):
    def __init__(self, folder, rows, charset, train, plain=False, strip_marks=False):
        self.folder, self.rows, self.charset, self.train = Path(folder), rows, charset, train
        self.plain, self.strip_marks = plain, strip_marks  # plain: no augmentation and no margin jitter (diagnostics)

    def __len__(self):
        return len(self.rows)

    def image(self, r):
        im = Image.open(self.folder / "img" / r["file"]).convert("L")
        w, h = im.size
        # keep a random part of the stored margin when training, none of it for val and test
        kl, kr = (random.randint(0, r["lm"]), random.randint(0, r["rm"])) if self.train and not self.plain else (0, 0)
        im = im.crop((r["lm"] - kl, 0, w - (r["rm"] - kr), h))
        if self.train and not self.plain:
            # light augmentation: width and height jitter, blur, contrast and brightness, noise
            sw, sh = random.uniform(0.9, 1.1), random.uniform(0.9, 1.1)
            im = im.resize((max(8, round(im.width * sw)), max(8, round(im.height * sh))), Image.Resampling.BICUBIC)
            if random.random() < 0.3:
                im = im.filter(ImageFilter.GaussianBlur(random.uniform(0.3, 1.0)))
            im = ImageEnhance.Contrast(im).enhance(random.uniform(0.7, 1.2))
            im = ImageEnhance.Brightness(im).enhance(random.uniform(0.9, 1.1))
            if random.random() < 0.3:
                a = np.asarray(im, dtype="float32") + np.random.normal(0, random.uniform(2, 8), (im.height, im.width))
                im = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
        return im

    def __getitem__(self, i):
        r = self.rows[i]
        im = self.image(r).transpose(Image.Transpose.FLIP_LEFT_RIGHT)
        w, h = im.size
        rw = IMG_W if math.ceil(IMG_H * w / h) > IMG_W else math.ceil(IMG_H * w / h)
        a = np.asarray(im.resize((rw, IMG_H), Image.Resampling.BICUBIC), dtype="float32") / 255.0
        t = torch.from_numpy((a - 0.5) / 0.5).unsqueeze(0)
        x = torch.zeros(1, IMG_H, IMG_W)
        x[:, :, :rw] = t
        if rw < IMG_W:
            x[:, :, rw:] = t[:, :, rw - 1].unsqueeze(2).expand(1, IMG_H, IMG_W - rw)
        lab = norm_label(r["label"], self.charset)
        if self.strip_marks:
            lab = MARKS.sub("", lab)
        return x, lab, i


def decode(chars, idx):
    out, prev = [], 0
    for k in idx:
        if k != 0 and k != prev:
            out.append(chars[k])
        prev = k
    return "".join(out)


@torch.no_grad()
def read_all(net, dev, chars, ds, batch=16):
    net.eval()
    if dev.type == "cuda":
        torch.cuda.empty_cache()  # training tensors are still cached while we score
    dl = torch.utils.data.DataLoader(ds, batch_size=batch, shuffle=False, num_workers=2)
    outs = {}
    for x, _lab, idx in dl:
        am = net(x.to(dev)).argmax(2).cpu().tolist()
        for i, a in zip(idx.tolist(), am):
            outs[i] = decode(chars, a)
    return [outs[i] for i in range(len(ds))]


def score(rows, preds, charset):
    nl = le = nm = me = nf = fe = exact = 0
    for r, p in zip(rows, preds):
        t = norm_label(r["label"], charset)
        nl += len(letters_of(t))
        le += O.ed(letters_of(t), letters_of(p))
        nm += len(marks_of(t))
        me += O.ed(marks_of(t), marks_of(p))
        nf += len(full_of(t))
        fe += O.ed(full_of(t), full_of(p))
        exact += full_of(t) == full_of(p)
    pct = lambda a, b: round(100 * a / max(b, 1), 2)  # noqa: E731
    return {"runs": len(rows), "letter_err": pct(le, nl), "mark_err": pct(me, nm), "full_err": pct(fe, nf),
            "exact": exact, "letters": nl, "marks": nm}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--weights", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--epochs", type=int, default=6)
    ap.add_argument("--lr", type=float, default=5e-5)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--drop-cer", type=float, default=0.4, help="drop train runs whose zero-shot letter error is above this")
    ap.add_argument("--limit", type=int, default=0, help="use only this many train runs (smoke test)")
    ap.add_argument("--freeze-bn", action="store_true", help="keep batch-norm layers in eval mode while training (small batches)")
    ap.add_argument("--fold", action="store_true", help="fold ك to ک, ه and ۃ to ہ, ي and ى to ی in the labels (train and score)")
    ap.add_argument("--train", choices=["all", "lstm", "head"], default="all", help="which part to train: all, the sequence layer and the head, or the head only")
    ap.add_argument("--plain", action="store_true", help="diagnostic: train without augmentation and margin jitter")
    ap.add_argument("--strip-marks", action="store_true", help="diagnostic: train on letters only (marks removed from the labels)")
    ap.add_argument("--no-tdrop", action="store_true", help="diagnostic: switch off UTRNet's temporal dropout while training")
    ap.add_argument("--skip-drop", action="store_true", help="do not run the zero-shot drop pass over the train runs")
    ap.add_argument("--val-only", action="store_true", help="score only the validation set")
    ap.add_argument("--max-steps", type=int, default=0, help="stop after this many steps (0 = all epochs)")
    ap.add_argument("--no-save", action="store_true", help="do not write weights")
    ap.add_argument("--warmup", type=int, default=100, help="steps of linear learning-rate warm-up")
    ap.add_argument("--log-every", type=int, default=100)
    ap.add_argument("--eval-every", type=int, default=300, help="score val and test every N steps; stop if the val error blows up")
    ap.add_argument("--seed", type=int, default=20261110)
    args = ap.parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    data = Path(args.data)
    global FOLD_LABELS
    FOLD_LABELS = args.fold
    utr = O.UTRNet(args.repo, args.weights)
    patch_hrnet()
    if args.no_tdrop:
        from modules.dropout_layer import dropout_layer
        orig = dropout_layer.forward
        dropout_layer.forward = lambda self, x: x if self.training else orig(self, x)
    net, dev, chars = utr.net, utr.dev, utr.chars
    charset = set(chars[1:])
    print("device:", dev, "glyphs:", len(chars), flush=True)
    train, val, test, seen = (load_tsv(data / f"{n}.tsv") for n in ("train", "val", "test", "test_seen"))
    if args.limit:
        random.shuffle(train)
        train, val, test, seen = train[: args.limit], val[: args.limit // 4], test[: args.limit // 4], seen[: args.limit // 4]
    ds_val, ds_test, ds_seen = (Runs(data, x, charset, False) for x in (val, test, seen))
    log = []

    def report(tag):
        res = {"tag": tag, "val": score(val, read_all(net, dev, chars, ds_val), charset)}
        if not args.val_only:
            res["test"] = score(test, read_all(net, dev, chars, ds_test), charset)
            if seen:
                res["test_seen"] = score(seen, read_all(net, dev, chars, ds_seen), charset)
        log.append(res)
        print(json.dumps(res, ensure_ascii=False), flush=True)
        (out / "log.json").write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
        return res

    zero = report("zero-shot")
    # step 1: drop runs that the unchanged model reads far from the label (pairing mistakes)
    ds_all = Runs(data, train, charset, False)
    reads = [""] * len(train) if args.skip_drop else read_all(net, dev, chars, ds_all)
    keep, dropped = [], []
    for r, p in zip(train, reads):
        t = letters_of(norm_label(r["label"], charset))
        cer = 0.0 if args.skip_drop else O.ed(t, letters_of(p)) / max(len(t), 1)
        (dropped if cer > args.drop_cer else keep).append((r, p, cer))
    (out / "dropped.tsv").write_text("".join(f"{r['file']}\t{r['label']}\t{p}\t{c:.2f}\n" for r, p, c in dropped), encoding="utf-8")
    print(f"train runs {len(train)}, kept {len(keep)}, dropped {len(dropped)} (zero-shot letter error > {args.drop_cer})", flush=True)
    train = [r for r, _p, _c in keep]
    ds_train = Runs(data, train, charset, True, plain=args.plain, strip_marks=args.strip_marks)
    dl = torch.utils.data.DataLoader(ds_train, batch_size=args.batch, shuffle=True, num_workers=args.workers, drop_last=True)
    converter = {c: i for i, c in enumerate(chars)}
    crit = torch.nn.CTCLoss(zero_infinity=True)
    if args.train != "all":
        for n, p in net.named_parameters():
            p.requires_grad = n.startswith("Prediction") or (args.train == "lstm" and n.startswith("SequenceModeling"))
    trainable = [p for p in net.parameters() if p.requires_grad]
    print("training", sum(p.numel() for p in trainable), "of", sum(p.numel() for p in net.parameters()), "weights", flush=True)
    opt = torch.optim.Adam(trainable, lr=args.lr, betas=(0.9, 0.999))
    total = args.epochs * len(dl)
    if args.max_steps:
        total = min(total, args.max_steps)
    sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: min(1.0, (s + 1) / max(args.warmup, 1)) * 0.5 * (1 + math.cos(math.pi * min(s, total) / max(total, 1))))
    def save(name):
        if not args.no_save:
            torch.save(net.state_dict(), out / name)

    best, t0, step = (zero["val"]["full_err"], None), time.time(), 0
    save("best.pth")
    def set_train():
        net.train()
        if args.freeze_bn:
            for m in net.modules():
                if isinstance(m, torch.nn.modules.batchnorm._BatchNorm):
                    m.eval()

    stop = False
    for ep in range(1, args.epochs + 1):
        set_train()
        run, gnorms = [], []
        for x, labs, _i in dl:
            targets = torch.IntTensor([converter[c] for lab in labs for c in lab])
            lens = torch.IntTensor([len(lab) for lab in labs])
            preds = net(x.to(dev)).log_softmax(2).permute(1, 0, 2)
            size = torch.IntTensor([preds.size(0)] * x.size(0))
            loss = crit(preds, targets, size, lens)
            net.zero_grad()
            loss.backward()
            gnorms.append(float(torch.nn.utils.clip_grad_norm_(net.parameters(), 5)))
            opt.step()
            sched.step()
            run.append(float(loss))
            step += 1
            if args.max_steps and step >= args.max_steps:
                report(f"final step {step}")
                stop = True
                break
            if step % args.log_every == 0:
                print(f"epoch {ep} step {step}/{total} loss {np.mean(run[-args.log_every:]):.4f} grad norm {np.mean(gnorms[-args.log_every:]):.2f} max {max(gnorms[-args.log_every:]):.1f} {time.time() - t0:.0f}s", flush=True)
            if step % args.eval_every == 0:
                res = report(f"step {step}")
                if res["val"]["full_err"] < best[0]:
                    best = (res["val"]["full_err"], f"step {step}")
                    save("best.pth")
                if res["val"]["full_err"] > max(30.0, 4 * zero["val"]["full_err"]):
                    print("validation error blew up: stop (best.pth keeps the best weights so far)", flush=True)
                    stop = True
                    break
                set_train()
        if stop:
            break
        res = report(f"epoch {ep}")
        res["loss"] = float(np.mean(run))
        if res["val"]["full_err"] < best[0]:
            best = (res["val"]["full_err"], ep)
            save("best.pth")
        save("last.pth")
    print("best val full error", best, flush=True)


if __name__ == "__main__":
    main()
