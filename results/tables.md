### Paired differences (accuracy of A minus B on the same items, points; 95% CI, tasks resampled)

| A - B | vision-v1 | vision-v2 | gui360-element | gui360-action | decisionbench | all image items |
|---|---|---|---|---|---|---|
| kev-4b-vision-webgpu - cua-s1-4b-0.2-multimodal-webgpu | +5.7 (+0.9, +11.5) | +10.2 (+4.6, +15.6) | -3.3 (-15.0, +8.3) | +13.0 (+1.2, +24.7) | +10.0 (-7.5, +28.6) | +7.3 (+3.3, +11.4) |
| kev-4b-vision-webgpu - jev-omni-webgpu | -0.9 (-4.5, +2.0) | +2.3 (-4.5, +8.7) | +6.7 (-5.0, +18.3) | +13.0 (+3.8, +22.9) | -27.5 (-42.1, -13.2) | +4.3 (+0.0, +8.5) |
| jev-omni-webgpu - cua-s1-4b-0.2-multimodal-webgpu | +6.6 (+1.0, +12.6) | +7.8 (-0.8, +16.3) | -10.0 (-21.7, +1.7) | +0.0 (-10.1, +11.1) | +37.5 (+19.5, +55.3) | +3.0 (-1.8, +7.7) |
| kev-4b-vision-webgpu - kev-0.8b-vision-webgpu | +6.6 (+1.0, +13.0) | +21.1 (+12.2, +29.6) | +8.3 (-3.3, +20.0) | +7.8 (-1.3, +17.3) | +20.0 (+0.0, +39.0) | +12.1 (+7.3, +16.8) |
| kev-0.8b-vision-webgpu - cua-s1-4b-0.2-multimodal-webgpu | -0.9 (-8.7, +6.5) | -10.9 (-18.6, -3.1) | -11.7 (-26.7, +1.7) | +5.2 (-7.5, +18.3) | -10.0 (-27.9, +7.9) | -4.9 (-10.1, +0.5) |

### Accuracy by source (95% CI, tasks resampled); Brier; flatness

| system | source | n | accuracy | 95% CI | chance | Brier | flatness | turf |
|---|---|---:|---:|---|---:|---:|---:|---|
| kev-4b-vision-torch | vision-v1 | 106 | 98.1 | 95.3-100.0 | 36.0 | 0.031 | 0.15 | home |
| kev-4b-vision-torch | vision-v2 | 128 | 87.5 | 82.0-92.7 | 32.0 | 0.184 | 0.34 | home |
| kev-4b-vision-torch | gui360-element | 60 | 61.7 | 48.3-75.0 | 6.4 | 0.534 | 0.60 | cross |
| kev-4b-vision-torch | gui360-action | 77 | 75.3 | 65.8-84.7 | 50.0 | 0.326 | 0.62 | cross |
| kev-4b-vision-torch | decisionbench | 40 | 62.5 | 48.8-75.7 | 34.5 | 0.465 | 0.63 | cross |
| kev-4b-vision-webgpu | vision-v1 | 106 | 97.2 | 93.6-100.0 | 36.0 | 0.032 | 0.15 | home |
| kev-4b-vision-webgpu | vision-v2 | 128 | 87.5 | 82.0-92.7 | 32.0 | 0.186 | 0.34 | home |
| kev-4b-vision-webgpu | gui360-element | 60 | 61.7 | 48.3-75.0 | 6.4 | 0.534 | 0.60 | cross |
| kev-4b-vision-webgpu | gui360-action | 77 | 75.3 | 65.8-84.7 | 50.0 | 0.326 | 0.62 | cross |
| kev-4b-vision-webgpu | decisionbench | 40 | 65.0 | 51.2-78.0 | 34.5 | 0.463 | 0.63 | cross |
| kev-0.8b-vision-torch | vision-v1 | 106 | 90.6 | 84.8-95.9 | 36.0 | 0.146 | 0.44 | home |
| kev-0.8b-vision-torch | vision-v2 | 128 | 67.2 | 58.6-75.8 | 32.0 | 0.453 | 0.74 | home |
| kev-0.8b-vision-torch | gui360-element | 60 | 53.3 | 40.0-66.7 | 6.4 | 0.661 | 0.66 | cross |
| kev-0.8b-vision-torch | gui360-action | 77 | 68.8 | 59.2-78.4 | 50.0 | 0.396 | 0.71 | cross |
| kev-0.8b-vision-torch | decisionbench | 40 | 45.0 | 30.8-60.0 | 34.5 | 0.652 | 0.90 | cross |
| kev-0.8b-vision-webgpu | vision-v1 | 106 | 90.6 | 84.8-95.9 | 36.0 | 0.146 | 0.43 | home |
| kev-0.8b-vision-webgpu | vision-v2 | 128 | 66.4 | 57.4-75.4 | 32.0 | 0.453 | 0.74 | home |
| kev-0.8b-vision-webgpu | gui360-element | 60 | 53.3 | 40.0-66.7 | 6.4 | 0.660 | 0.66 | cross |
| kev-0.8b-vision-webgpu | gui360-action | 77 | 67.5 | 57.7-77.0 | 50.0 | 0.397 | 0.71 | cross |
| kev-0.8b-vision-webgpu | decisionbench | 40 | 45.0 | 30.8-60.0 | 34.5 | 0.652 | 0.90 | cross |
| cua-s1-4b-0.2-multimodal-torch | vision-v1 | 106 | 91.5 | 85.5-96.3 | 36.0 | 0.103 | 0.21 | cross |
| cua-s1-4b-0.2-multimodal-torch | vision-v2 | 128 | 75.8 | 68.2-83.3 | 32.0 | 0.301 | 0.39 | cross |
| cua-s1-4b-0.2-multimodal-torch | gui360-element | 60 | 66.7 | 55.0-78.3 | 6.4 | 0.565 | 0.32 | home |
| cua-s1-4b-0.2-multimodal-torch | gui360-action | 77 | 62.3 | 50.0-72.8 | 50.0 | 0.596 | 0.25 | home |
| cua-s1-4b-0.2-multimodal-torch | decisionbench | 40 | 55.0 | 39.5-69.2 | 34.5 | 0.542 | 0.50 | cross |
| cua-s1-4b-0.2-multimodal-webgpu | vision-v1 | 106 | 91.5 | 85.5-96.3 | 36.0 | 0.101 | 0.21 | cross |
| cua-s1-4b-0.2-multimodal-webgpu | vision-v2 | 128 | 77.3 | 69.9-84.6 | 32.0 | 0.302 | 0.39 | cross |
| cua-s1-4b-0.2-multimodal-webgpu | gui360-element | 60 | 65.0 | 53.3-76.7 | 6.4 | 0.568 | 0.32 | home |
| cua-s1-4b-0.2-multimodal-webgpu | gui360-action | 77 | 62.3 | 50.0-72.8 | 50.0 | 0.607 | 0.24 | home |
| cua-s1-4b-0.2-multimodal-webgpu | decisionbench | 40 | 55.0 | 39.5-69.2 | 34.5 | 0.546 | 0.50 | cross |
| jev-omni-torch | vision-v1 | 106 | 99.1 | 97.0-100.0 | 36.0 | 0.021 | 0.04 | cross |
| jev-omni-torch | vision-v2 | 128 | 85.2 | 77.3-92.5 | 32.0 | 0.178 | 0.18 | cross |
| jev-omni-torch | gui360-element | 60 | 55.0 | 41.7-66.7 | 6.4 | 0.657 | 0.25 | cross |
| jev-omni-torch | gui360-action | 77 | 61.0 | 50.0-71.1 | 50.0 | 0.646 | 0.31 | cross |
| jev-omni-torch | decisionbench | 40 | 92.5 | 82.5-100.0 | 34.5 | 0.162 | 0.30 | home |
| jev-omni-webgpu | vision-v1 | 106 | 98.1 | 95.3-100.0 | 36.0 | 0.022 | 0.04 | cross |
| jev-omni-webgpu | vision-v2 | 128 | 85.2 | 77.3-92.5 | 32.0 | 0.182 | 0.18 | cross |
| jev-omni-webgpu | gui360-element | 60 | 55.0 | 41.7-66.7 | 6.4 | 0.683 | 0.24 | cross |
| jev-omni-webgpu | gui360-action | 77 | 62.3 | 51.8-72.0 | 50.0 | 0.649 | 0.31 | cross |
| jev-omni-webgpu | decisionbench | 40 | 92.5 | 82.5-100.0 | 34.5 | 0.162 | 0.30 | home |
| rsi-jev-v4.0-vl-torch | vision-v1 | 106 | 96.2 | 92.4-99.1 | 36.0 | 0.053 | 0.13 | cross |
| rsi-jev-v4.0-vl-torch | vision-v2 | 128 | 85.2 | 78.6-91.7 | 32.0 | 0.223 | 0.35 | cross |
| rsi-jev-v4.0-vl-torch | gui360-element | 60 | 48.3 | 36.7-61.7 | 6.4 | 0.791 | 0.28 | cross |
| rsi-jev-v4.0-vl-torch | gui360-action | 77 | 62.3 | 51.5-72.3 | 50.0 | 0.579 | 0.43 | cross |
| rsi-jev-v4.0-vl-torch | decisionbench | 40 | 57.5 | 41.5-73.3 | 34.5 | 0.495 | 0.69 | cross |

### Home turf vs cross-domain (and every image item)

| system | home n | home acc (CI) | cross n | cross acc (CI) | image items acc (CI) | GUI-360 tasks right |
|---|---:|---|---:|---|---|---|
| kev-4b-vision-torch | 234 | 92.3 (88.9-95.4) | 177 | 67.8 (60.0-75.9) | 83.8 (79.1-88.2) | 41/60 |
| kev-4b-vision-webgpu | 234 | 91.9 (88.5-95.2) | 177 | 68.4 (60.5-76.4) | 83.6 (78.9-87.9) | 41/60 |
| kev-0.8b-vision-torch | 234 | 77.8 (71.8-83.6) | 177 | 58.2 (50.0-66.1) | 72.0 (66.8-77.1) | 36/60 |
| kev-0.8b-vision-webgpu | 234 | 77.4 (71.0-83.4) | 177 | 57.6 (49.4-65.4) | 71.4 (65.9-76.8) | 35/60 |
| cua-s1-4b-0.2-multimodal-torch | 137 | 64.2 (54.7-73.3) | 274 | 78.8 (73.4-83.9) | 76.0 (71.0-80.5) | 31/60 |
| cua-s1-4b-0.2-multimodal-webgpu | 137 | 63.5 (53.8-72.8) | 274 | 79.6 (74.4-84.5) | 76.3 (71.2-80.8) | 31/60 |
| jev-omni-torch | 40 | 92.5 (82.5-100.0) | 371 | 79.2 (73.8-84.4) | 79.2 (73.8-84.4) | 30/60 |
| jev-omni-webgpu | 40 | 92.5 (82.5-100.0) | 371 | 79.2 (73.9-84.2) | 79.2 (73.9-84.2) | 31/60 |
| rsi-jev-v4.0-vl-torch | 0 | - | 411 | 75.7 (70.6-80.4) | 77.6 (72.5-82.5) | 31/60 |

### Accuracy by category

| system | counting | charts | small_text | scene | gui | text |
|---|---:|---:|---:|---:|---:|---:|
| kev-4b-vision-torch | 69.2 (n=39) | 90.5 (n=42) | 98.2 (n=112) | 100.0 (n=41) | 69.3 (n=137) | 62.5 (n=40) |
| kev-4b-vision-webgpu | 66.7 (n=39) | 90.5 (n=42) | 98.2 (n=112) | 100.0 (n=41) | 69.3 (n=137) | 65.0 (n=40) |
| kev-0.8b-vision-torch | 30.8 (n=39) | 88.1 (n=42) | 83.0 (n=112) | 97.6 (n=41) | 62.0 (n=137) | 45.0 (n=40) |
| kev-0.8b-vision-webgpu | 28.2 (n=39) | 88.1 (n=42) | 83.0 (n=112) | 97.6 (n=41) | 61.3 (n=137) | 45.0 (n=40) |
| cua-s1-4b-0.2-multimodal-torch | 46.2 (n=39) | 85.7 (n=42) | 90.2 (n=112) | 95.1 (n=41) | 64.2 (n=137) | 55.0 (n=40) |
| cua-s1-4b-0.2-multimodal-webgpu | 48.7 (n=39) | 85.7 (n=42) | 91.1 (n=112) | 95.1 (n=41) | 63.5 (n=137) | 55.0 (n=40) |
| jev-omni-torch | 64.1 (n=39) | 97.6 (n=42) | 95.5 (n=112) | 100.0 (n=41) | 58.4 (n=137) | 92.5 (n=40) |
| jev-omni-webgpu | 61.5 (n=39) | 97.6 (n=42) | 95.5 (n=112) | 100.0 (n=41) | 59.1 (n=137) | 92.5 (n=40) |
| rsi-jev-v4.0-vl-torch | 59.0 (n=39) | 100.0 (n=42) | 94.6 (n=112) | 97.6 (n=41) | 56.2 (n=137) | 57.5 (n=40) |

### Latency in the full runs (median ms per item: image = preprocess + vision tower; one model at a time, on a shared machine)

| system | source | items | total | image | decoder |
|---|---|---:|---:|---:|---:|
| kev-4b-vision-webgpu | vision-v1 | 106 | 1650 | 499 | 1188 |
| kev-4b-vision-webgpu | vision-v2 | 128 | 4046 | 1550 | 2501 |
| kev-4b-vision-webgpu | gui360-element | 60 | 1667 | 522 | 1136 |
| kev-4b-vision-webgpu | gui360-action | 77 | 1471 | 522 | 948 |
| kev-4b-vision-webgpu | decisionbench | 40 | 9835 | 0 | 9830 |
| kev-0.8b-vision-webgpu | vision-v1 | 106 | 821 | 298 | 513 |
| kev-0.8b-vision-webgpu | vision-v2 | 128 | 1514 | 755 | 759 |
| kev-0.8b-vision-webgpu | gui360-element | 60 | 1863 | 813 | 1015 |
| kev-0.8b-vision-webgpu | gui360-action | 77 | 1737 | 819 | 913 |
| kev-0.8b-vision-webgpu | decisionbench | 40 | 1061 | 0 | 1056 |
| cua-s1-4b-0.2-multimodal-webgpu | vision-v1 | 106 | 2126 | 550 | 1562 |
| cua-s1-4b-0.2-multimodal-webgpu | vision-v2 | 128 | 2645 | 1116 | 1521 |
| cua-s1-4b-0.2-multimodal-webgpu | gui360-element | 60 | 2225 | 752 | 1473 |
| cua-s1-4b-0.2-multimodal-webgpu | gui360-action | 60 | 2251 | 748 | 1504 |
| cua-s1-4b-0.2-multimodal-webgpu | decisionbench | 40 | 9422 | 0 | 9422 |
| jev-omni-webgpu | vision-v1 | 106 | 1241 | 26 | 1214 |
| jev-omni-webgpu | vision-v2 | 128 | 1283 | 39 | 1238 |
| jev-omni-webgpu | gui360-element | 60 | 2110 | 34 | 2074 |
| jev-omni-webgpu | gui360-action | 77 | 1487 | 34 | 1452 |

### Latency, interleaved passes (latency.sh: 35 items x 2 rounds per model; median ms)

| model | items | n | total | image | decoder | tokens | image tokens |
|---|---|---:|---:|---:|---:|---:|---:|
| Kev-4B | image, small (vision-v1) | 18 | 520 | 134 | 384 | 232 | 196 |
| Kev-4B | image, page (vision-v2, GUI-360) | 44 | 1352 | 489 | 856 | 624 | 560 |
| Kev-4B | text only (DecisionBench) | 8 | 4426 | 0 | 4421 | 2807 | 0 |
| Kev-0.8B | image, small (vision-v1) | 18 | 141 | 45 | 94 | 232 | 196 |
| Kev-0.8B | image, page (vision-v2, GUI-360) | 44 | 382 | 189 | 187 | 624 | 560 |
| Kev-0.8B | text only (DecisionBench) | 8 | 922 | 0 | 917 | 2807 | 0 |
| cua-s1-4b-0.2 | image, small (vision-v1) | 18 | 640 | 134 | 477 | 383 | 196 |
| cua-s1-4b-0.2 | image, page (vision-v2, GUI-360) | 44 | 2157 | 724 | 1431 | 1110 | 736 |
| cua-s1-4b-0.2 | text only (DecisionBench) | 8 | 4881 | 0 | 4881 | 2973 | 0 |
| Jev-Omni | image, small (vision-v1) | 106 | 1241 | 26 | 1214 | 328 | 256 |
| Jev-Omni | image, page (vision-v2, GUI-360) | 265 | 1390 | 34 | 1347 | 380 | 266 |

| system | adapter | load ms | bundle GB | browser memory peak GB (idle before load) |
|---|---|---:|---:|---|
| kev-4b-vision-webgpu | apple metal-3 | 11270 | 5.34 | 14.4 (0.6) |
| kev-0.8b-vision-webgpu | apple metal-3 | 1968 | 1.02 | 5.0 (0.6) |
| cua-s1-4b-0.2-multimodal-webgpu | apple metal-3 | 6461 | 5.34 | 15.9 (0.8) |

### Browser vs PyTorch

| system | reference | n | same pick | mean abs dp | max abs dp |
|---|---|---:|---:|---:|---:|
| cua-s1-4b-0.2-multimodal-webgpu | cua-s1-4b-0.2-multimodal-torch | 411 | 99.3 | 0.0039 | 0.116 |
| kev-0.8b-vision-webgpu | kev-0.8b-vision-torch | 411 | 99.5 | 0.0018 | 0.019 |
| kev-4b-vision-webgpu | kev-4b-vision-torch | 411 | 99.3 | 0.0016 | 0.048 |
| jev-omni-webgpu | jev-omni-torch | 411 | 99.0 | 0.0045 | 0.445 |
