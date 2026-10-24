# Execute the next Kalends release: human experience + discriminating research

You are the implementation agent working in the actual Kalends repository. This is a substantial autonomous execution assignment, not a request for another roadmap or another speculative architecture.

## Read these inputs first

Read these attached specifications in order:

1. `00_DECISIONS_AND_SOURCES.md`
2. `01_PRODUCT_AND_WEBSITE_SPEC.md`
3. `02_RESEARCH_PROTOCOL.md`
4. This execution contract.

Then read the current repository's Experience OS handoff, architecture, company thesis and results. The reported branch is `codex/experience-os`, through `21127f0`. Inspect the actual state rather than assuming that commit is still the tip. The reported launcher is `./scripts/run_experience_os.sh`, serving the local experience on port 8800. The existing PlayCanvas frontend and saved-life runtime must remain usable.

The planning pack was prepared from supplied reports and retrieved context, not direct inspection of the current UI. You must perform that inspection. Treat the repository and actual browser behavior as the implementation source of truth; report discrepancies instead of silently inventing missing capabilities.

## Mission

Build one human-facing product journey and one scientifically useful evaluation, using the existing runtime.

**Company/product track:** people should choose a world, understand their role, meet particular characters, make supported choices, develop an intelligible history and return to real consequences. Keep meaningful ordinary life, not just urgent tasks and reward notifications.

**Research track:** determine which evidence must survive interruptions for a plan or commitment to be carried out correctly. First prove the task is sensitive to memory. Then test one minimal mechanism against real baselines under declared budgets.

Do not conflate them. A product can improve while a candidate method ties; a method can improve while users remain uninterested. Report each honestly.

## Non-negotiable scope

- Keep Kalends as the project name. Do not create another grandly named generation or separate framework.
- Retain PlayCanvas, the two existing domains, the authoritative event/runtime infrastructure and existing provider transport.
- Do not add a new city, population-scale project, multiplayer, marketplace, VR/neural work, unlimited world compiler or new model adapter framework.
- Preserve user saves, previous studies, frozen source revisions and compatibility routes.
- No fabricated world histories, results, screenshots, customer demand or human participants.
- No public deployment, repository push, external outreach, account creation or purchases are authorized.
- External inference defaults to zero. Use only an explicitly authorized credential source and numeric spending cap, or an actually available approved local endpoint. Do not search unrelated files for secrets.
- Do not wait for routine design decisions. Make reversible choices and document them. Stop the specific unsafe/destructive action rather than the whole task when approval would be required.
- Use the available session productively; do not idle to satisfy an arbitrary elapsed-time target or promise unsupported background continuation. Checkpoint work so it can be resumed.

## Stage 0 — Protect, inspect and save the execution plan

1. Inspect Git status, current branch, uncommitted work and the active server/writer state. Create a safe development branch or isolated worktree without resetting the owner's files.
2. Record source revision and hashes of the user's original saves. Use a separate QA directory and port for browser actions.
3. Run the relevant baseline tests and launch the current Experience OS. Do not infer that the reported 947/110 counts still apply.
4. Walk through both domains as a new participant and as a returning participant. Capture actual desktop and narrow-layout screenshots. Attempt invalid, cancelled and stale actions as well as the success path.
5. Build a short defect list with reproduction, expected behavior, actual behavior and severity. Include actual friction around mode choice, reloads, unclear capacity, weak conversation and lack of a return story.
6. Save `docs/next_phase/EXECUTION_PLAN.md` with decisions, task order, file ownership, acceptance gates and unresolved constraints. Keep it brief. This is an execution record, not a transcript of hidden reasoning.
7. Have a separate review pass challenge the plan: is it another skin over the same awkward workflow? Is the research task structurally capable of distinguishing methods? Revise the plan once based on concrete defects, then implement.

Do not spend the entire session researching. The supplied sources are a starting set, and version-specific implementation questions should be checked against current primary documentation.

## Stage 1 — Fix continuity of the web experience

Implement the life-scoped shell before marketing polish:

- Stable selected life and revision.
- Preserved scene/camera, conversation recipient, unsent text, open history and focus during ordinary actions.
- No iframe remount on ordinary accepted actions unless technically unavoidable and explicitly documented.
- Late-response cancellation/invalidation on life, scene or recipient changes.
- Resource state from committed receipts only; immediate pending feedback without optimistic financial mutations.
- Clear saving, saved, failed, incompatible and writer-conflict states.
- Original lives preserved; examples copied before interaction; no accidental template overwrite.
- Private participant projections remain private after refresh, previews, errors and alternative runs.

Use the existing routes and compatibility bridge. Introduce the smallest state controller needed. Do not build a new network architecture when a tested refresh/reconciliation layer will suffice.

**Gate 1:** a user can enter, interact, inspect history, return to the scene and resume after restart without losing identity or crossing a visibility boundary.

## Stage 2 — Implement the website as specified

Implement the actual homepage, two-world catalog, experience detail/start view, saved-world home and research page. Follow the copy, hierarchy, palette direction and state behavior in the product specification.

Use actual captures and supported content. Keep the page lightweight until the user enters 3D. Do not add a login wall or a fake waitlist. Do not build unsupported catalog entries.

The main homepage idea is **Enter a world. Leave a history.** The technical OS and LIVE/LEARN/LAB controls are not the visitor's first task. Returning visitors should be able to continue directly.

Review screenshots at representative desktop and narrow layouts. Fix hierarchy, overlap, contrast, cropping, empty states and focus issues. A static screenshot is not sufficient to pass the next gate.

**Gate 2:** every primary action works, the actual capability is clear, and the visitor can reach a valid experience without understanding the engine.

## Stage 3 — Make one life feel connected

Improve the existing Pompeii content and the Observatory participant interface rather than adding more domains.

1. Create a readable personal-history projection from authorized evidence: chapters, people, commitments, consequences, unresolved matters and sources.
2. Author a restrained opening/ordinary-interaction/choice/return sequence over existing mechanics. Outcomes depend on receipts and accessible memory, not a predetermined script.
3. Humanize Observatory's team presentation through fictional display names, roles, concise conversation and concrete evidence. Preserve actual fixed IDs, execution order, deadlines and capacity semantics.
4. Clearly distinguish requests, promises, allocations and executed deliveries.
5. Improve conversations with supported contextual choices and optional natural input. Remove unnecessary modal friction only after classifying the operation and preserving the backend review boundary.
6. Add the participant-friendly time controls and warnings for known commitments. No fake offline progression, silent autopilot or hidden-event pacing leak.
7. Implement return summaries and reflection using what the participant knows. Show the original decision's evidence rather than hindsight when explaining it.
8. Make the existing omission retry legible and explicitly disclose the fixed later-command continuation and skipped infeasible commands.

Do not treat mundane time as an automatic deletion target. Preserve selected routines and moments that establish familiarity or anticipation. Do not use guilt, attachment pressure or streaks to manufacture a reason to return.

**Gate 3:** a complete first-session/return sequence contains one understandable person-specific consequence, one independent world development, and a genuine supported alternative. The original life remains unchanged by the alternative.

## Stage 4 — Research diagnostic before new cognition

Run the necessity/headroom audit from the research protocol. Use a small development-only subset.

Instrument actual reads of retained evidence, beliefs, pending plans, available actions and receipts. Compare current-observation-only, current V3 and an admissible-history reference. Keep the evaluator's private truth separate.

Determine whether plans influence action selection or just describe a decision after the fact. Use minimal-pair cases and negative controls. If the task or controller has no headroom, fix or replace that part before building a candidate method.

Save the diagnosis with exact trace examples. Do not rerun the old one-day sweep at a larger scale and call it a new intelligence experiment.

**Gate 4:** at least one legitimate delayed multi-step case is sensitive to prior evidence and at least one control shows that more memory is unnecessary or potentially misleading. The gate is a validity check, not permission to tune all tests to the candidate.

## Stage 5 — One cognitive change, one controlled comparison

Patch the existing mind only where the diagnosis supports it: goal-dependent evidence retention, plan-support invalidation and resumption after a correction or interruption are the candidate direction.

Keep the common action controller fixed across memory arms. If a better common planner is necessary, change it for all arms and measure memory separately. Count all cognitive state, not just the episode list.

Implement real executable baseline arms. A modern embedding arm requires a provisioned, pinned encoder and measured index/storage cost. An unavailable external framework is an unexecuted comparison, not a fake reproduction.

Use development/test separation, fresh structural variants, paired exogenous seeds, a frozen primary endpoint, all prespecified results and raw artifacts in durable directories. Avoid concurrent browser performance measurements while running CPU-heavy studies.

If the candidate ties or loses, preserve it as a finding and ship the better-performing supported default. Do not force a new mind version into production for branding.

**Gate 5:** a reviewer can reproduce the executed comparison, inspect failed cases and distinguish a memory effect from planner changes, additional information or extra budget.

## Stage 6 — Grounded expression, not another unused AI interface

Reuse the existing provider contracts. Add only the minimum needed to express supported character beliefs and intentions naturally.

When a real approved endpoint is available, demonstrate one complete foreground loop: permitted observations → retained context → model interpretation/expression → validated action proposal → confirmed receipt → later grounded recall.

Separate consequential facts from phrasing. Structured JSON is not semantic truth. Validate actions and citations, audit factual clauses, handle uncertainty, and preserve a deterministic fallback. Record model/version, latency, costs and rejection reasons.

When no authorized endpoint exists, leave spending at zero, exercise the existing offline path and mark live-model quality untested. Do not pretend a polished template is a newly intelligent NPC. Do not waste the session recreating the transport.

## Stage 7 — Human-use preparation and final integration

Instrument opt-in local events using build/session/life IDs and active-time distinctions. Do not collect raw free-text conversations by default. Prepare the existing formative usability protocol and a narrow authoring/interview task; do not recruit or contact people.

Implement supported Studio forms only after the participant path and research diagnostic are complete. Otherwise leave a clear experimental authoring boundary rather than shipping a nonfunctional general-world generator.

Run actual browser journeys for new/resumed lives, different routes, declined actions, invalid/stale offers, interruption, cross-life tabs, saving failure, restart, hidden information and research exposure.

Measure sustained frame pacing and web responsiveness separately. Capture the entire interface, not just the 3D canvas, when recording is supported. Preserve browser/hardware conditions and negative measurements.

## Work coordination

Use at most a small set of well-defined parallel roles if supported:

- Product implementer owns shell, presentation and content projections.
- Research implementer owns diagnostic harness, frozen experiments and the minimal mind patch.
- Reviewer performs read-only integration, privacy and empirical checks.

The lead owns shared interfaces and merges. Do not let multiple agents rewrite the same runtime files concurrently. Product snapshots must never expose extra research state because a subagent wanted easier debugging.

A useful substantial session leaves several tested milestones, not one giant unreviewable diff. Continue past planning and the first attractive screen. Do not stop while a high-priority fix can be completed safely with available resources.

## Deliverables

Keep the output compact and tied to real work:

- `KALENDS_NEXT_PHASE_HANDOFF.md`
- `docs/next_phase/EXECUTION_PLAN.md`
- `docs/next_phase/PRODUCT_QA.md`
- `docs/next_phase/RESEARCH_REPORT.md`
- `results/next_phase/` with frozen configs, raw data, source fingerprints and failures
- `demo/next_phase/` with actual captures and a complete walkthrough

The handoff must state:

1. Exact branch/commits, changed paths and launch command.
2. What a visitor can now do, demonstrated through a complete journey.
3. Reproduced defects fixed and important defects remaining.
4. What the human history/return experience actually knows and shows.
5. What the cognition diagnostic found and what the new experiment supports.
6. Whether live cognition was really executed, with exact spend and scope.
7. Performance measurements with their conditions and limits.
8. Save/replay/privacy compatibility and test results.
9. What was not completed and the next three evidence-driven tasks.

Do not make a long strategy memorandum the main deliverable. Do not treat more passing tests as proof of demand, or an accepted model response as proof of intelligence.

## Final release review

Ask three questions independently:

**Person:** Can an unfamiliar participant understand what is happening, act without fighting the interface and recognize a meaningful part of their own history?

**Researcher:** Does the controlled experiment actually distinguish the proposed mechanism from equal-information baselines, without hidden memory or evaluator privilege?

**Founder:** Is the next company decision based on observed use and a specific demand hypothesis, or only on increasingly impressive architecture language?

Fix the largest concrete failure from each review that is feasible. Save the result and report honestly.

**Begin with Stage 0 now. Preserve the world, make the experience coherent, and earn the scientific claims.**
