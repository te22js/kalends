# Kalends — research protocol for the next phase

Prepared 24 October 2026. **Prospective protocol; no new experimental results are claimed.** Register the final executable version before evaluating fresh test cases. Source IDs refer to `00_DECISIONS_AND_SOURCES.md`.

## 1. Research decision

Do not respond to the V3 tie by adding “V4” and another list of cognitive components.

The immediate research target is **continuity of a consequential plan across interruption and new evidence**, under a real memory budget. The product demonstration is a person remembering, revising and acting differently for a reason the participant can understand.

This is not a claim that plan state, episodic memory, belief revision, semantic graphs or reflection are new. MemoryArena, AMA-Bench, Mem2ActBench, Hindsight, StateMemBench and CounterMem already occupy important parts of this space. [R1–R6]

### One primary question

> With the same admitted observations, action controller and resource limits, does a goal/evidence-linked retention and revision mechanism improve completion of delayed, multi-step obligations after interruptions, relative to credible retrieval and current V3 baselines?

### Two secondary questions

1. Does any improvement survive charging for all cognitive state, retrieval and model computation?
2. Can the product preserve the participant's meaningful intervention opportunities when presenting long intervals compactly, without privileged-information leaks?

The second question is a separate pacing/interaction evaluation. It is not a claim of simulation compute acceleration or human learning.

## 2. What the existing results permit us to say

K4 reports 972 one-day executions, including 432 matched V3–V2 pairs with identical primary outcomes and executed ledgers. Autonomous background teams were disabled for the controlled comparison. Retention policies affected some promises/check costs, but project totals tied. Record limits were equal while serialized bytes differed.

These results support mechanism-specific observations, not general cognitive superiority. They do not prove V3 and V2 are equivalent in all environments. They also do not establish that the additional plan lifecycle is useful to the selected policy.

The temporal study preserves projections with exact/adaptive execution but shows no established adaptive speed advantage. The coarse baseline sometimes changed cognitive histories/actions without changing terminal aggregates. That motivates evaluating more than final balances; it does not by itself establish a novel abstraction algorithm. [K4]

The 90/120-day lives establish persistence and reproducible consequences. They must not be pooled with the one-day cognition cases as multi-month intelligence evidence.

## 3. First gate: determine why the benchmark ties

Before implementing a new method, build a diagnostic report over a small development-only subset.

### 3.1 Trace actual information use

For each consequential decision, record:

- The admitted observation IDs and their content hashes.
- Current private retained records, working state, belief revisions and pending plan.
- Evidence supplied to the action controller.
- Available actions and their preconditions.
- Selected action, validated execution and actual receipt.
- Whether a stored plan changed the selected action or merely described it afterward.

Do not use private model chain-of-thought as the scientific artifact. Record explicit structured inputs, proposals, cited evidence, plan state and execution receipts.

### 3.2 Necessity and headroom controls

Run these diagnostic conditions with the same controller wherever meaningful:

**Current-observation-only:** no access to prior experience beyond the explicitly permitted current state and common institutional registers.

**Current V3:** actual shipped state and retention behavior.

**Admissible-history reference:** a generous reference containing all evidence that this actor legitimately observed. It must not contain unobserved canonical truth. Label the larger memory budget rather than treating it as a fair deployable competitor.

**World-state oracle:** optional evaluator upper bound, explicitly separate from admissible history. Never use it as an ordinary agent baseline.

Also test removal of a genuinely relevant admitted record, insertion of an irrelevant distractor, and a change to an earlier commitment while holding the present observation constant.

If current-observation-only and admissible-history behavior tie everywhere, the task has no demonstrated memory headroom for that controller. Investigate the controller, action space and task before adding a sophisticated memory architecture.

Do not engineer every test to favor the candidate. Include cases where recency is sufficient, memory is irrelevant, a direct observation should defeat an old plan, and the correct response is uncertainty because no actor could know a hidden change.

### 3.3 Plans must affect execution

A “plan” containing only the already chosen next action cannot prove long-horizon planning. Require at least one supported task with a prerequisite, a deferred step, an interruption and a later revision opportunity. Inspect whether persistent state is actually read to resume or cancel that plan.

If the common controller cannot handle this task, improve the common controller for every memory arm and freeze that improvement as the new baseline. Do not compare a better planner plus better memory against an old planner and attribute the gain to memory alone.

## 4. Task design

Use the existing two domains; do not build a third engine for the benchmark.

### Family A — Interrupted obligation

A legitimate commitment is accepted or assigned under controlled initial conditions. The actor completes a prerequisite, experiences unrelated activity, then resumes after a session boundary. A deadline or permitted quantity changes through an actually received message. Completion requires the revised obligation, not the most recently mentioned distractor.

### Family B — Evidence revision and correlated reports

A dated source supports an initial plan. Other actors relay the same originating report. An independent correction may later arrive. The actor must distinguish source repetition from independent support and determine whether the correction changes a concrete action. Include both true and false reports, stale-but-once-true reports, and unjustified correction attempts.

### Family C — Conflicting commitments and replanning

Two legitimate goals compete for a finite resource or time. An interruption hides the immediate salience of an earlier obligation, not its existence. The actor must resume, obtain permitted evidence if needed, and choose or revise a feasible plan. Include a repair route after a failure and count its real costs.

### Negative controls

- A hardware change is genuinely hidden until a later report. An agent cannot be penalized for failing to know unobserved truth.
- A task is solvable from the current public observation alone.
- A correctly remembered old belief must be discarded after better evidence.
- An unsupported source ID or another agent's private episode is offered to the adapter and must be rejected.
- A forgotten record remains in the canonical archive but cannot be silently reloaded into bounded actor memory.

### Construction rules

Each family should contain multiple decision opportunities across at least three meaningful sessions or interruptions. Advancing the calendar without new decisions does not create a long-horizon cognitive challenge.

Separate a **fixed-observation evaluation** of representation/retrieval/revision from a **closed-loop rollout** where decisions affect later observations and resources. In the closed-loop case, pair exogenous seeds/schedules, but do not pretend actors acquire identical endogenous evidence after choosing different inspections or communications.

Holdout must include structural task variation, not only new random seeds or renamed characters. Use an independently authored variant when possible. A reviewer should not optimize its cases for the proposed method.

## 5. Candidate change: improve the existing mind, do not create a new framework

A tractable candidate is a small change to the existing PersistentMind:

**Retain and invalidate evidence according to active commitments and plan dependencies, while recording the difference between a dated fact, a current belief and an inferred social judgment.**

Implement only what diagnostics show is missing:

- Pending goal/plan references to legitimately available supporting evidence.
- Revision triggers when a relevant constraint or source changes.
- Retention priorities for unresolved obligations and costly-to-reacquire evidence.
- Explicit supersession or invalidation of outdated support.
- Replanning when a previously valid step becomes infeasible.
- Bounded, disclosed consolidation that does not manufacture independent observations.

This resembles established goal/state-aware memory ideas. Novelty is not presumed. The value must come from a controlled finding or a clearer failure analysis.

Do not pin all useful history forever. Charge the pinned support, indexes, summaries, goals and plan register to the budget. A compact record is not free memory just because it lives outside the “memory” list.

## 6. Baselines and budget accounting

Start with the strongest executable set, not a large table of unimplemented systems:

| Arm | Purpose |
|---|---|
| Current V3 with the frozen common controller | Genuine shipped baseline |
| Recency/FIFO plus lexical BM25 retrieval | Simple defensible baseline |
| Pinned modern dense retrieval, if actually provisioned | Semantic-retrieval comparator; never hashed pseudo-embedding |
| Candidate retention/revision patch | Proposed mechanism |
| Candidate minus dependency protection | Ablation of active-obligation support |
| Candidate minus belief invalidation | Ablation of revision |

Run ablations after the main comparison has a reason to exist. Hindsight or another established framework can be an external integration baseline only when its actual implementation, version, configuration, licenses and computational budget are available. A literature citation or a stub adapter is not a reproduced baseline.

### Count all state

Report raw retained bytes, serialized working-state bytes, text/token context, vector/index footprint, plan/goal registers, persistent summaries, retrieval latency, initialization cost, inference/embedding calls and total runtime. Include any model-written memory and setup work.

Use at least two declared regimes if exact matching is impossible:

1. A fixed accessible-byte/context-budget comparison.
2. An outcome-versus-total-cost frontier.

Same number of records does not imply same information or computation. Institutional registers such as one's own balances or enforceable obligations may persist separately, but all arms must receive the same explicitly defined access. Do not erase real institutional truth merely to make memory failures more common.

The canonical archive is evaluator storage, not a free retrieval tier. Provenance identifiers must not become an indirect unrestricted archive lookup.

## 7. Outcomes and attribution

### Primary endpoint

Choose and freeze one meaningful endpoint after development diagnostics, for example **completion of the predeclared obligation chain with actual validated deliveries/actions under the assigned resource budget**.

Fix the target tasks independently of the agent's willingness to accept obligations. An always-abstain agent must not win by accepting nothing. Report opportunity counts and changing eligibility explicitly when earlier actions alter future choices.

### Required secondary outcomes

- Executed quantities, failed/missed obligations and unrecovered resources.
- Inspection and repair costs.
- Stale-belief actions after a legitimate correction.
- Incorrect source-independence assumptions.
- Unauthorized-information use.
- Plan resumption, revision and invalidation rates.
- Invalid action proposals and validator failures.
- Decision latency and total memory/inference cost.
- Per-family outcome differences; no hidden aggregate that masks a regression.

Keep **objective world outcome**, **decision quality given available information**, and **memory failure** separate. An unlucky but justified decision is not necessarily a cognition error. A lucky outcome does not make unsupported knowledge use acceptable.

Use a failure taxonomy: unavailable evidence; failed encoding; eviction; retrieval miss; stale revision; plan-selection failure; invalid execution; evaluator mistake. Investigate a small number of traces deeply rather than counting all errors as hallucinations.

## 8. Development, freeze and test

A feasible sequence is:

1. Small development set, roughly 8–12 seeds per family, for instrumentation and diagnosis.
2. Freeze family generators, parameter ranges, controller, metrics, budget definitions and candidate implementation.
3. Register the source hash, hypotheses, primary comparison, exclusion rules and output directory.
4. Execute fresh test seeds, targeting about 30 per family if computationally appropriate.
5. Preserve raw receipts, admitted streams, checkpoints, results and failures outside temporary worktrees.
6. Run an arithmetic/replay check from frozen code and label whether it is reproduction or an independent implementation.

These counts are design defaults, not a power guarantee. Choose sufficient precision for the decision being made. Small numbers of shared templates limit generalization even with many seeds.

Pair comparisons on exogenous world seed. Report per-family paired differences and uncertainty; describe how any aggregate weights families. Do not treat agent decisions within one world as independent samples. Resampling templates only makes sense with enough independently varied templates; otherwise be explicit about a conditional analysis of the chosen families.

Choose the primary endpoint before test results. Report all prespecified comparisons and label post-hoc discoveries exploratory. Do not retune on the heldout set and continue calling it heldout. Preserve negative results and operational failures.

## 9. Optional live-model stage

The current no-live-call state is a limitation on claims about language-model intelligence, not a reason to fake a model run.

When an authorized provider or local endpoint and explicit budget are available, run a small real-model stage using the same frozen tasks and the same model, decoding parameters, allowed actions and evidence budget across arms. Preserve model identifiers and outputs. Model sampling is not guaranteed reproducible merely because a seed field is set; use repeated calls where justified and distinguish replay of saved outputs from resampling the model.

Start with one foreground agent and one complete observe → remember → interpret → propose → validate → execute → remember loop. Do not invoke a model for every background tick.

Track all inference, embeddings, retries and judge calls against the cap. If the provider is unavailable, the run is **unexecuted**, not failed intelligence and not a synthetic success. Schema tests establish transport/contract behavior only. [A1]

For dialogue evaluation, separate valid action arguments, evidence-backed consequential claims, voice/style consistency, latency and refusal/clarification quality. A response can be fluent and wrong. Automatic citation checking cannot prove every sentence follows from the cited evidence. Audit an independently authored sample and report uncertainty.

## 10. Time and experience research: keep the important distinction

The recovered Kalends vision asks when an interval can be compressed without losing something worth living. The existing CPU scheduler tests do not answer that human question.

Keep four quantities separate: simulated calendar duration; computation; participant exposure time; and subjective duration/experience.

### Technical pacing instrument

For participant-visible scripted opportunities, log:

- When the relevant information becomes legitimately available.
- The interval during which each consequential intervention remains feasible.
- Whether the presentation offers a chance to intervene.
- Which commitment/relationship/state effects depend on that opportunity.
- Whether a stop/notification leaks a hidden fact.

Compare exact chronological presentation, terminal-summary-only presentation and protected-opportunity presentation over the same underlying history where applicable. This tests presentation coverage and controls, not human preference or general causal equivalence.

A final state may match while an opportunity to change it has disappeared. The pacing system should therefore preserve more than terminal cash or event count. Some ordinary intervals may matter for anticipation, familiarity or effort even without a large state delta; those require human evaluation, not a programmer's salience score.

### Human pacing pilot, later

After basic usability works, prepare a voluntary, ethically reviewed study with an appropriate partner where needed. Compare meaningful chapter boundaries and retained choice windows against a credible alternative, with matched exposure and comparable content. Measure agency, causal understanding, remembered interpersonal episodes and preference separately. Delayed learning/transfer requires its own design.

Flores et al.'s segmentation experiments motivate examining boundaries, but do not validate this intervention or imply subjective-time expansion. [H2] Reuse the existing K3 human-study work rather than announcing a new educational claim.

Do not recruit participants or claim results as part of autonomous coding. No sleep, invasive neurotechnology or dangerous experience experiments are in scope.

## 11. An honest novelty statement

Potentially defensible direction:

> A controlled study of how private, bounded evidence and plan dependencies survive interruptions and revisions in persistent worlds, with authoritative execution receipts and explicit visibility boundaries.

That is a research question and an evaluation contract, not a proven novel method. Compare its exact mechanisms to R1–R6. The new StateMemBench preprint makes current-state tracking an especially close overlap; CounterMem makes verified alternative-action memory a close overlap. Distinctive environments alone do not establish scientific contribution.

Acceptable outcomes include a useful negative result, a sharper diagnostic taxonomy, a rigorously characterized efficiency tradeoff, or a small generalizable mechanism improvement. Do not attach publication claims to more code or more simulated days.

## 12. Research deliverables and stop rules

Deliver one concise research report, a frozen protocol/configuration, source fingerprints, raw runs, an executable reproduction command, per-family plots and a short failure-case appendix. Report actual live-model status. Mark methods read in the literature separately from systems implemented.

**Stop adding cognitive features** when no decision depends on the proposed state. Repair the task/controller or report redundancy.

**Stop speedup claims** when all consequential tasks remain exact and measured cost does not improve. Preserve that correctness work as infrastructure.

**Stop generality claims** when changes require domain-specific privileged annotations unavailable to baseline systems.

**Stop human-benefit claims** without human evidence.

A release can pass the product gate and fail the research-superiority gate, or vice versa. Record them separately. Their only legitimate shared claim is what the implemented system and measurements actually support.
