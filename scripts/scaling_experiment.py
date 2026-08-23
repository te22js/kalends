"""Scaling experiment: does the architecture survive larger worlds?

Sweeps world size (agents, with locations/props/ticks scaled alongside),
measures simulation runtime, benchmark runtime per system, per-agent memory
load, and accuracy. Writes results/scaling/scaling.csv + scaling.json.

Run:  python3 scripts/scaling_experiment.py [--seeds 3] [--max 128]
"""
import argparse
import csv
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalends.bench.harness import run_benchmark
from kalends.scenarios.generator import WorldConfig, generate
from kalends.simulation import run_scenario

SYSTEMS = ["recency", "vector", "vector_meta", "text_structured",
           "structured", "hybrid"]

SCALE_POINTS = [8, 16, 32, 64, 128]


def config_for(n_agents: int) -> WorldConfig:
    """Scale the world with the population; keep density roughly constant."""
    return WorldConfig(
        name=f"scale_{n_agents}",
        n_agents=n_agents,
        n_locations=max(3, n_agents // 3),
        n_ticks=48,
        n_props=max(4, n_agents // 3),
        n_decoys=max(1, n_agents // 16),
        changes_min=2, changes_max=4,
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--max", type=int, default=128)
    ap.add_argument("--out", default="results/scaling")
    args = ap.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    detail = {}
    for n_agents in [p for p in SCALE_POINTS if p <= args.max]:
        cfg = config_for(n_agents)
        per_seed = {s: {"overall": [], "bviol": [], "bench_s": []}
                    for s in SYSTEMS}
        sim_times, n_events, n_exp, n_q = [], [], [], []
        for seed in range(args.seeds):
            t0 = time.time()
            sim = run_scenario(generate(cfg, seed), seed)
            sim_times.append(time.time() - t0)
            n_events.append(len(sim.ledger))
            n_exp.append(statistics.fmean(
                len(v) for v in sim.experiences.values()))
            for name in SYSTEMS:
                t0 = time.time()
                res = run_benchmark(sim, [name])
                per_seed[name]["bench_s"].append(time.time() - t0)
                per_seed[name]["overall"].append(
                    res["systems"][name]["accuracy"])
                per_seed[name]["bviol"].append(
                    res["systems"][name]["boundary_violation_rate"])
                n_questions = res["n_questions"]
            n_q.append(n_questions)
        detail[n_agents] = {
            "config": cfg.to_json(),
            "sim_seconds": statistics.fmean(sim_times),
            "events": statistics.fmean(n_events),
            "experiences_per_agent": statistics.fmean(n_exp),
            "questions": statistics.fmean(n_q),
        }
        for name in SYSTEMS:
            rows.append({
                "n_agents": n_agents, "system": name,
                "overall_mean": round(statistics.fmean(per_seed[name]["overall"]), 4),
                "overall_sd": round(statistics.stdev(per_seed[name]["overall"])
                                    if args.seeds > 1 else 0.0, 4),
                "bviol_mean": round(statistics.fmean(per_seed[name]["bviol"]), 4),
                "bench_seconds": round(statistics.fmean(per_seed[name]["bench_s"]), 3),
                "sim_seconds": round(statistics.fmean(sim_times), 3),
                "experiences_per_agent": round(statistics.fmean(n_exp), 1),
                "questions": round(statistics.fmean(n_q), 1),
            })
        print(f"n_agents={n_agents}: sim {statistics.fmean(sim_times):.2f}s, "
              f"{statistics.fmean(n_exp):.0f} exp/agent, "
              f"{statistics.fmean(n_q):.0f} questions", flush=True)

    with open(out_dir / "scaling.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(out_dir / "scaling.json", "w") as f:
        json.dump({"seeds": args.seeds, "detail": detail, "rows": rows}, f,
                  indent=2)
    print(f"written {out_dir}/scaling.csv, scaling.json")


if __name__ == "__main__":
    main()
