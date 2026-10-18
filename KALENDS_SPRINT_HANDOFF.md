# Kalends — Fork the City sprint handoff

**Delivered:** a working offline simulation, playable browser inspector, isolated
history forks, actual message-deletion checks, and reproducible ActionBench data.
The scientific results are mixed and expose a material scoring limitation.

## Git and preservation

- Branch: `codex/fork-the-city`, created from clean `master` at `8040b22`.
- Frozen study implementation: `ce2f2b8`.
- Latest tested implementation, including causal replay/browser fixes: `70d069a`.
- The delivery commit containing this report is repository `HEAD`; obtain its
  exact latest hash with `git log -1 --format='%H %s'`. Git cannot embed a commit's
  own hash into that same versioned file without changing the hash.
- Original engine/memory/MemoryBench sources and historical results are intact.
  The historical seed-42 ledger still hashes to
  `d15f677449ca8596bf1e831e226d6b35228a06185e130bbdfab7e9db78ae8ef3`.
- No repository push, public deployment, model API use, or paid dependency.

## Implemented features and changed files

`kalends/city/` reuses the existing Ledger, WorldState, observation, epistemic,
Experience, and keyed-RNG primitives. It adds a24-tick grain economy, roles,
movements, queued reports, honest source roots, local memories, inspections,
cash/inventory/price changes, delivery commitments, trust updates and consequence
events. Engine populations 2–128 are supported; the browser offers8/32.

Forks copy the complete current state and queues, preserve an identical prefix,
and evolve independently. Interventions are verified inspection, pending-message
removal/replacement, and identity control. The operator can inspect private
information separately from world truth. Comparisons use actual state differences.
The optional causal checker reconstructs the factual prefix and deletes one
queued ancestor to test a selected original-timeline decision.

`kalends/city_server.py` serves the static interface and JSON API on loopback,
serializes mutations, and journals commands for deterministic restart recovery.
`kalends/city/static/` contains the map, playback, agent inspector, ledger,
structural traces, fork/comparison controls, causal-test button and JSON export.

`kalends/actionbench/` contains existing-memory adapters, a fixed action policy,
separate gates, paired-world runner and plot generation. New tests cover city,
memory adapters, branching, causal replay, evaluation, persistence and real HTTP.
`scripts/` adds reproduction, replay verification, sensitivity, independent
inspection, physical economy audit and isolated resource profiling.

Packaging entrypoints/static data, `.gitignore`, and README were extended.
All added/changed paths are listed in [FILES_CHANGED.txt](docs/fork_city/FILES_CHANGED.txt).

## Install, run and reproduce

From the checkout with Python 3.10+ (zero runtime dependencies):

```bash
python3 -m kalends.city_server
# Open http://127.0.0.1:8765
```

Optional conventional install/test environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest tests/ -q
.venv/bin/kalends-city
```

For the first branch: reset to seed 42/eight citizens/structured/no gate; step
twice to complete tick 1; give Livia a verified inspection; step once. At tick 2
her original reserve spends 12 denarii on 3 units, while the branch defers and
retains the cash. Select original decision#10, then **Test a message dependency**.
Actual deletion of queued message#5 changes reserve→defer in a paired replay.

```bash
python3 -m kalends.city.causal
python3 scripts/reproduce_fork_city.py --out results/fork_city_reproduction --no-plots
python3 scripts/actionbench_sensitivity.py --out results/fork_city_sensitivity_reproduction --seeds 30
python3 scripts/verify_actionbench_replay.py results/fork_city/heldout --sample 24
python3 scripts/inspect_actionbench.py results/fork_city/heldout --replay
python3 scripts/audit_city_economy.py --artifact results/fork_city/heldout --out results/my_economy_audit.json
python3 scripts/profile_fork_city.py --out results/my_city_profile.json
```

Plotting alone needs optional `matplotlib`:

```bash
python3 -m pip install matplotlib
python3 -m kalends.actionbench.plots results/fork_city/heldout
python3 -m kalends.actionbench.plots results/fork_city/scaling128
python3 scripts/plot_actionbench_sensitivity.py --root results/fork_city
```

Existing nonempty experiment outputs are protected against overwrite. The
ignored `.kalends/city_session.json` recovers both timelines after restart; use
`--journal ''` for a disposable session. Full instructions: [RUNNING.md](docs/fork_city/RUNNING.md).

## Validation and measured evidence

**227 tests passed in 10.89s** under CPython 3.12.14, including the original 40.
Python compilation, JavaScript syntax and Git whitespace checks passed. A clean
temporary Python 3.12 package installation included all three static assets and
ran the actual city. Browser QA verified stepping, running/pausing, inspector,
forking, comparisons, evidence navigation and the actual deletion test at mobile
and desktop sizes; the original viewport was restored. API tests cover reset,
restart recovery, rejected inputs, concurrency and branch-specific advancement.

Final held-out measurements contain **5,640 worlds and 1,041,627 decisions**, with
four scenario families, 30 paired seeds, 8/32/128-agent studies, retention/depth
sensitivity, four main memory architectures and separate gate ablations. There
are 30 independent seed clusters, not a million independent observations. Raw
decisions, configs, source hashes, world-level CSVs, clustered CIs and plots are
in `results/fork_city/`. Development pilots are marked and excluded. 24 sampled
main semantic hashes and selected failure cases replayed exactly. The posthoc
physical audit verified every decision and ledger in all 1,320 eight-agent worlds.

- Structured/guarded local QA is 1.000, yet declared action error is 37.59%, 43.90%,
  49.35% at 8/32/128. A faithfully remembered false report can still cause loss.
- Main lineage-vs-sender regret differences have CIs spanning zero. Lineage 2
  worsens regret versus ungated guarded at 8, is uncertain at 32, and improves the
  combined verification policy's score at 128. The 128 study lacks sender gating,
  so it cannot isolate lineage value there.
- At capacity 8, naive hybrid beats guarded on declared regret by 0.2863
  [0.1785, 0.3940]. The guard is not uniformly better under retention pressure.
- **Task loss is not economic welfare.** At 8 agents, actual delivery fill is
  65.87% ungated guarded, 58.62% sender gating, 53.08% lineage gating. The
  always-verify policy scores better than always-defer but has identical delivery outcomes
  and spends more cash. Zero-fill reserves can receive zero task loss.
- Isolated seed 42 simulation medians are 0.0117/0.0864/0.5220 seconds at 8/32/128;
  peak traced Python allocations are 0.63/3.49/15.44 MiB. These are five repeated
  runs of one configuration; suite timing used concurrent jobs and is not the
  isolated resource result.

Evidence: [research note](docs/fork_city/RESEARCH_NOTE.md),
[failure cases](docs/fork_city/FAILURE_CASES.md),
[validation record](results/fork_city/validation.json),
[physical audit](results/fork_city/economy_audit.json),
[resource profile](results/fork_city/profile.json),
[literature audit](docs/fork_city/LITERATURE_AUDIT.md),
[architecture](docs/fork_city/ARCHITECTURE.md),
[strategy](docs/fork_city/STRATEGY.md).

Genuine browser captures:

- `docs/fork_city/screenshots/live_fork.jpg`
- `docs/fork_city/screenshots/verified_dependency.jpg`
- `docs/fork_city/screenshots/decision_replay.jpg`

## Limits and next steps

The demonstration is a product prototype and a useful research instrument,
**not a validated commercial product or publication-strength superiority result**.
The closest literature already studies downstream memory, lineage admission and
paired worlds. The strongest finding here is conditional failure analysis and
the measured distinction between recall, declared task loss and actual delivery.

The main unresolved issue is utility alignment: fixed categorical scores can
credit unfilled orders. Per-world grain arrivals do not scale with population,
and scarce stock is allocated in fixed agent order. Scaling therefore changes
competition as well as communication/compute. Root labels are honest and
unauthenticated; structured schema/trust is supplied; embeddings are lexical.
Full audit histories remain unbounded. The causal checker tests one deletion,
not all necessary causes. Only current-tick forks and one visible altered branch
are supported. Explicit retractions, arbitrary action edits/past rewind, richer
role policies, long-duration storage management and multiplayer are unimplemented.

The three highest-value next steps:

1. Define prospective regret from **executed** fills, cash and commitment costs;
   model inspection delay and scale supply per capita as a controlled factor.
   Freeze a new protocol before using new held-out seeds.
2. Add an independently authored scenario and the missing128-agent sender-count
   ablation, comparing gates at matched coverage. Test authenticated/forged
   provenance and explicit retractions separately.
3. Run five user sessions. Predeclare success as four users finding a mistaken
   belief, forking an intervention and explaining a real changed outcome within
   ten minutes without help. Use failures to guide explanation/UI work.

## Acceptance checks

| Check | Evidence |
|---|---|
|1. Clean local launch|Clean package install and real loopback browser/API server|
|2. Genuine state changes|Actual movements, reports, purchases, accounts and settlements|
|3. Causally coherent changed history|Verified inspection fork plus exact message-deletion replay|
|4. Inspect supporting information|Agent histories, decision evidence and structural trace|
|5. Computed comparison|Actual independent snapshots/economy/decision differences|
|6. Reproducible policy experiment|Raw paired ActionBench studies, scripts and plots|
|7. Relevant tests pass|227 passing tests; original ledger hash unchanged|
|8. Candid handoff|Completed features, evidence and material limitations above|
