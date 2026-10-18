#!/usr/bin/env python3
"""Isolated local resource measurements for the fixed Fork City configuration.

Run after experiments finish, for example:
    python3 scripts/profile_fork_city.py --out results/fork_city/profile.json

Each population gets a fresh subprocess. Five untraced runs measure runtime;
then a separate traced run measures Python allocations. RSS is sampled before
tracing and includes imports and the worker's five untraced runs. None of these
resource measurements changes or selects the study's policies or thresholds.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import math
import platform
import statistics
import subprocess
import sys
import time
import tracemalloc
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REPEATS = 5
POPULATIONS = (8, 32, 128)


def _signature(sim):
    ledger_hash = sim.ledger.content_hash()
    semantic = {"config": asdict(sim.config), "ledger_hash": ledger_hash,
                "decisions": sim.decisions}
    return {"ledger_hash": ledger_hash,
            "semantic_hash": hashlib.sha256(json.dumps(semantic, sort_keys=True).encode()).hexdigest(),
            "events": len(sim.ledger), "decisions": len(sim.decisions)}


def _max_rss():
    try:
        import resource
    except ImportError:
        return {"max_rss_bytes": None, "max_rss_kib": None,
                "rss_availability": "resource.getrusage unavailable on this platform"}
    raw = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # Darwin exposes bytes; Linux and other supported Unix workers expose KiB.
    byte_count = int(raw if sys.platform == "darwin" else raw * 1024)
    return {"max_rss_bytes": byte_count, "max_rss_kib": byte_count / 1024,
            "rss_availability": "process high-water mark before allocation tracing"}


def profile_population(population):
    from kalends.city import CityConfig, CitySimulation

    config = CityConfig(seed=42, family="rumour", memory="hybrid_guarded",
                        capacity=64, n_agents=population)
    samples, signatures = [], []
    for _ in range(REPEATS):
        gc.collect()
        start = time.perf_counter()
        sim = CitySimulation(config).run()
        elapsed = time.perf_counter() - start
        samples.append(elapsed)
        signatures.append(_signature(sim))
        del sim
    # Capture this before tracemalloc adds its own memory overhead. The fresh
    # child isolates this population from the other populations' high-water marks.
    rss = _max_rss()
    gc.collect()
    tracemalloc.start()
    start = time.perf_counter()
    try:
        sim = CitySimulation(config).run()
        traced_seconds = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    traced_signature = _signature(sim)
    del sim
    deterministic = all(signature == signatures[0] for signature in signatures + [traced_signature])
    if not deterministic:
        raise ValueError("profile repetitions did not reproduce identical city semantics")
    median = statistics.median(samples)
    result = {"population": population, "config": asdict(config), "repeats": REPEATS,
              "runtime_seconds": samples, "median_seconds": median,
              "mean_seconds": statistics.fmean(samples),
              "min_seconds": min(samples), "max_seconds": max(samples),
              "sample_sd_seconds": statistics.stdev(samples),
              "worlds_per_second": 1 / median,
              "events_per_second": signatures[0]["events"] / median,
              "events": signatures[0]["events"], "decisions": signatures[0]["decisions"],
              "deterministic": deterministic, "ledger_hash": signatures[0]["ledger_hash"],
              "semantic_hash": signatures[0]["semantic_hash"],
              "repeat_ledger_hashes": [signature["ledger_hash"] for signature in signatures],
              "repeat_semantic_hashes": [signature["semantic_hash"] for signature in signatures],
              "peak_traced_bytes": peak, "traced_run_seconds": traced_seconds,
              "traced_semantic_hash": traced_signature["semantic_hash"], **rss}
    _validate_result(result)
    return result


def _validate_result(result):
    if result["population"] not in POPULATIONS or result["repeats"] != REPEATS:
        raise ValueError("profile must use the declared populations and five repeats")
    if len(result["runtime_seconds"]) != REPEATS or not result["deterministic"]:
        raise ValueError("profile repetitions are incomplete or nondeterministic")
    for key in ("median_seconds", "mean_seconds", "min_seconds", "max_seconds",
                "worlds_per_second", "events_per_second", "traced_run_seconds"):
        value = result[key]
        if not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"profile statistic {key} must be finite and positive")
    if any(not math.isfinite(value) or value <= 0 for value in result["runtime_seconds"]):
        raise ValueError("runtime samples must be finite and positive")
    if not math.isfinite(result["sample_sd_seconds"]) or result["sample_sd_seconds"] < 0:
        raise ValueError("runtime sample deviation must be finite and nonnegative")
    for key in ("events", "decisions", "peak_traced_bytes"):
        if type(result[key]) is not int or result[key] <= 0:
            raise ValueError(f"profile statistic {key} must be a positive integer")
    if result["max_rss_bytes"] is not None and result["max_rss_bytes"] <= 0:
        raise ValueError("available process RSS must be positive")
    if len(result["repeat_semantic_hashes"]) != REPEATS or len(result["repeat_ledger_hashes"]) != REPEATS:
        raise ValueError("profile hash samples are incomplete")
    if (len(set(result["repeat_semantic_hashes"] + [result["traced_semantic_hash"], result["semantic_hash"]])) != 1 or
            len(set(result["repeat_ledger_hashes"] + [result["ledger_hash"]])) != 1):
        raise ValueError("profile semantic hashes do not agree")
    expected = {"median_seconds": statistics.median(result["runtime_seconds"]),
                "mean_seconds": statistics.fmean(result["runtime_seconds"]),
                "min_seconds": min(result["runtime_seconds"]),
                "max_seconds": max(result["runtime_seconds"]),
                "sample_sd_seconds": statistics.stdev(result["runtime_seconds"])}
    expected["worlds_per_second"] = 1 / expected["median_seconds"]
    expected["events_per_second"] = result["events"] / expected["median_seconds"]
    if any(not math.isclose(result[key], value, rel_tol=1e-12, abs_tol=1e-12)
           for key, value in expected.items()):
        raise ValueError("profile summary statistics do not match their runtime samples")


def _environment():
    # Avoid hostname, username, environment variables, and machine identifiers.
    return {"python_version": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "os": platform.system(), "os_release": platform.release(),
            "machine": platform.machine(),
            "cpu_model": platform.processor() or "unavailable from platform.processor()"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="new JSON output file; never overwritten")
    parser.add_argument("--populations", default="8,32,128",
                        help="comma-separated subset of the declared 8,32,128 populations")
    parser.add_argument("--worker-population", type=int, choices=POPULATIONS,
                        help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker_population is not None:
        print(json.dumps(profile_population(args.worker_population), allow_nan=False))
        return
    if args.out is None:
        parser.error("--out is required")
    if args.out.exists():
        parser.error("--out already exists; choose a new output file")
    try:
        populations = [int(value) for value in args.populations.split(",")]
    except ValueError:
        parser.error("--populations must be a comma-separated subset of 8,32,128")
    if (not populations or len(set(populations)) != len(populations) or
            any(population not in POPULATIONS for population in populations)):
        parser.error("--populations must be a unique nonempty subset of 8,32,128")
    rows = []
    for population in populations:
        completed = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker-population", str(population)],
            cwd=str(ROOT), capture_output=True, text=True, check=True)
        result = json.loads(completed.stdout)
        _validate_result(result)
        rows.append(result)
    artifact = {"schema_version": 1, "environment": _environment(),
                "population_order": populations, "profiles": rows,
                "methodology": {
                    "isolation": "one fresh child process per population, executed sequentially",
                    "runtime": "five CitySimulation construction+run measurements without tracemalloc; gc.collect before each; hashing outside timing",
                    "warmth": "Python and city modules imported before repeats; first world run is included among the five",
                    "traced_memory": "one separate construction+run after timed repeats; peak Python traced allocations in bytes, not RSS; imports excluded",
                    "traced_runtime": "reported separately; instrumentation overhead is excluded from median runtime",
                    "rss": "fresh worker process maximum RSS after five untraced runs, sampled before tracing; includes imports, determinism hashing, and allocator retention; bytes and KiB normalized",
                    "rss_units": "macOS ru_maxrss bytes; other supported Unix ru_maxrss KiB; this is a process high-water mark, not incremental per-world RAM",
                    "determinism": "full ledger and decision semantic hashes agree across all five untraced runs and the separate traced run",
                    "study_separation": "diagnostic fixed configuration; no policy or threshold selection"}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(artifact, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(f"Saved isolated resource profile to {args.out}")


if __name__ == "__main__":
    main()
