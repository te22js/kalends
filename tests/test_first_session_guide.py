import copy
import json
import pytest
from kalends.experience_os.product import ProductService
from kalends.experience_os.guide import guide_view, known_target

@pytest.fixture
def service(tmp_path):
    return ProductService(tmp_path/'qa', include_examples=False)


def begin(service, template='pompeii_life', guided=True):
    data=service.start(template,guided=guided)
    return data['life']['id'],data


def ack(service,ident,name):
    return service.guide_update(ident,{'id':ident,'ack':name})


def act(service,ident,action):
    r=service.review(ident,action)
    return service.confirm_review(ident,r['proposal_id'])


def test_metadata_guide_never_changes_world_or_installs_history_in_memory(service):
    ident,data=begin(service)
    runtime=service.get(ident); before=runtime.state_hash(),copy.deepcopy(runtime.commands),runtime.journal_path.read_bytes()
    data=ack(service,ident,'role_arrival')
    service.guide_update(ident,{'id':ident,'card':'freedwoman'})
    service.guide_update(ident,{'id':ident,'enabled':False,'learn':False})
    assert before == (runtime.state_hash(),runtime.commands,runtime.journal_path.read_bytes())
    assert data['guide']['step']['id']=='p1'
    assert all('Naevoleia' not in json.dumps(m.to_dict()) for m in runtime.minds.values())


def test_existing_life_opt_in_off_resume_and_restart(service):
    ident,data=begin(service,guided=False)
    assert not data['guide']['enabled']
    service.guide_update(ident,{'id':ident,'enabled':True,'learn':True})
    ack(service,ident,'role_arrival')
    service.guide_update(ident,{'id':ident,'enabled':False})
    resumed=ProductService(service.directory,include_examples=False)
    assert not resumed.life(ident)['guide']['enabled']
    assert resumed.guide_update(ident,{'id':ident,'enabled':True})['guide']['step']['id']=='p1'
    assert resumed.life(ident)['guide']['excluded_from_unassisted_research']


def test_reading_ack_cannot_fabricate_action_or_unavailable_location(service):
    ident,data=begin(service)
    for bad in ['p7','support_market','allocate','reflection_done','dispute_explained']:
        with pytest.raises(ValueError): ack(service,ident,bad)
    with pytest.raises(ValueError): service.guide_update(ident,{'id':ident,'card':'food_counter'})
    assert len(service.get(ident).commands)==0


def test_real_move_early_document_and_alternative_route_update_tutorial(service):
    ident,data=begin(service)
    ack(service,ident,'role_arrival')
    act(service,ident,{'action':'move','x':750,'y':430,'location':'street'})
    assert service.life(ident)['guide']['step']['id']=='p2'
    act(service,ident,{'action':'examine_receipt','recipient':'Sabina'})
    guide=service.life(ident)['guide']
    assert 'p2' in guide['completed'] and 'p5' not in guide['completed']
    # Supported choice is allowed without the guide forcing a paid inspection.
    result=act(service,ident,{'action':'support_market','recipient':'Sabina'})
    guide=service.life(ident)['guide']
    assert guide['step']['id']=='p8'
    assert guide['result']['delivered']=={'Sabina':4,'Felix':2}
    assert 'paid 3 coins' in ' '.join(guide['result']['explanation'])
    assert len(service.get(ident).commands)==3


def test_cancelled_review_stale_offer_and_double_confirmation_no_tutorial_progress(service):
    ident,data=begin(service)
    ack(service,ident,'role_arrival')
    proposal=service.review(ident,{'action':'hear_dispute','recipient':'Sabina'})
    before=service.get(ident).state_hash()
    assert service.life(ident)['guide']['step']['id']=='p1'
    assert before==service.get(ident).state_hash()
    service.advance_product(ident,1)
    with pytest.raises(ValueError): service.confirm_review(ident,proposal['proposal_id'])
    result=act(service,ident,{'action':'hear_dispute','recipient':'Sabina'})
    assert service.life(ident)['guide']['step']['id']=='p3'
    with pytest.raises(ValueError): service.confirm_review(ident,proposal['proposal_id'])
    assert sum(c['data'].get('action')=='hear_dispute' for c in service.get(ident).commands)==1


def test_unaffordable_route_rejected_without_guide_charges(service):
    ident,data=begin(service)
    runtime=service.get(ident)
    # Execute existing resource spending, not an artificial account patch.
    for _ in range(4):
        try:
            act(service,ident,{'action':'inspect','recipient':'Sabina'})
        except ValueError:
            break
    before=runtime.state_hash(),len(runtime.commands)
    # Regardless of funds, guide metadata itself never buys an arrangement.
    service.guide_update(ident,{'id':ident,'ack':'controls_known'})
    assert before==(runtime.state_hash(),len(runtime.commands))


def test_known_waypoint_uses_admitted_last_seen_not_global_private_position():
    world={'agents':[{'id':'Dama','nearby':False,'location':'hidden_room','x':999,'y':888}]}
    events=[{'event_id':2,'tick':0,'etype':'move','actors':['Dama'],'payload':{'position':[850,430],'to':'street'}}]
    target,text=known_target(world,events,'Dama','household')
    assert (target['x'],target['y'])==(850,430)
    assert '999' not in json.dumps(target) and 'hidden_room' not in json.dumps(target)
    assert 'not live tracking' in text


def test_missed_dispute_has_supported_continuation_instead_of_impossible_objective(service):
    ident,data=begin(service)
    service.advance_product(ident,400,protect_known=False)
    guide=service.life(ident)['guide']
    assert guide['step']['id'] in ('p8','p9')
    assert guide['result'] is not None
    assert not any('paid 3 coins' in t for t in guide['result']['explanation'])


def test_practice_has_distinct_life_and_research_exclusion(service):
    ident,data=begin(service,'shared_observatory',False)
    act(service,ident,{'action':'inspect'})
    runtime=service.get(ident); before=runtime.state_hash(),runtime.journal_path.read_bytes()
    practice=service.practice(ident)
    assert practice['life']['id'] != ident
    assert practice['guide']['practice'] and practice['guide']['enabled']
    assert practice['snapshot']['command_count']==0
    assert practice['guide']['excluded_from_unassisted_research']
    assert before==(runtime.state_hash(),runtime.journal_path.read_bytes())


def test_observatory_does_not_leak_report_and_follows_actual_settlement(service):
    ident,data=begin(service,'shared_observatory')
    assert data['guide']['known']['report'] is None
    assert 'fragile' not in json.dumps(data['guide'])
    ack(service,ident,'role_arrival'); ack(service,ident,'request_read')
    assert service.life(ident)['guide']['step']['id']=='o2'
    act(service,ident,{'action':'share','recipient':'team_b'})
    guide=service.life(ident)['guide']
    assert guide['known']['report']['condition']=='fragile'
    assert guide['known']['report']['usable']==8
    act(service,ident,{'action':'commit','recipient':'team_c','quantity':4})
    act(service,ident,{'action':'allocate','allocation':{'team_a':4,'team_b':4,'team_c':4}})
    assert service.life(ident)['guide']['step']['id']=='o5'
    service.advance_product(ident,1439,protect_known=False)
    guide=service.life(ident)['guide']
    assert guide['step']['id']=='o6'
    assert guide['result']['executed']=={'team_a':4,'team_b':4,'team_c':0}
    assert guide['result']['promises']['team_c']==4
    assert guide['result']['missed_promises']==['team_c']
    assert 'promise was not met' in ' '.join(guide['result']['explanation'])
    assert len(guide['known']['project_requirements'])==3
    assert [p['status'] for p in guide['known']['project_requirements']].count('completed')==2
    ack(service,ident,'reflection_done')
    assert service.life(ident)['guide']['step']['id']=='o7'
    service.advance_product(ident,1,protect_known=False)
    assert [p['status'] for p in service.life(ident)['guide']['known']['project_requirements']].count('missed')==1


def test_history_cards_are_specific_and_have_no_unlicensed_image_or_fake_latin(service):
    ident,data=begin(service)
    cards=data['guide']['history_cards']
    assert len(cards)==5
    for c in cards:
        assert c['sources'] and c['claim'] and c['evidence'] and c['limits'] and c['game_changed']
        assert 'No external image' in c['rights']
        assert 'image_url' not in c
    act(service,ident,{'action':'move','location':'thermopolium'})
    card=next(c for c in service.life(ident)['guide']['history_cards'] if c['id']=='food_counter')
    assert card['available']
    service.guide_update(ident,{'id':ident,'card':'food_counter'})
    assert next(c for c in service.life(ident)['guide']['history_cards'] if c['id']=='food_counter')['read']


def test_context_never_previews_uncopied_document_or_private_report(service):
    from kalends.experience_os.runtime import ExperienceGameFacade
    ident,data=begin(service)
    runtime=service.get(ident); facade=ExperienceGameFacade(runtime,service.cognition)
    before=runtime.state_hash(),len(runtime.commands)
    context=facade.context('Sabina')
    topic=next(t for t in context['topics'] if t['id']=='market_receipt')
    assert topic['withheld'] and topic['evidence_ids']==[]
    assert '4 coins' not in topic['text'] and 'Two flour' not in topic['text']
    assert all(set(t.get('evidence_ids',[]))<=runtime.visible_ids() for t in context['topics'])
    assert before==(runtime.state_hash(),len(runtime.commands))
    act(service,ident,{'action':'examine_receipt','recipient':'Sabina'})
    topic=next(t for t in facade.context('Sabina')['topics'] if t['id']=='market_receipt')
    assert not topic['withheld'] and '4 coins' in topic['text']
    assert set(topic['evidence_ids'])<=runtime.visible_ids()


def test_confirmed_second_account_is_a_valid_alternative_to_the_messenger(service):
    ident,data=begin(service)
    ack(service,ident,'role_arrival'); ack(service,ident,'controls_known'); ack(service,ident,'skip_history')
    act(service,ident,{'action':'hear_dispute','recipient':'Sabina'})
    ack(service,ident,'dispute_explained')
    act(service,ident,{'action':'move','location':'household'})
    act(service,ident,{'action':'talk','recipient':'Lucius','topic':'dispute'})
    guide=service.life(ident)['guide']
    assert 'p5' in guide['completed']
    assert any(e['source']=='Lucius' and 'Four sacks' in e['text'] for e in guide['known']['evidence'])


@pytest.mark.parametrize('malformed', [
    True,
    {'version': 1},
    {'enabled': 1},
    {'learn': 'yes'},
    {'practice': 1},
    {'guided_origin': 'yes'},
    {'ack': None},
    {'ack': [{}]},
    {'read_cards': None},
    {'read_cards': [False]},
])
def test_malformed_guide_on_restart_preserves_metadata_and_valid_journal(service, malformed):
    ident, _ = begin(service)
    act(service, ident, {'action': 'hear_dispute', 'recipient': 'Sabina'})
    runtime = service.get(ident)
    original_hash, journal = runtime.state_hash(), runtime.journal_path.read_bytes()
    document = json.loads(service.meta_path.read_text())
    document['lives'][ident]['guide'] = malformed
    service.meta_path.write_text(json.dumps(document))
    metadata = service.meta_path.read_bytes()

    restored = ProductService(service.directory, include_examples=False)
    assert 'product_metadata' in restored.failures
    assert restored.catalog()['failures']
    assert restored.life(ident)['snapshot']['state_hash'] == original_hash
    assert not restored.life(ident)['guide']['enabled']
    with pytest.raises(ValueError, match='incompatible'):
        restored.guide_update(ident, {'enabled': True})
    assert restored.meta_path.read_bytes() == metadata
    assert restored.get(ident).journal_path.read_bytes() == journal


def test_pure_guide_projection_update_and_usage_defend_against_bad_optional_metadata(service):
    from kalends.experience_os.guide import preferences
    ident, _ = begin(service)
    runtime = service.get(ident)
    before = runtime.state_hash(), runtime.journal_path.read_bytes()
    for malformed in (True, {'ack': None}, {'ack': [{}]}, {'read_cards': None}):
        prefs = preferences(malformed)
        assert prefs['ack'] == [] and prefs['read_cards'] == []
    service.metadata[ident]['guide'] = True
    assert not service.life(ident)['guide']['enabled']
    service.metadata[ident]['telemetry_opt_in'] = True
    assert service.telemetry(ident, {'event': 'guide_help'})['recorded']
    assert service.guide_update(ident, {'enabled': True})['guide']['enabled']
    assert before == (runtime.state_hash(), runtime.journal_path.read_bytes())


def test_unknown_guide_version_resets_steps_but_preserves_assistance_exclusion(service):
    ident, _ = begin(service)
    service.metadata[ident]['guide'] = {'version': 'earlier-guide', 'enabled': True,
                                      'practice': True, 'ack': ['role_arrival']}
    guide = service.life(ident)['guide']
    assert not guide['enabled'] and guide['ack'] == [] and 'p0' not in guide['completed']
    assert guide['practice'] and guide['guided_origin']
    assert guide['excluded_from_unassisted_research']


@pytest.mark.parametrize('practice', [False, True])
def test_recovered_newborn_metadata_failure_never_classifies_assistance_as_unassisted(service, monkeypatch, practice):
    import kalends.experience_os.product as module
    with monkeypatch.context() as patch:
        patch.setattr(module, 'atomic_json', lambda *args: (_ for _ in ()).throw(OSError('injected display metadata failure')))
        created = service.start('pompeii_life', guided=True, practice=practice)
    ident = created['life']['id']
    runtime = service.get(ident)
    before = runtime.state_hash(), runtime.journal_path.read_bytes()
    assert created['metadata_warning']

    restored = ProductService(service.directory, include_examples=False)
    recovered = restored.life(ident)
    assert recovered['life']['provenance_unknown']
    assert recovered['guide']['provenance_unknown']
    assert recovered['guide']['excluded_from_unassisted_research']
    assert 'provenance could not be verified' in recovered['life']['metadata_warning']
    restored.telemetry(ident, {'opt_in': True})
    assert restored.telemetry(ident, {'event': 'guide_help'})['recorded']
    row = json.loads((restored.directory / '.product/events.jsonl').read_text())
    assert row['provenance_unknown'] and row['excluded_from_unassisted_research']
    again = ProductService(service.directory, include_examples=False)
    assert again.life(ident)['guide']['provenance_unknown']
    assert before == (again.get(ident).state_hash(), again.get(ident).journal_path.read_bytes())


def test_new_life_persists_known_guidance_provenance_and_legacy_missing_guide_is_unknown(service):
    ident, created = begin(service, guided=False)
    assert not created['life']['provenance_unknown']
    restored = ProductService(service.directory, include_examples=False)
    assert not restored.life(ident)['guide']['provenance_unknown']
    assert not restored.life(ident)['guide']['excluded_from_unassisted_research']
    document = json.loads(restored.meta_path.read_text())
    del document['lives'][ident]['guide']
    restored.meta_path.write_text(json.dumps(document))
    metadata = restored.meta_path.read_bytes()
    journal = restored.get(ident).journal_path.read_bytes()
    recovered = ProductService(restored.directory, include_examples=False)
    assert recovered.life(ident)['guide']['provenance_unknown']
    assert recovered.life(ident)['guide']['excluded_from_unassisted_research']
    assert recovered.meta_path.read_bytes() == metadata
    assert recovered.get(ident).journal_path.read_bytes() == journal


def test_market_copy_explains_immediate_time_cost_without_changing_exact_action(service):
    ident,_=begin(service)
    facade=service.game(ident); runtime=service.get(ident)
    choice=next(c for c in facade.context('Sabina')['choices'] if c['id']=='support_market')
    assert choice['label']=='Pay for the market delivery'
    assert choice['cost']=='3 coins · 20 world minutes'
    assert 'four sacks of flour to Sabina and two to Felix' in choice['description']
    before=runtime.state_hash(),len(runtime.commands)
    proposal=facade.propose({'recipient':'Sabina','choice_id':'support_market'})
    offered=proposal['interpretations'][0]
    assert offered['label']==choice['label'] and offered['cost']==choice['cost']
    stored=facade.legacy.proposals[proposal['proposal_id']]['interpretations'][0]
    assert offered['action']==stored['action']
    assert offered['action']['action']=='support_market' and offered['action']['recipient']=='Sabina'
    assert before==(runtime.state_hash(),len(runtime.commands))
    facade.act({'proposal_id':proposal['proposal_id'],'interpretation_id':offered['id']})
    result=service.life(ident)['guide']['result']
    assert runtime.minute==20 and result['delivered']=={'Sabina':4,'Felix':2}
