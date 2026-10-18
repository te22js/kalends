"""Post-hoc physical-economy replay audit of the frozen eight-agent main panel.

This measures existing cash, orders, inspections, and commitment outcomes. It
does not change the model, tune a policy, or replace categorical task regret.
Every replay must match the recorded ledger and full decision stream exactly.
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
import time

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from kalends.actionbench.policy import AlwaysDeferPolicy, AlwaysVerifyPolicy
from kalends.bench.stats import paired, summarize
from kalends.city import CityConfig, CitySimulation

NON_STUDY_EXCEPTIONS = {
    "city_server.py": "HTTP adapter: later optional intervention-verification endpoint",
    "actionbench/plots.py": "post-run plot-label layout; not imported by study execution",
}


def physical_metrics(sim):
    events = sim.ledger.events
    initial = next(e.payload for e in events if e.payload["category"] == "city_initialized")
    purchases = [e for e in events if e.payload["category"] == "purchase"]
    inspections = [e for e in events if e.payload["category"] == "inspection_booked"]
    settlements = [e for e in events if e.payload["category"] == "commitment_settled"]
    reserve_decisions = {d["event_id"]: d for d in sim.decisions if d["action"] == "reserve"}
    assert len(reserve_decisions) == len(purchases)
    filled = sum(e.payload["quantity"] for e in purchases)
    zero = [e for e in purchases if e.payload["quantity"] == 0]
    zero_loss = [e for e in zero if any(parent in reserve_decisions and
                 reserve_decisions[parent]["actual_value"] == "disrupted" and
                 reserve_decisions[parent]["loss"] == 0 for parent in e.payload["parents"])]
    spent = -sum(sum(e.payload.get("cash_delta", {}).values()) for e in purchases)
    fees = -sum(sum(e.payload.get("cash_delta", {}).values()) for e in inspections)
    settlement_cash = sum(sum(e.payload.get("cash_delta", {}).values()) for e in settlements)
    delivered = sum(e.payload["quantity"] for e in settlements)
    missing = sum(e.payload["missing"] for e in settlements)
    commitments = [c for values in sim.economy.commitments.values() for c in values]
    missed = sum(c["status"] == "missed" for c in commitments)
    fulfilled = sum(c["status"] == "fulfilled" for c in commitments)
    total_initial = sum(initial["cash"].values())
    total_final = sum(sim.economy.cash.values())
    assert abs(total_initial - spent - fees + settlement_cash - total_final) < 1e-7
    assert sum(initial["inventory"].values()) + filled - delivered == sum(sim.economy.inventory.values())
    assert sum(e.payload.get("market_stock_delta", 0) for e in events) == sim.economy.market_stock
    assert abs(fees-1.5*len(inspections)) < 1e-7
    assert missed + fulfilled == len(settlements) == len(commitments)
    assert delivered + missing == sum(c["quantity"] for c in commitments)
    assert all(0 <= e.payload["quantity"] <= 3 for e in purchases)
    n_agents = sim.config.n_agents
    return {
        "initial_mean_cash": total_initial/n_agents,
        "final_mean_cash": total_final/n_agents,
        "mean_cash_change": (total_final-total_initial)/n_agents,
        "purchase_orders": len(purchases),
        # _purchase explicitly attempts three units. Events record the filled
        # quantity, so requested quantity is reconstructed from that fixed rule.
        "purchase_ordered_quantity": 3*len(purchases),
        "purchase_filled_quantity": filled,
        "purchase_fill_rate": filled/(3*len(purchases)) if purchases else 0.0,
        "zero_fill_orders": len(zero),
        "zero_fill_order_rate": len(zero)/len(purchases) if purchases else 0.0,
        "zero_loss_disrupted_zero_fill_orders": len(zero_loss),
        "purchase_spend": spent,
        "paid_inspections": len(inspections),
        "inspection_fees": fees,
        "commitments_total": len(commitments),
        "commitments_missed": missed,
        "commitments_fulfilled": fulfilled,
        "commitment_miss_rate": missed/len(commitments) if commitments else 0.0,
        "delivered_quantity": delivered,
        "missing_delivery_quantity": missing,
        "delivery_fill_rate": delivered/(delivered+missing) if delivered+missing else 0.0,
        "final_agent_inventory": sum(sim.economy.inventory.values()),
        "final_market_stock": sim.economy.market_stock,
        "categorical_regret": statistics.fmean(d["regret"] for d in sim.decisions),
        "n_decisions": len(sim.decisions),
    }


def aggregate(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["condition"]].append(row)
    systems = {}
    for condition, worlds in sorted(grouped.items()):
        seeds = defaultdict(list)
        for world in worlds:
            seeds[world["seed"]].append(world)
        metrics = {metric: summarize([statistics.fmean(r["metrics"][metric] for r in family_worlds)
                                     for _, family_worlds in sorted(seeds.items())])
                   for metric in worlds[0]["metrics"]}
        systems[condition] = {"n_worlds": len(worlds), "n_seeds": len(seeds), "metrics": metrics,
                              "pooled_counts": {metric: sum(r["metrics"][metric] for r in worlds)
                                                for metric in ("purchase_orders", "purchase_ordered_quantity",
                                                    "purchase_filled_quantity", "zero_fill_orders",
                                                    "zero_loss_disrupted_zero_fill_orders", "paid_inspections",
                                                    "commitments_missed", "commitments_fulfilled")}}
    comparisons = {}
    pairs = (("hybrid_guarded", "guarded_lineage2"),
             ("guarded_sources2", "guarded_lineage2"),
             ("always_verify", "hybrid_guarded"),
             ("always_defer", "hybrid_guarded"),
             ("always_verify", "guarded_lineage2"),
             ("always_defer", "always_verify"),
             ("bm25", "hybrid_guarded"))
    for left, right in pairs:
        x = {(r["seed"], r["family"]): r for r in grouped[left]}
        y = {(r["seed"], r["family"]): r for r in grouped[right]}
        assert set(x) == set(y)
        seeds = defaultdict(list)
        for key in sorted(x):
            seeds[key[0]].append(key)
        comparisons[f"{left}-minus-{right}"] = {
            metric: paired([statistics.fmean(x[k]["metrics"][metric] for k in keys)
                            for _, keys in sorted(seeds.items())],
                           [statistics.fmean(y[k]["metrics"][metric] for k in keys)
                            for _, keys in sorted(seeds.items())])
            for metric in ("categorical_regret", "final_mean_cash", "mean_cash_change",
                           "commitment_miss_rate", "delivery_fill_rate", "delivered_quantity",
                           "purchase_spend", "inspection_fees", "zero_fill_order_rate")}
    return {"systems": systems, "paired_comparisons_left_minus_right": comparisons}


def audit(artifact, output):
    artifact, output = Path(artifact), Path(output)
    if output.exists():
        raise ValueError("refusing to overwrite an audit; choose a fresh --out path")
    config = json.loads((artifact/"config.json").read_text())
    summary = json.loads((artifact/"summary.json").read_text())
    mismatches = []
    for name, expected in config["source_hashes"].items():
        observed = hashlib.sha256((REPO/"kalends"/name).read_bytes()).hexdigest()
        if observed != expected:
            if name not in NON_STUDY_EXCEPTIONS:
                raise ValueError(f"studied source hash changed: {name}")
            mismatches.append({"file": name, "expected": expected, "observed": observed,
                               "exception": NON_STUDY_EXCEPTIONS[name]})
    assert config["seeds"] == list(range(1000, 1030))
    assert len(config["conditions"]) == 11 and len(config["families"]) == 4
    started = time.perf_counter()
    rows = []
    seen = set()
    last_seed = None
    with gzip.open(artifact/"raw.jsonl.gz", "rt") as stream:
        for line in stream:
            recorded = json.loads(line)
            if recorded["population"] != 8:
                continue
            key = (recorded["seed"], recorded["family"], recorded["condition"])
            assert key not in seen
            seen.add(key)
            condition = recorded["condition"]
            factory = None
            if condition == "always_defer":
                factory = lambda *_: AlwaysDeferPolicy()
            elif condition == "always_verify":
                factory = lambda *_: AlwaysVerifyPolicy()
            sim = CitySimulation(CityConfig(**recorded["config"]), policy_factory=factory).run()
            assert sim.ledger.content_hash() == recorded["ledger_hash"], key
            assert sim.decisions == recorded["decisions"], key
            semantic = {"config": asdict(sim.config), "condition": condition,
                        "ledger_hash": sim.ledger.content_hash(), "decisions": sim.decisions}
            semantic_hash = hashlib.sha256(json.dumps(semantic, sort_keys=True).encode()).hexdigest()
            assert semantic_hash == recorded["semantic_hash"], key
            rows.append({"seed": recorded["seed"], "family": recorded["family"],
                         "population": 8, "condition": condition, "config": recorded["config"],
                         "recorded_semantic_hash": semantic_hash, "ledger_hash": recorded["ledger_hash"],
                         "replay_exact": True, "metrics": physical_metrics(sim)})
            if recorded["seed"] != last_seed:
                if last_seed is not None:
                    print(f"audited seed {last_seed}; {len(rows)-1} worlds", flush=True)
                last_seed = recorded["seed"]
    expected_keys = {(seed, family, condition) for seed in config["seeds"]
                     for family in config["families"] for condition in config["conditions"]}
    assert seen == expected_keys and len(rows) == 1320
    print(f"audited seed {last_seed}; {len(rows)} worlds", flush=True)
    report = {
        "status": "complete", "analysis_type": "post-hoc exploratory physical economy replay audit",
        "input_artifact": str(artifact), "population": 8, "n_worlds": len(rows),
        "n_seeds": 30, "source_config": config, "source_hash_exceptions": mismatches,
        "all_ledger_and_full_decision_replays_exact": True,
        "conservation_checks": "cash flow, agent inventory, market stock, inspection fees, and settlement quantities passed in every replay",
        "independent_unit": "paired seed; four family-world rates averaged within seed",
        "ci_method": "95% approximate t intervals using existing stats helper; no multiplicity adjustment",
        "definitions": {
            "cash": "actual final nominal cash and change from initial cash, per agent; not a complete welfare measure",
            "ordered_quantity": "three units per actual purchase event, reconstructed from the fixed _purchase rule",
            "filled_quantity": "actual purchase-event quantity after stock and affordability constraints",
            "zero_fill_order_rate": "zero-quantity purchase events / purchase events; zero for no orders",
            "paid_inspections": "inspection_booked events, including terminal requests without a later inspection",
            "commitment_miss_rate": "commitments with status missed / all commitments; partial delivery counts missed",
            "delivery_fill_rate": "actually delivered units / required commitment units",
            "categorical_regret": "existing reserve-available=2, defer-disrupted=6, verify=1.5 loss; not replaced or retuned",
        },
        "limitations": ["same held-out worlds reused after observing categorical results; exploratory",
                        "nominal cash excludes the value of remaining grain and nonfinancial objectives",
                        "policy changes later decision eligibility; purchase and inspection counts may differ",
                        "worlds with no purchase orders contribute zero to order-rate means",
                        "no policy, scenario, cost, source artifact, or original result changed",
                        "elapsed audit time is not a performance benchmark"],
        "elapsed_audit_seconds": time.perf_counter()-started,
        **aggregate(rows), "worlds": rows,
        "input_summary_worlds": summary["n_worlds"],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as target:
        json.dump(report, target, indent=2, allow_nan=False)
        target.write("\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", type=Path, default=REPO/"results/fork_city/heldout")
    parser.add_argument("--out", type=Path, default=REPO/"results/fork_city/economy_audit.json")
    args = parser.parse_args()
    report = audit(args.artifact, args.out)
    print(f"Saved {report['n_worlds']} exact replays to {args.out}", flush=True)


if __name__ == "__main__":
    main()
