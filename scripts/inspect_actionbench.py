"""Read final ActionBench artifacts and audit rates, pairs, and decision cases.

Does not modify experiments or choose a policy. Examples are descriptive cases,
not additional independent samples. Optional replay checks the current source
against the frozen config hashes before recreating selected small worlds.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import sys

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
# This HTTP adapter is not imported by CitySimulation or the study runner.
# Its later optional-necessity endpoint is disclosed rather than silently
# accepting a hash change in an engine/memory/evaluator dependency.
ADAPTER_ONLY_HASH_ALLOWLIST = {"city_server.py"}
# Plot label layout changed after the run; the study runner does not import it.
ANALYSIS_ONLY_HASH_ALLOWLIST = {"actionbench/plots.py"}


def rates(decisions):
    n = len(decisions)
    reserves = [d for d in decisions if d["action"] == "reserve"]
    qa = [d for d in decisions if "qa_correct" in d]
    wrong = lambda d: (d["action"] == "reserve" and d["actual_value"] == "available" or
                       d["action"] == "defer" and d["actual_value"] == "disrupted")
    return {
        "decision_regret": statistics.fmean(d["loss"] for d in decisions) if n else 0.0,
        "action_error_rate": sum(wrong(d) for d in decisions) / n if n else 0.0,
        "autonomy": len(reserves) / n if n else 0.0,
        "selective_risk": sum(wrong(d) for d in reserves) / len(reserves) if reserves else 0.0,
        "qa_accuracy": sum(d["qa_correct"] for d in qa) / len(qa) if qa else 0.0,
        "boundary_violation_rate": sum(d["boundary_violation"] for d in decisions) / n if n else 0.0,
    }


def paired_interval(differences):
    # Same rounded critical-value lookup as the declared artifact method;
    # independently recompute the means/differences from raw decision records.
    from kalends.bench.stats import t_critical
    n = len(differences)
    mean = statistics.fmean(differences)
    half = t_critical(n-1) * statistics.stdev(differences) / n**0.5 if n > 1 else 0.0
    return {"n_seeds": n, "mean_difference": mean, "ci95": [mean-half, mean+half]}


def case(row, decision):
    return {"seed": row["seed"], "family": row["family"], "population": row["population"],
            "condition": row["condition"], "ledger_hash": row["ledger_hash"],
            "decision": decision}


def inspect(path, replay=False):
    path = Path(path)
    if not (path / "summary.json").exists():
        raise ValueError(f"{path}: summary.json absent; do not read an unfinished gzip stream")
    config = json.loads((path / "config.json").read_text())
    summary = json.loads((path / "summary.json").read_text())
    with gzip.open(path / "raw.jsonl.gz", "rt") as stream:
        rows = [json.loads(line) for line in stream]
    keys = [(r["seed"], r["family"], r["population"], r["condition"]) for r in rows]
    expected = len(config["seeds"]) * len(config["families"]) * len(config["populations"]) * len(config["conditions"])
    assert len(rows) == expected == len(set(keys)) == summary["n_worlds"]
    assert sum(len(r["decisions"]) for r in rows) == summary["n_decisions"]
    groups = defaultdict(dict)
    source_mismatches = [name for name, digest in config["source_hashes"].items()
                         if hashlib.sha256((REPO / "kalends" / name).read_bytes()).hexdigest() != digest]
    examples = {}
    counts = defaultdict(int)
    for row in rows:
        measured = rates(row["decisions"])
        for metric, value in measured.items():
            assert abs(value-row["metrics"][metric]) < 1e-12, (row["condition"], metric)
        groups[(row["population"], row["condition"])][(row["seed"], row["family"])] = row
        for decision in row["decisions"]:
            if decision.get("qa_correct") and decision["predicted_value"] != decision["actual_value"]:
                counts["local_qa_correct_world_wrong"] += 1
                if decision["loss"] > 0:
                    counts["local_qa_correct_positive_loss"] += 1
                    if row["condition"] == "structured" and row["population"] == 8:
                        examples.setdefault("local_qa_correct_but_costly", case(row, decision))
            if (decision.get("qa_correct") is False and decision["loss"] == 0 and
                    decision["predicted_value"] == decision["actual_value"]):
                counts["local_qa_wrong_world_right_zero_loss"] += 1
                if row["population"] == 8:
                    examples.setdefault("local_qa_wrong_but_world_right", case(row, decision))
            if decision["boundary_violation"] and row["population"] == 8:
                examples.setdefault("boundary_violation", case(row, decision))
    pairs = {}
    for population in config["populations"]:
        for left_name, right_name in (("hybrid", "hybrid_guarded"),
                                      ("guarded_sources2", "guarded_lineage2"),
                                      ("hybrid_guarded", "guarded_lineage2")):
            left, right = groups.get((population, left_name)), groups.get((population, right_name))
            if not left or not right:
                continue
            shared = sorted(set(left) & set(right))
            by_seed = defaultdict(list)
            for key in shared:
                by_seed[key[0]].append(key)
            result = {}
            for metric in ("decision_regret", "action_error_rate", "autonomy", "qa_accuracy", "selective_risk"):
                diffs = [statistics.fmean(rates(left[k]["decisions"])[metric] - rates(right[k]["decisions"])[metric]
                                         for k in family_keys)
                         for _, family_keys in sorted(by_seed.items())]
                result[metric] = paired_interval(diffs)
            pairs[f"{population}/{left_name}-minus-{right_name}"] = result
            if left_name == "hybrid" and population == 8:
                for key in shared:
                    right_decisions = {(d["tick"], d["agent"]): d for d in right[key]["decisions"]}
                    # The first action difference in a world avoids attributing
                    # a later cascade solely to the current memory response.
                    for x in left[key]["decisions"]:
                        y = right_decisions.get((x["tick"], x["agent"]))
                        if y is not None and x["action"] != y["action"]:
                            if (x["action"] == "reserve" and y["action"] == "defer" and
                                    x["actual_value"] == y["actual_value"] == "disrupted" and
                                    x["loss"] == 0 and y["loss"] == 6):
                                examples.setdefault("guarded_forgetting_misses_action", {
                                    "hybrid": case(left[key], x), "guarded": case(right[key], y)})
                            break
            if left_name == "guarded_sources2" and population == 8:
                for key in shared:
                    a = {(d["tick"], d["agent"]): d for d in left[key]["decisions"]}
                    b = {(d["tick"], d["agent"]): d for d in right[key]["decisions"]}
                    for decision_key in sorted(set(a) & set(b)):
                        x, y = a[decision_key], b[decision_key]
                        # Match the evidence view as well as seed/family/agent/tick.
                        if (x["action"] == "reserve" and y["action"] == "verify" and
                                x["predicted_value"] == y["predicted_value"] == "disrupted" and
                                x["evidence_ids"] == y["evidence_ids"] and
                                x["root_count"] == y["root_count"] == 1 and
                                x["source_count"] == y["source_count"] >= 2):
                            label = "lineage_withholds_useful_action" if x["actual_value"] == "disrupted" else "lineage_blocks_costly_action"
                            examples.setdefault(label, {"source_count": case(left[key], x), "lineage": case(right[key], y)})
    if replay:
        core_mismatches = (set(source_mismatches) - ADAPTER_ONLY_HASH_ALLOWLIST -
                           ANALYSIS_ONLY_HASH_ALLOWLIST)
        assert not core_mismatches, sorted(core_mismatches)
        from kalends.city import CityConfig, CitySimulation
        cache = {}
        def enrich(example):
            key = (example["seed"], example["family"], example["population"], example["condition"])
            row = next(r for r in rows if (r["seed"], r["family"], r["population"], r["condition"]) == key)
            if key not in cache:
                sim = CitySimulation(CityConfig(**row["config"])).run()
                assert sim.ledger.content_hash() == row["ledger_hash"], key
                assert sim.decisions == row["decisions"], key
                cache[key] = sim
            sim = cache[key]
            ids = set(example["decision"]["retrieved_ids"])
            example["retrieved_experiences"] = [asdict(e) for e in sim.experiences[example["decision"]["agent"]]
                                                if e.event_id in ids]
            example["replay_verified"] = True
        for example in examples.values():
            if "decision" in example:
                enrich(example)
            else:
                for item in example.values():
                    enrich(item)
    return {"artifact": str(path), "n_worlds": len(rows), "n_decisions": summary["n_decisions"],
            "current_source_hash_mismatches": source_mismatches,
            "adapter_only_mismatches_allowed_for_replay": sorted(set(source_mismatches) & ADAPTER_ONLY_HASH_ALLOWLIST),
            "analysis_only_mismatches_allowed_for_replay": sorted(set(source_mismatches) & ANALYSIS_ONLY_HASH_ALLOWLIST),
            "raw_rate_checks_passed": True,
            "paired_differences_left_minus_right": pairs,
            "descriptive_decision_counts": dict(counts),
            "examples": examples,
            "performance_warning": "Concurrent suite timings are not isolated performance measurements."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifacts", nargs="+", type=Path)
    parser.add_argument("--replay", action="store_true", help="replay selected eight-agent case worlds after source-hash verification")
    args = parser.parse_args()
    print(json.dumps([inspect(path, args.replay) for path in args.artifacts], indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
