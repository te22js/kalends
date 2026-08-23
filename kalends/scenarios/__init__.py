"""Scenario container: everything that defines one experimental world setup."""
from __future__ import annotations

from dataclasses import dataclass, field

from ..agents import AgentSpec
from ..propositions import Proposition
from ..world import WorldState


@dataclass(frozen=True)
class Incident:
    """A scripted world happening (ground-truth change) at a fixed tick."""
    tick: int
    etype: str            # "incident" | "state_change"
    location: str
    actors: tuple[str, ...]
    prop: Proposition
    value: str
    scope: str = "public"


@dataclass
class Scenario:
    name: str
    n_ticks: int
    locations: list[str]
    agents: list[AgentSpec]
    initial_state: WorldState
    incidents: list[Incident]
    propositions: list[Proposition]
    # subject -> alias phrase used in some renderings/queries ("bakery" -> "pistrinum")
    aliases: dict[str, str] = field(default_factory=dict)
    # value -> distorted value a careless teller may transmit instead
    distortion_map: dict[str, str] = field(default_factory=dict)
    # human-readable statement per proposition key; "{value}" is substituted.
    statements: dict[str, str] = field(default_factory=dict)
    # alias variant of the statement (used with alias_p probability)
    alias_statements: dict[str, str] = field(default_factory=dict)
    jitter_p: float = 0.15        # chance an agent deviates from its schedule
    alias_p: float = 0.3          # chance a rendering uses the alias phrasing
    gossip_recency: int = 12      # beliefs older than this many ticks are no longer "news"

    def agent_ids(self) -> list[str]:
        return [a.agent_id for a in self.agents]
