"""Vector-only memory: similarity retrieval over text renderings.

Embeddings are hashed bag-of-words vectors (stdlib-only, fully deterministic,
no network). This is a deliberately faithful miniature of RAG-style agent
memory: retrieval is by similarity with NO model of time, supersession, or
trust. Its expected failure modes (stale answers, similarity distractors,
boundary hallucination) are the point of the baseline. Results labeled
"vector" mean "similarity-retrieval architecture", not "SOTA embeddings" —
see DECISIONS.md #6 and the EmbeddingAdapter hook below.
"""
from __future__ import annotations

import hashlib
import math

from .base import Answer, Experience, MemorySystem, Query
from .retrieval import hits_answer, tokens

DIM = 512
# Below this the system says "unknown". Calibrated down from 0.25 after told-
# renderings grew origin clauses (longer texts dilute cosine; see
# METHODOLOGY_AUDIT.md on fair baseline tuning).
SIM_THRESHOLD = 0.15
TOP_K = 4


def embed(text: str) -> list[float]:
    """Hashed bag-of-words embedding. Swap point for a real embedding model:
    any function text -> unit vector works (see DECISIONS.md #6); keep this
    deterministic fallback so results remain reproducible offline."""
    vec = [0.0] * DIM
    for tok in tokens(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16) % DIM
        vec[h] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def cosine(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class VectorMemory(MemorySystem):
    name = "vector"
    pick = "top"           # answer from the most SIMILAR hit (classic RAG)
    use_metadata = False   # if True, filter candidates by query subject/predicate

    def __init__(self):
        self._records: list[tuple[list[float], Experience]] = []

    def ingest(self, exp: Experience) -> None:
        self._records.append((embed(exp.text), exp))

    def _candidates(self, q: Query) -> list[tuple[list[float], Experience]]:
        if self.use_metadata and q.subject is not None:
            filtered = [(v, e) for v, e in self._records
                        if e.subject == q.subject and e.predicate == q.predicate]
            # Metadata filtering handles structured queries; text-only queries
            # (alias phrasings) fall back to the full pool.
            return filtered
        return self._records

    def retrieve(self, q: Query) -> list[tuple[float, Experience]]:
        qv = embed(q.text)
        scored = [(cosine(qv, v), e) for v, e in self._candidates(q)]
        scored.sort(key=lambda p: (-p[0], -p[1].event_id))
        return [(s, e) for s, e in scored[:TOP_K] if s >= SIM_THRESHOLD]

    def answer(self, q: Query) -> Answer:
        return hits_answer(q, self.retrieve(q), pick=self.pick)
