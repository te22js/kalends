"""Additional baselines. The hybrid thesis has to beat these to matter.

recency        - trivial floor: latest lexically-matching record wins.
bm25           - non-embedding lexical retrieval (classic IR).
vector_recency - vector retrieval, but answer from the freshest hit.
vector_meta    - vector retrieval with metadata filtering on the query key.
                 The important challenger: if this matches hybrid, the
                 symbolic layer of hybrid is doing nothing that a metadata
                 filter doesn't.
"""
from __future__ import annotations

from .base import Answer, Experience, MemorySystem, Query
from .retrieval import BM25Index, hits_answer, tokens
from .vector import VectorMemory


class RecencyMemory(MemorySystem):
    """Answer from the most recent record sharing >=1 content token with the
    query. The floor every sophisticated system must beat."""
    name = "recency"

    def __init__(self):
        self._records: list[tuple[set, Experience]] = []

    def ingest(self, exp: Experience) -> None:
        self._records.append((set(tokens(exp.text)), exp))

    def answer(self, q: Query) -> Answer:
        qtoks = set(tokens(q.text))
        matches = [(1.0, e) for toks, e in self._records if toks & qtoks]
        matches.sort(key=lambda p: (p[1].tick, p[1].event_id), reverse=True)
        return hits_answer(q, matches[:4], pick="recent")


class BM25Memory(MemorySystem):
    name = "bm25"
    pick = "top"

    def __init__(self):
        self._index = BM25Index()

    def ingest(self, exp: Experience) -> None:
        self._index.add(exp)

    def answer(self, q: Query) -> Answer:
        return hits_answer(q, self._index.search(q.text, 4), pick=self.pick)


class VectorRecencyMemory(VectorMemory):
    """Same retrieval as VectorMemory; answers from the freshest accepted hit
    instead of the most similar one."""
    name = "vector_recency"
    pick = "recent"


class VectorMetaMemory(VectorMemory):
    """Vector retrieval + metadata filtering + recency selection. A cheap
    practical architecture that removes most cross-proposition leakage without
    any symbolic belief table."""
    name = "vector_meta"
    pick = "recent"
    use_metadata = True
