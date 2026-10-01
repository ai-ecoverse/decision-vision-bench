"""RSI-Jev over bench/kev.jsonl through its Jev-compatible server (POST /v1/systemone).

  pip install "rsi-jev[vision] @ git+https://github.com/Shanghua-Gao/RSI-Jev"
  rsi-jev serve shgao/rsi-jev-v4.0-vl-qwen3.5-2b          # http://127.0.0.1:8000
  python3 torch/rsijev_client.py --out results/rsi-jev-v4.0-vl-torch.jsonl

Kev's native requests, one question per request, unchanged; the image goes in the request's `images` as a data URL
of the file's own bytes, and the server puts it before the state. Probabilities come back in the API's native order
(noul: false, true; choice: criteria order; score: levels) and are written in the item's option order through
kev.jsonl's `perm`. One DecisionBench state (b3-m-0054) is an event list whose events carry a free-text `role`; the
server, like Jev's reference, reads that as a chat transcript and refuses it, so it is sent as the same events in
compact JSON text. Standard library only. Appends and resumes like the browser runner.
"""
import argparse
import base64
import json
import time
import urllib.request
from pathlib import Path

BENCH = Path(__file__).resolve().parents[1] / "bench"
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}


def post(url, body):
    req = urllib.request.Request(url, json.dumps(body).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


def native_probs(q, ans):
    if ans["type"] == "noul":
        return [1.0 - ans["noul"], ans["noul"]]
    p = ans["probabilities"]
    if ans["type"] == "score":
        return [p[str(k)] for k in range(len(q["criteria"]))]
    return [p[k] for k in q["criteria"]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", default="http://127.0.0.1:8000")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    lines = [json.loads(l) for l in open(BENCH / "kev.jsonl")]
    done = {json.loads(l)["id"] for l in open(a.out)} if a.out.exists() else set()
    limits = json.loads(urllib.request.urlopen(f"{a.server}/v1/limits", timeout=60).read())
    model = limits["served_model_name"]
    print(f"{model} {limits.get('version')}: {len(lines) - len(done)} of {len(lines)} items to go", flush=True)
    with open(a.out, "a") as f:
        for l in lines:
            if l["id"] in done:
                continue
            body = {"model": model, **l["request"]}
            state, note = body["state"], None
            if isinstance(state, list) and state and all(isinstance(e, dict) and "role" in e for e in state):
                body["state"], note = json.dumps(state, separators=(",", ":"), ensure_ascii=False), "state sent as JSON text"
            if l["image"]:
                p = BENCH / l["image"]
                body["images"] = [f"data:{MIME[p.suffix.lower()]};base64," + base64.b64encode(p.read_bytes()).decode()]
            t0 = time.perf_counter()
            resp = post(f"{a.server}/v1/systemone", body)
            ms = (time.perf_counter() - t0) * 1000
            nat = native_probs(l["request"]["questions"]["q"], resp["answers"]["q"])
            rec = {"id": l["id"], "probs": [nat[j] for j in l["perm"]], "tokens": resp["usage"].get("input_tokens"),
                   "ms": {"total": round(ms, 1)}, "model": resp["model"]}
            if note:
                rec["note"] = note
            f.write(json.dumps(rec) + "\n")
            f.flush()
    print("done", flush=True)


if __name__ == "__main__":
    main()
