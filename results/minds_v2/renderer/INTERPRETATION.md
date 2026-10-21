# Renderer fixture: interpretation of the preserved browser run

The [browser run](browser_run_20261021.json), committed with game integration `a287492`, completed all nine protocol cases with 180 recorded intervals each. All cases report complete, `overall_valid:true`, an unchanged 1280×720 backing surface and no recorded error, visibility or viewport interruption. Phaser identifies the actual runtime as4.2.1 and renderer as WebGL1.0. The raw JSON SHA256 is `6739dc45da9c85401f0c0a343d9d784969e4f914d7e3dc77f26b53fcb61694b5`.

The run also contains an apparatus cadence shift: the empty requestAnimationFrame control changes from approximately60Hz to30Hz. That rules out interpreting a simple pooled cadence difference as a renderer effect. The cause of the shift is unmeasured; neither browser throttling, hardware limits nor a framework bug is established by this trace.

| Mode | Repetition0 callback rate | Repetition1 callback rate | Repetition2 callback rate | Mean render-submission CPU span range |
|---|---:|---:|---:|---:|
| Empty rAF | 60.01Hz | 30.00Hz | 30.00Hz | 0.000–0.001ms |
| Canvas2D | 60.00Hz | 59.98Hz | 30.00Hz | 0.018–0.041ms |
| Phaser WebGL | 60.00Hz | 33.54Hz | 30.00Hz | 0.121–0.131ms |

Each CPU range contains the three per-case means, not an inferential confidence interval. Canvas submission spans are lower in this small fixture. The CPU hook scopes and renderer bookkeeping differ; low-resolution timers also return many zero-duration Canvas samples. These are CPU wall-time submission measurements, not GPU completion, physical refresh rate or actual hardware dropped frames. Initialization, shared asset decoding and fixed warmup are excluded. No framework-wide speed ratio follows from the values.

The protocol's valid flag checks its technical stop rules, not stationarity or causal attribution. The Latin-style orders give each renderer an early, middle and late position, but one nine-case sequence on one changing apparatus cannot estimate a reliable FPS ranking. The 1,620 frame intervals are dependent observations within nine cases, not 1,620 independent trials. No case was dropped or rerun to improve the comparison.

This is a painted background with seven sprites on shared elapsed-time paths. It excludes actual game simulation, request/save latency, dialogue, labels, masks, physics, interactions and richer scenes. It supports preserving Canvas while addressing measured controller/backend defects; it does not show that a complete Phaser migration would be faster or slower, that input is responsive, or that the full game sustains60FPS. The original [protocol](protocol.json) remains unchanged as the pre-execution design record. This interpretation is post-run analysis, not an amended preregistration.
