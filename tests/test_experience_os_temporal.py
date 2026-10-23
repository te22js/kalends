import copy

import pytest

from kalends.events import Ledger
from kalends.experience_os.temporal import (
    TemporalContractViolation, TemporalEngine, select_montage, significance,
)
from kalends.pompeii.temporal import EventClock


def cosmetic(value, **overrides):
    data = {"value": value, "entity": "sky", "_temporal": {
        "role": "cosmetic_assignment", "coalesce_key": "sky-color",
        "writes": ["presentation.sky"], "reads": [], "observed_by": [],
        "idempotent": True, "schedules": False, "semantic_effects": [],
    }}
    data["_temporal"].update(overrides)
    return data


def test_existing_clock_reference_exact_adaptive_preserve_dynamic_reactions():
    results = []
    for mode, strategy in (("live", "exact"), ("compress", "exact"), ("compress", "adaptive")):
        clock, seen = EventClock(), []
        clock.schedule(7, "arrival", {"agent": "Felix"})
        clock.schedule(21, "obligation_due", {})

        def handler(task):
            seen.append(copy.deepcopy(task))
            if task["kind"] == "arrival":
                clock.schedule(clock.now, "belief_revision", {})
                clock.schedule(clock.now + 4, "decision", {})

        engine = TemporalEngine(clock, handler)
        stats = engine.advance(60, mode, strategy)
        assert engine.clock is clock
        assert stats["handler_calls"] == 4
        assert stats["fidelity"]["consequential_handlers_omitted"] == 0
        assert stats["total_lateness"] == 0
        if strategy == "adaptive":
            assert stats["refinements"]["unknown_or_semantic_contract"] == 4
        results.append((seen, clock.snapshot(), stats["task_trace_hash"]))
    assert results[0] == results[1] == results[2]


def test_adaptive_only_coalesces_consecutive_declared_terminal_assignments():
    clock, seen, presentation = EventClock(), [], {}
    for minute, value in ((1, "blue"), (2, "gray"), (3, "white")):
        clock.schedule(minute, "sky_assignment", cosmetic(value))

    def handler(task):
        seen.append(task["key"])
        presentation["sky"] = task["data"]["value"]

    engine = TemporalEngine(clock, handler, [], semantic_probe=lambda: {"cash": 5})
    engine.declare_cosmetic("sky_assignment", writes=["presentation.sky"])
    stats = engine.advance(5, strategy="adaptive")
    assert len(seen) == 1 and presentation == {"sky": "white"}
    assert stats["dispatched"] == 3  # heap work is not claimed to disappear
    assert stats["handler_calls"] == 1 and stats["cosmetic_omitted_count"] == 2
    assert stats["fidelity"]["loss"] == "intermediate declared observation-free presentation assignments"
    assert stats["error_audit"] == []


@pytest.mark.parametrize("barrier", ["obligation_due", "decision", "belief_revision", "routine", "unknown"])
def test_semantic_or_unknown_dependency_forces_refinement(barrier):
    clock, seen = EventClock(), []
    clock.schedule(1, "sky_assignment", cosmetic("blue"))
    clock.schedule(2, barrier)
    clock.schedule(3, "sky_assignment", cosmetic("white"))
    engine = TemporalEngine(clock, lambda task: seen.append(task["kind"]))
    engine.declare_cosmetic("sky_assignment", writes=["presentation.sky"])
    stats = engine.advance(10, strategy="adaptive")
    assert seen == ["sky_assignment", barrier, "sky_assignment"]
    assert stats["cosmetic_omitted_count"] == 0


@pytest.mark.parametrize("contract_change", [
    {"observed_by": ["Player"]}, {"reads": ["beliefs.Felix"]},
    {"semantic_effects": ["resources"]}, {"idempotent": False},
    {"schedules": True}, {"writes": ["cash.Player"]},
    {"writes": [1, "presentation.sky"]},
])
def test_incomplete_or_unsafe_declaration_never_permits_coalescence(contract_change):
    clock, seen = EventClock(), []
    for minute in (1, 2):
        clock.schedule(minute, "sky_assignment", cosmetic(minute, **contract_change))
    engine = TemporalEngine(clock, seen.append)
    engine.declare_cosmetic("sky_assignment", writes=["presentation.sky"])
    assert engine.advance(10, strategy="adaptive")["cosmetic_omitted_count"] == 0
    assert len(seen) == 2


def test_task_metadata_alone_cannot_self_authorize_cosmetic_skipping():
    clock, seen = EventClock(), []
    for minute in (1, 2):
        clock.schedule(minute, "routine", cosmetic(minute))
    engine = TemporalEngine(clock, seen.append)
    assert engine.advance(10, strategy="adaptive")["handler_calls"] == 2
    with pytest.raises(ValueError, match="presentation"):
        engine.declare_cosmetic("routine", writes=["resources.cash"])


@pytest.mark.parametrize("violation", ["ledger", "queue", "semantic"])
def test_declared_handler_contract_violation_is_detected_and_not_called_rollback(violation):
    clock, ledger, state = EventClock(), Ledger(), {"cash": 5}
    clock.schedule(1, "sky_assignment", cosmetic("blue"))

    def handler(task):
        if violation == "ledger":
            ledger.append(clock.now, "state_change", "street", (), {"cash_delta": 1})
        elif violation == "queue":
            clock.schedule(clock.now + 1, "hidden_decision")
        else:
            state["cash"] -= 1

    engine = TemporalEngine(clock, handler, ledger, semantic_probe=lambda: state)
    engine.declare_cosmetic("sky_assignment", writes=["presentation.sky"])
    with pytest.raises(TemporalContractViolation):
        engine.advance(10, strategy="adaptive")
    assert not engine.last_stats["complete"] and engine.last_stats["rollback"] is False
    assert engine.last_stats["error_audit"]


def test_skip_next_and_montage_do_not_make_up_transition_history():
    clock, seen = EventClock(7), []
    engine = TemporalEngine(clock, seen.append)
    clock.schedule(11, "opportunity")
    assert engine.advance(mode="SKIP")["target"] == 11
    assert len(seen) == 1
    assert engine.advance(mode="skip")["target"] == 11
    clock.schedule(15, "obligation_due")
    assert engine.advance(20, mode="montage")["handler_calls"] == 1
    assert engine.last_stats["montage_selection"] == "separate_explicit_access_controlled_operation"
    with pytest.raises(ValueError):
        engine.advance(mode="compress")
    with pytest.raises(ValueError):
        engine.advance(30, mode="live", strategy="adaptive")


def test_naive_baseline_is_honest_about_delayed_consequences():
    clock, seen = EventClock(), []
    clock.schedule(1, "arrival")
    engine = TemporalEngine(clock, seen.append)
    stats = engine.advance(60, strategy="naive")
    assert seen[0]["executed_at"] == 60 and seen[0]["lateness"] == 59
    assert stats["total_lateness"] == 59 and stats["scheduler_mode"] == "naive"


def test_significance_reads_actual_effects_and_treats_routine_movement_conservatively():
    event = {"event_id": 1, "tick": 4, "payload": {"category": "decision", "missed": 2,
        "commitment_updates": [], "belief_revision": {}, "goal_updates": [],
        "relationship_updates": [], "access_add": [], "cash_delta": {"Player": -2}}}
    result = significance(event)
    assert {"resource_shortage", "obligation", "belief_revision", "goal_change", "relationship", "institution", "resource_change", "decision"} <= set(result["reasons"])
    assert significance({"payload": {"category": "routine"}, "etype": "move"})["consequential"]
    assert not significance({"payload": {"category": "presentation_assignment", "observation_free": True}})["consequential"]


def test_montage_enforces_access_and_selects_existing_records_without_mutation():
    events = [
        {"event_id": 1, "tick": 1, "payload": {"category": "routine"}},
        {"event_id": 2, "tick": 2, "payload": {"category": "promise_due", "deadline": 2}},
        {"event_id": 3, "tick": 3, "scope": "private", "payload": {"category": "belief_revision", "value": "secret"}},
        {"event_id": 4, "tick": 4, "payload": {"category": "opportunity"}},
    ]
    before = copy.deepcopy(events)
    selected = select_montage(events, {1, 2, 4}, 2)
    assert [event["event_id"] for event in selected] == [2, 4]
    assert events == before
    assert select_montage(events, [], 5) == []
    assert select_montage(events, {1, 2}, 0) == []
    with pytest.raises(ValueError, match="duplicate"):
        select_montage(events + [events[0]], {1}, 5)
    with pytest.raises(ValueError):
        select_montage(events, [True], 5)


def test_actual_world_adaptive_keeps_routine_gossip_and_obligations_exact():
    from kalends.pompeii.world import PompeiiWorld
    worlds = [PompeiiWorld(seed=41803) for _ in range(2)]
    results = []
    for world, strategy in zip(worlds, ("exact", "adaptive")):
        world.move(location="bakery")
        world.interact("accept_delivery", "Felix")
        engine = TemporalEngine(world.clock, world.on_task, world.ledger)
        stats = engine.advance(7 * 1440, strategy=strategy)
        assert stats["cosmetic_omitted_count"] == 0
        results.append(world.fidelity_state())
    assert results[0] == results[1]
    assert worlds[0].economy.commitments["Player"][0]["status"] == "missed"


def test_benchmark_output_is_never_overwritten(tmp_path):
    from kalends.experience_os.temporal_bench import main
    directory = tmp_path / "existing"
    directory.mkdir()
    marker = directory / "preserved.txt"
    marker.write_text("original")
    with pytest.raises(SystemExit, match="overwrite"):
        main(["--out", str(directory), "--seeds", "41803", "--days", "1", "--repeats", "1"])
    assert marker.read_text() == "original"


def test_benchmark_projects_actual_active_mind_actions_separately_from_legacy_decisions():
    from kalends.experience_os.temporal_bench import comparison, run_world
    reference = run_world("rebirth", 41800, 2, "minute_reference")
    exact = run_world("rebirth", 41800, 2, "conservative_adaptive")
    assert all(comparison(reference, exact)["equal"].values())
    assert reference["cognitive_decision_count"] > 0
    assert reference["projection"]["cognitive_actions"]["Felix"]
    assert reference["projection"]["cognitive_beliefs"]["Felix"]
    count = sum(len(actions) for actions in reference["projection"]["cognitive_actions"].values())
    assert count == reference["cognitive_decision_count"]
