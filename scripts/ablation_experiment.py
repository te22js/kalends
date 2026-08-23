"""Ablation study: which components of hybrid memory earn their keep?

Variants of HybridMemory with one mechanism removed each, evaluated on three
core families. Writes results/ablations/ablations.csv + .json and prints the
component-removed table (brief §6).

Run:  python3 scripts/ablation_experiment.py [--seeds 10]
"""
import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalends.bench.harness import run_benchmark
from kalends.bench.questions import generate_questions
from kalends.memory.hybrid import HybridMemory
from kalends.memory.vector import VectorMemory
from kalends.scenarios.generator import WorldConfig, generate
from kalends.simulation import run_scenario

VARIANTS = {
    "full": lambda: HybridMemory(),
    "no_supersession": lambda: HybridMemory({"use_supersession": False}),
    "no_trust": lambda: HybridMemory({"use_trust": False}),
    "no_provenance": lambda: HybridMemory({"use_provenance": False}),
    "no_vector_fallback": lambda: HybridMemory(use_vector_fallback=False),
    "vector_only": lambda: VectorMemory(),
}

FAMILIES = {
    "propagation": WorldConfig(name="propagation"),
    "supersession": WorldConfig(name="supersession", changes_min=4,
                                changes_max=6, n_props=5, n_ticks=72),
    "conflict": WorldConfig(name="conflict", distorter_frac=0.5,
                            distrust_pair_frac=0.3),
}

DIMS = ["belief", "supersession", "contradiction", "boundary", "source",
        "provenance", "temporal", "corroboration", "alias"]


def score_variant(sim, factory) -> dict:
    questions = generate_questions(sim)
    memories = {}
    for agent_id in sim.scenario.agent_ids():
        mem = factory()
        for exp in sim.experiences[agent_id]:
            mem.ingest(exp)
        memories[agent_id] = mem
    total = correct = 0
    dim_tot: dict[str, int] = {}
    dim_cor: dict[str, int] = {}
    for q in questions:
        ans = memories[q.agent_id].answer(q.query)
        ok = (ans.value or "unknown").strip().lower() == q.expected.strip().lower()
        total += 1
        correct += ok
        for d in q.dims:
            dim_tot[d] = dim_tot.get(d, 0) + 1
            dim_cor[d] = dim_cor.get(d, 0) + ok
    out = {"overall": correct / total}
    for d in DIMS:
        if dim_tot.get(d):
            out[d] = dim_cor.get(d, 0) / dim_tot[d]
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--out", default="results/ablations")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    raw: dict = {}
    for fam, cfg in FAMILIES.items():
        for seed in range(args.seeds):
            sim = run_scenario(generate(cfg, seed), seed)
            for var, factory in VARIANTS.items():
                r = score_variant(sim, factory)
                for metric, val in r.items():
                    raw.setdefault((fam, var, metric), []).append(val)
        print(f"{fam}: {args.seeds} seeds done", flush=True)

    rows = []
    for (fam, var, metric), vals in sorted(raw.items()):
        rows.append({"family": fam, "variant": var, "metric": metric,
                     "mean": round(statistics.fmean(vals), 4),
                     "sd": round(statistics.stdev(vals)
                                 if len(vals) > 1 else 0.0, 4),
                     "n": len(vals)})
    with open(out_dir / "ablations.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(out_dir / "ablations.json", "w") as f:
        json.dump({"families": {k: v.to_json() for k, v in FAMILIES.items()},
                   "seeds": args.seeds, "rows": rows}, f, indent=2)

    # Print the component table averaged over families.
    print("\ncomponent-removed table (mean over families and seeds):")
    cols = ["overall", "supersession", "contradiction", "boundary",
            "source", "temporal", "corroboration"]
    print(f"{'variant':<20}" + "".join(f"{c:>14}" for c in cols))
    for var in VARIANTS:
        cells = []
        for c in cols:
            vals = [statistics.fmean(raw[(f, var, c)])
                    for f in FAMILIES if (f, var, c) in raw]
            cells.append(f"{statistics.fmean(vals):.3f}" if vals else "-")
        print(f"{var:<20}" + "".join(f"{c:>14}" for c in cells))
    print(f"\nwritten {out_dir}/ablations.csv, ablations.json")


if __name__ == "__main__":
    main()
