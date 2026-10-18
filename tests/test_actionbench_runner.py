"""Evaluator arithmetic and experiment statistics independently of city policy.

Fixture decisions distinguish remembering a false report correctly from taking
an action that is good under actual supply. Real-world smoke tests cover every
predeclared condition without asserting any desired research result.
"""
import gzip
import hashlib
import json
from types import SimpleNamespace

import pytest

from kalends.actionbench import runner
from kalends.bench.stats import summarize
from kalends.memory.base import Experience


def decision(agent="A", tick=2, action="reserve", predicted="disrupted", actual="disrupted",
             regret=0.0, qa=True, event_id=10, **kwargs):
    result = dict(agent=agent, tick=tick, action=action, predicted_value=predicted,
                  actual_value=actual, regret=regret, loss=regret, qa_correct=qa,
                  boundary_violation=False, source_independence_failure=False,
                  opportunity_valid=True, event_id=event_id)
    result.update(kwargs)
    return result


def claim(event_id, tick, value, agent="A", kind="told", accepted=True):
    return Experience(tick=tick, kind=kind, subject="grain", predicate="supply", value=value,
                      source_agent="Courier" if kind == "told" else None,
                      as_of=tick, accepted=accepted, event_id=event_id,
                      text=f"grain supply {value}", claimed_origin_kind=kind,
                      claimed_origin_event=event_id, claimed_origin_observer=agent)


def fixture_sim(decisions, experiences=None, ticks=8):
    return SimpleNamespace(decisions=decisions, experiences=experiences or {},
                           config=SimpleNamespace(n_ticks=ticks))


def test_evaluator_known_losses_separates_local_qa_world_accuracy_and_abstention():
    decisions = [
        decision(),
        decision("B", actual="available", regret=2, boundary_violation=True,
                 source_independence_failure=True),
        decision("C", action="defer", predicted="available", regret=6),
        decision("D", action="verify", predicted="unknown", regret=1.5, qa=False),
        decision("E", action="defer", predicted="unknown", actual="available"),
    ]
    measured = runner.decision_metrics(fixture_sim(decisions))
    assert measured["n_decisions"] == 5
    assert measured["n_reserves"] == 2
    assert measured["n_useful_opportunities"] == 3
    assert measured["action_error_rate"] == pytest.approx(2 / 5)
    assert measured["autonomy"] == pytest.approx(2 / 5)
    assert measured["decision_regret"] == pytest.approx(1.9)
    assert measured["false_abstention_rate"] == pytest.approx(2 / 3)
    assert measured["belief_error_rate"] == pytest.approx(4 / 5)
    assert measured["qa_accuracy"] == pytest.approx(4 / 5)
    assert measured["verification_rate"] == pytest.approx(1 / 5)
    assert measured["selective_risk"] == pytest.approx(1 / 2)
    assert measured["boundary_violation_rate"] == pytest.approx(1 / 5)
    assert measured["source_independence_failure_rate"] == pytest.approx(1 / 5)


def test_empty_decisions_have_defined_zero_coverage_with_no_qa_samples():
    measured = runner.decision_metrics(fixture_sim([]))
    assert measured["n_decisions"] == measured["qa_n"] == 0
    assert measured["decision_regret"] == measured["autonomy"] == 0
    assert measured["selective_risk"] == 0  # Must always be read with coverage.
    assert measured["correction_n"] == measured["correction_recovered_n"] == 0


def test_correction_latency_counts_changes_once_and_reports_censoring_separately():
    exps = {
        "A": [claim(1, 0, "disrupted"), claim(2, 2, "available", kind="observed"),
              claim(3, 3, "available", kind="observed")],
        "B": [claim(4, 0, "available", "B"), claim(5, 2, "disrupted", "B", kind="observed")],
    }
    decisions = [decision("A", tick=4, predicted="available", actual="available", event_id=20),
                 decision("B", tick=4, predicted="unknown", event_id=21)]
    measured = runner.decision_metrics(fixture_sim(decisions, exps, ticks=6))
    assert measured["correction_n"] == 2
    assert measured["correction_recovered_n"] == 1
    assert measured["correction_latency"] == 2
    assert measured["correction_unrecovered_rate"] == .5


def test_decision_before_same_tick_observation_cannot_count_as_recovery():
    exps = {"A": [claim(1, 0, "disrupted"), claim(10, 2, "available", kind="observed")]}
    decisions = [decision("A", tick=2, predicted="available", actual="available", event_id=9),
                 decision("A", tick=3, predicted="unknown", actual="available", event_id=11)]
    measured = runner.decision_metrics(fixture_sim(decisions, exps, ticks=5))
    assert measured["correction_n"] == 1
    assert measured["correction_recovered_n"] == 0
    assert measured["correction_unrecovered_rate"] == 1


def test_later_same_tick_decision_can_recover_after_observation():
    exps = {"A": [claim(1, 0, "disrupted"), claim(10, 2, "available", kind="observed")]}
    decisions = [decision("A", tick=2, predicted="available", actual="available", event_id=11)]
    measured = runner.decision_metrics(fixture_sim(decisions, exps, ticks=5))
    assert measured["correction_n"] == measured["correction_recovered_n"] == 1
    assert measured["correction_latency"] == measured["correction_unrecovered_rate"] == 0


@pytest.mark.parametrize("condition", tuple(runner.CONDITIONS))
def test_every_condition_has_reproducible_semantic_hashes_and_evaluator_results(condition):
    first = runner.run_world(7, "rumour", 8, condition, capacity=8, n_ticks=6)
    second = runner.run_world(7, "rumour", 8, condition, capacity=8, n_ticks=6)
    assert first["semantic_hash"] == second["semantic_hash"]
    assert first["ledger_hash"] == second["ledger_hash"]
    assert first["decisions"] == second["decisions"]
    semantic = {"config": first["config"], "condition": condition,
                "ledger_hash": first["ledger_hash"], "decisions": first["decisions"]}
    assert first["semantic_hash"] == hashlib.sha256(json.dumps(semantic, sort_keys=True).encode()).hexdigest()
    for key in first["metrics"]:
        if key not in ("seconds", "events_per_second"):
            assert first["metrics"][key] == second["metrics"][key]
    assert first["metrics"]["n_decisions"] == len(first["decisions"]) > 0
    assert all(d["opportunity_valid"] for d in first["decisions"])


@pytest.mark.parametrize("condition", ("always_defer", "always_verify"))
def test_sanity_floor_has_nonzero_regret_under_true_shortage(condition):
    row = runner.run_world(13, "shortage", 8, condition, n_ticks=6)
    assert row["metrics"]["decision_regret"] > 0
    assert row["metrics"]["autonomy"] == 0
    assert row["metrics"]["false_abstention_rate"] == 1
    assert row["metrics"]["qa_n"] == 0
    if condition == "always_verify":
        assert row["metrics"]["verification_rate"] == 1
        assert row["metrics"]["decision_regret"] == 1.5
    else:
        assert row["metrics"]["decision_regret"] == 6
        assert row["metrics"]["action_error_rate"] == 1


def test_world_truth_and_locally_correct_qa_can_disagree_in_real_rumour_world():
    row = runner.run_world(42, "rumour", 8, "structured", n_ticks=6)
    ds = row["decisions"]
    assert any(d["qa_correct"] and d["predicted_value"] != d["actual_value"] for d in ds)
    assert row["metrics"]["qa_accuracy"] > 1 - row["metrics"]["belief_error_rate"]
    assert row["metrics"]["decision_regret"] > 0


def aggregate_row(seed, family, condition, value, n_decisions=1, recovered=1):
    metrics = {key: float(value) for key in runner.METRICS}
    metrics.update(n_decisions=n_decisions, correction_recovered_n=recovered)
    return dict(seed=seed, family=family, population=8, condition=condition, metrics=metrics)


def test_aggregate_averages_families_before_seed_ci_and_never_weights_decisions():
    rows = [aggregate_row(0, "rumour", "structured", 0, n_decisions=1000),
            aggregate_row(0, "shortage", "structured", 1, n_decisions=1),
            aggregate_row(1, "rumour", "structured", .2, n_decisions=10),
            aggregate_row(1, "shortage", "structured", .2, n_decisions=1)]
    result = runner.aggregate(rows)["systems"]["8/structured"]
    assert result["n_worlds"] == 4 and result["n_seeds"] == 2
    assert result["n_decisions"] == 1012
    assert result["metrics"]["decision_regret"] == summarize([.5, .2])
    assert result["metrics"]["decision_regret"]["n"] == 2


def test_aggregate_pairs_by_both_seed_and_family_and_excludes_unmatched_worlds():
    rows = [aggregate_row(0, "rumour", "hybrid", 1),
            aggregate_row(0, "shortage", "hybrid", 2),
            aggregate_row(1, "rumour", "hybrid", 100),
            aggregate_row(1, "private", "hybrid", 999),
            aggregate_row(1, "recovery", "hybrid_guarded", 9999),
            aggregate_row(0, "shortage", "hybrid_guarded", 1.5),
            aggregate_row(1, "rumour", "hybrid_guarded", 99),
            aggregate_row(0, "rumour", "hybrid_guarded", .5)]
    result = runner.aggregate(list(reversed(rows)))
    pair = result["paired_comparisons"]["8/hybrid-minus-hybrid_guarded"]["decision_regret"]
    assert pair["n"] == 2
    assert pair["mean_diff"] == .75


def test_aggregate_does_not_invent_a_pair_for_nonoverlapping_world_keys():
    rows = [aggregate_row(0, "rumour", "hybrid", .5),
            aggregate_row(1, "shortage", "hybrid_guarded", .2)]
    result = runner.aggregate(rows)
    assert "8/hybrid-minus-hybrid_guarded" not in result["paired_comparisons"]


def test_correction_ci_excludes_censored_worlds_from_latency_but_keeps_censor_rate():
    rows = [aggregate_row(0, "rumour", "structured", 2, recovered=1),
            aggregate_row(0, "shortage", "structured", 0, recovered=0),
            aggregate_row(1, "rumour", "structured", 0, recovered=0)]
    rows[0]["metrics"]["correction_unrecovered_rate"] = 0
    rows[1]["metrics"]["correction_unrecovered_rate"] = 1
    rows[2]["metrics"]["correction_unrecovered_rate"] = 1
    measured = runner.aggregate(rows)["systems"]["8/structured"]["metrics"]
    assert measured["correction_latency"] == summarize([2])
    assert measured["correction_unrecovered_rate"] == summarize([.5, 1])


def test_small_suite_exports_replayable_world_rows_and_refuses_existing_raw(tmp_path):
    destination = tmp_path / "experiment"
    summary = runner.run_suite(destination, seeds=[7], populations=(8,),
                               families=("private",), conditions=["structured", "always_verify"],
                               n_ticks=3)
    assert summary["n_worlds"] == 2
    with gzip.open(destination / "raw.jsonl.gz", "rt") as stream:
        rows = [json.loads(line) for line in stream]
    assert len(rows) == 2
    assert all(row["decisions"] for row in rows)
    config = json.loads((destination / "config.json").read_text())
    assert config["source_hashes"]["actionbench/runner.py"]
    assert config["query"] == {"subject": "grain", "predicate": "supply", "top_k": 4}
    before = {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()}
    with pytest.raises(ValueError):
        runner.run_suite(destination, seeds=[8], n_ticks=3)
    assert {p.name: p.read_bytes() for p in destination.iterdir() if p.is_file()} == before


def test_all_conditions_and_families_form_a_complete_paired_seed_grid(tmp_path):
    destination = tmp_path / "paired-grid"
    summary = runner.run_suite(destination, seeds=[7, 8], populations=(8,),
                               families=runner.FAMILIES, n_ticks=6, capacity=8)
    expected_worlds = 2 * len(runner.FAMILIES) * len(runner.CONDITIONS)
    assert summary["n_worlds"] == expected_worlds
    assert len(summary["systems"]) == len(runner.CONDITIONS)
    for condition in runner.CONDITIONS:
        system = summary["systems"][f"8/{condition}"]
        assert system["n_worlds"] == 2 * len(runner.FAMILIES)
        assert system["n_seeds"] == system["metrics"]["decision_regret"]["n"] == 2
    for comparison in summary["paired_comparisons"].values():
        assert comparison["decision_regret"]["n"] == 2
    with gzip.open(destination / "raw.jsonl.gz", "rt") as stream:
        rows = [json.loads(line) for line in stream]
    assert len(rows) == expected_worlds
    assert {(r["seed"], r["family"], r["condition"]) for r in rows} == {
        (seed, family, condition) for seed in (7, 8)
        for family in runner.FAMILIES for condition in runner.CONDITIONS}


@pytest.mark.parametrize("filename", ("summary.json", "config.json", "worlds.csv"))
def test_preexisting_experiment_outputs_are_never_overwritten_without_raw(tmp_path, filename):
    destination = tmp_path / "experiment"
    destination.mkdir()
    (destination / filename).write_text("reviewed experiment sentinel")
    before = {p.name: p.read_bytes() for p in destination.iterdir()}
    with pytest.raises(ValueError):
        runner.run_suite(destination, seeds=[7], populations=(8,),
                         families=("private",), conditions=["structured"], n_ticks=3)
    assert {p.name: p.read_bytes() for p in destination.iterdir()} == before


@pytest.mark.parametrize("options", (
    {"seeds": []}, {"populations": ()}, {"families": ()}, {"conditions": []},
    {"populations": (1,)}, {"families": ("unknown",)}, {"conditions": ["oracle"]},
    {"split": "invalid"}, {"capacity": -1}, {"depth": -1}, {"n_ticks": 0},
    {"seeds": [7, 7]}, {"populations": (8, 8)},
    {"families": ("private", "private")}, {"conditions": ["structured", "structured"]},
    {"seeds": [True]}, {"populations": (True,)},
))
def test_invalid_suite_configuration_writes_no_experiment_outputs(tmp_path, options):
    destination = tmp_path / "invalid"
    config = dict(seeds=[7], populations=(8,), families=("private",),
                  conditions=["structured"], n_ticks=3)
    config.update(options)
    with pytest.raises(ValueError):
        runner.run_suite(destination, **config)
    assert not destination.exists() or not list(destination.iterdir())
