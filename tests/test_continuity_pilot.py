"""Bounded optional pilot tests: deterministic mocks/injected wire only."""
import copy
import json
import threading

import pytest

from kalends.continuity_release.pilot import (
    CharacterPilot, FIXTURE_ENDPOINT, PHRASES, PilotConfig, RESPONSES_ENDPOINT, main,
)
from kalends_rebirth.ai import Cognition, LocalJSONAdapter, MockAdapter, OpenAIResponsesAdapter


@pytest.fixture
def scope():
    return {"actor": "Sabina", "viewer": "Player", "minute": 10,
        "evidence": [{"event_id": 4, "text": "The receipt records a payment of three coins.", "at": 5, "kind": "direct"},
                     {"event_id": 7, "text": "The retained record marks the promise as open.", "at": 8, "kind": "event"}],
        "allowed_event_ids": [4, 7], "retained_event_ids": [4, 7], "admitted_event_ids": [4, 7],
        "options": [{"id": "inspect", "label": "Review the receipt", "evidence_ids": [4]},
                    {"id": "reconcile", "label": "Review both records", "evidence_ids": [4, 7]}]}


def selection(**updates):
    return {"phrase_id": "careful", "event_ids": [4], "choice_id": "inspect", "evidence_ids": [4], **updates}


def fixture_pilot(payload=None, **limits):
    adapter = MockAdapter(selection() if payload is None else payload)
    config = PilotConfig(enabled=True, authorized_endpoint=FIXTURE_ENDPOINT,
        session_cap_usd=.01, fixture_mode=True, **limits)
    return CharacterPilot(config, cognition=Cognition(adapter)), adapter


def wire(payload=None, *, usage=True, status="completed"):
    response = {"id": "offline-fixture-only", "status": status,
        "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps(payload or selection())}]}]}
    if usage:
        response["usage"] = {"input_tokens": 100, "output_tokens": 20}
    return response


def wire_pilot(transport, *, budget=.01, cap=.01, **limits):
    adapter = OpenAIResponsesAdapter(api_key="fixture-key", model="fixture-model", enabled=True,
        budget_usd=budget, input_usd_per_million=1, output_usd_per_million=2, transport=transport)
    config = PilotConfig(enabled=True, authorized_endpoint=RESPONSES_ENDPOINT,
        session_cap_usd=cap, fixture_mode=True, **limits)
    return CharacterPilot(config, cognition=Cognition(adapter)), adapter


def test_default_never_reads_environment_or_credentials_or_calls_provider(monkeypatch, scope):
    monkeypatch.setenv("KALENDS_AI_PROVIDER", "openai_responses")
    monkeypatch.setenv("KALENDS_AI_ALLOW_EXTERNAL", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "ENVIRONMENT_SENTINEL")
    monkeypatch.setattr(Cognition, "from_env", lambda *args, **kwargs: pytest.fail("Environment must not be read"))
    pilot = CharacterPilot()
    result = pilot.interact(scope, local_text="LOCAL SENTINEL")
    assert result["receipt"]["status"] == "DISABLED"
    assert result["receipt"]["code"] == "explicit_enable_required"
    assert result["receipt"]["attempts"] == 0
    assert pilot.cognition.metrics["calls"] == 0
    assert "SENTINEL" not in json.dumps([result, pilot.status(), pilot.cognition.debug()])


@pytest.mark.parametrize("updates,reason", [
    ({"enabled": False}, "explicit_enable_required"),
    ({"authorized_endpoint": None}, "authorized_endpoint_required"),
    ({"session_cap_usd": None}, "positive_numeric_cap_required"),
    ({"session_cap_usd": 0}, "positive_numeric_cap_required"),
    ({"fixture_mode": False}, "explicit_fixture_configuration_required"),
    ({"authorized_endpoint": "https://unapproved.example"}, "explicit_fixture_configuration_required"),
])
def test_all_enable_endpoint_cap_gates_are_required(scope, updates, reason):
    config = {"enabled": True, "authorized_endpoint": FIXTURE_ENDPOINT, "session_cap_usd": .01, "fixture_mode": True, **updates}
    adapter = MockAdapter(selection())
    pilot = CharacterPilot(PilotConfig(**config), cognition=Cognition(adapter))
    assert pilot.interact(scope)["receipt"]["code"] == reason
    assert adapter.calls == []


@pytest.mark.parametrize("updates", [
    {"session_cap_usd": True}, {"session_cap_usd": float("nan")}, {"session_cap_usd": float("inf")},
    {"session_cap_usd": -1}, {"enabled": 1}, {"max_turns": 6}, {"max_turns": True},
    {"max_context_bytes": 12001}, {"max_output_tokens": 513}, {"max_output_bytes": 4001},
    {"timeout_seconds": 6}, {"timeout_seconds": float("nan")},
])
def test_invalid_configuration_cannot_expand_hard_limits(updates):
    with pytest.raises(ValueError):
        PilotConfig(**updates)


def test_character_clauses_are_literal_and_action_remains_offered(scope):
    pilot, adapter = fixture_pilot(selection(event_ids=[7, 4], choice_id="reconcile", evidence_ids=[7, 4]))
    before = copy.deepcopy(scope)
    result = pilot.interact(scope)
    output = result["output"]
    assert result["receipt"]["status"] == "ACCEPTED"
    assert output["text"] == PHRASES["careful"] + scope["evidence"][1]["text"] + " " + scope["evidence"][0]["text"]
    assert [clause["support_ids"] for clause in output["clauses"]] == [[7], [4]]
    assert all(clause["audit"] == "literal_host_evidence" for clause in output["clauses"])
    offered = output["action_suggestion"]
    assert offered["status"] == "OFFERED" and offered["choice_id"] == "reconcile"
    assert offered["review_required"] and offered["confirm_required"] and offered["current_state_revalidation_required"]
    assert result["review_required"] and result["confirm_required"]
    assert output["world_effects"] == 0 and scope == before
    assert "action" not in offered and adapter.calls[0]["task"] == "dialogue"
    assert pilot.cognition.policies["dialogue"].retries == 0
    assert pilot.cognition.cache_size == 0


@pytest.mark.parametrize("kind,prefix", [("testimony", "The supplied testimony states: "),
                                         ("inference", "The supplied inference states: ")])
def test_source_uncertainty_and_observation_time_survive_display(scope, kind, prefix):
    scope["evidence"][0]["kind"] = kind
    pilot, _ = fixture_pilot()
    result = pilot.interact(scope)
    clause = result["output"]["clauses"][0]
    assert clause["kind"] == kind and clause["at"] == 5
    assert clause["text"] == scope["evidence"][0]["text"]
    assert result["output"]["text"] == PHRASES["careful"] + prefix + clause["text"]


def test_existing_runtime_caller_uses_only_npc_retained_and_shared_admitted_episodes():
    from kalends.experience_os.compiler import ExperienceCompilerV1, SPEC_DIR
    runtime = ExperienceCompilerV1().compile(SPEC_DIR / "shared_observatory.json")
    actor, viewer = "team_b", "Player"
    before, commands = runtime.state_hash(), copy.deepcopy(runtime.commands)
    with runtime.lock:
        mind = runtime.minds[actor]
        allowed = set(mind.retained_event_ids()) & runtime.visible_ids(actor) & runtime.visible_ids(viewer)
        rows = [row for row in mind.to_dict()["base"]["episodes"]
                if row["event_id"] in allowed and row.get("accepted") is True
                and row["observed_at"] <= runtime.minute and len(row["text"]) <= 500][-8:]
        kinds = {"observed": "direct", "told": "testimony", "episodic": "event"}
        evidence = [{"event_id": row["event_id"], "text": row["text"],
                     "at": row["observed_at"], "kind": kinds[row["kind"]]} for row in rows]
        ids = [row["event_id"] for row in evidence]
        scope = {"actor": actor, "viewer": viewer, "minute": runtime.minute, "evidence": evidence,
            "allowed_event_ids": ids, "retained_event_ids": ids, "admitted_event_ids": ids, "options": []}
    assert ids and set(mind.retained_event_ids()) - runtime.visible_ids(viewer)
    pilot, adapter = fixture_pilot(selection(event_ids=ids[:1], choice_id="wait", evidence_ids=[]))
    result = pilot.interact(scope)
    assert result["receipt"]["status"] == "ACCEPTED"
    assert {row["event_id"] for row in adapter.calls[0]["context"]["evidence"]} <= allowed
    assert result["output"]["clauses"][0]["text"] == evidence[0]["text"]
    assert result["output"]["action_suggestion"]["status"] == "OFFERED"
    assert runtime.state_hash() == before and runtime.commands == commands


@pytest.mark.parametrize("payload", [
    selection(text="A fire destroyed the town."),
    selection(phrase_id="I privately remember another character's secret."),
    selection(event_ids=[999]), selection(event_ids=[4, 4]), selection(event_ids=[True]),
    selection(choice_id="mint_money", evidence_ids=[]), selection(evidence_ids=[7]),
    selection(choice_id="wait", evidence_ids=[4]), selection(execute=True),
    selection(world_patch={"cash": 100}), {"raw_prose": "Unsupported claim"},
    selection(phrase_id=[]), selection(choice_id={}),
])
def test_claim_and_action_injection_is_rejected_once_with_safe_fallback(scope, payload):
    pilot, adapter = fixture_pilot(payload)
    result = pilot.interact(scope)
    assert result["receipt"]["status"] == "FALLBACK"
    assert result["receipt"]["attempts"] == 1 and len(adapter.calls) == 1
    assert result["output"]["clauses"] == []
    assert result["output"]["action_suggestion"]["choice_id"] == "wait"
    assert result["output"]["action_suggestion"]["status"] == "OFFERED"
    assert "Unsupported claim" not in json.dumps(pilot.status())


@pytest.mark.parametrize("field,value", [
    ("archive", [{"event_id": 999, "text": "PRIVATE ARCHIVE SENTINEL"}]),
    ("world", {"private_truth": "PRIVATE WORLD SENTINEL"}),
    ("retained_event_ids", [4]), ("admitted_event_ids", [7]), ("allowed_event_ids", [4]),
    ("retained_event_ids", [4, True]), ("minute", True),
])
def test_unretained_unadmitted_or_unbounded_ingress_never_reaches_model(scope, field, value):
    pilot, adapter = fixture_pilot()
    scope[field] = value
    result = pilot.interact(scope)
    assert result["output"] is None and result["receipt"]["status"] == "REJECTED"
    assert result["receipt"]["code"] == "host_scope_rejected"
    assert adapter.calls == [] and "SENTINEL" not in json.dumps(pilot.status())


def test_permissions_do_not_retrieve_missing_evidence_or_disclose_disabled_options(scope):
    for field in ("allowed_event_ids", "retained_event_ids", "admitted_event_ids"):
        scope[field].append(999)
    scope["options"][1]["enabled"] = False
    pilot, adapter = fixture_pilot(selection(choice_id="reconcile", evidence_ids=[4, 7]))
    result = pilot.interact(scope)
    assert result["receipt"]["status"] == "FALLBACK"
    context = adapter.calls[0]["context"]
    assert all(context[field] == [4, 7] for field in ("allowed_event_ids", "retained_event_ids", "admitted_event_ids"))
    assert [option["id"] for option in context["options"]] == ["inspect"]


def test_future_context_and_oversized_context_get_redacted_rejection(scope):
    pilot, adapter = fixture_pilot()
    scope["evidence"][0]["at"] = 11
    assert pilot.interact(scope)["receipt"]["status"] == "REJECTED"
    scope["evidence"][0]["text"] = "PRIVATE_SENTINEL" * 1000
    assert pilot.interact(scope)["receipt"]["status"] == "REJECTED"
    assert adapter.calls == [] and "PRIVATE_SENTINEL" not in json.dumps(pilot.status())


def test_raw_local_free_text_is_excluded_from_request_hash_receipts_and_cache(scope):
    pilot, adapter = fixture_pilot()
    first = pilot.interact(scope, local_text="PRIVATE FIRST TEXT")
    second = pilot.interact(scope, local_text="PRIVATE SECOND TEXT")
    assert first["receipt"]["context_hash"] == second["receipt"]["context_hash"]
    assert "PRIVATE" not in json.dumps([adapter.calls, pilot.status(), pilot.cognition.debug(), first, second])
    assert pilot.cognition.debug()["cache_entries"] == 0


def test_turn_and_local_text_limits_are_enforced(scope):
    pilot, adapter = fixture_pilot(max_turns=2)
    assert pilot.interact(scope, local_text="x" * 2001)["receipt"]["code"] == "local_text_limit"
    assert pilot.interact(scope)["receipt"]["status"] == "ACCEPTED"
    assert pilot.interact(scope)["receipt"]["code"] == "turn_limit"
    assert len(adapter.calls) == 1 and pilot.status()["turns_remaining"] == 0


def test_invalid_local_unicode_has_a_redacted_rejection_receipt(scope):
    pilot, adapter = fixture_pilot()
    assert pilot.interact(scope, local_text="\ud800")["receipt"]["code"] == "local_text_limit"
    assert adapter.calls == []


def test_utf8_output_byte_limit_rejects_a_structurally_valid_large_selection(scope):
    scope["evidence"][0]["text"] = "界" * 400
    pilot, adapter = fixture_pilot(max_output_bytes=1400)
    result = pilot.interact(scope)
    assert len(adapter.calls) == 1
    assert result["receipt"]["status"] == "FALLBACK"
    assert len(json.dumps(result["output"], ensure_ascii=False, separators=(",", ":")).encode()) <= 1400


def test_one_inflight_call_and_timeout_halt_prevent_later_retries(scope):
    started, release = threading.Event(), threading.Event()
    def blocked(request):
        started.set()
        release.wait(2)
        return selection()
    pilot, adapter = fixture_pilot(blocked, timeout_seconds=.05)
    results = []
    worker = threading.Thread(target=lambda: results.append(pilot.interact(scope)))
    try:
        worker.start()
        assert started.wait(1)
        assert pilot.interact(scope)["receipt"]["code"] == "concurrency_limit"
        worker.join(1)
        assert not worker.is_alive()
        assert results[0]["receipt"]["status"] == "FALLBACK"
        assert pilot.interact(scope)["receipt"]["code"] == "uncertain_provider_charge"
        assert len(adapter.calls) == 1
    finally:
        release.set()
        worker.join(1)


def test_existing_wire_accounting_schema_and_budget_are_reused_without_network(scope):
    bodies = []
    def transport(body, timeout):
        bodies.append(body)
        return wire()
    pilot, adapter = wire_pilot(transport)
    result = pilot.interact(scope)
    assert result["receipt"]["kind"] == "transport_fixture"
    assert result["receipt"]["estimated_cost_usd"] == pytest.approx(.00014)
    assert result["receipt"]["input_tokens"] == 100
    assert adapter.network_calls == 0 and adapter.fixture_calls == 1
    assert adapter.spent_usd == pytest.approx(.00014)
    assert bodies[0]["store"] is False and bodies[0]["max_output_tokens"] == 256
    assert bodies[0]["text"]["format"]["strict"] is True
    assert "fixture-key" not in json.dumps([bodies, result, pilot.status()])


def test_semantic_rejection_still_accounts_one_charge(scope):
    pilot, adapter = wire_pilot(lambda *args: wire(selection(event_ids=[999])))
    result = pilot.interact(scope)
    assert result["receipt"]["status"] == "FALLBACK"
    assert result["receipt"]["estimated_cost_usd"] == pytest.approx(.00014)
    assert adapter.fixture_calls == 1 and adapter.spent_usd == pytest.approx(.00014)


@pytest.mark.parametrize("response", [wire(usage=False), {"not": "a usable envelope"}])
def test_uncertain_charge_retains_reserve_and_halts_even_across_turns(scope, response):
    pilot, adapter = wire_pilot(lambda *args: response)
    result = pilot.interact(scope)
    assert result["receipt"]["unknown_cost_attempts"] == 1
    assert result["receipt"]["estimated_cost_usd"] is None
    assert adapter.spent_usd > 0 and adapter.reserved_usd == 0
    assert pilot.interact(scope)["receipt"]["code"] == "uncertain_provider_charge"
    assert adapter.fixture_calls == 1 and adapter.network_calls == 0


def test_known_failed_response_is_charged_once(scope):
    pilot, adapter = wire_pilot(lambda *args: wire(status="incomplete"))
    result = pilot.interact(scope)
    assert result["receipt"]["status"] == "FALLBACK"
    assert result["receipt"]["estimated_cost_usd"] == pytest.approx(.00014)
    assert result["receipt"]["unknown_cost_attempts"] == 0 and adapter.fixture_calls == 1


def test_wire_timeout_holds_reserve_and_never_starts_a_second_call(scope):
    release = threading.Event()
    def blocked(body, timeout):
        release.wait(2)
        return wire()
    pilot, adapter = wire_pilot(blocked, timeout_seconds=.01)
    try:
        result = pilot.interact(scope)
        assert result["receipt"]["unknown_cost_attempts"] == 1
        assert result["receipt"]["estimated_cost_usd"] is None
        assert adapter.reserved_usd > 0
        assert pilot.interact(scope)["receipt"]["code"] == "uncertain_provider_charge"
        assert adapter.fixture_calls == 1 and adapter.network_calls == 0
    finally:
        release.set()
        pilot.cognition._pending.result(timeout=1)
    assert adapter.reserved_usd == 0 and adapter.spent_usd == pytest.approx(.00014)


def test_reported_output_token_overrun_is_accounted_rejected_and_terminal(scope):
    response = wire()
    response["usage"]["output_tokens"] = 257
    pilot, adapter = wire_pilot(lambda *args: response)
    result = pilot.interact(scope)
    assert result["receipt"]["status"] == "FALLBACK"
    assert result["output"]["clauses"] == []
    assert result["receipt"]["estimated_cost_usd"] == pytest.approx(.000614)
    assert pilot.interact(scope)["receipt"]["code"] == "provider_output_limit"
    assert adapter.fixture_calls == 1


def test_insufficient_budget_rejects_before_any_injected_transport(scope):
    calls = []
    pilot, adapter = wire_pilot(lambda *args: calls.append(args), budget=.000001, cap=.000001)
    result = pilot.interact(scope)
    assert result["receipt"]["status"] == "FALLBACK"
    assert result["receipt"]["errors"] == ["BudgetError"]
    assert calls == [] and adapter.spent_usd == 0


def test_adapter_cap_endpoint_and_unpriced_local_fail_closed(scope):
    pilot, adapter = wire_pilot(lambda *args: pytest.fail("Must not call"), budget=.02, cap=.01)
    assert pilot.interact(scope)["receipt"]["code"] == "existing_provider_budget_must_fit_session_cap"
    config = PilotConfig(enabled=True, authorized_endpoint="http://127.0.0.1:11434/kalends", session_cap_usd=.01)
    local = CharacterPilot(config, cognition=Cognition(LocalJSONAdapter(config.authorized_endpoint, enabled=True)))
    assert local.interact(scope)["receipt"]["code"] == "unsupported_or_unpriced_adapter"
    assert adapter.fixture_calls == adapter.network_calls == 0


def test_fixture_mode_cannot_fall_through_to_actual_network(scope):
    adapter = OpenAIResponsesAdapter(api_key="fixture-key", model="fixture-model", enabled=True,
        budget_usd=.01, input_usd_per_million=1, output_usd_per_million=2)
    config = PilotConfig(enabled=True, authorized_endpoint=RESPONSES_ENDPOINT, session_cap_usd=.01, fixture_mode=True)
    pilot = CharacterPilot(config, cognition=Cognition(adapter))
    assert pilot.interact(scope)["receipt"]["code"] == "fixture_mode_requires_injected_transport"
    assert adapter.network_calls == 0


def test_status_and_offline_fixture_cli_do_not_construct_a_live_adapter(capsys, tmp_path):
    assert main(["--status"]) == 0
    status = json.loads(capsys.readouterr().out)
    assert not status["enabled"] and status["network_calls"] == 0
    assert "not production authorization" in status["authorization_scope"]
    assert main(["--offline-fixture"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["receipt"]["kind"] == "mock" and result["output"]["action_suggestion"]["status"] == "OFFERED"
    path = tmp_path / "pilot.json"
    path.write_text(json.dumps({"enabled": False, "max_turns": 1}))
    assert main(["--status", "--config", str(path)]) == 0
    assert json.loads(capsys.readouterr().out)["turns_remaining"] == 1
