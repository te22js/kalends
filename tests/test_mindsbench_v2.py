"""Synthetic outcome evaluator, funding, fair-access and study-guard regressions."""
import copy
from dataclasses import asdict, replace
import json

import pytest

from kalends_rebirth.minds import Episode, Goal
from kalends_rebirth import mindsbench_v2 as bench


@pytest.mark.parametrize("family",bench.FAMILIES)
def test_development_controls_execute_all_arms_with_conserved_resources_and_real_budgets(family):
    for seed in bench.DEVELOPMENT_SEEDS[:4]:
        case=bench.generate_case(seed,family)
        tape=bench.canonical([asdict(e) for e in case.observations])
        for arm in bench.ARMS:
            result=bench.run_arm(case,arm)
            assert result["footprint"]["memory_records"]<= (256 if arm in bench.REFERENCE_ARMS else bench.CAPACITY)
            assert not result["unsupported_evidence_ids"]
            assert abs(sum(result["cash"].values())-(case.initial_cash+240))<1e-9
            assert sum(result["goods"].values())==4
            assert result["footprint"]["serialized_bytes"]>0
            assert all(len(d["context_event_ids"])<= (256 if arm in bench.REFERENCE_ARMS else bench.CONTEXT) for d in result["decisions"])
        assert bench.canonical([asdict(e) for e in case.observations])==tape


def test_changing_hidden_truth_does_not_change_first_decision_input_or_actor_belief():
    case=bench.generate_case(97000,"correlated_testimony")
    altered=replace(case,actual_ready=not case.actual_ready)
    for arm in bench.PRIMARY_ARMS:
        first=bench.run_arm(case,arm);second=bench.run_arm(altered,arm)
        assert first["decisions"][0]==second["decisions"][0]
        # Outcomes can diverge and paid verification can legitimately reveal it;
        # the initial tape itself contains no hidden-truth shortcut.
        assert bench.digest([asdict(e) for e in case.observations])==bench.digest([asdict(e) for e in altered.observations])


def test_correlated_relays_cannot_become_independent_by_changing_only_speaker():
    case=bench.generate_case(97000,"correlated_testimony")
    minds={name:bench.make_mind(name) for name in ("mind","no_lineage")}
    for mind in minds.values():
        mind.set_goals([Goal("settle","Make the bargain",relevant_keys=((case.subject,case.predicate),))])
        for episode in case.observations:mind.observe(episode)
    grounded=minds["mind"].believe(case.subject,case.predicate,now=case.now)
    ablated=minds["no_lineage"].believe(case.subject,case.predicate,now=case.now)
    assert len(grounded.source_groups)==1
    assert len(ablated.source_groups)==3
    assert grounded.value==ablated.value=="yes"


def test_verification_cost_changes_actual_cash_and_correction_diagnostic_uses_received_result():
    case=bench.generate_case(97001,"correlated_testimony")
    result=bench.run_arm(case,"mind")
    assert result["verification_used"]
    payments=[e for e in result["ledger"] if e.get("reason")=="paid direct check"]
    assert len(payments)==1 and payments[0]["coins"]==case.verification_cost
    assert result["cash"]["Inspector"]==20+case.verification_cost
    assert result["final_belief"]["value"]=="no"
    assert not result["stale_against_admitted_evidence"]
    assert result["goal_completed"] and result["utility"]==2


def test_correct_gossip_makes_unnecessary_check_cost_real_utility():
    case=bench.generate_case(97000,"correlated_testimony")
    cautious=bench.run_arm(case,"mind");trusting=bench.run_arm(case,"no_lineage")
    assert cautious["verification_used"] and not trusting["verification_used"]
    assert cautious["utility"]==trusting["utility"]-case.verification_cost
    assert cautious["goal_completed"] and trusting["goal_completed"]


def test_privileged_reference_is_an_actual_attainable_upper_bound_on_development_controls():
    for family in bench.FAMILIES:
        for seed in bench.DEVELOPMENT_SEEDS[:4]:
            case=bench.generate_case(seed,family)
            upper=bench.run_arm(case,"omniscient_upper_bound")
            assert not upper["verification_used"]
            assert all(bench.run_arm(case,arm)["utility"]<=upper["utility"] for arm in bench.PRIMARY_ARMS)


def test_option_construction_and_selection_share_one_complete_context_budget(monkeypatch):
    mind=bench.make_mind("fifo")
    case=bench.generate_case(97000,"temporal_correction")
    for n in range(12):
        mind.observe(Episode(n,"Merchant",n,"observed",f"supplier {'available' if n<6 else 'verified'} yes",
            "supplier","available" if n<6 else "verified","yes",n))
    mind.set_goals([Goal("settle","Finish",deadline=case.deadline,relevant_keys=(("supplier","available"),("supplier","verified")))])
    actual=mind._retrieve;reads=[]
    def log(*args,**kwargs):
        records=actual(*args,**kwargs);reads.extend(r["event_id"] for r in records);return records
    monkeypatch.setattr(mind,"_retrieve",log)
    decision=bench.options_from_view(mind,case.public(),own_coins=30,now=case.now,verified=False)
    assert len(set(reads))<=bench.CONTEXT
    assert set(decision.context_event_ids)==set(reads)
    assert set(decision.evidence_ids)<=set(reads)


def test_correction_trace_records_immediate_recovery_and_unrecovered_revision_ablation():
    case=bench.generate_case(97001,"temporal_correction")
    revised=bench.run_arm(case,"mind");frozen=bench.run_arm(case,"no_revision")
    assert revised["correction_recovery"][0]["target"]=="no"
    assert revised["correction_recovery"][0]["recovery_observations"]==0
    assert frozen["correction_recovery"][0]["recovery_observations"] is None
    assert frozen["obsolete_steps"]>revised["obsolete_steps"]


def test_credit_and_information_outcomes_are_funded_transfers_not_action_label_rewards():
    good_credit=bench.generate_case(97002,"personal_history")
    result=bench.run_arm(good_credit,"omniscient_upper_bound")
    assert any(e.get("reason")=="earlier kept promise" for e in result["ledger"])
    assert any(e.get("reason")=="settle kept obligation" for e in result["ledger"])
    assert result["goods"]["Merchant"]==0 and result["utility"]==6
    report=bench.generate_case(97002,"strategic_communication")
    result=bench.run_arm(report,"omniscient_upper_bound")
    assert result["reports"]["Buyer"]==["exclusive dispatch"]
    assert any(e.get("source")=="Buyer" and e.get("target")=="Merchant" for e in result["ledger"])
    assert result["utility"]==6


@pytest.mark.parametrize("problem",("funds","stock","deadline","buyer"))
def test_rejected_execution_is_atomic_and_does_not_mint_resources(problem):
    family="strategic_communication" if problem=="buyer" else "temporal_correction"
    case=bench.generate_case(97000,family);world=bench.Economy(case)
    if problem=="funds":world.cash["Merchant"]=0
    elif problem=="stock":world.goods["Preferred"]=0
    elif problem=="deadline":world.now=case.deadline
    elif problem=="buyer":world.cash["Buyer"]=0
    before=copy.deepcopy(world.__dict__)
    with pytest.raises(ValueError):world.execute("preferred_testimony")
    assert world.__dict__==before


def test_prospective_source_guard_refuses_mismatch_before_creating_output(tmp_path):
    registration=tmp_path/"registration.json"
    registered=bench.design();registered["source"]["sha256"]="changed"
    registration.write_text(json.dumps(registered))
    destination=tmp_path/"heldout"
    with pytest.raises(ValueError,match="registration/source"):
        bench.run(destination,phase="heldout",registration=registration)
    assert not destination.exists()


def test_failed_pilot_keeps_prior_rows_and_explicit_failure_record(tmp_path,monkeypatch):
    destination=tmp_path/"failed-pilot"
    actual=bench.run_arm;count=0
    def fail_second_world(case,arm):
        nonlocal count
        count+=1
        if count>len(bench.ARMS):raise RuntimeError("Injected evaluator validation failure")
        return actual(case,arm)
    monkeypatch.setattr(bench,"run_arm",fail_second_world)
    with pytest.raises(RuntimeError,match="Injected"):
        bench.run(destination,phase="pilot")
    failure=json.loads((destination/"failure.json").read_text())
    assert failure["completed_rows"]==1 and failure["family"]==bench.FAMILIES[1]
    assert len((destination/"raw.jsonl").read_text().splitlines())==1
    assert not (destination/"summary.json").exists()


def test_no_private_observation_or_arbitrary_claim_is_extracted_from_world():
    mind=bench.make_mind("mind")
    case=bench.generate_case(97000,"long_absence")
    for episode in case.observations:mind.observe(episode)
    secret=Episode(9000,"OtherAgent",case.now,"observed","An inaccessible balance is large.","private_balance","amount","999",case.now)
    with pytest.raises(ValueError):mind.observe(secret)
    assert mind.believe("private_balance","amount",now=case.now).status=="unknown"
