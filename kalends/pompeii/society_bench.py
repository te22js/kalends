"""Track B: matched information-policy experiments in the playable Pompeii world.

Development may run immediately. Heldout execution requires a source/protocol
registration made only after the external model freeze. No alternate toy model,
adaptive player, language-model call, or server session is used.
"""
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
REGISTRATION = ROOT / "results/pompeii/society_preregistration.json"
DEVELOPMENT_SEEDS = tuple(range(31000, 31010))
HELDOUT_SEEDS = tuple(range(71000, 71030))
HORIZONS = (7, 30)
CONDITIONS = {
    "baseline": {"information_policy": "cautious", "communication": True, "memory_capacity": 32},
    "credulous": {"information_policy": "credulous", "communication": True, "memory_capacity": 32},
    "no_communication": {"information_policy": "cautious", "communication": False, "memory_capacity": 32},
    "capacity8": {"information_policy": "cautious", "communication": True, "memory_capacity": 8},
}
PRIMARY = ("delivery_fill_rate", "player_origin_recipients", "retained_player_origin_recipients")
SCALAR_METRICS = PRIMARY + (
    "work_delivered", "work_required", "work_missed", "citizen_cash_change", "citizen_cash_postprefix",
    "player_cash_change", "player_cash_postprefix", "inspection_fees", "npc_inspection_fees", "inspections",
    "decisions", "decision_buy", "decision_inspect", "decision_defer", "decision_wait", "purchase_filled", "purchase_attempted",
    "reports", "accepted_reports", "player_origin_reports", "player_origin_relays", "accepted_player_origin_relays",
    "retained_direct_claim_recipients", "false_claim_contradicted", "false_claim_confirmed", "false_claim_unverified",
    "mean_trust_player", "felix_trust_player", "lucius_trust_player", "ordinary_memory_records", "consolidated_memory_records",
    "player_commitments_missed", "player_commitments_fulfilled", "player_commitments_open", "player_flour_delivered",
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def fingerprint():
    # Conservatively freeze all Python model/runner dependencies, including
    # imported base economy code, rather than guessing a transitive import set.
    files = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted((ROOT / "kalends").rglob("*.py"))}
    return {"sha256": digest(files), "files": files}


def registration():
    return {
        "version": 1, "track": "B: six-citizen actual-world information mechanisms",
        "development_seeds": list(DEVELOPMENT_SEEDS), "heldout_seeds": list(HELDOUT_SEEDS),
        "conditions": CONDITIONS, "contrasts": "each nonbaseline condition minus baseline, separately; no factorial interaction claim",
        "horizons_elapsed_days": list(HORIZONS), "minutes_per_day": 1440, "world_horizon_cap_days": 60,
        "population": 6, "player_policy": "fixed prefix then no player actions",
        "prefix": ["move to bakery", "accept Felix delivery", "claim disrupted to Felix",
                   "move to street x=930 y=415", "claim disrupted to Marcus", "move to household", "accept Lucius patronage"],
        "prefix_checks": "both claims must contradict actual available supply at utterance; all moves/actions use actual proximity-validated methods; no evaluator information supplied to NPCs",
        "phase_control": "each fresh world runs prefix, then advances exactly 7 or 30 elapsed days from prefix end with compress; same checkpoint partition at elapsed day1,7,30 when within horizon; stop at prefix minute plus days*1440; no adaptive correction/service/delivery",
        "communication_scope": "disables scheduled NPC gossip only; fixed Player claims remain enabled in every condition",
        "memory_scope": "ordinary FIFO capacity8 versus32; same bounded eight-record consolidation in all conditions, plus durable accounts/trust/commitments",
        "primary_metrics": list(PRIMARY), "all_scalar_metrics": list(SCALAR_METRICS),
        "physical_work": "actual daily_work/bread_ready delivered/required for Felix, Sabina, Lucius; three other citizens have no modeled recurring flour output",
        "propagation": "unique NPC listeners of actual Player-origin reports, including two fixed recipients; relays exclude direct Player speech; observer Player is one source, never independent confirmations",
        "retention": "retained told records rooted in either fixed claim, not global ledger presence; direct claim retention and ordinary/consolidated stores also reported",
        "assessment": "actual relationship assessment whose parents include a fixed direct-claim event; contradicted/confirmed/truthful_outdated/historically_unverified recorded separately; missed commitments are separate",
        "uncertainty": "descriptive paired-seed mean differences with 95% percentile bootstrap; 4000 resamples, random.Random(72831), ordered seed unit; indices99 and3899; no citizen/decision pseudoreplication; no multiplicity-adjusted confirmatory significance claim",
        "scope": "bounded six-character deterministic policies; no human or ancient population estimate, no universal information-benefit claim; seed varies dispatches/routines, not citizen identities",
        "source": fingerprint(),
    }


def player_prefix(world):
    """Only legitimate actions, with evaluator checks that never alter the world."""
    receipts = []
    receipts.append(world.move(location="bakery"))
    promise = world.interact("accept_delivery", "Felix"); receipts.append(promise)
    if world.state.facts["grain.supply"] != "available":
        raise AssertionError("fixed false-claim phase no longer has available supply")
    first = world.claim("Felix", "disrupted"); receipts.append(first)
    receipts.append(world.move(x=930, y=415))
    if world.state.facts["grain.supply"] != "available":
        raise AssertionError("second fixed claim must still contradict available supply")
    second = world.claim("Marcus", "disrupted"); receipts.append(second)
    receipts.append(world.move(location="household"))
    patronage = world.interact("patronage", "Lucius"); receipts.append(patronage)
    return {"minute": world.minute, "claim_ids": [first["event_id"], second["event_id"]],
            "promise_id": promise["event_id"], "patronage_id": patronage["event_id"],
            "cash": dict(world.economy.cash), "receipts": receipts,
            "ledger_hash": world.ledger.content_hash()}


def _origin_report(payload, claim_ids):
    return payload.get("root_event") in claim_ids and payload.get("root_observer") == "Player"


def retention(world, prefix):
    claims = set(prefix["claim_ids"])
    direct, origin = [], []
    agents = {}
    for agent in world.agent_ids:
        remembered = world.remembered(agent)
        direct_ids = sorted(e.event_id for e in remembered if e.event_id in claims)
        origin_ids = sorted(e.event_id for e in remembered if e.kind == "told" and
                            e.claimed_origin_event in claims and e.claimed_origin_observer == "Player")
        if direct_ids: direct.append(agent)
        if origin_ids: origin.append(agent)
        agents[agent] = {"ordinary": len(world.memories[agent]), "consolidated": len(world.consolidated[agent]),
                         "retained_union": len(remembered), "direct_claim_ids": direct_ids,
                         "player_origin_ids": origin_ids, "knowledge": world.knowledge(agent)}
    return {"minute": world.minute, "direct_claim_recipients": direct, "player_origin_recipients": origin, "agents": agents}


def measure(world, prefix):
    events = world.ledger.events
    category = lambda name: [e for e in events if e.payload.get("category") == name]
    work = category("daily_work") + category("bread_ready")
    claims = set(prefix["claim_ids"])
    reports = category("report")
    origins = [e for e in reports if _origin_report(e.payload, claims)]
    relays = [e for e in origins if e.payload["speaker"] != "Player"]
    assessments = [e for e in category("relationship") if e.payload.get("assessment") and
                   claims.intersection(e.payload.get("parents", []))]
    inspection_bookings = category("inspection_booked")
    retained = retention(world, prefix)
    trust = {a: world.state.trust.get((a,"Player"), .6) for a in world.agent_ids}
    commitments = world.economy.commitments["Player"]
    delivered = sum(e.payload["delivered"] for e in work)
    required = sum(e.payload["required"] for e in work)
    values = {
        "delivery_fill_rate": delivered / required if required else None,
        "work_delivered": delivered, "work_required": required, "work_missed": required-delivered,
        "citizen_cash_change": sum(world.economy.cash[a]-world._initial_cash[a] for a in world.agent_ids),
        "citizen_cash_postprefix": sum(world.economy.cash[a]-prefix["cash"][a] for a in world.agent_ids),
        "player_cash_change": world.economy.cash["Player"]-world._initial_cash["Player"],
        "player_cash_postprefix": world.economy.cash["Player"]-prefix["cash"]["Player"],
        "inspection_fees": sum(e.payload["fee"] for e in inspection_bookings),
        "npc_inspection_fees": sum(e.payload["fee"] for e in inspection_bookings if "Player" not in e.actors),
        "inspections": len(category("inspection")), "decisions": len(world.decisions),
        "purchase_filled": sum(e.payload["quantity"] for e in category("purchase")),
        "purchase_attempted": sum(e.payload["attempted"] for e in category("purchase")),
        "reports": len(reports), "accepted_reports": sum(e.payload["accepted"] for e in reports),
        "player_origin_reports": len(origins), "player_origin_relays": len(relays),
        "accepted_player_origin_relays": sum(e.payload["accepted"] for e in relays),
        "player_origin_recipients": len({e.payload["listener"] for e in origins}),
        "retained_player_origin_recipients": len(retained["player_origin_recipients"]),
        "retained_direct_claim_recipients": len(retained["direct_claim_recipients"]),
        "false_claim_contradicted": sum(e.payload["assessment"] == "contradicted" for e in assessments),
        "false_claim_confirmed": sum(e.payload["assessment"] in ("confirmed","truthful_outdated") for e in assessments),
        "false_claim_unverified": sum(e.payload["assessment"] == "historically_unverified" for e in assessments),
        "mean_trust_player": statistics.fmean(trust.values()), "felix_trust_player": trust["Felix"],
        "lucius_trust_player": trust["Lucius"], "ordinary_memory_records": sum(len(world.memories[a]) for a in world.agent_ids),
        "consolidated_memory_records": sum(len(world.consolidated[a]) for a in world.agent_ids),
        "player_flour_delivered": sum(e.payload["delivered"] for e in category("promise_settled")),
    }
    values.update({"decision_"+choice: sum(d["action"] == choice for d in world.decisions)
                   for choice in ("buy","inspect","defer","wait")})
    values.update({"player_commitments_"+status: sum(c["status"] == status for c in commitments)
                   for status in ("missed","fulfilled","open")})
    assert set(values) == set(SCALAR_METRICS)
    agents = {}
    for agent in world.agent_ids:
        settlements = [e for e in work if agent in e.actors]
        agents[agent] = {"cash": world.economy.cash[agent], "cash_change": world.economy.cash[agent]-world._initial_cash[agent],
                        "cash_postprefix": world.economy.cash[agent]-prefix["cash"][agent], "inventory": world.economy.inventory[agent],
                        "work_delivered": sum(e.payload["delivered"] for e in settlements),
                        "work_required": sum(e.payload["required"] for e in settlements), "trust_player": trust[agent],
                        "commitments": world.economy.commitments[agent], **retained["agents"][agent]}
    return {"metrics": values, "agents": agents, "retention": retained,
            "player_commitments": commitments, "relationships": [[a,b,v] for (a,b),v in sorted(world.state.trust.items())],
            "origin_reports": [e.to_dict() for e in origins], "claim_assessments": [e.to_dict() for e in assessments],
            "event_count": len(events), "ledger_hash": world.ledger.content_hash()}


def run_world(seed, days, condition):
    from .district import PompeiiConfig
    from .world import PompeiiWorld
    if type(seed) is not int or days not in HORIZONS or condition not in CONDITIONS:
        raise ValueError("invalid society benchmark cell")
    config = PompeiiConfig(seed=seed, horizon_days=60, **CONDITIONS[condition])
    world = PompeiiWorld(config=config)
    prefix = player_prefix(world)
    checkpoints = {"prefix": retention(world, prefix)}
    for checkpoint in (1, 7, 30):
        if checkpoint > days: break
        target = prefix["minute"] + checkpoint*1440
        world.advance(target-world.minute, "compress")
        checkpoints["day"+str(checkpoint)] = retention(world, prefix)
    assert world.minute == prefix["minute"]+days*1440
    return {"seed": seed, "days": days, "condition": condition, "config": asdict(config),
            "prefix": prefix, "end_minute": world.minute, "checkpoints": checkpoints, **measure(world, prefix)}


def interval(values):
    if not values: return None
    rng = random.Random(72831)
    samples = sorted(statistics.fmean(rng.choices(values,k=len(values))) for _ in range(4000))
    return {"mean": statistics.fmean(values), "median": statistics.median(values),
            "ci95_mean": [samples[99], samples[3899]], "n_independent_seeds": len(values)}


def summarize(rows):
    lookup = {(r["seed"],r["days"],r["condition"]):r for r in rows}
    cells, contrasts = [], []
    for days in HORIZONS:
        seeds = sorted(r["seed"] for r in rows if r["days"] == days and r["condition"] == "baseline")
        for condition in CONDITIONS:
            selected = [lookup[(seed,days,condition)] for seed in seeds]
            cells.append({"days": days,"condition": condition,"metrics": {
                metric: interval([r["metrics"][metric] for r in selected]) for metric in SCALAR_METRICS}})
            if condition != "baseline":
                contrasts.append({"days": days,"condition_minus_baseline": condition,
                    "paired_differences": {metric: interval([lookup[(seed,days,condition)]["metrics"][metric]-
                        lookup[(seed,days,"baseline")]["metrics"][metric] for seed in seeds]) for metric in SCALAR_METRICS}})
    return {"worlds":len(rows),"cells":cells,"contrasts":contrasts,
            "independent_units":"seeds; repeated horizons/conditions/citizens are matched dependent observations",
            "primary_metrics":list(PRIMARY), "inference":"descriptive intervals; no adjusted confirmatory significance tests"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", action="store_true", help="only after explicit external model freeze")
    parser.add_argument("--freeze-confirmed", action="store_true", help="attest explicit model-owner freeze before registering")
    parser.add_argument("--phase", choices=("development","heldout"), default="development")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    if args.register:
        if not args.freeze_confirmed:
            raise SystemExit("Explicit model-owner freeze is required before registration")
        REGISTRATION.parent.mkdir(parents=True,exist_ok=True)
        with REGISTRATION.open("x") as target:
            target.write(json.dumps(registration(),indent=2)+"\n")
        print(REGISTRATION)
        return
    before = fingerprint()
    protocol = registration()
    if args.phase == "heldout":
        if not REGISTRATION.is_file():
            raise SystemExit("Register frozen source and protocol before heldout")
        if json.loads(REGISTRATION.read_text()) != protocol:
            raise SystemExit("Source/protocol changed after registration; heldout not started")
    output = args.out or ROOT / "results/pompeii" / ("society_"+args.phase)
    if output.exists():
        raise SystemExit("Refusing to overwrite artifact path: "+str(output))
    output.mkdir(parents=True)
    manifest = {"phase":args.phase,"protocol":protocol,"python":platform.python_version(),
                "platform":platform.platform(),"source":before,
                "commit":subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
                "registration_sha256":hashlib.sha256(REGISTRATION.read_bytes()).hexdigest() if args.phase == "heldout" else None}
    (output/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    seeds = DEVELOPMENT_SEEDS if args.phase == "development" else HELDOUT_SEEDS
    rows,started = [],time.perf_counter()
    with (output/"worlds.jsonl").open("x") as raw, (output/"metrics.csv").open("x",newline="") as flat:
        writer=csv.DictWriter(flat,fieldnames=["seed","days","condition","prefix_minute","end_minute",*SCALAR_METRICS])
        writer.writeheader()
        for seed in seeds:
            for days in HORIZONS:
                prefixes=[]
                for condition in CONDITIONS:
                    row=run_world(seed,days,condition)
                    prefixes.append(row["prefix"])
                    raw.write(canonical(row)+"\n");raw.flush()
                    writer.writerow({"seed":seed,"days":days,"condition":condition,"prefix_minute":row["prefix"]["minute"],
                                     "end_minute":row["end_minute"],**row["metrics"]});flat.flush()
                    rows.append(row)
                # Prefix has not yet reached any policy-dependent procurement.
                if any(p != prefixes[0] for p in prefixes[1:]):
                    raise RuntimeError("matched prefix diverged before intervention phase")
                print(f"{args.phase} seed={seed} days={days}: {len(rows)} worlds",flush=True)
    summary=summarize(rows)
    summary.update(source_unchanged=fingerprint()==before,wall_seconds=time.perf_counter()-started,
                   raw_sha256=hashlib.sha256((output/"worlds.jsonl").read_bytes()).hexdigest(),
                   csv_sha256=hashlib.sha256((output/"metrics.csv").read_bytes()).hexdigest())
    (output/"summary.json").write_text(json.dumps(summary,indent=2,allow_nan=False)+"\n")
    if not summary["source_unchanged"]:
        raise SystemExit("Source changed during run; preserved results are not a frozen study")


if __name__ == "__main__":
    main()
