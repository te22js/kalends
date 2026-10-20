"""Research safeguards and actual-world accounting for Track B."""
import json

import pytest

from kalends.pompeii import society_bench as bench
from kalends.pompeii.district import PompeiiConfig
from kalends.pompeii.world import PompeiiWorld


def test_conditions_change_only_one_declared_factor():
    baseline = bench.CONDITIONS["baseline"]
    for name, config in bench.CONDITIONS.items():
        changed = [key for key in baseline if baseline[key] != config[key]]
        assert len(changed) == (0 if name == "baseline" else 1)
    assert set(bench.DEVELOPMENT_SEEDS).isdisjoint(bench.HELDOUT_SEEDS)
    assert bench.DEVELOPMENT_SEEDS == tuple(range(31000, 31010))
    assert bench.HELDOUT_SEEDS == tuple(range(71000, 71030))


def test_prefix_uses_actual_actions_and_is_matched_before_policy_phase():
    prefixes = []
    for condition in bench.CONDITIONS.values():
        world = PompeiiWorld(PompeiiConfig(seed=31000, **condition))
        prefix = bench.player_prefix(world)
        prefixes.append(prefix)
        assert world.economy.cash["Player"] == 14
        assert world.flags["quest"] == "active"
        assert world.flags["affiliation"] == "household client"
        assert world.minute < 25
        for event_id in prefix["claim_ids"]:
            event = world.ledger.events[event_id]
            assert event.payload["value"] == "disrupted"
            assert event.payload["speaker"] == "Player"
            assert event.payload["root_observer"] == "Player"
        assert world.state.facts["grain.supply"] == "available"
    assert all(prefix == prefixes[0] for prefix in prefixes)


def test_actual_work_metrics_reconcile_and_horizon_is_elapsed_after_prefix():
    row = bench.run_world(31000, 7, "baseline")
    m = row["metrics"]
    assert row["end_minute"] == row["prefix"]["minute"] + 7*1440
    assert m["work_required"] == 7*9
    assert m["work_delivered"] + m["work_missed"] == m["work_required"]
    assert m["delivery_fill_rate"] == m["work_delivered"] / m["work_required"]
    assert sum(a["work_delivered"] for a in row["agents"].values()) == m["work_delivered"]
    assert m["player_flour_delivered"] == 0
    assert m["player_commitments_missed"] == 2
    assert m["player_cash_change"] == 8 and m["player_cash_postprefix"] == 0
    assert m["decisions"] == sum(m["decision_"+c] for c in ("buy","inspect","defer","wait"))
    assert m["false_claim_confirmed"] == 0


def test_communication_off_keeps_fixed_claims_but_has_no_npc_relays():
    row = bench.run_world(31001, 7, "no_communication")
    assert row["metrics"]["player_origin_reports"] == 2
    assert row["metrics"]["player_origin_recipients"] == 2
    assert row["metrics"]["player_origin_relays"] == 0
    assert row["metrics"]["false_claim_contradicted"] >= 1


def test_retention_is_actual_bounded_local_store_not_archive():
    row = bench.run_world(31001, 30, "capacity8")
    assert set(row["checkpoints"]) == {"prefix", "day1", "day7", "day30"}
    for checkpoint in row["checkpoints"].values():
        for agent in checkpoint["agents"].values():
            assert agent["ordinary"] <= 8
            assert agent["consolidated"] <= 8
            assert agent["retained_union"] <= 16
            assert agent["retained_union"] < row["event_count"]
    assert row["metrics"]["retained_player_origin_recipients"] == len(row["retention"]["player_origin_recipients"])
    assert row["metrics"]["retained_direct_claim_recipients"] == len(row["retention"]["direct_claim_recipients"])


def test_repeated_actual_world_is_deterministic():
    assert bench.run_world(31002, 7, "credulous") == bench.run_world(31002, 7, "credulous")


def test_constant_paired_interval_has_seed_unit():
    result = bench.interval([2, 2, 2])
    assert result == {"mean": 2., "median": 2, "ci95_mean": [2., 2.], "n_independent_seeds": 3}


def test_no_registration_without_owner_freeze(tmp_path, monkeypatch):
    path = tmp_path/"registration.json"
    monkeypatch.setattr(bench, "REGISTRATION", path)
    with pytest.raises(SystemExit, match="freeze"):
        bench.main(["--register"])
    assert not path.exists()


def test_heldout_refuses_missing_or_changed_registration_before_worlds(tmp_path, monkeypatch):
    path = tmp_path/"registration.json"
    output = tmp_path/"out"
    monkeypatch.setattr(bench, "REGISTRATION", path)
    monkeypatch.setattr(bench, "fingerprint", lambda: {"sha256":"initial","files":{}})
    monkeypatch.setattr(bench, "run_world", lambda *a: pytest.fail("heldout world executed before verification"))
    with pytest.raises(SystemExit, match="Register"):
        bench.main(["--phase","heldout","--out",str(output)])
    assert not output.exists()
    bench.main(["--register","--freeze-confirmed"])
    registered = json.loads(path.read_text())
    assert registered["source"]["sha256"] == "initial"
    monkeypatch.setattr(bench, "fingerprint", lambda: {"sha256":"changed","files":{}})
    with pytest.raises(SystemExit, match="changed"):
        bench.main(["--phase","heldout","--out",str(output)])
    assert not output.exists()


def test_existing_artifacts_never_overwritten(tmp_path):
    output = tmp_path/"existing"
    output.mkdir()
    sentinel = output/"sentinel"
    sentinel.write_text("preserve")
    with pytest.raises(SystemExit, match="overwrite"):
        bench.main(["--out",str(output)])
    assert sentinel.read_text() == "preserve"
