# ARCHITECTURE

The whole system in ~10 minutes. Everything is Python stdlib, headless, deterministic.

## One-paragraph summary

Kalends is an event-sourced micro-world (Pompeii, 79 CE; ≤32 agents) in which
canonical reality is a deterministic fold over an append-only event ledger.
Each agent perceives only what visibility rules allow, and the simulator
maintains a per-agent **epistemic oracle**: exactly what information reached
that agent, when, from whom, with what provenance. Pluggable **memory systems**
(vector / structured / hybrid) receive the same experience stream and are then
scored — by Kalends-MemoryBench — against the oracle on belief accuracy,
staleness, provenance, and knowledge boundaries. No LLM is anywhere in the v0
loop; the LLM slot exists behind two narrow interfaces for v1.

## The pipeline

```
WorldEvent ──append──> Ledger ──project()──> WorldState        (objective reality)
     │
     └──observe()──> Observation ──> EpistemicState per agent  (ground truth of
     │                                “what could A believe?”)  ← the oracle
     └──────────────> Experience stream ──> MemorySystem       (system under test)

MemoryBench: questions generated from oracle → answered by MemorySystem → scored.
```

An LLM is never the authority on what happened. Agent behavior in v0 is
deterministic seeded policy (movement schedules + gossip rules), which is what
makes exact ground truth possible.

## Major entities

| Entity | File | What it is |
|---|---|---|
| `WorldEvent` | `kalends/events.py` | Frozen record: id, tick, type, location, actors, payload, scope |
| `Ledger` | `kalends/events.py` | Append-only list of events; hashable for replay checks |
| `WorldState` | `kalends/world.py` | Pure projection of the ledger: agent positions, object states, relationships |
| `Proposition` | `kalends/propositions.py` | `(subject, predicate)` key, e.g. `("bakery","condition")` |
| `Provenance` | `kalends/propositions.py` | `Observed(event)` or `Told(by, at_event, upstream_claim)` — a linked chain |
| `EpistemicState` | `kalends/epistemic.py` | Per-agent oracle: every exposure (observed/told), current normative belief per proposition |
| `MemorySystem` | `kalends/memory/base.py` | Interface under test: `ingest(Experience)`, `answer(Query) -> Answer` |
| `Scenario` | `kalends/scenarios/` | Agents, locations, relationships, schedules, scripted incidents |
| `Simulation` | `kalends/simulation.py` | The tick loop tying it all together |

## Event schema

```python
WorldEvent(
  event_id: int,          # ledger sequence number
  tick: int,              # integer simulation time (1 tick = 1 hour in v0)
  etype: str,             # "move" | "incident" | "state_change" | "tell"
  location: str,
  actors: tuple[str,...], # agent ids involved
  payload: dict,          # e.g. {"prop": ["bakery","condition"], "value": "burning"}
  scope: str,             # "public" (anyone co-located sees it) | "private" (actors only)
)
```

`tell` events carry: proposition, transmitted value (possibly distorted),
speaker, listener, and the speaker's *claimed* provenance chain. Communication
therefore always has an explicit source — an invariant, not a convention.

## Observation pipeline

An agent observes event E iff: agent is an actor of E, or (E.scope == "public"
and the agent's location at E.tick == E.location). Observation is computed by
the simulator from the ledger + projected positions — never asserted by agents.

## Belief representation & the oracle

For each agent, `EpistemicState` keeps per proposition a time-ordered list of
`Exposure`s (observed or told, value, source, tick, provenance, trusted-or-not).
The **normative belief** is the value of the latest *accepted* exposure
(direct observation always accepted; hearsay accepted iff relationship trust ≥
threshold and information is newer than what's held). Three distinct things are
therefore always separable:

- **World truth**: `WorldState` at tick t.
- **Normative belief**: what the agent *should* believe given its exposures
  (may be false — e.g. a trusted but distorted rumor; that's correct behavior).
- **Reported belief**: whatever the memory system under test answers.

Staleness = normative belief ≠ world truth (an oracle property, not an agent
error). Memory systems are scored against *normative belief*, not world truth.

## Memory interface (the experimental surface)

```python
class MemorySystem:
    def ingest(self, exp: Experience) -> None      # exp: structured fields + text rendering
    def answer(self, q: Query) -> Answer           # Answer(value, source_kind, source_agent, learned_tick)
```

Implementations in v0: `VectorMemory` (hashed bag-of-words cosine retrieval,
no supersession logic), `StructuredMemory` (keyed by proposition, latest-wins,
exact-match retrieval), `HybridMemory` (structured first, vector fallback).
Working/episodic/semantic/reflection layers are *future implementations behind
this same interface*, not separate subsystems.

## Simulation loop

```
for tick in range(T):
    scripted incidents for this tick → ledger
    each agent's movement policy (schedule + seeded jitter) → move events
    for each co-located pair: gossip policy → tell events (with optional seeded distortion)
    for each new event: compute observers → update EpistemicState → emit Experiences
```

Single RNG seeded per run; identical seed ⇒ identical ledger ⇒ identical
everything (tested).

## Benchmark interface

`kalends/bench/questions.py` generates questions from the oracle
(belief value, known-vs-unknown, source attribution, provenance chain depth,
learned-at tick, superseded-or-not — including alias-phrased and unanswerable
questions). `kalends/bench/harness.py` replays the experience stream into each
memory system and scores answers. Output: per-system, per-dimension table +
JSON dump.

## CLI

```
kalends simulate rumor --seed 42 [--out trace.json]   # deterministic trace + summary
kalends benchmark --seed 42                           # MemoryBench v0 table
kalends explain --seed 42 --agent Livia --prop bakery.condition   # provenance chain
```

## Invariants (tested in tests/)

1. Same seed ⇒ byte-identical trace (determinism/replay).
2. No agent's epistemic state references an event it could not observe or a
   fact it was never told (knowledge boundary).
3. Beliefs and canonical truth are separate objects; mutating world truth does
   not update any agent's belief without an observation or tell event.
4. Every `tell` has an explicit source agent.
5. Private events are known only to their actors until communicated.
