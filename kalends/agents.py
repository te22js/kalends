"""Agent specifications and the deterministic v0 behavior policies.

v0 agents are NOT LLMs. Movement follows a daily schedule with seeded jitter;
gossip follows a simple chattiness rule. This is deliberate: deterministic
policies are what make exact epistemic ground truth computable. The LLM slot
for richer behavior is a later layer that would *propose* the same event types.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    home: str
    # schedule: sorted list of (start_tick, location); agent intends to be at
    # `location` from start_tick until the next entry.
    schedule: tuple[tuple[int, str], ...]
    chattiness: float = 0.5   # probability of sharing news with a co-located agent
    distort_p: float = 0.0    # probability of distorting a value when telling

    def intended_location(self, tick: int) -> str:
        loc = self.home
        for start, location in self.schedule:
            if tick >= start:
                loc = location
            else:
                break
        return loc
