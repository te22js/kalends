#!/usr/bin/env python3
"""Compare the frozen Genesis study engine with post-study product instrumentation.

Uses reserved development configurations only. Each implementation runs in an
isolated Python process. The frozen package is read from git archive, never by
checking out or rewriting the working tree. Existing reports are not overwritten.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
from dataclasses import asdict
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
FROZEN_REF = "a1010fc"
ACCOUNTING_FIELDS = (
    "accounting_checkpoint", "inventory_dependency_events", "cash_dependency_events",
    "procurement_decision_events", "inventory_before_settlement", "inventory_allocation",
    "dependency_scope",
)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def configurations():
    return [dict(seed=seed, n_agents=population, n_ticks=96, family=family,
                 memory="hybrid_guarded", gate=gate, threshold=2, capacity=32,
                 communication_depth=3, supply_mode="per_capita", allocation="seeded", role_policy=True)
            for seed in (20000, 20001) for family in ("stable", "reversal", "scarcity")
            for population in (8, 32) for gate in ("none", "lineage")]


def source_hashes(root):
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((root / "kalends" / "genesis").glob("*.py"))}


def worker(root):
    sys.path.insert(0, str(root))
    from kalends.genesis import GenesisConfig, GenesisSimulation
    import kalends.genesis.simulation as engine_module
    if not Path(engine_module.__file__).resolve().is_relative_to(root.resolve()):
        raise RuntimeError("worker imported a package outside its authorized source root")
    rows = []
    for index, config in enumerate(configurations()):
        sim = GenesisSimulation(GenesisConfig(**config)).run()
        participants = sim.agent_ids + ["Player"]
        retained = {agent: [asdict(e) for e in sim.remembered(agent)] for agent in participants}
        archives = {agent: [asdict(e) for e in sim.experiences[agent]] for agent in participants}
        world = {"tick": sim.state.tick, "facts": sim.state.facts,
                 "agent_locations": sim.state.agent_locations,
                 "trust": [[a, b, value] for (a, b), value in sorted(sim.state.trust.items())]}
        economy = {"cash": sim.economy.cash, "inventory": sim.economy.inventory,
                   "market_stock": sim.economy.market_stock, "price": sim.economy.price,
                   "commitments": sim.economy.commitments,
                   "relationships": [[a, b, value] for (a, b), value in sorted(sim.economy.relationships.items())]}
        ledger = sim.ledger.to_json()
        messages = [e for e in ledger if e["etype"] == "tell" or e["payload"].get("category") == "message_queued"]
        normalized = []
        instrumentation = Counter()
        settlements, parents_valid = 0, True
        for position, event in enumerate(ledger):
            parents = event["payload"].get("parents", [])
            parents_valid &= event["event_id"] == position and parents == sorted(set(parents)) and all(
                type(parent) is int and 0 <= parent < position for parent in parents)
            copy_event = dict(event, payload=dict(event["payload"]))
            if event["payload"].get("category") == "commitment_settled":
                settlements += 1
                # These configurations contain no player actions/agreements;
                # all frozen recurring citizen settlements have empty parents.
                if event["actors"] == ["Player"]:
                    raise RuntimeError("unexpected player agreement in the fixed compatibility grid")
                for field in ACCOUNTING_FIELDS:
                    if field in copy_event["payload"]:
                        instrumentation[field] += 1
                        del copy_event["payload"][field]
                copy_event["payload"]["parents"] = []
            normalized.append(copy_event)
        values = {"metrics": sim.metrics(), "decisions": sim.decisions,
                  "retained_memories": retained, "archival_experiences": archives,
                  "world_facts_positions_trust": world, "accounts_inventory_commitments": economy,
                  "preferences": sim.preferences, "pending_messages": sim.messages,
                  "queued_and_delivered_messages": messages}
        rows.append({"config": config, "components": {name: digest(value) for name, value in values.items()},
                     "metrics": values["metrics"], "event_count": len(ledger),
                     "decision_count": len(sim.decisions), "message_event_count": len(messages),
                     "pending_message_count": len(sim.messages),
                     "retained_counts": {a: len(v) for a, v in retained.items()},
                     "archive_counts": {a: len(v) for a, v in archives.items()},
                     "ledger_hash": sim.ledger.content_hash(), "normalized_ledger_hash": digest(normalized),
                     "settlement_count": settlements, "instrumentation_fields": dict(instrumentation),
                     "indexed_parents_valid": bool(parents_valid)})
        print(f"{root.name}: configuration {index + 1}/24 complete", file=sys.stderr, flush=True)
    print(json.dumps({"source_hashes": source_hashes(root), "records": rows}, allow_nan=False))


def archive_frozen(destination, commit):
    completed = subprocess.run(["git", "archive", "--format=tar", commit, "kalends"],
                               cwd=ROOT, check=True, capture_output=True)
    with tarfile.open(fileobj=io.BytesIO(completed.stdout), mode="r:") as archive:
        for member in archive.getmembers():
            name = PurePosixPath(member.name)
            if name.is_absolute() or ".." in name.parts or not name.parts or name.parts[0] != "kalends":
                raise ValueError("git archive contains an unexpected package path")
            if not (member.isfile() or member.isdir()):
                raise ValueError("git archive contains unsupported symbolic or special entries")
        archive.extractall(destination)


def run_worker(root, python):
    completed = subprocess.run([python, "-I", "-B", str(Path(__file__).resolve()),
                                "--worker-root", str(root)], cwd=ROOT,
                               stdout=subprocess.PIPE, text=True, check=True)
    return json.loads(completed.stdout)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "results/genesis/poststudy_compatibility.json")
    parser.add_argument("--python", default=sys.executable, help="same Python executable for both isolated workers")
    parser.add_argument("--worker-root", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker_root is not None:
        worker(args.worker_root.resolve())
        return
    if args.out.exists():
        parser.error("output already exists; choose a fresh --out path")
    commit = subprocess.run(["git", "rev-parse", FROZEN_REF + "^{commit}"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    before_hashes = source_hashes(ROOT)
    with tempfile.TemporaryDirectory(prefix="kalends-genesis-compatibility-") as temporary:
        frozen_root = Path(temporary) / "frozen"
        frozen_root.mkdir()
        archive_frozen(frozen_root, commit)
        frozen = run_worker(frozen_root, args.python)
        current = run_worker(ROOT, args.python)
    after_hashes = source_hashes(ROOT)
    source_stable = before_hashes == after_hashes == current["source_hashes"]
    comparisons, failures = [], []
    for old, new in zip(frozen["records"], current["records"]):
        checks = {name: old["components"][name] == new["components"][name] for name in old["components"]}
        checks.update({name: old[name] == new[name] for name in (
            "config", "event_count", "decision_count", "message_event_count", "pending_message_count",
            "retained_counts", "archive_counts", "settlement_count")})
        checks["only_declared_settlement_ledger_metadata_differs"] = (
            old["ledger_hash"] == old["normalized_ledger_hash"] == new["normalized_ledger_hash"])
        checks["all_parent_references_valid"] = old["indexed_parents_valid"] and new["indexed_parents_valid"]
        checks["all_settlements_instrumented"] = all(
            new["instrumentation_fields"].get(field) == new["settlement_count"] for field in ACCOUNTING_FIELDS)
        comparison = {"config": old["config"], "checks": checks, "passed": all(checks.values()),
                      "frozen": old, "current": new,
                      "ledger_hash_changed": old["ledger_hash"] != new["ledger_hash"]}
        comparisons.append(comparison)
        if not comparison["passed"]:
            failure = {"config": old["config"], "failed_checks": [name for name, passed in checks.items() if not passed]}
            failures.append(failure)
            print("COMPATIBILITY FAILURE: " + json.dumps(failure), file=sys.stderr, flush=True)
    if len(comparisons) != 24 or len(frozen["records"]) != 24 or len(current["records"]) != 24:
        failures.append({"failed_checks": ["expected exactly twenty-four configurations in each worker"]})
    if not source_stable:
        failures.append({"failed_checks": ["current source hashes changed during compatibility run"]})
    report = {"schema_version": 1, "status": "passed" if not failures else "failed",
              "frozen_commit": commit, "frozen_ref": FROZEN_REF,
              "frozen_source_hashes": frozen["source_hashes"], "current_source_hashes": after_hashes,
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "current_source_stable_during_check": source_stable,
              "configuration_count": len(comparisons), "paired_world_runs": 48,
              "seeds": [20000, 20001], "sample_scope": "reserved development configurations, not held-out reruns",
              "runtime": {"controller_python": platform.python_version(),
                          "worker_python_executable": args.python},
              "method": "Frozen package extracted with git archive to a temporary directory; each implementation imported and run in a separate isolated Python process; no working-tree checkout or installation.",
              "allowed_difference": {"event_category": "commitment_settled", "payload_fields": list(ACCOUNTING_FIELDS),
                                     "parents": "auditor-only accounting parent links; frozen recurring citizen parents were empty"},
              "normalization_scope": "Only the seven declared settlement metadata fields and settlement parent arrays are normalized. All other full ledger content must hash identically. Grid has no player agreements; those are covered by dedicated engine projection/ancestry tests.",
              "interpretation": "Exact development-grid compatibility evidence for recorded outcomes, decisions, bounded memories and state; not a proof across all configurations or a new held-out result. Full ledger hashes deliberately change under versioned accounting metadata.",
              "records": comparisons, "failures": failures}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(report, stream, indent=2, allow_nan=False); stream.write("\n")
    print(f"{report['status']}: {len(comparisons)} configuration pairs; saved {args.out}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
