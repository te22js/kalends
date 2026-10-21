"""Pure navigation over the district's explicit floor geometry.

This does not mutate a world, advance time, infer furniture from illustrations,
or authorize an action. Public paths use the union of the authored street
rectangles. Interior transitions must use the room's designated door and a
straight doorway connector to its existing 15-unit inset floor.
"""
from __future__ import annotations

from dataclasses import dataclass
import heapq
import math
from typing import Iterable

from kalends.pompeii.district import LOCATIONS, MAP

Point = tuple[float, float]
EPSILON = 1e-8
PUBLIC_LOCATIONS = frozenset(("street", "water", "forum_access"))


@dataclass(frozen=True)
class Rect:
    left: float
    top: float
    right: float
    bottom: float

    def contains(self, point: Point) -> bool:
        x, y = point
        return self.left-EPSILON <= x <= self.right+EPSILON and self.top-EPSILON <= y <= self.bottom+EPSILON

    def nearest(self, point: Point) -> Point:
        x, y = point
        return max(self.left, min(self.right, x)), max(self.top, min(self.bottom, y))

    def corners(self) -> tuple[Point, ...]:
        return ((self.left, self.top), (self.right, self.top),
                (self.left, self.bottom), (self.right, self.bottom))


STREETS = tuple(Rect(float(r["x"]), float(r["y"]), float(r["x"]+r["w"]), float(r["y"]+r["h"])) for r in MAP["streets"])
ROOMS = {r["id"]: r for r in LOCATIONS if r["interior"]}


def _point(value) -> Point:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError("A position must contain two finite coordinates.")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
        raise ValueError("A position must contain two finite coordinates.")
    return float(value[0]), float(value[1])


def _room(location: str):
    try:
        return ROOMS[location]
    except (KeyError, TypeError):
        raise ValueError("Unknown navigation location.") from None


def floor_rect(location: str) -> Rect:
    room = _room(location)
    return Rect(room["x"]+15., room["y"]+15., room["x"]+room["w"]-15., room["y"]+room["h"]-15.)


def door_points(location: str) -> tuple[Point, Point]:
    """Return (public door, interior threshold), preserving the explicit portal."""
    room = _room(location)
    door = _point((room["door"]["x"], room["door"]["y"]))
    return door, floor_rect(location).nearest(door)


def _regions(location: str) -> tuple[Rect, ...]:
    if not isinstance(location, str):
        raise ValueError("Unknown navigation location.")
    if location in PUBLIC_LOCATIONS:
        return STREETS
    return (floor_rect(location),)


def point_walkable(point, location: str = "street") -> bool:
    value = _point(point)
    return any(r.contains(value) for r in _regions(location))


def project_point(point, location: str = "street", *, max_distance: float = 48.) -> Point:
    """Project a nearby click onto its current scene floor; reject far targets.

    Projection never chooses another room or crosses a doorway. A caller must
    still route the accepted position and commit it through the world validator.
    """
    value = _point(point)
    if type(max_distance) not in (int, float) or not math.isfinite(max_distance) or max_distance < 0:
        raise ValueError("Projection distance must be finite and nonnegative.")
    candidates = [r.nearest(value) for r in _regions(location)]
    projected = min(candidates, key=lambda q: (math.dist(value, q), q))
    if math.dist(value, projected) > max_distance+EPSILON:
        raise ValueError("Choose a nearby point on the street or use a marked doorway.")
    return projected


def _clip_interval(start: Point, end: Point, rect: Rect):
    low, high = 0., 1.
    for a, b, minimum, maximum in ((start[0], end[0], rect.left, rect.right),
                                    (start[1], end[1], rect.top, rect.bottom)):
        delta = b-a
        if abs(delta) < EPSILON:
            if a < minimum-EPSILON or a > maximum+EPSILON:
                return None
            continue
        first, last = sorted(((minimum-a)/delta, (maximum-a)/delta))
        low, high = max(low, first), min(high, last)
        if low > high+EPSILON:
            return None
    return max(0., low), min(1., high)


def _covered(start: Point, end: Point, regions: Iterable[Rect]) -> bool:
    intervals = sorted(interval for rect in regions if (interval := _clip_interval(start, end, rect)) is not None)
    covered = 0.
    for low, high in intervals:
        if low > covered+EPSILON:
            return False
        covered = max(covered, high)
        if covered >= 1.-EPSILON:
            return True
    return False


def segment_walkable(start, end, *, rooms: Iterable[str] = ()) -> bool:
    """Check the complete segment against public floor plus named portal rooms.

    A doorway connector is a zero-width navigation centerline, not an invented
    collision mesh. It cannot be used to enter an unnamed room through a wall.
    """
    regions = list(STREETS)
    for location in rooms:
        door, threshold = door_points(location)
        regions.extend((floor_rect(location), Rect(min(door[0], threshold[0]), min(door[1], threshold[1]),
                                                   max(door[0], threshold[0]), max(door[1], threshold[1]))))
    return _covered(_point(start), _point(end), regions)


def _public_path(start: Point, end: Point) -> list[Point]:
    if not point_walkable(start) or not point_walkable(end):
        raise ValueError("A public route must start and end on the street floor.")
    if _covered(start, end, STREETS):
        return [start] if start == end else [start, end]
    vertices = [start, end, *sorted({p for r in STREETS for p in r.corners()}-{start, end})]
    distances, previous = {0: 0.}, {}
    pending = [(0., 0)]
    while pending:
        distance, index = heapq.heappop(pending)
        if distance > distances[index]+EPSILON:
            continue
        if index == 1:
            route = [vertices[index]]
            while index:
                index = previous[index]
                route.append(vertices[index])
            return route[::-1]
        for other, point in enumerate(vertices):
            if other == index or not _covered(vertices[index], point, STREETS):
                continue
            candidate = distance+math.dist(vertices[index], point)
            if candidate < distances.get(other, math.inf)-EPSILON:
                distances[other] = candidate
                previous[other] = index
                heapq.heappush(pending, (candidate, other))
    raise ValueError("No connected street route exists between these positions.")


def path_between(start, end, current_location: str = "street", target_location: str = "street") -> list[Point]:
    """Shortest street route with mandatory room portals and valid floor ends.

    Room-internal portions are straight over their declared convex floors.
    Public portions are Euclidean shortest paths over the authored rectangle
    union. No endpoint projection is implicit; callers can explicitly request
    a bounded projection before authoritative validation.
    """
    start, end = _point(start), _point(end)
    if not point_walkable(start, current_location):
        raise ValueError("The starting position is outside its current floor.")
    if not point_walkable(end, target_location):
        raise ValueError("The destination is outside its selected floor.")
    if current_location == target_location and current_location not in PUBLIC_LOCATIONS:
        return [start] if start == end else [start, end]
    before, after = [start], [end]
    public_start, public_end = start, end
    if current_location not in PUBLIC_LOCATIONS:
        public_start, threshold = door_points(current_location)
        before.extend((threshold, public_start))
    if target_location not in PUBLIC_LOCATIONS:
        public_end, threshold = door_points(target_location)
        after = [public_end, threshold, end]
    result = []
    for point in (*before, *_public_path(public_start, public_end), *after):
        if not result or math.dist(result[-1], point) > EPSILON:
            result.append(point)
    return result


def path_distance(path: Iterable[Point]) -> float:
    points = [_point(p) for p in path]
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))
