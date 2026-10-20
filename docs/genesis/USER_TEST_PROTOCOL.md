# The City That Remembers You: prospective user study

**Protocol proposal, 20 October 2026. No external participants have been
recruited or tested, and no retention, enjoyment or creator-success result is
claimed.** These are internal product decision thresholds, not industry
benchmarks. Register the final protocol, build hash, scenarios, exclusions and
analysis script before recruitment. Engine experiments are a separate source of
evidence; thousands of simulated agents are not human users.

## Questions and staged samples

| Stage | Proposed sample | Question and decision |
|---|---:|---|
| Formative | 8 adults, varied simulation-game experience | Find comprehension, navigation and accessibility failures; revise freely. Exclude these participants from confirmatory cohorts. |
| Comparative usability | 48 new adults, 24 per condition | Can people act, understand an executed consequence, and enjoy branching? Compare the full experience with an otherwise matched version with the same world, dialogue and history inspector but no branch control. This control is a proposed study build, not a shipped feature. |
| Voluntary return | 200 new adults | Do people return to the same world without scheduled tasks, return payments or facilitator reminders? Measure actual resumed play. |
| Authoring | 12 new creators: 8 nonprogrammers, 4 developers | Can outsiders make a different valid scenario without core-engine edits? Run only after usable authoring tools exist; they are not presently an accepted product capability. |

Recruit adult participants outside the project team and friends who already know
the intended explanation. Record prior game experience and accessibility needs;
do not claim a representative consumer population from a convenience sample.
Obtain informed consent, explain event logging, offer withdrawal and compensate
initial study time at a disclosed fixed rate. Return visits in the retention
cohort are voluntary and unpaid, with this made clear in advance. Public sharing,
multiplayer and user-generated public worlds are outside the initial study.

Randomize usability condition within prior-experience strata. Counterbalance a
small preregistered set of scenario seeds between conditions. Both versions must
use actual simulation outcomes, equal time and the same introduction. Do not
give the full-condition group a curated successful branch while giving the
control an arbitrary seed. A 48-person study can expose major usability problems;
it cannot establish small retention improvements. Report intervals rather than
declaring a branching benefit from a noisy mean difference.

## Tasks and measures

The facilitator reads a fixed, neutral introduction: the world advances when the
player advances its clock, people hold private information, and actions have
rules. Do not reveal which policy or branch should perform better. Use a
30-minute session with up to five minutes of tutorial, then uncoached play.

1. Find a public fact and distinguish it from a selected character's belief.
2. Communicate a supply claim to a chosen recipient. Before confirming, explain
   who will receive what. Measure proposal errors, clarification, cancellation,
   successful ledger insertion and time to the first valid intervention.
3. Advance time and inspect an actual consequence. Measure whether the player
   can identify changed inventory, settlement or relationship state rather than
   merely repeat dialogue.
4. Ask a character why an interaction changed. Inspect the supporting events.
   Score a five-item quiz: original claim, recipient's available evidence,
   relevant decision, executed outcome, and whether an intervention actually
   tested the explanation. Distinguish chronology, dependency and counterfactual
   evidence. Two raters, blind to condition where practical, score recorded
   answers against the actual ledger; resolve disagreements and report agreement.
5. In the full condition, create an alternative history and compare results.
   A valid experiment can produce no change. Record whether the participant
   understands this, and whether they choose a second investigation themselves.
6. Offer optional uncoached continuation. Measure meaningful actions and active
   time. An open tab, animation playback or repeated clock clicks alone do not
   establish engagement.

Ask separate seven-point questions about enjoyment, attachment, agency,
intellectual interest and confusion. Do not substitute "interesting technology"
for enjoyment. Ask whether the participant wants to return, then compare this
stated intention with actual voluntary return. Collect open reasons for stopping,
including repetitive behavior, distrust, lack of stakes and interface friction.

## Prospective falsification gates

These gates deliberately test a large, useful signal. They may be revised after
formative work, then frozen for the independent cohort. A failure warrants fixing
or narrowing the product, not quietly lowering the threshold after seeing data.

| Test | Proposed continue threshold | Failure / interpretation |
|---|---|---|
| First intervention | At least 18/24 full-condition participants complete a valid communication within 3 minutes of the task, without facilitator rescue | Below this: interaction is not yet legible enough for a broader launch. |
| Causal comprehension | At least 17/24 full-condition participants score at least 4/5, with no credit for claiming a dependency alone proves necessity | Below this: the explanation promise is not demonstrated. Report each question, not just the total. |
| Enjoyment and continuation | At least 16/24 rate enjoyment at least 5/7; at least 12/24 voluntarily continue for 10 active minutes and perform a meaningful new action | Passing interest but failing enjoyment/continuation rejects the "playable medium" inference. |
| Branch preference | Report condition difference in enjoyment and voluntary continuation with participant-level intervals; at least 12/24 full-condition users voluntarily try a second branch/investigation | A null or adverse condition difference is evidence against prioritizing branching UX; this small study is not a definitive efficacy test. |
| Voluntary day-7 return | Of 200 initial participants, point estimate at least 25%, with Wilson 95% lower bound above 15% | Upper bound below 15% is a no-go for the current return proposition; intermediate results are inconclusive and require a fresh cohort. |
| Outside authoring | At least 8/12 complete a valid, meaningfully different scenario within 90 minutes, without an engine edit or staff doing the work | Fewer successes reject "accessible creator platform" for this build. Report novice and developer subgroups separately. |

For retention, day 1 is a resumed session starting in `[20 h, 48 h)` after the
first session; day 7 is `[6 d, 9 d)`. A return requires at least 10 active minutes
and one meaningful communication, transaction, commitment or investigation in the
same saved world. Use the full initial cohort as denominator; missing telemetry
counts as no observed return, with consent withdrawals reported separately and
excluded only under the preregistered rule. Scheduled interviews, prompted tasks
and compensated visits are reported separately and never counted as voluntary
return. An unprompted return outside a window is useful secondary evidence.

The app must accurately describe persistence: a local saved world resumes when
opened; no claim of off-line autonomous activity unless such advancement has
actually been implemented. Follow-up installation friction, crashes, loss of a
save and inability to launch are product failures to report, not inconvenient
participants to drop. At 200 participants a return proportion near 25% still has
several percentage points of uncertainty. The proposed threshold is a business
decision rule, not a claim of general population fit or a powered comparison to
another game.

## Authoring test and full-session cost

Give creators the same documentation and starter package. A new scenario must
change at least one institution, incentive or resource rule and produce a
different consequential interaction; renamed Roman characters alone do not
qualify. Log setup time, documentation searches, staff interventions, validation
errors, repair time, scenario size and engine modifications. Have independent
players try the result. Measure author hours per enjoyable retained player hour;
an exported file alone is not successful content creation.

For every complete player session capture wall time, simulation CPU time, peak
resident memory, event count, snapshot/journal bytes, network transfer, browser
frame time and input-to-visible-state latency (p50/p95). Record machine/browser
versions, population, ticks, branches and errors. Measure both client and server
if hosting is later introduced. A proposed local interaction target is p95 under
250 ms for ordinary actions on a declared reference machine; expensive branch
runs may use a visible progress state and a separately declared budget.

The deterministic implementation requires no model credentials and has zero
provider inference spend. Record optional future requests, tokens, failed
validations, retries, provider/model versions, voice characters/minutes, latency
and actual billing receipts separately. Proposed hosted text-session provider
budget: p95 at most $0.20 per 30-minute session, subject to a measured quality
gate. This is an untested budget, not an observed cost. Include hosting, storage,
content labor, support and moderation when evaluating commercial contribution;
model cost alone is insufficient. See the assumption-based scenarios in
[COMPANY_THESIS.md](COMPANY_THESIS.md).

## Instrumentation, analysis and integrity

Use consented pseudonymous participant/session IDs; build/config hashes;
condition and scenario seed; proposal/clarification/accept/reject events;
authoritative ledger IDs; branch IDs and hashes; active play intervals; evidence
opened; task completion; quiz scores; survey responses; crash/restart/save
failures; and return timestamps. Collect typed conversation content only with
specific consent and a deletion/redaction path. Do not record private keystrokes
or unrelated machine activity. Export deidentified study data and the analysis
code; preserve a private mapping only as long as consent administration requires.

Analyze assigned condition on an intention-to-treat basis. Report all attempted
sessions and technical failures, intervention help, exclusions and missing data.
Use participant-level bootstrap intervals for continuous/difference measures and
Wilson intervals for proportions; clicks, agents and events are not independent
human samples. Report raw counts alongside intervals. Preregister primary
questions and label all later subgroup searches and multiple comparisons as
exploratory. Do not tune the build using a confirmatory cohort and then report it
as an untouched validation set.

Stop a session if the participant requests it, data handling fails, or the build
corrupts a save. Diagnose the failure before further recruitment. A revised build
gets a new identifier and, for a confirmatory claim, a fresh cohort. Consent,
usable persistence and truthful representation of causality are prerequisites;
they do not establish that people enjoy the product.

**Decision rule:** advance a small first-party experience only after interaction,
comprehension, enjoyment and return gates are met. Test a creator business only
after outside authoring and resulting player value are demonstrated. No planned
study in this file is evidence that either condition currently holds.
