"""Participant histories are evidence views, never an operator-memory bridge."""
import json

import pytest

from kalends.experience_os.history import build_history, choices_then
from kalends.experience_os.server import ExperienceService


def test_history_contains_only_admitted_ids_and_no_hidden_condition_or_documents():
    service = ExperienceService()
    for ident in ("shared_observatory", "pompeii_life"):
        life = service.get(ident)
        before = life.state_hash(), list(life.commands)
        history = build_history(life)
        allowed = life.visible_ids()
        assert {i for b in history["beats"] for i in b["evidence_ids"]} <= allowed
        assert {i for b in history["beats"] for i in b["related_event_ids"]} <= allowed
        if ident == "shared_observatory":
            assert "fragile" not in json.dumps(history)
        else:
            for document in life.world.documents.values():
                assert document["text"] not in json.dumps(history)
        assert (life.state_hash(), life.commands) == before


def test_commons_history_distinguishes_promise_allocation_and_actual_delivery():
    life = ExperienceService().get("shared_observatory")
    life.commit("action", {"action": "commit", "recipient": "team_c", "quantity": 4})
    history = build_history(life)
    assert history["known_commitments"][0]["deadline"] == 1439
    assert history["known_commitments"][0]["person"] == "Lin"
    life.commit("action", {"action": "allocate", "allocation": {"team_a": 4, "team_b": 4, "team_c": 4}})
    assert all("outcome" not in p for p in build_history(life)["people"])
    life.commit("advance", {"minutes": 1439})
    history = build_history(life)
    lin = next(p for p in history["people"] if p["id"] == "team_c")
    assert lin["outcome"]["allocated"] == 4 and lin["outcome"]["delivered"] == 0
    assert lin["outcome"]["text"] == "Lin received 0 of 4 allocated units."
    assert all("remembers" not in p["outcome"]["text"] for p in history["people"])
    assert history["known_commitments"] == []
    assert any(b["kind"] == "consequence" for b in history["beats"])


def test_then_evidence_uses_exact_prefix_and_excludes_later_disclosure_and_action_effect():
    life = ExperienceService().get("shared_observatory")
    life.commit("action", {"action": "commit", "recipient": "team_c", "quantity": 4})
    life.commit("action", {"action": "share", "recipient": "team_b"})
    life.commit("action", {"action": "allocate", "allocation": {"team_a": 4, "team_b": 0, "team_c": 4}})
    before = life.state_hash(), list(life.commands)
    choices = choices_then(life)
    assert "fragile" not in json.dumps(choices[0]["then_evidence"])
    assert not choices[0]["known_commitments"]
    assert "fragile" not in json.dumps(choices[1]["then_evidence"])
    assert "fragile" in json.dumps(choices[2]["then_evidence"])
    assert choices[2]["known_commitments"][0]["quantity"] == 4
    for choice in choices:
        assert not any(e["category"] == "institution_decision" for e in choice["then_evidence"])
    assert (life.state_hash(), life.commands) == before


def test_same_minute_return_uses_revision_and_does_not_invent_offline_progress():
    life = ExperienceService().get("shared_observatory")
    life.commit("action", {"action": "commit", "recipient": "team_c", "quantity": 4})
    history = build_history(life, seen_revision=0)
    assert history["minute"] == 0 and history["return_summary"]["changes"]
    assert history["return_summary"]["offline_progress"] is False
    assert build_history(life, seen_revision=1)["return_summary"]["changes"] == []
    with pytest.raises(ValueError):
        build_history(life, seen_revision=True)


def test_public_known_stops_do_not_read_clock_queue_or_hidden_reports(monkeypatch):
    life = ExperienceService().get("shared_observatory")
    monkeypatch.setattr(life.world.clock, "peek", lambda: (_ for _ in ()).throw(AssertionError("private clock read")))
    history = build_history(life)
    assert history["known_stops"][0]["at"] == 1439
    assert history["known_stops"][0]["kind"] == "public_round_deadline"
    assert all(set(row["evidence_ids"]) <= life.visible_ids() for row in history["known_stops"])


def test_pompeii_own_agreement_remains_accessible_independently_of_npc_memory():
    life = ExperienceService().get("pompeii_life")
    life.commit("action", {"action": "move", "location": "household"})
    life.commit("action", {"action": "guarantee_household", "recipient": "Lucius", "quantity": 1})
    history = build_history(life)
    agreement = next(c for c in history["known_commitments"] if c["recipient"] == "Lucius")
    assert agreement["quantity"] == 120 and agreement["deadline"] > life.minute
    assert agreement["source"] == "own institutional commitment register"
    assert set(agreement["evidence_ids"]) <= life.visible_ids()


def test_quiet_routines_are_expandable_and_unchanged_by_projection():
    life = ExperienceService().get("shared_observatory")
    life.commit("advance", {"minutes": 1440})
    before = life.state_hash()
    history = build_history(life, seen_revision=0)
    routine_groups = [group for chapter in history["chapters"] for group in chapter["routines"]]
    assert routine_groups and all(group["expandable"] for group in routine_groups)
    assert any(b["kind"] == "routine" for b in history["beats"])
    assert life.state_hash() == before
