"""Local, offline HTTP adapter for Fork the City (stdlib only).

One lock serializes timeline mutations. A compact command journal permits
deterministic recovery after restart without pickles or executable input.
"""
from __future__ import annotations

import argparse
import copy
import json
import mimetypes
import threading
from dataclasses import asdict, fields
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


class CitySession:
    def __init__(self, journal_path=None):
        self.lock = threading.RLock()
        self.journal_path = Path(journal_path) if journal_path else None
        self.commands = []
        self.original = None
        self.branch = None
        self.reset({}, save=False)
        if self.journal_path and self.journal_path.exists():
            payload = json.loads(self.journal_path.read_text())
            if payload.get("version") != 1:
                raise ValueError("unsupported city journal version")
            for item in payload["commands"]:
                self.apply(item["operation"], item["data"], save=False)

    def reset(self, data, save=True):
        from .city import CityConfig, CitySimulation
        allowed = {f.name for f in fields(CityConfig)}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError("unknown configuration fields: " + ", ".join(sorted(unknown)))
        config = CityConfig(**data)
        self.original = CitySimulation(config)
        self.branch = None
        self.commands = [{"operation": "reset", "data": asdict(config)}]
        if save:
            self.save()

    def save(self):
        if self.journal_path:
            self.journal_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.journal_path.with_suffix(".tmp")
            temporary.write_text(json.dumps({"version": 1, "commands": self.commands}, indent=2) + "\n")
            temporary.replace(self.journal_path)

    def state(self):
        return {"original": self.original.snapshot(),
                "branch": self.branch.snapshot() if self.branch else None,
                "comparison": self.original.compare(self.branch) if self.branch else None}

    def apply(self, operation, data, save=True):
        with self.lock:
            if operation == "reset":
                self.reset(data, save=save)
                return self.state()
            if operation == "step":
                count = data.get("count", 1)
                if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 96:
                    raise ValueError("step count must be an integer from 1 to 96")
                timeline = data.get("timeline", "both")
                if timeline not in ("both", "original", "branch"):
                    raise ValueError("unknown timeline")
                if timeline == "branch" and self.branch is None:
                    raise ValueError("create a branch first")
                if timeline in ("original", "both"):
                    self.original.step(count)
                if self.branch and timeline in ("branch", "both"):
                    self.branch.step(count)
            elif operation == "fork":
                self.branch = self.original.fork(data)
            else:
                raise ValueError("unknown operation")
            self.commands.append({"operation": operation, "data": copy.deepcopy(data)})
            if save:
                self.save()
            return self.state()


def make_handler(session):
    static_root = Path(__file__).parent / "city" / "static"
    repo_root = Path(__file__).resolve().parent.parent

    class Handler(BaseHTTPRequestHandler):
        server_version = "KalendsLocal/1.0"

        def send_bytes(self, status, content, mime):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(content)

        def send_json(self, value, status=200):
            self.send_bytes(status, json.dumps(value, allow_nan=False).encode(), "application/json; charset=utf-8")

        def do_GET(self):
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            try:
                with session.lock:
                    if parsed.path == "/api/state":
                        return self.send_json(session.state())
                    if parsed.path == "/api/export":
                        return self.send_json({"version": 1, "commands": session.commands,
                                               "state": session.state()})
                    if parsed.path == "/api/necessity":
                        from .city.causal import verify_message_dependency
                        if query.get("timeline", ["original"])[0] != "original":
                            raise ValueError("dependency checks currently support the original timeline")
                        event_id = int(query.get("event_id", ["-1"])[0])
                        message = query.get("message_event_id", [None])[0]
                        return self.send_json(verify_message_dependency(
                            session.original, event_id, int(message) if message is not None else None))
                    if parsed.path == "/api/trace":
                        timeline = query.get("timeline", ["original"])[0]
                        if timeline not in ("original", "branch"):
                            raise ValueError("unknown timeline")
                        sim = session.branch if timeline == "branch" else session.original
                        if sim is None:
                            raise ValueError("create a branch first")
                        return self.send_json(sim.trace(int(query.get("event_id", ["-1"])[0])))
                if parsed.path == "/api/results":
                    path = repo_root / "results/fork_city/heldout/summary.json"
                    if not path.exists():
                        return self.send_json({"status": "experiments not yet generated"}, 404)
                    return self.send_bytes(200, path.read_bytes(), "application/json; charset=utf-8")
                if parsed.path == "/research":
                    path = repo_root / "docs/fork_city/RESEARCH_NOTE.md"
                    if not path.exists():
                        return self.send_bytes(404, b"Research note is not yet generated.", "text/plain")
                    return self.send_bytes(200, path.read_bytes(), "text/plain; charset=utf-8")
                routes = {"/": "index.html", "/index.html": "index.html",
                          "/style.css": "style.css", "/app.js": "app.js"}
                if parsed.path not in routes:
                    return self.send_json({"error": "route not found"}, 404)
                path = static_root / routes[parsed.path]
                mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
                return self.send_bytes(200, path.read_bytes(), mime + "; charset=utf-8")
            except (ValueError, KeyError, TypeError) as exc:
                return self.send_json({"error": str(exc)}, 400)

        def do_POST(self):
            # Loopback service: do not permit cross-origin browser mutations.
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).netloc != self.headers.get("Host"):
                return self.send_json({"error": "cross-origin request rejected"}, 403)
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 65536:
                    raise ValueError("JSON body must be 1..65536 bytes")
                data = json.loads(self.rfile.read(size))
                if not isinstance(data, dict):
                    raise ValueError("JSON body must be an object")
                routes = {"/api/reset": "reset", "/api/step": "step", "/api/fork": "fork"}
                if self.path not in routes:
                    return self.send_json({"error": "route not found"}, 404)
                return self.send_json(session.apply(routes[self.path], data))
            except (ValueError, KeyError, TypeError) as exc:
                return self.send_json({"error": str(exc)}, 400)

        def log_message(self, format, *args):
            pass  # Local UI polls frequently; keep terminal output useful.

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kalends: Fork the City — local deterministic world")
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--journal", default=".kalends/city_session.json",
                        help="command journal for restart recovery; empty string disables persistence")
    args = parser.parse_args(argv)
    session = CitySession(args.journal or None)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(session))
    print("KALENDS — FORK THE CITY", flush=True)
    print("Local: http://%s:%d" % (args.host, server.server_port), flush=True)
    print("Deterministic offline simulation. Ctrl+C stops the server.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
