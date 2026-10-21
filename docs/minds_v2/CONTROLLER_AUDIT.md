# Controller and navigation audit

21 October 2026. Independent source and model audit of frozen Rebirth commit
`277f645`, performed in `/tmp/kalends-playability-v2-audit`. No shared-browser
control or human playtest was performed by this reviewer. Root owns browser
reproduction, controller changes and the final defect register. Findings below
are not a claim that every visual or interaction problem has been found.

## Reproduced defects

| ID / priority | Reproduction and expected behavior | Actual result and cause | Repair / verification status |
|---|---|---|---|
| NAV-01 / P1 | Move to street point `(770,650)`, then request `(770,676)`, both on the vertical household corridor. Expect a 26-unit direct path. | Actual world path is `(770,650)→(770,415)→(770,415)→(770,676)`: 496 units and 6 world minutes. `PompeiiWorld.move` sends every public coordinate move through horizontal backbone `y=415`, even within one straight corridor. | New pure navigation utility returns direct 26-unit route. Geometry tests pass; authoritative V2 integration and real-browser verification belong to root. Old engine source was preserved. |
| NAV-02 / P1 | Cover the same 260 horizontal units by ten 26-unit keyboard-sized moves or one click. Expect the same travelled distance to have consistent world-time cost. | Fresh actual worlds consume 10 versus 3 minutes at the same final position. Each move independently applies `max(1,ceil(distance/90))`. Keyboard input therefore changes deadlines faster solely because of transaction granularity. | Root must accumulate distance/subminute remainder under a versioned command semantic before rounding. The geometry utility exposes exact distance and tests subdivision invariance; it does not silently change saved-world time. |
| INPUT-01 / P1 | During an accepted 550-unit visual walk, issue another click and a reverse arrow input. Expect responsive retargeting/stopping, or explicit pending feedback. | The shipped script's offline DOM harness sends exactly one movement request; both later inputs are ignored and no toast explains why. `blocked()` includes the Player display path, and pointer/key movement uses it. Long accepted animations lock movement controls after HTTP completion. | Root should separate pending network commit from visual interpolation, retain the latest movement intent and provide deterministic cancellation/retargeting semantics. This is a source/harness reproduction, not measured browser input latency. |

The old visual speed is 550 world units/s; NAV-01's 496-unit route nominally
requires about 0.902s of interpolation for an intended 26-unit displacement.
This is derived from path length and code, not an observed frame-time sample.
The keyboard controller additionally attempts 26-unit steps at most every 190ms;
the actual rate also depends on request completion and path completion.

Reproductions used the bundled Python 3.12 `RebirthWorld` and the actual shipped
`app.js` through the existing offline Node VM harness. No source mutation was
needed to expose these failures. The existing eight client tests still test
their original asynchronous and rendering contracts; their passing does not
establish responsive movement.

## Source risks to verify, not counted as reproduced defects

- Camera following applies a fixed 0.025 interpolation factor per rendered
  frame. It therefore has a frame-rate-dependent settling time: approximately
 119 frames to remove 95% of a fixed offset, or about 1.98s at 60Hz versus 3.97s
  at 30Hz. This is an analytic consequence, not an FPS or jitter measurement.
  Use elapsed-time smoothing and measure actual visible following.
- Context/proximity comes from the final authoritative snapshot while actors
  are still animating toward that snapshot. Verify prompts against displayed
  positions and animation state; do not silently authorize simulated actions
  from invented visual positions.
- Canvas panning has no `pointercancel`/`lostpointercapture` cleanup for its
  drag state. Verify interruption by OS gestures/focus loss before counting a
  stuck-pan defect.
- `confirm()` lacks the epoch guard used by proposals, but the current busy
  lock prevents opening another conversation and rendering checks selection.
  A stale conversation reopening was **not established**. Do not count the
  initial suspicion as a real defect without a failing sequence.
- The rendered environments are flat paintings. Region-valid navigation does
  not establish furniture collision, foreground occlusion or archaeological
  alignment of every painted object.

## New geometry contract

`kalends_rebirth/navigation_v2.py` is pure: it does not mutate a world, advance
time, emit a ledger event or authorize an interaction.

- `path_between(start,end,current_location='street',target_location='street')`
  returns finite coordinate tuples with exact required door waypoints.
- `path_distance(path)` computes total travelled length. A clock adapter must
  accumulate this quantity consistently across small and large input chunks.
- `point_walkable(point,location)` validates a center point on the authored
  public street union or the existing 15-unit inset room floor.
- `project_point(point,location,max_distance=48)` explicitly projects a nearby
  click within its selected scene, rejecting distant targets. Projection alone
  cannot enter another room or replace authoritative validation.
- `segment_walkable(start,end,rooms=())` checks complete segment coverage,
  including only the named rooms and their explicit doorway connectors.

Public routing uses a Euclidean visibility graph over the two authored street
rectangles. Concave-corner routing avoids cutting through building space;
same-corridor travel is straight. Interior travel crosses designated portals
via narrow centerline connectors between the public door and inset floor.
This is coarse actor-center floor geometry, not a furniture mesh or full-body
clearance model. No coordinates were inferred from the illustrations.

`tests/test_navigation_v2.py`: **30 passed in 0.06s**, including the final
unknown-location type check.
Coverage includes all 12 ordered room pairs, all six initial NPC destinations,
an analytic shortest concave-corner route, direct vertical/horizontal movement,
wall-crossing rejection, explicit bounded projection, subdivision-invariant
distance and malformed coordinates. Final integration must preserve legacy
accepted-command replay before enabling these new movement semantics.

## Diagnostic contract recommended to root

Keep diagnostics opt-in and developer-only, with a bounded ring buffer and a
manual local export. Do not store raw dialogue or poll private agent state for
performance labels. Use one monotonic clock and explicit command/scene IDs.

For each input, record event timestamp, accepted/ignored reason, intended
destination, supersession/cancellation, request start/end, parse/accept cost,
first visible response frame and completion frame. Separate input-to-feedback
from input-to-arrival; the latter naturally includes intended travel distance.
For each frame record raw rAF delta, actual render duration, interpolation
work, render/idle/hidden/modal status and scene. Do not compute percentiles from
the movement integrator's 50ms-clamped delta. Mark frame-budget exceedances,
request queue depth, path calculation time and asset readiness separately.
Unsupported browser memory/long-task APIs must be reported unavailable.

Use matched routes and viewport settings before/after, warm assets and include
failed/ignored inputs in denominators. Report the actual browser/reference
environment. 60FPS is a target until measured; mock animation frames are not
evidence that a physical device sustains it.

## Authoritative movement integration checkpoint

The follow-up integration adds `RebirthWorld.move` revision2 and accepted-command
`movement_revision` metadata. Direct world calls and old commands without the
field retain revision1, preserving the original ledger bytes. New session moves
use the pure floor route, end room exits at the public door, and append actual
distance/charged-time/cumulative carry metadata. The carry is projected from
move events into private world state, declared fidelity and World Lab. Charging
is `ceil(cumulative_distance/90)` minus minutes already charged; a prepaid
partial minute survives stops and restart. This is integer world-time accounting,
not a claim about physical travel time or wall-clock animation speed.

The current unit-test expectation for an already-stationary street destination
now correctly charges zero minutes. The old performance protocol and every raw
study artifact remain unchanged. The pinned old-memory journal fixture now
explicitly executes movement revision1 while constructing its old prefix; its
original `85a132c0…` expected hash was preserved. The actual saved browser prefix
also restores the original `75ebb2dc…` hash without changing its source bytes.

Full isolated suite before the last defensive fork guard: **570 passed in18.25s**.
After that guard and its regression, affected movement, HTTP server, offer and
benchmark suites: **109 passed in2.94s**. The guard rejects an unsupported
revision even on the action selected for omission, before changing or saving
the fork. Controller responsiveness and actual-browser measurement remain root's
integration work; these passing model checks do not establish smooth play.
