"""cua-s1-4b-0.2 (multimodal adapter) in PyTorch over bench/cua.jsonl, through upstream's own cua_s1.four_b.FourBModel
(fp32): the reference for the browser.

Run from cua-s1.js's export environment (export/.venv has cua_s1 and the export package four_b):

  cd <cua-s1.js>/export && .venv/bin/python /path/to/decision-vision-bench/torch/cua_torch.py \\
      --out /path/to/decision-vision-bench/results/cua-s1-4b-0.2-multimodal-torch.jsonl [--device mps]

Output lines match the browser runner's: probs in the item's option order; native GUI-360 items are the element's
action vs its skip from one pass over the fixture's own options (`letters`). Text items use modality="text" with the
state as the tree. Appends and resumes.
"""
import argparse
import json
import time
from pathlib import Path

import torch
from cua_s1.four_b import FourBModel, Option

from four_b import pin, snapshot

BENCH = Path(__file__).resolve().parents[1] / "bench"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adapter", default="cua-ai/cua-s1-4b-0.2@16818868b0cc7813808aae4e87b417657046ab79")
    ap.add_argument("--device", default="mps")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    run = pin(a.adapter)
    adir = snapshot(run)
    cfg = json.load(open(f"{adir}/multimodal/adapter_config.json"))
    bdir = snapshot(pin(f"{cfg['base_model_name_or_path']}@{cfg.get('revision') or ''}".rstrip("@")))
    model = FourBModel(base_model=bdir, lora_adapter_path=adir, device=a.device, dtype="float32", modality="multimodal")
    model.load()
    lines = [json.loads(l) for l in open(BENCH / "cua.jsonl")]
    done = {json.loads(l)["id"] for l in open(a.out)} if a.out.exists() else set()
    native: dict[str, list[float]] = {}
    print(f"{run}: {len(lines) - len(done)} of {len(lines)} items to go", flush=True)
    with open(a.out, "a") as f:
        for n, l in enumerate(lines):
            if l["id"] in done:
                continue
            t0 = time.perf_counter()
            if l.get("native") and l["native"] in native:
                p = native[l["native"]]
            else:
                opts = [Option(o["elementId"], o["role"], o["label"], o["action"], o.get("entityId")) for o in l["options"]]
                c = l["context"]
                kw = dict(app=c["app"], task_family=c["taskFamily"], goal=c.get("goal"))
                if l.get("text"):
                    kw.update(modality="text", ax_tree=c["axTree"])
                else:
                    kw.update(modality="multimodal", screenshot=str(BENCH / l["image"]))
                with torch.no_grad():
                    p = [o.probability for o in model.forward(opts, **kw)]
                if l.get("native"):
                    native[l["native"]] = p
            rec = {"id": l["id"], "probs": p, "ms": {"total": (time.perf_counter() - t0) * 1000}, "run": run}
            if l.get("native"):
                y, s = p[l["yes"]], p[l["no"]]
                rec.update(probs=[y / (y + s), s / (y + s)], letters=p)
            f.write(json.dumps(rec) + "\n")
            f.flush()
            if n % 25 == 0:
                print(f"[{n + 1}/{len(lines)}] {l['id']}", flush=True)


if __name__ == "__main__":
    main()
