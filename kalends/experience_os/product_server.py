"""Human-facing local routes, reusing the authoritative Experience OS service."""
from __future__ import annotations

import argparse
import fcntl
from http.server import ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
import re
from urllib.parse import parse_qs, unquote, urlparse

from .compiler import ExperienceCompilerV1
from .product import ProductService, TEMPLATES
from .server import ROOT, STATIC, make_handler

ARTIFACTS = {
    "cognition": ROOT / "docs/experience_os/RESEARCH_RESULTS.md",
    "lives": ROOT / "results/experience_os/life_v1/REPORT.md",
    "next-phase": ROOT / "docs/next_phase/RESEARCH_REPORT.md",
    "assets": ROOT / "kalends_3d/ASSET_PROVENANCE.json",
}


def make_product_handler(service):
    base = make_handler(service)

    class Handler(base):
        def do_GET(self):
            try:
                self.safe()
                url = urlparse(self.path)
                path, query = unquote(url.path), parse_qs(url.query)
                ident = query.get("id", [None])[0]
                if path.startswith("/product/api/"):
                    with service.lock:
                        if path == "/product/api/catalog": result = service.catalog()
                        elif path == "/product/api/research": result = service.research()
                        elif path == "/product/api/life": result = service.life(ident)
                        elif path == "/product/api/history": result = service.life(ident)["history"]
                        elif path == "/product/api/reflect": result = service.reflect(ident)
                        elif path == "/product/api/trace": result = service.get(ident).trace(int(query.get("event_id", ["-1"])[0]))
                        else: return self.send(404, {"error": "Unknown product operation"})
                        return self.send(200, result)
                # Operator entry must durably acknowledge exposure even when a
                # visitor follows a retained research URL rather than the UI.
                if path in ("/os/state", "/os/spec", "/os/trace") and query.get("mode", [""])[0] == "lab":
                    life_id = query.get("experience", ["shared_observatory"])[0]
                    if not service.metadata.get(life_id, {}).get("operator_exposed"):
                        raise ValueError("Enter Research tools for this life and acknowledge private-information exposure first")
                if path == "/os/debrief" or path == "/os/state" and query.get("mode", [""])[0] != "lab":
                    life_id = query.get("experience", ["shared_observatory"])[0]
                    return self.send(200, service.public_snapshot(service.get(life_id)) if path.endswith("state") else service.reflect(life_id)["debrief"])
                if path.startswith("/research/artifacts/"):
                    resource = ARTIFACTS.get(path.rsplit("/", 1)[-1])
                    if not resource or not resource.is_file():
                        return self.send(404, {"error": "This research artifact is not available yet"})
                    return self.send(200, resource.read_bytes(), "text/plain")
                if path.startswith("/product/"):
                    directory = STATIC / "product"
                    resource = (directory / path[len("/product/"):]).resolve()
                    if not resource.is_relative_to(directory.resolve()) or not resource.is_file() or resource.suffix not in {".html", ".js", ".css", ".png", ".jpg", ".webp", ".svg"}:
                        return self.send(404, {"error": "Unknown product resource"})
                    return self.send(200, resource.read_bytes(), mimetypes.guess_type(resource)[0] or "application/octet-stream")
                if path in {"/", "/worlds", "/your-worlds", "/research", "/studio", "/about", "/accessibility", "/data", "/data-and-saves", "/acknowledgements"} or re.fullmatch(r"/(?:worlds/[A-Za-z0-9_-]+|lives/[A-Za-z0-9_-]+(?:/(?:history|reflect))?|lab/[A-Za-z0-9_-]+)", path):
                    return self.send(200, (STATIC / "product/index.html").read_bytes(), "text/html")
                if path in {"/legacy", "/legacy/"}:
                    return self.send(200, (STATIC / "index.html").read_bytes(), "text/html")
                # Compatibility GETs preserve the existing 3D renderer and its
                # participant context protocol. No second simulation is loaded.
                return super().do_GET()
            except (ValueError, TypeError, KeyError, OSError) as error:
                return self.send(400, {"error": str(error)[:500]})

        def do_POST(self):
            ident = None
            try:
                self.safe()
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 262144:
                    raise ValueError("Request is empty or too large")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("Request must be an object")
                url = urlparse(self.path)
                path, query = url.path, parse_qs(url.query)
                with service.lock:
                    if path.startswith("/product/api/"):
                        ident = data.get("id")
                        if path == "/product/api/start": result = service.start(data.get("template_id"))
                        elif path == "/product/api/resume": result = service.resume(ident)
                        elif path == "/product/api/propose": result = service.review(ident, data.get("action"))
                        elif path == "/product/api/confirm": result = service.confirm_review(ident, data.get("proposal_id"))
                        elif path == "/product/api/advance": result = service.advance_product(ident, data.get("minutes"), mode=data.get("mode", "compress"), protect_known=data.get("protect_known", True))
                        elif path == "/product/api/seen": result = service.seen(ident, data.get("revision"))
                        elif path == "/product/api/lab": result = service.expose_lab(ident, data.get("acknowledged"))
                        elif path == "/product/api/intent": result = service.intention(ident, data.get("text"), data.get("recipient", "team_b"))
                        elif path == "/product/api/annotation": result = service.annotation(ident, note=data.get("note"), event_id=data.get("event_id"))
                        elif path == "/product/api/telemetry": result = service.telemetry(ident, data)
                        elif path == "/product/api/fork":
                            result = service.public_fork(ident, data.get("command_index"))
                        elif path == "/product/api/studio/validate": result = self.studio(data, compile=False)
                        elif path == "/product/api/studio/compile": result = self.studio(data, compile=True)
                        else: return self.send(404, {"error": "Unknown product operation"})
                        return self.send(200, result)
                    # Retained game host. Mutations guard recorded examples and
                    # use the same life identity rather than a tab-global slot.
                    default = "pompeii_life" if path.startswith("/api/") else "shared_observatory"
                    ident = data.pop("experience", query.get("experience", [default])[0])
                    if path.startswith("/api/"):
                        game = service.game(ident)
                        if path == "/api/route": return self.send(200, game.route(data))
                        if path == "/api/propose":
                            service.mutable(ident)
                            return self.send(200, game.propose(data))
                        if path == "/api/mode" and data == {"mode": "game"}:
                            return self.send(200, game.state())
                        service.mutable(ident)
                        before = len(game.runtime.commands)
                        if path == "/api/act": result = game.act(data)
                        elif path == "/api/move":
                            if set(data) - {"x", "y", "location"}: raise ValueError("Move endpoint accepts coordinates and location only")
                            game.runtime.commit("action", {**data, "action": "move"})
                            result = game.state()
                        elif path == "/api/advance":
                            game.runtime.commit("advance", data)
                            result = game.state()
                        else: raise ValueError("Unsupported game operation")
                        if len(game.runtime.commands) != before:
                            accepted = service.accepted(ident, {})
                            if accepted.get("metadata_warning"): result["metadata_warning"] = accepted["metadata_warning"]
                        return self.send(200, result)
                    if path == "/os/validate":
                        spec = ExperienceCompilerV1().validate(data["spec"])
                        return self.send(200, {"valid": True, "id": spec.id, "adapter": spec.setting["adapter"]})
                    if path == "/os/compile":
                        # Old compiler remains finite and preserves identity;
                        # register its metadata so a saved life is resumable.
                        if "product_metadata" in service.failures: raise ValueError("Product metadata is incompatible; original preserved")
                        runtime = service.add(data["spec"])
                        service.metadata.setdefault(runtime.spec.id, service._initial_meta(runtime, started=True))
                        try: service._update_meta(runtime.spec.id, started=True)
                        except (ValueError, OSError):
                            return self.send(200, {**service.public_snapshot(runtime), "metadata_warning": "World journal saved; display metadata could not be updated."})
                        return self.send(200, service.public_snapshot(runtime))
                    runtime = service.get(ident)
                    if path == "/os/assist":
                        if data.get("task") == "draft_spec" and not service.metadata.get(ident, {}).get("operator_exposed"):
                            raise ValueError("Acknowledge private-information exposure in Research tools first")
                        return self.send(200, service.assist(ident, data))
                    if path == "/os/fork": return self.send(200, service.public_fork(ident, data["command_index"]))
                    if path == "/os/assessment":
                        transfer = runtime.spec.debrief["transfer"]
                        choice = data["choice"]
                        if type(choice) is not int or not 0 <= choice < len(transfer["options"]): raise ValueError("Invalid assessment choice")
                        return self.send(200, {"correct": choice == transfer["answer"], "rationale": transfer["rationale"], "scope": "One authored transfer question; no measured human learning."})
                    service.mutable(ident)
                    if path == "/os/propose": return self.send(200, service.review(ident, data["action"]))
                    if path == "/os/confirm": return self.send(200, service.confirm_review(ident, data["proposal_id"]))
                    if path == "/os/advance": return self.send(200, service.advance_product(ident, data.get("minutes"), mode=data.get("mode", "compress"), protect_known=False))
                    raise ValueError("Unsupported operation")
            except (ValueError, TypeError, KeyError, OSError) as error:
                if isinstance(error, OSError) and ident in service.worlds:
                    service.save_errors[ident] = "The change could not be saved. The previous accepted world is preserved. Reload its current state before deciding what to do next."
                return self.send(400, {"error": str(error)[:500], "save_failed": isinstance(error, OSError), "retry_policy": "Read the current life before reviewing again. Never automatically resubmit a choice."})

        def studio(self, data, *, compile):
            # Finite authored template editor, not unconstrained generation.
            if set(data) - {"template_id", "title", "seed", "horizon_days"}:
                raise ValueError("Studio accepts template, title, seed and horizon only")
            template_id = data.get("template_id")
            if template_id not in TEMPLATES: raise ValueError("Choose a supported template")
            title = data.get("title", "An authored Kalends life")
            if not isinstance(title, str) or not 1 <= len(title.strip()) <= 90: raise ValueError("Use a short title")
            seed, days = data.get("seed", 2718), data.get("horizon_days", 30)
            if type(seed) is not int or not 0 <= seed <= 1_000_000 or type(days) is not int or not 1 <= days <= 90:
                raise ValueError("Choose seed 0–1000000 and horizon 1–90 days")
            spec = service.templates[template_id].to_dict()
            spec["title"] = title.strip()
            spec["setting"]["rules"]["seed"] = seed
            # Keep the finite template's horizon and event schedule consistent.
            spec["horizon_minutes"] = days * 1440
            spec["termination"]["at"] = days * 1440
            spec["opportunities"] = [o for o in spec["opportunities"] if o["at"] <= days * 1440]
            spec["goals"] = [g for g in spec["goals"] if g.get("deadline", 0) <= days * 1440]
            validated = ExperienceCompilerV1().validate(spec)
            if not compile: return {"valid": True, "template_id": template_id, "title": title.strip(), "horizon_days": days, "scope": "Only the two existing adapters; private setup is not a participant observation."}
            if "product_metadata" in service.failures: raise ValueError("Product metadata is incompatible; original preserved")
            # Reuse new-life generation, then replace only this unplayed clone's
            # setup before it is ever offered to a participant.
            import secrets
            from .runtime import ExperienceRuntime
            from .product import utc
            if sum(bool(m.get("started")) and not m.get("example") for m in service.metadata.values()) >= 8: raise ValueError("This local prototype has eight personal lives")
            spec = validated.to_dict()
            spec["id"] = "authored_" + secrets.token_hex(6)
            journal = service.directory / (spec["id"] + ".json") if service.directory else None
            runtime = ExperienceRuntime(spec, journal_path=journal)
            runtime.save()
            service.worlds[runtime.spec.id] = runtime
            service.metadata[runtime.spec.id] = {**service._initial_meta(runtime, started=True), "updated_at": utc()}
            try:
                service._update_meta(runtime.spec.id, started=True)
            except (ValueError, OSError):
                return {**service.life(runtime.spec.id), "metadata_warning": "New life journal saved; display metadata could not be updated."}
            return service.life(runtime.spec.id)

    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8810)
    parser.add_argument("--directory", default=".kalends/next_phase")
    parser.add_argument("--configured-ai", action="store_true", help="Use explicitly configured existing provider and required budget; default is offline")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535: parser.error("Port must be between 1 and 65535")
    directory = Path(args.directory)
    directory.mkdir(parents=True, exist_ok=True)
    writer_lock = (directory / ".writer.lock").open("a")
    try: fcntl.flock(writer_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError: parser.error("Another writer owns this save directory. Reuse its URL or choose a separate directory; saves are preserved.")
    from kalends_rebirth.ai import Cognition
    service = ProductService(directory, cognition=Cognition.from_env() if args.configured_ai else Cognition())
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_product_handler(service))
    print(f"Kalends: http://127.0.0.1:{args.port}/ — local saves: {directory}", flush=True)
    server.serve_forever()


if __name__ == "__main__": main()
