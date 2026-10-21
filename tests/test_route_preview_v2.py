"""The controller plans without committing and crosses rooms in short steps."""
import copy
import math

import pytest

from kalends_rebirth.navigation_v2 import path_distance
from kalends_rebirth.server import RebirthSession


def test_route_preview_is_read_only_and_exposes_only_public_geometry():
    session=RebirthSession();before=(session.original.ledger.content_hash(),copy.deepcopy(session.original.fidelity_state()),copy.deepcopy(session.commands))
    route=session.apply('route',{'location':'household'})
    assert route['navigation_revision']==2 and route['distance']>0
    assert set(route)=={'revision','navigation_revision','points','distance','destination'}
    assert all(set(node)=={'x','y','location'} for node in route['points'])
    assert before==(session.original.ledger.content_hash(),session.original.fidelity_state(),session.commands)


@pytest.mark.parametrize('body',[{}, {'x':1}, {'x':float('nan'),'y':415}, {'location':'private_vault'}, {'x':100,'y':100}, {'location':'bakery','cash':0}])
def test_route_rejection_does_not_modify_a_world(body):
    session=RebirthSession();before=session.original.ledger.content_hash()
    with pytest.raises((ValueError,TypeError)):session.apply('route',body)
    assert session.original.ledger.content_hash()==before and not session.commands


@pytest.mark.parametrize('destination',['bakery','fullery','thermopolium','household','water','forum_access'])
def test_preview_can_be_executed_as_short_authoritative_steps(destination):
    session=RebirthSession();route=session.apply('route',{'location':destination});distance=0
    for target in route['points'][1:]:
        for _ in range(100):
            x,y=session.original.positions['Player'];location=session.original.state.agent_locations['Player']
            delta=math.dist((x,y),(target['x'],target['y']))
            if delta<1e-7 and location==target['location']:break
            if location!=target['location']:
                body=dict(target)
            else:
                ratio=min(1,48/delta);body={'x':x+(target['x']-x)*ratio,'y':y+(target['y']-y)*ratio}
            result=session.apply('move',body);payload=result['receipt']['payload']
            assert payload['travel_distance']<=max(48,delta if 'location' in body else 0)+1e-7
            distance+=payload['travel_distance']
        else:raise AssertionError('Controller path failed to make progress')
    assert session.original.positions['Player']==pytest.approx((route['destination']['x'],route['destination']['y']))
    assert session.original.state.agent_locations['Player']==route['destination']['location']
    assert distance==pytest.approx(route['distance'])
    assert session.original.minute==math.ceil(distance/90-1e-10)
