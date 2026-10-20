"""Adversarial scoped cognition, reviewed actions, budgets and provider wire fixtures."""
from __future__ import annotations
import copy
import json
import threading
import time
import pytest
from kalends.pompeii.world import PompeiiWorld
from kalends_rebirth.ai import Cognition, MockAdapter, OpenAIResponsesAdapter, TaskPolicy, ProposalError, BudgetError, LocalJSONAdapter
from kalends_rebirth.language import Language, validate_action, grounded_reply, validate_dialogue, execute, action_label
from kalends_rebirth.world import RebirthWorld
import kalends_rebirth.ai as ai_module


def context(name="Sabina"):
    view=PompeiiWorld().private_view(name)
    view["beliefs"]={"grain.supply":{"value":"unknown","as_of":None,"evidence_ids":[],"confidence":0}}
    view.update(speaker=name,greeting={"text":"The accounts do not agree. Ask me what I received.","evidence_ids":[4]},
        experiences=[{"event_id":4,"tick":2,"kind":"observed","subject":"receipt","text":"The receipt records a payment of three coins."}],
        topics=[{"id":"dispute","text":"The receipt records a payment of three coins.","evidence_ids":[4]}],
        choices=[{"id":"receipt","label":"Read the receipt","description":"Inspect Sabina's retained copy.","action":{"action":"examine_receipt","recipient":name},"enabled":True}],
        plan_options=[{"id":"verify","label":"Verify the dispatch","enabled":True}],
        plan={"short_term":"Check the dated account before spending more.","evidence_ids":[4]})
    return view


@pytest.mark.parametrize('text,recipient,expected',[
    ('Buy four flour units','Felix','buy'),('Could I purchase two flour units?','Marcus','buy'),
    ('I promise four flour units','Felix','accept_delivery'),('I brought the flour','Felix','deliver'),
    ('I need a paid shift','Sabina','work'),('I need an advance','Lucius','patronage'),
    ('Sell my report','Felix','sell_information'),('Read the receipt','Sabina','examine_receipt'),
    ('What do you remember about me?','Felix','talk'),('What happened to the cart?','Sabina','talk'),
    ('What work is there?','Sabina','talk'),('Who are you?','Dama','talk'),
    ('I will not buy four flour','Felix','talk'),('Never promise anything','Felix','talk'),
    ('Can I deliver later?','Felix','talk'),('How can I buy flour?','Felix','talk'),
])
def test_ordinary_and_ambiguous_intents(text,recipient,expected):
    language=Language(Cognition())
    result=language.propose(text,recipient,context(recipient))
    action=result['interpretations'][0]['action']
    assert action['action']==expected
    assert action['actor_id']=='Player' and action['needs_confirmation'] is True
    assert language.metrics['external_calls']==0


def test_provider_cannot_change_actor_target_or_bypass_confirmation():
    for corrupt in ({'actor_id':'Lucius'},{'recipient':'Lucius'},{'needs_confirmation':False},{'evidence_ids':[9999]}):
        adapter=MockAdapter({'action':{'action':'examine_receipt','recipient':'Sabina',**corrupt}})
        language=Language(Cognition(adapter))
        result=language.propose('Read the receipt','Sabina',context())
        assert result['interpretations'][0]['action']['action']=='examine_receipt'
        assert result['interpretations'][0]['action']['recipient']=='Sabina'
        assert result['ai_receipt']['fallback']
        assert len(adapter.calls)==2
        assert language.metrics['rejected_outputs']==2


def test_unsupported_fields_quantities_and_unavailable_opportunities():
    view=context()
    for corrupt in ({'quantity':100},{'quantity':True},{'cash':100},{'code':'delete_world()'}):
        with pytest.raises(ProposalError):validate_action({'action':'examine_receipt','recipient':'Sabina',**corrupt},'Sabina',view)
    view['choices'][0]['enabled']=False
    with pytest.raises(ProposalError):validate_action({'action':'examine_receipt','recipient':'Sabina'},'Sabina',view)


def test_question_and_refusal_cannot_be_overridden_by_provider():
    adapter=MockAdapter({'action':{'action':'buy','recipient':'Felix','quantity':4}})
    language=Language(Cognition(adapter))
    for text in ('I will not buy flour','What is your work?','Can I deliver later?'):
        assert language.propose(text,'Felix',context('Felix'))['interpretations'][0]['action']['action']=='talk'
    assert adapter.calls==[]


def test_provider_receives_only_incoming_character_context_and_copies():
    view=context();adapter=MockAdapter()
    language=Language(Cognition(adapter))
    result=language.propose('Read the receipt','Sabina',view)
    supplied=adapter.calls[0]['context']
    assert supplied['id']=='Sabina'
    assert [e['event_id'] for e in supplied['experiences']]==[4]
    assert 'world' not in supplied and 'archive' not in supplied
    supplied['experiences'].clear()
    assert len(view['experiences'])==1
    result['interpretations'][0]['action']['recipient']='Lucius'
    again=language.propose('Read the receipt','Sabina',view)
    assert again['interpretations'][0]['action']['recipient']=='Sabina'
    assert language.metrics['cache_hits']==1


def test_cache_invalidates_on_memory_context_and_time_changes():
    adapter=MockAdapter();language=Language(Cognition(adapter));view=context()
    language.propose('Read the receipt','Sabina',view)
    view['minute']+=1
    language.propose('Read the receipt','Sabina',view)
    view['experiences'][0]['text']='The receipt records a different amount.'
    language.propose('Read the receipt','Sabina',view)
    assert len(adapter.calls)==3


def test_stalled_provider_is_bounded_and_does_not_queue_more_workers():
    gate=threading.Event()
    def stalled(request):gate.wait(2);return {'action':{'action':'talk','recipient':'Sabina','topic':'memory'}}
    adapter=MockAdapter(stalled)
    cognition=Cognition(adapter,policies={'intent':TaskPolicy(timeout_seconds=.01)})
    language=Language(cognition);start=time.perf_counter()
    for _ in range(3):assert language.propose('Read the receipt','Sabina',context())['ai_receipt']['fallback']
    assert time.perf_counter()-start<1
    assert len(adapter.calls)==1 and cognition.metrics['timeouts']==1
    gate.set()


def test_dialogue_cannot_invent_history_or_cite_another_character():
    view=context()
    for output in ({'text':'Lucius paid you a hundred coins','evidence_ids':[4]},
                   {'flavor_id':'plain','topic_id':'dispute','evidence_ids':[999]},
                   {'flavor_id':'plain','topic_id':'dispute','evidence_ids':[]}):
        with pytest.raises(ProposalError):validate_dialogue(output,view)
    adapter=MockAdapter({'flavor_id':'direct','topic_id':'dispute','evidence_ids':[4]})
    result=Language(Cognition(adapter)).dialogue(view,'dispute')
    assert result['reply']['text']=='Let us be clear about this. The receipt records a payment of three coins.'
    assert result['reply']['evidence_ids']==[4]


def test_character_specific_uncertainty_and_retained_relationship():
    unknown=[grounded_reply(context(name),'supply')['text'] for name in ('Felix','Sabina','Marcus','Dama')]
    assert len(set(unknown))==4
    view=context('Felix')
    view['topics']=[];view['experiences']=[{'event_id':18,'tick':5,'kind':'episodic','subject':'relationship','text':'Aelia kept the agreed promise.','source_agent':'Player'}]
    assert grounded_reply(view,'history')['text']=='Aelia kept the agreed promise.'
    assert grounded_reply(view,'history')['evidence_ids']==[18]


def test_reflection_rejects_fake_memory_and_selects_bounded_actual_records():
    view=context()
    adapter=MockAdapter({'memories':[{'evidence_id':4,'text':'Aelia stole the household silver.'}]})
    result=Language(Cognition(adapter)).reflect(view)
    assert result['receipt']['fallback']
    assert result['output']['memories']==[{'evidence_id':4,'text':'The receipt records a payment of three coins.'}]


def test_planning_only_selects_npc_plan_options_and_revises_with_context():
    adapter=MockAdapter();language=Language(Cognition(adapter));view=context()
    first=language.plan(view)
    assert first['output']['choice_id']=='verify'
    view['plan_options']=[{'id':'conserve_cash','enabled':True}]
    second=language.plan(view)
    assert second['output']['choice_id']=='conserve_cash'
    assert len(adapter.calls)==2
    malicious=Language(Cognition(MockAdapter({'choice_id':'mint_money','evidence_ids':[]}))).plan(view)
    assert malicious['receipt']['fallback']


def test_montage_and_world_content_are_scoped_drafts():
    language=Language(Cognition())
    assert language.montage(context())['output']=={'event_ids':[4]}
    draft=language.content_draft({'historical_source_ids':['H04']})['output']
    assert draft['draft'] is True
    bad=Language(Cognition(MockAdapter({'draft':False,'archetype':'commercial_dispute','source_ids':['fake']})))
    assert bad.content_draft({'historical_source_ids':['H04']})['receipt']['fallback']


def wire_response(payload,status='completed'):
    return {'id':'offline-wire-fixture','status':status,'usage':{'input_tokens':100,'output_tokens':20},
            'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(payload)}]}]}


def test_real_adapter_cannot_call_without_explicit_key_model_budget_and_rates():
    calls=[]
    adapter=OpenAIResponsesAdapter(api_key='fixture-key',model='fixture-model',transport=lambda body,timeout:calls.append(body))
    with pytest.raises(BudgetError):adapter.generate({'task':'intent'},{},TaskPolicy())
    assert calls==[] and adapter.network_calls==0
    for env in ({},{'KALENDS_AI_PROVIDER':'openai_responses'},{'KALENDS_AI_PROVIDER':'openai_responses','OPENAI_API_KEY':'fixture'}):
        cognition=Cognition.from_env(env)
        assert Language(cognition).propose('Read the receipt','Sabina',context())['interpretations']
        assert cognition.metrics['external_calls']==0


def test_responses_wire_shape_and_cost_accounting_without_network():
    bodies=[]
    def transport(body,timeout):
        bodies.append(body)
        return wire_response({'action':{'action':'examine_receipt','recipient':'Sabina'}})
    adapter=OpenAIResponsesAdapter(api_key='fixture-key',model='fixture-model',enabled=True,budget_usd=.1,
        input_usd_per_million=1,output_usd_per_million=2,transport=transport)
    language=Language(Cognition(adapter))
    result=language.propose('Read the receipt','Sabina',context())
    assert result['ai_receipt']['kind']=='transport_fixture'
    assert adapter.network_calls==0 and adapter.fixture_calls==1
    assert result['ai_receipt']['estimated_cost_usd']==pytest.approx(.00014)
    assert language.metrics['input_tokens']==100 and language.metrics['output_tokens']==20
    assert bodies[0]['store'] is False
    assert bodies[0]['text']['format']['type']=='json_schema'
    assert bodies[0]['text']['format']['strict'] is True
    assert 'fixture-key' not in json.dumps(bodies)


def test_invalid_provider_output_still_accounts_inference_cost():
    adapter=OpenAIResponsesAdapter(api_key='fixture-key',model='fixture-model',enabled=True,budget_usd=.1,
        input_usd_per_million=1,output_usd_per_million=2,
        transport=lambda body,timeout:wire_response({'action':{'action':'buy','recipient':'Lucius'}}))
    language=Language(Cognition(adapter));result=language.propose('Read the receipt','Sabina',context())
    assert result['ai_receipt']['fallback']
    assert language.metrics['estimated_cost_usd']==pytest.approx(.00028)
    assert result['ai_receipt']['estimated_cost_usd']==pytest.approx(.00028)
    assert result['ai_receipt']['unknown_cost_attempts']==0


@pytest.mark.parametrize('status',['incomplete','failed'])
def test_incomplete_provider_response_keeps_known_usage_and_cost(status):
    adapter=OpenAIResponsesAdapter(api_key='fixture-key',model='fixture-model',enabled=True,budget_usd=.1,
        input_usd_per_million=1,output_usd_per_million=2,
        transport=lambda *args:wire_response({},status=status))
    language=Language(Cognition(adapter));result=language.propose('Read the receipt','Sabina',context())
    assert result['ai_receipt']['fallback']
    assert result['ai_receipt']['estimated_cost_usd']==pytest.approx(.00028)
    assert result['ai_receipt']['input_tokens']==200 and result['ai_receipt']['output_tokens']==40
    assert adapter.spent_usd==pytest.approx(.00028)
    assert result['ai_receipt']['unknown_cost_attempts']==0


def test_missing_provider_usage_retains_reserve_and_reports_unknown_cost():
    def transport(*args):
        result=wire_response({'action':{'action':'examine_receipt','recipient':'Sabina'}})
        result.pop('usage')
        return result
    adapter=OpenAIResponsesAdapter(api_key='fixture-key',model='fixture-model',enabled=True,budget_usd=.1,
        input_usd_per_million=1,output_usd_per_million=2,transport=transport)
    result=Language(Cognition(adapter)).propose('Read the receipt','Sabina',context())
    assert result['ai_receipt']['fallback'] and adapter.spent_usd>0
    assert result['ai_receipt']['estimated_cost_usd'] is None
    assert result['ai_receipt']['unknown_cost_attempts']==2
    assert adapter.reserved_usd==0 and adapter.network_calls==0


def test_budget_refuses_before_transport_when_reserve_exceeds_remaining():
    calls=[]
    adapter=OpenAIResponsesAdapter(api_key='fixture-key',model='fixture-model',enabled=True,budget_usd=.000001,
        input_usd_per_million=10,output_usd_per_million=30,transport=lambda *args:calls.append(args))
    result=Language(Cognition(adapter)).propose('Read the receipt','Sabina',context())
    assert result['ai_receipt']['fallback'] and calls==[] and adapter.spent_usd==0


def test_local_endpoint_rejects_external_hosts_and_requires_protocol_opt_in():
    for endpoint in ('https://example.com/infer','http://192.168.0.1/infer','http://user:secret@localhost/infer'):
        with pytest.raises(ValueError):LocalJSONAdapter(endpoint)
    local=LocalJSONAdapter('http://127.0.0.1:11434/kalends')
    with pytest.raises(BudgetError):local.generate({}, {},TaskPolicy())


def test_local_protocol_rejection_and_redirect_guard_do_not_contact_a_server(monkeypatch):
    class Response:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def read(self,limit):return b'{"protocol":"unrelated-protocol","payload":{}}'
    monkeypatch.setattr(ai_module,'_open',lambda *args,**kwargs:Response())
    local=LocalJSONAdapter('http://127.0.0.1:11434/kalends',enabled=True)
    with pytest.raises(ProposalError):local.generate({}, {},TaskPolicy())
    with pytest.raises(ProposalError):ai_module._NoRedirect().redirect_request(None,None,302,'redirect',{},'https://example.com')


def test_executor_revalidates_world_proximity_and_affordability():
    world=PompeiiWorld();before=world.ledger.content_hash()
    with pytest.raises(ValueError):execute(world,{'action':'buy','recipient':'Felix','quantity':4})
    assert world.ledger.content_hash()==before
    world.move(location='bakery');before=world.ledger.content_hash()
    with pytest.raises(ValueError):execute(world,{'action':'buy','recipient':'Felix','quantity':4})
    assert world.ledger.content_hash()==before


def walk_to(world,name):
    if world._near(name):return
    location=world.state.agent_locations[name]
    if location in ('street','water','forum_access'):world.move(*world.positions[name])
    else:world.move(location=location)


def propose_and_execute(world,language,text,name):
    walk_to(world,name)
    proposal=language.propose(text,name,world.context(name))
    return execute(world,proposal['interpretations'][0]['action'])


def test_live_scenario_document_questions_preserve_paid_verification_and_broker_route():
    world=RebirthWorld();language=Language(Cognition())
    propose_and_execute(world,language,'Show me your receipt','Sabina')
    propose_and_execute(world,language,'Show me the household tablet','Dama')
    walk_to(world,'Marcus');before_cash=world.economy.cash['Player'];before_minute=world.minute
    view=world.context('Marcus')
    question=language.propose('What does the loading account say?','Marcus',view)
    assert question['reply']['evidence_ids']==[] and 'paid check' in question['reply']['text']
    execute(world,question['interpretations'][0]['action'])
    assert not world._record_known('Player','loading_record')
    assert world.economy.cash['Player']==before_cash and world.minute==before_minute
    propose_and_execute(world,language,'Pay to open the loading account','Marcus')
    assert world._record_known('Player','loading_record')
    assert world.economy.cash['Player']==before_cash-1 and world.minute>=before_minute+15
    propose_and_execute(world,language,'Bring the accounts together','Marcus')
    assert world.arc['route']=='broker'
    assert language.metrics['external_calls']==0


def test_dialogue_willingness_filters_private_known_records_before_provider():
    view=context('Marcus')
    view['experiences'].append({'event_id':900,'text':'Private withheld carrier terms.'})
    view['topics'].append({'id':'loading_record','text':'Private withheld carrier terms.','evidence_ids':[900]})
    view['disclosure_evidence_ids']=[4]
    adapter=MockAdapter({'flavor_id':'plain','topic_id':'loading_record','evidence_ids':[900]})
    result=Language(Cognition(adapter)).dialogue(view,'dispute')
    assert result['receipt']['fallback']
    assert result['reply']['evidence_ids']==[4]
    assert 'Private withheld carrier terms.' not in json.dumps(adapter.calls)
    assert grounded_reply(view,'loading_record')['epistemic_status']=='Disclosure withheld'


def test_scenario_planning_context_changes_and_history_retains_only_actual_dealings():
    world=RebirthWorld();language=Language(Cognition())
    initial=language.plan(world.context('Sabina'))
    assert initial['output']['choice_id']=='current_plan'
    propose_and_execute(world,language,'Support the market','Sabina')
    world.advance(7*1440)
    walk_to(world,'Sabina');view=world.context('Sabina')
    later=language.plan(view)
    assert later['receipt']['context_hash']!=initial['receipt']['context_hash']
    history=grounded_reply(view,'history')
    assert history['evidence_ids']
    known={e.event_id for e in world.remembered('Sabina')}
    assert set(history['evidence_ids'])<=known
    assert world.arc['route']=='market'


@pytest.mark.parametrize('text',[
    'Complete my household service','I will keep my service promise','Return for the promised service',
])
def test_migrated_service_language_selects_and_fulfills_the_actual_old_obligation(text):
    old=PompeiiWorld();old.move(location='household');old.interact('patronage','Lucius')
    world=RebirthWorld.from_legacy(old);language=Language(Cognition())
    view=world.context('Lucius')
    assert any(c['action']['action']=='service' and c['enabled'] for c in view['choices'])
    proposal=language.propose(text,'Lucius',view)
    action=proposal['interpretations'][0]['action']
    assert action['action']=='service'
    start=world.minute;execute(world,action)
    assert world.minute==start+120 and world.flags['service_done']
    assert next(c for c in world.economy.commitments['Player'] if c['id']=='household-service')['status']=='fulfilled'
    assert not world.arc['service_done']


def test_new_service_language_keeps_the_rebirth_obligation_separate():
    world=RebirthWorld();world.move(location='household');world.interact('guarantee_household','Lucius')
    language=Language(Cognition());view=world.context('Lucius')
    assert not any(c['action']['action']=='service' for c in view['choices'])
    proposal=language.propose('Complete my household service','Lucius',view)
    assert proposal['interpretations'][0]['action']['action']=='return_service'
    start=world.minute;execute(world,proposal['interpretations'][0]['action'])
    assert world.minute==start+120 and world.arc['service_done']
    assert next(c for c in world.economy.commitments['Player'] if c['id']=='rebirth-service')['status']=='fulfilled'


def test_service_is_not_invented_without_an_enabled_obligation_and_refusal_stays_talk():
    world=RebirthWorld();world.move(location='household');view=world.context('Lucius')
    language=Language(Cognition())
    assert language.propose('Complete my household service','Lucius',view)['interpretations'][0]['action']['action']=='talk'
    view['choices'].append({'action':{'action':'service','recipient':'Lucius'},'enabled':False})
    assert language.propose('Complete my household service','Lucius',view)['interpretations'][0]['action']['action']=='talk'
    with pytest.raises(ProposalError):validate_action({'action':'service','recipient':'Lucius'},'Lucius',view)
    view['choices'][-1]['enabled']=True
    assert language.propose('I will not complete household service','Lucius',view)['interpretations'][0]['action']['action']=='talk'
    malicious=Language(Cognition(MockAdapter({'action':{'action':'service','recipient':'Lucius'}})))
    actual=world.context('Lucius')
    assert malicious.propose('Complete my household service','Lucius',actual)['ai_receipt']['fallback']


def test_migrated_service_too_late_to_finish_is_not_proposed_as_a_transaction():
    old=PompeiiWorld();old.move(location='household');old.interact('patronage','Lucius')
    old.advance(old.flags['service_due']-old.minute-60)
    world=RebirthWorld.from_legacy(old);view=world.context('Lucius')
    service=next(c for c in view['choices'] if c['action']['action']=='service')
    assert not service['enabled']
    proposal=Language(Cognition()).propose('Complete my household service','Lucius',view)
    assert proposal['interpretations'][0]['action']['action']=='talk'


@pytest.mark.parametrize('extra',[
    {'topic':'PRIVATE DIARY SENTINEL'}, {'value':'PRIVATE DIARY SENTINEL'},
    {'topic':'memory'}, {'value':'available'},
])
def test_nonapplicable_action_fields_cannot_store_arbitrary_provider_text(tmp_path,extra):
    from kalends_rebirth.server import RebirthSession
    path=tmp_path/'life.json'
    adapter=MockAdapter({'action':{'action':'work','recipient':'Sabina',**extra}})
    language=Language(Cognition(adapter));session=RebirthSession(path,language=language)
    proposal=session.apply('propose',{'recipient':'Sabina','text':'I need a paid shift. PRIVATE DIARY SENTINEL'})
    action=proposal['interpretations'][0]['action']
    assert action['action']=='work' and not set(action)&{'topic','value'}
    assert language.metrics['fallbacks']==1
    session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert 'PRIVATE DIARY SENTINEL' not in path.read_text()


@pytest.mark.parametrize('payload',[None,[],42,'raw prose',{'action':[]},{'action':{'action':'talk','recipient':'Sabina','topic':'invented'}}])
def test_malformed_provider_payloads_leave_a_valid_reviewed_fallback(payload):
    # MockAdapter treats None as its authored fallback; this fixture deliberately
    # preserves actual null so the semantic boundary sees that malformed output.
    class ExplicitPayloadMock(MockAdapter):
        def generate(self,request,schema,policy):
            result=super().generate(request,schema,policy);result['payload']=payload
            return result
    adapter=ExplicitPayloadMock()
    result=Language(Cognition(adapter)).propose('Read your receipt','Sabina',context())
    assert result['ai_receipt']['fallback']
    assert result['interpretations'][0]['action']['action']=='examine_receipt'
    assert len(adapter.calls)==2


def test_quantity_review_matches_the_actual_offline_purchase_and_saved_effect(tmp_path):
    from kalends_rebirth.server import RebirthSession
    session=RebirthSession(tmp_path/'life.json',language=Language(Cognition()))
    proposal=session.apply('propose',{'recipient':'Sabina','choice_id':'work'})
    session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    session.apply('move',{'location':'bakery'})
    proposal=session.apply('propose',{'recipient':'Felix','text':'Buy four flour units'})
    choice=proposal['interpretations'][0]
    assert choice['action']['quantity']==4 and '4 flour units' in choice['label']
    assert 'one flour unit' not in choice['label']
    coins=session.original.economy.cash['Player'];price=session.original.economy.price
    session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert session.original.economy.inventory['Player']==4
    assert session.original.economy.cash['Player']==coins-4*price


def test_contextual_review_labels_require_matching_quantity_claim_and_topic():
    view={'choices':[
        {'label':'Buy one unit','action':{'action':'buy','recipient':'Felix','quantity':1}},
        {'label':'Assert availability','action':{'action':'claim','recipient':'Felix','value':'available'}},
        {'label':'Ask your role','action':{'action':'talk','recipient':'Felix','topic':'role'}},
    ]}
    assert action_label({'action':'buy','recipient':'Felix','quantity':1},view)[0]=='Buy one unit'
    assert '4 flour units' in action_label({'action':'buy','recipient':'Felix','quantity':4},view)[0]
    assert action_label({'action':'claim','recipient':'Felix','value':'available'},view)[0]=='Assert availability'
    assert 'disrupted' in action_label({'action':'claim','recipient':'Felix','value':'disrupted'},view)[0]
    assert action_label({'action':'talk','recipient':'Felix','topic':'role'},view)[0]=='Ask your role'
    assert action_label({'action':'talk','recipient':'Felix','topic':'memory'},view)[0]!='Ask your role'
