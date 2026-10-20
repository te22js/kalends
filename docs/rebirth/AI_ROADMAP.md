# Intelligence upgrades with explicit contracts

The current build supplies six task contracts, expressive authored fallback,
scoped evidence, validated proposals, bounded budgets and an optional real REST
transport. It does not claim unrestricted generative people. The following
levels are an engineering sequence, not a delivery claim or guaranteed roadmap.

| Level | Contract and dependencies | Validation and budget hypothesis | Failure modes / current status |
|---|---|---|---|
| **1 — Grounded conversation** | Selected NPC view → reviewed intent and grounded dialogue clause; committed effects through world executor | Adversarial evidence/actor/recipient tests; intent 2 s/300 output tokens, dialogue 3 s/400; authorized model trial needed | Current offline/mock path works; Responses wire fixture works. No live model trial. Exact-clause grounding limits expression; free paraphrase requires stronger evaluated support. |
| **2 — Autonomous plans** | Own goals/resources/evidence and `plan_options` → chosen intention or wait; world validates and executes at scheduled decision points | Compare actual executed outcomes and intervention response against shared-policy controls; 2 s/500 cap at significant decisions | Contract and state-change tests exist; authored world policies execute background activity. No continuous LLM planner or evidence of learned personality. |
| **3 — Long-horizon reflection** | Retained records → at most eight supported memory selections; separate institutional state remains durable | Reject invented summaries and archival recovery; paired retention/decision tests; 3 s/500 cap per selected episode | Literal selection and forgery rejection work. Generative abstractions, learned priorities and their value remain untested. |
| **4 — Narrative direction** | Player-visible state/events → ranked actual opportunities and montage IDs | Test coverage, factual support and interruption behavior; 3 s/350 cap only on return | Selection contract and authored world opportunity logic are available. Free-form model narration and adaptive dramatic optimization remain future work. |
| **5 — Voice** | Transcription → same reviewed intent; validated text → optional speech, with explicit microphone consent | Measure recognition errors, repair rate, p95 response, per-minute cost; no irreversible action from speech recognition alone | No voice implemented or vendor configured. Risks include latency, accidental commitments and private audio transmission. |
| **6 — Creator assistance** | Source-labeled scenario schema → draft characters, plans and art references; explicit human review and deterministic validation before loading | Five outside creators should build distinct valid scenarios without engine edits; bounded authoring budget and licensing checks | Draft-only archetype contract exists. Full authoring UI, safe ingestion, governance and marketplace remain future work. |

A subsequent live-model trial should first use a small fixed adversarial corpus
with explicit spending authorization. Freeze evaluation prompts before running
heldout cases. Report actual outputs and failures, including rejected but billed
calls. Do not label mock success as AI capability or change the test cases after
seeing outputs without preserving that development history.

For richer language, compare at least: current authored clauses; model-selected
clauses; constrained paraphrases with source attribution; and a deliberately
unconstrained comparator evaluated offline. Investigate whether players notice
more character specificity and continuity while preserving low unsupported-history
rates. A syntactically valid response can still be factually wrong.

For plans and reflection, score actual procurement, obligations, relationships,
resource use and recovery from changed evidence. Action-name diversity alone
cannot establish better agency. Keep the existing negative information-cost and
memory findings visible: extra caution or memory need not improve production.

Per-task model routing should eventually share one session-level cost ledger and
reservation lock across adapters, with separate task sub-budgets. Current instances
have bounded policies and their own budget controller; combining them without a
shared cap would not establish a global spending guarantee. Persist prompt/schema
versions and invalidate context caches across world upgrades.

The engine interface is replaceable: an SDK, authorized local model or another
vendor can implement `generate(request, schema, policy)` and pass the same semantic
validation. Vendor integration does not grant direct world mutation, archival
knowledge, completed-action authorship or permission to make unapproved paid calls.
