"""Persistent cognition over the existing admitted-observation AgentMind.

This is a compatibility extension, not a replacement simulation.  The canonical
world remains responsible for truth, observation routing, actions and receipts.
Plans are bounded working state; they do not grant archival retrieval.  The
decision loop never executes an option or treats a proposed action as success.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import hashlib
import json

from kalends_rebirth.minds import (
    ActionOption, AgentMind, Belief, BeliefCondition, Decision, Episode, Goal,
    MindConfig, SocialCondition, SocialSignal,
)


def _json(value):
    return json.loads(json.dumps(value, allow_nan=False))


def _minute(value):
    if type(value) is not int or value < 0:
        raise ValueError("time must be a nonnegative integer")
    return value


@dataclass(frozen=True)
class Plan:
    """One supported next step, not an invented multi-step action sequence."""

    plan_id: int
    action_id: str
    goal_id: str | None
    created_at: int
    updated_at: int
    due_at: int | None
    duration: int
    status: str
    evidence_ids: tuple[int, ...]
    reasons: tuple[str, ...]
    option_fingerprint: str
    previous_plan_id: int | None = None
    outcome: str | None = None


class PersistentMind(AgentMind):
    """Minds V3: the V2 bounded memory plus persistent, revisable plans.

    A maximum of four plans (including the current one) is retained.  Every
    evidence list fits the existing context budget.  Consolidated inferences
    compete for the *same* record budget as episodes and semantic facts.  They
    never become independent sources or fabricate event identifiers.
    """

    version = 3
    plan_capacity = 4

    def __init__(self, agent_id, config=None):
        super().__init__(agent_id, config)
        self.plans = []
        self._plan_serial = 0
        self._cycle_serial = 0
        self._last_cycle_at = None

    @property
    def current_plan(self):
        return self.plans[-1] if self.plans else None

    def retained_event_ids(self):
        """Actual retained experience identities, excluding derived references."""
        return tuple(sorted({r["event_id"] for r in self._episodes + self._semantic}))

    def provenance(self, event_id):
        """Explain one retained source without restoring an evicted experience."""
        if type(event_id) is not int or event_id < 0:
            raise ValueError("event identity must be a nonnegative integer")
        records = [r for r in self._episodes + self._semantic if r["event_id"] == event_id]
        if not records:
            return {"event_id": event_id, "kind": "unknown", "retained": False}
        record = records[-1]
        return {"event_id": event_id, "kind": "testimony" if record["kind"] == "told" else "direct",
            "experience_kind": record["kind"], "retained": True,
            "source_agent": record.get("source_agent"), "observed_at": record["observed_at"],
            "as_of": record.get("as_of"), "claimed_origin_event": record.get("origin_event"),
            "claimed_origin_observer": record.get("origin_observer"),
            "source_caution": "Communicated ancestry is a claim, not independently authenticated provenance."}

    @staticmethod
    def _fingerprint(option):
        return hashlib.sha256(json.dumps(asdict(option), sort_keys=True,
            separators=(",", ":"), allow_nan=False).encode()).hexdigest()

    def _plan(self, decision, options, now):
        old = self.current_plan
        option = next((o for o in options if o.action_id == decision.action_id), None)
        fingerprint = self._fingerprint(option) if option else None
        same = bool(old and old.status == "planned" and option
            and old.option_fingerprint == fingerprint)
        if same:
            self.plans[-1] = replace(old, updated_at=now,
                evidence_ids=decision.evidence_ids, reasons=decision.reasons)
            return "continued"
        if old and old.status == "planned":
            self.plans[-1] = replace(old, status="revised" if option else "cancelled",
                updated_at=now, outcome="The current evidence, goals or offered prerequisites no longer support the previous next step.")
        if option is None:
            return "cancelled" if old else "no supported action"
        goal = next((g for g in self.goals if g.goal_id == option.goal_id), None)
        self._plan_serial += 1
        self.plans.append(Plan(self._plan_serial, option.action_id, option.goal_id,
            now, now, option.deadline if option.deadline is not None else goal.deadline if goal else None,
            option.duration, "planned", decision.evidence_ids, decision.reasons,
            fingerprint, old.plan_id if old else None))
        self.plans = self.plans[-self.plan_capacity:]
        return "revised" if old else "created"

    def evaluate(self, action_id, outcome, *, now, evidence_ids=(), detail=None):
        """Accept explicit authoritative feedback; this method performs no action.

        Evidence, when supplied, must already be admitted and retained.  A bare
        execution receipt may record success/failure but creates no observation
        or social score.  The integrating runtime must route the real receipt
        through the actor's observation boundary separately.
        """
        _minute(now)
        plan = self.current_plan
        if plan is None or plan.action_id != action_id or plan.status != "planned":
            raise ValueError("feedback must concern the currently pending action")
        if now < plan.updated_at:
            raise ValueError("feedback cannot precede its plan")
        if outcome not in ("succeeded", "failed", "cancelled"):
            raise ValueError("feedback must be an authoritative terminal outcome")
        refs = tuple(evidence_ids)
        retained = set(self.retained_event_ids())
        if len(refs) > self.config.context_records or any(type(i) is not int or i not in retained for i in refs):
            raise ValueError("feedback evidence must fit the retained context")
        if detail is not None and (not isinstance(detail, str) or len(detail) > 256):
            raise ValueError("feedback detail must be bounded text")
        self.plans[-1] = replace(plan, status=outcome, updated_at=now,
            outcome=detail or "An explicit world execution receipt was supplied.")
        self._last_cycle_at = max(self._last_cycle_at or 0, now)
        return {"plan_id": plan.plan_id, "action_id": action_id, "status": outcome,
            "at": now, "evidence_ids": list(refs), "detail": self.plans[-1].outcome}

    def consolidate(self, *, now):
        """Grounded inference over retained records, without a second archive.

        Policies are an explanatory assessment, not a new eyewitness or a
        directly executable permission.  Decisions still check original facts
        and signals through AgentMind.choose's single shared context.
        """
        _minute(now)
        if not self.config.consolidation:
            return {"enabled": False, "patterns": [], "evidence_ids": []}
        pairs = sorted({(s["other"], s["axis"]) for r in self._episodes + self._semantic
            for s in r.get("social_signals", ())})
        patterns = []
        admitted_ids = set()
        for other, axis in pairs[:8]:
            assessment = self.social(other, axis, now=now)
            refs = assessment["evidence_ids"]
            if not refs:
                continue
            # Enforce one shared evidence budget across all derived patterns.
            kept = []
            for identifier in refs:
                if identifier in admitted_ids or len(admitted_ids) < self.config.context_records:
                    admitted_ids.add(identifier); kept.append(identifier)
            if not kept:
                continue
            records = [r for r in self._episodes + self._semantic if r["event_id"] in kept]
            bounded = self._social(other, axis, records)
            policy = "require verification before extending credit" if axis in ("reliability", "credibility") and bounded["value"] < .4 else "retain the witnessed assessment while its evidence survives"
            patterns.append({"kind": "inference", "rule": "bounded witnessed social assessment",
                "other": other, "axis": axis, "value": bounded["value"], "policy": policy,
                "evidence_ids": kept, "uncertainty": "heuristic assessment, not a calibrated probability"})
        # Replace the previous derived record instead of accumulating an
        # ever-growing autobiographical side channel. Its evidence is admitted
        # before it is summarized; an inference receives no synthetic event ID.
        self._reflections = []
        if patterns:
            refs = sorted(admitted_ids)
            self._reflections.append(self._new(record_type="reflection", event_id=max(refs),
                observed_at=now, created_at=now, patterns=patterns, evidence_ids=refs,
                salience=.65, prediction_error=0, goal_tags=[], epistemic_kind="inference"))
            self._prune(now)
        retained_patterns = [p for r in self._reflections for p in r.get("patterns", ())]
        return {"enabled": True, "patterns": retained_patterns,
            "evidence_ids": sorted({i for p in retained_patterns for i in p["evidence_ids"]})}

    def cycle(self, episodes, goals, options, own_resources, now):
        """Observe → Encode → Retrieve → Update → Select → Plan → Act → Evaluate → Consolidate.

        Act is an explicit handoff to the authoritative world, never a claim
        that the selected action happened.  The returned trace is not archived
        in the mind.  Input contracts and time are checked before mutation.
        """
        _minute(now)
        if self._last_cycle_at is not None and now < self._last_cycle_at:
            raise ValueError("a cognition cycle cannot go back in world time")
        episodes, goals, options = list(episodes), list(goals), list(options)
        if len(episodes) > 1024 or any(not isinstance(e, Episode) or e.agent_id != self.agent_id or e.observed_at > now for e in episodes):
            raise ValueError("cycle admits only bounded, already observed own episodes")
        validator = AgentMind(self.agent_id, self.config)
        validator.set_goals(goals)
        validator.choose(options, own_resources=own_resources, now=now)
        self.set_goals(goals)
        accepted = [e.event_id for e in sorted(episodes, key=lambda e: (e.observed_at, e.event_id)) if self.observe(e)]
        decision = self.choose(options, own_resources=own_resources, now=now)
        revision = self._plan(decision, options, now)
        keys = sorted({(c.subject, c.predicate) for o in options for c in o.conditions})
        context = [r for r in self._episodes + self._semantic if r["event_id"] in decision.context_event_ids]
        beliefs = []
        for key in keys[:self.config.context_records]:
            belief = self._belief(*key, context)
            beliefs.append({**asdict(belief), "epistemic_kind": "unknown" if belief.status != "known" else "direct" if belief.direct else "testimony"})
        consolidated = self.consolidate(now=now)
        self._cycle_serial += 1
        self._last_cycle_at = now
        plan = asdict(self.current_plan) if self.current_plan else None
        return _json({"version": 3, "agent_id": self.agent_id, "cycle": self._cycle_serial, "at": now,
            "stages": {
                "Observe": {"admitted_event_ids": accepted},
                "Encode": {"record_capacity": self.config.capacity},
                "Retrieve": {"context_event_ids": decision.context_event_ids, "context_capacity": self.config.context_records},
                "Update Beliefs": beliefs,
                "Select Goals": [asdict(g) for g in self._active(now)],
                "Plan": {"revision": revision, "current": plan},
                "Act": {"action_id": decision.action_id, "status": "awaiting authoritative execution" if decision.action_id else "no supported action"},
                "Evaluate": {"current_status": self.current_plan.status if self.current_plan else None,
                    "basis": "Only explicit execution feedback can mark a plan successful."},
                "Consolidate": consolidated},
            "decision": asdict(decision), "plan": plan, "footprint": self.footprint(),
            "epistemic_boundary": "Admitted own observations and bounded retained evidence only; no world or canonical archive access."})

    def to_dict(self):
        base = super().to_dict()
        base["version"] = AgentMind.version
        return _json({"version": self.version, "base": base,
            "plans": [asdict(p) for p in self.plans], "plan_capacity": self.plan_capacity,
            "plan_serial": self._plan_serial, "cycle_serial": self._cycle_serial,
            "last_cycle_at": self._last_cycle_at})

    @classmethod
    def from_dict(cls, value):
        if not isinstance(value, dict) or type(value.get("version")) is not int or value.get("version") != cls.version:
            raise ValueError("unsupported persistent mind snapshot version")
        value = _json(value)
        allowed = {"version", "base", "plans", "plan_capacity", "plan_serial", "cycle_serial", "last_cycle_at"}
        if set(value) != allowed or value["plan_capacity"] != cls.plan_capacity:
            raise ValueError("unknown persistent mind fields or plan capacity")
        base = AgentMind.from_dict(value["base"])
        mind = cls(base.agent_id, base.config)
        mind.__dict__.update(base.__dict__)
        if not isinstance(value["plans"], list) or len(value["plans"]) > cls.plan_capacity:
            raise ValueError("snapshot exceeds the plan budget")
        plans = []
        for row in value["plans"]:
            if not isinstance(row, dict) or set(row) != set(Plan.__dataclass_fields__):
                raise ValueError("unknown plan fields")
            for key in ("plan_id", "created_at", "updated_at", "duration"):
                _minute(row[key])
            for key in ("due_at", "previous_plan_id"):
                if row[key] is not None:
                    _minute(row[key])
            if row["updated_at"] < row["created_at"] or row["status"] not in ("planned", "revised", "succeeded", "failed", "cancelled"):
                raise ValueError("invalid plan time or status")
            if not isinstance(row["evidence_ids"], list) or len(row["evidence_ids"]) > mind.config.context_records:
                raise ValueError("plan evidence exceeds context budget")
            for identifier in row["evidence_ids"]:
                _minute(identifier)
            if not isinstance(row["reasons"], list) or len(row["reasons"]) > 16 or any(not isinstance(r, str) or len(r) > 512 for r in row["reasons"]):
                raise ValueError("invalid plan explanation")
            if not isinstance(row["action_id"], str) or not 1 <= len(row["action_id"]) <= 64 or row["goal_id"] is not None and (not isinstance(row["goal_id"], str) or not 1 <= len(row["goal_id"]) <= 64):
                raise ValueError("invalid planned identity")
            if not isinstance(row["option_fingerprint"], str) or len(row["option_fingerprint"]) != 64 or any(c not in "0123456789abcdef" for c in row["option_fingerprint"]):
                raise ValueError("invalid option fingerprint")
            if row["outcome"] is not None and (not isinstance(row["outcome"], str) or len(row["outcome"]) > 256):
                raise ValueError("invalid plan feedback")
            plans.append(Plan(**{**row, "evidence_ids": tuple(row["evidence_ids"]), "reasons": tuple(row["reasons"])}))
        if len({p.plan_id for p in plans}) != len(plans) or plans != sorted(plans, key=lambda p: p.plan_id):
            raise ValueError("plan identities must be unique and ordered")
        if any(p.status == "planned" for p in plans[:-1]):
            raise ValueError("only the current plan may be pending")
        for field, key in (("_plan_serial", "plan_serial"), ("_cycle_serial", "cycle_serial")):
            setattr(mind, field, _minute(value[key]))
        if plans and mind._plan_serial < plans[-1].plan_id:
            raise ValueError("plan serial precedes retained plans")
        mind._last_cycle_at = value["last_cycle_at"]
        if mind._last_cycle_at is not None:
            _minute(mind._last_cycle_at)
        mind.plans = plans
        return mind

    def footprint(self):
        # AgentMind.footprint calls self.to_dict; override the calculation so the
        # new plan state is explicitly included rather than hidden side memory.
        snapshot = self.to_dict()
        return {"memory_records": len(self._all()), "capacity": self.config.capacity,
            "episodic_records": len(self._episodes), "semantic_social_records": len(self._semantic),
            "revision_records": len(self._revisions), "reflection_records": len(self._reflections),
            "plan_records": len(self.plans), "plan_capacity": self.plan_capacity,
            "active_goal_records": len(self.goals),
            "reference_ids": sum(len(r.get("evidence_ids", ())) + len(r.get("replaces", ())) for r in self._all()) + sum(len(p.evidence_ids) for p in self.plans),
            "serialized_bytes": len(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()),
            "budget_scope": "One shared episode/semantic/revision/inference budget; separately bounded goals, four plans, last decision, and scalar cursors. Bytes include all persisted state."}

    def inspect(self, *, now):
        base = super().inspect(now=now)
        return {**base, "plans": [asdict(p) for p in self.plans],
            "current_plan": asdict(self.current_plan) if self.current_plan else None}


class PompeiiMindBridge:
    """Activate all six existing NPCs without changing their legacy engine.

    sync reads per-agent remembered(), own cash/inventory/location, the current
    clock and declared setting roles. It never reads the event ledger, dispatch
    archive, another agent's memory, private documents or relationship tables.
    Existing event IDs are monotonic in this engine; ingress watermarks prevent
    a currently accessible old episode from repeatedly restoring forgotten data.
    Actual execution remains an explicit runtime responsibility.
    """

    version = 1

    def __init__(self, config=None, previous=None):
        from kalends.pompeii.district import PEOPLE
        if config is None and isinstance(previous, dict) and previous.get("minds"):
            config = next(iter(previous["minds"].values())).get("base", {}).get("config")
        self.config = config if isinstance(config, MindConfig) else MindConfig(**(config or {}))
        self.minds = {a: PersistentMind(a, self.config) for a in PEOPLE}
        self.watermarks = {a: -1 for a in PEOPLE}
        if previous is not None:
            if not isinstance(previous, dict) or type(previous.get("version")) is not int or previous.get("version") != self.version or set(previous.get("minds", {})) != set(PEOPLE):
                raise ValueError("unsupported Pompeii mind bridge snapshot")
            restored = {a: PersistentMind.from_dict(v) for a, v in previous["minds"].items()}
            if any(a != m.agent_id or m.config != self.config for a, m in restored.items()):
                raise ValueError("bridge identity or memory configuration mismatch")
            self.minds = restored
            marks = previous.get("watermarks", {})
            if set(marks) != set(PEOPLE) or any(type(i) is not int or i < -1 for i in marks.values()):
                raise ValueError("invalid observation ingress watermarks")
            self.watermarks = dict(marks)

    @staticmethod
    def _episode(agent, exp):
        # Exact authored structured receipt mapping, never extraction from prose
        # or a lookup of the canonical event payload.
        outcome = None
        if exp.accepted and exp.kind in ("observed", "episodic"):
            if (exp.subject, exp.predicate) == ("v2_social", "Player"):
                outcome = exp.value
            elif exp.subject == "rebirth":
                outcome = {"rb_commission_settled": "kept", "rb_service_kept": "kept",
                    "rb_reconcile": "repaired", "rb_commission_missed": "missed", "rb_service_missed": "missed"}.get(exp.predicate)
        signals = ()
        if outcome in ("kept", "missed", "repaired", "repaid"):
            signals = (SocialSignal("Player", "reliability", {"kept": .18, "missed": -.25, "repaired": .16, "repaid": .08}[outcome]),)
        metadata = dict(participants=(agent, "Player") if signals else (),
            salience=.95 if signals else .65 if exp.subject == "grain" else .2,
            goal_tags=("credit",) if signals else ("supply",) if exp.subject == "grain" else (), social_signals=signals)
        atomic = all(v is None or isinstance(v, str) and 0 < len(v) <= 128
            for v in (exp.subject, exp.predicate, exp.value))
        if atomic and len(exp.text) <= 1024:
            return Episode.from_experience(agent, exp, **metadata)
        # Existing wax-tablet values contain whole JSON documents, beyond the
        # V2 atomic proposition contract. Preserve their already admitted
        # literal account as an episode; truncating a proposition would invent
        # a different fact. No document/archive lookup or guessed extraction.
        return Episode(exp.event_id, agent, exp.tick, exp.kind,
            exp.text[:1024] or "An admitted personal account.", as_of=exp.as_of,
            source_agent=exp.source_agent, origin_event=exp.claimed_origin_event,
            origin_observer=exp.claimed_origin_observer, accepted=exp.accepted, **metadata)

    def admit(self, world, agent):
        """Admit new legitimate records without replanning or executing anything."""
        if agent not in self.minds:
            raise ValueError("unknown Pompeii agent")
        admitted = sorted(world.remembered(agent), key=lambda e: (e.tick, e.event_id))
        fresh = [e for e in admitted if e.event_id > self.watermarks[agent]]
        episodes = [self._episode(agent, e) for e in fresh]
        for episode in episodes:
            if episode.observed_at > world.minute:
                raise ValueError("a world cannot admit an observation from its future")
        added = [episode.event_id for episode in episodes if self.minds[agent].observe(episode)]
        if fresh:
            self.watermarks[agent] = max(e.event_id for e in fresh)
        return added

    def sync(self, world, agents=None):
        from kalends.pompeii.district import PEOPLE
        from kalends_rebirth.scenario import PERSONALITY
        selected = list(PEOPLE) if agents is None else list(agents)
        if len(set(selected)) != len(selected) or any(a not in PEOPLE for a in selected):
            raise ValueError("select only distinct existing Pompeii agents")
        traces = {}
        for agent in selected:
            role = PEOPLE[agent]
            admitted = sorted(world.remembered(agent), key=lambda e: (e.tick, e.event_id))
            fresh = [e for e in admitted if e.event_id > self.watermarks[agent]]
            episodes = [self._episode(agent, e) for e in fresh]
            cash, stock = world.economy.cash[agent], world.economy.inventory[agent]
            resources = {"coins": cash, "flour": stock}
            goals = [Goal("livelihood", PERSONALITY[agent]["long_term"], priority=.6,
                relevant_keys=(("grain", "supply"),), tags=("supply",)),
                Goal("current-duty", role["goal"], priority=1, tags=("supply", "credit"))]
            registry = {"wait": {"kind": "wait", "agent": agent}}
            options = [ActionOption("wait", "Keep the current resources and reassess", 0)]
            if agent in ("Dama", "Chreste"):
                location = "bakery" if agent == "Dama" else role["location"]
                registry["routine"] = {"kind": "routine", "data": {"agent": agent, "location": location}}
                options.append(ActionOption("routine", "Continue the declared assigned duties", 2, "current-duty"))
                if agent == "Dama" and world.state.agent_locations[agent] == "bakery":
                    for value in ("available", "disrupted"):
                        action_id = "gossip-" + value
                        registry[action_id] = {"kind": "gossip", "data": {"speaker": agent, "listener": "Felix"}}
                        options.append(ActionOption(action_id, "Relay the retained dated report", 3, "current-duty",
                            conditions=(BeliefCondition("grain", "supply", value, max_age=360),)))
            else:
                target = 5 if agent == "Felix" else 3 if agent == "Lucius" else 8 if agent == "Marcus" else 2
                if stock < target:
                    registry["purchase"] = {"kind": "purchase", "data": {"agent": agent, "quantity": 1},
                        "validation": "World validates actual price, available stock and owned funds; 3.5 is the setting's conservative price ceiling."}
                    options.append(ActionOption("purchase", "Procure one supported flour unit", 4, "current-duty", costs={"coins": 3.5},
                        conditions=(BeliefCondition("grain", "supply", "available", max_age=180, allow_direct=True),)))
                    registry["inspection"] = {"kind": "inspection_booking", "agent": agent}
                    options.append(ActionOption("inspection", "Pay the existing dispatch inspection fee", 1, "current-duty", costs={"coins": 1}, duration=15))
                else:
                    registry["routine"] = {"kind": "routine", "data": {"agent": agent, "location": role["location"]}}
                    options.append(ActionOption("routine", "Work using the stock already held", 2, "current-duty"))
            trace = self.minds[agent].cycle(episodes, goals, options, resources, world.minute)
            if fresh:
                self.watermarks[agent] = max(e.event_id for e in fresh)
            trace["execution_spec"] = registry.get(trace["decision"]["action_id"])
            trace["declared_role"] = role["role"]
            traces[agent] = trace
        return traces

    def decide(self, world, agent):
        return self.sync(world, agents=[agent])[agent]

    cycle_for = decide

    def to_dict(self):
        return _json({"version": self.version, "minds": {a: m.to_dict() for a, m in self.minds.items()}, "watermarks": self.watermarks})


def attach_pompeii_minds(world, previous=None, config=None):
    bridge = PompeiiMindBridge(config, previous)
    bridge.sync(world)
    return bridge


__all__ = ["PersistentMind", "PompeiiMindBridge", "attach_pompeii_minds", "Plan",
    "AgentMind", "MindConfig", "Episode", "Goal", "ActionOption", "Decision",
    "Belief", "BeliefCondition", "SocialCondition", "SocialSignal"]
