"""Structured memory that must PARSE its beliefs out of natural language.

Same belief-table architecture as StructuredMemory, but its ingest contract is
text-only: it never reads the structured fields of an Experience (by contract —
enforced in ingest below). Everything — proposition, value, time, source, trust
judgment, origin — is extracted from the rendering with regexes.

This is the system that turns the structured "ceiling" into a real system
under test: the gap between `structured` and `text_structured` measures how
much of structured memory's advantage was by-construction access to the
oracle's fields (METHODOLOGY_AUDIT.md).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .base import Answer, Experience, MemorySystem, Query

OBSERVED_RE = re.compile(
    r"^At hour (?P<tick>\d+) I saw with my own eyes that (?P<stmt>.+)\.$")
TOLD_RE = re.compile(
    r"^At hour (?P<tick>\d+) (?P<speaker>\w+) told me that "
    r"(?:as of hour (?P<as_of>\d+), )?(?P<stmt>.+?) \((?P<origin>.+?)\)\."
    r"(?P<distrust> I did not believe it\.)?$")
STMT_RE = re.compile(r"^the (?P<subject>.+?) is (?P<value>.+)$")
ORIGIN_SELF_RE = re.compile(r"^(?P<obs>\w+) saw it personally$")
ORIGIN_ROOT_RE = re.compile(r"^it goes back to (?P<obs>\w+) who saw it$")


@dataclass(frozen=True)
class ParsedRecord:
    tick: int
    as_of: int
    value: str
    kind: str                     # "observed" | "told"
    source: Optional[str]
    accepted: bool
    origin_kind: str              # "observed" | "told"
    origin_observer: Optional[str]
    order: int


class TextStructuredMemory(MemorySystem):
    name = "text_structured"

    def __init__(self):
        self._table: dict[str, list[ParsedRecord]] = {}
        self._n = 0

    def ingest(self, exp: Experience) -> None:
        text = exp.text  # contract: nothing else from exp is read
        self._n += 1
        m = OBSERVED_RE.match(text)
        if m:
            stmt = STMT_RE.match(m.group("stmt"))
            if not stmt:
                return
            tick = int(m.group("tick"))
            self._table.setdefault(stmt.group("subject"), []).append(
                ParsedRecord(tick=tick, as_of=tick, value=stmt.group("value"),
                             kind="observed", source=None, accepted=True,
                             origin_kind="observed", origin_observer="me",
                             order=self._n))
            return
        m = TOLD_RE.match(text)
        if m:
            stmt = STMT_RE.match(m.group("stmt"))
            if not stmt:
                return
            tick = int(m.group("tick"))
            as_of = int(m.group("as_of")) if m.group("as_of") else tick
            origin = m.group("origin")
            if ORIGIN_SELF_RE.match(origin):
                origin_kind, origin_obs = "observed", ORIGIN_SELF_RE.match(origin).group("obs")
            elif ORIGIN_ROOT_RE.match(origin):
                origin_kind, origin_obs = "observed", ORIGIN_ROOT_RE.match(origin).group("obs")
            else:
                origin_kind, origin_obs = "told", None
            self._table.setdefault(stmt.group("subject"), []).append(
                ParsedRecord(tick=tick, as_of=as_of, value=stmt.group("value"),
                             kind="told", source=m.group("speaker"),
                             accepted=m.group("distrust") is None,
                             origin_kind=origin_kind, origin_observer=origin_obs,
                             order=self._n))
        # anything else (moves, filler) has no propositional content

    def _resolve(self, q: Query) -> Optional[list[ParsedRecord]]:
        """Match the query to the known subject phrase with the largest
        content-token overlap (parsed subjects can be ornate, e.g. "fountain
        in the forum", while queries say just "fountain")."""
        from .retrieval import tokens
        qtoks = set(tokens(q.text))
        best, best_score = None, 0
        for subject in sorted(self._table):
            overlap = len(set(tokens(subject)) & qtoks)
            if overlap > best_score or (overlap == best_score and overlap
                                        and best and len(subject) > len(best)):
                best, best_score = subject, overlap
        return self._table[best] if best_score > 0 else None

    @staticmethod
    def _current(entries: list[ParsedRecord]) -> Optional[ParsedRecord]:
        accepted = [e for e in entries if e.accepted]
        if not accepted:
            return None
        return max(accepted, key=lambda e: (e.as_of, e.tick, e.order))

    def answer(self, q: Query) -> Answer:
        entries = self._resolve(q)
        if q.qtype == "heard_of":
            return Answer(value="yes" if entries else "no")
        if not entries:
            return Answer(value="unknown", confidence=0.0)
        cur = self._current(entries)
        if cur is None:
            return Answer(value="unknown", confidence=0.0)
        if q.qtype == "belief":
            return Answer(value=cur.value, source_agent=cur.source)
        if q.qtype == "source":
            return Answer(value="observed" if cur.kind == "observed"
                          else (cur.source or "unknown"))
        if q.qtype == "learned_tick":
            return Answer(value=str(cur.tick))
        if q.qtype == "direct":
            return Answer(value="yes" if cur.kind == "observed" else "no")
        if q.qtype == "superseded":
            accepted = sorted((e for e in entries if e.accepted),
                              key=lambda e: (e.as_of, e.tick, e.order))
            return Answer(value="yes" if len({e.value for e in accepted}) > 1
                          else "no")
        if q.qtype == "independent":
            origins = {(e.origin_kind,
                        "me" if e.origin_observer == "me" and e.kind == "observed"
                        else e.origin_observer)
                       for e in entries if e.accepted and e.value == cur.value}
            return Answer(value="yes" if len(origins) > 1 else "no")
        return Answer(value="unknown", confidence=0.0)
