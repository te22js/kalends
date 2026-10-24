# Frozen continuity comparison: results and limits

The frozen dependency-retention candidate shows **no primary completion advantage
over V3 hybrid**, its strongest baseline and direct ablation. Each completes
140/160 case-seed runs (87.5%): 80/100 principal runs and 60/60 controls. Their
paired primary outcomes are identical: 140 both pass, 20 both fail, zero wins and
zero losses. On `h_exhibit_release`, both fail every seed; the candidate spends
4 credits against V3's 3 because it additionally delivers the private annex.
This is a cost regression on the fixed primary endpoint, with a narrower
secondary completion benefit. It does not establish a research or production
advantage for the candidate.

The candidate remains a frozen research mechanism. No candidate, controller,
task, assertion, weight, budget or source was changed for this analysis. The first
final run, including all failures, remains at
[`frozen_heldout`](../../results/continuity_release/research/frozen_heldout/).
The machine-readable audit is
[`analysis.json`](../../results/continuity_release/research/analysis.json).

## What was evaluated

The [protocol](RESEARCH_PROTOCOL.md), [blind design](blind_design.md),
[task manifest](blind_manifest.json),
[candidate freeze](../../results/continuity_release/candidate_freeze.json) and
[final source freeze](../../results/continuity_release/research_freeze.json)
precede the final comparison. Task authorship was procedurally independent inside
this project: the author attests to reading the public contract without target
code, prior outcomes or Git history. This is not an external benchmark or a
security-enforced separation of the agents.

There are **eight independently authored heldout cases**, five principal and
three controls. Each spans 14 virtual days and 11 decision windows. Seeds
1000–1019 vary distraction timing/text within each authored structure. They make
160 case-seed pairs, each compared across five arms: 800 recorded arm runs, plus
800 uninterrupted replay counterparts. They do not make 800 independent task
worlds. All primary outcomes, assertion results, spend, inspection counts and
receipt sequences are constant across the 20 seeds for each case-arm pairing.
The limited generalization unit is the authored case; no population confidence
interval or significance claim is warranted from these noise repetitions.

The fixed primary endpoint requires every assertion to pass on executed state.
There are 76 authored heldout assertions. Secondary assertion fractions below
are unweighted across cases within each partition. Waiting, intended actions and
completed public goals do not replace the fixed endpoint.

All arms share native V3 belief revision/planning and the same public controller.
The candidate adds the existing 0.6 retention bonus for accepted records whose
keys match active goals' declared conditions; removing this override is V3
hybrid. Other arms are FIFO retention with BM25 retrieval, task-aware lexical
retention with BM25, and accepted latest-per-key revision heads. These three
also disable consolidation and use recency configuration. Their comparisons
therefore include representation/consolidation differences, not only one
retention-score difference. There is no dense/embedding or live-model arm.

## Paired case completions and costs

Each cell is **all-assertions-pass runs / 20; credits spent per run**. The spend
is invariant across the 20 seeds, so the listed value is both its mean and range.

| Partition and authored case | Candidate | V3 hybrid | FIFO + BM25 | Task lexical + BM25 | Latest per key |
| --- | ---: | ---: | ---: | ---: | ---: |
| Principal: `h_box_migration` | 20; 6 | 20; 6 | 0; 0 | 20; 6 | 0; 0 |
| Principal: `h_exhibit_release` | 0; 4 | 0; 3 | 0; 3 | 0; 4 | 0; 3 |
| Principal: `h_bundle_fulfilment` | 20; 7 | 20; 7 | 20; 8 | 20; 7 | 20; 8 |
| Principal: `h_workspace_handover` | 20; 6 | 20; 6 | 0; 8 | 0; 6 | 20; 7 |
| Principal: `h_projection_incident` | 20; 2 | 20; 2 | 0; 0 | 20; 2 | 0; 0 |
| Control: `h_current_brief` | 20; 3 | 20; 3 | 20; 3 | 20; 3 | 20; 3 |
| Control: `h_superseded_brief` | 20; 2 | 20; 2 | 20; 2 | 0; 0 | 20; 2 |
| Control: `h_unannounced_gate` | 20; 3 | 20; 3 | 20; 3 | 20; 3 | 20; 3 |

| Arm | Principal completion | Control completion | Principal mean assertion pass | Control mean assertion pass | Total credits / 160 runs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Candidate | 80/100 (4/5 authored cases) | 60/60 (3/3) | 95.56% | 100% | 660 |
| V3 hybrid | 80/100 (4/5) | 60/60 (3/3) | 93.33% | 100% | 640 |
| FIFO + BM25 | 20/100 (1/5) | 60/60 (3/3) | 58.38% | 100% | 540 |
| Task lexical + BM25 | 60/100 (3/5) | 40/60 (2/3) | 91.56% | 85.71% | 620 |
| Latest per key | 40/100 (2/5) | 60/60 (3/3) | 68.38% | 100% | 520 |

Against FIFO + BM25 the candidate has 60 candidate-only passes, 80 both pass and
20 both fail. Against task lexical + BM25 and latest per key it has 40
candidate-only passes, 100 both pass and 20 both fail. No baseline-only primary
passes occur. These weaker-baseline differences do not supersede the exact V3
tie. Lower spend by a baseline that never attempts an unfinished task is not a
completion-adjusted efficiency result.

The candidate's total spend exceeds V3 by 20 credits, entirely from the extra
annex operation in each exhibit run. Their other seven case costs are identical.

## Assertion and unfinished-work diagnostics

These per-case assertion pass counts are also invariant across seeds.

| Case | Candidate | V3 hybrid | FIFO + BM25 | Task lexical + BM25 | Latest per key |
| --- | ---: | ---: | ---: | ---: | ---: |
| `h_box_migration` | 13/13 | 13/13 | 4/13 | 13/13 | 4/13 |
| `h_exhibit_release` | 7/9 | 6/9 | 6/9 | 7/9 | 6/9 |
| `h_bundle_fulfilment` | 13/13 | 13/13 | 13/13 | 13/13 | 13/13 |
| `h_workspace_handover` | 10/10 | 10/10 | 5/10 | 8/10 | 10/10 |
| `h_projection_incident` | 9/9 | 9/9 | 4/9 | 9/9 | 4/9 |
| `h_current_brief` | 8/8 | 8/8 | 8/8 | 8/8 | 8/8 |
| `h_superseded_brief` | 7/7 | 7/7 | 7/7 | 4/7 | 7/7 |
| `h_unannounced_gate` | 7/7 | 7/7 | 7/7 | 7/7 | 7/7 |

Every failed assertion is listed below; each fails on all 20 seeds of its
case-arm pairing. All unlisted assertions pass.

- **Box migration, FIFO and latest:** `migration.finalized=yes`,
  `migration.verified_seal=seal_29`, `migration.copy_count=1`,
  `export.sent_to=registrar`, `original.present=no`; exactly one unknown
  `copy_box` receipt and one successful `confirm_box` receipt; successful
  `verify_seal` before `retire_box` and `export_registrar` before `retire_box`.
  Neither arm executes a receipt; copy, verify, export and retire goals remain
  unfinished.
- **Exhibit release, every arm:** `packet.public_version=edition_3` and successful
  `finish_three` before `publish_three`. V3, FIFO and latest additionally fail
  `annex.stored_at=owner_vault`. Publication remains unfinished everywhere;
  the annex also remains unfinished for those three arms.
- **Workspace handover, FIFO:** `workspace.final_scope=view`,
  `workspace.verified=yes`, `former_owner.active=no`; successful `verify_nuri`
  before `retire_former_owner` and `send_html_guide` before `retire_former_owner`.
  Grant, verify and retire goals remain unfinished; the guide completes. The arm
  spends six credits on six workspace inspections without completing the grant.
- **Workspace handover, task lexical:** `never grant_nuri_edit` and
  `rejections_max: 0`. It attempts the obsolete edit grant and receives a rejected
  precondition receipt before recovering to the correct final scope. All public
  goals complete, but that does not erase the prohibited attempt or its rejection.
- **Projection incident, FIFO and latest:**
  `incident.disposition=pending_diagnosis`, `report.cause_claim=unverified`,
  `report.sent_to=duty_owner`; exactly one successful `record_unresolved` and one
  successful `report_unresolved` receipt. Neither arm executes a receipt; both
  goals remain unfinished. Avoiding an unsupported repair alone is insufficient.
- **Superseded brief, task lexical:** `package.sent_destination=south`,
  `package.sent_wrap=paper`, `receipt.sent_to=current_owner`. It executes no
  receipt and leaves both package and receipt goals unfinished.

The machine-readable analysis preserves each original assertion object, its
20-seed pass/fail count, unfinished goals, and exact timed receipt sequence for
every case-arm pairing. In particular, all arms pass the bundle's exact
uncertain-success, failed-attempt, recovery, cancellation and duplicate-effect
checks; the candidate and V3 also pass the migration and handover order checks.

## Why every exhibit-release run fails

The raw traces give the same action/status sequence across seeds:

- Every arm executes `stage_three` with a **partial** receipt and then successful
  `finish_three` at minute 10080. Staging is completed, and edition 4 is never
  published.
- Candidate and task lexical additionally execute successful
  `store_private_annex` at minute 11520. The other arms do not retain usable
  annex-destination support.
- Every arm executes one successful `inspect_packet` at minute 11520. That
  inspection reads target/text/images staging, not either version-bound approval.
  No arm ever attempts `publish_three`.

The original editor and rights approvals were observed at minute 0. The owner
provisionally changes the target and suspends approval at minute 2880, then
restores edition 3 and the original approval state at minute 8640. The signed
approval archive goes offline at minute 5760; its inspection also requires an
open execution window, which does not start until minute 10080. It is therefore
unavailable throughout every opportunity to execute.

At the candidate's minute-11520 annex decision, the actual native planner rejects
`publish_three` for missing settled editor and rights approval support. The
retrieved context has the annex instruction and revoked/reinstated approval-state
records, but neither original approval binding. At minutes 14400 and 17280, its
mutation retrieval returns only the reinstated and revoked state records. V3
similarly retrieves the approval-state pair without the two bindings. Given the
native exact-key retrieval filter, this supports loss of the accepted approval
records from their usable retained pool, rather than a hidden archival lookup
that could restore them. FIFO and latest likewise lack the old binding support.
The traces do not snapshot every intermediate retained record, so the precise
pruning event is not separately measured.

Task lexical exhibits a different evidence failure. At its annex decision the
planner retrieves the editor/right bindings plus the **revoked** state, and
rejects publication for missing `approval_state=active`. Later mutation retrieval
returns the original active state (minute 0) and revoked state (minute 2880),
without the reinstatement at minute 8640. The more recent revoked record wins
within that retrieved set. Retaining old approvals alone is not enough when the
valid reinstatement is absent from usable context.

The common controller records the partial staging action as needing recovery,
then clears it after the staging inspection. It cannot obtain the missing
approvals: the only relevant signed-record inspection is publicly unavailable.
Its fallback inspection cycle replaces the first mutation decision in the final
trace detail; therefore a final `wait` row can have an empty rejection list even
though its earlier mutation retrieval lacked evidence. The recorded retrieval
contexts and earlier explicit publication rejection are the diagnostic evidence.

No byte eviction, context-byte truncation or budget-withheld decision occurs for
candidate or V3. Their failure persists after identical checkpoint/uninterrupted
replay. The native 16-record retention/representation limit and effective
retrieval are implicated; this is not evidence that the authored task itself was
impossible with the necessary approvals preserved. No repair, favorable rerun,
case exclusion or threshold adjustment was made after seeing this result.

## Execution, resource and replay checks

Counts below cover all 160 recorded runs per arm. Scripted failed, partial and
unknown outcomes are separate from rejected preconditions. Inspections cost one
credit each and are included in successful receipts and total spend.

| Arm | Succeeded receipts | Unknown | Partial | Scripted failed | Rejected | Inspections / credits |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Candidate | 560 | 40 | 40 | 20 | 0 | 100 |
| V3 hybrid | 540 | 40 | 40 | 20 | 0 | 100 |
| FIFO + BM25 | 460 | 20 | 40 | 20 | 0 | 200 |
| Task lexical + BM25 | 520 | 40 | 40 | 20 | 20 | 100 |
| Latest per key | 440 | 20 | 40 | 20 | 0 | 120 |

Each arm is configured for 16 total retained records, four retrieved context
records, 16,384 bytes of complete serialized accessible state, and 4,096 context
bytes. State includes controller, goals, bounded plans, references and actual
lexical query/index material. The lexical index reserves copied Experience
payloads, postings, lengths and document frequencies. This is a logical
serialized footprint; it does not measure Python RSS, execution speed, or equal
numbers of useful facts across representations.

| Arm | Max state bytes | Max context bytes | Max index bytes, included in state | Byte evictions, total | Retrieval calls, total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Candidate | 9,486 | 1,592 | 0 | 0 | 9,280 |
| V3 hybrid | 9,475 | 1,592 | 0 | 0 | 9,220 |
| FIFO + BM25 | 16,384 | 1,672 | 7,154 | 900 | 6,900 |
| Task lexical + BM25 | 16,383 | 1,682 | 7,532 | 780 | 6,400 |
| Latest per key | 9,889 | 1,631 | 0 | 0 | 6,460 |

Byte evictions are additional common-gate evictions; zero does not mean native
record-cap pruning never occurred. All arms report zero context-prefix drops
and zero withheld decisions. Auditing the raw retrieval diagnostics finds at
most four returned context records and no logged state/context budget breach.
Different retrieval call counts reflect different observation/execution paths
as well as the native observe/belief/planning calls; they are not a runtime
benchmark.

All **800 recorded checkpoint/replay comparisons match** on actual ledger,
remaining cash and goal outcomes. All 800 raw result projections match their
summary rows, and receipt costs/statuses agree with each raw result. Thirty
manifest comparisons across the candidate, blind task, final source and recorded
run manifests pass; the heldout digest also matches both frozen and run records.
The audit records input hashes and a digest of the unchanged compressed raw
corpus. The run records 142.108 seconds, **zero model calls and $0 inference
spend**. Analysis used only existing files and did not rerun the study.

## Information boundaries and scope of the result

`h_unannounced_gate` changes actual station availability from north to south at
minute 10000 without an observation or public-register update. The action
contract requires evidence at most 60 minutes old; the old north observation
cannot qualify at minute 10080. Every arm buys `inspect_station`, observes south,
reserves it and executes the token-bound job, with no rejection. This correctly
shows that persistence cannot supply the hidden change before observation. The
freshness rule and inspection fallback make this a shared observation control;
it is not evidence of a candidate-specific ability to discover surprises.

`h_projection_incident` withdraws the original diagnosis, explicitly observes
cause/evidence as unknown, and makes the diagnostic source unavailable before
the work window. Correct completion is an executed pending disposition and an
unverified-cause report, not an unsupported repair. Candidate, V3 and task lexical
complete that disposition; FIFO/latest do not. The fixture does not ask a memory
mechanism to infer an unavailable new cause. It tests persistence of the explicit
revocation/unresolved state and the follow-up obligation.

These information limits are clear from the contracts and observation boundary,
but they are **not measured counterfactual causal effects**: seeds do not change
the hidden south value, source availability, or true cause, and there is no paired
no-inspection ablation or alternate hidden-value experiment. The result therefore
supports bounded behavior on these authored information conditions, not a
statistical or information-theoretic impossibility claim.

The public controller supplies goal resumption, current completion predicates,
public prerequisite filtering, cost feasibility, action schemas and relevant
post-uncertainty inspections equally to all arms. Static outcome attempts,
statuses and private override values are stripped from controller input; possible
written key names remain public for recovery relevance. Actual public effects
and current institutional registers can convey execution state without memory.
Trust acceptance/rejection is supplied by the host, rather than inferred from
language. These are material design constraints: the study evaluates usable
retained evidence in structured workflows, not unrestricted natural-language
planning, autonomous social trust, or a playable-world improvement.

## Reproduction without replacing the first final run

From the repository root, the original run used the bundled Python 3.12 runtime
and seeds 1000–1019. The following reproduces it into a new output directory,
verified absent when this report was prepared. It was **not executed** during
analysis. The evaluator refuses an existing output directory and checks frozen
source/task hashes and exact heldout seeds before execution.

```sh
cd /Users/tanmaygoswami/Claude_backup/Projects/kalends
PYTHONPYCACHEPREFIX=/tmp/kalends-pycache \
  /Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m kalends.continuity_release.evaluation \
  --tasks specs/continuity_release/heldout.json \
  --out /private/tmp/kalends-continuity-frozen-heldout-reproduction-20261024-audit \
  --seeds 20 --seed-start 1000
```

The frozen heldout bytes, all first-run failures, source manifests, and superseded
development artifacts remain intact. The result supplies no basis for promoting
the candidate over unchanged V3 on the primary endpoint.
