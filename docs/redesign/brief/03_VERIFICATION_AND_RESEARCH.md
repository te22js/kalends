# Verification, evidence and research disposition

## 1. What was tested in this assistant session

The live user application and repository were not accessible through the browser connector. It returned an originating-browser-context error. The assistant did not operate `localhost:8823`, inspect actual 3D assets or validate real saves.

Directly inspected:

- All four supplied documents, including the complete HTML copy catalog.
- 52 primary copy cases and 649 primary text blocks, excluding narrow-layout duplicates.
- Local Chromium rendering of that HTML at desktop and 390 CSS pixels. At 390, the catalog document width matched the viewport; this is not a game responsiveness claim.
- The standalone newly authored interaction reference, using fixed frontend data.

`evidence/REFERENCE_TEST_RESULTS.json` records **46 passed assertions** in Chromium 144.0.7559.96. These cover the reference’s declared navigation, conversation, evidence, payment review/cancel, accepted-versus-draft allocation/promise distinction, settlement arithmetic, history, research-status disclosure, reset, focus, numeric guards, reduced motion and no document-width overflow across five views at 390/768/1440 pixels.

The first prototype implementation allowed draft promise edits to affect the later settlement summary. It was corrected by separating the accepted promise from draft input, and the regression test now explicitly changes both allocation and promise after saving, then verifies the committed version is used.

Visual inspection also found obsolete “allocation saved / can change it” copy and an old pending-action toast after settlement. Both were corrected and covered by explicit state-transition assertions.

An initial screenshot captured the entry animation mid-fade. Captures were regenerated with finite animations disabled to show the settled reference state. This is a capture correction, not evidence of performance optimization.

The test code is included. It does not run a human-comprehension study, a screen-reader audit, live-model cognition, the real simulation or the user's app. No frame-rate result is claimed for either application.

## 2. Product gates for the repository-connected agent

### Gate A — Authoritative action integrity

| Test | Required result |
|---|---|
| Open a conversation | No payment, promise, allocation or unintended time advance |
| Ask a free permitted question | Exactly one validated observation/disclosure; no extra review modal; no pre-click hidden contents |
| Ask a paid question | Actual fee/time shown before commitment; cancellation leaves canonical state unchanged |
| Preview then receive a state update | Stale preview cannot commit without fresh validation; useful explanation |
| Double click, delayed reply or reconnect | At most one accepted consequential action; ambiguous result reconciled by receipt/command identity |
| Draft edits after saving | Actual execution uses accepted allocation/promise, not uncommitted fields |
| Open notebook or historical card | No facts installed in NPC memory, no deadline unintentionally crossed |
| Read source/evidence | Only participant-authorized content; no private fields hidden merely with CSS |
| Two lives in two tabs | Every interaction addresses the correct journal; no global current-life ambiguity |
| Save failure | No partial live-world mutation; intelligible error and safe reconciliation |

### Gate B — First-session comprehension and interaction

In both domains, test a complete default path, a valid alternative, a cancellation, an out-of-order discovery, an unavailable action, a deliberate time crossing, a reload and a saved return. Include guidance off/resume.

Pompeii must visibly teach moving, approaching, speaking, obtaining information, comparing an account, reviewing a consequence and finding a next possibility. Do not require precise parser phrases. An inaccessible messenger must not trap the tutorial.

The controller must permit ordinary experimentation: short keyboard taps, retargeting, interrupted routes, notebook during movement, changing rooms in an unusual order, clicking another person and returning from Help. Respect text-entry focus. No movement hotkey should move Aelia while typing.

Measure unnecessary steps in a fixed task: asking Sabina for her free account, obtaining a report, inspecting a known document. The goal is removing redundant forms, not reducing explicit consent for consequential actions. Report click counts, modal count, visible text and completion failures against the current actual baseline.

A proposed user gate is that a fresh participant can explain role, immediate situation, available action, cost, result and one historical evidence/fiction distinction. This is a small formative check, not a validated score or statistically powered efficacy outcome. Record coaching. Do not count guide acknowledgments as comprehension.

### Gate C — Actual displayed copy

Read the production DOM and visible scene, not just formatter outputs. Every surface needs clear actor, action, quantities, units, tense and next step. A generic review string might be overridden in the frontend; determine where the user actually sees it before declaring it a visual blocker.

Prioritize:

- “Retained memory” and “admitted report” leaking into speech.
- Policy goal fragments and privacy errors presented as personality.
- Duplicate generic instructions and time disclaimers.
- Unqualified factual claims created by smoothing an uncertainty sentence.
- Empty memory confused with “never met.”
- Raw world minutes mistaken for a participant-facing clock.
- Pending versus completed transactions and current versus historical requirements.
- Revealing an unseen relationship score in the result screen.

Case 048 needs a dedicated regression: use an OPEN round with no earlier closure/permission failure, submit zero for an operation that requires a positive promise, and verify the intended rejection with no mutation. Then separately verify the closed-round guard. Its existing observed error proves only the latter.

### Gate D — Historical education

Reconcile the source-register ID collision. Every historical assertion should have a correct claim-scoped reference. Distinguish direct observation, scholarly reconstruction and fictional gameplay. Verify the object taught by an interactive prompt is actually visible. Do not introduce new antiquity claims from model prose.

Cards should not expose source/licensing boilerplate as the first thing a learner reads, but those details must remain available. Changing placement does not authorize removing important limitations. No unlicensed historical photographs or fabricated ancient quotations.

### Gate E — Graphics, motion and access

Inspect matched actual-game captures at representative desktop and narrow viewports, enlarged text and reduced motion. Test keyboard-only primary flows and the basic screen-reader path where supported. DOM accessibility snapshots alone do not substitute for assistive-technology use.

Record actual browser/hardware, viewport, device pixel ratio, graphics quality and whether recording is active. Separate initial load, warmed-up movement, idle, conversation and a longer session. Frame callbacks are not physical input-to-display latency. Compare like with like.

Require no overlap of main action and dialogue, reachable controls, stable focus, sensible collision/occlusion, no repeated camera reset, truthful NPC activities and a preserved context on return. Do not claim a universal 60 FPS guarantee from a short local sample.

Capture the entire interface when evaluating tutorial clarity. A canvas-only video cannot demonstrate HTML instructions, modal sequencing or conversation layout.

## 3. The research result now on record

The supplied latest handoff reports:

- 8 held-out workflow structures × 20 noise seeds × 5 arms = 800 executions.
- Candidate and V3: 140/160 primary passes each.
- 160 paired ties; one workflow fails across all arms.
- An independent agent wrote tasks from a public contract, without target implementation access.

Conclusion: **no held-out advantage was demonstrated in this test.** Do not call this an external independent replication, claim general equivalence, or combine it with the earlier 30/30-versus-0/30 authored case into one superiority result.

The research page should show the progression: earlier narrow positive case; later no generalization advantage under these workflows; open failure diagnosis. This is scientifically more useful than highlighting only the best number.

## 4. The next research work, without another architecture spree

### A. Freeze and diagnose

Preserve tasks, source, parameters, receipts and evaluator. Diagnose the all-arm failure on explicit development/debug copies: insufficient observable information, impossible action chain, observation encoding, memory retention, retrieval, plan controller or evaluator error. A hidden unobserved change is not automatically a memory failure.

Do not tune on exposed held-out cases and then relabel them unseen. Any next confirmatory test requires genuinely new structures, not just new names or noise seeds. Task authors should receive the domain contract and objective, not the candidate's favored dependencies.

### B. Test whether richer expression helps without changing truth

If an endpoint and numeric budget are authorized, evaluate one foreground character with:

1. Strong authored dialogue baseline.
2. Model realization of the same permitted semantic content.
3. Model intent interpretation plus validated action proposal, as a separate intervention.

Do not change planning, memory capacity, action affordances and dialogue simultaneously and attribute the gain to memory. Measure intent correctness, supported factual statements, invalid/unauthorized proposals, requests for appropriate clarification, temporal updates, grounded return recall, latency, failure recovery and actual cost.

A fabricated citation is failure even when the prose sounds natural. No retry may silently spend twice. Log model/version, prompts, admitted context and accepted/rejected outputs without secrets. Live model generations are not deterministic merely because temperature is low. Replay recorded accepted actions for exact world reconstruction; new generations form a different experimental path.

LongMemEval and LongMemEval-V2 provide already-established memory evaluation categories. They are comparators, not implemented baselines unless the agent really runs them. The separate simulator's downstream outcomes are useful, but not an invention claim for memory-to-action evaluation.

### C. Budget accounting

Count all accessible memory: episodes, summaries, semantic records, plans, goal registers, retrieval index, cached context and archive read access. Equal record counts are not equal byte/token budgets. State clearly whether embeddings are genuinely provisioned, which model/version produced them and what their index/inference cost is. Otherwise mark the arm unavailable.

Use seed-level paired outcomes within task structures, and show the task-structure count separately. Avoid pseudoreplication through large numbers of correlated events. Prefer practical effects and failure cases to headline test counts.

## 5. Company and learning gates

This redesign is a product hypothesis. Its strongest result would be a person independently choosing to continue, recognizing someone they met and understanding a later consequence. A nicer screenshot is not that evidence.

School use requires more than accurate cards: a clear learning objective, appropriate lesson fit, teacher workflow, accessibility, age/privacy safeguards and a meaningful assessment. This release can prepare an optional teacher guide and small source-reasoning exercise. It cannot claim educational benefit without a suitable human study. No recruitment or outreach is authorized by this brief.

Preserve the broader world technology. Do not turn every session into compulsory coursework, and do not claim that compressed simulated time equals additional human subjective years.

## 6. Final report structure

Report:

- Actual current commit, launch command, browser URL and tested save directory.
- Old/new participant journeys and matched current screenshots.
- What the participant now sees instead of machine terminology.
- Accepted and rejected interaction paths, including delayed/cancelled/reloaded cases.
- Graphical and motion changes with measured scope.
- Source corrections, not a blanket historical-accuracy claim.
- The null research finding and any genuinely new diagnostic/model data.
- Whether the model was live, local, offline or mocked, and authorized spend.
- Human questions still open, high-severity remaining defects and the smallest next useful test.

An honest incomplete gate is better than a success label unsupported by the captured experience.
