"""Bounded-capacity wrapper: any memory system under a record budget.

Unlimited stores make structured memory an unrealistic comparison for
long-lived agents. CappedMemory holds at most `cap` experiences under an
eviction policy and rebuilds the wrapped system from the surviving buffer.

Policies:
  fifo       - evict oldest experience regardless of content
  importance - evict in order: episodic filler first, then rejected hearsay,
               then accepted propositional records oldest-first. A deliberately
               simple, interpretable retention heuristic — not cognitive
               science.
"""
from __future__ import annotations

from .base import Answer, Experience, MemorySystem, Query


def _importance(exp: Experience) -> int:
    if exp.value is None:
        return 0            # episodic filler: first to go
    if not exp.accepted:
        return 1            # heard-but-distrusted claims
    if exp.kind == "observed":
        return 3            # direct observations: most protected
    return 2                # accepted hearsay


class CappedMemory(MemorySystem):
    def __init__(self, factory, cap: int, policy: str = "fifo"):
        self._factory = factory
        self._cap = cap
        self._policy = policy
        self._buffer: list[Experience] = []
        self._inner: MemorySystem | None = None
        self.name = f"{factory().name}@{cap}:{policy}"

    def ingest(self, exp: Experience) -> None:
        self._buffer.append(exp)
        if len(self._buffer) > self._cap:
            if self._policy == "fifo":
                self._buffer.pop(0)
            else:  # importance: evict lowest importance, oldest first
                victim = min(range(len(self._buffer)),
                             key=lambda i: (_importance(self._buffer[i]),
                                            self._buffer[i].tick, i))
                self._buffer.pop(victim)
        self._inner = None  # rebuilt lazily on next answer

    def answer(self, q: Query) -> Answer:
        if self._inner is None:
            self._inner = self._factory()
            for exp in self._buffer:
                self._inner.ingest(exp)
        return self._inner.answer(q)
