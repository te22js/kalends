"""Agent cognition on admitted streams, bounded memory and consequential choices."""
from dataclasses import asdict
import copy
import json

import pytest

from kalends.memory.base import Experience
from kalends_rebirth.minds import (ActionOption, AgentMind, BeliefCondition,
    Episode, Goal, MindConfig, SocialCondition, SocialSignal)


def claim(identifier, value="ready", *, agent="Felix", received=None, vintage=None,
          source=None, origin="Marcus", root=0, salience=.2):
    received = identifier if received is None else received
    vintage = received if vintage is None else vintage
    return Episode(identifier,agent,received,"told" if source else "observed",f"A received report: cargo is {value}.",
        "cargo","condition",value,vintage,source,root,origin,True,(),salience,("supply",))


def mind(**settings):
    return AgentMind("Felix",MindConfig(**settings))


def options(*, independent=1, maximum_age=None):
    return [ActionOption("buy","Buy the ready cargo",5,costs={"coins":2},
            conditions=(BeliefCondition("cargo","condition","ready",independent,maximum_age),)),
        ActionOption("verify","Commission a costly check",1,costs={"coins":1}),
        ActionOption("wait","Wait for another opportunity",0)]


def execute_trade(decision, *, actual_ready, purse=4):
    """Tiny actual resource validator, deliberately separate from agent beliefs."""
    inventory=0
    if decision.action_id=="buy":
        assert purse>=2
        purse-=2
        inventory+=int(actual_ready)
    elif decision.action_id=="verify":
        assert purse>=1
        purse-=1
    return {"coins":purse,"goods":inventory,"utility":purse+5*inventory}


def test_admission_has_no_archive_surface_and_rejects_another_agents_experience():
    m=mind();before=m.to_dict()
    with pytest.raises(ValueError,match="own admitted"):
        m.observe(claim(1,agent="Marcus"))
    assert m.to_dict()==before
    assert m.believe("cargo","condition",now=1).status=="unknown"
    with pytest.raises(TypeError):
        m.believe("cargo","condition",now=1,archive={0:"secret"})


def test_existing_experience_adapter_preserves_receipt_time_vintage_and_claimed_lineage():
    exp=Experience(20,"told","cargo","condition","ready","Dama",3,True,7,"The earlier cargo report.","observed",2,"Marcus")
    episode=Episode.from_experience("Felix",exp)
    m=mind();m.observe(episode);b=m.believe("cargo","condition",now=20)
    assert b.value=="ready" and b.as_of==3 and b.learned_at==20
    assert b.evidence_ids==(7,) and b.source_groups==("origin-observer:Marcus",)
    assert "not independently authenticated" in b.lineage_kind
    assert b.confidence_kind=="uncalibrated evidence heuristic"


def test_newer_correction_changes_an_executed_purchase_not_only_a_retrieved_label():
    revised=mind();static=mind(belief_revision=False)
    for m in (revised,static):
        m.observe(claim(1,"ready",received=1,vintage=1))
        m.observe(claim(5,"blocked",received=5,vintage=5))
    good=revised.choose(options(),own_resources={"coins":4},now=5)
    bad=static.choose(options(),own_resources={"coins":4},now=5)
    assert good.action_id=="verify" and bad.action_id=="buy"
    good_result=execute_trade(good,actual_ready=False)
    bad_result=execute_trade(bad,actual_ready=False)
    assert good_result=={"coins":3,"goods":0,"utility":3}
    assert bad_result=={"coins":2,"goods":0,"utility":2}
    assert revised.believe("cargo","condition",now=5).superseded_ids==(1,)
    revision=revised.inspect(now=5)["revisions"][0]
    assert revision["replaces"]==[1] and revision["evidence_ids"]==[5]


def test_a_late_stale_relay_cannot_resurrect_an_obsolete_belief():
    m=mind(context_records=1)
    m.observe(claim(1,"ready",received=1,vintage=1,source="Dama",salience=1))
    m.observe(claim(10,"blocked",received=10,vintage=10,source="Marcus"))
    m.observe(claim(20,"ready",received=20,vintage=1,source="Lucius",salience=1))
    b=m.believe("cargo","condition",now=20)
    assert b.value=="blocked" and b.evidence_ids==(10,)


def test_correlated_relays_do_not_become_independent_witnesses_and_change_credit_cost():
    guarded=mind();naive=mind(source_lineage=False)
    for m in (guarded,naive):
        for i,speaker in enumerate(("Dama","Sabina","Lucius"),1):
            m.observe(claim(i,"ready",received=i,vintage=0,source=speaker,origin="Marcus",root=0))
    assert len(guarded.believe("cargo","condition",now=3).source_groups)==1
    assert len(naive.believe("cargo","condition",now=3).source_groups)==3
    safe=guarded.choose(options(independent=2),own_resources={"coins":4},now=3)
    risky=naive.choose(options(independent=2),own_resources={"coins":4},now=3)
    assert execute_trade(safe,actual_ready=False)["utility"]>execute_trade(risky,actual_ready=False)["utility"]
    guarded.observe(claim(4,"ready",received=4,vintage=0,source="Chreste",origin="Chreste",root=4))
    assert guarded.choose(options(independent=2),own_resources={"coins":4},now=4).action_id=="buy"


def test_direct_observation_and_its_relay_share_one_origin_group():
    m=mind();m.observe(claim(1,origin="Felix"))
    m.observe(claim(2,received=2,vintage=1,source="Dama",origin="Felix",root=1))
    assert m.believe("cargo","condition",now=2).source_groups==("origin-observer:Felix",)


def test_equal_vintage_contradiction_requires_recovery_without_an_oracle_tiebreak():
    m=mind()
    m.observe(claim(1,"ready",received=1,vintage=0,source="Dama",origin="Marcus"))
    m.observe(claim(2,"blocked",received=2,vintage=0,source="Chreste",origin="Chreste"))
    b=m.believe("cargo","condition",now=2)
    assert b.status=="conflicted" and b.value is None and b.contradictory_ids==(1,2)
    assert m.choose(options(),own_resources={"coins":4},now=2).action_id=="verify"
    m.observe(claim(3,"ready",received=3,vintage=3))
    assert m.choose(options(),own_resources={"coins":4},now=3).action_id=="buy"


def test_newly_received_old_report_does_not_satisfy_a_freshness_requirement():
    m=mind();m.observe(claim(3,received=100,vintage=0,source="Dama"))
    assert m.choose(options(maximum_age=30),own_resources={"coins":4},now=100).action_id=="verify"


def test_retained_personal_consequence_changes_credit_and_retains_its_reason():
    m=mind();terms=[ActionOption("advance","Extend a working advance",5,costs={"coins":3},
        social_conditions=(SocialCondition("Player","reliability",minimum=.45),)),ActionOption("cash","Trade for cash",1)]
    assert m.choose(terms,own_resources={"coins":5},now=0).action_id=="cash"
    m.observe(Episode(0,"Felix",0,"episodic","Aelia kept an earlier delivery.",participants=("Felix","Player"),
        salience=.9,social_signals=(SocialSignal("Player","reliability",.2),)))
    assert m.choose(terms,own_resources={"coins":5},now=0).action_id=="advance"
    m.observe(Episode(1,"Felix",1,"episodic","Aelia missed a witnessed delivery.",participants=("Felix","Player"),
        salience=.9,social_signals=(SocialSignal("Player","reliability",-.5),SocialSignal("Player","obligation",2))))
    decision=m.choose(terms,own_resources={"coins":5},now=2)
    assert decision.action_id=="cash"
    assert m.social("Player","reliability",now=2)=={"value":.2,"evidence_ids":[0,1],"baseline":.5,"basis":"retained witnessed social consequences"}
    reflection=m.reflect(now=2)
    assert reflection["assessments"][0]["evidence_ids"]==[1]
    assert any(s["policy"]=="require verification before extending credit" for s in reflection["assessments"])
    # A real, later positive outcome can revise an evaluation; reflection cannot
    # fabricate that recovery by changing a scalar without an experience.
    m.observe(Episode(3,"Felix",3,"episodic","Aelia kept the next delivery.",participants=("Felix","Player"),
        salience=.9,social_signals=(SocialSignal("Player","reliability",.35),SocialSignal("Player","obligation",-2))))
    assert m.choose(terms,own_resources={"coins":5},now=3).action_id=="advance"
    assert m.social("Player","obligation",now=3)["value"]==0


def test_all_record_types_compete_in_one_hard_capacity_and_complete_bytes_are_measured():
    m=mind(capacity=8,context_records=4)
    for i in range(60):
        m.observe(claim(i,"ready" if i%2 else "blocked",received=i,vintage=i))
        m.reflect(now=i)
        footprint=m.footprint()
        assert footprint["memory_records"]<=8
        assert sum(footprint[k] for k in ("episodic_records","semantic_social_records","revision_records","reflection_records"))==footprint["memory_records"]
        assert footprint["serialized_bytes"]==len(json.dumps(m.to_dict(),sort_keys=True,separators=(',',':'),allow_nan=False).encode())
    assert m.believe("missing","secret",now=60).status=="unknown"
    assert len(json.dumps(m.to_dict()))<30000


@pytest.mark.parametrize("policy",["recency","salience","prediction_error","goal","hybrid"])
def test_retention_policies_are_deterministic_and_never_restore_evicted_episodes(policy):
    def run():
        m=mind(capacity=6,context_records=3,retention_policy=policy)
        m.set_goals([Goal("supply","Obtain usable stock",relevant_keys=(("cargo","condition"),),tags=("supply",))])
        for i in range(30):
            m.observe(claim(i,salience=(i%5)/5))
        return m
    a,b=run(),run()
    assert a.to_dict()==b.to_dict() and a.footprint()["memory_records"]<=6
    assert a.believe("unknown","value",now=31).status=="unknown"


def test_goal_relevance_preserves_a_useful_observation_after_routine_interference():
    retained=mind(capacity=6,context_records=3,retention_policy="goal")
    fifo=mind(capacity=6,context_records=3,retention_policy="recency",consolidation=False)
    for m in (retained,fifo):
        m.set_goals([Goal("supply","Obtain usable stock",relevant_keys=(("cargo","condition"),))])
        m.observe(claim(0,salience=.8))
        for i in range(1,40):
            m.observe(Episode(i,"Felix",i,"episodic","An ordinary witnessed routine."))
    a=retained.choose(options(),own_resources={"coins":4},now=40)
    b=fifo.choose(options(),own_resources={"coins":4},now=40)
    assert a.action_id=="buy" and b.action_id=="verify"
    assert execute_trade(a,actual_ready=True)["utility"]>execute_trade(b,actual_ready=True)["utility"]


def test_goals_resources_and_deadlines_revise_a_plan_without_mutating_an_account():
    m=mind();m.set_goals([Goal("delivery","Keep the delivery",priority=2,deadline=10)])
    candidate=[ActionOption("deliver","Perform delivery",5,goal_id="delivery",costs={"flour":2},duration=4),ActionOption("recover","Seek recovery work",1)]
    resources={"flour":2}
    first=m.choose(candidate,own_resources=resources,now=2)
    assert first.action_id=="deliver" and resources=={"flour":2}
    second=m.choose(candidate,own_resources={"flour":0},now=3)
    assert second.action_id=="recover" and second.previous_action=="deliver"
    third=m.choose(candidate,own_resources=resources,now=8)
    assert third.action_id=="recover" and any("deadline" in message for _,messages in third.rejected for message in messages)
    assert m.reflect(now=11)["goal_states"]==[{"goal_id":"delivery","status":"overdue"}]


def test_options_share_one_context_budget_instead_of_each_reading_the_whole_memory():
    m=mind(capacity=16,context_records=2)
    for i in range(8):
        m.observe(Episode(i,"Felix",i,"observed",f"I observed item{i}.",f"item{i}","available","yes",i))
    candidates=[ActionOption(f"buy{i}",f"Buy item{i}",10-i,conditions=(BeliefCondition(f"item{i}","available","yes"),)) for i in range(8)]
    decision=m.choose(candidates,own_resources={},now=8)
    assert len(decision.context_event_ids)<=2
    assert set(decision.evidence_ids)<=set(decision.context_event_ids)
    assert len(decision.rejected)>=6


def test_snapshot_roundtrip_is_detached_exact_and_cannot_admit_another_agents_memory():
    m=mind();m.observe(claim(1));m.set_goals([Goal("supply","Keep stock",relevant_keys=(("cargo","condition"),))])
    m.choose(options(),own_resources={"coins":4},now=2)
    payload=json.loads(json.dumps(m.to_dict()))
    restored=AgentMind.from_dict(payload)
    assert restored.to_dict()==m.to_dict()
    assert restored.choose(options(),own_resources={"coins":4},now=2)==m.choose(options(),own_resources={"coins":4},now=2)
    detached=m.to_dict();detached["episodes"][0]["value"]="forged"
    assert m.believe("cargo","condition",now=2).value=="ready"
    payload["episodes"][0]["agent_id"]="Lucius"
    with pytest.raises(ValueError,match="another agent"):
        AgentMind.from_dict(payload)


def test_unaccepted_testimony_and_invalid_contracts_cannot_change_a_belief():
    m=mind();bad=asdict(claim(1));bad["accepted"]=False
    m.observe(Episode(**bad));assert m.believe("cargo","condition",now=1).status=="unknown"
    with pytest.raises(ValueError,match="future"):
        claim(2,received=2,vintage=3)
    with pytest.raises(ValueError,match="participant"):
        Episode(3,"Felix",3,"episodic","A private imagined event.",social_signals=(SocialSignal("Player","reliability",-.3),))
    with pytest.raises(ValueError,match="invent"):
        ActionOption("mint","Invent an advance",1,costs={"coins":-3})
    with pytest.raises(ValueError,match="finite"):
        ActionOption("nan","Invalid utility",float("nan"))


def test_rejected_testimony_does_not_hide_a_retained_accepted_fact_in_a_tiny_context():
    m=mind(context_records=1)
    m.observe(claim(0,"blocked",received=0,vintage=0))
    for i in range(1,9):
        rejected=asdict(claim(i,"ready",received=i,vintage=i,source="Dama",salience=1))
        rejected["accepted"]=False
        m.observe(Episode(**rejected))
    assert m.believe("cargo","condition",now=10).value=="blocked"
    assert m.choose(options(),own_resources={"coins":4},now=10).action_id=="verify"
