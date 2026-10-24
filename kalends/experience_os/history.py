"""Participant history from admitted records and the participant's own register.

This is a presentation projection. It neither supplies NPC memories nor reads
the clock queue, operator snapshot, or another person's institutional account.
"""
from __future__ import annotations

import copy
import json
from .participant_copy import event_text, quantity


PERSON_LABELS = {"Player": "Aelia", "team_a": "Amir", "team_b": "Mira", "team_c": "Lin"}
ROLES = {"team_a": "Survey", "team_b": "Instrument systems", "team_c": "Follow-up"}
_ROUTINES = {"move", "movement", "player_move", "time_advanced", "routine", "institutional_routine", "routine_note", "request", "inspection_paid"}


def _label(actor, setting):
    return "You" if actor == "Player" and setting == "commons" else PERSON_LABELS.get(actor, actor)


def _human(text, setting):
    text = str(text)
    for actor in ("team_a", "team_b", "team_c", "Player"):
        text = text.replace(actor, _label(actor, setting))
    return text.replace("You promises", "You promise").replace("with You", "with you")


def _value(event):
    value = event["payload"].get("value")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            pass
    return value


def _kind(event):
    p = event["payload"]
    category = p.get("category", "record")
    if category in ("arrival", "city_initialized", "goal_register"):
        return "arrival"
    if category in _ROUTINES or "routine" in category:
        return "routine"
    if "correction" in category or "revision" in category:
        return "correction"
    if "membership" in category or "affiliation" in category or p.get("access_add"):
        return "affiliation"
    if category == "promise" or p.get("new_commitment") or category == "rb_commission":
        return "commitment"
    if any(word in category for word in ("settled", "kept", "missed", "resolution", "reconcile", "work_complete")):
        return "consequence"
    if category in ("report", "condition") or event.get("etype") == "tell":
        return "encounter"
    return "encounter"


def _evidence(events, setting):
    """A bounded record shape; source IDs never become archive lookup grants."""
    allowed = {e["event_id"] for e in events}
    result = []
    for e in events:
        p = e["payload"]
        row = {"event_id": e["event_id"], "at": e["tick"], "category": p.get("category", "record"),
               "title": _human(event_text(e), setting),
               "actors": list(e.get("actors", ())),
               "claim_kind": "testimony" if e.get("etype") == "tell" else "recorded_observation",
               "related_event_ids": [i for i in p.get("parents", ()) if i in allowed]}
        # A disclosed document/report is admitted evidence. Its canonical source
        # identity is intentionally not promoted to an accessible trace link.
        if "value" in p:
            row["value"] = copy.deepcopy(p["value"])
        if "as_of" in p:
            row["as_of"] = p["as_of"]
        if isinstance(p.get("document"), dict):
            row["document"] = {k: copy.deepcopy(p["document"][k]) for k in ("title", "text", "as_of", "kind") if k in p["document"]}
        result.append(row)
    return result


def _beat(event, setting, allowed):
    p = event["payload"]
    title = _human(event_text(event), setting)
    factual = title
    if p.get("category") in ("report", "condition") and "value" in p:
        factual = f"{title} Reported condition: {p['value']}, dated minute {p.get('as_of', event['tick'])}."
    return {"id": f"event-{event['event_id']}", "kind": _kind(event), "at": event["tick"],
            "title": title, "text": factual, "body": factual,
            "participants": [{"id": a, "name": _label(a, setting)} for a in event.get("actors", ())],
            "evidence_ids": [event["event_id"]],
            "related_event_ids": [i for i in p.get("parents", ()) if i in allowed],
            "claim_kind": "testimony" if event.get("etype") == "tell" else "recorded_outcome" if _kind(event) == "consequence" else "recorded_observation",
            "uncertainties": ["A dated report does not establish the present condition."] if p.get("category") in ("report", "condition") else []}


def _known_commitments(runtime, events):
    setting = runtime.spec.setting["adapter"]
    allowed = {e["event_id"] for e in events}
    rows = []
    if setting == "commons":
        r = runtime.world.round
        matching = [e for e in events if e["payload"].get("prop") == ["experience", f"promises:{r}"]]
        # This public register, unlike episodic recall, survives forgetting.
        settled = any(e["payload"].get("prop") == ["experience", f"outcome:{r}"] for e in events)
        promises = {} if settled else runtime.world.get(f"promises:{r}", {})
        for actor, quantity in promises.items():
            support = next((e for e in reversed(matching) if _value(e).get(actor) == quantity), None)
            if support is None:
                continue
            deadline = (r + 1) * runtime.world.rules["round_minutes"] - 1
            text = f"You promised {quantity} {'unit' if quantity == 1 else 'units'} to {_label(actor, setting)} by minute {deadline}. Allocation and delivery are separate steps."
            rows.append({"id": f"promise:{r}:{actor}", "recipient": actor, "person": _label(actor, setting),
                         "quantity": quantity, "fulfilled": 0, "deadline": deadline, "status": "open",
                         "text": text, "evidence_ids": [support["event_id"]], "source": "own institutional promise register"})
    else:
        # Access to one's enforceable register is permitted independently of
        # episode retention; no NPC's private account is read here.
        for c in runtime.world.economy.commitments.get("Player", ()):
            if c.get("status") != "open":
                continue
            support = [c["event_id"]] if c.get("event_id") in allowed else []
            for e in events:
                p = e["payload"]
                initial = p.get("commitments", {}).get("Player", ())
                updates = p.get("commitment_updates", ())
                if (any(row.get("id") == c.get("id") for row in initial)
                        or any(row.get("id") == c.get("id") and row.get("agent") == "Player" for row in updates)):
                    support.append(e["event_id"])
            support = sorted(set(support))
            if not support:
                continue
            recipient = c.get("beneficiary", "")
            unit = "service minutes" if c.get("id") in {"rebirth-service", "household-service"} else "units"
            text = f"Your agreement with {recipient}: {c.get('fulfilled', 0)} of {c.get('quantity', 0)} {unit} completed, due minute {c.get('deadline')}."
            rows.append({"id": c.get("id"), "recipient": recipient, "person": recipient,
                         "quantity": c.get("quantity", 0), "fulfilled": c.get("fulfilled", 0),
                         "unit": unit,
                         "deadline": c.get("deadline"), "status": "open", "text": text,
                         "evidence_ids": support, "source": "own institutional commitment register"})
    return rows


def _known_stops(runtime, events, commitments):
    stops = [{"at": c["deadline"], "kind": "known_commitment", "title": c["text"],
              "evidence_ids": list(c["evidence_ids"])} for c in commitments
             if type(c.get("deadline")) is int and c["deadline"] > runtime.minute]
    if runtime.spec.setting["adapter"] == "commons":
        deadline = (runtime.world.round + 1) * runtime.world.rules["round_minutes"] - 1
        public_round = next((e for e in reversed(events) if e["payload"].get("prop") == ["experience", f"requests:{runtime.world.round}"]), None)
        if public_round and runtime.minute < deadline < runtime.spec.termination["at"]:
            stops.append({"at": deadline, "kind": "public_round_deadline", "title": "The current allocation settles at this publicly declared deadline.",
                          "evidence_ids": [public_round["event_id"]], "rule": "round_minutes - 1; fixed public settlement rule"})
    # Declared future opportunities are not consulted: their presence may expose
    # an event the participant has not yet observed. No clock peek is involved.
    return sorted(stops, key=lambda row: (row["at"], row["kind"]))


def _replay(runtime):
    from .runtime import ExperienceRuntime
    return ExperienceRuntime(runtime.spec, retention=runtime.retention)


def _apply_prefix(replay, command):
    replay._perform(command["operation"], copy.deepcopy(command["data"]))
    replay.commands.append(copy.deepcopy(command))


def choices_then(runtime):
    """Evidence at the exact accepted-command boundary, before its effects.

    A later correction is never attached to an earlier decision. The complete
    admitted prefix is included for review; it is not NPC working memory.
    """
    replay = _replay(runtime)
    setting = runtime.spec.setting["adapter"]
    choices = []
    for index, command in enumerate(runtime.commands):
        if command["operation"] == "action":
            events = replay.events()
            choices.append({"index": index, "action": copy.deepcopy(command["data"]), "at": command["at"],
                            "then_evidence": _evidence(events, setting),
                            "known_commitments": _known_commitments(replay, events),
                            "uncertainties": ["These are the participant's admitted records before the choice, not present-day hindsight or another person's retained memory."]})
        _apply_prefix(replay, command)
    return choices


def build_history(runtime, *, last_seen_minute=0, seen_revision=None):
    if type(last_seen_minute) is not int or last_seen_minute < 0:
        raise ValueError("last_seen_minute must be a nonnegative whole minute")
    if seen_revision is not None and (type(seen_revision) is not int or not 0 <= seen_revision <= len(runtime.commands)):
        raise ValueError("seen_revision must identify an accepted-command prefix")
    events = runtime.events()
    setting = runtime.spec.setting["adapter"]
    allowed = {e["event_id"] for e in events}
    beats = [_beat(e, setting, allowed) for e in events]
    chapters, routine = [], []
    for beat in beats:
        if beat["kind"] == "routine":
            routine.append(beat)
            continue
        boundary = beat["kind"] in {"arrival", "commitment", "consequence", "affiliation", "correction"}
        if not chapters or boundary:
            chapters.append({"id": f"chapter-{beat['id']}", "kind": beat["kind"], "title": beat["title"],
                             "at": beat["at"], "evidence_ids": list(beat["evidence_ids"]), "beats": [], "routines": []})
        if routine:
            chapters[-1]["routines"].append({"title": "Everyday activity", "expandable": True,
                                               "count": len(routine), "beats": routine})
            routine = []
        chapters[-1]["beats"].append(beat)
    if routine:
        if not chapters:
            chapters.append({"id": "ordinary-life", "kind": "routine", "title": "Everyday activity", "at": routine[0]["at"], "evidence_ids": [], "beats": [], "routines": []})
        chapters[-1]["routines"].append({"title": "Everyday activity", "expandable": True, "count": len(routine), "beats": routine})
    commitments = _known_commitments(runtime, events)
    people = []
    identities = [p["id"] for p in runtime.spec.participants if p["id"] != "Player"]
    for actor in identities:
        encounters = [b for b in beats if actor in {p["id"] for p in b["participants"]}]
        row = {"id": actor, "name": _label(actor, setting), "role": ROLES.get(actor, next(p["role"] for p in runtime.spec.participants if p["id"] == actor)),
               "episodes": encounters[-6:], "evidence_ids": [i for b in encounters[-6:] for i in b["evidence_ids"]],
               "uncertainties": ["Recorded encounters do not establish what this person currently remembers."]}
        if setting == "commons":
            settled = [e for e in events if e["payload"].get("category") == "allocation_settled"]
            if settled:
                event = settled[-1]
                outcome = _value(event)
                allocated, delivered = outcome["allocation"].get(actor, 0), outcome["executed"].get(actor, 0)
                row["outcome"] = {"text": f"{row['name']} received {delivered} of {allocated} allocated {'unit' if allocated == 1 else 'units'}.",
                                  "allocated": allocated, "delivered": delivered, "evidence_ids": [event["event_id"]], "claim_kind": "recorded_outcome"}
        people.append(row)
    if seen_revision is not None:
        prior = _replay(runtime)
        for command in runtime.commands[:seen_revision]:
            _apply_prefix(prior, command)
        seen = {e["event_id"] for e in prior.events()}
        fresh = [b for b in beats if b["evidence_ids"][0] not in seen]
    else:
        fresh = [b for b in beats if b["at"] > last_seen_minute]
    material = [b for b in fresh if b["kind"] != "routine"][-3:]
    independent = [b for b in fresh if all(p["id"] != "Player" for p in b["participants"])][-2:]
    return {"schema_version": 1, "experience": runtime.spec.id, "revision": len(runtime.commands), "minute": runtime.minute,
            "chapters": chapters, "beats": beats, "people": people, "unresolved": commitments,
            "known_commitments": commitments, "known_stops": _known_stops(runtime, events, commitments),
            "return_summary": {"changes": material, "independent_developments": independent,
                               "unresolved": commitments[:1], "from_minute": last_seen_minute,
                               "text": "Your saved world resumes from its recorded moment. Movement, accepted work and explicit time controls can advance world time.",
                               "offline_progress": False},
            "elapsed_policy": "Paused while the local server is stopped; no offline progression is claimed.",
            "uncertainties": ["History contains participant-admitted evidence. Testimony remains testimony; related records do not prove necessary causes."]}
