"""Structured/symbolic memory: an explicit belief table keyed by proposition.

Keeps every exposure per (subject, predicate) key and answers with the latest
accepted one — i.e. it implements supersession and provenance retention
directly. Its known weakness is schema brittleness: text-only queries (alias
phrasings like "pistrinum" for "bakery") only resolve if the canonical subject
name appears in the query text; there is no fuzzy matching. Near-ceiling
scores on structured queries are expected BY CONSTRUCTION (it stores the same
fields the oracle does) — it serves as the solvability ceiling of the
benchmark, not as a discovery. See DECISIONS.md #7.
"""
from __future__ import annotations

import re

from .base import Answer, Experience, MemorySystem, Query

TOKEN_RE = re.compile(r"[a-z_]+")


class StructuredMemory(MemorySystem):
    name = "structured"

    def __init__(self):
        self._table: dict[tuple[str, str], list[Experience]] = {}

    def ingest(self, exp: Experience) -> None:
        if exp.subject is None or exp.predicate is None:
            return  # non-propositional episodes have no slot in the table
        self._table.setdefault((exp.subject, exp.predicate), []).append(exp)

    def _resolve(self, q: Query) -> list[Experience] | None:
        if q.subject is not None and q.predicate is not None:
            return self._table.get((q.subject, q.predicate))
        # Text-only query: exact token match against canonical key names only.
        toks = set(TOKEN_RE.findall(q.text.lower()))
        for (subject, predicate), entries in self._table.items():
            if subject.lower() in toks and predicate.lower() in toks:
                return entries
        return None

    @staticmethod
    def _current(entries: list[Experience]) -> Experience | None:
        accepted = [e for e in entries if e.accepted]
        if not accepted:
            return None
        return max(accepted, key=lambda e: (e.as_of, e.tick, e.event_id))

    def answer(self, q: Query) -> Answer:
        entries = self._resolve(q)
        if q.qtype == "heard_of":
            return Answer(value="yes" if entries else "no")
        if not entries:
            return Answer(value="unknown", confidence=0.0)
        cur = self._current(entries)
        if cur is None:
            # Heard claims but accepted none: no current belief.
            return Answer(value="unknown", confidence=0.0)

        if q.qtype == "belief":
            return Answer(value=cur.value, source_agent=cur.source_agent)
        if q.qtype == "source":
            src = "observed" if cur.kind == "observed" else (cur.source_agent or "unknown")
            return Answer(value=src, source_agent=cur.source_agent)
        if q.qtype == "learned_tick":
            return Answer(value=str(cur.tick))
        if q.qtype == "direct":
            return Answer(value="yes" if cur.kind == "observed" else "no")
        if q.qtype == "superseded":
            accepted = sorted((e for e in entries if e.accepted),
                              key=lambda e: (e.as_of, e.tick, e.event_id))
            values = [e.value for e in accepted]
            return Answer(value="yes" if len(set(values)) > 1 else "no")
        return Answer(value="unknown", confidence=0.0)
