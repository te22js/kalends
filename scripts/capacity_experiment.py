"""Capacity-pressure experiment: bounded memory budgets under overload.

Runs the overload world (heavy irrelevant-memory rate, long duration) with
each system wrapped at several record caps under fifo vs importance eviction.
Writes results/capacity/capacity.csv + capacity.json.

Run:  python3 scripts/capacity_experiment.py [--seeds 10]
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
from kalends.memory import MEMORY_SYSTEMS
from kalends.memory.capacity import CappedMemory
from kalends.scenarios.generator import WorldConfig, generate
from kalends.simulation import run_scenario

BASE_SYSTEMS = ["vector", "vector_meta", "structured", "hybrid"]
CAPS = [25, 50, 100, 200, None]
POLICIES = ["fifo", "importance"]

OVERLOAD = WorldConfig(name="capacity_overload", n_ticks=96,
                       irrelevant_memory_rate=0.8, n_props=5, n_decoys=2,
                       changes_min=3, changes_max=5)


def run_capped(sim, base_name: str, cap, policy: str) -> dict:
    """Same scoring as the harness, but with capped per-agent memories."""
    factory = MEMORY_SYSTEMS[base_name]
    questions = generate_questions(sim)
    memories = {}
    for agent_id in sim.scenario.agent_ids():
        mem = (factory() if cap is None
               else CappedMemory(factory, cap, policy))
        for exp in sim.experiences[agent_id]:
            mem.ingest(exp)
        memories[agent_id] = mem
    n_correct = bviol = btot = 0
    for q in questions:
        ans = memories[q.agent_id].answer(q.query)
        got = (ans.value or "unknown").strip().lower()
        n_correct += got == q.expected.strip().lower()
        if "boundary" in q.dims:
            btot += 1
            bviol += got not in ("unknown", "no")
    return {"overall": n_correct / len(questions),
            "bviol": bviol / btot if btot else 0.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=10)
    ap.add_argument("--out", default="results/capacity")
    args = ap.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for seed in range(args.seeds):
        sim = run_scenario(generate(OVERLOAD, seed), seed)
        for name in BASE_SYSTEMS:
            for cap in CAPS:
                for policy in (POLICIES if cap is not None else ["-"]):
                    r = run_capped(sim, name, cap, policy)
                    rows.append({"seed": seed, "system": name,
                                 "cap": cap or "unlimited", "policy": policy,
                                 **{k: round(v, 4) for k, v in r.items()}})
        print(f"seed {seed} done", flush=True)

    # aggregate
    agg = {}
    for row in rows:
        key = (row["system"], row["cap"], row["policy"])
        agg.setdefault(key, {"overall": [], "bviol": []})
        agg[key]["overall"].append(row["overall"])
        agg[key]["bviol"].append(row["bviol"])
    summary = [{"system": k[0], "cap": k[1], "policy": k[2],
                "overall_mean": round(statistics.fmean(v["overall"]), 4),
                "overall_sd": round(statistics.stdev(v["overall"])
                                    if len(v["overall"]) > 1 else 0.0, 4),
                "bviol_mean": round(statistics.fmean(v["bviol"]), 4),
                "n": len(v["overall"])}
               for k, v in sorted(agg.items(), key=lambda kv: (kv[0][0],
                                  str(kv[0][1]), kv[0][2]))]
    with open(out_dir / "capacity.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0]))
        w.writeheader()
        w.writerows(summary)
    with open(out_dir / "capacity.json", "w") as f:
        json.dump({"config": OVERLOAD.to_json(), "seeds": args.seeds,
                   "raw": rows, "summary": summary}, f, indent=2)
    for s in summary:
        print(s)
    print(f"written {out_dir}/capacity.csv, capacity.json")


if __name__ == "__main__":
    main()
