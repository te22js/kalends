"""Exact single-message interventions, kept outside the frozen study path."""
import json

import pytest

from kalends.actionbench.policy import AlwaysDeferPolicy
from kalends.city import CityConfig, CitySimulation
from kalends.city.causal import INTERPRETATION, main, verify_message_dependency


def target(sim, agent="Livia", tick=2):
    return next(d for d in sim.decisions if d["agent"] == agent and d["tick"] == tick)


def queue(sim, speaker="Dama", listener="Livia", tick=1):
    return next(e for e in sim.ledger.events if e.payload.get("category") == "message_queued"
                and e.payload["speaker"] == speaker and e.payload["listener"] == listener and e.tick == tick)


def unchanged_state(sim):
    return json.dumps(sim.snapshot(), sort_keys=True), {a: vars(p).copy() for a, p in sim._policies.items()}


def test_actual_message_deletion_changes_first_livia_decision_and_preserves_prefix():
    sim = CitySimulation(CityConfig(seed=42)).run()
    before = unchanged_state(sim)
    decision, message = target(sim), queue(sim)
    result = verify_message_dependency(sim, decision["event_id"])
    assert result["status"] == "verified"
    assert result["message_event_id"] == message.event_id
    assert result["changed_action"] and result["changed_prediction"]
    assert result["original"]["action"] == "reserve"
    assert result["original"]["predicted_value"] == "disrupted"
    assert result["original"]["loss"] == 2
    assert result["altered"]["action"] == "defer"
    assert result["altered"]["predicted_value"] == "unknown"
    assert result["altered"]["loss"] == 0
    boundary = CitySimulation(sim.config).step(message.tick + 1)
    assert result["shared_prefix_hash"] == boundary.ledger.content_hash()
    assert result["shared_prefix_count"] == len(boundary.ledger)
    assert boundary.ledger.to_json() == [e.to_dict() for e in sim.ledger.events if e.tick <= message.tick]
    assert result["intervention"] == {"kind": "remove_message", "event_id": message.event_id, "tick": message.tick}
    assert result["interpretation"] == INTERPRETATION
    assert unchanged_state(sim) == before


def test_structural_ancestor_can_be_inert_under_actual_deletion():
    sim = CitySimulation(CityConfig(seed=42)).run()
    decision = target(sim, "Marcus", 5)
    result = verify_message_dependency(sim, decision["event_id"])
    assert result["status"] == "verified"
    assert not result["changed_action"]
    assert not result["changed_prediction"]
    assert result["original"]["action"] == result["altered"]["action"] == "reserve"
    assert result["original"]["loss"] == result["altered"]["loss"] == 2
    ancestor_ids = {e["event_id"] for e in sim.trace(decision["event_id"])["ancestors"]}
    assert result["message_event_id"] in ancestor_ids


def test_explicit_old_ancestor_can_change_whether_future_opportunity_exists():
    sim = CitySimulation(CityConfig(seed=0, communication_depth=1)).run()
    decision = target(sim, "Marcus", 14)
    message = queue(sim, listener="Marcus")
    result = verify_message_dependency(sim, decision["event_id"], message.event_id)
    assert result["status"] == "verified" and result["changed_action"]
    assert result["original"]["action"] == "defer"
    assert result["altered"] == {"action": "no_opportunity", "predicted_value": "not_evaluated",
                                 "loss": None, "event_id": None}


def test_no_queued_ancestor_is_explicitly_unsupported():
    sim = CitySimulation(CityConfig(seed=42)).run()
    result = verify_message_dependency(sim, target(sim, "Flavia")["event_id"])
    assert result["status"] == "unsupported" and not result["supported"]
    assert "no queued-message ancestor" in result["reason"]
    assert result["altered"] is result["changed_action"] is None


def test_a_message_already_delivered_at_tick_boundary_is_not_deleted_retroactively(monkeypatch):
    original_queue = CitySimulation._queue

    def immediate_queue(self, tick, speaker, listener, exp, depth=1, delay=None):
        return original_queue(self, tick, speaker, listener, exp, depth, delay=0)

    monkeypatch.setattr(CitySimulation, "_queue", immediate_queue)
    sim = CitySimulation(CityConfig(seed=42)).step(3)
    before = unchanged_state(sim)
    result = verify_message_dependency(sim, target(sim)["event_id"], queue(sim).event_id)
    assert result["status"] == "unsupported"
    assert "no longer pending" in result["reason"]
    assert unchanged_state(sim) == before


@pytest.mark.parametrize("decision_id", (-1, 100000, True, "10", 0))
def test_invalid_decision_targets_raise_without_changing_simulation(decision_id):
    sim = CitySimulation(CityConfig(seed=42)).step(3)
    before = unchanged_state(sim)
    with pytest.raises(ValueError):
        verify_message_dependency(sim, decision_id)
    assert unchanged_state(sim) == before


@pytest.mark.parametrize("message_id", (-1, 100000, True, "5", 0, 6, 10))
def test_message_target_must_be_a_real_queued_structural_ancestor(message_id):
    sim = CitySimulation(CityConfig(seed=42)).step(3)
    before = unchanged_state(sim)
    with pytest.raises(ValueError):
        verify_message_dependency(sim, target(sim)["event_id"], message_id)
    assert unchanged_state(sim) == before


def test_branch_and_nondefault_custom_policies_are_rejected():
    sim = CitySimulation(CityConfig(seed=42)).step(3)
    branch = sim.fork({"kind": "none"})
    with pytest.raises(ValueError, match="original city timeline"):
        verify_message_dependency(branch, target(branch)["event_id"])
    custom = CitySimulation(CityConfig(seed=42), lambda *_: AlwaysDeferPolicy()).step(3)
    with pytest.raises(ValueError, match="default memory policies"):
        verify_message_dependency(custom, target(custom)["event_id"])


def test_modified_factual_prefix_is_rejected_instead_of_claiming_a_verified_result():
    sim = CitySimulation(CityConfig(seed=42)).step(3)
    queue(sim).payload["title"] = "A non-reproducible external ledger edit"
    before = unchanged_state(sim)
    with pytest.raises(ValueError, match="prefix cannot be reproduced"):
        verify_message_dependency(sim, target(sim)["event_id"])
    assert unchanged_state(sim) == before


def test_modified_evaluator_record_is_rejected_after_replay():
    sim = CitySimulation(CityConfig(seed=42)).step(3)
    target(sim)["action"] = "verify"
    before = unchanged_state(sim)
    with pytest.raises(ValueError, match="decision cannot be reproduced"):
        verify_message_dependency(sim, target(sim)["event_id"])
    assert unchanged_state(sim) == before


def test_result_is_deterministic_for_current_or_later_factual_prefix():
    early = CitySimulation(CityConfig(seed=42)).step(3)
    decision_id = target(early)["event_id"]
    first = verify_message_dependency(early, decision_id)
    second = verify_message_dependency(early, decision_id)
    early.run()
    assert first == second == verify_message_dependency(early, decision_id)


def test_optional_cli_emits_the_actual_deletion_demonstration(capsys):
    main([])
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "verified" and result["changed_action"]
    assert result["decision_semantic_key"] == "decision:2:Livia"
