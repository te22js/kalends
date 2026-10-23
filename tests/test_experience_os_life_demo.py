"""Short functional replicas of the recorded 90/120-day demonstration scripts."""
import json
from pathlib import Path

import pytest

from kalends.experience_os.compiler import ExperienceCompilerV1
from kalends.experience_os.life_demo import life_spec, run_commons, run_demo, run_pompeii
from kalends.experience_os.runtime import ExperienceRuntime


def test_derived_specs_are_valid_and_do_not_edit_the_source_scenarios():
    directory = Path(__file__).resolve().parents[1] / "specs"
    before = {p: p.read_bytes() for p in directory.glob("*.json")}
    a, b = life_spec("commons", days=3), life_spec("pompeii", days=2)
    assert a.id == "observatory_long_life" and b.id == "pompeii_long_life"
    assert "Recorded 3-day" in a.title and "Recorded 2-day" in b.title
    assert a.horizon_minutes == 4320 and b.horizon_minutes == 2880
    assert ExperienceCompilerV1().validate(a).to_dict() == a.to_dict()
    assert all(p.read_bytes() == data for p, data in before.items())


@pytest.mark.parametrize("adapter,days", [("commons", 0), ("commons", 91), ("pompeii", 121), ("imaginary", 30)])
def test_invalid_long_life_horizons_are_rejected(adapter, days):
    with pytest.raises(ValueError):
        life_spec(adapter, days=days)


def test_recorded_commons_trajectory_uses_disclosed_reports_actual_outcomes_and_restart(tmp_path):
    summary = run_commons(tmp_path, days=3)
    assert summary["world_minutes"] == 4320 and summary["commands"] == 12
    assert summary["metrics"]["rounds_settled"] == 3
    assert summary["metrics"]["promises_missed"] == 1
    assert summary["metrics"]["promises_kept"] == 2
    assert summary["metrics"]["affiliation"] == "consortium_member"
    assert summary["initial_total_credits"] == summary["final_total_credits"] == 48
    assert all(c["exact_restart"] for c in summary["checkpoints"])
    history = json.loads((tmp_path / "round_history.json").read_text())
    assert len(history) == 3
    assert history[0]["actual_outcome"]["executed"]["team_c"] == 0
    for row in history[1:]:
        assert row["actual_outcome"]["executed"]["team_c"] == 4
        assert len(row["actual_outcome"]["completed"]) == (3 if row["reported_value"] == "stable" else 2)
    saved = (tmp_path / "accepted_journal.json").read_bytes()
    restored = ExperienceRuntime(life_spec("commons", days=3), journal_path=tmp_path / "accepted_journal.json")
    assert restored.state_hash() == summary["final_state_hash"]
    assert (tmp_path / "accepted_journal.json").read_bytes() == saved
    assert all(row["report_event_id"] in restored.visible_ids() for row in history)


def test_actual_omission_has_matched_horizon_material_difference_and_preserves_original(tmp_path):
    summary = run_commons(tmp_path, days=2)
    alternate = json.loads((tmp_path / "actual_omission.json").read_text())
    assert alternate["omitted_command"] == 2
    assert alternate["skipped"] == []
    assert alternate["alternative"]["minute"] == alternate["original"]["minute"] == 2880
    assert alternate["differences"]["completed_projects"]["original"] - alternate["differences"]["completed_projects"]["alternative"] == 2
    assert alternate["differences"]["unused_capacity"]["alternative"] - alternate["differences"]["unused_capacity"]["original"] == 8
    assert summary["original_preserved"]


def test_existing_recorded_life_is_never_overwritten(tmp_path):
    run_commons(tmp_path, days=1)
    path = tmp_path / "accepted_journal.json"; before = path.read_bytes()
    with pytest.raises(ValueError, match="existing recorded"):
        run_commons(tmp_path, days=1)
    assert path.read_bytes() == before


def test_pompeii_has_actual_missed_delivery_kept_service_and_six_executed_minds(tmp_path):
    summary = run_pompeii(tmp_path, days=2)
    assert summary["world_minutes"] == 2880 and summary["exact_restart"]
    assert set(summary["v3_decision_counts"]) == {"Felix", "Sabina", "Marcus", "Dama", "Chreste", "Lucius"}
    assert all(n >= 1 for n in summary["v3_decision_counts"].values())
    commitments = summary["player_commitments"]
    assert any(c["status"] == "missed" and c["beneficiary"] == "Felix" for c in commitments)
    assert any(c["status"] == "fulfilled" and c["fulfilled"] == 120 and c["beneficiary"] == "Lucius" for c in commitments)
    assert summary["affiliation"] == "household client"
    assert summary["metrics"]["cash"] == 11
    saved = (tmp_path / "accepted_journal.json").read_bytes()
    restored = ExperienceRuntime(life_spec("pompeii", days=2), journal_path=tmp_path / "accepted_journal.json")
    assert restored.state_hash() == summary["final_state_hash"]
    history = json.loads((tmp_path / "personal_history.json").read_text())
    assert all(e["event_id"] in restored.visible_ids() for e in history["consequences"])
    assert (tmp_path / "accepted_journal.json").read_bytes() == saved


def test_cli_workflow_generates_a_grounded_cross_adapter_report(tmp_path):
    summary = run_demo(tmp_path, commons_days=1, pompeii_days=0)
    assert set(summary) == {"commons"}
    report = (tmp_path / "REPORT.md").read_text()
    assert "No biography text was invented" in report
    assert "subjective time acceleration" in report
    assert (tmp_path / "commons/validated_spec.json").is_file()
