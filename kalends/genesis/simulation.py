"""A participant world reusing the historical city's event-sourced machinery.

The archival ledger/Experience streams are for operators and evaluation only.
Every citizen memory query, acceptance decision, conversation view and gossip
uses the same FIFO-retained records. Current owned resources and institutional
trust are durable world state, not a secret factual memory oracle.
"""
from __future__ import annotations

import copy
import json
import math
from dataclasses import asdict

from ..city.simulation import CityEconomy, CitySimulation, SUPPLY
from ..city.scenario import LOCATIONS
from ..epistemic import EpistemicState, Exposure
from ..memory.base import Experience
from ..observation import observers_of
from ..propositions import Provenance
from ..rng import det_choice, det_rand, det_randint
from .config import GenesisConfig
from .evaluation import executed_metrics
from .policy import GenesisPolicy, effective_records, preferences_for, read_knowledge

INSPECTION_FEE = 2.0


class GenesisEconomy(CityEconomy):
    def apply(self, event):
        super().apply(event)
        if "new_commitment" in event.payload:
            commitment = copy.deepcopy(event.payload["new_commitment"])
            self.commitments[event.payload.get("owner", "Player")].append(commitment)


class GenesisSimulation(CitySimulation):
    def __init__(self, config=None, policy_factory=None):
        config = config or GenesisConfig()
        if not isinstance(config, GenesisConfig):
            raise ValueError("GenesisSimulation requires GenesisConfig")
        self._retained = {}
        self.preferences = {}
        self._initial_accounts = {}
        self._last_quote = None
        self._pending_inspections = set()
        super().__init__(config, policy_factory=policy_factory)
        self.economy = GenesisEconomy()
        for event in self.ledger.events:
            self.economy.apply(event)
        self.experiences["Player"] = []
        self.epistemic["Player"] = EpistemicState("Player")
        self._retained = {a: [] for a in self.agent_ids + ["Player"]}
        self.preferences = {a: preferences_for(self.roles[a]) for a in self.agent_ids}
        self.preferences["Player"] = {"caution": .5}
        if policy_factory is None and config.role_policy:
            self._policies = {a: GenesisPolicy(config) for a in self.agent_ids}
        self._emit(-1, "move", "forum", ("Player",), "player_arrived", "The player arrives in the forum",
                   to="forum", scope="public")
        self._initial_accounts = {a: {"cash": self.economy.cash[a], "inventory": self.economy.inventory[a]}
                                  for a in self.agent_ids + ["Player"]}

    def _settlement_dependencies(self, owner):
        """Auditor-only resource checkpoints, never an operational memory query.

        Grain is pooled/fungible. These links record account dependencies and
        contemporaneous procurement choices, not necessary or minimal causes.
        """
        events = self.ledger.events
        checkpoints = [e for e in events if e.payload.get("category") == "commitment_settled"
                       and e.payload.get("owner") == owner]
        checkpoint = checkpoints[-1].event_id if checkpoints else 0
        period = [e for e in events if e.event_id > checkpoint]
        inventory = [e.event_id for e in period if owner in e.payload.get("inventory_delta", {})]
        cash = [e.event_id for e in period if owner in e.payload.get("cash_delta", {})]
        decisions = [e.event_id for e in period if e.payload.get("category") == "decision"
                     and e.actors == (owner,)]
        return checkpoint, inventory, cash, decisions

    def _emit(self, tick, etype, location, actors, category, title, parents=(), scope="public", **payload):
        if category == "commitment_settled":
            owner = payload.get("owner", actors[0])
            checkpoint, inventory, cash, decisions = self._settlement_dependencies(owner)
            parents = list(parents) + [0, checkpoint] + inventory + cash + decisions
            payload.update(accounting_checkpoint=checkpoint,
                           inventory_dependency_events=inventory,
                           cash_dependency_events=cash,
                           procurement_decision_events=decisions,
                           inventory_before_settlement=self.economy.inventory[owner],
                           inventory_allocation="pooled fungible inventory; no per-unit FIFO attribution",
                           dependency_scope="auditor-only period accounts and recorded procurement; not necessary or minimal causes")
        if category == "city_initialized":
            quantities = {"baker": 4, "mill worker": 3, "merchant": 3, "trader": 2,
                          "courier": 1, "porter": 1, "grain official": 1}
            cash = {"merchant": 115, "trader": 135, "baker": 100, "courier": 80,
                    "grain official": 100}
            payload["cash"] = {a: float(cash.get(self.roles[a], 100) +
                                            det_randint(-6, 6, self.config.seed, "genesis-cash", a))
                               for a in self.agent_ids}
            payload["inventory"] = {a: det_randint(0, 2, self.config.seed, "genesis-inventory", a)
                                    for a in self.agent_ids}
            payload["commitments"] = {
                a: [{"id": f"{a}:delivery:{due}", "deadline": due,
                     "quantity": quantities.get(self.roles[a], 2), "status": "open", "fulfilled": 0}
                    for due in range(7, self.config.n_ticks, 8)] for a in self.agent_ids}
            payload["cash"]["Player"] = 75.0
            payload["inventory"]["Player"] = 0
            payload["commitments"]["Player"] = []
        return super()._emit(tick, etype, location, actors, category, title, parents, scope, **payload)

    @property
    def player(self):
        return self.private_view("Player")

    def _participant(self, agent):
        if not isinstance(agent, str) or agent not in self.experiences:
            raise ValueError("unknown participant")

    def _retain(self, agent, exp):
        store = self._retained[agent]
        store.append(exp)
        del store[:-self.config.capacity]

    def _remember(self, agent, exp):
        self.experiences[agent].append(exp)
        self._retain(agent, exp)

    def remembered(self, agent):
        self._participant(agent)
        return list(self._retained[agent])

    def knowledge(self, agent):
        records = self.remembered(agent)
        return {"grain.supply": read_knowledge(records, self.config, getattr(self, "_active_tick", self.tick), agent)}

    def _receipt(self, agent, event, **data):
        self._remember(agent, Experience(
            tick=event.tick, kind="episodic", subject=None, predicate=None, value=None,
            source_agent=None, as_of=event.tick, accepted=True, event_id=event.event_id,
            text="Receipt: " + json.dumps({"event_id": event.event_id, "tick": event.tick, **data}, sort_keys=True)))

    def _receipts(self, agent):
        return [json.loads(e.text[len("Receipt: "):]) for e in self.remembered(agent)
                if e.text.startswith("Receipt: ")]

    def _move(self, agent, target, tick, reason="daily route", parents=()):
        event = super()._move(agent, target, tick, reason, parents)
        if event is not None:
            self._retain(agent, self.experiences[agent][-1])
        return event

    def _movement(self, tick):
        verifying = {v["agent"] for v in self._verifications if v["tick"] == tick}
        for spec in self.specs:
            target = "granary" if spec.agent_id in verifying else spec.intended_location(tick % 24)
            if spec.agent_id not in verifying and det_rand(self.config.seed, "genesis-jitter", tick, spec.agent_id) < .08:
                target = det_choice([loc["id"] for loc in LOCATIONS], self.config.seed,
                                    "genesis-route", tick, spec.agent_id)
            self._move(spec.agent_id, target, tick, "booked inspection" if spec.agent_id in verifying else "daily route")

    def _supply_truth(self, tick):
        if self.config.family == "stable":
            return "available"
        if self.config.family == "scarcity":
            return "available" if tick >= 12 and det_rand(self.config.seed, "genesis-scarcity", tick // 8) < .2 else "disrupted"
        if tick < 4:
            return "available"
        if tick < 12:
            return "disrupted"
        if tick < 20:
            return "available"
        return "available" if det_rand(self.config.seed, "genesis-reversal", tick // 8) < .55 else "disrupted"

    def _world(self, tick):
        truth = self._supply_truth(tick)
        arrival = tick % 8 == 0
        if tick == 0 or truth != self.state.facts.get(SUPPLY.key) or arrival:
            official = "Flavia" if "Flavia" in self.agent_ids else self.agent_ids[-1]
            actors = [official]
            self._move(official, "granary", tick, "checking incoming grain")
            if tick == 0 and "Dama" in self.agent_ids:
                self._move("Dama", "granary", tick, "witnessing the original shipment")
                actors.append("Dama")
            stock = (22 if truth == "available" else 6) if self.config.supply_mode == "fixed" else (
                math.ceil(self.config.n_agents * (2.6 if truth == "available" else .7)))
            event = self._emit(tick, "state_change", "granary", tuple(actors), "supply",
                               f"A local shipment inspection finds deliveries {truth}",
                               parents=(self._supply_event,), prop=["grain", "supply"], value=truth,
                               market_stock_delta=stock if arrival else 0,
                               semantic_key=f"genesis-supply:{tick}", genuine_observation=True)
            self._supply_event = event.event_id
            for agent in observers_of(event, self.state, self.agent_ids + ["Player"]):
                self._observe(agent, event)
            if tick == 0 and "Dama" in self.agent_ids and "Livia" in self.agent_ids:
                # The source is an actual earlier observation. Delivery at six
                # follows the exogenous reversal at four, without invented history.
                exp = next(e for e in self.remembered("Dama") if e.event_id == event.event_id)
                self._queue(tick, "Dama", "Livia", exp, delay=6)
        price = (4.0 if truth == "available" else 10.0) + .5 * det_randint(
            0, 2, self.config.seed, "genesis-price", tick // 4)
        if price != self.economy.price or tick == 0:
            event = self._emit(tick, "state_change", "forum", (), "price",
                               f"The market posts grain at {price:g} denarii", parents=(self._supply_event,),
                               prop=["grain", "price"], value=str(price), price=price,
                               semantic_key=f"genesis-price:{tick}")
            self._price_event = event.event_id
        # Quotes reach only people actually at the market, including the player.
        for agent in self.agent_ids + ["Player"]:
            if self.state.agent_locations.get(agent) == "forum" and tick % 2 == 0:
                quote = self._emit(tick, "state_change", "forum", (agent,), "price_read",
                                   f"{agent} reads the posted grain quote", parents=(self._price_event,),
                                   scope="private", quoted_price=self.economy.price)
                self._remember(agent, Experience(
                    tick=tick, kind="observed", subject="grain", predicate="price",
                    value=str(self.economy.price), source_agent=None, as_of=tick,
                    accepted=True, event_id=quote.event_id,
                    text=f"At hour {tick} I read the public grain price: {self.economy.price:g}."))

    def _observe(self, agent, event, prop=SUPPLY, value=None, assess=True):
        value = event.payload["value"] if value is None else value
        prior = self.remembered(agent)
        self.epistemic[agent].record_observation(event.tick, prop, value, event.event_id)
        self._remember(agent, Experience(
            tick=event.tick, kind="observed", subject=prop.subject, predicate=prop.predicate,
            value=value, source_agent=None, as_of=event.tick, accepted=True, event_id=event.event_id,
            claimed_origin_kind="observed", claimed_origin_event=event.event_id,
            claimed_origin_observer=agent,
            text=f"At hour {event.tick} I personally inspected grain {prop.predicate}: {value}."))
        if prop == SUPPLY and assess:
            self._update_relationships(agent, value, event, prior)

    def _update_relationships(self, agent, value, observation, prior=None, verified_records=None):
        prior = self.remembered(agent) if prior is None else prior
        reports = {}
        for exp in effective_records(prior):
            if exp.kind == "told" and exp.subject == "grain" and exp.predicate == "supply" and exp.accepted:
                if exp.source_agent in self.agent_ids + ["Player"]:
                    reports[exp.source_agent] = exp
        receipts = self._receipts(agent)
        for speaker, exp in sorted(reports.items()):
            root = exp.claimed_origin_event if exp.claimed_origin_event is not None else exp.event_id
            checks = verified_records or {}
            dated = checks.get(exp.as_of)
            checked_value = dated["value"] if dated else value if exp.as_of == observation.tick else None
            if exp.value == "unknown":
                assessment = "incomplete"
            elif checked_value is None:
                assessment = "outdated" if exp.value != value else "not_checked_historically"
            elif checked_value != exp.value:
                assessment = "contradicted"
            else:
                assessment = "truthful_outdated" if exp.value != value else "confirmed"
            earlier = [r for r in receipts if r.get("action") == "assessment" and r.get("claim_root") == root
                       and r.get("claim_as_of") == exp.as_of]
            if any(r.get("assessment") in ("confirmed", "contradicted", "truthful_outdated") for r in earlier):
                continue
            if any(r.get("assessment") == assessment for r in earlier):
                continue
            old = self.state.trust.get((agent, speaker), .6)
            matches = assessment in ("confirmed", "truthful_outdated")
            trust = round(max(.05, min(.95, old + (.06 if matches else -.28 if assessment == "contradicted" else 0))), 2)
            costs = [r for r in receipts if exp.event_id in r.get("evidence_ids", []) and r.get("cash_delta", 0) < 0]
            event = self._emit(observation.tick, "state_change", self.state.agent_locations[agent],
                               (agent,), "relationship",
                               f"{agent} assesses {speaker}'s remembered report: {assessment}",
                               parents=[exp.event_id, observation.event_id] + [r["event_id"] for r in costs] +
                               ([dated["event_id"]] if dated else []),
                               scope="private", relationship_updates=[{"listener": agent, "speaker": speaker, "value": trust}],
                               matched=matches if checked_value is not None else None, assessment=assessment,
                               claim_as_of=exp.as_of, claim_event=exp.event_id, root_event=root,
                               known_cost_events=[r["event_id"] for r in costs],
                               access_allowed=trust >= .35)
            self._remember(agent, Experience(
                tick=observation.tick, kind="episodic", subject="relationship", predicate=speaker,
                value=str(trust), source_agent=speaker, as_of=observation.tick, accepted=True,
                event_id=event.event_id,
                text=f"I checked {speaker}'s report E{exp.event_id} dated {exp.as_of}; my inspection E{observation.event_id} "
                     f"recorded assessment {assessment}. An older report conflicting with now is not proof it was false. "
                     f"My trust is now {trust:.2f}. Recorded cost receipts: {[r['event_id'] for r in costs]}."))
            self._receipt(agent, event, action="assessment", claim_root=root, claim_event=exp.event_id,
                          claim_as_of=exp.as_of, assessment=assessment, trust=trust, cash_delta=0,
                          evidence_ids=[exp.event_id, observation.event_id], description=event.payload["title"])

    def _hear(self, event, report):
        listener, speaker = report["listener"], report["speaker"]
        predicate = report.get("predicate", "supply")
        retraction = predicate == "retraction"
        current = self.knowledge(listener)["grain.supply"]
        trust = self.state.trust.get((listener, speaker), .6)
        as_of = report["as_of"]
        accepted = retraction or (trust >= .3 and (current["as_of"] is None or as_of > current["as_of"] or
                                                  as_of == current["as_of"] and report["value"] == current["value"]))
        origin = Provenance(kind="told", event_id=report["root_event"], source_agent=report["root_source"],
                            upstream=Provenance(kind="observed", event_id=report["root_event"])
                            if report.get("root_kind") == "observed" else None)
        exposure = Exposure(event.tick, as_of, SUPPLY, report["value"], "told", event.event_id,
                            Provenance("told", event.event_id, speaker, origin), speaker, accepted)
        self.epistemic[listener].exposures.setdefault("grain." + predicate, []).append(exposure)
        self._remember(listener, Experience(
            tick=event.tick, kind="retracted" if retraction else "told", subject="grain", predicate=predicate,
            value=report["value"], source_agent=speaker, as_of=as_of, accepted=accepted,
            event_id=event.event_id, claimed_origin_kind=report.get("root_kind", "told"),
            claimed_origin_event=report["root_event"], claimed_origin_observer=report["root_source"],
            text=(f"At hour {event.tick} {speaker} retracted source root E{report['value']}." if retraction else
                  f"At hour {event.tick} {speaker} told me grain supply was {report['value']} as of {as_of}; "
                  f"origin {report['root_source']} E{report['root_event']}.") +
                 f" [relay depth={report.get('depth', 0)}]" +
                 ("" if accepted else " I did not accept this older or distrusted claim.")))

    def _queue(self, tick, speaker, listener, exp, depth=1, delay=None):
        if exp not in self.remembered(speaker) or depth > self.config.communication_depth:
            return None
        delay = det_randint(1, 3, self.config.seed, "genesis-delay", tick, speaker, listener) if delay is None else delay
        event = self._emit(tick, "state_change", self.state.agent_locations[speaker], (speaker, listener),
                           "message_queued", f"{speaker} sends a remembered report to {listener}",
                           parents=(exp.event_id,), scope="private", speaker=speaker, listener=listener,
                           value=exp.value, as_of=exp.as_of, predicate=exp.predicate,
                           delivery_tick=tick + delay, root_event=exp.claimed_origin_event or exp.event_id,
                           root_source=exp.claimed_origin_observer or speaker,
                           root_kind=exp.claimed_origin_kind or exp.kind, depth=depth)
        self._pending.append({**copy.deepcopy(event.payload), "event_id": event.event_id})
        self._receipt(speaker, event, action="send_report", recipient=listener,
                      root_event=event.payload["root_event"], value=exp.value, cash_delta=0,
                      evidence_ids=[exp.event_id], description=event.payload["title"])
        return event

    def _deliver(self, tick):
        due = sorted([m for m in self._pending if m["delivery_tick"] <= tick], key=lambda m: (m["delivery_tick"], m["event_id"]))
        self._pending = [m for m in self._pending if m["delivery_tick"] > tick]
        for report in due:
            event = self._emit(tick, "tell", self.state.agent_locations[report["listener"]],
                               (report["speaker"], report["listener"]), "message_delivered",
                               f"A report from {report['speaker']} reaches {report['listener']}",
                               parents=[report["event_id"]] + report.get("parents", []), scope="private",
                               speaker=report["speaker"], listener=report["listener"],
                               prop=["grain", report.get("predicate", "supply")], value=report["value"],
                               as_of=report["as_of"], root_event=report["root_event"],
                               root_source=report["root_source"], queued_event=report["event_id"], depth=report["depth"])
            self._hear(event, report)

    def _gossip(self, tick):
        news = {}
        for agent in self.agent_ids:
            retained = self.remembered(agent)
            recent_retractions = [e for e in retained if e.kind == "retracted" and tick - e.tick <= 4]
            belief = self.knowledge(agent)["grain.supply"]
            support = [e for e in retained if e.event_id in belief["evidence_ids"] and
                       e.subject == "grain" and e.predicate == "supply"]
            prefs = self.preferences[agent]
            if recent_retractions:
                exp = recent_retractions[-1]
            elif support and (prefs.get("share_unverified") or belief["confidence"] >= prefs.get("sharing_threshold", .7)):
                exp = max(support, key=lambda e: (e.as_of, e.tick, e.event_id))
            else:
                continue
            # Relay depth is carried by the retained message itself; no archive lookup.
            depth = int(exp.text.split("[relay depth=")[-1].split("]")[0]) if "[relay depth=" in exp.text else 0
            if depth < self.config.communication_depth:
                news[agent] = (exp, depth + 1)
        for speaker, (exp, depth) in sorted(news.items()):
            colocated = [a for a in self.agent_ids if a != speaker and self.state.agent_locations[a] == self.state.agent_locations[speaker]]
            for listener in sorted(colocated, key=lambda a: det_rand(self.config.seed, "genesis-gossip-budget", tick, speaker, a))[:4]:
                if any(r.get("action") == "send_report" and r.get("recipient") == listener and
                       r.get("root_event") == exp.claimed_origin_event and r.get("value") == exp.value
                       for r in self._receipts(speaker)):
                    continue
                if det_rand(self.config.seed, "genesis-gossip", tick, speaker, listener) < .65:
                    self._queue(tick, speaker, listener, exp, depth)

    def _order(self, tick):
        if self.config.allocation == "fixed":
            return list(self.agent_ids)
        if self.config.allocation == "rotating":
            shift = (tick // 2) % len(self.agent_ids)
            return self.agent_ids[shift:] + self.agent_ids[:shift]
        return sorted(self.agent_ids, key=lambda a: det_rand(self.config.seed, "genesis-allocation", tick, a))

    def _decision_phase(self, tick):
        if tick % 2 and tick != self.config.n_ticks - 1:
            return
        for agent in self._order(tick):
            view = self.private_view(agent)
            open_contracts = [c for c in view["commitments"] if c["status"] == "open"]
            next_contract = min(open_contracts, key=lambda c: c["deadline"]) if open_contracts else None
            need = next_contract["quantity"] if next_contract else 0
            buffer = self.preferences[agent].get("speculative_buffer", 0)
            target = need + buffer
            eligible = self.economy.inventory[agent] < target
            official = self.roles[agent] == "grain official"
            if not eligible and not official:
                continue
            policy = self._policies[agent]
            choice = (policy.decide_local(view, tick) if hasattr(policy, "decide_local") else
                      policy.decide(effective_records(self.remembered(agent)), tick, agent))
            choice = dict(choice)
            action = choice.get("action", "defer")
            if action not in ("reserve", "defer", "verify"):
                raise ValueError("invalid citizen action")
            prediction = choice.get("predicted_value", "unknown")
            if prediction not in ("available", "disrupted", "unknown"):
                raise ValueError("invalid citizen supply prediction")
            evidence = list(dict.fromkeys(choice.get("evidence_ids", [])))
            if not set(evidence).issubset({e.event_id for e in self.remembered(agent)}):
                raise ValueError("citizen action cites forgotten or inaccessible evidence")
            if action == "verify" and (agent in self._pending_inspections or self.economy.cash[agent] < INSPECTION_FEE or
                                       tick + 1 >= self.config.n_ticks):
                action = "defer"
            if action == "reserve" and not eligible:
                action = "defer"
            event = self._emit(tick, "state_change", self.state.agent_locations[agent], (agent,),
                               "decision", f"{agent} chooses {action}: {choice.get('reason', 'local policy')}",
                               parents=evidence, scope="private", decision={**choice, "action": action},
                               semantic_key=f"decision:{tick}:{agent}")
            reference = [e for e in effective_records(self.remembered(agent)) if e.accepted and
                         e.subject == "grain" and e.predicate == "supply"]
            local_expected = max(reference, key=lambda e: (e.as_of, e.tick, e.event_id)).value if reference else "unknown"
            decision = {**choice, "predicted_value": prediction, "agent": agent, "tick": tick, "action": action,
                        "event_id": event.event_id, "evidence_ids": evidence,
                        "opportunity_valid": eligible, "autonomous": action == "reserve",
                        "actual_value": self.state.facts[SUPPLY.key], "attempted": 0, "filled": 0,
                        "local_expected": local_expected, "local_recall_correct": prediction == local_expected,
                        "belief_current_correct": prediction == self.state.facts[SUPPLY.key],
                        "abstained": action != "reserve",
                        "executed_cost": 0.0, "evaluation": "executed outcomes; no categorical regret"}
            self.decisions.append(decision)
            if action == "verify":
                self._book_inspection(agent, tick, (event.event_id,), evidence)
                decision["executed_cost"] = INSPECTION_FEE
            elif action == "reserve":
                attempted = max(1, min(4, target - self.economy.inventory[agent]))
                purchase = self._purchase_quantity(agent, attempted, tick, event, evidence)
                decision.update(attempted=attempted, filled=purchase.payload["quantity"],
                                executed_cost=-purchase.payload["cash_delta"][agent])

    def _purchase_quantity(self, agent, attempted, tick, decision_event=None, evidence=()):
        parents = [self._supply_event, self._price_event]
        if decision_event is not None:
            parents.append(decision_event.event_id)
        self._move(agent, "forum", tick, "buying grain", parents)
        quantity = min(attempted, self.economy.market_stock, max(0, int(self.economy.cash[agent] // self.economy.price)))
        price = self.economy.price
        event = self._emit(tick, "state_change", "forum", (agent,),
                           "player_market_purchase" if agent == "Player" else "purchase",
                           f"{agent}'s order fills {quantity}/{attempted} units", parents=parents,
                           owner=agent, attempted=attempted, quantity=quantity, unit_price=price,
                           cash_delta={agent: -quantity * price}, inventory_delta={agent: quantity},
                           market_stock_delta=-quantity)
        self._receipt(agent, event, action="purchase", attempted=attempted, quantity=quantity,
                      cash_delta=-quantity * price, evidence_ids=list(evidence),
                      description=f"Bought {quantity} of {attempted} requested grain at {price:g} per unit.")
        return event

    def _book_inspection(self, agent, tick, parents=(), evidence=()):
        event = self._emit(tick, "state_change", self.state.agent_locations[agent], (agent,),
                           "inspection_booked", f"{agent} pays {INSPECTION_FEE:g} for a next-hour inspection",
                           parents=parents, scope="private", owner=agent, fee=INSPECTION_FEE, cash_delta={agent: -INSPECTION_FEE})
        self._verifications.append({"agent": agent, "tick": tick + 1, "decision_event": event.event_id})
        self._pending_inspections.add(agent)
        self._receipt(agent, event, action="inspection", cash_delta=-INSPECTION_FEE, evidence_ids=list(evidence),
                      description=f"Paid {INSPECTION_FEE:g} for a next-hour inspection, not an immediate oracle answer.")
        return event

    def _verification(self, tick):
        due = [v for v in self._verifications if v["tick"] == tick]
        self._verifications = [v for v in self._verifications if v["tick"] != tick]
        for visit in due:
            self._pending_inspections.discard(visit["agent"])
            self._verify_now(visit["agent"], tick, (visit["decision_event"],))

    def _verify_now(self, agent, tick, parents=(), category="inspection", operator=False):
        if operator:
            category = "intervention_correction"
        self._move(agent, "granary", tick, "performing a booked inspection", parents)
        prior = self.remembered(agent)
        event = self._emit(tick, "state_change", "granary", (agent,), category,
                           f"{agent} privately verifies the current shipment", parents=list(parents) + [self._supply_event],
                           scope="private", prop=["grain", "supply"], value=self.state.facts[SUPPLY.key],
                           verification=True, operator_intervention=category == "intervention_correction")
        self._observe(agent, event, assess=False)
        checks = {}
        # A paid visit can also inspect at most two dated dispatch records for
        # claims still remembered at arrival, within an explicit eight-hour
        # lookback. These are new world observations, never archive recovery.
        dates = sorted({e.as_of for e in effective_records(prior) if e.kind == "told" and
                        e.subject == "grain" and e.predicate == "supply" and e.value != "unknown"
                        and 0 <= tick - e.as_of <= 8 and e.as_of < tick}, reverse=True)[:2]
        for date in dates:
            historical = [e for e in self.ledger.events if e.payload.get("category") == "supply" and e.tick <= date]
            if not historical:
                continue
            record = max(historical, key=lambda e: (e.tick, e.event_id))
            observed = self._emit(tick, "state_change", "granary", (agent,), "inspection_record",
                                  f"{agent} reads the dated dispatch record for hour {date}",
                                  parents=[event.event_id, record.event_id], scope="private",
                                  record_as_of=date, recorded_value=record.payload["value"],
                                  mechanism=("operator dispatch-log inspection" if operator or category == "intervention_correction" else
                                             "paid dispatch-log inspection") + "; at most two records, lookback eight ticks")
            self._remember(agent, Experience(
                tick=tick, kind="observed", subject="dispatch_log", predicate=f"grain_supply_at_{date}",
                value=record.payload["value"], source_agent=None, as_of=date, accepted=True,
                event_id=observed.event_id, claimed_origin_kind="observed", claimed_origin_event=observed.event_id,
                claimed_origin_observer=agent,
                text=f"At hour {tick} I inspected a dated dispatch log: grain supply as of hour {date} was {record.payload['value']}."))
            checks[date] = {"value": record.payload["value"], "event_id": observed.event_id}
        self._update_relationships(agent, self.state.facts[SUPPLY.key], event, prior, checks)
        return event

    def _settle(self, tick):
        for agent in self.agent_ids + ["Player"]:
            for commitment in self.economy.commitments[agent]:
                if commitment["status"] != "open" or commitment["deadline"] != tick:
                    continue
                quantity = min(commitment["quantity"], self.economy.inventory[agent])
                missing = commitment["quantity"] - quantity
                cash_delta = {agent: quantity * 3 - missing * 5}
                inventory_delta = {agent: -quantity}
                beneficiary = commitment.get("beneficiary")
                if beneficiary:
                    payment = quantity * commitment.get("unit_payment", 4)
                    cash_delta = {agent: payment - missing * 5, beneficiary: -payment + missing * 5}
                    inventory_delta[beneficiary] = quantity
                event = self._emit(tick, "state_change", self.state.agent_locations[agent], (agent,),
                                   "commitment_settled", f"{agent} delivers {quantity}/{commitment['quantity']} committed units",
                                   scope="private", owner=agent, quantity=quantity, missing=missing,
                                   cash_delta=cash_delta, inventory_delta=inventory_delta,
                                   parents=(commitment.get("event_id"),),
                                   commitment_updates=[{"agent": agent, "id": commitment["id"],
                                                        "status": "missed" if missing else "fulfilled", "fulfilled": quantity}])
                self._receipt(agent, event, action="settlement", quantity=quantity, missing=missing,
                              cash_delta=cash_delta[agent], evidence_ids=[], description=event.payload["title"])
                if beneficiary:
                    self._receipt(beneficiary, event, action="contract_receipt", quantity=quantity,
                                  cash_delta=cash_delta[beneficiary], evidence_ids=[], description=event.payload["title"])

    def step(self, count=1):
        if type(count) is not int or count < 0:
            raise ValueError("step count must be a nonnegative integer")
        for _ in range(count):
            if self.done:
                break
            tick = self.tick + 1
            self._active_tick = tick
            self._movement(tick)
            self._world(tick)
            self._verification(tick)
            self._deliver(tick)
            self._gossip(tick)
            self._decision_phase(tick)
            self._settle(tick)
            self.tick = tick
        return self

    def inject_claim(self, recipient, value, source="Player", as_of=None, parents=(), root_event=None, kind="player_message"):
        self._participant(recipient)
        self._participant(source)
        if recipient == source or value not in ("available", "disrupted", "unknown"):
            raise ValueError("a claim requires a different recipient and a valid supply value")
        as_of = self.tick if as_of is None else as_of
        if type(as_of) is not int or not -1 <= as_of <= self.tick:
            raise ValueError("claim as_of must be an elapsed world tick")
        if any(type(p) is not int or not 0 <= p < len(self.ledger) for p in parents):
            raise ValueError("claim parents must be existing events")
        accessible = self.remembered(source)
        origin = next((e for e in accessible if (e.claimed_origin_event or e.event_id) == root_event
                       and e.value == value and e.as_of == as_of), None) if root_event is not None else None
        if root_event is not None and origin is None:
            raise ValueError("a claimed observed root must be remembered by its actual sender")
        root = root_event if root_event is not None else len(self.ledger)
        event = self._emit(self.tick, "tell", self.state.agent_locations[recipient], (source, recipient), kind,
                           f"{source} tells {recipient}: grain {value}", parents=list(parents) + ([origin.event_id] if origin else []),
                           scope="private", speaker=source, listener=recipient, prop=["grain", "supply"],
                           value=value, as_of=as_of, root_kind=origin.claimed_origin_kind if origin else "told",
                           root_event=root, root_source=origin.claimed_origin_observer if origin else source)
        self._hear(event, {"listener": recipient, "speaker": source, "value": value, "as_of": as_of,
                           "root_event": root, "root_source": origin.claimed_origin_observer if origin else source,
                           "root_kind": origin.claimed_origin_kind if origin else "told"})
        self._receipt(source, event, action="tell", recipient=recipient, value=value, root_event=root, as_of=as_of,
                      cash_delta=0, evidence_ids=[origin.event_id] if origin else [], description=event.payload["title"])
        return self._event_dict(event)

    def retract(self, agent, root_event, speaker="Player"):
        self._participant(agent)
        self._participant(speaker)
        if agent == speaker:
            raise ValueError("a retraction must be sent to another participant")
        if type(root_event) is not int or not 0 <= root_event < len(self.ledger):
            raise ValueError("retraction requires an existing source root")
        root = self.ledger.events[root_event]
        # This is authority validation, not agent retrieval: no historical fact
        # value is restored. The new tombstone itself consumes a normal FIFO slot.
        if not (root.payload.get("speaker") == speaker or
                root.payload.get("category") in ("inspection", "supply") and speaker in root.actors):
            raise ValueError("a speaker can retract only their own originating claim")
        event = self._emit(self.tick, "tell", self.state.agent_locations[agent], (speaker, agent), "retraction",
                           f"{speaker} retracts source root E{root_event} to {agent}", parents=(root_event,), scope="private",
                           speaker=speaker, listener=agent, prop=["grain", "retraction"], value=str(root_event))
        self._hear(event, {"speaker": speaker, "listener": agent, "predicate": "retraction", "value": str(root_event),
                           "as_of": self.tick, "root_event": event.event_id, "root_source": speaker, "root_kind": "told"})
        self._receipt(speaker, event, action="retract", root_event=root_event, cash_delta=0, evidence_ids=[], description=event.payload["title"])
        return self._event_dict(event)

    def inspect(self, agent="Player"):
        self._participant(agent)
        if self.done or self.tick + 1 >= self.config.n_ticks:
            raise ValueError("there is no remaining tick for a delayed inspection")
        if agent in self._pending_inspections or self.economy.cash[agent] < INSPECTION_FEE:
            raise ValueError("inspection is already pending or unaffordable")
        return self._event_dict(self._book_inspection(agent, self.tick))

    def player_trade(self, recipient, quantity, direction="sell"):
        if type(quantity) is not int or not 1 <= quantity <= 12:
            raise ValueError("trade quantity must be an integer 1..12")
        if direction not in ("buy", "sell"):
            raise ValueError("invalid trade direction")
        if recipient == "market":
            cost = quantity * self.economy.price
            if self.economy.market_stock < quantity or self.economy.cash["Player"] < cost:
                raise ValueError("market order cannot be filled or afforded")
            return self._event_dict(self._purchase_quantity("Player", quantity, self.tick))
        self._participant(recipient)
        if recipient == "Player" or direction not in ("buy", "sell"):
            raise ValueError("invalid player trade counterparty or direction")
        if self.state.trust.get((recipient, "Player"), .6) < .35:
            raise ValueError("commercial access refused because the citizen distrusts Player")
        seller, buyer = (recipient, "Player") if direction == "buy" else ("Player", recipient)
        cost = quantity * self.economy.price
        if self.economy.inventory[seller] < quantity or self.economy.cash[buyer] < cost:
            raise ValueError("trade is not backed by inventory and affordable cash")
        event = self._emit(self.tick, "state_change", self.state.agent_locations[recipient], ("Player", recipient),
                           "player_trade", f"{buyer} buys {quantity} grain from {seller}",
                           parents=(self._price_event,), owner="Player", buyer=buyer, seller=seller,
                           attempted=quantity, quantity=quantity, price=self.economy.price,
                           inventory_delta={seller: -quantity, buyer: quantity}, cash_delta={seller: cost, buyer: -cost})
        for agent in ("Player", recipient):
            self._receipt(agent, event, action="trade", quantity=quantity,
                          cash_delta=event.payload["cash_delta"][agent], evidence_ids=[], description=event.payload["title"])
        return self._event_dict(event)

    def player_contract(self, recipient, quantity, deadline):
        self._participant(recipient)
        if recipient == "Player" or type(quantity) is not int or not 1 <= quantity <= 12:
            raise ValueError("invalid contract counterparty or quantity")
        if type(deadline) is not int or not self.tick < deadline < self.config.n_ticks:
            raise ValueError("contract deadline must be a future tick inside the horizon")
        if self.state.trust.get((recipient, "Player"), .6) < .35:
            raise ValueError("commercial access refused because the citizen distrusts Player")
        if self.economy.cash[recipient] < quantity * 4:
            raise ValueError("counterparty cannot afford the proposed agreement")
        future_id = len(self.ledger)
        commitment = {"id": f"Player:contract:{future_id}", "deadline": deadline, "quantity": quantity,
                      "status": "open", "fulfilled": 0, "beneficiary": recipient, "unit_payment": 4,
                      "event_id": future_id}
        event = self._emit(self.tick, "state_change", self.state.agent_locations[recipient], ("Player", recipient),
                           "player_contract", f"Player promises {quantity} grain to {recipient} at hour {deadline}",
                           scope="private", quantity=quantity, deadline=deadline, recipient=recipient,
                           owner="Player", new_commitment=commitment)
        self._receipt("Player", event, action="contract", quantity=quantity, deadline=deadline,
                      recipient=recipient, cash_delta=0, evidence_ids=[], description=event.payload["title"])
        self._receipt(recipient, event, action="agreement", quantity=quantity, deadline=deadline,
                      cash_delta=0, evidence_ids=[], description=event.payload["title"])
        return self._event_dict(event)

    def apply_player_action(self, action):
        if not isinstance(action, dict):
            raise ValueError("player action must be an object")
        kind = action.get("kind", action.get("action"))
        allowed = {"tell": {"recipient", "value", "as_of", "root_event"},
                   "claim": {"recipient", "value", "as_of", "root_event"},
                   "message": {"recipient", "value", "as_of", "root_event"},
                   "retract": {"recipient", "root_event"}, "verify": {"agent"}, "inspect": {"agent"},
                   "trade": {"recipient", "quantity", "direction"},
                   "contract": {"recipient", "quantity", "deadline"}, "move": {"location", "to"}}
        if not isinstance(kind, str) or kind not in allowed or set(action) - allowed[kind] - {"kind", "action"}:
            raise ValueError("unknown player action or unsupported action fields")
        if kind in ("tell", "claim", "message"):
            return self.inject_claim(action.get("recipient"), action.get("value"),
                                     as_of=action.get("as_of"), root_event=action.get("root_event"))
        if kind == "retract":
            return self.retract(action.get("recipient"), action.get("root_event"))
        if kind in ("verify", "inspect"):
            if action.get("agent", "Player") != "Player":
                raise ValueError("player actions cannot spend another citizen's inspection budget")
            return self.inspect("Player")
        if kind == "trade":
            return self.player_trade(action.get("recipient", "market"), action.get("quantity"), action.get("direction", "sell"))
        if kind == "contract":
            return self.player_contract(action.get("recipient"), action.get("quantity"), action.get("deadline"))
        if kind == "move":
            location = action.get("location", action.get("to"))
            if location not in {loc["id"] for loc in LOCATIONS}:
                raise ValueError("unknown destination")
            event = self._move("Player", location, self.tick, "player movement")
            return self._event_dict(event) if event is not None else {"status": "already_here", "location": location}
        raise ValueError("unknown player action")

    def private_view(self, agent):
        self._participant(agent)
        records = self.remembered(agent)
        quotes = [e for e in records if e.subject == "grain" and e.predicate == "price" and e.accepted]
        quoted = max(quotes, key=lambda e: (e.tick, e.event_id)).value if quotes else None
        role = self.roles.get(agent, "visitor")
        return {"id": agent, "name": agent, "role": role, "location": self.state.agent_locations[agent],
                "cash": self.economy.cash[agent], "inventory": self.economy.inventory[agent],
                "commitments": copy.deepcopy(self.economy.commitments[agent]),
                "goals": ["Meet my own delivery commitments", "Protect affordable working capital",
                          "Maintain reliable commercial relationships"],
                "preferences": copy.deepcopy(self.preferences[agent]),
                "beliefs": self.knowledge(agent), "experiences": [asdict(e) for e in records],
                "relationships": [{"listener": a, "speaker": b, "trust": v} for (a, b), v in sorted(self.state.trust.items()) if a == agent],
                "receipts": self._receipts(agent), "quoted_price": float(quoted) if quoted is not None else None,
                "memory": {"architecture": self.config.memory, "capacity": self.config.capacity, "retained": len(records)},
                "trust_player": self.state.trust.get((agent, "Player"), .6),
                "commercial_access": self.state.trust.get((agent, "Player"), .6) >= .35,
                "status": "inspection_pending" if agent in self._pending_inspections else "active"}

    def metrics(self, terminal_inventory_value=3.0):
        return executed_metrics(self, terminal_inventory_value)

    def snapshot(self, operator=False):
        visible = {e.event_id for e in self.remembered("Player")}
        events = [self._event_dict(e) for e in self.ledger.events if operator or
                  e.payload.get("category") in ("movement", "player_arrived", "price") or
                  e.event_id in visible or "Player" in e.actors and e.payload.get("category") != "city_initialized"]
        snapshot = {"config": asdict(self.config), "tick": self.tick, "day": max(0, self.tick) // 24 + 1,
                    "done": self.done, "branch_id": self.branch_id, "parent_tick": self.parent_tick,
                    "locations": copy.deepcopy(list(LOCATIONS)),
                    "agents": [self.private_view(a) if operator else {
                        "id": a, "name": a, "role": self.roles[a], "location": self.state.agent_locations[a],
                        "trust_player": self.state.trust.get((a, "Player"), .6),
                        "commercial_access": self.state.trust.get((a, "Player"), .6) >= .35}
                        for a in self.agent_ids], "player": self.private_view("Player"),
                    "world": {"price": self.economy.price, "inventory": self.economy.market_stock,
                              "market_stock": self.economy.market_stock, "supply": "unknown", "facts": {}},
                    "events": events, "player_events": events,
                    "messages": [{k: v for k, v in m.items() if operator or k in
                                 ("event_id", "speaker", "listener", "delivery_tick")}
                                 for m in self.messages if operator or "Player" in (m["speaker"], m["listener"])],
                    "decisions": [{k: v for k, v in d.items() if k not in ("actual_value", "qa_expected", "qa_correct")}
                                  for d in self.decisions] if operator else [],
                    "metrics": self.metrics() if operator else {"player": self.metrics()["player"]},
                    "information_mode": "bounded character memories; operator truth is separate"}
        if operator:
            snapshot["operator"] = {"facts": dict(self.state.facts), "supply": self.state.facts.get(SUPPLY.key),
                                    "ledger_hash": self.ledger.content_hash(), "all_events": self.ledger.to_json(),
                                    "archive_sizes": {a: len(v) for a, v in self.experiences.items()}}
        return snapshot

    def compare(self, other):
        result = super().compare(other)
        result["executed_outcomes"] = {"baseline": self.metrics(), "branch": other.metrics()}
        result["player"] = {"baseline": self.private_view("Player"), "branch": other.private_view("Player")}
        result["identical"] = result["identical"] and self.private_view("Player") == other.private_view("Player")
        return result

    def _beliefs(self, agent):
        return self.knowledge(agent)
