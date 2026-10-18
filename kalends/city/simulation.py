"""Live event-sourced city with local memories and exact continuation forks.

Policies receive only an agent's Experience stream. Truth is used by the world
for observations and consequences and by evaluator metadata after the choice.
"""
from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Callable, Optional

from ..epistemic import EpistemicState
from ..events import Ledger, WorldEvent
from ..memory.base import Experience
from ..observation import observers_of
from ..propositions import Proposition, Provenance
from ..rng import det_choice, det_rand, det_randint
from ..world import WorldState, apply_event
from .policy import StructuredCityPolicy, current_evidence, root_of
from .scenario import CityConfig, LOCATIONS, build_agents, initial_inventory, supply_at

SUPPLY = Proposition("grain", "supply")
RESERVE = Proposition("grain", "reserve")


@dataclass
class CityEconomy:
    cash: dict[str, float] = field(default_factory=dict)
    inventory: dict[str, int] = field(default_factory=dict)
    market_stock: int = 0
    price: float = 4.0
    commitments: dict[str, list[dict]] = field(default_factory=dict)
    relationships: dict[tuple[str, str], float] = field(default_factory=dict)

    def apply(self, event: WorldEvent) -> None:
        """The economy is a projection of explicit effects in canonical events."""
        payload = event.payload
        if payload.get("category") == "city_initialized":
            self.cash = dict(payload["cash"])
            self.inventory = dict(payload["inventory"])
            self.commitments = copy.deepcopy(payload["commitments"])
        for agent, amount in payload.get("cash_delta", {}).items():
            self.cash[agent] = round(self.cash.get(agent, 0) + amount, 2)
        for agent, amount in payload.get("inventory_delta", {}).items():
            self.inventory[agent] = self.inventory.get(agent, 0) + amount
        self.market_stock += payload.get("market_stock_delta", 0)
        if "price" in payload:
            self.price = float(payload["price"])
        for update in payload.get("commitment_updates", []):
            for commitment in self.commitments[update["agent"]]:
                if commitment["id"] == update["id"]:
                    commitment.update(update)
        for update in payload.get("relationship_updates", []):
            self.relationships[(update["listener"], update["speaker"])] = update["value"]


class CitySimulation:
    def __init__(self, config: Optional[CityConfig] = None,
                 policy_factory: Optional[Callable] = None):
        self.config = config or CityConfig()
        self.specs, self.roles = build_agents(self.config)
        self.agent_ids = [a.agent_id for a in self.specs]
        self.ledger = Ledger()
        self.state = WorldState(agent_locations={a.agent_id: a.home for a in self.specs})
        self.economy = CityEconomy()
        self.epistemic = {a: EpistemicState(a) for a in self.agent_ids}
        self.experiences: dict[str, list[Experience]] = {a: [] for a in self.agent_ids}
        self.decisions: list[dict] = []
        self.tick = -1
        self.branch_id = "main"
        self.parent_tick = None
        self._pending: list[dict] = []
        self._verifications: list[dict] = []
        self._supply_event: Optional[int] = None
        self._price_event: Optional[int] = None
        self._stock_event: Optional[int] = None
        self._sent: set[tuple] = set()
        self._policies = {}
        for agent in self.agent_ids:
            if policy_factory is not None:
                try:
                    self._policies[agent] = policy_factory(agent, self.config)
                except TypeError:
                    self._policies[agent] = policy_factory(agent)
            else:
                try:
                    from ..actionbench.policy import MemoryDecisionPolicy
                except ImportError:
                    self._policies[agent] = StructuredCityPolicy(agent, self.config)
                else:
                    self._policies[agent] = MemoryDecisionPolicy(
                        self.config.memory, self.config.gate, self.config.threshold,
                        self.config.capacity)
        commitments = {
            a: [{"id": f"{a}:delivery:{due}", "deadline": due, "quantity": 3,
                 "status": "open", "fulfilled": 0} for due in (8, 16, 23)
                if due < self.config.n_ticks] for a in self.agent_ids}
        self._emit(-1, "state_change", "forum", (), "city_initialized",
                   "The district opens its grain accounts", scope="private",
                   cash={a: float(det_randint(85, 115, self.config.seed, "city-cash", a))
                         for a in self.agent_ids},
                   inventory={a: initial_inventory(self.config, a) for a in self.agent_ids},
                   commitments=commitments)

    @property
    def done(self) -> bool:
        return self.tick >= self.config.n_ticks - 1

    @property
    def messages(self) -> list[dict]:
        return copy.deepcopy(self._pending)

    def _emit(self, tick, etype, location, actors, category, title,
              parents=(), scope="public", **payload) -> WorldEvent:
        parents = list(parents)
        if payload.get("market_stock_delta") and self._stock_event is not None:
            parents.append(self._stock_event)
        payload.update(category=category, title=title,
                       semantic_key=payload.pop("semantic_key", f"{category}:{tick}:{':'.join(actors)}"),
                       parents=sorted(set(p for p in parents if p is not None)))
        event = self.ledger.append(tick, etype, location, tuple(actors), payload, scope)
        apply_event(self.state, event)
        self.economy.apply(event)
        if payload.get("market_stock_delta"):
            self._stock_event = event.event_id
        for update in payload.get("relationship_updates", []):
            self.state.trust[(update["listener"], update["speaker"])] = update["value"]
        return event

    def _move(self, agent, target, tick, reason="daily route", parents=()):
        origin = self.state.agent_locations[agent]
        if origin == target:
            return None
        event = self._emit(tick, "move", target, (agent,), "movement",
                           f"{agent} walks to {target.replace('_', ' ')}", parents=parents,
                           to=target, origin=origin, reason=reason)
        self.experiences[agent].append(Experience(
            tick=tick, kind="episodic", subject=None, predicate=None, value=None,
            source_agent=None, as_of=tick, accepted=True, event_id=event.event_id,
            text=f"At hour {tick} I walked to {target.replace('_', ' ')} for {reason}."))
        return event

    def _observe(self, agent, event, prop=SUPPLY, value=None):
        value = event.payload["value"] if value is None else value
        self.epistemic[agent].record_observation(event.tick, prop, value, event.event_id)
        self.experiences[agent].append(Experience(
            tick=event.tick, kind="observed", subject=prop.subject,
            predicate=prop.predicate, value=value, source_agent=None,
            as_of=event.tick, accepted=True, event_id=event.event_id,
            claimed_origin_kind="observed", claimed_origin_event=event.event_id,
            claimed_origin_observer=agent,
            text=f"At hour {event.tick} I personally inspected {prop.subject} {prop.predicate}: {value}."))
        if prop == SUPPLY:
            self._update_relationships(agent, value, event)

    def _update_relationships(self, agent, value, observation):
        # First-hand checking has social consequences for recent informants.
        latest_by_speaker = {}
        for exp in self.experiences[agent]:
            if exp.kind == "told" and exp.subject == "grain" and exp.predicate == "supply":
                if exp.as_of == observation.tick or observation.tick - exp.as_of <= 5:
                    latest_by_speaker[exp.source_agent] = exp
        for speaker, exp in sorted(latest_by_speaker.items()):
            if speaker not in self.agent_ids:
                continue
            old = self.state.trust.get((agent, speaker), 0.6)
            trust = round(max(0.05, min(0.95, old + (0.08 if exp.value == value else -0.22))), 2)
            self._emit(observation.tick, "state_change", self.state.agent_locations[agent],
                       (agent, speaker), "relationship",
                       f"{agent} {'trusts' if exp.value == value else 'distrusts'} {speaker} after checking",
                       parents=(exp.event_id, observation.event_id), scope="private",
                       relationship_updates=[{"listener": agent, "speaker": speaker, "value": trust}],
                       verified_claim=exp.event_id, matched=exp.value == value)

    def _movement(self, tick):
        verifying = {v["agent"] for v in self._verifications if v["tick"] == tick}
        for spec in self.specs:
            target = "granary" if spec.agent_id in verifying else spec.intended_location(tick)
            if spec.agent_id not in verifying and det_rand(self.config.seed, "city-jitter", tick, spec.agent_id) < .12:
                target = det_choice([x["id"] for x in LOCATIONS], self.config.seed,
                                    "city-route", tick, spec.agent_id)
            self._move(spec.agent_id, target, tick,
                       "a booked grain inspection" if spec.agent_id in verifying else "daily route")

    def _world(self, tick):
        truth = supply_at(self.config, tick)
        if tick == 0 or truth != self.state.facts.get(SUPPLY.key) or tick % 7 == 0:
            official = "Flavia" if "Flavia" in self.agent_ids else self.agent_ids[-1]
            self._move(official, "granary", tick, "inspecting incoming grain deliveries")
            public = self.config.family != "private"
            event = self._emit(tick, "state_change", "granary", (official,), "supply",
                               f"Grain deliveries are {truth}", parents=(self._supply_event,),
                               scope="public" if public else "private",
                               prop=["grain", "supply"], value=truth,
                               market_stock_delta=22 if truth == "available" else 6,
                               semantic_key=f"supply:{tick}")
            self._supply_event = event.event_id
            for agent in observers_of(event, self.state, self.agent_ids):
                self._observe(agent, event)
        if tick == 0:
            owner = "Gaius" if "Gaius" in self.agent_ids else self.agent_ids[-1]
            private = self._emit(tick, "state_change", "house_of_gaius", (owner,),
                                 "private_reserve", f"{owner} inspects a household reserve",
                                 scope="private", prop=["grain", "reserve"], value="available")
            self._observe(owner, private, RESERVE)
        price = (10 if truth == "disrupted" else 4) + max(0, 12 - self.economy.market_stock) * .25
        if price != self.economy.price or tick == 0:
            event = self._emit(tick, "state_change", "forum", (), "price",
                       f"Posted grain price is {price:g} denarii", parents=(self._supply_event,),
                       prop=["grain", "price"], value=str(price), price=price)
            self._price_event = event.event_id

    def _verification(self, tick):
        due = [v for v in self._verifications if v["tick"] == tick]
        self._verifications = [v for v in self._verifications if v["tick"] != tick]
        for visit in due:
            self._verify_now(visit["agent"], tick, (visit["decision_event"],), "inspection")

    def _verify_now(self, agent, tick, parents=(), category="inspection"):
        movement = self._move(agent, "granary", tick, "checking the grain yard", parents)
        parent_ids = list(parents) + [self._supply_event]
        if movement is not None:
            parent_ids.append(movement.event_id)
        event = self._emit(tick, "state_change", "granary", (agent,), category,
                           f"{agent} verifies grain deliveries are {self.state.facts[SUPPLY.key]}",
                           parents=parent_ids, scope="private", prop=["grain", "supply"],
                           value=self.state.facts[SUPPLY.key], verification=True)
        self._observe(agent, event)
        return event

    def _hear(self, event, report):
        listener, speaker = report["listener"], report["speaker"]
        old = self.epistemic[listener].belief(SUPPLY)
        trust = self.state.trust.get((listener, speaker), .6)
        origin = Provenance(kind="told", event_id=report["root_event"],
                            source_agent=report["root_source"],
                            upstream=(Provenance(kind="observed", event_id=report["root_event"])
                                      if report.get("root_kind", "observed") == "observed" else None))
        exp = self.epistemic[listener].record_told(
            event.tick, SUPPLY, report["value"], event.event_id, speaker,
            report["as_of"], origin, trust)
        same_claim = (trust >= .3 and old is not None and old.as_of == report["as_of"]
                      and old.value == report["value"])
        annotation = (" [trusted corroboration: same claim, no new origin]" if same_claim
                      else "" if exp.accepted else " I did not believe this older or untrusted claim.")
        self.experiences[listener].append(Experience(
            tick=event.tick, kind="told", subject="grain", predicate="supply",
            value=report["value"], source_agent=speaker, as_of=report["as_of"],
            accepted=exp.accepted, event_id=event.event_id,
            claimed_origin_kind=report.get("root_kind", "observed"),
            claimed_origin_event=report["root_event"],
            claimed_origin_observer=report["root_source"],
            text=f"At hour {event.tick} {speaker} told me grain supply was {report['value']} "
                 f"as of hour {report['as_of']}; origin {report['root_source']} "
                 f"at event {report['root_event']}." + annotation))

    def _queue(self, tick, speaker, listener, exp, depth=1, delay=None):
        if depth > self.config.communication_depth:
            return None
        if delay is None:
            delay = det_randint(1, 3, self.config.seed, "city-message-delay", tick, speaker, listener)
        root = root_of(exp)
        event = self._emit(tick, "state_change", self.state.agent_locations[speaker],
                           (speaker, listener), "message_queued",
                           f"{speaker} sends a grain report to {listener}",
                           parents=(exp.event_id,), scope="private",
                           speaker=speaker, listener=listener, proposition=["grain", "supply"],
                           value=exp.value, as_of=exp.as_of, delivery_tick=tick + delay,
                           root_event=root[1], root_source=root[2], root_kind=root[0], depth=depth,
                           semantic_key=f"message:{tick}:{speaker}:{listener}:{exp.as_of}:{depth}")
        report = {k: copy.deepcopy(v) for k, v in event.payload.items()}
        report.update(event_id=event.event_id, sent_tick=tick)
        self._pending.append(report)
        return event

    def _scripted_reports(self, tick):
        if self.config.family == "private" or self.config.communication_depth == 0:
            return
        if tick == 1:
            courier = "Dama" if "Dama" in self.agent_ids else self.agent_ids[0]
            # A stale manifest is information, never a change to actual supply.
            value = "available" if supply_at(self.config, 0) == "disrupted" else "disrupted"
            event = self._emit(tick, "tell", "harbour", (courier,), "outdated_manifest",
                               f"{courier} receives an outdated harbour manifest", scope="private",
                               speaker="Manifest clerk", listener=courier,
                               prop=["grain", "supply"], value=value, as_of=0,
                               outdated=True, root_source="harbour manifest")
            report = dict(speaker="Manifest clerk", listener=courier, value=value, as_of=0,
                          root_event=event.event_id, root_source="harbour manifest", root_kind="told")
            self._hear(event, report)
            exp = self.experiences[courier][-1]
            for target, delay in (("Livia", 1), ("Marcus", 2)):
                if target in self.agent_ids and target != courier:
                    self._queue(tick, courier, target, exp, delay=delay)

    def _deliver(self, tick):
        due = sorted([m for m in self._pending if m["delivery_tick"] <= tick],
                     key=lambda m: (m["delivery_tick"], m["event_id"]))
        self._pending = [m for m in self._pending if m["delivery_tick"] > tick]
        for message in due:
            speaker, listener = message["speaker"], message["listener"]
            event = self._emit(tick, "tell", self.state.agent_locations[listener],
                               (speaker, listener), "message_delivered",
                               f"{listener} hears from {speaker}: grain {message['value']}",
                               parents=[message["event_id"]] + message.get("parents", []), scope="private",
                               speaker=speaker, listener=listener, prop=["grain", "supply"],
                               value=message["value"], as_of=message["as_of"],
                               root_event=message["root_event"], root_source=message["root_source"],
                               depth=message["depth"], queued_event=message["event_id"])
            self._hear(event, message)

    def _gossip(self, tick):
        # Snapshot the news first: no agent relays a message before receiving it.
        news = {}
        for agent in self.agent_ids:
            current, _ = current_evidence(self.experiences[agent])
            if current is not None and tick - current.tick <= 10:
                depth = self.ledger.events[current.event_id].payload.get("depth", 0)
                if depth < self.config.communication_depth:
                    news[agent] = (current, depth + 1)
        for spec in self.specs:
            if spec.agent_id not in news:
                continue
            exp, depth = news[spec.agent_id]
            colocated = [a for a in self.agent_ids if a != spec.agent_id and
                         self.state.agent_locations[a] == self.state.agent_locations[spec.agent_id]]
            # A person has a finite conversation budget even in a larger city.
            recipients = sorted(colocated, key=lambda a: det_rand(
                self.config.seed, "city-conversation-budget", tick, spec.agent_id, a))[:4]
            for listener in recipients:
                signature = (spec.agent_id, listener, root_of(exp), exp.value, exp.as_of)
                if signature in self._sent:
                    continue
                if det_rand(self.config.seed, "city-gossip", tick, spec.agent_id, listener) < spec.chattiness:
                    self._queue(tick, spec.agent_id, listener, exp, depth)
                    self._sent.add(signature)

    def _decision_phase(self, tick):
        if tick % 3 != 2 and tick != self.config.n_ticks - 1:
            return
        for agent in self.agent_ids:
            upcoming = [c for c in self.economy.commitments[agent] if c["status"] == "open"]
            need = 3 if not upcoming else upcoming[0]["quantity"]
            valid = self.economy.inventory[agent] < need
            if not valid:
                continue
            # The callback gets no simulation/world/epistemic object.
            choice = dict(self._policies[agent].decide(list(self.experiences[agent]), tick, agent))
            action = choice.get("action", "verify")
            prediction = choice.get("predicted_value", "unknown")
            if action not in ("reserve", "defer", "verify"):
                raise ValueError(f"policy returned invalid city action {action!r}")
            if prediction not in ("available", "disrupted", "unknown"):
                raise ValueError(f"policy returned invalid supply prediction {prediction!r}")
            local_ids = {e.event_id for e in self.experiences[agent]}
            evidence_ids = list(dict.fromkeys(choice.get("evidence_ids", [])))
            if any(e not in local_ids for e in evidence_ids):
                raise ValueError("policy evidence must have reached that agent")
            actual = self.state.facts[SUPPLY.key]  # evaluator/world consequence only
            loss = 1.5 if action == "verify" else (2.0 if action == "reserve" and actual == "available"
                                                  else 6.0 if action == "defer" and actual == "disrupted" else 0.0)
            has_heard_supply = any(e.subject == "grain" and e.predicate == "supply"
                                   for e in self.experiences[agent])
            boundary = bool(choice.get("boundary_violation", False) or
                            (prediction != "unknown" and not has_heard_supply))
            decision = dict(choice)
            decision.update(agent=agent, tick=tick, action=action, predicted_value=prediction,
                            actual_value=actual, loss=loss, regret=loss, autonomous=action == "reserve",
                            opportunity_valid=valid, evidence_ids=evidence_ids,
                            root_count=int(choice.get("root_count", 0)),
                            source_count=int(choice.get("source_count", 0)),
                            boundary_violation=boundary,
                            source_independence_failure=bool(choice.get("source_independence_failure", False)))
            # Actual supply is deliberately absent from the public decision event.
            public_choice = {k: copy.deepcopy(v) for k, v in decision.items()
                             if k not in ("actual_value", "loss", "regret", "qa_expected", "qa_correct")}
            event = self._emit(tick, "state_change", self.state.agent_locations[agent],
                               (agent,), "decision", f"{agent} chooses to {action}",
                               parents=evidence_ids, scope="private", decision=public_choice,
                               semantic_key=f"decision:{tick}:{agent}")
            decision["event_id"] = event.event_id
            self.decisions.append(decision)
            if action == "verify":
                self._emit(tick, "state_change", self.state.agent_locations[agent], (agent,),
                           "inspection_booked", f"{agent} pays for a grain inspection",
                           parents=(event.event_id,), scope="private", cash_delta={agent: -1.5})
                if tick + 1 < self.config.n_ticks:
                    self._verifications.append({"agent": agent, "tick": tick + 1,
                                                "decision_event": event.event_id})
            elif action == "reserve" and valid:
                self._purchase(agent, tick, event)

    def _purchase(self, agent, tick, decision_event):
        movement = self._move(agent, "forum", tick, "reserving grain", (decision_event.event_id,))
        quantity = min(3, self.economy.market_stock,
                       max(0, int(self.economy.cash[agent] // self.economy.price)))
        price = self.economy.price
        parents = [decision_event.event_id, self._price_event, self._supply_event]
        if movement is not None:
            parents.append(movement.event_id)
        event = self._emit(tick, "state_change", "forum", (agent,), "purchase",
                           f"{agent} reserves {quantity} grain for {quantity * price:g} denarii",
                           parents=parents, quantity=quantity, unit_price=price,
                           cash_delta={agent: -quantity * price}, inventory_delta={agent: quantity},
                           market_stock_delta=-quantity, commitment="grain reservation")
        self.experiences[agent].append(Experience(
            tick=tick, kind="episodic", subject=None, predicate=None, value=None,
            source_agent=None, as_of=tick, accepted=True, event_id=event.event_id,
            text=f"I reserved {quantity} measures of grain at {price:g} denarii each."))

    def _settle(self, tick):
        for agent in self.agent_ids:
            for commitment in self.economy.commitments[agent]:
                if commitment["status"] != "open" or commitment["deadline"] != tick:
                    continue
                quantity = min(commitment["quantity"], self.economy.inventory[agent])
                missing = commitment["quantity"] - quantity
                parents = [d["event_id"] for d in self.decisions if d["agent"] == agent][-3:]
                self._emit(tick, "state_change", self.state.agent_locations[agent], (agent,),
                           "commitment_settled", f"{agent} {'misses' if missing else 'fulfills'} a grain delivery",
                           parents=parents, scope="private", inventory_delta={agent: -quantity},
                           cash_delta={agent: quantity * 3 - missing * 5},
                           missing=missing, quantity=quantity,
                           commitment_updates=[{"agent": agent, "id": commitment["id"],
                                                "status": "missed" if missing else "fulfilled",
                                                "fulfilled": quantity}])

    def step(self, count=1):
        if type(count) is not int or count < 0:
            raise ValueError("step count must be a nonnegative integer")
        for _ in range(count):
            if self.done:
                break
            tick = self.tick + 1
            self._movement(tick)
            self._world(tick)
            self._verification(tick)
            self._scripted_reports(tick)
            self._deliver(tick)
            self._gossip(tick)
            self._decision_phase(tick)
            self._settle(tick)
            self.tick = tick
        return self

    def run(self):
        return self.step(max(0, self.config.n_ticks - 1 - self.tick))

    def fork(self, intervention):
        intervention = dict(intervention or {"kind": "none"})
        kind = intervention.get("kind", "none")
        if kind not in ("none", "correction", "remove_message", "replace_message"):
            raise ValueError("unknown intervention kind")
        target = intervention.get("agent")
        event_id = intervention.get("event_id")
        if kind == "correction":
            if target not in self.agent_ids:
                raise ValueError("correction target must be an existing agent")
            if self._supply_event is None:
                raise ValueError("run at least one tick before verifying supply")
            value = intervention.get("value", self.state.facts[SUPPLY.key])
            if value != self.state.facts[SUPPLY.key]:
                raise ValueError("a verified correction must match the locally inspected supply")
        if kind in ("remove_message", "replace_message"):
            if not any(m["event_id"] == event_id for m in self._pending):
                raise ValueError("message intervention must target a pending delivery")
            if kind == "replace_message" and intervention.get("value") not in ("available", "disrupted"):
                raise ValueError("replacement must be available or disrupted")
        branch = copy.deepcopy(self)
        branch.parent_tick = self.tick
        digest = hashlib.sha256(json.dumps(intervention, sort_keys=True).encode()).hexdigest()[:8]
        branch.branch_id = f"fork-{self.tick}-{digest}"
        if kind == "correction":
            branch._verify_now(target, self.tick, category="intervention_correction")
        elif kind in ("remove_message", "replace_message"):
            message = next(m for m in branch._pending if m["event_id"] == event_id)
            if kind == "remove_message":
                branch._pending.remove(message)
            else:
                message["value"] = intervention["value"]
            event = branch._emit(self.tick, "state_change", "forum", (), f"intervention_{kind}",
                                 f"A queued message is {'removed' if kind == 'remove_message' else 'replaced'}",
                                 parents=(event_id,), scope="private", target_event=event_id,
                                 replacement=intervention.get("value"))
            if kind == "replace_message":
                # The changed report is a new provenance root, not a false claim
                # that the original witness asserted a different value.
                message.update(root_event=event.event_id, root_source="message intervention",
                               root_kind="told", parents=[event.event_id])
        return branch

    def _beliefs(self, agent):
        result = {}
        for key in sorted(self.epistemic[agent].exposures):
            subject, predicate = key.rsplit(".", 1)
            current = self.epistemic[agent].belief(Proposition(subject, predicate))
            if current is None:
                continue
            eligible = [e for e in self.experiences[agent] if e.subject == subject and
                        e.predicate == predicate and e.as_of == current.as_of and e.value == current.value
                        and (e.accepted or "[trusted corroboration:" in e.text)]
            result[key] = {"value": current.value, "as_of": current.as_of, "tick": current.tick,
                           "evidence_ids": [e.event_id for e in eligible],
                           "root_count": len({root_of(e) for e in eligible}),
                           "source_count": len({e.source_agent or agent for e in eligible})}
        return result

    def _event_dict(self, event):
        result = event.to_dict()
        result.update(category=event.payload.get("category"), title=event.payload.get("title"),
                      parents=list(event.payload.get("parents", [])))
        return result

    def snapshot(self):
        valid = [d for d in self.decisions if d["opportunity_valid"]]
        metrics = {"decision_count": len(self.decisions), "valid_opportunities": len(valid),
                   "total_loss": sum(d["loss"] for d in valid),
                   "total_regret": sum(d["regret"] for d in valid),
                   "mean_loss": sum(d["loss"] for d in valid) / max(1, len(valid)),
                   "correct_predictions": sum(d["predicted_value"] == d["actual_value"] for d in self.decisions),
                   "boundary_violations": sum(d["boundary_violation"] for d in self.decisions),
                   "source_independence_failures": sum(d["source_independence_failure"] for d in self.decisions),
                   "reserves": sum(d["action"] == "reserve" for d in self.decisions),
                   "verifications": sum(d["action"] == "verify" for d in self.decisions),
                   "missed_commitments": sum(c["status"] == "missed" for cs in self.economy.commitments.values() for c in cs),
                   "ledger_hash": self.ledger.content_hash()}
        return {"config": asdict(self.config), "tick": self.tick, "done": self.done,
                "branch_id": self.branch_id, "parent_tick": self.parent_tick,
                "locations": copy.deepcopy(list(LOCATIONS)),
                "agents": [{"id": a, "name": a, "role": self.roles[a],
                            "location": self.state.agent_locations[a],
                            "cash": self.economy.cash[a], "inventory": self.economy.inventory[a],
                            "beliefs": self._beliefs(a),
                            "experiences": [asdict(e) for e in self.experiences[a][-30:]],
                            "goals": ["Meet grain deliveries", "Protect cash", "Check costly claims"],
                            "commitments": copy.deepcopy(self.economy.commitments[a]),
                            "decisions": copy.deepcopy([d for d in self.decisions if d["agent"] == a])}
                           for a in self.agent_ids],
                "world": {"facts": dict(self.state.facts), "price": self.economy.price,
                          "supply": self.state.facts.get(SUPPLY.key, "unknown"),
                          "inventory": self.economy.market_stock,
                          "market_stock": self.economy.market_stock,
                          "total_agent_inventory": sum(self.economy.inventory.values()),
                          "relationships": [{"listener": a, "speaker": b, "trust": v}
                                            for (a, b), v in sorted(self.economy.relationships.items())]},
                "events": [self._event_dict(e) for e in self.ledger.events],
                "messages": self.messages, "decisions": copy.deepcopy(self.decisions),
                "metrics": metrics}

    def compare(self, other):
        agents, beliefs = [], []
        for agent in self.agent_ids:
            changes = {}
            for field_name, ours, theirs in (
                    ("location", self.state.agent_locations.get(agent), other.state.agent_locations.get(agent)),
                    ("cash", self.economy.cash.get(agent), other.economy.cash.get(agent)),
                    ("inventory", self.economy.inventory.get(agent), other.economy.inventory.get(agent)),
                    ("commitments", self.economy.commitments.get(agent), other.economy.commitments.get(agent))):
                if ours != theirs:
                    changes[field_name] = {"baseline": copy.deepcopy(ours), "branch": copy.deepcopy(theirs)}
            if changes:
                agents.append({"agent": agent, "changes": changes})
            our_beliefs, their_beliefs = self._beliefs(agent), other._beliefs(agent)
            for prop in sorted(set(our_beliefs) | set(their_beliefs)):
                # Event IDs shift after intervention; compare actual belief values/times.
                left = {k: v for k, v in our_beliefs.get(prop, {}).items() if k != "evidence_ids"}
                right = {k: v for k, v in their_beliefs.get(prop, {}).items() if k != "evidence_ids"}
                if left != right:
                    beliefs.append({"agent": agent, "prop": prop, "baseline": left, "branch": right})
        our_actions = {(d["tick"], d["agent"]): d for d in self.decisions}
        their_actions = {(d["tick"], d["agent"]): d for d in other.decisions}
        actions = []
        for key in sorted(set(our_actions) | set(their_actions)):
            left, right = our_actions.get(key, {}), their_actions.get(key, {})
            if any(left.get(k) != right.get(k) for k in ("action", "predicted_value", "loss")):
                actions.append({"tick": key[0], "agent": key[1],
                                "baseline": {k: left.get(k) for k in ("action", "predicted_value", "loss")},
                                "branch": {k: right.get(k) for k in ("action", "predicted_value", "loss")}})
        relationships = []
        for pair in sorted(set(self.economy.relationships) | set(other.economy.relationships)):
            left, right = self.economy.relationships.get(pair, .6), other.economy.relationships.get(pair, .6)
            if left != right:
                relationships.append({"listener": pair[0], "speaker": pair[1], "baseline": left, "branch": right})
        messages_changed = self.messages != other.messages
        return {"baseline": self.branch_id, "branch": other.branch_id,
                "tick": self.tick, "branch_tick": other.tick, "agents": agents,
                "beliefs": beliefs, "actions": actions, "relationships": relationships,
                "world": {"baseline": self.snapshot()["world"], "branch": other.snapshot()["world"]},
                "changed_agents": len(agents), "changed_beliefs": len(beliefs),
                "changed_actions": len(actions), "changed_relationships": len(relationships),
                "messages_changed": messages_changed,
                "messages": {"baseline": self.messages, "branch": other.messages},
                "identical": not (agents or beliefs or actions or relationships or messages_changed or
                                  self.state.facts != other.state.facts or
                                  self.economy.market_stock != other.economy.market_stock)}

    def trace(self, event_id):
        if type(event_id) is not int or not 0 <= event_id < len(self.ledger):
            raise ValueError("trace target must be an existing event id")
        seen, links = set(), []
        pending = [event_id]
        while pending:
            target = pending.pop()
            if target in seen:
                continue
            seen.add(target)
            for parent in self.ledger.events[target].payload.get("parents", []):
                if 0 <= parent < target:
                    links.append({"source": parent, "target": target})
                    pending.append(parent)
        events = [self._event_dict(self.ledger.events[i]) for i in sorted(seen)]
        return {"event_id": event_id, "event": self._event_dict(self.ledger.events[event_id]),
                "events": events, "ancestors": [e for e in events if e["event_id"] != event_id],
                "links": links, "root_ids": [i for i in sorted(seen) if not self.ledger.events[i].payload.get("parents")],
                "interpretation": "Structural information ancestry; a parent link alone does not establish causal necessity."}
