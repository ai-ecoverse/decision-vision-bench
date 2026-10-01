# decision-vision-bench

Three browser decision models on one mixed set of image (and some text) questions. Each model gets every item in its
own native request format. The models come from three sibling projects: [kev.js](https://github.com/ai-ecoverse/kev.js),
[cua-s1.js](https://github.com/ai-ecoverse/cua-s1.js) and [jev-omni.js](https://github.com/ai-ecoverse/jev-omni.js).

| model | what it is | bundle |
|---|---|---|
| **Kev-4B vision** (Kev-0.8B as a second row) | [kev.js](https://github.com/ai-ecoverse/kev.js) ([#18](https://github.com/ai-ecoverse/kev.js/pull/18) @ 8ee0118): Kev's pointer head behind Qwen3.5's stock vision tower | 5.34 GB (1.02 GB) |
| **cua-s1-4b-0.2 multimodal** | [cua-s1.js](https://github.com/ai-ecoverse/cua-s1.js) 0.3.0 `./4b`: a LoRA on Qwen3.5-4B that picks one lettered (element, action) option from a screenshot | 5.34 GB |
| **Jev-Omni** | [jev-omni.js](https://github.com/ai-ecoverse/jev-omni.js) @ 008099d: Gemma 4 12B with a 256-way head, and images through Gemma 4's own vision embedder | 13.58 GB |
| **RSI-Jev v4.0-VL** (server, not a browser model) | [RSI-Jev](https://github.com/Shanghua-Gao/RSI-Jev) @ 887cbeb: a 2B open model (Apache-2.0 weights) on Qwen3.5-2B, served through a Jev-compatible API. See [below](#rsi-jev-v40-vl) | 5.62 GB (PyTorch weights) |

The set has 411 items (`bench/items.jsonl`):
- kev.js vision-v1 (106) and vision-v2 (128);
- cua-s1.js's 60 GUI-360 screens, asked two ways: element choice (60) and per-element action (77);
- a 40-question DecisionBench medium slice (text only), as a sanity row.

[CONVERSIONS.md](CONVERSIONS.md) describes every mapping. Each model's home turf is where its own data comes from:
- Kev: vision-v1/v2, which were built in the kev.js vision work;
- cua-s1: GUI-360;
- Jev-Omni: DecisionBench.

All numbers are Chrome WebGPU on an Apple M-series GPU (`apple metal-3`), q8f32 bundles. PyTorch fp32 references ran
alongside, and the browser matches them. The full tables are in [results/tables.md](results/tables.md) and the raw
numbers in `results/summary.json`.

## Recommendation

**Use Kev-4B vision as the default browser model for decisions about images.**
- **Image questions (234 items):** it ties Jev-Omni, within 1-2 points either way and not significant, and beats
  cua-s1 by 7 points (95% CI +3 to +11).
- **Calibration:** it is the best calibrated of the three on image items (Brier 0.23, against 0.31 for Jev-Omni and
  0.35 for cua-s1).
- **Download:** 40% of Jev-Omni's.
- **Speed:** 2.4x faster than Jev-Omni on small images, and as fast on full pages.

Kev-0.8B (1 GB, 0.14-0.38 s) is the choice when download size or latency matters most. It is fine on charts and
scenes but poor at counting (28%) and weaker on rendered pages (66% on vision-v2).

Keep Jev-Omni for long text case records. On DecisionBench, its home turf, it is 27 points ahead of Kev-4B and 37
points ahead of cua-s1. It is also the slowest model and the largest download.

**Do not use cua-s1-4b-0.2 multimodal as a general image decision model:**
- On image questions it is worse than Kev-4B and Jev-Omni.
- Even on GUI-360, its own data, it does not beat Kev-4B:
  - element choice: 65.0% against 61.7%, not significant;
  - per-element action: 62.3% against 75.3%.

**None of the three can pick the next GUI action on a real Office screen yet.** On the per-element action items, no
model beats always answering "yes":
- always yes: 77.9% of items, 43/60 screens;
- Kev-4B: 75.3%, 41/60;
- cua-s1: 62.3%, 31/60;
- Jev-Omni: 62.3%, 31/60.

## Results (Chrome WebGPU)

Accuracy in %, with 95% intervals from resampling tasks (an image, screen or state, together with all its questions).
**Bold** marks each model's home turf. Chance is the mean of 1/K.

| source (n, chance) | Kev-4B | Kev-0.8B | cua-s1-4b-0.2 | Jev-Omni | RSI-Jev v4.0-VL* |
|---|---|---|---|---|---|
| vision-v1 (106, 36.0) | **97.2** (93.6-100) | **90.6** (84.8-95.9) | 91.5 (85.5-96.3) | 98.1 (95.3-100) | 96.2 (92.4-99.1) |
| vision-v2 (128, 32.0) | **87.5** (82.0-92.7) | **66.4** (57.4-75.4) | 77.3 (69.9-84.6) | 85.2 (77.3-92.5) | 85.2 (78.6-91.7) |
| GUI-360 element choice (60, 6.4) | 61.7 (48.3-75.0) | 53.3 (40.0-66.7) | **65.0** (53.3-76.7) | 55.0 (41.7-66.7) | 48.3 (36.7-61.7) |
| GUI-360 action, yes/no (77, 50.0; always yes 77.9) | 75.3 (65.8-84.7) | 67.5 (57.7-77.0) | **62.3** (50.0-72.8) | 62.3 (51.8-72.0) | 62.3 (51.5-72.3) |
| GUI-360 screens right (cua-bench-s1 task score; always yes 43/60) | 41/60 | 35/60 | **31/60** | 31/60 | 31/60 |
| DecisionBench slice, text (40, 34.5) | 65.0 (51.2-78.0) | 45.0 (30.8-60.0) | 55.0 (39.5-69.2) | **92.5** (82.5-100) | 57.5 (41.5-73.3) |

*PyTorch bf16 on an NVIDIA GPU, not Chrome WebGPU. It has no home turf in this set.

**Home turf vs cross-domain.** Kev and Jev-Omni lose accuracy away from home; cua-s1 does better away from home:

| | Kev-4B | Kev-0.8B | cua-s1-4b-0.2 | Jev-Omni | RSI-Jev v4.0-VL* |
|---|---|---|---|---|---|
| home: n, accuracy | 234: 91.9 (88.5-95.2) | 234: 77.4 (71.0-83.4) | 137: 63.5 (53.8-72.8) | 40: 92.5 (82.5-100) | - |
| cross-domain: n, accuracy | 177: 68.4 (60.5-76.4) | 177: 57.6 (49.4-65.4) | 274: 79.6 (74.4-84.5) | 371: 79.2 (73.9-84.2) | 411: 75.7 (70.6-80.4) |
| all 371 image items | 83.6 (78.9-87.9) | 71.4 (65.9-76.8) | 76.3 (71.2-80.8) | 79.2 (73.9-84.2) | 77.6 (72.5-82.5) |

cua-s1's home turf is its weakest source. Its GUI-360 score matches its own published multimodal number, 31/60
(cua-s1.js README). Its adapter was trained on synthetic cua-bench-s1 forms, so real Office screens are hard for it
too.

**Paired differences.** Accuracy points on the same items, 95% CI:

| A − B | vision-v1 | vision-v2 | GUI element | GUI action | DecisionBench | all images |
|---|---|---|---|---|---|---|
| Kev-4B − cua-s1 | +5.7 (+0.9, +11.5) | +10.2 (+4.6, +15.6) | −3.3 (−15.0, +8.3) | +13.0 (+1.2, +24.7) | +10.0 (−7.5, +28.6) | +7.3 (+3.3, +11.4) |
| Kev-4B − Jev-Omni | −0.9 (−4.5, +2.0) | +2.3 (−4.5, +8.7) | +6.7 (−5.0, +18.3) | +13.0 (+3.8, +22.9) | −27.5 (−42.1, −13.2) | +4.3 (+0.0, +8.5) |
| Jev-Omni − cua-s1 | +6.6 (+1.0, +12.6) | +7.8 (−0.8, +16.3) | −10.0 (−21.7, +1.7) | +0.0 (−10.1, +11.1) | +37.5 (+19.5, +55.3) | +3.0 (−1.8, +7.7) |
| Kev-4B − Kev-0.8B | +6.6 (+1.0, +13.0) | +21.1 (+12.2, +29.6) | +8.3 (−3.3, +20.0) | +7.8 (−1.3, +17.3) | +20.0 (+0.0, +39.0) | +12.1 (+7.3, +16.8) |

**By category** (accuracy, n). `small_text` covers screenshots, receipts, tables and fine print; see CONVERSIONS.md:

| | counting (39) | charts (42) | small text (112) | scene (41) | GUI (137) | text (40) |
|---|---:|---:|---:|---:|---:|---:|
| Kev-4B | 66.7 | 90.5 | **98.2** | 100.0 | **69.3** | 65.0 |
| Kev-0.8B | 28.2 | 88.1 | 83.0 | 97.6 | 61.3 | 45.0 |
| cua-s1-4b-0.2 | 48.7 | 85.7 | 91.1 | 95.1 | 63.5 | 55.0 |
| Jev-Omni | 61.5 | **97.6** | 95.5 | 100.0 | 59.1 | **92.5** |
| RSI-Jev v4.0-VL* | 59.0 | 100.0 | 94.6 | 97.6 | 56.2 | 57.5 |

**Calibration.** Brier is summed over options: 0 is perfect, and uniform guessing scores 1 − 1/K. Flatness is the
mean entropy divided by log K, where 1 is uniform.

| | Brier: home / cross / images | flatness: home / cross / images |
|---|---|---|
| Kev-4B | 0.116 / 0.427 / **0.227** | 0.25 / 0.61 / 0.39 |
| Kev-0.8B | 0.314 / 0.544 / 0.387 | 0.60 / 0.74 / 0.63 |
| cua-s1-4b-0.2 | 0.590 / 0.260 / 0.351 | 0.28 / 0.34 / 0.30 |
| Jev-Omni | 0.162 / 0.314 / 0.314 | 0.30 / 0.18 / 0.18 |
| RSI-Jev v4.0-VL* | - / 0.355 / 0.340 | - / 0.33 / 0.30 |

- **Kev** spreads its probabilities when it leaves home. The answer is uncertain, not confidently wrong.
- **Jev-Omni and cua-s1** stay sharp away from home. cua-s1 on its GUI home turf is confidently wrong (Brier 0.59 at
  flatness 0.28).

## Latency, size and memory

**Latency.** Median ms per item, cold: every item runs its own vision and decoder pass, and Kev's state cache is off.
"Image" means preprocessing plus the vision tower.
- **Kev and cua-s1:** `latency.sh` ran them interleaved over two rounds (35 spread-out items each), so load from other
  work on the machine fell on all of them alike.
- **Jev-Omni:** the Jev-Omni thread ran it separately, over all 371 image rows, in Playwright's headless Chromium.
  Its text-only row comes from its earlier DecisionBench run.

| | small image (vision-v1): total / image / decoder | page (vision-v2, GUI-360): total / image / decoder | text only, ~2.5k tokens | image tokens: small / page |
|---|---|---|---|---|
| Kev-4B | 520 / 134 / 384 | 1352 / 489 / 856 | 4426 | 196 / 560 |
| Kev-0.8B | **141** / 45 / 94 | **382** / 189 / 187 | **922** | 196 / 560 |
| cua-s1-4b-0.2 | 640 / 134 / 477 | 2157 / 724 / 1431 | 4881 | 196 / 736 |
| Jev-Omni | 1241 / 26 / 1214 | 1390 / 34 / 1347 | 12080 | 256 / 266 |

- Kev and cua-s1 share the Qwen3.5 tower. cua-s1 is slower because its processor allows more pixels (736 tokens on a
  page, against 560) and its prompt is longer (the system prompt and the lettered options).
- Jev-Omni's vision embedder is almost free. It caps every image at 256-280 tokens, and its 12B decoder costs about
  1.2 s even on a small image.

**Size and memory.** Bundle sizes come from each manifest (the decoder variant plus the vision graph). Memory is the
peak physical footprint of the browser's processes during the full run, GPU buffers included (top's MEM, summed over
the Chrome process tree), with the idle browser in parentheses.

| | bundle | load from local disk | browser memory, peak |
|---|---:|---:|---|
| Kev-4B | 5.34 GB | 11.3 s | 14.4 GB (0.6) |
| Kev-0.8B | 1.02 GB | 2.0 s | 5.0 GB (0.6) |
| cua-s1-4b-0.2 | 5.34 GB | 6.5 s | 15.9 GB (0.8) |
| Jev-Omni | 13.58 GB | 12-18 s | about 16 GB in Chrome's GPU process alone (Jev-Omni thread, `footprint`; measured differently) |

PyTorch fp32 needs at least 16 GB for the weights of Kev-4B or cua-s1, and about 48 GB for Jev-Omni (Jev-Omni
thread).

## Browser vs PyTorch

Every browser run agrees with its fp32 PyTorch reference: Kev through `kev_web_export.vision`, cua-s1 through
upstream's `cua_s1.four_b.FourBModel`, Jev-Omni through its `predict.py`. Accuracies match to within one or two items
per source.

| | items | same pick | mean abs dp | max abs dp |
|---|---:|---:|---:|---:|
| Kev-4B | 411 | 99.3% | 0.0016 | 0.048 |
| Kev-0.8B | 411 | 99.5% | 0.0018 | 0.019 |
| cua-s1-4b-0.2 | 411 | 99.3% | 0.0039 | 0.116 |
| Jev-Omni | 411 | 99.0% | 0.0045 | 0.445 |

## Caveats

- **Shared machine.** Other training jobs were running during the full runs. Latency in those runs was 2-6x the
  interleaved numbers (results/tables.md has both), so only the interleaved table should be quoted.
- **Different browser for Jev-Omni.** Its latency and memory come from a separate run in Playwright's Chromium, not
  Chrome.
- **GUI-360 labels.** The gold labels are one recorded trajectory, and a few are debatable. In 20 screens, duplicate
  element names are merged or ambiguous (CONVERSIONS.md). The action items lean towards yes.
- **Small DecisionBench slice.** It has only 40 questions, so its intervals are about ±15 points.
- **cua-s1 on text is off-distribution.** The multimodal adapter answers text-only questions through the text-modality
  prompt it was not trained with.
- **Serving temperature.** Kev probabilities are at the checkpoint's serving temperature, as kev.js serves them.
  cua-s1 and Jev-Omni have no temperature.

## RSI-Jev v4.0-VL

[RSI-Jev](https://github.com/Shanghua-Gao/RSI-Jev) v4.0-VL is a 2B open model (Apache-2.0 weights,
[shgao/rsi-jev-v4.0-vl-qwen3.5-2b](https://huggingface.co/shgao/rsi-jev-v4.0-vl-qwen3.5-2b)), served through a
Jev-compatible API. Its rows come from PyTorch bf16 on an NVIDIA GPU (code @ 887cbeb, weights @ 079ec5f), so it has
no latency, memory or browser-parity rows. It gets Kev's native requests from `bench/kev.jsonl`, one question per
request, with the image before the state (CONVERSIONS.md). The results file was written through the package's Python
`Decider`, which runs the same request path as the server's `POST /v1/systemone`. `torch/rsijev_client.py` sends the
same requests over HTTP. Per-item outputs: `results/rsi-jev-v4.0-vl-torch.jsonl`.

On the 234 image items (vision-v1 and vision-v2), it scores **90.2%** (85.7-94.0):

| 234 image items | accuracy (95% CI) |
|---|---|
| Kev-4B | 91.9 (88.5-95.2) |
| Kev-0.8B | 77.4 (71.0-83.4) |
| cua-s1-4b-0.2 | 83.8 (78.5-88.8) |
| Jev-Omni | 91.0 (86.2-95.3) |
| RSI-Jev v4.0-VL | 90.2 (85.7-94.0) |

To reproduce, on a CUDA GPU (the run also had flash-linear-attention, the package's `fast` extra):

```sh
pip install "rsi-jev[vision] @ git+https://github.com/Shanghua-Gao/RSI-Jev"
rsi-jev serve shgao/rsi-jev-v4.0-vl-qwen3.5-2b          # http://127.0.0.1:8000
python3 torch/rsijev_client.py --out results/rsi-jev-v4.0-vl-torch.jsonl
python3 metrics.py
```

## Running it

```sh
npm install
python3 convert.py                  # bench/*.jsonl and bench/images from ../kev-vision, a cua-s1.js checkout and the HF cache
# models/: kev-4b-vision and kev-0.8b-vision (symlinks into ../kev-vision/public/models), cua-s1-4b-0.2-multimodal
./run-all.sh                        # Chrome WebGPU, every model, resumable -> results/<model>-webgpu.jsonl + .meta.json
./latency.sh                        # interleaved latency passes -> results/lat-*.jsonl
./torch/run.sh                      # PyTorch references (kev.js and cua-s1.js export environments)
# Jev-Omni (in jev-omni.js): predict.py and scripts/predict.ts over bench/jev.jsonl -> build/eval/dvb-{torch,webgpu}.jsonl
#   (image paths are relative to this repo's root: run them from here, or rewrite the prefix)
python3 metrics.py                  # results/summary.json, results/tables.md
```

One model at a time: `BENCH_MODEL=kev-4b-vision npx playwright test`. The options are `BENCH_LIMIT`, `BENCH_ONLY` (id
prefix), `BENCH_EVERY`, `BENCH_EP=wasm` and `BENCH_CHANNEL` (default `chrome`: Playwright's own headless Chromium
stalls on the 4B graphs on macOS).

## Licenses

The code is Apache-2.0 ([LICENSE](LICENSE)). The items come from:
- kev.js `eval/vision-v1` and `eval/vision-v2`: generated images (Apache-2.0) and 7 scikit-image sample photos (public
  domain or CC0), listed in kev.js's `eval/vision-v1/README.md`;
- [GUI-360](https://huggingface.co/datasets/vyokky/GUI-360) test-split screenshots and steps (MIT), as selected in
  cua-s1.js;
- [DecisionBench](https://huggingface.co/datasets/akhilaaa3/decision-bench) medium (Apache-2.0).
