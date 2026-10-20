# Rebirth cognition: scoped proposals and expressive offline characters

The game works without a model service. Its current conversations use authored,
character-specific clauses, retained experiences, local beliefs and the actual
scenario context. A model can help select an intent, grounded speech clause,
plan, or memory record through a provider-neutral interface. The world remains
the only authority over money, movement, knowledge acquisition and obligations.

This implementation lives in `kalends_rebirth/ai.py` and `language.py`; the old
Pompeii language module and frozen study sources are preserved.

## Six explicit task contracts

| Task | Input and permitted output | Current operational scope |
|---|---|---|
| Intent | Selected character context and player text → canonical reviewed action | Offline parser and mock/optional provider path; action revalidated at execution. |
| Dialogue | Own accessible topics/memories → a grounded topic clause plus optional safe expression | Character-specific offline realization; provider may select a supported clause and safe tone. It cannot write unrestricted factual prose. |
| Planning | NPC `plan_options`, goals and evidence → one permissible intention or wait | Validated proposal interface; world-authored policies execute background activity. No automatic LLM call on every tick. |
| Reflection | Retained records → at most eight selected literal supported memories | Validated selection, rejecting invented text and duplicate evidence. World decides what to consolidate. |
| Montage | Player-accessible records → up to eight actual event IDs | Presentation selection only; no invented outcome. |
| World content | Historical-source IDs and authored archetypes → a marked draft | Draft-only sandbox. No automatic ingestion into the authoritative game. |

Planning choices are **NPC intentions** in `plan_options`. The scenario's
`choices` are **player interactions**; the two are not interchangeable. The
model-facing layer returns data, never Python, SQL, HTML or executable code.

## Stable action protocol

```json
{
  "action": "examine_receipt",
  "recipient": "Sabina",
  "actor_id": "Player",
  "evidence_ids": [],
  "needs_confirmation": true
}
```

Optional quantity/value/topic fields are tightly bounded. Only Player can be the
actor of this reviewed interaction protocol. The selected recipient cannot be
changed by a provider. Unsupported fields, excessive or boolean quantities,
invalid verbs, unsupported citations, wrong role/target combinations, and bypassed
confirmation are rejected. New scenario transactions must also be an enabled
choice in the current supplied context. At confirmation the executor rechecks
proximity and current choices before calling the world, where cash, inventories,
permissions, deadlines and consequences are checked again.

Non-null `topic` is permitted only for a conversation and must be a declared
topic ID. Non-null `value` is permitted only for an assertion and must be one of
the two declared supply values. A provider cannot persist arbitrary prose inside
irrelevant action metadata. Contextual review labels are reused only when their
effective quantity, assertion value or conversation topic matches the proposal;
a typed four-unit purchase is reviewed as four units, not the one-unit shortcut.

A proposal does not complete a transaction. Assertions remain assertions: proposing
a supply claim does not edit physical supply or manufacture inspection evidence.
Question and refusal patterns cannot be overridden into transactions by a model.
The UI exposes explicit choices alongside typing, so exact parser phrases are
not the only interaction route.

## Observation and grounding boundary

`world.context(recipient)` provides that speaker's private view plus scenario-
scoped greeting, topics, available choices, relationship facets and current plan.
The AI code never receives a world object or an archive accessor. It only reads
the detached incoming JSON. Cache keys contain the entire scoped context, input,
provider/model and protocol/schema versions, so a changed minute, memory,
relationship or opportunity invalidates that cached proposal.

Dialogue provider results select a topic and its exact supporting IDs. The
realizer uses the corresponding authored/retained clause and a small safe tone
vocabulary. Unsupported history, arbitrary free-text facts, another character's
citations and mismatched clause citations are rejected. This intentionally trades
expressive freedom for a strong grounding boundary. Rich unrestricted paraphrase
is **not implemented or validated**. A future model-based entailment check alone
would not make it an authoritative source of history.

Knowing a record does not imply willingness to disclose it. Scenario contexts
also declare `disclosure_evidence_ids`. The dialogue adapter receives a reduced
context containing permitted topics and records, and the realizer checks the same
disclosure boundary. Marcus's unpaid loading account stays closed even though
he retains it. Planning and reflection receive separate private contexts; their
standalone proposal methods are operator tools, not a way to disclose all NPC
memories to the player. The game's reflection interaction recalls shared dealings.

The offline path already improves differentiation: Marcus distinguishes a cart,
a promise and a receipt; Felix cares about arrival and dependable goods; Sabina
focuses on her counter; Dama describes entrusted messages; Chreste cannot give
away workshop goods; Lucius frames assistance as reciprocal obligation. Scenario
clauses take precedence and reflect actual local state. Shared-history replies
use retained records instead of fabricated biography.

## Registry, transport and defaults

`AdapterRegistry` supports offline, deterministic mock, optional official OpenAI
Responses REST, and an opt-in loopback JSON protocol. `Cognition.from_env()`
selects a server-side adapter. `.env.rebirth.example` documents the configuration;
it is a template, not an automatically loaded credentials file.

Default external spending is **zero**. OpenAI inference requires an explicitly
enabled flag, server-side key, explicit model, positive approved budget, and
finite nonnegative price assumptions. A key or subscription alone is insufficient.
The transport sends `store:false`, bounded output tokens and a strict JSON schema
to the fixed HTTPS Responses endpoint. Redirects are refused. Refusals, incomplete
responses, malformed output and missing usage trigger fallback. No paid request
was made during implementation or its evaluation.

The REST shape was checked against current [official OpenAI structured-output
documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
on 21 October 2026. Schema-conforming output still needs semantic validation.
The API adapter is tested through an injected wire fixture; it has not been
validated against a configured live model in this sprint. A future SDK integration
can implement the same adapter interface without changing the world protocol.

A local endpoint must be loopback HTTP, explicitly enabled and confirm
`rebirth-cognition-1` in its response. It receives no API key. This project does
not assume that an arbitrary running local server speaks this protocol.
No local model was discovered or contacted as part of this work.

## Budgets, isolation, receipts and failure recovery

Each task has its own timeout/output/context policy. The default intent budget
is two seconds and 300 output tokens; dialogue and reflection allow three seconds.
At most one retry is allowed. A single pending daemon worker bounds concurrency;
a stalled call returns fallback and cannot create an unbounded queue of workers.
A stalled provider must still implement its own transport timeout. A Python
thread is not a process-isolation sandbox.

The external adapter reserves a conservative byte-based input estimate plus the
output cap before transport. It refuses a request that exceeds the remaining
configured estimated-cost budget. Failed calls with unknown usage retain their
reserve; they are not silently refunded. Reported usage and configured rates
account for paid invalid outputs as well as accepted ones. This is estimated
application accounting, not a guarantee of a vendor invoice.

The bounded in-memory cache stores only validated successful results. Failures
and timed-out fallbacks are not cached. Returned data are copies. Redacted run
receipts record protocol/prompt versions, task, provider/source kind, attempts,
latency, token usage, cost estimate, cache status and context hash. Errors expose
error types rather than credentials. World Lab can show `language.cognition.debug()`;
normal gameplay should not expose provider internals or private contexts.

## Evidence, tests and remaining limits

The adversarial suite exercises ordinary/ambiguous intents, protected questions,
wrong actors/targets, invalid quantities, unavailable choices, unsupported facts
and citations, context/cache separation, stale context, timeout recovery,
reflection forgery, plan changes, draft-only content, budget refusal, Responses
wire shape and usage accounting. Wire fixtures are labeled separately from mocks
and live model outputs. All are developer tests, not an independent model trial.

Current limitations include bounded vocabulary, rigid grounded clauses, authored
plan options, literal memory selection, a single configured provider/model per
Cognition instance, and no voice. Separate Cognition instances can supply different
models/budgets, but shared multi-provider session accounting is not yet built.
Actual model quality, token consumption, latency and unsupported-claim rates need
an explicitly authorized bounded live-provider evaluation.

`python -m kalends_rebirth.ai_eval --out <new-directory>` reproduces the fixed
functional corpus without loading configured providers or credentials. The
completed release run in `results/rebirth/ai_evaluation_release_v2` passes 42/42 cases, with
raw proposals/receipts, source and artifact hashes, and a readable report. Its
22 ordinary intent cases, adversarial fixtures, world integration, stalled worker,
zero-budget refusal and injected REST response remain distinct groups. The
58-test AI suite additionally covers willingness filtering, redirect refusal,
missing usage, context isolation and known-usage accounting after incomplete
responses. Neither result is evidence about live LLM performance.

Migration regressions distinguish the original `household-service` commitment
from Rebirth's `rebirth-service`. Typed service requests select the currently
enabled offer (`service` or `return_service`); no offer or insufficient remaining
time leaves a conversational proposal. Actual migrated fulfillment, new chapter
fulfillment and protected refusal cases are tested separately.
