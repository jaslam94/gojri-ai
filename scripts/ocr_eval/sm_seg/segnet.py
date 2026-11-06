"""SegNet: labels every pixel column of a text-line image as gap (0), Arabic script (1) or Latin (2).

Input: (B, 1, 64, W) grey image scaled to [-1, 1] (ink dark, paper white). Output: (B, 3, W) class scores per column.
The height is collapsed by four 3x3 conv blocks with (2,1) pooling; dilated 1D convolutions then give each column
a horizontal context of about 150 px, enough to see whether it sits inside an English word or an Arabic word.
"""
import torch
import torch.nn as nn


class SegNet(nn.Module):
    def __init__(self, hid=128):
        super().__init__()
        ch = [1, 16, 32, 64, 96]
        layers = []
        for i in range(4):
            layers += [nn.Conv2d(ch[i], ch[i + 1], 3, padding=1), nn.BatchNorm2d(ch[i + 1]), nn.ReLU(),
                       nn.MaxPool2d((2, 1))]
        self.cnn = nn.Sequential(*layers)  # (B, 96, 4, W)
        self.inp = nn.Sequential(nn.Conv1d(96 * 4, hid, 5, padding=2), nn.BatchNorm1d(hid), nn.ReLU())
        self.blocks = nn.ModuleList([
            nn.Sequential(nn.Conv1d(hid, hid, 5, padding=2 * d, dilation=d), nn.BatchNorm1d(hid), nn.ReLU())
            for d in (1, 2, 4, 8, 16)])
        self.out = nn.Conv1d(hid, 3, 1)

    def forward(self, x):
        f = self.cnn(x)
        b, c, h, w = f.shape
        f = self.inp(f.reshape(b, c * h, w))
        for blk in self.blocks:
            f = f + blk(f)
        return self.out(f)


def spans_from_logits(logits, min_w=12, fill=None):
    """Column class per pixel -> [(cls, x0, x1)] spans. Same-class neighbours closer than `fill` px merge;
    spans narrower than min_w are dropped. logits: (3, W) tensor or array."""
    import numpy as np
    pred = np.asarray(logits).argmax(0) if not isinstance(logits, torch.Tensor) else logits.argmax(0).numpy()
    spans, i, n = [], 0, len(pred)
    while i < n:
        if pred[i] == 0:
            i += 1
            continue
        j = i
        while j < n and pred[j] == pred[i]:
            j += 1
        spans.append([int(pred[i]), i, j])
        i = j
    fill = fill if fill is not None else 10
    merged = []
    for s in spans:
        if merged and merged[-1][0] == s[0] and s[1] - merged[-1][2] <= fill:
            merged[-1][2] = s[2]
        else:
            merged.append(s)
    return [tuple(s) for s in merged if s[2] - s[1] >= min_w]
