"""Consequential intrigue, private evidence, progression and safe old-world continuation."""
import copy
import json
import pytest
from kalends.pompeii.world import PompeiiWorld
from kalends.pompeii.district import PompeiiConfig
from kalends_rebirth.world import RebirthWorld


def broker(world):
    world.interact('examine_receipt','Sabina')
    world.move(x=850,y=430);world.interact('examine_tablet','Dama')
    world.move(x=930,y=415);world.interact('verify_cart','Marcus')
    return world.interact('mediate','Marcus')


def test_opening_is_real_colocated_dispute_with_private_original_accounts():
    w=RebirthWorld()
    assert w.snapshot()['nearby']==['Sabina']
    assert w.state.agent_locations['Sabina']=='street'
    assert w.state.agent_locations['Dama']=='street'
    assert w.economy.market_stock==8 and w.economy.inventory['Cart']==6
    assert w.economy.cash['Sabina']==22 and w.economy.cash['Lucius']==52
    assert 'six' in w.objective()['title'].lower()
    assert not w.snapshot()['player']['documents']
    private_docs={d['event_id'] for d in w.documents.values()}
    assert not private_docs.intersection(e['event_id'] for e in w.snapshot()['journal'])
    assert all(o['action']['recipient']=='Sabina' for o in w.snapshot()['opportunities'])


def test_broker_uses_three_real_copies_and_carrier_and_reward_are_funded():
    w=RebirthWorld();initial=sum(w.economy.cash.values());grain=sum(w.economy.inventory.values())+w.economy.market_stock
    broker(w)
    assert w.arc['route']=='broker' and w.arc['stage']=='resolved'
    assert w.economy.inventory['Cart']==0
    assert w.economy.inventory['Sabina']==4 and w.economy.inventory['Lucius']==9
    assert w.economy.cash['Player']==7 and w.economy.cash['Carrier']==3
    assert sum(w.economy.cash.values())==initial
    assert sum(w.economy.inventory.values())+w.economy.market_stock==grain
    assert w.progression['access']==['broker']
    assert w.axes['Marcus']['competence']==.5 and w.axes['Marcus']['affinity']==.38
    assert w.axes['Sabina']['affinity']==.62
    with pytest.raises(ValueError): w.interact('mediate','Marcus')


def test_three_routes_have_different_allocations_access_and_obligations():
    worlds={route:RebirthWorld() for route in ('market','household','broker')}
    worlds['market'].interact('support_market','Sabina')
    worlds['household'].move(location='household');worlds['household'].interact('guarantee_household','Lucius')
    broker(worlds['broker'])
    assert [worlds[r].economy.cash['Player'] for r in worlds]==[3,12,7]
    assert [worlds[r].progression['access'] for r in worlds]==[['market'],['household'],['broker']]
    assert worlds['market'].economy.inventory['Sabina']==6
    assert worlds['household'].economy.inventory['Sabina']==2
    assert worlds['broker'].economy.inventory['Sabina']==4
    assert any(c['id']=='rebirth-service' and c['status']=='open' for c in worlds['household'].economy.commitments['Player'])
    assert not worlds['market'].economy.commitments['Player']


def test_evidence_route_cannot_use_parser_or_remote_document_shortcuts():
    w=RebirthWorld();before=w.ledger.content_hash()
    with pytest.raises(ValueError): w.interact('examine_tablet','Dama')
    with pytest.raises(ValueError): w.interact('mediate','Marcus')
    assert before==w.ledger.content_hash()
    w.move(x=930,y=415)
    context=w.context('Marcus')
    topic=next(t for t in context['topics'] if t['id']=='loading_record')
    assert topic['withheld'] and topic['evidence_ids']==[]
    assert w.documents['loading_record']['event_id'] not in context['disclosure_evidence_ids']
    cash=w.economy.cash['Player'];w.talk('Marcus','loading_record')
    assert not w._record_known('Player','loading_record')
    assert w.economy.cash['Player']==cash
    w.interact('verify_cart','Marcus')
    assert w._record_known('Player','loading_record')
    assert w.economy.cash['Player']==cash-1
    with pytest.raises(ValueError): w.interact('verify_cart','Marcus')


def test_confirmed_document_questions_acquire_only_the_speakers_held_record():
    w=RebirthWorld();w.talk('Sabina','market_receipt')
    assert w._record_known('Player','market_receipt')
    w.talk('Sabina','documents')
    with pytest.raises(ValueError):w.talk('Sabina','household_tablet')
    assert not w._record_known('Player','household_tablet')
    w.move(x=930,y=415);w.talk('Marcus','news')
    assert w.knowledge('Player')['value']=='available'


def test_world_settles_ignored_dispute_without_player_money_or_forced_quest():
    w=RebirthWorld();w.interact('decline_dispute','Sabina');cash=w.economy.cash['Player']
    w.move(location='fullery');w.advance(360)
    assert w.arc['route']=='ignored' and w.arc['stage']=='resolved'
    assert w.economy.cash['Player']==cash and w.economy.inventory['Cart']==0
    assert w.economy.inventory['Lucius']>=6
    assert w.arc['followup_ready']
    resolution=w.ledger.events[w.arc['resolution_event']]
    assert not w._visible(resolution)
    assert 'cart went on' in w.objective()['title'].lower()


def test_market_followup_repair_changes_professional_access_and_spends_actual_coins():
    w=RebirthWorld();w.interact('support_market','Sabina')
    assert w.axes['Lucius']['affinity']==.28
    w.advance(45);w.move(location='household')
    assert any(c['action']['action']=='reconcile' for c in w.context('Lucius')['choices'])
    before=w.economy.cash['Lucius'];w.interact('reconcile','Lucius')
    assert w.economy.cash['Player']==0 and w.economy.cash['Lucius']==before+3
    assert w.arc['followup_done'] and 'household' in w.progression['access']
    with pytest.raises(ValueError):w.interact('reconcile','Lucius')


def test_household_service_has_actual_time_and_unmet_service_closes_future_access():
    w=RebirthWorld();w.move(location='household');w.interact('guarantee_household','Lucius');w.advance(45)
    with pytest.raises(ValueError):w.interact('accept_commission','Lucius')
    kept=copy.deepcopy(w);start=kept.minute;kept.interact('return_service','Lucius')
    assert kept.minute==start+120 and kept.arc['service_done']
    assert next(c for c in kept.economy.commitments['Player'] if c['id']=='rebirth-service')['status']=='fulfilled'
    kept.interact('accept_commission','Lucius')
    w.advance(3*1440)
    assert w.arc['service_missed'] and 'household' not in w.progression['access']
    assert w.axes['Lucius']['favors']==0
    assert next(c for c in w.economy.commitments['Player'] if c['id']=='rebirth-service')['status']=='missed'


def test_commission_escrow_real_goods_daily_cap_and_no_double_payment():
    w=RebirthWorld();w.interact('support_market','Sabina');w.advance(45);w.move(location='thermopolium')
    pay_before=w.economy.cash['Sabina'];w.interact('accept_commission','Sabina')
    assert w.economy.cash['Sabina']==pay_before-5 and w.economy.cash['CommissionEscrow']==5
    with pytest.raises(ValueError):w.interact('fulfill_commission','Sabina')
    w.interact('work','Sabina')
    w.move(x=930,y=415);w.interact('buy','Marcus',quantity=2)
    w.move(location='thermopolium');cash=w.economy.cash['Player'];stock=w.economy.inventory['Sabina']
    w.interact('fulfill_commission','Sabina')
    assert w.economy.cash['Player']==cash+5 and w.economy.cash['CommissionEscrow']==0
    assert w.economy.inventory['Sabina']==stock+2 and w.economy.inventory['Player']==0
    assert w.progression['completed_commissions']==1
    with pytest.raises(ValueError):w.interact('fulfill_commission','Sabina')
    with pytest.raises(ValueError):w.interact('accept_commission','Sabina')


def test_missed_commission_returns_reserved_money_and_reduces_reliability():
    w=RebirthWorld();w.interact('support_market','Sabina');w.advance(45);w.move(location='thermopolium')
    cash=w.economy.cash['Sabina'];w.interact('accept_commission','Sabina');deadline=w.commissions[-1]['deadline']
    reliability=w.axes['Sabina']['reliability'];w.advance(deadline-w.minute)
    assert w.economy.cash['Sabina']==cash and w.economy.cash['CommissionEscrow']==0
    assert w.commissions[-1]['status']=='missed'
    assert w.axes['Sabina']['reliability']==round(reliability-.18,3)


def test_broker_commission_demands_new_direct_evidence_and_pays_once():
    w=RebirthWorld();broker(w);w.advance(45);w.interact('accept_commission','Marcus')
    with pytest.raises(ValueError):w.interact('fulfill_commission','Marcus')
    w.interact('inspect','Marcus');w.advance(15)
    cash=w.economy.cash['Player'];w.interact('fulfill_commission','Marcus')
    assert w.economy.cash['Player']==cash+3
    with pytest.raises(ValueError):w.interact('fulfill_commission','Marcus')


def test_relationship_dimensions_and_plans_have_explicit_causes():
    w=RebirthWorld();w.interact('support_market','Sabina');w.move(location='thermopolium')
    assert w.axes['Sabina']['affinity']==.75 and w.axes['Sabina']['credibility']==.6
    with pytest.raises(ValueError):w.interact('guarantee_household','Lucius')
    changes=[e for e in w.ledger.events if e.payload.get('relationship_axes')]
    assert changes and all(e.payload.get('parents') for e in changes)
    plan=w.private_view('Sabina')['plan']
    assert plan['long_term'] and plan['medium_term'] and plan['short_term']
    w.advance(600)
    assert w.decisions and all(d['action'] in ('wait','conserve','inspect','defer','buy','await_commission') for d in w.decisions)


def test_factual_credibility_controls_report_acceptance_independently_of_promises_and_affinity():
    trusted=RebirthWorld();doubted=RebirthWorld()
    trusted._emit('test_fixture','An honestly reported but missed errand',actors=('Player','Sabina'),scope='private',
        relationship_axes=[trusted._axis_change('Sabina',reliability=-.5,affinity=-.4,credibility=.2)])
    doubted._emit('test_fixture','A kept errand followed by an unreliable report',actors=('Player','Sabina'),scope='private',
        relationship_axes=[doubted._axis_change('Sabina',reliability=.3,affinity=.4,credibility=-.4)])
    good=trusted.claim('Sabina','available');bad=doubted.claim('Sabina','available')
    assert good['payload']['accepted'] and not bad['payload']['accepted']
    assert good['payload']['credibility_used']==.8 and bad['payload']['credibility_used']==.2
    assert trusted.knowledge('Sabina')['value']=='available' and doubted.knowledge('Sabina')['value']=='unknown'


def test_an_earned_favor_can_back_one_commission_when_reliability_has_fallen():
    w=RebirthWorld();w.interact('support_market','Sabina');w.advance(45);w.move(location='thermopolium')
    assert w.axes['Sabina']['favors']==1
    w._emit('test_fixture','Later missed promises damaged reliability',actors=('Player','Sabina'),scope='private',
        relationship_axes=[w._axis_change('Sabina',reliability=-.5)])
    choice=next(c for c in w.context('Sabina')['choices'] if c['id']=='accept_commission')
    assert choice['enabled'] and choice['cost']=='One earned favor'
    event=w.interact('accept_commission','Sabina')
    assert event['payload']['favor_used'] and w.axes['Sabina']['favors']==0
    w.advance(w.commissions[-1]['deadline']-w.minute+1440)
    with pytest.raises(ValueError,match='earned favor'):w.interact('accept_commission','Sabina')


def test_saved_legacy_prefix_accounts_and_trust_are_preserved_without_source_mutation():
    old=PompeiiWorld();old.move(location='bakery');old.interact('accept_delivery','Felix');old.advance(600)
    events=old.ledger.to_json();cash=old.economy.cash['Player'];trust=dict(old.state.trust);old_hash=old.ledger.content_hash()
    w=RebirthWorld.from_legacy(old)
    assert w.ledger.to_json()[:len(events)]==events
    assert w.economy.cash['Player']==cash and w.state.trust==trust
    assert w.axes['Felix']['reliability']==trust[('Felix','Player')]
    assert old.ledger.content_hash()==old_hash and not hasattr(old,'arc')
    assert w.arc['migrated'] and w.arc['opened_at']==old.minute


def test_genuine_old_service_can_be_reviewed_and_settled_after_saved_life_migration(tmp_path):
    from kalends.pompeii.server import PompeiiSession
    from kalends_rebirth.ai import Cognition
    from kalends_rebirth.language import Language
    from kalends_rebirth.server import RebirthSession
    source=tmp_path/'old-life.json';legacy=PompeiiSession(source)
    legacy.apply('move',{'location':'household'});legacy.apply('interact',{'action':'patronage','recipient':'Lucius'})
    preserved=source.read_bytes();destination=tmp_path/'new-life.json'
    migrated=RebirthSession(destination,migrate_from=source,language=Language(Cognition()))
    options=migrated.context('Lucius')['choices']
    assert any(c['id']=='service' and c['enabled'] for c in options)
    assert not any(c['id']=='return_service' for c in options)
    before=migrated.original.minute;cash=migrated.original.economy.cash['Player']
    proposal=migrated.apply('propose',{'recipient':'Lucius','choice_id':'service'})
    assert proposal['interpretations'][0]['action']['action']=='service'
    migrated.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert migrated.original.minute==before+120 and migrated.original.economy.cash['Player']==cash
    assert next(c for c in migrated.original.economy.commitments['Player'] if c['id']=='household-service')['status']=='fulfilled'
    assert migrated.original.axes['Lucius']['reliability']==.78 and migrated.original.axes['Lucius']['competence']==.4
    settlement=next(e for e in migrated.original.ledger.events if e.payload.get('commitment_updates') and e.payload['commitment_updates'][0]['id']=='household-service')
    assert settlement.payload['relationship_axes'] and settlement.payload['parents']
    assert not any(c['id']=='service' for c in migrated.context('Lucius')['choices'])
    assert source.read_bytes()==preserved
    restored=RebirthSession(destination,language=Language(Cognition()))
    assert restored.original.fidelity_state()==migrated.original.fidelity_state()
    fresh=RebirthWorld();fresh.move(location='household');fresh.interact('guarantee_household','Lucius')
    assert any(c['id']=='return_service' for c in fresh.context('Lucius')['choices'])
    assert not any(c['id']=='service' for c in fresh.context('Lucius')['choices'])


def test_inherited_open_flour_promise_has_contextual_delivery_without_new_commitment():
    old=PompeiiWorld();old.move(location='thermopolium');old.interact('work','Sabina')
    old.move(x=930,y=415);old.interact('buy','Marcus',quantity=4)
    old.move(location='bakery');old.interact('accept_delivery','Felix')
    w=RebirthWorld.from_legacy(old)
    offered=next(c for c in w.context('Felix')['choices'] if c['id']=='deliver')
    assert offered['enabled'] and offered['action']=={'action':'deliver','recipient':'Felix'}
    old_count=len(w.economy.commitments['Player']);w.interact('deliver','Felix')
    assert len(w.economy.commitments['Player'])==old_count and w.flags['quest']=='fulfilled'
    assert w.economy.inventory['Player']==0
    assert not any(c['id']=='deliver' for c in w.context('Felix')['choices'])


def test_old_service_still_gates_repaired_household_work_and_default_has_actual_social_cause():
    old=PompeiiWorld();old.move(location='household');old.interact('patronage','Lucius')
    w=RebirthWorld.from_legacy(old);w.move(x=750,y=435);w.interact('support_market','Sabina');w.advance(45)
    w.move(location='household');w.interact('reconcile','Lucius')
    assert 'household' in w.progression['access']
    assert not next(c for c in w.context('Lucius')['choices'] if c['id']=='accept_commission')['enabled']
    with pytest.raises(ValueError,match='promised service'):w.interact('accept_commission','Lucius')
    kept=copy.deepcopy(w);kept.interact('service','Lucius');kept.interact('accept_commission','Lucius')
    due=next(c['deadline'] for c in w.economy.commitments['Player'] if c['id']=='household-service')
    reliability=w.axes['Lucius']['reliability'];favors=w.axes['Lucius']['favors']
    w.advance(due-w.minute)
    assert w.axes['Lucius']['reliability']==round(reliability-.25,3) and w.axes['Lucius']['favors']==favors
    assert 'household' not in w.progression['access']
    event=next(e for e in reversed(w.ledger.events) if e.payload.get('flags',{}).get('service_missed'))
    assert event.payload['parents'] and event.payload['relationship_axes']


@pytest.mark.parametrize('days',[1,7,30])
def test_reference_and_shared_ledger_have_identical_worlds_and_future_continuation(days):
    worlds=[RebirthWorld(seed=80001,optimized=optimized) for optimized in (False,True)]
    for w in worlds:
        w.interact('support_market','Sabina');w.clock.advance(days*1440,w.on_task,'compress')
    assert worlds[0].fidelity_state()==worlds[1].fidelity_state()
    branch=copy.deepcopy(worlds[1]);branch.move(location='household')
    assert worlds[1].ledger.content_hash()!=branch.ledger.content_hash()
    assert worlds[0].fidelity_state()==worlds[1].fidelity_state()


def test_extended_horizon_migration_and_no_goods_creation_when_legacy_stock_is_short():
    old=PompeiiWorld(PompeiiConfig(horizon_days=60));old.advance(60*1440)
    assert RebirthWorld.from_legacy(old).config.horizon_days==90
    poor=PompeiiWorld();poor._emit('test_fixture','A real shortage fixture',actors=('Marcus',),scope='private',market_stock_delta=-poor.economy.market_stock)
    before=sum(poor.economy.inventory.values())+poor.economy.market_stock
    continued=RebirthWorld.from_legacy(poor)
    assert continued.arc['stage']=='awaiting_stock'
    assert sum(continued.economy.inventory.values())+continued.economy.market_stock==before
    with pytest.raises(ValueError):continued.interact('support_market','Sabina')
    advances={a:continued.economy.cash[a] for a in ('Sabina','Lucius')}
    continued.advance(360)
    assert continued.arc['route']=='unclaimed' and continued.economy.inventory.get('Cart',0)==0
    assert continued.economy.cash['Sabina']==advances['Sabina']+continued.arc['sabina_advance']
    assert continued.economy.cash['Lucius']==advances['Lucius']+continued.arc['household_advance']
