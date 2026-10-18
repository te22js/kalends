"""Existing Kalends memories behind one local-information decision rule.

All architectures see the same FIFO record budget and a keyed grain query.
Retrieval architectures keep their original top-4 retrieval. Structured stores
keep their exact-key lookup; diagnostic/gating support is capped at four too.
The structured encodings and trust flag are supplied, not inferred from text.
No policy receives WorldState or the evaluator's actual supply value.
"""
from __future__ import annotations

from typing import Sequence

from ..memory.base import Experience, Query
from ..memory.baselines import BM25Memory
from ..memory.hybrid import HybridGuardedMemory, HybridMemory
from ..memory.structured import StructuredMemory
from ..memory.vector import VectorMemory

QUERY = Query("belief", "What is the current grain supply?", "grain", "supply")
FACTORIES = {
    "structured": StructuredMemory,
    "bm25": BM25Memory,
    "hybrid": HybridMemory,
    "hybrid_guarded": HybridGuardedMemory,
    "vector": VectorMemory,
}


def root_signature(e: Experience) -> tuple:
    # A lineage label, not a claim of statistical independence in the world.
    if e.claimed_origin_event is None:
        return ("unattributed", e.event_id, e.source_agent)
    return (e.claimed_origin_kind, e.claimed_origin_event,
            e.claimed_origin_observer)


class MemoryDecisionPolicy:
    """Reserve on a disruption belief; otherwise defer or request inspection.

    `lineage` requires distinct origin labels, `source_count` is its deliberate
    ablation counting immediate senders. A direct current observation satisfies
    either gate. Inspections cost 1.5, arrive the following tick, and never
    retroactively repair the decision that requested them.
    """

    def __init__(self, memory="structured", gate="none", threshold=2, capacity=64):
        if memory not in FACTORIES:
            raise ValueError("unknown memory: " + str(memory))
        if gate not in ("none", "lineage", "source_count"):
            raise ValueError("unknown gate: " + str(gate))
        if threshold < 1 or capacity < 0:
            raise ValueError("threshold must be positive; capacity nonnegative")
        self.memory = memory
        self.gate = gate
        self.threshold = threshold
        self.capacity = capacity

    def _answer(self, records):
        mem = FACTORIES[self.memory]()
        for e in records:
            mem.ingest(e)
        ans = mem.answer(QUERY)
        if self.memory == "bm25":
            hits = mem._index.search(QUERY.text, 4)
            support = [e for _, e in hits]
        elif self.memory == "vector":
            support = [e for _, e in mem.retrieve(QUERY)]
        else:
            structured = mem if self.memory == "structured" else mem._structured
            entries = structured._resolve(QUERY) or []
            # Mirror the exact router used in HybridMemory.answer().
            structured_answer = structured.answer(QUERY)
            fallback = (self.memory == "hybrid" and
                        structured_answer.value == "unknown" and
                        structured_answer.confidence == 0.0)
            if fallback:
                support = [e for _, e in mem._vector.retrieve(QUERY)]
            else:
                # Include trusted repeated claims for corroboration diagnostics.
                # accepted=False in the base engine can mean merely same-as_of,
                # so exclude explicit distrust text but preserve honest repeats.
                current = structured._current(entries)
                pool = [e for e in entries if e.value == ans.value and
                        (e.accepted or "[trusted corroboration:" in e.text) and
                        (current is None or e.as_of == current.as_of)]
                support = sorted(pool, key=lambda e: (e.as_of, e.tick, e.event_id),
                                 reverse=True)[:4]
        return ans, support

    def decide(self, experiences: Sequence[Experience], tick: int, agent_id: str):
        local = list(experiences)
        records = local[-self.capacity:] if self.capacity else local
        ans, retrieved = self._answer(records)
        value = ans.value if ans.value in ("disrupted", "available") else "unknown"
        # Gating may use only the architecture's selected support, never a
        # shadow unbounded store. Wrong-proposition retrieval remains visible.
        support = [e for e in retrieved if e.value == value]
        roots = {root_signature(e) for e in support}
        sources = {e.source_agent or agent_id for e in support}
        direct = any(e.kind == "observed" and e.subject == "grain" and
                     e.predicate == "supply" for e in support)
        known = any(e.subject == "grain" and e.predicate == "supply" for e in local)
        boundary = value != "unknown" and not known
        correlated = len(sources) >= self.threshold and len(roots) < self.threshold
        evidence_count = len(roots) if self.gate == "lineage" else len(sources)
        allowed = self.gate == "none" or direct or evidence_count >= self.threshold
        if value == "disrupted":
            action = "reserve" if allowed else "verify"
        elif value == "unknown" and self.gate != "none":
            action = "verify"
        else:
            action = "defer"
        accepted = [e for e in local if e.subject == "grain" and
                    e.predicate == "supply" and e.accepted]
        normative = (max(accepted, key=lambda e: (e.as_of, e.tick, e.event_id)).value
                     if accepted else "unknown")
        return {
            "action": action, "predicted_value": value,
            "evidence_ids": [e.event_id for e in support],
            "root_count": len(roots), "source_count": len(sources),
            "boundary_violation": boundary,
            "source_independence_failure": correlated and action == "reserve",
            "qa_expected": normative, "qa_correct": value == normative,
            "retrieved_ids": [e.event_id for e in retrieved],
            "gate": self.gate, "threshold": self.threshold,
        }


class AlwaysDeferPolicy:
    """Sanity floor: never purchases and pays missed-shortage regret."""

    def decide(self, experiences, tick, agent_id):
        return {"action": "defer", "predicted_value": "unknown", "evidence_ids": [],
                "root_count": 0, "source_count": 0, "boundary_violation": False,
                "source_independence_failure": False}


class AlwaysVerifyPolicy(AlwaysDeferPolicy):
    """Sanity floor: consumes inspection cost at every opportunity."""

    def decide(self, experiences, tick, agent_id):
        return dict(super().decide(experiences, tick, agent_id), action="verify")
