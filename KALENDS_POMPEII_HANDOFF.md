# KALENDS — POMPEII: THE LIVED WORLD

**Delivered 21 October 2026.** A working local historical-fiction game and two
fresh reproducible studies. This is a six-character vertical slice with explicit
limits, not the completed long-term vision of an entire artificial civilization.

## Open and play

The delivered game runs at **http://127.0.0.1:8780/**. If the local process has
stopped, run from this repository:

```sh
./scripts/run_pompeii.sh
# Fresh unsaved life on another port:
./scripts/run_pompeii.sh --temporary --port 8781
```

The launcher selects Python 3.10+ and can use the bundled Codex runtime when the
system Python is too old. There are no runtime dependencies, external asset
requests or required API keys. Direct equivalent:
`python3 -m kalends.pompeii.server --port 8780`.

Click a street or building to walk. WASD/arrows move, **E** speaks, **X** steps
outside. Enter Felix's bread counter, say **“I promise four flour units”**, review
and confirm. Earn a shift at Sabina's counter, seek Lucius's household advance,
or obtain and sell a dated report. Buy four flour and deliver them before dusk.
The [full gameplay guide](docs/pompeii/GAMEPLAY_LOOP.md) explains each route.

LIVE advances time while enabled in the foreground; COMPRESS advances thirty
minutes; MONTAGE reaches the next scheduled change and summarizes available
records; SKIP can simulate a week. A montage can have no visible highlights when
only private events occur. The world does not claim to continue while the local
application is closed. Use an explicit skip to return after a longer interval.

Open the journal for places, inventory and actual events. SHOW WHY traces
available recorded dependencies. **World Lab** is a separate operator view for
private state, export and a genuinely executed removed-action alternative.
It does not install the operator's knowledge into an NPC.

The final opening uses `.kalends/pompeii_session.json`. The browser walkthrough
is preserved separately in `.kalends/pompeii_qa.json`; reopen it on another port
with `./scripts/run_pompeii.sh --port 8781 --journal .kalends/pompeii_qa.json`.
An earlier development save was retained as
`.kalends/pompeii_session.development_20261021.json`. Genesis saves are intact.
Owned baseline/QA servers were stopped; the delivered Pompeii application remains
running at port 8780.

## What was implemented

| Area | Concrete implementation |
|---|---|
| Embodiment | Player identity Aelia; legal movement through a 1600×1100 schematic street network, authoritative routes/durations, doors, cutaway interiors, proximity checks, minimap, camera, mouse/keyboard/touch controls. |
| Historical setting | Via dell'Abbondanza district; Fullonica of Stephanus I.6.7, thermopolium I.8.8 and House of Menander I.10.4; explicitly fictional bread counter, people, balancing rules and compressed geography. Twenty-three claim-level source entries, including contested-date and status restrictions. |
| Work and commerce | Owned coins/flour, finite stocks, changing price, two daily extra shifts per employer, purchases backed by resources and actual transfers. |
| Promises and social standing | Four-unit delivery contract, time/location-sensitive settlement, actual payment, trust and reputation, subsequent daily orders, low-trust trade/promise restrictions. |
| Patronage | Eight-coin household advance, client affiliation, real 120-minute service obligation and deadline, institutional fulfilled/missed record and later relationship consequence. |
| Information economy | Observation date, declared origin and transmission chain; one-coin delayed inspection and bounded dated-log access; recipient-specific report prices/refusals; deduplicated observer confidence; costly verification and content-sensitive deferral. |
| Characters | Six fictional people with distinct resources, duties, status, caution, knowledge, information values and routines. Cash/trust conditions revise immediate stated goals; procurement plans change with evidence and resources. These are authored agents, not learned minds. |
| Memory and institutions | FIFO ordinary memory plus a separate eight-record literal consolidation store; durable accounts, commitments and trust; growing operator archive separated from agent retrieval. |
| Lived time | Reusable stable heap scheduler; minute reference, exact event dispatch, explicit coarse baseline; actual LIVE/COMPRESS/MONTAGE/SKIP controls. |
| Narrative | An objective with three demonstrated resource paths, real settlement and return consequences, and a selector of existing relevant events. No hidden fabricated outcome. |
| Language | Limited offline intent grammar, grounded literal replies, reviewed canonical actions, provider-independent callable proposal adapter, schema/scope checks, bounded retry/timeout/fallback and bounded stalled-worker handling. No configured external provider or measured LLM conversation. |
| Persistence and alternatives | Atomic accepted-command journal, exact replay hash check, all-or-nothing session actions, saved operator intervention; actual command-removal replay with explicitly skipped infeasible later commands. |

The first default-seed demonstrations finish at minutes **79 / 22 / 11** for
wage / household / brokerage routes. They leave **7 / 12 / 6 coins**; the household
route still owes service. These are automated fixtures, not an optimal-policy
result or a claim that these routes always succeed.

## Baseline and code organization

Genesis was inspected and launched before new code was added. Its clean baseline
was `d37e8e7`; all **288 existing tests** passed. Its previous source, results,
negative findings and saves remain intact. The new work is on
**`codex/pompeii-lived-world`**. Implementation/study runtime freeze commit:
**`a024da5768f2eb1deaae3b89c586a56a574e3adb`**. Later work changes presentation,
documentation and result artifacts; the evaluated Python source stays frozen.

The previous four Genesis commits remain in history: `a1010fc`, `66b17e8`,
`76b6fa5`, `d37e8e7`. Pompeii reuses `Ledger`, `WorldState/apply_event`, `Experience`,
keyed random draws and `GenesisEconomy`; no replacement is presented as having
rewritten or repaired Genesis's heldout result.

| File | Purpose |
|---|---|
| `kalends/pompeii/district.py` | Validated configuration, geometry, source references and fictional cast. |
| `world.py` | Authoritative movement, memory, information, planning, transactions, tasks and player consequences. |
| `temporal.py` | Reusable stable event clock and exact/reference/coarse execution. |
| `language.py` | Bounded intent proposals, scoped reply realization, optional-provider contract and validation. |
| `server.py` | Local HTTP game, atomic session commands, saves, privacy-aware traces, World Lab reruns. |
| `static/index.html`, `style.css`, `app.js` | Original Canvas game art, interaction, accessible HTML controls and separate operator UI. |
| `temporal_bench.py`, `society_bench.py` | Registered actual-world studies with fresh seed sets and raw records. |
| `evidence.py` | Reproducible scripted gameplay, return histories and offline language fixtures. |
| `tests/test_pompeii_*.py` | 57 new tests across gameplay, independent audit, scheduling and society measurements. |
| `scripts/run_pompeii.sh` | Portable local launch wrapper; no installation step. |
| `pyproject.toml`, `README.md` | New console entry, packaged static assets and current launch instructions. |

## Fresh research and exact findings

Both studies registered before heldout execution against the same 57-file
Python fingerprint:
`3e99eb91af66bf6fcb61ea57d7ce714ba008807c12ad464910677f1c20d22dbd`.
The end-of-run source guards passed. Development pilots and a rejected
source-changing pilot remain preserved and labeled.

**Track A:** 30 fresh seeds 70000–70029, horizons 1/7/30 days, minute/exact/coarse
modes. Five fresh timing repetitions plus a separate traced-allocation repeat
per cell: **1,620 worlds**. The actual autonomous model matches exactly in
**90/90 minute-versus-compressed comparisons across ten projections**. Mean paired
speedups: **1.1168× [1.0911, 1.1405]**, **1.2101× [1.1952, 1.2267]**,
**1.1950× [1.1848, 1.2062]**, descriptive paired-seed 95% intervals.
Thirty-day compressed mean time is **8.728 ms**, with comparable roughly 621 KB
traced allocations. Fewer empty-minute checks are real computation savings;
this is not an animation-speed or hosted-scale claim.

The coarse baseline fails full dated-record equality in all ninety cells, but
**its action histories, terminal beliefs, executed outcomes, commitments and
relationships match in all ninety**. Some intermediate predictions differ.
The study does not establish that coarse execution worsens final economics.
Exactness covers deterministic scheduled transitions; continuous or unscheduled
dynamics require additional modeling. Discrete-event simulation is prior art.

**Track B:** 30 fresh seeds 71000–71029, four one-factor conditions and two
elapsed horizons, **240 worlds**. Credulous-minus-cautious physical fill is
**+1.534 percentage points [0.423, 2.804]** at seven days and **+7.988
[6.420, 9.827]** at thirty days. Caution spends **11.967 / 38.400 coins** on
inspections and detects one direct false claim per world; credulous procurement
spends none and detects none. Thus verification improves one epistemic/social
measure while lowering modeled output. Removing communication or reducing
ordinary capacity 32→8 changes propagation/retention, but has **exactly zero
physical fill, cash and inspection-cost effect in every paired seed** here.
These nulls limit the scene; they are not concealed as successes.

The earlier Genesis result remains a small adverse gate effect, −0.18031 pp
[−0.25745, −0.10381], with no realized structured-versus-guarded ungated
architecture contrast. No new benchmark is claimed to invalidate that evidence.

The [paper](docs/pompeii/RESEARCH_PAPER.md),
[time architecture](docs/pompeii/LIVED_TIME_ARCHITECTURE.md), and
[society report](docs/pompeii/EPISTEMIC_STUDY.md) explain methods and limits.
The [novelty audit](docs/pompeii/NOVELTY_AUDIT.md) rejects broad scheduling,
generative-town and general memory-superiority claims.

## Verification and evidence

- **345 tests passed** in the complete suite, including all 288 baseline tests.
  New cases cover spatial permissions, transactions, saves/replays, privacy,
  three quest routes, remote delivery prevention, service deadline ordering,
  repeated-source confidence, parser negation/questions, provider failure/timeout,
  exact scheduler behavior and research metrics.
- Browser walkthrough actually completed work, purchase and delivery, persisted
  the accepted events, showed a dependency trace, advanced LIVE while idle,
  used COMPRESS/MONTAGE/SKIP, returned after a week and tested an alternative.
  See [actual captures](results/pompeii/DEMO_WALKTHROUGH.md).
- An independent agent recomputed both studies' main means and paired bootstrap
  intervals from raw records, and verified source, raw-data and society CSV hashes.
- Twenty offline language fixtures produced twenty expected bounded intents and
  evidence IDs in the selected character's retained memory. Final median/max
  proposal latency: **0.071 / 0.283 ms**, zero external provider calls and
  **$0 model inference**. This does not measure rich dialogue quality.
- JavaScript syntax and launcher shell syntax pass; screenshots are visually
  inspected. No supported video-recording API was exposed, so real screenshots,
  a walkthrough and executable histories are supplied instead of a fake recording.

To rerun safely into new directories with the frozen Python sources:

```sh
python3 -m pytest tests/ -q
python3 -m kalends.pompeii.temporal_bench --phase development --out /tmp/pompeii-time-new
python3 -m kalends.pompeii.temporal_bench --phase heldout --out /tmp/pompeii-time-heldout-new
python3 -m kalends.pompeii.society_bench --phase heldout --out /tmp/pompeii-society-new
python3 -m kalends.pompeii.evidence --out /tmp/pompeii-gameplay-new
```

Use Python 3.10+, or set `KALENDS_PYTHON` for the launcher. On this host the
bundled runtime is `/Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.
Pytest and plotting are development tools; the server itself needs only stdlib.
Existing output directories are refused. The saved registered source must match
before a heldout rerun; changing policy source requires a new declared study,
not overwriting the original evidence.

See the [verification record](docs/pompeii/VERIFICATION.md) for exact checks and
independent audit scope.

## Delivered documents

- [Historical source ledger](docs/pompeii/HISTORICAL_SOURCE_LEDGER.md)
- [Product design](docs/pompeii/PRODUCT_DESIGN.md)
- [Gameplay loop](docs/pompeii/GAMEPLAY_LOOP.md)
- [Lived-time architecture](docs/pompeii/LIVED_TIME_ARCHITECTURE.md)
- [Research paper](docs/pompeii/RESEARCH_PAPER.md)
- [Epistemic society study](docs/pompeii/EPISTEMIC_STUDY.md)
- [Novelty audit](docs/pompeii/NOVELTY_AUDIT.md)
- [Company thesis](docs/pompeii/COMPANY_THESIS.md)
- [All seven application roadmaps](docs/pompeii/APPLICATIONS_ROADMAP.md)
- [Future independent playtest protocol](docs/pompeii/PLAYTEST_PROTOCOL.md)

The company thesis names real competitors and dated primary sources, models
explicit scenario costs and break-even, includes failure conditions, and treats
a trillion-dollar outcome as extreme speculation. No customers, retention,
learning gains, revenue or valuation are invented. Education, training, research,
creator, cognitive, entertainment and future VR/neural ambitions have separate
evidence and deployment gates.

## Acceptance accounting and remaining limits

| Requested acceptance | Evidence / scope |
|---|---|
| 1–3 Local game, navigation, motivated characters | Actual Canvas district, proximity/geometry tests, distinct policies and resources; six authored NPCs. |
| 4–5 Language and canonical persistence | Reviewed intent/action path, scoped literal replies, atomic replay journal and hash check. |
| 6–7 Inactive world and four time modes | Foreground LIVE request loop and explicit elapsed simulation; browser demonstrated all controls. No closed-app continuous-world claim. |
| 8 Compute savings with fidelity reporting | Fresh actual-world paired study; modest measured savings, all distortions and null terminal effects reported. |
| 9–10 Meaningful return and grounded history | Kept/missed promises and service, bounded significant memory, literal recall; no invented personal biography. |
| 11–12 Explanation and genuine alternative | Available dependency trace plus freshly executed command-removal history with declared replay rules. |
| 13 Historical support | Twenty-three source claims, source IDs in place descriptions, explicit contested/fictional labels. |
| 14–15 Fresh experiment and regression safety | Two registered heldout runs, independent recomputation, 345 tests including 288 baseline. |
| 16 Interface improvement | Real scene, moving player, rooms, conversations and time controls versus the original research dashboard; actual screenshots. No claimed user preference result. |
| 17 Company thesis | Named current competitors, quantitative assumptions and staged failure gates; no traction claim. |
| 18 Honest handoff | Implemented, measured and future work separated throughout this document. |

The game is local and single-player. It has a small schematic district, one main
commodity, simple routines and policies, limited offline language, literal
consolidation and a repeated introductory order rather than an entire life.
Interior furniture has no detailed collision mesh; NPC location changes are
discrete scheduled state changes rather than a continuous crowd simulator.
There is no voice, configured generative provider, full city, public multiplayer,
production save migration or hosted offline catch-up. The optional provider is
a programmatic callable interface, not a turnkey vendor/credential UI.

No independent human playtest has yet run. The protocol is ready for a person
outside this implementation to test believability, agency, readability, historical
interpretation and willingness to return. Historical specialists have not
reviewed the slice. External people were not contacted without authorization.

The long-term computational-reality ambition remains a research/product
hypothesis. Consciousness, real subjective lives, neural acceleration, therapeutic
benefits and a large company are not implemented or demonstrated outcomes.
