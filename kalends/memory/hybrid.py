"""Hybrid memory: structured table first, vector retrieval as fallback.

The hypothesis under test (NOT an assumption — the benchmark can falsify it):
structured storage handles supersession/provenance, vector retrieval handles
fuzzy phrasings, and routing between them keeps both strengths. The known risk
is that the router inherits vector memory's failure modes exactly when the
structured path misses — which the alias questions probe.
"""
from __future__ import annotations

from .base import Answer, Experience, MemorySystem, Query
from .structured import StructuredMemory
from .vector import VectorMemory


class HybridMemory(MemorySystem):
    name = "hybrid"

    def __init__(self):
        self._structured = StructuredMemory()
        self._vector = VectorMemory()

    def ingest(self, exp: Experience) -> None:
        self._structured.ingest(exp)
        self._vector.ingest(exp)

    def answer(self, q: Query) -> Answer:
        ans = self._structured.answer(q)
        # Route to vector retrieval only when the structured path found nothing
        # at all (an unresolved key). A confident structured "no"/"unknown"
        # backed by entries is a real answer, not a miss.
        if ans.value == "unknown" and ans.confidence == 0.0:
            vec_ans = self._vector.answer(q)
            if vec_ans.value != "unknown":
                return vec_ans
        if q.qtype == "heard_of" and ans.value == "no":
            vec_ans = self._vector.answer(q)
            if vec_ans.value == "yes":
                return vec_ans
        return ans
