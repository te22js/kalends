"""Inspectible role strategies operating on authorized bounded local views."""
from __future__ import annotations

from ..actionbench.policy import MemoryDecisionPolicy, root_signature


def effective_records(records):
    """Retractions consume ordinary FIFO slots; there is no shadow tombstone set."""
    roots = {(int(e.value), e.claimed_origin_observer) for e in records if e.kind == "retracted" and e.accepted
             and e.value is not None and str(e.value).lstrip("-").isdigit()}
    return [e for e in records if e.kind != "retracted" and
            (e.claimed_origin_event if e.claimed_origin_event is not None else e.event_id,
             e.claimed_origin_observer) not in roots]


def read_knowledge(records, config, tick, agent):
    effective = effective_records(records)
    adapter = MemoryDecisionPolicy(config.memory, config.gate, config.threshold, config.capacity)
    answer, hits = adapter._answer(effective)
    value = answer.value if answer.value in ("available", "disrupted") else "unknown"
    support = [e for e in hits if e.value == value]
    roots = {root_signature(e) for e in support}
    direct = any(e.kind == "observed" and e.subject == "grain" and e.predicate == "supply" for e in support)
    as_of = max((e.as_of for e in support), default=None)
    confidence = 0.0 if value == "unknown" else 1.0 if direct else min(answer.confidence, .45 + .15 * len(roots))
    if as_of is not None and tick - as_of > 8:
        confidence *= .65
    return {"value": value, "as_of": as_of, "tick": max((e.tick for e in support), default=None),
            "root_count": len(roots), "source_count": len({e.source_agent or agent for e in support}),
            "confidence": round(confidence, 4), "direct": direct,
            "evidence_ids": [e.event_id for e in support],
            "boundary_violation": value != "unknown" and not any(
                e.subject == "grain" and e.predicate == "supply" for e in effective)}


def preferences_for(role):
    prefs = {"caution": .65, "urgency_window": 2, "speculative_buffer": 0,
             "sharing_threshold": .7, "share_unverified": False, "procure_early": False}
    if role == "merchant":
        prefs.update(caution=.75)
    elif role in ("baker", "mill worker", "cook"):
        prefs.update(procure_early=True, caution=.3)
    elif role == "trader":
        prefs.update(speculative_buffer=2, caution=.35, cheap_price=6.0)
    elif role in ("courier", "porter"):
        prefs.update(share_unverified=True, sharing_threshold=0.0)
    elif role == "grain official":
        prefs.update(caution=.9, inspect_interval=6)
    return prefs


class GenesisPolicy:
    def __init__(self, config):
        self.config = config

    def decide_local(self, view, tick):
        belief = view["beliefs"]["grain.supply"]
        prefs, role = view["preferences"], view["role"]
        open_contracts = [c for c in view["commitments"] if c["status"] == "open"]
        next_contract = min(open_contracts, key=lambda c: c["deadline"]) if open_contracts else None
        due = next_contract["deadline"] - tick if next_contract else 10000
        quantity = next_contract["quantity"] if next_contract else 0
        deficit = max(0, quantity - view["inventory"])
        urgent = due <= prefs.get("urgency_window", 2)
        count = belief["root_count"] if self.config.gate == "lineage" else belief["source_count"]
        allowed = self.config.gate == "none" or belief["direct"] or count >= self.config.threshold
        action, reason = "defer", "Protect cash until a delivery or useful opportunity approaches."
        if role == "grain official" and (belief["as_of"] is None or tick - belief["as_of"] >= prefs.get("inspect_interval", 6)):
            action, reason = "verify", "Inspect deliveries as part of the official's information duty."
        elif deficit and (urgent or prefs.get("procure_early", False)):
            action, reason = "reserve", "Secure the grain required by my own upcoming delivery."
        elif role == "trader" and prefs.get("speculative_buffer", 0) > 0:
            quote = view.get("quoted_price")
            if quote is not None and quote <= prefs.get("cheap_price", 6) and allowed:
                action, reason = "reserve", "Accumulate a bounded inventory while my observed quote is inexpensive."
        elif deficit and belief["value"] == "disrupted":
            if allowed and belief["confidence"] >= prefs.get("caution", .65):
                action, reason = "reserve", "Act on the supply report admitted by my memory and evidence gate."
            else:
                action, reason = "verify", "Check a costly supply claim before an early purchase."
        elif deficit and belief["value"] == "unknown" and role == "merchant":
            action, reason = "verify", "I lack a remembered supply report and am not yet under deadline pressure."
        elif deficit and belief["value"] == "unknown" and self.config.gate != "none":
            action, reason = "verify", "The configured admission rule requests a local inspection."
        return {"action": action, "predicted_value": belief["value"], "reason": reason,
                "evidence_ids": list(belief["evidence_ids"]), "root_count": belief["root_count"],
                "source_count": belief["source_count"], "boundary_violation": belief["boundary_violation"]}
