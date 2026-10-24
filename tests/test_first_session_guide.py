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
    ack(service,ident,'reflection_done')
    assert service.life(ident)['guide']['step']['id']=='o7'


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
