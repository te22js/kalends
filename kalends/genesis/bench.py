"""Prospective paired-world experiments. No categorical reward or optimal regret.

Run development seeds first, freeze source, then run the untouched held-out set.
The independent inference unit is the seed, averaged across balanced cells.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import statistics
import subprocess
import time

from .config import GenesisConfig
from .simulation import GenesisSimulation

ROOT = Path(__file__).resolve().parents[2]
PREREG = ROOT / "results/genesis/preregistration.json"


def design(registration, phase):
    seeds = registration[phase + "_seeds"]
    if phase == "development":
        seeds = seeds[:2]
    primary = registration["primary_design"]
    jobs = []
    for seed in seeds:
        for family in primary["families"]:
            for population in primary["populations"]:
                for policy in primary["policies"]:
                    config = GenesisConfig(seed=seed, n_ticks=registration["horizon"], n_agents=population,
                        family=family, memory=policy["memory"], gate=policy["gate"],
                        capacity=primary["capacity"], threshold=primary["threshold"],
                        supply_mode=primary["supply_mode"], allocation=primary["allocation"], role_policy=True)
                    jobs.append({"track": "primary", "condition": policy["label"], "config": asdict(config)})
        # One-factor capacity and role ablations, plus the complete 2x2 resource/order control.
        controls = [("capacity8", {"capacity": 8}), ("capacity128", {"capacity": 128}),
                    ("shared_policy", {"role_policy": False}),
                    ("fixed_stock_fixed_order", {"supply_mode": "fixed", "allocation": "fixed"}),
                    ("fixed_stock_seeded_order", {"supply_mode": "fixed", "allocation": "seeded"}),
                    ("per_capita_fixed_order", {"supply_mode": "per_capita", "allocation": "fixed"})]
        for label, changes in controls:
            config = GenesisConfig(**dict(asdict(GenesisConfig(seed=seed, n_agents=32)), **changes))
            jobs.append({"track": "control", "condition": label, "config": asdict(config)})
    return jobs


def run_world(specification):
    started = time.perf_counter()
    sim = GenesisSimulation(GenesisConfig(**specification["config"])).run()
    metrics = sim.metrics()
    decisions = sim.decisions
    nonabstained = [d for d in decisions if d.get("predicted_value") != "unknown"]
    def ratio(field, rows):
        return sum(bool(d.get(field)) for d in rows) / len(rows) if rows else None
    selected = {key: value for key, value in metrics.items() if key not in ("agents", "player")}
    selected.update({"zero_fill_orders": sum(a["zero_fill_orders"] for a in metrics["agents"]),
        "missed_contracts": sum(a["missed_contracts"] for a in metrics["agents"]),
        "missed_units": sum(a["missed_units"] for a in metrics["agents"]),
        "terminal_inventory_delta": sum(a["inventory_delta"] for a in metrics["agents"]),
        "local_recall_accuracy": ratio("local_recall_correct", decisions),
        "belief_current_accuracy": ratio("belief_current_correct", decisions),
        "belief_accuracy_when_answered": ratio("belief_current_correct", nonabstained),
        "answer_coverage": len(nonabstained) / len(decisions) if decisions else None,
        "boundary_violations": sum(bool(d.get("boundary_violation")) for d in decisions),
        "inspections": sum(e.payload.get("category") == "inspection_booked" for e in sim.ledger.events),
        "events": len(sim.ledger), "messages": sum(e.etype == "tell" for e in sim.ledger.events),
        "changed_relationships": sum(v != .6 for v in sim.state.trust.values()),
        "closed_commercial_relationships": sum(v < .35 for v in sim.state.trust.values()),
        "asset_value_1": sim.metrics(1)["net_asset_change"],
        "asset_value_6": sim.metrics(6)["net_asset_change"]})
    return {**specification, "metrics": selected, "agents": metrics["agents"],
            "ledger_sha256": sim.ledger.content_hash(), "elapsed_seconds": round(time.perf_counter() - started, 6),
            "actual_inference_cost_usd": 0,
            "decision_counts": {action: sum(d["action"] == action for d in decisions)
                                for action in ("reserve", "verify", "defer")}}


def bootstrap_interval(values, iterations=10000, seed=72831):
    if not values:
        return None
    rng = random.Random(seed)
    estimates = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(iterations))
    return {"mean": statistics.fmean(values), "ci95": [estimates[249], estimates[9749]],
            "n_independent_seeds": len(values), "resampling": "paired seed-cluster percentile bootstrap"}


def summarize(rows, registration):
    primary = [r for r in rows if r["track"] == "primary"]
    keys = ("delivery_fill_rate", "net_asset_change", "inspection_cost", "local_recall_accuracy",
            "belief_current_accuracy", "belief_accuracy_when_answered", "answer_coverage",
            "purchase_fill_rate", "zero_fill_orders", "asset_value_1", "asset_value_6")
    conditions = {}
    for label in sorted({r["condition"] for r in rows}):
        selected = [r for r in rows if r["condition"] == label]
        seeds = sorted({r["config"]["seed"] for r in selected})
        conditions[label] = {key: bootstrap_interval([
            statistics.fmean(r["metrics"][key] for r in selected
                             if r["config"]["seed"] == seed and r["metrics"][key] is not None)
            for seed in seeds]) for key in keys if all(r["metrics"][key] is not None for r in selected)}
    # Pair within seed, family and population before averaging each independent seed.
    seed_contrasts = []
    for seed in sorted({r["config"]["seed"] for r in primary}):
        differences = []
        for family in registration["primary_design"]["families"]:
            for population in registration["primary_design"]["populations"]:
                cell = {r["condition"]: r for r in primary if r["config"]["seed"] == seed and
                        r["config"]["family"] == family and r["config"]["n_agents"] == population}
                differences.append(cell["guarded_lineage"]["metrics"]["delivery_fill_rate"] -
                                   cell["guarded_none"]["metrics"]["delivery_fill_rate"])
        seed_contrasts.append({"seed": seed, "difference": statistics.fmean(differences)})
    contrast = bootstrap_interval([r["difference"] for r in seed_contrasts])
    cells = []
    for family in registration["primary_design"]["families"]:
        for population in registration["primary_design"]["populations"]:
            for label in sorted({r["condition"] for r in primary}):
                selected = [r for r in primary if r["config"]["family"] == family and
                            r["config"]["n_agents"] == population and r["condition"] == label]
                cells.append({"family": family, "population": population, "condition": label,
                    **{key: statistics.fmean(r["metrics"][key] for r in selected)
                       for key in keys if all(r["metrics"][key] is not None for r in selected)}})
    return {"worlds": len(rows), "primary_worlds": len(primary), "conditions": conditions,
            "confirmatory_contrast": {"name": "guarded_lineage minus guarded_none delivery fill",
                                      **contrast, "seed_differences": seed_contrasts},
            "cells_descriptive": cells, "total_events": sum(r["metrics"]["events"] for r in rows),
            "total_decisions": sum(r["metrics"]["n_decisions"] for r in rows),
            "inference_cost_usd": 0, "sum_worker_seconds": sum(r["elapsed_seconds"] for r in rows),
            "interpretation": "Primary inference clusters by seed across six paired cells. Per-cell and control estimates are descriptive; no multiplicity-adjusted claim. Net assets are not collective welfare or optimal regret."}


def source_fingerprint():
    paths = sorted((ROOT / "kalends").rglob("*.py"))
    files = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest(), files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("development", "heldout"), default="development")
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    registration = json.loads(PREREG.read_text())
    output = args.output or ROOT / "results/genesis" / args.phase
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise SystemExit("Refusing to overwrite existing research artifacts: " + str(output))
    if not 1 <= args.jobs <= 8:
        raise SystemExit("jobs must be from 1 to 8")
    if args.phase == "heldout":
        status = subprocess.check_output(["git", "status", "--porcelain", "--", "kalends", "results/genesis/preregistration.json"], cwd=ROOT, text=True)
        if status.strip():
            raise SystemExit("Freeze and commit runtime and preregistration before heldout: " + status)
    source_hash, files = source_fingerprint()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    specifications = design(registration, args.phase)
    manifest = {"phase": args.phase, "source_commit": commit, "runtime_sha256": source_hash,
        "runtime_files": files, "preregistration_sha256": hashlib.sha256(PREREG.read_bytes()).hexdigest(),
        "preregistration": registration, "world_count": len(specifications), "jobs": args.jobs,
        "language_mode": "deterministic citizen rules; no model calls"}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    started, results = time.perf_counter(), []
    with (output / "worlds.jsonl").open("w") as raw, ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(run_world, specification) for specification in specifications]
        for future in as_completed(futures):
            result = future.result()
            raw.write(json.dumps(result, sort_keys=True, allow_nan=False) + "\n")
            raw.flush()
            results.append(result)
            if len(results) % 30 == 0:
                print("%s/%s worlds; %.1fs" % (len(results), len(specifications), time.perf_counter() - started), flush=True)
    results.sort(key=lambda r: (r["config"]["seed"], r["track"], r["condition"], r["config"]["family"], r["config"]["n_agents"]))
    summary = summarize(results, registration)
    summary["wall_seconds"] = time.perf_counter() - started
    summary["worlds_sha256"] = hashlib.sha256((output / "worlds.jsonl").read_bytes()).hexdigest()
    summary["source_unchanged_during_run"] = source_fingerprint()[0] == source_hash
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"worlds": len(results), "wall_seconds": summary["wall_seconds"],
                      "contrast": summary["confirmatory_contrast"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
