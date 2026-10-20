"""End-to-end participant permissions, confirmation, persistence and reruns."""
import copy
import json

import pytest

from kalends.genesis.server import GenesisSession


def say(session, text="Grain supply is disrupted", recipient="Livia"):
    proposal = session.propose({"recipient": recipient, "text": text})
    return session.act({"proposal_id": proposal["proposal_id"], "interpretation_id": "0"})


def test_proposal_has_no_world_effect_confirmation_is_once_only_and_private():
    session = GenesisSession()
    before = session.original.ledger.content_hash()
    proposal = session.propose({"recipient": "Livia", "text": "Grain is disrupted"})
    assert session.original.ledger.content_hash() == before
    request = {"proposal_id": proposal["proposal_id"], "interpretation_id": "0"}
    response = session.act(request)
    event = response["receipt"]
    assert event["actors"] == ["Player", "Livia"]
    assert session.original.state.facts["grain.supply"] == "available"
    assert not any(e.source_agent == "Player" for e in session.original.remembered("Marcus"))
    after = session.original.ledger.content_hash()
    with pytest.raises(ValueError, match="already confirmed"):
        session.act(request)
    assert session.original.ledger.content_hash() == after


def test_player_api_and_trace_do_not_disclose_private_citizen_records():
    session = GenesisSession()
    state = session.state()["original"]
    for agent in state["agents"]:
        assert not set(agent) & {"beliefs", "experiences", "preferences", "cash", "inventory", "commitments"}
    assert not state.get("decisions")
    assert "operator" not in state
    assert not state["world"].get("facts")
    assert "private" not in session.agent("Livia")
    secret = next(e.event_id for e in session.original.ledger.events if e.payload.get("category") == "supply")
    with pytest.raises(ValueError, match="not accessible"):
        session.trace(secret)
    session.apply("mode", {"mode": "operator"})
    assert session.state()["original"]["operator"]["facts"]
    assert session.trace(secret)["event_id"] == secret


def test_refresh_and_process_restart_recover_conversation_actions_and_historical_fork(tmp_path):
    path = tmp_path / "genesis.json"
    session = GenesisSession(path)
    receipt = say(session)["receipt"]
    session.propose({"recipient": "Livia", "text": "Why don't you trust me?"})
    session.apply("step", {"count": 6})
    session.apply("mode", {"mode": "operator"})
    session.apply("fork", {"kind": "remove_message", "event_id": receipt["event_id"]})
    assert session.branch.tick == session.original.tick
    assert not any(e.payload.get("category") == "player_message" for e in session.branch.ledger.events)
    assert session.original.ledger.events[receipt["event_id"]].payload["category"] == "player_message"
    session.apply("step", {"count": 3})
    session.apply("mode", {"mode": "player"})
    expected = session.state()
    recovered = GenesisSession(path)
    assert recovered.state() == expected
    assert recovered.commands == session.commands
    assert json.loads(path.read_text())["version"] == 2


def test_identity_rerun_preserves_executed_outcomes_and_full_ledger():
    session = GenesisSession()
    say(session)
    session.apply("step", {"count": 14})
    session.apply("mode", {"mode": "operator"})
    session.apply("fork", {"kind": "none", "at_tick": 4})
    assert session.original.ledger.content_hash() == session.branch.ledger.content_hash()
    assert session.original.metrics() == session.branch.metrics()


def test_stale_proposal_and_rejected_order_do_not_mutate_the_world_or_journal(tmp_path):
    session = GenesisSession(tmp_path / "session.json")
    proposal = session.propose({"recipient": "Livia", "text": "Grain is disrupted"})
    session.apply("step", {"count": 1})
    before = (session.original.ledger.content_hash(), copy.deepcopy(session.commands))
    with pytest.raises(ValueError, match="advanced"):
        session.act({"proposal_id": proposal["proposal_id"], "interpretation_id": "0"})
    with pytest.raises(ValueError):
        say(session, "buy 12 grain from Livia")
    assert (session.original.ledger.content_hash(), session.commands) == before


def test_operator_interventions_are_explicit_and_participant_inspection_costs_time_and_cash():
    session = GenesisSession()
    with pytest.raises(ValueError, match="Research mode"):
        session.apply("fork", {"kind": "correction", "agent": "Livia"})
    initial_cash = session.original.economy.cash["Player"]
    say(session, "I want to verify the grain supply")
    assert session.original.economy.cash["Player"] == initial_cash - 2
    assert not any(e.kind == "observed" and e.predicate == "supply" for e in session.original.remembered("Player"))
    session.apply("step", {"count": 1})
    assert any(e.kind == "observed" and e.predicate == "supply" for e in session.original.remembered("Player"))
    session.apply("mode", {"mode": "operator"})
    session.apply("fork", {"kind": "correction", "agent": "Livia"})
    assert session.intervention["operator_intervention"]


def test_return_reports_actual_elapsed_ticks_not_an_unexecuted_story():
    session = GenesisSession()
    state = session.apply("step", {"count": 72})
    report = state["return_report"]
    assert report["from_tick"] == 2
    assert report["to_tick"] == 74
    assert report["elapsed_ticks"] == 72
    assert "background" not in report["summary"]
