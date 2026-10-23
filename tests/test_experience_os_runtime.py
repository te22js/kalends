"""Independent integration checks of compiled lives, boundaries and continuity."""
import copy
import json
from pathlib import Path

import pytest

from kalends.experience_os.compiler import ExperienceCompilerV1, ExperienceSpec, SPEC_DIR
from kalends.experience_os.runtime import ExperienceGameFacade, ExperienceRuntime


def runtime(name="shared_observatory", journal_path=None):
    return ExperienceRuntime(ExperienceCompilerV1().load(SPEC_DIR / (name + ".json")), journal_path=journal_path)


def test_player_cannot_obtain_private_condition_from_history_montage_trace_or_debrief():
    life = runtime()
    hidden = next(e for e in life.world.ledger.events
                  if e.payload.get("category") == "condition" and e.actors == ("team_b",))
    assert hidden.event_id not in life.visible_ids()
    assert hidden.event_id in life.visible_ids("team_b")
    public = life.snapshot()
    assert "lab" not in public and not public["own_reports"]
    assert hidden.event_id not in {e["event_id"] for e in public["events"] + public["montage"]}
    assert hidden.event_id not in {e["event_id"] for e in life.debrief()["consequences"]}
    with pytest.raises(ValueError, match="not observed"):
        life.trace(hidden.event_id)
    lab = life.snapshot(operator=True)
    assert lab["lab"]["truth"]["state"]["facts"]["observatory.condition"] == "fragile"
    assert life.trace(hidden.event_id, operator=True)["events"][-1]["payload"]["value"] == "fragile"
    # Disclosure is a real accepted action, with the actual source kept private.
    accepted = life.commit("action", {"action": "share", "recipient": "team_b"})
    report = accepted["receipt"]
    assert report["payload"]["value"] == "fragile" and report["event_id"] in life.visible_ids()
    trace = life.trace(report["event_id"])
    assert hidden.event_id not in {e["event_id"] for e in trace["events"]}
    assert trace["hidden_parent_count"] >= 1


@pytest.mark.parametrize("action", [
    {"action": "allocate", "actor": "team_a", "allocation": {"team_a": 4, "team_b": 4, "team_c": 4}},
    {"action": "wait", "actor": "team_b"},
    {"action": "inspect", "actor": "team_b"},
    {"action": "allocate", "allocation": {"team_a": 13, "team_b": 0, "team_c": 0}},
    {"action": "allocate", "allocation": {"team_a": True, "team_b": 0, "team_c": 0}},
    {"action": "allocate", "allocation": {"team_a": 1, "team_b": 1, "team_c": 1}, "cash_delta": {"Player": 100}},
    {"action": "share", "recipient": "team_a", "event_id": 1},
    {"action": "mint_credits", "quantity": 100},
])
def test_rejected_actions_preserve_world_commands_and_existing_save(tmp_path, action):
    journal = tmp_path / "life.json"
    life = runtime(journal_path=journal)
    life.save()
    before, commands, saved = life.state_hash(), copy.deepcopy(life.commands), journal.read_bytes()
    with pytest.raises(ValueError):
        life.commit("action", action)
    assert life.state_hash() == before and life.commands == commands and journal.read_bytes() == saved


def test_finite_inspection_payment_and_rejection_cannot_create_credits():
    life = runtime()
    initial = sum(life.world.economy.cash.values())
    while life.world.economy.cash["Player"]:
        previous = dict(life.world.economy.cash)
        result = life.commit("action", {"action": "inspect"})
        assert result["receipt"]["payload"]["prop"] == ["observatory", "condition"]
        assert life.world.economy.cash["Player"] == previous["Player"] - 1
        assert life.world.economy.cash["consortium"] == previous["consortium"] + 1
        assert sum(life.world.economy.cash.values()) == initial
    before = life.state_hash(), len(life.commands)
    with pytest.raises(ValueError, match="credits"):
        life.commit("action", {"action": "inspect"})
    assert (life.state_hash(), len(life.commands)) == before


@pytest.mark.parametrize("failure", ["write", "rename"])
def test_disk_failure_keeps_in_memory_world_and_last_saved_life(tmp_path, monkeypatch, failure):
    journal = tmp_path / "life.json"
    life = runtime(journal_path=journal)
    life.commit("action", {"action": "inspect"})
    before, saved, commands = life.state_hash(), journal.read_bytes(), copy.deepcopy(life.commands)
    method = "write_text" if failure == "write" else "replace"
    original = getattr(Path, method)

    def broken(path, *args, **kwargs):
        if path == journal.with_name(journal.name + ".tmp"):
            raise OSError("injected full disk or interrupted atomic rename")
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, method, broken)
    with pytest.raises(OSError):
        life.commit("action", {"action": "inspect"})
    assert life.state_hash() == before and life.commands == commands
    assert journal.read_bytes() == saved
    restored = runtime(journal_path=journal)
    assert restored.state_hash() == before


def test_ninety_day_history_has_settlements_membership_resources_and_exact_restart(tmp_path):
    journal = tmp_path / "months.json"
    life = runtime(journal_path=journal)
    initial_credits = sum(life.world.economy.cash.values())
    life.commit("action", {"action": "inspect"})
    for _ in range(3):
        life.commit("action", {"action": "commit", "recipient": "team_a", "quantity": 4})
        life.commit("action", {"action": "allocate", "allocation": {"team_a": 4, "team_b": 4, "team_c": 0}})
        life.commit("advance", {"minutes": 1440})
    assert life.metrics()["affiliation"] == "consortium_member"
    assert life.metrics()["promises_kept"] == 3
    life.commit("advance", {"minutes": 87 * 1440})
    assert life.minute == 90 * 1440 and life.metrics()["rounds_settled"] == 90
    assert life.snapshot()["terminated"]
    assert sum(life.world.economy.cash.values()) == initial_credits
    outcomes = [e for e in life.world.ledger.events if e.payload.get("category") == "allocation_settled"]
    assert len(outcomes) == 90 and outcomes[-1].tick == 90 * 1440 - 1
    assert all(mind.inspect(now=life.minute)["current_plan"]["status"] == "succeeded" for mind in life.minds.values())
    before, saved = life.state_hash(), journal.read_bytes()
    restored = runtime(journal_path=journal)
    assert restored.state_hash() == before and restored.commands == life.commands
    assert journal.read_bytes() == saved
    with pytest.raises(ValueError, match="horizon|terminated"):
        life.commit("advance", {"minutes": 1})
    assert life.state_hash() == before


def test_clamped_advance_reports_actual_start_and_charges_only_available_horizon():
    life = runtime()
    life.commit("action", {"action": "wait"})
    result = life.commit("advance", {"minutes": 100 * 1440})
    assert result["receipt"]["from"] == 1
    assert result["receipt"]["to"] == 90 * 1440
    assert life.minute == 90 * 1440


def test_compiled_spec_permissions_and_forged_value_object_are_revalidated(tmp_path):
    spec = ExperienceCompilerV1().load(SPEC_DIR / "shared_observatory.json").to_dict()
    spec["actions"].remove("inspect")
    life = ExperienceRuntime(spec)
    with pytest.raises(ValueError, match="permissions"):
        life.commit("action", {"action": "inspect"})
    bad = copy.deepcopy(spec)
    bad["participants"][0]["resources"]["credits"] = -100
    journal = tmp_path / "preserved.json"
    journal.write_text("preserve this prior world")
    with pytest.raises(ValueError):
        ExperienceRuntime(ExperienceSpec(bad), journal_path=journal)
    assert journal.read_text() == "preserve this prior world"


def test_all_six_pompeii_minds_make_executed_evidence_grounded_decisions():
    life = runtime("pompeii_life")
    life.commit("advance", {"minutes": 2 * 1440})
    expected = {"Felix", "Sabina", "Marcus", "Chreste", "Dama", "Lucius"}
    decisions = [e for e in life.world.ledger.events if e.payload.get("category") == "os_decision"]
    assert {e.actors[0] for e in decisions} == expected
    for actor, mind in life.minds.items():
        view = mind.inspect(now=life.minute)
        assert view["current_plan"]["status"] == "succeeded"
        assert view["current_plan"]["outcome"]
        for identifier in mind.retained_event_ids():
            source = life.world.ledger.events[identifier]
            if source.scope == "private":
                assert actor in source.actors, "A retained private record must belong to this actor's legitimate observation"
        # The persisted plan's evidence really existed no later than its decision.
        for event in (e for e in decisions if actor in e.actors):
            assert all(life.world.ledger.events[eid].tick <= event.tick for eid in event.payload["decision"]["evidence_ids"])
    for actor in ("Felix", "Sabina"):
        bookings = [e for e in life.world.ledger.events if e.payload.get("category") == "inspection_booked" and actor in e.actors]
        checks = [e for e in life.world.ledger.events if e.payload.get("category") == "inspection" and actor in e.actors]
        assert bookings and checks
        assert any(check.tick == booking.tick + 15 and booking.event_id in check.payload["parents"]
                   for booking in bookings for check in checks)
    assert any(e.payload.get("category") == "purchase" and "Marcus" in e.actors
               and e.payload.get("inventory_delta", {}).get("Marcus", 0) > 0 for e in life.world.ledger.events)
    public = life.snapshot()
    assert "experience_os_minds_v3" not in json.dumps(public)
    assert set(life.snapshot(operator=True)["lab"]["minds"]) == expected


def test_pompeii_action_actor_and_private_evidence_are_rejected_at_execution_boundary():
    life = runtime("pompeii_life")
    marcus = life.world.positions["Marcus"]
    life.commit("action", {"action": "move", "x": marcus[0], "y": marcus[1], "location": "street"})
    private = next(e for e in life.world.ledger.events if e.payload.get("document_key") == "market_receipt")
    for changed in ({"actor_id": "Marcus"}, {"needs_confirmation": False}, {"evidence_ids": [private.event_id]}):
        before = life.state_hash(), len(life.commands)
        with pytest.raises(ValueError):
            life.commit("action", {"action": "buy", "recipient": "Marcus", "quantity": 1, **changed})
        assert (life.state_hash(), len(life.commands)) == before


def test_actual_omission_replays_a_later_wait_at_the_recorded_time(tmp_path):
    life = runtime("pompeii_life", tmp_path / "original.json")
    sabina = life.world.positions["Sabina"]
    life.commit("action", {"action": "move", "x": sabina[0], "y": sabina[1], "location": "street"})
    life.commit("action", {"action": "work", "recipient": "Sabina"})
    life.commit("advance", {"minutes": 120})
    before, commands = life.state_hash(), copy.deepcopy(life.commands)
    alternative = life.fork(1)
    assert alternative["alternative"]["minute"] == life.minute
    assert alternative["alternative"]["metrics"]["cash"] == life.metrics()["cash"] - 3
    assert (life.state_hash(), life.commands) == (before, commands)
    assert not alternative["skipped"]


def test_3d_dialogue_facade_acts_on_the_same_compiled_world_and_invalidates_stale_review():
    life = runtime("pompeii_life")
    facade = ExperienceGameFacade(life)
    marcus = life.world.positions["Marcus"]
    life.commit("action", {"action": "move", "x": marcus[0], "y": marcus[1], "location": "street"})
    assert facade.state()["world"]["minute"] == life.minute
    proposal = facade.propose({"recipient": "Marcus", "choice_id": "buy"})
    before = life.world.economy.inventory["Player"]
    accepted = facade.act({"proposal_id": proposal["proposal_id"], "interpretation_id": "0"})
    assert life.world.economy.inventory["Player"] == before + 1
    assert accepted["world"]["player"]["inventory"] == before + 1
    assert facade.legacy.original is life.world and life.commands[-1]["data"]["action"] == "buy"
    with pytest.raises(ValueError):
        facade.act({"proposal_id": proposal["proposal_id"], "interpretation_id": "0"})
    stale = facade.propose({"recipient": "Marcus", "choice_id": "buy"})
    life.commit("advance", {"minutes": 1})
    with pytest.raises(ValueError, match="changed"):
        facade.act({"proposal_id": stale["proposal_id"], "interpretation_id": "0"})


@pytest.mark.parametrize("field,value", [("at", 999), ("after", 999), ("receipt_id", 999)])
def test_replay_rejects_forged_command_timeline_or_receipt_even_when_final_state_hash_matches(tmp_path, field, value):
    journal = tmp_path / "timeline.json"
    life = runtime(journal_path=journal)
    life.commit("action", {"action": "inspect"})
    payload = json.loads(journal.read_text())
    payload["commands"][0][field] = value
    journal.write_text(json.dumps(payload))
    corrupted = journal.read_bytes()
    with pytest.raises(ValueError, match="replay|timeline|receipt|command|recorded"):
        runtime(journal_path=journal)
    assert journal.read_bytes() == corrupted


def configured_observatory():
    return json.loads((SPEC_DIR / "shared_observatory.json").read_text())


def stable_observatory():
    spec = configured_observatory()
    spec["setting"]["rules"]["initial_condition"] = "stable"
    spec["observations"][0]["value"] = "stable"
    return spec


def test_compiled_goal_prerequisite_requires_an_earlier_actual_settlement():
    spec = stable_observatory()
    first, dependent = spec["goals"][:2]
    dependent["requires"] = [first["id"]]
    dependent["deadline"] = 2880
    life = ExperienceRuntime(spec)
    assert life.world.get("goal_status")[dependent["id"]]["status"] == "blocked"
    assert "team_b" not in life.world.get("requests:0")
    # Even giving the blocked team real capacity cannot retroactively establish
    # that its prerequisite was already completed before this first batch.
    life.commit("action", {"action": "allocate", "allocation": {"team_a": 4, "team_b": 4, "team_c": 0}})
    life.commit("advance", {"minutes": 1440})
    statuses = life.world.get("goal_status")
    assert statuses[first["id"]]["status"] == "completed"
    assert statuses[dependent["id"]]["status"] == "active"
    assert life.world.get("requests:1")["team_b"] == 4
    assert next(g for g in life.minds["team_b"].goals if g.goal_id == dependent["id"]).deadline == 2880
    life.commit("action", {"action": "allocate", "allocation": {"team_a": 0, "team_b": 4, "team_c": 0}})
    life.commit("advance", {"minutes": 1440})
    achieved = life.world.get("goal_status")[dependent["id"]]
    assert achieved["status"] == "completed" and achieved["completed_at"] == 2879
    assert life.world.ledger.events[achieved["evidence_event"]].payload["category"] == "allocation_settled"


def test_larger_goal_target_changes_the_request_and_requires_real_full_batch_delivery():
    spec = stable_observatory()
    goal = spec["goals"][1]
    goal["target"]["quantity"], goal["deadline"] = 6, 2880
    life = ExperienceRuntime(spec)
    assert life.world.get("requests:0")["team_b"] == 6
    life.commit("action", {"action": "allocate", "allocation": {"team_a": 0, "team_b": 4, "team_c": 0}})
    life.commit("advance", {"minutes": 1440})
    assert life.world.get("goal_status")[goal["id"]]["status"] == "active"
    life.commit("action", {"action": "allocate", "allocation": {"team_a": 0, "team_b": 6, "team_c": 0}})
    life.commit("advance", {"minutes": 1440})
    status = life.world.get("goal_status")[goal["id"]]
    assert status["status"] == "completed" and status["executed_units"] == 6


def test_declared_mid_round_deadline_expires_at_its_actual_minute():
    spec = stable_observatory()
    goal = spec["goals"][1]
    goal["deadline"] = 2000
    life = ExperienceRuntime(spec)
    life.commit("advance", {"minutes": 1999})
    assert life.world.get("goal_status")[goal["id"]]["status"] == "active"
    life.commit("advance", {"minutes": 1})
    status = life.world.get("goal_status")[goal["id"]]
    assert status["status"] == "missed" and status["updated_at"] == 2000
    assert all(g.goal_id != goal["id"] for g in life.minds["team_b"].goals)


def test_all_declared_opportunities_fire_once_at_exact_times_including_zero():
    spec = configured_observatory()
    times = [0, 37, 719, 1440, 1499]
    spec["opportunities"] = [{"at": at, "label": f"Declared decision opportunity at minute {at}."} for at in times]
    life = ExperienceRuntime(spec)
    life.commit("advance", {"minutes": 1500})
    actual = [e for e in life.world.ledger.events if "opportunity_index" in e.payload]
    assert [e.tick for e in actual] == times
    assert [e.payload["title"] for e in actual] == [item["label"] for item in spec["opportunities"]]
    assert [e.payload["declared_at"] for e in actual] == times


def test_goal_contract_rejects_typed_or_temporally_impossible_declarations():
    for change in ({"priority": 0}, {"label": "x" * 257}, {"id": "a" * 65}):
        spec = configured_observatory()
        spec["goals"][0].update(change)
        with pytest.raises(ValueError):
            ExperienceRuntime(spec)
    spec = configured_observatory()
    spec["goals"][0]["priority"] = .5
    ExperienceRuntime(spec)
    spec = configured_observatory()
    spec["goals"][1]["requires"] = [spec["goals"][0]["id"]]
    with pytest.raises(ValueError, match="prerequisite.*settle"):
        ExperienceRuntime(spec)


def test_relayed_testimony_preserves_original_witness_date_and_world_truth():
    spec = configured_observatory()
    spec["setting"]["rules"].update(seed=0, maintenance_interval=1)
    life = ExperienceRuntime(spec)
    first = life.commit("action", {"action": "share", "recipient": "team_b"})["receipt"]
    original = first["payload"]["origin_event"]
    assert first["payload"]["origin_observer"] == "team_b"
    assert first["event_id"] in {e["event_id"] for e in life.snapshot()["own_reports"]}
    life.commit("advance", {"minutes": 1440})
    assert life.world.state.facts["observatory.condition"] == "stable"
    forwarded = life.commit("action", {"action": "share", "recipient": "team_a", "event_id": first["event_id"]})["receipt"]
    assert forwarded["etype"] == "tell" and forwarded["payload"]["value"] == "fragile"
    assert forwarded["payload"]["as_of"] == 0
    assert forwarded["payload"]["origin_event"] == original
    assert forwarded["payload"]["origin_observer"] == "team_b"
    assert life.world.state.facts["observatory.condition"] == "stable"
    provenance = life.minds["team_a"].provenance(forwarded["event_id"])
    assert provenance["kind"] == "testimony" and provenance["source_agent"] == "Player"
    assert provenance["claimed_origin_observer"] == "team_b"
    # The same transmitted claim can be relayed again without becoming another
    # independent firsthand observation in the recipient's persistent mind.
    second = life.commit("action", {"action": "share", "recipient": "team_a", "event_id": forwarded["event_id"]})["receipt"]
    assert second["payload"]["origin_event"] == original
    assert life.minds["team_a"].provenance(second["event_id"])["kind"] == "testimony"


@pytest.mark.parametrize("name", ["shared_observatory", "pompeii_life"])
def test_compiled_actual_worlds_match_minute_reference_with_exact_and_conservative_time(name):
    hashes, ledgers = [], []
    for mode, strategy in (("live", "exact"), ("compress", "exact"), ("compress", "adaptive")):
        life = runtime(name)
        life.commit("advance", {"minutes": 7 * 1440, "mode": mode, "strategy": strategy})
        hashes.append(life.state_hash())
        ledgers.append(life.world.ledger.content_hash())
        assert life.last_time["total_lateness"] == 0
        assert life.last_time["cosmetic_omitted_count"] == 0
    assert len(set(hashes)) == len(set(ledgers)) == 1
