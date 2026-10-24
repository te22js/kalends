"""Consequential outcome, checkpoint and visibility checks for the new study."""
from dataclasses import replace

import pytest

from kalends.next_phase import diagnostic as study
from kalends_rebirth.minds import Episode


def test_old_pending_plan_is_not_a_causal_planner():
    result = study.old_plan_diagnostic()
    assert result["same"]
    assert result["original_decisions"] == ["equal", "protect-stable"]


def test_memory_headroom_changes_actual_obligation_settlements():
    spec = study.DEV[0]
    bounded = study.run_case(spec, 7, "v3_hybrid")
    reference = study.run_case(spec, 7, "admissible_history")
    assert not bounded["chain_complete"] and reference["chain_complete"]
    assert bounded["metrics"]["promises_missed"] == 1
    assert reference["metrics"]["promises_kept"] == 2
    assert reference["goal_register"]["deferred"]["completed_at"] > reference["goal_register"]["prerequisite"]["completed_at"]
    assert bounded["metrics"]["credits_spent"] == 1
    assert all(c["receipt_id"] is not None for c in reference["commands"])


def test_current_report_control_and_same_action_contracts():
    a = study.run_case(study.DEV[2], 0, "current_observation")
    b = study.run_case(study.DEV[2], 0, "v3_hybrid")
    assert a["chain_complete"] and b["chain_complete"]
    assert {t["option_hash"] for t in a["trace"]} == {t["option_hash"] for t in b["trace"]}
    assert a["trace"][-1]["decision"]["action_id"] == "equal"
    assert b["trace"][-1]["decision"]["action_id"] == "equal"


def test_world_and_mind_session_restores_and_replay_are_exact():
    first = study.run_case(study.DEV[0], 3, "v3_hybrid")
    second = study.run_case(study.DEV[0], 3, "v3_hybrid")
    assert first["scientific_hash"] == second["scientific_hash"]
    assert len(first["session_restores"]) == 4
    for checkpoint in first["session_restores"]:
        restored = study.restore_world(checkpoint["world_checkpoint"])
        assert study.digest(study.world_snapshot(restored)) == checkpoint["world_sha256"]
        assert checkpoint["exact"]
    assert all(t["controller_plan_read"]["phase"] == "review_after_interruption" for t in first["trace"])
    assert [t["controller_plan_read"]["round"] for t in first["trace"]] == [0, 0, 1]


def test_relevant_record_intervention_and_irrelevant_distractor():
    spec = replace(study.DEV[0], distractors=0)
    kept = study.run_case(spec, 0, "admissible_history")
    removed = study.run_case(spec, 0, "admissible_history", remove_report=True)
    distracted = study.run_case(replace(spec, distractors=24), 0, "admissible_history")
    assert kept["chain_complete"] and not removed["chain_complete"]
    assert kept["decisions"] == distracted["decisions"]
    assert kept["trace"][0]["option_hash"] == removed["trace"][0]["option_hash"]


def test_hidden_change_is_information_limited_and_not_exposed():
    row = study.run_case(study.DEV[3], 1, "admissible_history")
    assert not row["chain_complete"] and row["information_limit"]
    private_condition_ids = {e["event_id"] for e in row["ledger"] if e["payload"].get("category") == "condition" and e["actors"] == ["team_b"]}
    assert private_condition_ids.isdisjoint({e["event_id"] for e in row["admitted_stream"]})
    assert all("condition" not in trace["public_register"] for trace in row["trace"])


def test_visibility_adapter_rejects_foreign_unsupported_and_altered_records():
    world = study.make_world(study.DEV[0], 0)
    with pytest.raises(ValueError, match="unsupported"):
        study.verified_ingress(world, [Episode(9999, "Player", 0, "episodic", "Unrecorded claim")])
    own = world.player_stream[0]
    with pytest.raises(ValueError, match="unsupported"):
        study.verified_ingress(world, [replace(own, agent_id="team_b")])
    with pytest.raises(ValueError, match="unsupported"):
        study.verified_ingress(world, [replace(own, text="Altered canonical content")])
    assert study.verified_ingress(world, [own]) == [own]


def test_complete_state_is_charged_and_no_provider_is_used():
    row = study.run_case(study.DEV[0], 0, "v3_hybrid")
    assert row["max_total_state_bytes"] <= study.STATE_BYTES
    assert row["accessible_byte_cap"] == study.STATE_BYTES
    assert row["live_model_calls"] == row["embedding_calls"] == row["vector_index_bytes"] == 0
    for saved in row["session_restores"]:
        assert len(study.canonical(saved["snapshot"]).encode()) <= study.STATE_BYTES


def test_controller_plan_is_required_to_resume_validated_actions():
    world = study.make_world(study.DEV[0], 0)
    controller = study.ChainController("v3_hybrid")
    with pytest.raises(ValueError, match="plan"):
        controller.commit(world)
    with pytest.raises(ValueError, match="phase"):
        controller.select(world, [])
    controller.mark_report()
    controller.commit(world)
    controller.plan["round"] = 1
    with pytest.raises(ValueError, match="phase"):
        controller.select(world, [])


def test_small_patch_uses_same_budget_and_revises_after_real_correction():
    row = study.run_case(study.DEV[0], 4, "dependency_retention")
    assert row["chain_complete"] and row["decisions"] == ["equal", "protect"]
    assert row["metrics"]["credits_spent"] == 0
    assert row["secondary_outcomes"]["stale_actions_after_received_correction"] == 0
    assert row["secondary_outcomes"]["unauthorized_evidence_uses"] == 0
    assert row["max_total_state_bytes"] <= study.STATE_BYTES
    assert row["session_restores"][0]["snapshot"]["mind"]["base"]["config"]["capacity"] == 16


def test_legacy_plan_ablation_does_not_get_claimed_as_patch_causality():
    spec = study.DEV[0]
    actual = study.run_case(spec, 2, "dependency_retention")
    erased = study.run_case(spec, 2, "dependency_retention", drop_legacy_plans=True)
    assert actual["decisions"] == erased["decisions"]
    assert actual["final_ledger_hash"] == erased["final_ledger_hash"]


def test_minimal_pair_uses_earlier_evidence_not_different_action_contracts():
    stable = study.run_case(replace(study.DEV[0], distractors=0, initial="stable"), 0, "admissible_history")
    fragile = study.run_case(replace(study.DEV[0], distractors=0, initial="fragile"), 0, "admissible_history")
    assert stable["trace"][0]["decision"]["action_id"] == "equal"
    assert fragile["trace"][0]["decision"]["action_id"] == "protect"
    assert stable["trace"][0]["option_hash"] == fragile["trace"][0]["option_hash"]
    assert stable["trace"][0]["public_register"] == fragile["trace"][0]["public_register"]
