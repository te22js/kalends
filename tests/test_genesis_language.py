"""Capability and information-boundary tests for player input compilation."""
import copy

import pytest

from kalends.genesis.language import compile_utterance


@pytest.fixture
def views():
    citizen = {"role": "merchant", "trust_player": .3, "experiences": [
        {"event_id": 12, "text": "Player said supply was disrupted.", "source_agent": "Player"}],
        "beliefs": {"grain.supply": {"value": "disrupted", "as_of": 2, "evidence_ids": [12]}},
        "commitments": []}
    return citizen, {"cash": 75, "inventory": 0, "tick": 3, "experiences": []}


def test_a_message_is_a_private_claim_proposal_and_does_not_mutate_views(views):
    citizen, player = views
    before = copy.deepcopy(views)
    result = compile_utterance("I heard that tomorrow's grain shipment isn't arriving.", "Livia", citizen, player)
    action = result["interpretations"][0]["action"]
    assert action == {"kind": "claim", "recipient": "Livia", "value": "disrupted", "as_of": 3, "root_event": None}
    assert result["interpretations"][0]["requires_confirmation"]
    assert views == before


def test_ambiguous_supply_message_requires_a_choice(views):
    result = compile_utterance("Maybe grain is available or disrupted", "Livia", *views)
    assert len(result["interpretations"]) == 2
    assert result["clarification"]


def test_dialogue_cites_only_retained_evidence_and_admits_forgetting(views):
    citizen, player = views
    result = compile_utterance("Why don't you trust me?", "Livia", citizen, player)
    assert result["reply"]["evidence_ids"] == [12]
    citizen["experiences"] = []
    result = compile_utterance("Why don't you trust me?", "Livia", citizen, player)
    assert result["reply"]["evidence_ids"] == []
    assert "cannot recall" in result["reply"]["text"]
    result = compile_utterance("What do you know about grain?", "Livia", citizen, player)
    assert result["reply"]["epistemic_status"] == "uncertain"


def test_adapter_cannot_invent_evidence_or_operator_capabilities(views):
    class BadAdapter:
        model_id = "test/untrusted"

        def propose(self, *args):
            return {"interpretations": [], "reply": {"text": "I saw it", "evidence_ids": [999]}, "clarification": None}

    with pytest.raises(ValueError, match="outside"):
        compile_utterance("hello", "Livia", *views, adapter=BadAdapter())

    class OperatorAdapter:
        model_id = "test/untrusted"

        def propose(self, *args):
            return {"interpretations": [{"action": {"kind": "set_truth", "value": "available"}}], "reply": None}

    with pytest.raises(ValueError, match="unsupported"):
        compile_utterance("change truth", "Livia", *views, adapter=OperatorAdapter())


def test_inspection_requires_actual_player_cash(views):
    citizen, player = views
    player["cash"] = 1
    with pytest.raises(ValueError, match="costs 2"):
        compile_utterance("I want to verify the grain supply.", "Livia", citizen, player)


def test_needs_a_quantity_instead_of_guessing_a_commitment(views):
    result = compile_utterance("I want a contract", "Livia", *views)
    assert not result["interpretations"]
    assert "How many" in result["clarification"]


def test_a_correction_cannot_claim_an_unseen_inspection(views):
    citizen, player = views
    result = compile_utterance("I verified the grain supply", "Livia", citizen, player)
    assert not result["interpretations"]
    player["experiences"] = [{"kind": "observed", "subject": "grain", "predicate": "supply",
        "value": "available", "as_of": 1, "event_id": 7, "claimed_origin_event": 7}]
    result = compile_utterance("Share what I verified", "Livia", citizen, player)
    action = result["interpretations"][0]["action"]
    assert action["root_event"] == 7
    assert action["as_of"] == 1


def test_optional_adapter_cannot_smuggle_narration_as_clarification_and_malformed_action_is_rejected(views):
    class BadAdapter:
        model_id = "test/untrusted"

        def propose(self, *args):
            return {"interpretations": [], "reply": None,
                    "clarification": "Your rumour caused a loss of 40 denarii."}

    result = compile_utterance("hello", "Livia", *views, adapter=BadAdapter())
    assert "40" not in result["clarification"]
    class MalformedAdapter(BadAdapter):
        def propose(self, *args):
            return {"interpretations": ["not an action"]}

    with pytest.raises(ValueError, match="action object"):
        compile_utterance("hello", "Livia", *views, adapter=MalformedAdapter())


def test_trust_explanation_never_uses_unrelated_citizen_memories(views):
    citizen, player = views
    citizen["experiences"] = [{"event_id": 99, "source_agent": "Dama", "text": "I distrusted Dama's claim; my trust changed."}]
    result = compile_utterance("Why don't you trust me?", "Livia", citizen, player)
    assert result["reply"]["epistemic_status"] == "uncertain"
    assert result["reply"]["evidence_ids"] == []
    assert "Dama" not in result["reply"]["text"]
