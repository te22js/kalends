"""Public terms must agree with the transaction the player actually confirms."""
import copy
import json
from unittest.mock import patch

import pytest

from kalends_rebirth.ai import Cognition
from kalends_rebirth.language import Language
from kalends_rebirth.scenario import COMMISSION_SPECS
from kalends_rebirth.server import RebirthSession
from kalends_rebirth.world import RebirthWorld


def session():
    return RebirthSession(language=Language(Cognition()))


def choose(s,action,recipient):
    proposal=s.apply('propose',{'recipient':recipient,'choice_id':action})
    return s.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})


def broker(s):
    choose(s,'examine_receipt','Sabina')
    s.apply('move',{'x':850,'y':430});choose(s,'examine_tablet','Dama')
    s.apply('move',{'x':930,'y':415});choose(s,'verify_cart','Marcus')
    choose(s,'mediate','Marcus')


def commission_session(recipient):
    s=session()
    if recipient=='Sabina':
        choose(s,'support_market','Sabina');s.apply('advance',{'minutes':45})
        s.apply('move',{'location':'thermopolium'})
    elif recipient=='Marcus':
        broker(s);s.apply('advance',{'minutes':45})
    else:
        s.apply('move',{'location':'household'});choose(s,'guarantee_household','Lucius')
        s.apply('advance',{'minutes':45});choose(s,'return_service','Lucius')
    return s


def funded_buyer():
    s=session();choose(s,'work','Sabina')
    s.apply('move',{'x':930,'y':415})
    assert s.original.economy.cash['Player']==9
    return s


@pytest.mark.parametrize('recipient',['Sabina','Marcus','Lucius'])
def test_commission_deadline_is_disclosed_before_review_and_equals_actual_obligation(recipient):
    s=commission_session(recipient);world=s.original
    before=world.fidelity_state();digest=world.ledger.content_hash()
    offer=next(c for c in s.context(recipient)['choices'] if c['id']=='accept_commission')
    duration=COMMISSION_SPECS[recipient]['duration'];deadline=world.minute+duration
    assert offer['terms']=={'deadline':deadline,'duration_minutes':duration,'reward':COMMISSION_SPECS[recipient]['reward']}
    assert str(duration)+' world minutes' in offer['description']
    assert world._due_label(deadline) in offer['description']
    proposal=s.apply('propose',{'recipient':recipient,'choice_id':'accept_commission'})
    review=proposal['interpretations'][0]
    assert review['terms']==offer['terms'] and world._due_label(deadline) in review['transmission']
    assert world.fidelity_state()==before and world.ledger.content_hash()==digest
    s.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    accepted=s.original.commissions[-1]
    contract=next(c for c in s.original.economy.commitments['Player'] if c['id']==accepted['id'])
    assert accepted['deadline']==contract['deadline']==deadline
    assert accepted['reward']==review['terms']['reward']


def test_contextual_purchase_quote_and_executed_debit_match_without_mutating_world():
    s=funded_buyer();before=s.original.fidelity_state();digest=s.original.ledger.content_hash()
    proposal=s.apply('propose',{'recipient':'Marcus','choice_id':'buy'})
    review=proposal['interpretations'][0];quote=review['quote']
    assert quote['quantity']==1 and quote['unit_price']==2 and quote['total_cost']==2
    assert quote['available'] and review['cost']=='1 × 2 = 2 coins'
    assert s.original.fidelity_state()==before and s.original.ledger.content_hash()==digest
    cash=s.original.economy.cash['Player'];goods=s.original.economy.inventory['Player']
    s.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert cash-s.original.economy.cash['Player']==quote['total_cost']
    assert s.original.economy.inventory['Player']-goods==quote['quantity']


def test_typed_custom_quantity_quote_agrees_with_real_payment_and_cannot_be_edited_by_client():
    s=funded_buyer()
    proposal=s.apply('propose',{'recipient':'Marcus','text':'Buy four flour units'})
    review=proposal['interpretations'][0]
    assert review['action']['quantity']==4 and '4 flour units' in review['label']
    assert review['cost']=='4 × 2 = 8 coins' and review['cost_amount']==8
    assert review['quote']['total_cost']==8 and review['quote']['available']
    # The returned quote and action are detached from the stored reviewed offer.
    review['quote']['total_cost']=0;review['action']['quantity']=1
    s.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert s.original.economy.cash['Player']==1 and s.original.economy.inventory['Player']==4


@pytest.mark.parametrize('recipient',['Felix','Marcus'])
@pytest.mark.parametrize('quantity',range(1,13))
def test_every_canonical_quantity_quotes_the_debit_and_goods_for_both_sellers(recipient,quantity):
    w=RebirthWorld();w.move(location='bakery' if recipient=='Felix' else 'street')
    if recipient=='Marcus':w.move(x=930,y=415)
    w._emit('test_fixture','Fund the buyer and supply the two counters',actors=('Player','Marcus'),scope='private',
        cash_delta={'Player':100},inventory_delta={'Marcus':12},market_stock_delta=12)
    quote=w.buy_quote(recipient,quantity)
    cash=w.economy.cash['Player'];goods=w.economy.inventory['Player']
    assert quote['available']
    w.interact('buy',recipient,quantity)
    assert cash-w.economy.cash['Player']==quote['total_cost']==quantity*quote['unit_price']
    assert w.economy.inventory['Player']-goods==quote['quantity']==quantity


def test_typed_commission_review_discloses_the_same_deadline_as_contextual_offer():
    s=commission_session('Marcus')
    offer=next(c for c in s.context('Marcus')['choices'] if c['id']=='accept_commission')
    proposal=s.apply('propose',{'recipient':'Marcus','text':'take the contract'})
    review=proposal['interpretations'][0]
    assert review['action']['action']=='accept_commission'
    assert review['terms']==offer['terms'] and review['transmission']==offer['description']
    s.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert s.original.commissions[-1]['deadline']==review['terms']['deadline']


def test_public_quote_exposes_offer_terms_without_private_seller_balances_or_stock():
    s=funded_buyer();world=s.original
    before=world.fidelity_state();quote=world.buy_quote('Marcus',2)
    assert set(quote)=={'action','recipient','quantity','unit_price','total_cost','currency','minute','available','reason'}
    assert quote['currency']=='coins' and quote['recipient']=='Marcus'
    assert not {'cash','inventory','stock','max_quantity','accounts','memories'}&set(quote)
    assert world.fidelity_state()==before
    offer=next(c for c in s.context('Marcus')['choices'] if c['id']=='buy')
    assert offer['terms']==world.buy_quote('Marcus')


def test_unaffordable_typed_quote_explains_failure_without_changing_or_charging_world():
    s=session();s.apply('move',{'x':930,'y':415})
    proposal=s.apply('propose',{'recipient':'Marcus','text':'Buy four flour units'})
    review=proposal['interpretations'][0]
    assert review['quote']['total_cost']==8 and review['available'] is False
    assert '8 coins' in review['unavailable_reason']
    before=s.original.fidelity_state();commands=copy.deepcopy(s.commands)
    with pytest.raises(ValueError,match='coins'):
        s.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert s.original.fidelity_state()==before and s.commands==commands


def test_offer_distinguishes_stock_and_standing_without_reporting_private_counts():
    s=funded_buyer();w=s.original
    w._emit('test_fixture','The counter reserves its remaining flour',actors=('Marcus',),scope='private',
        inventory_delta={'Marcus':-w.economy.inventory['Marcus']})
    quote=w.buy_quote('Marcus',1)
    assert not quote['available'] and quote['reason']=='This seller cannot fill that quantity now.'
    assert not next(c for c in w.choices('Marcus') if c['id']=='buy')['enabled']
    with pytest.raises(ValueError,match='less flour'):w.interact('buy','Marcus')
    w._emit('test_fixture','The trader refuses another unsupported dealing',actors=('Player','Marcus'),scope='private',
        relationship_updates=[{'listener':'Marcus','speaker':'Player','value':.2}])
    assert w.buy_quote('Marcus')['reason']=='This seller is not trading with you now.'
    with pytest.raises(ValueError,match='not trade'):w.interact('buy','Marcus')


def test_any_accepted_time_change_expires_an_earlier_numeric_quote():
    s=funded_buyer();proposal=s.apply('propose',{'recipient':'Marcus','text':'Buy two flour units'})
    old=proposal['interpretations'][0]['quote']
    s.apply('advance',{'minutes':240});before=s.original.fidelity_state()
    with pytest.raises(ValueError,match='changed'):
        s.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert s.original.fidelity_state()==before
    current=s.original.buy_quote('Marcus',2)
    assert current['minute']>old['minute']
    assert current['total_cost']==2*s.original.economy.price


@pytest.mark.parametrize('quantity',[True,0,13,1.5])
def test_public_quote_rejects_noncanonical_quantities(quantity):
    w=RebirthWorld();before=w.ledger.content_hash()
    with pytest.raises(ValueError,match='quantity'):w.buy_quote('Marcus',quantity)
    assert w.ledger.content_hash()==before


def test_inspection_and_paid_shift_choices_disable_at_actual_cash_and_daily_limits():
    w=RebirthWorld()
    w._emit('test_fixture','Aelia has spent her last coins',actors=('Player',),scope='private',cash_delta={'Player':-6})
    inspect=next(c for c in w.choices('Sabina') if c['id']=='inspect')
    assert not inspect['enabled'] and 'one coin' in inspect['reason']
    with pytest.raises(ValueError,match='coin'):w.interact('inspect','Sabina')
    w._emit('test_fixture','The counter has allocated its two extra shifts',actors=('Player','Sabina'),scope='private',flags={'work:0:Sabina':2})
    work=next(c for c in w.choices('Sabina') if c['id']=='work')
    assert not work['enabled'] and 'already' in work['reason']
    with pytest.raises(ValueError,match='already'):w.interact('work','Sabina')
    w._emit('test_fixture','The household account is exhausted',actors=('Lucius',),scope='private',cash_delta={'Lucius':-w.economy.cash['Lucius']})
    w.move(location='fullery');work=next(c for c in w.choices('Chreste') if c['id']=='work')
    assert not work['enabled'] and 'fund' in work['reason']
    with pytest.raises(ValueError,match='pay'):w.interact('work','Chreste')


def test_repair_and_commission_settlement_require_real_goods_and_new_observations():
    market=commission_session('Sabina');choose(market,'accept_commission','Sabina')
    offer=next(c for c in market.context('Sabina')['choices'] if c['id']=='fulfill_commission')
    assert not offer['enabled'] and '2 flour' in offer['reason']
    with pytest.raises(ValueError):market.apply('propose',{'recipient':'Sabina','choice_id':'fulfill_commission'})
    brokered=commission_session('Marcus');choose(brokered,'accept_commission','Marcus')
    choices={c['id']:c for c in brokered.context('Marcus')['choices']}
    assert not choices['reconcile']['enabled'] and not choices['fulfill_commission']['enabled']
    choose(brokered,'inspect','Marcus');brokered.apply('advance',{'minutes':15})
    choices={c['id']:c for c in brokered.context('Marcus')['choices']}
    assert choices['reconcile']['enabled'] and choices['fulfill_commission']['enabled']
    choose(brokered,'fulfill_commission','Marcus')
    assert brokered.original.commissions[-1]['status']=='fulfilled'


def test_week_old_fulfilled_commission_is_recalled_with_exact_support_despite_buffer_order():
    s=commission_session('Marcus');choose(s,'accept_commission','Marcus')
    choose(s,'inspect','Marcus');s.apply('advance',{'minutes':15})
    result=choose(s,'fulfill_commission','Marcus')
    settled=result['receipt']['event_id']
    s.apply('advance',{'minutes':10080});w=s.original
    eligible=[e for e in w.remembered('Marcus') if e.subject in ('rebirth','relationship') and
        (e.source_agent=='Player' or e.subject=='relationship')]
    assert settled in [e.event_id for e in eligible]
    assert settled not in [e.event_id for e in eligible[-2:]]  # Consolidation's storage order caused the regression.
    expected=sorted(eligible,key=lambda e:(e.tick,e.event_id))[-2:]
    x,y=w.positions['Marcus'];w.move(x=x,y=y)
    before=w.fidelity_state();context=w.context('Marcus')
    memory=next(t for t in context['topics'] if t['id']=='memory')
    assert memory['text']==' '.join(e.text for e in expected)
    assert memory['evidence_ids']==[e.event_id for e in expected]
    assert settled in memory['evidence_ids'] and 'keep Marcus\'s commission' in memory['text']
    assert w.fidelity_state()==before
    conversation=w.talk('Marcus','memory')['payload']
    assert conversation['spoken_text']==memory['text'] and conversation['parents']==memory['evidence_ids']
    reflection=w.interact('reflect','Marcus')['payload']
    assert reflection['title']==memory['text'] and reflection['parents']==memory['evidence_ids']
    assert reflection['reflection_records']==[e.text for e in expected]


def legacy_memory_journal(tmp_path):
    # Generate the actual old-runtime fixture with its movement semantics;
    # current Session moves use revision2 and must not redefine this pinned hash.
    original_perform=RebirthSession._perform
    def legacy_perform(world,operation,data,**kwargs):
        return original_perform(world,operation,data,**{**kwargs,'movement_revision':1,'minds_revision':0})
    with patch.object(RebirthSession,'_perform',staticmethod(legacy_perform)):
        s=commission_session('Marcus');choose(s,'accept_commission','Marcus')
        choose(s,'inspect','Marcus');s.apply('advance',{'minutes':15});choose(s,'fulfill_commission','Marcus')
        s.apply('advance',{'minutes':10080})
        x,y=s.original.positions['Marcus'];s.apply('move',{'x':x,'y':y})
    commands=copy.deepcopy(s.commands)
    for command in commands:
        command.pop('memory_presentation_revision',None)
        command.pop('movement_revision',None)
        command.pop('minds_revision',None)
    for data in ({'action':'talk','recipient':'Marcus','topic':'memory'},{'action':'reflect','recipient':'Marcus'}):
        at=s.original.minute
        receipt=RebirthSession._perform(s.original,'action',data,memory_presentation_revision=1)
        commands.append({'operation':'action','data':data,'at':at,'after':s.original.minute,'receipt_id':receipt['event_id']})
    # Independently generated with the original world.py from checkpoint3c971b6.
    expected_hash='85a132c0609d6835b17eb88caba3c0cc91e69f4816f363b5bec73ccf9313fe9f'
    assert s.original.ledger.content_hash()==expected_hash
    payload={'version':4,'config':s.config,'origin':None,'commands':commands,'mode':'game',
        'ledger_hash':expected_hash,'intervention':None,'telemetry_enabled':False,'product_events':[]}
    path=tmp_path/'legacy-v4.json';path.write_text(json.dumps(payload))
    return path,expected_hash


def test_legacy_memory_commands_restore_exact_hash_then_new_chronological_actions_and_fork_restart(tmp_path):
    path,legacy_hash=legacy_memory_journal(tmp_path);original_bytes=path.read_bytes()
    s=RebirthSession(path,language=Language(Cognition()))
    assert path.read_bytes()==original_bytes and s.original.ledger.content_hash()==legacy_hash
    legacy_talk=s.original.ledger.events[276].payload
    legacy_reflection=s.original.ledger.events[277].payload
    assert list(legacy_talk['parents'])==list(legacy_reflection['parents'])==[26,28,44]
    assert legacy_talk['spoken_text']==legacy_reflection['title']
    assert len(legacy_reflection['reflection_records'])==3
    memory=next(t for t in s.context('Marcus')['topics'] if t['id']=='memory')
    assert 53 in memory['evidence_ids'] and 'keep Marcus\'s commission' in memory['text']
    assert all('memory_presentation_revision' not in c for c in s.commands)
    proposal=s.apply('propose',{'recipient':'Marcus','text':'What do you remember of our dealings?'})
    result=s.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert result['receipt']['payload']['spoken_text']==memory['text']
    assert list(result['receipt']['parents'])==memory['evidence_ids']
    assert s.commands[-1]['memory_presentation_revision']==2
    assert all('memory_presentation_revision' not in c for c in s.commands[:-1])
    current_hash=s.original.ledger.content_hash();saved=path.read_bytes()
    restored=RebirthSession(path,language=Language(Cognition()))
    assert path.read_bytes()==saved and restored.original.ledger.content_hash()==current_hash
    assert restored.original.fidelity_state()==s.original.fidelity_state()
    restored.apply('mode',{'mode':'lab'});restored.apply('fork',{'kind':'remove_action','event_id':276})
    assert not restored.intervention['skipped']
    reflected=next(e for e in reversed(restored.branch.ledger.events) if e.payload['category']=='rb_reflection')
    assert reflected.payload['title']==legacy_reflection['title']
    assert list(reflected.payload['parents'])==[26,28,44]
    branch_talk=restored.branch.ledger.events[-1].payload
    assert list(branch_talk['parents'])==[53,reflected.event_id]
    assert 'keep Marcus\'s commission' in branch_talk['spoken_text']
    branch_hash=restored.branch.ledger.content_hash();forked_bytes=path.read_bytes()
    restarted=RebirthSession(path,language=Language(Cognition()))
    assert path.read_bytes()==forked_bytes and restarted.original.ledger.content_hash()==current_hash
    assert restarted.branch.ledger.content_hash()==branch_hash
    assert restarted.intervention==restored.intervention


@pytest.mark.parametrize('revision',[0,3,True,'2'])
def test_unknown_memory_presentation_revision_rejects_without_changing_save(tmp_path,revision):
    path,_=legacy_memory_journal(tmp_path)
    payload=json.loads(path.read_text());payload['commands'][-1]['memory_presentation_revision']=revision
    path.write_text(json.dumps(payload));before=path.read_bytes()
    with pytest.raises(ValueError,match='Unsupported memory presentation revision'):
        RebirthSession(path,language=Language(Cognition()))
    assert path.read_bytes()==before
