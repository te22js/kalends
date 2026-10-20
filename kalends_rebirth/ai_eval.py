"""Reproducible cognition contract QA. This runner never loads provider credentials.

Run: python -m kalends_rebirth.ai_eval --out results/rebirth/ai_evaluation
Results describe offline behavior and injected fixtures, never live model quality.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path
import statistics
import subprocess
import threading
import time

from .ai import Cognition, MockAdapter, OpenAIResponsesAdapter, TaskPolicy, allowed_evidence, canonical
from .language import Language, execute, validate_action
from .world import RebirthWorld


def walk_to(world, name):
    if world._near(name):
        return
    location = world.state.agent_locations[name]
    if location in ("street", "water", "forum_access"):
        world.move(*world.positions[name])
    else:
        world.move(location=location)


def _wire(payload):
    return {"id":"injected-offline-wire", "status":"completed",
            "usage":{"input_tokens":100,"output_tokens":20},
            "output":[{"type":"message","content":[{"type":"output_text","text":canonical(payload)}]}]}


def evaluate():
    rows = []

    def intent_case(identifier, text, name, expected, *, adapter=None, should_accept=True, fallback=False):
        world = RebirthWorld()
        walk_to(world,name)
        view = world.context(name)
        language = Language(Cognition(adapter))
        before = world.ledger.content_hash()
        started = time.perf_counter()
        proposal = language.propose(text,name,view)
        latency = time.perf_counter()-started
        action = proposal["interpretations"][0]["action"]
        valid = validate_action(action,name,view)==action
        preconfirmation_unchanged = world.ledger.content_hash()==before
        error = None
        try:
            receipt = execute(world,action)
            accepted = True
        except ValueError as problem:
            accepted = False
            receipt = None
            error = str(problem)
        result = {"id":identifier,"task":"intent","group":"offline_intents" if adapter is None else "injected_intents",
            "input":{"text":text,"recipient":name},"context_hash":hashlib.sha256(canonical(view).encode()).hexdigest(),
            "proposal":proposal,"valid_proposal":valid,"preconfirmation_unchanged":preconfirmation_unchanged,
            "world_accepted":accepted,"world_error":error,"world_receipt":receipt,"expected_action":expected,
            "expected_world_accepted":should_accept,"latency_seconds":latency,"metrics":language.metrics,
            "passed":valid and action["action"]==expected and accepted==should_accept and preconfirmation_unchanged and
                     (not fallback or proposal["ai_receipt"]["fallback"])}
        rows.append(result)

    cases = [
        ("receipt","Show me your receipt","Sabina","examine_receipt",True),
        ("tablet","Read the household tablet","Dama","examine_tablet",True),
        ("paid_verification","Pay to open the loading account","Marcus","verify_cart",True),
        ("dispute","Tell me about the dispute","Sabina","hear_dispute",True),
        ("market","Support the market","Sabina","support_market",True),
        ("household","I will guarantee the household","Lucius","guarantee_household",True),
        ("decline","I decline this dispute","Sabina","decline_dispute",True),
        ("work","I need a paid shift","Sabina","work",True),
        ("buy_one","Could I purchase one flour unit?","Felix","buy",True),
        ("unaffordable","Buy four flour units","Felix","buy",False),
        ("quantity_bound","Buy 500 flour units","Felix","talk",True),
        ("role_question","Who are you?","Dama","talk",True),
        ("history_question","What do you remember of me?","Sabina","talk",True),
        ("loading_question","What does the loading account say?","Marcus","talk",True),
        ("work_question","What work is there?","Sabina","talk",True),
        ("buy_question","How can I buy flour?","Felix","talk",True),
        ("negated_buy","I will not buy four flour","Felix","talk",True),
        ("negated_promise","Never promise anything","Felix","talk",True),
        ("deferred_delivery","Can I deliver later?","Felix","talk",True),
        ("unavailable_mediation","Bring the accounts together","Marcus","talk",True),
        ("wrong_role","Buy one flour unit","Dama","talk",True),
        ("unsupported_commission","Take the contract","Sabina","talk",True),
    ]
    for identifier,text,name,expected,accept in cases:
        intent_case(identifier,text,name,expected,should_accept=accept)
    for identifier,patch in [
        ("wrong_actor",{"actor_id":"Lucius"}),
        ("remote_target",{"recipient":"Lucius"}),
        ("false_confirmation",{"needs_confirmation":False}),
        ("unknown_evidence",{"evidence_ids":[999999]}),
        ("arbitrary_code",{"code":"credit_cash(1000)"}),
        ("boolean_quantity",{"quantity":True}),
        ("unsupported_verb",{"action":"create_money"}),
    ]:
        intent_case(identifier,"Show me your receipt","Sabina","examine_receipt",
            adapter=MockAdapter({"action":{"action":"examine_receipt","recipient":"Sabina",**patch}}),fallback=True)
    intent_case("unavailable_provider_choice","Bring the accounts together","Marcus","talk",
        adapter=MockAdapter({"action":{"action":"mediate","recipient":"Marcus"}}),fallback=True)
    intent_case("valid_mock","Show me your receipt","Sabina","examine_receipt",adapter=MockAdapter())

    world=RebirthWorld();view=world.context("Sabina")
    for identifier,task,output in [
        ("fabricated_dialogue","dialogue",{"text":"Lucius paid Aelia one hundred coins.","evidence_ids":[]}),
        ("foreign_citation","dialogue",{"flavor_id":"plain","topic_id":"memory","evidence_ids":[999999]}),
        ("invented_reflection","reflect",{"memories":[{"evidence_id":999999,"text":"Aelia stole silver."}]}),
        ("invented_montage","montage",{"event_ids":[999999]}),
        ("invented_plan","plan",{"choice_id":"mint_money","evidence_ids":[]}),
        ("unapproved_content","content_draft",{"draft":False,"archetype":"commercial_dispute","source_ids":["fake"]}),
    ]:
        language=Language(Cognition(MockAdapter(output)))
        if task=="content_draft":result=language.content_draft({"historical_source_ids":["H04"]})
        elif task=="dialogue":result=language.dialogue(view,"memory")
        else:result=getattr(language,task)(view)
        receipt=result.get("receipt",{})
        rows.append({"id":identifier,"task":task,"group":"injected_contract_attacks","result":result,
                     "metrics":language.metrics,"passed":receipt.get("fallback") is True})

    # The paid document must remain unavailable after an ordinary question.
    world=RebirthWorld();walk_to(world,"Marcus");language=Language(Cognition())
    view=world.context("Marcus");question=language.propose("What does the loading account say?","Marcus",view)
    cash,minute=world.economy.cash["Player"],world.minute
    execute(world,question["interpretations"][0]["action"])
    rows.append({"id":"no_free_loading_record","task":"dialogue","group":"world_integration","proposal":question,
                 "passed":not world._record_known("Player","loading_record") and world.economy.cash["Player"]==cash and world.minute==minute})

    # A completed route changes the actual remembered context after seven days.
    world=RebirthWorld();language=Language(Cognition());initial=world.context("Sabina")
    initial_plan=language.plan(initial)
    proposal=language.propose("Support the market","Sabina",initial)
    execute(world,proposal["interpretations"][0]["action"]);world.advance(7*1440);walk_to(world,"Sabina")
    later=world.context("Sabina");history=language.dialogue(later,"history");later_plan=language.plan(later)
    ids=history["reply"]["evidence_ids"]
    rows.append({"id":"seven_day_grounded_history","task":"dialogue","group":"world_integration",
                 "result":history,"initial_plan":initial_plan,"later_plan":later_plan,
                 "passed":bool(ids) and set(ids)<=allowed_evidence(later) and world.arc["route"]=="market" and
                          initial_plan["receipt"]["context_hash"]!=later_plan["receipt"]["context_hash"]})

    gate=threading.Event()
    def stalled(request):
        gate.wait(2)
        return request["fallback"]
    adapter=MockAdapter(stalled)
    language=Language(Cognition(adapter,policies={"intent":TaskPolicy(timeout_seconds=.01)}))
    started=time.perf_counter()
    outcomes=[language.propose("Show me your receipt","Sabina",initial) for _ in range(3)]
    elapsed=time.perf_counter()-started;gate.set()
    rows.append({"id":"stalled_provider","task":"intent","group":"timeout_fixture","outcomes":outcomes,
        "elapsed_seconds":elapsed,"metrics":language.metrics,
        "passed":all(r["ai_receipt"]["fallback"] for r in outcomes) and len(adapter.calls)==1 and elapsed<1})

    called=[]
    adapter=OpenAIResponsesAdapter(api_key="injected-placeholder",model="injected-model",transport=lambda *args:called.append(args))
    language=Language(Cognition(adapter));result=language.propose("Show me your receipt","Sabina",initial)
    rows.append({"id":"zero_budget_refuses_transport","task":"intent","group":"budget_fixture","result":result,
        "metrics":language.metrics,"passed":result["ai_receipt"]["fallback"] and not called and adapter.network_calls==0})

    adapter=OpenAIResponsesAdapter(api_key="injected-placeholder",model="injected-model",enabled=True,budget_usd=.1,
        input_usd_per_million=1,output_usd_per_million=2,
        transport=lambda *args:_wire({"action":{"action":"examine_receipt","recipient":"Sabina"}}))
    language=Language(Cognition(adapter));result=language.propose("Show me your receipt","Sabina",initial)
    rows.append({"id":"responses_rest_wire_fixture","task":"intent","group":"transport_fixture","result":result,
        "metrics":language.metrics,"fixture_estimated_cost_usd":result["ai_receipt"]["estimated_cost_usd"],
        "passed":result["ai_receipt"]["kind"]=="transport_fixture" and adapter.network_calls==0 and adapter.fixture_calls==1})
    return rows


def write_results(destination):
    destination=Path(destination)
    if destination.exists():
        raise ValueError("Choose a new output directory; evaluation results are never overwritten")
    rows=evaluate()
    root=Path(__file__).resolve().parents[1]
    files=list((root/"kalends").rglob("*.py"))+[
        root/"kalends_rebirth"/name for name in ("ai.py","language.py","ai_eval.py","world.py","scenario.py","immutable.py")]
    hashes={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}
    source_digest=hashlib.sha256(canonical(hashes).encode()).hexdigest()
    try:
        commit=subprocess.check_output(["git","rev-parse","HEAD"],cwd=root,text=True).strip()
    except (OSError,subprocess.SubprocessError):
        commit=None
    groups={}
    for row in rows:
        group=groups.setdefault(row["group"],{"cases":0,"passed":0})
        group["cases"]+=1;group["passed"]+=int(row["passed"])
    latencies=[r["latency_seconds"] for r in rows if r["group"]=="offline_intents"]
    actual_calls=sum(row.get("metrics",{}).get("external_calls",0) for row in rows)
    if actual_calls:
        raise RuntimeError("Offline QA unexpectedly contacted an external inference provider")
    summary={"evaluation_kind":"functional_contract_qa","cases":len(rows),"passed":sum(bool(r["passed"]) for r in rows),
        "groups":groups,"actual_external_inference_calls":actual_calls,"actual_external_inference_spend_usd":0,
        "real_model_quality_measured":False,"offline_intent_median_seconds":statistics.median(latencies),
        "limitations":["Offline parser behavior and deterministic mocks are not measurements of LLM quality.",
                       "Wire-fixture token counts and prices are synthetic; no provider was contacted.",
                       "Latency is local functional-QA timing, not a controlled model comparison.",
                       "Hashes describe these source bytes; the Git HEAD may precede uncommitted changes."]}
    destination.mkdir(parents=True)
    (destination/"raw.jsonl").write_text("".join(canonical(row)+"\n" for row in rows))
    (destination/"summary.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    report=["# Cognition contract QA", "", f"**{summary['passed']}/{summary['cases']} functional cases passed.** Actual external inference: 0 calls, $0 spent.",
            "", "These are authored-parser checks and injected fixtures. No real model quality was measured.", "",
            "| Case group | Passed |", "|---|---:|"]
    report.extend(f"| {name} | {group['passed']}/{group['cases']} |" for name,group in groups.items())
    report.extend(["", "The raw JSONL preserves proposals, validator results, confirmed world receipts and redacted cognition receipts.",
                   "The manifest records the source bytes, runtime and artifact hashes. Its Git HEAD can precede uncommitted changes.",
                   "Synthetic wire usage and hypothetical prices test accounting only. Local timings are functional QA, not a model benchmark.", ""])
    (destination/"report.md").write_text("\n".join(report))
    manifest={"created_utc":datetime.now(timezone.utc).isoformat(),"source_commit":commit,"source_hash":source_digest,
              "source_files":hashes,"python":platform.python_version(),"platform":platform.platform(),"world_seed":79,
              "command":"python -m kalends_rebirth.ai_eval --out "+str(destination),
              "artifacts":{name:hashlib.sha256((destination/name).read_bytes()).hexdigest() for name in ("raw.jsonl","summary.json","report.md")}}
    (destination/"manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",required=True)
    summary=write_results(parser.parse_args().out)
    print(json.dumps(summary,indent=2,sort_keys=True))
    return 0 if summary["cases"]==summary["passed"] else 1


if __name__=="__main__":
    raise SystemExit(main())
