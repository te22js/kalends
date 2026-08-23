"""The simulation loop: ties ledger, world state, observation and the
epistemic oracle together.

Per tick, in fixed order (fixed order + a single seeded RNG = determinism):
  1. movement   - each agent follows its schedule, with seeded jitter
  2. incidents  - scripted ground-truth changes fire; witnesses observe
  3. gossip     - co-located pairs may exchange recent news (with optional
                  seeded distortion), producing `tell` events

Every event goes through the same path: append to ledger -> fold into world
state -> compute observers -> update per-agent epistemic oracle -> emit
Experience records (the stream later replayed into memory systems).
"""
from __future__ import annotations

import random

from .epistemic import EpistemicState, Exposure
from .events import Ledger
from .memory.base import Experience
from .observation import observers_of
from .propositions import Proposition
from .scenarios import Scenario
from .world import WorldState, apply_event


class Simulation:
    def __init__(self, scenario: Scenario, seed: int):
        self.scenario = scenario
        self.seed = seed
        self.rng = random.Random(seed)
        self.ledger = Ledger()
        init = scenario.initial_state
        self.state = WorldState(
            tick=-1,
            agent_locations=dict(init.agent_locations),
            facts=dict(init.facts),
            trust=dict(init.trust),
        )
        self.epistemic: dict[str, EpistemicState] = {
            a: EpistemicState(a) for a in scenario.agent_ids()
        }
        self.experiences: dict[str, list[Experience]] = {
            a: [] for a in scenario.agent_ids()
        }
        self._specs = {a.agent_id: a for a in scenario.agents}

    # -- rendering ---------------------------------------------------------
    def _statement(self, prop: Proposition, value: str) -> str:
        use_alias = (prop.key in self.scenario.alias_statements
                     and self.rng.random() < self.scenario.alias_p)
        template = (self.scenario.alias_statements[prop.key] if use_alias
                    else self.scenario.statements.get(
                        prop.key, f"the {prop.predicate} of the {prop.subject} is {{value}}"))
        return template.format(value=value)

    # -- phases ------------------------------------------------------------
    def _movement(self, tick: int) -> None:
        for spec in self.scenario.agents:
            target = spec.intended_location(tick)
            if self.rng.random() < self.scenario.jitter_p:
                target = self.rng.choice(self.scenario.locations)
            if self.state.agent_locations.get(spec.agent_id) == target:
                continue
            ev = self.ledger.append(tick, "move", target, (spec.agent_id,),
                                    {"to": target})
            apply_event(self.state, ev)
            # Episodic filler for the mover's own memory (retrieval noise).
            self.experiences[spec.agent_id].append(Experience(
                tick=tick, kind="episodic", subject=None, predicate=None,
                value=None, source_agent=None, as_of=tick, accepted=True,
                event_id=ev.event_id,
                text=f"At hour {tick} I went to the {target.replace('_', ' ')}.",
            ))

    def _incidents(self, tick: int) -> None:
        for inc in self.scenario.incidents:
            if inc.tick != tick:
                continue
            prop = inc.prop
            ev = self.ledger.append(
                tick, inc.etype, inc.location, inc.actors,
                {"prop": [prop.subject, prop.predicate], "value": inc.value},
                scope=inc.scope,
            )
            apply_event(self.state, ev)
            for agent_id in observers_of(ev, self.state, self.scenario.agent_ids()):
                self.epistemic[agent_id].record_observation(
                    tick, prop, inc.value, ev.event_id)
                self.experiences[agent_id].append(Experience(
                    tick=tick, kind="observed", subject=prop.subject,
                    predicate=prop.predicate, value=inc.value,
                    source_agent=None, as_of=tick, accepted=True,
                    event_id=ev.event_id,
                    text=f"At hour {tick} I saw with my own eyes that "
                         f"{self._statement(prop, inc.value)}.",
                ))

    def _news_of(self, agent_id: str, tick: int) -> Exposure | None:
        """The speaker's most newsworthy current belief: the most recently
        acquired accepted belief within the gossip recency window."""
        best: Exposure | None = None
        for key in sorted(self.epistemic[agent_id].exposures):
            subject, predicate = key.split(".", 1)
            cur = self.epistemic[agent_id].belief(Proposition(subject, predicate))
            if cur is None or tick - cur.tick > self.scenario.gossip_recency:
                continue
            if best is None or (cur.tick, cur.event_id) > (best.tick, best.event_id):
                best = cur
        return best

    def _gossip(self, tick: int) -> None:
        by_location: dict[str, list[str]] = {}
        for agent_id in self.scenario.agent_ids():
            by_location.setdefault(
                self.state.agent_locations[agent_id], []).append(agent_id)
        for location in sorted(by_location):
            members = by_location[location]
            if len(members) < 2:
                continue
            for speaker in members:
                spec = self._specs[speaker]
                for listener in members:
                    if listener == speaker:
                        continue
                    if self.rng.random() >= spec.chattiness:
                        continue
                    news = self._news_of(speaker, tick)
                    if news is None:
                        continue
                    value = news.value
                    if (self.rng.random() < spec.distort_p
                            and value in self.scenario.distortion_map):
                        value = self.scenario.distortion_map[value]
                    prop = news.prop
                    ev = self.ledger.append(
                        tick, "tell", location, (speaker, listener),
                        {"speaker": speaker, "listener": listener,
                         "prop": [prop.subject, prop.predicate],
                         "value": value, "as_of": news.as_of},
                        scope="private",
                    )
                    trust = self.state.trust.get((listener, speaker), 0.5)
                    exposure = self.epistemic[listener].record_told(
                        tick, prop, value, ev.event_id, speaker,
                        claimed_as_of=news.as_of,
                        claimed_chain=news.provenance,
                        trust_in_speaker=trust,
                    )
                    self.experiences[listener].append(Experience(
                        tick=tick, kind="told", subject=prop.subject,
                        predicate=prop.predicate, value=value,
                        source_agent=speaker, as_of=news.as_of,
                        accepted=exposure.accepted, event_id=ev.event_id,
                        text=f"At hour {tick} {speaker} told me that "
                             f"{self._statement(prop, value)}.",
                    ))

    # -- run ---------------------------------------------------------------
    def run(self) -> "Simulation":
        for tick in range(self.scenario.n_ticks):
            self._movement(tick)
            self._incidents(tick)
            self._gossip(tick)
        return self


def run_scenario(scenario: Scenario, seed: int) -> Simulation:
    return Simulation(scenario, seed).run()
