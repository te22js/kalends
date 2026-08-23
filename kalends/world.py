"""WorldState: a pure, deterministic projection of the event ledger.

project(ledger, scenario) folds events in order into the canonical state.
Nothing else in the system is allowed to define "what is true".
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .events import Ledger, WorldEvent


@dataclass
class WorldState:
    tick: int = -1
    agent_locations: dict[str, str] = field(default_factory=dict)
    # object states, keyed by proposition key, e.g. "bakery.condition" -> "burning"
    facts: dict[str, str] = field(default_factory=dict)
    # trust weights, keyed (a, b) -> how much a trusts b, in [0, 1]
    trust: dict[tuple[str, str], float] = field(default_factory=dict)

    def location_of(self, agent_id: str) -> str:
        return self.agent_locations[agent_id]


def apply_event(state: WorldState, ev: WorldEvent) -> None:
    """Fold one event into the state. Mutates in place (callers own the copy)."""
    state.tick = ev.tick
    if ev.etype == "move":
        state.agent_locations[ev.actors[0]] = ev.payload["to"]
    elif ev.etype in ("incident", "state_change"):
        # Incidents/state changes may assert new fact values.
        if "prop" in ev.payload:
            subject, predicate = ev.payload["prop"]
            state.facts[f"{subject}.{predicate}"] = ev.payload["value"]
    elif ev.etype == "tell":
        pass  # communication changes beliefs, never world facts


def project(ledger: Ledger, initial: WorldState) -> WorldState:
    """Fold the whole ledger over a copy of the initial state."""
    state = WorldState(
        tick=initial.tick,
        agent_locations=dict(initial.agent_locations),
        facts=dict(initial.facts),
        trust=dict(initial.trust),
    )
    for ev in ledger.events:
        apply_event(state, ev)
    return state
