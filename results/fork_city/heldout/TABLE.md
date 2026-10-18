# Final held-out ActionBench measurements

All values are averages of seed means (four families per seed), not pooled decision rates. CIs are 95% t intervals over30 seeds.

| Agents | Condition | Local QA | Action error | Autonomy | Reserve risk | Regret [95% CI] |
|---:|---|---:|---:|---:|---:|---|
| 8 | always_defer | 0.000 | 0.471 | 0.000 | 0.000 | 2.828 [2.338, 3.317] |
| 8 | always_verify | 0.000 | 0.000 | 0.000 | 0.000 | 1.500 [1.500, 1.500] |
| 8 | bm25 | 0.971 | 0.378 | 0.406 | 0.408 | 1.627 [1.443, 1.811] |
| 8 | bm25_lineage2 | 0.790 | 0.421 | 0.316 | 0.358 | 2.071 [1.822, 2.321] |
| 8 | guarded_lineage1 | 1.000 | 0.401 | 0.432 | 0.513 | 1.756 [1.615, 1.897] |
| 8 | guarded_lineage2 | 1.000 | 0.317 | 0.246 | 0.344 | 1.815 [1.631, 2.001] |
| 8 | guarded_lineage3 | 1.000 | 0.300 | 0.219 | 0.305 | 1.823 [1.630, 2.016] |
| 8 | guarded_sources2 | 1.000 | 0.340 | 0.279 | 0.463 | 1.828 [1.654, 2.001] |
| 8 | hybrid | 0.979 | 0.376 | 0.411 | 0.394 | 1.611 [1.426, 1.795] |
| 8 | hybrid_guarded | 1.000 | 0.376 | 0.411 | 0.394 | 1.611 [1.426, 1.795] |
| 8 | structured | 1.000 | 0.376 | 0.411 | 0.394 | 1.611 [1.426, 1.795] |
| 32 | always_defer | 0.000 | 0.470 | 0.000 | 0.000 | 2.822 [2.336, 3.308] |
| 32 | always_verify | 0.000 | 0.000 | 0.000 | 0.000 | 1.500 [1.500, 1.500] |
| 32 | bm25 | 0.981 | 0.443 | 0.426 | 0.545 | 1.851 [1.666, 2.035] |
| 32 | bm25_lineage2 | 0.718 | 0.458 | 0.372 | 0.499 | 2.098 [1.869, 2.327] |
| 32 | guarded_lineage1 | 1.000 | 0.436 | 0.436 | 0.567 | 1.871 [1.705, 2.037] |
| 32 | guarded_lineage2 | 1.000 | 0.345 | 0.275 | 0.543 | 1.851 [1.675, 2.027] |
| 32 | guarded_lineage3 | 1.000 | 0.327 | 0.245 | 0.500 | 1.849 [1.669, 2.029] |
| 32 | guarded_sources2 | 1.000 | 0.356 | 0.292 | 0.555 | 1.854 [1.680, 2.028] |
| 32 | hybrid | 0.995 | 0.439 | 0.428 | 0.541 | 1.832 [1.646, 2.018] |
| 32 | hybrid_guarded | 1.000 | 0.439 | 0.428 | 0.541 | 1.832 [1.646, 2.018] |
| 32 | structured | 1.000 | 0.439 | 0.428 | 0.541 | 1.832 [1.646, 2.018] |

Always-defer/verify have no memory QA task; their raw QA field is0 because no QA label is emitted. Their zero reserve risk must be read together with zero coverage.

Recorded 2,640 worlds and 368,385 decisions. See raw.jsonl.gz, config.json and summary.json for all diagnostics and paired contrasts.
