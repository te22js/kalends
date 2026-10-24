# Independent continuity task design

Status: independently authored tasks and scoring frozen. Exact artifact digests are recorded in `blind_manifest.json`. No candidate comparison has been run or inspected by this author.

## Scope and independence

This document defines task requirements from first principles. It must not prescribe the content, shape, selection, retention, or retrieval of a target agent's memories. Task success concerns what the agent actually completes, the validity of its decisions when evidence changes, and the recovery of unfinished work.

The author has not inspected a target memory implementation, agent or policy code, Git history, previous experiments or outcomes, research reports, `kalends/next_phase/`, `kalends/minds*`, or previous `results/` directories. The sole pre-existing repository file read was `/Users/tanmaygoswami/Claude_backup/Projects/kalends/docs/continuity_release/TASK_CONTRACT.md`. Other inputs were inherited instructions/environment context and root coordination messages: the independent-design assignment; notice of the public contract and its bounds; clarification of relevant recovery inspections and deadline handling; notice that the candidate configuration had frozen; and clarification that scripted outcome values stay private while unrelated obligations can proceed during recovery. None supplied target behavior or results. The author subsequently read only its own two JSON artifacts, this document, and the generated manifest for consistency checking and hashing.

All existing user saves and artifacts are outside this author's edit scope and were untouched. This author wrote this document, `specs/continuity_release/development.json`, `specs/continuity_release/heldout.json`, and the corresponding `docs/continuity_release/blind_manifest.json` freeze record.

## Evaluation requirements

1. Each principal task has a horizon longer than a two-round decision and contains dependencies spanning interruptions.
2. At least two obligations can remain live simultaneously. Some constraints are hard requirements; others are preferences, tentative information, or canceled commitments.
3. Revisions have observable provenance and temporal scope. A correction can invalidate an earlier belief; a retraction can invalidate the correction. No general rule equates the latest text with the most reliable source.
4. At least one attempted action is partial, fails, or has an uncertain acknowledgement. A statement of intent does not satisfy an obligation. Recovery must reconcile execution state before taking an action that could create a duplicate or destroy the only usable result.
5. Some needed evidence can be unavailable. Valid behavior may involve leaving a gated action pending or reporting an unresolved obligation rather than pretending it completed.
6. At least one hidden environment change is discoverable through a current observation. No mechanism can be credited for knowing that change before observation.
7. Success is scored from executed outcomes and explicit dependencies. Claimed completion without its effects earns no completion credit.
8. Explicit controls separate continuity from other competencies: a self-contained final request, a current authoritative source that supersedes history, and a hidden change that requires fresh observation regardless of persistence.
9. Counterexamples include stale instructions, canceled obligations, misleading old preferences, and historical facts unrelated to the current request. Retaining or applying more history is not intrinsically rewarded.
10. The final heldout scenarios and endpoint scoring are frozen before any agent comparisons. Development examples may establish syntax and ordinary task semantics, but their results must not be used to tailor heldout cases to a target mechanism.

## Structurally distinct task families

### Dependent handover and recovery

A replacement must be created and verified before an original is retired. The first copy attempt partially succeeds. An independent export remains due across interruptions. An unverified cancellation conflicts with the owner's instruction, and a later hidden destination change requires a fresh observation. The agent must reconcile the partial copy, deliver the export, and retire the original only after a usable replacement is verified. Endpoint checks cover both deliverables, dependency order, preservation of the original until safe retirement, and duplicate effects.

### Version-gated publication

A public artifact depends on approval of a specific version and completion of requested edits. A correction is later retracted; a forwarded claim is not approval. A concurrent private deliverable is still owed. A publication attempt can fail after staging. The terminal state must show the intended approved version publicly available and the separate private deliverable completed, while an unapproved revision remains unpublished. This tests version binding and gates, rather than merely remembering an approval word.

### Claim and order reconciliation

Several line items have distinct outcomes: one succeeds, another fails, and a third is later canceled. A partial response must not be treated as all-or-nothing completion. A receipt or status source can supersede an earlier message. Recovery should complete only outstanding valid line items and should not repeat successful side effects or revive canceled work. The score follows actual item states and exact final obligations.

### Staged access transition

Permissions for a successor depend on a verification step; retirement of predecessor access depends on a separate handover condition. A grant can partly fail. A low-trust request can suggest a conflicting shortcut, while an owner later narrows the intended scope. An unrelated obligation must survive the interruption. The task rewards the correctly scoped final access state and preservation of the dependency sequence.

### Incident triage under source loss

The agent must resolve an operational issue using source-specific observations while retaining a follow-up obligation. Early evidence is provisional. An apparently authoritative observation is explicitly retracted, and a primary source later becomes unavailable. A fresh secondary observation can support only part of the conclusion. The desired outcome distinguishes a justified repair from an unresolved gated action and avoids fabricated certainty when evidence is unavailable.

### Reservation and dispatch with reversible preparation

A user needs an executed booking or dispatch plus a secondary commitment. Preparation can succeed before final execution fails. A preference changes, then the change is withdrawn. A current capacity or destination observation can differ from previously stated facts. The agent must verify current feasibility, complete the currently valid request, and unwind obsolete preparation without canceling successful current work.

### No-history and misleading-history controls

One control restates all actionable requirements at the final decision. Another supplies an authoritative current status that makes historical preferences inapplicable. A third changes private environment state after the previous turn, so fresh observation is necessary. A final control contains realistic but irrelevant prior obligations for a different request. These cases are not expected to reward continuity; they bound claims that a persistence mechanism generally improves task success.

## Frozen inventory

There are six development cases and eight heldout cases. Each case spans 20,160 virtual minutes (14 days), uses 11 decision windows and checkpoints at 2,880, 8,640, and 14,400 minutes, and has at most four goals and nine actions. All ordinary actions and inspections are bounded by a public work-window gate that closes immediately after minute 18,720. Decisions continue through the final endpoint so an incomplete task cannot obtain late completion credit.

The development cases cover all six principal workflow families described above. The heldout set has five principal cases covering dependent handover, version-gated publication, item reconciliation, staged access transition, and source-limited triage; its three controls cover fully restated current instructions, superseded authentic history, and a hidden current-state change. The JSON family fields identify this partition. Noise seeds vary admitted distractions within authored bounds and do not create new independent task designs.

Both item-reconciliation cases contain an uncertain successful side effect, a separate operational failure, an authentic cancellation, a distinct export obligation, and exact duplicate-effect checks. Handover tasks bind destructive retirement to independently completed dependencies. Version tasks bind approval to specific editions and contain an explicit retraction of a provisional revision. These are workflow structures authored from the contract, rather than substitutions into a two-round allocation template.

## Frozen scoring rubric

The primary endpoint for each case is the conjunction of every assertion in that case's JSON `assertions` array, evaluated on the actual executed ledger state and receipts. Each assertion has fixed weight 1; the complete suite contains 133 assertions. No prose claim by an agent counts as an executed completion. All goals' completion predicates refer to public institutional workflow facts, while the evaluator additionally checks exact outcomes and ordering.

- Report case-level all-assertions-pass success first. Report the five principal heldouts and three controls separately; do not pool controls into an undifferentiated continuity-benefit result.
- Report each assertion's result and the unweighted assertion-pass fraction per case as secondary diagnostics. If an aggregate is needed, use an unweighted mean over cases within the principal/control partition; do not let the number of assertions change case weight.
- Report completion of every goal, precondition rejections, scripted operational failures/partial/unknown outcomes, action receipts, duplicate-effect counters, resource spend, and inspection costs. These diagnostics do not replace the primary endpoint.
- `never` assertions prohibit every attempt of the named action, including a rejected attempt. Fixed `rejections_max: 0` assertions exclude deliberately scripted operational failures. The hidden-change control therefore requires fresh evidence by an explicit age bound before acting; it does not punish an agent for failing to guess an undisclosed replacement value.
- Required operational receipts and counters are exact where a repeated side effect would be invalid. A partial or unknown acknowledgement is reconciled through a declared inspection of a contract-relevant key. Recovery does not earn credit merely for saying that a retry is needed.
- Every case requires positive completion facts or successful receipts. In source-limited triage, the scored endpoint is an executed pending disposition and a delivered report explicitly identifying the unverified cause. Waiting indefinitely or asserting an unsupported repair fails.
- Every assertion and its weight is frozen in the JSON bytes. No post-comparison exclusions, reweighting, threshold changes, or new success conditions are authorized by this design.

The following principles informed those fixed assertions:

- Each task names concrete terminal outcomes, unmet obligations, forbidden or premature effects, and the evidence or ordering conditions on gated effects.
- Completion and reliability are reported separately when possible. A task that finishes by violating a required gate must not be classified as fully successful.
- Every outcome used for scoring must be representable by the interface's executed state or action trace. Prose assertions alone are insufficient.
- Partial credit, if used, is determined before comparisons and tied to independently valuable obligations. Failure and recovery checks are not reweighted after results are seen.
- Observation-dependent cases do not reward clairvoyance. Scoring permits a justified pending result where the contract makes the necessary source inaccessible.
- Control results are reported alongside principal cases. Hidden-state cases cannot by themselves establish a persistence benefit.

## Interface adaptations and limits

- Deadlines are represented by public execution gates as well as the declared goal deadlines, because the assertion vocabulary has no timestamp assertion. All actions are closed after the shared deadline, including verification and reporting actions.
- Freshness bounds force current observation in hidden-change controls. The action contract does not grant the agent private knowledge of a hidden replacement value, and assertions never require prior knowledge of an unobserved change.
- Historical instruction records and execution-status endpoints are separate in a subset of cases. Instructions can become unavailable after being legally observed while runtime inspection remains available to reconcile a partial or uncertain action. Thus inspection is a real recovery operation rather than a universal historical archive.
- The unavailable-diagnosis cases cannot establish a new cause from unavailable evidence. Their correct terminal outcome preserves the unresolved obligation explicitly. Recalling a withdrawn diagnosis cannot justify repair.
- Trust is represented by the contract's admitted/rejected provenance flag and source labels. These cases test behavior with admitted evidence, explicit revocation, and unavailable sources; they do not independently test a language model's social credibility classification.
- The common controller supplies goal resumption, prerequisite filtering, and mandatory post-uncertainty inspection identically for all arms. Results concern usable evidence across those workflows; they do not alone demonstrate unrestricted long-horizon planning or autonomous natural-language task management.
- The controller sees declared possible written key names for recovery relevance, but not the scripted attempts, statuses, or hidden outcome values. An uncertain mutation does not block independent obligations; its own retry remains gated on a relevant inspection.

## Freeze and attestation

Validation was limited to independently authored JSON syntax and contract consistency: case counts, field bounds, string proposition values, chronological windows/timeline, bounded noise, goal/action references, public completion and prerequisite keys, recognized assertion forms, fixed weights, inspection gates, and relevant inspection-key intersections for scripted operational outcomes. The author manually reasoned through the workflows but executed no candidate agent, memory arm, controller, or comparative evaluation.

The pre-freeze consistency pass also checked that ordinary operations and inspections are bounded by explicit public execution gates and that unknown private effects are not directly used as public goal completion. The two JSONs, this rubric, and the public contract are SHA-256 hashed in the manifest. The manifest records the exact read set and author independence statement. Heldout bytes and scoring must remain unchanged after comparisons begin; a necessary correction requires a newly identified release rather than an in-place scoring revision.
