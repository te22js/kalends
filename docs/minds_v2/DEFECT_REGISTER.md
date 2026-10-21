# Playable V2 defect register

Baseline runtime277f645,21October2026. Source/model checks and actual browser observations are labeled separately. A developer walkthrough is not a human fun test.

| ID / severity | Reproduction | Expected / actual | Root cause | Status at baseline audit (historical) |
|---|---|---|---|---|
| P01 / high | Actual RebirthWorld: walk to(770,650), then request(770,676). | A26-unit vertical step. Actual route returns toy415 and traverses496units, charging6worldminutes. | All street coordinate paths are forced through the horizontal backbone. | Pure collision-valid navigation in progress; baseline raw record saved. Must preserve old-command replay. |
| P02 / high | Request a long walk; click a different destination or reverse direction while the displayed path is running. | New input should be acknowledged/replan. Source and actual shipped-script harness show ignored input and no feedback. | `blocked()` includes the entire rendered path, coupling input admission to animation completion. | Controller replacement in progress. Real browser retarget verification required. |
| P03 / medium | One brief ArrowLeft press at the household in the baseline browser. | A short tap should move once. Observed clock stayed08:08; instrumented replication pending. | Keys are sampled only in RAF and deleted on keyup, allowing a full press to fall between samples. | Pending measured verification; do not count as a confirmed general failure rate. |
| P04 / high | Journal→Places→House of the Menander from the opening. | Arrival prompts should match the visible scene. Actual screenshot shows Aelia on the main street while location label says Household and context offers nearbyLucius. | Authoritative endpoint is committed before interpolation; HUD/interaction use endpoint rather than rendered presence. | Separate authoritative route from visible interaction readiness. Baseline screenshot01 retained. |
| P05 / high | Same260-unit horizontal displacement, once as a click and once as ten26-unit steps. | Equivalent travel should consume equivalent world time. Actual model reports3 vs10minutes. | Every movement command independently rounds up and charges at least one minute. | Accumulate physical travel before rounding; regression must compare segmented and single-command paths. |

The table statuses above record the initial audit; current dispositions follow below.

Baseline full suite:524passed in18.05s. Existing eight client integration checks also pass with diagnostics hooks; passing them did not prevent these movement defects. Instrumentation is developer-only (`?dev=1`), local and bounded, with no dialogue/private-memory collection.

## Verified release disposition

P01/P05: distance-valid V2 paths and cumulative rounding pass matched engine regressions; old commands retain revision1. The3,200-call movement CPU study records shorter routes with a small CPU cost increase, not a speedup.

P02/P04: browser retarget with ArrowLeft and Stop interrupted household→fullery travel; then household→fullery→bakery→thermopolium completed. Street labels and Stop stayed consistent during travel; conversation opened on visual arrival. Independent shipped-app checks also cover modal cancellation and delayed movement→Lab response ordering. Public `water`/`forum_access` aliases no longer bypass the48-unit ordinary-step bound.

P03: immediate keydown queues a tap; deterministic keyup-before-RAF and browser tap observations pass. The original baseline browser key observation was confounded by focus behavior and is not a measured tap-failure rate. The earlier continued raw trace records eight accepted inputs, zero ignored inputs and eight next-changed-actor-paint rows. Two rows captured residual prior motion before the new route returned: these are not eight causally attributed new-intent trials. Recorded lower-empirical p50 is19.6ms (conventional median20.8ms), maximum33.2ms. Its16HTTP samples have recorded p50 7.1ms (median7.3ms). This small warm sample does not establish cold-start, physical-device or general tail latency.

Final diagnostics add a separate strict-idle metric: each input must start with no active navigation or remaining animation, receive its matching accepted movement, and submit a changed Player draw after scene filtering. The final eight-input same-room browser sample has median31.0ms/max32.8ms, no cancellations or pending observations. All586 raw rows remain. It measures JavaScript Canvas submission, not physical display. Nonidle, cancelled, superseded and unmoved inputs are excluded rather than counted as zero latency;11 independent-clock regressions cover attribution/censoring/quantiles. See `results/minds_v2/playability/idle_trace_protocol.json`.

Additional failures reproduced during V2 integration: Lab/Wait resumed an old route; holding a rejected arrow during conversation queued a later walk; typing prevented Escape; interrupted pointer/drag state survived blur/lost capture; an unsent Felix draft appeared in Sabina's conversation. Red→green shipped-script regressions cover the fixes. Editable Escape was also exercised in the actual browser; the recipient-switch draft fix was not browser-rechecked. OS capture behavior is not fully established by a VM harness.

No causal FPS comparison is supported: the9-case renderer fixture's empty control changes60→30Hz. Physical mobile performance, controlled cold-start tails, many-agent/large-history performance and human enjoyment remain unverified. An earlier exploratory startup input outlier was about1.07s; it was not retained as a controlled baseline. See the main handoff and raw evidence for scope.
