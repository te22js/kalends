"""Independent regressions for Genesis confirmation and historical identity.

The custom-adapter cases deliberately distrust presentation text as well as
capability schemas. The fork cases reference sources that survive the edit.
"""
import copy

import pytest

from kalends.genesis.language import OfflineAdapter, compile_utterance
from kalends.genesis.server import GenesisSession


def say(session, text, recipient="Livia"):
    proposal = session.propose({"recipient": recipient, "text": text})
    return session.act({"proposal_id": proposal["proposal_id"],
                        "interpretation_id": "0"})["receipt"]


def views():
    return ({"id": "Livia", "role": "merchant", "trust_player": .6,
             "experiences": [], "beliefs": {}, "commitments": []},
            {"id": "Player", "cash": 75, "tick": 2, "experiences": []})


def test_an_adapter_cannot_describe_a_paid_inspection_as_a_free_greeting():
    class DeceptiveAdapter:
        model_id = "test/deceptive-presentation"

        def propose(self, text, recipient, view, player_view):
            return {"interpretations": [{"id": "0", "label": "Free hello",
                     "action": {"kind": "verify", "agent": "Player"},
                     "transmission": "Only say hello. No money is spent.",
                     "requires_confirmation": False}], "reply": None,
                    "clarification": None}

    result = compile_utterance("hello", "Livia", *views(), adapter=DeceptiveAdapter())
    interpretation = result["interpretations"][0]
    assert interpretation["requires_confirmation"] is True
    assert "No money is spent" not in interpretation["transmission"]
    assert "2" in interpretation["transmission"]


def test_a_custom_subclass_does_not_inherit_trust_for_uncited_generated_prose():
    class HallucinatingSubclass(OfflineAdapter):
        model_id = "test/subclass-prose"

        def propose(self, *args):
            return {"interpretations": [], "reply": {
                "text": "The secret shipment arrives at midnight; I inspected it.",
                "evidence_ids": [], "epistemic_status": "certain"},
                "clarification": None}

    result = compile_utterance("hello", "Livia", *views(), adapter=HallucinatingSubclass())
    assert "secret shipment" not in result["reply"]["text"]
    assert result["reply"]["epistemic_status"] == "uncertain"


def test_custom_clarification_cannot_smuggle_an_unverified_causal_account():
    class FabricatedClarification:
        model_id = "test/clarification-prose"

        def propose(self, *args):
            return {"interpretations": [], "reply": None,
                    "clarification": "Your rumour caused Livia to lose 40 denarii. Should I apologize?"}

    result = compile_utterance("hello", "Livia", *views(), adapter=FabricatedClarification())
    assert "lose 40 denarii" not in str(result.get("clarification"))


def test_malformed_adapter_interpretation_is_a_validation_error():
    class MalformedAdapter:
        model_id = "test/malformed-entry"

        def propose(self, *args):
            return {"interpretations": ["not an interpretation object"],
                    "reply": None, "clarification": None}

    with pytest.raises(ValueError):
        compile_utterance("hello", "Livia", *views(), adapter=MalformedAdapter())


def test_current_moment_correction_preserves_already_confirmed_same_tick_actions():
    session = GenesisSession()
    say(session, "Grain supply is disrupted")
    prefix = [event.to_dict() for event in session.original.ledger.events]
    session.apply("mode", {"mode": "operator"})
    session.apply("fork", {"kind": "correction", "agent": "Livia"})
    assert [event.to_dict() for event in session.branch.ledger.events[:len(prefix)]] == prefix
    assert [event.to_dict() for event in session.original.ledger.events] == prefix


def test_removing_one_claim_remaps_a_later_retraction_of_a_surviving_claim():
    session = GenesisSession()
    removed = say(session, "Grain supply is available")
    retained = say(session, "Grain supply is disrupted")
    say(session, "retract #%s" % retained["event_id"])
    before = session.original.ledger.content_hash()
    session.apply("mode", {"mode": "operator"})
    session.apply("fork", {"kind": "remove_message", "event_id": removed["event_id"]})
    claims = [event for event in session.branch.ledger.events
              if event.payload.get("category") == "player_message"]
    retractions = [event for event in session.branch.ledger.events
                   if event.payload.get("category") == "retraction"]
    assert len(claims) == len(retractions) == 1
    assert claims[0].payload["value"] == "disrupted"
    assert retractions[0].payload["value"] == str(claims[0].event_id)
    assert session.original.ledger.content_hash() == before


def test_removing_a_claim_remaps_a_later_surviving_inspection_reference():
    session = GenesisSession()
    removed = say(session, "Grain supply is disrupted")
    say(session, "verify the grain supply")
    session.apply("step", {"count": 1})
    say(session, "Share what I verified")
    before = session.original.ledger.content_hash()
    session.apply("mode", {"mode": "operator"})
    session.apply("fork", {"kind": "remove_message", "event_id": removed["event_id"]})
    surviving = [event for event in session.branch.ledger.events
                 if event.payload.get("category") == "player_message"]
    assert len(surviving) == 1
    root = session.branch.ledger.events[surviving[0].payload["root_event"]]
    assert root.payload.get("category") == "inspection"
    assert "Player" in root.actors
    assert root.payload["value"] == surviving[0].payload["value"]
    assert session.original.ledger.content_hash() == before


def test_unconfirmed_proposals_never_enter_a_historical_rerun_or_restart(tmp_path):
    path = tmp_path / "adversarial-session.json"
    session = GenesisSession(path)
    ledger = session.original.ledger.content_hash()
    pending = session.propose({"recipient": "Livia", "text": "Grain is disrupted"})
    session.apply("mode", {"mode": "operator"})
    session.apply("fork", {"kind": "none"})
    assert session.original.ledger.content_hash() == ledger
    assert session.branch.ledger.content_hash() == ledger
    restored = GenesisSession(path)
    assert restored.original.ledger.content_hash() == ledger
    assert restored.branch.ledger.content_hash() == ledger
    assert not restored.proposals[pending["proposal_id"]]["accepted"]


def test_cited_dialogue_disclosure_does_not_open_unrelated_private_events():
    session = GenesisSession()
    reply = session.propose({"recipient": "Flavia", "text": "What do you know about grain?"})["reply"]
    disclosed = set(reply["evidence_ids"])
    before = copy.deepcopy(session.original.private_view("Flavia"))
    for event_id in disclosed:
        trace = session.trace(event_id)
        assert {event["event_id"] for event in trace["events"]}.issubset(session._visible_ids(session.original))
        assert all(link["source"] in session._visible_ids(session.original)
                   and link["target"] in session._visible_ids(session.original)
                   for link in trace["links"])
    assert session.original.private_view("Flavia") == before
