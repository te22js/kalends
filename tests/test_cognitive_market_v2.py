"""The cognitive market runs through actual ledger, goods and cash projections."""
import pytest

from kalends.memory.base import Experience
from kalends_rebirth.cognitive_market import BUYERS, ESCROW, CognitiveMarketMixin, batch_account
from kalends_rebirth.minds import MindConfig
from kalends_rebirth.world import RebirthWorld


class _HookedMarketWorld(RebirthWorld):
    """Exactly the explicit hooks the root game will install, with no fake world."""
    def __init__(self,*args,**kwargs):
        self.v2_defaults();super().__init__(*args,**kwargs)

    def _emit(self,*args,**kwargs):
        event=super()._emit(*args,**kwargs)
        self.v2_fold_event(event,event.payload)
        return event

    def _remember(self,agent,experience,significant=False):
        super()._remember(agent,experience,significant)
        self.v2_admit_experience(agent,experience)

    def on_task(self,task):
        if not self.v2_on_task(task["kind"],task["data"]):super().on_task(task)


if issubclass(RebirthWorld,CognitiveMarketMixin):
    MarketWorld=RebirthWorld
else:
    class MarketWorld(CognitiveMarketMixin,_HookedMarketWorld):
        pass


def active(config=None):
    world=MarketWorld();world.v2_activate_minds(config);world.advance(20,"compress")
    return world


def near(world,name):
    if world._near(name):return
    location=world.state.agent_locations[name]
    if location in ("street","water","forum_access"):world.move(*world.positions[name])
    else:world.move(location=location)


def run(world,action,buyer="Felix",quantity=1):
    near(world,buyer)
    return world.v2_interact(action,buyer,quantity)


def cash(world):return round(sum(world.economy.cash.values()),8)
def flour(world):return sum(world.economy.inventory.values())+world.economy.market_stock+world.v2_market["consumed_flour"]


def buy(world,quantity):
    near(world,"Marcus");world.interact("buy","Marcus",quantity)


def test_inactive_boot_preserves_the_exact_original_ledger_and_has_no_new_tasks():
    a=MarketWorld();b=RebirthWorld()
    assert a.ledger.content_hash()==b.ledger.content_hash()
    assert a.clock.snapshot()==b.clock.snapshot()
    assert a.v2_snapshot()=={"active":False}


def test_independent_buyers_pay_for_inspections_and_reserve_real_offer_money_without_acceptance():
    w=MarketWorld();before=cash(w);w.v2_activate_minds();w.advance(20,"compress")
    assert cash(w)==before
    assert w.economy.cash["V2DispatchClerk"]==2
    assert w.economy.cash[ESCROW]==12
    assert all(w.v2_market["offers"][a]["mode"]=="bonded" for a in BUYERS)
    assert all(w.v2_minds[a].believe("grain","supply",now=w.minute).direct for a in BUYERS)
    assert not w.v2_market["contracts"]


def test_bonded_order_is_feasible_from_six_coins_and_full_delivery_pays_exactly_once():
    w=active();initial_cash=cash(w);initial_flour=flour(w)
    assert w.economy.cash["Player"]==6
    run(w,"v2_bonded_order")
    assert w.economy.cash["Player"]==4
    buy(w,2)
    assert w.economy.cash["Player"]==0 and w.economy.inventory["Player"]==2
    receipt=run(w,"v2_deliver_order",quantity=2)
    assert receipt["payload"]["category"]=="v2_order_kept"
    assert w.economy.cash["Player"]==8 and w.economy.inventory["Player"]==0
    assert w.v2_market["completed_batches"]["Felix"]==1
    assert w.economy.inventory[batch_account("Felix")]==0
    assert cash(w)==initial_cash and flour(w)==initial_flour
    assert w.v2_minds["Felix"].social("Player","reliability",now=w.minute)["value"]==.68
    accepted=w.ledger.content_hash()
    with pytest.raises(ValueError,match="open order"):
        run(w,"v2_deliver_order",quantity=2)
    assert w.ledger.content_hash()==accepted


def test_cash_stock_strategy_completes_the_same_real_batch_without_a_promise_or_bond():
    w=active();initial=cash(w);goods=flour(w)
    buy(w,2);assert w.economy.cash["Player"]==2
    result=run(w,"v2_cash_order",quantity=2)
    assert result["payload"]["category"]=="v2_cash_trade"
    assert w.economy.cash["Player"]==8 and not w.v2_market["contracts"]
    assert w.v2_market["completed_batches"]["Felix"]==1
    assert cash(w)==initial and flour(w)==goods
    assert w.v2_minds["Felix"].last_decision.action_id=="cash"


def test_partial_bonded_delivery_has_no_interim_payment_and_default_pays_only_earned_goods():
    w=active();initial=cash(w)
    run(w,"v2_bonded_order");buy(w,1);run(w,"v2_deliver_order",quantity=1)
    assert w.economy.cash["Player"]==2
    contract=w._v2_contract("Felix","open")
    w.advance(contract["deadline"]-w.minute,"compress")
    failed=w._v2_contract("Felix","defaulted")
    assert failed["delivered"]==1 and failed["debt"]==0 and failed["escrow"]==0
    assert w.economy.cash["Player"]==5 # 3 coin value for the delivered unit; bond forfeited.
    # Existing base-engine purchases burn coins, so inspect this new settlement's
    # explicit balanced transfers rather than pretending the old economy closed.
    event=next(e for e in reversed(w.ledger.events) if e.payload.get("category")=="v2_order_missed" and e.actors[-1]=="Felix")
    assert sum(event.payload["cash_delta"].values())==0
    assert event.payload["cash_delta"]=={ESCROW:-8,"Player":3,"Felix":5}


def earn_reliability(w,buyer="Felix"):
    run(w,"v2_bonded_order",buyer);buy(w,2);run(w,"v2_deliver_order",buyer,2)


def next_cycle(w):
    target=w.v2_market["activated_at"]+1441
    w.advance(max(0,target-w.minute),"compress")
    w.advance(20,"compress")


def test_kept_order_opens_actual_advance_terms_on_a_later_order():
    w=active();earn_reliability(w);next_cycle(w)
    assert w.v2_market["offers"]["Felix"]["mode"]=="advance"
    before=w.economy.cash["Player"]
    run(w,"v2_advance_order")
    assert w.economy.cash["Player"]==before+4
    contract=w._v2_contract("Felix","open")
    assert contract["advance"]==4 and contract["escrow"]==2


def test_partial_advance_default_credits_goods_before_creating_debt_and_repayment_is_real():
    w=active();earn_reliability(w);next_cycle(w);run(w,"v2_advance_order")
    buy(w,1);run(w,"v2_deliver_order",quantity=1)
    contract=w._v2_contract("Felix","open");w.advance(contract["deadline"]-w.minute,"compress")
    failed=w._v2_contract("Felix","defaulted")
    assert failed["debt"]==1 # 4 advanced minus one actually delivered unit valued at3.
    before=w.economy.cash["Player"];buyer_cash=w.economy.cash["Felix"]
    run(w,"v2_repay_order")
    assert w.economy.cash["Player"]==before-1 and w.economy.cash["Felix"]==buyer_cash+1
    assert w._v2_contract("Felix")["status"]=="repaid"
    institutional=next(c for c in w.economy.commitments["Player"] if c["id"]==failed["id"])
    assert institutional["status"]=="missed" and institutional["repaired"]


def test_failed_bond_can_be_repaired_with_actual_replacement_without_second_reward():
    w=active();run(w,"v2_bonded_order");contract=w._v2_contract("Felix","open")
    w.advance(contract["deadline"]-w.minute,"compress")
    buy(w,2);before=w.economy.cash["Player"]
    run(w,"v2_replace_order",quantity=2)
    assert w.economy.cash["Player"]==before
    assert w._v2_contract("Felix")["status"]=="repaired"
    assert w.v2_market["completed_batches"]["Felix"]==1


def test_ignored_offers_release_reserved_funds_and_buyers_act_without_a_quest():
    w=active();w.advance(221,"compress")
    assert not w.v2_market["contracts"] and w.economy.cash[ESCROW]==0
    assert all(w.v2_market["offers"][a]["status"]=="closed" for a in BUYERS)
    records=[e for e in w.ledger.events if e.payload.get("category") in ("v2_self_supply","v2_batch_shortfall")]
    assert {e.actors[0] for e in records}==set(BUYERS)
    for event in records:assert sum(event.payload.get("cash_delta",{}).values())==0


def test_personal_memory_retention_changes_later_funded_offers_under_identical_experiences():
    worlds=[active(MindConfig(capacity=8,context_records=4,retention_policy=policy,consolidation=consolidate))
        for policy,consolidate in (("hybrid",True),("recency",False))]
    for w in worlds:
        earn_reliability(w)
        # These are actual admitted private routine experiences, not a hidden
        # fact lookup or synthetic replacement of the old fulfilled record.
        for i in range(16):
            event=w._emit("v2_test_routine","Felix sorts an ordinary counter notice",actors=("Felix",),scope="private")
            w._remember("Felix",Experience(w.minute,"episodic",None,None,None,None,w.minute,True,event.event_id,event.payload["title"]))
        next_cycle(w)
    a,b=worlds
    assert a.economy.cash==b.economy.cash and a.economy.inventory==b.economy.inventory
    assert a.v2_market["offers"]["Felix"]["mode"]=="advance"
    assert b.v2_market["offers"]["Felix"]["mode"]=="bonded"
    before=[w.economy.cash["Player"] for w in worlds]
    run(a,"v2_advance_order");run(b,"v2_bonded_order")
    assert a.economy.cash["Player"]==before[0]+4 and b.economy.cash["Player"]==before[1]-2


def test_no_private_mind_or_seller_balance_leaks_into_public_market_projection():
    w=active();public=w.v2_snapshot()
    assert "operator" not in public
    assert not {"minds","semantic","episodes","decisions","cash"}.intersection(public)
    context=w.v2_context("Felix")
    assert set(context)=={"topics","offer","contract"}
    assert all(not t["evidence_ids"] for t in context["topics"])
    lab=w.v2_snapshot(operator=True)
    assert set(lab["operator"]["minds"])==set(BUYERS)
    assert all(m["footprint"]["memory_records"]<=m["footprint"]["capacity"] for m in lab["operator"]["minds"].values())


def test_proximity_resources_and_unearned_advance_cannot_be_bypassed_and_do_not_mutate():
    w=active();before=w.ledger.content_hash()
    with pytest.raises(ValueError,match="Walk"):
        w.v2_interact("v2_bonded_order","Felix")
    assert w.ledger.content_hash()==before
    near(w,"Felix");before=w.ledger.content_hash()
    with pytest.raises(ValueError,match="cash bond"):
        w.v2_interact("v2_advance_order","Felix")
    with pytest.raises(ValueError,match="actual flour"):
        w.v2_interact("v2_cash_order","Felix")
    assert w.ledger.content_hash()==before


def test_actual_retained_inspection_transfer_can_correct_a_buyers_dated_belief():
    w=active();near(w,"Felix")
    old=w.v2_minds["Felix"].believe("grain","supply",now=w.minute)
    with pytest.raises(ValueError,match="direct supply inspection"):
        w.v2_interact("v2_share_report","Felix")
    w.interact("inspect","Felix");w.advance(16,"compress")
    exp=max((e for e in w.remembered("Player") if e.kind=="observed" and e.subject=="grain" and e.predicate=="supply"),key=lambda e:e.as_of)
    w.v2_interact("v2_share_report","Felix")
    new=w.v2_minds["Felix"].believe("grain","supply",now=w.minute)
    assert new.as_of==exp.as_of and new.as_of>old.as_of
    assert new.value==exp.value and new.source_groups==("origin-observer:Player",)
    with pytest.raises(ValueError,match="already received"):
        w.v2_interact("v2_share_report","Felix")


def test_correlated_testimony_changes_funded_terms_and_a_new_direct_check_repairs_the_decision():
    worlds=[active(MindConfig(source_lineage=enabled)) for enabled in (True,False)]
    for w in worlds:
        earn_reliability(w);next_cycle(w)
        # The world stages a real direct dispatch check and actual communications
        # at a shared location. Every relay preserves that one communicated root.
        for actor in ("Marcus","Dama","Sabina","Lucius","Felix"):
            w._emit("v2_dispatch_meeting",f"{actor} joins the street's dispatch discussion",actors=(actor,),etype="move",to="street",position=(930,415))
        root=w._emit("v2_dispatch_observation","Marcus directly checks the current dispatch",actors=("Marcus",),scope="private",
            value=w.state.facts["grain.supply"],as_of=w.minute)
        w._observe("Marcus",root.payload["value"],root.event_id,w.minute)
        for speaker in ("Dama","Sabina","Lucius"):
            received=w._hear(speaker,"Marcus",root.payload["value"],w.minute,root.event_id,parents=(root.event_id,),observer="Marcus")
            w._hear("Felix",speaker,root.payload["value"],w.minute,root.event_id,parents=(received.event_id,),observer="Marcus")
        w._v2_decide("Felix",w.v2_market["offers"]["Felix"]["cycle"])
    guarded,naive=worlds
    assert guarded.v2_market["offers"]["Felix"]["mode"]=="bonded"
    assert naive.v2_market["offers"]["Felix"]["mode"]=="advance"
    # Only the memory policy changed: before accepting terms, actual cash/goods
    # remain matched. Different terms lead to different executed transfers.
    assert guarded.economy.cash==naive.economy.cash and guarded.economy.inventory==naive.economy.inventory
    before=[w.economy.cash["Player"] for w in worlds]
    run(naive,"v2_advance_order")
    assert naive.economy.cash["Player"]==before[1]+4
    guarded.advance(1,"compress")
    correction=guarded._emit("v2_direct_correction","Felix personally checks the newest dispatch",actors=("Felix",),scope="private",
        value=guarded.state.facts["grain.supply"],as_of=guarded.minute)
    guarded._observe("Felix",correction.payload["value"],correction.event_id,guarded.minute)
    guarded._v2_decide("Felix",guarded.v2_market["offers"]["Felix"]["cycle"])
    assert guarded.v2_market["offers"]["Felix"]["mode"]=="advance"
    run(guarded,"v2_advance_order")
    assert guarded.economy.cash["Player"]==before[0]+4


def test_unfunded_buyers_defer_without_negative_cash_or_invented_escrow():
    w=MarketWorld()
    for buyer in BUYERS:
        amount=w.economy.cash[buyer]
        w._emit("v2_test_prior_expense",f"{buyer} pays an actual prior account",actors=(buyer,),scope="private",cash_delta={buyer:-amount,"PriorAccounts":amount})
    total=cash(w);w.v2_activate_minds();w.advance(20,"compress")
    assert all(w.v2_market["offers"][a]["status"]=="considering" for a in BUYERS)
    assert w.economy.cash.get(ESCROW,0)==0 and cash(w)==total
    assert all(value>=0 for value in w.economy.cash.values())


def test_operational_reconsideration_never_refills_a_mind_from_accessible_or_archival_history():
    w=active();original=w.remembered
    def guarded(agent):
        if agent in BUYERS:raise AssertionError("operational archive/memory refill")
        return original(agent)
    w.remembered=guarded
    for buyer in BUYERS:
        w._v2_decide(buyer,w.v2_market["offers"][buyer]["cycle"])
    assert w.v2_activate_minds() is None
    assert all(w.v2_market["offers"][a]["status"]=="offered" for a in BUYERS)


def test_bootstrap_uses_retained_experience_chronology_not_the_storage_order():
    worlds=[MarketWorld(),MarketWorld()]
    for w in worlds:
        for i in range(3):
            event=w._emit("v2_prior_direct_check","Felix checks the currently available dispatch",actors=("Felix",),scope="private")
            w._observe("Felix",w.state.facts["grain.supply"],event.event_id,w.minute)
    original=worlds[1].remembered
    worlds[1].remembered=lambda agent:list(reversed(original(agent)))
    for w in worlds:w.v2_activate_minds()
    assert worlds[0].v2_minds["Felix"].to_dict()==worlds[1].v2_minds["Felix"].to_dict()


@pytest.mark.parametrize("kind,subject,predicate,value,speaker,accepted",[
    ("told","rebirth","rb_commission_settled","Aelia kept it","Dama",True),
    ("told","v2_social","Player","kept","Dama",True),
    ("episodic","v2_social","Player","kept","Player",False),
    ("episodic","rebirth","rb_commission_settled","Aelia kept it","Dama",True),
    ("episodic","unrelated","rb_commission_settled","Aelia kept it","Player",True),
])
def test_hearsay_rejected_and_unrelated_receipts_do_not_become_personal_credit(kind,subject,predicate,value,speaker,accepted):
    w=active()
    event=w._emit("v2_reported_receipt","Dama reports another person's receipt",actors=("Dama","Felix"),scope="private")
    w._remember("Felix",Experience(w.minute,kind,subject,predicate,value,speaker,w.minute,accepted,event.event_id,event.payload["title"]))
    social=w.v2_minds["Felix"].social("Player","reliability",now=w.minute)
    assert social["value"]==.5 and social["evidence_ids"]==[]
    w._v2_decide("Felix",w.v2_market["offers"]["Felix"]["cycle"])
    assert w.v2_market["offers"]["Felix"]["mode"]=="bonded"
    stored=next(e for e in w.v2_minds["Felix"].to_dict()["episodes"] if e["event_id"]==event.event_id)
    assert stored["kind"]==kind and stored["source_agent"]==speaker and stored["accepted"] is accepted


def test_two_partial_late_replacements_preserve_the_full_institutional_repair_account():
    w=active();run(w,"v2_bonded_order")
    contract=w._v2_contract("Felix","open")
    w.advance(contract["deadline"]-w.minute,"compress")
    buy(w,2)
    before=w.economy.cash["Player"];completed=w.v2_market["completed_batches"]["Felix"]
    run(w,"v2_replace_order",quantity=1)
    partial=w._v2_contract("Felix","defaulted")
    assert partial["delivered"]==1 and partial["replacement_units"]==1
    run(w,"v2_replace_order",quantity=1)
    repaired=w._v2_contract("Felix")
    institutional=next(c for c in w.economy.commitments["Player"] if c["id"]==contract["id"])
    assert repaired["status"]=="repaired" and repaired["replacement_units"]==2
    assert institutional["status"]=="missed" and institutional["repaired"] and institutional["replacement_units"]==2
    assert w.economy.cash["Player"]==before and w.economy.inventory["Player"]==0
    assert w.v2_market["completed_batches"]["Felix"]==completed+1
    assert w.economy.inventory[batch_account("Felix")]==0


def test_actual_authored_rebirth_receipt_can_support_later_credit():
    w=active()
    event=w._emit("rb_commission_settled","Felix directly settles Aelia's completed commission",actors=("Player","Felix"),scope="private")
    social=w.v2_minds["Felix"].social("Player","reliability",now=w.minute)
    assert social["value"]==.68 and social["evidence_ids"]==[event.event_id]
    w._v2_decide("Felix",w.v2_market["offers"]["Felix"]["cycle"])
    assert w.v2_market["offers"]["Felix"]["mode"]=="advance"
