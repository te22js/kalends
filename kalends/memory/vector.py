"""Vector-only memory: similarity retrieval over text renderings.

Embeddings are hashed bag-of-words vectors (stdlib-only, fully deterministic,
no network). This is a deliberately faithful miniature of RAG-style agent
memory: retrieval is by semantic-ish similarity with NO model of time,
supersession, or trust. Its expected failure modes (stale answers, ignoring
the accepted-flag, similarity distractors) are the point of the baseline.
"""
from __future__ import annotations

import hashlib
import math
import re

from .base import Answer, Experience, MemorySystem, Query

DIM = 512
TOKEN_RE = re.compile(r"[a-z]+")
SIM_THRESHOLD = 0.25   # below this, the system says "unknown"
TOP_K = 4

# Scaffolding words shared by nearly every rendering/question; without removing
# them, cosine similarity matches everything to everything.
STOPWORDS = {
    "the", "a", "an", "of", "is", "at", "i", "me", "my", "that", "to", "in",
    "with", "what", "own", "eyes", "saw", "told", "went", "hour", "did", "you",
    "your", "who", "or", "have", "heard", "anything", "about", "was", "it",
    "by", "for", "has", "since", "first", "changed", "believe", "and", "know",
    "current", "learn", "learned", "source",
}


def _tokens(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


def _embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for tok in _tokens(text):
        h = int(hashlib.md5(tok.encode()).hexdigest(), 16) % DIM
        vec[h] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cos(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


class VectorMemory(MemorySystem):
    name = "vector"

    def __init__(self):
        self._records: list[tuple[list[float], Experience]] = []

    def ingest(self, exp: Experience) -> None:
        self._records.append((_embed(exp.text), exp))

    def _retrieve(self, text: str) -> list[tuple[float, Experience]]:
        qv = _embed(text)
        scored = [(_cos(qv, v), e) for v, e in self._records]
        scored.sort(key=lambda p: (-p[0], -p[1].event_id))
        return [(s, e) for s, e in scored[:TOP_K] if s >= SIM_THRESHOLD]

    def answer(self, q: Query) -> Answer:
        hits = self._retrieve(q.text)
        # Only propositional records can answer propositional questions.
        prop_hits = [(s, e) for s, e in hits if e.value is not None]
        if not prop_hits:
            if q.qtype == "heard_of":
                return Answer(value="no", confidence=0.5)
            return Answer(value="unknown", confidence=0.0)
        top_sim, top = prop_hits[0]

        if q.qtype == "belief":
            return Answer(value=top.value, confidence=top_sim)
        if q.qtype == "heard_of":
            return Answer(value="yes", confidence=top_sim)
        if q.qtype == "source":
            src = "observed" if top.kind == "observed" else (top.source_agent or "unknown")
            return Answer(value=src, source_agent=top.source_agent, confidence=top_sim)
        if q.qtype == "learned_tick":
            return Answer(value=str(top.tick), confidence=top_sim)
        if q.qtype == "direct":
            return Answer(value="yes" if top.kind == "observed" else "no",
                          confidence=top_sim)
        if q.qtype == "superseded":
            values = {e.value for _, e in prop_hits}
            return Answer(value="yes" if len(values) > 1 else "no",
                          confidence=top_sim)
        return Answer(value="unknown", confidence=0.0)
