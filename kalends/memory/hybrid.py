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

    def __init__(self, structured_kwargs: dict | None = None,
                 use_vector_fallback: bool = True):
        self._structured = StructuredMemory(**(structured_kwargs or {}))
        self._vector = VectorMemory()
        self._use_vector_fallback = use_vector_fallback

    def ingest(self, exp: Experience) -> None:
        self._structured.ingest(exp)
        self._vector.ingest(exp)

    def answer(self, q: Query) -> Answer:
        ans = self._structured.answer(q)
        if not self._use_vector_fallback:
            return ans
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


class HybridGuardedMemory(HybridMemory):
    """Hybrid with an epistemically honest router — the design iteration the
    v1 ablations earned (results/ablations: the unguarded fallback is net
    NEGATIVE, and its boundary hallucinations dominate at scale).

    Rule: when the query carries a structured key, an empty belief table IS
    the answer ("I have no information about that") — falling back to
    similarity retrieval there manufactures knowledge out of adjacent
    memories. The vector path is consulted ONLY for text-only queries (alias
    phrasings), where the structured path genuinely has no opinion."""
    name = "hybrid_guarded"

    def answer(self, q: Query) -> Answer:
        ans = self._structured.answer(q)
        if q.subject is not None:
            return ans          # keyed query: the table's answer is the answer
        if ans.value == "unknown" and ans.confidence == 0.0:
            vec_ans = self._vector.answer(q)
            if vec_ans.value != "unknown":
                return vec_ans
        if q.qtype == "heard_of" and ans.value == "no":
            vec_ans = self._vector.answer(q)
            if vec_ans.value == "yes":
                return vec_ans
        return ans
