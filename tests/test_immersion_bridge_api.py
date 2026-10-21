"""One real 3D bridge -> HTTP -> reviewed simulation -> saved journal round trip.

Native renderer/input QA is separate. No provider calls or user journal access.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import threading

import pytest

from kalends_rebirth.server import RebirthSession, make_server


ROOT = Path(__file__).resolve().parents[1]


def test_real_3d_bridge_reviewed_trade_rejection_time_and_resume(tmp_path):
    node = shutil.which("node")
    if not node:
        pytest.skip("Optional 3D client integration requires Node.js")
    journal = tmp_path / "isolated_immersion.json"
    session = RebirthSession(journal)
    server = make_server(session, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    origin = f"http://127.0.0.1:{server.server_port}"
    script = r'''
import assert from 'node:assert/strict';
import {KalendsBridge} from './kalends_3d/bridge.js';
const base=process.argv[1],bridge=new KalendsBridge({base});
await bridge.state();
const marcus=bridge.world.agents.find(a=>a.id==='Marcus');
const route=await bridge.route({x:marcus.x,y:marcus.y,location:'street'});
for(const p of route.points.slice(1))await bridge.move({x:p.x,y:p.y,location:p.location});
const context=await bridge.context('Marcus');
const choice=context.choices.find(c=>c.id==='buy'&&c.enabled);
assert.ok(choice,'Actual merchant offers a valid unit purchase');
const before={cash:bridge.world.player.cash,flour:bridge.world.player.inventory};
const proposal=await bridge.propose('Marcus',{choice_id:choice.id});
const a=bridge.confirm(proposal.proposal_id),b=bridge.confirm(proposal.proposal_id);
assert.strictEqual(a,b,'duplicate UI activation must share its pending action');
const confirmed=await a;
assert.equal(confirmed.world.player.inventory,before.flour+1);
assert.ok(confirmed.world.player.cash<before.cash);
await assert.rejects(bridge.confirm(proposal.proposal_id),/situation changed/);
const after={cash:bridge.world.player.cash,flour:bridge.world.player.inventory,minute:bridge.world.minute};
await assert.rejects(bridge.move({x:-500,y:-500}),/street|floor|point|position|outside|walkable/i);
assert.equal(bridge.world.player.cash,after.cash);
assert.equal(bridge.world.player.inventory,after.flour);
// Opening the separately runnable legacy World Lab changes the shared view.
// The next valid 3D action must still return public state without replaying it.
await fetch(base+'/api/mode',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:'lab'})});
await bridge.advance(30);
assert.equal(bridge.snapshot.mode,'game');
assert.equal(bridge.world.minute,after.minute+30);
const reloaded=new KalendsBridge({base});await reloaded.state();
assert.equal(reloaded.world.player.cash,after.cash);
assert.equal(reloaded.world.player.inventory,after.flour);
assert.equal(reloaded.world.minute,after.minute+30);
assert.equal(JSON.stringify(reloaded.snapshot).includes('"operator"'),false);
assert.equal(reloaded.snapshot.language.external_calls,0);
console.log(JSON.stringify({cash:reloaded.world.player.cash,flour:reloaded.world.player.inventory,minute:reloaded.world.minute,external_calls:reloaded.snapshot.language.external_calls}));
'''
    try:
        result = subprocess.run(
            [node, "--input-type=module", "-e", script, origin],
            cwd=ROOT, text=True, capture_output=True, timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        outcome = json.loads(result.stdout.strip().splitlines()[-1])
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()
    accepted = json.loads(journal.read_text())
    buys = [command for command in accepted["commands"] if command["operation"] == "action" and command["data"]["action"] == "buy"]
    assert len(buys) == 1
    assert buys[0]["data"]["quantity"] == 1
    before = journal.read_bytes()
    restored = RebirthSession(journal)
    assert journal.read_bytes() == before
    assert restored.original.ledger.content_hash() == accepted["ledger_hash"]
    assert restored.original.economy.cash["Player"] == outcome["cash"]
    assert restored.original.economy.inventory["Player"] == outcome["flour"]
    assert restored.original.minute == outcome["minute"]
    assert outcome["external_calls"] == 0


def test_3d_asset_mount_is_binary_correct_scoped_and_legacy_still_runs(tmp_path, monkeypatch):
    import http.client
    import kalends_rebirth.server as server_module

    root = tmp_path / "repository"
    dist = root / "kalends_3d" / "dist"
    assets = root / "kalends_3d" / "assets"
    dist.mkdir(parents=True)
    assets.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>Isolated 3D fixture</title>")
    (dist / "app.js").write_text("export const fixture = true;")
    glb = b"glTF\x02\0\0\0\x0c\0\0\0"
    (assets / "fixture.glb").write_bytes(glb)
    (assets / "fixture.gltf").write_text('{"asset":{"version":"2.0"}}')
    (assets / "manifest.json").write_text('{"asset":"fixture.glb","clips":["Idle","Walk"]}')
    (assets / "fixture.bin").write_bytes(b"\0\x80\xff")
    (assets / "ambient.wav").write_bytes(b"RIFFfixtureWAVE")
    (assets / "unapproved.py").write_text("private = True")
    secret = root / "secret.js"
    secret.write_text("private = 'must not be served';")
    (assets / "escape.js").symlink_to(secret)
    monkeypatch.setattr(server_module, "ROOT", root)
    session = RebirthSession()
    server = make_server(session, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    def request(path, *, method="GET", body=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    try:
        status, headers, body = request("/immersion")
        assert status == 302 and headers["Location"] == "/immersion/"
        assert request("/immersion/")[0] == 200
        status, headers, body = request("/immersion/app.js")
        assert status == 200 and headers["Content-Type"].startswith("application/javascript")
        for name, mime, expected in (("fixture.glb", "model/gltf-binary", glb), ("fixture.bin", "application/octet-stream", b"\0\x80\xff")):
            status, headers, body = request("/immersion-assets/" + name)
            assert status == 200 and body == expected
            assert headers["Content-Type"] == mime
            assert "charset" not in headers["Content-Type"]
            assert headers["X-Content-Type-Options"] == "nosniff"
        assert request("/immersion-assets/fixture.gltf")[1]["Content-Type"] == "model/gltf+json"
        status, headers, body = request("/immersion-assets/manifest.json")
        assert status == 200 and json.loads(body) == {"asset": "fixture.glb", "clips": ["Idle", "Walk"]}
        assert headers["Content-Type"].startswith("application/json")
        assert request("/immersion-assets/ambient.wav")[1]["Content-Type"].startswith("audio/")
        for path in ("/immersion/%2e%2e/%2e%2e/secret.js", "/immersion-assets/../bridge.js", "/immersion-assets/escape.js", "/immersion-assets/unapproved.py"):
            assert request(path)[0] == 404
        status, headers, body = request("/")
        assert status == 200 and b"Kalends" in body, "Legacy client must remain separately runnable"
        assert request("/immersion/", headers={"Host": "evil.test"})[0] == 403
        assert request("/api/move", method="POST", body='{"x":800,"y":415}', headers={"Origin": "https://evil.test", "Content-Type": "application/json"})[0] == 403
        before = session.original.ledger.content_hash()
        assert request("/api/move", method="POST", body='{"x":800,"y":415,"cash":999}', headers={"Content-Type": "application/json"})[0] == 400
        assert session.original.ledger.content_hash() == before
        assert session.original.economy.cash["Player"] == 6
    finally:
        server.shutdown()
        thread.join(timeout=3)
        server.server_close()
