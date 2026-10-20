"""Deterministic event scheduling with an explicit minute-scanning reference.

This is ordinary discrete-event simulation, not a new compression algorithm.
Only scheduled tasks can change the supported world between player commands.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import heapq
import json
import time
from typing import Any, Callable


def _integer(value: Any, name: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _payload(data: Any) -> str:
    if not isinstance(data, dict):
        raise ValueError("task data must be a JSON object")
    try:
        return json.dumps(data, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("task data must contain finite JSON values") from exc


@dataclass(frozen=True, order=True)
class ScheduledTask:
    """Internally immutable: serialized payloads cannot alias caller dictionaries."""

    due: int
    sequence: int
    key: str
    kind: str = field(compare=False)
    payload: str = field(compare=False, repr=False)

    def to_dict(self) -> dict:
        return {"due": self.due, "sequence": self.sequence, "key": self.key,
                "kind": self.kind, "data": json.loads(self.payload)}


class EventClock:
    """Stable heap clock. ``advance`` includes tasks due at its target minute.

    ``live`` really checks every integer minute, without calling the handler for
    empty minutes. ``compress`` visits task minutes and the final target only.
    ``naive`` rounds execution up to a global coarse grid; it retains every task
    and stable order, but intentionally loses within-bin timing and reactions.
    Handlers read ``clock.now`` for execution time. Their task dictionaries also
    retain original ``due``, plus ``executed_at`` and ``lateness``.
    """

    def __init__(self, now: int = 0):
        self.now = _integer(now, "now")
        self._queue: list[ScheduledTask] = []
        self._sequence = 0
        self._advancing = False

    @property
    def queue(self) -> tuple[dict, ...]:
        """A detached, sorted inspection view; mutations cannot change the clock."""
        return tuple(task.to_dict() for task in sorted(self._queue))

    def __len__(self) -> int:
        return len(self._queue)

    def peek(self) -> int | None:
        return self._queue[0].due if self._queue else None

    def schedule(self, due: int, kind: str, data: dict | None = None) -> dict:
        due = _integer(due, "due")
        if due < self.now:
            raise ValueError("cannot schedule a task before the current clock minute")
        if not isinstance(kind, str) or not kind.strip():
            raise ValueError("task kind must be a nonempty string")
        payload = _payload({} if data is None else data)
        sequence = self._sequence
        task = ScheduledTask(due, sequence, f"task-{sequence:012d}", kind, payload)
        heapq.heappush(self._queue, task)
        self._sequence += 1
        return task.to_dict()

    def snapshot(self) -> dict:
        return {"version": 1, "now": self.now, "sequence": self._sequence,
                "queue": list(self.queue)}

    @classmethod
    def from_snapshot(cls, snapshot: dict) -> EventClock:
        if not isinstance(snapshot, dict) or snapshot.get("version") != 1:
            raise ValueError("unsupported clock snapshot")
        clock = cls(snapshot.get("now"))
        clock._sequence = _integer(snapshot.get("sequence"), "sequence")
        records = snapshot.get("queue")
        if not isinstance(records, list):
            raise ValueError("snapshot queue must be a list")
        seen = set()
        for record in records:
            if not isinstance(record, dict):
                raise ValueError("invalid task record")
            due = _integer(record.get("due"), "due")
            sequence = _integer(record.get("sequence"), "task sequence")
            kind, key = record.get("kind"), record.get("key")
            if (sequence >= clock._sequence or sequence in seen
                    or key != f"task-{sequence:012d}"
                    or not isinstance(kind, str) or not kind.strip()):
                raise ValueError("invalid or duplicate task identity")
            # An overdue task is valid after a naive advance ending inside a bin.
            seen.add(sequence)
            clock._queue.append(ScheduledTask(due, sequence, key, kind,
                                               _payload(record.get("data"))))
        heapq.heapify(clock._queue)
        return clock

    def advance(self, target: int, handler: Callable[[dict], Any],
                mode: str = "compress", coarse: int = 60) -> dict:
        target = _integer(target, "target")
        if target < self.now:
            raise ValueError("target cannot precede the current clock minute")
        if mode not in {"compress", "live", "naive"}:
            raise ValueError("mode must be compress, live, or naive")
        coarse = _integer(coarse, "coarse", 1)
        if not callable(handler):
            raise ValueError("handler must be callable")
        if self._advancing:
            raise ValueError("advance cannot be called recursively")
        start, began = self.now, time.perf_counter()
        dispatched, ticks_visited, lateness = 0, 0, 0
        self._advancing = True

        def dispatch(at: int) -> None:
            nonlocal dispatched, lateness
            self.now = at
            # New tasks scheduled for this minute are drained in sequence order.
            while self._queue and self._queue[0].due <= at:
                task = heapq.heappop(self._queue)
                record = task.to_dict()
                record.update(executed_at=at, lateness=at - task.due)
                handler(record)
                dispatched += 1
                lateness += at - task.due

        try:
            if mode == "live":
                for minute in range(start, target + 1):
                    ticks_visited += 1
                    # No callback at empty minutes, but the reference scans them.
                    if self._queue and self._queue[0].due <= minute:
                        dispatch(minute)
            else:
                last_visited = None
                while self._queue:
                    due = max(start, self._queue[0].due)
                    at = due if mode == "compress" else ((due + coarse - 1) // coarse) * coarse
                    if at > target:
                        break
                    if at != last_visited:
                        ticks_visited += 1
                        last_visited = at
                    dispatch(at)
                if last_visited != target:
                    ticks_visited += 1
            self.now = target
        finally:
            self._advancing = False
        full_minutes = target - start + 1
        return {"mode": mode, "start": start, "target": target,
                "wall_seconds": time.perf_counter() - began,
                "ticks_visited": ticks_visited, "dispatched": dispatched,
                "idle_skipped": max(0, full_minutes - ticks_visited),
                "total_lateness": lateness, "pending": len(self._queue)}
