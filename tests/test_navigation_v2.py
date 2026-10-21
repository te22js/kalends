"""Navigation must follow declared floors, rather than merely valid endpoints."""
import itertools
import math

import pytest

from kalends.pompeii.district import LOCATIONS
from kalends_rebirth.navigation_v2 import (PUBLIC_LOCATIONS, door_points, floor_rect,
    path_between, path_distance, point_walkable, project_point, segment_walkable)
from kalends_rebirth.world import RebirthWorld


ROOMS = [r for r in LOCATIONS if r['interior']]


def center(room):
    return room['x']+room['w']*.5, room['y']+room['h']*.85


def assert_route_valid(path, current='street', target='street'):
    rooms = tuple(location for location in (current, target) if location not in PUBLIC_LOCATIONS)
    assert path
    assert all(a != b for a, b in zip(path, path[1:]))
    assert all(segment_walkable(a, b, rooms=rooms) for a, b in zip(path, path[1:]))
    assert path_distance(path) == pytest.approx(sum(math.dist(a, b) for a, b in zip(path, path[1:])))


def test_same_corridor_steps_are_direct_instead_of_backtracking_to_backbone():
    vertical=path_between((770,650),(770,676))
    horizontal=path_between((650,400),(910,400))
    assert vertical == [(770.,650.),(770.,676.)]
    assert path_distance(vertical) == 26
    assert path_distance(horizontal) == 260
    assert_route_valid(vertical);assert_route_valid(horizontal)


def test_street_corner_route_is_shortest_without_crossing_a_building():
    start,end=(385,480),(770,790)
    assert not segment_walkable(start,end)
    path=path_between(start,end)
    assert path==[(385.,480.),(700.,480.),(770.,790.)]
    assert path_distance(path)==pytest.approx(315+math.hypot(70,310))
    assert_route_valid(path)


@pytest.mark.parametrize('first,second',itertools.permutations(ROOMS,2))
def test_all_room_orders_use_both_portals_and_collision_valid_segments(first,second):
    path=path_between(center(first),center(second),first['id'],second['id'])
    assert path[0]==center(first) and path[-1]==center(second)
    assert door_points(first['id'])[0] in path and door_points(second['id'])[0] in path
    assert_route_valid(path,first['id'],second['id'])
    backward=path_between(center(second),center(first),second['id'],first['id'])
    assert path_distance(path)==pytest.approx(path_distance(backward))


@pytest.mark.parametrize('room',ROOMS)
def test_interior_movement_stays_inside_its_convex_floor(room):
    floor=floor_rect(room['id']);start=(floor.left+5,floor.top+5);end=(floor.right-5,floor.bottom-5)
    path=path_between(start,end,room['id'],room['id'])
    assert path==[start,end]
    assert_route_valid(path,room['id'],room['id'])


def test_every_initial_npc_position_is_reachable_from_player_without_wall_shortcuts():
    world=RebirthWorld()
    for agent in world.agent_ids:
        location=world.state.agent_locations[agent]
        path=path_between(world.positions['Player'],world.positions[agent],'street',location)
        assert path[-1]==world.positions[agent]
        assert_route_valid(path,'street',location)


def test_endpoint_validity_does_not_authorize_crossing_room_walls():
    # A straight bakery-to-street diagonal intersects the room wall away from its door.
    assert not segment_walkable((700,200),(650,415),rooms=('bakery',))
    path=path_between((700,200),(650,415),'bakery','street')
    assert (810.,350.) in path
    assert_route_valid(path,'bakery','street')
    with pytest.raises(ValueError,match='destination'):path_between((650,415),(700,200))
    with pytest.raises(ValueError,match='starting'):path_between((100,100),(650,415))


def test_nearby_projection_is_explicit_scene_scoped_and_distance_bounded():
    assert project_point((800,500))==(800.,500.)
    assert project_point((690,650),max_distance=12)==(700.,650.)
    assert project_point((650,330),max_distance=25)==(650.,350.)
    assert project_point((660,200),'bakery',max_distance=10)==(665.,200.)
    with pytest.raises(ValueError):project_point((100,100))
    with pytest.raises(ValueError):project_point((690,650),max_distance=5)
    with pytest.raises(ValueError):project_point((810,350),'bakery',max_distance=20)
    assert not point_walkable((810,350),'bakery')
    assert point_walkable((810,350),'street')


def test_distance_is_invariant_to_splitting_a_straight_walk():
    once=path_distance(path_between((650,415),(910,415)))
    split=sum(path_distance(path_between((650+n*26,415),(650+(n+1)*26,415))) for n in range(10))
    assert once==split==260
    # Root's clock adapter can accumulate this quantity before rounding once.
    assert once/90==split/90


@pytest.mark.parametrize('point',[None,(1,),(1,2,3),(True,415),('650',415),(float('nan'),415),(650,float('inf'))])
def test_nonfinite_or_noncoordinate_points_are_rejected(point):
    with pytest.raises(ValueError):path_between((650,415),point)


def test_unknown_locations_and_invalid_projection_limits_are_rejected():
    with pytest.raises(ValueError,match='Unknown'):path_between((650,415),(650,415),target_location='roof')
    with pytest.raises(ValueError,match='Unknown'):point_walkable((650,415),[])
    for limit in (-1,True,float('nan'),float('inf')):
        with pytest.raises(ValueError):project_point((650,415),max_distance=limit)
    assert path_between((650,415),(650,415))==[(650.,415.)]
    assert path_distance([])==0
