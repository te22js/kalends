"""One disabled-by-default character pilot over existing cognition contracts.

This module has no transport, environment/credential reader, archive access or
world executor. A host supplies the entire retained/admitted evidence boundary.
The model selects identities; every displayed factual clause is copied literally
from that boundary. This experiment is not production authorization machinery.
"""
from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass
import json
import math
from pathlib import Path
import threading

from kalends.experience_os.providers import _evidence_view, _ids, _object, _text
from kalends_rebirth.ai import (
    Cognition, MockAdapter, OfflineAdapter, OpenAIResponsesAdapter,
    ProposalError, TaskPolicy, canonical,
)


RESPONSES_ENDPOINT = "https://api.openai.com/v1/responses"
FIXTURE_ENDPOINT = "fixture://continuity-character"
PHRASES = {
    "plain": "",
    "careful": "I will stick to the supplied record. ",
    "direct": "Let us be precise. ",
}
_CLAUSE_PREFIXES = {"event": "", "direct": "",
    "testimony": "The supplied testimony states: ",
    "inference": "The supplied inference states: "}
_EMPTY_REPLY = "I will leave that open."
_WAIT_LABEL = "Wait for review"


@dataclass(frozen=True)
class PilotConfig:
    """Explicit host configuration; missing authorization always disables calls.

    Limits may be reduced, but cannot exceed this single small pilot's ceilings.
    There is deliberately no ``from_env`` or provider/key configuration here.
    """

    enabled: bool = False
    authorized_endpoint: str | None = None
    session_cap_usd: float | None = None
    fixture_mode: bool = False
    max_turns: int = 3
    max_context_bytes: int = 8000
    max_output_tokens: int = 256
    max_output_bytes: int = 2400
    timeout_seconds: float = 2.0

    def __post_init__(self):
        if type(self.enabled) is not bool or type(self.fixture_mode) is not bool:
            raise ValueError("Pilot enable and fixture flags must be booleans")
        if self.authorized_endpoint is not None and (
            type(self.authorized_endpoint) is not str or len(self.authorized_endpoint) > 256
        ):
            raise ValueError("Pilot endpoint must be an explicit bounded string")
        cap = self.session_cap_usd
        if cap is not None and (type(cap) not in (int, float) or not math.isfinite(cap) or cap < 0):
            raise ValueError("Pilot cap must be a finite nonnegative number")
        for value, lower, upper in (
            (self.max_turns, 1, 5), (self.max_context_bytes, 1000, 12000),
            (self.max_output_tokens, 32, 512), (self.max_output_bytes, 1000, 4000),
        ):
            if type(value) is not int or not lower <= value <= upper:
                raise ValueError("Pilot limit exceeds the bounded experiment")
        if type(self.timeout_seconds) not in (int, float) or not 0 < self.timeout_seconds <= 5:
            raise ValueError("Pilot timeout must be positive and at most five seconds")


class CharacterPilot:
    """Review-only character phrasing and an OFFERED action identity.

    ``cognition`` supplies a dedicated existing adapter, never a new transport.
    A fresh Cognition owns this pilot's metrics, zero retries and zero cache.
    Do not share its adapter with unrelated work: its existing total budget is
    the session ceiling and must already be no larger than the approved cap.
    """

    def __init__(self, config=None, *, cognition=None):
        self.config = config if config is not None else PilotConfig()
        if not isinstance(self.config, PilotConfig):
            raise ValueError("Expected an explicit PilotConfig")
        adapter = cognition.adapter if cognition is not None else OfflineAdapter()
        self.cognition = Cognition(adapter, policies={"dialogue": TaskPolicy(
            timeout_seconds=self.config.timeout_seconds, retries=0,
            output_tokens=self.config.max_output_tokens,
            maximum_context_bytes=self.config.max_context_bytes,
        )}, cache_size=0)
        self._inflight = threading.Lock()
        self._state_lock = threading.Lock()
        self._turns = 0
        self._halted = None
        self._receipts = []

    def _disabled_reason(self):
        config, adapter = self.config, self.cognition.adapter
        if not config.enabled:
            return "explicit_enable_required"
        if not config.authorized_endpoint:
            return "authorized_endpoint_required"
        if config.session_cap_usd is None or config.session_cap_usd <= 0:
            return "positive_numeric_cap_required"
        if isinstance(adapter, (OfflineAdapter, MockAdapter)):
            if not config.fixture_mode or config.authorized_endpoint != FIXTURE_ENDPOINT:
                return "explicit_fixture_configuration_required"
            return None
        if not isinstance(adapter, OpenAIResponsesAdapter):
            # LocalJSONAdapter supplies no price/cost reserve; do not pretend a
            # numeric dollar cap can be honored for that unpriced endpoint.
            return "unsupported_or_unpriced_adapter"
        if config.authorized_endpoint != RESPONSES_ENDPOINT:
            return "endpoint_does_not_match_existing_transport"
        if config.fixture_mode and adapter.transport is None:
            return "fixture_mode_requires_injected_transport"
        if not adapter.enabled:
            return "existing_provider_enable_required"
        if adapter.budget_usd <= 0 or adapter.budget_usd > config.session_cap_usd:
            return "existing_provider_budget_must_fit_session_cap"
        if adapter.spent_usd + adapter.reserved_usd >= adapter.budget_usd:
            return "session_budget_exhausted"
        rates = (adapter.input_rate, adapter.output_rate)
        if any(type(rate) not in (int, float) or not math.isfinite(rate) or rate < 0 for rate in rates):
            return "explicit_provider_prices_required"
        return None

    def status(self):
        """Redacted status only; no request text, key, archive or local prose."""
        reason = self._disabled_reason()
        adapter = self.cognition.adapter
        with self._state_lock:
            turns, halted, receipts = self._turns, self._halted, copy.deepcopy(self._receipts)
        return {
            "enabled": reason is None and halted is None and turns < self.config.max_turns,
            "disabled_reason": halted or reason or ("turn_limit" if turns >= self.config.max_turns else None),
            "turns_used": turns, "turns_remaining": max(0, self.config.max_turns - turns),
            "max_concurrency": 1, "max_context_bytes": self.config.max_context_bytes,
            "max_output_tokens": self.config.max_output_tokens,
            "max_output_bytes": self.config.max_output_bytes,
            "timeout_seconds": self.config.timeout_seconds,
            "session_cap_usd": self.config.session_cap_usd,
            "estimated_spent_usd": getattr(adapter, "spent_usd", self.cognition.metrics["estimated_cost_usd"]),
            "reserved_usd": getattr(adapter, "reserved_usd", 0.0),
            "network_calls": getattr(adapter, "network_calls", 0),
            "fixture_calls": getattr(adapter, "fixture_calls", 0),
            "raw_local_text_retained": False, "proposal_only": True,
            "authorization_scope": "bounded paid-live limit gate; not production authorization",
            "receipts": receipts,
        }

    def _receipt(self, status, code, *, ai=None):
        receipt = {"status": status, "code": code, "attempts": 0,
            "proposal_only": True, "raw_local_text_retained": False,
            "clauses_audited": True, "new_world_facts": 0, "world_effects": 0}
        if ai is not None:
            # Existing Cognition receipts contain no request/result prose. Keep
            # only the accounting/validation fields needed by this experiment.
            for key in ("attempts", "kind", "fallback", "errors", "input_tokens", "output_tokens",
                        "estimated_cost_usd", "unknown_cost_attempts", "context_hash", "cached"):
                if key in ai:
                    receipt[key] = copy.deepcopy(ai[key])
        with self._state_lock:
            self._receipts.append(copy.deepcopy(receipt))
            self._receipts = self._receipts[-16:]
        return receipt

    def _reject(self, code):
        return {"output": None, "receipt": self._receipt("REJECTED", code),
            "review_required": True, "confirm_required": True}

    def _scope(self, context):
        try:
            if len(canonical(context).encode()) > self.config.max_context_bytes:
                raise ProposalError("Pilot context is oversized")
        except (TypeError, ValueError, OverflowError):
            raise ProposalError("Pilot context is not bounded finite JSON") from None
        view = _evidence_view(context, {"actor", "viewer", "retained_event_ids", "admitted_event_ids", "options"})
        _text(view["actor"], 64)
        _text(view["viewer"], 64)
        retained = set(_ids(view["retained_event_ids"]))
        admitted = set(_ids(view["admitted_event_ids"]))
        if not set(view["allowed_event_ids"]) <= retained & admitted:
            raise ProposalError("Evidence must be retained and admitted by the host")
        if len(view["evidence"]) > 8:
            raise ProposalError("Pilot evidence exceeds eight clauses")
        for row in view["evidence"]:
            _text(row["text"], 500)
        options, seen = [], set()
        if type(view["options"]) is not list or len(view["options"]) > 8:
            raise ProposalError("Pilot options exceed eight offered identities")
        for option in view["options"]:
            _object(option, {"id", "label", "evidence_ids"}, {"enabled"})
            ident = _text(option["id"], 64)
            _text(option["label"], 160)
            if ident == "wait" or ident in seen:
                raise ProposalError("Pilot option identities must be distinct")
            seen.add(ident)
            if "enabled" in option and type(option["enabled"]) is not bool:
                raise ProposalError("Pilot option enable must be boolean")
            if not set(_ids(option["evidence_ids"], 8)) <= set(view["allowed_event_ids"]):
                raise ProposalError("Option support must be present in the host evidence")
            if option.get("enabled", True):
                options.append(option)
        # Permission sets are ingress checks, not additional lookup authority.
        # Reduce all three to exactly the records sent in this bounded request.
        view["retained_event_ids"] = view["admitted_event_ids"] = list(view["allowed_event_ids"])
        view["options"] = options
        view["reviewed_phrase_ids"] = list(PHRASES)
        if len(canonical(view).encode()) > self.config.max_context_bytes:
            raise ProposalError("Projected pilot context exceeds its declared budget")
        return view

    def _render(self, selection, view):
        rows = {row["event_id"]: row for row in view["evidence"]}
        clauses = [{"text": rows[event_id]["text"], "support_ids": [event_id],
                    "kind": rows[event_id].get("kind", "event"),
                    **({"at": rows[event_id]["at"]} if "at" in rows[event_id] else {}),
                    "audit": "literal_host_evidence"} for event_id in selection["event_ids"]]
        option = next((o for o in view["options"] if o["id"] == selection["choice_id"]), None)
        return {"character": view["actor"], "viewer": view["viewer"],
            "phrase_id": selection["phrase_id"],
            "text": PHRASES[selection["phrase_id"]] + (
                " ".join(_CLAUSE_PREFIXES[c["kind"]] + c["text"] for c in clauses) or _EMPTY_REPLY),
            "clauses": clauses, "support_ids": list(selection["event_ids"]),
            "action_suggestion": {"status": "OFFERED", "choice_id": selection["choice_id"],
                "label": option["label"] if option else _WAIT_LABEL,
                "support_ids": list(selection["evidence_ids"]),
                "review_required": True, "confirm_required": True,
                "current_state_revalidation_required": True},
            "factual_clause_audit": "all factual clauses are literal supplied evidence",
            "world_effects": 0}

    def interact(self, context, *, local_text=None):
        """Consume a host scope; local free text is neither used nor retained.

        Returns a redacted rejection receipt on ingress/limit errors. A rejected
        model selection produces the literal empty/wait fallback and accounting.
        Host review, explicit confirmation, and current-world validation remain
        necessary before any separate command executor is called.
        """
        if not self._inflight.acquire(blocking=False):
            return self._reject("concurrency_limit")
        try:
            with self._state_lock:
                if self._halted:
                    halted = self._halted
                elif self._turns >= self.config.max_turns:
                    halted = "turn_limit"
                else:
                    halted = None
                    self._turns += 1
            if halted:
                return self._reject(halted)
            if local_text is not None:
                try:
                    if type(local_text) is not str or len(local_text.encode()) > 2000:
                        return self._reject("local_text_limit")
                except UnicodeError:
                    return self._reject("local_text_limit")
            try:
                view = self._scope(context)
            except (ProposalError, TypeError, KeyError):
                return self._reject("host_scope_rejected")
            fallback = {"phrase_id": "plain", "event_ids": [], "choice_id": "wait", "evidence_ids": []}
            if len(canonical(self._render(fallback, view)).encode()) > self.config.max_output_bytes:
                return self._reject("minimum_output_exceeds_byte_limit")
            disabled = self._disabled_reason()
            if disabled:
                return {"output": self._render(fallback, view),
                    "receipt": self._receipt("DISABLED", disabled),
                    "review_required": True, "confirm_required": True}
            options = {option["id"]: option for option in view["options"]}
            schema = {"type": "object", "properties": {
                "phrase_id": {"type": "string", "enum": list(PHRASES)},
                "event_ids": {"type": "array", "items": {"type": "integer"}, "maxItems": 3},
                "choice_id": {"type": "string", "enum": [*options, "wait"]},
                "evidence_ids": {"type": "array", "items": {"type": "integer"}, "maxItems": 8}},
                "required": ["phrase_id", "event_ids", "choice_id", "evidence_ids"], "additionalProperties": False}

            def validate(output, supplied):
                _object(output, {"phrase_id", "event_ids", "choice_id", "evidence_ids"})
                phrase, choice = output["phrase_id"], output["choice_id"]
                if type(phrase) is not str or phrase not in PHRASES or type(choice) is not str or choice not in [*options, "wait"]:
                    raise ProposalError("Only reviewed phrase/option identities are permitted")
                if not set(_ids(output["event_ids"], 3)) <= set(supplied["allowed_event_ids"]):
                    raise ProposalError("Factual clauses must select supplied evidence")
                support = set(_ids(output["evidence_ids"], 8))
                expected = set(options[choice]["evidence_ids"]) if choice != "wait" else set()
                if support != expected:
                    raise ProposalError("Offered suggestion support must match exactly")
                if len(canonical(self._render(output, supplied)).encode()) > self.config.max_output_bytes:
                    raise ProposalError("Rendered character output exceeds its byte limit")
                return copy.deepcopy(output)

            result = self.cognition.run("dialogue", view, {"purpose": "bounded_character_selection",
                "review_required": True}, fallback=fallback, validator=validate, schema=schema)
            ai = result["receipt"]
            # No later turn can retry a timed-out or ambiguously billed request.
            # The existing adapter retains its own reserve for uncertain charges.
            if ai.get("unknown_cost_attempts") or "timeout" in ai.get("errors", []) or "provider_busy" in ai.get("errors", []):
                with self._state_lock:
                    self._halted = "uncertain_provider_charge"
            if ai.get("output_tokens", 0) > self.config.max_output_tokens:
                result["output"] = fallback
                ai["fallback"] = True
                ai["errors"].append("reported_output_limit_exceeded")
                with self._state_lock:
                    self._halted = "provider_output_limit"
            adapter = self.cognition.adapter
            if isinstance(adapter, OpenAIResponsesAdapter) and adapter.spent_usd + adapter.reserved_usd > self.config.session_cap_usd:
                with self._state_lock:
                    self._halted = "reported_session_cap_exceeded"
            receipt = self._receipt("FALLBACK" if ai["fallback"] else "ACCEPTED",
                "model_selection_rejected" if ai["fallback"] else "literal_selection_validated", ai=ai)
            return {"output": self._render(result["output"], view), "receipt": receipt,
                "review_required": True, "confirm_required": True}
        finally:
            self._inflight.release()


def _fixture_scope():
    return {"actor": "Sabina", "viewer": "Player", "minute": 10,
        "evidence": [{"event_id": 4, "text": "The supplied receipt records three coins.", "at": 5, "kind": "direct"}],
        "allowed_event_ids": [4], "retained_event_ids": [4], "admitted_event_ids": [4],
        "options": [{"id": "inspect", "label": "Review the supplied receipt", "evidence_ids": [4]}]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Disabled character pilot status or deterministic offline fixture")
    parser.add_argument("--status", action="store_true", help="Show redacted configuration status (default)")
    parser.add_argument("--config", type=Path, help="Explicit JSON PilotConfig; no environment or credentials are read")
    parser.add_argument("--offline-fixture", action="store_true", help="Run one deterministic mock fixture; no network")
    args = parser.parse_args(argv)
    if args.offline_fixture and args.config is not None:
        parser.error("The offline fixture uses its fixed fixture-only configuration")
    if args.offline_fixture:
        config = PilotConfig(enabled=True, authorized_endpoint=FIXTURE_ENDPOINT, session_cap_usd=.01, fixture_mode=True)
        pilot = CharacterPilot(config, cognition=Cognition(MockAdapter({"phrase_id": "careful", "event_ids": [4],
            "choice_id": "inspect", "evidence_ids": [4]})))
        print(json.dumps(pilot.interact(_fixture_scope()), indent=2, sort_keys=True))
    else:
        config = PilotConfig(**json.loads(args.config.read_text())) if args.config else PilotConfig()
        print(json.dumps(CharacterPilot(config).status(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
