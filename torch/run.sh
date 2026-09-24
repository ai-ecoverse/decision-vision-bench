#!/bin/sh
# The PyTorch references, one after the other (each resumes if interrupted).
set -e
B="$(cd "$(dirname "$0")/.." && pwd)"
CUA="${CUA_EXPORT:-$B/../cua-s1.js/export}"
cd "$B/../kev-vision/export"
PYTHONPATH="$PWD" uv run --group vision python "$B/torch/kev_torch.py" --run jaredpalmer/kev-4b@4bc64c6b4c4881148661ffb823ce21fcfdc79a0e --out "$B/results/kev-4b-vision-torch.jsonl"
PYTHONPATH="$PWD" uv run --group vision python "$B/torch/kev_torch.py" --run jaredpalmer/kev-0.8b@225679690cdd1de6fceb1258b1bddf61c493cee9 --out "$B/results/kev-0.8b-vision-torch.jsonl"
cd "$CUA"
PYTHONPATH="$CUA" .venv/bin/python "$B/torch/cua_torch.py" --out "$B/results/cua-s1-4b-0.2-multimodal-torch.jsonl"
