# Kalends

## Experience OS — two domains, shared continuity

Compile a Pompeii life or a shared-instrument coordination experience on the
existing Kalends ledger, observation, economy and clock. LIVE participates;
LEARN debriefs actual choices and runs an omission retry; LAB inspects the same
world's private minds, plans and evidence. Runs offline by default.

```sh
./scripts/run_experience_os.sh                 # http://127.0.0.1:8800/
./scripts/run_experience_os.sh --port 8802 --directory /tmp/my-kalends-lives
```

Keep the foreground terminal running; Ctrl-C stops its server. The directory
has a writer lock. Reopening uses its embedded-spec command journals and checks
exact replay. Existing Rebirth/Immersion saves use their original servers.
The 3D frontend uses the existing `kalends_3d/dist/` build; if absent, build it
with `cd kalends_3d && npm ci && npm run build`.

Start in **Shared Observatory**: request the systems team's dated report,
promise capacity, review an allocation and compress one day. Then enter LEARN
and retry a real choice. The compiler accepts a finite supported schema, not
arbitrary natural-language worlds. Changed specifications need new IDs.

[Complete handoff](KALENDS_EXPERIENCE_OS_HANDOFF.md) ·
[Architecture and limits](docs/experience_os/ARCHITECTURE.md) ·
[Executed research](docs/experience_os/RESEARCH_RESULTS.md) ·
[Company and research thesis](docs/experience_os/COMPANY_AND_RESEARCH_THESIS.md)

The recorded demonstrations span 90 Commons days and 120 Pompeii days. The
972-world final cognitive study found no V3-over-V2 outcome benefit; retention
strategy affected promises/check costs. Conservative time compression preserved
the measured histories but demonstrated no additional adaptive speed advantage.
There are no human learning or subjective-time results.

## Rebirth — the illustrated account at the fountain

A painted Pompeii district, portrait conversations, and a disputed six-sack cart.
Use documents, coins or household service; then live with changed access,
relationships and funded commissions. Works offline with no runtime packages.

```sh
./scripts/start_rebirth.sh                     # detached, http://127.0.0.1:8782/
./scripts/start_rebirth.sh --status             # check or use --stop
./scripts/run_rebirth.sh                       # foreground alternative
./scripts/run_rebirth.sh --temporary --port 8784 # separate unsaved life
```

Start with Sabina by the fountain. Click to walk, use the offered choices, and
review before confirming. Arrows/WASD move; E talks; X leaves a room; J opens
your journal. Actions and explicit time controls advance the world. Closing it
preserves the present moment. Saves use `.kalends/rebirth_session.json`.

[Rebirth handoff](KALENDS_REBIRTH_HANDOFF.md) ·
[First session](docs/rebirth/FIRST_SESSION_WALKTHROUGH.md) ·
[Actual browser screenshots](docs/rebirth/VISUAL_QA.md) ·
[Research results and limits](docs/rebirth/RESEARCH_RESULTS.md)

The detached launcher keeps the local server running when its terminal closes.
See [local operations](docs/rebirth/LOCAL_OPERATIONS.md) for logs and restart checks.

To continue an old life, choose a **new** destination; the source stays intact:

```sh
./scripts/run_rebirth.sh --migrate-from .kalends/pompeii_session.json --journal .kalends/rebirth_continuation.json
```

The earlier Pompeii chapter and its frozen studies remain available below.

## Pompeii — the playable lived-world prototype

Walk a historical-fiction district, earn wages, trade flour, broker dated reports,
make promises, accept household obligations, and return after a week. Gameplay
and the operator World Lab have separate screens. Runs offline without API keys.

```sh
./scripts/run_pompeii.sh                       # http://127.0.0.1:8780/
./scripts/run_pompeii.sh --temporary --port 8781 # fresh unsaved life
```

Click streets/buildings to walk; WASD/arrows move, E speaks, X exits interiors.
Start at Felix's bread counter. Natural-language actions show a confirmation card.
Use the journal for places, belongings, evidence, and World Lab alternatives.
Python 3.10+ is required; the launcher also finds the Codex bundled runtime.

[Complete handoff](KALENDS_POMPEII_HANDOFF.md) ·
[Gameplay guide](docs/pompeii/GAMEPLAY_LOOP.md) ·
[Research paper and limits](docs/pompeii/RESEARCH_PAPER.md) ·
[Actual browser captures](results/pompeii/DEMO_WALKTHROUGH.md)

Frozen fresh studies: exact scheduled compression in 90/90 matched comparisons,
1.12–1.21× local speedup, and a 240-world society study with reported negative
and null results. No human playtest or historical behavioral validation is claimed.
The earlier projects below and their results are preserved.

## Fork the City — runnable local world

The new city demonstration connects the existing ledger, private experiences,
and memory backends to consequential grain decisions and isolated history forks.
It runs offline with no runtime dependencies or model API keys.

```bash
python3 -m kalends.city_server                 # http://127.0.0.1:8765
python3 -m pytest tests/                      # original + city/ActionBench invariants
python3 -m kalends.city.causal                 # actual message-deletion replay
```

For the first branch: reset to seed 42, **Step twice** to complete tick 1,
deliver a verified inspection to Livia, then **Step**. Her original and altered
choices, cash and inventory differ. Select her decision to inspect the evidence
and run **Test a message dependency**. All displayed values come from the engine.

See [local demo instructions](docs/fork_city/RUNNING.md),
[architecture](docs/fork_city/ARCHITECTURE.md),
[new research note](docs/fork_city/RESEARCH_NOTE.md), and
[sprint handoff](KALENDS_SPRINT_HANDOFF.md). New measurements live only in
`results/fork_city/`; the historical MemoryBench artifacts below are unchanged.

```bash
python3 -m kalends.actionbench.runner --split heldout --seeds 30 --populations 8,32 --out results/my_actionbench
python3 -m kalends.actionbench.plots results/my_actionbench  # optional matplotlib
```

## Original MemoryBench substrate

A research substrate for **persistent AI worlds** in which agents maintain
temporally correct, causally grounded, individually bounded memories and
beliefs over a changing shared reality — and **Kalends-MemoryBench**, a
benchmark that scores memory architectures against an *exactly computed*
per-agent epistemic ground truth (no LLM judges, no annotation, fully
deterministic and replayable).

The core separation, enforced structurally:

```
WorldEvent → World State → Observation → Agent Belief/Memory → Decision → Action → New WorldEvent
```

- **Objective reality** is a deterministic fold over an append-only event
  ledger. No LLM can assert what happened.
- **Observation** is computed by the world (event scope + positions).
- **Belief** is per-agent with machine-checkable **provenance**:
  `heard it from Livia at E135 → Livia observed E84 directly` — including
  root signatures that distinguish independent evidence from shared ancestry.
- **Counterfactual surgery**: rerun the same world minus one event; because
  all randomness is context-keyed, the runs differ only through genuine
  causal channels.
- **Memory systems** receive only the information that actually reached each
  agent and are scored on belief accuracy, staleness (a stale belief can be
  the *correct* answer), supersession, source attribution, provenance,
  independent corroboration, and knowledge boundaries.

## Quickstart

No runtime dependencies. Python ≥ 3.10 (matplotlib only for plots).

```bash
python3 -m kalends simulate rumor --seed 42          # deterministic demo world
python3 -m kalends benchmark --seed 42               # 9 systems on the demo world
python3 -m kalends explain --agent Holconius --prop bakery.condition
python3 -m kalends counterfactual --seed 42 --drop 2 # causal-descendant diff
python3 -m kalends experiment --suite core --seeds 30 --out results/core
python3 -m pytest tests/                             # 40 invariant/audit/fuzz tests
```

## Historical MemoryBench results (30 seeds × 9 scenario families)

Mean overall accuracy (±sd across seeds; boundary-violation rate in brackets):

| system | core avg | notes |
|---|---|---|
| recency (floor) | ~0.67 | strong floor; must be beaten |
| bm25 | ~0.78 | beats hashed-BoW vector everywhere |
| vector (hashed BoW) | ~0.70 [0.20–0.51] | classic RAG failure profile |
| vector+metadata | ~0.82 [~0.01] | filtering kills boundary hallucination |
| text_structured (parser) | ~0.83 [0.10–0.41] | the ceiling made real; entity-resolution failures |
| structured (**ceiling**) | ~0.94 [0.00] | by-construction; only alias misses |
| hybrid (naive) | ~0.92 [0.28–0.59] | **loses to structured on 9/9 families; collapses at scale (0.68 @ 128 agents)** |
| **hybrid_guarded** | **~0.96 [0.00–0.03]** | fallback only where the belief table has no opinion; beats both parents on 9/9 families, scale-stable (0.92 @ 128) |

The benchmark falsified the naive hybrid hypothesis, the failure analysis
located the mechanism (boundary hallucination through the fallback path), and
the guarded router — a one-rule change — wins everywhere. That loop
(benchmark → diagnosis → fix → verification) is the research story.
Details: [FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md),
[METHODOLOGY_AUDIT.md](METHODOLOGY_AUDIT.md) (which scores are meaningful vs
ceilings), plots in `results/plots/`.

## Repository map

| File | What it is |
|---|---|
| `ARCHITECTURE.md` | the system in ~10 minutes |
| `FORMALISM.md` | precise task definition (information sets, normative belief, root signatures) |
| `METHODOLOGY_AUDIT.md` | circularity/fairness audit; which numbers to trust |
| `RESEARCH_NOTES.md` | two literature passes incl. honest MemArena repositioning |
| `FAILURE_ANALYSIS.md` | categorized failure modes + the guarded-router case study |
| `TEMPORAL_RESOLUTION.md` | why adaptive resolution is future work |
| `DECISIONS.md` / `WHAT_I_BUILT.md` / `WORK_QUEUE.md` / `PAPER_OUTLINE.md` | project memory |
| `kalends/` | substrate: events, world, observation, epistemic oracle, rng, counterfactual, memory/, bench/, scenarios/ |
| `scripts/` | scaling, capacity, ablation, failure-analysis, plotting |
| `tests/` | 40 tests: invariants, oracle audit, property fuzzing |
| `results/` | 30-seed suites, scaling, capacity, ablations, failures, plots |

Baseline tag: `kalends-memorybench-v0` (the original single-scenario v0,
exactly reproducible).
