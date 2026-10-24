"""Real loopback HTTP, information-cost, persistence and 3D bridge integration."""
import copy
import http.client
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import threading

import pytest

from kalends.experience_os.compiler import SPEC_DIR
from kalends.experience_os.runtime import ExperienceRuntime
from kalends.experience_os.server import ExperienceService, make_handler


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def http_service(tmp_path):
    service = ExperienceService(tmp_path / "lives")
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(service))
    thread = threading.Thread(target=lambda: server.serve_forever(poll_interval=.01), daemon=True)
    thread.start()

    def request(path, data=None, *, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=20)
        body = None if data is None else json.dumps(data)
        request_headers = {"Content-Type": "application/json", **(headers or {})}
        try:
            connection.request("GET" if data is None else "POST", path, body, request_headers)
            response = connection.getresponse()
            raw = response.read()
            value = json.loads(raw) if response.getheader("Content-Type", "").startswith("application/json") else raw
            return response.status, dict(response.getheaders()), value
        finally:
            connection.close()

    try:
        yield service, server, request
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()


def test_inspection_preview_cannot_reveal_the_result_before_payment_and_confirmation(http_service):
    service, server, request = http_service
    life = service.get("shared_observatory")
    before = life.state_hash(), len(life.commands), life.world.economy.cash["Player"]
    status, _, proposal = request("/os/propose", {"action": {"action": "inspect"}})
    assert status == 200
    assert "fragile" not in json.dumps(proposal).lower(), "A paid private inspection cannot be disclosed by an uncommitted trial"
    assert (life.state_hash(), len(life.commands), life.world.economy.cash["Player"]) == before
    status, _, accepted = request("/os/confirm", {"proposal_id": proposal["proposal_id"]})
    assert status == 200 and accepted["receipt"]["payload"]["value"] == "fragile"
    assert accepted["state"]["own_reports"]
    assert life.world.economy.cash["Player"] == before[2] - 1
    unchanged = life.state_hash(), len(life.commands)
    assert request("/os/confirm", {"proposal_id": proposal["proposal_id"]})[0] == 400
    assert (life.state_hash(), len(life.commands)) == unchanged


def test_public_state_and_spec_do_not_disclose_private_author_records_or_assessment_answers(http_service):
    service, server, request = http_service
    status, _, public = request("/os/state")
    assert status == 200 and "lab" not in public and public["own_reports"] == []
    status, _, spec = request("/os/spec")
    if status == 200:
        text = json.dumps(spec)
        assert "initial_condition" not in text and "maintenance_log" not in text
        assert '"answer"' not in text and '"rationale"' not in text
    else:
        assert status in (400, 403)
    status, _, author = request("/os/spec?mode=lab")
    assert status == 200 and author["setting"]["rules"]["initial_condition"] == "fragile"
    status, _, lab = request("/os/state?mode=lab")
    assert status == 200 and lab["lab"]["truth"]["state"]["facts"]["observatory.condition"] == "fragile"
    debrief = request("/os/debrief")[2]
    assert "answer" not in debrief["transfer"] and "rationale" not in debrief["transfer"]
    grade = request("/os/assessment", {"choice": 1})
    assert grade[0] == 200 and grade[2]["correct"] and "not evidence" in grade[2]["scope"]


def test_private_trace_rejected_until_disclosure_and_lab_explicitly_authorized(http_service):
    service, server, request = http_service
    life = service.get("shared_observatory")
    hidden = next(e for e in life.world.ledger.events if e.payload.get("category") == "condition" and e.actors == ("team_b",))
    assert request(f"/os/trace?id={hidden.event_id}")[0] == 400
    assert request(f"/os/trace?id={hidden.event_id}&mode=lab")[0] == 200
    before = life.state_hash()
    assert request("/os/propose", {"action": {"action": "share", "recipient": "team_a", "event_id": hidden.event_id}})[0] == 400
    assert life.state_hash() == before


def test_proposals_are_world_specific_fresh_and_confirm_the_saved_action(http_service):
    service, server, request = http_service
    action = {"action": "allocate", "allocation": {"team_a": 4, "team_b": 4, "team_c": 0}}
    proposed = request("/os/propose", {"action": action})[2]
    assert request("/os/confirm", {"experience": "pompeii_life", "proposal_id": proposed["proposal_id"]})[0] == 400
    assert request("/os/advance", {"minutes": 1})[0] == 200
    assert request("/os/confirm", {"proposal_id": proposed["proposal_id"]})[0] == 400
    proposal = request("/os/propose", {"action": action})[2]
    tampered = copy.deepcopy(action)
    tampered["allocation"]["team_c"] = 12
    status, _, accepted = request("/os/confirm", {"proposal_id": proposal["proposal_id"], "action": tampered})
    assert status == 200
    life = service.get("shared_observatory")
    assert life.world.get("allocation:0") == action["allocation"]
    assert life.commands[-1]["data"] == action


def test_move_endpoint_cannot_override_its_action_to_bypass_review(http_service):
    service, server, request = http_service
    life = service.get("pompeii_life")
    before = life.state_hash(), len(life.commands), life.world.economy.cash["Player"]
    status, _, rejected = request("/api/move", {"action": "support_market", "recipient": "Sabina"})
    assert status == 400
    assert (life.state_hash(), len(life.commands), life.world.economy.cash["Player"]) == before


def test_compilation_and_cross_origin_rejections_preserve_existing_lives(http_service):
    service, server, request = http_service
    life = service.get("shared_observatory")
    before = life.state_hash(), len(service.worlds)
    spec = json.loads((SPEC_DIR / "shared_observatory.json").read_text())
    spec["setting"]["rules"]["capacity"] = 11
    spec["institutions"][0]["capacity"] = 11
    assert request("/os/compile", {"spec": spec})[0] == 400
    assert request("/os/advance", {"minutes": 1}, headers={"Origin": "https://untrusted.example"})[0] in (400, 403)
    assert request("/os/state", headers={"Host": "untrusted.example"})[0] in (400, 403)
    assert request("/os/advance", {"minutes": True})[0] == 400
    assert (life.state_hash(), len(service.worlds)) == before


def test_http_save_failure_does_not_accept_or_consume_a_reviewed_choice(http_service, monkeypatch):
    service, server, request = http_service
    life = service.get("shared_observatory")
    life.save()
    saved, before = life.journal_path.read_bytes(), life.state_hash()
    token = request("/os/propose", {"action": {"action": "inspect"}})[2]["proposal_id"]
    original = ExperienceRuntime.save

    def fail(self):
        raise OSError("injected persistence failure")

    monkeypatch.setattr(ExperienceRuntime, "save", fail)
    assert request("/os/confirm", {"proposal_id": token})[0] in (400, 500)
    assert life.state_hash() == before and life.journal_path.read_bytes() == saved
    assert token in service.proposals
    monkeypatch.setattr(ExperienceRuntime, "save", original)
    assert request("/os/confirm", {"proposal_id": token})[0] == 200


def test_shipped_3d_bridge_roundtrip_uses_the_compiled_pompeii_life_and_resumes_exactly(http_service):
    node = shutil.which("node")
    if not node:
        pytest.skip("Optional existing PlayCanvas bridge integration requires Node")
    service, server, request = http_service
    script = r'''
import assert from 'node:assert/strict';
import {KalendsBridge} from './kalends_3d/bridge.js';
const bridge=new KalendsBridge({base:process.argv[1]});
await bridge.state();
assert.equal(bridge.snapshot.mode,'game');
const marcus=bridge.world.agents.find(a=>a.id==='Marcus');
const route=await bridge.route({x:marcus.x,y:marcus.y,location:'street'});
for(const point of route.points.slice(1))await bridge.move({x:point.x,y:point.y,location:point.location});
const before={cash:bridge.world.player.cash,inventory:bridge.world.player.inventory,minute:bridge.world.minute};
const context=await bridge.context('Marcus');assert.ok(context.choices.some(c=>c.id==='buy'&&c.enabled));
const reviewed=await bridge.propose('Marcus',{choice_id:'buy'});
const confirmed=await bridge.confirm(reviewed.proposal_id);
assert.equal(confirmed.world.player.inventory,before.inventory+1);
assert.ok(confirmed.world.player.cash<before.cash);
await assert.rejects(bridge.confirm(reviewed.proposal_id));
await bridge.advance(30);
assert.equal(bridge.world.minute,before.minute+30);
assert.equal(JSON.stringify(bridge.snapshot).includes('"operator"'),false);
assert.equal(bridge.snapshot.language.external_calls,0);
console.log(JSON.stringify({minute:bridge.world.minute,cash:bridge.world.player.cash,inventory:bridge.world.player.inventory}));
'''
    result = subprocess.run([node, "--input-type=module", "-e", script, f"http://127.0.0.1:{server.server_port}"],
                            cwd=ROOT, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    actual = json.loads(result.stdout.strip().splitlines()[-1])
    life = service.get("pompeii_life")
    assert actual == {"minute": life.minute, "cash": life.world.economy.cash["Player"], "inventory": life.world.economy.inventory["Player"]}
    buys = [c for c in life.commands if c["operation"] == "action" and c["data"].get("action") == "buy"]
    assert len(buys) == 1
    saved = life.journal_path.read_bytes()
    restored = ExperienceRuntime(life.spec, journal_path=life.journal_path)
    assert restored.state_hash() == life.state_hash() and life.journal_path.read_bytes() == saved
    public = request("/api/state")[2]
    assert public["world"]["minute"] == life.snapshot()["world"]["minute"]


def test_authored_compiled_life_persists_its_spec_and_restarts_without_a_new_source_file(http_service):
    service, server, request = http_service
    spec = json.loads((SPEC_DIR / "shared_observatory.json").read_text())
    spec.update(id="authored_instrument", title="Nine-slot independent research consortium")
    rules = spec["setting"]["rules"]
    rules.update(seed=7771, capacity=9, quota=3)
    spec["institutions"][0]["capacity"] = 9
    for goal in spec["goals"]:
        goal["target"]["quantity"] = 3
    before_specs = set(SPEC_DIR.glob("*.json"))
    status, _, compiled = request("/os/compile", {"spec": spec})
    assert status == 200 and compiled["experience"] == spec["id"]
    life = service.get(spec["id"])
    assert life.journal_path.exists() and json.loads(life.journal_path.read_text())["spec"] == spec
    assert json.loads(life.journal_path.read_text())["commands"] == []
    action = {"action": "allocate", "allocation": {"team_a": 3, "team_b": 3, "team_c": 0}}
    reviewed = request("/os/propose", {"experience": spec["id"], "action": action})
    assert reviewed[0] == 200
    assert request("/os/confirm", {"experience": spec["id"], "proposal_id": reviewed[2]["proposal_id"]})[0] == 200
    assert request("/os/advance", {"experience": spec["id"], "minutes": 1440})[0] == 200
    before_hash, before_bytes = life.state_hash(), life.journal_path.read_bytes()
    restored_service = ExperienceService(service.directory)
    restored = restored_service.get(spec["id"])
    assert restored.spec.to_dict() == spec and restored.state_hash() == before_hash
    assert restored.commands == life.commands and restored.minute == 1440
    assert restored.metrics()["executed_units"] == 6
    assert life.journal_path.read_bytes() == before_bytes
    assert set(SPEC_DIR.glob("*.json")) == before_specs


def test_service_rejects_misnamed_authored_journal_without_resetting_it(tmp_path):
    directory = tmp_path / "lives"
    service = ExperienceService(directory)
    spec = json.loads((SPEC_DIR / "shared_observatory.json").read_text())
    spec["id"] = "authored_identity"
    life = service.add(spec)
    path = directory / "different_identity.json"
    life.journal_path.rename(path)
    saved = path.read_bytes()
    with pytest.raises(ValueError, match="filename|identity"):
        ExperienceService(directory)
    assert path.read_bytes() == saved
    assert not life.journal_path.exists()


def test_authored_pompeii_api_selects_its_own_life_facade_review_and_save(http_service):
    service, server, request = http_service
    spec = json.loads((SPEC_DIR / "pompeii_life.json").read_text())
    spec.update(id="second_pompeii", title="A separate authored Pompeii life")
    spec["setting"]["rules"]["seed"] = 1117
    assert request("/os/compile", {"spec": spec})[0] == 200
    default, authored = service.get("pompeii_life"), service.get(spec["id"])
    original_default = default.state_hash()
    suffix = "?experience=" + spec["id"]
    assert request("/api/advance" + suffix, {"minutes": 11})[0] == 200
    assert request("/api/state" + suffix)[2]["world"]["minute"] == 11
    assert request("/api/state")[2]["world"]["minute"] == 0
    assert default.state_hash() == original_default and not default.commands
    # A body selector is supported as well as the iframe's query selector.
    assert request("/api/advance", {"experience": spec["id"], "minutes": 2})[0] == 200
    assert authored.minute == 13 and default.minute == 0
    marcus = authored.world.positions["Marcus"]
    assert request("/api/move" + suffix, {"x": marcus[0], "y": marcus[1], "location": "street"})[0] == 200
    assert request("/api/context" + suffix + "&recipient=Marcus")[0] == 200
    status, _, proposal = request("/api/propose" + suffix, {"recipient": "Marcus", "choice_id": "buy"})
    assert status == 200
    token = {"proposal_id": proposal["proposal_id"], "interpretation_id": "0"}
    assert request("/api/act", token)[0] == 400, "Another life has no such reviewed action"
    before = authored.world.economy.inventory["Player"]
    assert request("/api/act" + suffix, token)[0] == 200
    assert authored.world.economy.inventory["Player"] == before + 1
    retry_status, _, retry = request("/api/act" + suffix, token)
    assert retry_status == 200 and retry["outcome"] == "already_accepted"
    assert authored.world.economy.inventory["Player"] == before + 1
    assert service.game(spec["id"]).runtime is authored
    assert service.game().runtime is default
    assert service.game(spec["id"]) is not service.game()
    assert default.state_hash() == original_default and not default.commands
    # Review freshness belongs to the selected life, including an empty minute.
    status, _, stale = request("/api/propose" + suffix, {"recipient": "Marcus", "choice_id": "buy"})
    assert status == 200
    assert request("/api/advance" + suffix, {"minutes": 1})[0] == 200
    assert request("/api/act" + suffix, {"proposal_id": stale["proposal_id"], "interpretation_id": "0"})[0] == 400
    assert request("/api/state?experience=shared_observatory")[0] == 400
    assert request("/api/advance?experience=shared_observatory", {"minutes": 1})[0] == 400
    assert service.get("shared_observatory").minute == 0
    saved = authored.journal_path.read_bytes()
    restored = ExperienceRuntime(authored.spec, journal_path=authored.journal_path)
    assert restored.state_hash() == authored.state_hash() and authored.journal_path.read_bytes() == saved


def test_immersion_injects_external_host_before_bundle_preserves_selector_and_source(http_service, tmp_path, monkeypatch):
    import kalends.experience_os.server as module
    service, server, request = http_service
    root = tmp_path / "retained_repository"
    dist = root / "kalends_3d/dist"
    dist.mkdir(parents=True)
    original = b'<!doctype html><html><head><script type="module" src="/immersion/assets/original.js"></script></head><body>Retained 3D</body></html>'
    (dist / "index.html").write_bytes(original)
    monkeypatch.setattr(module, "ROOT", root)
    status, headers, body = request("/immersion?experience=authored_pompeii")
    assert status == 302 and headers["Location"] == "/immersion/?experience=authored_pompeii"
    for path in ("/immersion/?experience=authored_pompeii", "/immersion/index.html?experience=authored_pompeii"):
        status, headers, body = request(path)
        assert status == 200 and headers["Content-Type"].startswith("text/html")
        assert body.count(b'<script src="/game-host.js"></script>') == 1
        assert body.index(b'/game-host.js') < body.index(b'type="module"')
        assert b'connect-src \'self\'' in headers["Content-Security-Policy"].encode()
    assert (dist / "index.html").read_bytes() == original
