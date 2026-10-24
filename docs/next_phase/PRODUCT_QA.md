# Product verification

## Baseline audit

Source `21127f0`; QA port 8811 and separate temporary journals. Desktop and
390×844 captures are under `demo/next_phase/baseline/`. The baseline tests were
actually rerun: 947 Python and 110 frontend tests passed.

| Reproduction | Expected | Observed | Priority |
|---|---|---|---|
| Enter Pompeii, speak to Sabina, leave an unsent draft, open LEARN, return LIVE | Preserve local scene and conversation | Loading overlay remounts; local draft/context lost | High |
| Select Pompeii then reload the host | Resume selected life | Host returns to Shared Observatory | High |
| Visit homepage as a newcomer | Choose a place and understand a role | Mode controls, metrics and raw transaction review lead the journey | High |
| Inspect a life with a corrupted journal | Other valid lives remain accessible | Existing service constructor fails closed for the entire directory | High, source review |
| Enter LAB then return | Explicit exposure warning and durable marker | Private view is deliberate but exposure is not recorded | High, source review |
| Review allocation, advance one minute in another tab, confirm original review | Reject stale action, no allocation | Correctly rejected with visible stale message | Passed |
| Cancel an inspection | No spending or new observation | Correct; accepted command count remains zero | Passed |
| Submit 5+5+5 allocation | Reject without state mutation | Correctly rejected; no accepted command | Passed |

The familiar capacity rule is public conditional information. Its presence alone
does not prove leakage of the current private condition. The product projection
will distinguish public rules, actual dated reports and current uncertainty.
Global private-inspection/report counters will not be presented as the
participant's own spending or knowledge.

## Implemented release and actual journeys

The new service runs at port 8810 with `.kalends/next_phase/`; port 8800 and its
original journals remain separate. The old reported 8790 URL was not listening
at this phase's inspection. Public routes lead through two actual templates and
new unique life identities. Existing `/api/`, `/os/`, `/immersion/`, navigation
and asset routes remain served; `/legacy/` retains the previous console.
Operator URLs on the new service require a recorded acknowledgement.

Actual browser QA uses the in-app browser, approximately 1265×720 desktop and
390×844 narrow layouts. Captures are under `demo/next_phase/final/`. These are
product executions, not human-participant sessions.

| Journey/check | Executed result |
|---|---|
| Fresh Observatory `observatory_2898dc1a5d60` | Entered through catalog, requested Mira's dated report, cancelled then accepted it; credits remained 12. |
| Invalid allocation | 5+5+5 rejected, preserving the accepted world. |
| Two tabs on that life | The second tab advanced an hour. The first tab's allocation review was rejected as stale and could not confirm. |
| Promise and consequence | Promised Lin 4 units, allocated 4/4/4, stopped at minute 1438, then explicitly crossed the publicly known minute-1439 settlement. Actual execution delivered 4/4/0 and missed Lin's promise. |
| Supported alternative | Omitted allocation command 3, replayed later commands, and displayed executed units 8→0 and completed projects 2→0. The original journal remained unchanged. |
| Fresh Pompeii `pompeii_b2436bc08914` | Entered an actual new 3D life, spoke with Sabina, read an ordinary-life topic, cancelled a consequential preview, then paid the reviewed 3-coin market arrangement. Cash changed 6→3 only after acceptance. |
| History round trip | Camera, selected Sabina conversation and unsent draft survived opening and closing Your story; the same iframe stayed mounted. |
| Full page reload | Same life URL, entered state, adjusted camera and unsent Sabina draft restored after scene readiness. No Enter screen was required again. |
| Time, independent development and return | Explicitly advanced an hour. Dama went to the household independently. Sabina offered counter work and Lucius sought replacement supplies. Walked to Sabina's new counter; her changed greeting described the actual 4/2 delivery. The unsent draft survived the interrupted encounter and later reopening. |
| Writer conflict | A second launcher against the active save directory refused to start; no second writer or reset was created. |

A real browser pass found that the compatibility bridge announced successful
preview POSTs as accepted actions. Restricting notifications to successful
`act`, `move` and `advance` fixed disappearing reviews and inaccurate meaningful
action telemetry. A regression test checks previews, routes and mode reads.
The corrected preview remained open until explicitly cancelled or confirmed.

## Verification scope

The final full Python suite passed **1015 tests** and the full frontend suite passed
**144 tests**. Logs are `results/next_phase/python-tests.log` and
`results/next_phase/frontend-tests.log`. Backend tests exercise isolated malformed journals, exact restart,
cross-life/stale proposals, journal-save rollback, post-accept metadata warnings,
read-only examples across compatibility mutation routes, duplicate LAB query
parameters, public reflection/alternative projections and Host/Origin checks.
Frontend tests include actual app handlers against a small DOM boundary and
the real scene adapter; they cover iframe identity, visibility restoration,
local view persistence, bounded read-only retries, revision ordering and LAB
DOM removal. Those harnesses do not substitute for native layout/WebGL QA.

The new bundle builds successfully. Existing build notices remain: retained
classic navigation script, runtime portrait URL and the large PlayCanvas bundle.
The marketing page loads no iframe or PlayCanvas runtime until a life is entered.

`results/next_phase/safety_check.json` compares all 17 original journals with the
recorded baseline. Previous studies, world templates, the existing runtime and
default cognition are unchanged. Personal notes, bookmarks and local view state
are distinct from canonical facts and NPC memories. Telemetry is opt-in and
contains no raw conversation text. No live inference, embedding calls, public
deployment, repository push, recruitment, outreach or purchases were performed.

Accessibility is a functional keyboard/layout
check, not an assistive-technology certification. No enjoyment, demand, learning
or unprompted retention result follows from this verification.

## Final adversarial/browser checks

- **Journal failure:** in the disposable 8812 fixture, preserved the original
  journal and temporarily blocked its replacement. An inspection failed visibly,
  with zero accepted commands and all 12 credits retained. Restoring the exact
  journal and making a newly reviewed choice charged once, leaving 11 credits.
- **Metadata failure after acceptance:** independently blocked only display
  metadata. The world journal accepted one inspection, deducted one credit, and
  the UI said **World saved · Display metadata needs attention**. It did not
  report the financial choice as failed. Both journals replay from disk with
  exactly one accepted command and 11 credits. See `failure_recovery.json`.
- **Incompatible save:** the malformed fixture appears alongside the valid
  life, without an invented role/date. Show diagnostics displays the real parse
  failure. Original malformed bytes are preserved; no reset is offered.
- **Research:** the first LAB screen warns before disclosure. Acknowledgement
  persists operator exposure. Returning removes the private research DOM; the
  ordinary hidden `#main` was empty. This is a local tool, not multi-user auth.
- **Opt-in:** consent persisted only in the disposable fixture. Its local event
  file contains only the declared allowlisted fields, with no raw free text.
- **Studio:** validated Pompeii and Observatory in the browser and compiled a
  separate one-day Observatory. Backend regressions also validate/compile/reload
  both adapters at 1, 30 and 90 days. The discovered horizon/rule mismatch and
  end-boundary opportunity bug are fixed. Forms match backend limits.
- **Cross-life tabs:** advanced Observatory in a second 8810 tab while Pompeii
  stayed open. Observatory advanced to minute 1499; Pompeii remained at minute
  89 and its journal hash was identical. See `cross_life_tabs.json`.
- **Narrow:** checked home, saved lives, Observatory conversations, reflection
  and the resumed 3D world at 390×844. The story drawer/body measured 375 px
  content width with no horizontal overflow. Escape closed the drawer and
  restored the participant view. Temporary viewport overrides were reset.
- **Restart:** after the local processes stopped between work sessions, both
  product lives reloaded from their journals with their actual balances and
  positions. Only the new 8810 service is left running at delivery. The old
  8800 process is not claimed to remain running. Closing a browser tab discards
  its local sessionStorage drafts; accepted world choices remain durable.

## Performance, separately measured

`scene_performance.json` and the full-interface developer trace capture a
36.184-second idle rendered Thermopolium scene: **1088 frame intervals**, mean
33.257 ms, p95 34.7 ms, p99 35.313 ms, approximately **30.07 callbacks/s**.
Conditions: Apple M2 reported through ANGLE/Metal, PlayCanvas 2.23.3, Chromium
155 in the in-app browser, balanced quality, DPR 2, iframe 1280×642 and render
target 1920×963. Render submission averaged 3.017 ms. No GPU/compositor or
physical-display timing was measured. This does not establish a 60 FPS target.
Warm-cache scene readiness was 334 ms, first ready draw 461 ms; cold load and
real-device mobile performance remain unmeasured. Paused hosts are excluded
from rendered-frame accounting and stop rendering while history is shown.

`backend_timing.json` separately records 20 serial loopback GETs per endpoint
after one warmup: catalog median 32.91 ms / empirical p95 41.51 ms; life median
9.28 ms / p95 10.19 ms. These include connection/server/full-body-read time,
exclude JSON parsing, and are **API timings**, not browser INP or frame pacing.
The machine was shared and uncontrolled. No real-time speedup or learning claim
is attached to either measurement.

Full-interface screenshots and a written walkthrough are delivered. The
retained video recorder captures only the canvas; it was not presented as a
recording of the HTML interface.
