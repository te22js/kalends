"""Detached immutable history for cheap, isolated transactional world copies.

This is persistent-data-structure engineering, not a new simulation algorithm.
Live state is still deeply copied. Shared events have no mutable descendants;
normal exports and explicit copies of payload mappings are detached structures.
The cached hash is exactly the legacy Ledger canonical JSON SHA-256.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import hashlib
import json
import math
from types import MappingProxyType

from kalends.events import WorldEvent


class FrozenList(tuple):
    """Tuple storage with a list-origin marker for shape-preserving exports."""


class FrozenMapping(Mapping):
    """Read-only mapping whose explicit deepcopy yields a detached dict.

    Legacy economic projection deepcopies new_commitment into owned live state.
    It therefore needs a mutable *copy* while the source history stays sealed.
    """
    __slots__ = ("_data",)

    def __init__(self, value):
        object.__setattr__(self, "_data", MappingProxyType({key: freeze(item) for key, item in value.items()}))

    def __setattr__(self, name, value):
        raise TypeError("historical event payloads are immutable")

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return f"FrozenMapping({dict(self._data)!r})"

    def __deepcopy__(self, memo):
        result = thaw(self)
        memo[id(self)] = result
        return result


def freeze(value):
    if isinstance(value, FrozenMapping):
        return value
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError("event payload object keys must be strings")
        return FrozenMapping(value)
    if isinstance(value, FrozenList):
        return value
    if isinstance(value, list):
        return FrozenList(freeze(item) for item in value)
    if isinstance(value, tuple):
        return tuple(freeze(item) for item in value)
    if value is None or type(value) in (str, bool, int):
        return value
    if type(value) is float and math.isfinite(value):
        return value
    raise TypeError("event payloads require finite JSON-compatible data")


def thaw(value):
    if isinstance(value, Mapping):
        return {key: thaw(item) for key, item in value.items()}
    if isinstance(value, FrozenList):
        return [thaw(item) for item in value]
    if isinstance(value, tuple):
        return tuple(thaw(item) for item in value)
    return value


@dataclass(frozen=True)
class SealedWorldEvent(WorldEvent):
    def __post_init__(self):
        super().__post_init__()
        actors = tuple(self.actors)
        if (type(self.event_id) is not int or type(self.tick) is not int
                or not isinstance(self.location, str)
                or any(not isinstance(actor, str) for actor in actors)):
            raise TypeError("event identity, time, location and actors require immutable scalar values")
        object.__setattr__(self, "actors", actors)
        object.__setattr__(self, "payload", freeze(self.payload))

    def __deepcopy__(self, memo):
        memo[id(self)] = self
        return self

    def to_dict(self):
        return {"event_id": self.event_id, "tick": self.tick, "etype": self.etype,
                "location": self.location, "actors": list(self.actors),
                "payload": thaw(self.payload), "scope": self.scope}


class PersistentLedger:
    """Append-only sealed events with isolated list heads and streaming hash."""
    def __init__(self):
        self._events = []
        self._prefix_hash = hashlib.sha256(b"[")

    @classmethod
    def from_ledger(cls, ledger):
        result = cls()
        if isinstance(ledger, cls):
            result._events = list(ledger._events)
            result._prefix_hash = ledger._prefix_hash.copy()
            return result
        for event in ledger.events:
            sealed = SealedWorldEvent(event.event_id, event.tick, event.etype, event.location,
                                      tuple(event.actors), event.payload, event.scope)
            result._append_sealed(sealed)
        return result

    def _append_sealed(self, event):
        # Serialize before mutation: invalid values cannot partly append/hash.
        raw = json.dumps(event.to_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
        if self._events:
            self._prefix_hash.update(b",")
        self._prefix_hash.update(raw)
        self._events.append(event)
        return event

    def append(self, tick, etype, location, actors, payload, scope="public"):
        event = SealedWorldEvent(len(self._events), tick, etype, location,
                                 tuple(actors), payload, scope)
        return self._append_sealed(event)

    def __deepcopy__(self, memo):
        result = type(self)()
        memo[id(self)] = result
        result._events = list(self._events)
        result._prefix_hash = self._prefix_hash.copy()
        return result

    @property
    def events(self):
        return tuple(self._events)

    def __len__(self):
        return len(self._events)

    def content_hash(self):
        finished = self._prefix_hash.copy()
        finished.update(b"]")
        return finished.hexdigest()

    def to_json(self):
        return [event.to_dict() for event in self._events]
