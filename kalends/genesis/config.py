"""Prospective Genesis controls, separate from the historical city study."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class GenesisConfig:
    seed: int = 2026
    n_agents: int = 8
    n_ticks: int = 96
    family: str = "reversal"
    memory: str = "hybrid_guarded"
    gate: str = "none"
    threshold: int = 2
    capacity: int = 32
    communication_depth: int = 3
    supply_mode: str = "per_capita"
    allocation: str = "seeded"
    role_policy: bool = True

    def __post_init__(self):
        for name in ("seed", "n_agents", "n_ticks", "threshold", "capacity", "communication_depth"):
            if type(getattr(self, name)) is not int:
                raise ValueError(f"{name} must be an integer")
        if not 2 <= self.n_agents <= 128 or not 1 <= self.n_ticks <= 720:
            raise ValueError("population must be 2..128 and horizon 1..720")
        if self.capacity < 1 or self.threshold < 1 or not 0 <= self.communication_depth <= 16:
            raise ValueError("Genesis requires positive capacity/threshold and depth 0..16")
        if self.family not in ("stable", "reversal", "scarcity"):
            raise ValueError("unknown Genesis family")
        if self.memory not in ("structured", "bm25", "hybrid", "hybrid_guarded", "vector"):
            raise ValueError("unknown memory")
        if self.gate not in ("none", "lineage", "source_count"):
            raise ValueError("unknown evidence gate")
        if self.supply_mode not in ("per_capita", "fixed"):
            raise ValueError("supply_mode must be per_capita or fixed")
        if self.allocation not in ("seeded", "rotating", "fixed"):
            raise ValueError("allocation must be seeded, rotating, or fixed")
        if type(self.role_policy) is not bool:
            raise ValueError("role_policy must be a boolean")
