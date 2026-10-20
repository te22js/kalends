"""Scoped natural-language compilation and evidence-grounded offline dialogue.

The adapter receives a single authorized view, never a simulation or ledger.
It proposes actions; only a separately validated confirmation can execute one.
No paid service or unconstrained text generator is used by the default adapter.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import time
from typing import Protocol

VERSION = "genesis-rules-1"


class LanguageAdapter(Protocol):
    model_id: str

    def propose(self, text: str, recipient: str, view: dict, player_view: dict) -> dict: ...


def _records(view):
    return view.get("experiences", view.get("memories", []))


def _ids(view):
    return {r["event_id"] for r in _records(view) if isinstance(r.get("event_id"), int)}


def _reply(text, evidence=(), status="remembered"):
    return {"text": text, "evidence_ids": sorted(set(evidence)), "epistemic_status": status}


def grounded_reply(text, view):
    """Render only current bounded memories and durable own account state."""
    normalized = text.lower()
    records = _records(view)
    if any(word in normalized for word in ("trust", "remember me", "remember you")):
        trust = view.get("trust_player", next((r["trust"] for r in view.get("relationships", [])
                                              if r.get("speaker") == "Player"), .6))
        if isinstance(trust, dict):
            trust = trust.get("Player", .6)
        relevant = [r for r in records if r.get("source_agent") == "Player" or
                    r.get("subject") == "relationship" and r.get("predicate") == "Player"]
        if not relevant:
            return _reply("My trust in you is %.0f%%. I cannot recall a retained event that explains it. "
                          "I won't invent a reason." % (100 * trust), status="uncertain")
        assessments = [r for r in relevant if r.get("subject") == "relationship" and
                       r.get("predicate") == "Player"]
        chosen = assessments[-2:] if assessments else relevant[-2:]
        details = " ".join(r.get("text", "") for r in chosen)
        accessible = _ids(view)
        evidence = {r["event_id"] for r in chosen}
        for receipt in view.get("receipts", []):
            if receipt.get("event_id") in evidence:
                evidence.update(i for i in receipt.get("evidence_ids", []) if i in accessible)
                date = receipt.get("claim_as_of")
                evidence.update(r["event_id"] for r in records if r.get("kind") == "observed" and
                                r.get("as_of") == date and
                                (r.get("subject") == "grain" and r.get("predicate") == "supply" or
                                 r.get("subject") == "dispatch_log" and r.get("predicate") == "grain_supply_at_%s" % date))
                evidence.update(r["event_id"] for r in view.get("receipts", []) if
                                receipt.get("claim_event") in r.get("evidence_ids", []) and
                                r.get("cash_delta", 0) < 0 and r["event_id"] in accessible)
        if not assessments:
            details += " I don't retain a Player-specific assessment that explains my current trust."
        return _reply("My trust in you is %.0f%%. What I can still recall: %s" %
                      (100 * trust, details), evidence)
    if any(word in normalized for word in ("goal", "need", "contract", "delivery", "deliveries")):
        commitments = view.get("commitments", [])
        due = [c for c in commitments if c.get("status", "open") == "open"]
        detail = "; ".join("%s grain due at tick %s" %
                           (c.get("quantity", c.get("required", "?")), c.get("due_tick", c.get("deadline", "?")))
                           for c in due[:3])
        return _reply("I work as %s. %s" % (view.get("role", "a citizen"),
                      ("My open commitments: " + detail + ".") if detail else
                      "I have no open delivery commitment in my account."), status="own_account")
    beliefs = view.get("beliefs", view.get("knowledge", {}))
    supply = beliefs.get("grain.supply", {})
    value = supply.get("value", "unknown")
    if value == "unknown":
        return _reply("I don't have a retained, accepted report about the grain supply. "
                      "Ask for an inspection if you need current evidence.", status="uncertain")
    evidence = [i for i in supply.get("evidence_ids", []) if i in _ids(view)]
    # An accepted value without accessible evidence is not enough to generate a story.
    if not evidence:
        return _reply("I cannot recall evidence for a supply report right now.", status="uncertain")
    return _reply("The report I can recall says grain supply was %s as of tick %s. "
                  "That is what reached me, not a guarantee about the present." %
                  (value, supply.get("as_of", "unknown")), evidence, "reported")


class OfflineAdapter:
    model_id = "offline/scoped-grammar"

    def propose(self, text, recipient, view, player_view):
        text = text.strip()
        if not text or len(text) > 2000:
            raise ValueError("message must contain 1..2000 characters")
        lower = text.lower().replace("’", "'")
        result = {"interpretations": [], "reply": None, "clarification": None}

        def add(action, label, transmission):
            result["interpretations"].append({"id": str(len(result["interpretations"])),
                "label": label, "action": action, "transmission": transmission,
                "requires_confirmation": True})

        sharing_verified = any(phrase in lower for phrase in
                               ("i verified", "i inspected", "share my inspection", "share what i verified", "correct my claim"))
        if sharing_verified:
            observed = [r for r in _records(player_view) if r.get("kind") == "observed" and
                        r.get("subject") == "grain" and r.get("predicate") == "supply"]
            if not observed:
                result["clarification"] = "You don't have a retained personal inspection to share. Verify the grain supply first."
                return result
            observation = max(observed, key=lambda r: (r["as_of"], r["event_id"]))
            add({"kind": "claim", "recipient": recipient, "value": observation["value"],
                 "as_of": observation["as_of"], "root_event": observation.get("claimed_origin_event") or observation["event_id"]},
                "Share your actual inspection", "Tell %s what you personally inspected: grain was %s as of tick %s. "
                "Your inspection #%s is the source; this does not prove a later state." %
                (recipient, observation["value"], observation["as_of"], observation["event_id"]))
        elif re.search(r"\b(verify|inspect|check the (?:grain|supply)|verification)\b", lower):
            add({"kind": "verify", "agent": "Player"}, "Pay for an inspection",
                "Pay 2 denarii now. A private inspection reaches you next tick; citizens do not receive it automatically.")
        elif re.search(r"\b(retract|withdraw|take back)\b", lower):
            own = [r for r in _records(player_view) if r.get("kind") == "told" or
                   "claim" in r.get("text", "").lower()]
            own = [r for r in own if r.get("source_agent") == "Player" or
                   "player" in r.get("text", "").lower()]
            numbers = re.findall(r"#(\d+)", lower)
            if numbers:
                root = int(numbers[0])
            elif own:
                root = own[-1].get("claimed_origin_event", own[-1]["event_id"])
            else:
                result["clarification"] = "Which claim should be retracted? Use its event number, for example ‘retract #12’."
                return result
            add({"kind": "retract", "recipient": recipient, "root_event": root},
                "Retract claim #%s" % root, "Tell %s that you withdraw claim #%s. The retraction must travel too." % (recipient, root))
        elif re.search(r"\b(buy|trade|sell|contract|promise|agreement)\b", lower):
            quantity_match = re.search(r"\b(\d+)\b", lower)
            if not quantity_match:
                result["clarification"] = "How many grain units? For example, ‘buy 2 grain’ or ‘contract 2 grain due in 4 ticks’."
                return result
            quantity = int(quantity_match[1])
            if not 1 <= quantity <= 12:
                raise ValueError("quantity must be from 1 to 12 units")
            if any(w in lower for w in ("contract", "promise", "agreement")):
                match = re.search(r"(?:in|tick|ticks)\s+(\d+)", lower)
                deadline = player_view.get("tick", 0) + (int(match[1]) if match else 4)
                add({"kind": "contract", "recipient": recipient, "quantity": quantity, "deadline": deadline},
                    "Accept a delivery obligation", "Promise %s %s grain units by tick %s. Actual deliveries earn payment; missing units incur penalties." % (recipient, quantity, deadline))
            elif "sell" in lower:
                result["clarification"] = "This demo supports buying grain and delivery contracts. To deliver, create a contract and hold enough grain by its deadline."
            else:
                counterparty = "market" if "market" in lower else recipient
                add({"kind": "trade", "recipient": counterparty, "quantity": quantity, "direction": "buy"},
                    "Buy grain through %s" % recipient,
                    "Buy %s grain units from %s. Inventory, your cash, and commercial access must back the trade." % (quantity, counterparty))
        elif re.search(r"\b(go to|move to|walk to)\b", lower):
            result["clarification"] = "Travel is currently automatic for citizens. You can speak, buy, verify or enter a delivery agreement."
        else:
            grain = any(w in lower for w in ("grain", "shipment", "supply"))
            negative = bool(re.search(r"isn't|is not|not arriving|won't|will not|disrupt|shortage|cancel|late|no grain|not available|unavailable", lower))
            positive = bool(re.search(r"\b(available|arriving|arrive|normal|plentiful|restored|reliable)\b", lower))
            question = lower.endswith("?") or re.match(r"^(what|why|who|how|do you|tell me|show|hello|hi)\b", lower)
            if grain and not question and (negative or positive):
                values = ["disrupted"] if negative else ["available"]
                # Explicit alternatives require the player to choose; simple negation doesn't.
                if re.search(r"\b(or|maybe|either|not sure)\b", lower):
                    values = ["disrupted", "available"]
                    result["clarification"] = "Which claim do you want to transmit?"
                for value in values:
                    add({"kind": "claim", "recipient": recipient, "value": value,
                         "as_of": max(0, player_view.get("tick", 0)), "root_event": None},
                        "Say supply is %s" % value,
                        "Tell only %s: ‘Grain supply is %s.’ Source: Player. This is an unverified claim, not a world-state change." % (recipient, value))
            else:
                result["reply"] = grounded_reply(text, view)
        return result


def validate_result(result, recipient, view, player_view):
    """Reject injected capabilities or inaccessible evidence from any adapter."""
    if not isinstance(result, dict) or set(result) - {"interpretations", "reply", "clarification"}:
        raise ValueError("invalid adapter response")
    interpretations = result.get("interpretations", [])
    if not isinstance(interpretations, list) or len(interpretations) > 3:
        raise ValueError("adapter may return at most three interpretations")
    allowed = {"claim": {"kind", "recipient", "value", "as_of", "root_event"},
               "verify": {"kind", "agent"}, "trade": {"kind", "recipient", "quantity", "direction"},
               "contract": {"kind", "recipient", "quantity", "deadline"},
               "retract": {"kind", "recipient", "root_event"}}
    for interpretation in interpretations:
        if not isinstance(interpretation, dict) or not isinstance(interpretation.get("action"), dict):
            raise ValueError("each interpretation requires an action object")
        action = interpretation.get("action", {})
        kind = action.get("kind")
        if not isinstance(kind, str) or kind not in allowed or set(action) != allowed[kind]:
            raise ValueError("adapter proposed an unsupported action schema")
        if (action.get("recipient", recipient) != recipient and not
                (kind == "trade" and action.get("recipient") == "market")) or action.get("agent", "Player") != "Player":
            raise ValueError("adapter cannot change another participant's authority")
        if kind == "claim":
            if action["value"] not in ("available", "disrupted"):
                raise ValueError("invalid supply claim")
            if action["root_event"] is None:
                if action["as_of"] != max(0, player_view.get("tick", 0)):
                    raise ValueError("unverified claims must identify the current utterance time")
            elif not any(r.get("kind") == "observed" and r.get("subject") == "grain" and
                         r.get("predicate") == "supply" and r.get("value") == action["value"] and
                         r.get("as_of") == action["as_of"] and
                         (r.get("claimed_origin_event") or r["event_id"]) == action["root_event"]
                         for r in _records(player_view)):
                raise ValueError("a verified claim requires your retained personal inspection")
        if kind in ("trade", "contract") and (type(action["quantity"]) is not int or not 1 <= action["quantity"] <= 12):
            raise ValueError("invalid quantity")
        if kind == "trade" and action["direction"] != "buy":
            raise ValueError("invalid trade direction")
        if kind == "verify" and player_view.get("cash", 0) < 2:
            raise ValueError("an inspection costs 2 denarii")
        if kind == "contract" and (type(action["deadline"]) is not int or
                 not player_view.get("tick", 0) < action["deadline"] <= player_view.get("tick", 0) + 24):
            raise ValueError("contract deadline must be within the next 24 ticks")
        if kind == "retract" and (type(action["root_event"]) is not int or action["root_event"] < 0):
            raise ValueError("invalid claim id")
    reply = result.get("reply")
    if reply is not None and (not isinstance(reply, dict) or
                             not set(reply.get("evidence_ids", [])).issubset(_ids(view))):
        raise ValueError("adapter cited evidence outside the character's retained memory")
    return copy.deepcopy(result)


def compile_utterance(text, recipient, view, player_view, adapter=None):
    started = time.perf_counter()
    default_adapter = adapter is None
    adapter = adapter or OfflineAdapter()
    result = validate_result(adapter.propose(text, recipient, copy.deepcopy(view), copy.deepcopy(player_view)),
                             recipient, view, player_view)
    if not default_adapter and result.get("reply") is not None:
        # Evidence IDs alone cannot establish that arbitrary generated prose is true.
        # Optional adapters can interpret intent; factual replies use this grounded renderer.
        result["reply"] = grounded_reply(text, view)
    if not default_adapter:
        result["clarification"] = ("Choose the permitted action below." if result["interpretations"] else
                                   "Try a supply claim, an inspection, a grain purchase, a delivery contract, or a question.")
    for index, choice in enumerate(result["interpretations"]):
        action = choice["action"]
        kind = action["kind"]
        if kind == "claim":
            label = "Tell %s: supply %s" % (action["recipient"], action["value"])
            source = ("your personal inspection #%s" % action["root_event"] if action["root_event"] is not None
                      else "Player's unverified claim")
            transmission = "Tell only %s: ‘Grain supply is %s as of tick %s.’ Source: %s. Citizens may pass it on; the claim does not change the shipment." % (action["recipient"], action["value"], action["as_of"], source)
        elif kind == "verify":
            label, transmission = "Pay for an inspection", "Pay 2 denarii now. A private inspection arrives next tick. The visit may include at most two dispatch records from the last 8 ticks."
        elif kind == "trade":
            label = "Buy %s grain" % action["quantity"]
            transmission = "Buy %s grain units from %s at the current market price. Cash, inventory, and commercial access must back the trade." % (action["quantity"], action["recipient"])
        elif kind == "contract":
            label = "Promise a grain delivery"
            transmission = "Promise %s %s grain units by tick %s. You receive 4 denarii per delivered unit and pay 5 per missing unit." % (action["recipient"], action["quantity"], action["deadline"])
        else:
            label = "Retract claim #%s" % action["root_event"]
            transmission = "Tell %s that you withdraw your source claim #%s. Retractions travel through the same bounded communication system." % (action["recipient"], action["root_event"])
        choice.update(id=str(index), label=label, transmission=transmission, requires_confirmation=True)
    authorized = {"recipient": view, "player": player_view}
    result["adapter"] = {"model_id": adapter.model_id, "version": VERSION,
        "authorized_view_sha256": hashlib.sha256(json.dumps(authorized, sort_keys=True).encode()).hexdigest(),
        "compile_wall_ms": round((time.perf_counter() - started) * 1000, 4),
        "inference_latency_ms": 0 if default_adapter else None,
        "inference_cost_usd": 0 if default_adapter else None}
    return result
