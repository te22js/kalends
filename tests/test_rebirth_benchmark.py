import json

import pytest

from kalends_rebirth import benchmark as bench


@pytest.mark.parametrize("seed", range(32000, 32004))
def test_real_opening_routes_and_history_match_optimization_modes(seed):
    a, accepted_a, stats = bench.build_world(seed, 1, "ordinary", False)
    b, accepted_b, _ = bench.build_world(seed, 1, "ordinary", True)
    assert not bench.changed_fields(bench.semantic_snapshot(a), bench.semantic_snapshot(b))
    assert accepted_a == accepted_b
    assert a.arc["route"] == bench.ROUTES[seed % 4]
    if a.arc["route"] == "broker":
        assert a.commissions[0]["status"] == ("fulfilled" if (seed//4)%2 == 0 else "missed")
    assert stats["events"] == len(a.ledger)
    assert a.minute == b.minute == 1440


def test_conversation_stress_uses_legitimate_events_and_detached_candidate(tmp_path):
    from kalends_rebirth.server import RebirthSession
    world, commands, _ = bench.build_world(32000, 1, "conversation_heavy", True)
    assert sum(e.payload["category"] == "conversation" for e in world.ledger.events) == 12
    before = bench.digest(bench.semantic_snapshot(world))
    session, _, _ = bench._timed_transaction(world, commands, tmp_path / "journal.json")
    assert before == bench.digest(bench.semantic_snapshot(world))
    assert session.original.minute == world.minute + 1
    replayed = RebirthSession(tmp_path / "journal.json")
    assert not bench.changed_fields(bench.semantic_snapshot(session.original), bench.semantic_snapshot(replayed.original))
    bench._reject_check(world, commands)


def test_registration_freezes_sources_and_refuses_overwrite(tmp_path, monkeypatch):
    path = tmp_path / "registered.json"
    bench.register(path)
    assert bench.validate_registration(path)["heldout_seeds"] == list(range(83000, 83020))
    with pytest.raises(FileExistsError):
        bench.register(path)
    old_fingerprint = bench.fingerprint()
    monkeypatch.setattr(bench, "fingerprint", lambda: {**old_fingerprint, "sha256": "changed"})
    with pytest.raises(ValueError, match="runtime changed"):
        bench.validate_registration(path)


def test_registered_holdout_cannot_be_sliced_and_pilot_cannot_use_holdout(tmp_path):
    path = bench.register(tmp_path / "registered.json")
    with pytest.raises(ValueError, match="cannot be selected"):
        bench.run(tmp_path / "bad", heldout=True, seeds=[83000], registration_path=path)
    with pytest.raises(ValueError, match="development range"):
        bench.run(tmp_path / "bad", seeds=[83000])


def test_semantics_ignore_only_measured_wall_time():
    first = {"time_stats": {"wall_seconds": .1, "dispatched": 4}, "player": {"cash": 2}}
    second = {"time_stats": {"wall_seconds": 2, "dispatched": 4}, "player": {"cash": 2}}
    assert bench.semantic_game(first) == bench.semantic_game(second)
    assert "wall_seconds" in first["time_stats"]
    second["player"]["cash"] = 3
    assert bench.semantic_game(first) != bench.semantic_game(second)
    second["player"]["cash"] = 2
    second["time_stats"]["dispatched"] = 5
    assert bench.semantic_game(first) != bench.semantic_game(second)


def test_uncertainty_uses_paired_seed_ratios():
    interval = bench.paired_interval([2, 2, 2])
    assert interval == {"geometric_mean": 2, "low95": 2, "high95": 2, "paired_seeds": 3}
    with pytest.raises(ValueError):
        bench.paired_interval([0, 1])
