"""The six-sack dispute: consequential social play over the preserved Pompeii world.

Every material or institutional change is projected from an appended event.
Private documents reach the player through actual, proximity-checked readings.
"""
from __future__ import annotations

import copy
from dataclasses import asdict, replace
import json
import math

from kalends.memory.base import Experience
from kalends.pompeii.world import PompeiiWorld
from kalends.pompeii.district import LOCATIONS, PEOPLE
from .scenario import COMMISSION_SPECS, HISTORICAL_DISCLAIMER, NEW_ACTIONS, PERSONALITY, SCENARIO_VERSION
from .cognitive_market import CognitiveMarketMixin, V2_ACTIONS


class RebirthWorld(CognitiveMarketMixin, PompeiiWorld):
    def __init__(self, config=None, seed=None, optimized=True):
        self._addon_defaults()
        super().__init__(config=config, seed=seed)
        self.optimized = bool(optimized)
        self._install_ledger()
        self._open_chapter()

    def _addon_defaults(self):
        self.v2_defaults()
        self.arc = {}
        self.documents = {}
        self.axes = {agent:{"reliability":.6,"credibility":.6,"affinity":.5,"competence":.3,"favors":0} for agent in PEOPLE}
        self.progression = {"access":[],"completed_commissions":0,"paid_shifts":0}
        self.commissions = []
        self.plans = {}
        self.npc_paths = {}
        self._movement_state = {"distance":0.,"charged_minutes":0}
        self.optimized = False
        self._rebirth_ready = False

    def _install_ledger(self):
        if self.optimized:
            from .immutable import PersistentLedger
            self.ledger = PersistentLedger.from_ledger(self.ledger)

    @classmethod
    def from_legacy(cls, old, optimized=True):
        """Preserve every legacy event and account; add a dated new chapter afterward."""
        world = cls.__new__(cls)
        world.__dict__ = copy.deepcopy(old.__dict__)
        world._addon_defaults()
        for agent in world.agent_ids:
            inherited=world.state.trust.get((agent,"Player"),.6)
            world.axes[agent]["reliability"]=inherited
            world.axes[agent]["credibility"]=inherited
        world.optimized = bool(optimized)
        requested = max(world.config.horizon_days,(world.minute+30*1440+1439)//1440)
        if requested > 365:
            raise ValueError("This old world has insufficient remaining configured time for Rebirth. Its save is preserved; start a separate fresh life.")
        world.config = replace(world.config,horizon_days=requested)
        world._install_ledger()
        world._open_chapter(migrated=True)
        return world

    def _emit(self, category, title, actors=(), location=None, scope="public", parents=(), etype="state_change", **payload):
        inherited_service=next((update for update in payload.get("commitment_updates",[]) if update.get("id")=="household-service" and update.get("status") in ("fulfilled","missed")),None)
        if inherited_service and hasattr(self,"axes"):
            kept=inherited_service["status"]=="fulfilled"
            cause=next((c.get("event_id") for c in self.economy.commitments.get("Player",[]) if c["id"]=="household-service"),None)
            parents=(*parents,cause)
            payload["relationship_axes"]=[*payload.get("relationship_axes",[]),self._axis_change("Lucius",**({"reliability":.18,"competence":.1} if kept else {"reliability":-.25,"affinity":-.15}))]
            if not kept:
                payload["access_remove"]=[*payload.get("access_remove",[]),"household"]
        if etype == "move" and actors and actors[0] != "Player" and "position" in payload:
            agent = actors[0]
            start = self.positions.get(agent)
            if start is not None:
                old_location = self.state.agent_locations.get(agent,"street")
                target = payload["position"]
                route = [list(start)]
                old_place = next((p for p in LOCATIONS if p["id"] == old_location and p["interior"]),None)
                new_place = next((p for p in LOCATIONS if p["id"] == payload.get("to") and p["interior"]),None)
                if old_place:
                    route.extend([[old_place["door"]["x"],old_place["door"]["y"]],[old_place["door"]["x"],415]])
                else:
                    route.append([start[0],415])
                if new_place:
                    route.extend([[new_place["door"]["x"],415],[new_place["door"]["x"],new_place["door"]["y"]]])
                else:
                    route.append([target[0],415])
                route.append(list(target))
                payload.setdefault("path",route)
        event = super()._emit(category,title,actors,location,scope,parents,etype,**payload)
        if not hasattr(self,"arc"):
            return event
        self.arc.update(copy.deepcopy(payload.get("story_patch",{})))
        self.flags.update(copy.deepcopy(payload.get("rebirth_flags",{})))
        for change in payload.get("relationship_axes",[]):
            relationship = self.axes[change["agent"]]
            for axis,delta in change.get("delta",{}).items():
                if axis not in relationship:
                    raise ValueError("unknown relationship axis")
                relationship[axis] = round(max(-9,min(9,relationship[axis]+delta)),3) if axis == "favors" else round(max(0,min(1,relationship[axis]+delta)),3)
        for access in payload.get("access_add",[]):
            if access not in self.progression["access"]:
                self.progression["access"].append(access)
        for access in payload.get("access_remove",[]):
            if access in self.progression["access"]:
                self.progression["access"].remove(access)
        for key,delta in payload.get("progression_delta",{}).items():
            self.progression[key] = self.progression.get(key,0)+delta
        if "commission" in payload:
            self.commissions.append(copy.deepcopy(payload["commission"]))
        for change in payload.get("commission_updates",[]):
            for commission in self.commissions:
                if commission["id"] == change["id"]:
                    commission.update(copy.deepcopy(change))
        if "plan" in payload:
            self.plans[actors[0]] = copy.deepcopy(payload["plan"])
        if category == "player_move" and "movement_state" in payload:
            self._movement_state = copy.deepcopy(payload["movement_state"])
        if "position" in payload and actors and actors[0] != "Player":
            self.npc_paths[actors[0]]={"event_id":event.event_id,"path":copy.deepcopy(payload.get("path",[])),"minute":self.minute}
        if category == "promise_settled":
            self.axes["Felix"]["reliability"] = round(min(1,max(0,self.axes["Felix"]["reliability"]+(.15 if not payload["missing"] else -.22))),3)
        if category == "relationship" and payload.get("assessment"):
            agent = actors[0]
            if agent in self.axes:
                delta = -.28 if payload["assessment"] == "contradicted" else .06 if payload["assessment"] in ("confirmed","truthful_outdated") else 0
                self.axes[agent]["credibility"] = round(min(1,max(0,self.axes[agent]["credibility"]+delta)),3)
        if category == "work_complete" and "Player" in actors:
            self.progression["paid_shifts"] += int(bool(payload.get("cash_delta",{}).get("Player",0)>0))
        if category.startswith("rb_") and "Player" in actors:
            for agent in actors:
                if agent != "Player" and agent in self.memories:
                    self._remember(agent,Experience(self.minute,"episodic","rebirth",category,title,"Player",self.minute,True,
                        event.event_id,title),significant=category in ("rb_resolution","rb_reconcile","rb_service_kept","rb_commission_settled"))
        self.v2_fold_event(event,payload)
        return event

    def _remember(self,agent,experience,significant=False):
        super()._remember(agent,experience,significant)
        self.v2_admit_experience(agent,experience)

    def move(self,x=None,y=None,location=None):
        """Keep old command bytes; V2 sessions explicitly opt into new movement."""
        revision=getattr(self,"_movement_revision",1)
        if type(revision) is not int or revision not in (1,2):
            raise ValueError("Unsupported movement revision.")
        if revision == 1:
            return super().move(x=x,y=y,location=location)
        from .navigation_v2 import PUBLIC_LOCATIONS, door_points, path_between, path_distance, point_walkable
        start=self.positions["Player"];current=self.state.agent_locations["Player"]
        destination=None
        if location is not None:
            if not isinstance(location,str):raise ValueError("Unknown destination.")
            explicit=x is not None or y is not None
            if explicit and (x is None or y is None):raise ValueError("A movement destination needs both coordinates.")
            if location == "street":
                # Exiting reaches the actual public doorway, rather than a
                # second invisible walk all the way to the horizontal backbone.
                target=(x,y) if explicit else door_points(current)[0] if current not in PUBLIC_LOCATIONS else start
            else:
                destination=next((r for r in LOCATIONS if r["id"]==location),None)
                if destination is None:raise ValueError("Unknown destination.")
                target=(x,y) if explicit else (destination["x"]+destination["w"]*.5,destination["y"]+destination["h"]*.85) if destination["interior"] else (destination["door"]["x"],destination["door"]["y"])
        else:
            target=(x,y)
            if current not in PUBLIC_LOCATIONS and point_walkable(target,current):
                location=current;destination=next(r for r in LOCATIONS if r["id"]==current)
            else:
                location="street"
        points=path_between(start,target,current,location)
        distance=path_distance(points)
        previous=self._movement_state
        total=math.fsum((previous["distance"],distance))
        # A prepaid partial travel minute survives stops and save/restart.
        # The tolerance only avoids floating arithmetic crossing an exact
        # 90-unit boundary by a few ulps; it is not a movement-speed discount.
        charged=math.ceil(total/90-1e-10) if total else 0
        minutes=charged-previous["charged_minutes"]
        if self.minute+minutes > self.config.horizon_days*1440:
            raise ValueError("There is not enough configured world time to finish this walk.")
        if minutes:
            self.advance(minutes,"live")
        name=destination["name"] if destination else "the street"
        title=f"You enter {name}" if current!=location else f"You walk through {name}"
        event=self._emit("player_move",title,actors=("Player",),etype="move",to=location,position=points[-1],path=points,
            movement_revision=2,travel_distance=distance,world_minutes=minutes,
            movement_state={"distance":total,"charged_minutes":charged})
        self.player_path=[list(point) for point in points]
        if location in PUBLIC_LOCATIONS:
            self._remember("Player",Experience(self.minute,"observed","grain","price",str(self.economy.price),None,self.minute,True,
                event.event_id,"I read the street's posted flour price: %.1f coins." % self.economy.price))
        return self.event_dict(event)

    def _open_chapter(self,migrated=False):
        self._rebirth_ready = True
        start = self.minute
        sabina_advance = min(4,max(0,self.economy.cash["Sabina"]))
        household_advance = min(8,max(0,self.economy.cash["Lucius"]))
        # New transactions occur now, including on migration. No invented old payment.
        agreement = self._emit("rb_cart_account","Two orders share one six-sack cart",actors=("Sabina","Marcus","Lucius"),scope="private",
            cash_delta={"Sabina":-sabina_advance,"Lucius":-household_advance,"Marcus":sabina_advance+household_advance},
            story_patch={"version":SCENARIO_VERSION,"opened_at":start,"deadline":start+360,"stage":"unresolved","route":None,
                "heard":False,"followup_ready":False,"followup_done":False,"service_done":False,
                "sabina_advance":sabina_advance,"household_advance":household_advance,"cart_units":0,"migrated":migrated,
                "resolution_event":None,"holding_charge":3,"status":"ready"})
        self._new_document("market_receipt","Sabina",{"title":"Sabina's wax account","text":f"Two flour units ordered for the food counter; {sabina_advance:g} coins advanced to Marcus.",
            "quantity":2,"paid":sabina_advance,"as_of":start},agreement.event_id)
        self._new_document("household_tablet","Dama",{"title":"The household's delivery instructions","text":f"Four flour units reserved for the household; {household_advance:g} coins advanced. Dama is instructed to repeat the quantity, not claim the whole cart.",
            "quantity":4,"paid":household_advance,"as_of":start},agreement.event_id)
        self._new_document("loading_record","Marcus",{"title":"The carrier's loading account","text":"Six sacks share the cart. A three-coin carrying charge must be met before release. The earlier dispatch describes readiness, not completed delivery.",
            "quantity":6,"fee":3,"as_of":start},agreement.event_id)
        self._reserve_cart()
        for agent,position in (("Sabina",(750,435)),("Dama",(850,430))):
            self._emit("rb_arrival",f"{agent} comes to the disputed cart",actors=(agent,),etype="move",to="street",position=position)
            self.clock.schedule(start+45,"routine",{"agent":agent,"location":PEOPLE[agent]["location"],"day":self.minute//1440})
        opening="Sabina stops beside the cart. “I paid for two sacks. Why is the household asking for all six?”" if self.state.agent_locations["Player"] in ("street","water","forum_access") else "A new lead reaches you: Sabina and a household messenger are disputing a flour cart by the fountain."
        self._emit("rb_hook",opening,actors=("Player",),location=self.state.agent_locations["Player"],story_patch={"hook_event":len(self.ledger)},fiction=True)
        self.clock.schedule(start+8,"rb_cart_hold",{})
        self.clock.schedule(start+360,"rb_dispute_due",{})
        self._refresh_plans()

    def _new_document(self,key,owner,content,parent):
        event = self._emit("rb_document",content["title"],actors=(owner,),scope="private",parents=(parent,),document_key=key,document=content)
        self.documents[key]={"owner":owner,"event_id":event.event_id,**copy.deepcopy(content)}
        self._remember(owner,Experience(self.minute,"observed","cart",key,json.dumps(content,sort_keys=True),None,self.minute,True,
            event.event_id,content["text"],"observed",event.event_id,owner),significant=True)

    def _reserve_cart(self):
        if self.arc.get("cart_units",0)>=6 or self.arc.get("stage") not in ("unresolved","awaiting_stock"):
            return
        missing=6-self.arc.get("cart_units",0)
        take=min(missing,self.economy.market_stock)
        if take:
            self._emit("rb_cart_reserved",f"{take} flour units are set aside for the disputed orders",actors=("Marcus",),scope="private",
                market_stock_delta=-take,inventory_delta={"Cart":take},story_patch={"cart_units":self.arc.get("cart_units",0)+take})
        if self.arc["cart_units"]<6:
            self._emit("rb_waiting_stock","The cart still lacks flour; the account must await a real arrival",actors=("Player",),scope="private",
                story_patch={"stage":"awaiting_stock"})
        elif self.arc["stage"]=="awaiting_stock":
            self._emit("rb_opportunity","The reserved cart now has all six units",actors=("Player",),scope="private",story_patch={"stage":"unresolved"})

    def _record_known(self,agent,key):
        rows=[e for e in self.remembered(agent) if e.subject=="cart" and e.predicate==key]
        return rows[-1] if rows else None

    def _read_document(self,key,recipient):
        doc=self.documents[key]
        if recipient!=doc["owner"]:
            raise ValueError("That character does not hold this document.")
        retained=self._record_known(recipient,key)
        if retained is None:
            raise ValueError("They no longer retain those instructions.")
        if self._record_known("Player",key):
            raise ValueError("You have already copied these terms.")
        event=self._emit("rb_evidence",f"You read {doc['title'].lower()}",actors=("Player",recipient),scope="private",
            parents=(retained.event_id,),document_key=key,document={k:v for k,v in doc.items() if k not in ("owner","event_id")})
        self._remember("Player",Experience(self.minute,"observed","cart",key,retained.value,recipient,retained.as_of,True,event.event_id,
            retained.text,"observed",retained.event_id,recipient),significant=True)
        self._refresh_plans()
        return self.event_dict(event)

    def _axis_change(self,agent,**delta):
        return {"agent":agent,"delta":delta}

    def _outstanding_household_service(self):
        return next((c for c in self.economy.commitments["Player"] if c["id"] in ("household-service","rebirth-service") and c["status"]=="open"),None)

    def _hear(self,listener,speaker,value,as_of,root,parents=(),observer=None):
        if speaker!="Player" or listener not in self.axes:
            return super()._hear(listener,speaker,value,as_of,root,parents,observer)
        prior=self.knowledge(listener)
        credibility=self.axes[listener]["credibility"]
        accepted=credibility>=.3 and (prior["as_of"] is None or as_of>prior["as_of"] or as_of==prior["as_of"] and value==prior["value"])
        event=self._emit("report",f"{speaker} tells {listener} that flour supply is {value} (observed at minute {as_of})",
            actors=(speaker,listener),scope="private",parents=parents,etype="tell",speaker=speaker,listener=listener,
            prop=["grain","supply"],value=value,as_of=as_of,root_event=root,root_observer=observer or speaker,accepted=accepted,
            credibility_used=credibility,relationship_axis="credibility")
        self._remember(listener,Experience(self.minute,"told","grain","supply",value,speaker,as_of,accepted,
            event.event_id,event.payload["title"],"told",root,observer or speaker))
        self._refresh_plans([listener])
        return event

    def _need_open_cart(self):
        if self.arc.get("stage") not in ("unresolved","awaiting_stock"):
            raise ValueError("The cart has already been committed or settled.")
        if self.arc.get("cart_units",0)<6 or self.economy.inventory.get("Cart",0)<6:
            raise ValueError("All six reserved flour units must physically arrive before this agreement can be made.")
        if self.minute>=self.arc["deadline"]:
            raise ValueError("The original bargaining window has closed.")

    def interact(self,action,recipient=None,quantity=1,**payload):
        if payload:
            raise ValueError("Unexpected action fields")
        if type(quantity) is not int or not 1<=quantity<=12:
            raise ValueError("quantity must be 1..12")
        self.require_near(recipient)
        if action in V2_ACTIONS:
            return self.v2_interact(action,recipient,quantity)
        if action not in NEW_ACTIONS:
            if action=="work" and recipient=="Sabina" and self.axes["Sabina"]["affinity"]<.35:
                raise ValueError("Sabina will not offer another shift until your dispute is repaired.")
            result=super().interact(action,recipient,quantity)
            self._refresh_plans()
            return result
        if action=="hear_dispute":
            if recipient!="Sabina": raise ValueError("Ask Sabina what happened at the counter.")
            if self.arc["heard"]: raise ValueError("Sabina has already told you the dispute.")
            return self.event_dict(self._emit("rb_dispute_heard","Sabina asks you to find out who the six sacks were actually promised to",actors=("Player","Sabina"),scope="private",
                story_patch={"heard":True},parents=(self.arc["hook_event"],)))
        if action=="examine_receipt": return self._read_document("market_receipt",recipient)
        if action=="examine_tablet": return self._read_document("household_tablet",recipient)
        if action=="verify_cart":
            if recipient!="Marcus": raise ValueError("Marcus holds the loading account.")
            if self.economy.cash["Player"]<1: raise ValueError("Marcus wants one coin to open and copy the carrier's account.")
            if self._record_known("Player","loading_record"): raise ValueError("You have already checked this loading account.")
            if not self._record_known("Marcus","loading_record"): raise ValueError("Marcus no longer retains that loading account; he cannot sell you a check of it.")
            self._emit("rb_verification_fee","You pay Marcus one coin and wait while the loading account is checked",actors=("Player","Marcus"),scope="private",
                cash_delta={"Player":-1,"Marcus":1},fee=1)
            self.advance(15,"compress")
            return self._read_document("loading_record",recipient)
        if action=="mediate":
            if recipient!="Marcus": raise ValueError("Marcus must agree to release the cart.")
            self._need_open_cart()
            evidence=[self._record_known("Player",key) for key in ("market_receipt","household_tablet","loading_record")]
            if not all(evidence): raise ValueError("Bring Sabina's receipt, Dama's household instructions and the checked loading account.")
            if self.economy.cash["Marcus"]<3: raise ValueError("Marcus cannot cover the carrying charge from his account now.")
            reward=min(2,max(0,self.economy.cash["Marcus"]-3))
            event=self._emit("rb_agreement","You set the two accounts side by side: four sacks for the house, two for the counter",actors=("Player","Marcus"),scope="private",
                parents=[e.event_id for e in evidence],story_patch={"stage":"committed","route":"broker","choice_event":len(self.ledger)},
                cash_delta={"Player":reward,"Marcus":-reward-3,"Carrier":3},brokerage_payment=reward,carrying_fee=3,fee_payer="Marcus")
            self.clock.schedule(self.minute+20,"rb_cart_delivery",{"route":"broker","parent":event.event_id})
            self.advance(20,"compress")
            return self.event_dict(event)
        if action=="support_market":
            if recipient!="Sabina": raise ValueError("Make the market arrangement with Sabina.")
            self._need_open_cart()
            if self.economy.cash["Player"]<3: raise ValueError("Releasing the cart on the market arrangement costs three coins.")
            event=self._emit("rb_agreement","You pay the carrying charge and stand behind the market counters",actors=("Player","Sabina","Marcus"),scope="private",
                cash_delta={"Player":-3,"Carrier":3},story_patch={"stage":"committed","route":"market","choice_event":len(self.ledger)},
                carrying_fee=3)
            self.clock.schedule(self.minute+20,"rb_cart_delivery",{"route":"market","parent":event.event_id})
            self.advance(20,"compress")
            return self.event_dict(event)
        if action=="guarantee_household":
            if recipient!="Lucius": raise ValueError("Only Lucius can make a household advance.")
            self._need_open_cart()
            if self.flags.get("affiliation")!="independent": raise ValueError("You already have a household affiliation or advance.")
            if self.economy.cash["Lucius"]<9: raise ValueError("The household cannot fund both this advance and the carrying charge.")
            deadline=self.minute+3*1440
            event=self._emit("rb_agreement","You back the household's priority and accept six coins against two hours of service",actors=("Player","Lucius"),scope="private",
                cash_delta={"Player":6,"Lucius":-9,"Carrier":3},story_patch={"stage":"committed","route":"household","choice_event":len(self.ledger),"service_due":deadline},
                flags={"affiliation":"household client"},owner="Player",new_commitment={"id":"rebirth-service","beneficiary":"Lucius","quantity":120,"fulfilled":0,"deadline":deadline,"status":"open","event_id":len(self.ledger)})
            self.clock.schedule(deadline,"rb_service_due",{"parent":event.event_id})
            self.clock.schedule(self.minute+20,"rb_cart_delivery",{"route":"household","parent":event.event_id})
            self.advance(20,"compress")
            return self.event_dict(event)
        if action=="return_service":
            if recipient!="Lucius" or self.arc.get("route")!="household" or self.arc.get("service_done"):
                raise ValueError("There is no outstanding Rebirth household service here.")
            if self.minute+120>=self.arc["service_due"]: raise ValueError("There is not enough time to finish before the household deadline.")
            self.advance(120,"compress")
            return self.event_dict(self._emit("rb_service_kept","Lucius enters your completed service in the household account",actors=("Player","Lucius"),scope="private",
                story_patch={"service_done":True},commitment_updates=[{"agent":"Player","id":"rebirth-service","status":"fulfilled","fulfilled":120}],
                relationship_axes=[self._axis_change("Lucius",reliability=.18,competence=.1,favors=-1)],flags={"reputation":self.flags["reputation"]+1}))
        if action=="reconcile": return self._reconcile(recipient)
        if action=="accept_commission": return self._accept_commission(recipient)
        if action=="fulfill_commission": return self._fulfill_commission(recipient)
        if action=="decline_dispute":
            if recipient!="Sabina" or self.arc.get("stage") not in ("unresolved","awaiting_stock"):
                raise ValueError("There is no undecided dispute to decline.")
            if self.arc.get("declined"): raise ValueError("You have already declined to intervene.")
            return self.event_dict(self._emit("rb_declined","You leave the cart dispute to its buyers; their own deadline still approaches",actors=("Player","Sabina"),scope="private",story_patch={"declined":True}))
        if action=="reflect":
            revision=getattr(self,"_memory_presentation_revision",2)
            shared=self._memory_support(recipient,revision)
            if self.flags.get(f"reflection:{recipient}:{self.minute//1440}"): raise ValueError("You have already reflected on today's dealings together.")
            return self.event_dict(self._emit("rb_reflection",self._memory_line(recipient,revision),actors=("Player",recipient),scope="private",parents=[e.event_id for e in shared],
                rebirth_flags={f"reflection:{recipient}:{self.minute//1440}":True},reflection_records=[e.text for e in shared]))
        raise ValueError("Unknown Rebirth action")

    def _reconcile(self,recipient):
        if not self.arc.get("followup_ready") or self.arc.get("stage")!="resolved": raise ValueError("Let the first agreement take effect before repairing its consequences.")
        expected={"market":"Lucius","household":"Sabina","broker":"Marcus","ignored":"Sabina"}.get(self.arc.get("route"))
        if recipient!=expected: raise ValueError("This person is not the outstanding relationship in your agreement.")
        if self.arc.get("followup_done"): raise ValueError("You have already settled this consequence.")
        cash={};inventory={};access=[]
        parents=[self.arc["resolution_event"]]
        if recipient=="Lucius":
            if self.economy.cash["Player"]<3: raise ValueError("Lucius asks you to contribute three coins toward a replacement delivery.")
            cash={"Player":-3,"Lucius":3};access=["household"]
            title="You help fund the household's replacement delivery; Lucius reopens his account to you"
        elif recipient=="Sabina":
            if self.economy.inventory["Player"]<2: raise ValueError("Sabina asks for two flour units she can actually serve, not another guarantee.")
            inventory={"Player":-2,"Sabina":2};access=["market"]
            title="You bring two flour units to Sabina; the counter has a reason to welcome you again"
        else:
            knowledge=self.knowledge("Player")
            if not knowledge.get("direct") or self.minute-knowledge["as_of"]>60:
                raise ValueError("Bring Marcus a direct dispatch inspection no more than an hour old.")
            parents.extend(knowledge["evidence_ids"])
            title="You bring Marcus a checked fresh report; the trader agrees to work with your evidence"
        return self.event_dict(self._emit("rb_reconcile",title,actors=("Player",recipient),scope="private",parents=parents,
            cash_delta=cash,inventory_delta=inventory,story_patch={"followup_done":True},access_add=access,
            relationship_axes=[self._axis_change(recipient,affinity=.25,reliability=.08,credibility=.08,competence=.1)]))

    def _accept_commission(self,recipient):
        spec=COMMISSION_SPECS.get(recipient)
        if not spec or spec["access"] not in self.progression["access"]: raise ValueError("Your dealings have not opened this professional opportunity.")
        if not self.arc.get("followup_ready"): raise ValueError("This new account will open once the cart agreement has settled into the day's business.")
        if recipient=="Lucius" and self._outstanding_household_service():
            raise ValueError("Complete your promised service before taking a household commission.")
        favor_used=self.axes[recipient]["reliability"]<.35
        if favor_used and self.axes[recipient]["favors"]<1: raise ValueError("They need a kept commitment or an earned favor before extending another commission.")
        day=self.minute//1440
        if any(c["recipient"]==recipient and c["day"]==day for c in self.commissions): raise ValueError("This account offers at most one commission each day.")
        if any(c["status"]=="open" for c in self.commissions): raise ValueError("Finish the commission you already accepted first.")
        if self.economy.cash[recipient]<spec["reward"]: raise ValueError("This payer cannot reserve the commission's reward now.")
        identifier=f"rebirth:{recipient}:{day}"
        commission={"id":identifier,"recipient":recipient,"day":day,"kind":spec["kind"],"quantity":spec["quantity"],"reward":spec["reward"],
            "accepted_at":self.minute,"deadline":self.minute+spec["duration"],"status":"open","event_id":len(self.ledger)}
        # Escrow is a real account: payer cannot spend the promised reward twice.
        event=self._emit("rb_commission",f"{recipient} offers you a new account: {spec['title']}",actors=("Player",recipient),scope="private",
            commission=commission,cash_delta={recipient:-spec["reward"],"CommissionEscrow":spec["reward"]},
            relationship_axes=[self._axis_change(recipient,favors=-1)] if favor_used else [],favor_used=favor_used,
            owner="Player",new_commitment={"id":identifier,"beneficiary":recipient,"quantity":spec["quantity"],"fulfilled":0,"deadline":commission["deadline"],"status":"open","event_id":len(self.ledger)})
        self.clock.schedule(commission["deadline"],"rb_commission_due",{"id":identifier,"parent":event.event_id})
        return self.event_dict(event)

    def _fulfill_commission(self,recipient):
        commission=next((c for c in self.commissions if c["recipient"]==recipient and c["status"]=="open"),None)
        if not commission: raise ValueError("There is no open commission with this person.")
        if self.minute>=commission["deadline"]: raise ValueError("This commission's deadline has passed.")
        inventory={};parents=[commission["event_id"]]
        if commission["kind"]=="goods":
            if self.economy.inventory["Player"]<commission["quantity"]: raise ValueError(f"You need {commission['quantity']} flour units in your own bag.")
            inventory={"Player":-commission["quantity"],recipient:commission["quantity"]}
        else:
            knowledge=self.knowledge("Player")
            if not knowledge.get("direct") or knowledge["as_of"]<commission["accepted_at"]:
                raise ValueError("This commission requires a new direct inspection after you accepted it.")
            parents.extend(knowledge["evidence_ids"])
        if self.economy.cash.get("CommissionEscrow",0)<commission["reward"]: raise ValueError("The reserved commission reward is unavailable.")
        return self.event_dict(self._emit("rb_commission_settled",f"You keep {recipient}'s commission and receive {commission['reward']} coins",actors=("Player",recipient),scope="private",parents=parents,
            cash_delta={"Player":commission["reward"],"CommissionEscrow":-commission["reward"]},inventory_delta=inventory,
            commission_updates=[{"id":commission["id"],"status":"fulfilled"}],commitment_updates=[{"agent":"Player","id":commission["id"],"status":"fulfilled","fulfilled":commission["quantity"]}],
            relationship_axes=[self._axis_change(recipient,reliability=.08,competence=.05,favors=1)],progression_delta={"completed_commissions":1},flags={"reputation":self.flags["reputation"]+1}))

    def on_task(self,task):
        kind,data=task["kind"],task["data"]
        if self.v2_on_task(kind,data):return
        if kind=="procure":
            self._procure_with_plan(data)
            return
        if kind=="rb_cart_hold":
            if self.arc.get("stage") in ("unresolved","awaiting_stock"):
                self._emit("rb_cart_held","Marcus receives the carrying charge; the earlier ready notice no longer guarantees departure",actors=("Marcus",),scope="private",
                    story_patch={"status":"held"},prop=["cart","status"],value="held",parents=(self.documents["loading_record"]["event_id"],))
            return
        if kind=="rb_dispute_due":
            if self.arc.get("stage") in ("unresolved","awaiting_stock"):
                if self.economy.inventory.get("Cart",0)>=6 and self.economy.cash["Lucius"]>=3:
                    event=self._emit("rb_npc_agreement","Lucius pays the carrying charge and secures the cart before the counter can",actors=("Lucius","Marcus"),location="street",
                        cash_delta={"Lucius":-3,"Carrier":3},story_patch={"stage":"committed","route":"ignored","choice_event":len(self.ledger)})
                    self._deliver_cart("ignored",event.event_id)
                else:
                    reserved=self.economy.inventory.get("Cart",0)
                    available=max(0,self.economy.cash["Marcus"])
                    refund_sabina=min(self.arc["sabina_advance"],available)
                    refund_household=min(self.arc["household_advance"],max(0,available-refund_sabina))
                    self._emit("rb_resolution","No buyer can release the cart; its flour returns to shared stock",actors=("Player",),scope="private",
                        inventory_delta={"Cart":-reserved},market_stock_delta=reserved,
                        cash_delta={"Marcus":-refund_sabina-refund_household,"Sabina":refund_sabina,"Lucius":refund_household},
                        returned_advances={"Sabina":refund_sabina,"Lucius":refund_household},
                        story_patch={"stage":"resolved","route":"unclaimed","resolution_event":len(self.ledger),"followup_ready":True})
            return
        if kind=="rb_cart_delivery":
            self._deliver_cart(data["route"],data["parent"])
            return
        if kind=="rb_followup":
            if self.arc.get("stage")=="resolved":
                self._emit("rb_opportunity",self._followup_title(),actors=("Player",),scope="private",parents=(self.arc.get("resolution_event"),),story_patch={"followup_ready":True})
            return
        if kind=="rb_service_due":
            if not self.arc.get("service_done"):
                self._emit("rb_service_missed","The household waited for your promised service; Lucius closes new commissions",actors=("Player","Lucius"),scope="private",
                    parents=(data.get("parent"),),story_patch={"service_missed":True},access_remove=["household"],
                    commitment_updates=[{"agent":"Player","id":"rebirth-service","status":"missed","fulfilled":0}],
                    relationship_axes=[self._axis_change("Lucius",reliability=-.25,affinity=-.15,favors=-1)],flags={"reputation":self.flags["reputation"]-1})
            return
        if kind=="rb_commission_due":
            commission=next((c for c in self.commissions if c["id"]==data["id"] and c["status"]=="open"),None)
            if commission:
                recipient=commission["recipient"]
                self._emit("rb_commission_missed",f"{recipient} closes the commission you did not bring back",actors=("Player",recipient),scope="private",
                    parents=(data.get("parent"),),cash_delta={"CommissionEscrow":-commission["reward"],recipient:commission["reward"]},
                    commission_updates=[{"id":commission["id"],"status":"missed"}],commitment_updates=[{"agent":"Player","id":commission["id"],"status":"missed","fulfilled":0}],
                    relationship_axes=[self._axis_change(recipient,reliability=-.18)],flags={"reputation":self.flags["reputation"]-1})
            return
        super().on_task(task)
        if kind=="dawn": self._reserve_cart()
        affected=[data["agent"]] if data.get("agent") in self.agent_ids else self.agent_ids if kind in ("dawn","settle") else []
        self._refresh_plans(affected)

    def _deliver_cart(self,route,parent):
        if self.arc.get("stage")!="committed" or self.arc.get("route")!=route: return
        if self.economy.inventory.get("Cart",0)<6: raise ValueError("The reserved cart cannot deliver goods it does not hold.")
        allocation={"Lucius":4,"Sabina":2} if route=="broker" else {"Sabina":4,"Felix":2} if route=="market" else {"Lucius":6}
        cash={}
        # Private parties renegotiate/refund the displaced order. No state tribunal.
        if route=="market":
            refund=min(self.arc["household_advance"],max(0,self.economy.cash["Marcus"]))
            cash["Marcus"]=cash.get("Marcus",0)-refund
            cash["Lucius"]=cash.get("Lucius",0)+refund
        elif route in ("household","ignored"):
            refund=min(self.arc["sabina_advance"],max(0,self.economy.cash["Marcus"]))
            cash["Marcus"]=cash.get("Marcus",0)-refund
            cash["Sabina"]=cash.get("Sabina",0)+refund
        relationships={
            "broker":[self._axis_change("Marcus",affinity=-.12,competence=.2),self._axis_change("Sabina",credibility=.15,affinity=.12),self._axis_change("Lucius",credibility=.15,affinity=-.05)],
            "market":[self._axis_change("Sabina",affinity=.25,reliability=.1,favors=1),self._axis_change("Lucius",affinity=-.22)],
            "household":[self._axis_change("Lucius",affinity=.22,favors=1),self._axis_change("Sabina",affinity=-.25)],
            "ignored":[],
        }[route]
        event=self._emit("rb_resolution",{
            "broker":"The cart moves: four sacks to the household, two to Sabina; Marcus remembers who opened his accounts",
            "market":"The counters receive the cart; Lucius receives a refund and remembers whose claim you put first",
            "household":"The household receives all six sacks; Sabina has her advance back and an empty counter",
            "ignored":"The household's own agreement moves the cart; Sabina loses the morning's supply",
        }[route],actors=("Player","Marcus","Lucius","Sabina","Felix") if route!="ignored" else ("Marcus","Lucius","Sabina"),location="street",scope="public",
            parents=(parent,),inventory_delta={"Cart":-6,**allocation},cash_delta=cash,
            story_patch={"stage":"resolved","resolution_event":len(self.ledger),"cart_units":0,"status":"delivered"},allocation=allocation,
            relationship_axes=relationships,access_add=[route] if route in ("market","household","broker") else [],
            flags={"reputation":self.flags["reputation"]+(1 if route!="ignored" else 0)})
        if route=="ignored":
            # A public new lead is presented; private accounts are still absent from player memory.
            self._emit("rb_public_notice","The cart has left for the household; Sabina's counter is still waiting. Ask her what happened",actors=("Player",),scope="private",
                story_patch={"followup_ready":True},parents=())
        else:
            self.clock.schedule(self.minute+45,"rb_followup",{"parent":event.event_id})
        for agent in allocation:
            self._remember(agent,Experience(self.minute,"episodic","rebirth","allocation",str(allocation[agent]),None,self.minute,True,event.event_id,
                f"The disputed cart delivered {allocation[agent]} flour units to my account."),significant=True)
        self._refresh_plans()

    def _plan(self,agent):
        own=self.economy.inventory[agent];cash=self.economy.cash[agent];knowledge=self.knowledge(agent)
        target=5 if agent=="Felix" else 3 if agent=="Lucius" else 8 if agent=="Marcus" else 2
        if agent in ("Dama","Chreste"):
            short="carry assigned delivery instructions" if agent=="Dama" else "finish the assigned cloth work"
            reason="My assigned role limits the promises and purchases I may make."
        elif cash<3:
            short="conserve working coins";reason="My own account cannot fund an ordinary order."
        elif own>=target:
            short="continue work with the stock already held";reason=f"My own stores contain {own} flour units."
        elif knowledge["value"]=="unknown" or knowledge["confidence"]<PEOPLE[agent]["caution"]:
            short="verify supply before the next purchase";reason="My retained report is missing or insufficient for my caution."
        elif knowledge["value"]=="disrupted" and PEOPLE[agent]["caution"]>=.7:
            short="defer once and reconsider the order";reason="The dated report I currently accept describes disruption."
        else:
            short="buy the uncovered flour requirement";reason="My own stock is below the working target."
        return {"long_term":PERSONALITY[agent]["long_term"],"medium_term":PERSONALITY[agent]["medium_term"],"short_term":short,
            "reason":reason,"evidence_ids":knowledge["evidence_ids"],"owned_stock":own,"owned_cash":cash}

    def _procure_with_plan(self,data):
        """A bounded hierarchical plan selects real tasks using owned state and records."""
        agent=data["agent"]
        plan=self._plan(agent)
        known=self.knowledge(agent)
        target=5 if agent=="Felix" else 3 if agent=="Lucius" else 8 if agent=="Marcus" else 2
        deficit=max(0,target-self.economy.inventory[agent])
        commitment=next((c for c in self.commissions if c["recipient"]==agent and c["kind"]=="goods" and c["status"]=="open"),None)
        if not deficit: choice="wait"
        elif self.economy.cash[agent]<1: choice="conserve"
        elif commitment and commitment["quantity"]>=deficit and self.axes[agent]["reliability"]>=.65: choice="await_commission"
        elif self.config.information_policy=="cautious" and (known["value"]=="unknown" or known["confidence"]<PEOPLE[agent]["caution"]) and agent in ("Felix","Lucius"):
            choice="inspect"
        elif known["value"]=="disrupted" and known["confidence"]>=PEOPLE[agent]["caution"] and PEOPLE[agent]["caution"]>=.7:
            choice="defer"
        else: choice="buy"
        parents=list(known["evidence_ids"])
        if choice=="await_commission": parents.append(commitment["event_id"])
        event=self._emit("decision",f"{agent} chooses to {choice.replace('_',' ')}: {plan['reason']}",actors=(agent,),scope="private",parents=parents,
            choice=choice,predicted_value=known["value"],plan=plan,plan_scope="own accounts, retained supply evidence and owned accepted commission only")
        self.decisions.append({"minute":self.minute,"agent":agent,"action":choice,"value":known["value"],"event_id":event.event_id})
        if choice=="inspect":
            self._book_inspection(agent,event.event_id)
            self.clock.schedule(self.minute+20,"purchase",{"agent":agent,"quantity":deficit,"decision":event.event_id})
        elif choice=="buy": self._purchase(agent,deficit,event.event_id)
        elif choice=="defer" and not data.get("retry"):
            self.clock.schedule(self.minute+90,"procure",{"agent":agent,"retry":1})
        elif choice=="await_commission" and not data.get("retry"):
            self.clock.schedule(commitment["deadline"]+1,"procure",{"agent":agent,"retry":1})
        self._refresh_plans([agent])

    def _refresh_plans(self,agents=None):
        if not self._rebirth_ready: return
        for agent in self.agent_ids if agents is None else agents:
            plan=self._plan(agent)
            if self.plans.get(agent)!=plan:
                self._emit("rb_plan_revision",f"{agent} revises the next step: {plan['short_term']}",actors=(agent,),scope="private",
                    parents=plan["evidence_ids"],plan=plan)

    def private_view(self,agent):
        view=super().private_view(agent)
        if agent in self.axes:
            view.update(relationship=copy.deepcopy(self.axes[agent]),plan=copy.deepcopy(self.plans.get(agent,self._plan(agent))),
                voice=PERSONALITY[agent]["voice"],scenario_version=SCENARIO_VERSION)
        return view

    def _recent_shared_memories(self,recipient):
        # Consolidated records precede the ordinary buffer, regardless of age.
        shared=[e for e in self.remembered(recipient) if e.subject in ("rebirth","relationship") and
                (e.source_agent=="Player" or e.subject=="relationship")]
        return sorted(shared,key=lambda e:(e.tick,e.event_id))[-2:]

    def _memory_support(self,recipient,revision=2):
        if revision==1:
            # Exact pre-revision parent selection, used only for old accepted commands.
            return [e for e in self.remembered(recipient) if e.subject in ("rebirth","relationship")][-3:]
        return self._recent_shared_memories(recipient)

    def _memory_line(self,recipient,revision=2):
        shared=self._recent_shared_memories(recipient) if revision==2 else [e for e in self.remembered(recipient) if
            e.subject in ("rebirth","relationship") and (e.source_agent=="Player" or e.subject=="relationship")][-2:]
        if shared: return " ".join(e.text for e in shared)
        return "We have no consequential shared dealing in my retained memory yet."

    def talk(self,recipient,topic="memory"):
        """A confirmed conversation can disclose only the speaker's retained material."""
        self.require_near(recipient)
        topic={"history":"memory","supply":"news"}.get(topic,topic)
        if topic not in {"role","goals","work","memory","news","dispute","documents","market_receipt","household_tablet","loading_record"}:
            raise ValueError("This conversation topic is not available.")
        own={e.predicate for e in self.remembered(recipient) if e.subject=="cart"}
        if topic=="documents":
            topic=next((key for key in ("market_receipt","household_tablet","loading_record") if key in own),"dispute")
        if topic in ("market_receipt","household_tablet"):
            if topic not in own: raise ValueError("This character does not retain that document.")
            if not self._record_known("Player",topic): return self._read_document(topic,recipient)
        if topic=="news":
            known=self.knowledge(recipient)
            if known["value"]!="unknown":
                exp=next(e for e in self.remembered(recipient) if e.event_id in known["evidence_ids"])
                root=exp.claimed_origin_event if exp.claimed_origin_event is not None else exp.event_id
                return self.event_dict(self._hear("Player",recipient,exp.value,exp.as_of,root,parents=(exp.event_id,),observer=exp.claimed_origin_observer or recipient))
            text="I have no current dispatch I can stand behind. Pay for an inspection, or ask someone who has seen it."
            parents=[]
        elif topic=="role": text=PERSONALITY[recipient]["role"];parents=[]
        elif topic in ("work","goals"):
            plan=self._plan(recipient)
            text=f"{plan['medium_term']}. For now, I must {plan['short_term']}."
            parents=plan["evidence_ids"]
        elif topic=="memory":
            revision=getattr(self,"_memory_presentation_revision",2)
            text=self._memory_line(recipient,revision)
            parents=[e.event_id for e in self._memory_support(recipient,revision)]
        elif topic=="loading_record" and not self._record_known("Player","loading_record"):
            if recipient!="Marcus": raise ValueError("This character does not hold the loading account.")
            text="My loading account stays closed until the check is paid for. One coin and fifteen minutes; then you can copy what it actually says."
            parents=[]
        elif topic in own:
            record=self._record_known(recipient,topic)
            text=record.text;parents=[record.event_id]
        else:
            text=self.context(recipient)["greeting"]["text"];parents=[]
        return self.event_dict(self._emit("conversation",f"You speak with {recipient} about {topic}",actors=("Player",recipient),scope="private",parents=parents,
            spoken_text=text,recalled=[text],topic=topic,grounding="retained records or authored role/offer only"))

    def _followup_title(self):
        return {"broker":"Marcus has a new account for a careful broker—and a grievance about your first bargain",
            "market":"Sabina offers a place at her counter; Lucius wants a replacement for the cart he lost",
            "household":"The household opens its account; Sabina asks what your advance cost her counter",
            "ignored":"Sabina's counter still needs help after the household took the cart",
            "unclaimed":"The cart dispute ended without a buyer; ordinary work still needs doing"}.get(self.arc.get("route"),"The street has another day's work")

    def buy_quote(self,recipient,quantity=1):
        """A public offer, without disclosing the seller's private accounts.

        This only reads current terms. Confirmation still checks location,
        funds, standing and stock in the unchanged authoritative transaction.
        """
        if recipient not in ("Felix","Marcus"):
            raise ValueError("This person is not selling flour.")
        if type(quantity) is not int or not 1<=quantity<=12:
            raise ValueError("quantity must be 1..12")
        unit_price=self.economy.price
        total=quantity*unit_price
        reason=""
        if self.state.trust.get((recipient,"Player"),.6)<.35:
            reason="This seller is not trading with you now."
        elif self.economy.cash["Player"]<total:
            reason=f"You need {total:g} coins for this order."
        elif (self.economy.inventory[recipient] if recipient=="Marcus" else self.economy.market_stock)<quantity:
            reason="This seller cannot fill that quantity now."
        return {"action":"buy","recipient":recipient,"quantity":quantity,"unit_price":unit_price,
            "total_cost":total,"currency":"coins","minute":self.minute,"available":not reason,"reason":reason}

    @staticmethod
    def _due_label(deadline):
        return f"Day {deadline//1440+1} · {(8+deadline//60)%24:02d}:{deadline%60:02d}"

    def choices(self,recipient):
        def choice(action,label,description,cost="",consequence="",enabled=True,reason="",quantity=None,terms=None):
            payload={"action":action,"recipient":recipient}
            if quantity is not None: payload["quantity"]=quantity
            return {"id":action,"label":label,"description":description,"cost":cost,"consequence":consequence,
                "action":payload,"enabled":bool(enabled),"reason":reason,**({"terms":copy.deepcopy(terms)} if terms is not None else {})}
        items=[];stage=self.arc.get("stage");open_arc=stage in ("unresolved","awaiting_stock")
        if recipient=="Sabina":
            if not self.arc.get("heard"): items.append(choice("hear_dispute","What happened to your order?","Hear Sabina's account before choosing a side."))
            if not self._record_known("Player","market_receipt"): items.append(choice("examine_receipt","Show me what you paid for","Copy the quantity and payment in Sabina's wax account.",consequence="Adds a dated piece of evidence."))
            if open_arc:
                items.append(choice("support_market","Stand behind the market","Pay the carrying charge and direct four sacks to Sabina and two to Felix.","3 coins","Household advance refunded; market work opens; Lucius loses priority.",self.economy.cash["Player"]>=3 and self.arc.get("cart_units",0)>=6,"Needs three coins and six arrived sacks."))
                if not self.arc.get("declined"): items.append(choice("decline_dispute","This is not my bargain","Let the buyers decide at their own deadline.",consequence="The world will settle the dispute without your choice."))
        if recipient=="Dama" and not self._record_known("Player","household_tablet"):
            items.append(choice("examine_tablet","What did the steward actually order?","Dama repeats the delivery instructions she was assigned to carry.",consequence="Adds the household's dated quantity."))
        if recipient=="Marcus" and open_arc:
            if not self._record_known("Player","loading_record"):
                items.append(choice("verify_cart","Open the loading account","Pay to check what the old ready notice did—and did not—promise.","1 coin · 15 minutes","Adds a checked loading record.",self.economy.cash["Player"]>=1,"Needs one coin."))
            known=all(self._record_known("Player",key) for key in ("market_receipt","household_tablet","loading_record"))
            items.append(choice("mediate","Put the two accounts together","Use the actual documents to bargain for four household sacks and two market sacks.","Three retained documents","Broker work opens; Marcus resents the scrutiny.",known and self.arc.get("cart_units",0)>=6,"Collect Sabina's receipt, Dama's instructions and Marcus's checked loading record."))
        if recipient=="Lucius" and open_arc:
            items.append(choice("guarantee_household","Put my name behind the household","Accept six coins against service and give the household the cart's priority.","120 minutes of service within three days","Household work opens; Sabina loses her supply and welcomes you less.",self.economy.cash["Lucius"]>=9 and self.flags.get("affiliation")=="independent" and self.arc.get("cart_units",0)>=6,"Needs an available household advance, carrying funds and arrived sacks."))
        if recipient=="Lucius" and self.arc.get("route")=="household" and not self.arc.get("service_done") and not self.arc.get("service_missed"):
            items.append(choice("return_service","Keep my service promise","Do the two hours you promised before taking another household account.","120 world minutes","Settles the institutional service obligation.",self.minute+120<self.arc["service_due"],"The shift must finish before the household deadline."))
        if recipient=="Lucius":
            inherited_service=next((c for c in self.economy.commitments["Player"] if c["id"]=="household-service" and c["status"]=="open"),None)
            if inherited_service:
                items.append(choice("service","Keep my earlier household service promise","Settle the service recorded in your earlier household account.",
                    "120 world minutes","Completes the existing household service commitment without taking another advance.",
                    self.minute+120<inherited_service["deadline"],"The shift must finish before the existing household deadline."))
        if recipient=="Felix" and self.flags.get("quest")=="active":
            inherited_delivery=next((c for c in self.economy.commitments["Player"] if c["id"]==self.flags.get("active_contract") and c["status"]=="open"),None)
            if inherited_delivery:
                needed=inherited_delivery["quantity"]
                items.append(choice("deliver","Keep my earlier flour promise",f"Bring the {needed} flour units already promised in Felix's open account.",
                    f"{needed} flour units from your bag","Settles the existing delivery and releases payment from Felix's available account.",
                    self.economy.inventory["Player"]>=needed,"Collect the flour you already promised before this account closes."))
        if self.arc.get("followup_ready") and not self.arc.get("followup_done"):
            target={"market":"Lucius","household":"Sabina","broker":"Marcus","ignored":"Sabina"}.get(self.arc.get("route"))
            if recipient==target:
                reason=""
                if recipient=="Lucius" and self.economy.cash["Player"]<3: reason="You need three coins for the replacement delivery."
                elif recipient=="Sabina" and self.economy.inventory["Player"]<2: reason="Bring two flour units in your own bag."
                elif recipient=="Marcus":
                    report=self.knowledge("Player")
                    if not report.get("direct") or self.minute-report["as_of"]>60:
                        reason="Bring a direct supply inspection no more than an hour old."
                items.append(choice("reconcile",{"Lucius":"Help replace the lost delivery","Sabina":"Bring something the counter can serve","Marcus":"Rebuild our working arrangement"}[recipient],
                    {"Lucius":"Contribute three coins to the household's replacement delivery.","Sabina":"Bring two flour units from your own bag.","Marcus":"Bring a direct supply inspection no more than an hour old."}[recipient],
                    {"Lucius":"3 coins","Sabina":"2 flour units","Marcus":"Fresh inspected report"}[recipient],"Repairs this specific grievance and changes future access.",not reason,reason))
        spec=COMMISSION_SPECS.get(recipient)
        if spec and spec["access"] in self.progression["access"] and self.arc.get("followup_ready"):
            active=next((c for c in self.commissions if c["recipient"]==recipient and c["status"]=="open"),None)
            if active:
                reason=""
                if self.minute>=active["deadline"]: reason="This commission's deadline has passed."
                elif active["kind"]=="goods" and self.economy.inventory["Player"]<active["quantity"]:
                    reason=f"Bring {active['quantity']} flour units in your own bag."
                elif active["kind"]=="evidence":
                    report=self.knowledge("Player")
                    if not report.get("direct") or report["as_of"]<active["accepted_at"]:
                        reason="Obtain a new direct inspection after accepting this commission."
                if not reason and self.economy.cash.get("CommissionEscrow",0)<active["reward"]:
                    reason="The reserved commission payment is unavailable."
                items.append(choice("fulfill_commission","Settle our commission",spec["description"]+f" Due by {self._due_label(active['deadline'])}.",
                    consequence=f"Receive the reserved {active['reward']} coins for actual fulfilment.",enabled=not reason,reason=reason,
                    terms={"deadline":active["deadline"],"reward":active["reward"]}))
            else:
                used=any(c["recipient"]==recipient and c["day"]==self.minute//1440 for c in self.commissions)
                service_ok=recipient!="Lucius" or not self._outstanding_household_service()
                has_credit=self.axes[recipient]["reliability"]>=.35 or self.axes[recipient]["favors"]>=1
                spending_favor=self.axes[recipient]["reliability"]<.35 and has_credit
                deadline=self.minute+spec["duration"]
                description=spec["description"]+f" Due within {spec['duration']} world minutes, by {self._due_label(deadline)}."
                items.append(choice("accept_commission",spec["title"],description,cost="One earned favor" if spending_favor else "A promise, with no advance",
                    consequence="A real deadline and reserved reward. An earned favor replaces the usual reliability requirement." if spending_favor else "A real deadline and reserved reward.",
                    enabled=not used and service_ok and self.economy.cash[recipient]>=spec["reward"] and has_credit and not any(c["status"]=="open" for c in self.commissions),
                    reason="One open commission and one account per day; available funds, service and reliability or an earned favor are required.",
                    terms={"deadline":deadline,"duration_minutes":spec["duration"],"reward":spec["reward"]}))
        if recipient in ("Sabina","Chreste"):
            payer="Sabina" if recipient=="Sabina" else "Lucius"
            wage=3 if recipient=="Sabina" else 4
            reason=""
            if recipient=="Sabina" and self.axes["Sabina"]["affinity"]<.35: reason="Repair your dealing with Sabina first."
            elif self.flags.get(f"work:{self.minute//1440}:{recipient}",0)>=2: reason="Today's extra work has already been taken."
            elif self.economy.cash[payer]<wage: reason="This account cannot fund another shift now."
            items.append(choice("work","Is there paid work here?","Take a real shift, paid from the counter or household account.","55 minutes" if recipient=="Sabina" else "80 minutes",f"The shift pays {wage} coins if funds remain available.",not reason,reason))
        if recipient in ("Felix","Marcus"):
            quote=self.buy_quote(recipient)
            items.append(choice("buy","Buy one flour unit","Trade one flour unit at the offered price.",f"{quote['total_cost']:g} coins",
                "One actual flour unit enters your bag.",quote["available"],quote["reason"],quantity=1,terms=quote))
        items.append(choice("inspect","Arrange a current supply inspection","Pay one coin; the result arrives after fifteen world minutes.","1 coin · 15 minutes","Obtain a direct dated observation.",self.economy.cash["Player"]>=1,"You need one coin to arrange an inspection."))
        if not self.flags.get(f"reflection:{recipient}:{self.minute//1440}"):
            items.append(choice("reflect","What do you remember of our dealings?","Recall selected retained shared experiences."))
        return self.v2_choices(recipient)+items

    def context(self,recipient):
        self.require_near(recipient)
        view=self.private_view(recipient)
        own_keys={e.predicate for e in self.remembered(recipient) if e.subject=="cart"}
        topics=[{"id":"role","label":"Your life here","text":PERSONALITY[recipient]["role"],"evidence_ids":[]},
            {"id":"goals","label":"What needs doing?","text":f"{view['plan']['medium_term']}. For now, I must {view['plan']['short_term']}.","evidence_ids":view["plan"]["evidence_ids"]},
            {"id":"memory","label":"Our history","text":self._memory_line(recipient),"evidence_ids":[e.event_id for e in self._recent_shared_memories(recipient)]}]
        known=self.knowledge(recipient)
        topics.append({"id":"news","label":"What have you heard?",
            "text":f"My retained dispatch says supply was {known['value']} at world minute {known['as_of']}. It is a dated report, not a promise about now." if known["value"]!="unknown" else "I have no current dispatch I can stand behind. Ask someone who inspected it, or pay for a check.",
            "evidence_ids":known["evidence_ids"]})
        for key in sorted(own_keys):
            record=self._record_known(recipient,key)
            withheld=key=="loading_record" and not self._record_known("Player",key)
            topics.append({"id":key,"label":{"market_receipt":"The counter's order","household_tablet":"The household instructions","loading_record":"The old dispatch and the carrying charge"}.get(key,key),
                "text":"The loading account stays closed until a paid check. One coin and fifteen minutes, then you may copy the terms." if withheld else record.text,
                "evidence_ids":[] if withheld else [record.event_id],"withheld":withheld})
        if self.arc.get("route")=="market" and self.arc.get("stage")=="resolved" and recipient=="Sabina":
            greeting="Four sacks arrived here, and two went to Felix. You got the counters supplied. Lucius may tell the story differently."
        elif self.arc.get("route")=="household" and recipient=="Sabina": greeting="My money came back. My customers did not. If you want another welcome, bring flour I can serve."
        elif self.arc.get("route")=="market" and recipient=="Lucius": greeting="You found a way to move the cart. You also chose whose account would wait. What do you propose for this house?"
        elif self.arc.get("route")=="broker" and recipient=="Marcus": greeting="You have an eye for quantities. Next time, remember the trader whose account you opened still has to earn."
        else: greeting=PERSONALITY[recipient]["opening"]
        market=self.v2_context(recipient)
        topics=market.get("topics",[])+topics
        return {**view,"speaker":recipient,"greeting":{"text":greeting,"evidence_ids":[]},"topics":topics,"choices":self.choices(recipient),
            "counter_order":{k:v for k,v in market.items() if k!="topics"},
            "relationship":copy.deepcopy(self.axes[recipient]),"dialogue_version":1,
            "disclosure_evidence_ids":sorted({identifier for topic in topics for identifier in topic["evidence_ids"]}),
            "plan_options":[{"id":"current_plan","label":view["plan"]["short_term"],"action":"continue_current_plan","reason":view["plan"]["reason"],"evidence_ids":view["plan"]["evidence_ids"]},
                {"id":"reconsider","label":"Reconsider using the same permitted records","action":"reconsider","reason":"New actions still need authoritative validation.","evidence_ids":view["plan"]["evidence_ids"]}]}

    def objective(self):
        if not self.arc: return super().objective()
        route=self.arc.get("route");stage=self.arc.get("stage")
        if stage in ("unresolved","awaiting_stock"):
            return {"id":"six-sacks","title":"Six sacks. Two promises.","status":stage,
                "description":"Sabina's counter and Lucius's household both claim the cart. Read their terms, pay for a different arrangement, or put your name behind one side.",
                "steps":[{"text":"Hear Sabina's account by the fountain","done":self.arc.get("heard",False)},
                    {"text":"Choose what your coins, evidence or promise will put first","done":False}],"deadline":self.arc["deadline"]}
        if not self.arc.get("followup_ready"):
            arrived=stage=="resolved"
            return {"id":"cart-consequence","title":"The cart has arrived" if arrived else "The cart is moving","status":"waiting",
                "description":"The flour has reached the agreed buyers. Give them a little time to take stock, then return to the people affected." if arrived else "Your arrangement has changed who receives the flour. Let a little time pass, then return to the people affected.","steps":[]}
        if route=="ignored" and not self.arc.get("followup_done"):
            return {"id":"a-counter-left-waiting","title":"The cart went on without you","status":"open",
                "description":"The buyers settled their own bargain. Sabina still needs two flour units she can serve; helping now can open a place at her counter.","steps":[]}
        if not self.arc.get("followup_done") and route in ("market","household","broker"):
            return {"id":"the-next-account","title":{"market":"The house that waited","household":"The empty counter","broker":"The price of opening an account"}[route],"status":"open",
                "description":{"market":"Lucius received his advance back, but lost the delivery. Return to the household and decide whether to help replace it.",
                    "household":"Sabina received her money back, but her counter lost its flour. You can bring two units and repair that consequence.",
                    "broker":"Marcus fulfilled both orders and paid your fee. A fresh checked report could rebuild a working arrangement."}[route],"steps":[]}
        return {"id":"your-place","title":"A name people can work with","status":"open","description":"Keep a commission, earn a shift, investigate a new report, or leave and see what the district does without you.","steps":[]}

    def snapshot(self,operator=False):
        snap=super().snapshot(operator=operator)
        market=self.v2_snapshot(operator=operator)
        snap["counter_market"]={k:v for k,v in market.items() if k!="operator"}
        snap["historical_note"]=HISTORICAL_DISCLAIMER
        snap["player"]["progression"]=copy.deepcopy(self.progression)
        snap["player"]["commissions"]=copy.deepcopy(self.commissions)
        snap["player"]["documents"]=[{"id":e.predicate,"title":self.documents[e.predicate]["title"],"text":e.text,"event_id":e.event_id,"as_of":e.as_of}
            for e in self.remembered("Player") if e.subject=="cart" and e.predicate in self.documents]
        for agent in snap["agents"]:
            agent["portrait"]=agent["id"].lower()
            agent["relationship"]=copy.deepcopy(self.axes[agent["id"]]) if operator or agent["nearby"] else None
            agent["activity"]={"Sabina":"waiting by her disputed order" if agent["location"]=="street" and self.arc.get("stage") in ("unresolved","awaiting_stock") else "working at the food counter",
                "Marcus":"minding the flour cart" if self.arc.get("stage") in ("unresolved","awaiting_stock","committed") else "keeping the trader's accounts",
                "Dama":"carrying household instructions","Felix":"keeping the bread counter","Lucius":"attending to household stores","Chreste":"working the fullery's cloth"}[agent["id"]]
            if agent["nearby"] or operator:
                agent["activity"]=market.get("business_activity",{}).get(agent["id"],agent["activity"])
            movement=self.npc_paths.get(agent["id"])
            if movement: agent.update(path=copy.deepcopy(movement["path"]),movement_event=movement["event_id"],movement_minute=movement["minute"])
        leads=[]
        if self.arc.get("stage") in ("unresolved","awaiting_stock"):
            for agent,key,location,label in (("Sabina","market_receipt",self.state.agent_locations["Sabina"],"Read the counter's receipt"),
                ("Dama","household_tablet",self.state.agent_locations["Dama"],"Ask Dama what the household ordered"),
                ("Marcus","loading_record",self.state.agent_locations["Marcus"],"Find out why the cart is waiting")):
                leads.append({"id":key,"recipient":agent,"location":location,"title":label,"done":bool(self._record_known("Player",key))})
            leads.append({"id":"household_offer","recipient":"Lucius","location":"household","title":"Hear the steward's offer","done":False})
        snap["story"]={"chapter":"The account at the fountain","title":"Six sacks. Two promises.","hook":"A cart waits while two buyers insist it is theirs.",
            "stage":self.arc.get("stage"),"route":self.arc.get("route"),"objective":self.objective(),"leads":leads,
            "deadline":self.arc.get("deadline"),"followup_ready":self.arc.get("followup_ready"),"followup_done":self.arc.get("followup_done"),
            "service_due":self.arc.get("service_due"),"service_done":self.arc.get("service_done"),"service_missed":self.arc.get("service_missed",False)}
        snap["opportunities"]=[]
        for recipient in self.agent_ids:
            if not operator and not self._near(recipient): continue
            for choice in self.choices(recipient):
                if choice["action"]["action"] in ("hear_dispute","mediate","support_market","guarantee_household","reconcile","accept_commission","return_service"):
                    snap["opportunities"].append({"id":f"{recipient}:{choice['id']}","title":choice["label"],"text":choice["description"],
                        "action":choice["action"],"enabled":choice["enabled"],"reason":choice["reason"]})
        if self.montage:
            visible=[self.event_dict(e) for e in self.ledger.events if e.tick>=self.montage["from_minute"] and self._visible(e) and
                e.payload.get("category") in ("rb_resolution","rb_service_kept","rb_service_missed","rb_commission_settled","rb_commission_missed","rb_opportunity","rb_reconcile")]
            snap["montage"]["events"]=(snap["montage"]["events"]+visible)[-10:]
        if operator:
            snap["operator"].update(story=copy.deepcopy(self.arc),relationships=copy.deepcopy(self.axes),plans=copy.deepcopy(self.plans),
                progression=copy.deepcopy(self.progression),commissions=copy.deepcopy(self.commissions),optimized=self.optimized,
                movement=copy.deepcopy(self._movement_state))
            if market.get("operator"):snap["operator"]["cognition_v2"]=market["operator"]
        return snap

    def metrics(self):
        metrics=super().metrics()
        metrics.update(rebirth_route=self.arc.get("route"),rebirth_stage=self.arc.get("stage"),commission_fulfilled=sum(c["status"]=="fulfilled" for c in self.commissions),
            commission_missed=sum(c["status"]=="missed" for c in self.commissions),relationship_axes=copy.deepcopy(self.axes),access=copy.deepcopy(self.progression["access"]))
        return metrics

    def fidelity_state(self):
        state=super().fidelity_state()
        state.update(rebirth={"arc":copy.deepcopy(self.arc),"axes":copy.deepcopy(self.axes),"progression":copy.deepcopy(self.progression),
            "commissions":copy.deepcopy(self.commissions),"plans":copy.deepcopy(self.plans),"documents":copy.deepcopy(self.documents),"npc_paths":copy.deepcopy(self.npc_paths)},
            witnessed=sorted(self.witnessed),disclosed=sorted(self.disclosed),queue=self.clock.snapshot())
        state["movement_v2"]=copy.deepcopy(self._movement_state)
        if self.v2_active():state["minds_v2"]=self.v2_fidelity()
        return state
