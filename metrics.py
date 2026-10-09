"""Score every system's results against bench/items.jsonl: results/summary.json and results/tables.md.

  python3 metrics.py

A system is a results file (results/<system>.jsonl, one line per item id with `probs` in the item's option order).
Jev-Omni's runs are read from results/jev/: dvb-{torch,webgpu}.jsonl (the image rows of bench/jev.jsonl, run in
jev-omni.js) and its earlier DecisionBench runs (reference-fp32.jsonl, browser-q8f32.jsonl) under unprefixed ids.

Accuracy: argmax = label. The 95% interval resamples tasks (one image, screen or DecisionBench state and all its
questions), since questions about one image are not independent. Brier: summed over options (uniform = 1 - 1/K).
Flatness: mean entropy / log K (1 = uniform). GUI-360 task accuracy: a screen is right when every one of its action
items is (cua-bench-s1's score). Latency: medians over items that ran their own pass (native cua items after the first
of a screen share it).
"""
import json
import math
import random
from collections import defaultdict
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
RES = HERE / "results"
JEV = RES / "jev"   # copies of jev-omni.js build/eval/*: this bench's rows, without prompts and hidden states

MODELS = {"kev-4b-vision": "Kev-4B", "kev-0.8b-vision": "Kev-0.8B", "cua-s1-4b-0.2-multimodal": "cua-s1-4b-0.2", "jev-omni": "Jev-Omni",
          "rsi-jev-v6.1-vl-4b": "RSI-Jev v6.1-VL 4B", "rsi-jev-v6.1-vl-27b": "RSI-Jev v6.1-VL 27B"}
HOME = {"kev-4b-vision": {"vision-v1", "vision-v2"}, "kev-0.8b-vision": {"vision-v1", "vision-v2"},
        "cua-s1-4b-0.2-multimodal": {"gui360"}, "jev-omni": {"decisionbench"},
        "rsi-jev-v6.1-vl-4b": set(), "rsi-jev-v6.1-vl-27b": set()}
SOURCES = [("vision-v1", None), ("vision-v2", None), ("gui360", "element"), ("gui360", "action"), ("decisionbench", None)]
CATEGORIES = ["counting", "charts", "small_text", "scene", "gui", "text"]


def load(path: Path, prefix: str = "") -> dict:
    if not path.exists():
        return {}
    out = {}
    for line in open(path):
        r = json.loads(line)
        if "embed_ms" in r:   # Jev-Omni's predict output: the same split under its own names
            r["ms"] = {"preprocess": r.get("prep_ms") or 0, "vision": r["embed_ms"] or 0, "decoder": r["decoder_ms"], "total": r["ms"]}
            r["imageTokens"] = r.get("image_tokens") or 0
        out[prefix + r["id"]] = r
    return out


def systems() -> dict[str, dict]:
    s = {}
    for p in sorted(RES.glob("*.jsonl")):
        if not p.stem.startswith("lat-"):
            s[p.stem] = load(p)
    # the bench's own rows first (dvb-*.jsonl, run by the Jev-Omni thread on bench/jev.jsonl), then earlier runs of
    # the same questions under their unprefixed ids
    for name, file, prefix in (("jev-omni-torch", "dvb-torch.jsonl", ""), ("jev-omni-webgpu", "dvb-webgpu.jsonl", ""),
                               ("jev-omni-torch", "reference-fp32.jsonl", "decisionbench/"), ("jev-omni-webgpu", "browser-q8f32.jsonl", "decisionbench/")):
        extra = load(JEV / file, prefix)
        if extra:
            s.setdefault(name, {})
            for k, v in extra.items():
                s[name].setdefault(k, v)
    return s


def model_of(system: str) -> str:
    return next(m for m in sorted(MODELS, key=len, reverse=True) if system.startswith(m))


def argmax(p):
    return max(range(len(p)), key=p.__getitem__)


def stats(rows, n_boot=2000, seed=0):
    """rows: (item, probs). Accuracy with a task-resampled 95% interval, Brier, flatness."""
    if not rows:
        return None
    correct = [argmax(p) == it["label"] for it, p in rows]
    brier = [sum((q - (k == it["label"])) ** 2 for k, q in enumerate(p)) for it, p in rows]
    flat = [-sum(q * math.log(max(q, 1e-12)) for q in p) / math.log(len(p)) for it, p in rows]
    by = defaultdict(list)
    for (it, _), c in zip(rows, correct):
        by[(it["source"], it["task"])].append(c)
    groups, rng, accs = list(by.values()), random.Random(seed), []
    for _ in range(n_boot):
        pick = [groups[rng.randrange(len(groups))] for _ in groups]
        accs.append(sum(map(sum, pick)) / sum(map(len, pick)))
    accs.sort()
    return {"n": len(rows), "acc": sum(correct) / len(rows), "ci": [accs[int(0.025 * n_boot)], accs[int(0.975 * n_boot) - 1]],
            "brier": sum(brier) / len(rows), "flatness": sum(flat) / len(rows),
            "chance": sum(1 / len(it["options"]) for it, _ in rows) / len(rows)}


def latency(recs):
    own = [r for r in recs if isinstance(r.get("ms"), dict) and not r.get("shared") and "vision" in r["ms"]]
    if not own:
        return None
    med = lambda k: round(median(r["ms"][k] for r in own))
    return {"n": len(own), "total": med("total"), "vision": round(median(r["ms"]["preprocess"] + r["ms"]["vision"] for r in own)),
            "decoder": med("decoder")}


def task_accuracy(items, res):
    by = defaultdict(list)
    for it in items:
        if it["format"] == "action":
            by[it["task"]].append(argmax(res[it["id"]]["probs"]) == it["label"] if it["id"] in res else None)
    done = [v for v in by.values() if None not in v]
    return {"tasks": len(done), "correct": sum(all(v) for v in done)} if done else None


def main():
    items = [json.loads(l) for l in open(HERE / "bench/items.jsonl")]
    summary = {}
    for name, res in systems().items():
        if name.endswith(".meta"):
            continue
        model = model_of(name)
        meta_p = RES / f"{name}.meta.json"
        meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
        rows = [(it, res[it["id"]]["probs"]) for it in items if it["id"] in res]
        if not rows:
            continue
        s = {"model": MODELS[model], "coverage": f"{len(rows)}/{len(items)}", "meta": meta, "sources": {}, "categories": {}, "turf": {}}
        for src, fmt in SOURCES:
            sub = [(it, p) for it, p in rows if it["source"] == src and (fmt is None or it["format"] == fmt)]
            key = src if fmt is None else f"{src}-{fmt}"
            if sub:
                s["sources"][key] = {**stats(sub), "latency": latency([res[it["id"]] for it, _ in sub]), "home": src in HOME[model]}
        for c in CATEGORIES:
            sub = [(it, p) for it, p in rows if it["category"] == c]
            if sub:
                s["categories"][c] = stats(sub)
        s["turf"]["home"] = stats([(it, p) for it, p in rows if it["source"] in HOME[model]])
        s["turf"]["cross"] = stats([(it, p) for it, p in rows if it["source"] not in HOME[model]])
        s["turf"]["image"] = stats([(it, p) for it, p in rows if it["image"]])
        s["gui_tasks"] = task_accuracy(items, res)
        s["latency"] = latency(list(res.values()))
        summary[name] = s

    # browser against PyTorch, per model: how often the pick agrees and the largest probability gap
    parity, ids, every = {}, {it["id"] for it in items}, systems()
    for name in summary:
        if name.endswith("-webgpu"):
            ref = name.replace("-webgpu", "-torch")
            a, b = every.get(name, {}), every.get(ref, {})
            common = [k for k in a if k in b and k in ids]
            if common:
                parity[name] = {"vs": ref, "n": len(common), "argmax_agree": sum(argmax(a[k]["probs"]) == argmax(b[k]["probs"]) for k in common) / len(common),
                                "max_abs_dp": max(max(abs(x - y) for x, y in zip(a[k]["probs"], b[k]["probs"])) for k in common),
                                "mean_abs_dp": sum(sum(abs(x - y) for x, y in zip(a[k]["probs"], b[k]["probs"])) / len(a[k]["probs"]) for k in common) / len(common)}
    pairs = {}
    for a, b in PAIRS:
        ra, rb = every.get(a, {}), every.get(b, {})
        for src, fmt in SOURCES + [("image", None)]:
            sub = [it for it in items if it["id"] in ra and it["id"] in rb
                   and (it["image"] if src == "image" else it["source"] == src and (fmt is None or it["format"] == fmt))]
            if sub:
                pairs.setdefault(f"{a} - {b}", {})[src if fmt is None else f"{src}-{fmt}"] = paired(sub, ra, rb)
    lat = controlled_latency(items)
    (RES / "summary.json").write_text(json.dumps({"systems": summary, "parity": parity, "paired": pairs, "latency": lat}, indent=1) + "\n")
    (RES / "tables.md").write_text(tables(summary, parity, lat, pairs))
    print((RES / "tables.md").read_text())


PAIRS = [("kev-4b-vision-webgpu", "cua-s1-4b-0.2-multimodal-webgpu"), ("kev-4b-vision-webgpu", "jev-omni-webgpu"),
         ("jev-omni-webgpu", "cua-s1-4b-0.2-multimodal-webgpu"), ("kev-4b-vision-webgpu", "kev-0.8b-vision-webgpu"),
         ("kev-0.8b-vision-webgpu", "cua-s1-4b-0.2-multimodal-webgpu")]


def paired(sub, ra, rb, n_boot=2000, seed=0):
    """Accuracy of a minus b on the same items, with a task-resampled 95% interval."""
    by = defaultdict(list)
    for it in sub:
        by[(it["source"], it["task"])].append((argmax(ra[it["id"]]["probs"]) == it["label"]) - (argmax(rb[it["id"]]["probs"]) == it["label"]))
    groups, rng, ds = list(by.values()), random.Random(seed), []
    for _ in range(n_boot):
        pick = [groups[rng.randrange(len(groups))] for _ in groups]
        ds.append(sum(map(sum, pick)) / sum(map(len, pick)))
    ds.sort()
    d = sum(map(sum, groups)) / sum(map(len, groups))
    return {"n": len(sub), "diff": d, "ci": [ds[int(0.025 * n_boot)], ds[int(0.975 * n_boot) - 1]]}


def controlled_latency(items):
    """latency.sh's interleaved passes: per model, medians over both rounds, by kind of item."""
    kinds = {"image, small (vision-v1)": lambda it: it["source"] == "vision-v1",
             "image, page (vision-v2, GUI-360)": lambda it: it["source"] in ("vision-v2", "gui360"),
             "text only (DecisionBench)": lambda it: it["source"] == "decisionbench"}
    by_id, out = {it["id"]: it for it in items}, {}
    for model in MODELS:
        recs = [r for p in sorted(RES.glob(f"lat-{model}-r*.jsonl")) for r in load(p).values() if not r.get("shared")]
        if model == "jev-omni":   # not interleaved: its own WebGPU run of every image row, at another time
            recs = [r for r in load(JEV / "dvb-webgpu.jsonl").values() if isinstance(r.get("ms"), dict)]
        if not recs:
            continue
        out[model] = {}
        for k, f in kinds.items():
            sub = [r for r in recs if f(by_id[r["id"]])]
            if sub:
                med = lambda g: round(median(g(r) for r in sub))
                out[model][k] = {"n": len(sub), "total": med(lambda r: r["ms"]["total"]), "image": med(lambda r: r["ms"]["preprocess"] + r["ms"]["vision"]),
                                 "decoder": med(lambda r: r["ms"]["decoder"]), "tokens": med(lambda r: r["tokens"]), "image_tokens": med(lambda r: r["imageTokens"])}
    return out


def pct(x):
    return f"{100 * x:.1f}"


def tables(summary, parity, lat, pairs) -> str:
    out = []
    if pairs:
        out.append("### Paired differences (accuracy of A minus B on the same items, points; 95% CI, tasks resampled)\n")
        out.append("| A - B | vision-v1 | vision-v2 | gui360-element | gui360-action | decisionbench | all image items |")
        out.append("|---|" + "---|" * 6)
        for name, d in pairs.items():
            cells = [f"{100 * v['diff']:+.1f} ({100 * v['ci'][0]:+.1f}, {100 * v['ci'][1]:+.1f})" if (v := d.get(k)) else "-"
                     for k in ("vision-v1", "vision-v2", "gui360-element", "gui360-action", "decisionbench", "image")]
            out.append(f"| {name} | " + " | ".join(cells) + " |")
        out.append("")
    names = sorted(summary, key=lambda n: (list(MODELS).index(model_of(n)), n))
    out.append("### Accuracy by source (95% CI, tasks resampled); Brier; flatness\n")
    out.append("| system | source | n | accuracy | 95% CI | chance | Brier | flatness | turf |")
    out.append("|---|---|---:|---:|---|---:|---:|---:|---|")
    for n in names:
        for src, v in summary[n]["sources"].items():
            out.append(f"| {n} | {src} | {v['n']} | {pct(v['acc'])} | {pct(v['ci'][0])}-{pct(v['ci'][1])} | {pct(v['chance'])} | {v['brier']:.3f} | {v['flatness']:.2f} | {'home' if v['home'] else 'cross'} |")
    out.append("\n### Home turf vs cross-domain (and every image item)\n")
    out.append("| system | home n | home acc (CI) | cross n | cross acc (CI) | image items acc (CI) | GUI-360 tasks right |")
    out.append("|---|---:|---|---:|---|---|---|")
    for n in names:
        t, g = summary[n]["turf"], summary[n]["gui_tasks"]
        cell = lambda v: f"{pct(v['acc'])} ({pct(v['ci'][0])}-{pct(v['ci'][1])})" if v else "-"
        tasks = f"{g['correct']}/{g['tasks']}" if g else "-"
        out.append(f"| {n} | {t['home']['n'] if t['home'] else 0} | {cell(t['home'])} | {t['cross']['n'] if t['cross'] else 0} | {cell(t['cross'])} | {cell(t['image'])} | {tasks} |")
    out.append("\n### Accuracy by category\n")
    out.append("| system | " + " | ".join(CATEGORIES) + " |")
    out.append("|---|" + "---:|" * len(CATEGORIES))
    for n in names:
        c = summary[n]["categories"]
        out.append(f"| {n} | " + " | ".join(f"{pct(c[k]['acc'])} (n={c[k]['n']})" if k in c else "-" for k in CATEGORIES) + " |")
    out.append("\n### Latency in the full runs (median ms per item: image = preprocess + vision tower; one model at a time, on a shared machine)\n")
    out.append("| system | source | items | total | image | decoder |")
    out.append("|---|---|---:|---:|---:|---:|")
    for n in names:
        if not n.endswith("-webgpu"):
            continue
        for src, v in summary[n]["sources"].items():
            if v["latency"]:
                l = v["latency"]
                out.append(f"| {n} | {src} | {l['n']} | {l['total']} | {l['vision']} | {l['decoder']} |")
    if lat:
        out.append("\n### Latency, interleaved passes (latency.sh: 35 items x 2 rounds per model; median ms)\n")
        out.append("| model | items | n | total | image | decoder | tokens | image tokens |")
        out.append("|---|---|---:|---:|---:|---:|---:|---:|")
        for m, ks in lat.items():
            for k, v in ks.items():
                out.append(f"| {MODELS[m]} | {k} | {v['n']} | {v['total']} | {v['image']} | {v['decoder']} | {v['tokens']} | {v['image_tokens']} |")
    out.append("\n| system | adapter | load ms | bundle GB | browser memory peak GB (idle before load) |")
    out.append("|---|---|---:|---:|---|")
    for n in names:
        m = summary[n]["meta"]
        if "bundleBytes" in m:   # browser runs
            out.append(f"| {n} | {m.get('adapter')} | {m.get('loadMs')} | {m['bundleBytes'] / 1e9:.2f} | {m['memoryMB']['peak'] / 1024:.1f} ({m['memoryMB']['baseline'] / 1024:.1f}) |")
    if parity:
        out.append("\n### Browser vs PyTorch\n")
        out.append("| system | reference | n | same pick | mean abs dp | max abs dp |")
        out.append("|---|---|---:|---:|---:|---:|")
        for n, p in parity.items():
            out.append(f"| {n} | {p['vs']} | {p['n']} | {pct(p['argmax_agree'])} | {p['mean_abs_dp']:.4f} | {p['max_abs_dp']:.3f} |")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    main()
