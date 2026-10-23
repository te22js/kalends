"""Declarative capacity-coordination rules on the existing continuity primitives.

This is a domain plugin, not a replacement ledger, clock, memory or economy.
CitySimulation._emit, WorldState/apply_event, GenesisEconomy, observers_of,
EventClock and the existing typed mind contracts supply those mechanisms.
"""
from __future__ import annotations

import copy
import json
from dataclasses import asdict

from kalends.city.simulation import CitySimulation
from kalends.events import Ledger
from kalends.genesis.simulation import GenesisEconomy
from kalends.observation import observers_of
from kalends.pompeii.temporal import EventClock
from kalends.rng import det_rand
from kalends.world import WorldState
from kalends_rebirth.minds import ActionOption, BeliefCondition, Episode, Goal, MindConfig


TEAMS = ("team_a", "team_b", "team_c")


class CoordinationWorld(CitySimulation):
    """Reuse the city projection mechanism with a compiled domain rule registry.

    The project owns no alternative state fold. All mutable domain records are
    JSON-valued propositions in the existing WorldState projection. Credits use
    the existing economic projection; capacity is a declared per-round flow.
    """
    def __init__(self, spec, *, retention="hybrid"):
        from .minds import PersistentMind
        self.spec = spec.to_dict() if hasattr(spec, "to_dict") else copy.deepcopy(spec)
        self.rules = self.spec["setting"]["rules"]
        self.ledger, self.economy, self.clock = Ledger(), GenesisEconomy(), EventClock()
        self.agent_ids = list(TEAMS)
        self.state = WorldState(agent_locations={a: "council" for a in ("Player", *TEAMS)})
        self._stock_event = None
        self.minds = {a: PersistentMind(a, MindConfig(retention_policy=retention)) for a in TEAMS}
        self.visible = {a: set() for a in ("Player", *TEAMS)}
        self.decisions = []
        self._initial_cash = sum(p["resources"].get("credits", 0) for p in self.spec["participants"])
        self._emit(0, "state_change", "council", (), "city_initialized", "The consortium opens its finite credit accounts", scope="private",
                   cash={p["id"]: p["resources"].get("credits", 0) for p in self.spec["participants"]} | {"consortium": 0},
                   inventory={a: 0 for a in ("Player", *TEAMS, "consortium")}, commitments={a: [] for a in ("Player", *TEAMS, "consortium")})
        # Authored projects have absolute deadlines. Their register is public
        # institutional information; private hardware evidence remains private.
        self.put("goal_status", {g["id"]: {
            "status": "blocked" if g["requires"] else "active", "actor": g["actor"],
            "deadline": g["deadline"], "quantity": g["target"]["quantity"],
            "requires": list(g["requires"]), "updated_at": 0,
        } for g in self.spec["goals"]}, "goal_register", "The consortium records its declared research projects", ("Player", *TEAMS))
        for deadline in sorted({g["deadline"] for g in self.spec["goals"]}):
            self.clock.schedule(deadline, "goal_deadline", {})
        for index, opportunity in enumerate(self.spec["opportunities"]):
            if opportunity["at"] == 0:
                self._declared_opportunity(index)
            else:
                self.clock.schedule(opportunity["at"], "declared_opportunity", {"index": index})
        self._round_start()

    @property
    def minute(self):
        return self.clock.now

    @property
    def round(self):
        return self.minute // self.rules["round_minutes"]

    def _emit(self, tick, etype, location, actors, category, title, parents=(), scope="public", **payload):
        event = super()._emit(tick, etype, location, actors, category, title, parents, scope, **payload)
        if not hasattr(self, "visible"):
            return event
        seen = observers_of(event, self.state, ["Player", *TEAMS])
        for actor in seen:
            self.visible[actor].add(event.event_id)
            if actor in self.minds:
                prop = event.payload.get("prop")
                factual = bool(prop and prop[0] == "observatory")
                testimony = factual and event.etype == "tell" and actor == payload.get("listener")
                direct = factual and event.etype != "tell"
                informative = testimony or direct
                episode = Episode(event.event_id, actor, tick, "told" if testimony else "observed" if direct else "episodic", title,
                                  subject=prop[0] if informative else None, predicate=prop[1] if informative else None,
                                  value=str(payload["value"]) if informative else None,
                                  as_of=payload.get("as_of", tick) if testimony else tick,
                                  source_agent=payload.get("speaker") if testimony else None,
                                  origin_event=payload.get("origin_event", event.event_id) if testimony else event.event_id,
                                  origin_observer=payload.get("origin_observer") if testimony else actor,
                                  participants=tuple(actors),
                                  salience=.9 if category in ("condition", "promise_kept", "promise_missed", "allocation_settled") else .25,
                                  goal_tags=("coordination",))
                self.minds[actor].observe(episode)
        return event

    def emit(self, category, title, actors=(), *, scope="public", parents=(), **payload):
        return self._emit(self.minute, "state_change", "council", actors, category, title, parents, scope, **payload)

    def put(self, key, value, category, title, actors=(), *, scope="public", parents=(), **payload):
        return self.emit(category, title, actors, scope=scope, parents=parents,
                         prop=["experience", key], value=json.dumps(value, sort_keys=True, separators=(",", ":")), **payload)

    def get(self, key, default=None):
        value = self.state.facts.get("experience." + key)
        return json.loads(value) if value is not None else copy.deepcopy(default)

    def _round_start(self):
        if self.minute >= self.spec["horizon_minutes"]:
            return
        r = self.round
        condition = self.rules["initial_condition"] if r < self.rules["maintenance_interval"] else ("fragile" if det_rand(self.rules["seed"], "condition", r // self.rules["maintenance_interval"]) < .35 else "stable")
        self.emit("condition", "The systems team inspects the instrument condition", ("team_b",), scope="private",
                  prop=["observatory", "condition"], value=condition)
        self.put(f"requests:{r}", {}, "opportunity", f"Round {r + 1}: teams may negotiate the shared instrument", ("Player", *TEAMS))
        if r:
            self.emit("institutional_routine", f"Round {r + 1} opens the consortium's regular instrument work", ("Player", *TEAMS))
        for team in TEAMS:
            self._decide(team)
        period = self.rules["round_minutes"]
        self.clock.schedule(self.minute + period // 2, "coordination_review", {})
        self.clock.schedule(self.minute + period - 1, "allocation_due", {})
        self.clock.schedule(self.minute + period, "round_start", {})

    def _declared_opportunity(self, index):
        opportunity = self.spec["opportunities"][index]
        return self.emit("opportunity", opportunity["label"], ("Player", *TEAMS),
                         opportunity_index=index, declared_at=opportunity["at"])

    def _refresh_goals(self, outcome=None, parent=None):
        """Project success from actual settled units, never requests or promises.

        Prerequisites must have been completed before this batch settled. A
        dependent project cannot claim the same batch that first establishes
        its prerequisite. A project needs its target in one settled batch.
        """
        old = self.get("goal_status", {})
        status = copy.deepcopy(old)
        eligible = {ident for ident, row in old.items() if row["status"] == "active"
                    and all(old[required]["status"] == "completed" for required in row["requires"])}
        if outcome is not None:
            for ident in eligible:
                row = status[ident]
                units = sum(outcome["executed"].values()) if row["actor"] == "Player" else outcome["executed"][row["actor"]]
                if self.minute <= row["deadline"] and units >= row["quantity"]:
                    row.update(status="completed", updated_at=self.minute,
                               completed_at=self.minute, evidence_event=parent, executed_units=units)
        for ident, row in status.items():
            if row["status"] in {"completed", "missed"}:
                continue
            current = "missed" if self.minute >= row["deadline"] else "active" if all(
                status[required]["status"] == "completed" for required in row["requires"]) else "blocked"
            if current != row["status"]:
                row.update(status=current, updated_at=self.minute)
        changed = {row["actor"] for ident, row in status.items() if row != old[ident]}
        if changed:
            self.put("goal_status", status, "goal_revision", "Recorded settlements and deadlines revise the declared project register", ("Player", *TEAMS),
                     parents=() if parent is None else (parent,))
        return changed

    def _goals(self, actor):
        status = self.get("goal_status", {})
        configured = [g for g in self.spec["goals"] if g["actor"] == actor]
        active = sorted((g for g in configured if status[g["id"]]["status"] == "active"),
                        key=lambda g: (-g["priority"], g["deadline"], g["id"]))
        if active:
            return [Goal(g["id"], g["label"], g["priority"], g["deadline"],
                         relevant_keys=(("observatory", "condition"),), tags=("coordination",))
                    for g in active[:self.minds[actor].config.max_goals]]
        if any(status[g["id"]]["status"] == "blocked" for g in configured):
            return []
        # Continuing institutional work is distinct from claiming that an
        # expired/completed authored project renewed itself.
        return [Goal(f"routine-{actor}-{self.round}", "Perform the consortium's regular instrument work", 1,
                     (self.round + 1) * self.rules["round_minutes"] - 1,
                     relevant_keys=(("observatory", "condition"),), tags=("coordination",))]

    def _decide(self, actor):
        mind = self.minds[actor]
        goals = self._goals(actor)
        gid = goals[0].goal_id if goals else None
        declared = next((g for g in self.spec["goals"] if g["id"] == gid), None)
        quota = declared["target"]["quantity"] if declared else self.rules["quota"]
        options = [
            ActionOption("reserve_full", "Request a full research slot", 3, gid,
                         conditions=(BeliefCondition("observatory", "condition", "stable", max_age=self.rules["round_minutes"], allow_direct=True),)),
            ActionOption("reserve_cautious", "Request a reduced slot under a fragile condition", 2, gid,
                         conditions=(BeliefCondition("observatory", "condition", "fragile", max_age=self.rules["round_minutes"], allow_direct=True),)),
            ActionOption("inspect", "Buy a current direct systems check", 1, gid, costs={"credits": self.rules["inspection_cost"]}),
            ActionOption("wait", "Wait without an unsupported request", 0),
        ]
        if not goals:
            options = [options[-1]]  # a blocked project cannot request work
        trace = mind.cycle([], goals, options, {"credits": self.economy.cash[actor]}, self.minute)
        decision = mind.last_decision
        choice = decision.action_id
        event = self.emit("decision", f"{actor} chooses {choice or 'wait'} from its retained information", (actor,), scope="private",
                          decision=asdict(decision), parents=decision.evidence_ids)
        self.decisions.append({"event_id": event.event_id, "actor": actor, "at": self.minute, **asdict(decision)})
        if choice == "inspect":
            receipt = self.execute({"action": "inspect", "actor": actor})
        elif choice in ("reserve_full", "reserve_cautious"):
            receipt = self.execute({"action": "reserve", "actor": actor, "quantity": quota if choice == "reserve_full" else max(1, quota // 2)})
        else:
            receipt = event
        mind.evaluate(choice, "succeeded", now=self.minute, evidence_ids=(receipt.event_id,) if receipt.event_id in mind.retained_event_ids() else ())
        return trace

    def on_task(self, task):
        kind = task["kind"]
        if kind == "round_start":
            self._round_start()
        elif kind == "coordination_review":
            for actor in TEAMS:
                self._decide(actor)
        elif kind == "allocation_due":
            self._settle()
        elif kind == "declared_opportunity":
            self._declared_opportunity(task["data"]["index"])
        elif kind == "goal_deadline":
            changed = self._refresh_goals()
            # At day boundaries, round_start already provides the next decision
            # after updating the hardware report. Mid-round expiry needs review.
            if self.minute % self.rules["round_minutes"]:
                for actor in TEAMS:
                    if actor in changed:
                        self._decide(actor)
        else:
            raise ValueError("Unknown compiled coordination task")

    def execute(self, action):
        kind, actor = action.get("action"), action.get("actor", "Player")
        if actor not in ("Player", *TEAMS):
            raise ValueError("Unknown actor")
        r = self.round
        allowed_fields = {"reserve": {"action", "actor", "quantity"}, "release": {"action", "actor"},
                          "inspect": {"action", "actor"}, "share": {"action", "actor", "recipient", "event_id"},
                          "allocate": {"action", "actor", "allocation"}, "commit": {"action", "actor", "recipient", "quantity"}}
        if kind not in allowed_fields or set(action) - allowed_fields[kind]:
            raise ValueError("Unsupported action or fields")
        if kind == "inspect":
            fee = self.rules["inspection_cost"]
            if self.economy.cash[actor] < fee:
                raise ValueError("Insufficient owned credits")
            payment = self.emit("inspection_paid", f"{actor} funds a direct inspection", (actor,), scope="private",
                                cash_delta={actor: -fee, "consortium": fee})
            condition = self.state.facts["observatory.condition"]
            return self.emit("condition", f"{actor} directly checks the instrument", (actor,), scope="private", parents=(payment.event_id,),
                             prop=["observatory", "condition"], value=condition)
        if kind == "share":
            recipient, eid = action.get("recipient"), action.get("event_id")
            if actor == "Player" and eid is None and recipient in TEAMS:
                mind = self.minds[recipient]
                belief = mind.believe("observatory", "condition", now=self.minute)
                retained = mind.retained_event_ids()
                candidates = [i for i in belief.evidence_ids if i in retained and self.ledger.events[i].payload.get("prop") == ["observatory", "condition"]]
                if not candidates:
                    raise ValueError("This team has no retained direct report it can disclose; request a fresh inspection")
                return self.execute({"action": "share", "actor": recipient, "recipient": "Player", "event_id": candidates[-1]})
            if recipient not in self.visible or recipient == actor or type(eid) is not int or eid not in self.visible[actor]:
                raise ValueError("A report must use the sender's legitimately observed event")
            if actor in self.minds and eid not in self.minds[actor].retained_event_ids():
                raise ValueError("An NPC cannot retrieve a forgotten report from the archive")
            source = self.ledger.events[eid]
            if source.payload.get("prop") != ["observatory", "condition"]:
                raise ValueError("Only an actual condition report can be shared")
            event = self._emit(self.minute, "tell", "council", (actor, recipient), "report", f"{actor} shares a dated condition report with {recipient}",
                               (eid,), "private", speaker=actor, listener=recipient, report_event=eid,
                               prop=["observatory", "condition"], as_of=source.payload.get("as_of", source.tick),
                               value=source.payload["value"], origin_event=source.payload.get("origin_event", eid),
                               origin_observer=source.payload.get("origin_observer", actor))
            return event
        if kind in ("reserve", "release"):
            if actor not in TEAMS:
                raise ValueError("Only a research team reserves its own request")
            quantity = 0 if kind == "release" else action.get("quantity")
            if type(quantity) is not int or not 0 <= quantity <= self.rules["capacity"]:
                raise ValueError("Request must fit the declared instrument capacity")
            requests = self.get(f"requests:{r}", {})
            requests[actor] = quantity
            return self.put(f"requests:{r}", requests, "request", f"{actor} requests {quantity} capacity units", (actor,))
        if actor != "Player":
            raise ValueError("Only the elected participant coordinates allocations and promises")
        if kind == "commit":
            recipient, quantity = action.get("recipient"), action.get("quantity")
            if recipient not in TEAMS or type(quantity) is not int or not 1 <= quantity <= self.rules["capacity"]:
                raise ValueError("Invalid promise")
            promises = self.get(f"promises:{r}", {})
            if recipient in promises:
                raise ValueError("A promise to this team already exists in this round")
            if sum(promises.values()) + quantity > self.rules["capacity"]:
                raise ValueError("Promises cannot exceed nominal capacity")
            promises[recipient] = quantity
            return self.put(f"promises:{r}", promises, "promise", f"Player promises {quantity} units to {recipient}", (actor, recipient))
        allocation = action.get("allocation")
        if not isinstance(allocation, dict) or set(allocation) != set(TEAMS) or any(type(x) is not int or x < 0 for x in allocation.values()):
            raise ValueError("Provide a nonnegative integer allocation for all three teams")
        if sum(allocation.values()) > self.rules["capacity"]:
            raise ValueError("Allocation exceeds declared capacity")
        if self.get(f"allocation:{r}") is not None:
            raise ValueError("The current allocation is already committed")
        return self.put(f"allocation:{r}", allocation, "institution_decision", f"The coordinator commits round {r + 1}'s allocation", ("Player", *TEAMS))

    def _settle(self):
        r = self.round
        if self.get(f"outcome:{r}") is not None:
            raise ValueError("Allocation cannot settle twice")
        allocation = self.get(f"allocation:{r}", {a: 0 for a in TEAMS})
        capacity = self.rules["capacity"] if self.state.facts["observatory.condition"] == "stable" else max(1, self.rules["capacity"] * 2 // 3)
        remaining, delivered = capacity, {}
        # Allocation order is public, fixed and disclosed; it is not a fair optimum.
        for team in TEAMS:
            delivered[team] = min(allocation[team], remaining)
            remaining -= delivered[team]
        fulfilled = [a for a in TEAMS if delivered[a] >= self.rules["quota"]]
        record = {"allocation": allocation, "executed": delivered, "actual_capacity": capacity, "completed": fulfilled}
        outcome = self.put(f"outcome:{r}", record,
                           "allocation_settled", f"Round {r + 1} executes {sum(delivered.values())}/{sum(allocation.values())} allocated units; {len(fulfilled)} projects complete", ("Player", *TEAMS))
        self._refresh_goals(record, outcome.event_id)
        for team, quantity in self.get(f"promises:{r}", {}).items():
            kept = delivered[team] >= quantity
            old = self.state.trust.get((team, "Player"), .5)
            trust = max(0, min(1, old + (.05 if kept else -.1)))
            self.emit("promise_kept" if kept else "promise_missed", f"The promise to {team} is {'kept' if kept else 'missed'}", ("Player", team),
                      parents=(outcome.event_id,), relationship_updates=[{"listener": team, "speaker": "Player", "value": trust}])
        total = self.metrics()["completed_projects"]
        if total >= 6 and self.get("affiliation") != "consortium_member":
            self.put("affiliation", "consortium_member", "membership", "Recorded completed projects qualify the coordinator for consortium membership", ("Player",), parents=(outcome.event_id,))

    def metrics(self):
        outcomes = [json.loads(value) for key, value in self.state.facts.items() if key.startswith("experience.outcome:")]
        events = self.ledger.events
        return {"rounds_settled": len(outcomes), "completed_projects": sum(len(o["completed"]) for o in outcomes),
                "executed_units": sum(sum(o["executed"].values()) for o in outcomes),
                "allocated_units": sum(sum(o["allocation"].values()) for o in outcomes),
                "promises_kept": sum(e.payload.get("category") == "promise_kept" for e in events),
                "promises_missed": sum(e.payload.get("category") == "promise_missed" for e in events),
                "credits_spent": self.economy.cash["consortium"], "credit_total": sum(self.economy.cash.values()),
                "initial_credit_total": self._initial_cash, "affiliation": self.get("affiliation", "visitor")}

    def fidelity_state(self):
        return {"minute": self.minute, "state": asdict(self.state), "accounts": dict(self.economy.cash), "clock": self.clock.snapshot(),
                "minds": {a: m.to_dict() for a, m in self.minds.items()}, "decisions": copy.deepcopy(self.decisions), "ledger": self.ledger.content_hash()}

