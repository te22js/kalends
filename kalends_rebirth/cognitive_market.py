"""A funded counter-order market driven by bounded, non-omniscient AgentMinds.

The mixin has no implicit boot hook. The host explicitly activates it in a
versioned accepted command, folds its event payloads after the normal ledger
projection, and forwards each *new legitimate per-agent Experience*. Existing
worlds therefore retain their original boot and replay until activation.

Money is transferred between actual accounts. Flour is moved into a batch
account and consumed only by a completed production event. An advance is part
of the six-coin price, not an extra reward; on default, delivered units are
credited at three coins before any debt is recorded. A late replacement repairs
the shortfall without paying the same reward twice.
"""
from __future__ import annotations

import copy
from dataclasses import asdict

from kalends.memory.base import Experience
from .minds import ActionOption, AgentMind, BeliefCondition, Episode, Goal, MindConfig, SocialCondition, SocialSignal


BUYERS = ("Felix", "Sabina")
ESCROW = "V2OrderEscrow"
SUPPLIER = "V2Wholesaler"
VERIFIER = "V2DispatchClerk"
V2_ACTIONS = frozenset({"v2_bonded_order", "v2_advance_order", "v2_cash_order", "v2_deliver_order",
    "v2_share_report", "v2_repay_order", "v2_replace_order"})
V2_FIXED_QUANTITIES = {"v2_cash_order":2,"v2_bonded_order":1,"v2_advance_order":1,"v2_share_report":1,"v2_repay_order":1}
ORDER_QUANTITY = 2
ORDER_PRICE = 6
UNIT_CREDIT = 3
BOND = 2
ADVANCE = 4
WINDOW = 240


def batch_account(buyer):
    return "V2Batch:" + buyer


class CognitiveMarketMixin:
    """Host calls the v2_* hooks; no original engine method is overridden here."""

    def v2_defaults(self):
        self.v2_market = None
        self.v2_minds = {}
        self._v2_initializing = False

    def v2_active(self):
        return isinstance(getattr(self,"v2_market",None),dict)

    def v2_fold_event(self, event, payload):
        if "v2_activation" in payload:
            activation=payload["v2_activation"]
            config=MindConfig(**activation["mind_config"])
            self.v2_market={"version":2,"activated_at":event.tick,"mind_config":asdict(config),
                "offers":{},"contracts":[],"activity":{},"decisions":[],"inspection_cycles":{},
                "queued":{},"last_shared":{},"completed_batches":{a:0 for a in BUYERS},"consumed_flour":0}
            self.v2_minds={a:AgentMind(a,config) for a in BUYERS}
        if not self.v2_active():
            return
        patch=payload.get("v2_market_patch",{})
        for key in ("offers","activity","inspection_cycles","queued","last_shared"):
            self.v2_market[key].update(copy.deepcopy(patch.get(key,{})))
        for contract in patch.get("contracts",[]):
            known=next((c for c in self.v2_market["contracts"] if c["id"]==contract["id"]),None)
            if known:known.update(copy.deepcopy(contract))
            else:self.v2_market["contracts"].append(copy.deepcopy(contract))
        unresolved=[c for c in self.v2_market["contracts"] if c["status"] in ("open","defaulted")]
        closed=[c for c in self.v2_market["contracts"] if c["status"] not in ("open","defaulted")][-8:]
        self.v2_market["contracts"]=sorted(unresolved+closed,key=lambda c:(c["accepted_at"],c["id"]))
        if "decision" in patch:
            self.v2_market["decisions"]=(self.v2_market["decisions"]+[copy.deepcopy(patch["decision"])])[-8:]
        self.v2_market["consumed_flour"]+=patch.get("consumed_flour",0)
        for buyer,amount in patch.get("completed_batches",{}).items():
            self.v2_market["completed_batches"][buyer]+=amount

    def v2_activate_minds(self, config=None):
        if self.v2_active():
            return None
        config=config if isinstance(config,MindConfig) else MindConfig(**(config or {}))
        self._v2_initializing=True
        event=self._emit("v2_activation","New counter orders put working coins and Aelia's word at stake",actors=("Player",),scope="private",
            v2_activation={"version":2,"mind_config":asdict(config)},fiction=True)
        if not self.v2_active():
            raise RuntimeError("The host must fold V2 payloads after emitting their authoritative event")
        # This is the one bootstrap. These are the agent's currently accessible
        # memories, not an archive scan or another person's private knowledge.
        for buyer in BUYERS:
            self.v2_minds[buyer].set_goals([Goal("counter-batch","Secure two flour units for an additional working batch",
                deadline=self.minute+1+WINDOW,relevant_keys=(("grain","supply"),("Player","offered_flour")),tags=("supply","credit"))])
            for experience in sorted(self.remembered(buyer),key=lambda e:(e.tick,e.event_id)):
                self.v2_admit_experience(buyer,experience)
        self._v2_initializing=False
        for buyer in BUYERS:
            self.clock.schedule(self.minute+1,"v2_market_cycle",{"buyer":buyer,"cycle":0})
        return self.event_dict(event)

    def v2_admit_experience(self, agent, experience):
        if not self.v2_active() or agent not in self.v2_minds:
            return False
        signals=()
        salient=.12
        tags=()
        if experience.kind in ("observed","told") and (experience.subject,experience.predicate) in (("grain","supply"),("Player","offered_flour")):
            episode=Episode.from_experience(agent,experience,salience=.65,goal_tags=("supply",))
        else:
            # An admitted communication can mention a kept bargain without
            # becoming this buyer's own credit history. Preserve that boundary
            # even when its structured fields resemble an authored receipt.
            personal=experience.kind in ("observed","episodic") and experience.accepted and experience.source_agent in (None,"Player")
            outcome=None
            if personal and (experience.subject,experience.predicate)==("v2_social","Player"):
                outcome=experience.value
            elif personal and experience.subject=="rebirth":
                outcome={"rb_commission_settled":"kept","rb_service_kept":"kept","rb_reconcile":"repaired",
                    "rb_commission_missed":"missed","rb_service_missed":"missed"}.get(experience.predicate)
            if outcome in ("kept","missed","repaired","repaid"):
                delta={"kept":.18,"missed":-.25,"repaired":.16,"repaid":.08}[outcome]
                signals=(SocialSignal("Player","reliability",delta),)
                salient=.95;tags=("credit",)
            # Non-propositional episodes retain their literal account. A rich
            # episode is not reclassified by guessing facts out of prose.
            episode=Episode(experience.event_id,agent,experience.tick,experience.kind,experience.text[:1024] or "An admitted personal experience.",
                participants=(agent,"Player") if signals else (),salience=salient,goal_tags=tags,social_signals=signals,
                source_agent=experience.source_agent,origin_event=experience.claimed_origin_event,
                origin_observer=experience.claimed_origin_observer,as_of=experience.as_of,accepted=bool(experience.accepted))
        added=self.v2_minds[agent].observe(episode)
        if added and not self._v2_initializing and (episode.key or signals):
            self._v2_queue_decision(agent)
        return added

    def _v2_queue_decision(self,buyer):
        offer=self.v2_market["offers"].get(buyer)
        if not offer or self.minute>=offer["deadline"] or self.v2_market["queued"].get(buyer):
            return
        self.v2_market["queued"][buyer]=True
        self.clock.schedule(self.minute+1,"v2_market_decide",{"buyer":buyer,"cycle":offer["cycle"]})

    def _v2_contract(self,buyer,status=None):
        records=[c for c in self.v2_market["contracts"] if c["buyer"]==buyer and (status is None or c["status"]==status)]
        return max(records,key=lambda c:c["accepted_at"]) if records else None

    def _v2_personal(self,buyer,event,outcome):
        self._remember(buyer,Experience(self.minute,"episodic","v2_social","Player",outcome,"Player",self.minute,True,
            event.event_id,event.payload["title"]),significant=True)

    def _v2_release_offer(self,buyer,reason):
        offer=self.v2_market["offers"].get(buyer)
        if not offer or not offer.get("reserved") or offer.get("status")!="offered":
            return
        amount=offer["reserved"]
        if self.economy.cash.get(ESCROW,0)<amount:
            raise ValueError("The order's reserved reward is not funded")
        self._emit("v2_offer_released",f"{buyer} releases the unaccepted order's reserved coins: {reason}",actors=(buyer,),scope="private",
            parents=(offer.get("event_id"),),cash_delta={ESCROW:-amount,buyer:amount},
            v2_market_patch={"offers":{buyer:{**offer,"reserved":0,"status":"withdrawn"}}})

    def _v2_decide(self,buyer,cycle,*,offered_goods=False):
        offer=self.v2_market["offers"].get(buyer)
        if not offer or offer["cycle"]!=cycle or self.minute>=offer["deadline"]:
            return None
        self.v2_market["queued"][buyer]=False
        if self._v2_contract(buyer,"open") or offer["status"] in ("fulfilled","closed"):
            return None
        mind=self.v2_minds[buyer]
        mind.set_goals([Goal("counter-batch","Secure two flour units for an additional working batch",priority=1.1 if buyer=="Felix" else 1,
            deadline=offer["deadline"],relevant_keys=(("grain","supply"),("Player","offered_flour")),tags=("supply","credit"))])
        # Both corroboration and directness are checked inside choose's one
        # shared context. A separate belief query could see a direct record
        # which the actual decision context has displaced with social history.
        supply=(BeliefCondition("grain","supply","available",min_sources=2,max_age=120,allow_direct=True),)
        blocked=self._v2_contract(buyer,"defaulted") is not None
        cash=self.economy.cash[buyer]+(offer.get("reserved",0) if offer["status"]=="offered" else 0)
        resources={"coins":cash,"credit_capacity":0 if blocked else 1,"trading_capacity":0 if blocked else 1}
        options=[ActionOption("advance","Offer an advance against the completed order",8 if buyer=="Sabina" else 7,goal_id="counter-batch",
            costs={"coins":ORDER_PRICE,"credit_capacity":1},conditions=supply,
            social_conditions=(SocialCondition("Player","reliability",minimum=.6 if buyer=="Sabina" else .65),)),
            ActionOption("bonded","Reserve a completion price against a cash bond",4,goal_id="counter-batch",costs={"coins":ORDER_PRICE,"trading_capacity":1},
                conditions=(BeliefCondition("grain","supply","available",max_age=180),)),
            ActionOption("defer","Protect working coins until an order is feasible",0)]
        if offered_goods:
            options.append(ActionOption("cash","Buy the physically presented two-unit lot",9,goal_id="counter-batch",costs={"coins":ORDER_PRICE,"trading_capacity":1},
                conditions=(BeliefCondition("Player","offered_flour","2",max_age=0),)))
        inspected=self.v2_market["inspection_cycles"].get(buyer)==cycle
        if not inspected and not offered_goods:
            options.append(ActionOption("verify","Pay for a direct current dispatch inspection",2,goal_id="counter-batch",costs={"coins":1}))
        decision=mind.choose(options,own_resources=resources,now=self.minute)
        record={"buyer":buyer,"cycle":cycle,"minute":self.minute,"decision":asdict(decision)}
        event=self._emit("v2_cognitive_decision",f"{buyer} chooses {decision.action_id or 'defer'} from retained evidence and working resources",actors=(buyer,),scope="private",
            parents=decision.evidence_ids,v2_market_patch={"decision":record})
        selected=decision.action_id
        if selected in ("bonded","advance","cash"):
            mode="advance" if selected=="advance" else "bonded"
            if offer["status"]=="offered" and offer.get("reserved")==ORDER_PRICE:
                updated={**offer,"mode":mode,"decision_event":event.event_id}
                self._emit("v2_offer_posted",f"{buyer} {'will advance four coins' if mode=='advance' else 'asks for a two-coin bond'} on a six-coin order",actors=(buyer,),scope="public",
                    parents=(event.event_id,),v2_market_patch={"offers":{buyer:updated},"activity":{buyer:"taking a two-unit counter order"}})
            else:
                if self.economy.cash[buyer]<ORDER_PRICE:
                    raise ValueError("The buyer cannot reserve this order's six-coin price")
                updated={**offer,"mode":mode,"status":"offered","reserved":ORDER_PRICE,"decision_event":event.event_id,"event_id":len(self.ledger)}
                self._emit("v2_offer_posted",f"{buyer} reserves six working coins for two flour units; {'four can be advanced' if mode=='advance' else 'a two-coin bond is required'}",actors=(buyer,),scope="public",
                    parents=(event.event_id,),cash_delta={buyer:-ORDER_PRICE,ESCROW:ORDER_PRICE},
                    v2_market_patch={"offers":{buyer:updated},"activity":{buyer:"taking a two-unit counter order"}})
        elif selected=="verify":
            self._v2_release_offer(buyer,"checking the dispatch before committing")
            if self.economy.cash[buyer]<1:
                raise ValueError("The buyer cannot pay the dispatch clerk")
            booking=self._emit("v2_verification_booked",f"{buyer} pays a dispatch clerk and waits for a current inspection",actors=(buyer,),scope="public",
                parents=(event.event_id,),cash_delta={buyer:-1,VERIFIER:1},v2_market_patch={"inspection_cycles":{buyer:cycle},"activity":{buyer:"checking a dispatch before opening an extra batch"}})
            self.clock.schedule(self.minute+15,"v2_market_inspection",{"buyer":buyer,"cycle":cycle,"parent":booking.event_id})
        else:
            self._v2_release_offer(buyer,"the retained reports do not support the risk")
            self._emit("v2_order_deferred",f"{buyer} holds the extra batch rather than spend on an unsupported promise",actors=(buyer,),scope="public",
                v2_market_patch={"activity":{buyer:"holding an extra batch for lack of dependable terms"}})
        return selected

    def v2_on_task(self,kind,data):
        if not self.v2_active() or not kind.startswith("v2_market_"):
            return False
        buyer=data.get("buyer")
        if buyer not in BUYERS:
            raise ValueError("Unknown counter-order buyer")
        cycle=data.get("cycle",0)
        if kind=="v2_market_cycle":
            if not self._v2_contract(buyer,"open"):
                start=self.minute
                offer={"buyer":buyer,"cycle":cycle,"opened_at":start,"deadline":start+WINDOW,"status":"considering","mode":None,"reserved":0,"event_id":len(self.ledger)}
                self._emit("v2_counter_need",f"{buyer} opens a working window for two additional flour units",actors=(buyer,),scope="public",
                    v2_market_patch={"offers":{buyer:offer},"activity":{buyer:"planning an additional working batch"}})
                self.clock.schedule(start+WINDOW,"v2_market_close",{"buyer":buyer,"cycle":cycle})
                self._v2_decide(buyer,cycle)
            self.clock.schedule(self.minute+1440,"v2_market_cycle",{"buyer":buyer,"cycle":cycle+1})
        elif kind=="v2_market_decide":
            self._v2_decide(buyer,cycle)
        elif kind=="v2_market_inspection":
            event=self._emit("v2_dispatch_checked",f"{buyer} receives a direct current dispatch inspection",actors=(buyer,),scope="private",
                parents=(data.get("parent"),),value=self.state.facts.get("grain.supply","unknown"),as_of=self.minute)
            value=event.payload["value"]
            if value in ("available","disrupted"):
                self._observe(buyer,value,event.event_id,self.minute)
            self._v2_decide(buyer,cycle)
        elif kind=="v2_market_close":
            offer=self.v2_market["offers"].get(buyer)
            if not offer or offer["cycle"]!=cycle:
                return True
            contract=self._v2_contract(buyer,"open")
            if contract and contract["cycle"]==cycle:
                self._v2_default(contract)
            else:
                self._v2_release_offer(buyer,"the unaccepted working window ended")
                self._v2_self_supply(buyer,cycle)
        else:
            return False
        return True

    def _v2_self_supply(self,buyer,cycle):
        offer=self.v2_market["offers"].get(buyer)
        if not offer or offer["cycle"]!=cycle or offer["status"]=="fulfilled":
            return
        stock=self.economy.inventory.get(batch_account(buyer),0)
        needed=max(0,ORDER_QUANTITY-stock)
        filled=min(needed,self.economy.market_stock,max(0,int(self.economy.cash[buyer]//self.economy.price)))
        if filled:
            cost=round(filled*self.economy.price,2)
            event=self._emit("v2_self_supply",f"{buyer} buys {filled} flour units for the batch after no agreement arrives",actors=(buyer,),scope="public",
                cash_delta={buyer:-cost,SUPPLIER:cost},inventory_delta={batch_account(buyer):filled},market_stock_delta=-filled,
                v2_market_patch={"offers":{buyer:{**offer,"status":"closed","reserved":0}},"activity":{buyer:"procuring flour without Aelia"}})
            if stock+filled>=ORDER_QUANTITY:self._v2_finish_batch(buyer,event.event_id)
        else:
            self._emit("v2_batch_shortfall",f"{buyer}'s extra batch stays closed: no affordable flour arrived",actors=(buyer,),scope="public",
                v2_market_patch={"offers":{buyer:{**offer,"status":"closed","reserved":0}},"activity":{buyer:"extra batch closed for lack of affordable flour"}})

    def _v2_finish_batch(self,buyer,parent):
        account=batch_account(buyer)
        if self.economy.inventory.get(account,0)<ORDER_QUANTITY:
            return None
        return self._emit("v2_batch_ready",f"{buyer} uses the delivered flour and opens an additional {'bread batch' if buyer=='Felix' else 'counter service'}",actors=(buyer,),scope="public",
            parents=(parent,),inventory_delta={account:-ORDER_QUANTITY},consumed=ORDER_QUANTITY,
            v2_market_patch={"completed_batches":{buyer:1},"consumed_flour":ORDER_QUANTITY,"activity":{buyer:"baking an additional bread batch" if buyer=="Felix" else "serving an additional food-counter batch"}})

    def _v2_accept(self,buyer,mode):
        offer=self.v2_market["offers"].get(buyer)
        if not offer or offer["status"]!="offered" or self.minute>=offer["deadline"]:
            raise ValueError("This working order is not currently open")
        if self._v2_contract(buyer,"open") or self._v2_contract(buyer,"defaulted"):
            raise ValueError("Settle or repair the existing order with this buyer first")
        if mode=="advance" and offer["mode"]!="advance":
            raise ValueError("The buyer requires a cash bond on the currently disclosed terms")
        if mode=="bonded" and self.economy.cash["Player"]<BOND:
            raise ValueError("The completion bargain needs a two-coin bond")
        if offer.get("reserved")!=ORDER_PRICE or self.economy.cash.get(ESCROW,0)<ORDER_PRICE:
            raise ValueError("The buyer's completion price is not actually reserved")
        advance=ADVANCE if mode=="advance" else 0
        bond=BOND if mode=="bonded" else 0
        identifier=f"v2:{buyer}:{offer['cycle']}"
        contract={"id":identifier,"buyer":buyer,"cycle":offer["cycle"],"mode":mode,"quantity":ORDER_QUANTITY,"delivered":0,
            "price":ORDER_PRICE,"unit_credit":UNIT_CREDIT,"advance":advance,"bond":bond,"escrow":ORDER_PRICE-advance+bond,
            "debt":0,"status":"open","accepted_at":self.minute,"deadline":offer["deadline"],"event_id":len(self.ledger)}
        event=self._emit("v2_order_accepted",f"You accept {buyer}'s two-unit order {'with a four-coin advance' if advance else 'against a two-coin bond'}",actors=("Player",buyer),scope="private",
            parents=(offer["event_id"],),cash_delta={"Player":advance-bond,ESCROW:bond-advance},
            owner="Player",new_commitment={"id":identifier,"beneficiary":buyer,"quantity":ORDER_QUANTITY,"fulfilled":0,"deadline":offer["deadline"],"status":"open","event_id":len(self.ledger)},
            v2_market_patch={"contracts":[contract],"offers":{buyer:{**offer,"reserved":0,"status":"accepted"}},"activity":{buyer:"waiting for Aelia's promised two-unit delivery"}})
        return self.event_dict(event)

    def _v2_deliver(self,buyer,quantity):
        contract=self._v2_contract(buyer,"open")
        if not contract or self.minute>=contract["deadline"]:
            raise ValueError("There is no open order that can still be kept")
        remaining=contract["quantity"]-contract["delivered"]
        if quantity>remaining:
            raise ValueError(f"Only {remaining} flour units remain on this order")
        if self.economy.inventory["Player"]<quantity:
            raise ValueError("Bring the actual flour units before delivering")
        complete=quantity==remaining
        payment=contract["escrow"] if complete else 0
        if self.economy.cash.get(ESCROW,0)<payment:
            raise ValueError("The promised completion payment is not funded")
        updated={**contract,"delivered":contract["delivered"]+quantity,"status":"fulfilled" if complete else "open","escrow":0 if complete else contract["escrow"]}
        event=self._emit("v2_order_kept" if complete else "v2_order_partial",f"You {'complete' if complete else 'partly supply'} {buyer}'s order with {quantity} actual flour units",actors=("Player",buyer),scope="private",
            parents=(contract["event_id"],),inventory_delta={"Player":-quantity,batch_account(buyer):quantity},cash_delta={ESCROW:-payment,"Player":payment},
            commitment_updates=[{"agent":"Player","id":contract["id"],"fulfilled":updated["delivered"],"status":updated["status"]}],
            relationship_axes=[self._axis_change(buyer,reliability=.18,competence=.1)] if complete else [],
            v2_market_patch={"contracts":[updated],"offers":{buyer:{**self.v2_market["offers"][buyer],"status":"fulfilled" if complete else "accepted"}}})
        if complete:
            self._v2_personal(buyer,event,"kept");self._v2_finish_batch(buyer,event.event_id)
        return self.event_dict(event)

    def _v2_default(self,contract):
        buyer=contract["buyer"];earned=contract["delivered"]*UNIT_CREDIT
        owed=max(0,contract["advance"]-earned)
        earned_payment=max(0,earned-contract["advance"])
        refund=contract["escrow"]-earned_payment
        if refund<0 or self.economy.cash.get(ESCROW,0)<contract["escrow"]:
            raise ValueError("The order's default settlement is not funded")
        updated={**contract,"status":"defaulted","debt":owed,"escrow":0,"missed_at":self.minute}
        event=self._emit("v2_order_missed",f"{buyer} closes the late order: {contract['delivered']}/2 units arrived; {owed:g} advance coins remain owed",actors=("Player",buyer),scope="private",
            parents=(contract["event_id"],),cash_delta={ESCROW:-contract["escrow"],"Player":earned_payment,buyer:refund},
            commitment_updates=[{"agent":"Player","id":contract["id"],"status":"missed","fulfilled":contract["delivered"]}],
            relationship_axes=[self._axis_change(buyer,reliability=-.25,affinity=-.08)],
            v2_market_patch={"contracts":[updated],"offers":{buyer:{**self.v2_market["offers"][buyer],"status":"closed"}},
                "activity":{buyer:"an extra batch is short after Aelia's missed order"}})
        self._v2_personal(buyer,event,"missed")

    def _v2_recover(self,buyer,quantity,*,repay=False):
        contract=self._v2_contract(buyer,"defaulted")
        if not contract:
            raise ValueError("There is no failed order to repair here")
        if repay:
            amount=contract["debt"]
            if amount<=0:
                raise ValueError("No advance coins remain owed; replace the missing flour instead")
            if self.economy.cash["Player"]<amount:
                raise ValueError(f"Repayment requires {amount:g} actual coins")
            updated={**contract,"debt":0,"status":"repaid","repaired_at":self.minute}
            event=self._emit("v2_advance_repaid",f"You repay {buyer} the {amount:g} advance coins not covered by delivered flour",actors=("Player",buyer),scope="private",
                parents=(contract["event_id"],),cash_delta={"Player":-amount,buyer:amount},relationship_axes=[self._axis_change(buyer,reliability=.08)],
                commitment_updates=[{"agent":"Player","id":contract["id"],"repaired":True,"repair_kind":"repayment"}],
                v2_market_patch={"contracts":[updated],"activity":{buyer:"the advance is repaid; the missed batch remains part of the account"}})
            self._v2_personal(buyer,event,"repaid")
        else:
            remaining=contract["quantity"]-contract["delivered"]
            if quantity>remaining or self.economy.inventory["Player"]<quantity:
                raise ValueError("Replace only missing units, using actual flour in your bag")
            delivered=contract["delivered"]+quantity;complete=delivered==contract["quantity"]
            replacements=contract.get("replacement_units",0)+quantity
            updated={**contract,"delivered":delivered,"replacement_units":replacements,"debt":max(0,contract["debt"]-quantity*UNIT_CREDIT),
                "status":"repaired" if complete else "defaulted",**({"repaired_at":self.minute} if complete else {})}
            event=self._emit("v2_order_repaired",f"You replace {quantity} missing flour units for {buyer}; no second reward is paid",actors=("Player",buyer),scope="private",
                parents=(contract["event_id"],),inventory_delta={"Player":-quantity,batch_account(buyer):quantity},
                relationship_axes=[self._axis_change(buyer,reliability=.16,affinity=.06)] if complete else [],
                commitment_updates=[{"agent":"Player","id":contract["id"],"repaired":complete,"replacement_units":replacements}],
                v2_market_patch={"contracts":[updated],"activity":{buyer:"replacement flour has arrived after the missed order"}})
            if complete:
                self._v2_personal(buyer,event,"repaired");self._v2_finish_batch(buyer,event.event_id)
        return self.event_dict(event)

    def v2_interact(self,action,recipient,quantity=1):
        if not self.v2_active() or action not in V2_ACTIONS:
            raise ValueError("This cognitive market action is not active")
        if recipient not in BUYERS:
            raise ValueError("Ask Felix or Sabina about their counter orders")
        if type(quantity) is not int or not 1<=quantity<=12:
            raise ValueError("quantity must be1..12")
        if action in V2_FIXED_QUANTITIES and quantity!=V2_FIXED_QUANTITIES[action]:
            raise ValueError("This counter action requires quantity "+str(V2_FIXED_QUANTITIES[action]))
        self.require_near(recipient)
        if action in ("v2_bonded_order","v2_advance_order"):
            return self._v2_accept(recipient,"advance" if action=="v2_advance_order" else "bonded")
        if action=="v2_deliver_order":return self._v2_deliver(recipient,quantity)
        if action=="v2_repay_order":return self._v2_recover(recipient,quantity,repay=True)
        if action=="v2_replace_order":return self._v2_recover(recipient,quantity)
        if action=="v2_share_report":
            offer=self.v2_market["offers"].get(recipient)
            if not offer or self.minute>=offer["deadline"] or offer["status"] not in ("considering","offered","withdrawn"):
                raise ValueError("No open counter window needs this inspection")
            retained=[e for e in self.remembered("Player") if e.kind=="observed" and e.subject=="grain" and e.predicate=="supply" and e.accepted and self.minute-e.as_of<=120]
            if not retained:raise ValueError("Obtain an actual direct supply inspection no more than two hours old")
            report=max(retained,key=lambda e:(e.as_of,e.tick,e.event_id))
            if self.v2_market["last_shared"].get(recipient)==report.event_id:
                raise ValueError("This buyer has already received that inspection")
            event=self._hear(recipient,"Player",report.value,report.as_of,report.event_id,parents=(report.event_id,),observer="Player")
            self._emit("v2_report_shared",f"You let {recipient} reconsider the order using your actual dated inspection",actors=("Player",recipient),scope="private",
                parents=(event.event_id,report.event_id),v2_market_patch={"last_shared":{recipient:report.event_id}})
            self._v2_decide(recipient,self.v2_market["offers"].get(recipient,{}).get("cycle",0))
            return self.event_dict(event)
        if action=="v2_cash_order":
            offer=self.v2_market["offers"].get(recipient)
            if not offer or self.minute>=offer["deadline"] or offer["status"] in ("accepted","fulfilled","closed"):
                raise ValueError("The buyer has no open batch window for this lot")
            if self._v2_contract(recipient,"open") or self._v2_contract(recipient,"defaulted"):
                raise ValueError("Keep or repair the existing order before selling another lot")
            if self.economy.inventory["Player"]<ORDER_QUANTITY:
                raise ValueError("Bring two actual flour units to sell for cash")
            available=self.economy.cash[recipient]+(offer.get("reserved",0) if offer["status"]=="offered" else 0)
            if available<ORDER_PRICE:raise ValueError("The buyer cannot pay six coins for this lot")
            proof=self._emit("v2_goods_presented",f"You physically present two flour units to {recipient}",actors=("Player",recipient),scope="private")
            self._remember(recipient,Experience(self.minute,"observed","Player","offered_flour","2",None,self.minute,True,proof.event_id,
                "I directly saw Aelia present two flour units."))
            if self._v2_decide(recipient,offer["cycle"],offered_goods=True)!="cash":
                raise ValueError("The buyer's retained evidence does not authorize this cash purchase")
            current=self.v2_market["offers"][recipient]
            if self.economy.cash.get(ESCROW,0)<ORDER_PRICE:raise ValueError("The cash price is not funded")
            event=self._emit("v2_cash_trade",f"You sell two actual flour units to {recipient} for six coins",actors=("Player",recipient),scope="private",
                parents=(proof.event_id,current["event_id"]),cash_delta={ESCROW:-ORDER_PRICE,"Player":ORDER_PRICE},inventory_delta={"Player":-ORDER_QUANTITY,batch_account(recipient):ORDER_QUANTITY},
                v2_market_patch={"offers":{recipient:{**current,"status":"fulfilled","reserved":0}}})
            self._v2_finish_batch(recipient,event.event_id)
            return self.event_dict(event)
        raise ValueError("Unknown cognitive market action")

    def v2_choices(self,recipient):
        if not self.v2_active() or recipient not in BUYERS:return []
        offer=self.v2_market["offers"].get(recipient);contract=self._v2_contract(recipient,"open");failed=self._v2_contract(recipient,"defaulted")
        choices=[]
        def add(action,label,description,cost,*,enabled=True,reason="",quantity=1,consequence="",terms=None,choice_id=None):
            choices.append({"id":choice_id or action,"label":label,"description":description,"cost":cost,"consequence":consequence,
                "enabled":bool(enabled),"reason":reason,"action":{"action":action,"recipient":recipient,"quantity":quantity},"terms":terms or {}})
        if contract:
            remaining=contract["quantity"]-contract["delivered"]
            unit="unit" if remaining==1 else "units"
            add("v2_deliver_order",f"Bring the remaining {remaining} flour {unit}",f"Keep this order by {self._due_label(contract['deadline'])}. Completion settles the reserved balance and bond.",
                f"{remaining} actual flour {unit}",quantity=remaining,enabled=self.economy.inventory["Player"]>=remaining and self.minute<contract["deadline"],
                reason="Bring the actual missing flour before the deadline.",terms=copy.deepcopy(contract),consequence="No interim payment; partial delivery is credited at three coins per unit if the deadline is missed.")
            if remaining>1:
                add("v2_deliver_order","Deliver one flour unit now","Make a real partial delivery. The completion balance stays reserved until the entire order arrives on time.",
                    "1 actual flour unit",quantity=1,enabled=self.economy.inventory["Player"]>=1 and self.minute<contract["deadline"],
                    reason="Bring at least one actual flour unit before the deadline.",choice_id="v2_deliver_one")
        elif failed:
            remaining=failed["quantity"]-failed["delivered"]
            if remaining:
                unit="unit" if remaining==1 else "units"
                add("v2_replace_order",f"Replace the {remaining} missing flour {unit}","Repair the missed batch without another reward. Late units cancel advance debt at three coins each; the original deadline stays missed.",
                    f"{remaining} actual flour {unit}",quantity=remaining,enabled=self.economy.inventory["Player"]>=remaining,reason="Bring the actual replacement flour.")
                if remaining>1:
                    add("v2_replace_order","Replace one missing unit now","Begin repairing the shortfall with actual goods. There is no new reward, and advance debt falls by up to three coins.",
                        "1 actual flour unit",quantity=1,enabled=self.economy.inventory["Player"]>=1,reason="Bring at least one actual replacement unit.",choice_id="v2_replace_one")
            if failed["debt"]:
                add("v2_repay_order",f"Repay {failed['debt']:g} advance coins","Settle the unfunded part of the advance. Repayment repairs the financial account, not the missed batch.",
                    f"{failed['debt']:g} coins",enabled=self.economy.cash["Player"]>=failed["debt"],reason="Earn enough coins to cover the remaining advance.")
        elif offer and self.minute<offer["deadline"] and offer["status"] not in ("accepted","fulfilled","closed"):
            if offer["status"]=="offered":
                action="v2_advance_order" if offer["mode"]=="advance" else "v2_bonded_order"
                description=f"Two flour units by {self._due_label(offer['deadline'])}; total price six coins. "
                description+="Four coins now, two only on full timely completion. Undelivered advance becomes repayable debt, after crediting actual delivered units at three coins each." if offer["mode"]=="advance" else "Post two coins now. Six coins plus your two-coin bond return on timely completion. Missing the deadline forfeits the bond; actual partial delivery is valued at three coins per unit."
                add(action,"Take the funded advance" if offer["mode"]=="advance" else "Back the order with a cash bond",description,
                    "Receive 4 coins now; 2 on completion" if offer["mode"]=="advance" else "2-coin bond · 6-coin completion price",enabled=offer["mode"]=="advance" or self.economy.cash["Player"]>=BOND,
                    reason="The bond requires two coins.",terms={"deadline":offer["deadline"],"quantity":2,"price":6,"advance":4 if offer["mode"]=="advance" else 0,"bond":0 if offer["mode"]=="advance" else 2})
            funded=self.economy.cash[recipient]+(offer.get("reserved",0) if offer["status"]=="offered" else 0)>=ORDER_PRICE
            add("v2_cash_order","Sell two flour units now","Offer actual goods for the six-coin cash price, without a future promise or bond.","2 actual flour units → 6 coins",
                enabled=self.economy.inventory["Player"]>=2 and funded,reason="Bring two actual flour units." if funded else "The buyer cannot fund this six-coin price now.",quantity=2)
        if offer and offer["status"] in ("considering","offered","withdrawn") and self.minute<offer["deadline"] and not contract and not failed:
            direct=[e for e in self.remembered("Player") if e.kind=="observed" and e.subject=="grain" and e.predicate=="supply" and e.accepted and self.minute-e.as_of<=120]
            fresh=max(direct,key=lambda e:(e.as_of,e.event_id)) if direct else None
            add("v2_share_report","Show my actual dispatch inspection","Share a retained direct inspection so the buyer can reconsider. Repetition is not a new independent source.","No fee; actual retained inspection required",
                enabled=bool(fresh and self.v2_market["last_shared"].get(recipient)!=fresh.event_id),reason="Arrange a fresh direct inspection first, or obtain a different one.")
        return choices

    def v2_context(self,recipient):
        if not self.v2_active() or recipient not in BUYERS:return {}
        offer=self.v2_market["offers"].get(recipient)
        contract=self._v2_contract(recipient,"open") or self._v2_contract(recipient,"defaulted")
        latest=self._v2_contract(recipient)
        if contract:
            text=f"Your order: {contract['delivered']}/2 flour units, due by {self._due_label(contract['deadline'])}. "
            if contract["status"]=="defaulted":
                if contract["mode"]=="bonded":
                    text+=f"The {contract['bond']:g}-coin bond was forfeited. No advance coins remain owed; replace the missing flour to repair the batch. The original deadline stays missed."
                else:text+=f"The missed advance still leaves {contract['debt']:g} coins owed." if contract["debt"] else "The deadline stays missed. No advance coins remain owed; replace the missing flour to repair the batch."
            else:text+="Bring the actual goods; your reserved terms stay in force."
        elif offer and offer["status"]=="fulfilled":
            text="The two flour units arrived and the six-coin price is settled. "
            if latest and latest["cycle"]==offer["cycle"] and latest["status"]=="fulfilled":
                text+="Your two-coin bond has also been returned. " if latest["bond"] else "The remaining two coins have been paid. "
                text+="A kept order supports our dealings; future credit also depends on what I retain and a fresh dispatch."
            else:text+="That cash sale is complete; there is no future delivery or bond to settle."
        elif offer and offer["status"]=="offered":
            text="I can advance four of the six coins because my retained reports and our dealings support the risk." if offer["mode"]=="advance" else "I have reserved six coins for two flour units. Until I have dependable experience with you, I need a two-coin bond—or bring the goods now."
        elif latest and latest["status"]=="repaired" and (not offer or latest["cycle"]==offer["cycle"]):
            text="The replacement flour has arrived. No second reward is due, and the original deadline stays missed. Future credit depends on the dealings I retain and a fresh dispatch."
        elif latest and latest["status"]=="repaid" and (not offer or latest["cycle"]==offer["cycle"]):
            text="The advance has been repaid. The financial account is settled; the missed batch remains part of our dealings. Future credit still needs dependable retained history and a fresh dispatch."
        else:text="My extra batch depends on affordable flour and dependable terms. I will not turn an old dispatch into a fresh guarantee."
        return {"topics":[{"id":"v2_counter_order","label":"The next working batch","text":text,"evidence_ids":[]}],
            "offer":{k:copy.deepcopy(offer[k]) for k in ("buyer","deadline","status","mode") if offer and k in offer},
            "contract":copy.deepcopy(contract) if contract else None}

    def v2_snapshot(self,operator=False):
        if not self.v2_active():return {"active":False}
        public={"active":True,"version":2,"title":"Working coins, dated words", "contracts":copy.deepcopy(self.v2_market["contracts"]),
            "business_activity":copy.deepcopy(self.v2_market["activity"]),"completed_batches":copy.deepcopy(self.v2_market["completed_batches"]),
            "nearby_offers":[self.v2_context(a) for a in BUYERS if self._near(a)]}
        if operator:
            public["operator"]={"market":copy.deepcopy(self.v2_market),"minds":{a:m.inspect(now=self.minute) for a,m in self.v2_minds.items()}}
        return public

    def v2_fidelity(self):
        return {"market":copy.deepcopy(getattr(self,"v2_market",None)),"minds":{a:m.to_dict() for a,m in getattr(self,"v2_minds",{}).items()}}


def activate_minds_v2(world,config=None):return world.v2_activate_minds(config)
def hook_payload(world,event,payload):return world.v2_fold_event(event,payload)
def admit_experience(world,agent,experience):return world.v2_admit_experience(agent,experience)
def on_task_v2(world,kind,data):return world.v2_on_task(kind,data)
