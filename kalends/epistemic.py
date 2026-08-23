"""The epistemic oracle: exact ground truth of what each agent could know.

For every agent the simulator records every Exposure (a piece of information
reaching the agent, by observation or by being told) and derives the agent's
*normative belief* per proposition. This is the reference the benchmark scores
memory systems against. It is computed mechanically — never by an LLM.

Acceptance rule for hearsay (deliberately simple, documented in DECISIONS.md):
  - direct observation is always accepted;
  - a tell is accepted iff trust(listener -> speaker) >= TRUST_THRESHOLD
    AND the information is fresher (its `as_of` origination tick is newer)
    than whatever the listener currently holds.
A rejected tell still becomes an exposure (the agent heard the claim), so
memory systems are expected to record it without believing it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from .propositions import Proposition, Provenance

TRUST_THRESHOLD = 0.3


@dataclass(frozen=True)
class Exposure:
    tick: int                # when the info reached the agent
    as_of: int               # when the info originated (observation tick at chain root)
    prop: Proposition
    value: str
    kind: str                # "observed" | "told"
    event_id: int            # the event that delivered the info
    provenance: Provenance
    source_agent: Optional[str] = None   # speaker, for kind == "told"
    accepted: bool = True


@dataclass
class EpistemicState:
    """Ground-truth information record for one agent."""
    agent_id: str
    exposures: dict[str, list[Exposure]] = field(default_factory=dict)
    observed_event_ids: set[int] = field(default_factory=set)

    def _current(self, key: str) -> Optional[Exposure]:
        accepted = [e for e in self.exposures.get(key, []) if e.accepted]
        if not accepted:
            return None
        # Latest accepted exposure wins; ties broken by delivery order.
        return max(accepted, key=lambda e: (e.as_of, e.tick, e.event_id))

    # -- recording ---------------------------------------------------------
    def record_observation(self, tick: int, prop: Proposition, value: str,
                           event_id: int) -> Exposure:
        exp = Exposure(
            tick=tick, as_of=tick, prop=prop, value=value, kind="observed",
            event_id=event_id,
            provenance=Provenance(kind="observed", event_id=event_id),
        )
        self.exposures.setdefault(prop.key, []).append(exp)
        self.observed_event_ids.add(event_id)
        return exp

    def record_told(self, tick: int, prop: Proposition, value: str,
                    event_id: int, speaker: str, claimed_as_of: int,
                    claimed_chain: Optional[Provenance],
                    trust_in_speaker: float) -> Exposure:
        current = self._current(prop.key)
        accepted = (
            trust_in_speaker >= TRUST_THRESHOLD
            and (current is None or claimed_as_of > current.as_of)
        )
        exp = Exposure(
            tick=tick, as_of=claimed_as_of, prop=prop, value=value,
            kind="told", event_id=event_id,
            provenance=Provenance(kind="told", event_id=event_id,
                                  source_agent=speaker, upstream=claimed_chain),
            source_agent=speaker, accepted=accepted,
        )
        self.exposures.setdefault(prop.key, []).append(exp)
        return exp

    # -- oracle queries ----------------------------------------------------
    def belief(self, prop: Proposition) -> Optional[Exposure]:
        """The agent's normative current belief, or None (no accepted info)."""
        return self._current(prop.key)

    def has_heard_of(self, prop: Proposition) -> bool:
        """True if any information (accepted or not) about prop reached the agent."""
        return bool(self.exposures.get(prop.key))

    def belief_history(self, prop: Proposition) -> list[Exposure]:
        return list(self.exposures.get(prop.key, []))

    def independent_origins(self, prop: Proposition) -> int:
        """Number of independent evidence lines behind the current belief:
        distinct provenance root signatures among accepted exposures carrying
        the currently believed value. Reports relayed from the same witness
        share a signature and count once."""
        cur = self._current(prop.key)
        if cur is None:
            return 0
        sigs = set()
        for e in self.exposures.get(prop.key, []):
            if not e.accepted or e.value != cur.value:
                continue
            owner = self.agent_id if e.kind == "observed" else (e.source_agent or "?")
            sigs.add(e.provenance.root_signature(owner))
        return len(sigs)

    def was_superseded(self, prop: Proposition) -> bool:
        """Did an accepted later exposure replace an earlier accepted one?"""
        accepted = [e for e in self.exposures.get(prop.key, []) if e.accepted]
        values = [e.value for e in sorted(accepted,
                                          key=lambda e: (e.as_of, e.tick, e.event_id))]
        return len(set(values)) > 1
