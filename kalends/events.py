"""Canonical reality layer: WorldEvent and the append-only Ledger.

Everything that "actually happened" in the world is a WorldEvent in the Ledger.
World state is always derived from the ledger by projection (world.py), never
mutated directly. An LLM (or any agent policy) can only *propose* events; the
simulator validates and appends them.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict

# Event scopes control observability (see observation.py):
#   "public"  - observable by any agent co-located with the event
#   "private" - observable only by the event's actors
SCOPES = ("public", "private")

# Event types used in v0. Kept deliberately small.
#   "move"         - an agent changes location
#   "incident"     - something happens in the world (fire, theft, ...)
#   "state_change" - a world object changes state (fire out, shop repaired, ...)
#   "tell"         - one agent communicates a proposition to another
ETYPES = ("move", "incident", "state_change", "tell")


@dataclass(frozen=True)
class WorldEvent:
    event_id: int
    tick: int
    etype: str
    location: str
    actors: tuple[str, ...]
    payload: dict
    scope: str = "public"

    def __post_init__(self):
        if self.etype not in ETYPES:
            raise ValueError(f"unknown event type: {self.etype}")
        if self.scope not in SCOPES:
            raise ValueError(f"unknown scope: {self.scope}")
        # "tell" must always carry an explicit source (invariant #4).
        if self.etype == "tell":
            if "speaker" not in self.payload or "listener" not in self.payload:
                raise ValueError("tell event requires speaker and listener")

    def to_dict(self) -> dict:
        d = asdict(self)
        d["actors"] = list(self.actors)
        return d


class Ledger:
    """Append-only sequence of WorldEvents. The single source of truth."""

    def __init__(self):
        self._events: list[WorldEvent] = []

    def append(self, tick: int, etype: str, location: str,
               actors: tuple[str, ...], payload: dict,
               scope: str = "public") -> WorldEvent:
        ev = WorldEvent(
            event_id=len(self._events), tick=tick, etype=etype,
            location=location, actors=tuple(actors), payload=payload,
            scope=scope,
        )
        self._events.append(ev)
        return ev

    @property
    def events(self) -> tuple[WorldEvent, ...]:
        return tuple(self._events)

    def __len__(self) -> int:
        return len(self._events)

    def content_hash(self) -> str:
        """Stable hash of the full ledger; used by the determinism tests."""
        blob = json.dumps([e.to_dict() for e in self._events],
                          sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode()).hexdigest()

    def to_json(self) -> list[dict]:
        return [e.to_dict() for e in self._events]
