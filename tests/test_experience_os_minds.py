"""Minds V3 on the preserved V2 memory and real Pompeii action primitives."""
import copy
from types import SimpleNamespace

import pytest

from kalends.memory.base import Experience
from kalends.experience_os.minds import (
    ActionOption, AgentMind, BeliefCondition, Episode, Goal, MindConfig,
    PersistentMind, PompeiiMindBridge, SocialCondition, SocialSignal,
    attach_pompeii_minds,
)


def claim(identifier, value="available", *, agent="Felix", source=None, origin=None, salience=.5):
    return Episode(identifier, agent, identifier, "told" if source else "observed",
        "The dated supply report.", "grain", "supply", value, identifier,
        source_agent=source, origin_event=identifier if origin is None or isinstance(origin, str) else origin,
        origin_observer=origin if isinstance(origin, str) else None,
        salience=salience, goal_tags=("supply",))


def procurement():
    return [ActionOption("buy", "Buy one unit", 4, "supply", costs={"coins": 2},
        conditions=(BeliefCondition("grain", "supply", "available", max_age=180),)),
        ActionOption("verify", "Check before committing", 1, "supply", costs={"coins": 1})]


def goals():
    return [Goal("supply", "Have enough material for tomorrow", relevant_keys=(("grain", "supply"),), tags=("supply",))]


def run(mind, episodes=(), *, now=1, owned=None, options=None, current_goals=None):
    return mind.cycle(episodes, goals() if current_goals is None else current_goals,
        procurement() if options is None else options,
        {"coins": 5} if owned is None else owned, now)


def test_reuses_existing_contracts_and_reports_complete_loop_without_executing():
    mind = PersistentMind("Felix")
    assert isinstance(mind, AgentMind)
    owned = {"coins": 5}
    trace = run(mind, [claim(1)], owned=owned)
    assert trace["decision"]["action_id"] == "buy"
    assert list(trace["stages"]) == ["Observe", "Encode", "Retrieve", "Update Beliefs", "Select Goals", "Plan", "Act", "Evaluate", "Consolidate"]
    assert trace["stages"]["Act"]["status"] == "awaiting authoritative execution"
    assert trace["plan"]["status"] == "planned" and owned == {"coins": 5}
    assert "serialized_bytes" in trace["footprint"]


def test_distinguishes_direct_testimony_unknown_and_derived_inference():
    direct = run(PersistentMind("Felix"), [claim(1)])
    told = run(PersistentMind("Felix"), [claim(1, source="Marcus", origin="Marcus")])
    unknown = run(PersistentMind("Felix"))
    assert direct["stages"]["Update Beliefs"][0]["epistemic_kind"] == "direct"
    assert told["stages"]["Update Beliefs"][0]["epistemic_kind"] == "testimony"
    assert "communicated" in told["stages"]["Update Beliefs"][0]["lineage_kind"]
    assert unknown["stages"]["Update Beliefs"][0]["epistemic_kind"] == "unknown"
    assert unknown["decision"]["action_id"] == "verify"


def test_provenance_is_retained_source_information_and_unknown_after_forgetting():
    mind = PersistentMind("Felix", MindConfig(capacity=2, context_records=1, consolidation=False, retention_policy="recency"))
    mind.observe(claim(1, source="Dama", origin="Marcus"))
    source = mind.provenance(1)
    assert source["kind"] == "testimony" and source["source_agent"] == "Dama"
    assert source["claimed_origin_observer"] == "Marcus"
    assert mind.retained_event_ids() == (1,)
    for identifier in (2, 3):
        mind.observe(Episode(identifier, "Felix", identifier, "episodic", "A later own experience."))
    assert mind.provenance(1) == {"event_id": 1, "kind": "unknown", "retained": False}
    assert mind.retained_event_ids() == (2, 3)


def test_private_foreign_or_future_observations_are_rejected_before_mutation():
    mind = PersistentMind("Felix")
    before = mind.to_dict()
    for episodes in ([claim(1, agent="Sabina")], [claim(2)]):
        with pytest.raises(ValueError, match="own episodes"):
            run(mind, episodes)
        assert mind.to_dict() == before
    with pytest.raises(TypeError):
        mind.cycle([], goals(), procurement(), {"coins": 5}, 1, archive={"secret": 1})


def test_invalid_option_contract_does_not_partially_admit_an_episode():
    mind = PersistentMind("Felix"); before = mind.to_dict()
    with pytest.raises(ValueError):
        run(mind, [claim(1)], options=[])
    assert mind.to_dict() == before


def test_new_evidence_revises_an_actual_pending_plan():
    mind = PersistentMind("Felix")
    first = run(mind, [claim(1)])
    second = run(mind, [claim(2, "disrupted")], now=2)
    assert first["decision"]["action_id"] == "buy"
    assert second["decision"]["action_id"] == "verify"
    assert mind.plans[0].status == "revised" and mind.current_plan.previous_plan_id == first["plan"]["plan_id"]
    assert second["stages"]["Plan"]["revision"] == "revised"
    assert mind.believe("grain", "supply", now=2).value == "disrupted"


def test_changed_goal_cancels_old_plan_and_selects_independent_goal():
    mind = PersistentMind("Felix")
    opts = [ActionOption("supply-action", "Do supply work", 3, "supply"),
        ActionOption("care-action", "Attend a care obligation", 2, "care")]
    run(mind, options=opts)
    trace = run(mind, now=2, options=opts, current_goals=[Goal("supply", "Supply", status="completed"), Goal("care", "Care for a dependent")])
    assert trace["decision"]["action_id"] == "care-action"
    assert mind.plans[0].status == "revised" and mind.current_plan.goal_id == "care"
    assert dict(trace["decision"]["rejected"])["supply-action"] == ["the associated goal is inactive or overdue"]


def test_resource_loss_cancels_supported_action_without_fabricated_execution():
    mind = PersistentMind("Felix"); run(mind, [claim(1)])
    trace = run(mind, now=2, owned={"coins": 0})
    assert trace["decision"]["action_id"] is None
    assert mind.current_plan.status == "cancelled"
    assert mind.current_plan.outcome and "previous" in mind.current_plan.outcome


def test_unchanged_supported_plan_persists_with_same_identity_and_updates_evidence():
    mind = PersistentMind("Felix")
    first = run(mind, [claim(1)])
    second = run(mind, [claim(2)], now=2)
    assert second["plan"]["plan_id"] == first["plan"]["plan_id"]
    assert second["plan"]["evidence_ids"] == [2]
    assert second["stages"]["Plan"]["revision"] == "continued"
    assert len(mind.plans) == 1


def test_feedback_is_explicit_bounded_and_cannot_be_faked_from_proposal():
    mind = PersistentMind("Felix"); run(mind, [claim(1)])
    for action, outcome, refs in (("foreign", "succeeded", (1,)), ("buy", "maybe", (1,)), ("buy", "succeeded", (999,))):
        before = mind.to_dict()
        with pytest.raises(ValueError):
            mind.evaluate(action, outcome, now=1, evidence_ids=refs)
        assert mind.to_dict() == before
    result = mind.evaluate("buy", "failed", now=1, evidence_ids=(1,), detail="World rejected the actual transaction.")
    assert result["status"] == "failed"
    assert mind.current_plan.status == "failed"
    assert mind.believe("grain", "supply", now=1).value == "available"
    trace = run(mind, now=2)
    assert trace["plan"]["plan_id"] == 2  # An explicit retry is a new plan.


def test_social_obligations_require_witnessed_participation_and_not_hearsay():
    mind = PersistentMind("Felix")
    receipt = Episode(1, "Felix", 1, "episodic", "I accepted a personal obligation.",
        participants=("Felix", "Player"), social_signals=(SocialSignal("Player", "obligation", 2), SocialSignal("Player", "reliability", -.25)))
    trace = run(mind, [receipt])
    assert mind.social("Player", "obligation", now=1)["value"] == 2
    pattern = trace["stages"]["Consolidate"]["patterns"]
    assert {p["kind"] for p in pattern} == {"inference"}
    assert {i for p in pattern for i in p["evidence_ids"]} == {1}
    assert mind.social("Player", "reliability", now=1)["value"] == .25
    assert mind.social("Marcus", "reliability", now=1)["evidence_ids"] == []
    with pytest.raises(ValueError, match="direct personal"):
        Episode(2, "Felix", 2, "told", "Someone says the promise was kept.", source_agent="Marcus",
            participants=("Player",), social_signals=(SocialSignal("Player", "reliability", .2),))


def test_consolidation_competes_with_memory_and_does_not_multiply_a_source():
    mind = PersistentMind("Felix", MindConfig(capacity=6, context_records=2))
    for identifier in range(1, 25):
        receipt = Episode(identifier, "Felix", identifier, "episodic", "An actual personal dealing.",
            participants=("Player",), social_signals=(SocialSignal("Player", "reliability", -.05),), salience=.8)
        run(mind, [receipt], now=identifier)
        assert mind.footprint()["memory_records"] <= 6
        assert len(mind._reflections) <= 1
        assert len(mind.plans) <= 4
        refs = {i for r in mind._reflections for i in r["evidence_ids"]}
        assert len(refs) <= 2 and refs <= set(range(1, identifier + 1))
    # Repeating a consolidation does not create another social signal.
    before = mind.social("Player", "reliability", now=24)
    mind.consolidate(now=24); mind.consolidate(now=24)
    assert mind.social("Player", "reliability", now=24) == before


@pytest.mark.parametrize("policy", ["recency", "salience", "goal", "hybrid"])
def test_all_requested_retention_strategies_obey_same_record_and_context_budgets(policy):
    mind = PersistentMind("Felix", MindConfig(capacity=8, context_records=3, retention_policy=policy))
    for identifier in range(1, 40):
        trace = run(mind, [claim(identifier, salience=(identifier % 5) / 5)], now=identifier)
        assert trace["footprint"]["memory_records"] <= 8
        assert len(trace["decision"]["context_event_ids"]) <= 3
        assert len(mind.plans) <= 4
    assert mind.config.retention_policy == policy


def test_disabled_consolidation_has_no_hidden_pattern_store():
    mind = PersistentMind("Felix", MindConfig(consolidation=False))
    trace = run(mind, [claim(1)])
    assert trace["stages"]["Consolidate"] == {"enabled": False, "patterns": [], "evidence_ids": []}
    assert not mind._semantic and not mind._reflections and not mind._revisions


def test_snapshot_is_versioned_detached_exact_and_continues_identically():
    mind = PersistentMind("Felix"); run(mind, [claim(1)]); run(mind, [claim(2, "disrupted")], now=2)
    snapshot = mind.to_dict(); restored = PersistentMind.from_dict(snapshot)
    assert restored.to_dict() == snapshot
    assert run(mind, [claim(3)], now=3) == run(restored, [claim(3)], now=3)
    assert restored.to_dict() == mind.to_dict()
    snapshot["base"]["episodes"].clear()
    assert restored._episodes
    with pytest.raises(ValueError, match="version"):
        PersistentMind.from_dict({"version": 1})


@pytest.mark.parametrize("mutation", ["capacity", "foreign_memory", "too_many_plans", "invalid_plan", "unknown_field", "future_feedback"])
def test_snapshot_rejects_budget_identity_and_plan_corruption(mutation):
    mind = PersistentMind("Felix"); run(mind, [claim(1)])
    value = mind.to_dict()
    if mutation == "capacity":
        value["plan_capacity"] = 999
    elif mutation == "foreign_memory":
        value["base"]["episodes"][0]["agent_id"] = "Sabina"
    elif mutation == "too_many_plans":
        value["plans"] *= 5
    elif mutation == "invalid_plan":
        value["plans"][0]["status"] = "magically completed"
    elif mutation == "unknown_field":
        value["private_archive"] = ["secret"]
    else:
        value["plans"][0]["updated_at"] = 0
    with pytest.raises(ValueError):
        PersistentMind.from_dict(value)


def test_cycle_cannot_go_back_in_time():
    mind = PersistentMind("Felix"); run(mind, [claim(2)], now=2)
    before = mind.to_dict()
    with pytest.raises(ValueError, match="back"):
        run(mind, now=1)
    assert mind.to_dict() == before


def test_feedback_advances_cognitive_time_without_running_another_cycle():
    mind = PersistentMind("Felix"); run(mind, [claim(1)])
    mind.evaluate("buy", "succeeded", now=5, evidence_ids=(1,))
    before = mind.to_dict()
    with pytest.raises(ValueError, match="back"):
        run(mind, now=2)
    assert mind.to_dict() == before
    assert PersistentMind.from_dict(before).to_dict() == before


def test_six_minds_use_legitimate_own_stream_and_no_canonical_archive():
    from kalends.pompeii.district import PEOPLE
    accesses = []
    private = {"Marcus": Experience(0, "observed", "grain", "supply", "available", None, 0, True, 1, "My direct inspection.")}
    class NoArchiveWorld:
        minute = 0
        economy = SimpleNamespace(cash={a: r["cash"] for a, r in PEOPLE.items()}, inventory={a: r["inventory"] for a, r in PEOPLE.items()})
        state = SimpleNamespace(agent_locations={a: r["location"] for a, r in PEOPLE.items()})
        def remembered(self, agent):
            accesses.append(agent)
            return [private[agent]] if agent in private else []
        def __getattr__(self, name):
            raise AssertionError("Forbidden world access: " + name)
    bridge = PompeiiMindBridge(); traces = bridge.sync(NoArchiveWorld())
    assert set(traces) == set(PEOPLE) and accesses == list(PEOPLE)
    assert bridge.minds["Marcus"].believe("grain", "supply", now=0).value == "available"
    assert bridge.minds["Felix"].believe("grain", "supply", now=0).status == "unknown"
    assert traces["Marcus"]["decision"]["action_id"] == "purchase"
    assert traces["Felix"]["decision"]["action_id"] == "inspection"
    assert traces["Chreste"]["decision"]["action_id"] == "routine"
    assert traces["Dama"]["decision"]["action_id"] == "routine"


def test_single_actor_decision_does_not_replan_other_five_and_bridge_restore_exact():
    from kalends_rebirth.world import RebirthWorld
    world = RebirthWorld(); bridge = PompeiiMindBridge(MindConfig(capacity=8, context_records=3))
    before = {a: m.to_dict() for a, m in bridge.minds.items()}
    trace = bridge.cycle_for(world, "Marcus")
    assert trace["agent_id"] == "Marcus"
    assert all(m.to_dict() == before[a] for a, m in bridge.minds.items() if a != "Marcus")
    restored = PompeiiMindBridge(previous=bridge.to_dict())
    assert restored.to_dict() == bridge.to_dict()
    assert bridge.sync(world) == restored.sync(world)


def test_bridge_does_not_resurrect_forgotten_accessible_old_records():
    from kalends_rebirth.world import RebirthWorld
    world = RebirthWorld(); bridge = PompeiiMindBridge(MindConfig(capacity=4, context_records=2, retention_policy="recency"))
    bridge.decide(world, "Marcus")
    for identifier in range(1000, 1010):
        bridge.minds["Marcus"].observe(Episode(identifier, "Marcus", identifier, "episodic", "An admitted later personal occurrence."))
    assert bridge.minds["Marcus"].believe("grain", "supply", now=1010).status == "unknown"
    later_view = SimpleNamespace(minute=1010, economy=world.economy, state=world.state, remembered=world.remembered)
    bridge.decide(later_view, "Marcus")
    assert bridge.minds["Marcus"].believe("grain", "supply", now=1010).status == "unknown"


def test_real_world_purchase_is_independent_material_and_receipt_grounded():
    from kalends_rebirth.world import RebirthWorld
    world = RebirthWorld(); bridge = PompeiiMindBridge()
    old_hash = world.ledger.content_hash()
    trace = bridge.decide(world, "Marcus")
    assert trace["decision"]["action_id"] == "purchase"
    assert world.ledger.content_hash() == old_hash  # Planning itself is read-only.
    before_cash = world.economy.cash["Marcus"]; before_goods = world.economy.inventory["Marcus"]
    event = world._purchase("Marcus", 1)
    assert world.economy.cash["Marcus"] < before_cash and world.economy.inventory["Marcus"] == before_goods + 1
    bridge.admit(world, "Marcus")
    feedback = bridge.minds["Marcus"].evaluate("purchase", "succeeded", now=world.minute, evidence_ids=(event.event_id,))
    assert feedback["evidence_ids"] == [event.event_id]
    assert bridge.minds["Marcus"].current_plan.status == "succeeded"
    assert not world.v2_active()  # The legacy V2 market was neither replaced nor activated.


def test_attach_does_not_mutate_real_world_or_activate_legacy_market():
    from kalends_rebirth.world import RebirthWorld
    world = RebirthWorld(); before = copy.deepcopy(world.fidelity_state()); ledger_hash = world.ledger.content_hash()
    bridge = attach_pompeii_minds(world)
    assert len(bridge.minds) == 6
    assert world.fidelity_state() == before and world.ledger.content_hash() == ledger_hash
    assert not world.v2_active()
