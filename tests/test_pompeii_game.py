"""End-to-end gameplay, information boundaries, and durable accepted actions."""
import copy
import json
import pytest
from kalends.pompeii.world import PompeiiWorld
from kalends.pompeii.server import PompeiiSession
from kalends.pompeii.language import ProposalLanguage


def do(session,action,recipient,**extra):
    return session.apply('interact',{'action':action,'recipient':recipient,**extra})


def test_wage_delivery_save_and_executed_alternative(tmp_path):
    path=tmp_path/'save.json';s=PompeiiSession(path)
    s.apply('move',{'location':'bakery'})
    p=s.apply('propose',{'recipient':'Felix','text':'I promise four flour units'})
    before=s.original.ledger.content_hash()
    assert s.original.flags['quest']=='unaccepted' and s.original.ledger.content_hash()==before
    s.apply('act',{'proposal_id':p['proposal_id'],'interpretation_id':'0'})
    with pytest.raises(ValueError): s.apply('act',{'proposal_id':p['proposal_id'],'interpretation_id':'0'})
    s.apply('move',{'location':'thermopolium'});do(s,'work','Sabina')
    assert s.original.economy.cash['Player']==9
    s.apply('move',{'location':'bakery'});do(s,'buy','Felix',quantity=4)
    receipt=do(s,'deliver','Felix')['receipt']
    assert s.original.flags['quest']=='fulfilled'
    assert s.original.economy.cash['Player']==7
    assert s.original.economy.inventory['Player']==0
    assert s.original.state.trust[('Felix','Player')]==.75
    restored=PompeiiSession(path)
    assert restored.original.fidelity_state()==s.original.fidelity_state()
    s.apply('mode',{'mode':'lab'})
    original=s.original.ledger.content_hash()
    s.apply('fork',{'kind':'remove_action','event_id':receipt['event_id']})
    assert s.original.ledger.content_hash()==original
    assert s.branch.flags['quest']=='active'
    assert s.branch.economy.inventory['Player']==4
    assert 'relationships' in s.state()['comparison']['changed_fields']
    restored=PompeiiSession(path)
    assert restored.branch.fidelity_state()==s.branch.fidelity_state()


def test_proximity_invalid_move_and_failed_action_are_atomic():
    s=PompeiiSession();before=s.original.fidelity_state()
    for operation,data in [('interact',{'action':'work','recipient':'Sabina'}),('move',{'x':100,'y':100}),('advance',{'minutes':-2})]:
        with pytest.raises(ValueError): s.apply(operation,data)
        assert s.original.fidelity_state()==before
        assert s.commands==[]
    s.apply('move',{'location':'bakery'})
    assert s.original.positions['Player']!=s.original.positions['Felix']
    assert s.original._near('Felix')


def test_entering_room_does_not_reveal_its_past():
    w=PompeiiWorld()
    w.advance(600)
    private=[e for e in w.ledger.events if e.payload['category']=='decision' and e.actors==('Felix',)][0]
    public=[e for e in w.ledger.events if e.payload['category']=='bread_ready'][0]
    w.move(location='bakery')
    assert not w._visible(private) and not w._visible(public)
    assert private.event_id not in [e['event_id'] for e in w.snapshot()['journal']]


def test_dated_inspection_information_sale_and_local_conversation():
    s=PompeiiSession();s.apply('move',{'x':930,'y':415})
    s.original.require_near('Marcus')
    p=s.apply('propose',{'recipient':'Marcus','text':'What have you heard about flour supply?'})
    assert 'available' in p['reply']['text']
    assert s.original.knowledge('Player')['value']=='unknown'
    s.apply('act',{'proposal_id':p['proposal_id'],'interpretation_id':'0'})
    assert s.original.knowledge('Player')['value']=='available'
    s.apply('move',{'location':'bakery'})
    do(s,'sell_information','Felix')
    assert s.original.economy.cash['Player']==8
    with pytest.raises(ValueError): do(s,'sell_information','Felix')
    do(s,'inspect','Felix')
    s.apply('advance',{'minutes':15,'mode':'compress'})
    assert s.original.knowledge('Player')['direct']
    with pytest.raises(ValueError): s.trace(2) # Marcus's private source remains hidden.
    s.apply('mode',{'mode':'lab'})
    assert s.trace(2)['events'][0]['event_id']==2


def test_patronage_has_actual_service_cost_and_long_absence_consequence():
    s=PompeiiSession();s.apply('move',{'location':'household'})
    do(s,'patronage','Lucius')
    assert s.original.economy.cash['Player']==14
    assert s.original.flags['affiliation']=='household client'
    kept=copy.deepcopy(s.original);kept.interact('service','Lucius')
    assert kept.flags['service_done'] and kept.minute==s.original.minute+120
    s.apply('advance',{'minutes':7*1440,'mode':'skip'})
    assert s.original.flags['service_missed']
    assert s.original.state.trust[('Lucius','Player')]==pytest.approx(.4)
    assert s.original.snapshot()['montage']['elapsed_minutes']==7*1440
    assert 'did not return' in ' '.join(e.text for e in s.original.remembered('Lucius'))


def test_provider_schema_scope_and_failure_fallback():
    w=PompeiiWorld();view=w.private_view('Felix')
    seen=[]
    def malicious(request):
        seen.append(request)
        return {'action':{'action':'buy','recipient':'Lucius','quantity':1},'facts':'oracle'}
    adapter=ProposalLanguage(malicious)
    result=adapter.propose('Buy two flour units','Felix',view)
    assert result['interpretations'][0]['action']['recipient']=='Felix'
    assert adapter.metrics['fallbacks']==1 and adapter.metrics['provider_calls']==2
    assert 'facts' not in seen[0]['character_view']
    assert all(e['event_id'] in [x.event_id for x in w.remembered('Felix')] for e in seen[0]['character_view']['experiences'])
    assert ProposalLanguage().metrics['known_cost_usd']==0


def test_bounded_memory_consolidation_has_no_archive_retrieval():
    w=PompeiiWorld();w.move(location='household');w.interact('patronage','Lucius');w.advance(30*1440)
    assert len(w.memories['Lucius'])<=32 and len(w.consolidated['Lucius'])<=8
    view=w.private_view('Lucius')
    retained={e.event_id for e in w.remembered('Lucius')}
    assert {e['event_id'] for e in view['experiences']}==retained
    assert len(retained)<len(w.ledger)
    assert 'did not return' in ' '.join(e['text'] for e in view['experiences'])


def test_repeated_one_observer_is_not_independent_corroboration():
    w=PompeiiWorld();w.move(location='bakery')
    for _ in range(4): w.claim('Felix','disrupted')
    assert w.knowledge('Felix')['roots']==1
    assert w.knowledge('Felix')['confidence']==pytest.approx(.55)
    w.advance(196)
    assert any(e.payload.get('choice')=='inspect' for e in w.ledger.events if e.actors==('Felix',))
    assert w.state.trust[('Felix','Player')]<.6


def test_private_opinion_is_learned_on_return_not_broadcast():
    w=PompeiiWorld();w.move(location='bakery');w.claim('Felix','disrupted');w.move(location='household');w.advance(200)
    assessment=next(e for e in w.ledger.events if e.payload['category']=='relationship' and e.actors[0]=='Felix')
    assert not w._visible(assessment)
    assert next(a for a in w.snapshot()['agents'] if a['id']=='Felix')['trust_player'] is None
    w.move(location='bakery')
    assert next(a for a in w.snapshot()['agents'] if a['id']=='Felix')['trust_player']<.6
    assert 'contradicted' in ProposalLanguage().propose('What do you remember about me?','Felix',w.private_view('Felix'))['reply']['text']


def test_optional_provider_timeout_is_bounded_and_does_not_queue_workers():
    import threading,time
    gate=threading.Event()
    def stalled(request): gate.wait(2);return {}
    language=ProposalLanguage(stalled,timeout_seconds=.01)
    view=PompeiiWorld().private_view('Felix')
    start=time.perf_counter()
    for _ in range(3): assert language.propose('Buy two flour','Felix',view)['interpretations'][0]['action']['action']=='buy'
    assert time.perf_counter()-start<1
    assert language.metrics['provider_calls']==1
    gate.set()


def test_http_serves_game_and_persists_confirmed_actions(tmp_path):
    from urllib.request import Request,urlopen
    from urllib.error import HTTPError
    import threading
    from kalends.pompeii.server import make_server
    session=PompeiiSession(tmp_path/'http.json');server=make_server(session,port=0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    def post(path,data,origin=None):
        headers={'Content-Type':'application/json'}
        if origin: headers['Origin']=origin
        return urlopen(Request(base+path,data=json.dumps(data).encode(),headers=headers),timeout=3)
    try:
        with urlopen(base+'/',timeout=3) as response:
            assert b'Playable town' in response.read()
            assert "frame-ancestors 'none'" in response.headers['Content-Security-Policy']
        with post('/api/move',{'location':'bakery'}) as response: assert json.load(response)['world']['nearby']==['Felix']
        with post('/api/propose',{'recipient':'Felix','text':'I promise four flour'}) as response: proposal=json.load(response)
        with post('/api/act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'}) as response: assert json.load(response)['receipt']['category']=='promise'
        assert PompeiiSession(tmp_path/'http.json').original.flags['quest']=='active'
        with pytest.raises(HTTPError) as error: post('/api/advance',{'minutes':1},origin='https://unrelated.example')
        assert error.value.code==403
        with pytest.raises(HTTPError): urlopen(base+'/api/export',timeout=3)
    finally: server.shutdown();server.server_close();thread.join(2)
