"""Local LIVE / LEARN / LAB on compiled experiences and the retained 3D client."""
from __future__ import annotations

import argparse
import copy
import fcntl
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import secrets
import threading
from urllib.parse import parse_qs, unquote, urlparse

from .compiler import ExperienceCompilerV1, SPEC_DIR
from .runtime import ExperienceRuntime, ExperienceGameFacade, canonical

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).with_name("static")


class ExperienceService:
    def __init__(self, directory=None, *, cognition=None):
        from kalends_rebirth.ai import Cognition
        self.cognition = cognition or Cognition()
        self.directory = Path(directory) if directory else None
        self.lock = threading.RLock()
        self.worlds, self.proposals, self.game_facades = {}, {}, {}
        for path in sorted(SPEC_DIR.glob("*.json")):
            self.add(ExperienceCompilerV1().load(path))
        # Authored lives carry their validated specification in their own journal.
        # Refuse malformed/revision-incompatible journals rather than resetting one.
        if self.directory and self.directory.exists():
            for path in sorted(self.directory.glob("*.json")):
                document = json.loads(path.read_text())
                spec = ExperienceCompilerV1().validate(document["spec"])
                if path.name != spec.id + ".json":
                    raise ValueError("Journal filename must match its experience identity")
                self.add(spec)

    def add(self, spec):
        spec = ExperienceCompilerV1().validate(spec)
        if spec.id in self.worlds:
            if self.worlds[spec.id].spec_hash != __import__("hashlib").sha256(canonical(spec.to_dict()).encode()).hexdigest():
                raise ValueError("Existing experience identity cannot be replaced; choose a new id")
            return self.worlds[spec.id]
        if len(self.worlds) >= 8:
            raise ValueError("This local demonstration supports at most eight compiled lives")
        journal = self.directory / (spec.id + ".json") if self.directory else None
        runtime = ExperienceRuntime(spec, journal_path=journal)
        if journal and not journal.exists():
            runtime.save()
        self.worlds[spec.id] = runtime
        return runtime

    def get(self, ident):
        if ident not in self.worlds:
            raise ValueError("Unknown compiled experience")
        return self.worlds[ident]

    def game(self, ident="pompeii_life"):
        runtime = self.get(ident)
        if runtime.spec.setting["adapter"] != "pompeii":
            raise ValueError("The 3D game interface requires a compiled Pompeii experience")
        if ident not in self.game_facades:
            self.game_facades[ident] = ExperienceGameFacade(runtime, self.cognition)
        return self.game_facades[ident]

    def assist(self, ident, data):
        """Host-scoped proposals over admitted records, never caller-supplied truth."""
        from .providers import ExperienceProposals
        proposals = ExperienceProposals(self.cognition)
        task = data.get("task")
        if task == "draft_spec" and set(data) == {"task", "prompt", "mode"} and data["mode"] == "lab":
            return proposals.draft_spec(data["prompt"], [w.spec for w in list(self.worlds.values())[:4]])
        if set(data) != {"task"} or task not in ("debrief", "consolidate", "plan"):
            raise ValueError("Choose a supported assistance task; evidence is scoped by the host")
        runtime = self.get(ident)
        events = runtime.events()[-24:]
        evidence = [{"event_id": e["event_id"], "text": e["payload"].get("title", e["payload"]["category"]), "at": e["tick"],
                     "kind": "testimony" if e["etype"] == "tell" else "event"} for e in events]
        view = {"minute": runtime.minute, "evidence": evidence, "allowed_event_ids": [e["event_id"] for e in evidence]}
        if task == "debrief":
            return proposals.debrief({**view, "viewer": "Player", "objective": runtime.spec.debrief["objective"], "questions": runtime.spec.debrief["questions"]})
        if task == "consolidate":
            return proposals.consolidate({**view, "actor": "Player"})
        # Current authoritative preconditions generate offered actions. The
        # suggestion is not an accepted action and cannot bypass review later.
        options = []
        if runtime.spec.setting["adapter"] == "commons":
            candidates = [("inspect", "Buy a dated direct inspection", {"action": "inspect"}),
                          ("ask_report", "Request the systems team's retained report", {"action": "share", "recipient": "team_b"})]
            for option_id, label, action in candidates:
                trial = object.__new__(ExperienceRuntime)
                trial.__dict__ = {**runtime.__dict__, "world": copy.deepcopy(runtime.world), "journal_path": None}
                try:
                    trial._perform("action", action)
                    options.append({"id": option_id, "label": label, "evidence_ids": []})
                except ValueError:
                    pass
        return proposals.suggest_plan({**view, "actor": "Player", "options": options})

    def propose(self, ident, action):
        runtime = self.get(ident)
        trial = object.__new__(ExperienceRuntime)
        trial.__dict__ = {**runtime.__dict__, "world": copy.deepcopy(runtime.world), "commands": list(runtime.commands), "journal_path": None}
        before = runtime.metrics()
        trial._perform("action", action)
        token = secrets.token_hex(12)
        self.proposals[token] = {"id": ident, "hash": runtime.state_hash(), "action": copy.deepcopy(action)}
        if len(self.proposals) > 16:
            self.proposals.pop(next(iter(self.proposals)))
        return {"proposal_id": token, "action": action,
                "receipt": {"validated": True, "action": action["action"],
                            "notice": "New observations and private report contents are disclosed only after confirmation."},
                "before": before, "after": trial.metrics(),
                "notice": "Trial preview only. Confirmation revalidates this exact proposal against the saved world."}

    def confirm(self, ident, token):
        proposal = self.proposals.get(token)
        runtime = self.get(ident)
        if not proposal or proposal["id"] != ident or proposal["hash"] != runtime.state_hash():
            raise ValueError("The proposal is stale or already consumed. Review again.")
        result = runtime.commit("action", proposal["action"])
        self.proposals.pop(token)
        return result


def make_handler(service):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def safe(self):
            port = self.server.server_port
            if self.headers.get("Host") not in (f"127.0.0.1:{port}", f"localhost:{port}"):
                raise ValueError("This service accepts loopback hosts only")
            origin = self.headers.get("Origin")
            if origin and origin not in (f"http://127.0.0.1:{port}", f"http://localhost:{port}"):
                raise ValueError("Cross-origin mutation is not permitted")

        def send(self, status, value, mime="application/json"):
            data = value if isinstance(value, bytes) else canonical(value).encode()
            self.send_response(status)
            self.send_header("Content-Type", mime + ("; charset=utf-8" if mime.startswith("text/") or mime in ("application/json", "application/javascript") else ""))
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob:; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'")
            self.end_headers(); self.wfile.write(data)

        def do_GET(self):
            try:
                self.safe()
                url = urlparse(self.path)
                path = unquote(url.path)
                query = parse_qs(url.query)
                ident = query.get("experience", ["pompeii_life" if path.startswith("/api/") else "shared_observatory"])[0]
                lab = query.get("mode", [""])[0] == "lab"
                with service.lock:
                    if path == "/os/catalog":
                        return self.send(200, {"cognition": service.cognition.metrics, "experiences": [{"id": r.spec.id, "title": r.spec.title, "adapter": r.spec.setting["adapter"], "objective": r.spec.debrief["objective"]} for r in service.worlds.values()]})
                    if path == "/os/state": return self.send(200, service.get(ident).snapshot(operator=lab))
                    if path == "/os/spec":
                        if not lab: raise ValueError("Author specifications include private initial conditions; explicitly enter LAB")
                        return self.send(200, service.get(ident).spec.to_dict())
                    if path == "/os/debrief": return self.send(200, service.get(ident).debrief())
                    if path == "/os/trace": return self.send(200, service.get(ident).trace(int(query.get("id", ["-1"])[0]), operator=lab))
                    if path == "/api/state": return self.send(200, service.game(ident).state())
                    if path == "/api/context": return self.send(200, service.game(ident).context(query.get("recipient", [""])[0]))
                if path == "/history-rebirth":
                    return self.send(200, (ROOT / "docs/rebirth/HISTORY_NOTES.md").read_bytes(), "text/plain")
                if path == "/immersion":
                    location = "/immersion/" + ("?" + url.query if url.query else "")
                    self.send_response(302); self.send_header("Location", location); self.end_headers(); return
                mounts = [("/immersion-assets/", ROOT / "kalends_3d/assets"), ("/immersion/", ROOT / "kalends_3d/dist"),
                          ("/assets/", ROOT / "kalends_rebirth/static/assets"), ("/", STATIC)]
                for prefix, directory in mounts:
                    if not path.startswith(prefix): continue
                    relative = path[len(prefix):] or "index.html"
                    if path == "/navigation.js": directory, relative = ROOT / "kalends_rebirth/static", "navigation.js"
                    file = (directory / relative).resolve()
                    if not file.is_relative_to(directory.resolve()) or not file.is_file() or file.suffix not in (".html", ".js", ".css", ".json", ".glb", ".gltf", ".bin", ".png", ".jpg", ".webp", ".svg", ".woff2"):
                        return self.send(404, {"error": "Unknown local resource"})
                    content = file.read_bytes()
                    if prefix == "/immersion/" and relative == "index.html":
                        # The OS host selects the compiled life through this
                        # external classic script before the deferred 3D module.
                        # The retained source and production bundle stay intact.
                        script = b'<script src="/game-host.js"></script>'
                        content = content.replace(b"<head>", b"<head>" + script, 1) if b"<head>" in content else script + content
                    return self.send(200, content, {".glb": "model/gltf-binary", ".js": "application/javascript"}.get(file.suffix, mimetypes.guess_type(file)[0] or "application/octet-stream"))
            except (ValueError, TypeError, KeyError) as error:
                self.send(400, {"error": str(error)})

        def do_POST(self):
            try:
                self.safe()
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 262144: raise ValueError("Request is empty or too large")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict): raise ValueError("Request must be an object")
                url = urlparse(self.path)
                path, query = url.path, parse_qs(url.query)
                default = "pompeii_life" if path.startswith("/api/") else "shared_observatory"
                ident = data.pop("experience", query.get("experience", [default])[0])
                with service.lock:
                    if path.startswith("/api/"):
                        game = service.game(ident)
                        if path == "/api/route": return self.send(200, game.route(data))
                        if path == "/api/propose": return self.send(200, game.propose(data))
                        if path == "/api/act": return self.send(200, game.act(data))
                        if path == "/api/move":
                            if set(data) - {"x", "y", "location"}: raise ValueError("Move endpoint accepts coordinates and location only")
                            game.runtime.commit("action", {**data, "action": "move"}); return self.send(200, game.state())
                        if path == "/api/advance":
                            game.runtime.commit("advance", data); return self.send(200, game.state())
                        if path == "/api/mode" and data == {"mode": "game"}: return self.send(200, game.state())
                        raise ValueError("Unsupported game operation")
                    if path == "/os/validate":
                        spec = ExperienceCompilerV1().validate(data["spec"])
                        return self.send(200, {"valid": True, "id": spec.id, "adapter": spec.setting["adapter"]})
                    if path == "/os/compile": return self.send(200, service.add(data["spec"]).snapshot())
                    runtime = service.get(ident)
                    if path == "/os/assist": return self.send(200, service.assist(ident, data))
                    if path == "/os/propose": return self.send(200, service.propose(ident, data["action"]))
                    if path == "/os/confirm": return self.send(200, service.confirm(ident, data["proposal_id"]))
                    if path == "/os/advance": return self.send(200, runtime.commit("advance", data))
                    if path == "/os/fork": return self.send(200, runtime.fork(data["command_index"]))
                    if path == "/os/assessment":
                        transfer = runtime.spec.debrief["transfer"]
                        choice = data["choice"]
                        if type(choice) is not int or not 0 <= choice < len(transfer["options"]): raise ValueError("Invalid assessment choice")
                        return self.send(200, {"correct": choice == transfer["answer"], "rationale": transfer["rationale"], "scope": "One authored transfer question; not evidence of learning or real-world transfer."})
                    raise ValueError("Unsupported operation")
            except (ValueError, TypeError, KeyError, OSError) as error:
                self.send(400, {"error": str(error)})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8800)
    parser.add_argument("--directory", default=".kalends/experience_os")
    parser.add_argument("--configured-ai", action="store_true", help="Explicitly use the existing provider environment and its required budget; otherwise offline")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535: parser.error("Port must be between 1 and 65535")
    directory = Path(args.directory)
    directory.mkdir(parents=True, exist_ok=True)
    writer_lock = (directory / ".writer.lock").open("a")
    try:
        fcntl.flock(writer_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        parser.error("This experience directory already has a server writer. Reuse its URL or choose a separate directory.")
    from kalends_rebirth.ai import Cognition
    service = ExperienceService(directory, cognition=Cognition.from_env() if args.configured_ai else Cognition())
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(service))
    print(f"Kalends Experience OS: http://127.0.0.1:{args.port}/", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
