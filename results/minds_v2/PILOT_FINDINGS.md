# Development pilot — not confirmatory evidence

21 October 2026. The current study source is `01ab6af`; `pilot_v3/` contains 48 authored worlds (eight development seeds × six families), each executing fourteen memory/reference arms. No registration or heldout run has occurred at this checkpoint. `source_provenance.json` verifies all recorded method hashes against the commit.

| Policy | Mean executed utility | Goal completion | Verification rate | Mean serialized bytes |
|---|---:|---:|---:|---:|
| Bounded structured |3.667|91.7%|25.0%|3319|
| Minds V2 |3.833|91.7%|8.3%|3950|
| No consolidation |3.833|91.7%|8.3%|3356|
| No lineage |3.542|87.5%|0%|4047|
| No revision |1.875|66.7%|8.3%|3629|

The paired seed-mean utility difference from structured is **+0.167 coin-equivalent**; the descriptive development bootstrap interval is [0.042,0.292]. The gain comes from fewer paid checks after interference in personal-history and absence cases. Goal completion did not improve. Disabling consolidation has **no utility loss and uses fewer bytes**: this pilot does not support a consolidation-benefit claim. Salience/goal retention can retain these simple old facts without a semantic layer.

Removing lineage loses on misleading repeated testimony but saves an unnecessary check when the shared report happens to be right. Removing revision leaves fourteen correction episodes unrecovered and thirty-six obsolete-belief steps in this pilot. These are effects of explicitly authored information rules under a fixed selector, not evidence of open-ended social intelligence. Structured and guarded coincide on the keyed track; the guarded text fallback is never presented as a real dense baseline.

The first two development pilots are preserved separately. V2 corrected the privileged-reference verification behavior and specified harder future parameter/text shifts. V3 fixed an option-construction bug that could query separate context caps before the selector; all decision reads now share one complete cap. Correction diagnostics use actually admitted paid-check observations. Pilot1 source bytes are preserved and hash-verified; pilot2 and3 have committed-source provenance. The pilots are not pooled.

`verify_artifacts.py` independently folds every recorded cash/goods transfer and recomputes utilities, completion, access/budget assertions and aggregate/paired intervals without importing the memory architecture or evaluator. All 672 pilot3 arm cases pass. The Matplotlib figure `pilot_v3/comparison.png` was visually inspected. Both scripts are outside the zero-dependency game runtime.

Reproduce the development run into a new directory:

```sh
python3 -m kalends_rebirth.mindsbench_v2 pilot --out results/minds_v2/NEW_PILOT
python3 results/minds_v2/verify_artifacts.py results/minds_v2/NEW_PILOT
MPLCONFIGDIR=/tmp/kalends-mpl python3 results/minds_v2/plot_results.py results/minds_v2/NEW_PILOT results/minds_v2/NEW_PLOT.png
```

The game/study requires Python3.10+; the independent verifier and plotting script can use Python3.9+. On this machine, bundled Python3.12 runs the study and `/usr/bin/python3` has Matplotlib3.9.4. Do not add plotting dependencies to the game just to draw this figure.

Before heldout execution, review the fixed policy/evaluator, register the unchanged design/source with `register --out NEW_REGISTRATION.json`, and use `run --registration NEW_REGISTRATION.json --out NEW_HELDOUT`. The runner refuses changed source or an existing destination. The prospective shifted conditions remain within the same six authored families; they are not new-task, language-understanding, live-model or human-play validation.
