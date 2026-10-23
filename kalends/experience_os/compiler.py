"""Strict, deliberately finite authoring surface for two existing world adapters.

An ExperienceSpec describes an experience; it is not an executable world patch.
Every executable rule, action, metric and initial observation is allowlisted.
The Pompeii adapter preserves the existing Rebirth initialization rather than
quietly applying authored cash or observations to an incompatible legacy save.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re
from typing import Any, Mapping
from urllib.parse import urlsplit


SPEC_DIR = Path(__file__).resolve().parents[2] / "specs"
TOP_FIELDS = frozenset({"version", "id", "title", "setting", "participants",
    "institutions", "observations", "goals", "actions", "opportunities",
    "horizon_minutes", "termination", "measures", "debrief", "sources"})
COMMONS_ACTIONS = frozenset({"reserve", "release", "share", "inspect", "commit", "allocate", "wait"})
COMMONS_MEASURES = frozenset({"completed_rounds", "failed_promises", "equity", "information_shared",
    "credits_spent", "unused_capacity", "elapsed_days"})
POMPEII_MEASURES = frozenset({"cash", "inventory", "reputation", "deliveries", "service_minutes",
    "completed_commissions", "elapsed_days", "fulfilled_obligations", "missed_obligations"})
POMPEII_INITIAL = {
    "Player": {"cash": 6, "flour": 0}, "Felix": {"cash": 28, "flour": 3},
    "Sabina": {"cash": 22, "flour": 2}, "Marcus": {"cash": 58, "flour": 6},
    "Chreste": {"cash": 0, "flour": 0}, "Dama": {"cash": 0, "flour": 0},
    "Lucius": {"cash": 52, "flour": 5},
}
COMMONS_ACTORS = frozenset({"Player", "team_a", "team_b", "team_c"})
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,79}$")


class SpecValidationError(ValueError):
    """An authoring error with its location in the specification."""


def _fail(path: str, message: str) -> None:
    raise SpecValidationError(f"{path}: {message}")


def _object(value: Any, path: str, required: set | frozenset,
            optional: set | frozenset = frozenset()) -> dict:
    if type(value) is not dict:
        _fail(path, "must be an object")
    unknown = set(value) - required - optional
    missing = required - set(value)
    if unknown:
        _fail(path, "unsupported fields: " + ", ".join(sorted(unknown)))
    if missing:
        _fail(path, "missing fields: " + ", ".join(sorted(missing)))
    return value


def _text(value: Any, path: str, limit: int = 600, *, identifier: bool = False) -> str:
    if type(value) is not str or not value.strip() or len(value) > limit:
        _fail(path, f"must be a nonempty string of at most {limit} characters")
    if identifier and not _ID.fullmatch(value):
        _fail(path, "must be a simple identifier")
    return value


def _number(value: Any, path: str, low: float, high: float, *, integer: bool = False) -> float:
    if type(value) not in ((int,) if integer else (int, float)) or not math.isfinite(value):
        _fail(path, "must be a finite " + ("integer" if integer else "number"))
    if not low <= value <= high:
        _fail(path, f"must be between {low} and {high}")
    return value


def _list(value: Any, path: str, maximum: int = 128, minimum: int = 0) -> list:
    if type(value) is not list or not minimum <= len(value) <= maximum:
        _fail(path, f"must be a list of {minimum}..{maximum} entries")
    return value


def _unique_strings(value: Any, path: str, maximum: int = 128, minimum: int = 0) -> list[str]:
    rows = _list(value, path, maximum, minimum)
    for i, item in enumerate(rows):
        _text(item, f"{path}[{i}]", identifier=True)
    if len(set(rows)) != len(rows):
        _fail(path, "duplicate entries")
    return rows


def _json_tree(value: Any, path: str = "$", depth: int = 0, count: list | None = None) -> None:
    """Reject non-JSON objects, cycles/depth attacks, nonfinite numbers and huge inputs."""
    count = [0] if count is None else count
    count[0] += 1
    if depth > 16 or count[0] > 12000:
        _fail(path, "specification is too deeply nested or too large")
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        if abs(value) > 10**12 or not math.isfinite(value):
            _fail(path, "number must be finite and within the authoring bound")
    elif type(value) is str:
        if len(value) > 8000:
            _fail(path, "string is too long")
    elif type(value) is list:
        for i, item in enumerate(value):
            _json_tree(item, f"{path}[{i}]", depth + 1, count)
    elif type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                _fail(path, "object keys must be strings")
            _json_tree(item, f"{path}.{key}", depth + 1, count)
    else:
        _fail(path, "must contain only JSON values")


@dataclass(frozen=True)
class ExperienceSpec:
    """Validated JSON value object. Attribute reads return independent copies.

    The compiler revalidates even an ExperienceSpec before instantiation, so
    constructing this type directly cannot bypass validation at the boundary.
    """
    _document: dict

    def to_dict(self) -> dict:
        return copy.deepcopy(self._document)

    def __getattr__(self, name: str) -> Any:
        if name in TOP_FIELDS:
            return copy.deepcopy(self._document[name])
        raise AttributeError(name)


class ExperienceCompilerV1:
    """Compile finite ExperienceSpec V1 files into the shared experience runtime."""

    def validate(self, mapping: Mapping[str, Any]) -> ExperienceSpec:
        if isinstance(mapping, ExperienceSpec):
            mapping = mapping.to_dict()
        _json_tree(mapping)
        doc = _object(mapping, "$", TOP_FIELDS)
        if type(doc["version"]) is not int or doc["version"] != 1:
            _fail("$.version", "only ExperienceSpec version 1 is supported")
        _text(doc["id"], "$.id", identifier=True)
        _text(doc["title"], "$.title", 160)
        setting = _object(doc["setting"], "$.setting", {"adapter", "rules"})
        adapter = setting["adapter"]
        if adapter not in ("pompeii", "commons"):
            _fail("$.setting.adapter", "supported adapters are pompeii and commons")
        horizon = _number(doc["horizon_minutes"], "$.horizon_minutes", 1, 365*1440, integer=True)
        self._rules(setting["rules"], adapter, horizon)
        end = _object(doc["termination"], "$.termination", {"at"})["at"]
        _number(end, "$.termination.at", 1, horizon, integer=True)
        rules = setting["rules"]
        actors = self._participants(doc["participants"], adapter)
        institutions = self._institutions(doc["institutions"], actors, adapter, rules)
        self._observations(doc["observations"], actors, institutions, adapter, rules)
        measures = _unique_strings(doc["measures"], "$.measures", 20, 1)
        supported = COMMONS_MEASURES if adapter == "commons" else POMPEII_MEASURES
        if set(measures) - supported:
            _fail("$.measures", "contains unimplemented outcome measures")
        self._goals(doc["goals"], actors, adapter, rules, end)
        actions = _unique_strings(doc["actions"], "$.actions", 64, 1)
        if adapter == "pompeii":
            from kalends_rebirth.language import ACTIONS
            supported_actions = set(ACTIONS) | {"move", "wait"}
        else:
            supported_actions = COMMONS_ACTIONS
        if set(actions) - supported_actions:
            _fail("$.actions", "contains unsupported actions; arbitrary state effects are prohibited")
        if adapter == "commons" and not {"allocate", "wait"}.issubset(actions):
            _fail("$.actions", "commons requires allocate and wait to execute and settle a round")
        opportunities = _list(doc["opportunities"], "$.opportunities", 128, 1)
        previous = -1
        for i, row in enumerate(opportunities):
            path = f"$.opportunities[{i}]"
            _object(row, path, {"at", "label"})
            at = _number(row["at"], path + ".at", 0, end - 1, integer=True)
            if at < previous:
                _fail(path + ".at", "opportunities must be in chronological order")
            previous = at
            _text(row["label"], path + ".label")
        self._debrief(doc["debrief"])
        self._sources(doc["sources"])
        return ExperienceSpec(copy.deepcopy(doc))

    @staticmethod
    def _rules(rules: Any, adapter: str, horizon: int) -> None:
        if adapter == "pompeii":
            _object(rules, "$.setting.rules", {"seed", "horizon_days"},
                {"memory_capacity", "information_policy", "communication"})
            _number(rules["horizon_days"], "$.setting.rules.horizon_days", 1, 365, integer=True)
            if horizon != rules["horizon_days"] * 1440:
                _fail("$.horizon_minutes", "must equal the Pompeii horizon_days in minutes")
            if "memory_capacity" in rules:
                _number(rules["memory_capacity"], "$.setting.rules.memory_capacity", 4, 256, integer=True)
            if "information_policy" in rules and rules["information_policy"] not in ("cautious", "credulous"):
                _fail("$.setting.rules.information_policy", "unsupported policy")
            if "communication" in rules and type(rules["communication"]) is not bool:
                _fail("$.setting.rules.communication", "must be boolean")
        else:
            _object(rules, "$.setting.rules", {"seed", "round_minutes", "capacity", "rounds",
                "quota", "inspection_cost", "maintenance_interval", "initial_condition"})
            if type(rules["round_minutes"]) is not int or rules["round_minutes"] != 1440:
                _fail("$.setting.rules.round_minutes", "commons V1 rounds are exactly one day")
            for key, low, high in (("capacity", 3, 120), ("rounds", 1, 365),
                ("quota", 1, 40), ("inspection_cost", 1, 100), ("maintenance_interval", 1, 90)):
                _number(rules[key], "$.setting.rules." + key, low, high, integer=True)
            if rules["quota"] > rules["capacity"]:
                _fail("$.setting.rules.quota", "a project's quota cannot exceed nominal daily capacity")
            if rules["initial_condition"] not in ("stable", "fragile"):
                _fail("$.setting.rules.initial_condition", "must be stable or fragile")
            if horizon != rules["round_minutes"] * rules["rounds"]:
                _fail("$.horizon_minutes", "must equal round_minutes multiplied by rounds")
        _number(rules["seed"], "$.setting.rules.seed", 0, 2**31-1, integer=True)

    @staticmethod
    def _participants(rows: Any, adapter: str) -> set[str]:
        rows = _list(rows, "$.participants", 16, 1)
        seen = set()
        for i, row in enumerate(rows):
            path = f"$.participants[{i}]"
            _object(row, path, {"id", "role", "player", "resources"})
            actor = _text(row["id"], path + ".id", identifier=True)
            if actor in seen:
                _fail(path + ".id", "duplicate actor")
            seen.add(actor)
            _text(row["role"], path + ".role", 160)
            if type(row["player"]) is not bool or row["player"] != (actor == "Player"):
                _fail(path + ".player", "only Player is the player-controlled participant")
            resource_keys = {"credits"} if adapter == "commons" else {"cash", "flour"}
            resources = _object(row["resources"], path + ".resources", resource_keys)
            for key, value in resources.items():
                _number(value, path + ".resources." + key, 0, 10000,
                    integer=key in ("credits", "flour"))
            if adapter == "pompeii" and resources != POMPEII_INITIAL.get(actor):
                _fail(path + ".resources", "Pompeii preserves exact existing Rebirth initial accounts")
        expected = COMMONS_ACTORS if adapter == "commons" else set(POMPEII_INITIAL)
        if seen != expected:
            _fail("$.participants", "adapter requires its exact supported participant identities")
        if adapter == "commons" and sum(r["resources"]["credits"] for r in rows) > 400:
            _fail("$.participants", "initial finite inspection credit pool exceeds 400")
        return seen

    @staticmethod
    def _institutions(rows: Any, actors: set[str], adapter: str, rules: dict) -> set[str]:
        rows = _list(rows, "$.institutions", 16, 1)
        seen = set()
        for i, row in enumerate(rows):
            path = f"$.institutions[{i}]"
            _object(row, path, {"id", "members", "capacity", "rule"})
            ident = _text(row["id"], path + ".id", identifier=True)
            if ident in seen or ident in actors:
                _fail(path + ".id", "institution identity must be unique")
            seen.add(ident)
            members = _unique_strings(row["members"], path + ".members", 16, 1)
            if set(members) - actors:
                _fail(path + ".members", "references an unknown participant")
            _number(row["capacity"], path + ".capacity", 1, 10000, integer=True)
            if adapter == "commons":
                if ident != "consortium" or set(members) != actors or row["rule"] != "coordinator_quota" or row["capacity"] != rules["capacity"]:
                    _fail(path, "commons supports the consortium coordinator_quota capacity rule only")
            elif row["rule"] != "legacy_household_service" or ident != "household" or set(members) != {"Player", "Dama", "Lucius"} or row["capacity"] != 120:
                _fail(path, "Pompeii institution must describe the existing 120-minute household service rule")
        if len(rows) != 1:
            _fail("$.institutions", "this adapter supports exactly one declared institution")
        return seen

    @staticmethod
    def _observations(rows: Any, actors: set[str], institutions: set[str], adapter: str, rules: dict) -> None:
        rows = _list(rows, "$.observations", 128)
        if adapter == "pompeii" and rows:
            _fail("$.observations", "Pompeii observations are initialized by the preserved engine, not authored patches")
        seen = set()
        for i, row in enumerate(rows):
            path = f"$.observations[{i}]"
            _object(row, path, {"id", "subject", "predicate", "value", "at", "observers", "kind"}, {"source"})
            ident = _text(row["id"], path + ".id", identifier=True)
            if ident in seen:
                _fail(path + ".id", "duplicate observation")
            seen.add(ident)
            if row["subject"] != "observatory" or row["predicate"] != "condition":
                _fail(path, "commons permits the observatory.condition observation only")
            if type(row["at"]) is not int or row["at"] != 0:
                _fail(path + ".at", "only initial observations may be authored")
            if row["value"] != rules["initial_condition"]:
                _fail(path + ".value", "initial direct observation must match the configured hardware condition")
            observers = _unique_strings(row["observers"], path + ".observers", 1, 1)
            if observers != ["team_b"]:
                _fail(path + ".observers", "only the maintenance team team_b has initial private access")
            if row["kind"] != "direct" or "source" in row:
                _fail(path, "initial hardware evidence must be direct; testimony requires an executed share")
        if adapter == "commons" and len(rows) != 1:
            _fail("$.observations", "commons requires exactly one private initial maintenance observation")

    @staticmethod
    def _goals(rows: Any, actors: set[str], adapter: str, rules: dict, end: int) -> None:
        rows = _list(rows, "$.goals", 64, 1)
        goals = {}
        for i, row in enumerate(rows):
            path = f"$.goals[{i}]"
            _object(row, path, {"id", "actor", "label", "priority", "deadline", "requires", "target"})
            ident = _text(row["id"], path + ".id", identifier=True)
            if ident in goals:
                _fail(path + ".id", "duplicate goal")
            goals[ident] = row
            if type(row["actor"]) is not str or row["actor"] not in actors:
                _fail(path + ".actor", "unknown participant")
            _text(row["label"], path + ".label")
            _number(row["priority"], path + ".priority", 0, 100)
            _number(row["deadline"], path + ".deadline", 1, end, integer=True)
            _unique_strings(row["requires"], path + ".requires", 64)
            target = _object(row["target"], path + ".target", {"resource", "quantity", "metric"})
            _number(target["quantity"], path + ".target.quantity", 1, 10000, integer=True)
            if adapter == "commons":
                if target["resource"] != "capacity" or target["metric"] != "completed_rounds":
                    _fail(path + ".target", "commons target is completed_rounds requiring capacity")
                if target["quantity"] > rules["capacity"] or target["quantity"] < rules["quota"]:
                    _fail(path + ".target.quantity", "project target must fit capacity and meet the fixed minimum quota")
                if row["deadline"] < rules["round_minutes"]:
                    _fail(path + ".deadline", "a completed research round requires at least one day")
            elif target["resource"] not in ("flour", "cash") or type(target["metric"]) is not str or target["metric"] not in POMPEII_MEASURES:
                _fail(path + ".target", "unsupported Pompeii resource or outcome metric")
        visiting, visited = set(), set()
        def visit(ident: str) -> None:
            if ident in visiting:
                _fail("$.goals", "circular goal dependency")
            if ident in visited:
                return
            visiting.add(ident)
            row = goals[ident]
            for required in row["requires"]:
                if required not in goals:
                    _fail("$.goals", "unknown prerequisite goal " + required)
                if goals[required]["deadline"] > row["deadline"]:
                    _fail("$.goals", "prerequisite deadline falls after its dependent goal")
                visit(required)
            visiting.remove(ident)
            visited.add(ident)
        for ident in goals:
            visit(ident)

    @staticmethod
    def _debrief(value: Any) -> None:
        _object(value, "$.debrief", {"objective", "questions", "transfer"})
        _text(value["objective"], "$.debrief.objective", 1500)
        for i, question in enumerate(_list(value["questions"], "$.debrief.questions", 12, 1)):
            _text(question, f"$.debrief.questions[{i}]", 1000)
        transfer = _object(value["transfer"], "$.debrief.transfer", {"prompt", "options", "answer", "rationale"})
        _text(transfer["prompt"], "$.debrief.transfer.prompt", 1500)
        options = _list(transfer["options"], "$.debrief.transfer.options", 6, 2)
        for i, option in enumerate(options):
            _text(option, f"$.debrief.transfer.options[{i}]", 1000)
        if len(set(options)) != len(options):
            _fail("$.debrief.transfer.options", "options must be distinct")
        _number(transfer["answer"], "$.debrief.transfer.answer", 0, len(options)-1, integer=True)
        _text(transfer["rationale"], "$.debrief.transfer.rationale", 1500)

    @staticmethod
    def _sources(rows: Any) -> None:
        seen = set()
        for i, row in enumerate(_list(rows, "$.sources", 64, 1)):
            path = f"$.sources[{i}]"
            _object(row, path, {"id", "title", "url", "kind"})
            ident = _text(row["id"], path + ".id", identifier=True)
            if ident in seen:
                _fail(path + ".id", "duplicate source")
            seen.add(ident)
            _text(row["title"], path + ".title", 600)
            _text(row["url"], path + ".url", 2000)
            if row["kind"] not in ("fiction", "primary", "reconstruction"):
                _fail(path + ".kind", "unsupported provenance label")
            try:
                parsed = urlsplit(row["url"])
            except ValueError:
                _fail(path + ".url", "malformed provenance reference")
            if parsed.scheme not in ("https", "project") or not parsed.netloc or parsed.username or parsed.password:
                _fail(path + ".url", "must be an https or project provenance reference without credentials")
            if parsed.scheme == "project" and row["kind"] == "primary":
                _fail(path, "a local project description is not a primary historical/scientific source")

    def load(self, path: str | Path) -> ExperienceSpec:
        path = Path(path)
        if path.stat().st_size > 2_000_000:
            _fail("$", "specification file exceeds 2 MB")
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    _fail("$", "duplicate JSON field: " + key)
                result[key] = value
            return result
        try:
            value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=pairs,
                parse_constant=lambda value: _fail("$", "nonfinite JSON number: " + value))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise SpecValidationError("$: invalid UTF-8 JSON specification") from error
        return self.validate(value)

    def compile(self, spec: ExperienceSpec | Mapping[str, Any] | str | Path, **kwargs):
        validated = self.load(spec) if isinstance(spec, (str, Path)) else self.validate(spec)
        from .runtime import ExperienceRuntime
        return ExperienceRuntime(validated, **kwargs)
