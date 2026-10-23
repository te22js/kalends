"""The live host scopes optional assistance and grants it no mutation path."""
import json

import pytest

from kalends.experience_os.server import ExperienceService


def test_default_host_ignores_external_provider_environment_and_scopes_debrief(monkeypatch):
    monkeypatch.setenv("KALENDS_AI_PROVIDER", "openai_responses")
    monkeypatch.setenv("KALENDS_AI_ALLOW_EXTERNAL", "1")
    service = ExperienceService()
    life = service.get("shared_observatory")
    before = life.state_hash(), list(life.commands)
    hidden = {e.event_id for e in life.world.ledger.events if e.event_id not in life.visible_ids()}
    result = service.assist(life.spec.id, {"task": "debrief"})
    assert result["receipt"]["provider"] == "offline"
    assert not set(result["output"]["event_ids"]) & hidden
    assert all(row["event_id"] in life.visible_ids() for row in result["output"]["clauses"])
    assert (life.state_hash(), life.commands) == before
    assert service.cognition.metrics["external_calls"] == 0


def test_author_drafts_require_explicit_lab_and_never_compile_or_replace_a_life():
    service = ExperienceService()
    life = service.get("shared_observatory")
    before = {k: w.state_hash() for k, w in service.worlds.items()}
    with pytest.raises(ValueError):
        service.assist(life.spec.id, {"task": "draft_spec", "prompt": "Practice coordination"})
    draft = service.assist(life.spec.id, {"task": "draft_spec", "prompt": "Practice coordination", "mode": "lab"})
    assert draft["output"]["compiler_validated"] and draft["review_required"]
    assert {k: w.state_hash() for k, w in service.worlds.items()} == before
    for task in ("debrief", "plan", "consolidate"):
        with pytest.raises(ValueError):
            service.assist(life.spec.id, {"task": task, "truth": {"condition": "fragile"}})
        proposal = service.assist(life.spec.id, {"task": task})
        assert proposal["review_required"]
        assert {k: w.state_hash() for k, w in service.worlds.items()} == before


def test_mismatched_embedded_spec_rejects_without_rewriting_valid_journal(tmp_path):
    service = ExperienceService(tmp_path)
    life = service.get("shared_observatory")
    document = json.loads(life.journal_path.read_text())
    document["spec"]["title"] = "Forged metadata"
    life.journal_path.write_text(json.dumps(document))
    before = life.journal_path.read_bytes()
    from kalends.experience_os.runtime import ExperienceRuntime
    with pytest.raises(ValueError, match="revision/configuration"):
        ExperienceRuntime(life.spec, journal_path=life.journal_path)
    assert life.journal_path.read_bytes() == before
