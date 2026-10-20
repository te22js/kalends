"""Scoped language proposals. The world, never a language provider, authorizes effects.

The optional provider is a callable adapter receiving this module's JSON envelope.
No credentials or provider is required; the default is deterministic and costs $0.
"""
from __future__ import annotations

from concurrent.futures import Future, TimeoutError
from dataclasses import dataclass
import json
import re
import threading
from typing import Protocol


class LanguageProvider(Protocol):
    def __call__(self, request: dict) -> dict: ...


ACTIONS = {"accept_delivery", "work", "buy", "deliver", "inspect", "patronage", "service", "sell_information", "claim", "talk"}
NUMBERS = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"ten":10}


def validate_action(action):
    if not isinstance(action,dict) or set(action)-{"action","recipient","quantity","value","topic"}:
        raise ValueError("Unexpected proposal fields")
    if action.get("action") not in ACTIONS or not isinstance(action.get("recipient"),str):
        raise ValueError("Invalid action schema")
    if type(action.get("quantity",1)) is not int or not 1 <= action.get("quantity",1) <=12:
        raise ValueError("Quantity must be 1..12")
    if action["action"] == "claim" and action.get("value") not in ("available","disrupted"):
        raise ValueError("Invalid claim")
    if action["action"] == "talk" and action.get("topic","memory") not in ("memory","supply","role"):
        raise ValueError("Invalid conversation topic")
    return dict(action)


def grounded_reply(view, topic="memory"):
    """Only a character's retained experiences and own role are inputs."""
    if topic == "role":
        return {"text":f"I am {view['role']}. {view['social_position']}. {view['goals'][0]}.","evidence_ids":[],"epistemic_status":"Authored fictional role; historical status is labeled separately."}
    if topic == "supply":
        knowledge=view["beliefs"]["grain.supply"]
        if knowledge["value"] == "unknown":
            return {"text":"I have no retained report of the flour dispatch. I would have to ask or pay for an inspection.","evidence_ids":[],"epistemic_status":"Unknown to this character"}
        return {"text":f"My retained report says flour supply was {knowledge['value']} at world minute {knowledge['as_of']}. That is a dated report, not a guarantee about now.","evidence_ids":knowledge["evidence_ids"],"epistemic_status":"Dated observation" if knowledge.get("direct") else "Dated hearsay"}
    significant=sorted([e for e in view["experiences"] if e["subject"] == "relationship" or e["kind"] == "episodic" and "You " in e["text"]],
                       key=lambda e:(e["tick"],e["event_id"]))[-3:]
    if significant:
        return {"text":" ".join(e["text"] for e in significant),"evidence_ids":[e["event_id"] for e in significant],"epistemic_status":"Literal retained experiences; bounded memory"}
    return {"text":f"I have no retained personal dealings with you yet. {view['goals'][0]}.","evidence_ids":[],"epistemic_status":"No retained shared episode"}


@dataclass
class ProposalLanguage:
    provider: LanguageProvider | None = None
    timeout_seconds: float = 2.0
    retries: int = 1

    def __post_init__(self):
        if not 0 < self.timeout_seconds <=10 or not 0 <= self.retries <=1:
            raise ValueError("Provider budget must be bounded")
        self.metrics={"provider_configured":self.provider is not None,"provider_calls":0,"fallbacks":0,"known_cost_usd":0.0 if self.provider is None else None}
        # One bounded worker: a stalled provider cannot create unbounded request threads.
        self._pending=None

    def _submit(self,request):
        future=Future()
        def call():
            try: future.set_result(self.provider(request))
            except Exception as error: future.set_exception(error)
        threading.Thread(target=call,daemon=True,name="pompeii-optional-language").start()
        return future

    def propose(self,text,recipient,view):
        if not isinstance(text,str) or not 1<=len(text.strip())<=2000:
            raise ValueError("Say between 1 and 2,000 characters")
        t=text.lower().strip()
        topic="supply" if any(w in t for w in ("supply","dispatch","news","heard","shortage")) else "role" if any(w in t for w in ("who are","your work","your life")) else "memory"
        reply=grounded_reply(view,topic)
        base={"recipient":recipient}
        quantity=next((v for word,v in NUMBERS.items() if re.search(r'\b'+word+r'\b',t)),None)
        digit=re.search(r'\b(\d{1,2})\b',t)
        quantity=int(digit.group()) if digit else quantity or 1
        if re.search(r'\b(buy|purchase)\b',t): action={**base,"action":"buy","quantity":quantity}
        elif any(w in t for w in ("sell information","sell my report","pay for my report","sell news")): action={**base,"action":"sell_information"}
        elif any(w in t for w in ("kept my service","complete service","do the service","household service")): action={**base,"action":"service"}
        elif any(w in t for w in ("patron","advance","backing","eight coins")): action={**base,"action":"patronage"}
        elif any(w in t for w in ("i promise","accept delivery","promise four","take the delivery")): action={**base,"action":"accept_delivery"}
        elif any(w in t for w in ("deliver","here is your flour","brought the flour")): action={**base,"action":"deliver"}
        elif any(w in t for w in ("inspect","check the dispatch","verify")): action={**base,"action":"inspect"}
        elif any(w in t for w in ("work","job","shift","wage")) and "who are" not in t: action={**base,"action":"work"}
        elif re.search(r'\b(supply|flour|grain)\b.*\b(disrupted|shortage|unavailable)\b',t) and not t.endswith('?'):
            action={**base,"action":"claim","value":"disrupted"}
        elif re.search(r'\b(supply|flour|grain)\b.*\b(available|plentiful)\b',t) and not t.endswith('?'):
            action={**base,"action":"claim","value":"available"}
        else: action={**base,"action":"talk","topic":topic}
        action=validate_action(action)
        protected=bool(re.search(r"\b(not|never|decline|cancel|later)\b|don't|do not",t) or
                       re.match(r"(what|who|why|when|how|where)\b",t))
        if protected:
            action={**base,"action":"talk","topic":topic}
        source="offline bounded parser"
        if self.provider and not protected:
            request={"schema_version":1,"text":text,"recipient":recipient,"character_view":view,
                "allowed_actions":sorted(ACTIONS),"instruction":"Return only {action: structured action}. Do not invent evidence or state; recipient must remain selected character."}
            for attempt in range(self.retries+1):
                if self._pending is not None and not self._pending.done(): break
                self.metrics["provider_calls"]+=1
                self._pending=self._submit(json.loads(json.dumps(request)))
                try:
                    result=self._pending.result(timeout=self.timeout_seconds)
                    if not isinstance(result,dict) or set(result)!={"action"}: raise ValueError("Invalid provider envelope")
                    candidate=validate_action(result["action"])
                    if candidate["recipient"]!=recipient: raise ValueError("Provider changed recipient")
                    action=candidate;source="optional provider proposal; grounded reply remains deterministic";break
                except (TimeoutError,ValueError,TypeError,KeyError,RuntimeError):
                    continue
                except Exception:
                    break
            else: source="offline fallback"
            if source.startswith("offline"):
                self.metrics["fallbacks"]+=1
        label={"accept_delivery":"Promise Felix four flour units before dusk","work":"Complete a paid shift (world time will pass)","buy":f"Buy {action.get('quantity',1)} flour unit(s) at the current price","deliver":"Deliver the four flour units you hold","inspect":"Pay one coin; inspection arrives in 15 world minutes","patronage":"Accept eight coins and owe two hours within three days","service":"Complete two hours of promised household service","sell_information":"Offer your retained dated report for payment","claim":"Assert flour supply is "+action.get("value",""),"talk":"Speak and remember the reply"}[action["action"]]
        transmission=label+"."
        if action["action"]=="claim": transmission+=" This is an assertion; it is not marked as a verified inspection."
        return {"reply":reply,"interpretations":[{"id":"0","label":label,"transmission":transmission,"action":action}],
                "clarification":"Review this interpretation before it changes the world.","language_source":source}


def execute(world,action):
    action=validate_action(action)
    kind=action["action"]
    if kind == "claim": return world.claim(action["recipient"],action["value"])
    if kind == "talk": return world.talk(action["recipient"],action.get("topic","memory"))
    return world.interact(kind,action["recipient"],action.get("quantity",1))
