"""Registered paired performance/fidelity study of the actual Rebirth game.

The optimization changes historical representation, not simulated time. The
strong reference uses the same world, exact scheduler and atomic session path.
Heldout execution requires a registered, unchanged runtime and refuses overwrite.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import asdict
import gc
import hashlib
import json
import math
from pathlib import Path
import platform
import random
import statistics
import sys
import tempfile
import time
import tracemalloc


ROOT = Path(__file__).resolve().parents[1]
REGISTRATION = ROOT / "results/rebirth/performance_preregistration_v2.json"
DEVELOPMENT_SEEDS = tuple(range(32000, 32006))
HELDOUT_SEEDS = tuple(range(83000, 83020))
HORIZONS = (1, 30, 60)
DENSITIES = ("ordinary", "conversation_heavy")
REPEATS = 5
ROUTES = ("broker", "market", "household", "ignored")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fingerprint():
    files = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
             for package in ("kalends", "kalends_rebirth")
             for path in sorted((ROOT / package).rglob("*.py"))}
    return {"sha256": digest(files), "files": files}


def design():
    return {"version": 2, "question": "Does sealed historical sharing plus incremental ledger hashing reduce actual isolated transaction latency without changing world outcomes?",
        "development_seeds": list(DEVELOPMENT_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
        "horizons_days": list(HORIZONS), "densities": list(DENSITIES), "population": 6,
        "memory_capacity": 32, "world_horizon_days": 365,
        "routes": list(ROUTES), "route_assignment": "seed modulo four, using ROUTES order",
        "social_prefix": "broker worlds accept a real follow-on evidence commission and alternate fulfilled/missed by integer(seed/4) parity; household worlds alternate kept/missed service using the same parity; other routes retain their distinct allocations/access",
        "density": "ordinary adds no stress conversations; conversation_heavy performs twelve actual nearby Marcus memory conversations per world-day, including movement; this is archive-interaction stress, not increased NPC population",
        "reference": "RebirthWorld optimized=False: original mutable Ledger, ordinary deepcopy and full canonical JSON hash; same game and exact event scheduler",
        "optimized": "RebirthWorld optimized=True: sealed historical event bodies shared across detached candidate list heads, copied streaming SHA256 prefix; current world state still deepcopied",
        "transaction": "actual RebirthSession.commit move(location=street) plus the HTTP handler's canonical response JSON serialization; world/session setup and independent revision-hash measurement excluded",
        "revision_hash": "separate post-transaction ledger.content_hash measurement, representing proposal revision checks; never added to primary transaction latency; saved commit already includes its real persistence hash",
        "durability": "same transaction with actual JSON command-journal write and atomic replace in a fresh temporary directory; no fsync durability or network/browser latency claim",
        "repeats": REPEATS, "order": "deterministically shuffled paired optimization order for each seed/cell/repeat, unrelated to world RNG",
        "bulk_cost": "matched legal opening followed by actual history advancement; report elapsed build and advancement, including per-event sealing/hash cost; separate from transaction claim",
        "fidelity": "canonical event contents and ledger hash, complete declared fidelity_state, ordinary+consolidated memory buffers, game snapshot, account provenance index, auxiliary supply/sale indexes and economic relationship projection; every timed accepted transaction compared against matched reference; only snapshot.time_stats.wall_seconds is excluded as nondeterministic measurement metadata",
        "rejection": "invalid off-street movement must leave accepted world, command journal and hashes unchanged in each mode",
        "restart": "reopen a written actual session journal per cell/mode and compare declared semantics",
        "memory": "separate transaction repeat under tracemalloc; Python incremental allocation peak, not total world RAM or RSS; traced timings excluded",
        "primary": "zero semantic mismatches; paired transaction speedup optimized versus reference after history",
        "secondary": "disk transaction cost, bulk advancement write tradeoff, history-size dependence and incremental allocations",
        "uncertainty": "descriptive95% percentile bootstrap of paired-seed geometric mean ratios within each horizon/density;2000resamples; seed is unit, no event-level pseudo-replication",
        "limits": "single machine; six authored NPCs; finite authored routes; no new temporal abstraction, no LLM calls, no human enjoyment/retention evidence",
        "source": fingerprint()}


def register(path=REGISTRATION):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        stream.write(json.dumps(design(), indent=2) + "\n")
    return path


def validate_registration(path=REGISTRATION):
    actual = json.loads(Path(path).read_text())
    if actual != design():
        raise ValueError("Registration or runtime changed; preserve artifacts and register a new version before any heldout rerun")
    return actual


def semantic_snapshot(world):
    """Declared outcomes include new intrigue/plans and underlying game history."""
    return {"state": world.fidelity_state(), "events": world.ledger.to_json(),
        "ordinary_memories": {a: [asdict(e) for e in rows] for a, rows in world.memories.items()},
        "consolidated_memories": {a: [asdict(e) for e in rows] for a, rows in world.consolidated.items()},
        "game": semantic_game(world.snapshot()), "account_parent_index": dict(world._last_account),
        "agent_locations": dict(world.state.agent_locations),
        "auxiliary_state": {"dispatch_records": copy.deepcopy(world.dispatch_records),
            "information_sales": copy.deepcopy(world.information_sales), "world_tick": world.state.tick,
            "economy_relationships": [[a,b,value] for (a,b),value in sorted(world.economy.relationships.items())],
            "initial_cash": dict(world._initial_cash), "initial_inventory": dict(world._initial_inventory),
            "config": asdict(world.config), "agent_ids": list(world.agent_ids), "ready": world._rebirth_ready}}


def semantic_game(snapshot):
    snapshot = copy.deepcopy(snapshot)
    if snapshot.get("time_stats"):
        snapshot["time_stats"].pop("wall_seconds", None)
    return snapshot


def changed_fields(first, second):
    """Report top-level semantic failures without treating event IDs as outcomes."""
    return [key for key in sorted(set(first) | set(second))
            if canonical(first.get(key)) != canonical(second.get(key))]


def outcome_summary(world):
    commitments = [commitment for rows in world.economy.commitments.values() for commitment in rows]
    return {"metrics": world.metrics(),
        "commitments_by_status": {status: sum(c["status"] == status for c in commitments)
                                  for status in sorted({c["status"] for c in commitments})},
        "commission_statuses": [c["status"] for c in world.commissions],
        "service_done": bool(world.arc.get("service_done")),
        "service_missed": bool(world.arc.get("service_missed")),
        "pending_tasks": len(world.clock),
        "decision_actions": {action: sum(d["action"] == action for d in world.decisions)
                             for action in sorted({d["action"] for d in world.decisions})}}


def _perform(world, operation, data):
    if operation == "move":
        return world.move(**data)
    if operation == "advance":
        return world.advance(**data)
    if operation == "action":
        from .language import execute
        return execute(world, data)
    raise ValueError("Unknown study command")


def build_world(seed, days, density, optimized):
    """All stress records arise from legitimate game actions, never fake events."""
    from kalends.pompeii.district import PompeiiConfig
    from .world import RebirthWorld
    from .language import execute  # Import setup is excluded from runtime costs.
    if days not in HORIZONS or density not in DENSITIES:
        raise ValueError("Unsupported registered condition")
    commands = []
    started = time.perf_counter_ns()
    world = RebirthWorld(PompeiiConfig(seed=seed, horizon_days=365), optimized=optimized)

    def command(operation, **data):
        at = world.minute
        receipt = _perform(world, operation, data)
        commands.append({"operation": operation, "data": copy.deepcopy(data), "at": at,
            "receipt_id": receipt.get("event_id") if isinstance(receipt, dict) else None,
            "after": world.minute})
        return receipt

    def near(agent):
        location = world.state.agent_locations[agent]
        if world.state.agent_locations["Player"] != location:
            command("move", location=location)
        x, y = world.positions[agent]
        command("move", x=x, y=y)

    def action(name, recipient, **data):
        near(recipient)
        return command("action", action=name, recipient=recipient, **data)

    route = ROUTES[seed % len(ROUTES)]
    if route == "broker":
        action("hear_dispute", "Sabina")
        action("examine_receipt", "Sabina")
        action("examine_tablet", "Dama")
        action("verify_cart", "Marcus")
        action("mediate", "Marcus")
        command("advance", minutes=45, mode="compress")
        action("accept_commission", "Marcus")
        if (seed // 4) % 2 == 0:
            action("inspect", "Marcus")
            command("advance", minutes=15, mode="compress")
            action("fulfill_commission", "Marcus")
    elif route == "market":
        action("support_market", "Sabina")
    elif route == "household":
        action("guarantee_household", "Lucius")
        # Alternate kept and missed services across seeds without oracle control.
        if (seed // 4) % 2 == 0:
            action("return_service", "Lucius")
    else:
        action("decline_dispute", "Sabina")
    opening_ns = time.perf_counter_ns() - started

    started = time.perf_counter_ns()
    for day in range(days):
        if density == "conversation_heavy":
            near("Marcus")
            for _ in range(12):
                command("action", action="talk", recipient="Marcus", topic="memory")
        target = (day + 1) * 1440
        if world.minute < target:
            command("advance", minutes=target-world.minute, mode="compress")
    advance_ns = time.perf_counter_ns() - started
    if world.minute != days * 1440:
        raise AssertionError("Opening/history exceeded the registered absolute horizon")
    return world, commands, {"opening_ms": opening_ns/1e6, "history_ms": advance_ns/1e6,
        "total_build_ms": (opening_ns+advance_ns)/1e6, "events": len(world.ledger),
        "decisions": len(world.decisions), "commands": len(commands), "route": route,
        "ledger_bytes": len(canonical(world.ledger.to_json()).encode())}


def _session(world, commands, journal_path=None):
    # Import failure is an integration failure, never silently benchmark a stand-in.
    from .server import RebirthSession
    session = RebirthSession(journal_path=journal_path, optimized=world.optimized)
    session.original = world
    session.config = asdict(world.config)
    session.commands = copy.deepcopy(commands)
    session.mode = "game"
    return session


def _transaction(session):
    response = session.commit("move", {"location": "street"})
    raw = canonical(response).encode()  # Same sorted compact JSON as the HTTP handler.
    # Serialized byte counts may differ because the diagnostic wall-time number
    # has a different textual length; preserve it as a cost, not semantic truth.
    return {"response": response, "response_bytes": len(raw)}


def _timed_transaction(world, commands, journal_path=None, traced=False):
    session = _session(world, commands, journal_path)
    gc.collect()
    if traced:
        tracemalloc.start()
        try:
            result = _transaction(session)
            current, peak = tracemalloc.get_traced_memory()
        finally:
            tracemalloc.stop()
        measurement = {"current_bytes": current, "peak_bytes": peak}
    else:
        started = time.perf_counter_ns()
        result = _transaction(session)
        measurement = {"elapsed_ms": (time.perf_counter_ns()-started)/1e6}
    # Revision checking is a real proposal-path operation, measured separately.
    started = time.perf_counter_ns()
    result["revision"] = session.original.ledger.content_hash()
    measurement["revision_hash_ms"] = (time.perf_counter_ns()-started)/1e6
    return session, result, measurement


def _reject_check(world, commands):
    session = _session(world, commands)
    before = digest({"world": semantic_snapshot(session.original), "commands": session.commands})
    try:
        session.commit("move", {"x": 25, "y": 25})
    except ValueError:
        pass
    else:
        raise AssertionError("Off-street movement was unexpectedly accepted")
    after = digest({"world": semantic_snapshot(session.original), "commands": session.commands})
    if after != before:
        raise AssertionError("Rejected action changed accepted state")


def paired_interval(values, seed=1927):
    if not values or any(v <= 0 or not math.isfinite(v) for v in values):
        raise ValueError("Ratios must be finite and positive")
    logs = [math.log(v) for v in values]
    rng = random.Random(seed)
    means = sorted(math.exp(statistics.mean(rng.choices(logs, k=len(logs)))) for _ in range(2000))
    return {"geometric_mean": math.exp(statistics.mean(logs)), "low95": means[49], "high95": means[1949],
            "paired_seeds": len(logs)}


def summarize(rows):
    result = []
    for days in sorted({row["days"] for row in rows}):
        for density in sorted({row["density"] for row in rows}):
            cells = [row for row in rows if row["days"] == days and row["density"] == density]
            summary = {"days": days, "density": density, "seeds": len(cells),
                "all_semantics_equal": all(row["fidelity_equal"] for row in cells),
                "events_range": [min(row["modes"]["reference"]["build"]["events"] for row in cells),
                                 max(row["modes"]["reference"]["build"]["events"] for row in cells)]}
            for condition in ("memory_transaction", "disk_transaction"):
                summary[condition] = paired_interval([row["modes"]["reference"][condition]["median_ms"] /
                    row["modes"]["optimized"][condition]["median_ms"] for row in cells])
                for mode in ("reference", "optimized"):
                    summary[condition][mode+"_median_ms"] = statistics.median(row["modes"][mode][condition]["median_ms"] for row in cells)
            summary["history_speed_ratio"] = paired_interval([row["modes"]["reference"]["build"]["history_ms"] /
                row["modes"]["optimized"]["build"]["history_ms"] for row in cells])
            summary["transaction_peak_ratio"] = paired_interval([row["modes"]["reference"]["traced_transaction"]["peak_bytes"] /
                row["modes"]["optimized"]["traced_transaction"]["peak_bytes"] for row in cells])
            result.append(summary)
    return result


def run(output, *, heldout=False, seeds=None, horizons=None, densities=None, registration_path=REGISTRATION):
    if heldout:
        validate_registration(registration_path)
        if seeds is not None or horizons is not None or densities is not None:
            raise ValueError("Heldout conditions cannot be selected after registration")
    seeds = tuple(seeds or (HELDOUT_SEEDS if heldout else DEVELOPMENT_SEEDS))
    horizons = tuple(horizons or HORIZONS)
    densities = tuple(densities or DENSITIES)
    if not heldout and not set(seeds) <= set(DEVELOPMENT_SEEDS):
        raise ValueError("Pilot seeds must come from the development range")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    start_source = fingerprint()
    metadata = {"phase": "heldout" if heldout else "development", "source": start_source,
        "python": sys.version, "executable": sys.executable, "platform": platform.platform(),
        "seeds": list(seeds), "horizons": list(horizons), "densities": list(densities),
        "design": design(), "note": "Timings are local CPU/session/filesystem measurements; no rendering, network, GPU or paid inference."}
    (output/"metadata.json").write_text(json.dumps(metadata, indent=2)+"\n")
    def fail(message, **detail):
        (output/"failure.json").write_text(json.dumps({"error": message, **detail}, indent=2)+"\n")
        raise AssertionError(message)
    rows = []
    for seed in seeds:
        for days in horizons:
            for density in densities:
                row = {"seed": seed, "days": days, "density": density, "modes": {}}
                worlds, commands, snapshots = {}, {}, {}
                order = [False, True]
                random.Random(seed*1000+days).shuffle(order)
                for optimized in order:
                    name = "optimized" if optimized else "reference"
                    gc.collect()
                    world, accepted, build = build_world(seed, days, density, optimized)
                    worlds[name], commands[name] = world, accepted
                    snapshots[name] = semantic_snapshot(world)
                    row["modes"][name] = {"build": build}
                mismatches = changed_fields(snapshots["reference"], snapshots["optimized"])
                if mismatches:
                    fail("History semantic mismatch", seed=seed, days=days, density=density, fields=mismatches)
                row["history_semantic_digest"] = digest(snapshots["reference"])
                row["semantic_projection_digests"] = {key: digest(value) for key, value in snapshots["reference"].items()}
                row["outcomes"] = outcome_summary(worlds["reference"])
                del snapshots
                for condition in ("memory_transaction", "disk_transaction"):
                    elapsed = {name: [] for name in worlds}
                    revision_costs = {name: [] for name in worlds}
                    response_sizes = {name: [] for name in worlds}
                    for repeat in range(REPEATS):
                        pair = list(worlds)
                        random.Random(seed*100000+days*100+repeat).shuffle(pair)
                        outcomes = {}
                        for name in pair:
                            with tempfile.TemporaryDirectory(prefix="kalends-rebirth-study-") as directory:
                                path = Path(directory)/"world.json" if condition == "disk_transaction" else None
                                session, response, timing = _timed_transaction(worlds[name], commands[name], path)
                                elapsed[name].append(timing["elapsed_ms"])
                                revision_costs[name].append(timing["revision_hash_ms"])
                                response_sizes[name].append(response["response_bytes"])
                                outcomes[name] = {"world": semantic_snapshot(session.original),
                                    "response": {**response["response"], "world": semantic_game(response["response"]["world"])},
                                    "revision": response["revision"]}
                                if path is not None and repeat == 0:
                                    from .server import RebirthSession
                                    replayed = RebirthSession(journal_path=path, optimized=name == "optimized")
                                    if changed_fields(semantic_snapshot(session.original), semantic_snapshot(replayed.original)):
                                        fail("Written session replay changed declared semantics", seed=seed, days=days,
                                             density=density, mode=name, condition=condition, repeat=repeat)
                        if changed_fields(outcomes["reference"], outcomes["optimized"]):
                            fail("Accepted actual session responses/outcomes differ", seed=seed, days=days,
                                 density=density, condition=condition, repeat=repeat,
                                 fields=changed_fields(outcomes["reference"], outcomes["optimized"]))
                    for name in worlds:
                        row["modes"][name][condition] = {"samples_ms": elapsed[name], "median_ms": statistics.median(elapsed[name]),
                            "revision_hash_samples_ms": revision_costs[name], "revision_hash_median_ms": statistics.median(revision_costs[name]),
                            "response_bytes": response_sizes[name]}
                for name, world in worlds.items():
                    _, _, allocations = _timed_transaction(world, commands[name], traced=True)
                    row["modes"][name]["traced_transaction"] = allocations
                    _reject_check(world, commands[name])
                row.update(fidelity_equal=True, rejection_isolated=True, disk_replay_equal=True)
                rows.append(row)
                with (output/"raw.jsonl").open("a") as stream:
                    stream.write(json.dumps(row, sort_keys=True)+"\n")
                print(f"{metadata['phase']}: seed={seed} days={days} density={density} fidelity=equal", flush=True)
    if fingerprint() != start_source:
        (output/"failure.json").write_text(json.dumps({"error": "Runtime changed during execution",
            "before": start_source, "after": fingerprint(), "completed_cells": len(rows)}, indent=2)+"\n")
        raise RuntimeError("Runtime source changed during execution; raw development artifacts retained but no valid summary produced")
    result = {"cells": len(rows), "accepted_timed_transactions": len(rows)*REPEATS*4,
        "all_semantics_equal": all(row["fidelity_equal"] for row in rows), "conditions": summarize(rows)}
    (output/"summary.json").write_text(json.dumps(result, indent=2)+"\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("register", "pilot", "heldout"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--registration", type=Path, default=REGISTRATION)
    parser.add_argument("--smoke", action="store_true", help="One development cell; never heldout")
    args = parser.parse_args()
    if args.command == "register":
        print(register(args.registration)); return
    if args.output is None:
        parser.error("--output is required and must not already exist")
    if args.smoke and args.command != "pilot":
        parser.error("--smoke is development-only")
    options = {"seeds": (DEVELOPMENT_SEEDS[0],), "horizons": (1,), "densities": ("ordinary",)} if args.smoke else {}
    print(json.dumps(run(args.output, heldout=args.command == "heldout", registration_path=args.registration, **options), indent=2))


if __name__ == "__main__":
    main()
