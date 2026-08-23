# FORMALISM

Concise mathematical specification of the Kalends task. Notation chosen to
match the epistemic-logic literature (interpreted systems) where possible.
Everything here is implemented literally in the code; file pointers included.

## 1. World

- Discrete time t ∈ {0, …, T−1} (ticks).
- Agents i ∈ A, locations ℓ ∈ L, propositions p ∈ P (each p a
  (subject, predicate) pair with values from a finite vocabulary V_p).
- **Event stream** E₁:ₜ: an append-only sequence of typed events
  (move / incident / state_change / tell), each with tick, location, actors,
  payload, scope ∈ {public, private}.   [events.py]
- **Canonical state** S_t = Π(E₁:ₜ, S₀): a deterministic fold (projection) of
  the event prefix over the initial state. S_t assigns agent positions and a
  value val_t(p) to every proposition.   [world.py]

The generative process (movement policies, gossip policies, distortion) is a
deterministic function of (config, seed): all randomness is context-keyed
hash draws, r = H(seed, context) ∈ [0,1).   [rng.py]

## 2. Observation

Observation function O_i(e, S_t):
    agent i perceives event e  iff  i ∈ actors(e)
                                or (scope(e) = public ∧ loc_i(t) = loc(e)).
Observation is computed by the world, never asserted by agents. [observation.py]

## 3. Information set (the agent's horizon)

The **information set** I_{i,t} is the sequence of *exposures* reaching i by
time t. An exposure is either:
- obs(e): a direct observation of a prop-bearing event, carrying
  (t, p, v, provenance = Observed(e)); or
- told(j → i, e_tell): a communication, carrying (t, p, v', as_of,
  provenance = Told(j, e_tell, χ_j)), where χ_j is the speaker's *claimed*
  chain and v' may be distorted (v' ≠ value at χ_j's root).

Every exposure is causally grounded: its provenance references only events in
E₁:ₜ that precede it (no retrocausality — tested).   [epistemic.py, tests/]

## 4. Belief (normative)

The **normative belief** B_{i,t}(p) is a deterministic function of I_{i,t}
under the fixed revision rule R:
- direct observations are always accepted;
- told(j → i, ·) is accepted iff trust_i(j) ≥ θ and its as_of is strictly
  greater than the as_of of i's currently accepted exposure for p;
- B_{i,t}(p) = value of the accepted exposure with maximal (as_of, t, order),
  or ⊥ (no belief) if none is accepted.

R is a modeling choice (one point in the belief-revision design space), stated
once and applied uniformly; results are conditional on R. [epistemic.py]

Distinctions that are **not interchangeable** (each a different object here):
| concept | definition | where |
|---|---|---|
| truth | val_t(p) from S_t | world.py |
| observed | ∃ obs(e) ∈ I_{i,t} for p | epistemic.py `observed_event_ids` |
| heard | ∃ any exposure ∈ I_{i,t} for p | `has_heard_of` |
| available | heard (regardless of acceptance) | exposure list |
| believed | B_{i,t}(p) ≠ ⊥ | `belief` |
| stale | B_{i,t}(p) ≠ val_t(p) ∧ B_{i,t}(p) ≠ ⊥ | oracle property |
| retrieved | R(M_{i,t}, q) — whatever the memory system answers | memory/* |

## 5. Provenance

A provenance chain χ is a linked list of links Observed(e) | Told(j, e, χ').
Its **root signature** σ(χ) = (kind, event, observer) identifies the evidence
origin. Two exposures are **independent evidence** iff their root signatures
differ; the oracle's independent-origin count is
    |{σ(χ) : accepted exposures for p with the currently believed value}|.
Reports relayed from the same witness share σ and count once. [propositions.py]

## 6. Memory system (the object under test)

A memory system is a pair (ingest, answer):
    M_{i,t+1} = ingest(M_{i,t}, x_t)      x_t = next experience (exposure
                                          rendering + fields)
    R(M_{i,T}, q) → answer
subject to: M_i receives exactly the experiences derived from I_{i,·} — never
S_t, never another agent's I. (Equal-information contract; audited in
METHODOLOGY_AUDIT.md.)   [memory/base.py]

## 7. Benchmark queries

For each (i, p), queries q with oracle answers G(q) computed from I_{i,T},
B_{i,T}, and S_T:
- value: G = B_{i,T}(p) if ≠ ⊥ else "unknown"
- heard: G = 1[heard]
- source: G = source of the currently accepted exposure
- direct: G = 1[current exposure is obs]
- learned: G = arrival tick of current exposure
- superseded: G = 1[accepted values changed over time]
- independent: G = 1[independent-origin count ≥ 2]

Scoring is exact match; "unknown" is correct exactly when G says so. A value
answer where G = "unknown" is a **knowledge-boundary violation** (the metric
reported separately from accuracy).   [bench/questions.py, bench/harness.py]

## 8. Counterfactual ground truth

For an incident e*, the counterfactual world is the same generative process
run on E-schedule minus e* with identical context-keyed draws. Because draws
are keyed, the two runs differ only through causal descendants of e*. The
**causal descendant set** of e* is
    D(e*) = {(i, p) : B_{i,T}(p) ≠ B'_{i,T}(p)}
computed exactly, not estimated.   [counterfactual.py]
