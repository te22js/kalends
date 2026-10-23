"""Experience authoring rejects unsupported effects before a runtime is created."""
import copy
import json
from pathlib import Path
import sys
import types

import pytest

from kalends.experience_os.compiler import (
    ExperienceCompilerV1, ExperienceSpec, POMPEII_INITIAL, SPEC_DIR, SpecValidationError,
)


@pytest.fixture
def compiler():
    return ExperienceCompilerV1()


@pytest.fixture
def observatory():
    return json.loads((SPEC_DIR / "shared_observatory.json").read_text())


@pytest.fixture
def pompeii():
    return json.loads((SPEC_DIR / "pompeii_life.json").read_text())


def changed(document, path, value):
    document = copy.deepcopy(document)
    target = document
    for part in path[:-1]:
        target = target[part]
    target[path[-1]] = value
    return document


def test_both_specs_have_distinct_domain_rules_and_valid_boundaries(compiler):
    life = compiler.load(SPEC_DIR / "pompeii_life.json")
    commons = compiler.load(SPEC_DIR / "shared_observatory.json")
    assert life.setting["adapter"] == "pompeii"
    assert commons.setting["adapter"] == "commons"
    assert life.horizon_minutes == 120 * 1440
    assert commons.horizon_minutes == 90 * 1440
    assert "allocate" in commons.actions and "allocate" not in life.actions
    assert "deliver" in life.actions and "deliver" not in commons.actions
    assert commons.observations[0]["observers"] == ["team_b"]
    assert life.observations == []  # Existing world initializer owns its private evidence.


@pytest.mark.parametrize("name", ["pompeii_life", "shared_observatory"])
def test_real_compilation_reuses_continuity_primitives(compiler, name):
    from kalends.events import Ledger
    from kalends.genesis.simulation import GenesisEconomy
    from kalends.pompeii.temporal import EventClock
    from kalends.world import WorldState
    runtime = compiler.compile(SPEC_DIR / (name + ".json"))
    assert runtime.spec.id == name
    assert runtime.minute == 0
    assert len(runtime.world.ledger) > 0
    assert isinstance(runtime.world.ledger, Ledger) or type(runtime.world.ledger).__name__ == "PersistentLedger"
    assert isinstance(runtime.world.economy, GenesisEconomy)
    assert isinstance(runtime.world.state, WorldState)
    assert isinstance(runtime.world.clock, EventClock)
    if name == "pompeii_life":
        for actor, resources in POMPEII_INITIAL.items():
            assert runtime.world.economy.cash[actor] == resources["cash"]
            assert runtime.world.economy.inventory[actor] == resources["flour"]
    else:
        private = next(e for e in runtime.world.ledger.events if e.payload.get("category") == "condition")
        assert private.event_id in runtime.world.visible["team_b"]
        assert private.event_id not in runtime.world.visible["Player"]


def test_validated_spec_reads_and_exports_cannot_mutate_internal_contract(compiler, observatory):
    spec = compiler.validate(observatory)
    observatory["participants"][0]["resources"]["credits"] = 999
    exported = spec.to_dict()
    exported["setting"]["rules"]["capacity"] = 999
    read = spec.setting
    read["rules"]["capacity"] = 999
    assert spec.setting["rules"]["capacity"] == 12
    assert spec.participants[0]["resources"]["credits"] == 12
    with pytest.raises(AttributeError):
        _ = spec.no_such_field


@pytest.mark.parametrize("path,value,message", [
    (("version",), True, "version"),
    (("version",), 2, "version"),
    (("setting", "adapter"), "arbitrary_python", "adapters"),
    (("setting", "rules", "round_minutes"), 60, "one day"),
    (("setting", "rules", "rounds"), True, "integer"),
    (("setting", "rules", "capacity"), float("nan"), "finite"),
    (("setting", "rules", "capacity"), float("inf"), "finite"),
    (("setting", "rules", "quota"), 13, "cannot exceed"),
    (("setting", "rules", "inspection_cost"), 0, "between"),
    (("setting", "rules", "initial_condition"), "always_free", "stable or fragile"),
    (("horizon_minutes",), 90, "round_minutes"),
    (("termination", "at"), 129601, "between"),
    (("actions",), ["allocate", "wait", "mint_credits"], "unsupported actions"),
    (("actions",), ["allocate", "allocate", "wait"], "duplicate"),
    (("actions",), ["reserve"], "requires allocate and wait"),
    (("measures",), ["human_learning_proven"], "unimplemented"),
    (("participants", 0, "resources", "credits"), True, "integer"),
    (("participants", 0, "resources", "credits"), -1, "between"),
    (("participants", 0, "player"), "true", "only Player"),
    (("participants", 1, "id"), "team_unknown", "identities"),
    (("institutions", 0, "members"), ["Player", "team_unknown"], "unknown participant"),
    (("institutions", 0, "rule"), "mint_100_every_tick", "coordinator_quota"),
    (("institutions", 0, "capacity"), 13, "coordinator_quota"),
    (("observations", 0, "value"), "stable", "must match"),
    (("observations", 0, "observers"), ["Player"], "private access"),
    (("observations", 0, "at"), 1, "initial observations"),
    (("observations", 0, "kind"), "testimony", "executed share"),
    (("observations", 0, "subject"), "world_archive", "condition"),
    (("goals", 0, "actor"), "invisible_npc", "unknown participant"),
    (("goals", 0, "actor"), [], "unknown participant"),
    (("goals", 0, "deadline"), 60, "at least one day"),
    (("goals", 0, "target", "quantity"), 13, "fit capacity"),
    (("goals", 0, "target", "quantity"), 3, "minimum quota"),
    (("goals", 0, "target", "metric"), "write_world_state", "completed_rounds"),
    (("goals", 0, "requires"), ["unknown_goal"], "unknown prerequisite"),
    (("opportunities", 0, "at"), 129600, "between"),
    (("debrief", "transfer", "answer"), True, "integer"),
    (("debrief", "transfer", "answer"), 3, "between"),
    (("sources", 0, "url"), "javascript:alert(1)", "provenance reference"),
    (("sources", 0, "url"), "https://[invalid", "malformed provenance reference"),
    (("sources", 0, "kind"), "primary", "not a primary"),
])
def test_invalid_authoring_is_rejected(compiler, observatory, path, value, message):
    with pytest.raises(SpecValidationError, match=message):
        compiler.validate(changed(observatory, path, value))


@pytest.mark.parametrize("path,field,value", [
    ((), "state_patch", {"cash": 999999}),
    (("setting", "rules"), "credit_per_round", 100),
    (("participants", 0, "resources"), "unlimited_energy", 100),
    (("institutions", 0), "effects", {"grant_credits": 100}),
    (("observations", 0), "private_archive_access", True),
    (("goals", 0, "target"), "python_expression", "__import__('os')"),
    (("termination",), "eval", "while True"),
    (("debrief",), "invent_events", True),
])
def test_undefined_effects_cannot_enter_any_authoring_boundary(compiler, observatory, path, field, value):
    target = observatory
    for part in path:
        target = target[part]
    target[field] = value
    with pytest.raises(SpecValidationError, match="unsupported fields"):
        compiler.validate(observatory)


def test_goal_cycles_and_incompatible_prerequisite_deadlines_are_rejected(compiler, observatory):
    a, b = observatory["goals"][:2]
    a["requires"] = [b["id"]]
    b["requires"] = [a["id"]]
    with pytest.raises(SpecValidationError, match="circular"):
        compiler.validate(observatory)
    b["requires"] = []
    b["deadline"] = 2880
    with pytest.raises(SpecValidationError, match="deadline falls after"):
        compiler.validate(observatory)


def test_bounded_acyclic_dependency_is_permitted(compiler, observatory):
    observatory["goals"][1]["deadline"] = 2880
    observatory["goals"][1]["requires"] = [observatory["goals"][0]["id"]]
    assert compiler.validate(observatory).goals[1]["requires"] == ["survey_deadline"]


def test_duplicate_actors_and_initial_private_observations_are_rejected(compiler, observatory):
    doc = copy.deepcopy(observatory)
    doc["participants"].append(copy.deepcopy(doc["participants"][0]))
    with pytest.raises(SpecValidationError, match="duplicate actor"):
        compiler.validate(doc)
    doc = copy.deepcopy(observatory)
    doc["observations"].append(copy.deepcopy(doc["observations"][0]))
    with pytest.raises(SpecValidationError, match="duplicate observation"):
        compiler.validate(doc)


def test_oversized_finite_initial_pool_is_not_a_resource_generation_escape(compiler, observatory):
    for actor in observatory["participants"]:
        actor["resources"]["credits"] = 101
    with pytest.raises(SpecValidationError, match="exceeds 400"):
        compiler.validate(observatory)


def test_pompeii_initial_accounts_are_exact_legacy_adapter_accounts(compiler, pompeii):
    assert {r["id"]: r["resources"] for r in compiler.validate(pompeii).participants} == POMPEII_INITIAL
    pompeii["participants"][0]["resources"]["cash"] += 1
    with pytest.raises(SpecValidationError, match="exact existing Rebirth"):
        compiler.validate(pompeii)


def test_pompeii_cannot_inject_private_evidence(compiler, pompeii, observatory):
    pompeii["observations"] = observatory["observations"]
    with pytest.raises(SpecValidationError, match="preserved engine"):
        compiler.validate(pompeii)


def test_pompeii_time_must_match_existing_world_configuration(compiler, pompeii):
    pompeii["setting"]["rules"]["horizon_days"] = 90
    with pytest.raises(SpecValidationError, match="horizon_days"):
        compiler.validate(pompeii)


def test_direct_object_cannot_bypass_compile_validation(compiler, observatory):
    forged = ExperienceSpec(changed(observatory, ("actions",), ["mint_cash"]))
    with pytest.raises(SpecValidationError, match="unsupported actions"):
        compiler.compile(forged)


def test_compile_instantiates_lazy_runtime_with_validated_copy(compiler, observatory, monkeypatch):
    observed = []
    class Runtime:
        def __init__(self, spec, **kwargs):
            observed.append((spec, kwargs))
    monkeypatch.setitem(sys.modules, "kalends.experience_os.runtime", types.SimpleNamespace(ExperienceRuntime=Runtime))
    result = compiler.compile(observatory, checkpoint="test-only")
    assert isinstance(result, Runtime)
    assert isinstance(observed[0][0], ExperienceSpec)
    assert observed[0][1] == {"checkpoint": "test-only"}
    result = compiler.compile(SPEC_DIR / "pompeii_life.json")
    assert observed[1][0].setting["adapter"] == "pompeii"


@pytest.mark.parametrize("payload,message", [
    ('{"version":1,"version":1}', "duplicate JSON field"),
    ('{"number": NaN}', "nonfinite"),
    ('{"number": Infinity}', "nonfinite"),
    ('[', "invalid UTF-8 JSON"),
])
def test_json_loading_does_not_silently_normalize_ambiguous_documents(compiler, tmp_path, payload, message):
    path = tmp_path / "experience.json"
    path.write_text(payload)
    with pytest.raises(SpecValidationError, match=message):
        compiler.load(path)


def test_non_json_objects_and_deep_nesting_fail_as_authoring_errors(compiler, observatory):
    observatory["setting"]["rules"]["seed"] = {1, 2}
    with pytest.raises(SpecValidationError, match="JSON values"):
        compiler.validate(observatory)
    doc = []
    for _ in range(20):
        doc = [doc]
    with pytest.raises(SpecValidationError, match="deeply nested"):
        compiler.validate(doc)
