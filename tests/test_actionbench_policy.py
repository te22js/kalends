"""Regression contracts for local-memory decisions, independent of the engine.

These tests exercise actual existing memory backends. They deliberately retain
their different routing/time behavior rather than expecting every backend to
behave like the structured ceiling.
"""
from dataclasses import replace
import inspect

import pytest

from kalends.actionbench.policy import (
    AlwaysDeferPolicy,
    AlwaysVerifyPolicy,
    FACTORIES,
    MemoryDecisionPolicy,
    QUERY,
)
from kalends.memory.base import Experience


MEMORIES = tuple(FACTORIES)


def claim(event_id=1, *, value="disrupted", tick=None, as_of=1,
          source="Courier", root=101, observer="Witness", accepted=True,
          kind="told", subject="grain", predicate="supply", text=None,
          corroboration=False):
    """A local claim; ground-truth supply is deliberately not represented."""
    rendered = text if text is not None else f"grain supply {value}"
    if corroboration:
        rendered += " [trusted corroboration: same claim, no new origin]"
    return Experience(
        tick=event_id if tick is None else tick,
        kind=kind, subject=subject, predicate=predicate, value=value,
        source_agent=source, as_of=as_of, accepted=accepted,
        event_id=event_id, text=rendered,
        claimed_origin_kind="observed", claimed_origin_event=root,
        claimed_origin_observer=observer,
    )


def filler(event_id):
    return Experience(
        tick=event_id, kind="episodic", subject=None, predicate=None,
        value=None, source_agent=None, as_of=event_id, accepted=True,
        event_id=event_id, text="walking through the baths",
    )


def decide(policy, records):
    return policy.decide(records, tick=20, agent_id="Merchant")


@pytest.mark.parametrize("memory", MEMORIES)
def test_adapter_answers_match_native_memory_on_identical_retained_records(memory):
    # The older direct observation is the strongest lexical match. Retrieval
    # can retain it; the structured path should instead retain the correction.
    records = [
        claim(1, kind="observed", source=None, text="grain supply disrupted"),
        claim(2, value="available", as_of=2,
              text="a lengthy correction: grain supply available after inspection"),
        claim(3, accepted=False, as_of=1, source="Relay",
              text="grain supply disrupted"),
    ]
    native = FACTORIES[memory]()
    for record in records:
        native.ingest(record)
    expected = native.answer(QUERY).value
    result = decide(MemoryDecisionPolicy(memory), records)
    assert result["predicted_value"] == expected
    assert result["action"] == ("reserve" if expected == "disrupted" else "defer")


@pytest.mark.parametrize("memory", ("structured", "hybrid", "hybrid_guarded"))
def test_one_origin_relayed_by_many_senders_is_one_lineage(memory):
    records = [
        claim(1, source="Courier"),
        claim(2, source="Trader", accepted=False, corroboration=True),
        claim(3, source="Resident", accepted=False, corroboration=True),
    ]
    by_lineage = decide(MemoryDecisionPolicy(memory, "lineage", 2), records)
    by_sender = decide(MemoryDecisionPolicy(memory, "source_count", 2), records)
    assert by_lineage["root_count"] == by_sender["root_count"] == 1
    assert by_lineage["source_count"] == by_sender["source_count"] == 3
    assert by_lineage["action"] == "verify"
    assert by_sender["action"] == "reserve"
    assert by_sender["source_independence_failure"]
    assert not by_lineage["source_independence_failure"]


def test_separate_root_labels_can_pass_lineage_gate_with_one_sender():
    # A courier may report two distinct eyewitness origins. The source-count
    # ablation intentionally discards that distinction in the other direction.
    records = [
        claim(1, root=101, observer="Witness A"),
        claim(2, root=102, observer="Witness B", accepted=False,
              corroboration=True),
    ]
    lineage = decide(MemoryDecisionPolicy("structured", "lineage", 2), records)
    source = decide(MemoryDecisionPolicy("structured", "source_count", 2), records)
    assert (lineage["root_count"], lineage["source_count"]) == (2, 1)
    assert lineage["action"] == "reserve"
    assert source["action"] == "verify"


def test_explicit_distrust_is_not_promoted_to_corroboration():
    records = [claim(1), claim(2, source="Distrusted", root=102,
                               accepted=False, text="grain supply disrupted; I did not believe it.")]
    result = decide(MemoryDecisionPolicy("structured", "lineage", 2), records)
    assert result["action"] == "verify"
    assert result["evidence_ids"] == [1]
    assert result["root_count"] == 1


@pytest.mark.parametrize("memory", MEMORIES)
@pytest.mark.parametrize("gate", ("lineage", "source_count"))
def test_direct_grain_observation_satisfies_gate_without_multiple_sources(memory, gate):
    direct = claim(1, kind="observed", source=None)
    result = decide(MemoryDecisionPolicy(memory, gate, threshold=5), [direct])
    assert result["action"] == "reserve"
    assert result["root_count"] == 1
    assert result["evidence_ids"] == [1]


def test_keyed_guard_blocks_cross_proposition_retrieval_fallback():
    # A lexically adjacent price record must not become supply knowledge.
    distractor = claim(1, subject="grain_market", predicate="price",
                       text="grain supply disrupted")
    naive = decide(MemoryDecisionPolicy("hybrid"), [distractor])
    guarded = decide(MemoryDecisionPolicy("hybrid_guarded"), [distractor])
    structured = decide(MemoryDecisionPolicy("structured"), [distractor])
    assert naive["action"] == "reserve"
    assert naive["predicted_value"] == "disrupted"
    assert naive["boundary_violation"]
    assert naive["retrieved_ids"] == [1]
    for result in (guarded, structured):
        assert result["action"] == "defer"
        assert result["predicted_value"] == "unknown"
        assert not result["boundary_violation"]
        assert result["evidence_ids"] == []


def test_hybrid_diagnostics_do_not_invent_fallback_for_confident_unknown_answer():
    records = [
        claim(1, value="unknown", text="grain supply status unresolved"),
        claim(2, subject="grain_market", predicate="price",
              text="grain supply disrupted"),
    ]
    result = decide(MemoryDecisionPolicy("hybrid"), records)
    assert result["predicted_value"] == "unknown"
    assert result["retrieved_ids"] == [1]


@pytest.mark.parametrize("memory", ("structured", "hybrid", "hybrid_guarded"))
def test_delivered_correction_supersedes_old_claim_despite_later_stale_relay(memory):
    records = [
        claim(1, as_of=1),
        claim(2, value="available", as_of=2, source="Inspector", root=202),
        claim(3, as_of=1, source="Slow relay", accepted=False,
              corroboration=True),
    ]
    result = decide(MemoryDecisionPolicy(memory, "lineage", 2), records)
    assert result["predicted_value"] == "available"
    assert result["action"] == "defer"
    assert result["evidence_ids"] == [2]
    assert result["qa_correct"]


@pytest.mark.parametrize("memory", MEMORIES)
def test_fifo_capacity_limits_actual_backend_ingestion_and_evidence(memory):
    # All architectures lose exactly the same information. Capacity pressure
    # must not silently leave a secondary full-history evidence store.
    records = [claim(1), filler(2), filler(3)]
    result = decide(MemoryDecisionPolicy(memory, capacity=2), records)
    assert result["predicted_value"] == "unknown"
    assert result["action"] == "defer"
    assert 1 not in result["retrieved_ids"]
    assert 1 not in result["evidence_ids"]
    # The evaluator may retain the full received information horizon even
    # though the memory under test has forgotten it.
    assert result["qa_expected"] == "disrupted"
    assert not result["qa_correct"]


@pytest.mark.parametrize("memory", MEMORIES)
def test_zero_capacity_uses_city_contract_of_unlimited_records(memory):
    result = decide(MemoryDecisionPolicy(memory, capacity=0), [claim(1)])
    assert result["predicted_value"] == "disrupted"
    assert result["retrieved_ids"] == [1]
    assert result["evidence_ids"] == [1]


@pytest.mark.parametrize("memory", MEMORIES)
def test_shared_experiment_budget_evicts_the_sixty_fifth_oldest_record(memory):
    records = [claim(1)] + [filler(i) for i in range(2, 66)]
    capped = decide(MemoryDecisionPolicy(memory, capacity=64), records)
    unlimited = decide(MemoryDecisionPolicy(memory, capacity=0), records)
    assert capped["predicted_value"] == "unknown"
    assert capped["retrieved_ids"] == []
    assert unlimited["predicted_value"] == "disrupted"


@pytest.mark.parametrize("memory", MEMORIES)
def test_gates_only_count_four_selected_support_records(memory):
    records = [claim(i, source=f"Sender {i}", root=100+i, observer=f"Witness {i}",
                     accepted=i == 1, corroboration=i != 1)
               for i in range(1, 8)]
    result = decide(MemoryDecisionPolicy(memory, "lineage", threshold=5), records)
    assert result["predicted_value"] == "disrupted"
    assert result["action"] == "verify"
    assert result["root_count"] <= 4
    assert len(result["evidence_ids"]) <= 4


@pytest.mark.parametrize("memory", MEMORIES)
def test_policy_has_no_world_argument_and_observation_only_decision_is_repeatable(memory):
    parameters = tuple(inspect.signature(MemoryDecisionPolicy.decide).parameters)
    assert parameters == ("self", "experiences", "tick", "agent_id")
    policy = MemoryDecisionPolicy(memory)
    record = claim(1)
    original = (record,)
    first = decide(policy, original)
    # An intervening call cannot plant knowledge in a hidden persistent store.
    decide(policy, [replace(record, value="available", event_id=2)])
    assert decide(policy, original) == first
    assert original == (record,)
    assert decide(policy, [])["predicted_value"] == "unknown"


@pytest.mark.parametrize("floor, expected_action", (
    (AlwaysDeferPolicy, "defer"), (AlwaysVerifyPolicy, "verify"),
))
def test_sanity_floors_keep_their_action_under_every_information_state(floor, expected_action):
    policy = floor()
    for records in ([], [claim(1)], [claim(1, value="available")]):
        result = decide(policy, records)
        assert result["action"] == expected_action
        assert result["predicted_value"] == "unknown"
        assert result["evidence_ids"] == []
        assert not result["boundary_violation"]


@pytest.mark.parametrize("kwargs", (
    {"memory": "oracle"}, {"gate": "global_truth"},
    {"threshold": 0}, {"capacity": -1},
))
def test_invalid_policy_configuration_is_rejected(kwargs):
    with pytest.raises(ValueError):
        MemoryDecisionPolicy(**kwargs)
