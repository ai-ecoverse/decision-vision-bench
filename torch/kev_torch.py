"""Kev in PyTorch (fp32, the stock Qwen3.5 vision tower in front) over bench/kev.jsonl: the reference for the browser.

Run from kev.js's export environment (kev-vision/export), which has kev and kev_web_export:

  cd ../kev-vision/export && uv run --group vision python ../../decision-vision-bench/torch/kev_torch.py \\
      --run jaredpalmer/kev-4b@<sha> --out ../../decision-vision-bench/results/kev-4b-vision-torch.jsonl

Probabilities are at the checkpoint's serving temperature (what kev.js serves), in the item's option order. Appends
and resumes like the browser runner.
"""
import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from PIL import Image

from kev_web_export.vision import VisionKev
from kev_web_export.vision_eval import NIGHT2_T

BENCH = Path(__file__).resolve().parents[1] / "bench"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--device", default="mps")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    lines = [json.loads(l) for l in open(BENCH / "kev.jsonl")]
    done = {json.loads(l)["id"] for l in open(a.out)} if a.out.exists() else set()
    vk = VisionKev(a.run, a.device)
    T = vk.meta.temperature if vk.meta.temperature != 1.0 else NIGHT2_T.get(vk.run.partition("@")[2], 1.0)
    print(f"{vk.run}: temperature {T}, {len(lines) - len(done)} of {len(lines)} items to go", flush=True)
    embeds = {}
    with open(a.out, "a") as f:
        for n, l in enumerate(lines):
            if l["id"] in done:
                continue
            t0 = time.perf_counter()
            e = None
            if l["image"]:
                if l["image"] not in embeds:
                    embeds.clear()   # items of one image are consecutive; keep one tower output at a time
                    embeds[l["image"]] = vk.image_embeds(Image.open(BENCH / l["image"]).convert("RGB"))
                e = embeds[l["image"]]
            (z,), _ = vk.logits(l["request"], embeds=e)
            p = F.softmax(z.float() / T, -1).tolist()
            f.write(json.dumps({"id": l["id"], "probs": [p[j] for j in l["perm"]], "logits": z.tolist(), "temperature": T,
                                "ms": {"total": (time.perf_counter() - t0) * 1000}, "run": vk.run}) + "\n")
            f.flush()
            if n % 25 == 0:
                print(f"[{n + 1}/{len(lines)}] {l['id']}", flush=True)


if __name__ == "__main__":
    main()
