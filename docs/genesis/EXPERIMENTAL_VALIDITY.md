# Genesis: experimental validity and claim boundaries

This study is separate from Fork the City. The historical code, results and
claims remain under `kalends/city`, `results/fork_city` and `docs/fork_city`.
Do not merge their categorical loss with Genesis executed outcomes.

## Prospective record and independent units

The plan is `results/genesis/preregistration.json`, committed with the runtime
at **a1010fc** before held-out execution. Seeds 20000–20009 were reserved for
development; the development runner actually uses 20000 and 20001. Seeds
50000–50029 are fresh held-out seeds. The primary experiment contains 720 worlds:
30 seeds × three families × two populations × four configured policies.
There are 180 additional control worlds. All horizons are 96 ticks. The run
manifest embeds the complete plan, exact source commit, hashes of Python source
files and the preregistration, and the worker count. The completed summary
records whether source stayed unchanged during execution and hashes raw data.

The one confirmatory comparison is lineage-gated guarded memory minus ungated
guarded memory on delivery fill. First pair conditions within each seed, family
and population; average the six differences within seed; bootstrap the 30 seed
means, with replacement, 10,000 times. The 2.5th/97.5th percentile endpoints use
fixed bootstrap seed 72831. The estimand weights six cells equally; it is not a
population-weighted individual treatment effect. Paired exogenous draws use
seed/tick/identity keys. Agents, ticks, decisions and families sharing one seed
are not counted as independent samples.

This plan is a repository preregistration, not a third-party registry or a claim
of blinding researchers to their own simulator. Held-out source correctness
failures would invalidate affected runs; changes and reruns must be documented.
Do not tune policy parameters against these results. Cells, capacity controls,
resource controls, role comparisons and valuation sensitivity are descriptive;
their many intervals do not support a family of adjusted discoveries.

## What each measurement means

| Layer | Measurement | What it does not establish |
|---|---|---|
| Local recall | Selected value equals latest accepted retained supply record, after retained retractions | Truth about the current world; human-like memory; byte/token efficiency |
| Present belief | Prediction equals evaluator supply at decision time; abstention and answered-only accuracy reported separately | Profitable action or correct historical source assessment |
| Action choice | Executed reserve/verify/defer counts and local evidence IDs | Optimal action, optimal regret, intelligence |
| Physical execution | Attempted versus filled orders, stock and inventory deltas | Value from an unfilled order |
| Contract outcome | Units delivered divided by units due in settled citizen obligations | Social welfare, satisfaction, all forms of consumption |
| Economic valuation | Cash change + disclosed terminal inventory value × inventory change | Welfare, market equilibrium, optimal-policy regret |
| Social state | Trust changes and commerce-access rules | A validated model of human trust or human relationships |

The decision opportunity set is policy-dependent: inventory, obligations and
official duties determine who decides. Recall and belief fractions therefore
have different denominators across conditions and are diagnostic, not causal
memory-quality rankings. Structured and guarded backends receive exact canonical
keys and can hit a local-reference ceiling. A ceiling is disclosed rather than
presented as a hard memory challenge. The primary experiment does not measure
LLM reasoning, stochastic language quality or real user behavior.

## Executed economic accounting

Every purchase moves only the quantity actually filled. A zero fill adds zero
inventory and spends zero purchase cash; later missed obligations still incur
their penalties. Settlement records delivered and missing units. Cash already
contains expenditure, inspection fees, delivery revenue and penalties, so these
components are not subtracted or added a second time. Primary utility sensitivity
uses terminal unit values **1, 3 and 6**. Changing this value can reverse an asset
comparison; delivered units remain the primary physical outcome.

Citizen delivery obligations are scheduled at ticks 7,15,…,95, with role-specific
quantities. Their denominator is fixed by population/role/horizon and is not
selected after observing success. Player-created contracts are reported in the
player account, separately from the citizen primary outcome. Incomplete future
obligations are not counted as settled failure. There is no computed optimal
oracle, so a regret field is null. Missed units and zero fills are observed
shortfalls; unobserved foregone opportunities are not assigned invented prices.

The narrow economy has one good, exogenous arrivals and supply-linked posted
prices, working capital, delivery payment and debt-producing penalties.
Consumption and utility are simplified. External settlement payments and losses
mean citizen cash is not a closed conservation quantity. Direct bilateral trades
do conserve cash and grain. Debt is allowed; a fine does not silently disappear
when a citizen lacks cash. This is not a calibrated Roman or modern economy.

## Resource and ordering controls

At each eight-tick arrival, fixed supply adds 22 units in the available regime
or 6 in the disrupted regime, independent of population. Per-capita supply adds
ceil(2.6N) or ceil(0.7N). Seeded order uses a fresh keyed ordering at each decision
tick; rotating and historical fixed ordering are also implemented. These rules
make the confounds testable; seeded ordering is not a universal fairness theorem.

The complete fixed/per-capita × fixed/seeded resource/order control is at
reversal-family, 32 citizens, guarded ungated memory, capacity32. The primary
cell supplies one of its four baselines. Capacity8 and128 vary only capacity;
the shared-policy comparison changes the whole role strategy to the historical
shared reserve/defer rule. It is **not** an isolated preference-only treatment.
Controls cannot establish robustness across every family, population or economy.

Role strategies can override evidence admission under deadline pressure or
producer procurement. Consequently a null gate effect is meaningful for this
combined policy, not proof that provenance never matters. Both gate conditions
use a common confidence rule that already counts source roots. Sender counting
is an admission comparator, not a fully provenance-blind agent. Declared distinct
roots are also not statistically independent or authenticated physical witnesses.

## Information boundary and source history

FIFO memory limits the number of experiences, not bytes or tokens. Every
acceptance, belief query, gossip selection, dialogue and decision reads retained
records. Gossip hop metadata and send receipts are bounded too. Owned cash,
inventory, commitments, location and institutional trust persist as world state;
these are not a backdoor store of supply facts or episodic explanations. A full
archival ledger and archival exposure stream remain for auditing/evaluation.
Eviction tests poison archival beliefs and verify that forgotten information
does not return through operational queries.

The delayed opening report comes from Dama's actual tick0 observation and
arrives at tick6 after the reversal at tick4. This is a genuine outdated report,
not an invented “old manifest.” Retractions are messages, scoped by source root
and observer, and consume FIFO slots. A forgotten tombstone can permit a later
claim to be accepted again; this is part of the bounded model and a limitation.

A paid inspection costs 2 and arrives next tick. It produces new private world
observations; it may also inspect at most two actual dispatch records dated
within eight ticks of retained claims. Those log reads are explicit events with
`record_as_of` and parents referencing real earlier supply events. This is a
declared external information source, not free archive access by a policy.
Matching dated evidence can establish a contradiction or a truthful old report.
Current disagreement alone does not establish earlier falsity; unchecked old
claims and “unknown” claims receive distinct assessments. Retained assessment
receipts prevent repeatedly punishing the same remembered report.

## Interventions and causal interpretation

An identity rerun must reproduce ledger and accounts. Removing a selected player
claim reconstructs accepted commands from the initial seed, omits the action,
and reruns subsequent simulation. Surviving source references are remapped to
their actual counterparts. Dependent retractions of a removed source are
explicitly skipped and reported; ambiguous/nonexistent source counterparts reject
the fork. Other future commands stay fixed rather than being reinterpreted by an
LLM. This estimates a specified simulator intervention conditional on retained
player commands, not a model of how a human would choose differently.

Immediate operator corrections are free and privileged. Ordinary inspections
are costly, delayed, private and available through participant actions. The
primary policy comparison gives all autonomous policies the same fee/delay/rules;
it never treats an operator correction as a fair competing autonomous baseline.
Separate verification controls disclose payer, recipient, timing and costs.

A parent edge documents a recorded structural dependency, not causal necessity.
A changed branch is evidence of that intervention's effect in this simulator,
not proof that every differing descendant requires the original message. Player
mode exposes witnessed or explicitly cited records; Research mode intentionally
exposes private/operator information. The local toggle is not an authenticated
multiuser security system.

## Product and external validity

Default capacity32 can forget an old relationship episode while durable trust
persists. Dialogue must then admit that the reason is no longer retained.
The curated three-day demonstration uses capacity256 and seed2026, disclosed
separately from benchmark defaults. No retention policy was tuned on held-out
experiments. A curated demonstration is not a typical-effect estimate.

The grammar is deliberately narrow. It normalizes claims for confirmation and
does not implement unrestricted language or tomorrow forecasts. Custom adapters
can propose permitted actions but cannot supply uncensored factual narration.
The measured path makes zero provider calls and incurs zero provider inference
charges; CPU time and engineering are not free. No human study, hosted background
world, multiplayer, creator SDK, second world or commercial demand is claimed.
The research contribution, if any, is a controlled and reproducible case study;
memory/action gaps, agent societies and replay have substantial prior art.
