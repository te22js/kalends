import copy
import json
from kalends.experience_os.product import ProductService
from kalends.experience_os.history_cards import cards_for


def new(service):
    return service.get(service.start('pompeii_life',guided=True)['life']['id'])


def test_grounded_return_changes_after_accepted_choice_and_omission_does_not_thank(tmp_path):
    service=ProductService(tmp_path,include_examples=False)
    chosen,omitted=new(service),new(service)
    chosen.commit('action',{'action':'support_market','recipient':'Sabina'})
    omitted.commit('advance',{'minutes':20,'mode':'compress'})
    assert chosen.minute==omitted.minute
    before=(chosen.state_hash(),copy.deepcopy(chosen.commands))
    yes=service.game(chosen.spec.id).context('Sabina')
    no=service.game(omitted.spec.id).context('Sabina')
    assert 'Thank you' in yes['greeting']['text']
    assert 'Thank you' not in no['greeting']['text']
    assert yes['greeting']['kind']=='recalled_response'
    supported=set(yes['greeting']['evidence_ids'])
    assert supported<=chosen.visible_ids()
    assert supported<={e.event_id for e in chosen.world.remembered('Sabina') if e.accepted}
    assert len(supported)==2
    assert before==(chosen.state_hash(),chosen.commands)
    # A separate controlled forgetting ablation removes just the originating
    # agreement from the actual bounded speaker stores, never the global ledger.
    agreement=next(e['event_id'] for e in chosen.events() if e['payload'].get('category')=='rb_agreement')
    chosen.world.memories['Sabina']=[e for e in chosen.world.memories['Sabina'] if e.event_id!=agreement]
    chosen.world.consolidated['Sabina']=[e for e in chosen.world.consolidated['Sabina'] if e.event_id!=agreement]
    forgotten=service.game(chosen.spec.id).context('Sabina')
    assert 'Thank you' not in forgotten['greeting']['text']
    assert forgotten['greeting']['kind']=='recalled_observation'
    assert 'received 4 flour units' in forgotten['greeting']['text']


def test_participant_default_voice_does_not_reveal_numeric_regard_or_diagnostics(tmp_path):
    service=ProductService(tmp_path,include_examples=False);runtime=new(service)
    context=service.game(runtime.spec.id).context('Sabina')
    assert 'relationship' not in context
    assert all(t.get('voice') in {'person','notebook'} for t in context['topics'])
    text=' '.join([context['greeting']['text'],*[t['text'] for t in context['topics']]])
    assert not any(word in text for word in ('retained memory','admitted','For now, I must'))
    runtime.commit('action',{'action':'support_market','recipient':'Sabina'})
    life=service.life(runtime.spec.id)
    assert 'regard' not in json.dumps(life['guide']['result'])
    assert not any('remembers whose claim' in b['text'] for b in life['history']['beats'])
    assert all('relationship' not in a for a in life['snapshot']['world']['agents'])
    assert any('relationship_axes' in e['payload'] for e in runtime.events()) # canonical data unchanged


def test_history_layers_have_qualified_source_crosswalks_and_limits():
    cards=cards_for({'world':{'player':{'location':'thermopolium'}}},[])
    for card in cards:
        assert card['voice']=='historian'
        assert card['primary']['text']==card['claim']
        assert [d['label'] for d in card['details']]==['Evidence','Reconstruction','Fictional gameplay']
        assert card['limits'] in card['details'][0]['text']
        for source in card['sources']:
            assert source['qualified_id'].startswith('first-session-history-v1:')
            assert source['ledger_crosswalk']==source['id']
    notices=next(c for c in cards if c['id']=='wall_notices')
    assert 'could name' in notices['claim']


def test_request_smaller_than_project_is_displayed_honestly(tmp_path):
    service=ProductService(tmp_path,include_examples=False)
    life=service.start('shared_observatory',guided=True)
    assert life['snapshot']['requests']['team_b']==2
    requirement=next(p for p in life['guide']['known']['project_requirements'] if p['actor']=='team_b')
    assert requirement['quantity']==4
    assert 'no partial project completion' in requirement['completion_rule']
    assert 'Day 2, 00:00' in requirement['text']
    assert 'deadline minute' not in requirement['text']


def test_typed_document_preview_uses_same_privacy_boundary_as_context(tmp_path):
    service=ProductService(tmp_path,include_examples=False);runtime=new(service)
    facade=service.game(runtime.spec.id)
    before=runtime.state_hash(),len(runtime.commands)
    proposal=facade.propose({'recipient':'Sabina','text':'May I see the receipt?'})
    assert 'Two flour units' not in json.dumps(proposal)
    assert before==(runtime.state_hash(),len(runtime.commands))
    accepted=facade.act({'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert runtime.world._record_known('Player','market_receipt')
    assert 'Two flour units' in json.dumps(accepted['conversation'])
    assert accepted['reply']['voice'] in {'person','notebook'}


def test_current_report_reply_has_actual_origin_and_age(tmp_path):
    service=ProductService(tmp_path,include_examples=False)
    runtime=service.get(service.start('shared_observatory')['life']['id'])
    reply=service.observe(runtime.spec.id,{'action':{'action':'share','recipient':'team_b'},'expected_revision':0,'expected_state_hash':runtime.state_hash()})
    mira=next(p for p in reply['people'] if p['id']=='team_b')
    assert mira['reply']=='I observed 8 usable units at Day 1, 00:00.'
    assert mira['known_report']['origin_observer']=='team_b'
    assert mira['known_report']['received_at']==0
    assert 'out of date' not in reply['guide']['step']['body']


def test_forgetting_does_not_hide_an_enforceable_household_obligation(tmp_path):
    service=ProductService(tmp_path,include_examples=False);runtime=new(service)
    runtime.commit('action',{'action':'move','location':'household'})
    runtime.commit('action',{'action':'guarantee_household','recipient':'Lucius'})
    known=service.life(runtime.spec.id)['known_commitments']
    assert len(known)==1 and known[0]['quantity']==120
    # Controlled bounded-memory ablation, not a claimed naturally occurring
    # forgetful episode or a human playtest. The institutional register persists.
    runtime.world.memories['Lucius']=[]
    runtime.world.consolidated['Lucius']=[]
    context=service.game(runtime.spec.id).context('Lucius')
    memory=next(t for t in context['topics'] if t['id']=='memory')
    assert memory['text']=='I don’t remember us doing business before.'
    assert context['obligations'][0]['kind']=='obligation_reminder'
    assert '120 minutes' in context['obligations'][0]['text']
    assert service.life(runtime.spec.id)['known_commitments']==known


def test_project_need_question_uses_public_register_without_mutation_or_hidden_condition(tmp_path):
    service = ProductService(tmp_path, include_examples=False)
    ident = service.start('shared_observatory', guided=True)['life']['id']
    runtime = service.get(ident)
    before = (runtime.state_hash(), copy.deepcopy(runtime.commands))
    answer = service.intention(ident, 'What does your project need?', 'team_a')
    assert answer['kind'] == 'public_record'
    assert '4 units in one delivery' in answer['reply']
    assert 'not submitted a request' in answer['reply']
    assert 'fragile' not in answer['reply'] and '8 usable' not in answer['reply']
    assert 'action' not in answer and 'proposal_id' not in answer
    assert before == (runtime.state_hash(), runtime.commands)
