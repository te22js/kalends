# Playable V2 defect register

Baseline runtime277f645,21October2026. Source/model checks and actual browser observations are labeled separately. A developer walkthrough is not a human fun test.

| ID / severity | Reproduction | Expected / actual | Root cause | Fix / verification |
|---|---|---|---|---|
| P01 / high | Actual RebirthWorld: walk to(770,650), then request(770,676). | A26-unit vertical step. Actual route returns toy415 and traverses496units, charging6worldminutes. | All street coordinate paths are forced through the horizontal backbone. | Pure collision-valid navigation in progress; baseline raw record saved. Must preserve old-command replay. |
| P02 / high | Request a long walk; click a different destination or reverse direction while the displayed path is running. | New input should be acknowledged/replan. Source and actual shipped-script harness show ignored input and no feedback. | `blocked()` includes the entire rendered path, coupling input admission to animation completion. | Controller replacement in progress. Real browser retarget verification required. |
| P03 / medium | One brief ArrowLeft press at the household in the baseline browser. | A short tap should move once. Observed clock stayed08:08; instrumented replication pending. | Keys are sampled only in RAF and deleted on keyup, allowing a full press to fall between samples. | Pending measured verification; do not count as a confirmed general failure rate. |
| P04 / high | Journal→Places→House of the Menander from the opening. | Arrival prompts should match the visible scene. Actual screenshot shows Aelia on the main street while location label says Household and context offers nearbyLucius. | Authoritative endpoint is committed before interpolation; HUD/interaction use endpoint rather than rendered presence. | Separate authoritative route from visible interaction readiness. Baseline screenshot01 retained. |
| P05 / high | Same260-unit horizontal displacement, once as a click and once as ten26-unit steps. | Equivalent travel should consume equivalent world time. Actual model reports3 vs10minutes. | Every movement command independently rounds up and charges at least one minute. | Accumulate physical travel before rounding; regression must compare segmented and single-command paths. |

Baseline full suite:524passed in18.05s. Existing eight client integration checks also pass with diagnostics hooks; passing them did not prevent these movement defects. Instrumentation is developer-only (`?dev=1`), local and bounded, with no dialogue/private-memory collection.
