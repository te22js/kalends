"""Controlled game diagnostics; these authored cases are not held-out research.

Run from the repository root: python -m scripts.minds_v2_game_case --output
results/minds_v2/game_cases.json. Every transaction uses the real game world;
player actions use the same reviewed Session flow as the browser. The retention
case deliberately injects matched, legitimate Felix-only routine experiences
through the host admission hook. It has no durable replay claim because the
experimental policy is explicitly configured outside an accepted command.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import tempfile

from kalends.memory.base import Experience
from kalends_rebirth.ai import Cognition
from kalends_rebirth.language import Language
from kalends_rebirth.minds import MindConfig
from kalends_rebirth.server import RebirthSession


ROOT=Path(__file__).resolve().parents[1]


def canonical(value):return json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False)
def digest(value):return hashlib.sha256(canonical(value).encode()).hexdigest()


def fresh(*,config=None,path=None):return RebirthSession(path,config=config,language=Language(Cognition()))


def near(s,recipient):
    for _ in range(3):
        if s.original._near(recipient):return
        location=s.original.state.agent_locations[recipient]
        target={"location":location} if location not in ("street","water","forum_access") else dict(zip(("x","y"),s.original.positions[recipient]))
        s.apply("move",target)
    raise AssertionError("Could not reach "+recipient)


def choose(s,recipient,choice):
    p=s.apply("propose",{"recipient":recipient,"choice_id":choice})
    return s.apply("act",{"proposal_id":p["proposal_id"],"interpretation_id":"0"})


def buy(s,quantity):
    near(s,"Marcus")
    p=s.apply("propose",{"recipient":"Marcus","text":f"Buy {quantity} flour units"})
    return s.apply("act",{"proposal_id":p["proposal_id"],"interpretation_id":"0"})


def purse(s):return s.original.economy.cash["Player"]


def accounts(s):
    w=s.original
    return {"cash":dict(w.economy.cash),"inventory":dict(w.economy.inventory),"market_stock":w.economy.market_stock,"price":w.economy.price}


def retention_case():
    arms={}
    for policy in ("hybrid","recency"):
        s=fresh();w=s.original
        w.v2_activate_minds(MindConfig(retention_policy=policy))
        s.apply("advance",{"minutes":20,"mode":"compress"});near(s,"Felix")
        choose(s,"Felix","v2_bonded_order");buy(s,2);near(s,"Felix")
        receipt=choose(s,"Felix","v2_deliver_order")["receipt"]
        near(s,"Marcus")
        for _ in range(4):choose(s,"Marcus","inspect")
        w=s.original;admissions=[]
        for _ in range(48):
            event=w._emit("v2_counter_routine","Felix sorts an ordinary local counter notice",actors=("Felix",),scope="private")
            experience=Experience(w.minute,"episodic",None,None,None,None,w.minute,True,event.event_id,event.payload["title"])
            w._remember("Felix",experience);admissions.append(asdict(experience))
        s.apply("advance",{"minutes":w.v2_market["activated_at"]+1461-w.minute,"mode":"compress"})
        w=s.original;near(s,"Felix");w=s.original
        before=accounts(s);mind=w.v2_minds["Felix"]
        decision=asdict(mind.last_decision);social=mind.social("Player","reliability",now=w.minute)
        offered=w.v2_market["offers"]["Felix"]["mode"]
        choose(s,"Felix","v2_advance_order" if offered=="advance" else "v2_bonded_order")
        liquidity=purse(s)
        # Fixed disclosed continuation: buy the largest affordable lot up to2,
        # deliver it, then let the deadline settle. Alternate paid work remains
        # possible in the game and is deliberately not taken in this diagnostic.
        quantity=min(2,int(purse(s)//s.original.economy.price))
        if quantity:buy(s,quantity);near(s,"Felix");choose(s,"Felix","v2_deliver_order" if quantity==2 else "v2_deliver_one")
        contract=s.original._v2_contract("Felix")
        if s.original.minute<contract["deadline"]:s.apply("advance",{"minutes":contract["deadline"]-s.original.minute,"mode":"compress"})
        arms[policy]={"config":asdict(mind.config),"first_kept_event":receipt["event_id"],"interference":admissions,
            "interference_sha256":digest(admissions),"accounts_before_terms":before,"terms":offered,
            "retained_reliability":social,"decision":decision,"footprint_at_decision":mind.footprint(),
            "coins_after_accepting_terms":liquidity,"final_minute":s.original.minute,"final_coins":purse(s),"final_inventory":s.original.economy.inventory["Player"],
            "contract":s.original._v2_contract("Felix"),"completed_batches":s.original.v2_market["completed_batches"],
            "external_calls":s.language.metrics["external_calls"],"ledger_hash":s.original.ledger.content_hash()}
    a,b=arms["hybrid"],arms["recency"]
    assert a["accounts_before_terms"]==b["accounts_before_terms"] and a["interference_sha256"]==b["interference_sha256"]
    assert a["final_minute"]==b["final_minute"]
    assert a["terms"]=="advance" and b["terms"]=="bonded"
    assert a["contract"]["status"]=="fulfilled" and b["contract"]["status"]=="defaulted"
    return {"kind":"controlled retention ablation in actual game world","arms":arms,
        "claims":["Only retention policy differs; capacity32, context8 and consolidationTrue match.",
            "The buyer retains or loses its own kept-order receipt under matched authored routine interference.",
            "Different funded terms change working liquidity and the fixed subsequent purchase/delivery path."],
        "limits":["Authored diagnostic selected to exercise retention; not a registered held-out estimate or old-runtime comparison.",
            "The48 routine episodes are harness-authored legitimate Felix-only observations, not naturally sampled browser play.",
            "The fixed continuation takes no additional wage work; the real game offers other recovery strategies.",
            "Experimental policy activation is outside the durable command format; no save/resume claim is made for these arms."]}


def correction_case():
    # A declared seed80 late dispatch changes at minute240. A valid legacy-only
    # advance prefix places activation at200 so the change occurs inside the
    # new order window. The prefix and all following commands replay exactly.
    with tempfile.TemporaryDirectory(prefix="kalends-correction-") as temporary:
        path=Path(temporary)/"case.json";prefix=fresh(config={"seed":80})
        RebirthSession._perform(prefix.original,"advance",{"minutes":200,"mode":"compress"},minds_revision=0,movement_revision=1)
        payload={"version":4,"config":prefix.config,"origin":None,"commands":[{"operation":"advance","data":{"minutes":200,"mode":"compress"},
            "at":0,"after":200,"receipt_id":None}],"mode":"game","ledger_hash":prefix.original.ledger.content_hash(),
            "intervention":None,"telemetry_enabled":False,"product_events":[]}
        path.write_text(canonical(payload));s=fresh(path=path)
        s.apply("advance",{"minutes":20,"mode":"compress"})
        old={a:asdict(s.original.v2_minds[a].believe("grain","supply",now=s.original.minute)) for a in ("Felix","Sabina")}
        s.apply("advance",{"minutes":25,"mode":"compress"});near(s,"Felix")
        choose(s,"Felix","inspect");s.apply("advance",{"minutes":15,"mode":"compress"})
        paid_report=max((e for e in s.original.remembered("Player") if e.kind=="observed" and e.subject=="grain" and e.predicate=="supply"),key=lambda e:e.as_of)
        before=accounts(s);share=choose(s,"Felix","v2_share_report")["receipt"]
        new={a:asdict(s.original.v2_minds[a].believe("grain","supply",now=s.original.minute)) for a in ("Felix","Sabina")}
        offers={a:dict(s.original.v2_market["offers"][a]) for a in ("Felix","Sabina")}
        assert old["Felix"]["value"]==old["Sabina"]["value"]=="available"
        assert new["Felix"]["value"]==paid_report.value=="disrupted" and new["Sabina"]["value"]=="available"
        assert offers["Felix"]["status"]=="withdrawn" and offers["Sabina"]["status"]=="offered"
        restored=fresh(path=path)
        assert restored.original.fidelity_state()==s.original.fidelity_state()
        journal=json.loads(path.read_text())
        return {"kind":"different legitimate exposure to an actual changed dispatch","seed":80,"old_beliefs":old,
            "paid_player_report":asdict(paid_report),"shared_event":share["event_id"],"new_beliefs":new,"offers":offers,
            "accounts_before_sharing":before,"accounts_after_sharing":accounts(s),"exact_resume_verified":True,
            "external_calls":s.language.metrics["external_calls"],"ledger_hash":s.original.ledger.content_hash(),
            "limits":["Declared seed80/window chosen to exercise a real scheduled correction; not a held-out performance estimate.",
                "The legacy prefix is a controlled compatibility fixture, not a user's historical save.",
                "Sabina does not receive Felix's or the player's private inspection; differing beliefs reflect exposure."]},journal


def run():
    correction,journal=correction_case()
    files=["kalends_rebirth/"+name+".py" for name in ("minds","cognitive_market","world","server","language")]+["scripts/minds_v2_game_case.py"]
    return {"version":1,"classification":"post-study authored game diagnostics; separate from MindsBench results",
        "source_sha256":{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files},
        "retention":retention_case(),"correction":correction},journal


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();report,journal=run()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    journal_path=args.output.with_name(args.output.stem+"_correction_journal.json")
    journal_path.write_text(json.dumps(journal,indent=2,sort_keys=True,allow_nan=False)+"\n")
    print(json.dumps({"output":str(args.output),"correction_journal":str(journal_path),
        "terms":{a:r["terms"] for a,r in report["retention"]["arms"].items()},"correction_resume":report["correction"]["exact_resume_verified"]}))


if __name__=="__main__":main()
