"""Compiled public views must retain legacy payload redaction and visibility."""
import json

import pytest

from kalends.experience_os.compiler import ExperienceCompilerV1, SPEC_DIR
from kalends.experience_os.runtime import ExperienceRuntime
from kalends.experience_os.server import ExperienceService
from kalends_rebirth.ai import Cognition, MockAdapter


def life(journal=None):
    return ExperienceRuntime(ExperienceCompilerV1().load(SPEC_DIR / "pompeii_life.json"), journal_path=journal)


def initial(rows):
    return next(e for e in rows if e["payload"].get("category") == "city_initialized")


def assert_only_owned_initial_accounts(event):
    for field in ("cash", "inventory", "commitments"):
        assert set(event["payload"][field]) == {"Player"}, f"public {field} exposed foreign accounts"


def test_public_events_apply_the_existing_pompeii_payload_projection():
    runtime = life()
    public = initial(runtime.events())
    assert_only_owned_initial_accounts(public)
    raw = runtime.world.ledger.events[public["event_id"]]
    assert public == runtime.world.event_dict(raw, operator=False)
    assert "Felix" in raw.payload["cash"]
    assert "Felix" in initial(runtime.events(operator=True))["payload"]["cash"]


def test_public_snapshot_montage_debrief_and_trace_redact_the_same_initial_accounts():
    runtime = life()
    snapshot = runtime.snapshot()
    event_id = initial(runtime.events())["event_id"]
    surfaces = [snapshot["events"], snapshot["montage"], snapshot["world"]["journal"],
        runtime.debrief()["consequences"], runtime.trace(event_id)["events"]]
    found = 0
    for rows in surfaces:
        matching = [row for row in rows if row["payload"].get("category") == "city_initialized"]
        for event in matching:
            assert_only_owned_initial_accounts(event)
            found += 1
    assert found >= 4
    assert "Felix" in initial(runtime.trace(event_id, operator=True)["events"])["payload"]["inventory"]


def test_hidden_documents_and_npc_decisions_do_not_enter_any_public_surface():
    runtime = life()
    hidden = [e for e in runtime.world.ledger.events if e.payload.get("category") == "rb_document"]
    secret = runtime.world._emit("os_decision", "PRIVATE NPC planning evidence", actors=("Felix",), scope="private",
        private_bookkeeping={"account_balance": 98765}, decision={"action_id": "secret-plan"})
    hidden.append(secret)
    public = json.dumps({"events": runtime.events(), "snapshot": runtime.snapshot(), "debrief": runtime.debrief()})
    assert "PRIVATE NPC planning evidence" not in public and "private_bookkeeping" not in public
    for event in hidden:
        assert event.event_id not in {e["event_id"] for e in runtime.events()}
        with pytest.raises(ValueError, match="not observed"):
            runtime.trace(event.event_id)
        assert runtime.trace(event.event_id, operator=True)["events"]
    for key in ("loading_record", "household_tablet", "market_receipt"):
        assert runtime.world.documents[key]["text"] not in public


def test_actually_disclosed_document_contents_are_preserved_without_exposing_other_sources():
    runtime = life()
    result = runtime.commit("action", {"action": "examine_receipt", "recipient": "Sabina", "quantity": 1})
    receipt = result["receipt"]
    text = runtime.world.documents["market_receipt"]["text"]
    assert receipt["payload"]["document"]["text"] == text
    for view in (runtime.events(), runtime.snapshot()["events"], runtime.debrief()["consequences"], runtime.trace(receipt["event_id"])["events"]):
        event = next(e for e in view if e["event_id"] == receipt["event_id"])
        assert event["payload"]["document"]["text"] == text
    traced = runtime.trace(receipt["event_id"])
    assert traced["hidden_parent_count"] >= 1
    public = json.dumps(runtime.snapshot())
    assert runtime.world.documents["loading_record"]["text"] not in public
    assert runtime.world.documents["household_tablet"]["text"] not in public


def test_projection_reads_and_mutated_returns_leave_canonical_state_journal_and_replay_exact(tmp_path):
    journal = tmp_path / "life.json"
    runtime = life(journal); runtime.save()
    before, saved = runtime.state_hash(), journal.read_bytes()
    public = runtime.events(); initial(public)["payload"]["cash"]["Player"] = -999
    traced = runtime.trace(initial(runtime.events())["event_id"])
    initial(traced["events"])["payload"]["commitments"]["Player"].append({"fake": True})
    runtime.snapshot(); runtime.debrief()
    assert runtime.state_hash() == before and journal.read_bytes() == saved
    assert runtime.world.economy.cash["Player"] == 6
    assert life(journal).state_hash() == before


def test_host_assistance_passes_only_public_event_titles_and_never_caller_private_evidence():
    adapter = MockAdapter()
    service = ExperienceService(cognition=Cognition(adapter))
    runtime = service.get("pompeii_life")
    hidden_ids = {e.event_id for e in runtime.world.ledger.events if not runtime.world._visible(e)}
    before = runtime.state_hash(), len(runtime.commands)
    for task in ("debrief", "consolidate", "plan"):
        result = service.assist("pompeii_life", {"task": task})
        assert result["review_required"]
    assert adapter.calls
    for call in adapter.calls:
        context = call["context"]
        assert set(context["allowed_event_ids"]).isdisjoint(hidden_ids)
        for evidence in context["evidence"]:
            assert set(evidence) == {"event_id", "text", "at", "kind"}
            source = next(e for e in runtime.events() if e["event_id"] == evidence["event_id"])
            assert evidence["text"] == source["payload"]["title"]
        text = json.dumps(context)
        assert "private_bookkeeping" not in text and '"cash"' not in text and '"inventory"' not in text
        for document in runtime.world.documents.values():
            assert document["text"] not in text
    with pytest.raises(ValueError, match="supported assistance"):
        service.assist("pompeii_life", {"task": "debrief", "evidence": [{"event_id": next(iter(hidden_ids)), "text": "secret"}]})
    assert (runtime.state_hash(), len(runtime.commands)) == before


@pytest.mark.parametrize("field,value", [("version", True), ("version", 1.0), ("revision", True), ("revision", 1.0), ("receipt_id", "float_alias")])
def test_saved_replay_metadata_rejects_boolean_and_float_integer_aliases_without_rewriting(tmp_path, field, value):
    path = tmp_path / "saved.json"
    runtime = life(path)
    runtime.commit("action", {"action": "examine_receipt", "recipient": "Sabina", "quantity": 1})
    document = json.loads(path.read_text())
    if field == "version":
        document[field] = value
    elif field == "receipt_id":
        document["commands"][0][field] = float(document["commands"][0][field])
    else:
        document["commands"][0][field] = value
    path.write_text(json.dumps(document))
    saved = path.read_bytes()
    with pytest.raises(ValueError):
        life(path)
    assert path.read_bytes() == saved
