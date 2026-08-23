"""Multi-seed experiment runner.

A *suite* is a named set of scenario families (WorldConfigs). For each family
we run N seeds; each seed generates a fresh world, simulates it, and scores
every memory system on the oracle-generated questions. Aggregates report
mean / sd / median / 95% CI per (family, system, metric), plus paired
comparisons on the exact same seeds.

Everything written to the output directory:
  configs.json    - exact WorldConfig per family + seed list (reproducibility)
  raw.json        - per-seed metric values, nothing aggregated away
  summary.json    - aggregated stats + paired comparisons
  summary.csv     - flat rows for plotting/analysis
"""
from __future__ import annotations

import csv
import json
import os
import time

from ..memory import MEMORY_SYSTEMS
from ..scenarios.generator import WorldConfig, generate
from ..simulation import run_scenario
from .harness import run_benchmark
from .stats import paired, summarize

# Scenario families. Names describe the stress each family applies.
SUITES: dict[str, dict[str, WorldConfig]] = {
    "core": {
        # Baseline information-propagation world (the default config).
        "propagation": WorldConfig(name="propagation"),
        # Facts change many times; different agents see different subsets.
        "supersession": WorldConfig(name="supersession", changes_min=4,
                                    changes_max=6, n_props=5, n_ticks=72),
        # Most incidents are private; public decoys tempt leakage.
        "private": WorldConfig(name="private", private_event_p=0.6,
                               n_decoys=3),
        # Heavy irrelevant-memory load (retrieval degradation).
        "overload": WorldConfig(name="overload", irrelevant_memory_rate=0.6,
                                n_decoys=2),
        # Sparse communication -> long multi-hop provenance chains.
        "multihop": WorldConfig(name="multihop", chattiness_min=0.05,
                                chattiness_max=0.35, n_ticks=96),
        # Many distorters + widespread distrust -> conflicting testimony.
        "conflict": WorldConfig(name="conflict", distorter_frac=0.5,
                                distrust_pair_frac=0.3),
    },
    # Held-out configurations: same machinery, parameter regions never used
    # during development/tuning (see METHODOLOGY_AUDIT.md on leakage).
    "heldout": {
        "dense_small": WorldConfig(name="dense_small", n_agents=8,
                                   n_locations=3, n_ticks=36, n_props=6,
                                   changes_min=2, changes_max=4,
                                   chattiness_min=0.4, chattiness_max=0.9),
        "sprawl": WorldConfig(name="sprawl", n_agents=24, n_locations=12,
                              n_ticks=96, n_props=8, private_event_p=0.3,
                              irrelevant_memory_rate=0.3),
        "hostile": WorldConfig(name="hostile", distorter_frac=0.7,
                               distrust_pair_frac=0.5, private_event_p=0.4,
                               changes_min=3, changes_max=5),
    },
}

# Metrics collected per run. Dimension accuracies are added dynamically.
TOP_METRICS = ["overall", "boundary_violation_rate",
               "epistemic_precision", "epistemic_recall"]

# Paired comparisons of interest (x vs y; positive diff favors x).
PAIRINGS = [
    ("hybrid", "vector_meta"),      # does the symbolic layer earn its keep?
    ("hybrid", "recency"),          # does anything beat the trivial floor?
    ("structured", "text_structured"),  # size of the by-construction advantage
    ("vector_recency", "vector"),   # value of a time model alone
    ("vector_meta", "vector"),      # value of metadata filtering alone
]


def run_suite(suite: str, seeds: int, out_dir: str,
              systems: list[str] | None = None,
              progress: bool = True) -> dict:
    families = SUITES[suite]
    systems = systems or list(MEMORY_SYSTEMS)
    os.makedirs(out_dir, exist_ok=True)
    seed_list = list(range(seeds))

    raw: dict = {fam: {sys_name: {} for sys_name in systems}
                 for fam in families}
    t0 = time.time()
    for fam, config in families.items():
        for seed in seed_list:
            sim = run_scenario(generate(config, seed), seed)
            results = run_benchmark(sim, systems)
            for sys_name in systems:
                r = results["systems"][sys_name]
                metrics = {
                    "overall": r["accuracy"],
                    "boundary_violation_rate": r["boundary_violation_rate"],
                    "epistemic_precision": r["epistemic_precision"],
                    "epistemic_recall": r["epistemic_recall"],
                }
                for dim, dd in r["by_dimension"].items():
                    metrics[f"dim_{dim}"] = dd["accuracy"]
                for m, v in metrics.items():
                    raw[fam][sys_name].setdefault(m, []).append(v)
        if progress:
            print(f"  [{suite}] {fam}: {seeds} seeds done "
                  f"({time.time() - t0:.0f}s elapsed)", flush=True)

    # -- aggregate ---------------------------------------------------------
    summary: dict = {"suite": suite, "seeds": seed_list, "systems": systems,
                     "families": {}}
    for fam in families:
        fam_summary = {"config": families[fam].to_json(), "systems": {},
                       "paired": {}}
        for sys_name in systems:
            fam_summary["systems"][sys_name] = {
                m: summarize(vals) for m, vals in raw[fam][sys_name].items()}
        for x, y in PAIRINGS:
            if x in systems and y in systems:
                fam_summary["paired"][f"{x}_vs_{y}"] = paired(
                    raw[fam][x]["overall"], raw[fam][y]["overall"])
        summary["families"][fam] = fam_summary

    # -- write everything --------------------------------------------------
    with open(os.path.join(out_dir, "configs.json"), "w") as f:
        json.dump({fam: cfg.to_json() for fam, cfg in families.items()},
                  f, indent=2)
    with open(os.path.join(out_dir, "raw.json"), "w") as f:
        json.dump(raw, f)
    with open(os.path.join(out_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    with open(os.path.join(out_dir, "summary.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["family", "system", "metric", "mean", "sd", "median",
                    "ci95_lo", "ci95_hi", "n"])
        for fam in families:
            for sys_name in systems:
                for m, s in summary["families"][fam]["systems"][sys_name].items():
                    if s.get("n"):
                        w.writerow([fam, sys_name, m, s["mean"], s["sd"],
                                    s["median"], s["ci95"][0], s["ci95"][1],
                                    s["n"]])
    return summary


def format_suite_summary(summary: dict) -> str:
    """Compact text report: overall mean±sd per family/system + pairings."""
    lines = []
    systems = summary["systems"]
    for fam, fs in summary["families"].items():
        lines.append(f"\n== {fam} (n={len(summary['seeds'])} seeds) ==")
        width = max(len(s) for s in systems) + 2
        for sys_name in systems:
            s = fs["systems"][sys_name]["overall"]
            b = fs["systems"][sys_name]["boundary_violation_rate"]
            lines.append(f"  {sys_name:<{width}} overall {s['mean']:.3f} "
                         f"±{s['sd']:.3f}  CI[{s['ci95'][0]:.3f},"
                         f"{s['ci95'][1]:.3f}]  bviol {b['mean']:.3f}")
        for pair_name, p in fs["paired"].items():
            lines.append(f"    Δ {pair_name}: {p['mean_diff']:+.3f} "
                         f"CI[{p['ci95'][0]:+.3f},{p['ci95'][1]:+.3f}] "
                         f"d_z={p['cohen_dz']}")
    return "\n".join(lines)
