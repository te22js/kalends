"""Trace export: everything about one run, as plain JSON."""
from __future__ import annotations

import json

from .simulation import Simulation


def build_trace(sim: Simulation) -> dict:
    scenario = sim.scenario
    agents = {}
    for agent_id in scenario.agent_ids():
        eps = sim.epistemic[agent_id]
        beliefs = {}
        for prop in scenario.propositions:
            cur = eps.belief(prop)
            if cur is None:
                beliefs[prop.key] = None
                continue
            beliefs[prop.key] = {
                "value": cur.value,
                "kind": cur.kind,
                "source_agent": cur.source_agent,
                "learned_tick": cur.tick,
                "as_of": cur.as_of,
                "stale_vs_world": cur.value != sim.state.facts.get(prop.key),
                "provenance": cur.provenance.chain(),
            }
        agents[agent_id] = {
            "final_location": sim.state.agent_locations[agent_id],
            "beliefs": beliefs,
            "n_exposures": sum(len(v) for v in eps.exposures.values()),
            "n_experiences": len(sim.experiences[agent_id]),
        }
    return {
        "scenario": scenario.name,
        "seed": sim.seed,
        "n_ticks": scenario.n_ticks,
        "n_events": len(sim.ledger),
        "ledger_hash": sim.ledger.content_hash(),
        "world_facts": dict(sim.state.facts),
        "agents": agents,
        "events": sim.ledger.to_json(),
    }


def write_trace(sim: Simulation, path: str) -> None:
    with open(path, "w") as f:
        json.dump(build_trace(sim), f, indent=2)
