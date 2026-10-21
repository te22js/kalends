"""New movement is distance-based while every old accepted command stays exact."""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from kalends_rebirth.ai import Cognition
from kalends_rebirth.language import Language
from kalends_rebirth.navigation_v2 import door_points, path_distance, segment_walkable
from kalends_rebirth.server import RebirthSession
from kalends_rebirth.world import RebirthWorld


def session(path=None):
    return RebirthSession(path,language=Language(Cognition()))


def choose(s,choice,recipient='Sabina'):
    p=s.apply('propose',{'recipient':recipient,'choice_id':choice})
    return s.apply('act',{'proposal_id':p['proposal_id'],'interpretation_id':'0'})


def physical(s):
    return copy.deepcopy((s.original.fidelity_state(),s.commands,s.original.ledger.content_hash(),s.intervention,
                          s.branch.fidelity_state() if s.branch else None))


def test_direct_world_stays_legacy_but_new_session_steps_do_not_backtrack():
    old=RebirthWorld();old.move(770,650);before=old.minute
    legacy=old.move(770,676)['payload']
    assert path_distance(legacy['path'])==496 and old.minute-before==6
    assert old._movement_state=={'distance':0.,'charged_minutes':0}
    s=session();s.apply('move',{'x':770,'y':650});before=s.original.minute
    result=s.apply('move',{'x':770,'y':676})['receipt']['payload']
    assert list(map(tuple,result['path']))==[(770.,650.),(770.,676.)]
    assert result['travel_distance']==26
    assert s.original.minute-before in (0,1)
    assert result['world_minutes']==s.original.minute-before
    assert result['movement_revision']==s.commands[-1]['movement_revision']==2
    assert not hasattr(s.original,'_movement_revision')


def test_small_steps_and_single_walk_charge_same_total_time_and_preserve_accounts():
    split,once=session(),session()
    for n in range(10):split.apply('move',{'x':650+(n+1)*26,'y':415})
    once.apply('move',{'x':910,'y':415})
    assert split.original.minute==once.original.minute==3
    assert split.original.positions['Player']==once.original.positions['Player']==(910.,415.)
    assert split.original._movement_state==once.original._movement_state=={'distance':260.,'charged_minutes':3}
    assert [c['after']-c['at'] for c in split.commands]==[1,0,0,1,0,0,1,0,0,0]
    assert split.original.economy.cash==once.original.economy.cash
    assert split.original.economy.inventory==once.original.economy.inventory


def test_zero_distance_move_does_not_advance_world_or_pretend_to_consume_time():
    s=session();before=s.original.minute
    result=s.apply('move',{'location':'street'})
    assert s.original.minute==before
    assert list(map(tuple,result['receipt']['payload']['path']))==[(650.,415.)]
    assert result['receipt']['payload']['travel_distance']==result['receipt']['payload']['world_minutes']==0


@pytest.mark.parametrize('room',['bakery','fullery','thermopolium','household'])
def test_room_exit_ends_at_reachable_public_door_instead_of_teleporting_to_backbone(room):
    s=session();s.apply('move',{'location':room})
    result=s.apply('move',{'location':'street'})['receipt']['payload']
    assert s.original.positions['Player']==door_points(room)[0]
    assert s.original.state.agent_locations['Player']=='street'
    assert all(segment_walkable(a,b,rooms=(room,)) for a,b in zip(result['path'],result['path'][1:]))
    assert result['path'][-1][1] != 415


def test_carry_state_is_event_projected_inspectable_detached_and_durable(tmp_path):
    path=tmp_path/'life.json';s=session(path)
    receipt=s.apply('move',{'x':676,'y':415})['receipt']
    assert receipt['payload']['movement_state']=={'distance':26.,'charged_minutes':1}
    receipt['payload']['movement_state']['distance']=9999
    assert s.original._movement_state['distance']==26
    saved=path.read_bytes();restored=session(path)
    assert path.read_bytes()==saved and physical(restored)==physical(s)
    before=restored.original.minute
    restored.apply('move',{'x':702,'y':415})
    assert restored.original.minute==before
    assert restored.original.fidelity_state()['movement_v2']=={'distance':52.,'charged_minutes':1}
    lab=restored.original.snapshot(operator=True)['operator']['movement']
    assert lab==restored.original._movement_state
    assert physical(session(path))==physical(restored)


def test_old_actual_browser_journal_reads_unchanged_then_mixed_moves_and_fork_restore(tmp_path):
    source=Path(__file__).resolve().parents[1]/'results/rebirth/browser_walkthrough/before_week.json'
    raw=source.read_bytes();source_hash=hashlib.sha256(raw).hexdigest()
    assert source_hash=='100a104c7dd2af00c7c5025903f217d33cac74824a3b14d2945ca02df1d7c996'
    path=tmp_path/'mixed.json';path.write_bytes(raw);s=session(path)
    assert s.original.ledger.content_hash()=='75ebb2dc2da2d9f156cad219ec87717a3d3cdf0a91b9274fee50218e649c1cde'
    assert s.original.minute==172 and path.read_bytes()==raw
    assert s.original._movement_state=={'distance':0.,'charged_minutes':0}
    s.apply('move',{'location':'street'})
    assert s.commands[-1]['movement_revision']==2
    assert all('movement_revision' not in c for c in s.commands[:-1])
    assert physical(session(path))==physical(s)
    s.apply('fork',{'kind':'remove_action','event_id':24})
    restarted=session(path)
    assert physical(restarted)==physical(s)
    assert restarted.branch._movement_state==s.branch._movement_state
    assert source.read_bytes()==raw


@pytest.mark.parametrize('revision',[0,3,True,'2',None])
def test_unsupported_movement_revision_rejects_save_without_overwriting_it(tmp_path,revision):
    path=tmp_path/'bad.json';s=session(path);s.apply('move',{'x':676,'y':415})
    payload=json.loads(path.read_text());payload['commands'][0]['movement_revision']=revision
    path.write_text(json.dumps(payload));before=path.read_bytes()
    with pytest.raises(ValueError,match='Unsupported movement revision'):session(path)
    assert path.read_bytes()==before


def test_invalid_destination_and_save_failure_roll_back_travel_carry_and_every_world_effect(tmp_path,monkeypatch):
    path=tmp_path/'life.json';s=session(path);s.apply('move',{'x':676,'y':415})
    before=physical(s);saved=path.read_bytes()
    for data in ({'x':100,'y':100},{'x':float('nan'),'y':415},{'location':'roof'},
                 {'location':'bakery','x':810},{'location':'bakery','x':100,'y':100}):
        with pytest.raises(ValueError):s.apply('move',data)
        assert physical(s)==before and path.read_bytes()==saved
    def no_save():raise OSError('injected storage failure')
    monkeypatch.setattr(s,'save',no_save)
    with pytest.raises(OSError):s.apply('move',{'x':702,'y':415})
    assert physical(s)==before and path.read_bytes()==saved


def test_fork_rejects_invalid_revision_even_on_the_action_selected_for_omission(tmp_path):
    path=tmp_path/'life.json';s=session(path)
    result=choose(s,'examine_receipt');event_id=result['receipt']['event_id']
    s.apply('mode',{'mode':'lab'});saved=path.read_bytes()
    s.commands[0]['movement_revision']=3
    before=physical(s)
    with pytest.raises(ValueError,match='Unsupported movement revision'):
        s.apply('fork',{'kind':'remove_action','event_id':event_id})
    assert physical(s)==before and path.read_bytes()==saved


def test_movement_rejects_insufficient_horizon_before_any_world_mutation():
    world=RebirthWorld();world.advance(world.config.horizon_days*1440,'skip')
    before=world.fidelity_state();digest=world.ledger.content_hash()
    with pytest.raises(ValueError,match='configured world time'):
        RebirthSession._perform(world,'move',{'x':676,'y':415})
    assert world.fidelity_state()==before and world.ledger.content_hash()==digest
    assert not hasattr(world,'_movement_revision')


@pytest.mark.parametrize('room',['bakery','fullery','thermopolium','household'])
def test_explicit_scene_coordinates_allow_short_portal_entry_and_exit(room):
    s=session();door,threshold=door_points(room)
    s.apply('move',{'x':door[0],'y':door[1]})
    entered=s.apply('move',{'location':room,'x':threshold[0],'y':threshold[1]})['receipt']['payload']
    assert s.original.state.agent_locations['Player']==room
    assert s.original.positions['Player']==threshold
    assert list(map(tuple,entered['path']))==[door,threshold]
    assert entered['travel_distance']==path_distance([door,threshold])
    assert entered['travel_distance']<=55
    exited=s.apply('move',{'location':'street','x':door[0],'y':door[1]})['receipt']['payload']
    assert s.original.state.agent_locations['Player']=='street'
    assert s.original.positions['Player']==door
    assert list(map(tuple,exited['path']))==[threshold,door]
    assert exited['travel_distance']==entered['travel_distance']


def test_explicit_scene_coordinate_override_is_v2_only_and_legacy_hash_is_exact():
    original,with_fields=RebirthWorld(),RebirthWorld()
    original.move(location='bakery')
    RebirthSession._perform(with_fields,'move',{'location':'bakery','x':25,'y':25},movement_revision=1)
    assert original.positions['Player']==with_fields.positions['Player']==(810.,275.5)
    assert original.ledger.content_hash()==with_fields.ledger.content_hash()
    assert original.fidelity_state()==with_fields.fidelity_state()
    s=session()
    s.apply('move',{'location':'bakery','x':810,'y':200})
    assert s.original.positions['Player']==(810.,200.)
    assert s.original.state.agent_locations['Player']=='bakery'
