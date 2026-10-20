# Genesis architecture

**20 October 2026.** This describes the implemented local system, including
post-study correctness repairs. The original Fork the City application and its
historical artifacts remain separate.

## Runtime and interfaces

[`GenesisSimulation`](../../kalends/genesis/simulation.py) extends the existing
`CitySimulation`, reusing the canonical ledger, event representation, state
projection, schematic locations, agent identities and keyed randomness.
`GenesisEconomy` adds player delivery agreements to the existing economy
projection. The new browser application is buildless HTML, CSS and JavaScript;
the HTTP adapter uses Python's standard library. There is no required model
service, external asset service or browser framework.

The operational chain is:

**seeded world → events → legitimate observations → retained experiences →
local knowledge → role decisions → executed transactions → persistent history.**

`GET /api/state` returns original/altered snapshots, the current view mode,
comparison, dialogue history and optional return report. `GET /api/agent?id=…`
returns a public character view, with an additional private view in operator
mode. `/api/trace` returns permitted evidence ancestry; `/api/export` exports
the current permitted state and accepted commands. Mutation endpoints handle
proposals, confirmation, stepping, reset, mode changes and historical forks.

[`GenesisSession`](../../kalends/genesis/server.py) serializes these operations
with a reentrant lock. A new session deterministically executes ticks 0–2 before
the player arrives at the controls. Time subsequently advances only on explicit
step/run requests. “Return after three days” executes up to 72 ticks, bounded by
the configured horizon, and reports the actual elapsed count. It does not
simulate background processing during a stopped server or unopened browser.

## Player actions and dialogue

[`language.py`](../../kalends/genesis/language.py) compiles a limited natural
language grammar into explicit actions: claim, inspection, trade, contract or
retraction. Questions produce a grounded reply without inserting a world action.
A proposal records its recipient, creation tick, interpretations, model/version
metadata and authorized-view hash. It does not mutate the simulation.

The player reviews canonical transmission text and explicitly confirms one
interpretation through `/api/act`. The server rejects missing, repeated or stale
confirmations. It validates the action again and executes it against a copied
candidate simulation; a rejected transaction leaves the original intact. The
accepted action, its receipt and event identifier enter the command journal.

The offline grammar is the working default. Optional adapters receive copied
local views, rather than the simulator or evaluator. Their action schemas and
evidence identifiers are validated. Confirmation descriptions are rendered from
validated actions; custom factual replies use the grounded renderer, and custom
clarifications cannot introduce an unsupported causal story. This is a bounded
intent interface, not an implemented general conversational model.

## Information and character behavior

Each participant has an archival experience stream and a separate FIFO retained
window. Capacity counts experience records, including receipts and movement;
it is not a token or byte budget. Knowledge, acceptance, dialogue, decision
evidence and gossip operate on retained records. The archive remains available
for auditing, not ordinary recovery of forgotten claims. Retractions consume
normal slots; forgetting a retraction can therefore matter.

Role preferences change actual policy behavior: producers procure early,
traders seek inexpensive observed quotes, couriers relay less certain reports,
officials inspect periodically, and merchants check uncertain costly reports.
Policies receive local beliefs, owned accounts, commitments and observed quotes.
Execution validates inventories, cash and commercial access against world state.

Ordinary inspection costs two denarii and delivers a private observation on the
next tick. A visit can inspect at most two dated dispatch records within an
eight-tick lookback. These are new observations of an explicit record mechanism,
not unlimited memory recovery. Assessments distinguish a contradicted historical
claim from an old report that was true when made. Trust and access can change;
current owned accounts and institutional relationships are durable world state.

Player snapshots omit citizens' private beliefs, preferences, accounts and
decision records. Player traces disclose witnessed or explicitly cited records;
operator mode exposes privileged facts and audit history. This local toggle is
an intentional research view, not an authenticated multiplayer security boundary.

## Persistence and historical alternatives

The version-2 JSON session file contains initial configuration, accepted
commands, proposals, dialogues, disclosure identifiers and view mode. Saving
writes a temporary file and replaces the journal. Restart reconstructs the world
from configuration and accepted operations, including the deterministic opening;
questions and proposal acceptance state are then restored. There is no pickle
loading or wall-clock catch-up. This implementation assumes compatible runtime
code, not a promised cross-version migration protocol or crash-proof database.

Historical forks reconstruct from the same initial seed and replay accepted
structured actions. Removing a confirmed player claim omits that action.
Surviving source references are remapped to their counterparts in the rerun;
dependent actions targeting a removed source can be skipped with an explicit
diagnostic. Ambiguous or missing surviving counterparts are rejected rather
than guessed. Current-moment correction preserves already accepted same-tick
actions before appending the privileged observation. The original is preserved.

The intervention occurs within a tick, so a removed message does not imply an
identical prefix through the whole tick. Both histories subsequently use the
same keyed exogenous schedules. This is constrained historical replay, not an
arbitrary event editor. Recorded parent links describe structural dependencies;
accounting links for fungible inventory are neither minimal nor necessary causes.
An actual fork establishes the result of that particular intervention.

## Outcome measurement and disclosed curation

[`evaluation.py`](../../kalends/genesis/evaluation.py) measures actual filled
purchases, settled deliveries, inspection fees and account changes. Net assets
equal cash change plus disclosed terminal value times inventory change; cash
already includes fees, payments and penalties. No optimal-policy regret or
general social welfare estimate is computed.

Ordinary `GenesisConfig` defaults to **capacity 32**. The independently launchable
[`scenario.json`](../../demo/genesis/scenario.json) deliberately uses **256** so
Livia can retain both the original message and its assessment after 72 ticks.
This is product-demo curation, not a finding about default memory. The frozen
primary study used **capacity 32**, with separate capacity-8/128 controls. Its
runtime commit and hashes are recorded in the held-out manifest; subsequent
source repairs do not silently replace that measured artifact. See
[Experimental validity](EXPERIMENTAL_VALIDITY.md) and
[the results audit](RESULTS_AUDIT.md) for the scientific limits.
