"""Local participant UI, durable accepted-action journal and historical reruns."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import mimetypes
import threading
from dataclasses import asdict, fields
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .language import compile_utterance, validate_result


class GenesisSession:
    version = 2

    def __init__(self, journal_path=None, adapter=None):
        self.lock = threading.RLock()
        self.journal_path = Path(journal_path) if journal_path else None
        self.adapter = adapter
        self.mode = "player"
        self.proposals, self.dialogues, self.disclosed = {}, [], set()
        self.branch, self.intervention, self.return_report = None, None, None
        self.reset({}, save=False)
        if self.journal_path and self.journal_path.exists():
            payload = json.loads(self.journal_path.read_text())
            if payload.get("version") != self.version:
                raise ValueError("unsupported Genesis journal version")
            self.mode = "operator"  # Replay already-authorized historical operator commands.
            for item in payload["commands"]:
                self.apply(item["operation"], item["data"], save=False)
            self.proposals = payload.get("proposals", {})
            self.dialogues = payload.get("dialogues", [])
            self.disclosed = set(payload.get("disclosed", []))
            self.mode = payload.get("mode", "player")

    def reset(self, data, save=True):
        from .config import GenesisConfig
        from .simulation import GenesisSimulation
        allowed = {field.name for field in fields(GenesisConfig)}
        if set(data) - allowed:
            raise ValueError("unknown configuration fields")
        config = GenesisConfig(**data)
        self.original = GenesisSimulation(config)
        self.branch, self.intervention, self.return_report = None, None, None
        self.proposals, self.dialogues, self.disclosed = {}, [], set()
        self.commands = [{"operation": "reset", "data": asdict(config)}]
        # The settlement is moving when a new player enters; this is deterministic.
        self.original.step(min(3, config.n_ticks))
        if save:
            self.save()

    def save(self):
        if self.journal_path:
            self.journal_path.parent.mkdir(parents=True, exist_ok=True)
            payload = {"version": self.version, "commands": self.commands,
                       "proposals": self.proposals, "dialogues": self.dialogues,
                       "disclosed": sorted(self.disclosed), "mode": self.mode}
            temporary = self.journal_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
            temporary.replace(self.journal_path)

    def _view(self, agent):
        view = copy.deepcopy(self.original.private_view(agent))
        view["tick"] = self.original.tick
        if "experiences" not in view:
            view["experiences"] = [asdict(e) for e in self.original.remembered(agent)]
        return view

    def _visible_ids(self, sim):
        snapshot = sim.snapshot(operator=False)
        events = snapshot.get("player_events", [e for e in snapshot.get("events", [])
                                                if e.get("player_visible")])
        return {e["event_id"] for e in events} | (self.disclosed if sim is self.original else set())

    def state(self):
        operator = self.mode == "operator"
        original = self.original.snapshot(operator=operator)
        branch = self.branch.snapshot(operator=operator) if self.branch else None
        comparison = self.original.compare(self.branch) if self.branch else None
        if comparison and not operator:
            # Counterfactual private beliefs and other citizens' accounts stay in research mode.
            comparison = {key: comparison[key] for key in
                          ("tick", "branch_tick", "changed_agents", "changed_actions", "changed_relationships", "identical")
                          if key in comparison}
            comparison["interpretation"] = "A rerun under one changed intervention; aggregate differences are not proof that every changed event was caused by that message."
        return {"original": original, "branch": branch, "comparison": comparison,
                "mode": self.mode, "return_report": self.return_report,
                "intervention": self.intervention, "dialogues": copy.deepcopy(self.dialogues[-40:]),
                "language": {"mode": "offline deterministic grammar" if self.adapter is None else "custom adapter",
                             "automatic_inference_cost_usd": 0 if self.adapter is None else None}}

    def agent(self, agent):
        if agent not in self.original.agent_ids:
            raise ValueError("unknown citizen")
        public = next(a for a in self.original.snapshot(operator=False)["agents"] if a["id"] == agent)
        result = copy.deepcopy(public)
        if self.mode == "operator":
            result["private"] = self._view(agent)
        return result

    def propose(self, data):
        with self.lock:
            recipient, text = data.get("recipient"), data.get("text")
            if recipient not in self.original.agent_ids or not isinstance(text, str):
                raise ValueError("select a citizen and enter a message")
            view, player_view = self._view(recipient), self._view("Player")
            result = compile_utterance(text, recipient, view, player_view, self.adapter)
            proposal_id = hashlib.sha256(json.dumps({"text": text, "recipient": recipient,
                "tick": self.original.tick, "sequence": len(self.proposals),
                "ledger": self.original.ledger.content_hash()}, sort_keys=True).encode()).hexdigest()[:20]
            record = {"proposal_id": proposal_id, "tick": self.original.tick,
                      "recipient": recipient, "text": text, "result": result, "accepted": False}
            self.proposals[proposal_id] = record
            if result.get("reply"):
                reply = result["reply"]
                self.disclosed.update(reply.get("evidence_ids", []))
                self.dialogues.append({"recipient": recipient, "tick": self.original.tick,
                                       "utterance": text, "reply": reply})
            self.save()
            return dict(result, proposal_id=proposal_id)

    def act(self, data):
        with self.lock:
            proposal = self.proposals.get(data.get("proposal_id"))
            if not proposal or proposal["accepted"]:
                raise ValueError("proposal is missing or was already confirmed")
            if proposal["tick"] != self.original.tick:
                raise ValueError("the town has advanced; ask again to review a current proposal")
            choices = [i for i in proposal["result"]["interpretations"]
                       if str(i["id"]) == str(data.get("interpretation_id"))]
            if len(choices) != 1:
                raise ValueError("choose one proposed interpretation")
            validate_result({k: proposal["result"].get(k) for k in ("interpretations", "reply", "clarification")},
                            proposal["recipient"], self._view(proposal["recipient"]), self._view("Player"))
            result = self.apply("action", {"action": choices[0]["action"],
                    "proposal_id": proposal["proposal_id"], "adapter": proposal["result"]["adapter"]}, save=False)
            proposal["accepted"] = True
            self.save()
            return result

    @staticmethod
    def _execute(sim, action):
        return sim.apply_player_action(copy.deepcopy(action))

    def _historical_fork(self, data):
        kind = data.get("kind", "none")
        if kind not in ("none", "remove_message", "correction"):
            raise ValueError("unknown intervention")
        if self.mode != "operator":
            raise ValueError("historical interventions require Research mode")
        at_tick = data.get("at_tick", self.original.tick)
        if type(at_tick) is not int or not 2 <= at_tick <= self.original.tick:
            raise ValueError("historical tick must be from opening tick 2 through the current tick")
        target = data.get("event_id")
        action_index = None
        if kind == "remove_message":
            candidates = [(i, item) for i, item in enumerate(self.commands)
                          if item["operation"] == "action" and item["data"]["action"].get("kind") == "claim"]
            if target is not None:
                candidates = [(i, item) for i, item in candidates if item["data"].get("event_id") == target]
            if not candidates:
                raise ValueError("select a confirmed player claim to remove from history")
            action_index, selected = candidates[-1]
            at_tick = selected["data"]["tick"]
            target = selected["data"]["event_id"]
        from .config import GenesisConfig
        from .simulation import GenesisSimulation
        branch = GenesisSimulation(GenesisConfig(**self.commands[0]["data"]))
        branch.step(min(3, branch.config.n_ticks))
        inserted, replayed = False, 0
        reference_map, skipped = {}, []
        removed_id = target if kind == "remove_message" else None

        def identity(event):
            payload = event.payload
            return (event.tick, event.etype, event.actors, payload.get("category"),
                    tuple(payload.get("prop", [])), payload.get("value"), payload.get("as_of"),
                    payload.get("record_as_of"), payload.get("owner"))

        def remap_root(root):
            if root in reference_map:
                return reference_map[root]
            if root == removed_id:
                return None
            if type(root) is not int or not 0 <= root < len(self.original.ledger):
                raise ValueError("historical action refers to a nonexistent source event")
            original_event = self.original.ledger.events[root]
            matches = [e for e in branch.ledger.events if identity(e) == identity(original_event)]
            if len(matches) != 1:
                raise ValueError("historical action's source no longer has a unique counterpart; this fork cannot replay it safely")
            reference_map[root] = matches[0].event_id
            return matches[0].event_id

        def intervene():
            nonlocal inserted
            if kind == "correction":
                agent = data.get("agent", "Livia")
                if agent not in branch.agent_ids:
                    raise ValueError("unknown intervention recipient")
                # A privileged counterfactual is explicitly labelled; ordinary inspections cost 2 and take a tick.
                branch._verify_now(agent, max(0, branch.tick), operator=True)
            inserted = True

        for index, item in enumerate(self.commands[1:], 1):
            operation, payload = item["operation"], item["data"]
            if operation == "step" and payload.get("timeline", "both") in ("original", "both"):
                for _ in range(payload.get("count", 1)):
                    if not inserted and branch.tick >= at_tick and kind != "remove_message":
                        intervene()
                    branch.step()
                    replayed += 1
            elif operation == "action":
                if index == action_index:
                    inserted = True
                    continue
                # Accepted structured actions are rerun, never reinterpreted by a model.
                action = copy.deepcopy(payload["action"])
                if action.get("root_event") is not None:
                    mapped = remap_root(action["root_event"])
                    if mapped is None:
                        skipped.append({"command_index": index, "original_event_id": payload["event_id"],
                                        "reason": "source claim was removed; dependent retraction or correction has no target"})
                        continue
                    action["root_event"] = mapped
                executed = self._execute(branch, action)
                reference_map[payload["event_id"]] = executed["event_id"]
        if not inserted:
            intervene()
        branch.branch_id, branch.parent_tick = "genesis-counterfactual", at_tick
        return branch, {"kind": kind, "at_tick": at_tick, "event_id": target,
                        "rerun_through_tick": branch.tick, "replayed_ticks": replayed,
                        "skipped_dependent_actions": skipped,
                        "operator_intervention": True,
                        "note": "Accepted actions replayed from the same initial seed. Removing a claim omits its original action, including all downstream propagation."}

    def apply(self, operation, data, save=True):
        with self.lock:
            receipt = None
            if operation == "reset":
                self.reset(data, save=save)
                return self.state()
            if operation == "step":
                count, timeline = data.get("count", 1), data.get("timeline", "both")
                if type(count) is not int or not 1 <= count <= 96:
                    raise ValueError("step count must be an integer from 1 to 96")
                if timeline not in ("both", "original", "branch") or (timeline == "branch" and not self.branch):
                    raise ValueError("unknown or unavailable timeline")
                start = self.original.tick
                before = {a: self.original.economy.relationships.get((a, "Player"), .6) for a in self.original.agent_ids}
                if timeline in ("original", "both"):
                    self.original.step(count)
                if self.branch and timeline in ("branch", "both"):
                    self.branch.step(count)
                if count >= 24:
                    changes = [{"agent": a, "text": "%s's trust in you changed from %.0f%% to %.0f%%." %
                                (a, before[a] * 100, self.original.economy.relationships.get((a, "Player"), .6) * 100),
                                "event_ids": []} for a in self.original.agent_ids
                               if before[a] != self.original.economy.relationships.get((a, "Player"), .6)]
                    self.return_report = {"from_tick": start, "to_tick": self.original.tick,
                        "elapsed_ticks": self.original.tick - start, "changes": changes,
                        "summary": "The town advanced %s ticks. Ask a citizen what they remember; their account may be incomplete." % (self.original.tick - start)}
            elif operation == "action":
                candidate = copy.deepcopy(self.original)
                receipt = self._execute(candidate, data["action"])
                self.original = candidate
                data = dict(copy.deepcopy(data), event_id=receipt["event_id"], tick=self.original.tick)
            elif operation == "fork":
                branch, intervention = self._historical_fork(data)
                self.branch, self.intervention = branch, intervention
            elif operation == "mode":
                if data.get("mode") not in ("player", "operator"):
                    raise ValueError("mode must be player or operator")
                self.mode = data["mode"]
                if save:
                    self.save()
                return self.state()
            else:
                raise ValueError("unknown operation")
            self.commands.append({"operation": operation, "data": copy.deepcopy(data)})
            if save:
                self.save()
            result = self.state()
            if receipt is not None:
                result["receipt"] = receipt
            return result

    def trace(self, event_id, timeline="original"):
        if timeline not in ("original", "branch"):
            raise ValueError("unknown timeline")
        sim = self.original if timeline == "original" else self.branch
        if sim is None:
            raise ValueError("create a branch first")
        if self.mode == "operator":
            return sim.trace(event_id)
        allowed = self._visible_ids(sim)
        if event_id not in allowed:
            raise ValueError("that event is not accessible to the player")
        trace = sim.trace(event_id)
        trace["events"] = [e for e in trace["events"] if e["event_id"] in allowed]
        trace["ancestors"] = [e for e in trace.get("ancestors", []) if e["event_id"] in allowed]
        trace["links"] = [link for link in trace["links"] if link["source"] in allowed and link["target"] in allowed]
        trace["root_ids"] = [i for i in trace["root_ids"] if i in allowed]
        trace["interpretation"] = "Only events witnessed by you or cited to you are shown. Hidden ancestry is not disclosed. Structural links do not establish causal necessity."
        return trace


def make_handler(session):
    static_root = Path(__file__).parent / "static"
    repo_root = Path(__file__).resolve().parents[2]

    class Handler(BaseHTTPRequestHandler):
        server_version = "KalendsGenesis/2.0"

        def send_bytes(self, status, content, mime):
            self.send_response(status)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; script-src 'self'; connect-src 'self'; frame-ancestors 'none'")
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
                    if parsed.path == "/api/agent":
                        return self.send_json(session.agent(query.get("id", ["Livia"])[0]))
                    if parsed.path == "/api/trace":
                        return self.send_json(session.trace(int(query.get("event_id", ["-1"])[0]), query.get("timeline", ["original"])[0]))
                    if parsed.path == "/api/export":
                        return self.send_json({"version": session.version, "state": session.state(),
                            "commands": session.commands if session.mode == "operator" else
                            [c for c in session.commands if c["operation"] == "action"]})
                if parsed.path == "/research":
                    path = repo_root / "docs/genesis/RESEARCH_PAPER.md"
                    content = path.read_bytes() if path.exists() else b"Genesis research is in progress. Historical results remain in docs/fork_city/."
                    return self.send_bytes(200, content, "text/plain; charset=utf-8")
                routes = {"/": "index.html", "/index.html": "index.html", "/style.css": "style.css", "/app.js": "app.js"}
                if parsed.path not in routes:
                    return self.send_json({"error": "route not found"}, 404)
                path = static_root / routes[parsed.path]
                return self.send_bytes(200, path.read_bytes(), (mimetypes.guess_type(str(path))[0] or "application/octet-stream") + "; charset=utf-8")
            except (ValueError, KeyError, TypeError) as exc:
                return self.send_json({"error": str(exc)}, 400)

        def do_POST(self):
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
                if self.path == "/api/propose":
                    return self.send_json(session.propose(data))
                if self.path == "/api/act":
                    return self.send_json(session.act(data))
                routes = {"/api/reset": "reset", "/api/step": "step", "/api/fork": "fork", "/api/mode": "mode"}
                if self.path not in routes:
                    return self.send_json({"error": "route not found"}, 404)
                return self.send_json(session.apply(routes[self.path], data))
            except (ValueError, KeyError, TypeError) as exc:
                return self.send_json({"error": str(exc)}, 400)

        def log_message(self, format, *args):
            pass

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description="Kalends Genesis — The City That Remembers You")
    parser.add_argument("--host", default="127.0.0.1", choices=("127.0.0.1", "localhost"))
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--journal", default=".kalends/genesis_session.json")
    args = parser.parse_args(argv)
    session = GenesisSession(args.journal or None)
    server = ThreadingHTTPServer((args.host, args.port), make_handler(session))
    print("KALENDS GENESIS — http://%s:%s" % (args.host, server.server_port), flush=True)
    print("Offline grammar; no model service or background clock. State persists after accepted actions.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
