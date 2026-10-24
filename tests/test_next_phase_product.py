"""Real life/save/projection boundaries for the participant ProductService."""
import json
import http.client
from http.server import ThreadingHTTPServer
import threading

import pytest

from kalends.experience_os.compiler import ExperienceCompilerV1, SPEC_DIR
from kalends.experience_os.product import ProductService
from kalends.experience_os.runtime import ExperienceRuntime


@pytest.fixture
def product(tmp_path):
    return ProductService(tmp_path / "lives", include_examples=False)


def start(service, template="shared_observatory"):
    return service.start(template)["life"]["id"]


def test_start_creates_unique_personal_ids_and_preserves_the_two_template_lives(product):
    defaults = {ident: (r.state_hash(), r.journal_path.read_bytes()) for ident, r in product.worlds.items()}
    first, second = start(product), start(product)
    roman = start(product, "pompeii_life")
    assert len({first, second, roman}) == 3
    assert not {first, second, roman} & set(defaults)
    assert {m["id"] for m in product.catalog()["lives"]} == {first, second, roman}
    assert {t["id"] for t in product.catalog()["templates"]} == {"shared_observatory", "pompeii_life"}
    for ident, (state, data) in defaults.items():
        assert product.get(ident).state_hash() == state
        assert product.get(ident).journal_path.read_bytes() == data
    restored = ProductService(product.directory, include_examples=False)
    assert {m["id"] for m in restored.catalog()["lives"]} == {first, second, roman}
    assert restored.life(roman)["life"]["participant"] == "Aelia"


def test_one_incompatible_journal_does_not_reset_it_or_block_another_life(product):
    good, bad = start(product), start(product)
    token = product.review(good, {"action": "inspect"})["proposal_id"]
    product.confirm_review(good, token)
    good_life = product.get(good)
    good_hash, good_bytes = good_life.state_hash(), good_life.journal_path.read_bytes()
    bad_path = product.get(bad).journal_path
    document = json.loads(bad_path.read_text())
    document["version"] = 999
    bad_path.write_text(json.dumps(document))
    bad_bytes = bad_path.read_bytes()
    restored = ProductService(product.directory, include_examples=False)
    assert restored.get(good).state_hash() == good_hash
    assert restored.get(good).journal_path.read_bytes() == good_bytes
    assert any(row["id"] == bad and row["save_status"] == "incompatible" for row in restored.catalog()["failures"])
    with pytest.raises(ValueError):
        restored.get(bad)
    assert bad_path.read_bytes() == bad_bytes


def test_review_and_cancel_are_nonmutating_and_private_result_is_disclosed_only_after_confirm(product):
    ident = start(product)
    runtime = product.get(ident)
    before = runtime.state_hash(), len(runtime.commands), runtime.journal_path.read_bytes()
    proposal = product.review(ident, {"action": "inspect"})
    assert "fragile" not in json.dumps(proposal).lower()
    assert proposal["before"]["credits"] == 12 and proposal["after"]["credits"] == 11
    assert (runtime.state_hash(), len(runtime.commands), runtime.journal_path.read_bytes()) == before
    # Cancelling is simply declining to consume the issued proposal.
    assert product.life(ident)["snapshot"]["own_reports"] == []
    accepted = product.confirm_review(ident, proposal["proposal_id"])
    assert accepted["receipt"]["payload"]["value"] == "fragile"
    assert accepted["snapshot"]["metrics"]["own_inspection_spend"] == 1
    assert runtime.world.economy.cash["Player"] == 11 and len(runtime.commands) == 1
    with pytest.raises(ValueError, match="stale|consumed"):
        product.confirm_review(ident, proposal["proposal_id"])
    assert len(runtime.commands) == 1


def test_invalid_cross_life_and_stale_reviews_preserve_actual_accounts(product):
    ident, other = start(product), start(product)
    runtime = product.get(ident)
    before = runtime.state_hash(), len(runtime.commands), runtime.journal_path.read_bytes()
    with pytest.raises(ValueError):
        product.review(ident, {"action": "allocate", "allocation": {"team_a": 5, "team_b": 5, "team_c": 5}})
    assert (runtime.state_hash(), len(runtime.commands), runtime.journal_path.read_bytes()) == before
    proposal = product.review(ident, {"action": "inspect"})
    with pytest.raises(ValueError):
        product.confirm_review(other, proposal["proposal_id"])
    product.advance_product(ident, 1)
    with pytest.raises(ValueError, match="stale|consumed"):
        product.confirm_review(ident, proposal["proposal_id"])
    assert runtime.world.economy.cash["Player"] == 12
    assert not product.get(other).commands


def test_participant_life_and_reflection_never_reintroduce_private_global_spending(product):
    ident = start(product)
    runtime = product.get(ident)
    assert runtime.metrics()["credits_spent"] > 0, "fixture includes private NPC inspections"
    public = product.life(ident)
    metrics = public["snapshot"]["metrics"]
    assert metrics["own_inspection_spend"] == 0 and metrics["reports_received"] == 0
    assert "credits_spent" not in metrics and "information_shared" not in metrics
    reflection = product.reflect(ident)
    assert reflection["debrief"]["outcomes"] == metrics
    assert "fragile" not in json.dumps({"life": public, "reflection": reflection}).lower()


def test_failed_world_save_preserves_journal_accounts_and_review_token(product, monkeypatch):
    ident = start(product)
    runtime = product.get(ident)
    proposal = product.review(ident, {"action": "inspect"})
    before = runtime.state_hash(), len(runtime.commands), runtime.journal_path.read_bytes()
    with monkeypatch.context() as patch:
        patch.setattr(ExperienceRuntime, "save", lambda self: (_ for _ in ()).throw(OSError("injected journal failure")))
        with pytest.raises(OSError, match="journal failure"):
            product.confirm_review(ident, proposal["proposal_id"])
    assert (runtime.state_hash(), len(runtime.commands), runtime.journal_path.read_bytes()) == before
    assert proposal["proposal_id"] in product.proposals
    assert product.confirm_review(ident, proposal["proposal_id"])["snapshot"]["credits"] == 11


def test_metadata_write_failure_after_acceptance_reports_saved_choice_and_never_resubmits(product, monkeypatch):
    import kalends.experience_os.product as module
    ident = start(product)
    runtime = product.get(ident)
    proposal = product.review(ident, {"action": "inspect"})
    with monkeypatch.context() as patch:
        patch.setattr(module, "atomic_json", lambda *args: (_ for _ in ()).throw(OSError("injected metadata failure")))
        result = product.confirm_review(ident, proposal["proposal_id"])
    assert result["metadata_warning"] and result["receipt"]
    assert runtime.world.economy.cash["Player"] == 11 and len(runtime.commands) == 1
    restored = ProductService(product.directory, include_examples=False)
    assert restored.get(ident).state_hash() == runtime.state_hash()
    with pytest.raises(ValueError):
        product.confirm_review(ident, proposal["proposal_id"])
    assert len(runtime.commands) == 1


def test_newborn_with_failed_metadata_write_remains_discoverable_after_restart(product, monkeypatch):
    import kalends.experience_os.product as module
    with monkeypatch.context() as patch:
        patch.setattr(module, "atomic_json", lambda *args: (_ for _ in ()).throw(OSError("injected metadata failure")))
        saved = product.start("shared_observatory")
        assert saved["metadata_warning"] and saved["life"]["save_status"] == "saved"
    personal = [i for i in product.worlds if i not in product.templates]
    assert len(personal) == 1 and product.get(personal[0]).journal_path.exists()
    restored = ProductService(product.directory, include_examples=False)
    assert personal[0] in {m["id"] for m in restored.catalog()["lives"]}
    assert restored.get(personal[0]).commands == []


def test_known_incompatible_metadata_never_turns_an_accepted_world_choice_into_reported_failure(product):
    ident = start(product)
    product.meta_path.write_text("{invalid metadata")
    restored = ProductService(product.directory, include_examples=False)
    runtime = restored.get(ident)
    before = runtime.state_hash(), runtime.journal_path.read_bytes()
    try:
        proposal = restored.review(ident, {"action": "inspect"})
        result = restored.confirm_review(ident, proposal["proposal_id"])
    except (ValueError, OSError):
        assert (runtime.state_hash(), runtime.journal_path.read_bytes()) == before, "a failed response must not conceal an already accepted charge"
    else:
        assert result["receipt"] and result.get("metadata_warning")
        assert runtime.world.economy.cash["Player"] == 11


def test_invalid_metadata_entry_is_reported_without_crashing_catalog_or_rewriting_it(product):
    ident = start(product)
    document = json.loads(product.meta_path.read_text())
    document["lives"][ident] = None
    product.meta_path.write_text(json.dumps(document))
    original = product.meta_path.read_bytes()
    restored = ProductService(product.directory, include_examples=False)
    catalog = restored.catalog()
    assert catalog["failures"], "malformed metadata must be surfaced as a load problem"
    assert restored.get(ident).spec.id == ident
    assert product.meta_path.read_bytes() == original


def test_read_only_recorded_example_has_no_write_handle_and_custom_mutations_are_rejected(tmp_path, monkeypatch):
    import kalends.experience_os.product as module
    source = ExperienceCompilerV1().load(SPEC_DIR / "shared_observatory.json").to_dict()
    source.update(id="recorded_example", title="A recorded example")
    path = tmp_path / "reference/results/experience_os/life_v1/commons/accepted_journal.json"
    runtime = ExperienceRuntime(source, journal_path=path)
    runtime.save()
    before = path.read_bytes()
    monkeypatch.setattr(module, "ROOT", tmp_path / "reference")
    service = ProductService(tmp_path / "personal", include_examples=True)
    assert service.get("recorded_example").journal_path is None
    assert service.life("recorded_example")["life"]["read_only"]
    for action in (lambda: service.review("recorded_example", {"action": "inspect"}),
                   lambda: service.advance_product("recorded_example", 1),
                   lambda: service.intention("recorded_example", "Inspect"),
                   lambda: service.annotation("recorded_example", note="A personal note")):
        with pytest.raises(ValueError, match="read-only"):
            action()
    assert service.resume("recorded_example")["life"]["read_only"]
    assert path.read_bytes() == before and not service.get("recorded_example").commands


def test_notes_and_opt_in_local_telemetry_do_not_become_world_facts(product):
    ident = start(product)
    runtime = product.get(ident)
    before = runtime.state_hash(), runtime.journal_path.read_bytes()
    assert product.telemetry(ident, {"event": "history_opened"})["recorded"] is False
    path = product.directory / ".product/events.jsonl"
    assert not path.exists()
    product.annotation(ident, note="My interpretation, not a fact the team knows")
    assert (runtime.state_hash(), runtime.journal_path.read_bytes()) == before
    with pytest.raises(ValueError, match="Raw conversations"):
        product.telemetry(ident, {"event": "history_opened", "text": "private draft"})
    product.telemetry(ident, {"opt_in": True})
    assert product.telemetry(ident, {"event": "history_opened", "session_id": "session_1", "active_ms": 40})["recorded"]
    row = json.loads(path.read_text())
    assert row["active_ms"] == 40 and "text" not in row and "note" not in row
    assert (runtime.state_hash(), runtime.journal_path.read_bytes()) == before


@pytest.fixture
def product_http(tmp_path, monkeypatch):
    import kalends.experience_os.product as module
    from kalends.experience_os.product_server import make_product_handler
    reference = tmp_path / "reference"
    source_paths = {}
    for adapter, template in (("commons", "shared_observatory"), ("pompeii", "pompeii_life")):
        spec = ExperienceCompilerV1().load(SPEC_DIR / f"{template}.json").to_dict()
        spec.update(id=f"recorded_{adapter}", title=f"Recorded {adapter}")
        path = reference / f"results/experience_os/life_v1/{adapter}/accepted_journal.json"
        runtime = ExperienceRuntime(spec, journal_path=path)
        if adapter == "commons":
            runtime.commit("action", {"action": "inspect"})
        else:
            runtime.commit("action", {"action": "move", "location": "bakery"})
        source_paths[spec["id"]] = path
    monkeypatch.setattr(module, "ROOT", reference)
    service = ProductService(tmp_path / "personal", include_examples=True)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_product_handler(service))
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
    thread.start()

    def request(path, data=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=20)
        try:
            connection.request("GET" if data is None else "POST", path, None if data is None else json.dumps(data), {"Content-Type": "application/json", **(headers or {})})
            response = connection.getresponse()
            raw = response.read()
            value = json.loads(raw) if response.getheader("Content-Type", "").startswith("application/json") else raw
            return response.status, value
        finally:
            connection.close()

    try:
        yield service, source_paths, request
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


@pytest.mark.parametrize("path,payload,ident", [
    ("/product/api/propose", {"action": {"action": "inspect"}}, "recorded_commons"),
    ("/product/api/confirm", {"proposal_id": "unused"}, "recorded_commons"),
    ("/product/api/advance", {"minutes": 1}, "recorded_commons"),
    ("/product/api/intent", {"text": "Inspect"}, "recorded_commons"),
    ("/product/api/annotation", {"note": "Don't change this example"}, "recorded_commons"),
    ("/api/propose", {"recipient": "Sabina", "choice_id": "buy"}, "recorded_pompeii"),
    ("/api/act", {"proposal_id": "unused", "interpretation_id": "0"}, "recorded_pompeii"),
    ("/api/move", {"location": "street"}, "recorded_pompeii"),
    ("/api/advance", {"minutes": 1}, "recorded_pompeii"),
    ("/os/propose", {"action": {"action": "inspect"}}, "recorded_commons"),
    ("/os/confirm", {"proposal_id": "unused"}, "recorded_commons"),
    ("/os/advance", {"minutes": 1}, "recorded_commons"),
])
def test_every_mutating_route_rejects_recorded_examples_before_changing_history(product_http, path, payload, ident):
    service, paths, request = product_http
    runtime = service.get(ident)
    before = runtime.state_hash(), len(runtime.commands), paths[ident].read_bytes()
    selector = {"id": ident} if path.startswith("/product/") else {"experience": ident}
    status, result = request(path, {**selector, **payload})
    assert status == 400 and "read-only" in result["error"]
    assert (runtime.state_hash(), len(runtime.commands), paths[ident].read_bytes()) == before


def test_readonly_game_state_mode_and_route_keep_the_compatibility_protocol_usable(product_http):
    service, paths, request = product_http
    runtime = service.get("recorded_pompeii")
    before = runtime.state_hash(), paths["recorded_pompeii"].read_bytes()
    assert request("/api/state?experience=recorded_pompeii")[0] == 200
    assert request("/api/mode", {"experience": "recorded_pompeii", "mode": "game"})[0] == 200
    x, y = runtime.world.positions["Player"]
    status, route = request("/api/route", {"experience": "recorded_pompeii", "x": x, "y": y, "location": runtime.world.state.agent_locations["Player"]})
    assert status == 200 and route["points"]
    assert (runtime.state_hash(), paths["recorded_pompeii"].read_bytes()) == before


@pytest.mark.parametrize("path", ["/product/api/fork", "/os/fork"])
def test_public_alternative_routes_preserve_example_and_exclude_private_aggregate_metrics(product_http, path):
    service, paths, request = product_http
    runtime = service.get("recorded_commons")
    before = runtime.state_hash(), paths["recorded_commons"].read_bytes()
    selector = {"id": "recorded_commons"} if path.startswith("/product/") else {"experience": "recorded_commons"}
    status, alternative = request(path, {**selector, "command_index": 0})
    assert status == 200
    private_keys = {"credits_spent", "information_shared", "credit_total", "initial_credit_total"}
    assert not private_keys & set(alternative["differences"])
    for name in ("original", "alternative"):
        assert "lab" not in alternative[name]
        assert not private_keys & set(alternative[name]["metrics"])
    assert (runtime.state_hash(), paths["recorded_commons"].read_bytes()) == before


@pytest.mark.parametrize("path", ["/product/api/reflect?id=recorded_commons", "/os/debrief?experience=recorded_commons"])
def test_all_participant_reflection_routes_use_personal_spending(product_http, path):
    service, paths, request = product_http
    status, reflected = request(path)
    assert status == 200
    debrief = reflected.get("debrief", reflected)
    assert debrief["outcomes"] == service.participant_metrics(service.get("recorded_commons"))


@pytest.mark.parametrize("path", ["/os/state", "/os/spec", "/os/trace"])
@pytest.mark.parametrize("mode_query", ["mode=lab", "mode=lab&mode=other", "mode=lab&mode=lab"])
def test_duplicate_lab_query_cannot_bypass_saved_exposure_acknowledgement(product_http, path, mode_query):
    service, paths, request = product_http
    status, result = request(f"{path}?experience=recorded_commons&id=3&{mode_query}")
    assert status == 400 and "acknowledge" in result["error"].lower()
    assert not service.metadata["recorded_commons"]["operator_exposed"]


def test_legacy_draft_assistance_requires_the_same_operator_exposure_acknowledgement(product_http):
    service, paths, request = product_http
    body = {"experience": "recorded_commons", "task": "draft_spec", "prompt": "A finite observatory", "mode": "lab"}
    status, result = request("/os/assist", body)
    assert status == 400 and "acknowledge" in result["error"].lower()
    status, result = request("/product/api/lab", {"id": "recorded_commons", "acknowledged": True})
    assert status == 200 and result["operator_exposed"]
    assert request("/os/assist", body)[0] == 200
    restored = ProductService(service.directory, include_examples=True)
    assert restored.metadata["recorded_commons"]["operator_exposed"]


def test_legacy_compile_cannot_save_a_new_journal_when_metadata_is_known_incompatible(product_http):
    service, paths, request = product_http
    service.failures["product_metadata"] = {"error": "incompatible"}
    source = service.templates["shared_observatory"].to_dict()
    source["id"] = "blocked_authored"
    before = set(service.worlds)
    status, result = request("/os/compile", {"spec": source})
    assert status == 400 and "incompatible" in result["error"]
    assert set(service.worlds) == before
    assert not (service.directory / "blocked_authored.json").exists()


def test_product_http_retains_loopback_host_and_origin_guards(product_http):
    service, paths, request = product_http
    before = set(service.worlds)
    status, _ = request("/product/api/start", {"template_id": "shared_observatory"}, headers={"Origin": "https://untrusted.example"})
    assert status == 400 and set(service.worlds) == before
    assert request("/product/api/catalog", headers={"Host": "untrusted.example"})[0] == 400


@pytest.mark.parametrize("template", ["shared_observatory", "pompeii_life"])
@pytest.mark.parametrize("days", [1, 30, 90])
def test_studio_offered_horizons_validate_create_and_replay_without_changing_templates(product_http, template, days):
    service, paths, request = product_http
    original = service.templates[template].to_dict()
    payload = {"template_id": template, "title": "A finite authored life", "seed": 123, "horizon_days": days}
    before = set(service.worlds)
    status, result = request("/product/api/studio/validate", payload)
    assert status == 200, result
    assert result["valid"] is True and set(service.worlds) == before
    status, created = request("/product/api/studio/compile", payload)
    assert status == 200, created
    runtime = service.get(created["life"]["id"])
    assert runtime.spec.horizon_minutes == runtime.spec.termination["at"] == days * 1440
    assert all(row["at"] < runtime.spec.termination["at"] for row in runtime.spec.opportunities)
    rules = runtime.spec.setting["rules"]
    if template == "pompeii_life":
        assert rules["horizon_days"] == days
    else:
        assert rules["rounds"] == days
    assert service.templates[template].to_dict() == original
    restored = ProductService(service.directory, include_examples=False)
    assert restored.get(runtime.spec.id).spec.to_dict() == runtime.spec.to_dict()
    assert restored.get(runtime.spec.id).state_hash() == runtime.state_hash()


@pytest.mark.parametrize("error_type", [OSError, ValueError])
def test_http_confirm_metadata_failure_is_an_accepted_receipt_not_a_false_failed_charge(product_http, monkeypatch, error_type):
    service, paths, request = product_http
    ident = start(service)
    runtime = service.get(ident)
    proposal = service.review(ident, {"action": "inspect"})
    with monkeypatch.context() as patch:
        patch.setattr(service, "_persist_meta", lambda *args: (_ for _ in ()).throw(error_type("injected display save failure")))
        status, result = request("/product/api/confirm", {"id": ident, "proposal_id": proposal["proposal_id"]})
    assert status == 200 and result["receipt"] and result["metadata_warning"], result
    assert result["life"]["save_status"] == "saved" and result["life"]["metadata_warning"]
    assert result["snapshot"]["credits"] == 11 and len(runtime.commands) == 1
    read_status, reloaded = request(f"/product/api/life?id={ident}")
    assert read_status == 200 and reloaded["life"]["metadata_warning"]
    # A retry of the same accepted review cannot create another debit.
    assert request("/product/api/confirm", {"id": ident, "proposal_id": proposal["proposal_id"]})[0] == 400
    assert runtime.world.economy.cash["Player"] == 11 and len(runtime.commands) == 1
    restored = ProductService(service.directory, include_examples=False)
    assert restored.get(ident).state_hash() == runtime.state_hash()
    # A later accepted save can repair the display metadata and clears the
    # warning without changing the already accepted inspection charge.
    advance_status, advanced = request("/product/api/advance", {"id": ident, "minutes": 1})
    assert advance_status == 200 and advanced["life"]["metadata_warning"] is None
    assert request(f"/product/api/life?id={ident}")[1]["life"]["metadata_warning"] is None
    assert runtime.world.economy.cash["Player"] == 11 and len(runtime.commands) == 2


def test_usage_meaningful_status_comes_only_from_accepted_non_navigation_commands(product):
    ident = start(product)
    runtime = product.get(ident)
    assert product.life(ident)["telemetry"]["meaningful_revision"] == 0
    runtime.commit("advance", {"minutes": 1})
    runtime.commit("action", {"action": "wait"})
    assert product.life(ident)["telemetry"]["meaningful_revision"] == 0
    proposal = product.review(ident, {"action": "inspect"})
    assert product.life(ident)["telemetry"]["meaningful_revision"] == 0
    accepted = product.confirm_review(ident, proposal["proposal_id"])
    assert accepted["telemetry"]["meaningful_revision"] == 3
    assert accepted["telemetry"]["meaningful_kind"] == "inspect"
    product.advance_product(ident, 1)
    assert product.life(ident)["telemetry"]["meaningful_revision"] == 3


def test_usage_partition_exact_choice_and_operator_identity_are_validated_without_world_mutation(product):
    from kalends.experience_os.product import BUILD
    ident = start(product)
    runtime = product.get(ident)
    proposal = product.review(ident, {"action": "inspect"})
    product.confirm_review(ident, proposal["proposal_id"])
    product.advance_product(ident, 1)
    before = runtime.state_hash(), runtime.journal_path.read_bytes()
    product.telemetry(ident, {"opt_in": True})
    product.expose_lab(ident, True)
    assert product.telemetry(ident, {"event": "meaningful_action", "session_id": "test_session",
        "accepted_revision": 1, "first_meaningful": True, "active_ms": 30000,
        "foreground_ms": 45000, "visible_ms": 50000, "idle_ms": 15000, "elapsed_ms": 70000})["recorded"]
    row = json.loads((product.directory / ".product/events.jsonl").read_text())
    assert row == {"schema": "kalends-usage-v2", "build": BUILD, "life_id": ident, "session_id": "test_session",
                   "world_minute": runtime.minute, "event": "meaningful_action", "at": row["at"],
                   "operator_exposed": True, "accepted_revision": 1, "meaningful_kind": "inspect",
                   "first_meaningful": True, "active_ms": 30000, "foreground_ms": 45000,
                   "visible_ms": 50000, "idle_ms": 15000, "elapsed_ms": 70000}
    assert (runtime.state_hash(), runtime.journal_path.read_bytes()) == before
    assert "fragile" not in json.dumps(row)


@pytest.mark.parametrize("patch", [
    {"text": "PRIVATE"}, {"note": "PRIVATE"}, {"key": "PRIVATE"}, {"x": 812},
    {"build": "spoofed"}, {"operator_exposed": False}, {"reason": "PRIVATE ERROR"},
    {"event": "PRIVATE EVENT"}, {"active_ms": True}, {"visible_ms": -1},
    {"elapsed_ms": 3600001}, {"foreground_ms": 2, "active_ms": 3},
    {"foreground_ms": 10, "active_ms": 3, "idle_ms": 8},
    {"foreground_ms": 10, "visible_ms": 9}, {"session_id": "PRIVATE SESSION WITH SPACES"},
    {"accepted_revision": 1}, {"first_meaningful": False},
])
def test_usage_rejects_free_text_spoofed_identity_invalid_time_and_misplaced_markers(product, patch):
    ident = start(product)
    product.telemetry(ident, {"opt_in": True})
    with pytest.raises(ValueError):
        product.telemetry(ident, {"event": "active_interval", **patch})
    assert not (product.directory / ".product/events.jsonl").exists()


@pytest.mark.parametrize("revision", [0, -1, True, 1, 2, 3, 4])
def test_usage_cannot_call_navigation_waiting_unaccepted_or_boolean_revision_meaningful(product, revision):
    ident = start(product, "pompeii_life")
    runtime = product.get(ident)
    runtime.commit("action", {"action": "move", "location": "street"})
    runtime.commit("action", {"action": "wait"})
    runtime.commit("advance", {"minutes": 1})
    product.telemetry(ident, {"opt_in": True})
    with pytest.raises(ValueError):
        product.telemetry(ident, {"event": "meaningful_action", "accepted_revision": revision, "first_meaningful": True})
    assert not (product.directory / ".product/events.jsonl").exists()


def test_invalid_usage_cannot_implicitly_enable_collection_and_opt_out_is_durable(product):
    ident = start(product)
    with pytest.raises(ValueError):
        product.telemetry(ident, {"opt_in": True, "event": "history_opened", "text": "PRIVATE"})
    assert product.life(ident)["telemetry"]["opt_in"] is False
    product.telemetry(ident, {"opt_in": True})
    product.telemetry(ident, {"event": "life_entered", "reason": "new"})
    path = product.directory / ".product/events.jsonl"
    original = path.read_bytes()
    product.telemetry(ident, {"opt_in": False})
    assert product.telemetry(ident, {"event": "active_interval"})["recorded"] is False
    assert path.read_bytes() == original
    restored = ProductService(product.directory, include_examples=False)
    assert restored.life(ident)["telemetry"]["opt_in"] is False


def test_http_scene_acceptance_attaches_exact_meaningful_revision_and_never_movement(product_http):
    service, _, request = product_http
    ident = start(service, "pompeii_life")
    runtime = service.get(ident)
    suffix = "?experience=" + ident
    marcus = runtime.world.positions["Marcus"]
    status, moved = request("/api/move" + suffix, {"x": marcus[0], "y": marcus[1], "location": "street"})
    assert status == 200 and "accepted_revision" not in moved
    status, proposal = request("/api/propose" + suffix, {"recipient": "Marcus", "choice_id": "buy"})
    assert status == 200 and "accepted_revision" not in proposal
    status, accepted = request("/api/act" + suffix, {"proposal_id": proposal["proposal_id"], "interpretation_id": "0"})
    assert status == 200 and accepted["accepted_revision"] == 2
    assert runtime.commands[accepted["accepted_revision"] - 1]["data"]["action"] == "buy"
    # A later local command cannot relabel the exact revision from that response.
    status, advanced = request("/api/advance" + suffix, {"minutes": 1})
    assert status == 200 and "accepted_revision" not in advanced
    assert accepted["accepted_revision"] == 2
    status, life = request("/product/api/life?id=" + ident)
    assert status == 200 and life["telemetry"]["meaningful_revision"] == 2
    assert life["telemetry"]["meaningful_kind"] == "buy"


def test_http_optional_usage_write_failure_does_not_mark_saved_world_as_failed(product_http):
    service, _, request = product_http
    ident = start(service)
    runtime = service.get(ident)
    before = runtime.state_hash(), runtime.journal_path.read_bytes()
    assert request("/product/api/telemetry", {"id": ident, "opt_in": True})[0] == 200
    path = service.directory / ".product/events.jsonl"
    path.mkdir()
    status, failed = request("/product/api/telemetry", {"id": ident, "event": "history_opened"})
    assert status == 400 and failed["code"] == "telemetry_save_failed"
    assert failed["save_failed"] is False
    assert "World choices are unaffected" in failed["error"]
    assert service.life(ident)["life"]["save_status"] == "saved"
    assert (runtime.state_hash(), runtime.journal_path.read_bytes()) == before
