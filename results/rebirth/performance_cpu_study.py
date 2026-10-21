"""Amended local study: exact temporary-session CPU costs, no disk journals.

The original I/O protocol failed twice with ENOSPC. This amendment is registered
before fresh seed execution and keeps all game Python unchanged. Its runner is
hashed in addition to the runtime. It establishes no saved-endpoint speedup.
"""
from __future__ import annotations
import argparse
import gc
import hashlib
import json
from pathlib import Path
import platform
import random
import shutil
import statistics
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from kalends_rebirth import benchmark as bench

SEEDS = tuple(range(84000, 84020))
REGISTER = ROOT / "results/rebirth/performance_cpu_preregistration.json"


def source():
    return {"runtime": bench.fingerprint(), "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def design():
    return {"version": 1, "amendment": "Two ENOSPC failures prevented completion of saved-session protocol; no timing effects reviewed. CPU/temporary-session scope registered before fresh seeds. No final I/O speedup or durability inference.",
        "seeds": list(SEEDS), "horizons_days": list(bench.HORIZONS), "densities": list(bench.DENSITIES),
        "population": 6, "memory_capacity": 32, "routes": list(bench.ROUTES),
        "prefix": "Same actual legal route/commission/service prefix as frozen benchmark; route=seed%4, kept/missed broker commission and household service alternate by integer(seed/4)%2;12 legitimate Marcus conversations/day in stress condition",
        "reference": "Same RebirthWorld/Session and exact scheduler, optimized=False original Ledger",
        "optimized": "Same world/Session, optimized=True immutable historical sharing and streaming hash",
        "primary": "Zero declared semantic mismatches, paired actual temporary RebirthSession.commit(move,location=street)+canonical HTTP response serialization latency",
        "timing": "One discarded actual-transaction warmup per mode/cell;five fresh actual sessions against unchanged prepared world per mode; deterministic balanced pair order by seed/horizon/repeat; gc.collect before timing; construction and fidelity checks excluded",
        "hash": "Standalone ledger revision hash measured separately after primary timing; never added to temporary-session endpoint gain",
        "write_tradeoff": "One paired actual opening/history construction timing, including new-event sealing/hash writes; exploratory throughput cost, not five-repeat latency estimate",
        "memory": "Separate traced actual temporary transaction; Python incremental allocation peak, not whole-world RAM or RSS; traced timing ignored",
        "replay": "Per mode/cell, accepted command list canonical-JSON roundtrip in RAM and actual RebirthSession._perform replay; final move and declared semantics compared. No file save/restart or crash durability test.",
        "rejection": "Actual session invalid off-street move must preserve original semantic state and accepted commands",
        "fidelity": bench.design()["fidelity"],
        "uncertainty": "Descriptive95% percentile bootstrap of paired-seed geometric mean ratios separately within horizon/density;2000resamples; seed is independent unit",
        "environment": "Single active development machine, no CPU isolation, APFS low-space pressure incident recorded. No rendering, HTTP transport, GPU or model inference benchmark.",
        "stop": "Any declared semantic mismatch aborts; source bytes checked before/after; no source edits, interim effect selection or optional stopping for effect size",
        "source": source()}


def register():
    REGISTER.parent.mkdir(parents=True, exist_ok=True)
    with REGISTER.open("x") as stream:
        stream.write(json.dumps(design(), indent=2)+"\n")
    print(REGISTER)


def summary(rows):
    result=[]
    for days in bench.HORIZONS:
        for density in bench.DENSITIES:
            cells=[row for row in rows if row["days"]==days and row["density"]==density]
            record={"days":days,"density":density,"seeds":len(cells),"all_semantics_equal":all(row["fidelity_equal"] for row in cells),
                "events_range":[min(row["modes"]["reference"]["build"]["events"] for row in cells),max(row["modes"]["reference"]["build"]["events"] for row in cells)]}
            for field,measure in (("memory_transaction","median_ms"),("history_speed_ratio","history_ms"),("transaction_peak_ratio","peak_bytes")):
                container="build" if field=="history_speed_ratio" else "traced_transaction" if field=="transaction_peak_ratio" else "memory_transaction"
                ratios=[row["modes"]["reference"][container][measure]/row["modes"]["optimized"][container][measure] for row in cells]
                record[field]=bench.paired_interval(ratios)
                for mode in ("reference","optimized"):
                    record[field][mode+"_median"]=statistics.median(row["modes"][mode][container][measure] for row in cells)
            record["revision_hash_median_ms"]={mode:statistics.median(row["modes"][mode]["memory_transaction"]["revision_hash_median_ms"] for row in cells) for mode in ("reference","optimized")}
            result.append(record)
    return result


def run(output):
    registered=json.loads(REGISTER.read_text())
    if registered!=design():raise ValueError("Amended registration/runtime/runner changed")
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    before_source=source()
    metadata={"phase":"heldout_cpu_only","design":registered,"started_utc":datetime.now(timezone.utc).isoformat(),
        "platform":platform.platform(),"python":sys.version,"executable":sys.executable,
        "disk_usage_before":dict(zip(("total","used","free"),shutil.disk_usage(output)))}
    (output/"metadata.json").write_text(json.dumps(metadata,indent=2)+"\n")
    rows=[]
    try:
        for seed in SEEDS:
            for days in bench.HORIZONS:
                for density in bench.DENSITIES:
                    worlds={};accepted={};snapshots={}
                    row={"seed":seed,"days":days,"density":density,"modes":{}}
                    order=[False,True];random.Random(seed*1000+days).shuffle(order)
                    for optimized in order:
                        name="optimized" if optimized else "reference"
                        gc.collect()
                        world,commands,cost=bench.build_world(seed,days,density,optimized)
                        worlds[name]=world;accepted[name]=commands;snapshots[name]=bench.semantic_snapshot(world)
                        row["modes"][name]={"build":cost}
                    if bench.changed_fields(snapshots["reference"],snapshots["optimized"]):raise AssertionError("History semantic mismatch")
                    row["history_semantic_digest"]=bench.digest(snapshots["reference"])
                    row["projection_digests"]={key:bench.digest(value) for key,value in snapshots["reference"].items()}
                    row["outcomes"]=bench.outcome_summary(worlds["reference"])
                    del snapshots
                    for name in worlds:
                        bench._timed_transaction(worlds[name],accepted[name])  # Discarded warmup.
                    elapsed={name:[] for name in worlds};hashes={name:[] for name in worlds};post_move={}
                    for repeat in range(bench.REPEATS):
                        pair=list(worlds);random.Random(seed*100000+days*100+repeat).shuffle(pair)
                        outcomes={}
                        for name in pair:
                            session,response,cost=bench._timed_transaction(worlds[name],accepted[name])
                            elapsed[name].append(cost["elapsed_ms"]);hashes[name].append(cost["revision_hash_ms"])
                            state=bench.semantic_snapshot(session.original)
                            outcomes[name]={"state":state,"response":{**response["response"],"world":bench.semantic_game(response["response"]["world"])},"revision":response["revision"]}
                            if repeat==0:post_move[name]=state
                        if bench.changed_fields(outcomes["reference"],outcomes["optimized"]):raise AssertionError("Accepted transaction outcomes/responses differ")
                    for name,world in worlds.items():
                        row["modes"][name]["memory_transaction"]={"samples_ms":elapsed[name],"median_ms":statistics.median(elapsed[name]),
                            "revision_hash_samples_ms":hashes[name],"revision_hash_median_ms":statistics.median(hashes[name])}
                        _,_,allocations=bench._timed_transaction(world,accepted[name],traced=True)
                        row["modes"][name]["traced_transaction"]=allocations
                        bench._reject_check(world,accepted[name])
                        from kalends_rebirth.server import RebirthSession
                        replay=RebirthSession(config=world.config,optimized=world.optimized)
                        for command in json.loads(bench.canonical(accepted[name])):
                            replay._perform(replay.original,command["operation"],command["data"])
                        replay.commit("move",{"location":"street"})
                        if bench.changed_fields(post_move[name],bench.semantic_snapshot(replay.original)):raise AssertionError("In-memory command replay differs")
                    row.update(fidelity_equal=True,rejection_isolated=True,in_memory_replay_equal=True)
                    rows.append(row)
                    with (output/"raw.jsonl").open("a") as stream:stream.write(json.dumps(row,sort_keys=True)+"\n")
                    print(f"cpu-heldout:seed={seed}days={days}density={density}fidelity=equal",flush=True)
        if source()!=before_source:raise RuntimeError("Source changed during amended study")
        result={"cells":len(rows),"accepted_timed_transactions":len(rows)*bench.REPEATS*2,
            "warmups":len(rows)*2,"traced_transactions":len(rows)*2,"in_memory_replays":len(rows)*2,"rejection_checks":len(rows)*2,
            "all_semantics_equal":all(row["fidelity_equal"] for row in rows),"conditions":summary(rows),
            "disk_usage_after":dict(zip(("total","used","free"),shutil.disk_usage(output)))}
        (output/"summary.json").write_text(json.dumps(result,indent=2)+"\n")
        print(json.dumps(result,indent=2))
    except BaseException as error:
        (output/"failure.json").write_text(json.dumps({"error":str(error),"type":type(error).__name__,"completed_cells":len(rows),"source_unchanged":source()==before_source,
            "disk_usage_after":dict(zip(("total","used","free"),shutil.disk_usage(output)))},indent=2)+"\n")
        raise


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("register","run"));parser.add_argument("--output",type=Path)
    args=parser.parse_args()
    if args.command=="register":register()
    elif args.output:run(args.output)
    else:parser.error("--output required for run")
