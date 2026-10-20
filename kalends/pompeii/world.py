"""A playable district composed from Kalends' existing ledger and economy.

All physical/account/institutional effects are events. EventClock schedules
dated opportunities; no off-screen decision reads the omniscient archive.
"""
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
import json
import math

from ..events import Ledger
from ..world import WorldState, apply_event
from ..memory.base import Experience
from ..genesis.simulation import GenesisEconomy
from ..rng import det_rand, det_randint
from .district import PompeiiConfig, MAP, LOCATIONS, PEOPLE, center
from .temporal import EventClock


class PompeiiWorld:
    def __init__(self, config=None, seed=None):
        self.config = config or PompeiiConfig(seed=seed if seed is not None else 79)
        self.clock = EventClock(now=0)
        self.ledger, self.economy = Ledger(), GenesisEconomy()
        self.agent_ids = list(PEOPLE)
        self.state = WorldState(agent_locations={a:p["location"] for a,p in PEOPLE.items()} | {"Player":"street"})
        self.positions = {a:self._actor_position(a,p["location"]) for a,p in PEOPLE.items()} | {"Player":(650,415)}
        self.memories = {a:[] for a in self.agent_ids + ["Player"]}
        self.consolidated = {a:[] for a in self.memories}
        self.flags, self.decisions, self.information_sales = {}, [], []
        self.dispatch_records = []
        self.disclosed = set()
        self.witnessed = set()
        self.player_path, self.last_advance, self.montage = [], None, None
        self._last_account = {}
        self._emit("city_initialized", "Morning opens on the Via dell'Abbondanza", actors=("Player",),
            cash={a:float(p["cash"]) for a,p in PEOPLE.items()} | {"Player":6.0},
            inventory={a:p["inventory"] for a,p in PEOPLE.items()} | {"Player":0},
            commitments={a:[] for a in self.memories}, market_stock_delta=14, price=2.0,
            flags={"reputation":0,"quest":"unaccepted","affiliation":"independent","bread":0})
        self._emit("arrival", "You arrive as Aelia, a freedwoman earning her place between households and shops.",
                   actors=("Player",), scope="private", fiction=True)
        self._emit("supply", "The first flour cart is inspected at the street counter", actors=("Marcus",),
                   prop=["grain","supply"], value="available", scope="private")
        self._observe("Marcus", "available", self.ledger.events[-1].event_id, 0)
        self._initial_cash = dict(self.economy.cash)
        self._initial_inventory = dict(self.economy.inventory)
        self.clock.schedule(12,"routine",{"agent":"Dama","location":"street","day":0})
        self.clock.schedule(25,"gossip",{"speaker":"Marcus","listener":"Dama"})
        self.clock.schedule(65,"procure",{"agent":"Marcus"})
        self.clock.schedule(90,"routine",{"agent":"Dama","location":"bakery","day":0})
        self.clock.schedule(100,"gossip",{"speaker":"Dama","listener":"Felix"})
        self.clock.schedule(240,"supply",{"day":0,"phase":"late"})
        self.clock.schedule(600,"settle",{"day":0})
        self.clock.schedule(1440,"dawn",{"day":1})
        for agent in ("Felix","Sabina","Lucius"):
            self.clock.schedule(180,"procure",{"agent":agent})

    @property
    def minute(self):
        return self.clock.now

    @property
    def tick(self):
        return self.minute

    @staticmethod
    def _actor_position(agent,location):
        x,y=center(location)
        offset={"Dama":(-60,-30),"Lucius":(45,5)}.get(agent,(0,0))
        return x+offset[0],y+offset[1]

    def _emit(self, category, title, actors=(), location=None, scope="public", parents=(), etype="state_change", **payload):
        location = location or self.state.agent_locations.get(actors[0] if actors else "Player", "street")
        parents = sorted({p for p in parents if type(p) is int and 0 <= p < len(self.ledger)})
        event = self.ledger.append(self.minute, etype, location, tuple(actors),
            {"category":category,"title":title,"parents":parents,**payload}, scope)
        apply_event(self.state,event)
        self.economy.apply(event)
        for change in payload.get("relationship_updates",[]):
            self.state.trust[(change["listener"],change["speaker"])] = change["value"]
        if "position" in payload:
            self.positions[actors[0]] = tuple(payload["position"])
        self.flags.update(payload.get("flags",{}))
        if category == "supply":
            self.dispatch_records.append({"minute":self.minute,"value":payload["value"],"event_id":event.event_id})
        for a in payload.get("cash_delta",{}) | payload.get("inventory_delta",{}):
            self._last_account[a] = event.event_id
        personally_observed = "Player" in actors and (category != "relationship" or self.state.agent_locations["Player"] == location)
        if personally_observed or scope == "public" and self.state.agent_locations["Player"] == location:
            self.witnessed.add(event.event_id)
            self._remember("Player", Experience(self.minute,"episodic",None,None,None,None,self.minute,True,event.event_id,title))
        if "Player" in actors and category in ("work_complete","trade","promise","patronage","conversation"):
            for actor in actors:
                if actor != "Player":
                    self._remember(actor,Experience(self.minute,"episodic",None,None,None,None,self.minute,True,event.event_id,title),
                                   significant=category in ("work_complete","patronage"))
        return event

    def _remember(self, agent, experience, significant=False):
        self.memories[agent].append(experience)
        del self.memories[agent][:-self.config.memory_capacity]
        if significant:
            # Bounded literal consolidation, not a hidden autobiographical archive.
            self.consolidated[agent].append(experience)
            self.consolidated[agent] = self.consolidated[agent][-8:]

    def remembered(self, agent):
        if agent not in self.memories:
            raise ValueError("unknown character")
        return list({e.event_id:e for e in self.consolidated[agent] + self.memories[agent]}.values())

    def _observe(self, agent, value, event_id, as_of):
        self._remember(agent, Experience(self.minute,"observed","grain","supply",value,None,as_of,True,event_id,
            "I inspected flour supply: %s, dated minute %s." % (value,as_of),"observed",event_id,agent))

    def knowledge(self, agent):
        records = [e for e in self.remembered(agent) if e.subject == "grain" and e.predicate == "supply" and e.accepted]
        if not records:
            return {"value":"unknown","as_of":None,"evidence_ids":[],"confidence":0}
        chosen = max(records,key=lambda e:(e.as_of,e.tick,e.event_id))
        support = [e for e in records if e.as_of == chosen.as_of and e.value == chosen.value]
        # Repeating one observer's report does not create independent witnesses.
        roots = {e.claimed_origin_observer or e.source_agent or agent for e in support}
        direct = chosen.kind == "observed"
        confidence = (1 if direct else min(.85,.4+.15*len(roots))) * (.65 if self.minute-chosen.as_of>360 else 1)
        return {"value":chosen.value,"as_of":chosen.as_of,"evidence_ids":[e.event_id for e in support],
                "confidence":confidence,"roots":len(roots),"direct":direct}

    def _hear(self, listener, speaker, value, as_of, root, parents=(), observer=None):
        prior = self.knowledge(listener)
        accepted = self.state.trust.get((listener,speaker),.6) >= .3 and (prior["as_of"] is None or as_of > prior["as_of"] or
                    as_of == prior["as_of"] and value == prior["value"])
        event = self._emit("report",f"{speaker} tells {listener} that flour supply is {value} (observed at minute {as_of})",
            actors=(speaker,listener),scope="private",parents=parents,etype="tell",speaker=speaker,listener=listener,
            prop=["grain","supply"],value=value,as_of=as_of,root_event=root,root_observer=observer or speaker,accepted=accepted)
        self._remember(listener,Experience(self.minute,"told","grain","supply",value,speaker,as_of,accepted,
            event.event_id,event.payload["title"],"told",root,observer or speaker))
        return event

    def private_view(self, agent):
        if agent not in self.memories:
            raise ValueError("unknown character")
        role = PEOPLE[agent]["role"] if agent != "Player" else "freedwoman and errand worker"
        goals=[PEOPLE[agent]["goal"]] if agent in PEOPLE else ["Earn a dependable place without giving away every choice"]
        if agent in PEOPLE and self.economy.cash[agent]<5:
            goals.insert(0,"Protect the few working coins I have left; revise buying plans to what I can afford")
        if self.state.trust.get((agent,"Player"),.6)<.35:
            goals.insert(0,"Avoid trading on Aelia's unsupported word; seek independent verification")
        return {"id":agent,"role":role,"minute":self.minute,"location":self.state.agent_locations[agent],
            "cash":self.economy.cash[agent],"inventory":self.economy.inventory[agent],
            "commitments":copy.deepcopy(self.economy.commitments[agent]),"beliefs":{"grain.supply":self.knowledge(agent)},
            "experiences":[asdict(e) for e in self.remembered(agent)],"trust_player":self.state.trust.get((agent,"Player"),.6),
            "goals":goals,
            "social_position":PEOPLE[agent]["social_position"] if agent in PEOPLE else "Fictional freedwoman with ongoing social obligations",
            "consolidated_count":len(self.consolidated[agent])}

    def _near(self, agent):
        public = ("street", "water", "forum_access")
        return self.state.agent_locations[agent] == self.state.agent_locations["Player"] not in public or (
            self.state.agent_locations[agent] in public and self.state.agent_locations["Player"] in public and
            math.dist(self.positions[agent],self.positions["Player"]) <= 160)

    def require_near(self, agent):
        if agent not in self.agent_ids or not self._near(agent):
            raise ValueError("Walk to this character's location before interacting.")

    def move(self, x=None, y=None, location=None):
        start = self.positions["Player"]
        current = self.state.agent_locations["Player"]
        if location is not None:
            if location == "street":
                place = None
                target = (start[0],415)
            else:
                place = next((p for p in LOCATIONS if p["id"] == location),None)
                if not place:
                    raise ValueError("unknown destination")
                target = (place["x"]+place["w"]*.5,place["y"]+place["h"]*.85) if place["interior"] else (place["door"]["x"],place["door"]["y"])
        else:
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in (x,y)):
                raise ValueError("movement needs finite coordinates")
            target = (max(20,min(1580,float(x))),max(20,min(1080,float(y))))
            place = next((p for p in LOCATIONS if p["id"] == current and p["interior"] and
                          p["x"]+15 <= x <= p["x"]+p["w"]-15 and p["y"]+15 <= y <= p["y"]+p["h"]-15),None)
            walkable = any(r["x"] <= x <= r["x"]+r["w"] and r["y"] <= y <= r["y"]+r["h"] for r in MAP["streets"])
            if not walkable and place is None:
                raise ValueError("Use the street or enter through a marked doorway.")
            location = current if place else "street"
        points = [start]
        old_place = next((p for p in LOCATIONS if p["id"] == current and p["interior"]),None)
        if old_place and current != location:
            points += [(old_place["door"]["x"],old_place["door"]["y"]),(old_place["door"]["x"],415)]
        if place and place["interior"] and current != location:
            points += [(start[0] if not old_place else old_place["door"]["x"],415),(place["door"]["x"],415),
                       (place["door"]["x"],place["door"]["y"]),target]
        elif current != location or location == "street":
            points += [(points[-1][0],415),(target[0],415),target]
        else:
            points += [target]
        distance = sum(math.dist(a,b) for a,b in zip(points,points[1:]))
        self.advance(max(1,math.ceil(distance/90)),"live")
        event = self._emit("player_move", "You enter %s" % (place["name"] if place else "the street"), actors=("Player",),
            etype="move",to=location,position=target,path=points)
        self.player_path = [list(p) for p in points]
        # Local public records become observations on arrival, never by teleporting private knowledge.
        if location in ("street","water","forum_access"):
            self._remember("Player",Experience(self.minute,"observed","grain","price",str(self.economy.price),None,self.minute,True,
                event.event_id,"I read the street's posted flour price: %.1f coins." % self.economy.price))
        return self.event_dict(event)

    def advance(self, minutes=1, mode="compress"):
        if mode not in ("live","compress","montage","skip","naive"):
            raise ValueError("unknown time mode")
        if minutes == "next":
            target = self.clock.peek() or self.minute+60
            minutes = max(1,target-self.minute)
        if type(minutes) is not int or not 1 <= minutes <= 60*1440:
            raise ValueError("advance must be 1 minute through 60 days")
        start, start_id = self.minute,len(self.ledger)
        before_cash = self.economy.cash["Player"]
        target = min(self.config.horizon_days*1440,self.minute+minutes)
        if target <= self.minute:
            raise ValueError("this world's configured horizon has been reached")
        computational = mode if mode in ("live","naive") else "compress"
        stats = self.clock.advance(target,self.on_task,mode=computational)
        self._emit("time_advanced", "World time advances by %s minutes" % (target-start),actors=("Player",),scope="private",
                   elapsed=target-start,time_mode=mode)
        visible = [self.event_dict(e) for e in self.ledger.events[start_id:] if self._visible(e) and
                   e.payload["category"] in ("promise_settled","relationship","opportunity","work_complete","information_sale","report","bread_ready")]
        self.montage = {"from_minute":start,"to_minute":target,"elapsed_minutes":target-start,
            "title":"The days between", "events":visible[-8:],"cash_change":self.economy.cash["Player"]-before_cash,
            "summary":"%s days and %s hours passed. These are recorded events involving you, not an invented narration." %
                      ((target-start)//1440,((target-start)%1440)//60)} if mode in ("montage","skip") or minutes>=1440 else None
        self.last_advance = {**stats,"mode":mode,"from_minute":start,"to_minute":target,
                             "algorithm":"minute reference" if computational == "live" else "naive coarse execution" if computational == "naive" else "exact discrete-event dispatch"}
        return self.last_advance

    def on_task(self, task):
        kind,data = task["kind"],task["data"]
        day = data.get("day",self.minute//1440)
        if kind == "routine":
            a,location = data["agent"],data["location"]
            if self.state.agent_locations[a] != location:
                self._emit("routine",f"{a} goes to {location} for their duties",actors=(a,),etype="move",to=location,position=self._actor_position(a,location))
            if a == "Dama" and self.config.communication:
                others = [b for b in self.agent_ids if b != a and self.state.agent_locations[b] == location]
                for b in others[:2]: self.clock.schedule(self.minute+4,"gossip",{"speaker":a,"listener":b})
        elif kind == "gossip":
            if not self.config.communication: return
            a,b = data["speaker"],data["listener"]
            if self.state.agent_locations[a] != self.state.agent_locations[b]: return
            knowledge = self.knowledge(a)
            if knowledge["value"] == "unknown" or not knowledge["evidence_ids"]: return
            exp = next(e for e in self.remembered(a) if e.event_id == knowledge["evidence_ids"][-1])
            self._hear(b,a,exp.value,exp.as_of,exp.claimed_origin_event or exp.event_id,
                       parents=(exp.event_id,),observer=exp.claimed_origin_observer or a)
        elif kind in ("supply","dawn"):
            if kind == "dawn":
                if self.flags.get("quest") in ("fulfilled","missed"):
                    self._emit("opportunity","A new day's flour order can be negotiated with Felix",actors=("Player",),scope="private",
                        flags={"quest":"unaccepted"})
                # Only registered event times change policies; ordinary empty minutes are quiescent.
                self.clock.schedule(self.minute+1440,"dawn",{"day":day+1})
                self.clock.schedule(self.minute+240,"supply",{"day":day,"phase":"late"})
                self.clock.schedule(self.minute+600,"settle",{"day":day})
                for a in self.agent_ids:
                    self.clock.schedule(self.minute+det_randint(35,110,self.config.seed,"depart",day,a),"routine",
                                        {"agent":a,"location":PEOPLE[a]["location"],"day":day})
                for a in ("Felix","Sabina","Marcus","Lucius"):
                    self.clock.schedule(self.minute+180,"procure",{"agent":a})
                self.clock.schedule(self.minute+120,"routine",{"agent":"Dama","location":"street","day":day})
                self.clock.schedule(self.minute+150,"gossip",{"speaker":"Marcus","listener":"Dama"})
                self.clock.schedule(self.minute+210,"routine",{"agent":"Dama","location":"bakery","day":day})
            available = det_rand(self.config.seed,"pompeii-flour",day,data.get("phase","dawn")) > .32
            value = "available" if available else "disrupted"
            amount = (14 if available else 5) if kind == "dawn" else 0
            ev = self._emit("supply","A flour cart brings %s fresh units" % amount if amount else "A new dispatch reaches the flour trader",
                actors=("Marcus",),scope="private",prop=["grain","supply"],value=value,market_stock_delta=amount,
                price=2.0 if available else 3.5)
            self._observe("Marcus",value,ev.event_id,self.minute)
            if kind == "dawn" and day%7 == 0:
                self._emit("opportunity","A week of dealings brings another chance to earn household trust",actors=("Player",),scope="private",
                           flags={"weekly_opportunity":day})
        elif kind == "procure":
            a = data["agent"]
            knowledge = self.knowledge(a)
            deficit = max(0,(5 if a == "Felix" else 3 if a == "Lucius" else 2)-self.economy.inventory[a])
            caution = PEOPLE[a]["caution"]
            if a == "Marcus": deficit=max(0,8-self.economy.inventory[a])
            uncertain = knowledge["value"] == "unknown" or knowledge["confidence"] < caution
            choice = "wait" if not deficit else "inspect" if self.config.information_policy == "cautious" and uncertain and a in ("Felix","Lucius") else \
                     "defer" if knowledge["value"] == "disrupted" and not uncertain and caution >= .7 else "buy"
            event = self._emit("decision",f"{a} chooses to {choice} using their own records",actors=(a,),scope="private",
                               parents=knowledge["evidence_ids"],choice=choice,predicted_value=knowledge["value"])
            self.decisions.append({"minute":self.minute,"agent":a,"action":choice,"value":knowledge["value"],"event_id":event.event_id})
            if choice == "inspect" and self.economy.cash[a]>=1:
                self._book_inspection(a,event.event_id)
                self.clock.schedule(self.minute+20,"purchase",{"agent":a,"quantity":deficit,"decision":event.event_id})
            elif choice == "buy" and deficit:
                self._purchase(a,deficit,event.event_id)
            elif choice == "defer" and not data.get("retry"):
                self.clock.schedule(self.minute+90,"procure",{"agent":a,"retry":1})
        elif kind == "purchase":
            self._purchase(data["agent"],data["quantity"],data.get("decision"))
        elif kind == "inspection":
            a = data["agent"]
            value = self.state.facts["grain.supply"]
            event = self._emit("inspection",f"{a} inspects the current flour dispatch: {value}",actors=(a,),scope="private",
                parents=(data.get("booking"),),value=value,as_of=self.minute)
            self._observe(a,value,event.event_id,self.minute)
            # Assess only retained reports; old disagreement is explicitly not proof of a lie.
            for exp in [e for e in self.remembered(a) if e.kind == "told" and e.source_agent == "Player"][-1:]:
                if any(e.subject == "relationship" and e.claimed_origin_event == exp.event_id for e in self.remembered(a)):
                    continue
                dated = [r for r in self.dispatch_records if r["minute"] <= exp.as_of] if self.minute-exp.as_of <=1440 else []
                record = max(dated,key=lambda r:r["minute"]) if dated else None
                check = None
                if record:
                    check=self._emit("dated_inspection",f"{a} reads the dispatch dated to your report",actors=(a,),scope="private",
                        parents=(record["event_id"],event.event_id),record_as_of=exp.as_of,recorded_value=record["value"])
                    self._remember(a,Experience(self.minute,"observed","dispatch_log",f"supply_at_{exp.as_of}",record["value"],None,exp.as_of,
                        True,check.event_id,f"The dispatch record for minute {exp.as_of} says {record['value']}."))
                outcome = "historically_unverified" if not record else "contradicted" if record["value"] != exp.value else "truthful_outdated" if exp.value != value else "confirmed"
                trust = self.state.trust.get((a,"Player"),.6)
                if outcome in ("confirmed","truthful_outdated"): trust=min(.95,trust+.06)
                if outcome == "contradicted": trust=max(.1,trust-.28)
                assessment = self._emit("relationship",f"{a} checks your report: {outcome.replace('_',' ')}",actors=(a,"Player"),scope="private",
                    parents=(exp.event_id,event.event_id,check.event_id if check else None),assessment=outcome,
                    relationship_updates=[{"listener":a,"speaker":"Player","value":round(trust,2)}])
                self._remember(a,Experience(self.minute,"episodic","relationship","Player",str(trust),"Player",self.minute,True,
                    assessment.event_id,assessment.payload["title"]+f". Trust is {trust:.2f}.",claimed_origin_event=exp.event_id),significant=True)
        elif kind == "promise_due":
            self._settle_player(data["id"])
        elif kind == "settle":
            for a in ("Felix","Sabina","Lucius"):
                required = 5 if a == "Felix" else 2
                delivered = min(required,self.economy.inventory[a])
                event = self._emit("bread_ready" if a == "Felix" else "daily_work",f"{a} uses {delivered}/{required} flour units for the day's work",
                    actors=(a,),parents=(self._last_account.get(a),),inventory_delta={a:-delivered},cash_delta={a:delivered*2-(required-delivered)},
                    delivered=delivered,required=required,missed=required-delivered)
                self._remember(a,Experience(self.minute,"episodic",None,None,None,None,self.minute,True,event.event_id,event.payload["title"]))
        elif kind == "service_due" and not self.flags.get("service_done"):
            trust=max(.1,self.state.trust.get(("Lucius","Player"),.6)-.2)
            event=self._emit("relationship","The household waited for your service; Lucius withdraws his recommendation",actors=("Player","Lucius"),scope="private",
                flags={"service_missed":True,"reputation":self.flags["reputation"]-2},
                commitment_updates=[{"agent":"Player","id":"household-service","status":"missed","fulfilled":0}],
                relationship_updates=[{"listener":"Lucius","speaker":"Player","value":trust}])
            self._remember("Lucius",Experience(self.minute,"episodic","relationship","Player",str(trust),"Player",self.minute,True,event.event_id,
                "Aelia took the household advance but did not return for the promised service."),significant=True)

    def _purchase(self, agent, attempted, parent=None):
        filled = min(attempted,self.economy.market_stock,max(0,int(self.economy.cash[agent]//self.economy.price)))
        event=self._emit("purchase",f"{agent} obtains {filled}/{attempted} flour units",actors=(agent,),scope="private",
            parents=(parent,self._last_account.get(agent)),owner=agent,attempted=attempted,quantity=filled,
            cash_delta={agent:-filled*self.economy.price},inventory_delta={agent:filled},market_stock_delta=-filled)
        self._remember(agent,Experience(self.minute,"episodic",None,None,None,None,self.minute,True,event.event_id,event.payload["title"]))
        return event

    def _book_inspection(self, agent, parent=None):
        if self.economy.cash[agent]<1: raise ValueError("An inspection costs one coin.")
        event=self._emit("inspection_booked",f"{agent} pays one coin to inspect a dispatch",actors=(agent,),scope="private",parents=(parent,),cash_delta={agent:-1},fee=1)
        self.clock.schedule(self.minute+15,"inspection",{"agent":agent,"booking":event.event_id})
        return event

    def interact(self, action, recipient=None, quantity=1):
        if type(quantity) is not int or not 1<=quantity<=12:
            raise ValueError("quantity must be 1..12")
        self.require_near(recipient)
        if action == "accept_delivery":
            if recipient != "Felix" or self.flags["quest"] != "unaccepted": raise ValueError("This promise is not available.")
            deadline = (self.minute//1440)*1440+600
            if deadline<=self.minute: deadline+=1440
            if self.state.trust.get(("Felix","Player"),.6)<.35: raise ValueError("Felix needs a reliable report or a kept exchange before extending another promise.")
            identifier="felix-first" if not self.economy.commitments["Player"] else f"felix-day-{self.minute//1440+1}"
            ev=self._emit("promise", "You promise Felix four flour units before dusk",actors=("Player","Felix"),scope="private",quantity=4,deadline=deadline,
                flags={"quest":"active","active_contract":identifier},owner="Player",new_commitment={"id":identifier,"quantity":4,"deadline":deadline,"status":"open","fulfilled":0,"beneficiary":"Felix","event_id":len(self.ledger)})
            self.clock.schedule(deadline,"promise_due",{"id":identifier})
            return self.event_dict(ev)
        if action == "work":
            if recipient not in ("Sabina","Chreste"): raise ValueError("Ask the food counter or fullery about work.")
            day=self.minute//1440
            key=f"work:{day}:{recipient}"
            if self.flags.get(key,0)>=2: raise ValueError("Today's extra work has already been taken.")
            payer = "Sabina" if recipient == "Sabina" else "Lucius"
            wage = 3 if recipient == "Sabina" else 4
            if self.economy.cash[payer]<wage: raise ValueError("The household cannot pay another shift now.")
            self.advance(55 if recipient == "Sabina" else 80,"compress")
            if self.economy.cash[payer]<wage: raise ValueError("The payer can no longer afford this shift. Try another opportunity.")
            return self.event_dict(self._emit("work_complete",f"You finish a shift for {recipient} and receive {wage} coins",actors=("Player",recipient),scope="private",
                cash_delta={"Player":wage,payer:-wage},flags={key:self.flags.get(key,0)+1,"reputation":self.flags["reputation"]+1}))
        if action == "buy":
            if recipient not in ("Marcus","Felix"): raise ValueError("This person is not selling flour.")
            if self.state.trust.get((recipient,"Player"),.6)<.35: raise ValueError("They will not trade on your word now.")
            if self.economy.cash["Player"]<quantity*self.economy.price: raise ValueError("You need more coins for that amount.")
            if recipient == "Marcus":
                if self.economy.inventory[recipient]<quantity: raise ValueError("The trader has less flour than that.")
                return self.event_dict(self._emit("trade",f"You buy {quantity} flour units from Marcus",actors=("Player",recipient),scope="private",
                    quantity=quantity,price=self.economy.price,cash_delta={"Player":-quantity*self.economy.price,recipient:quantity*self.economy.price},
                    inventory_delta={"Player":quantity,recipient:-quantity},parents=(self._last_account.get(recipient),)))
            if self.economy.market_stock<quantity: raise ValueError("The shared flour stock cannot fill that order.")
            return self.event_dict(self._purchase("Player",quantity))
        if action == "deliver":
            if recipient != "Felix" or self.flags["quest"] != "active": raise ValueError("There is no open promise to deliver here.")
            return self.event_dict(self._settle_player(self.flags["active_contract"],early=True))
        if action == "inspect":
            return self.event_dict(self._book_inspection("Player"))
        if action == "patronage":
            if recipient != "Lucius" or self.flags["affiliation"] != "independent": raise ValueError("This household advance is unavailable.")
            if self.economy.cash["Lucius"]<8: raise ValueError("The steward cannot make another advance.")
            ev=self._emit("patronage", "You accept eight coins and promise two hours of household service within three days",actors=("Player","Lucius"),scope="private",
                cash_delta={"Player":8,"Lucius":-8},flags={"affiliation":"household client","service_due":self.minute+3*1440},
                owner="Player",new_commitment={"id":"household-service","quantity":120,"deadline":self.minute+3*1440,"status":"open","fulfilled":0,"beneficiary":"Lucius","event_id":len(self.ledger)})
            self.clock.schedule(self.minute+3*1440,"service_due",{})
            return self.event_dict(ev)
        if action == "service":
            if recipient != "Lucius" or self.flags.get("affiliation") != "household client" or self.flags.get("service_done"):
                raise ValueError("There is no outstanding household service to complete.")
            if self.minute+120>=self.flags["service_due"]: raise ValueError("Finish service before the household's deadline; this shift would finish too late.")
            self.advance(120,"compress")
            return self.event_dict(self._emit("work_complete","You keep your household service promise",actors=("Player","Lucius"),scope="private",
                commitment_updates=[{"agent":"Player","id":"household-service","status":"fulfilled","fulfilled":120}],
                flags={"service_done":True,"reputation":self.flags["reputation"]+1}))
        if action == "sell_information":
            knowledge=self.knowledge("Player")
            if knowledge["value"] == "unknown": raise ValueError("First obtain an actual report or paid inspection.")
            value=PEOPLE[recipient]["information_value"]
            known=self.knowledge(recipient)
            if value<=0 or known["as_of"] is not None and known["as_of"]>=knowledge["as_of"]:
                raise ValueError("This recipient will not pay for a report they already know or cannot use.")
            if known["value"] == knowledge["value"] and self.minute-(known["as_of"] or 0)<180:
                raise ValueError("A newer timestamp alone is not worth paying for while their report is still useful.")
            key=f"sale:{recipient}:{knowledge['as_of']}"
            if self.flags.get(key) or self.economy.cash[recipient]<value: raise ValueError("That report cannot be sold here again.")
            exp=next(e for e in self.remembered("Player") if e.event_id in knowledge["evidence_ids"])
            event=self._hear(recipient,"Player",exp.value,exp.as_of,exp.claimed_origin_event or exp.event_id,
                             parents=(exp.event_id,),observer=exp.claimed_origin_observer or "Player")
            sale=self._emit("information_sale",f"{recipient} pays {value} coins for your dated report",actors=("Player",recipient),scope="private",parents=(event.event_id,),
                cash_delta={"Player":value,recipient:-value},flags={key:True},recipient_value=value)
            self.information_sales.append({"recipient":recipient,"price":value,"minute":self.minute,"event_id":sale.event_id})
            return self.event_dict(sale)
        raise ValueError("unknown contextual action")

    def claim(self, recipient, value):
        self.require_near(recipient)
        if value not in ("available","disrupted"): raise ValueError("invalid supply claim")
        event=self._hear(recipient,"Player",value,self.minute,len(self.ledger))
        return self.event_dict(event)

    def talk(self, recipient, topic="memory"):
        """Transfer only retained, selected-character records through an actual conversation."""
        self.require_near(recipient)
        if topic == "supply":
            known = self.knowledge(recipient)
            if known["value"] != "unknown":
                exp = next(e for e in self.remembered(recipient) if e.event_id in known["evidence_ids"])
                return self.event_dict(self._hear("Player",recipient,exp.value,exp.as_of,
                    exp.claimed_origin_event if exp.claimed_origin_event is not None else exp.event_id,
                    parents=(exp.event_id,),observer=exp.claimed_origin_observer or recipient))
        memories = [e for e in self.remembered(recipient) if e.kind == "episodic" and
                    "Player" in self.ledger.events[e.event_id].actors][-3:]
        return self.event_dict(self._emit("conversation",f"You speak with {recipient} about {topic}",
            actors=("Player",recipient),scope="private",parents=[e.event_id for e in memories],
            recalled=[e.text for e in memories]))

    def _settle_player(self, identifier, early=False):
        contract=next((c for c in self.economy.commitments["Player"] if c["id"]==identifier and c["status"]=="open"),None)
        if not contract: return self._emit("promise_already_closed","The delivery has already been settled",actors=("Player",),scope="private")
        fulfilled=min(contract["quantity"],self.economy.inventory["Player"]) if early or self._near("Felix") else 0
        if early and fulfilled<contract["quantity"]: raise ValueError("You still need four flour units before you can complete this promise early.")
        missing=contract["quantity"]-fulfilled
        payment=fulfilled*1.5
        if self.economy.cash["Felix"]<payment: payment=max(0,self.economy.cash["Felix"])
        trust=round(min(.95,max(.1,self.state.trust.get(("Felix","Player"),.6)+(.15 if not missing else -.22))),2)
        ev=self._emit("promise_settled",f"You deliver {fulfilled}/4 flour units to Felix. "+("He will introduce you to the household." if not missing else "He cannot rely on the missing flour."),
            actors=("Player","Felix"),scope="private",parents=(contract["event_id"],self._last_account.get("Player")),
            cash_delta={"Player":payment,"Felix":-payment},inventory_delta={"Player":-fulfilled,"Felix":fulfilled},
            commitment_updates=[{"agent":"Player","id":identifier,"status":"fulfilled" if not missing else "missed","fulfilled":fulfilled}],
            relationship_updates=[{"listener":"Felix","speaker":"Player","value":trust}],
            flags={"quest":"fulfilled" if not missing else "missed","reputation":self.flags["reputation"]+(2 if not missing else -1),"introduction":not bool(missing)},
            delivered=fulfilled,missing=missing,payment=payment)
        self._remember("Felix",Experience(self.minute,"episodic","relationship","Player",str(trust),"Player",self.minute,True,ev.event_id,
            f"Aelia {'kept' if not missing else 'missed'} the flour promise; delivered {fulfilled}/4. I paid {payment:g} coins. My trust is {trust:.2f}."),significant=True)
        self._remember("Player",Experience(self.minute,"episodic",None,None,None,None,self.minute,True,ev.event_id,ev.payload["title"]),significant=True)
        return ev

    def _visible(self,event):
        return event.event_id in self.witnessed or event.event_id in self.disclosed

    def event_dict(self,event,operator=False):
        result=event.to_dict()
        if not operator:
            for field in ("cash","inventory","commitments"):
                if field in result["payload"]:
                    result["payload"][field]={"Player":result["payload"][field]["Player"]}
        return {**result,"category":event.payload["category"],"title":event.payload["title"],"minute":event.tick,"parents":event.payload.get("parents",[])}

    def objective(self):
        status=self.flags["quest"]
        return {"id":"flour-promise","title":"A promise before dusk","status":status,
            "description":"Felix needs four units of flour before dusk. Six coins are not enough at the morning price. Earn a wage, accept an obligation, or find someone who will pay for useful information.",
            "steps":[{"text":"Meet Felix at the bread counter","done":status!="unaccepted"},
                     {"text":"Obtain four flour units — work, trade, or seek household backing","done":self.economy.inventory["Player"]>=4 or status=="fulfilled"},
                     {"text":"Return to Felix and keep your word before dusk","done":status=="fulfilled"}]}

    def snapshot(self,operator=False):
        minute=self.minute
        hour=(8+minute//60)%24
        player={"id":"Player","name":"Aelia","role":"freedwoman and errand worker","x":self.positions["Player"][0],"y":self.positions["Player"][1],
            "location":self.state.agent_locations["Player"],"cash":self.economy.cash["Player"],"inventory":self.economy.inventory["Player"],
            "reputation":self.flags["reputation"],"commitments":copy.deepcopy(self.economy.commitments["Player"]),"path":self.player_path,
            "affiliation":self.flags["affiliation"],"social_position":"Fictional freedwoman navigating work and household obligations"}
        agents=[]
        for a,p in PEOPLE.items():
            agents.append({"id":a,"name":a,"role":p["role"],"x":self.positions[a][0],"y":self.positions[a][1],
                "location":self.state.agent_locations[a],"nearby":self._near(a),"trust_player":self.state.trust.get((a,"Player"),.6) if operator or self._near(a) else None,
                "goal":p["goal"],"social_position":p["social_position"],**({"private":self.private_view(a)} if operator else {})})
        events=[self.event_dict(e,operator=operator) for e in self.ledger.events if operator or self._visible(e)]
        opportunities=[{"id":"promise","title":"A promise before dusk","text":"Speak to Felix about tomorrow's bread.","action":{"recipient":"Felix","action":"accept_delivery"}}] if self.flags["quest"]=="unaccepted" else []
        if self.flags.get("introduction"):
            opportunities.append({"id":"household-introduction","title":"A word at the household","text":"Felix will vouch for you. Lucius can offer an advance, at the cost of a future obligation.","action":{"recipient":"Lucius","action":"patronage"}})
        snap={"minute":minute,"day":minute//1440+1,"clock":f"{hour:02d}:{minute%60:02d}","player":player,"map":copy.deepcopy(MAP),
            "agents":agents,"nearby":[a for a in self.agent_ids if self._near(a)],"objective":self.objective(),"opportunities":opportunities,
            "journal":[e for e in events if e["category"] not in ("routine","time_advanced")][-80:],"montage":copy.deepcopy(self.montage),
            "time_stats":copy.deepcopy(self.last_advance),"mode":"historical-fiction","historical_note":MAP["disclaimer"],
            "elapsed_policy":"World time advances through live play or explicit simulation; no offline wall-clock catch-up is implied."}
        if operator:
            snap["operator"]={"facts":dict(self.state.facts),"events":events,"decisions":copy.deepcopy(self.decisions),
                              "queue":list(self.clock.queue),"metrics":self.metrics(),"flags":dict(self.flags),"ledger_hash":self.ledger.content_hash()}
        return snap

    def metrics(self):
        settlements=[e for e in self.ledger.events if e.payload["category"] in ("daily_work","bread_ready")]
        required=sum(e.payload["required"] for e in settlements)
        delivered=sum(e.payload["delivered"] for e in settlements)
        return {"minute":self.minute,"events":len(self.ledger),"decisions":len(self.decisions),"delivered":delivered,"required":required,
            "delivery_fill_rate":delivered/required if required else None,"citizen_cash_change":sum(self.economy.cash[a]-self._initial_cash[a] for a in self.agent_ids),
            "player_cash_change":self.economy.cash["Player"]-self._initial_cash["Player"],"player_grain":self.economy.inventory["Player"],
            "stock":self.economy.market_stock,"trust_player":{a:self.state.trust.get((a,"Player"),.6) for a in self.agent_ids},
            "information_sales":len(self.information_sales),"inspection_cost":sum(e.payload.get("fee",0) for e in self.ledger.events),
            "player_commitments":copy.deepcopy(self.economy.commitments["Player"])}

    def fidelity_state(self):
        return {"minute":self.minute,"cash":dict(self.economy.cash),"inventory":dict(self.economy.inventory),"stock":self.economy.market_stock,
            "price":self.economy.price,"facts":dict(self.state.facts),"positions":copy.deepcopy(self.positions),
            "relationships":[[a,b,v] for (a,b),v in sorted(self.state.trust.items())],"commitments":copy.deepcopy(self.economy.commitments),
            "beliefs":{a:self.knowledge(a) for a in self.memories},"decisions":copy.deepcopy(self.decisions),
            "flags":dict(self.flags),"memories":{a:[asdict(e) for e in self.remembered(a)] for a in self.memories},
            "ledger_hash":self.ledger.content_hash()}
