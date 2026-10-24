"""Independent arithmetic over raw execution receipts plus controlled probes."""
import argparse
from dataclasses import asdict, replace
import gzip
import json
from pathlib import Path

from kalends.next_phase import diagnostic as study


def load(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads((args.results / "summary.json").read_text())
    files = sorted((args.results / "raw").glob("*.json.gz"))
    errors = []
    for path in files:
        row = load(path)
        ledger = row["ledger"]
        registers = [json.loads(e["payload"]["value"]) for e in ledger if e["payload"].get("prop") == ["experience", "goal_status"]]
        outcomes = [json.loads(e["payload"]["value"]) for e in ledger if e["payload"].get("category") == "allocation_settled"]
        categories = [e["payload"].get("category") for e in ledger]
        checks = {
            "contiguous_ids": [e["event_id"] for e in ledger] == list(range(len(ledger))),
            "chain_from_ledger": all(g["status"] == "completed" for g in registers[-1].values()) == row["chain_complete"],
            "kept_from_receipts": categories.count("promise_kept") == row["metrics"]["promises_kept"],
            "missed_from_receipts": categories.count("promise_missed") == row["metrics"]["promises_missed"],
            "paid_rechecks": categories.count("inspection_paid") == row["metrics"]["credits_spent"],
            "executed_units": sum(sum(o["executed"].values()) for o in outcomes) == row["metrics"]["executed_units"],
            "credit_conservation": row["metrics"]["credit_total"] == row["metrics"]["initial_credit_total"] == 37,
            "source_ids": all(i in {e["event_id"] for e in row["admitted_stream"]} for t in row["trace"] for i in t["decision"]["evidence_ids"]),
            "session_restores": len(row["session_restores"]) == 4 and all(s["exact"] for s in row["session_restores"]),
            "accessible_cap": row["arm"] == "admissible_history" or all(len(study.canonical(s["snapshot"]).encode()) <= study.STATE_BYTES for s in row["session_restores"]),
            "raw_hash": row["scientific_hash"] == study.digest({k: v for k, v in row.items() if k not in {"wall_seconds", "scientific_hash"}}),
        }
        errors.extend({"file": path.name, "check": name} for name, ok in checks.items() if not ok)
    if len(files) != summary["worlds"]:
        errors.append({"check": "summary_world_count", "files": len(files), "summary": summary["worlds"]})

    out = args.results / "controls"
    out.mkdir(exist_ok=False)
    base = replace(study.DEV[0], distractors=0)
    specs = [
        ("history", base, "admissible_history", {}),
        ("relevant_record_removed", base, "admissible_history", {"remove_report": True}),
        ("irrelevant_distractors", replace(base, distractors=24), "admissible_history", {}),
        ("earlier_fragile_evidence", replace(base, initial="fragile"), "admissible_history", {}),
        ("candidate", study.DEV[0], "dependency_retention", {}),
        ("legacy_plan_erased", study.DEV[0], "dependency_retention", {"drop_legacy_plans": True}),
    ]
    controls = {}
    for name, spec, arm, kwargs in specs:
        row = study.run_case(spec, 200, arm, **kwargs)
        (out / f"{name}.json.gz").write_bytes(gzip.compress((study.canonical(row) + "\n").encode(), mtime=0))
        controls[name] = {k: row[k] for k in ("chain_complete", "decisions", "final_ledger_hash", "scientific_hash")}

    # A literal public current observation gives every arm the same condition.
    # This one-round instrument is kept separate from the primary chain study.
    public_control = []
    for arm in study.ARMS:
        world = study.make_world(base, 200)
        controller = study.ChainController(arm)
        controller.mark_report()
        controller.commit(world)
        world.advance_to(99)
        event = world.emit("condition", "A public current instrument reading is posted", ("Player", *study.old.TEAMS),
                           scope="public", prop=["observatory", "condition"], value="fragile")
        own = study.verified_ingress(world, world.player_stream)
        controller.admit(own, world.minute)
        decision, trace = controller.select(world, [own[-1]])
        receipt = controller.allocate(world, decision)
        world.advance_to(1439)
        public_control.append({"arm": arm, "public_evidence_id": event.event_id, "decision": decision,
                               "actual_receipt_id": receipt.event_id, "prerequisite_completed": world.get("goal_status")["prerequisite"]["status"] == "completed",
                               "trace": trace, "ledger": world.ledger.to_json()})
    (out / "public_observation_control.json").write_text(json.dumps(public_control, indent=2) + "\n")

    # Changed earlier commitments are current institutional truth. They must not
    # require a hidden episodic memory to be noticed by the controller.
    world = study.make_world(base, 200)
    controller = study.ChainController("v3_hybrid")
    controller.mark_report()
    changed = world.execute({"action": "commit", "actor": "Player", "recipient": "team_c", "quantity": 2})
    controller.plan.update(phase="review_after_interruption")
    world.advance_to(100)
    try:
        controller.select(world, [])
        public_commitment = {"detected": False}
    except ValueError as error:
        public_commitment = {"detected": True, "reason": str(error), "receipt": changed.to_dict(),
                             "current_register": world.get("promises:0")}

    result = {"raw_worlds_checked": len(files), "arithmetic_errors": errors, "controls": controls,
              "record_removal_changes_completion": controls["history"]["chain_complete"] and not controls["relevant_record_removed"]["chain_complete"],
              "irrelevant_distractor_invariance": controls["history"]["decisions"] == controls["irrelevant_distractors"]["decisions"],
              "legacy_plan_ablation_ties": controls["candidate"]["final_ledger_hash"] == controls["legacy_plan_erased"]["final_ledger_hash"],
              "public_observation_all_complete": all(r["prerequisite_completed"] for r in public_control),
              "changed_commitment_control": public_commitment,
              "interpretation": "Arithmetic independently recounted from actual ledger effects; controller probes are authored internal controls, not independent replication."}
    (args.results / "arithmetic_controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if errors:
        raise SystemExit("raw arithmetic check failed")


if __name__ == "__main__":
    main()
