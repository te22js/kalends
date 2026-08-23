"""Counterfactual analysis: rerun the same world minus one incident and diff
the epistemic outcome.

Because all randomness is context-keyed (rng.py), the two runs share every
draw: movement, gossip willingness, distortion coin-flips. The only differences
are causal descendants of the removed event — which agents end up believing
what, through which chains. This turns "which later beliefs causally descend
from event E?" into an exact computation, something transcript-based
benchmarks cannot do.

No grand causal-inference claims: this is intervention-by-deletion on a fully
specified generative process, i.e. the easy case. Its value is as a benchmark
generator (questions with exact causal ground truth) and an inspection tool.
"""
from __future__ import annotations

from dataclasses import replace

from .scenarios import Scenario
from .simulation import Simulation, run_scenario


def drop_incident(scenario: Scenario, index: int) -> Scenario:
    incidents = [inc for i, inc in enumerate(scenario.incidents) if i != index]
    return replace(scenario, incidents=incidents)


def belief_snapshot(sim: Simulation) -> dict[tuple[str, str], str | None]:
    """(agent, prop_key) -> believed value or None."""
    snap = {}
    for agent_id in sim.scenario.agent_ids():
        for prop in sim.scenario.propositions:
            b = sim.epistemic[agent_id].belief(prop)
            snap[(agent_id, prop.key)] = b.value if b else None
    return snap


def compare(scenario: Scenario, seed: int, drop_index: int) -> dict:
    base = run_scenario(scenario, seed)
    cf = run_scenario(drop_incident(scenario, drop_index), seed)
    dropped = scenario.incidents[drop_index]

    base_beliefs = belief_snapshot(base)
    cf_beliefs = belief_snapshot(cf)
    changed = []
    for key in sorted(base_beliefs):
        if base_beliefs[key] != cf_beliefs[key]:
            agent, prop_key = key
            changed.append({
                "agent": agent, "prop": prop_key,
                "factual_belief": base_beliefs[key],
                "counterfactual_belief": cf_beliefs[key],
            })

    base_tells = sum(1 for e in base.ledger.events if e.etype == "tell")
    cf_tells = sum(1 for e in cf.ledger.events if e.etype == "tell")
    return {
        "dropped_incident": {
            "index": drop_index, "tick": dropped.tick,
            "prop": dropped.prop.key, "value": dropped.value,
            "scope": dropped.scope, "location": dropped.location,
        },
        "n_events": {"factual": len(base.ledger), "counterfactual": len(cf.ledger)},
        "n_tells": {"factual": base_tells, "counterfactual": cf_tells},
        "belief_changes": changed,
        # Agents epistemically downstream of the dropped event:
        "causal_descendants": sorted({c["agent"] for c in changed}),
    }
