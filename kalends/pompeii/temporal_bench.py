"""Paired actual-world timing and fidelity checks for Pompeii's event clock.

Development runs precede source registration. Heldout runs require an unchanged
registration and refuse to overwrite artifacts. No rendering is benchmarked.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import time
import tracemalloc


ROOT = Path(__file__).resolve().parents[2]
REGISTRATION = ROOT / "results/pompeii/temporal_preregistration.json"
MODES = ("live", "compress", "naive")
HORIZONS = (1, 7, 30)
DEVELOPMENT_SEEDS = tuple(range(30000, 30010))
HELDOUT_SEEDS = tuple(range(70000, 70030))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fingerprint():
    files = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in sorted((ROOT / "kalends").rglob("*.py"))}
    return {"sha256": digest(files), "files": files}


def registration():
    return {"version": 1, "design": "paired actual PompeiiWorld; no montage rendering",
        "development_seeds": list(DEVELOPMENT_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
        "horizons_days": list(HORIZONS), "minutes_per_day": 1440,
        "modes": list(MODES), "naive_coarse_minutes": 60,
        "population": 6, "memory_capacity": 32,
        "scripted_player_prefix": ["move to bakery", "accept Felix delivery"],
        "prefix_scope": "same legitimate game actions in every world; leave delivery open until its scheduled deadline; no oracle observations or adaptive player policy",
        "runtime_repeats": 5, "traced_peak_repeats": 1,
        "runtime_protocol": "five fresh matched worlds per mode/seed/horizon; report median construction plus advance; gc before each run; mode order seeded independently of world randomness; exclude one-time module import",
        "memory_protocol": "separate fresh repeat; tracemalloc Python allocation peak, not process RSS; timing not used for speedup",
        "primary": "exact equality of all declared semantic projections, live versus compress, in every matched cell",
        "secondary": "paired wall-time speedup live/other; naive fidelity divergence and task lateness",
        "projection_difference": "positionwise unequal JSON leaves, including missing leaves; not sequence edit distance or causal attribution",
        "semantic_projections": "actions_only is per-agent ordered action history; decision_choices additionally includes predictions, both excluding minute/event_id/inter-agent order; terminal belief_values excludes dates/evidence IDs; outcomes excludes minute/event/decision counts; ordinary and consolidated memory buffers are checked separately in state",
        "uncertainty": "descriptive 95% paired-seed percentile bootstrap separately by horizon; no decision-level pseudoreplication",
        "scope": "established discrete-event scheduling for explicitly scheduled autonomous changes; no novel algorithm or measured browser rendering claim",
        "source": fingerprint()}


def _world_type():
    # Import only on actual execution: this benchmark cannot replace the town
    # model with a synthetic task generator when integration is unavailable.
    from .world import PompeiiWorld
    return PompeiiWorld


def _projection(world):
    method = getattr(world, "temporal_projection", None)
    if callable(method):
        result = method()
    elif callable(getattr(world, "fidelity_state", None)):
        # Explicit adapter for the actual game world, not a replacement model.
        state = world.fidelity_state()
        result = {key: state.pop(key) for key in
                  ("decisions", "beliefs", "relationships", "commitments")}
        state.pop("ledger_hash", None)  # Full event content is checked below.
        state["locations"] = dict(world.state.agent_locations)
        state["queue"] = world.clock.snapshot()
        state["ordinary_memories"] = {a: [asdict(e) for e in rows] for a, rows in world.memories.items()}
        state["consolidated_memories"] = {a: [asdict(e) for e in rows] for a, rows in world.consolidated.items()}
        state["disclosed"] = sorted(world.disclosed)
        state["account_parent_index"] = dict(world._last_account)
        result.update(state=state, events=world.ledger.to_json())
        result["decision_choices"] = {
            agent: [{key: decision[key] for key in ("action", "value")}
                    for decision in result["decisions"] if decision["agent"] == agent]
            for agent in world.agent_ids}
        result["actions_only"] = {agent: [decision["action"] for decision in result["decisions"]
                                          if decision["agent"] == agent] for agent in world.agent_ids}
        result["belief_values"] = {agent: belief["value"] for agent, belief in result["beliefs"].items()}
        result["outcomes"] = {key: value for key, value in world.metrics().items()
                              if key not in ("minute", "events", "decisions")}
    else:
        raise RuntimeError("PompeiiWorld must expose its actual temporal_projection or fidelity_state")
    required = {"state", "decisions", "beliefs", "relationships", "commitments", "events"}
    if not isinstance(result, dict):
        raise RuntimeError("world temporal projection must be a JSON object")
    if not required <= set(result):
        raise RuntimeError("world temporal projection missing " + str(sorted(required - set(result))))
    # Round-trip prevents live mutable references from changing after capture.
    return json.loads(canonical(result))


def run_world(seed, days, mode, traced=False):
    if type(seed) is not int or type(days) is not int or days <= 0 or mode not in MODES:
        raise ValueError("invalid temporal benchmark cell")
    constructor = _world_type()  # Exclude one-time module import from all modes.
    gc.collect()
    if traced:
        tracemalloc.start()
    started = time.perf_counter()
    try:
        world = constructor(seed=seed)
        # A legitimate, fixed player prefix makes commitment and relationship
        # fidelity non-vacuous. The deadline remains pending for the scheduler.
        world.move(location="bakery")
        world.interact("accept_delivery", "Felix")
        stats = world.clock.advance(days * 1440, world.on_task, mode=mode, coarse=60)
        elapsed = time.perf_counter() - started
        peak = tracemalloc.get_traced_memory()[1] if traced else None
    finally:
        if traced:
            tracemalloc.stop()
    projection = _projection(world)
    return {"seed": seed, "days": days, "mode": mode,
            "wall_seconds": elapsed, "scheduler": stats,
            "peak_traced_bytes": peak,
            "hashes": {key: digest(value) for key, value in projection.items()},
            "event_count": len(projection["events"]),
            "decision_count": len(projection["decisions"]),
            "projection": projection}


def repeated_world(seed, days, mode, repeats=5):
    if type(repeats) is not int or repeats < 1:
        raise ValueError("repeats must be a positive integer")
    runs = [run_world(seed, days, mode) for _ in range(repeats)]
    first = runs[0]
    first["runtime_repeats_seconds"] = [run["wall_seconds"] for run in runs]
    first["runtime_repeat_hashes_equal"] = all(run["hashes"] == first["hashes"] for run in runs)
    first["wall_seconds"] = statistics.median(first["runtime_repeats_seconds"])
    first["scheduler"]["wall_seconds"] = statistics.median(run["scheduler"]["wall_seconds"] for run in runs)
    return first


def differences(left, right, max_examples=8):
    """Count unequal positionwise leaves; samples identify concrete mismatches."""
    examples, count = [], 0

    def visit(a, b, path):
        nonlocal count
        if type(a) is type(b) and isinstance(a, dict):
            for key in sorted(set(a) | set(b)):
                if key not in a or key not in b:
                    count += 1
                    if len(examples) < max_examples:
                        examples.append({"path": path + [key], "missing": "reference" if key not in a else "candidate"})
                else:
                    visit(a[key], b[key], path + [key])
        elif type(a) is type(b) and isinstance(a, list):
            for index in range(max(len(a), len(b))):
                if index >= len(a) or index >= len(b):
                    count += 1
                    if len(examples) < max_examples:
                        examples.append({"path": path + [index], "missing": "reference" if index >= len(a) else "candidate"})
                else:
                    visit(a[index], b[index], path + [index])
        elif type(a) is not type(b) or a != b:
            count += 1
            if len(examples) < max_examples:
                examples.append({"path": path, "reference": a, "candidate": b})

    visit(left, right, [])
    return {"equal": count == 0, "unequal_leaves": count, "examples": examples}


def compare(reference, candidate):
    return {key: differences(reference["projection"][key], candidate["projection"][key])
            for key in reference["projection"]}


def interval(values):
    if not values:
        return None
    rng = random.Random(71449)
    estimates = sorted(statistics.fmean(rng.choices(values, k=len(values))) for _ in range(4000))
    return {"mean": statistics.fmean(values), "median": statistics.median(values),
            "ci95_mean": [estimates[99], estimates[3899]], "n_independent_seeds": len(values)}


def summarize(rows):
    result = []
    for days in sorted({row["days"] for row in rows}):
        for mode in MODES:
            selected = [row for row in rows if row["days"] == days and row["mode"] == mode]
            result.append({"days": days, "mode": mode,
                "wall_seconds": interval([r["wall_seconds"] for r in selected]),
                "speedup_over_live": interval([r["speedup_over_live"] for r in selected]),
                "peak_traced_bytes": interval([r["peak_traced_bytes"] for r in selected]),
                "exact_cells": sum(all(d["equal"] for d in r["differences"].values()) for r in selected),
                "cells": len(selected),
                "mean_events": statistics.fmean(r["event_count"] for r in selected),
                "mean_decisions": statistics.fmean(r["decision_count"] for r in selected),
                "mean_dispatched": statistics.fmean(r["scheduler"]["dispatched"] for r in selected),
                "mean_ticks_visited": statistics.fmean(r["scheduler"]["ticks_visited"] for r in selected),
                "mean_lateness_minutes": statistics.fmean(r["scheduler"]["total_lateness"] for r in selected),
                "divergent_cells_by_projection": {key: sum(not r["differences"][key]["equal"] for r in selected)
                                                  for key in selected[0]["differences"]}})
    return {"cells": result, "world_runtime_runs": sum(len(r["runtime_repeats_seconds"]) for r in rows), "world_traced_runs": len(rows),
            "all_runtime_repeats_deterministic": all(r["runtime_repeat_hashes_equal"] for r in rows),
            "all_traced_repeats_deterministic": all(r["traced_repeat_equal"] for r in rows),
            "live_compress_exact": all(all(d["equal"] for d in r["differences"].values())
                                       for r in rows if r["mode"] == "compress"),
            "scope": "Paired fresh seeds; Python traced allocations, not RSS. Exactness is limited to scheduled model transitions. Montage/browser costs are excluded."}


def plot_results(rows, output):
    # A normal scientific plotting library is optional for the stdlib model.
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return {"status": "unavailable", "reason": "matplotlib is not installed in this Python"}
    semantic = all("actions_only" in row["differences"] and "outcomes" in row["differences"] for row in rows)
    fig, axes = plt.subplots(2 if semantic else 1, 2, figsize=(10, 7 if semantic else 4))
    axes = list(axes.flat)
    for mode in ("compress", "naive"):
        means = [statistics.fmean(r["speedup_over_live"] for r in rows
                                 if r["days"] == days and r["mode"] == mode) for days in HORIZONS]
        axes[0].plot(HORIZONS, means, marker="o", label=mode)
        fidelity = [sum(all(d["equal"] for d in r["differences"].values()) for r in rows
                        if r["days"] == days and r["mode"] == mode) /
                    sum(r["days"] == days and r["mode"] == mode for r in rows) for days in HORIZONS]
        axes[1].plot(HORIZONS, fidelity, marker="o", label=mode)
        if semantic:
            for axis, key in ((axes[2], "actions_only"), (axes[3], "outcomes")):
                fractions = [sum(r["differences"][key]["equal"] for r in rows
                                 if r["days"] == days and r["mode"] == mode) /
                             sum(r["days"] == days and r["mode"] == mode for r in rows) for days in HORIZONS]
                axis.plot(HORIZONS, fractions, marker="o", label=mode)
    axes[0].set(xlabel="Horizon (days)", ylabel="Mean paired speedup over minute scan")
    axes[0].axhline(1, color="gray", linewidth=.7)
    axes[1].set(xlabel="Horizon (days)", ylabel="Fraction of exactly equal world projections", ylim=(-.04, 1.04))
    if semantic:
        axes[2].set(xlabel="Horizon (days)", ylabel="Fraction matching each agent's action history", ylim=(-.04, 1.04))
        axes[3].set(xlabel="Horizon (days)", ylabel="Fraction matching executed terminal outcomes", ylim=(-.04, 1.04))
    for axis in axes:
        axis.legend(); axis.grid(alpha=.25)
    fig.suptitle("Actual Pompeii world: fidelity and scheduler timing (no rendering)")
    fig.tight_layout()
    for suffix in ("png", "svg"):
        fig.savefig(output / ("fidelity_speedup." + suffix), dpi=160)
    plt.close(fig)
    return {"status": "written", "files": ["fidelity_speedup.png", "fidelity_speedup.svg"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", action="store_true", help="freeze source and protocol before heldout")
    parser.add_argument("--phase", choices=("development", "heldout"), default="development")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--plot-existing", type=Path, help="render saved measurements; does not rerun worlds")
    args = parser.parse_args(argv)
    if args.plot_existing is not None:
        if args.register or args.out is not None:
            raise SystemExit("plot-existing cannot be combined with register or out")
        output = args.plot_existing
        if any((output / name).exists() for name in
               ("fidelity_speedup.png", "fidelity_speedup.svg", "plot_manifest.json")):
            raise SystemExit("Refusing to overwrite existing plots")
        rows = [json.loads(line) for line in (output / "worlds.jsonl").read_text().splitlines() if line]
        result = plot_results(rows, output)
        result.update(python=platform.python_version(), source=fingerprint(),
                      raw_sha256=hashlib.sha256((output / "worlds.jsonl").read_bytes()).hexdigest(),
                      scope="Saved measurements only; no simulation or timing rerun")
        (output / "plot_manifest.json").write_text(json.dumps(result, indent=2) + "\n")
        return
    if args.register:
        REGISTRATION.parent.mkdir(parents=True, exist_ok=True)
        with REGISTRATION.open("x") as target:
            target.write(json.dumps(registration(), indent=2) + "\n")
        print(str(REGISTRATION))
        return
    before = fingerprint()
    registered = None
    if args.phase == "heldout":
        if not REGISTRATION.is_file():
            raise SystemExit("Register the source and protocol before heldout")
        registered = json.loads(REGISTRATION.read_text())
        if registered != registration():
            raise SystemExit("Source/protocol changed after registration; heldout not started")
    output = args.out or ROOT / "results/pompeii" / ("temporal_" + args.phase)
    if output.exists():
        raise SystemExit("Refusing to overwrite existing artifact path: " + str(output))
    output.mkdir(parents=True)
    manifest = {"phase": args.phase, "protocol": registration(),
        "python": platform.python_version(), "platform": platform.system(),
        "processor": platform.processor(), "source": before,
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    rows, began = [], time.perf_counter()
    seeds = DEVELOPMENT_SEEDS if args.phase == "development" else HELDOUT_SEEDS
    with (output / "worlds.jsonl").open("x") as raw:
        for seed in seeds:
            for days in HORIZONS:
                order = list(MODES)
                random.Random(seed * 31 + days).shuffle(order)
                runs = {mode: repeated_world(seed, days, mode) for mode in order}
                paired = {mode: compare(runs["live"], runs[mode]) for mode in order}
                for mode in order:
                    traced = run_world(seed, days, mode, traced=True)
                    row = runs[mode]
                    row["differences"] = paired[mode]
                    row["speedup_over_live"] = runs["live"]["wall_seconds"] / row["wall_seconds"]
                    row["traced_repeat_equal"] = row["hashes"] == traced["hashes"]
                    row["peak_traced_bytes"] = traced["peak_traced_bytes"]
                    row.pop("projection")
                    raw.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n"); raw.flush()
                    rows.append(row)
                print(f"{args.phase} seed={seed} days={days}: {len(rows)} cells", flush=True)
    summary = summarize(rows)
    summary.update(wall_seconds=time.perf_counter() - began, source_unchanged=fingerprint() == before,
                   raw_sha256=hashlib.sha256((output / "worlds.jsonl").read_bytes()).hexdigest())
    summary["plots"] = plot_results(rows, output)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    if (not summary["source_unchanged"] or not summary["live_compress_exact"]
            or not summary["all_traced_repeats_deterministic"] or not summary["all_runtime_repeats_deterministic"]):
        raise SystemExit("Temporal verification failed; see preserved output artifacts")


if __name__ == "__main__":
    main()
