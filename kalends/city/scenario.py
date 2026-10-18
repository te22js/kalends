"""Seeded, schematic grain-market scenario used by the live city.

Coordinates are a legible diagram, not an archaeological reconstruction.
The exogenous supply schedule is keyed independently of policy decisions.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..agents import AgentSpec
from ..rng import det_rand, det_randint


@dataclass(frozen=True)
class CityConfig:
    seed: int = 42
    n_agents: int = 8
    n_ticks: int = 24
    family: str = "rumour"
    memory: str = "structured"
    gate: str = "none"
    threshold: int = 1
    capacity: int = 0
    communication_depth: int = 3

    def __post_init__(self):
        for name in ("seed", "n_agents", "n_ticks", "threshold", "capacity", "communication_depth"):
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer")
        if not 2 <= self.n_agents <= 128:
            raise ValueError("n_agents must be between 2 and 128")
        if not 1 <= self.n_ticks <= 240:
            raise ValueError("n_ticks must be between 1 and 240")
        if self.family not in ("rumour", "rumor", "shortage", "recovery", "private", "mixed"):
            raise ValueError("unknown city scenario family")
        if self.threshold < 1 or self.capacity < 0 or self.communication_depth < 0:
            raise ValueError("threshold must be positive; capacity/depth cannot be negative")
        if self.memory not in ("structured", "bm25", "hybrid", "hybrid_guarded", "vector"):
            raise ValueError("unknown memory")
        if self.gate not in ("none", "lineage", "source_count"):
            raise ValueError("unknown gate")


LOCATIONS = (
    {"id": "forum", "label": "Forum market", "x": 47, "y": 48},
    {"id": "bakery", "label": "Bakery", "x": 25, "y": 41},
    {"id": "thermopolium", "label": "Thermopolium", "x": 23, "y": 69},
    {"id": "baths", "label": "Baths", "x": 67, "y": 69},
    {"id": "house_of_gaius", "label": "House of Gaius", "x": 80, "y": 44},
    {"id": "temple", "label": "Temple", "x": 51, "y": 20},
    {"id": "harbour", "label": "Harbour", "x": 10, "y": 20},
    {"id": "granary", "label": "Grain yard", "x": 29, "y": 15},
)

ROLES = (
    ("Livia", "merchant", "forum"),
    ("Dama", "courier", "harbour"),
    ("Marcus", "trader", "thermopolium"),
    ("Flavia", "grain official", "granary"),
    ("Modestus", "baker", "bakery"),
    ("Julia", "innkeeper", "baths"),
    ("Gaius", "householder", "house_of_gaius"),
    ("Sabina", "temple steward", "temple"),
    ("Quintus", "mill worker", "bakery"),
    ("Aemilia", "cook", "house_of_gaius"),
    ("Celer", "porter", "harbour"),
    ("Vibia", "market seller", "forum"),
)


def build_agents(config: CityConfig) -> tuple[list[AgentSpec], dict[str, str]]:
    specs, roles = [], {}
    for index in range(config.n_agents):
        name, role, home = ROLES[index % len(ROLES)]
        if index >= len(ROLES):
            name = f"{name}{index // len(ROLES) + 1}"
        # Shared market hours produce encounters; intervening schedules differ.
        schedule = ((0, home), (3, "forum"), (7, home), (10, "thermopolium"),
                    (13, "forum"), (17, home), (20, "forum"))
        specs.append(AgentSpec(name, home, schedule, chattiness=0.46 +
                               0.16 * det_rand(config.seed, "city-chattiness", name)))
        roles[name] = role
    return specs, roles


def supply_at(config: CityConfig, tick: int) -> str:
    """Truth is fixed by family/seed/tick, never by a policy or branch id."""
    if config.family == "shortage":
        initial = "disrupted"
    elif config.family == "recovery":
        initial = "available"
    else:
        initial = "disrupted" if det_rand(config.seed, "city-initial-supply") < 0.5 else "available"
    phase = max(0, tick) // 7
    # Each phase has a stable draw, with guaranteed change at the first boundary.
    if phase == 0:
        return initial
    if phase == 1:
        return "available" if initial == "disrupted" else "disrupted"
    return "available" if det_rand(config.seed, "city-supply-phase", phase) < 0.6 else "disrupted"


def initial_inventory(config: CityConfig, agent: str) -> int:
    return det_randint(0, 3, config.seed, "city-inventory", agent)
