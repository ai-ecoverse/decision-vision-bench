#!/bin/sh
# Latency on a spread-out subset (every 12th item, 35 items), the models interleaved over two rounds so that load from
# other work on the machine falls on all of them alike. Results: results/lat-<model>-r<round>.jsonl (+ .meta.json).
set -e
cd "$(dirname "$0")"
for r in 1 2; do
  for m in kev-4b-vision kev-0.8b-vision cua-s1-4b-0.2-multimodal; do
    BENCH_MODEL=$m BENCH_EVERY=12 BENCH_OUT=lat-$m-r$r.jsonl npx playwright test 2>&1 | grep -v "onnxruntime:" | tail -3
  done
done
