"""The memory-system interface: the experimental surface of Kalends.

A MemorySystem receives one agent's Experience stream (exactly the information
the epistemic oracle says reached that agent — nothing more) and must later
answer queries about it. Different architectures (vector / structured / hybrid)
implement this same interface and are scored against the oracle by MemoryBench.

Design note: experiences carry both structured fields and a natural-language
`text` rendering. Structured memories use the fields; vector memories use the
text. The `accepted` flag records the agent's trust judgment at experience
time — retention and retrieval are what is under test here, not trust inference.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Experience:
    tick: int
    kind: str                       # "observed" | "told" | "episodic"
    subject: Optional[str]          # None for non-propositional episodes (e.g. moves)
    predicate: Optional[str]
    value: Optional[str]
    source_agent: Optional[str]     # speaker if kind == "told"
    as_of: int                      # origination tick of the information
    accepted: bool                  # the agent's trust judgment at the time
    event_id: int
    text: str                       # natural-language rendering
    # The speaker's honest claim about the chain root ("observed" if the info
    # traces back to an eyewitness) and which event that root was. Part of
    # communication content — enables independent-source accounting.
    claimed_origin_kind: Optional[str] = None
    claimed_origin_event: Optional[int] = None
    claimed_origin_observer: Optional[str] = None


# Query types (qtype):
#   "belief"       -> current value of (subject, predicate), or "unknown"
#   "heard_of"     -> "yes"/"no": did any info about the proposition reach me?
#   "source"       -> "observed" or the name of the agent who told me
#   "learned_tick" -> tick (as str) when the current belief was acquired
#   "direct"       -> "yes"/"no": is the current belief a direct observation?
#   "superseded"   -> "yes"/"no": did later info replace an earlier belief?
# If subject/predicate are None the query is text-only (e.g. alias phrasing)
# and the system must work from `text` alone.
@dataclass(frozen=True)
class Query:
    qtype: str
    text: str
    subject: Optional[str] = None
    predicate: Optional[str] = None


@dataclass(frozen=True)
class Answer:
    value: str                       # "unknown" is always a legal answer
    source_agent: Optional[str] = None
    confidence: float = 1.0


class MemorySystem:
    """Interface. Subclasses must be deterministic given the same stream."""

    name = "base"

    def ingest(self, exp: Experience) -> None:
        raise NotImplementedError

    def answer(self, q: Query) -> Answer:
        raise NotImplementedError
