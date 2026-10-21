"""Counter minds through reviewed actions, durable mixed replay and real forks."""
import copy
import json
from pathlib import Path

import pytest

from kalends_rebirth.ai import Cognition, MockAdapter, ProposalError
from kalends_rebirth.language import Language, action_label, validate_action
from kalends_rebirth.server import RebirthSession


BASELINE=Path(__file__).resolve().parents[1]/"results/minds_v2/playability/baseline_journal.json"


def session(path=None,adapter=None):
    return RebirthSession(path,language=Language(Cognition(adapter)))


def choose(s,recipient,choice_id):
    proposal=s.apply("propose",{"recipient":recipient,"choice_id":choice_id})
    return s.apply("act",{"proposal_id":proposal["proposal_id"],"interpretation_id":"0"})


def near(s,recipient):
    for _ in range(3):
        if s.original._near(recipient):return
        location=s.original.state.agent_locations[recipient]
        body={"location":location} if location not in ("street","water","forum_access") else dict(zip(("x","y"),s.original.positions[recipient]))
        s.apply("move",body)
    assert s.original._near(recipient)


def opening(s):
    s.apply("advance",{"minutes":20,"mode":"compress"})
    near(s,"Felix")
    assert s.original.v2_market["offers"]["Felix"]["mode"]=="bonded"


def buy_two(s):
    near(s,"Marcus")
    proposal=s.apply("propose",{"recipient":"Marcus","text":"Buy two flour units"})
    assert proposal["interpretations"][0]["action"]["quantity"]==2
    s.apply("act",{"proposal_id":proposal["proposal_id"],"interpretation_id":"0"})


def complete_order(s):
    opening(s);accepted=choose(s,"Felix","v2_bonded_order")["receipt"]
    buy_two(s);near(s,"Felix")
    delivered=choose(s,"Felix","v2_deliver_order")["receipt"]
    return accepted,delivered


def material(s):
    return (s.original.ledger.content_hash(),copy.deepcopy(s.original.fidelity_state()),copy.deepcopy(s.commands))


def test_read_only_route_context_and_review_never_activate_or_move_the_old_world(tmp_path):
    path=tmp_path/"life.json";s=session(path);s.save()
    before=material(s);saved=path.read_bytes()
    s.apply("route",{"location":"bakery"});s.context("Sabina")
    s.apply("propose",{"recipient":"Sabina","choice_id":"examine_receipt"})
    assert material(s)==before and path.read_bytes()==saved
    assert not s.original.v2_active() and not s.original.v2_minds
    assert s.state()["world"]["counter_market"]=={"active":False}


@pytest.mark.parametrize("operation,body",[("move",{"x":100,"y":100}),("advance",{"minutes":-1}),
    ("action",{"action":"v2_bonded_order","recipient":"Felix"})])
def test_failed_first_command_does_not_leave_activation_memory_or_scheduled_market_tasks(tmp_path,operation,body):
    path=tmp_path/"life.json";s=session(path);s.save()
    before=material(s);saved=path.read_bytes()
    with pytest.raises(ValueError):s.commit(operation,body)
    assert material(s)==before and path.read_bytes()==saved
    assert not s.original.v2_active() and not s.original.v2_minds


def test_first_command_save_failure_rolls_back_minds_and_same_review_can_retry(tmp_path,monkeypatch):
    path=tmp_path/"life.json";s=session(path);s.save()
    p=s.apply("propose",{"recipient":"Sabina","choice_id":"examine_receipt"})
    request={"proposal_id":p["proposal_id"],"interpretation_id":"0"}
    before=material(s);saved=path.read_bytes();save=s.save
    def fail():raise OSError("simulated disk full")
    monkeypatch.setattr(s,"save",fail)
    with pytest.raises(OSError):s.apply("act",request)
    assert material(s)==before and path.read_bytes()==saved and p["proposal_id"] in s.proposals
    monkeypatch.setattr(s,"save",save);s.apply("act",request)
    assert s.original.v2_active() and set(s.original.v2_minds)=={"Felix","Sabina"}
    assert s.commands[-1]["minds_revision"]==2
    assert sum(e.payload["category"]=="v2_activation" for e in s.original.ledger.events)==1


def test_reviewed_order_terms_are_read_only_detached_and_revision_bound(tmp_path):
    path=tmp_path/"life.json";s=session(path);opening(s)
    before=material(s);saved=path.read_bytes()
    p=s.apply("propose",{"recipient":"Felix","choice_id":"v2_bonded_order"})
    review=p["interpretations"][0]
    assert review["terms"]=={"deadline":241,"quantity":2,"price":6,"advance":0,"bond":2}
    assert "two coins now" in review["transmission"] and "three coins per unit" in review["transmission"]
    assert material(s)==before and path.read_bytes()==saved
    # HTTP response mutation cannot rewrite the stored agreement.
    review["terms"]["price"]=999;review["action"]["action"]="v2_advance_order"
    s.apply("act",{"proposal_id":p["proposal_id"],"interpretation_id":"0"})
    assert s.original._v2_contract("Felix","open")["bond"]==2
    assert s.original.economy.cash["Player"]==4
    with pytest.raises(ValueError):s.apply("act",{"proposal_id":p["proposal_id"],"interpretation_id":"0"})


def test_existing_real_browser_journal_restores_exactly_then_mixed_commands_resume_full_fidelity(tmp_path):
    path=tmp_path/"life.json";source=BASELINE.read_bytes();path.write_bytes(source)
    payload=json.loads(source);s=session(path)
    assert path.read_bytes()==source and s.original.ledger.content_hash()==payload["ledger_hash"]
    assert s.original.minute==32 and not s.original.v2_active()
    assert all("minds_revision" not in c for c in s.commands)
    s.apply("advance",{"minutes":20,"mode":"compress"})
    assert s.commands[:-1]==payload["commands"] and s.commands[-1]["minds_revision"]==2
    assert s.original.v2_active()
    saved=path.read_bytes();restored=session(path)
    assert path.read_bytes()==saved and material(restored)==material(s)
    assert restored.original.v2_fidelity()==s.original.v2_fidelity()
    s.apply("advance",{"minutes":3});restored.apply("advance",{"minutes":3})
    assert material(restored)==material(s)


@pytest.mark.parametrize("revision",[1,3,True,"2",None,2.0])
def test_unknown_mind_revision_rejects_save_without_changing_it(tmp_path,revision):
    path=tmp_path/"life.json";s=session(path);s.apply("advance",{"minutes":20})
    payload=json.loads(path.read_text());payload["commands"][0]["minds_revision"]=revision
    path.write_text(json.dumps(payload));before=path.read_bytes()
    with pytest.raises(ValueError,match="Unsupported minds revision"):session(path)
    assert path.read_bytes()==before


def test_saved_full_order_and_continuation_restore_cognitive_and_resource_state(tmp_path):
    path=tmp_path/"life.json";s=session(path);complete_order(s)
    assert s.original.economy.cash["Player"]==8
    assert s.original.v2_market["completed_batches"]["Felix"]==1
    before=material(s);saved=path.read_bytes();restored=session(path)
    assert path.read_bytes()==saved and material(restored)==before
    future=s.original.v2_market["activated_at"]+1461-s.original.minute
    s.apply("advance",{"minutes":future,"mode":"compress"});restored.apply("advance",{"minutes":future,"mode":"compress"})
    assert material(restored)==material(s)
    assert restored.original.v2_market["offers"]["Felix"]["mode"]=="advance"


@pytest.mark.parametrize("remove",["accept","deliver"])
def test_counterfactual_removes_actual_order_action_discloses_skips_and_survives_restart(tmp_path,remove):
    path=tmp_path/"life.json";s=session(path);accepted,delivered=complete_order(s)
    before=material(s);s.apply("mode",{"mode":"lab"})
    s.apply("fork",{"kind":"remove_action","event_id":(accepted if remove=="accept" else delivered)["event_id"]})
    assert material(s)==before and s.branch.minute==s.original.minute
    assert s.branch.v2_market["completed_batches"]["Felix"]==0
    assert s.branch.economy.inventory["Player"]==2
    assert "minds_v2" in s.state()["comparison"]["changed_fields"]
    if remove=="accept":
        assert not s.branch._v2_contract("Felix")
        assert s.intervention["skipped"] and s.intervention["skipped"][-1]["command"]==len(s.commands)-1
    else:
        assert s.branch._v2_contract("Felix","open")["delivered"]==0
        assert not s.intervention["skipped"]
    restored=session(path)
    assert restored.branch.fidelity_state()==s.branch.fidelity_state() and restored.intervention==s.intervention
    assert material(restored)==material(s)


def test_game_projection_hides_minds_and_lab_exposes_bounded_inspection():
    s=session();opening(s)
    state=s.state();context=s.context("Felix")
    assert "operator" not in state["world"]
    assert set(context["counter_order"])=={"offer","contract"}
    assert not {"experiences","beliefs","cash","inventory","plan_options"}.intersection(context)
    serialized=json.dumps(state)
    assert '"semantic"' not in serialized and '"episodes"' not in serialized and '"last_decision"' not in serialized
    s.apply("mode",{"mode":"lab"})
    minds=s.state()["world"]["operator"]["cognition_v2"]["minds"]
    assert set(minds)=={"Felix","Sabina"}
    assert all(m["footprint"]["memory_records"]<=m["footprint"]["capacity"] for m in minds.values())


def test_partial_late_repair_resumes_without_refunding_the_forfeited_bond_or_repeating_a_reward(tmp_path):
    path=tmp_path/"life.json";s=session(path);opening(s);choose(s,"Felix","v2_bonded_order")
    deadline=s.original._v2_contract("Felix","open")["deadline"]
    s.apply("advance",{"minutes":deadline-s.original.minute,"mode":"compress"})
    assert s.original._v2_contract("Felix","defaulted")["debt"]==0
    buy_two(s);near(s,"Felix");choose(s,"Felix","v2_replace_one")
    saved=path.read_bytes();restored=session(path)
    assert path.read_bytes()==saved and material(restored)==material(s)
    before=restored.original.economy.cash["Player"]
    choose(restored,"Felix","v2_replace_order")
    contract=restored.original._v2_contract("Felix")
    institutional=next(c for c in restored.original.economy.commitments["Player"] if c["id"]==contract["id"])
    assert restored.original.economy.cash["Player"]==before
    assert contract["status"]=="repaired" and contract["replacement_units"]==2
    assert institutional["status"]=="missed" and institutional["repaired"]
    assert restored.original.v2_market["completed_batches"]["Felix"]==1
    assert session(path).original.fidelity_state()==restored.original.fidelity_state()


def test_even_an_omitted_fork_command_must_have_a_supported_mind_revision():
    s=session();accepted,_=complete_order(s);s.apply("mode",{"mode":"lab"})
    command=next(c for c in s.commands if c["receipt_id"]==accepted["event_id"])
    command["minds_revision"]="2"
    before=material(s)
    with pytest.raises(ValueError,match="Unsupported minds revision"):
        s.apply("fork",{"kind":"remove_action","event_id":accepted["event_id"]})
    assert material(s)==before and s.branch is None and s.intervention is None


@pytest.mark.parametrize("action,quantity",[("v2_cash_order",1),("v2_cash_order",3),("v2_bonded_order",2),
    ("v2_advance_order",2),("v2_share_report",2),("v2_repay_order",2)])
def test_fixed_counter_quantities_cannot_be_reinterpreted_by_a_provider_or_direct_engine(action,quantity):
    s=session();opening(s);view=s.original.context("Felix")
    with pytest.raises(ProposalError,match="requires quantity"):
        validate_action({"action":action,"recipient":"Felix","quantity":quantity},"Felix",view)
    before=material(s)
    with pytest.raises(ValueError,match="requires quantity"):
        s.original.v2_interact(action,"Felix",quantity)
    assert material(s)==before


def test_malicious_provider_quantity_falls_back_to_exact_typed_offer_then_executes_reviewed_goods():
    adapter=MockAdapter({"action":{"action":"v2_cash_order","recipient":"Felix","quantity":1}})
    s=session(adapter=adapter);opening(s);buy_two(s);near(s,"Felix")
    before=s.original.economy.cash["Player"]
    p=s.apply("propose",{"recipient":"Felix","text":"Sell two flour units now"})
    review=p["interpretations"][0]
    assert review["action"]["quantity"]==2 and review["label"]=="Sell two flour units now"
    assert any(c.get("cost")=="2 actual flour units → 6 coins" for c in s.original.choices("Felix"))
    s.apply("act",{"proposal_id":p["proposal_id"],"interpretation_id":"0"})
    assert s.original.economy.inventory["Player"]==0 and s.original.economy.cash["Player"]==before+6
    assert s.language.metrics["rejected_outputs"]>=2


def test_partial_provider_action_is_labeled_with_its_actual_offered_quantity():
    s=session();opening(s);choose(s,"Felix","v2_bonded_order");buy_two(s);near(s,"Felix")
    action={"action":"v2_deliver_order","recipient":"Felix","quantity":1}
    view=s.original.context("Felix")
    label,_=action_label(validate_action(action,"Felix",view),view)
    assert label=="Deliver one flour unit now"
    typed=Language(Cognition()).propose("Deliver one flour unit now","Felix",view)
    assert typed["interpretations"][0]["action"]["quantity"]==1
    assert typed["interpretations"][0]["label"]==label


def test_settled_order_acknowledges_the_payment_without_offering_a_pointless_report():
    s=session();complete_order(s);before=material(s)
    context=s.context("Felix")
    topic=next(t for t in context["topics"] if t["id"]=="v2_counter_order")
    assert "six-coin price is settled" in topic["text"] and "bond has also been returned" in topic["text"]
    assert not any(c["id"]=="v2_share_report" for c in context["choices"])
    assert material(s)==before
    with pytest.raises(ValueError,match="No open counter window"):
        s.original.v2_interact("v2_share_report","Felix")
    assert material(s)==before


def test_authored_game_cases_demonstrate_actual_funded_terms_and_private_correction_at_declared_limits():
    from scripts.minds_v2_game_case import run
    report,journal=run();a,b=(report["retention"]["arms"][p] for p in ("hybrid","recency"))
    assert a["accounts_before_terms"]==b["accounts_before_terms"]
    assert a["interference_sha256"]==b["interference_sha256"]
    assert a["final_minute"]==b["final_minute"] and a["final_coins"]==6 and b["final_coins"]==3
    assert a["contract"]["status"]=="fulfilled" and b["contract"]["status"]=="defaulted"
    correction=report["correction"]
    assert correction["exact_resume_verified"] and correction["paid_player_report"]["kind"]=="observed"
    assert correction["offers"]["Felix"]["status"]=="withdrawn" and correction["offers"]["Sabina"]["status"]=="offered"
    assert correction["new_beliefs"]["Sabina"]["as_of"]<correction["paid_player_report"]["as_of"]
    assert correction["external_calls"]==a["external_calls"]==b["external_calls"]==0
    assert journal["commands"][0]["after"]==200 and "minds_revision" not in journal["commands"][0]
