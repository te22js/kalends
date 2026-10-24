"""Life-scoped product services over the existing Experience OS runtime.

Metadata and personal notes are not world facts or NPC memories. Templates,
individual journals and read-only examples have distinct identities here.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import secrets

from .compiler import ExperienceCompilerV1, SPEC_DIR
from .history import build_history, choices_then
from .guide import ACKS, VERSION as GUIDE_VERSION, guide_view, preferences as guide_preferences
from .runtime import ExperienceRuntime, digest
from .server import ExperienceService, ROOT

BUILD = "kalends-experience-redesign-1"
TEAMS = {"team_a": ("Amir", "Survey"), "team_b": ("Mira", "Instrument systems"), "team_c": ("Lin", "Follow-up")}
TEMPLATES = {
    "pompeii_life": {"title": "Pompeii", "subtitle": "A day in the neighborhood",
        "description": "Walk through a small Roman-inspired district as Aelia. Meet its residents, help resolve a disputed flour delivery, and learn what archaeological evidence tells us about work and daily life.",
        "badges": ["Historical fiction", "3D", "Persistent life"], "role": "Aelia, a fictional freedwoman",
        "opening": "Sabina, a food seller, and Lucius, a household steward, both claim flour from the same six-sack cart. Hear their accounts, inspect a written order, and decide whether or how to help.",
        "actions": ["Walk and meet the neighbors", "Ask Sabina about her day", "Choose whether to take on an obligation"],
        "preview_url": "/product/assets/hero.png"},
    "shared_observatory": {"title": "Shared Observatory", "subtitle": "Decide who gets to use the instrument",
        "description": "Three teams need the same instrument. Check the reports, decide how to divide its capacity, and see whether your promises can be kept.",
        "badges": ["Decision experience", "Conversation and planning", "Persistent consequences"], "role": "The consortium's elected coordinator",
        "opening": "Amir, Mira and Lin have work to complete on one instrument. Twelve nominal units are available; its usable condition must be checked or legitimately reported.",
        "actions": ["Meet the three representatives", "Ask for a dated report", "Make a feasible promise and allocation"], "preview_url": None},
}


USAGE_EVENTS = frozenset({"session_start", "life_entered", "meaningful_action", "consequence_viewed",
                          "history_opened", "return_resumed", "research_entered", "error", "active_interval",
                          "choice_declined", "life_left", "session_end", "guide_help", "guide_step", "guide_dismissed", "history_card_opened", "invalid_action"})
USAGE_REASONS = frozenset({"consent", "new", "return", "reload", "interval", "leave", "pagehide",
                           "visibility", "focus", "history", "alternative", "advance", "save_failed",
                           "unreadable", "stale", "rejected", "network", "scene", "cancelled", "guide", "notebook", "control_help", "unavailable", "affordability"})
USAGE_TIMINGS = ("active_ms", "visible_ms", "foreground_ms", "idle_ms", "elapsed_ms")


def meaningful_command(command):
    """Classify only accepted participant commands; never inspect their text."""
    return (command.get("operation") == "action" and
            command.get("data", {}).get("action") not in {None, "move", "wait"})


def meaningful_status(runtime):
    for index in range(len(runtime.commands) - 1, -1, -1):
        command = runtime.commands[index]
        if meaningful_command(command):
            return {"meaningful_revision": index + 1, "meaningful_kind": command["data"]["action"]}
    return {"meaningful_revision": 0, "meaningful_kind": None}


def utc():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


class ProductService(ExperienceService):
    """Compatibility layer, not another world, ledger, or provider transport."""
    def __init__(self, directory=None, *, cognition=None, include_examples=True):
        super().__init__(None, cognition=cognition)
        self.directory = Path(directory) if directory else None
        self.confirmed_receipts = {}
        self.templates = {p.stem: ExperienceCompilerV1().load(p) for p in SPEC_DIR.glob("*.json")}
        self.metadata, self.failures, self.examples, self.save_errors, self.metadata_warnings = {}, {}, set(), {}, {}
        self.meta_path = self.directory / ".product/state.json" if self.directory else None
        if self.meta_path and self.meta_path.exists():
            try:
                document = json.loads(self.meta_path.read_text())
                if not isinstance(document, dict) or type(document.get("version")) is not int or document["version"] != 1 or not isinstance(document.get("lives"), dict):
                    raise ValueError("Unsupported product metadata")
                for ident, meta in document["lives"].items():
                    if not isinstance(ident, str) or not isinstance(meta, dict):
                        raise ValueError("Malformed life metadata")
                    for key in ("started", "example", "operator_exposed", "telemetry_opt_in", "provenance_unknown"):
                        if key in meta and type(meta[key]) is not bool:
                            raise ValueError("Malformed life metadata flag")
                    for key in ("seen_revision", "last_seen_minute"):
                        if key in meta and (type(meta[key]) is not int or meta[key] < 0):
                            raise ValueError("Malformed life history position")
                    if any(key in meta and not isinstance(meta[key], list) for key in ("notes", "bookmarks")):
                        raise ValueError("Malformed personal annotations")
                    if any(key in meta and meta[key] is not None and not isinstance(meta[key], str) for key in ("created_at", "updated_at", "template_id")):
                        raise ValueError("Malformed life identity metadata")
                    if "guide" in meta:
                        guide = meta["guide"]
                        if not isinstance(guide, dict):
                            raise ValueError("Malformed guide metadata")
                        if "version" in guide and not isinstance(guide["version"], str):
                            raise ValueError("Malformed guide metadata version")
                        if any(key in guide and type(guide[key]) is not bool for key in ("enabled", "learn", "practice", "guided_origin")):
                            raise ValueError("Malformed guide metadata flag")
                        if any(key in guide and (not isinstance(guide[key], list) or any(not isinstance(item, str) for item in guide[key])) for key in ("ack", "read_cards")):
                            raise ValueError("Malformed guide reading metadata")
                self.metadata = document["lives"]
            except (ValueError, OSError, KeyError):
                # Keep the original bytes and surface a warning; do not replace
                # damaged metadata when a valid journal can still be inspected.
                self.failures["product_metadata"] = {"id": "product_metadata", "save_status": "incompatible", "error": "Product metadata could not be loaded; its file is preserved."}
        if self.directory:
            self.directory.mkdir(parents=True, exist_ok=True)
            for path in sorted(self.directory.glob("*.json")):
                ident = path.stem
                try:
                    if path.stat().st_size > 4_000_000:
                        raise ValueError("Journal exceeds this local build's size limit")
                    doc = json.loads(path.read_text())
                    spec = ExperienceCompilerV1().validate(doc["spec"])
                    if spec.id != ident:
                        raise ValueError("Journal identity differs from filename")
                    self.worlds[ident] = ExperienceRuntime(spec, journal_path=path, retention=doc.get("retention", "hybrid"))
                except (ValueError, KeyError, TypeError, OSError) as error:
                    self.worlds.pop(ident, None)
                    self.failures[ident] = {"id": ident, "title": ident, "save_status": "incompatible", "error": str(error)[:300] + "; original preserved"}
            # Retain established default IDs for the old API. They are quiet
            # compatibility lives, not the templates shown as "Begin a life".
            for ident in TEMPLATES:
                if ident in self.worlds:
                    world = self.worlds[ident]
                    world.journal_path = self.directory / (ident + ".json")
                    if not world.journal_path.exists():
                        world.save()
        for ident, runtime in self.worlds.items():
            initial = self._initial_meta(runtime, started=bool(runtime.commands) or ident not in TEMPLATES)
            saved = self.metadata.get(ident, {})
            guide = saved.get("guide", {})
            known_origin = isinstance(guide, dict) and all(type(guide.get(key)) is bool for key in ("enabled", "guided_origin", "practice"))
            self.metadata[ident] = {**initial, **saved}
            if ident not in TEMPLATES and (not known_origin or saved.get("provenance_unknown") is True):
                # A journal recovers actual choices, not lost display metadata.
                # Do not infer unassisted use from missing guidance provenance.
                self.metadata[ident]["provenance_unknown"] = True
        if include_examples:
            for adapter in ("commons", "pompeii"):
                path = ROOT / f"results/experience_os/life_v1/{adapter}/accepted_journal.json"
                if not path.exists():
                    continue
                doc = json.loads(path.read_text())
                runtime = ExperienceRuntime(doc["spec"], journal_path=path, retention=doc["retention"])
                runtime.journal_path = None  # reference material has no write handle
                ident = runtime.spec.id
                if ident in self.worlds:
                    continue
                self.worlds[ident] = runtime
                self.examples.add(ident)
                self.metadata[ident] = {**self._initial_meta(runtime, started=True, example=True), **self.metadata.get(ident, {}), "example": True}

    def _initial_meta(self, runtime, *, started=False, example=False):
        template = "pompeii_life" if runtime.spec.setting["adapter"] == "pompeii" else "shared_observatory"
        return {"template_id": template, "created_at": utc(), "updated_at": None,
                "started": started, "example": example, "seen_revision": 0, "last_seen_minute": 0,
                "operator_exposed": False, "telemetry_opt_in": False, "provenance_unknown": False,
                "notes": [], "bookmarks": []}

    def _persist_meta(self, values):
        if "product_metadata" in self.failures:
            raise ValueError("Product metadata is incompatible; choose a separate directory. Original preserved.")
        if self.meta_path:
            atomic_json(self.meta_path, {"version": 1, "lives": values})
        self.metadata = values

    def _update_meta(self, ident, **patch):
        values = copy.deepcopy(self.metadata)
        values[ident].update(patch)
        self._persist_meta(values)

    def mutable(self, ident):
        runtime = self.get(ident)
        if ident in self.examples:
            raise ValueError("This is a read-only recorded example. Begin a new life to make your own choices.")
        if "product_metadata" in self.failures:
            raise ValueError("Product metadata is incompatible; original saves are preserved. Use a separate directory for new play.")
        return runtime

    def metadata_for(self, ident):
        runtime = self.get(ident)
        meta = self.metadata.get(ident, self._initial_meta(runtime))
        roman = runtime.spec.setting["adapter"] == "pompeii"
        location = runtime.world.state.agent_locations.get("Player", "council")
        return {**{k: copy.deepcopy(v) for k, v in meta.items() if k not in ("notes", "bookmarks")},
                "id": ident, "title": runtime.spec.title, "participant": "Aelia" if roman else "You, the coordinator",
                "minute": runtime.minute, "day": runtime.minute // 1440 + 1, "revision": len(runtime.commands),
                "state_hash": runtime.state_hash(), "location": location, "save_status": "error" if ident in self.save_errors else "read_only" if ident in self.examples else "saved",
                "save_error": self.save_errors.get(ident),
                "metadata_warning": self.metadata_warnings.get(ident) or
                    ("Earlier guidance/practice provenance could not be verified; this life is excluded from unassisted research." if meta.get("provenance_unknown") else None),
                "read_only": ident in self.examples, "terminated": runtime.minute >= runtime.spec.termination["at"]}

    def catalog(self):
        lives = [self.metadata_for(i) for i in self.worlds if self.metadata.get(i, {}).get("started") and i not in self.examples]
        lives.sort(key=lambda m: (m.get("updated_at") or m.get("created_at") or "", m["id"]), reverse=True)
        return {"build": BUILD, "offline": not self.cognition.metrics["external"],
                "templates": [{"id": ident, **copy.deepcopy(TEMPLATES[ident])} for ident in TEMPLATES],
                "lives": lives, "examples": [self.metadata_for(i) for i in sorted(self.examples)],
                "failures": list(self.failures.values()), "life_limit": 8,
                "elapsed_policy": "Worlds advance when you play or explicitly advance time. No offline progression."}

    def start(self, template_id, *, guided=False, practice=False, _source=None, _practice_of=None):
        if type(guided) is not bool or type(practice) is not bool:
            raise ValueError("Guidance and practice settings must be booleans")
        if "product_metadata" in self.failures:
            raise ValueError("Product metadata is incompatible; choose a separate directory. Original preserved.")
        if template_id not in TEMPLATES:
            raise ValueError("Choose one of the two supported world templates")
        # Count personal worlds rather than readonly references, with the same
        # deliberately small local capacity as the retained service.
        if sum(bool(m.get("started")) and not m.get("example") for m in self.metadata.values()) >= 8:
            raise ValueError("This local prototype has eight personal lives. Existing histories are preserved.")
        source = copy.deepcopy(_source) if _source is not None else self.templates[template_id].to_dict()
        ident = ("pompeii_" if template_id == "pompeii_life" else "observatory_") + secrets.token_hex(6)
        source["id"] = ident
        source["title"] = "Aelia — a place in the city" if template_id == "pompeii_life" else "Your shared observatory"
        if practice:
            source["title"] += " · separate practice copy"
        journal = self.directory / (ident + ".json") if self.directory else None
        runtime = ExperienceRuntime(source, journal_path=journal)
        runtime.save()
        self.worlds[ident] = runtime
        values = copy.deepcopy(self.metadata)
        values[ident] = {**self._initial_meta(runtime, started=True), "updated_at": utc(),
                         "guide": {"version": GUIDE_VERSION, "enabled": guided, "guided_origin": guided,
                                   "learn": guided and template_id == "pompeii_life", "practice": practice, "ack": [], "read_cards": []}}
        if _practice_of:
            values[ident]["practice_of"] = _practice_of
        try:
            self._persist_meta(values)
        except (OSError, ValueError):
            # The saved newborn life is recoverable from its embedded journal.
            # Surface the failure; never delete it to simulate rollback.
            self.metadata[ident] = values[ident]
            self.metadata_warnings[ident] = "New life journal saved; display metadata could not be updated. Its journal remains recoverable."
            return {**self.life(ident), "metadata_warning": self.metadata_warnings[ident]}
        return self.life(ident)

    def participant_metrics(self, runtime):
        if runtime.spec.setting["adapter"] == "pompeii":
            return runtime.metrics()
        events = runtime.events()
        outcomes = [json.loads(e["payload"]["value"]) for e in events if e["payload"].get("category") == "allocation_settled"]
        return {"credits": runtime.world.economy.cash["Player"],
                "own_inspection_spend": sum(-e["payload"].get("cash_delta", {}).get("Player", 0) for e in events if e["payload"].get("category") == "inspection_paid"),
                "completed_projects": sum(len(o["completed"]) for o in outcomes),
                "executed_units": sum(sum(o["executed"].values()) for o in outcomes),
                "promises_kept": sum(e["payload"].get("category") == "promise_kept" for e in events),
                "promises_missed": sum(e["payload"].get("category") == "promise_missed" for e in events),
                "reports_received": sum(e["payload"].get("listener") == "Player" for e in events if e["etype"] == "tell")}

    def public_snapshot(self, runtime):
        snapshot = runtime.snapshot()
        if isinstance(snapshot.get('world'), dict):
            from .participant_copy import game_world_copy
            snapshot['world'] = game_world_copy(snapshot['world'])
        snapshot["metrics"] = self.participant_metrics(runtime)
        if runtime.spec.setting["adapter"] == "commons":
            snapshot["round_closed"] = any(e["payload"].get("prop") == ["experience", f"outcome:{runtime.world.round}"] for e in runtime.events())
        return snapshot

    def life(self, ident):
        runtime = self.get(ident)
        meta = self.metadata[ident]
        history = build_history(runtime, last_seen_minute=meta.get("last_seen_minute", 0), seen_revision=min(meta.get("seen_revision", 0), len(runtime.commands)))
        people = copy.deepcopy(history["people"])
        for person in people:
            if runtime.spec.setting["adapter"] == "commons":
                reports = [e for e in runtime.events() if e["etype"] == "tell" and e["payload"].get("listener") == "Player" and e["payload"].get("speaker") == person["id"] and e["payload"].get("category") == "report"]
                report = reports[-1] if reports else None
                person["known_report"] = ({"condition": report["payload"]["value"], "as_of": report["payload"]["as_of"],
                                           "received_at":report["tick"], "origin_observer":report["payload"].get("origin_observer"),
                                           "kind": "testimony", "evidence_ids": [report["event_id"]]} if report else None)
                person["style"] = {"team_a": "Concise and focused on completing the survey.", "team_b": "Careful about dated instrument evidence.", "team_c": "Attentive to what allocations actually deliver."}[person["id"]]
                person["reply"] = {"team_a": "Our survey work has a deadline. Please distinguish what you promise us from what the instrument actually delivers.",
                                   "team_b": "I work on the instrument systems. You can ask about the dated report before deciding what to promise.",
                                   "team_c": "Our follow-up work also depends on time at the instrument. I need to know what we can actually count on."}[person["id"]]
                if report:
                    from .guide import clock_label
                    observed = report['payload'].get('as_of', report['tick'])
                    condition = report['payload']['value']
                    nominal = runtime.spec.setting['rules']['capacity']
                    usable = nominal if condition == 'stable' else max(1, nominal * 2 // 3) if condition == 'fragile' else None
                    origin = report['payload'].get('origin_observer')
                    description = f"{usable} usable units" if usable is not None else f"a {condition} condition"
                    person['reply'] = (f"I observed {description} at {clock_label(observed)}." if origin == person['id']
                                       else f"The report I shared described {description}, observed at {clock_label(observed)}.")
                    person['reply_voice'] = 'person'
                    person['reply_evidence_ids'] = [report['event_id']]
                person["actions"] = [{"id": "ask_report", "label": "Ask about the dated report", "interaction": "observation", "action": {"action": "share", "recipient": person["id"]}},
                                     {"id": "inspect", "label": "Arrange a direct inspection", "action": {"action": "inspect"}}]
        snapshot = self.public_snapshot(runtime)
        guide = guide_view(snapshot, runtime.commands, runtime.events(), runtime.spec.setting["rules"], meta.get("guide"))
        guide["provenance_unknown"] = meta.get("provenance_unknown") is True
        guide["excluded_from_unassisted_research"] = guide["excluded_from_unassisted_research"] or guide["provenance_unknown"]
        snapshot["outcome"] = guide["result"]
        return {"build": BUILD, "life": self.metadata_for(ident), "snapshot": snapshot, "guide": guide,
                "people": people, "history": history, "known_commitments": history["known_commitments"],
                "return_summary": history["return_summary"], "time": {"minute": runtime.minute, "paused": True,
                    "known_stops": history["known_stops"], "elapsed_policy": history["elapsed_policy"]},
                "telemetry": {"opt_in": meta.get("telemetry_opt_in", False), "operator_exposed": meta.get("operator_exposed", False),
                              **meaningful_status(runtime)},
                "notes": copy.deepcopy(meta.get("notes", [])), "bookmarks": copy.deepcopy(meta.get("bookmarks", []))}

    def guide_update(self, ident, data):
        runtime = self.mutable(ident)
        if set(data) - {"id", "enabled", "learn", "ack", "card"}:
            raise ValueError("Guide updates contain only preferences and reading acknowledgements")
        prefs = guide_preferences(self.metadata[ident].get("guide"))
        for field in ("enabled", "learn"):
            if field in data:
                if type(data[field]) is not bool:
                    raise ValueError("Guide settings must be booleans")
                prefs[field] = data[field]
        if prefs["enabled"]:
            prefs["guided_origin"] = True
        current = guide_view(self.public_snapshot(runtime), runtime.commands, runtime.events(), runtime.spec.setting["rules"], prefs)
        if "ack" in data:
            ack = data["ack"]
            if not isinstance(ack, str) or ack not in ACKS:
                raise ValueError("Only a reading or controls acknowledgement can be saved; world actions need their ordinary review")
            if ack == "reflection_done" and current["result"] is None:
                raise ValueError("There is no recorded result to review yet")
            if ack == "request_read" and not current["known"].get("request", {}).get("quantities") and current["result"] is None:
                raise ValueError("No request has been published yet")
            if ack == "dispute_explained" and not any(c.get("data", {}).get("action") == "hear_dispute" for c in runtime.commands):
                raise ValueError("Hear an account before acknowledging its explanation")
            prefs["ack"] = list(dict.fromkeys([*prefs["ack"], ack]))
        if "card" in data:
            card = next((c for c in current["history_cards"] if c["id"] == data["card"]), None)
            if card is None or not card["available"]:
                raise ValueError("Visit this represented place before recording its location card; other notebook cards are available now")
            prefs["read_cards"] = list(dict.fromkeys([*prefs["read_cards"], card["id"]]))
        self._update_meta(ident, guide=prefs)
        return self.life(ident)

    def practice(self, ident):
        runtime = self.get(ident)
        template = self.metadata[ident]["template_id"]
        return self.start(template, guided=True, practice=True, _source=runtime.spec.to_dict(),
                          _practice_of={"life_id": ident, "revision": len(runtime.commands)})

    def resume(self, ident):
        if ident not in self.examples:
            self._update_meta(ident, updated_at=utc(), started=True)
        return self.life(ident)

    def seen(self, ident, revision):
        runtime = self.get(ident)
        if type(revision) is not int or not 0 <= revision <= len(runtime.commands):
            raise ValueError("Seen revision must identify an accepted command prefix")
        if ident not in self.examples:
            revision = max(revision, self.metadata[ident].get("seen_revision", 0))
            minute = runtime.commands[revision - 1]["after"] if revision else 0
            self._update_meta(ident, seen_revision=revision, last_seen_minute=minute)
        return {"saved": True, "revision": revision}

    def observe(self, ident, data, *, scene=False):
        from .observation import observe, ParticipantOperationError
        if set(data) - {'action', 'expected_revision', 'expected_state_hash'}:
            raise ParticipantOperationError('Unexpected fields in the question.', 'observation_invalid_identity')
        runtime = self.mutable(ident)
        result = observe(runtime, data.get('action'), data.get('expected_revision'), data.get('expected_state_hash'))
        from .participant_copy import event_copy
        if isinstance(result.get('receipt'), dict) and 'payload' in result['receipt']:
            result['receipt'] = event_copy(result['receipt'])
        accepted = self.accepted(ident, result)
        response = self.game(ident).state() if scene else accepted
        if scene:
            try:
                response['conversation'] = self.game(ident).context(data['action']['recipient'])
            except ValueError:
                response['conversation'] = None  # accepted retry may now be away from the speaker
            receipt = result.get('receipt') or {}
            category = receipt.get('payload', {}).get('category')
            text = ('Can you find out whom those six sacks were promised to?' if category == 'rb_dispute_heard'
                    else 'Here is the account you asked for.' if category == 'rb_evidence' else None)
            response['reply'] = {'text': text, 'voice': 'person', 'kind': 'speech', 'evidence_ids': [receipt['event_id']]} if text else None
        return {**response, **{k: result[k] for k in ('outcome', 'observation_id', 'command_index', 'accepted_revision', 'receipt')},
                **({'metadata_warning': accepted['metadata_warning']} if accepted.get('metadata_warning') else {})}

    def review(self, ident, action):
        runtime = self.mutable(ident)
        if not isinstance(action, dict):
            raise ValueError("Choose a supported action")
        if runtime.spec.setting["adapter"] == "commons" and action.get("action") in {"commit", "allocate"} and self.public_snapshot(runtime)["round_closed"]:
            raise ValueError("This round has settled. Advance to the next day before making a new promise or allocation.")
        trial = object.__new__(ExperienceRuntime)
        trial.__dict__ = {**runtime.__dict__, "world": copy.deepcopy(runtime.world), "commands": list(runtime.commands), "journal_path": None}
        try:
            trial._perform("action", copy.deepcopy(action))
        except ValueError as error:
            if str(error) == 'Insufficient owned credits' and action.get('action') == 'inspect':
                cost = runtime.spec.setting['rules']['inspection_cost']
                available = runtime.world.economy.cash['Player']
                raise ValueError(f"An inspection costs {cost:g} {'credit' if cost == 1 else 'credits'}. You have {available:g}.") from error
            raise
        token = secrets.token_hex(12)
        self.proposals[token] = {"id": ident, "hash": runtime.state_hash(), "action": copy.deepcopy(action)}
        if len(self.proposals) > 16:
            self.proposals.pop(next(iter(self.proposals)))
        summary = {"inspect": "Pay for a direct inspection; its result is disclosed after confirmation.",
                   "share": "Ask for a legitimately retained dated report; its content is disclosed after confirmation.",
                   "commit": "Make this quantity an obligation at the public settlement deadline.",
                   "allocate": "Fix this allocation for this round. It cannot be edited after confirmation. Actual delivery is determined at settlement."}.get(action.get("action"), "Review the terms before deciding.")
        return {"proposal_id": token, "action": copy.deepcopy(action), "summary": summary,
                "before": self.participant_metrics(runtime), "after": self.participant_metrics(trial),
                "revision": len(runtime.commands), "state_hash": runtime.state_hash(), "needs_confirmation": True,
                "notice": "The result appears after the choice goes through."}

    def accepted(self, ident, result):
        self.save_errors.pop(ident, None)
        if ident not in self.examples:
            try:
                self._update_meta(ident, updated_at=utc(), started=True)
                self.metadata_warnings.pop(ident, None)
            except (OSError, ValueError):
                # The world journal was already durably accepted. Do not tell
                # the user that its financial action failed, or resubmit it.
                result = {**result, "metadata_warning": "World choice saved; display metadata could not be updated."}
                self.metadata_warnings[ident] = result["metadata_warning"]
        return {**self.life(ident), "receipt": result.get("receipt"), "command_index": result.get("command_index"),
                **({"metadata_warning": result["metadata_warning"]} if result.get("metadata_warning") else {})}

    def confirm_review(self, ident, proposal_id):
        from .observation import ParticipantOperationError
        runtime = self.mutable(ident)
        if not isinstance(proposal_id, str):
            raise ParticipantOperationError('The review is missing. Reopen this choice.', 'review_missing')
        key = (ident, proposal_id)
        if key in self.confirmed_receipts:
            saved = self.confirmed_receipts[key]
            return {**self.accepted(ident, saved), 'outcome':'already_accepted', 'message':'That action already went through.'}
        proposal = self.proposals.get(proposal_id)
        if not proposal or proposal.get('id') != ident:
            raise ParticipantOperationError('We could not confirm this review’s result. Check your saved choices before trying again.', 'outcome_unknown', outcome='uncertain')
        if proposal['hash'] != runtime.state_hash():
            raise ParticipantOperationError('The offer changed. Check the new terms before deciding.', 'offer_changed')
        result = super().confirm(ident, proposal_id)
        self.confirmed_receipts[key] = copy.deepcopy(result)
        if len(self.confirmed_receipts) > 32:
            self.confirmed_receipts.pop(next(iter(self.confirmed_receipts)))
        return {**self.accepted(ident, result), 'outcome':'accepted'}

    def advance_product(self, ident, minutes, *, mode="compress", protect_known=True):
        runtime = self.mutable(ident)
        if type(protect_known) is not bool:
            raise ValueError("Choose whether to protect known opportunities")
        if minutes == "next":
            # Pacing may consult only participant-known obligations/public rules,
            # not the private simulator queue or upcoming hidden events.
            stops = build_history(runtime)["known_stops"]
            minutes = max(1, stops[0]["at"] - runtime.minute - 1) if stops else 30
        if type(minutes) is not int or not 1 <= minutes <= 365 * 1440:
            raise ValueError("Choose a bounded whole number of world minutes")
        original_target = runtime.minute + minutes
        protected = None
        if protect_known:
            stops = build_history(runtime)["known_stops"]
            relevant = [s for s in stops if runtime.minute < s["at"] <= original_target]
            if relevant:
                protected = relevant[0]
                available = protected["at"] - runtime.minute - 1
                if available <= 0:
                    raise ValueError("A known deadline is next. Make your choice or explicitly advance across it.")
                minutes = min(minutes, available)
        result = runtime.commit("advance", {"minutes": minutes, "mode": mode})
        return {**self.accepted(ident, result), "protected_stop": protected,
                "pacing_notice": "Only known obligations/public settlement windows can stop this advance. Your character does not spend or promise automatically."}

    def reflect(self, ident):
        runtime = self.get(ident)
        debrief = runtime.debrief()
        debrief["outcomes"] = self.participant_metrics(runtime)
        return {"life": self.metadata_for(ident), "choices": choices_then(runtime),
                "debrief": debrief, "history": build_history(runtime),
                "alternative_policy": "Try this history without that choice. Later recorded choices stay fixed when feasible; skipped commands are disclosed."}

    def public_fork(self, ident, command_index):
        result = self.get(ident).fork(command_index)
        if self.get(ident).spec.setting["adapter"] == "commons":
            hidden = {"credits_spent", "credit_total", "initial_credit_total", "information_shared"}
            for name in ("original", "alternative"):
                snapshot = result[name]
                snapshot["metrics"] = {k: v for k, v in snapshot["metrics"].items() if k not in hidden}
                snapshot["metrics"]["credits"] = snapshot["credits"]
            result["differences"] = {k: v for k, v in result["differences"].items() if k not in hidden}
        return result

    def expose_lab(self, ident, acknowledged):
        if acknowledged is not True:
            raise ValueError("Acknowledge that LAB reveals information your character may not know")
        self._update_meta(ident, operator_exposed=True)
        return {"life": self.metadata_for(ident), "snapshot": self.get(ident).snapshot(operator=True),
                "operator_exposed": True, "notice": "Local research view; this life is marked as operator-exposed."}

    def intention(self, ident, text, recipient="team_b"):
        self.mutable(ident)
        if not isinstance(text, str) or not 1 <= len(text.strip()) <= 600:
            raise ValueError("Use a short supported intention")
        if recipient not in TEAMS:
            raise ValueError("Choose a current representative")
        words = text.lower().strip()
        if re.search(r"\b(inspect|inspection|check)\b", words):
            action = {"action": "inspect"}
        elif re.search(r"\b(report|condition|news)\b", words):
            action = {"action": "share", "recipient": recipient}
        elif re.search(r"\b(promise|commit)\b", words):
            quantity = re.search(r"\b([1-9][0-9]?)\b", words)
            if not quantity:
                return {"clarification": "How many units would you like to promise? You will review it before committing.", "suggestions": ["Ask for the dated report", "Arrange an inspection", "Promise 4 units"]}
            action = {"action": "commit", "recipient": recipient, "quantity": int(quantity.group(1))}
        elif re.search(r"\b(need|needs|project|projects|request|requests)\b", words):
            view = self.life(ident)
            rows = [row['text'] for row in view.get('guide', {}).get('known', {}).get('project_requirements', []) if row.get('actor') == recipient]
            amount = view['snapshot'].get('requests', {}).get(recipient)
            request = f"Current request: {amount} capacity units." if amount is not None else "This team has not submitted a request in this round. That is different from requesting zero."
            return {"reply": "The public project register: " + ' '.join(rows or ["No project requirement is recorded for this team."]) + " " + request,
                    "kind": "public_record", "language_source": "authored public register"}
        else:
            return {"clarification": "Ask what the team's project needs, request a dated report, arrange an inspection, or review a quantified promise. Ordinary speech is not a commitment.",
                    "suggestions": ["Ask for the dated report", "Arrange an inspection", "Promise 4 units"]}
        return {**self.review(ident, action), "language_source": "offline supported-intent grammar"}

    def annotation(self, ident, *, note=None, event_id=None):
        runtime = self.mutable(ident)
        patch = {}
        if note is not None:
            if not isinstance(note, str) or not 1 <= len(note.strip()) <= 1200:
                raise ValueError("Personal notes must be short nonempty text")
            patch["notes"] = [*self.metadata[ident].get("notes", [])[-19:], {"text": note.strip(), "minute": runtime.minute, "created_at": utc(), "kind": "personal_interpretation"}]
        if event_id is not None:
            if type(event_id) is not int or event_id not in runtime.visible_ids():
                raise ValueError("A bookmark must identify an event you legitimately observed")
            patch["bookmarks"] = list(dict.fromkeys([*self.metadata[ident].get("bookmarks", []), event_id]))[-40:]
        if not patch:
            raise ValueError("Provide a note or a visible event to bookmark")
        self._update_meta(ident, **patch)
        return {"notes": self.metadata[ident].get("notes", []), "bookmarks": self.metadata[ident].get("bookmarks", []), "notice": "Personal notes are not world truth and are not installed into NPC memory."}

    def telemetry(self, ident, data):
        runtime = self.get(ident)
        fields = {"id", "opt_in", "event", "session_id", "reason", "accepted_revision", "first_meaningful", *USAGE_TIMINGS}
        if set(data) - fields:
            raise ValueError("Raw conversations and unknown telemetry fields are not collected")
        if "opt_in" in data and type(data["opt_in"]) is not bool:
            raise ValueError("Telemetry consent must be a boolean")
        event = data.get("event")
        if event is not None and (not isinstance(event, str) or event not in USAGE_EVENTS):
            raise ValueError("Unsupported local event")
        if "reason" in data and (not isinstance(data["reason"], str) or data["reason"] not in USAGE_REASONS):
            raise ValueError("Usage reasons must be a supported category, never free text")
        for key in USAGE_TIMINGS:
            if key in data and (type(data[key]) is not int or not 0 <= data[key] <= 3600000):
                raise ValueError("Usage time must be a bounded whole number of milliseconds")
        # Retain the older explicit-active-only client boundary; new clients send
        # the complete partition. No server wall time is inferred to be active.
        active = data.get("active_ms", 0)
        foreground = data.get("foreground_ms", active + data.get("idle_ms", 0))
        visible = data.get("visible_ms", foreground)
        idle = data.get("idle_ms", foreground - active)
        if not 0 <= active <= foreground <= visible <= 3600000 or idle != foreground - active:
            raise ValueError("Usage time must consistently partition visible and foreground intervals")
        session = data.get("session_id", "local")
        if not isinstance(session, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", session):
            raise ValueError("Session identity must be a short opaque local identifier")
        action = {}
        if event == "meaningful_action":
            revision = data.get("accepted_revision")
            if type(revision) is not int or not 1 <= revision <= len(runtime.commands):
                raise ValueError("Meaningful usage must identify an accepted command revision")
            command = runtime.commands[revision - 1]
            if not meaningful_command(command):
                raise ValueError("Navigation and waiting are not meaningful accepted choices")
            if type(data.get("first_meaningful")) is not bool:
                raise ValueError("First meaningful marker must be a boolean")
            action = {"accepted_revision": revision, "meaningful_kind": command["data"]["action"],
                      "first_meaningful": data["first_meaningful"]}
        elif "accepted_revision" in data or "first_meaningful" in data:
            raise ValueError("Accepted revision markers belong only to meaningful action events")
        if "opt_in" in data:
            self._update_meta(ident, telemetry_opt_in=data["opt_in"])
        enabled = self.metadata[ident].get("telemetry_opt_in", False)
        if not enabled or event is None:
            return {"opt_in": enabled, "recorded": False}
        row = {"schema": "kalends-usage-v2", "build": BUILD, "session_id": session, "life_id": ident,
               "world_minute": runtime.minute, "active_ms": active, "visible_ms": visible,
               "foreground_ms": foreground, "idle_ms": idle, "elapsed_ms": data.get("elapsed_ms", 0),
               "event": event, "at": utc(), "operator_exposed": self.metadata[ident].get("operator_exposed", False),
               **({"reason": data["reason"]} if "reason" in data else {}), **action}
        guide = guide_preferences(self.metadata[ident].get("guide"))
        row.update(guided=bool(guide.get("guided_origin") or guide.get("enabled")), practice=guide.get("practice") is True,
                   provenance_unknown=self.metadata[ident].get("provenance_unknown") is True,
                   excluded_from_unassisted_research=bool(guide.get("guided_origin") or guide.get("enabled") or guide.get("practice") or row["operator_exposed"] or self.metadata[ident].get("provenance_unknown")))
        if self.directory:
            path = self.directory / ".product/events.jsonl"
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a") as stream:
                stream.write(json.dumps(row) + "\n")
        return {"opt_in": True, "recorded": True}

    def research(self):
        current_path = ROOT / "results/next_phase/research/frozen_comparison_v2/summary.json"
        comparison = None
        if current_path.is_file():
            current = json.loads(current_path.read_text())
            comparison = {key: current[key] for key in ("worlds", "candidate_vs_v3", "interpretation", "source_unchanged", "failures")}
            comparison["groups"] = [g for g in current["groups"] if g["split"] == "reviewer_holdout"]
            comparison["scope"] = "Offline internal variants of one two-round scaffold. One completion improvement, two ties and one shared information limit; no human or general intelligence result."
        return {"build": BUILD, "live_model_calls": self.cognition.metrics["external_calls"], "comparison": comparison,
                "cards": [
                    {"title": "What is built", "claim": "Two finite world adapters share authoritative history, private observations, exact time and validated actions.", "limit": "A new domain still requires explicit rules and tests."},
                    {"title": "Persistent cognition", "claim": "V3 and V2 tied in all 432 matched pairs in the prior 972-world exploratory study.", "source": "results/experience_os/cognition_v2/", "sampling_unit": "paired world seed within authored family", "limit": "One-day authored tasks; no human or multi-month intelligence result."},
                    {"title": "Time and agency", "claim": "Exact/conservative scheduling preserved measured histories; no added adaptive speed advantage was established.", "source": "results/experience_os/temporal_v2_20261024/", "limit": "Protecting a visible choice window is a pacing property, not compute acceleration or human learning."},
                ], "next_phase_report_available": (ROOT / "docs/next_phase/RESEARCH_REPORT.md").exists(),
                "human_evidence": "No human participants, customer demand, retention or educational transfer results have been measured."}
