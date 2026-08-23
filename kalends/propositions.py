"""Propositions (units of belief) and Provenance (why a belief is held).

A Proposition is a (subject, predicate) key whose value can change over time,
e.g. ("bakery", "condition") -> "intact" | "burning" | "damaged" | "repaired".

Provenance is a linked chain answering "why does agent A believe P?":
    Observed(event_id)                          -- saw it directly
    Told(by, at_event, upstream)                -- heard it; upstream is the
                                                   speaker's *claimed* chain
Claimed chains matter: a speaker may pass on distorted information, and the
listener's provenance honestly records what they were told, not world truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Proposition:
    subject: str
    predicate: str

    @property
    def key(self) -> str:
        return f"{self.subject}.{self.predicate}"

    def __str__(self) -> str:
        return self.key


@dataclass(frozen=True)
class Provenance:
    """One link in a provenance chain."""
    kind: str                       # "observed" | "told"
    event_id: int                   # event through which the info arrived
    source_agent: Optional[str] = None      # who told us (kind == "told")
    upstream: Optional["Provenance"] = None  # the source's claimed chain

    def chain(self) -> list[str]:
        """Human-readable chain, outermost (this agent) first."""
        out = []
        node: Optional[Provenance] = self
        while node is not None:
            if node.kind == "observed":
                out.append(f"observed event E{node.event_id} directly")
            else:
                out.append(f"heard it from {node.source_agent} at E{node.event_id}")
            node = node.upstream
        return out

    def depth(self) -> int:
        """0 = direct observation, 1 = firsthand hearsay, etc."""
        d, node = 0, self.upstream
        while node is not None:
            d += 1
            node = node.upstream
        return d

    def root_kind(self) -> str:
        """'observed' if the chain bottoms out in an observation, else 'told'
        (an unterminated claim, e.g. the origin was itself hearsay)."""
        node: Provenance = self
        while node.upstream is not None:
            node = node.upstream
        return node.kind

    def to_dict(self) -> dict:
        return {
            "kind": self.kind,
            "event_id": self.event_id,
            "source_agent": self.source_agent,
            "upstream": self.upstream.to_dict() if self.upstream else None,
        }
