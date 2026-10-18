"""Optional exact single-message deletion checks for live-city decisions.

This module is outside ActionBench's policy/evaluator path. Structural ancestry
selects a candidate; a fresh simulation and an actual queued-message deletion
then test the selected action. An unchanged action is an informative result.
"""
from __future__ import annotations

import argparse
import json
from collections import deque

from ..actionbench.policy import MemoryDecisionPolicy
from .scenario import CityConfig
from .simulation import CitySimulation

INTERPRETATION = (
    "Single message deletion test under this simulator; not minimal cause or "
    "proof across all possible interventions"
)


def _summary(decision):
    if decision is None:
        return {"action": "no_opportunity", "predicted_value": "not_evaluated",
                "loss": None, "event_id": None}
    return {key: decision[key] for key in ("action", "predicted_value", "loss", "event_id")}


def _find_decision(sim, agent, tick):
    matches = [d for d in sim.decisions if d["agent"] == agent and d["tick"] == tick]
    if len(matches) > 1:
        raise ValueError("decision semantic key is not unique")
    return matches[0] if matches else None


def _unsupported(reason, decision_event_id, original=None, message_event_id=None):
    return {"status": "unsupported", "supported": False, "reason": reason,
            "decision_event_id": decision_event_id, "message_event_id": message_event_id,
            "original": _summary(original) if original is not None else None,
            "altered": None, "changed_action": None, "interpretation": INTERPRETATION}


def verify_message_dependency(sim, decision_event_id, message_event_id=None):
    """Delete one structural queued ancestor and replay to the decision tick.

    The nearest ancestor uses the fewest parent links; newest event ID breaks
    ties. Only the original timeline and reproducible default memory policies
    are supported. The supplied simulation and all of its state remain intact.
    """
    if not isinstance(sim, CitySimulation) or sim.branch_id != "main":
        raise ValueError("dependency checks require the original city timeline")
    expected_policy = {
        "memory": sim.config.memory, "gate": sim.config.gate,
        "threshold": sim.config.threshold, "capacity": sim.config.capacity,
    }
    if (set(sim._policies) != set(sim.agent_ids) or
            any(type(policy) is not MemoryDecisionPolicy or vars(policy) != expected_policy
                for policy in sim._policies.values())):
        raise ValueError("dependency checks require reproducible default memory policies")
    if type(decision_event_id) is not int or not 0 <= decision_event_id < len(sim.ledger):
        raise ValueError("target must be an existing decision event id")
    event = sim.ledger.events[decision_event_id]
    if event.payload.get("category") != "decision" or len(event.actors) != 1:
        raise ValueError("target event must be a city decision")
    agent, tick = event.actors[0], event.tick
    original = _find_decision(sim, agent, tick)
    if original is None or original["event_id"] != decision_event_id:
        raise ValueError("target decision is missing its evaluator record")
    semantic_key = event.payload.get("semantic_key")
    if semantic_key != f"decision:{tick}:{agent}":
        raise ValueError("target decision has an invalid semantic key")
    graph = {e["event_id"]: e for e in sim.trace(decision_event_id)["events"]}
    distances, pending = {}, deque([(decision_event_id, 0)])
    while pending:
        candidate, distance = pending.popleft()
        if candidate in distances:
            continue
        distances[candidate] = distance
        for parent in graph[candidate].get("parents", []):
            if parent in graph:
                pending.append((parent, distance + 1))
    messages = [e for e in graph.values() if e.get("category") == "message_queued"]
    if message_event_id is None:
        if not messages:
            return _unsupported("The decision has no queued-message ancestor.",
                                decision_event_id, original)
        message = min(messages, key=lambda e: (distances[e["event_id"]], -e["event_id"]))
        message_event_id = message["event_id"]
    else:
        if type(message_event_id) is not int:
            raise ValueError("message target must be an integer queued ancestor id")
        message = graph.get(message_event_id)
        if message is None or message.get("category") != "message_queued":
            raise ValueError("message target must be a queued ancestor of this decision")
    boundary_tick = message["tick"]
    # Reconstruct the complete tick, including every event after the queue was
    # created. This is the actual supported fork boundary, not a mid-tick cut.
    replay = CitySimulation(sim.config).step(boundary_tick + 1)
    factual_prefix = [e.to_dict() for e in sim.ledger.events if e.tick <= boundary_tick]
    if replay.ledger.to_json() != factual_prefix:
        raise ValueError("the factual ledger prefix cannot be reproduced from its configuration")
    if not any(m["event_id"] == message_event_id for m in replay.messages):
        return _unsupported("The message is no longer pending at the completed-tick fork boundary.",
                            decision_event_id, original, message_event_id)
    prefix_hash, prefix_count = replay.ledger.content_hash(), len(replay.ledger)
    altered = replay.fork({"kind": "remove_message", "event_id": message_event_id})
    remaining = tick - boundary_tick
    if remaining < 0:
        raise ValueError("a queued ancestor cannot occur after its target decision")
    replay.step(remaining)
    altered.step(remaining)
    replay_decision = _find_decision(replay, agent, tick)
    if replay_decision is None or any(replay_decision[key] != original[key]
                                      for key in ("action", "predicted_value", "loss", "event_id")):
        raise ValueError("the factual decision cannot be reproduced before intervention")
    replay_event = replay.ledger.events[replay_decision["event_id"]]
    if replay_event.payload.get("semantic_key") != semantic_key:
        raise ValueError("the replay did not reproduce the decision semantic key")
    altered_decision = _find_decision(altered, agent, tick)
    original_summary, altered_summary = _summary(original), _summary(altered_decision)
    return {"status": "verified", "supported": True,
            "decision_event_id": decision_event_id, "decision_semantic_key": semantic_key,
            "agent": agent, "tick": tick, "message_event_id": message_event_id,
            "original": original_summary, "altered": altered_summary,
            "changed_action": original_summary["action"] != altered_summary["action"],
            "changed_prediction": original_summary["predicted_value"] != altered_summary["predicted_value"],
            "shared_prefix_hash": prefix_hash, "shared_prefix_count": prefix_count,
            "intervention": {"kind": "remove_message", "event_id": message_event_id,
                             "tick": boundary_tick},
            "selection": "fewest structural parent links; newest event id breaks ties",
            "interpretation": INTERPRETATION}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    sim = CitySimulation(CityConfig(seed=42)).run()
    decision = next(d for d in sim.decisions if d["agent"] == "Livia")
    print(json.dumps(verify_message_dependency(sim, decision["event_id"]), indent=2))


if __name__ == "__main__":
    main()
