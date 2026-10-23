"""Functional/adversarial checks for the exploratory study, not held-out data."""
import json

import pytest

from kalends.experience_os import cognition_bench as bench
from kalends_rebirth.minds import Episode


@pytest.mark.parametrize("family", bench.FAMILIES)
def test_every_family_executes_actual_settlement_conserves_credits_and_matches_access(family):
    rows = [bench.run_case(family, 7, arm) for arm in bench.ARMS]
    assert len({r["input_stream_hash"] for r in rows}) == 1
    assert all(r["credit_total"] == r["initial_credit_total"] == 48 for r in rows)
    assert all(r["inspection_fees"] in (0, 1) for r in rows)
    assert all(r["max_memory_records"] <= 16 and r["max_context_records"] <= 4 for r in rows)
    for row in rows:
        assert sum(row["actual_delivered"].values()) + row["unused_capacity"] in (8, 12)
        assert row["settlement_event_id"] >= max(row["admitted_input_event_ids"])
        allowed = set(row["admitted_input_event_ids"]) | {e["event_id"] for e in row["endogenous_inspection_episodes"]}
        assert all(set(d["context_event_ids"]) <= allowed and set(d["evidence_ids"]) <= allowed for d in row["decision_sequence"])
        assert row["exploratory_score"] == row["completed_projects"] - row["promises_missed"] - .1 * row["inspection_fees"]


def test_private_withheld_correction_does_not_enter_evaluator_stream():
    world, epochs = bench.scenario("strategic_communication", 7)
    assert world.state.facts["observatory.condition"] == "fragile"
    received = [e for _, stream, _ in epochs for e in stream if e.subject == "observatory"]
    assert received and {e.value for e in received} == {"stable"}
    assert all(e.kind == "told" and e.source_agent == "team_b" for e in received)
    assert all(e.event_id in world.visible["Player"] for e in received)


def test_repeated_source_reports_retain_one_claimed_ancestor_not_three():
    world, epochs = bench.scenario("shared_source", 7)
    reports = [e for _, stream, _ in epochs for e in stream if e.kind == "told"]
    assert len(reports) == 3 and len({e.origin_event for e in reports}) == 1
    row = bench.run_case("shared_source", 7, "v3_hybrid")
    assert row["decision_sequence"][0]["action_id"] == "inspect"
    assert row["inspection_fees"] == 1 and row["completed_projects"] == 3


def test_forgotten_information_is_recovered_only_by_actual_paid_inspection():
    fifo = bench.run_case("forget_recover", 7, "v3_recency")
    goal = bench.run_case("forget_recover", 7, "v3_goal")
    assert fifo["decision_sequence"][0]["action_id"] == "inspect"
    assert fifo["inspection_fees"] == 1 and goal["inspection_fees"] == 0
    assert fifo["completed_projects"] == goal["completed_projects"] == 3
    assert any(e["kind"] == "observed" and e["subject"] == "observatory" for e in fifo["endogenous_inspection_episodes"])


def test_forgotten_promise_changes_actual_recipient_instead_of_forcing_inaction():
    fifo = bench.run_case("important_promise", 7, "v3_recency")
    salient = bench.run_case("important_promise", 7, "v3_salience")
    assert fifo["decision_sequence"][-1]["action_id"] == "ordinary"
    assert salient["decision_sequence"][-1]["action_id"] == "protect"
    assert fifo["completed_projects"] == salient["completed_projects"] == 2
    assert fifo["actual_delivered"]["team_c"] == 0 and salient["actual_delivered"]["team_c"] == 4
    assert fifo["promises_missed"] == 1 and salient["promises_missed"] == 0


def test_changed_goal_alters_next_action_before_allocation_and_creates_v3_revision():
    row = bench.run_case("changed_goals", 7, "v3_hybrid")
    assert [d["action_id"] for d in row["decision_sequence"]] == ["equal", "protect-stable"]
    assert row["executed_allocation"] == {"team_a": 4, "team_b": 0, "team_c": 4}
    assert row["retained_plan_records"] == 2
    assert row["completed_projects"] == 2


def test_unobserved_future_transition_causes_actual_later_missed_promise():
    row = bench.run_case("delayed_consequence", 7, "v3_hybrid")
    assert row["decision_sequence"][0]["action_id"] == "equal"
    assert row["inspection_fees"] == 0
    assert row["completed_projects"] == 2 and row["promises_missed"] == 1
    assert row["actual_delivered"]["team_c"] == 0


def test_bm25_can_retrieve_actual_inspection_content_despite_a_different_title():
    row = bench.run_case("strategic_communication", 7, "bm25_fifo")
    assert row["inspection_fees"] == 1
    assert row["decision_sequence"][-1]["action_id"] == "protect"
    assert row["promises_missed"] == 0


def test_v3_is_not_assumed_to_improve_the_same_existing_planner():
    left = bench.run_case("outdated", 7, "v3_hybrid")
    right = bench.run_case("outdated", 7, "v2_hybrid")
    for key in ("completed_projects", "unused_capacity", "inspection_fees", "promises_missed", "world_ledger_hash"):
        assert left[key] == right[key]
    assert left["serialized_mind_bytes"] > right["serialized_mind_bytes"]


def test_deterministic_case_repeats_exactly_except_real_timing():
    first = bench.run_case("important_promise", 18, "v3_goal")
    second = bench.run_case("important_promise", 18, "v3_goal")
    first.pop("cognition_and_execution_ms"); second.pop("cognition_and_execution_ms")
    assert first == second


def test_protocol_is_written_before_cases_and_records_detached_observations(tmp_path, monkeypatch):
    execute = bench.run_case
    calls = []
    def checked(*args, **kwargs):
        protocol = json.loads((tmp_path / "protocol.json").read_text())
        assert protocol["source_fingerprints_before"]
        calls.append(args)
        return execute(*args, **kwargs)
    monkeypatch.setattr(bench, "run_case", checked)
    report = bench.run_study(tmp_path, seeds=(1, 2), families=("outdated", "delayed_consequence"),
        arms=("v2_hybrid", "v3_hybrid"), bootstrap_samples=30)
    assert len(calls) == report["world_runs"] == 8
    assert report["source_stable_during_execution"] and report["matched_pre_action_access"]
    raw = [json.loads(line) for line in (tmp_path / "raw.jsonl").read_text().splitlines()]
    streams = [json.loads(line) for line in (tmp_path / "observations.jsonl").read_text().splitlines()]
    assert len(raw) == 8 and len(streams) == 4
    assert all(bench.digest(s["episodes"]) == s["hash"] for s in streams)
    assert (tmp_path / "REPORT.md").is_file()
    difference = report["v3_minus_v2_seed_cluster_intervals"]["hybrid"]["completed_projects"]
    assert difference["mean"] == difference["lower_95"] == difference["upper_95"] == 0
    assert difference["paired_seed_clusters"] == 2
    with pytest.raises(ValueError, match="registered protocol"):
        bench.run_study(tmp_path)


def test_summary_rejects_mismatched_pre_action_information():
    left = bench.run_case("outdated", 7, "v3_hybrid")
    right = bench.run_case("outdated", 7, "v2_hybrid")
    right["input_stream_hash"] = "hidden extra observations"
    with pytest.raises(AssertionError, match="different"):
        bench.summarize([left, right], bootstrap_samples=10)


def test_paired_interval_clusters_seed_level_differences_and_is_reproducible():
    expected = bench.paired_interval([-1, 0, 2], samples=100, seed=4)
    assert expected == bench.paired_interval([-1, 0, 2], samples=100, seed=4)
    assert expected["mean"] == pytest.approx(1 / 3)
    assert expected["paired_seed_clusters"] == 3


def test_bm25_cannot_retrieve_a_forgotten_fact_from_its_index():
    mind = bench.make_mind("bm25_fifo", capacity=2, context=1)
    mind.observe(Episode(1, "Player", 1, "observed", "Observatory condition stable", "observatory", "condition", "stable", 1))
    for i in (2, 3):
        mind.observe(Episode(i, "Player", i, "episodic", "An unrelated observed event"))
    assert mind.believe("observatory", "condition", now=3).status == "unknown"
