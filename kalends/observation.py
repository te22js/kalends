"""Observation rules: who is capable of perceiving an event.

Computed by the simulator from event scope + agent positions at the event's
tick. Agents never decide what they observed; the world does.
"""
from __future__ import annotations

from .events import WorldEvent
from .world import WorldState


def observers_of(ev: WorldEvent, state: WorldState,
                 all_agents: list[str]) -> list[str]:
    """Agents that perceive `ev`, given positions in `state` (state as of the
    event's tick, after movement for that tick has been applied)."""
    if ev.scope == "private":
        return [a for a in all_agents if a in ev.actors]
    # public: actors plus anyone standing at the event's location
    seen = []
    for a in all_agents:
        if a in ev.actors or state.agent_locations.get(a) == ev.location:
            seen.append(a)
    return seen
