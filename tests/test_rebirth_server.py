"""Reviewed actions, scoped game views, durable replay and local HTTP boundaries."""
from __future__ import annotations

import copy
from http.client import HTTPConnection
import json
import threading

import pytest

from kalends.pompeii.server import PompeiiSession
from kalends_rebirth.ai import Cognition, MockAdapter
from kalends_rebirth.language import Language
from kalends_rebirth.server import RebirthSession, make_server


def session_at(path=None):
    # Tests never select configured providers or read credentials.
    return RebirthSession(path,language=Language(Cognition()))


def choose(session,choice='examine_receipt',recipient='Sabina'):
    proposal=session.apply('propose',{'recipient':recipient,'choice_id':choice})
    return session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})


def fingerprint(session):
    return (session.original.ledger.content_hash(),session.original.fidelity_state(),copy.deepcopy(session.commands),
            session.mode,session.telemetry_enabled,copy.deepcopy(session.product_events),
            session.branch.ledger.content_hash() if session.branch else None,copy.deepcopy(session.intervention))


def test_contextual_choice_requires_once_only_review_and_returns_copies():
    session=session_at();before=fingerprint(session)
    proposal=session.apply('propose',{'recipient':'Sabina','choice_id':'support_market'})
    assert fingerprint(session)==before
    assert proposal['interpretations'][0]['cost']=='3 coins'
    # Editing an HTTP response cannot alter the server's stored reviewed action.
    proposal['interpretations'][0]['action']['action']='create_money'
    request={'proposal_id':proposal['proposal_id'],'interpretation_id':'0'}
    result=session.apply('act',request)
    assert session.original.arc['route']=='market'
    assert session.original.economy.cash['Player']==3
    assert result['receipt']['payload']['category'] in ('rb_agreement','rb_resolution')
    accepted=fingerprint(session)
    with pytest.raises(ValueError):session.apply('act',request)
    assert fingerprint(session)==accepted


def test_proposals_expire_on_committed_world_revision_and_unavailable_choice_is_rejected():
    session=session_at()
    proposal=session.apply('propose',{'recipient':'Sabina','choice_id':'support_market'})
    session.apply('advance',{'minutes':1})
    before=fingerprint(session)
    with pytest.raises(ValueError):session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    with pytest.raises(ValueError):session.apply('propose',{'recipient':'Sabina','choice_id':'create_money'})
    session.apply('move',{'x':930,'y':415});before=fingerprint(session)
    with pytest.raises(ValueError):session.apply('propose',{'recipient':'Marcus','choice_id':'mediate'})
    assert fingerprint(session)==before


def test_invalid_interpretation_or_injected_action_cannot_bypass_review():
    session=session_at();proposal=session.apply('propose',{'recipient':'Sabina','choice_id':'examine_receipt'})
    before=fingerprint(session)
    with pytest.raises(ValueError):session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'999','action':'support_market'})
    with pytest.raises(ValueError):session.apply('action',{'action':'support_market','recipient':'Sabina'})
    assert fingerprint(session)==before


def test_game_hides_private_world_context_and_ai_receipts_while_lab_exposes_operator_tools():
    session=session_at()
    private_id=session.original.documents['loading_record']['event_id']
    game=session.state()
    assert 'operator' not in game['world'] and game['branch'] is None and game['intervention'] is None
    assert 'product_metrics' not in game and 'removable_actions' not in game
    for agent in game['world']['agents']:
        assert not set(agent)&{'experiences','beliefs','cash','inventory','commitments','plan_options'}
    assert private_id not in [e['event_id'] for e in game['world']['journal']]
    with pytest.raises(ValueError):session.trace(private_id)
    context=session.context('Sabina')
    assert not set(context)&{'experiences','beliefs','cash','inventory','plan','plan_options','disclosure_evidence_ids'}
    proposal=session.apply('propose',{'recipient':'Sabina','text':'Read your receipt'})
    assert 'ai_receipt' not in proposal
    session.apply('mode',{'mode':'lab'})
    operator=session.state()
    assert 'operator' in operator['world'] and 'receipts' in operator['language']
    assert session.trace(private_id)['events'][-1]['event_id']==private_id
    proposal=session.apply('propose',{'recipient':'Sabina','text':'Read your receipt'})
    assert 'ai_receipt' in proposal


def test_game_language_status_does_not_claim_offline_for_an_injected_adapter():
    session=RebirthSession(language=Language(Cognition(MockAdapter())))
    status=session.state()['language']
    assert status.get('mode')!='offline'
    assert not set(status)&{'receipts','metrics','estimated_budget_remaining_usd'}


def test_replay_recovers_world_and_actions_without_raw_typed_text(tmp_path):
    path=tmp_path/'life.json';session=session_at(path)
    private_text='Show me your receipt. My private diary belongs to me.'
    proposal=session.apply('propose',{'recipient':'Sabina','text':private_text})
    session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    session.apply('advance',{'minutes':90,'mode':'compress'})
    restored=session_at(path)
    assert restored.original.fidelity_state()==session.original.fidelity_state()
    assert restored.original.ledger.content_hash()==session.original.ledger.content_hash()
    assert restored.commands==session.commands and restored.proposals=={}
    assert private_text not in path.read_text()
    assert json.loads(path.read_text())['version']==4


def test_tampered_replay_and_older_save_are_rejected_without_modification(tmp_path):
    path=tmp_path/'life.json';session=session_at(path);choose(session)
    payload=json.loads(path.read_text());payload['ledger_hash']='tampered';path.write_text(json.dumps(payload))
    before=path.read_bytes()
    with pytest.raises(ValueError,match='replay differs'):session_at(path)
    assert path.read_bytes()==before
    old=tmp_path/'older.json';old.write_text('{"version":3}')
    before=old.read_bytes()
    with pytest.raises(ValueError,match='older save'):session_at(old)
    assert old.read_bytes()==before


def test_legacy_migration_preserves_source_bytes_and_replays_to_new_destination(tmp_path):
    source=tmp_path/'pompeii.json';legacy=PompeiiSession(source)
    legacy.apply('move',{'location':'bakery'})
    legacy.apply('interact',{'action':'accept_delivery','recipient':'Felix'})
    legacy.apply('advance',{'minutes':15})
    original_bytes=source.read_bytes();old_events=legacy.original.ledger.to_json()
    destination=tmp_path/'rebirth.json'
    migrated=RebirthSession(destination,migrate_from=source,language=Language(Cognition()))
    assert source.read_bytes()==original_bytes
    assert migrated.original.ledger.to_json()[:len(old_events)]==old_events
    assert migrated.original.flags['quest']=='active'
    assert migrated.original.economy.cash['Player']==legacy.original.economy.cash['Player']
    restored=session_at(destination)
    assert restored.original.fidelity_state()==migrated.original.fidelity_state()
    with pytest.raises(ValueError):RebirthSession(source,migrate_from=source,language=Language(Cognition()))
    assert source.read_bytes()==original_bytes
    payload=json.loads(original_bytes);payload['ledger_hash']='tampered';source.write_text(json.dumps(payload))
    rejected_bytes=source.read_bytes();rejected=tmp_path/'rejected.json'
    with pytest.raises(ValueError,match='Legacy replay hash'):RebirthSession(rejected,migrate_from=source,language=Language(Cognition()))
    assert source.read_bytes()==rejected_bytes and not rejected.exists()


@pytest.mark.parametrize('operation,data',[
    ('move',{'x':100,'y':100}),('move',{'x':float('nan'),'y':415}),
    ('advance',{'minutes':-1}),('advance',{'minutes':True}),
    ('advance',{'minutes':1,'mode':'naive'}),('move',{'location':'bakery','cash':100}),
])
def test_rejected_world_commands_leave_memory_ledger_and_save_untouched(tmp_path,operation,data):
    path=tmp_path/'life.json';session=session_at(path);session.save()
    before=fingerprint(session);old_bytes=path.read_bytes()
    with pytest.raises(ValueError):session.apply(operation,data)
    assert fingerprint(session)==before and path.read_bytes()==old_bytes


def test_rejected_confirmed_purchase_is_atomic_and_review_remains_available(tmp_path):
    path=tmp_path/'life.json';session=session_at(path);session.apply('move',{'location':'bakery'})
    proposal=session.apply('propose',{'recipient':'Felix','text':'Buy four flour units'})
    before=fingerprint(session);old_bytes=path.read_bytes()
    with pytest.raises(ValueError):session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert fingerprint(session)==before and path.read_bytes()==old_bytes
    assert proposal['proposal_id'] in session.proposals


def fail_save():raise OSError('simulated disk full')


def test_world_save_failure_rolls_back_and_same_review_can_be_retried(tmp_path,monkeypatch):
    path=tmp_path/'life.json';session=session_at(path);session.save()
    proposal=session.apply('propose',{'recipient':'Sabina','choice_id':'support_market'})
    before=fingerprint(session);old_bytes=path.read_bytes();original_save=session.save
    monkeypatch.setattr(session,'save',fail_save)
    request={'proposal_id':proposal['proposal_id'],'interpretation_id':'0'}
    with pytest.raises(OSError):session.apply('act',request)
    assert fingerprint(session)==before and path.read_bytes()==old_bytes
    assert proposal['proposal_id'] in session.proposals
    monkeypatch.setattr(session,'save',original_save);session.apply('act',request)
    assert session.original.arc['route']=='market'


@pytest.mark.parametrize('operation,data',[
    ('mode',{'mode':'lab'}),('settings',{'telemetry_enabled':True}),
])
def test_settings_and_view_save_failure_roll_back_all_session_state(tmp_path,monkeypatch,operation,data):
    path=tmp_path/'life.json';session=session_at(path);session.save()
    before=fingerprint(session);old_bytes=path.read_bytes()
    monkeypatch.setattr(session,'save',fail_save)
    with pytest.raises(OSError):session.apply(operation,data)
    assert fingerprint(session)==before and path.read_bytes()==old_bytes


def test_counterfactual_removes_real_action_preserves_original_and_replays_on_restart(tmp_path):
    path=tmp_path/'life.json';session=session_at(path)
    receipt=choose(session,'support_market')['receipt']
    session.apply('advance',{'minutes':60})
    before=session.original.ledger.content_hash()
    with pytest.raises(ValueError):session.apply('fork',{'kind':'remove_action','event_id':receipt['event_id']})
    session.apply('mode',{'mode':'lab'})
    session.apply('fork',{'kind':'remove_action','event_id':receipt['event_id']})
    assert session.original.ledger.content_hash()==before and session.original.arc['route']=='market'
    assert session.branch.arc['route'] is None
    assert session.branch.minute==session.original.minute
    assert 'rebirth' in session.state()['comparison']['changed_fields']
    restored=session_at(path)
    assert restored.branch.fidelity_state()==session.branch.fidelity_state()
    assert restored.intervention==session.intervention
    session.apply('mode',{'mode':'game'})
    assert session.state()['branch'] is None and session.state()['comparison'] is None
    assert session.state()['intervention'] is None


def test_fork_save_failure_leaves_previous_alternative_intact(tmp_path,monkeypatch):
    session=session_at(tmp_path/'life.json');receipt=choose(session,'support_market')['receipt']
    session.apply('mode',{'mode':'lab'});before=fingerprint(session)
    monkeypatch.setattr(session,'save',fail_save)
    with pytest.raises(OSError):session.apply('fork',{'kind':'remove_action','event_id':receipt['event_id']})
    assert fingerprint(session)==before


def test_later_commands_do_not_create_a_different_branch_only_after_restart(tmp_path):
    path=tmp_path/'life.json';session=session_at(path)
    receipt=choose(session,'support_market')['receipt']
    session.apply('mode',{'mode':'lab'})
    session.apply('fork',{'kind':'remove_action','event_id':receipt['event_id']})
    session.apply('advance',{'minutes':60})
    restored=session_at(path)
    assert restored.original.fidelity_state()==session.original.fidelity_state()
    assert bool(restored.branch)==bool(session.branch)
    if session.branch:
        assert restored.branch.fidelity_state()==session.branch.fidelity_state()
        assert restored.intervention==session.intervention


def test_removing_required_checked_document_discloses_infeasible_later_mediation():
    session=session_at();choose(session,'examine_receipt')
    session.apply('move',{'x':850,'y':430});choose(session,'examine_tablet','Dama')
    session.apply('move',{'x':930,'y':415});checked=choose(session,'verify_cart','Marcus')['receipt']
    choose(session,'mediate','Marcus')
    assert session.original.arc['route']=='broker'
    session.apply('mode',{'mode':'lab'})
    session.apply('fork',{'kind':'remove_action','event_id':checked['event_id']})
    assert session.branch.arc['route'] is None
    assert any('document' in item['reason'].lower() or 'opportunity' in item['reason'].lower() for item in session.intervention['skipped'])


def test_telemetry_is_opt_in_local_persistent_and_never_stores_typed_proposals(tmp_path):
    path=tmp_path/'life.json';session=session_at(path)
    session.apply('product-event',{'event':'start','detail':{'screen':'opening'}})
    assert session.product_events==[]
    session.apply('settings',{'telemetry_enabled':True})
    session.apply('product-event',{'event':'journal_open','detail':{'screen':'journal'}})
    text='My private typed diary contains a secret'
    session.apply('propose',{'recipient':'Sabina','text':text})
    restored=session_at(path)
    assert restored.telemetry_enabled and len(restored.product_events)==1
    assert text not in path.read_text() and 'product_metrics' not in restored.state()
    session.apply('settings',{'telemetry_enabled':False});size=len(session.product_events)
    session.apply('product-event',{'event':'return','detail':{'screen':'journal'}})
    assert len(session.product_events)==size


@pytest.mark.parametrize('text,action',[
    ('Who are you?','talk'),('Flour supply is disrupted','claim'),
])
def test_telemetry_enabled_typed_dialogue_and_assertions_commit_normally(tmp_path,text,action):
    path=tmp_path/'life.json';session=session_at(path)
    session.apply('settings',{'telemetry_enabled':True})
    proposal=session.apply('propose',{'recipient':'Sabina','text':text})
    session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert session.commands[-1]['data']['action']==action
    assert session.product_events[-1]['detail']=={'choice':action}
    restored=session_at(path)
    assert restored.original.fidelity_state()==session.original.fidelity_state()
    assert restored.product_events==session.product_events


def test_product_event_persistence_failure_does_not_leave_an_unsaved_note(tmp_path,monkeypatch):
    path=tmp_path/'life.json';session=session_at(path)
    session.apply('settings',{'telemetry_enabled':True})
    before=fingerprint(session);old_bytes=path.read_bytes()
    monkeypatch.setattr(session,'save',fail_save)
    with pytest.raises(OSError):session.apply('product-event',{'event':'journal_open','detail':{'screen':'journal'}})
    assert fingerprint(session)==before and path.read_bytes()==old_bytes


def test_failed_action_persistence_rolls_back_its_decision_note_in_the_same_transaction(tmp_path,monkeypatch):
    path=tmp_path/'life.json';session=session_at(path)
    session.apply('settings',{'telemetry_enabled':True})
    proposal=session.apply('propose',{'recipient':'Sabina','choice_id':'support_market'})
    before=fingerprint(session);old_bytes=path.read_bytes();save=session.save
    monkeypatch.setattr(session,'save',fail_save)
    request={'proposal_id':proposal['proposal_id'],'interpretation_id':'0'}
    with pytest.raises(OSError):session.apply('act',request)
    assert fingerprint(session)==before and path.read_bytes()==old_bytes
    monkeypatch.setattr(session,'save',save);session.apply('act',request)
    assert len(session.product_events)==1
    assert session.product_events[0]['event']=='decision'
    restored=session_at(path)
    assert restored.product_events==session.product_events


def test_decision_note_validation_failure_rolls_back_world_before_save(tmp_path,monkeypatch):
    path=tmp_path/'life.json';session=session_at(path)
    session.apply('settings',{'telemetry_enabled':True})
    proposal=session.apply('propose',{'recipient':'Sabina','choice_id':'support_market'})
    before=fingerprint(session);old_bytes=path.read_bytes()
    def reject_note(*args):raise ValueError('Rejected categorical note fixture')
    monkeypatch.setattr(session,'record_product',reject_note)
    with pytest.raises(ValueError):session.apply('act',{'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    assert fingerprint(session)==before and path.read_bytes()==old_bytes


@pytest.mark.parametrize('data',[
    {'event':'raw_message','detail':{}},
    {'event':'conversation_open','detail':{'text':'private diary'}},
    {'event':'conversation_open','detail':{'choice':'My private typed diary'}},
    {'event':'conversation_open','detail':{'screen':'x'*81}},
    {'event':'conversation_open','detail':{'location':False}},
])
def test_telemetry_rejects_free_text_and_unbounded_or_non_categorical_metadata(data):
    session=session_at();session.apply('settings',{'telemetry_enabled':True});before=fingerprint(session)
    with pytest.raises(ValueError):session.apply('product-event',data)
    assert fingerprint(session)==before


@pytest.fixture
def http_game():
    session=session_at();server=make_server(session,port=0)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def request(method,path,body=None,headers=None):
        connection=HTTPConnection('127.0.0.1',server.server_port,timeout=2)
        try:
            connection.request(method,path,body=body,headers=headers or {})
            response=connection.getresponse();raw=response.read()
            try:payload=json.loads(raw)
            except (ValueError,UnicodeDecodeError):payload=raw
            return response.status,dict(response.getheaders()),payload
        finally:connection.close()
    yield session,server,request
    server.shutdown();server.server_close();thread.join(2)


def test_http_game_review_persistence_and_security_headers(http_game):
    session,server,request=http_game
    status,headers,state=request('GET','/api/state')
    assert status==200 and state['mode']=='game'
    assert headers['Cache-Control']=='no-store' and headers['X-Content-Type-Options']=='nosniff'
    assert "frame-ancestors 'self'" in headers['Content-Security-Policy']
    body=json.dumps({'recipient':'Sabina','choice_id':'support_market'})
    before=session.original.ledger.content_hash()
    status,_,proposal=request('POST','/api/propose',body,{'Content-Type':'application/json'})
    assert status==200 and session.original.ledger.content_hash()==before
    status,_,result=request('POST','/api/act',json.dumps({'proposal_id':proposal['proposal_id'],'interpretation_id':'0'}),{'Content-Type':'application/json'})
    assert status==200 and result['world']['story']['route']=='market'
    assert len(session.commands)==1


def test_http_rejects_host_origin_nonfinite_oversized_and_nonobject_inputs(http_game):
    session,server,request=http_game;before=fingerprint(session)
    assert request('GET','/api/state',headers={'Host':'evil.example'})[0]==403
    assert request('POST','/api/mode','{"mode":"lab"}',{'Content-Type':'application/json','Origin':'https://evil.example'})[0]==403
    for body,headers in [
        ('{"x":NaN,"y":415}',{'Content-Type':'application/json'}),
        ('[]',{'Content-Type':'application/json'}),
        ('{"x":930,"y":415}',{'Content-Type':'text/plain'}),
        ('{}',{'Content-Type':'application/json','Content-Length':'16385'}),
    ]:
        assert request('POST','/api/move',body,headers)[0]==400
    assert fingerprint(session)==before


def test_http_archive_export_and_path_traversal_boundaries(http_game):
    session,server,request=http_game
    assert request('GET','/api/export')[0]==400
    assert request('GET','/../server.py')[0]==404
    assert request('GET','/%2e%2e/server.py')[0]==404
    assert request('GET','/api/trace?event_id=999999')[0]==400
    session.apply('mode',{'mode':'lab'})
    status,_,archive=request('GET','/api/export')
    assert status==200 and archive['version']==4
    assert len(archive['events'])==len(session.original.ledger)
    assert 'operator' in archive['state']['world']


def test_http_save_failure_returns_redacted_500_and_leaves_the_review_retryable(http_game,monkeypatch):
    session,server,request=http_game
    proposal=session.apply('propose',{'recipient':'Sabina','choice_id':'support_market'})
    before=fingerprint(session);save=session.save
    def disk_failure():raise OSError('/private/sensitive/credential-file simulated failure')
    monkeypatch.setattr(session,'save',disk_failure)
    body=json.dumps({'proposal_id':proposal['proposal_id'],'interpretation_id':'0'})
    status,_,response=request('POST','/api/act',body,{'Content-Type':'application/json'})
    assert status==500 and 'error' in response
    assert 'sensitive' not in json.dumps(response) and 'credential-file' not in json.dumps(response)
    assert fingerprint(session)==before
    monkeypatch.setattr(session,'save',save)
    assert request('POST','/api/act',body,{'Content-Type':'application/json'})[0]==200
