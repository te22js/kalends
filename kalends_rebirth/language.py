"""Grounded, character-specific dialogue and reviewed action proposals for Rebirth."""
from __future__ import annotations

import copy
import re
from .ai import Cognition, ProposalError, allowed_evidence, check_evidence, evidence_records
from .cognitive_market import V2_ACTIONS, V2_FIXED_QUANTITIES, BUYERS

OLD_ACTIONS={"accept_delivery","work","buy","deliver","inspect","patronage","service","sell_information","claim","talk"}
NEW_TARGETS={
    "hear_dispute":{"Sabina"},"examine_receipt":{"Sabina"},"examine_tablet":{"Dama"},
    "verify_cart":{"Marcus"},"mediate":{"Marcus"},"support_market":{"Sabina"},
    "guarantee_household":{"Lucius"},"return_service":{"Lucius"},"reconcile":{"Sabina","Marcus","Lucius"},
    "accept_commission":{"Sabina","Marcus","Lucius"},"fulfill_commission":{"Sabina","Marcus","Lucius"},
    "decline_dispute":{"Sabina"},"reflect":{"Felix","Sabina","Marcus","Chreste","Dama","Lucius"},
}
ACTIONS=OLD_ACTIONS|set(NEW_TARGETS)
ACTIONS|=V2_ACTIONS
NEW_TARGETS.update({action:set(BUYERS) for action in V2_ACTIONS})
TOPICS={"memory","history","supply","news","role","dispute","goals","work","promise","documents","plans","relationship","market_receipt","household_tablet","loading_record","v2_counter_order"}
NUMBERS={"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10,"eleven":11,"twelve":12}
PERSON_IDS={"Felix","Sabina","Marcus","Chreste","Dama","Lucius"}

ACTION_SCHEMA={"type":"object","properties":{
    "action":{"type":"string","enum":sorted(ACTIONS)},"recipient":{"type":"string","enum":sorted(PERSON_IDS)},
    "quantity":{"type":["integer","null"]},"value":{"type":["string","null"]},"topic":{"type":["string","null"]},
    "actor_id":{"type":"string","enum":["Player"]},"evidence_ids":{"type":"array","items":{"type":"integer"}},
    "needs_confirmation":{"type":"boolean","enum":[True]}},
    "required":["action","recipient","quantity","value","topic","actor_id","evidence_ids","needs_confirmation"],"additionalProperties":False}
INTENT_SCHEMA={"type":"object","properties":{"action":ACTION_SCHEMA},"required":["action"],"additionalProperties":False}


def validate_action(action,recipient=None,view=None,*,enforce_choices=True):
    if not isinstance(action,dict) or set(action)-{"action","recipient","quantity","value","topic","actor_id","target_id","evidence_ids","needs_confirmation"}:
        raise ProposalError("Unexpected action fields")
    action={key:value for key,value in action.items() if value is not None}
    if action.get("actor_id","Player")!="Player" or action.get("needs_confirmation",True) is not True:
        raise ProposalError("Only confirmed player proposals are accepted")
    target=action.get("recipient",action.get("target_id"))
    if target not in PERSON_IDS or recipient is not None and target!=recipient or action.get("target_id",target)!=target:
        raise ProposalError("Action target is outside the selected conversation")
    kind=action.get("action")
    if kind not in ACTIONS:
        raise ProposalError("Unsupported action")
    if "topic" in action and kind!="talk" or "value" in action and kind!="claim":
        raise ProposalError("This action contains an irrelevant free-text field")
    if type(action.get("quantity",1)) is not int or not 1<=action.get("quantity",1)<=12:
        raise ProposalError("Quantity must be an integer from one through twelve")
    if kind in V2_FIXED_QUANTITIES and action.get("quantity",1)!=V2_FIXED_QUANTITIES[kind]:
        raise ProposalError("This counter action requires quantity "+str(V2_FIXED_QUANTITIES[kind]))
    if kind=="claim" and action.get("value") not in ("available","disrupted"):
        raise ProposalError("Supply assertions require a supported value")
    if kind=="talk" and action.get("topic","memory") not in TOPICS:
        raise ProposalError("Unsupported conversation topic")
    role_targets={"accept_delivery":{"Felix"},"deliver":{"Felix"},"work":{"Sabina","Chreste"},"buy":{"Felix","Marcus"},
                  "patronage":{"Lucius"},"service":{"Lucius"},"sell_information":{"Felix","Marcus","Sabina","Lucius"}}
    if target not in (NEW_TARGETS|role_targets).get(kind,PERSON_IDS):
        raise ProposalError("This character cannot perform that transaction")
    ids=action.get("evidence_ids",[])
    if view is not None:
        ids=check_evidence(ids,view)
        if enforce_choices and (kind in NEW_TARGETS or kind=="service") and isinstance(view.get("choices"),list):
            offered=[c.get("action",{}) for c in view["choices"] if c.get("enabled",True)]
            if not any(c.get("action")==kind and c.get("recipient",target)==target for c in offered):
                raise ProposalError("This opportunity is not currently offered")
    elif not isinstance(ids,list) or len(ids)>12 or any(type(i) is not int or i<0 for i in ids):
        raise ProposalError("Invalid evidence IDs")
    result={key:value for key,value in action.items() if key not in ("actor_id","target_id","evidence_ids","needs_confirmation")}
    result["recipient"]=target
    return {**result,"actor_id":"Player","evidence_ids":list(dict.fromkeys(ids)),"needs_confirmation":True}


def _topic(text):
    t=text.lower()
    if any(word in t for word in ("remember","history","last time","before","trust me","our past")):return "history"
    if any(word in t for word in ("who are","your life","about yourself")):return "role"
    if any(word in t for word in ("goal","plan","want","worry","need most")):return "goals"
    if any(word in t for word in ("receipt","counter.s order")):return "market_receipt"
    if any(word in t for word in ("tablet","household instructions","sealed message")):return "household_tablet"
    if any(word in t for word in ("loading account","loading record","carrier")):return "loading_record"
    if any(word in t for word in ("document","seal","evidence")):return "documents"
    if any(word in t for word in ("dispute","cart","argument","owed","priority","situation","happened")):return "dispute"
    if any(word in t for word in ("supply","dispatch","news","heard","shortage","flour")):return "supply"
    if any(word in t for word in ("work","job","wage","commission","business")):return "work"
    return "memory"


def _shared_experiences(view):
    records=[e for e in view.get("experiences",[]) if e.get("subject")=="relationship" or e.get("kind")=="episodic" and
             any(w in e.get("text","") for w in ("Aelia","You ","your "))]
    return sorted(records,key=lambda e:(e.get("tick",0),e.get("event_id",0)))[-2:]


def _grounded_reply(view,topic="memory"):
    """Short authored speech tied to supplied context; no archive or world object."""
    aliases={"history":"memory","news":"supply","plans":"goals","relationship":"memory"}
    wanted=aliases.get(topic,topic)
    topics=view.get("topics",[])
    # Scenario author provides evidence-scoped statements. Exact chosen text is
    # used, with IDs checked against this character's incoming context.
    match=next((item for item in topics if aliases.get(item.get("id"),item.get("id"))==wanted),None)
    if match and isinstance(match.get("text"),str):
        return {"text":match["text"],"evidence_ids":check_evidence(match.get("evidence_ids",[]),view),
                "epistemic_status":"Character's accessible account","topic":topic,"source":"authored-scoped"}
    name=view.get("speaker",view.get("id","Neighbour"))
    if wanted=="role":
        introductions={
            "Felix":"Felix. Bread keeps this street moving; a promise only helps if the flour arrives.",
            "Sabina":"Sabina. This is my counter. I need tomorrow's customers to have a reason to come back.",
            "Marcus":"Marcus. I arrange supplies. A cart, a promise, and a signed receipt are three different things.",
            "Chreste":"Chreste. I work in the fullery. Ask before taking anything; these goods are not mine to give.",
            "Dama":"Dama. I carry household messages. I can tell you what I was entrusted to carry, no more.",
            "Lucius":"Lucius. I answer for household supplies. Assistance carries obligations on both sides."}
        return {"text":introductions.get(name,"I can speak for my own work, not everyone else's."),"evidence_ids":[],
                "epistemic_status":"Authored fictional identity","topic":topic,"source":"authored-role"}
    if wanted=="supply":
        belief=view.get("beliefs",{}).get("grain.supply",{})
        if belief.get("value","unknown")=="unknown":
            text={"Felix":"I need flour, but need is not evidence. I haven't kept a reliable dispatch report.",
                  "Sabina":"I've no fresh dispatch report. If you're going to spend money on it, check the date.",
                  "Marcus":"I have no retained dispatch I can stand behind just now.",
                  "Dama":"I have no message about that which I can repeat with confidence."}.get(name,"I don't know. Someone closer to the dispatch may have a dated report.")
            return {"text":text,"evidence_ids":[],"epistemic_status":"Unknown to this character","topic":topic,"source":"authored-uncertainty"}
        verb="saw" if belief.get("direct") else "heard"
        return {"text":f"I {verb} that supply was {belief['value']}, dated world minute {belief.get('as_of')}. Check how old that is before relying on it.",
                "evidence_ids":check_evidence(belief.get("evidence_ids",[]),view),"epistemic_status":"Dated observation" if belief.get("direct") else "Dated hearsay","topic":topic,"source":"retained-belief"}
    if wanted=="goals":
        plan=view.get("plan",{})
        text=plan.get("short_term") or next(iter(view.get("goals",[])),"I need to settle today's work before making more promises.")
        return {"text":str(text),"evidence_ids":check_evidence(plan.get("evidence_ids",[]),view),"epistemic_status":"Current stated plan","topic":topic,"source":"scoped-plan"}
    shared=_shared_experiences(view)
    if shared:
        latest=shared[-1]
        return {"text":latest["text"],"evidence_ids":[latest["event_id"]],"epistemic_status":"Retained shared experience","topic":topic,"source":"retained-memory"}
    greeting=view.get("greeting",{})
    if isinstance(greeting,dict) and greeting.get("text"):
        return {"text":greeting["text"],"evidence_ids":check_evidence(greeting.get("evidence_ids",[]),view),
                "epistemic_status":"Character's current account","topic":topic,"source":"authored-scoped"}
    text={"Felix":"We haven't settled any dealings I remember. Tell me what you're offering, and when it will arrive.",
          "Sabina":"Start with what you can actually do. A little help at the right moment matters here.",
          "Marcus":"What are you asking for: a price, a report, or my word? Those have different costs.",
          "Chreste":"I remember no dealings between us. If you're here to help, be clear about whose work you mean.",
          "Dama":"I have no shared business with you in my memory. What is it you need?",
          "Lucius":"I have no settled arrangement with you in my retained account. Say what you want, and what you can undertake."}.get(name,"What do you need?")
    return {"text":text,"evidence_ids":[],"epistemic_status":"No retained shared episode","topic":topic,"source":"authored-role"}


def disclosure_context(view):
    """Dialogue gets what the speaker is willing to disclose, not every known fact."""
    permitted=set(view.get("disclosure_evidence_ids",allowed_evidence(view)))
    result={key:copy.deepcopy(view[key]) for key in ("id","speaker","minute","location","voice","dialogue_version") if key in view}
    result["disclosure_evidence_ids"]=sorted(permitted)
    result["experiences"]=[copy.deepcopy(e) for e in view.get("experiences",[]) if e.get("event_id") in permitted]
    result["topics"]=[copy.deepcopy(t) for t in view.get("topics",[]) if set(t.get("evidence_ids",[]))<=permitted]
    greeting=view.get("greeting",{})
    if set(greeting.get("evidence_ids",[]))<=permitted:result["greeting"]=copy.deepcopy(greeting)
    belief=view.get("beliefs",{}).get("grain.supply",{})
    if set(belief.get("evidence_ids",[]))<=permitted:result["beliefs"]={"grain.supply":copy.deepcopy(belief)}
    plan=view.get("plan",{})
    if set(plan.get("evidence_ids",[]))<=permitted:result["plan"]=copy.deepcopy(plan)
    return result


def grounded_reply(view,topic="memory"):
    reply=_grounded_reply(view,topic)
    permitted=set(view.get("disclosure_evidence_ids",allowed_evidence(view)))
    if not set(reply["evidence_ids"])<=permitted:
        return {"text":"I cannot open that account in this conversation. Ask what I can share, or arrange the required check.",
            "evidence_ids":[],"epistemic_status":"Disclosure withheld","topic":topic,"source":"authored-permission"}
    return reply


FLAVOR={"plain":"","cautious":"I would rather be precise.","direct":"Let us be clear about this.","warm":"Take a moment. We can talk."}
DIALOGUE_SCHEMA={"type":"object","properties":{"flavor_id":{"type":"string","enum":list(FLAVOR)},"topic_id":{"type":"string"},
    "evidence_ids":{"type":"array","items":{"type":"integer"}}},"required":["flavor_id","topic_id","evidence_ids"],"additionalProperties":False}


def validate_dialogue(output,view):
    if not isinstance(output,dict) or set(output)!={"flavor_id","topic_id","evidence_ids"}:
        raise ProposalError("Dialogue must select grounded clauses, not unrestricted facts")
    if output["flavor_id"] not in FLAVOR or output["topic_id"] not in TOPICS:
        raise ProposalError("Unsupported dialogue selection")
    reply=grounded_reply(view,output["topic_id"])
    ids=check_evidence(output["evidence_ids"],view)
    if set(ids)!=set(reply["evidence_ids"]):
        raise ProposalError("Dialogue citations do not match the selected grounded clause")
    return {"flavor_id":output["flavor_id"],"topic_id":output["topic_id"],"evidence_ids":ids}


def realize_dialogue(output,view):
    output=validate_dialogue(output,view)
    reply=grounded_reply(view,output["topic_id"])
    flavor=FLAVOR[output["flavor_id"]]
    if flavor: reply["text"]=flavor+" "+reply["text"]
    return reply


def _quantity(t):
    digits=re.search(r"\b(\d{1,3})\b",t)
    if digits:return int(digits.group())
    return next((number for word,number in NUMBERS.items() if re.search(r"\b"+word+r"\b",t)),1)


def offline_intent(text,recipient,view):
    t=text.lower().strip();topic=_topic(t);base={"recipient":recipient}
    protected=bool(re.search(r"\b(not|never|cancel|later)\b|don't|do not",t))
    question=bool(re.match(r"(what|who|why|when|how|where)\b",t))
    if protected or question:return {**base,"action":"talk","topic":topic}
    # The exact visible counter-order wording is also a stable typed command.
    # Copy its disclosed quantity before broader legacy terms such as 'advance'.
    normalize=lambda value:re.sub(r"[^\w\s]","",value.casefold()).strip()
    for choice in view.get("choices",[]):
        candidate=choice.get("action",{})
        if candidate.get("action") in V2_ACTIONS and choice.get("enabled",True) and normalize(t)==normalize(choice.get("label","")):
            return copy.deepcopy(candidate)
    offered={c.get("action",{}).get("action") for c in view.get("choices",[]) if c.get("enabled",True)}
    service_request=re.search(r"\b(return|keep|complete|finish|fulfill|fulfil)\b.*\bservice\b|\bhousehold service\b",t)
    if recipient=="Lucius" and service_request:
        # Migrated household-service and new Rebirth service are distinct durable
        # obligations. Choose the actual enabled offer rather than inferring one
        # from affiliation or routing every old promise to the new chapter.
        for kind in ("return_service","service"):
            if kind in offered:return {**base,"action":kind}
        return {**base,"action":"talk","topic":topic}
    # Match new dramatic actions before broad legacy keywords such as work/news.
    patterns=[
        ("decline_dispute",r"\b(decline|leave it|stay out|ignore the dispute)\b"),
        ("examine_receipt",r"\b(receipt|seller.s paper|counter.s document)\b"),
        ("examine_tablet",r"\b(tablet|household document|sealed message)\b"),
        ("verify_cart",r"\b(verify|inspect|check|investigate|open)\b.*\b(cart|shipment|delivery|dispatch|loading account|loading record)\b"),
        ("reconcile",r"\b(reconcile|repair|replace the delivery|make amends|rebuild our arrangement)\b"),
        ("mediate",r"\b(mediate|negotiate|bring the accounts together|compare the documents)\b"),
        ("support_market",r"\b(support the market|support sabina|fund the market|pool|pay the deposit|help the counter)\b"),
        ("guarantee_household",r"\b(guarantee|household priority|household backing|back the household)\b"),
        ("fulfill_commission",r"\b(fulfill|finish|complete|settle|deliver)\b.*\b(commission|order|contract)\b"),
        ("accept_commission",r"\b(commission|new order|commercial agreement|take the contract)\b"),
        ("hear_dispute",r"\b(tell me|hear|explain|investigate)\b.*\b(dispute|argument|situation)\b"),
        ("reflect",r"\b(reflect|think it over|remember what matters)\b"),
    ]
    for kind,pattern in patterns:
        if re.search(pattern,t) and recipient in NEW_TARGETS[kind] and (not view.get("choices") or kind in offered):
            return {**base,"action":kind}
    if re.search(r"\b(buy|purchase)\b",t):return {**base,"action":"buy","quantity":_quantity(t)}
    if any(w in t for w in ("sell information","sell my report","sell news","pay for my report")):return {**base,"action":"sell_information"}
    if any(w in t for w in ("advance","patronage","backing")):return {**base,"action":"patronage"}
    if any(w in t for w in ("i promise","accept delivery","take the delivery")):return {**base,"action":"accept_delivery"}
    if any(w in t for w in ("brought the flour","deliver the flour","here is your flour")):return {**base,"action":"deliver"}
    if any(w in t for w in ("inspect","verification")):return {**base,"action":"inspect"}
    if any(w in t for w in ("paid shift","work","job","wage")):return {**base,"action":"work"}
    if re.search(r"\b(supply|flour|grain)\b.*\b(disrupted|shortage|unavailable)\b",t):return {**base,"action":"claim","value":"disrupted"}
    if re.search(r"\b(supply|flour|grain)\b.*\b(available|plentiful)\b",t):return {**base,"action":"claim","value":"available"}
    return {**base,"action":"talk","topic":topic}


def action_label(action,view):
    def parameters(candidate):
        kind=candidate.get("action")
        if kind in ("buy","v2_cash_order","v2_deliver_order","v2_replace_order"):
            return {"quantity":candidate.get("quantity",1)}
        if kind=="claim":return {"value":candidate.get("value")}
        if kind=="talk":
            topic=candidate.get("topic","memory")
            return {"topic":{"history":"memory","relationship":"memory","promise":"memory","supply":"news","plans":"goals"}.get(topic,topic)}
        return {}
    for choice in view.get("choices",[]):
        candidate=choice.get("action",{})
        if candidate.get("action")==action["action"] and candidate.get("recipient",action["recipient"])==action["recipient"] and parameters(candidate)==parameters(action):
            return choice.get("label",action["action"].replace("_"," ").capitalize()),choice.get("description",choice.get("consequence",""))
    labels={"accept_delivery":"Promise Felix four flour units before dusk","work":"Take a paid shift; world time will pass",
        "buy":f"Buy {action.get('quantity',1)} flour {'unit' if action.get('quantity',1)==1 else 'units'} at the current price","deliver":"Deliver the four flour units you hold",
        "inspect":"Pay one coin; dispatch inspection arrives in fifteen world minutes","patronage":"Accept eight coins and owe two hours of household service",
        "service":"Complete the promised household service","sell_information":"Offer your retained dated report for payment",
        "claim":"Assert that flour supply is "+action.get("value",""),"talk":"Say this and hear their answer"}
    label=labels.get(action["action"],action["action"].replace("_"," ").capitalize())
    return label,"The world checks location, resources and current availability when you confirm."


class Language:
    def __init__(self,cognition=None):
        self.cognition=cognition or Cognition.from_env()
    @property
    def metrics(self):return self.cognition.debug()["metrics"]
    def propose(self,text,recipient,view):
        if not isinstance(text,str) or not 1<=len(text.strip())<=2000:
            raise ProposalError("Say between one and 2,000 characters")
        if recipient not in PERSON_IDS or view.get("id",view.get("speaker"))!=recipient:
            raise ProposalError("Select the character whose context is supplied")
        view=copy.deepcopy(view)
        try:offline=validate_action(offline_intent(text,recipient,view),recipient,view)
        except ProposalError:
            offline=validate_action({"action":"talk","recipient":recipient,"topic":_topic(text)},recipient,view)
        def validate_intent(output,context):
            if not isinstance(output,dict) or set(output)!={"action"}:raise ProposalError("Invalid intent envelope")
            return {"action":validate_action(output["action"],recipient,context)}
        protected=bool(re.search(r"\b(not|never|cancel|later)\b|don't|do not",text.lower()) or re.match(r"(what|who|why|when|how|where)\b",text.lower()))
        if protected:
            # A model cannot override a refusal/question into a transaction.
            result={"output":{"action":offline},"receipt":{"kind":"protected_offline","fallback":False,"latency_seconds":0,"estimated_cost_usd":0}}
        else:
            result=self.cognition.run("intent",view,{"text":text,"recipient":recipient},fallback={"action":offline},validator=validate_intent,schema=INTENT_SCHEMA)
        action=result["output"]["action"]
        reply=grounded_reply(view,action.get("topic",_topic(text)))
        label,description=action_label(action,view)
        return {"reply":reply,"interpretations":[{"id":"0","label":label,"transmission":description,"action":action}],
            "clarification":"Review the choice. Your word will become part of the city only when you confirm.",
            "language_source":result["receipt"]["kind"],"ai_receipt":result["receipt"]}

    def dialogue(self,view,topic="memory"):
        view=disclosure_context(view)
        reply=grounded_reply(view,topic)
        fallback={"flavor_id":"plain","topic_id":topic,"evidence_ids":reply["evidence_ids"]}
        result=self.cognition.run("dialogue",view,{"topic":topic},fallback=fallback,validator=validate_dialogue,schema=DIALOGUE_SCHEMA)
        return {"reply":realize_dialogue(result["output"],view),"receipt":result["receipt"]}

    def plan(self,view):
        offered=[c for c in view.get("plan_options",[]) if c.get("enabled",True)]
        ids=[str(c["id"]) for c in offered]
        fallback={"choice_id":ids[0] if ids else "wait","evidence_ids":[]}
        schema={"type":"object","properties":{"choice_id":{"type":"string","enum":ids+["wait"]},"evidence_ids":{"type":"array","items":{"type":"integer"}}},"required":["choice_id","evidence_ids"],"additionalProperties":False}
        def validate(output,context):
            if not isinstance(output,dict) or set(output)!={"choice_id","evidence_ids"} or output["choice_id"] not in ids+["wait"]:
                raise ProposalError("Plan must select an offered choice or wait")
            return {"choice_id":output["choice_id"],"evidence_ids":check_evidence(output["evidence_ids"],context)}
        return self.cognition.run("planning",view,{"available_choice_ids":ids},fallback=fallback,validator=validate,schema=schema)

    def reflect(self,view):
        records=evidence_records(view)
        selected=list(records)[-8:]
        fallback={"memories":[{"evidence_id":i,"text":records[i][0]} for i in selected]}
        schema={"type":"object","properties":{"memories":{"type":"array","items":{"type":"object","properties":{"evidence_id":{"type":"integer"},"text":{"type":"string"}},"required":["evidence_id","text"],"additionalProperties":False}}},"required":["memories"],"additionalProperties":False}
        def validate(output,context):
            if not isinstance(output,dict) or set(output)!={"memories"} or not isinstance(output["memories"],list) or len(output["memories"])>8:
                raise ProposalError("Reflection is a bounded list of supported memory clauses")
            allowed=evidence_records(context);seen=set()
            for memory in output["memories"]:
                if not isinstance(memory,dict) or set(memory)!={"evidence_id","text"} or memory["evidence_id"] not in allowed or memory["text"] not in allowed[memory["evidence_id"]] or memory["evidence_id"] in seen:
                    raise ProposalError("Reflection invented or duplicated an experience")
                seen.add(memory["evidence_id"])
            return copy.deepcopy(output)
        return self.cognition.run("reflection",view,{"maximum_memories":8},fallback=fallback,validator=validate,schema=schema)

    def montage(self,view):
        ids=sorted(allowed_evidence(view))[-8:]
        fallback={"event_ids":ids}
        schema={"type":"object","properties":{"event_ids":{"type":"array","items":{"type":"integer"}}},"required":["event_ids"],"additionalProperties":False}
        def validate(output,context):
            if not isinstance(output,dict) or set(output)!={"event_ids"}:raise ProposalError("Invalid montage selection")
            return {"event_ids":check_evidence(output["event_ids"],context,maximum=8)}
        return self.cognition.run("montage",view,{"maximum_events":8},fallback=fallback,validator=validate,schema=schema)

    def content_draft(self,view):
        fallback={"draft":True,"archetype":"commercial_dispute","source_ids":[]}
        schema={"type":"object","properties":{"draft":{"type":"boolean","enum":[True]},"archetype":{"type":"string","enum":["commercial_dispute","household_obligation","work_commission"]},"source_ids":{"type":"array","items":{"type":"string"}}},"required":["draft","archetype","source_ids"],"additionalProperties":False}
        def validate(output,context):
            if not isinstance(output,dict) or set(output)!={"draft","archetype","source_ids"} or output["draft"] is not True or output["archetype"] not in ("commercial_dispute","household_obligation","work_commission") or not isinstance(output["source_ids"],list) or not set(output["source_ids"])<=set(context.get("historical_source_ids",[])):
                raise ProposalError("Content draft is outside the authored sandbox")
            return copy.deepcopy(output)
        return self.cognition.run("world_content",view,{"draft_only":True},fallback=fallback,validator=validate,schema=schema)


ProposalLanguage=Language


def execute(world,action):
    recipient=action.get("recipient",action.get("target_id"))
    world.require_near(recipient)
    view=world.context(recipient) if hasattr(world,"context") else world.private_view(recipient)
    action=validate_action(action,recipient,view)
    kind=action["action"]
    if kind=="claim":return world.claim(recipient,action["value"])
    if kind=="talk":
        topic=action.get("topic","memory")
        topic={"plans":"goals","relationship":"memory","promise":"memory"}.get(topic,topic)
        return world.talk(recipient,topic)
    return world.interact(kind,recipient,action.get("quantity",1))
