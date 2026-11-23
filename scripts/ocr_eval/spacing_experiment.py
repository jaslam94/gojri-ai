"""Split the 200 Kahawat-Kosh spacing cards, tune the character n-gram space inserter by cross-validation, score once.

  py -3 -X utf8 scripts/ocr_eval/spacing_experiment.py split        # once: 100 dev cards, 100 locked test cards
  py -3 -X utf8 scripts/ocr_eval/spacing_experiment.py cv [--grid small|full]   # cross-validation on the 100 dev cards only
  py -3 -X utf8 scripts/ocr_eval/spacing_experiment.py test --config best.json  # score the locked 100, once per config

Rules (so that the test number is honest):
- `split` refuses to run twice. The split file is tracked.
- `cv` reads only the dev cards. The locked cards are never opened by it.
- `test` appends a row to the test log. Run it only with a config that cv chose, at a milestone.
Truth of a card is the speaker's text ("fixed") or the OCR text ("ok"); see score_spacing.py. Space errors count only on cards
whose letters equal the truth, as in score_spacing.py.
"""
import argparse
import collections
import glob
import itertools
import json
import random
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import score_spacing as SS  # noqa: E402
import spacing_lm as L  # noqa: E402

D = ROOT / "data/reviews/kahawat-spacing"
SPLIT = D / "split_20261123.json"
WORK = ROOT / "data/ocr/spacing_lm"
SEED = 20261123


def cmd_split():
    if SPLIT.exists():
        sys.exit(f"{SPLIT} exists: the split is frozen")
    cards = SS.load()
    ids = sorted(c["id"] for c in cards)
    rng = random.Random(SEED)
    test = sorted(rng.sample(ids, len(ids) // 2))
    dev = [i for i in ids if i not in set(test)]
    SPLIT.write_text(json.dumps({"seed": SEED, "note": "test = locked cards: do not tune on them (scripts/ocr_eval/spacing_experiment.py)",
                                 "dev": dev, "test": test}, indent=1), encoding="utf-8")
    print("dev", len(dev), "test", len(test), "->", SPLIT)


def load_split():
    s = json.loads(SPLIT.read_text(encoding="utf-8"))
    byid = {c["id"]: c for c in SS.load()}
    return [byid[i] for i in s["dev"]], [byid[i] for i in s["test"]]


def fli_lines():
    """Sentences of the FLI literature corpus as 'word word word' lines (letters only, folded). Local data, never published."""
    out = []
    for f in sorted(glob.glob(str(ROOT / "datasets/Gojri Language Corpus/*.txt"))):
        text = open(f, encoding="utf-8").read()
        for sent in re.split(r"[۔؟!\n]+", text):
            if "￿" in sent or re.search(r"[0-9A-Za-z]", sent):
                continue
            ln = L.words_line(sent)
            if ln.count(" ") >= 1:
                out.append(ln)
    return out


def counts(cards, key, ins_texts):
    """Space counts on the letter-identical cards. ins_texts: {card id: text with spaces added}."""
    sp = collections.Counter()
    for c in cards:
        tl, tm, ts = SS.parse(c["truth"])
        t = ins_texts[c["id"]]
        ol, om, os_ = SS.parse(t)
        o0l, _, o0s = SS.parse(c["ocr"])
        assert ol == o0l, "letters changed"   # the inserter must never touch a letter
        assert o0s <= os_, "an OCR space was removed"
        if ol != tl:
            continue
        sp["cards"] += 1
        sp["truth"] += len(ts)
        sp["text"] += len(os_)
        sp["hit"] += len(ts & os_)
        sp["missing"] += len(ts - os_)
        sp["extra"] += len(os_ - ts)
        sp["exact"] += ts == os_
    sp["errors"] = sp["missing"] + sp["extra"]
    return sp


def fmt(sp):
    p = sp["hit"] / sp["text"] if sp["text"] else 0
    r = sp["hit"] / sp["truth"] if sp["truth"] else 0
    f = 2 * p * r / (p + r) if p + r else 0
    return (f"cards {sp['cards']} truth {sp['truth']} text {sp['text']} hit {sp['hit']} missing {sp['missing']} extra {sp['extra']} "
            f"errors {sp['errors']} P {100 * p:.1f} R {100 * r:.1f} F1 {100 * f:.1f} exact {sp['exact']}")


def run(cards, train_cards, fli_lm, order, lam, bonus, where, wcards, cache):
    """Decode cards with a cards-LM trained on train_cards (truth lines) plus the FLI model. Returns {id: text}."""
    if lam >= 1.0 or not train_cards:
        lms, ws = [fli_lm], [1.0]
    else:
        key = (order, tuple(c["id"] for c in train_cards), wcards)
        lm = cache.get(key)
        if lm is None:
            lm = L.CharLM(order)
            lm.add([L.words_line(c["truth"]) for c in train_cards], weight=wcards)
            cache[key] = lm
        if lam <= 0.0:
            lms, ws = [lm], [1.0]
        else:
            lms, ws = [fli_lm, lm], [lam, 1.0 - lam]
    return {c["id"]: L.insert_spaces(c["ocr"], lms, ws, bonus, where) for c in cards}


def cv_eval(dev, fli_lm, order, lam, bonus, where, wcards, cache, folds):
    texts = {}
    for k, fold in enumerate(folds):
        held = {c["id"] for c in fold}
        train = [c for c in dev if c["id"] not in held]
        texts.update(run(fold, train, fli_lm, order, lam, bonus, where, wcards, cache))
    return counts(dev, "ocr", texts)


def cmd_cv(grid):
    dev, _ = load_split()
    assert len(dev) == 100
    rng = random.Random(SEED + 1)
    ids = [c["id"] for c in dev]
    rng.shuffle(ids)
    byid = {c["id"]: c for c in dev}
    folds = [[byid[i] for i in ids[k::5]] for k in range(5)]
    base = counts(dev, "ocr", {c["id"]: c["ocr"] for c in dev})
    print("dev baseline (OCR as read):", fmt(base))
    t0 = time.time()
    fli = fli_lines()
    print("FLI lines", len(fli), "chars", sum(len(x) for x in fli), f"{time.time() - t0:.0f}s", flush=True)
    if grid == "small":
        orders, lams, bonuses, wheres, wcs = [4, 6], [0.8, 1.0], [0, 3, 6], ["nonjoin"], [5]
    else:
        orders, lams, bonuses, wheres, wcs = [3, 4, 5, 6, 7], [0.0, 0.5, 0.8, 0.95, 1.0], [-2, 0, 2, 4, 6, 8, 10], ["nonjoin"], [1, 5]
    results = []
    cache = {}
    for order in orders:
        fli_lm = L.CharLM(order)
        fli_lm.add(fli)
        for lam, wc, where in itertools.product(lams, wcs, wheres):
            if lam == 1.0 and wc != wcs[0]:
                continue
            for bonus in bonuses:
                sp = cv_eval(dev, fli_lm, order, lam, bonus, where, wc, cache, folds)
                results.append({"order": order, "lam": lam, "bonus": bonus, "where": where, "wcards": wc, "errors": sp["errors"], "hit": sp["hit"],
                                "missing": sp["missing"], "extra": sp["extra"], "text": sp["text"], "truth": sp["truth"]})
                print(order, lam, wc, where, bonus, fmt(sp), f"{time.time() - t0:.0f}s", flush=True)
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "cv_results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    best = min(results, key=lambda r: (r["errors"], r["extra"]))
    (WORK / "best_config.json").write_text(json.dumps(best, indent=1), encoding="utf-8")
    print("best:", best)


def cmd_test(config):
    cfg = json.loads(Path(config).read_text(encoding="utf-8"))
    dev, test = load_split()
    fli = fli_lines()
    fli_lm = L.CharLM(cfg["order"])
    fli_lm.add(fli)
    texts = run(test, dev, fli_lm, cfg["order"], cfg["lam"], cfg["bonus"], cfg["where"], cfg["wcards"], {})
    base = counts(test, "ocr", {c["id"]: c["ocr"] for c in test})
    sp = counts(test, "ocr", texts)
    print("test baseline (OCR as read):", fmt(base))
    print("test, character n-gram inserter:", fmt(sp))
    v = SS.vocab()
    fx = {c["id"]: __import__("space_fix").fix_line(re.sub(r"([۔،])(?=[^\s۔،])", r"\1 ", c["ocr"]), v, 4) for c in test}
    try:
        print("test, word splitter margin 4 (margin chosen on all 200 cards, so favoured):", fmt(counts(test, "ocr", fx)))
    except AssertionError as e:
        print("splitter check:", e)
    log = D / "test_log.tsv"
    new = not log.exists()
    with open(log, "a", encoding="utf-8") as f:
        if new:
            f.write("date\tconfig\terrors\thit\tmissing\textra\ttext\ttruth\tbaseline_errors\n")
        f.write(f"{time.strftime('%Y-%m-%d')}\t{json.dumps(cfg, sort_keys=True)}\t{sp['errors']}\t{sp['hit']}\t{sp['missing']}\t{sp['extra']}\t{sp['text']}\t{sp['truth']}\t{base['errors']}\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["split", "cv", "test"])
    ap.add_argument("--grid", default="small")
    ap.add_argument("--config")
    a = ap.parse_args()
    if a.cmd == "split":
        cmd_split()
    elif a.cmd == "cv":
        cmd_cv(a.grid)
    else:
        cmd_test(a.config)
