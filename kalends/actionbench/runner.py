"""Paired, world-clustered ActionBench experiments; no paid services.

Frozen before held-out runs: seeds 0..9 development, 1000..1029 held-out;
families rumour/shortage/recovery/private. No threshold selection on held-out.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import platform
import statistics
import sys
import time
import tracemalloc
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from ..bench.stats import paired, summarize
from .policy import AlwaysDeferPolicy, AlwaysVerifyPolicy

CONDITIONS = {
    "structured": ("structured", "none", 2),
    "bm25": ("bm25", "none", 2),
    "hybrid": ("hybrid", "none", 2),
    "hybrid_guarded": ("hybrid_guarded", "none", 2),
    "guarded_lineage1": ("hybrid_guarded", "lineage", 1),
    "guarded_lineage2": ("hybrid_guarded", "lineage", 2),
    "guarded_lineage3": ("hybrid_guarded", "lineage", 3),
    "guarded_sources2": ("hybrid_guarded", "source_count", 2),
    "bm25_lineage2": ("bm25", "lineage", 2),
    "always_defer": ("structured", "none", 2),
    "always_verify": ("structured", "none", 2),
}
FAMILIES = ("rumour", "shortage", "recovery", "private")
METRICS = ("action_error_rate", "autonomy", "decision_regret", "false_abstention_rate",
           "belief_error_rate", "qa_accuracy", "boundary_violation_rate",
           "source_independence_failure_rate", "verification_rate", "selective_risk",
           "correction_latency", "correction_unrecovered_rate", "seconds", "events_per_second")


def decision_metrics(sim):
    ds = sim.decisions
    n = len(ds)
    ratio = lambda numerator, denominator: numerator / denominator if denominator else 0.0
    reserves = [d for d in ds if d["action"] == "reserve"]
    valid = [d for d in ds if d.get("actual_value") == "disrupted"]
    # Verification is neither a task violation nor free: its 1.5 cost appears
    # in regret, and failure to take a currently useful reserve in abstention.
    bad = lambda d: ((d["action"] == "reserve" and d.get("actual_value") != "disrupted") or
                     (d["action"] == "defer" and d.get("actual_value") == "disrupted"))
    qas = [d for d in ds if "qa_correct" in d]
    # Correction recovery is measured from a valid local direct observation to
    # the next same-agent decision with that value, censored at world end.
    lags, unrecovered, corrections = [], 0, 0
    for agent, exps in sim.experiences.items():
        relevant = sorted([e for e in exps if e.subject == "grain" and e.predicate == "supply"],
                          key=lambda e: (e.tick, e.event_id))
        for i, e in enumerate(relevant):
            if e.kind != "observed" or not e.accepted:
                continue
            prior = [x for x in relevant[:i] if x.accepted]
            previous = max(prior, key=lambda x: (x.as_of, x.tick, x.event_id)) if prior else None
            # Rechecking an already corrected belief is not another correction.
            if previous is None or previous.value == e.value:
                continue
            corrections += 1
            start = (e.tick, e.event_id)
            end = min([(x.tick, x.event_id) for x in relevant[i + 1:]
                       if x.kind == "observed" and x.accepted and x.value != e.value]
                      or [(sim.config.n_ticks, -1)])
            candidates = [d for d in ds if d["agent"] == agent and
                          start < (d["tick"], d.get("event_id", -1)) < end and
                          d.get("predicted_value") == e.value]
            if candidates:
                lags.append(min(d["tick"] for d in candidates) - e.tick)
            else:
                unrecovered += 1
    return {
        "n_decisions": n, "n_reserves": len(reserves), "n_useful_opportunities": len(valid),
        "action_error_rate": ratio(sum(bad(d) for d in ds), n),
        "autonomy": ratio(len(reserves), n),
        "decision_regret": statistics.fmean(d.get("regret", d.get("loss", 0)) for d in ds) if ds else 0,
        "false_abstention_rate": ratio(sum(d["action"] != "reserve" for d in valid), len(valid)),
        "belief_error_rate": ratio(sum(d.get("predicted_value") != d.get("actual_value") for d in ds), n),
        "qa_accuracy": ratio(sum(d["qa_correct"] for d in qas), len(qas)),
        "qa_n": len(qas),
        "boundary_violation_rate": ratio(sum(bool(d.get("boundary_violation")) for d in ds), n),
        "source_independence_failure_rate": ratio(sum(bool(d.get("source_independence_failure")) for d in ds), n),
        "verification_rate": ratio(sum(d["action"] == "verify" for d in ds), n),
        "selective_risk": ratio(sum(bad(d) for d in reserves), len(reserves)),
        "correction_latency": statistics.fmean(lags) if lags else 0.0,
        "correction_n": corrections, "correction_recovered_n": len(lags),
        "correction_unrecovered_rate": ratio(unrecovered, corrections),
    }


def run_world(seed, family, population, condition, capacity=64, depth=3, n_ticks=24,
              measure_memory=False):
    from ..city import CityConfig, CitySimulation
    memory, gate, threshold = CONDITIONS[condition]
    config = CityConfig(seed=seed, family=family, n_agents=population, n_ticks=n_ticks,
                        memory=memory, gate=gate, threshold=threshold, capacity=capacity,
                        communication_depth=depth)
    factory = None
    if condition == "always_defer":
        factory = lambda agent, cfg: AlwaysDeferPolicy()
    elif condition == "always_verify":
        factory = lambda agent, cfg: AlwaysVerifyPolicy()
    if measure_memory:
        tracemalloc.start()
    start = time.perf_counter()
    sim = CitySimulation(config, policy_factory=factory).run()
    seconds = time.perf_counter() - start
    peak = tracemalloc.get_traced_memory()[1] if measure_memory else None
    if measure_memory:
        tracemalloc.stop()
    metrics = decision_metrics(sim)
    metrics.update(seconds=seconds, events_per_second=len(sim.ledger) / max(seconds, 1e-12))
    semantic = {"config": asdict(config), "condition": condition,
                "ledger_hash": sim.ledger.content_hash(), "decisions": sim.decisions}
    digest = hashlib.sha256(json.dumps(semantic, sort_keys=True).encode()).hexdigest()
    return {"seed": seed, "family": family, "population": population, "condition": condition,
            "capacity": capacity, "communication_depth": depth, "config": asdict(config),
            "n_events": len(sim.ledger), "semantic_hash": digest,
            "ledger_hash": sim.ledger.content_hash(), "metrics": metrics,
            "peak_traced_bytes": peak, "decisions": sim.decisions}


def aggregate(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["population"], row["condition"])].append(row)
    systems = {}
    for (pop, condition), group in sorted(grouped.items()):
        # Seed is the independent unit. Average scenario-family worlds first;
        # do not count per-agent decisions or four families as independent n.
        by_seed = defaultdict(list)
        for row in group:
            by_seed[row["seed"]].append(row)
        systems[f"{pop}/{condition}"] = {
            "population": pop, "condition": condition, "n_worlds": len(group),
            "n_seeds": len(by_seed), "n_decisions": sum(r["metrics"]["n_decisions"] for r in group),
            "metrics": {metric: summarize([
                statistics.fmean(r["metrics"][metric] for r in rs
                                 if metric != "correction_latency" or r["metrics"]["correction_recovered_n"])
                for _, rs in sorted(by_seed.items())
                if metric != "correction_latency" or any(r["metrics"]["correction_recovered_n"] for r in rs)])
                for metric in METRICS},
        }
    comparisons = {}
    pairs = [("hybrid", "hybrid_guarded"), ("guarded_sources2", "guarded_lineage2"),
             ("hybrid_guarded", "guarded_lineage2"), ("bm25", "bm25_lineage2"),
             ("always_defer", "guarded_lineage2"), ("always_verify", "guarded_lineage2")]
    for pop in sorted({r["population"] for r in rows}):
        for a, b in pairs:
            if (pop, a) not in grouped or (pop, b) not in grouped:
                continue
            left = {(r["seed"], r["family"]): r for r in grouped[(pop, a)]}
            right = {(r["seed"], r["family"]): r for r in grouped[(pop, b)]}
            common = sorted(set(left) & set(right))
            if not common:
                continue
            by_seed = defaultdict(list)
            for key in common:
                by_seed[key[0]].append(key)
            comparisons[f"{pop}/{a}-minus-{b}"] = {
                metric: paired(
                    [statistics.fmean(left[k]["metrics"][metric] for k in keys)
                     for _, keys in sorted(by_seed.items())],
                    [statistics.fmean(right[k]["metrics"][metric] for k in keys)
                     for _, keys in sorted(by_seed.items())])
                for metric in ("decision_regret", "action_error_rate", "autonomy", "qa_accuracy")}
    return {"systems": systems, "paired_comparisons": comparisons,
            "ci_method": "95% t interval across paired seed means; scenario families averaged within seed",
            "independent_unit": "seed, not decision, agent, or family",
            "risk_definition": "incorrect reserves / all reserves (zero if no reserves; inspect coverage)",
            "regret_definition": "reserve while available=2, defer while disrupted=6, verify=1.5; otherwise 0",
            "correction_definition": "local direct contradictory observation to next agreeing decision; non-recovery reported separately"}


def run_suite(out, split="development", seeds=None, populations=(8,), families=FAMILIES,
              conditions=None, capacity=64, depth=3, n_ticks=24):
    from ..city import CityConfig

    if split not in ("development", "heldout"):
        raise ValueError("split must be development or heldout")
    try:
        conditions = list(CONDITIONS) if conditions is None else list(conditions)
        seeds = list(seeds if seeds is not None else (
            range(10) if split == "development" else range(1000, 1030)))
        populations, families = list(populations), list(families)
    except TypeError as error:
        raise ValueError("experiment axes must be nonempty iterables") from error
    axes = {"seeds": seeds, "populations": populations,
            "families": families, "conditions": conditions}
    for name, values in axes.items():
        if not values:
            raise ValueError(f"{name} cannot be empty")
        try:
            unique = len(set(values)) == len(values)
        except TypeError as error:
            raise ValueError(f"{name} must contain scalar values") from error
        if not unique:
            raise ValueError(f"{name} cannot contain duplicate values")
    if any(type(seed) is not int for seed in seeds):
        raise ValueError("seeds must be integers")
    if any(family not in FAMILIES for family in families):
        raise ValueError("unknown experiment family")
    if any(condition not in CONDITIONS for condition in conditions):
        raise ValueError("unknown experiment condition")
    # Validate every changing configuration axis before creating any artifact.
    memory, gate, threshold = CONDITIONS[conditions[0]]
    for population in populations:
        CityConfig(seed=seeds[0], family=families[0], n_agents=population,
                   n_ticks=n_ticks, memory=memory, gate=gate, threshold=threshold,
                   capacity=capacity, communication_depth=depth)
    out = Path(out)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError("refusing to overwrite an experiment; choose a fresh --out directory")
    out.mkdir(parents=True, exist_ok=True)
    source_root = Path(__file__).resolve().parent.parent
    source_files = sorted(p for p in source_root.rglob("*.py") if "__pycache__" not in str(p))
    source_hashes = {str(p.relative_to(source_root)): hashlib.sha256(p.read_bytes()).hexdigest()
                     for p in source_files}
    config = {"split": split, "seeds": seeds, "populations": list(populations), "families": list(families),
              "conditions": {k: CONDITIONS[k] for k in conditions}, "capacity": capacity,
              "communication_depth": depth, "n_ticks": n_ticks,
              "query": {"subject": "grain", "predicate": "supply", "top_k": 4},
              "capacity_semantics": "FIFO experiences per agent, including episodic records; 0 means unlimited",
              "fairness": "same local input schema and cap, original architecture lookup rules; structured exact-key versus retrieval top-4 is disclosed",
              "source_hashes": source_hashes,
              "eligibility": "scheduled decisions only when own inventory is below next delivery need; policy can change future opportunity count",
              "environment": {"python": sys.version, "platform": platform.platform(), "processor": platform.processor()},
              "freeze": "development0:9; heldout1000:1029; thresholds1,2,3 predeclared; no heldout selection"}
    with (out / "config.json").open("x") as stream:
        stream.write(json.dumps(config, indent=2) + "\n")
    rows = []
    total = len(seeds) * len(families) * len(populations) * len(conditions)
    start = time.perf_counter()
    with (out / "raw.jsonl.gz").open("xb") as raw:
        with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
            for seed in seeds:
                for family in families:
                    for population in populations:
                        for condition in conditions:
                            row = run_world(seed, family, population, condition, capacity, depth, n_ticks)
                            compressed.write((json.dumps(row, separators=(",", ":")) + "\n").encode())
                            rows.append({k: v for k, v in row.items() if k != "decisions"})
                print(f"seed={seed}: {len(rows)}/{total} worlds; {time.perf_counter()-start:.1f}s", flush=True)
    summary = aggregate(rows)
    summary.update(config=config, elapsed_seconds=time.perf_counter()-start,
                   n_worlds=len(rows), n_decisions=sum(r["metrics"]["n_decisions"] for r in rows))
    with (out / "summary.json").open("x") as stream:
        stream.write(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    with (out / "worlds.csv").open("x", newline="") as stream:
        fields = ["seed", "family", "population", "condition", "capacity", "communication_depth", "n_events", "semantic_hash"] + list(rows[0]["metrics"])
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(dict({k: r[k] for k in fields if k in r}, **r["metrics"]))
    print(f"Saved {len(rows)} worlds, {summary['n_decisions']} decisions to {out}", flush=True)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kalends ActionBench paired-world experiments")
    parser.add_argument("--out", required=True)
    parser.add_argument("--split", choices=("development", "heldout"), default="development")
    parser.add_argument("--seeds", type=int, help="count from split starting seed")
    parser.add_argument("--populations", default="8")
    parser.add_argument("--families", default=",".join(FAMILIES))
    parser.add_argument("--conditions", default=",".join(CONDITIONS))
    parser.add_argument("--capacity", type=int, default=64)
    parser.add_argument("--depth", type=int, default=3)
    parser.add_argument("--ticks", type=int, default=24)
    args = parser.parse_args(argv)
    first = 0 if args.split == "development" else 1000
    seeds = range(first, first+args.seeds) if args.seeds is not None else None
    if args.seeds is not None and args.seeds <= 0:
        parser.error("--seeds must be positive")
    run_suite(args.out, args.split, seeds, tuple(map(int, args.populations.split(","))),
              tuple(args.families.split(",")), args.conditions.split(","), args.capacity, args.depth, args.ticks)


if __name__ == "__main__":
    main()
