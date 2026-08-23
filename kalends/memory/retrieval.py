"""Shared machinery for retrieval-style memories (vector, BM25, recency…).

All of these systems reduce to: score records against the query text, keep the
top-k above a floor, then answer each question type from the hit list. The
`pick` policy is the interesting knob: "top" answers from the most *similar*
hit (classic RAG — no time model), "recent" answers from the freshest accepted
hit (recency-aware retrieval).
"""
from __future__ import annotations

import math
import re
from collections import Counter

from .base import Answer, Experience, Query

TOKEN_RE = re.compile(r"[a-z]+")

# Scaffolding words shared by nearly every rendering/question; without removing
# them, similarity matches everything to everything.
STOPWORDS = {
    "the", "a", "an", "of", "is", "at", "i", "me", "my", "that", "to", "in",
    "with", "what", "own", "eyes", "saw", "told", "went", "hour", "did", "you",
    "your", "who", "or", "have", "heard", "anything", "about", "was", "it",
    "by", "for", "has", "since", "first", "changed", "believe", "and", "know",
    "current", "learn", "learned", "source", "as", "they", "say", "he", "she",
    "personally", "goes", "back", "would", "these", "days", "make", "do",
    "far", "now", "think", "state", "report", "asked", "if", "when",
}


def tokens(text: str) -> list[str]:
    return [t for t in TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]


def hits_answer(q: Query, hits: list[tuple[float, Experience]],
                pick: str = "top") -> Answer:
    """Answer a query from scored hits (sorted best-first).

    pick="top":    answer from the most similar propositional hit.
    pick="recent": answer from the freshest (max as_of, tick) accepted hit —
                   falls back to most similar if none is accepted.
    """
    prop_hits = [(s, e) for s, e in hits if e.value is not None]
    if not prop_hits:
        if q.qtype == "heard_of":
            return Answer(value="no", confidence=0.5)
        return Answer(value="unknown", confidence=0.0)

    if pick == "recent":
        accepted = [(s, e) for s, e in prop_hits if e.accepted]
        pool = accepted or prop_hits
        top_sim, top = max(pool, key=lambda p: (p[1].as_of, p[1].tick, p[0]))
    else:
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
    if q.qtype == "independent":
        origins = {(e.claimed_origin_kind, e.claimed_origin_event,
                    e.claimed_origin_observer)
                   for _, e in prop_hits if e.value == top.value}
        return Answer(value="yes" if len(origins) > 1 else "no",
                      confidence=top_sim)
    return Answer(value="unknown", confidence=0.0)


class BM25Index:
    """Minimal Okapi BM25 over experience texts (k1=1.5, b=0.75)."""

    def __init__(self):
        self._docs: list[tuple[Counter, int, Experience]] = []
        self._df: Counter = Counter()
        self._total_len = 0

    def add(self, exp: Experience) -> None:
        toks = Counter(tokens(exp.text))
        self._docs.append((toks, sum(toks.values()), exp))
        for t in toks:
            self._df[t] += 1
        self._total_len += sum(toks.values())

    def search(self, text: str, k: int) -> list[tuple[float, Experience]]:
        if not self._docs:
            return []
        qtoks = tokens(text)
        n = len(self._docs)
        avg_len = self._total_len / n or 1.0
        scored = []
        for toks, dlen, exp in self._docs:
            score = 0.0
            for t in qtoks:
                tf = toks.get(t, 0)
                if not tf:
                    continue
                idf = math.log(1 + (n - self._df[t] + 0.5) / (self._df[t] + 0.5))
                score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * dlen / avg_len))
            if score > 0:
                scored.append((score, exp))
        scored.sort(key=lambda p: (-p[0], -p[1].event_id))
        return scored[:k]
