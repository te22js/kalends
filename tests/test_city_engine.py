"""Live-city invariants: exact forks, local information, and real consequences."""
import json
from dataclasses import asdict

import pytest

from kalends.actionbench.policy import AlwaysDeferPolicy, AlwaysVerifyPolicy
from kalends.city import CityConfig, CitySimulation
from kalends.city.policy import current_evidence, root_of
from kalends.city.scenario import supply_at
from kalends.city.simulation import CityEconomy, SUPPLY
from kalends.world import WorldState, apply_event


def test_identical_seed_and_identity_fork_have_identical_future_ledgers():
    baseline = CitySimulation(CityConfig(seed=42)).step(6)
    branch = baseline.fork({"kind": "none"})
    baseline.run()
    branch.run()
    fresh = CitySimulation(CityConfig(seed=42)).run()
    assert baseline.ledger.to_json() == branch.ledger.to_json() == fresh.ledger.to_json()
    assert baseline.decisions == branch.decisions
    assert baseline.compare(branch)["identical"]
    assert baseline.done and baseline.tick == 23
    assert all(d["opportunity_valid"] for d in baseline.decisions)


def test_exact_fork_prefix_and_whole_state_isolation():
    original = CitySimulation(CityConfig(seed=42)).step(2)
    prefix = original.ledger.to_json()
    queue = original.messages
    memories = {a: list(exps) for a, exps in original.experiences.items()}
    branch = original.fork({"kind": "correction", "agent": "Livia"})
    assert branch.ledger.to_json()[:len(prefix)] == prefix
    assert original.ledger.to_json() == prefix
    assert original.messages == queue
    assert original.experiences == memories
    assert branch.experiences["Livia"] is not original.experiences["Livia"]
    branch.step(4)
    assert original.tick == 1
    assert original.messages == queue
    assert original.experiences == memories


def test_grounded_correction_changes_action_and_economic_outcomes():
    baseline = CitySimulation(CityConfig(seed=42)).step(2)
    branch = baseline.fork({"kind": "correction", "agent": "Livia"})
    baseline.run()
    branch.run()
    first_base = next(d for d in baseline.decisions if d["agent"] == "Livia")
    first_branch = next(d for d in branch.decisions if d["agent"] == "Livia")
    assert first_base["action"] == "reserve"
    assert first_branch["action"] == "defer"
    assert first_base["actual_value"] == first_branch["actual_value"] == "available"
    assert baseline.economy.cash != branch.economy.cash
    changes = baseline.compare(branch)
    assert changes["changed_actions"] > 0 and changes["changed_agents"] > 0
    correction = next(e for e in branch.ledger.events if e.payload["category"] == "intervention_correction")
    assert correction.scope == "private" and correction.actors == ("Livia",)
    assert correction.location == "granary" and correction.payload["verification"]
    assert any(e.kind == "observed" and e.event_id == correction.event_id
               for e in branch.experiences["Livia"])
    for agent in branch.agent_ids:
        if agent != "Livia":
            assert not any(e.kind == "observed" and e.event_id == correction.event_id
                           for e in branch.experiences[agent])


def test_removing_and_replacing_pending_messages_are_real_continuations():
    baseline = CitySimulation(CityConfig(seed=42)).step(2)
    message = next(m for m in baseline.messages if m["listener"] == "Livia")
    removed = baseline.fork({"kind": "remove_message", "event_id": message["event_id"]}).step()
    replaced = baseline.fork({"kind": "replace_message", "event_id": message["event_id"],
                              "value": "available"}).step()
    assert not any(e.payload.get("queued_event") == message["event_id"] for e in removed.ledger.events)
    delivery = next(e for e in replaced.ledger.events if e.payload.get("queued_event") == message["event_id"])
    assert delivery.payload["value"] == "available"
    ancestors = replaced.trace(delivery.event_id)["ancestors"]
    assert any(e["category"] == "intervention_replace_message" for e in ancestors)
    exp = next(e for e in replaced.experiences["Livia"] if e.event_id == delivery.event_id)
    assert exp.claimed_origin_kind == "told"
    assert exp.claimed_origin_observer == "message intervention"


@pytest.mark.parametrize("intervention", [
    {"kind": "correction", "agent": "Nobody"},
    {"kind": "correction", "agent": "Livia", "value": "disrupted"},
    {"kind": "remove_message", "event_id": -1},
    {"kind": "replace_message", "event_id": -1, "value": "available"},
    {"kind": "oracle_edit"},
])
def test_invalid_interventions_leave_original_unchanged(intervention):
    sim = CitySimulation(CityConfig(seed=42)).step(2)
    before = json.dumps(sim.snapshot(), sort_keys=True)
    with pytest.raises(ValueError):
        sim.fork(intervention)
    assert json.dumps(sim.snapshot(), sort_keys=True) == before


def test_economy_and_world_replay_from_ledger():
    sim = CitySimulation(CityConfig(seed=19)).run()
    economy = CityEconomy()
    world = WorldState(agent_locations={a.agent_id: a.home for a in sim.specs})
    for event in sim.ledger.events:
        economy.apply(event)
        apply_event(world, event)
        for update in event.payload.get("relationship_updates", []):
            world.trust[(update["listener"], update["speaker"])] = update["value"]
    assert asdict(economy) == asdict(sim.economy)
    assert asdict(world) == asdict(sim.state)
    assert sim.economy.market_stock >= 0
    assert all(v >= 0 for v in sim.economy.inventory.values())
    assert any(e.payload["category"] == "purchase" for e in sim.ledger.events)
    assert any(e.payload["category"] == "commitment_settled" for e in sim.ledger.events)


def test_private_supply_and_nearby_reserve_do_not_create_supply_knowledge():
    sim = CitySimulation(CityConfig(seed=1, family="private", communication_depth=0)).step(3)
    assert any(e.subject == "grain" and e.predicate == "reserve" for e in sim.experiences["Gaius"])
    assert not any(e.subject == "grain" and e.predicate == "supply" for e in sim.experiences["Gaius"])
    assert sim.epistemic["Gaius"].belief(SUPPLY) is None
    decision = next(d for d in sim.decisions if d["agent"] == "Gaius")
    assert decision["predicted_value"] == "unknown"
    assert not decision["boundary_violation"]


def test_every_experience_has_a_local_observation_or_addressed_delivery():
    sim = CitySimulation(CityConfig(seed=42, gate="lineage", threshold=2)).run()
    locations = {a.agent_id: a.home for a in sim.specs}
    at_event = {}
    for event in sim.ledger.events:
        if event.etype == "move":
            locations[event.actors[0]] = event.payload["to"]
        at_event[event.event_id] = dict(locations)
        assert all(parent < event.event_id for parent in event.payload["parents"])
    for agent, experiences in sim.experiences.items():
        for exp in experiences:
            event = sim.ledger.events[exp.event_id]
            if exp.kind == "observed":
                assert (event.scope == "private" and agent in event.actors or
                        event.scope == "public" and at_event[event.event_id][agent] == event.location)
                if exp.subject == "grain" and exp.predicate == "supply":
                    assert at_event[event.event_id][agent] == event.location
            elif exp.kind == "told":
                assert event.etype == "tell"
                assert event.payload["listener"] == agent
                assert event.payload["speaker"] == exp.source_agent
    for decision in sim.decisions:
        local_ids = {e.event_id for e in sim.experiences[decision["agent"]] if e.tick <= decision["tick"]}
        assert set(decision["evidence_ids"]).issubset(local_ids)
        public_event = sim.ledger.events[decision["event_id"]]
        assert "actual_value" not in public_event.payload["decision"]
        assert "loss" not in public_event.payload["decision"]


def test_repeated_same_root_reports_are_preserved_without_new_origins():
    sim = CitySimulation(CityConfig(seed=42)).step(7)
    found = False
    for agent, experiences in sim.experiences.items():
        grouped = {}
        for exp in experiences:
            if exp.subject == "grain" and exp.predicate == "supply":
                grouped.setdefault(root_of(exp), []).append(exp)
        for root, entries in grouped.items():
            sources = {e.source_agent for e in entries if e.source_agent}
            if len(sources) > 1 and any(e.accepted for e in entries):
                found = True
                assert len({root_of(e) for e in entries}) == 1
                assert any("[trusted corroboration:" in e.text for e in entries)
                # Epistemic provenance agrees with the explicit Experience label.
                exposure = next(e for e in sim.epistemic[agent].exposures[SUPPLY.key]
                                if e.event_id == entries[-1].event_id)
                assert exposure.provenance.root_signature(agent) == root
                current, evidence = current_evidence(experiences)
                if current and root_of(current) == root and len({root_of(e) for e in evidence}) == 1:
                    assert sim.epistemic[agent].independent_origins(SUPPLY) == 1
    assert found, "scenario must exercise correlated repetition"


def test_world_truth_is_independent_of_policy_and_always_verify_costs_money():
    config = CityConfig(seed=13, family="shortage")
    defer = CitySimulation(config, lambda *_: AlwaysDeferPolicy()).run()
    verify = CitySimulation(config, lambda *_: AlwaysVerifyPolicy()).run()
    truth = lambda s: [(e.tick, e.payload["value"]) for e in s.ledger.events
                       if e.payload["category"] == "supply"]
    assert truth(defer) == truth(verify)
    assert sum(d["regret"] for d in defer.decisions) > 0
    assert sum(d["regret"] for d in verify.decisions) > 0
    assert all(not d["autonomous"] for d in verify.decisions + defer.decisions)
    assert all(d["loss"] == 1.5 for d in verify.decisions)
    assert any(e.payload["category"] == "inspection" for e in verify.ledger.events)
    values = {supply_at(CityConfig(seed=seed), 0) for seed in range(10)}
    assert values == {"available", "disrupted"}


def test_trace_is_structural_ancestry_and_includes_action_and_price():
    sim = CitySimulation(CityConfig()).run()
    purchase = next(e for e in sim.ledger.events if e.payload["category"] == "purchase")
    trace = sim.trace(purchase.event_id)
    categories = {e["category"] for e in trace["ancestors"]}
    assert {"decision", "price", "supply"}.issubset(categories)
    assert "causal necessity" in trace["interpretation"]
    with pytest.raises(ValueError):
        sim.trace(len(sim.ledger))


@pytest.mark.parametrize("kwargs", [{"n_agents": 1}, {"n_agents": 129}, {"n_ticks": True},
                                    {"seed": "42"}, {"gate": "oracle"}, {"memory": "magic"}])
def test_config_rejects_invalid_api_values(kwargs):
    with pytest.raises(ValueError):
        CityConfig(**kwargs)
