"""Aggregate categorized failures over several generated worlds.

Writes results/failures/failures.json (full detail) and prints the
category x system count matrix used in FAILURE_ANALYSIS.md.

Run:  python3 scripts/failure_analysis.py [--seeds 10]
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalends.bench.failures import collect_failures
from kalends.scenarios.generator import WorldConfig, generate
from kalends.simulation import run_scenario

FAMILIES = {
    "propagation": WorldConfig(name="propagation"),
    "supersession": WorldConfig(name="supersession", changes_min=4,
                                changes_max=6, n_props=5, n_ticks=72),
    "private": WorldConfig(name="private", private_event_p=0.6, n_decoys=3),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--out", default="results/failures")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    totals: dict[str, Counter] = {}
    n_questions: Counter = Counter()
    kept_examples: dict[str, dict[str, list]] = {}
    for fam, cfg in FAMILIES.items():
        for seed in range(args.seeds):
            sim = run_scenario(generate(cfg, seed), seed)
            report = collect_failures(sim)
            for sys_name, r in report["systems"].items():
                totals.setdefault(sys_name, Counter()).update(r["categories"])
                n_questions[sys_name] += r["n_questions"]
                for cat, exs in r["examples"].items():
                    slot = kept_examples.setdefault(sys_name, {}).setdefault(cat, [])
                    for ex in exs:
                        if len(slot) < 3:
                            slot.append({"family": fam, "seed": seed, **ex})
        print(f"{fam}: done", flush=True)

    cats = sorted({c for t in totals.values() for c in t})
    print(f"\nfailure counts per 1000 questions "
          f"({args.seeds} seeds x {len(FAMILIES)} families):")
    print(f"{'system':<18}" + "".join(f"{c[:14]:>16}" for c in cats))
    matrix = {}
    for sys_name, t in totals.items():
        rates = {c: round(1000 * t.get(c, 0) / n_questions[sys_name], 1)
                 for c in cats}
        matrix[sys_name] = rates
        print(f"{sys_name:<18}" + "".join(f"{rates[c]:>16}" for c in cats))

    with open(out_dir / "failures.json", "w") as f:
        json.dump({"seeds": args.seeds,
                   "families": {k: v.to_json() for k, v in FAMILIES.items()},
                   "rates_per_1000": matrix,
                   "examples": kept_examples}, f, indent=2)
    print(f"\nwritten {out_dir}/failures.json")


if __name__ == "__main__":
    main()
