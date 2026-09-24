#!/bin/sh
# Every browser model over the whole set, one after the other (resumable: rerun to finish an interrupted model).
set -e
cd "$(dirname "$0")"
for m in ${BENCH_MODELS:-kev-4b-vision kev-0.8b-vision cua-s1-4b-0.2-multimodal}; do
  BENCH_MODEL=$m npx playwright test 2>&1 | grep -v "onnxruntime:" | tee "results/$m-webgpu.log"
done
