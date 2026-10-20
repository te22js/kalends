import json

import pytest

from kalends.pompeii.temporal import EventClock


def run_clock(mode):
    clock, seen = EventClock(), []
    clock.schedule(0, "opening", {"nested": {"value": 1}})
    clock.schedule(7, "arrival", {"value": 2})
    clock.schedule(7, "arrival", {"value": 3})
    clock.schedule(1440, "deadline", {})

    def handler(task):
        seen.append((clock.now, task))
        if task["kind"] == "opening":
            clock.schedule(clock.now, "same_minute", {})
            clock.schedule(clock.now + 11, "followup", {})

    stats = clock.advance(1440, handler, mode=mode)
    return clock, seen, stats


def test_compression_matches_actual_full_minute_traversal():
    live, live_seen, ls = run_clock("live")
    compressed, seen, cs = run_clock("compress")
    assert seen == live_seen
    assert live.snapshot() == compressed.snapshot()
    assert ls["ticks_visited"] == 1441
    assert cs["ticks_visited"] == 4
    assert cs["idle_skipped"] == 1437
    assert cs["dispatched"] == ls["dispatched"] == 6
    assert cs["total_lateness"] == 0


def test_task_payload_cannot_alias_input_output_or_handler():
    clock = EventClock()
    payload = {"nested": {"value": 1}}
    returned = clock.schedule(3, "read", payload)
    payload["nested"]["value"] = 99
    returned["data"]["nested"]["value"] = 98
    view = clock.queue
    view[0]["data"]["nested"]["value"] = 97
    seen = []
    clock.advance(3, seen.append)
    assert seen[0]["data"]["nested"]["value"] == 1


def test_saved_queue_replays_stable_ties_and_future_scheduling():
    original = EventClock(10)
    original.schedule(13, "a", {"a": [1, 2]})
    original.schedule(13, "b", {})
    restored = EventClock.from_snapshot(json.loads(json.dumps(original.snapshot())))
    first, second = [], []
    original.advance(15, first.append)
    restored.advance(15, second.append)
    assert first == second
    assert original.schedule(20, "c") == restored.schedule(20, "c")


def test_partitioned_exact_advance_has_same_results():
    full, split = EventClock(), EventClock()
    for clock in (full, split):
        for minute in (0, 2, 8, 8, 10):
            clock.schedule(minute, "work", {"minute": minute})
    a, b = [], []
    full.advance(10, a.append)
    split.advance(2, b.append)
    split.advance(7, b.append)
    split.advance(10, b.append)
    assert a == b
    assert full.snapshot() == split.snapshot()


def test_naive_delays_instead_of_dropping_tasks_and_reacts_at_execution_time():
    clock, seen = EventClock(), []
    clock.schedule(1, "arrival", {})
    clock.schedule(59, "deadline", {})

    def handler(task):
        seen.append((clock.now, task["kind"], task["due"], task["lateness"]))
        if task["kind"] == "arrival":
            clock.schedule(clock.now + 1, "reaction", {})

    early = clock.advance(30, handler, mode="naive", coarse=60)
    assert not seen and len(clock) == 2 and early["dispatched"] == 0
    replay = EventClock.from_snapshot(clock.snapshot())
    assert replay.peek() == 1
    stats = clock.advance(120, handler, mode="naive", coarse=60)
    assert seen == [(60, "arrival", 1, 59), (60, "deadline", 59, 1),
                    (120, "reaction", 61, 59)]
    assert stats["dispatched"] == 3 and stats["total_lateness"] == 119
    assert not clock.queue and clock.now == 120


def test_empty_minutes_do_not_call_handler():
    clock, seen = EventClock(), []
    stats = clock.advance(100, seen.append, mode="live")
    assert not seen and stats["ticks_visited"] == 101


@pytest.mark.parametrize("bad", [True, -1, 1.5, "2", None])
def test_time_validation(bad):
    with pytest.raises(ValueError):
        EventClock(bad)
    clock = EventClock()
    with pytest.raises(ValueError):
        clock.schedule(bad, "bad")
    with pytest.raises(ValueError):
        clock.advance(bad, lambda task: None)


def test_invalid_operations_leave_queue_unchanged():
    clock = EventClock(3)
    before = clock.snapshot()
    for operation in (lambda: clock.schedule(2, "past"),
                      lambda: clock.schedule(4, ""),
                      lambda: clock.schedule(4, "bad", {"x": float("nan")}),
                      lambda: clock.advance(2, lambda task: None),
                      lambda: clock.advance(4, lambda task: None, mode="teleport"),
                      lambda: clock.advance(4, lambda task: None, coarse=0)):
        with pytest.raises(ValueError):
            operation()
        assert clock.snapshot() == before


def test_bad_replay_duplicate_identity_rejected():
    clock = EventClock()
    clock.schedule(2, "a")
    snapshot = clock.snapshot()
    snapshot["queue"].append(snapshot["queue"][0].copy())
    with pytest.raises(ValueError):
        EventClock.from_snapshot(snapshot)


def test_benchmark_projection_difference_is_explicit_and_seed_interval_unit():
    from kalends.pompeii.temporal_bench import differences, interval
    result = differences({"decision": ["buy", {"roots": 2}]},
                         {"decision": ["wait", {"roots": 1}], "new": True})
    assert not result["equal"] and result["unequal_leaves"] == 3
    assert result["examples"][0]["path"] == ["decision", 0]
    assert differences({"a": [1]}, {"a": [1]})["equal"]
    assert interval([1., 1., 1.])["n_independent_seeds"] == 3
    assert interval([1., 1., 1.])["ci95_mean"] == [1., 1.]


def test_heldout_refuses_missing_or_changed_registration_before_world_runs(tmp_path, monkeypatch):
    from kalends.pompeii import temporal_bench as bench
    registered = tmp_path / "registration.json"
    output = tmp_path / "report"
    monkeypatch.setattr(bench, "REGISTRATION", registered)
    monkeypatch.setattr(bench, "fingerprint", lambda: {"sha256": "initial", "files": {}})
    with pytest.raises(SystemExit, match="Register"):
        bench.main(["--phase", "heldout", "--out", str(output)])
    assert not output.exists()
    bench.main(["--register"])
    monkeypatch.setattr(bench, "fingerprint", lambda: {"sha256": "changed", "files": {}})
    with pytest.raises(SystemExit, match="changed"):
        bench.main(["--phase", "heldout", "--out", str(output)])
    assert not output.exists()


def test_benchmark_refuses_existing_output_without_touching_it(tmp_path):
    from kalends.pompeii.temporal_bench import main
    output = tmp_path / "existing"
    output.mkdir()
    saved = output / "important.json"
    saved.write_text('{"keep":true}\n')
    with pytest.raises(SystemExit, match="overwrite"):
        main(["--out", str(output)])
    assert saved.read_text() == '{"keep":true}\n'


@pytest.mark.parametrize("days", [1, 7, 30])
def test_actual_pompeii_world_matches_reference_all_semantic_projections(days):
    from kalends.pompeii.temporal_bench import compare, run_world
    live = run_world(30000, days, "live")
    compressed = run_world(30000, days, "compress")
    assert all(result["equal"] for result in compare(live, compressed).values())
    assert live["event_count"] > 10 and live["decision_count"] >= 4
    assert live["scheduler"]["dispatched"] == compressed["scheduler"]["dispatched"]
    assert live["scheduler"]["ticks_visited"] > compressed["scheduler"]["ticks_visited"]


def test_actual_naive_world_has_recorded_timing_and_evidence_divergence():
    from kalends.pompeii.temporal_bench import compare, run_world
    live = run_world(30000, 1, "live")
    naive = run_world(30000, 1, "naive")
    result = compare(live, naive)
    assert not result["beliefs"]["equal"]
    assert not result["decisions"]["equal"]
    assert result["actions_only"]["equal"]  # Record differences do not prove changed choices.
    assert result["outcomes"]["equal"]
    assert naive["scheduler"]["total_lateness"] > 0


def test_actual_player_promise_settlement_and_relationship_are_preserved():
    from kalends.pompeii.temporal_bench import _projection
    from kalends.pompeii.world import PompeiiWorld
    worlds = [PompeiiWorld(seed=30001) for _ in range(2)]
    for world, mode in zip(worlds, ("live", "compress")):
        world.move(location="bakery")
        world.interact("accept_delivery", "Felix")
        world.clock.advance(7 * 1440, world.on_task, mode=mode)
    assert _projection(worlds[0]) == _projection(worlds[1])
    assert worlds[0].state.trust[("Felix", "Player")] < .6
    assert worlds[0].economy.commitments["Player"][0]["status"] == "missed"


def test_actual_world_saved_clock_continuation_matches_without_aliases():
    import copy
    from kalends.pompeii.temporal_bench import _projection
    from kalends.pompeii.world import PompeiiWorld
    world = PompeiiWorld(seed=30002)
    world.clock.advance(100, world.on_task)
    replay = copy.deepcopy(world)
    replay.clock = EventClock.from_snapshot(json.loads(json.dumps(world.clock.snapshot())))
    world.clock.advance(1440, world.on_task, mode="live")
    replay.clock.advance(1440, replay.on_task, mode="compress")
    assert _projection(world) == _projection(replay)
    replay.memories["Marcus"].clear()
    assert world.memories["Marcus"]
