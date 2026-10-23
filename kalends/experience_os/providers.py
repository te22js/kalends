"""Optional proposal assistance over the existing budgeted cognition service.

There is no network transport, model client, archive lookup or world mutation in
this module. The caller supplies an already-authorized, bounded evidence view.
Models may choose templates, literal feedback and offered options; generated
prose is never accepted as a world fact or as permission to execute an action.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from kalends_rebirth.ai import Cognition, ProposalError, canonical
from kalends_rebirth.language import Language

from .compiler import ExperienceCompilerV1, ExperienceSpec


OBJECTIVE_FOCI = {
    "evidence": "Practice distinguishing dated direct evidence, testimony and uncertainty before making a consequential choice.",
    "continuity": "Trace how accepted choices and obligations shape a persistent personal history, using actual simulated records.",
    "coordination": "Practice making feasible shared-capacity allocations under competing deadlines and private condition information.",
    "obligations": "Practice accounting for owned resources, deadlines and the actual consequences of a promise.",
}
_FOCI = {"commons": ("evidence", "coordination", "continuity"),
         "pompeii": ("evidence", "obligations", "continuity")}
_CLAIM_LIMIT = "This is a reviewed proposal over supplied evidence, not an executed action or a validated learning outcome."


def _object(value, required, optional=frozenset()):
    if type(value) is not dict or set(value) - set(required) - set(optional) or set(required) - set(value):
        raise ProposalError("Unexpected or missing scoped proposal fields")
    return value


def _text(value, maximum=2000):
    if type(value) is not str or not value.strip() or len(value) > maximum:
        raise ProposalError("Proposal text must be bounded and nonempty")
    return value


def _minute(value):
    if type(value) is not int or not 0 <= value <= 365 * 1440:
        raise ProposalError("Proposal time must be a bounded nonnegative integer")
    return value


def _ids(value, maximum=64):
    if type(value) is not list or len(value) > maximum or any(type(i) is not int or i < 0 for i in value):
        raise ProposalError("Evidence identities must be a bounded list of nonnegative integers")
    if len(set(value)) != len(value):
        raise ProposalError("Evidence identities must be distinct")
    return value


def _detach(value):
    try:
        text = canonical(value)
        if len(text.encode()) > 24000:
            raise ProposalError("Proposal scope exceeds 24,000 bytes")
        return json.loads(text)
    except (TypeError, ValueError, OverflowError) as error:
        if isinstance(error, ProposalError):
            raise
        raise ProposalError("Proposal scope must contain finite JSON values") from None


def _evidence_view(context, required, optional=frozenset()):
    """Validate, then project; an incoming operator dump cannot reach a model.

    allowed_event_ids is an explicit ingress permission supplied by the host's
    visibility/retention boundary, not a request to retrieve those IDs. This
    helper cannot authenticate a host that lies about its own permission set.
    """
    context = _detach(context)
    _object(context, set(required) | {"minute", "evidence", "allowed_event_ids"}, optional)
    _minute(context["minute"])
    allowed = set(_ids(context["allowed_event_ids"]))
    rows = context["evidence"]
    if type(rows) is not list or len(rows) > 32:
        raise ProposalError("At most 32 explicitly supplied evidence clauses are permitted")
    seen = set()
    for row in rows:
        _object(row, {"event_id", "text"}, {"at", "kind"})
        identifier = row["event_id"]
        if type(identifier) is not int or identifier not in allowed or identifier in seen:
            raise ProposalError("Evidence must be distinct and inside the caller's admitted permission set")
        seen.add(identifier)
        _text(row["text"], 2000)
        if "at" in row and _minute(row["at"]) > context["minute"]:
            raise ProposalError("Future evidence is not accessible")
        if "kind" in row and row["kind"] not in ("event", "direct", "testimony", "inference"):
            raise ProposalError("Unsupported epistemic evidence label")
    # Only supplied records are usable, even if an input permission list has
    # more IDs. No method follows an ID to a canonical event archive.
    context["allowed_event_ids"] = sorted(seen)
    return context


class ExperienceProposals:
    """Proposal-only helpers, offline unless a configured Cognition is supplied.

    ``from_env`` explicitly delegates to the existing provider configuration,
    credential, pricing and budget gates. Default construction does not read
    credentials or enable a model from environment variables.
    """

    def __init__(self, cognition=None):
        self.cognition = cognition if cognition is not None else Cognition()

    @classmethod
    def from_env(cls, environment=None):
        return cls(Cognition.from_env(environment))

    def debug(self):
        return self.cognition.debug()

    @staticmethod
    def _proposal(result, output, kind):
        receipt = {**copy.deepcopy(result["receipt"]), "experience_os_task": kind, "proposal_only": True}
        return {"output": output, "receipt": receipt, "review_required": True, "claim_limit": _CLAIM_LIMIT}

    def draft_spec(self, prompt, templates):
        """Select a validated template and authored objective focus; never run it.

        templates is one spec/mapping/path or a list of 1..4 such templates.
        This intentionally finite V1 authoring assistant does not generate new
        executable rules, resources, historical claims or private observations.
        """
        _text(prompt, 2000)
        items = templates if type(templates) is list else [templates]
        if not 1 <= len(items) <= 4:
            raise ProposalError("Provide one through four validated templates")
        compiler = ExperienceCompilerV1()
        specs = [compiler.load(item) if isinstance(item, (str, Path)) else compiler.validate(item) for item in items]
        by_id = {spec.id: spec for spec in specs}
        if len(by_id) != len(specs):
            raise ProposalError("Draft templates must have distinct experience identities")
        context = {"templates": [{"id": spec.id, "title": spec.title,
            "adapter": spec.setting["adapter"], "objective": spec.debrief["objective"],
            "actions": spec.actions, "focus_ids": list(_FOCI[spec.setting["adapter"]]),
            "source_ids": [source["id"] for source in spec.sources]} for spec in specs],
            "focus_clauses": OBJECTIVE_FOCI, "scope": "Select a finite draft only; no world exists in this request."}
        context = _detach(context)
        first = specs[0]
        fallback = {"draft": True, "template_id": first.id, "focus_id": "evidence",
                    "source_ids": [source["id"] for source in first.sources]}
        schema = {"type": "object", "properties": {"draft": {"type": "boolean", "enum": [True]},
            "template_id": {"type": "string", "enum": list(by_id)},
            "focus_id": {"type": "string", "enum": list(OBJECTIVE_FOCI)},
            "source_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 64}},
            "required": ["draft", "template_id", "focus_id", "source_ids"], "additionalProperties": False}
        def validate(output, supplied):
            _object(output, {"draft", "template_id", "focus_id", "source_ids"})
            if output["draft"] is not True or type(output["template_id"]) is not str or output["template_id"] not in by_id:
                raise ProposalError("Draft must select a supplied template")
            spec = by_id[output["template_id"]]
            if output["focus_id"] not in _FOCI[spec.setting["adapter"]]:
                raise ProposalError("Objective focus is unsupported by this domain")
            sources = output["source_ids"]
            if type(sources) is not list or any(type(i) is not str for i in sources) or len(set(sources)) != len(sources):
                raise ProposalError("Draft provenance identities must be distinct")
            if set(sources) != {source["id"] for source in spec.sources}:
                raise ProposalError("A draft cannot invent or discard its template's required provenance")
            draft = spec.to_dict()
            draft["debrief"]["objective"] = OBJECTIVE_FOCI[output["focus_id"]] + " Simulated performance does not establish human learning or transfer."
            compiler.validate(draft)  # Semantic boundary checked before accepting a provider suggestion.
            return copy.deepcopy(output)
        result = self.cognition.run("world_content", context, {"prompt": prompt, "draft_only": True},
            fallback=fallback, validator=validate, schema=schema)
        selection = result["output"]
        draft = by_id[selection["template_id"]].to_dict()
        draft["debrief"]["objective"] = OBJECTIVE_FOCI[selection["focus_id"]] + " Simulated performance does not establish human learning or transfer."
        validated = compiler.validate(draft)
        return self._proposal(result, {"draft": True, "selection": selection, "spec": validated.to_dict(),
            "spec_hash": hashlib.sha256(canonical(validated.to_dict()).encode()).hexdigest(), "compiler_validated": True,
            "limitation": "Template selection and authored objective focus only; no new world rules are generated."}, "spec_draft")

    def debrief(self, context):
        """Select existing feedback and questions; never synthesize causal facts.

        Required keys: viewer, minute, objective, evidence, allowed_event_ids,
        questions. Evidence rows are {event_id,text,at?,kind?}; all must already
        be legitimate for viewer. Unknown fields (including LAB truth) fail.
        """
        view = _evidence_view(context, {"viewer", "objective", "questions"})
        _text(view["viewer"], 64)
        _text(view["objective"], 1500)
        questions = view["questions"]
        if type(questions) is not list or not 1 <= len(questions) <= 12:
            raise ProposalError("Provide one through twelve authored debrief questions")
        for question in questions:
            _text(question, 1000)
        fallback = {"event_ids": [row["event_id"] for row in view["evidence"]][-8:],
                    "question_ids": list(range(min(3, len(questions))))}
        schema = {"type": "object", "properties": {
            "event_ids": {"type": "array", "items": {"type": "integer"}, "maxItems": 8},
            "question_ids": {"type": "array", "items": {"type": "integer"}, "maxItems": 3}},
            "required": ["event_ids", "question_ids"], "additionalProperties": False}
        def validate(output, supplied):
            _object(output, {"event_ids", "question_ids"})
            events = _ids(output["event_ids"], 8)
            questions_ = _ids(output["question_ids"], 3)
            if not set(events) <= set(supplied["allowed_event_ids"]) or any(i >= len(supplied["questions"]) for i in questions_):
                raise ProposalError("Debrief may select only supplied accessible events and questions")
            return copy.deepcopy(output)
        result = self.cognition.run("reflection", view, {"purpose": "grounded_debrief_selection"},
            fallback=fallback, validator=validate, schema=schema)
        selected = set(result["output"]["event_ids"])
        clauses = sorted((row for row in view["evidence"] if row["event_id"] in selected),
                         key=lambda row: (row.get("at", view["minute"]), row["event_id"]))
        return self._proposal(result, {"viewer": view["viewer"], "at": view["minute"], "objective": view["objective"],
            "clauses": clauses, "questions": [questions[i] for i in result["output"]["question_ids"]],
            "event_ids": [row["event_id"] for row in clauses], "selection": result["output"],
            "limitation": "Selected literal feedback only; recorded dependencies are not a new counterfactual proof."}, "debrief")

    def suggest_plan(self, context):
        """Select an offered supported option or wait, without executing it.

        Required keys: actor, minute, evidence, allowed_event_ids, options.
        Each option is {id,label,evidence_ids,enabled?}. The host must derive
        availability/resources from its authoritative action validator and must
        revalidate a reviewed suggestion before any later command is committed.
        """
        view = _evidence_view(context, {"actor", "options"})
        _text(view["actor"], 64)
        if type(view["options"]) is not list or len(view["options"]) > 16:
            raise ProposalError("At most sixteen offered plan options are permitted")
        options, seen = {}, set()
        for option in view["options"]:
            _object(option, {"id", "label", "evidence_ids"}, {"enabled"})
            ident = _text(option["id"], 64)
            _text(option["label"], 200)
            if ident == "wait" or ident in seen:
                raise ProposalError("Offered option identities must be distinct and must not redefine wait")
            seen.add(ident)
            if "enabled" in option and type(option["enabled"]) is not bool:
                raise ProposalError("Option availability must be a boolean")
            refs = _ids(option["evidence_ids"], 8)
            if not set(refs) <= set(view["allowed_event_ids"]):
                raise ProposalError("Offered plan support must already be admitted")
            if option.get("enabled", True):
                options[ident] = option
        view["options"] = list(options.values())
        schema = {"type": "object", "properties": {"choice_id": {"type": "string", "enum": [*options, "wait"]},
            "evidence_ids": {"type": "array", "items": {"type": "integer"}, "maxItems": 8}},
            "required": ["choice_id", "evidence_ids"], "additionalProperties": False}
        def validate(output, supplied):
            _object(output, {"choice_id", "evidence_ids"})
            choice = output["choice_id"]
            if type(choice) is not str or choice not in [*options, "wait"]:
                raise ProposalError("A model can only select an offered option or wait")
            refs = _ids(output["evidence_ids"], 8)
            expected = set(options[choice]["evidence_ids"]) if choice != "wait" else set()
            if set(refs) != expected:
                raise ProposalError("A suggested plan must cite exactly its offered supporting evidence")
            return {"choice_id": choice, "evidence_ids": list(refs)}
        result = self.cognition.run("planning", view, {"purpose": "reviewed_next_step"},
            fallback={"choice_id": "wait", "evidence_ids": []}, validator=validate, schema=schema)
        return self._proposal(result, {**result["output"], "actor": view["actor"], "at": view["minute"],
            "context_hash": result["receipt"]["context_hash"], "status": "awaiting host review and current-state validation"}, "plan")

    def consolidate(self, context):
        """Reuse Language.reflect's literal-memory selector; never install it.

        Required keys: actor, minute, evidence, allowed_event_ids. This is an
        optional presentation proposal, not an additional hidden memory store.
        """
        view = _evidence_view(context, {"actor"})
        _text(view["actor"], 64)
        # Reuse the existing authored literal-memory fallback, then add the
        # stricter identity check required by this boundary. No new model
        # client/transport or mutation path is introduced.
        fallback = Language(Cognition()).reflect(view)["output"]
        schema = {"type": "object", "properties": {"memories": {"type": "array", "maxItems": 8,
            "items": {"type": "object", "properties": {"evidence_id": {"type": "integer"}, "text": {"type": "string"}},
            "required": ["evidence_id", "text"], "additionalProperties": False}}},
            "required": ["memories"], "additionalProperties": False}
        records = {row["event_id"]: row["text"] for row in view["evidence"]}
        def validate(output, supplied):
            _object(output, {"memories"})
            memories = output["memories"]
            if type(memories) is not list or len(memories) > 8:
                raise ProposalError("Consolidation must select at most eight literal clauses")
            seen = []
            for memory in memories:
                _object(memory, {"evidence_id", "text"})
                _ids([memory["evidence_id"]], 1)
                identifier = memory["evidence_id"]
                if identifier not in records or identifier in seen or memory["text"] != records[identifier]:
                    raise ProposalError("Consolidation cannot invent, duplicate or rewrite an admitted memory")
                seen.append(identifier)
            return copy.deepcopy(output)
        result = self.cognition.run("reflection", view, {"purpose": "literal_consolidation_proposal"},
            fallback=fallback, validator=validate, schema=schema)
        return self._proposal(result, {**result["output"], "actor": view["actor"], "at": view["minute"],
            "status": "literal retained-memory suggestion; no mind state was changed"}, "consolidation")
