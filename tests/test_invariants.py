"""Invariant tests: the epistemic guarantees the whole project rests on."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalends.epistemic import TRUST_THRESHOLD, EpistemicState
from kalends.propositions import Proposition
from kalends.scenarios import rumor
from kalends.scenarios.rumor import BAKERY, SILVER
from kalends.simulation import run_scenario
from kalends.world import project

SEED = 42


def _sim(seed=SEED):
    return run_scenario(rumor.build(), seed)


def test_determinism_same_seed_same_ledger():
    a, b = _sim(), _sim()
    assert a.ledger.content_hash() == b.ledger.content_hash()
    assert len(a.ledger) == len(b.ledger)


def test_different_seed_different_ledger():
    assert _sim(1).ledger.content_hash() != _sim(2).ledger.content_hash()


def test_projection_replay_matches_live_state():
    """Folding the finished ledger from the initial state must reproduce the
    exact state the simulation ended in (event sourcing works)."""
    sim = _sim()
    replayed = project(sim.ledger, sim.scenario.initial_state)
    assert replayed.facts == sim.state.facts
    assert replayed.agent_locations == sim.state.agent_locations


def test_knowledge_boundary_private_event():
    """Only actors of the private theft may know silver.status — until told.
    Every agent that knows must have a provenance chain rooting in an actor's
    observation."""
    sim = _sim()
    theft_actors = {"Felix", "Gaius"}
    for agent_id, eps in sim.epistemic.items():
        cur = eps.belief(SILVER)
        if cur is None:
            continue
        if cur.kind == "observed":
            assert agent_id in theft_actors, (
                f"{agent_id} claims to have observed the private theft")
        else:
            # Hearsay must bottom out in a real observation by an actor,
            # or in another agent's claim — never appear from nowhere.
            assert cur.source_agent is not None


def test_every_exposure_has_a_causal_event():
    """No agent knows anything that is not backed by a ledger event that the
    agent actually observed or that was a tell addressed to it."""
    sim = _sim()
    events = {e.event_id: e for e in sim.ledger.events}
    for agent_id, eps in sim.epistemic.items():
        for exposures in eps.exposures.values():
            for exp in exposures:
                ev = events[exp.event_id]
                if exp.kind == "observed":
                    assert agent_id in ev.actors or ev.scope == "public"
                else:
                    assert ev.etype == "tell"
                    assert ev.payload["listener"] == agent_id
                    assert ev.payload["speaker"] == exp.source_agent


def test_tell_always_has_source():
    sim = _sim()
    for ev in sim.ledger.events:
        if ev.etype == "tell":
            assert ev.payload.get("speaker")
            assert ev.payload.get("listener")


def test_belief_and_truth_are_separate_objects():
    """Changing canonical truth does not touch any agent's belief."""
    sim = _sim()
    before = {a: sim.epistemic[a].belief(BAKERY) for a in sim.epistemic}
    sim.state.facts["bakery.condition"] = "collapsed"  # mutate world truth
    after = {a: sim.epistemic[a].belief(BAKERY) for a in sim.epistemic}
    assert before == after


def test_stale_beliefs_exist():
    """The scenario must actually produce agents whose epistemically correct
    belief differs from world truth — otherwise the benchmark's stale
    dimension is vacuous."""
    sim = _sim()
    stale = [a for a, eps in sim.epistemic.items()
             if (b := eps.belief(BAKERY)) is not None
             and b.value != sim.state.facts["bakery.condition"]]
    assert stale, "no stale beliefs in the rumor scenario — scenario too easy"


def test_information_propagates():
    """Someone who was not at the bakery fire must end up with a hearsay
    belief about it (the whole point of the scenario)."""
    sim = _sim()
    hearsay = [a for a, eps in sim.epistemic.items()
               if (b := eps.belief(BAKERY)) is not None and b.kind == "told"]
    assert hearsay, "no information propagation occurred"
    # And each hearsay belief must have a chain of depth >= 1.
    for a in hearsay:
        assert sim.epistemic[a].belief(BAKERY).provenance.depth() >= 1


def test_distrusted_tell_is_recorded_but_rejected():
    eps = EpistemicState("A")
    p = Proposition("x", "y")
    eps.record_told(tick=5, prop=p, value="v1", event_id=0, speaker="B",
                    claimed_as_of=4, claimed_chain=None,
                    trust_in_speaker=TRUST_THRESHOLD - 0.1)
    assert eps.belief(p) is None          # not believed
    assert eps.has_heard_of(p)            # but the claim was heard


def test_newer_info_supersedes_older_but_not_vice_versa():
    eps = EpistemicState("A")
    p = Proposition("x", "y")
    eps.record_told(5, p, "old", 0, "B", claimed_as_of=3, claimed_chain=None,
                    trust_in_speaker=0.9)
    eps.record_told(6, p, "new", 1, "C", claimed_as_of=5, claimed_chain=None,
                    trust_in_speaker=0.9)
    assert eps.belief(p).value == "new"
    # A later tell carrying OLDER information must not clobber the newer belief.
    eps.record_told(9, p, "stale-echo", 2, "D", claimed_as_of=2,
                    claimed_chain=None, trust_in_speaker=0.9)
    assert eps.belief(p).value == "new"
    assert eps.was_superseded(p)
