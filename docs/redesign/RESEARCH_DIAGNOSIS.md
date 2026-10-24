# Frozen exhibit-release failure: post-exposure diagnosis

24 October 2026. This is a development diagnosis of an already exposed workflow, not a new held-out evaluation, a tuned candidate, external replication, or live-model result. No source, task, budget, weights or primary result was changed. Model calls and spend: zero.

## Preserved result

The original experiment contains eight workflow structures, twenty noise seeds and five arms (800 executions). Candidate and V3 each pass 140/160 primary cases; their 160 paired primary outcomes tie. The workflow `h_exhibit_release` fails all twenty seeds in all five arms. No held-out advantage was demonstrated. This does not establish general equivalence, and it does not replace the older narrow authored-task result.

The original frozen receipts show the same within-arm action trajectory across all twenty seeds. Candidate and task-aware BM25 finish staging and store the private annex, but do not publish. V3, FIFO BM25 and latest-per-key finish staging but neither publish nor store the annex. Thus primary pass/fail ties conceal subgoal differences; those exposed secondary differences are diagnostic observations, not a retrospectively selected superiority endpoint.

## What was executed

`python3 results/redesign/debug/diagnose_exhibit.py`

The script reads all 100 original exhibit-release records, then performs one unchanged instrumented replay at seed 1000 for each of the five arms. Instrumentation copies memory metadata for inspection and preserves every return value. Each replay's complete canonical evaluator result matches its frozen record exactly (the batch-added `replay_equal` field is excluded from that comparison). There is no treatment intervention or parameter search.

A separate, explicitly analyst-specified feasibility witness submits `stage_three`, `finish_three`, `publish_three`, then `store_private_annex` to the unchanged authoritative validator, two operations at minute 10080 and two at 11520. All original assertions pass. This witness is not a bounded-memory arm: it establishes that the action chain, deadline, credit budget and evaluator permit completion. The required approvals were genuinely observed at minute 0; the unsigned later claim was rejected and did not alter truth. An impossible objective or missing initial evidence is therefore not the explanation for this seed.

All 822 protected files—including the full frozen results directory, held-out task, research freeze dependencies and candidate manifest—have matching before/after SHA-256 hashes. The source/task hashes also match the historical freeze. Full records and reproducibility hashes are in `results/redesign/debug/exhibit_diagnosis.json`. A first diagnostic assertion compared Python tuples against JSON arrays and failed; canonical JSON comparison corrected that diagnostic-only comparison. No experimental file was changed.

## Causal localization at seed 1000

| Arm | Direct observation from instrumentation | Scope of diagnosis |
| --- | --- | --- |
| Dependency retention | Both original edition-3 approvals survive until staging. Admission of `text_staged` at 10080 removes the last editor approval; admission of `images_staged` removes the last rights approval. At 11520 neither is retained, and `publish_three` reports both missing. | Record-capacity retention failure. The extra dependency score does not protect all downstream prerequisites when equally relevant recent observations, duplicate episode/semantic representations and revision records compete. This is not a byte-gate eviction: the saved run reports zero byte evictions. |
| V3 hybrid | Last editor approval disappears at 8640; last accepted rights approval disappears during staging at 10080. Rejected edition-4 testimony remains represented but is excluded from valid retrieval. | Retention failure under the existing shared record budget. No evidence that rejected testimony authorizes publication. |
| FIFO BM25 | Original approvals disappear as noise is admitted at 1585 and 1651. | Early retention failure; later retrieval cannot restore absent records. |
| Latest per key | Original approvals likewise disappear at 1585 and 1651. | Keeping a latest head per key does not protect distinct old keys from the global recency cap. |
| Task-aware BM25 | At 11520 both original approvals and the reinstated active state (event 89) remain retained. The decision retrieves events 19, 16, 17, 53: annex instruction, both approvals and the superseded revoked state. After annex storage it retrieves 16, 17, 53, 18, again omitting the reinstatement. | Retrieval ranking/context limitation rather than missing retained evidence at this point. The four-record context selects old lexical matches instead of the current temporal head, so the common planner correctly refuses unsupported publication. |

The signed archive becomes unavailable at 5760, before the release window. That is an explicit public task condition, not an unobserved hidden change. Once approval support is lost or omitted, `inspect_packet` only observes staging keys and cannot recover approvals. The controller eventually waits; it does not cheat by reading evaluator truth. The authoritative evaluator correctly records the missing publication. A secondary limitation is the fallback inspection of staging after it is already completed, prompted by outstanding recovery bookkeeping; it does not supply missing approval evidence.

The exact eviction timestamps and mechanism distinctions above were instrumented at one seed. The stored 100 records establish identical within-arm action trajectories and assertion patterns across the twenty seeds; they do not by themselves prove identical internal eviction timing across every seed.

## Consequence for the research page

Use: “The later eight-workflow study found no candidate advantage on the primary outcome. A post-exposure diagnosis localized the failed publication workflow to lost prerequisite records in several arms and stale context selection in task-aware BM25; the task is feasible through the unchanged validator.”

Do not call the diagnostic a new held-out win or claim a fix. A future development intervention could examine dependency coverage, duplicate representations and revision-aware retrieval. It would require a declared intervention, equal total memory/context accounting and new independently authored workflow structures for any confirmatory claim. This release changes none of those research mechanisms.
