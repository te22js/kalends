# Public evaluator interface for the blind task designer

This describes only the environment and common controller contract. It exposes
no evaluated memory implementation, prior outcome or target-specific tuning.
New workflows are research fixtures over Kalends' existing Ledger, projected
WorldState, cash accounting and EventClock. They do not create a playable domain.

Write two JSON documents, each `{ "version": 1, "cases": [...] }`. Six development
workflows and eight final heldout cases are suitable. Do not read candidate code
or run comparisons. Freeze both files and the scoring rubric before comparisons.

## Case fields

Each case has `id`, `family`, `label`, `horizon_minutes` (1..129600), `credits`
(0..20), `initial_facts`, `timeline`, `goals`, `actions`, `decisions`, `assertions`.
IDs use short lowercase identifiers. All proposition values are **strings**.
Use days/weeks of virtual time, not merely new labels on two adjacent choices.

A fact is `{ "subject":"parcel", "predicate":"destination", "value":"north",
"public":false }`. Public defaults to false. Initial facts establish actual
world truth. Public facts are available equally through an institutional register;
other facts require an admitted observation. Public registers may contain workflow
status and balances; do not make all needed historical evidence public by accident.

Timeline proposition row:

```
{"at":0,"subject":"parcel","predicate":"destination","value":"north",
 "visibility":"direct","update_truth":true,"text":"Owner's dated routing instruction",
 "as_of":0,"accepted":true,"salience":0.5}
```

`visibility` is `direct`, `told`, `public` or `hidden`. `update_truth` defaults true
except for `told` (false). Direct observations must match world truth when received.
Testimony may be wrong; specify `source` for `told`. `accepted:false` marks a
host-rejected/unverified claim rather than granting it authority. `as_of` defaults
to receipt time and cannot be in the future. A newer direct value can supersede
an old report. Model retraction using explicit `revoked`/`unknown` state and a
corresponding correction. Hidden updates produce no observation or pacing hint.

Noise row: `{"at":300,"kind":"noise","count":32,"spread_minutes":400,
"label":"Unrelated intake receipts"}`. The seed changes receipt text/timing
within that declared interval. Do not treat seeds as independently authored tasks.
At most 128 timeline rows, with bounded noise counts <=64 per row.

## Goals and offered actions

Goal: `{"id":"delivery","label":"Deliver the correct parcel", "priority":90,
"deadline":10080,"complete_when":[{"subject":"parcel","predicate":"delivered",
"value":"yes"}]}`. Completion facts must be public institutional facts, not
an undisclosed side effect. At most eight goals. Goal prerequisites/active state
must be visible in the public workflow register. The same controller resumes
these goals and reads receipts for every arm; memory cannot alter the workflow.

Action:

```
{"id":"send_north","label":"Send parcel to the north depot","goal":"delivery",
 "priority":5,"requires":[{"subject":"parcel","predicate":"destination",
 "value":"north","max_age":43200}],
 "public_requires":[{"subject":"parcel","predicate":"prepared","value":"yes"}],
 "cost":1,"effects":[{"subject":"parcel","predicate":"delivered","value":"yes","public":true}]}
```

At most 14 actions, including explicit inspection actions. IDs/labels describe
real choices, never an evaluator answer label. An action's `requires` are the
declared evidence requirements for proposing it and actual preconditions for
world execution. The world does not filter actions using hidden truth. If an
agent chooses from stale/false evidence, execution rejects the precondition and
records that failure without revealing the hidden replacement value.
`max_age` defaults to the case horizon. Public prerequisite filtering uses only
public facts. Own credits and public workflow status are available equally.
Completed-goal actions are no longer offered. All ordinary mutations need a goal.
The common controller derives its task cues from this public action contract;
do not prescribe what a memory arm should retain or discard.

An inspection action uses `inspect:[{"subject":"parcel","predicate":"destination"}]`
instead of effects, has a finite `cost`, and may have `public_requires` such as
source availability. Inspection returns actual fresh direct observations to the
actor. It does not secretly replenish an archive. Goal may be omitted for an
inspection, making it available as a shared recovery operation.

Effects are fact rows. Optional `op:"increment"` adds integer string `value` to
the prior integer string. This supports count-based duplicate/partial execution
checks. Default effect visibility is public, except explicitly private effects.

An action may declare `outcomes:[{"attempt":1,"status":"partial","effects":[...]}]`.
Statuses are `succeeded`, `failed`, `partial`, `unknown`. Defaults: succeeded with
the normal effects. A scripted outcome overrides effects for that attempt.
Operational failure/partial/unknown may spend the action's stated cost; a rejected
precondition does not. All outcomes create an actual receipt. Unknown private
effects remain hidden until an inspection; do not expose them as goal completion.

## Decision windows, interruption and recovery

`decisions` is a chronological list of `{"at":1440,"max_actions":2,"checkpoint":true}`.
Use 6..32 windows; up to four operations per window. The common controller:

1. receives only new legally admitted timeline/receipt observations;
2. reads current public workflow/goals/own cash, identical for all arms;
3. chooses a supported offered action or waits from bounded retained context;
4. if it has no supported mutation, may buy an available explicit inspection;
5. after failed/partial/unknown execution, requires a relevant available inspection
   before retrying that mutation. It never blindly repeats an uncertain write.

The controller's goal/pending-recovery state and references count toward each
arm's memory budget. It cannot look up evicted content by a source ID. Checkpoints
serialize the real ledger, clock, economy, memory and controller, then reconstruct
them; the agent never sees evaluator checkpoints or assertions. Events may change
hidden state between decision windows, without any guarantee of success.

## Frozen scoring assertions

Primary endpoint: **all declared assertions pass on actual executed state**.
Also report each assertion, completion of each goal, failed/precondition-rejected
actions, resource spend, duplicate effects, inspection costs and real outcomes.
Use only these fixed assertion forms (optional `label`, `weight` defaults 1):

- `{"type":"fact","subject":"parcel","predicate":"delivered","value":"yes"}`
- `{"type":"receipt_count","action":"copy","status":"succeeded","min":1,"max":1}`
  (`status` optional to count all outcomes).
- `{"type":"order","before":"verify_copy","after":"retire_original"}`
  requires first successful before to precede first successful after.
- `{"type":"never","action":"unsafe_publish"}` (all attempts, not just successes).
- `{"type":"credits_min","value":0}`.
- `{"type":"rejections_max","value":0}` for rejected preconditions, excluding
  deliberately scripted operational failures.

Assertions and hidden truth are evaluator-only. Do not encode the right action in
the current observation. A fully restated current-information control and a case
with unobserved change are required. Explain cases that are information-limited,
not failures to remember unknowable truth. Avoid a rubric that rewards simply
waiting forever; completion facts/required receipts should matter.

Attest which files were read. When ready, hash both JSONs and the rubric into a
manifest. Neither final heldout bytes nor scoring may change after comparisons.
