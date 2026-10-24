import copy
import json
import pytest
from kalends.continuity_release.evaluation import (
    ARMS, Controller, WorkflowWorld, canonical, new_mind, run_case, score, validate, verify_candidate,
)
from kalends_rebirth.minds import Episode


def fixture():
    return {'version': 1, 'cases': [{
        'id':'fixture', 'family':'operational_test', 'label':'Harness semantics fixture',
        'horizon_minutes':10080, 'credits':4,
        'initial_facts':[{'subject':'job','predicate':'status','value':'open','public':True},
                         {'subject':'parcel','predicate':'destination','value':'north'},
                         {'subject':'parcel','predicate':'copies','value':'0','public':True}],
        'timeline':[{'at':0,'subject':'parcel','predicate':'destination','value':'north','visibility':'direct'}],
        'goals':[{'id':'deliver','label':'Deliver the parcel','priority':90,'deadline':10080,
                  'complete_when':[{'subject':'job','predicate':'status','value':'done'}]}],
        'actions':[{'id':'send','label':'Send parcel','goal':'deliver','priority':5,'cost':1,
                    'requires':[{'subject':'parcel','predicate':'destination','value':'north'}],
                    'effects':[{'subject':'job','predicate':'status','value':'done'},
                               {'subject':'parcel','predicate':'copies','value':'1','op':'increment'}]},
                   {'id':'inspect','label':'Inspect parcel instructions','cost':1,'priority':1,
                    'inspect':[{'subject':'parcel','predicate':'destination'}]}],
        'decisions':[{'at':at,'max_actions':2,'checkpoint':True} for at in [0,1440,2880,4320,5760,10080]],
        'assertions':[{'type':'fact','subject':'job','predicate':'status','value':'done'},
                      {'type':'receipt_count','action':'send','status':'succeeded','min':1,'max':1},
                      {'type':'credits_min','value':3}, {'type':'rejections_max','value':0}]
    }]}


@pytest.mark.parametrize('arm', ARMS)
def test_real_execution_checkpoint_and_matched_bounds(arm):
    spec = validate(fixture())['cases'][0]
    result = run_case(spec, 7, arm)
    uninterrupted = run_case(spec, 7, arm, checkpoint=False)
    assert result['passed']
    assert result['world']['ledger'] == uninterrupted['world']['ledger']
    assert result['world']['receipts'][0]['action'] == 'send'
    assert result['peak_bytes']['state'] <= 16384
    assert result['peak_bytes']['context'] <= 4096
    assert result['checkpoints'] >= 6
    assert result['accounting'] == uninterrupted['accounting']
    assert result['accounting']['retrieval_calls'] > 0


@pytest.mark.parametrize('arm', ARMS)
def test_unknown_write_inspection_before_retry_actual_cost(arm):
    spec = fixture()['cases'][0]
    spec['actions'][0]['outcomes'] = [{'attempt':1,'status':'unknown','effects':[]}]
    spec['assertions'] = [{'type':'receipt_count','action':'send','status':'unknown','min':1,'max':1},
                          {'type':'receipt_count','action':'send','status':'succeeded','min':1,'max':1}]
    result = run_case(spec, 3, arm)
    assert result['passed']
    assert [(r['action'],r['status']) for r in result['world']['receipts']][:3] == [('send','unknown'),('inspect','succeeded'),('send','succeeded')]
    assert result['spend'] == 3


def test_hidden_truth_never_filters_offered_actions_or_supplies_replacement():
    spec = fixture()['cases'][0]
    spec['timeline'].append({'at':10,'subject':'parcel','predicate':'destination','value':'south','visibility':'hidden'})
    spec['decisions'] = [{'at':at,'max_actions':1} for at in [20,1440,2880,4320,5760,10080]]
    result = run_case(spec, 1, 'dependency_retention')
    assert not result['passed']
    assert result['world']['receipts'][0]['status'] == 'rejected'
    assert 'south' not in canonical(result['trace'][0])
    assert result['world']['receipts'][0]['cost'] == 0


def test_unknown_private_effect_is_not_admitted_or_public():
    spec = fixture()['cases'][0]
    spec['actions'][0]['outcomes'] = [{'attempt':1,'status':'unknown','effects':[{'subject':'secret','predicate':'token','value':'new','public':False}]}]
    world = WorkflowWorld(spec, 4)
    world.advance(0)
    world.execute(spec['actions'][0])
    assert world.state.facts['secret.token'] == 'new'
    assert 'secret.token' not in world.register()
    assert not any(e.subject == 'secret' for e in world.stream)


def test_no_recovery_inspection_no_blind_retry():
    spec = fixture()['cases'][0]
    spec['actions'] = spec['actions'][:1]
    spec['actions'][0]['outcomes'] = [{'attempt':1,'status':'partial','effects':[]}]
    result = run_case(spec, 1, 'v3_hybrid')
    assert [(r['action'],r['status']) for r in result['world']['receipts']] == [('send','partial')]


@pytest.mark.parametrize('arm', ARMS)
def test_correction_and_rejected_claim(arm):
    mind = new_mind(arm)
    for eid, value, at, accepted in [(1,'north',0,True),(2,'south',50,True),(3,'north',60,False)]:
        mind.observe(Episode(eid,'Player',at,'observed',f'Destination {value}', 'parcel','destination',value,at,accepted=accepted))
    assert mind.believe('parcel','destination',now=100).value == 'south'
    restored = type(mind).from_dict(json.loads(canonical(mind.to_dict())))
    assert restored.believe('parcel','destination',now=100).value == 'south'


def test_frozen_candidate_dependencies():
    verify_candidate()


def test_scoring_counts_actual_attempts_order_and_never():
    spec = fixture()['cases'][0]
    world = WorkflowWorld(spec, 0)
    world.advance(0)
    world.execute(spec['actions'][0])
    spec['assertions'] = [{'type':'never','action':'send'}, {'type':'order','before':'inspect','after':'send'},
                          {'type':'receipt_count','action':'send','min':1,'max':1}]
    assert [r['passed'] for r in score(spec,world)] == [False,False,True]


def test_validation_and_bounds_fail_explicitly():
    bad = fixture(); bad['cases'][0]['decisions'][0]['max_actions'] = 5
    with pytest.raises(ValueError): validate(bad)
    bad = fixture(); bad['cases'][0]['actions'].append(copy.deepcopy(bad['cases'][0]['actions'][0]))
    with pytest.raises(ValueError): validate(bad)


def test_hidden_update_cannot_refresh_previously_public_register():
    spec = fixture()['cases'][0]
    spec['timeline'].append({'at':10,'subject':'job','predicate':'status','value':'secret_pause','visibility':'hidden'})
    world = WorkflowWorld(spec, 1); world.advance(20)
    assert world.state.facts['job.status'] == 'secret_pause'
    assert world.register()['job.status'] == 'open'
    restored = WorkflowWorld.restore(spec, json.loads(canonical(world.snapshot())))
    assert restored.register() == world.register()


def test_unrecoverable_mutation_does_not_deadlock_unrelated_obligation():
    spec = fixture()['cases'][0]
    spec['actions'] = spec['actions'][:1]
    spec['actions'][0]['outcomes'] = [{'attempt':1,'status':'unknown','effects':[]}]
    spec['goals'].append({'id':'archive','label':'Archive a separate receipt','priority':80,'deadline':10080,
                         'complete_when':[{'subject':'archive','predicate':'done','value':'yes'}]})
    spec['actions'].append({'id':'archive','goal':'archive','label':'Archive receipt','priority':1,'cost':0,
                           'effects':[{'subject':'archive','predicate':'done','value':'yes'}]})
    result = run_case(spec, 1, 'v3_hybrid')
    assert [(r['action'],r['status']) for r in result['world']['receipts']] == [('send','unknown'),('archive','succeeded')]
    assert result['goals']['archive']


def test_public_contract_strips_outcome_script_but_declares_possible_write_keys():
    from kalends.continuity_release.evaluation import public_actions
    spec = fixture()['cases'][0]
    spec['actions'][0]['outcomes'] = [{'attempt':1,'status':'unknown','effects':[{'subject':'secret','predicate':'token','value':'not_exposed','public':False}]}]
    contract = public_actions(spec['actions'])
    assert 'outcomes' not in contract[0]
    assert 'secret.token' in contract[0]['effect_keys']
    assert 'not_exposed' not in canonical(contract)


def test_full_bm25_index_payload_metadata_and_actual_query_are_charged():
    from dataclasses import asdict
    from kalends.memory.base import Experience
    from kalends.memory.retrieval import BM25Index, tokens
    from kalends_rebirth.minds import Goal
    controller = Controller('bm25_fifo')
    goals = [Goal('g', 'Deliver parcel', 90, 10080, relevant_keys=(('parcel', 'destination'),))]
    controller.admit([Episode(1, 'Player', 0, 'observed', 'Parcel destination north.',
        'parcel', 'destination', 'north', 0)], goals, 0)
    row = controller.mind.to_dict()['base']['episodes'][0]
    experience = Experience(0, 'observed', 'parcel', 'destination', 'north', None, 0, True, 1,
        controller.mind._text(row))
    actual = BM25Index(); actual.add(experience)
    query = 'parcel destination unavailable status'
    material = controller.index_material(query)
    assert material['documents'][0]['experience'] == asdict(actual._docs[0][2])
    assert material['documents'][0]['tokens'] == dict(actual._docs[0][0])
    assert material['documents'][0]['length'] == actual._docs[0][1]
    assert material['document_frequency'] == dict(actual._df)
    assert material['total_length'] == actual._total_len
    assert material['query'] == query and material['query_tokens'] == tokens(query)
    assert controller.charge(0, query=query) == len(canonical(controller.snapshot()).encode()) + len(canonical(material).encode())


def test_observe_believe_and_discarded_mutation_cycle_all_count_actual_retrieval():
    from kalends_rebirth.minds import Goal
    controller = Controller('bm25_fifo')
    goals = [Goal('g', 'Deliver parcel', 90, 10080, relevant_keys=(('parcel', 'destination'),))]
    controller.admit([Episode(1, 'Player', 0, 'observed', 'The parcel destination is south.',
        'parcel', 'destination', 'south', 0)], goals, 0)
    assert controller.retrieval_calls == 1  # observe asks for its prior belief
    controller.mind.believe('parcel', 'destination', now=0)
    assert controller.retrieval_calls == 2
    actions = [{'id': 'send', 'label': 'Send north', 'goal': 'g',
        'requires': [{'subject': 'parcel', 'predicate': 'destination', 'value': 'north'}]},
        {'id': 'inspect', 'label': 'Inspect destination', 'inspect': [{'subject': 'parcel', 'predicate': 'destination'}]}]
    decision, detail = controller.select(goals, actions, {}, 5, 0)
    assert decision['action_id'] == 'inspect' and detail['context'] == []
    assert controller.retrieval_calls == 4
    assert any(call['context_event_ids'] == [1] for call in detail['retrievals'])
    assert controller.max_context_bytes > 2  # final inspection's empty context
    assert all(call['state_bytes'] <= 16384 for call in detail['retrievals'])
    assert controller.max_query_bytes == len(canonical('parcel destination').encode())


def test_context_byte_budget_is_enforced_before_belief_or_planner_consumption():
    from kalends_rebirth.minds import Goal
    controller = Controller('bm25_fifo')
    keys = [('parcel' + suffix, 'destination') for suffix in 'abcd']
    goals = [Goal('g', 'Route four parcels', 90, 10080, relevant_keys=tuple(keys))]
    controller.admit([Episode(i, 'Player', i, 'observed', 'Parcel destination north. ' * 36,
        subject, predicate, 'north', i) for i, (subject, predicate) in enumerate(keys)], goals, 4)
    result = controller.mind._retrieve(4, keys=keys)
    assert 0 < len(result) < 4
    assert len(canonical(result).encode()) <= 4096
    assert controller.context_dropped_records > 0
    assert controller._retrieval_events[-1]['context_dropped_records'] > 0
    assert controller.max_context_bytes <= 4096


@pytest.mark.parametrize('arm', ARMS)
def test_actual_query_memory_is_reserved_before_native_retrieval(monkeypatch, arm):
    import kalends.continuity_release.evaluation as evaluation
    from kalends_rebirth.minds import Goal
    controller = Controller(arm)
    goals = [Goal('g', 'Route parcel', 90, 10080, relevant_keys=(('parcel', 'destination'),))]
    controller.admit([Episode(1, 'Player', 0, 'observed', 'The parcel goes north.',
        'parcel', 'destination', 'north', 0)], goals, 0)
    baseline = controller.charge(0)
    monkeypatch.setattr(evaluation, 'STATE_BYTES', baseline + 16)
    before = controller.byte_evictions
    controller.mind._retrieve(0, keys=[('parcel' + 'x' * 100, 'destination' + 'y' * 100)])
    assert controller.byte_evictions > before
    call = controller._retrieval_events[-1]
    assert call['query_bytes'] > 16 and call['state_bytes'] <= baseline + 16


def test_postselection_byte_eviction_cancels_instead_of_executing_missing_support():
    from kalends_rebirth.minds import Goal
    controller = Controller('v3_hybrid')
    keys = [('s' + str(i) + 'x' * 120, 'p' + str(i) + 'y' * 120) for i in range(14)]
    goals = [Goal('g' + str(i), 'Complete supported operation', 90, 10080,
        relevant_keys=tuple(keys[i * 8:(i + 1) * 8])) for i in range(2)]
    episodes = [Episode(i, 'Player', i, 'observed',
        ('s' + str(i) + ' p' + str(i) + ' parcel destination ' + 'word ' * 210)[:900],
        keys[i % 4][0], keys[i % 4][1], 'ok', i) for i in range(12)]
    actions = [{'id': 'a' + str(i), 'label': 'Operation ' + str(i), 'goal': 'g' + str(i // 8),
        'priority': 10 if i == 0 else 1,
        'requires': [{'subject': keys[j][0], 'predicate': keys[j][1], 'value': 'ok'}
                     for j in (range(4) if i == 0 else [i])]} for i in range(14)]
    controller.admit(episodes, goals, 12)
    decision, detail = controller.select(goals, actions, {}, 5, 12)
    assert decision['action_id'] == 'wait' and not decision['evidence_ids']
    assert controller.withheld_decisions == 1
    assert detail['budget_withheld'][0]['action_id'] == 'a0'
    assert detail['budget_withheld'][0]['missing_evidence_ids']
    assert any(plan.status == 'cancelled' and plan.action_id == 'a0' for plan in controller.mind.plans)
    assert detail['state_bytes'] <= 16384
    assert set(decision['context_event_ids']) <= set(controller.mind.retained_event_ids())
