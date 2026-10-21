"""Independently fold transfers/goods and recompute summaries from saved rows.

This verifier does not import AgentMind, the scenario generator or evaluator.
It verifies recorded outcomes/accounting and declared aggregate calculations;
it cannot establish that an authored task is externally valid or enjoyable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import random
import statistics


def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)


def interval(values):
    rng=random.Random(94617)
    draws=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(2000))
    return {"mean":statistics.mean(values),"low":draws[49],"high":draws[1949],"unit":"paired seed mean","n":len(values)}


def verify(folder):
    folder=Path(folder)
    rows=[json.loads(line) for line in (folder/"raw.jsonl").read_text().splitlines()]
    metadata=json.loads((folder/"metadata.json").read_text());summary=json.loads((folder/"summary.json").read_text())
    registered=metadata["design"]
    seeds=registered["development_seeds"] if metadata["phase"]=="pilot" else registered["heldout_seeds"]
    families=registered["families"]
    expected={(seed,family) for seed in seeds for family in families}
    assert {(r["seed"],r["family"]) for r in rows}==expected and len(rows)==len(expected)
    arms=registered["primary_arms"]+registered["secondary_retention_arms"]+registered["separate_references"]
    checks=0
    for row in rows:
        case=row["case"]
        assert hashlib.sha256(canonical(case["observations"]).encode()).hexdigest()==row["observation_digest"]
        assert set(row["arms"])==set(arms)
        for arm,result in row["arms"].items():
            cash={"Merchant":float(case["initial_cash"]),"Partner":100.,"Inspector":20.,"Courier":20.,"Buyer":100.,"Escrow":0.}
            goods={"Merchant":0,"Preferred":2,"Safe":2};starting=cash["Merchant"]
            last_fulfilled=False
            for event in result["ledger"]:
                if "source" in event:
                    source,target,amount=event["source"],event["target"],event["coins"]
                    assert amount>=0 and cash[source]>=amount
                    cash[source]-=amount;cash[target]+=amount
                if "earlier_obligation" in event:starting=cash["Merchant"]
                if "goods_from" in event:
                    quantity=event["quantity"];assert quantity>=0 and goods[event["goods_from"]]>=quantity
                    goods[event["goods_from"]]-=quantity;goods[event["goods_to"]]+=quantity
                if "contract" in event:
                    assert event["at"]<=case["deadline"]
                    last_fulfilled=event["fulfilled"]
                if "communication" in event:assert event["authorized"] is True
            assert cash==result["cash"] and goods==result["goods"]
            assert abs(sum(cash.values())-(case["initial_cash"]+240))<1e-9
            assert sum(goods.values())==4 and min(cash.values())>=0
            utility=cash["Merchant"]-starting+goods["Merchant"]*case["goods_value"]
            assert utility==result["utility"] and result["goal_completed"]==last_fulfilled
            allowed={e["event_id"] for e in case["observations"]}
            if result["verification_used"]:allowed.update((1000,1001))
            if arm=="omniscient_upper_bound":allowed.update((2000,2001))
            context=256 if arm in registered["separate_references"] else registered["decision_context_records"]
            capacity=256 if arm in registered["separate_references"] else registered["capacity_records"]
            assert result["footprint"]["memory_records"]<=capacity and result["max_memory_records"]<=capacity
            for decision in result["decisions"]:
                assert len(decision["context_event_ids"])<=context
                assert set(decision["context_event_ids"])<=allowed and set(decision["evidence_ids"])<=allowed
            assert result["unsupported_evidence_ids"]==[]
            checks+=1
    assert summary["worlds"]==len(rows)
    for arm in arms:
        assert summary["arms"][arm]["mean_utility"]==statistics.mean(row["arms"][arm]["utility"] for row in rows)
        assert summary["arms"][arm]["goal_completion_rate"]==statistics.mean(row["arms"][arm]["goal_completed"] for row in rows)
        assert summary["arms"][arm]["mean_serialized_bytes"]==statistics.mean(row["arms"][arm]["footprint"]["serialized_bytes"] for row in rows)
    differences=[statistics.mean(row["arms"]["mind"]["utility"]-row["arms"]["structured"]["utility"] for row in rows if row["seed"]==seed) for seed in seeds]
    assert summary["primary_contrast"]==interval(differences)
    for family in families:
        assert summary["per_family_primary_contrast"][family]==interval([row["arms"]["mind"]["utility"]-row["arms"]["structured"]["utility"] for row in rows if row["family"]==family])
        for arm in arms:
            selected=[row["arms"][arm] for row in rows if row["family"]==family]
            assert summary["families"][family][arm]["mean_utility"]==statistics.mean(result["utility"] for result in selected)
            assert summary["families"][family][arm]["goal_completion_rate"]==statistics.mean(result["goal_completed"] for result in selected)
    return {"worlds":len(rows),"executed_arm_cases_checked":checks,"complete_seed_family_grid":True,"accounting_goods_utility_access_and_budgets_verified":True,
        "primary_and_family_intervals_recomputed":True,"raw_sha256":hashlib.sha256((folder/"raw.jsonl").read_bytes()).hexdigest(),
        "scope":"Independent fold of recorded transfers/goods and summary arithmetic; not independent generation, memory implementation, semantic language evaluation or human validity proof."}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("run",type=Path);parser.add_argument("--out",type=Path)
    args=parser.parse_args();result=verify(args.run)
    if args.out:
        with args.out.open("x") as stream:stream.write(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
