"""Shared experience lifecycle and compatibility adapters, not a new simulator.

Legacy save formats and research runtimes are untouched. New experience journals
record their spec, adapter version and accepted commands, and verify exact replay.
"""
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import threading

from kalends.pompeii.district import PEOPLE, PompeiiConfig
from kalends_rebirth.language import execute
from kalends_rebirth.server import RebirthSession
from kalends_rebirth.world import RebirthWorld


def clean(value):
    if isinstance(value, dict):
        return {json.dumps(k) if isinstance(k, tuple) else str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    return value


def canonical(value):
    return json.dumps(clean(value), sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class ExperiencePompeiiWorld(RebirthWorld):
    """Opt-in V3 decisions on legacy scheduled procurement/duty opportunities.

    The old class/command revisions remain unchanged. No legacy save is loaded
    into this new behavioral revision without explicitly compiling a new life.
    """
    def __init__(self, config=None, *, retention="hybrid", opportunities=()):
        self._os_bridge = None
        super().__init__(config=config)
        from .minds import PompeiiMindBridge, MindConfig
        capacity = self.config.memory_capacity
        self._os_bridge = PompeiiMindBridge(MindConfig(capacity=capacity, context_records=min(8, capacity), retention_policy=retention))
        for actor in self.agent_ids:
            self._os_bridge.admit(self, actor)
        for actor in ("Dama", "Chreste"):
            self.clock.schedule(180, "os_mind", {"agent": actor})
        for opportunity in opportunities:
            if opportunity["at"] == 0:
                self._emit("experience_opportunity", opportunity["label"], actors=("Player",), scope="private")
            else:
                self.clock.schedule(opportunity["at"], "os_opportunity", {"label": opportunity["label"]})

    def on_task(self, task):
        actor = task["data"].get("agent")
        if task["kind"] == "os_opportunity":
            self._emit("experience_opportunity", task["data"]["label"], actors=("Player",), scope="private")
        elif self._os_bridge is not None and task["kind"] in ("procure", "os_mind") and actor in self.agent_ids:
            trace = self._os_bridge.decide(self, actor)
            decision = trace["decision"]
            event = self._emit("os_decision", f"{actor} chooses {decision['action_id']} from retained evidence", actors=(actor,), scope="private",
                               parents=decision["evidence_ids"], decision=decision)
            execution = trace.get("execution_spec") or {"kind": "wait"}
            kind = execution["kind"]
            try:
                if kind == "purchase":
                    event = self._purchase(actor, execution["data"]["quantity"], event.event_id)
                elif kind == "inspection_booking":
                    event = self._book_inspection(actor, event.event_id)
                elif kind in ("routine", "gossip"):
                    super().on_task({"kind": kind, "data": execution["data"]})
                self._os_bridge.admit(self, actor)
                known = self._os_bridge.minds[actor].retained_event_ids()
                self._os_bridge.minds[actor].evaluate(decision["action_id"], "succeeded", now=self.minute,
                    evidence_ids=(event.event_id,) if event.event_id in known else (), detail="Existing world rule executed the selected option.")
            except ValueError as error:
                self._os_bridge.minds[actor].evaluate(decision["action_id"], "failed", now=self.minute, detail=str(error)[:256])
            if task["kind"] == "os_mind" and self.minute + 1440 <= self.config.horizon_days * 1440:
                self.clock.schedule(self.minute + 1440, "os_mind", {"agent": actor})
        else:
            super().on_task(task)
        if self._os_bridge is not None:
            for actor in self.agent_ids:
                self._os_bridge.admit(self, actor)

    def fidelity_state(self):
        result = super().fidelity_state()
        result["experience_os_minds_v3"] = self._os_bridge.to_dict() if self._os_bridge else None
        return result


class ExperienceRuntime:
    version = 1

    def __init__(self, spec, *, journal_path=None, retention="hybrid"):
        from .compiler import ExperienceCompilerV1, ExperienceSpec
        self.spec = ExperienceCompilerV1().validate(spec)
        self.spec_hash = digest(self.spec.to_dict())
        self.retention, self.commands = retention, []
        self.journal_path = Path(journal_path) if journal_path else None
        self.lock = threading.RLock()
        self.last_time = None
        self._new_world()
        if self.journal_path and self.journal_path.exists():
            document = json.loads(self.journal_path.read_text())
            if (document.get("version") != self.version or document.get("spec_hash") != self.spec_hash or
                    document.get("retention") != self.retention or digest(document.get("spec")) != self.spec_hash):
                raise ValueError("Experience journal revision/configuration differs; original preserved")
            for command in document["commands"]:
                if (set(command) != {"revision", "operation", "data", "at", "after", "receipt_id"} or
                        command.get("revision") != 1 or type(command.get("at")) is not int or
                        command["at"] != self.minute):
                    raise ValueError("Unsupported revision or inconsistent accepted-command start time")
                receipt = self._perform(command["operation"], command["data"])
                expected_id = receipt.get("event_id") if isinstance(receipt, dict) else None
                if (type(command.get("after")) is not int or command["after"] != self.minute or
                        command["receipt_id"] != expected_id):
                    raise ValueError("Accepted-command replay metadata differs; original preserved")
                self.commands.append(copy.deepcopy(command))
            if self.state_hash() != document["state_hash"]:
                raise ValueError("Experience replay differs; original preserved")

    def _new_world(self):
        if self.spec.setting["adapter"] == "pompeii":
            self.world = ExperiencePompeiiWorld(PompeiiConfig(**self.spec.setting["rules"]), retention=self.retention, opportunities=self.spec.opportunities)
        else:
            from .commons import CoordinationWorld
            self.world = CoordinationWorld(self.spec, retention=self.retention)

    @property
    def minute(self):
        return self.world.minute

    @property
    def minds(self):
        return self.world._os_bridge.minds if self.spec.setting["adapter"] == "pompeii" else self.world.minds

    def state_hash(self):
        return digest(self.world.fidelity_state())

    def _perform(self, operation, data):
        if not isinstance(data, dict):
            raise ValueError("A command needs an object payload")
        if operation == "advance":
            if set(data) - {"minutes", "mode", "strategy"}:
                raise ValueError("Unknown time command fields")
            minutes, mode = data.get("minutes"), data.get("mode", "compress")
            if minutes == "next":
                minutes = max(1, (self.world.clock.peek() or self.minute + 1) - self.minute)
            if type(minutes) is not int or not 1 <= minutes <= 365 * 1440:
                raise ValueError("Choose a bounded whole number of world minutes")
            start = self.minute
            target = min(self.minute + minutes, self.spec.termination["at"], self.spec.horizon_minutes)
            if target <= self.minute:
                raise ValueError("The declared experience horizon has been reached")
            from .temporal import TemporalEngine
            engine = TemporalEngine(self.world.clock, self.world.on_task, ledger=self.world.ledger)
            self.last_time = engine.advance(target, mode=mode, strategy=data.get("strategy", "exact"))
            return {"from": start, "to": target, "mode": mode}
        if operation != "action":
            raise ValueError("Unknown experience operation")
        if self.minute >= self.spec.termination["at"]:
            raise ValueError("This experience has terminated")
        action = data.get("action")
        if data.get("actor", "Player") != "Player" or data.get("actor_id", "Player") != "Player":
            raise ValueError("Only the compiled participant may submit an action")
        if action == "wait" and action in self.spec.actions:
            if set(data) - {"action", "actor"}:
                raise ValueError("Unknown wait fields")
            return self._perform("advance", {"minutes": 1, "mode": "compress"})
        if action not in self.spec.actions or data.get("actor", "Player") != "Player":
            raise ValueError("Action/actor is outside this participant's compiled permissions")
        if self.spec.setting["adapter"] == "commons":
            return self.world.execute(data).to_dict()
        if action == "move":
            if set(data) - {"action", "actor", "x", "y", "location"}:
                raise ValueError("Unknown movement fields")
            previous = getattr(self.world, "_movement_revision", None)
            self.world._movement_revision = 2
            try:
                return self.world.move(**{k: v for k, v in data.items() if k in ("x", "y", "location")})
            finally:
                if previous is None:
                    del self.world._movement_revision
                else:
                    self.world._movement_revision = previous
        if set(data) - {"action", "actor", "recipient", "quantity", "topic", "value", "actor_id", "evidence_ids", "needs_confirmation"}:
            raise ValueError("Unknown player action fields")
        return execute(self.world, {k: v for k, v in data.items() if k != "actor"})

    def commit(self, operation, data):
        """All-or-nothing trial execution, including persistence failure rollback."""
        with self.lock:
            trial = object.__new__(type(self))
            trial.__dict__ = {**self.__dict__, "world": copy.deepcopy(self.world), "commands": list(self.commands)}
            start = self.minute
            receipt = trial._perform(operation, copy.deepcopy(data))
            trial.commands.append({"revision": 1, "operation": operation, "data": copy.deepcopy(data), "at": start,
                                   "after": trial.minute, "receipt_id": receipt.get("event_id") if isinstance(receipt, dict) else None})
            trial.save()
            self.world, self.commands, self.last_time = trial.world, trial.commands, trial.last_time
            return {"receipt": receipt, "state": self.snapshot(), "command_index": len(self.commands) - 1}

    def save(self):
        if not self.journal_path:
            return
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        doc = {"version": self.version, "spec_hash": self.spec_hash, "spec": self.spec.to_dict(), "retention": self.retention,
               "commands": self.commands, "state_hash": self.state_hash()}
        temporary = self.journal_path.with_name(self.journal_path.name + ".tmp")
        temporary.write_text(json.dumps(doc, indent=2, allow_nan=False) + "\n")
        temporary.replace(self.journal_path)

    def visible_ids(self, viewer="Player"):
        if self.spec.setting["adapter"] == "commons":
            return set(self.world.visible[viewer])
        return {e.event_id for e in self.world.ledger.events if self.world._visible(e)}

    def events(self, *, operator=False):
        allowed = self.visible_ids()
        return [e.to_dict() for e in self.world.ledger.events if operator or e.event_id in allowed]

    def metrics(self):
        w = self.world
        if self.spec.setting["adapter"] == "commons":
            base = w.metrics()
            outcomes = [w.get(k[len("experience."):]) for k in w.state.facts if k.startswith("experience.outcome:")]
            totals = [sum(o["executed"][a] for o in outcomes) for a in ("team_a", "team_b", "team_c")]
            return {**base, "completed_rounds": sum(bool(o["completed"]) for o in outcomes), "failed_promises": base["promises_missed"],
                    "equity": min(totals) / max(totals) if max(totals, default=0) else 1,
                    "information_shared": sum(e.payload.get("category") == "report" for e in w.ledger.events),
                    "unused_capacity": sum(o["actual_capacity"] - sum(o["executed"].values()) for o in outcomes), "elapsed_days": self.minute / 1440}
        snapshot = w.snapshot()
        commitments = w.economy.commitments["Player"]
        return {"cash": w.economy.cash["Player"], "inventory": w.economy.inventory["Player"], "reputation": snapshot["player"]["reputation"],
                "deliveries": sum(e.payload.get("category") in ("promise_settled", "rb_commission_settled") for e in w.ledger.events),
                "service_minutes": sum(c.get("fulfilled", 0) for c in commitments if c.get("id") in ("rebirth-service", "household-service")),
                "completed_commissions": sum(c["status"] == "fulfilled" for c in w.commissions),
                "fulfilled_obligations": sum(c["status"] == "fulfilled" for c in commitments), "missed_obligations": sum(c["status"] == "missed" for c in commitments),
                "elapsed_days": self.minute / 1440}

    def snapshot(self, *, operator=False):
        from .temporal import TemporalEngine
        events = self.events(operator=operator)
        summary = TemporalEngine(self.world.clock, self.world.on_task, ledger=self.world.ledger).montage(events, {e["event_id"] for e in events}, limit=10)
        participants = [{"id": p["id"], "role": p["role"]} for p in self.spec.participants]
        result = {"experience": self.spec.id, "title": self.spec.title, "setting": self.spec.setting["adapter"], "minute": self.minute,
                  "day": self.minute // 1440 + 1, "horizon": self.spec.horizon_minutes, "terminated": self.minute >= self.spec.termination["at"],
                  "participants": participants, "metrics": self.metrics(), "objectives": self.spec.debrief["objective"],
                  "events": events[-80:], "montage": summary, "command_count": len(self.commands), "state_hash": self.state_hash(),
                  "capabilities": {"kernel": "existing ledger/state/economy", "minds": "V3, authored bounded options", "temporal": "existing exact clock + conservative adapter"}}
        if self.spec.setting["adapter"] == "commons":
            r = self.world.round
            result.update(requests=self.world.get(f"requests:{r}", {}), allocation=self.world.get(f"allocation:{r}"),
                          promises=self.world.get(f"promises:{r}", {}), credits=self.world.economy.cash["Player"],
                          own_reports=[e for e in events if e["payload"].get("prop") == ["observatory", "condition"]][-5:])
        else:
            result["world"] = self.world.snapshot(operator=False)
        if operator:
            result["lab"] = {"truth": clean(self.world.fidelity_state()), "minds": {a: m.inspect(now=self.minute) for a, m in self.minds.items()},
                             "commands": copy.deepcopy(self.commands), "notice": "Local operator view; private information is deliberately visible here only."}
        return clean(result)

    def trace(self, event_id, *, operator=False):
        if type(event_id) is not int or not 0 <= event_id < len(self.world.ledger):
            raise ValueError("Unknown event")
        allowed = set(range(len(self.world.ledger))) if operator else self.visible_ids()
        if event_id not in allowed:
            raise ValueError("This participant has not observed this event")
        todo, seen, hidden = [event_id], set(), set()
        while todo:
            eid = todo.pop()
            if eid in seen:
                continue
            if eid not in allowed:
                hidden.add(eid); continue
            seen.add(eid)
            todo.extend(self.world.ledger.events[eid].payload.get("parents", []))
        return {"events": [self.world.ledger.events[i].to_dict() for i in sorted(seen)], "hidden_parent_count": len(hidden),
                "interpretation": "Recorded dependency links are evidence/accounting; only an executed intervention tests an alternative."}

    def debrief(self):
        from .temporal import significance
        personal = [e for e in self.events() if "Player" in e["actors"] and significance(e).get("consequential")]
        return {"objective": self.spec.debrief["objective"], "questions": self.spec.debrief["questions"],
                "choices": [{"index": i, **c} for i, c in enumerate(self.commands) if c["operation"] == "action"],
                "consequences": personal[-16:], "outcomes": self.metrics(), "transfer": {k: v for k, v in self.spec.debrief["transfer"].items() if k not in ("answer", "rationale")},
                "claim_limit": "This describes simulated performance and actual records. Human learning and real-world transfer have not been measured."}

    def fork(self, command_index):
        if type(command_index) is not int or not 0 <= command_index < len(self.commands) or self.commands[command_index]["operation"] != "action":
            raise ValueError("Select an actual accepted participant action")
        branch = ExperienceRuntime(self.spec, retention=self.retention)
        skipped = []
        for i, command in enumerate(self.commands):
            if i == command_index:
                continue
            try:
                if branch.minute < command["at"]:
                    branch.commit("advance", {"minutes": command["at"] - branch.minute, "mode": "compress"})
                if command["operation"] == "advance":
                    remaining = command["after"] - branch.minute
                    if remaining > 0:
                        branch.commit("advance", {**command["data"], "minutes": remaining})
                else:
                    branch.commit(command["operation"], command["data"])
            except ValueError as error:
                skipped.append({"index": i, "reason": str(error)})
        return {"omitted_command": command_index, "skipped": skipped, "original": self.snapshot(), "alternative": branch.snapshot(),
                "differences": {k: {"original": self.metrics().get(k), "alternative": branch.metrics().get(k)} for k in self.metrics() if self.metrics().get(k) != branch.metrics().get(k)},
                "alternative_hash": branch.state_hash(), "interpretation": "Executed omission with declared later commands; not an optimal or necessary-cause proof."}


class ExperienceGameFacade:
    """Reuse the shipped dialogue/route protocol against the SAME compiled life."""
    def __init__(self, runtime, cognition=None):
        self.runtime = runtime
        from kalends_rebirth.ai import Cognition
        from kalends_rebirth.language import Language
        self.legacy = RebirthSession(config=runtime.spec.setting["rules"], language=Language(cognition or Cognition()))

    def sync(self):
        self.legacy.original = self.runtime.world
        self.legacy.commands = self.runtime.commands
        return self.legacy

    def state(self):
        return self.sync().state()

    def context(self, recipient):
        return self.sync().context(recipient)

    def route(self, data):
        return self.sync().route(data)

    def propose(self, data):
        result = self.sync().propose(data)
        self.legacy.proposals[result["proposal_id"]]["experience_revision"] = self.runtime.state_hash()
        return result

    def act(self, data):
        session = self.sync()
        proposal = session.proposals.get(data.get("proposal_id"))
        if not proposal or proposal.get("experience_revision") != self.runtime.state_hash():
            raise ValueError("The situation changed. Review this choice again.")
        interpretation = next((i for i in proposal["interpretations"] if i["id"] == data.get("interpretation_id")), None)
        if not interpretation:
            raise ValueError("Unknown reviewed choice")
        result = self.runtime.commit("action", interpretation["action"])
        session.proposals.clear()
        return {**self.state(), "receipt": result["receipt"]}

