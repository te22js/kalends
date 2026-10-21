# Kalends Immersion: measured rendering and responsiveness

Measured on 21 October 2026 in the actual local browser. The earlier balanced sample sustained a **16.667 ms mean frame interval and 18.1 ms p95** across 3,062 intervals. Five separate idle movement inputs reached their matching accepted player draw in **38.18 ms mean / 48.22 ms p95**. After an interruption, a later comparison recorded approximately 33.3 ms intervals in **both** the legacy and 3D clients. The observed cadence changed between sessions; its cause was not established. These results support feasibility of the small district on this machine, without qualifying sustained 60 FPS across sessions, scenes, browsers or devices.

## Reference machine and scope

- Physical machine: Apple M2, Mac14,2, arm64, 8 GiB RAM, from local system fields.
- In-app Chromium: Chrome/155.0.0.0. Its compatibility user agent reports Intel Mac OS X 10_15_7; that is not the physical CPU or an independently verified macOS version.
- WebGL2 through `ANGLE (Apple, ANGLE Metal Renderer: Apple M2, Unspecified Version)`; 8 browser-reported hardware threads.
- Unmodified desktop viewport: 1280 × 720 CSS pixels, device pixel ratio 2. Balanced/high canvas backing size: 1920 × 1080, capped at 1.5 pixels per CSS pixel. Low backing size: 1280 × 720, with an additional 0.75 scene render-target scale.
- PlayCanvas 2.23.3, seven animated actors, one loaded district. Local offline Python server; no external inference calls in these runs.

These windows are mostly stationary rendering with occasional completed keyboard taps, rather than identical sustained movement courses. Window lengths and input counts differ. Measurements include the short menu operations needed to reset and freeze the trace. They are not a controlled ranking of quality settings: the smaller high-tier p95 is not evidence that enabling effects improves performance.

## Frame and resource samples

All durations below are milliseconds. Quantiles use linear interpolation at `(n − 1) × p`.

| Quality | Trace window | Frame intervals | Frame mean / p95 / maximum | Update-to-submission mean / p95 | Snapshot draw calls | Estimated texture allocation | Used JS heap |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: |
| Balanced | 51.05 s | 3,062 | 16.667 / 18.1 / 32.9 | 1.801 / 2.4 | 661 | 91.27 MiB | 90.86 MiB |
| Low | 17.51 s | 1,048 | 16.699 / 17.9 / 71.4 | 1.165 / 1.6 | 189 | 79.36 MiB | 91.97 MiB |
| High | 32.03 s | 1,921 | 16.666 / 17.6 / 27.8 | 2.028 / 2.8 | 829 | 115.14 MiB | 87.66 MiB |

Balanced uses 1024-pixel sun shadows, two-sample MSAA and no SSAO. High uses 2048-pixel shadows, two-sample MSAA and eight-sample SSAO. Low disables shadows, uses one sample and reduces scene resolution. Warm grading and the restrained post-processing remain. Reduced motion is a separate preference.

Draw calls are PlayCanvas counters at export, including rendering passes; they are not GLB primitive counts or a run average. Texture allocation is an engine estimate, not total GPU memory. JS heap is Chromium's point-in-time estimate and excludes textures, other GPU allocations and Python. Garbage collection makes the lower high-tier heap snapshot unsuitable as an optimization claim.

No long tasks were retained in balanced/high. Low retained one 56 ms long task and one interval above 33.33 ms; its maximum interval was 71.4 ms. No frame interval above 33.33 ms occurred in the balanced or high samples. Absence in these short samples does not establish an absence of stalls during loading or longer play.

Raw evidence: [balanced](perf_balanced.json), [low](perf_low.json), [high](perf_high.json). All rows fit within the 12,000-row buffer; none of these windows was evicted.

## Movement and local backend responsiveness

| Quality | Accepted idle inputs / matched draws | Input-to-accepted-player-draw mean / p95 / maximum | Local HTTP samples | HTTP mean / p95 |
| --- | ---: | --- | ---: | --- |
| Balanced | 5 / 5 | 38.18 / 48.22 / 49.2 | 10 | 12.3 / 20.9 |
| Low | 2 / 2 | 50.8 / 73.12 / 75.6 | 4 | 8.175 / 10.375 |
| High | 2 / 2 | 47.25 / 62.505 / 64.2 | 4 | 16.625 / 26.905 |

All counted inputs began with controller and displayed movement idle, have their own identifier, were accepted by the server, and ended at a changed player draw. None was cancelled or pending at export. Inputs superseded, cancelled, nonidle, rejected or producing no movement are excluded, not assigned zero latency. Two-input percentiles are descriptive only and have little statistical weight.

The endpoint is the engine's JavaScript `frameend` after changing the rendered player transform. It is **not** GPU completion, browser composition, a measured visible pixel, or physical input-to-display latency. The update-to-submission span includes client update and render submission work, not GPU elapsed time. HTTP durations include local request, route/action processing, serialization and response handling; they do not isolate Python CPU. No retry of a consequential action is needed for measurement.

Navigation collision remains the existing authoritative floor/visibility-graph and portal system, translated into the 3D scene. These timings do not benchmark Recast, rigid-body physics, dynamic NPC collision, foot sliding or measured animation quality. Scene transitions and conversations passed separate browser checks; this dataset has no independently isolated doorway-transition latency metric.

## Loading

[The warm reload snapshot](warm_load.json) records:

| Endpoint | Elapsed time |
| --- | ---: |
| Module application boot start → assets/state ready | 318.8 ms |
| Navigation time origin → client ready | 443.5 ms |
| Navigation time origin → first ready engine draw submission | 571.8 ms |

Application boot excludes module transfer/parse before its start. Navigation readiness includes the earlier part of this warm reload, but this is **one cached localhost reload**, not a cold network/download benchmark. The first ready draw is still a submission endpoint. It is not the first physical pixel, and it does not measure how long the player waited before pressing Continue.

Loading had visible compilation/initialization cost: the retained early 32 intervals averaged 22.887 ms, p95 74.31 ms, maximum 139.5 ms. Two long tasks averaged 118.5 ms, maximum 128 ms. These startup rows were reset before the steady rendering windows, rather than silently included in an overall 60 FPS claim. Cold cache, throttled network, mobile hardware and prolonged thermal behavior remain unmeasured.

## Prior-client comparison

An actual later comparison used the retained legacy client at `/?dev=1` and a new balanced 3D control. Both used the same M2, 1280 × 720 CSS viewport, DPR 2 and offline QA journal in the daylight period 09:02–09:03. Each received two separated left/right keyboard taps. The journal advanced between runs, positions differed slightly, and the windows had different lengths; these are comparable local observations, not an identical checkpoint or deterministic course benchmark. The user's original saved life was not used.

| Client in later session | Trace window | Frame intervals | Frame mean / p95 / maximum | Instrumented draw/update span mean / p95 | Idle inputs / matched draws | Input-to-accepted-draw mean / p95 | Local HTTP mean / p95 | Used JS heap |
| --- | ---: | ---: | --- | --- | ---: | --- | --- | ---: |
| Legacy illustrated client | 27.09 s | 817 | 33.129 / 34.3 / 34.4 ms | 0.208 / 0.4 ms | 2 / 2 | 64.75 / 65.335 ms | 23.625 / 30.74 ms | 7.00 MiB |
| 3D balanced control | 42.69 s | 1,283 | 33.256 / 34.4 / 39.5 ms | 2.204 / 3.2 ms | 2 / 2 | 68.5 / 71.2 ms | 24.65 / 35.445 ms | 91.85 MiB |

Raw evidence: [legacy browser trace](perf_legacy_attempt.json) and [3D balanced control](perf_balanced_control.json). The legacy file is a valid completed trace despite its historical `attempt` filename. Legacy means above were calculated from retained raw rows, because its summary exposes quantiles but no means. Each HTTP column has four samples. Both had no retained long tasks or pending input, and all accepted inputs had matching idle draw observations. Both windows fit within their respective 3,000/12,000-row buffers.

The later clients both ran near a 30 Hz callback cadence. Comparing the earlier 60 Hz 3D sample directly against the later 30 Hz legacy sample would produce a misleading speedup. No cause is inferred for the cross-session change, and the legacy diagnostic's estimated missed 60 Hz slots are not evidence of GPU frame drops or a diagnosed renderer bottleneck. This later comparison does **not** demonstrate a 3D frame-rate advantage. The two-input latency difference is too small a sample for a reliable responsiveness ranking.

The 3D client costs more rendering work and memory than the illustrated client: the later 3D snapshot has approximately 91.85 MiB used JS heap and 91.27 MiB estimated textures, versus 7.00 MiB used JS heap for legacy. The legacy trace does not supply an equivalent GPU texture allocation. The draw/update spans have different implementations and endpoints, so they should not be treated as a precise engine CPU ratio. The 3D benefit demonstrated here is the actual modeled, animated and interactive presentation, rather than a claimed performance improvement over a 2D canvas.

Comparison protocol: stop movement and Live time, reset the visible local developer trace, focus the game, perform separated idle taps, then freeze/export its raw trace. Keep the same viewport, daylight situation and owned QA life; retain world checkpoint, window length and any unmatched conditions. More confidence requires repeated equal-length courses at a confirmed stable browser cadence, longer input samples, cold-load tests and an additional physical device.

## Actual capture support and limits

`src/capture.js` uses `canvas.captureStream(30)` and browser `MediaRecorder`, requesting a 20-second, 5 Mbps WebM recording. It prefers VP9, with VP8/WebM fallback when supported. This records the actual WebGL scene, not a screenshot montage. The canvas stream excludes HTML HUD, nameplates, dialogue, menus and Web Audio ambience. Requested frame rate/bitrate are encoder requests, not verified output properties.

An actual recording was saved separately from the performance windows: [kalends_immersion_scene.webm](../../demo/immersion/kalends_immersion_scene.webm), **14,090,645 bytes**, SHA-256 `f5e9453d2b2602f5791d43f2076ff268ad90f1bef8714e1713e85db2ac432480`. The client exposes its finished capture through an explicit menu download link.

[The read-only container audit](capture_validation.json) identifies one 1920 × 1080 VP9 track, 576 nonempty distinct encoded frame payloads and six keyframes. Timestamps are monotonic from 0 to 19.950 seconds; adding the median positive frame interval gives an estimated 19.983-second duration. The observed encoded rate is approximately 28.82 frames/second, rather than an assumed exact 30. The largest timestamp interval is 600 ms, so the capture itself is not evidence of uniform animation cadence. No frames were inserted or transcoded.

This certifies a nonempty recorded WebM stream and its encoded container properties, **not independently decoded visual playback**. The available macOS AVFoundation importer did not recognize WebM/VP9; no ffmpeg/ffprobe was installed, and the in-app browser rejected attempted blob playback under its security policy. No bypass was used. The running game and full viewport PNG screenshots were visually examined separately. Encoding adds work and its run is excluded from the rendering comparison. PNG screenshots provide the HTML interaction context missing from the canvas video. Audio is implemented as optional local synthesized ambience/feedback; listening quality was not measured here.
