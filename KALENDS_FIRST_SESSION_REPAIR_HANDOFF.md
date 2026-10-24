# Kalends first-session repair handoff

24 October 2026 · `codex/continuity-release-prep`, based on the verified
`codex/experience-journey` commit `6ebe9ec463c0144ba4ce53cb182646f5bf87f152`.
Verified implementation and walkthrough milestone: **`16cc062`**. Later
handoff-only commits do not change that implementation; `git rev-parse HEAD`
identifies the final local documentation checkpoint.
The owner’s reported inability to understand the original experience remains
the motivating release blocker. This is an implemented and browser-checked
repair ready for another observed first session; it is not a passed human
comprehension, enjoyment or educational-benefit gate.

## Open the repaired build

**<http://127.0.0.1:8823/>** is running with separate durable review saves in
`.kalends/first_session_review`. Choose **Start with a guide** for Pompeii or
**Guide me through a round** for Shared Observatory. Help can resume guidance;
Practice creates a labelled, separate fresh life. Your worlds returns to the
same saved identity. Reading does not advance the world; walking, accepted work
and deliberate time controls retain their real costs.

From the repository root, the exact launch command is:

```sh
./scripts/run_next_phase.sh --port 8823 --directory .kalends/first_session_review
```

Stop the process already using that port before launching it again. Existing
older servers were left alone. A pre-repair Python server must be restarted to
load the new backend; changing its browser URL or refreshing static files alone
does not upgrade that process. No existing user save was imported, reset or used
as a tutorial fixture. Browser QA used `/private/tmp/kalends-first-session-qa`
on port 8822, not the durable review directory.

## What changed

- Both introductions use per-life, versioned guidance derived from actual
  accepted commands, admitted evidence and recorded outcomes. Reading
  acknowledgements cannot fabricate movement, copied documents, a payment,
  promise, allocation or delivery. Live time stays off during guidance.
- Homepage, role/situation pages, current objectives, dialogue openings,
  choice descriptions, reviews, time controls, results and return copy were
  rewritten. Priced choices show both their purpose and cost. Market delivery
  discloses its twenty-minute action before confirmation and its actual split
  afterwards. No large map, renderer or AI framework was added.
- Observatory distinguishes missing records from zero, requests from promises,
  saved allocation from actual delivery, and rated capacity from dated reports.
  Reviews include totals, dated capacity warnings, public execution order and
  known obligations. Project requirements show the latest admitted status.
- Five history cards distinguish historical evidence, reconstruction and
  fictional gameplay, with source links, limits and image-rights statements.
  The modern notebook does not install facts in NPC memory.
- Existing NPC work and scheduled travel are labelled. The guide uses public
  meeting places or admitted dated sightings; it does not track unseen current
  coordinates. A second account from Lucius is a supported alternative to Dama.
- Saved-world entry resumes the current situation, including resolved outcomes.
  Help navigation can leave a conversation safely; enlarged instructions scroll
  to their controls. Reflection selects the latest substantive action and makes
  earlier admitted records accessible. Travel/clock records remain expandable.
- Malformed guide metadata preserves files and permits inspection rather than
  crashing a valid life. Recovery with unknown guidance/practice provenance is
  conservatively excluded from unassisted research. Optional local telemetry
  remains off until consent and excludes free text and character-private memory.

The complete defect/reproduction record is [DEFECT_REGISTER.md](docs/first_session/DEFECT_REGISTER.md).
Implementation milestones include `f40e4eb`, `eafc996`, `e04e26d`, `29d8b4a`,
`ecb6c56`, `08796c5` and `aa39475`; final documentation/evidence commits follow
them on the same preparation branch.

## What actually ran

These were agent-operated native-browser walkthroughs, not recruited playtests:

| Separate QA life | Accepted outcome and checks |
| --- | --- |
| `pompeii_11a5ed48dde8` | Real walking; reload at p2; Sabina review cancelled then accepted; document copied before its guide prompt; onsite food-counter card; Dama’s instructions; market arrangement paid 3 coins and delivered 4 units to Sabina / 2 to Felix during 20 minutes. Help, larger text, reduced motion, actual duty movement and saved return checked. Final minute 67. |
| `observatory_188b91ee9911` | Report cancelled then accepted; invalid negative allocation rejected; unsupported speech clarified; guidance off/resume/reload; explicit 4/4/4 allocation against an 8-unit report; optional 4-unit promise to Lin; cancelled then confirmed1439-minute finish; actual 4/4/0 delivery and missed promise. Next round opened at 1440 with prior result retained. |
| `pompeii_a21844646586` | Separate practice identity; explicit controls skip; early decline without copying accounts or making payment; guide waited for outcome; reviewed 360-minute deadline; buyers autonomously delivered 6 units to Lucius. Original market life remained separate. Fresh-browser saved entry resumed this outcome. |
| `observatory_4ba95fb62e67` | Separate practice; deliberately finished early without a report, allocation or promise. Review disclosed zero allocations; actual settlement delivered zero to every team. Guide moved to the recorded result. Settled summary and one-minute next-round review were captured; next advance was cancelled at 1439. |

[BROWSER_QA.md](docs/first_session/BROWSER_QA.md) contains the ordered walkthrough
and capture inventory. [Browser evidence](results/first_session/browser/) includes
actual PNGs, full accessibility snapshots, accepted journals and the raw local
performance trace. Superseded failure captures remain labelled as such. The
canvas recorder completed, but it excludes HTML instructions/dialogue and its
download was not recovered through the browser tool; no full-interface video
or saved current video is claimed.

The normal 1280px scene, a 503px Observatory viewport and a 390 CSS-pixel embedded
fixture were inspected. These are not physical-phone or screen-reader tests.
One M2/WebGL2 trace during canvas recording had 1897 frame intervals,
p95=28.12ms, maximum373.1ms, and one accepted idle movement sample at111.8ms.
Recording overhead is included. These are browser callbacks/draw submissions,
not GPU/display latency or a general performance guarantee.

Final backend suite: **1176 passed**, 53.73s. Final frontend suite: **224 passed**,
zero failures/skips. Vite build passed; the final scene bundle is
`index-CbuBMLFg.js` / `index-BdUbm4iJ.css`. Existing build notices concern the
separately served navigation script, runtime portrait path and bundle size.
Exact logs/commands are in [FINAL_TESTS.md](docs/first_session/FINAL_TESTS.md) and
[verification artifacts](results/first_session/verification/). No product
release success is inferred from those counts.

## Copy, historical sources and research

The [rendered copy review](results/first_session/copy_review.html) contains 52
executed/explicitly labelled formatter cases, 649 displayed blocks and 279 distinct
backend strings; the [review record](docs/first_session/COPY_REVIEW.md) maps the
actual frontend surfaces and observed mistakes as well. This is a bounded
state/surface review, not every possible historical-save/string combination.
Source fingerprints and machine-readable cases accompany the HTML.

See [historical source review](docs/first_session/HISTORY_SOURCE_REVIEW.md),
[source ledger addendum](docs/first_session/HISTORICAL_SOURCE_ADDENDUM.md),
and [optional teacher guide](docs/first_session/TEACHER_GUIDE.md). Cards use
original paraphrases and schematic existing game geometry; no external source
photograph or invented ancient inscription was reproduced.

The parallel frozen research milestone is preserved. An independent agent
authored tasks from a public contract without target implementation access.
Eight held-out workflows × 20 noise seeds × 5 arms produced 800 executions with
matched logical budgets and checkpoint/uninterrupted replay agreement. Candidate
and V3 both passed 140/160 primary cases, with 160 paired ties: **no candidate
advantage was shown**. One workflow failed for every arm. The final cases were
not tuned after exposure. [RESEARCH_RESULTS.md](docs/continuity_release/RESEARCH_RESULTS.md)
states the baselines, executed outcomes, costs, failures and independence limits.

The bounded existing-provider character pilot is implemented and **disabled**.
Its current status has no authorized endpoint, no numeric session cap, no paid
calls and zero estimated spend. An endpoint plus explicit numeric cap and enable
configuration remain prerequisites, not authorization inferred from this handoff.
See [AI_PILOT.md](docs/continuity_release/AI_PILOT.md).

## Preservation and the release decision

The verified release ref remains at 6ebe9ec. All 25 inventoried non-display-metadata
save files and 2212 historical artifacts still match their baseline hashes; all 20
frozen research/task checks match. One pre-existing live display-metadata file,
`.kalends/next_phase/.product/state.json`, drifted during the session while the
old server remained active. Its origin is unconfirmed; **byte preservation of
that file is not claimed**. Its original/current hashes are recorded and no
rollback erased it. See [preservation.json](results/first_session/verification/preservation.json).
The repository has no Git remote: protection here is the preserved release ref,
separate preparation branch and local verification guard, not hosted enforcement.

The next release remains gated on real human feedback. Re-run the owner’s
first-session test and observe consenting unfamiliar users for 15 minutes and an
actual return. Use the brief’s six unaided questions: role, situation, available
actions, cost/consequence, actual result, and historical evidence versus fiction.
The proposed 5-of-6 threshold has not been measured here. Record coaching and
mistakes rather than counting guide acknowledgements as understanding.

Human decisions still needed: whether the role and first choice are clear;
whether the two paths feel worth continuing and returning to; whether the history
is understandable and appropriately qualified; whether/where to recruit an
observed test; and whether a later bounded live pilot merits an explicitly
authorized endpoint and spending cap. Physical-device/accessibility coverage,
long-save variants and broad conversational quality remain limited. No paid
service was launched, no new company thesis was substituted, and no claim of a
compelling 15-minute experience is established until people demonstrate it.

## Reproduction commands

```sh
# Repository root; Python3.10+ required. These exact commands use the installed runtime.
PYTHONPYCACHEPREFIX=/tmp/kalends-pycache PYTHONPATH=/Users/tanmaygoswami/Library/Python/3.9/lib/python/site-packages /Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest -q
node --test tests/frontend/*.test.cjs
cd kalends_3d
npm run build
cd ..
PYTHONPATH=. /Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/verify_continuity_release.py
PYTHONPATH=. /Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m kalends.continuity_release.pilot --status
```

The strict preservation variant `scripts/verify_continuity_release.py
--strict-metadata` intentionally fails while the separately audited display
metadata differs. Research reproduction, using a **new** output directory so
historical results are not overwritten:

```sh
PYTHONPATH=. /Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m kalends.continuity_release.evaluation --tasks specs/continuity_release/heldout.json --out /private/tmp/kalends-frozen-study-reproduction --seeds 20 --seed-start 1000
```
