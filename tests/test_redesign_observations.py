import copy
import pytest
from kalends.experience_os.product import ProductService
from kalends.experience_os.observation import ParticipantOperationError, observation_trial
from kalends.experience_os.runtime import ExperienceRuntime


@pytest.fixture
def service(tmp_path):
    return ProductService(tmp_path/'redesign-qa', include_examples=False)


def start(service, template='pompeii_life'):
    data = service.start(template, guided=True)
    return service.get(data['life']['id'])


def request(runtime, action):
    return {'action':action, 'expected_revision':len(runtime.commands), 'expected_state_hash':runtime.state_hash()}


def invariant(runtime):
    return (runtime.state_hash(), copy.deepcopy(runtime.commands), runtime.journal_path.read_bytes())


def test_observation_is_private_until_accepted_and_reconciles_after_restart(service):
    runtime = start(service)
    action = {'action':'examine_receipt','recipient':'Sabina'}
    before = invariant(runtime)
    context = service.game(runtime.spec.id).context('Sabina')
    assert next(t for t in context['topics'] if t['id']=='market_receipt')['withheld']
    assert not runtime.world._record_known('Player','market_receipt')
    assert before == invariant(runtime)
    q = request(runtime, action)
    response = service.observe(runtime.spec.id, q, scene=True)
    assert response['outcome'] == 'accepted'
    assert response['receipt']['kind']=='receipt'
    assert response['reply']['voice']=='person'
    assert runtime.minute == 0 and runtime.world.economy.cash['Player']==6
    assert runtime.commands == [{'revision':1,'operation':'action','data':action,'at':0,'after':0,'receipt_id':response['receipt']['event_id']}]
    saved = invariant(runtime)
    assert service.observe(runtime.spec.id, q, scene=True)['outcome']=='already_accepted'
    assert saved == invariant(runtime)
    restarted = ProductService(service.directory, include_examples=False)
    response2 = restarted.observe(runtime.spec.id, q, scene=True)
    assert response2['outcome']=='already_accepted'
    assert response2['observation_id']==response['observation_id']
    assert saved == invariant(restarted.get(runtime.spec.id))
    assert not next(t for t in response2['conversation']['topics'] if t['id']=='market_receipt')['withheld']


@pytest.mark.parametrize('action',[
    {'action':'support_market','recipient':'Sabina'},
    {'action':'hear_dispute','recipient':'Lucius'},
    {'action':'hear_dispute','recipient':'Sabina','quantity':1},
    {'action':'hear_dispute','recipient':'Sabina','actor':'Player'},
    {'action':'talk','recipient':'Sabina','topic':'documents'},
    {'action':'verify_cart','recipient':'Marcus'},
    {'action':'hear_dispute','recipient':[]},
])
def test_observation_whitelist_is_exact_and_rejects_without_mutation(service, action):
    runtime = start(service); before=invariant(runtime)
    with pytest.raises(ParticipantOperationError):
        service.observe(runtime.spec.id, request(runtime,action))
    assert before == invariant(runtime)


def test_stale_question_cannot_execute_or_claim_a_different_receipt(service):
    runtime=start(service)
    q=request(runtime,{'action':'hear_dispute','recipient':'Sabina'})
    service.observe(runtime.spec.id,request(runtime,{'action':'examine_receipt','recipient':'Sabina'}))
    before=invariant(runtime)
    with pytest.raises(ParticipantOperationError) as exc:
        service.observe(runtime.spec.id,q)
    assert exc.value.code=='observation_stale'
    assert before==invariant(runtime)


def test_wrong_hash_cannot_claim_existing_receipt(service):
    runtime=start(service);q=request(runtime,{'action':'hear_dispute','recipient':'Sabina'})
    service.observe(runtime.spec.id,q)
    q['expected_state_hash']='0'*64
    with pytest.raises(ParticipantOperationError) as exc: service.observe(runtime.spec.id,q)
    assert exc.value.code=='observation_stale'
    assert len(runtime.commands)==1


def test_observation_save_failure_rolls_back_and_identical_retry_is_safe(service, monkeypatch):
    runtime=start(service);q=request(runtime,{'action':'hear_dispute','recipient':'Sabina'});before=invariant(runtime)
    original=ExperienceRuntime.save
    monkeypatch.setattr(ExperienceRuntime,'save',lambda self: (_ for _ in ()).throw(OSError('fixture disk failure')))
    with pytest.raises(OSError):service.observe(runtime.spec.id,q)
    assert before==invariant(runtime)
    monkeypatch.setattr(ExperienceRuntime,'save',original)
    assert service.observe(runtime.spec.id,q)['outcome']=='accepted'
    assert len(runtime.commands)==1


def test_free_trial_cannot_hide_a_resource_charge(service, monkeypatch):
    runtime=start(service);before=invariant(runtime); original=ExperienceRuntime._perform
    def changed(self,operation,data):
        result=original(self,operation,data)
        self.world.economy.cash['Player']-=1
        return result
    monkeypatch.setattr(ExperienceRuntime,'_perform',changed)
    with pytest.raises(ParticipantOperationError) as exc:observation_trial(runtime,{'action':'hear_dispute','recipient':'Sabina'})
    assert exc.value.code=='observation_not_free'
    assert before==invariant(runtime)


def test_unavailable_distant_document_stays_private(service):
    runtime=start(service);before=invariant(runtime)
    with pytest.raises(ValueError):service.observe(runtime.spec.id,request(runtime,{'action':'examine_tablet','recipient':'Dama'}))
    assert before==invariant(runtime)


def test_commons_legitimate_free_report_and_unknown_report_rejection(service, monkeypatch):
    runtime=start(service,'shared_observatory');credits=runtime.world.economy.cash['Player']
    assert not service.life(runtime.spec.id)['snapshot']['own_reports']
    q=request(runtime,{'action':'share','recipient':'team_b'})
    response=service.observe(runtime.spec.id,q)
    assert response['outcome']=='accepted'
    assert runtime.minute==0 and runtime.world.economy.cash['Player']==credits
    assert response['guide']['known']['report']['usable']==8
    monkeypatch.setattr(runtime.minds['team_c'], 'retained_event_ids', lambda: ())
    before=invariant(runtime)
    with pytest.raises(ValueError):service.observe(runtime.spec.id,request(runtime,{'action':'share','recipient':'team_c'}))
    assert before==invariant(runtime)


def test_open_round_zero_promise_rejected_without_mutation(service):
    runtime=start(service,'shared_observatory');before=invariant(runtime)
    assert not service.life(runtime.spec.id)['snapshot']['round_closed']
    with pytest.raises(ValueError):service.review(runtime.spec.id,{'action':'commit','recipient':'team_c','quantity':0})
    assert before==invariant(runtime)
    assert service.life(runtime.spec.id)['snapshot']['promises']=={}


def test_closed_round_positive_promise_is_separately_rejected(service):
    runtime=start(service,'shared_observatory');runtime.commit('advance',{'minutes':1439,'mode':'compress'});before=invariant(runtime)
    assert service.life(runtime.spec.id)['snapshot']['round_closed']
    with pytest.raises(ValueError,match='settled'):service.review(runtime.spec.id,{'action':'commit','recipient':'team_c','quantity':1})
    assert before==invariant(runtime)


def test_paid_review_typed_duplicate_stale_unknown_do_not_repeat_cost(service):
    runtime=start(service);q=service.review(runtime.spec.id,{'action':'support_market','recipient':'Sabina'})
    assert service.confirm_review(runtime.spec.id,q['proposal_id'])['outcome']=='accepted'
    before=invariant(runtime)
    assert service.confirm_review(runtime.spec.id,q['proposal_id'])['outcome']=='already_accepted'
    assert before==invariant(runtime)
    with pytest.raises(ParticipantOperationError) as exc:service.confirm_review(runtime.spec.id,'not-a-review')
    assert exc.value.code=='outcome_unknown'
    other=start(service);q=service.review(other.spec.id,{'action':'support_market','recipient':'Sabina'})
    service.observe(other.spec.id,request(other,{'action':'hear_dispute','recipient':'Sabina'}))
    before=invariant(other)
    with pytest.raises(ParticipantOperationError) as exc:service.confirm_review(other.spec.id,q['proposal_id'])
    assert exc.value.code=='offer_changed'
    assert before==invariant(other)
