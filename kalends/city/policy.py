"""A small local-only fallback policy; ActionBench may provide other adapters."""
from __future__ import annotations

from ..memory.base import Experience


def root_of(exp: Experience) -> tuple:
    return (exp.claimed_origin_kind or exp.kind,
            exp.claimed_origin_event if exp.claimed_origin_event is not None else exp.event_id,
            exp.claimed_origin_observer or exp.source_agent or "self")


def current_evidence(experiences: list[Experience]) -> tuple:
    relevant = [e for e in experiences if e.subject == "grain" and e.predicate == "supply"]
    accepted = [e for e in relevant if e.accepted]
    if not accepted:
        return None, []
    current = max(accepted, key=lambda e: (e.as_of, e.tick, e.event_id))
    evidence = [e for e in relevant if e.value == current.value and e.as_of == current.as_of
                and (e.accepted or "[trusted corroboration:" in e.text)]
    return current, evidence


class StructuredCityPolicy:
    """Use the latest accepted local claim; repeated roots remain one root.

    Trusted same-time repeats are eligible evidence even though the original
    epistemic oracle's strict freshness rule marks the exposure unaccepted.
    They never replace a newer claim or create a new origin.
    """
    def __init__(self, agent_id=None, config=None):
        self.config = config

    def decide(self, experiences, tick, agent_id):
        current, evidence = current_evidence(experiences)
        roots = {root_of(e) for e in evidence}
        sources = {e.source_agent or agent_id for e in evidence}
        value = current.value if current else "unknown"
        gate = getattr(self.config, "gate", "none")
        threshold = getattr(self.config, "threshold", 1)
        count = len(roots) if gate == "lineage" else len(sources)
        direct = bool(current and current.kind == "observed")
        gated = gate != "none" and count < threshold and not direct
        action = "verify" if value == "unknown" or gated else (
            "reserve" if value == "disrupted" else "defer")
        return {"action": action, "predicted_value": value,
                "evidence_ids": [e.event_id for e in evidence],
                "root_count": len(roots), "source_count": len(sources),
                "boundary_violation": False,
                "source_independence_failure": bool(gate == "source_count" and
                                                     len(sources) >= threshold > len(roots))}
