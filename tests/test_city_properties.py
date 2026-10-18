"""Metamorphic live-world properties across seeds, families and memory budgets."""
from dataclasses import asdict

import pytest

from kalends.city import CityConfig, CitySimulation


@pytest.mark.parametrize("seed", [0, 17, 42])
@pytest.mark.parametrize("family", ["rumour", "shortage", "recovery", "private"])
def test_identity_branch_and_step_partition_invariance_under_bounded_gated_memory(seed, family):
    config = CityConfig(seed=seed, family=family, capacity=8,
                        memory="hybrid_guarded", gate="lineage", threshold=2)
    original = CitySimulation(config).step(4)
    branch = original.fork({"kind": "none"})
    original.run()
    # Deliberately change API batching without changing the simulated clock.
    for count in (0, 1, 3, 2, 0, 7, 40):
        branch.step(count)
    fresh = CitySimulation(config).run()
    assert original.ledger.to_json() == branch.ledger.to_json() == fresh.ledger.to_json()
    assert original.decisions == branch.decisions == fresh.decisions
    assert asdict(original.economy) == asdict(branch.economy) == asdict(fresh.economy)
    assert original.experiences == branch.experiences == fresh.experiences
    assert original.compare(branch)["identical"]


def test_policy_cannot_cite_private_information_that_never_reached_its_agent():
    class UnobservedEvidencePolicy:
        def decide(self, experiences, tick, agent_id):
            # Event1 is the official's private grain observation in this family.
            return {"action": "reserve", "predicted_value": "disrupted", "evidence_ids": [1]}

    sim = CitySimulation(CityConfig(seed=42, family="private", communication_depth=0),
                         policy_factory=lambda *_: UnobservedEvidencePolicy())
    with pytest.raises(ValueError, match="evidence must have reached"):
        sim.step(3)
    assert not sim.decisions  # Livia is first; unauthorized proposal never executes.
    assert not any(e.payload.get("category") == "purchase" for e in sim.ledger.events)


def test_verification_is_delayed_and_each_purchase_conserves_stock_and_cash():
    sim = CitySimulation(CityConfig(seed=42, gate="lineage", threshold=2)).run()
    inspections = [e for e in sim.ledger.events if e.payload.get("category") == "inspection"]
    assert inspections
    for inspection in inspections:
        booking_decisions = [sim.ledger.events[p] for p in inspection.payload["parents"]
                             if sim.ledger.events[p].payload.get("category") == "decision"]
        assert len(booking_decisions) == 1
        assert inspection.tick == booking_decisions[0].tick + 1
        assert inspection.event_id > booking_decisions[0].event_id
    purchases = [e for e in sim.ledger.events if e.payload.get("category") == "purchase"]
    assert purchases
    for event in purchases:
        p = event.payload
        agent = event.actors[0]
        assert p["quantity"] >= 0
        assert p["inventory_delta"][agent] == p["quantity"] == -p["market_stock_delta"]
        assert p["cash_delta"][agent] == -p["quantity"] * p["unit_price"]
