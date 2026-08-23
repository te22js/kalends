"""Property-based / fuzzing tests: invariants over many RANDOM worlds.

These try to break the epistemic guarantees on generated scenarios (not just
the hand-built rumor world). Each test sweeps a set of configs x seeds chosen
to hit edge regions: dense gossip, heavy privacy, heavy distortion, long runs.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from kalends.counterfactual import belief_snapshot, compare
from kalends.propositions import Proposition, Provenance
from kalends.scenarios.generator import WorldConfig, generate
from kalends.simulation import run_scenario
from kalends.world import project

FUZZ_CONFIGS = [
    WorldConfig(name="fuzz_default"),
    WorldConfig(name="fuzz_dense", n_agents=10, n_locations=2,
                chattiness_min=0.7, chattiness_max=0.95, jitter_p=0.4),
    WorldConfig(name="fuzz_private", private_event_p=0.9, n_props=6),
    WorldConfig(name="fuzz_distort", distorter_frac=0.8,
                distrust_pair_frac=0.5),
    WorldConfig(name="fuzz_long", n_ticks=120, changes_min=5, changes_max=8),
]
FUZZ_SEEDS = [0, 1, 2]


def _worlds():
    for cfg in FUZZ_CONFIGS:
        for seed in FUZZ_SEEDS:
            yield cfg, seed, run_scenario(generate(cfg, seed), seed)


@pytest.mark.parametrize("cfg", FUZZ_CONFIGS, ids=lambda c: c.name)
def test_replay_determinism_fuzz(cfg):
    for seed in FUZZ_SEEDS:
        a = run_scenario(generate(cfg, seed), seed)
        b = run_scenario(generate(cfg, seed), seed)
        assert a.ledger.content_hash() == b.ledger.content_hash()
        assert belief_snapshot(a) == belief_snapshot(b)


def test_ledger_monotonic_and_projection():
    for cfg, seed, sim in _worlds():
        last_tick, last_id = -1, -1
        for ev in sim.ledger.events:
            assert ev.tick >= last_tick, f"{cfg.name}/{seed}: time went backwards"
            assert ev.event_id == last_id + 1
            last_tick, last_id = ev.tick, ev.event_id
        replayed = project(sim.ledger, sim.scenario.initial_state)
        assert replayed.facts == sim.state.facts
        assert replayed.agent_locations == sim.state.agent_locations


def test_epistemic_containment_fuzz():
    """No agent may hold knowledge not causally reachable: every exposure is
    backed by an event the agent was an actor of, could publicly co-observe,
    or a tell addressed to it — verified against a position replay."""
    for cfg, seed, sim in _worlds():
        events = {e.event_id: e for e in sim.ledger.events}
        # Reconstruct each agent's location at each event, by replay.
        positions_at_event: dict[int, dict[str, str]] = {}
        locs = dict(sim.scenario.initial_state.agent_locations)
        for ev in sim.ledger.events:
            if ev.etype == "move":
                locs[ev.actors[0]] = ev.payload["to"]
            positions_at_event[ev.event_id] = dict(locs)
        for agent_id, eps in sim.epistemic.items():
            for exposures in eps.exposures.values():
                for exp in exposures:
                    ev = events[exp.event_id]
                    if exp.kind == "observed":
                        if agent_id in ev.actors:
                            continue
                        assert ev.scope == "public", (
                            f"{cfg.name}/{seed}: {agent_id} observed private "
                            f"E{ev.event_id} without being an actor")
                        assert positions_at_event[ev.event_id][agent_id] == ev.location, (
                            f"{cfg.name}/{seed}: {agent_id} observed E{ev.event_id} "
                            f"from elsewhere")
                    else:
                        assert ev.etype == "tell"
                        assert ev.payload["listener"] == agent_id


def test_no_retrocausality_fuzz():
    """No provenance link may reference an event later than the delivering
    event; information can never originate in the future."""
    for cfg, seed, sim in _worlds():
        events = {e.event_id: e for e in sim.ledger.events}
        for eps in sim.epistemic.values():
            for exposures in eps.exposures.values():
                for exp in exposures:
                    assert exp.as_of <= exp.tick
                    node = exp.provenance
                    prev_id = None
                    while node is not None:
                        assert node.event_id in events
                        if prev_id is not None:
                            assert node.event_id <= prev_id, "future evidence cited"
                        prev_id = node.event_id
                        node = node.upstream


def test_provenance_links_reference_real_event_types():
    for cfg, seed, sim in _worlds():
        events = {e.event_id: e for e in sim.ledger.events}
        for eps in sim.epistemic.values():
            for exposures in eps.exposures.values():
                for exp in exposures:
                    node = exp.provenance
                    while node is not None:
                        ev = events[node.event_id]
                        if node.kind == "observed":
                            assert ev.etype in ("incident", "state_change")
                        else:
                            assert ev.etype == "tell"
                            assert ev.payload["speaker"] == node.source_agent
                        node = node.upstream


def test_supersession_preserves_history_fuzz():
    """Newer beliefs never erase the record of older exposures."""
    for cfg, seed, sim in _worlds():
        for eps in sim.epistemic.values():
            for key, exposures in eps.exposures.items():
                ids = [e.event_id for e in exposures]
                assert ids == sorted(ids)  # append-only, in arrival order


def test_shared_ancestry_counts_once():
    """Two reports relayed from the same witness are ONE line of evidence;
    a second independent witness makes two."""
    from kalends.epistemic import EpistemicState
    eps = EpistemicState("D")
    p = Proposition("x", "y")
    root = Provenance(kind="observed", event_id=10)  # A observed E10
    via_b = Provenance(kind="told", event_id=20, source_agent="A", upstream=root)
    via_c = Provenance(kind="told", event_id=21, source_agent="A", upstream=root)
    # B and C both relay A's observation to D.
    eps.record_told(5, p, "v", 30, "B", claimed_as_of=1,
                    claimed_chain=via_b, trust_in_speaker=0.9)
    eps.record_told(6, p, "v", 31, "C", claimed_as_of=1,
                    claimed_chain=via_c, trust_in_speaker=0.9)
    assert eps.independent_origins(p) == 1  # shared ancestry: one origin
    # An actual second witness (different observer, different event) adds one.
    eps.record_observation(7, p, "v", 40)
    assert eps.independent_origins(p) == 2


def test_counterfactual_only_causal_descendants_change():
    """Dropping an incident may only change beliefs about... anything, but the
    movement layer and unrelated random draws must be identical: event count
    differs by exactly the dropped incident minus tells whose content chain
    descended from it; and no NEW belief about an unrelated proposition may
    appear that differs for a non-descendant reason. We verify the cheap,
    exact half: move events are identical in both runs."""
    cfg = WorldConfig(name="cf_check")
    for seed in (0, 1):
        scenario = generate(cfg, seed)
        base = run_scenario(scenario, seed)
        from kalends.counterfactual import drop_incident
        cf = run_scenario(drop_incident(scenario, 0), seed)
        base_moves = [(e.tick, e.actors, e.payload["to"])
                      for e in base.ledger.events if e.etype == "move"]
        cf_moves = [(e.tick, e.actors, e.payload["to"])
                    for e in cf.ledger.events if e.etype == "move"]
        assert base_moves == cf_moves, "counterfactual perturbed movement"
        result = compare(scenario, seed, 0)
        dropped_prop = result["dropped_incident"]["prop"]
        # Belief changes about OTHER propositions are allowed only through
        # gossip displacement (a tell replaced by another); they must involve
        # agents who are also connected to changed communication, which we
        # approximate by requiring SOME tell-count change if any belief moved.
        if result["belief_changes"]:
            assert (result["n_tells"]["factual"]
                    != result["n_tells"]["counterfactual"]
                    or all(c["prop"] == dropped_prop
                           for c in result["belief_changes"]))
