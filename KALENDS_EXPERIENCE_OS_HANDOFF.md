# Kalends Experience OS handoff

24 October 2026 · development branch `codex/experience-os` · preserved baseline
`658ccec` on `codex/project-immersion`.

This phase delivers a working, finite experience-platform prototype. It reuses
the existing simulation infrastructure for two different domains. It does not
deliver a universal synthetic-life OS, general autonomous intelligence,
validated training or subjective-time acceleration.

## Open and use it

**Local interface: <http://127.0.0.1:8800/>**

```sh
./scripts/run_experience_os.sh
# Separate fresh lives, if the default directory already has a running writer:
./scripts/run_experience_os.sh --port 8802 --directory /tmp/my-kalends-experiences
```

Python 3.10+ is required. The script finds the bundled Python runtime. It runs
in the foreground; keep its terminal open and use Ctrl-C to stop that server.
One directory has one server writer, guarded by a file lock. No API key or paid
inference is required. The existing built 3D client is reused; if absent:

```sh
cd kalends_3d
npm ci
npm run build
```

Four lives are installed in this checkout's new `.kalends/experience_os/`
directory: fresh `shared_observatory` and `pompeii_life`, plus copies of the
verified `observatory_long_life` and `pompeii_long_life` journals. The recorded
lives have reached their declared horizons: inspect them in LEARN or LAB.
Their canonical experiment originals remain under `results/experience_os/life_v1/`.
Installing these copies never replaces an existing different journal. A fresh
directory starts with the two source specifications only.

Suggested first five minutes:

1. Select **Shared Observatory** in LIVE. Request the systems team's report and
   confirm. Read its dated condition in your timeline.
2. Promise four units to a team. Review and commit an allocation. Nominal capacity
   is twelve; a fragile instrument executes eight, in the disclosed order A/B/C.
3. Compress one day. Actual settlement may keep or miss the promise and changes
   the recorded relationship. Available credits remain finite.
4. Enter LEARN. Read actual consequences, answer the transfer question, and
   omit an accepted allocation to execute an alternative continuation. Original
   and alternative metrics are computed; your life is preserved.
5. Enter LAB to inspect canonical truth, private minds, goals, plans and evidence.
   LAB deliberately reveals operator information; it is a local research view.

For Pompeii, select its fresh life, enter the existing 3D client, and use its own
time controls. Those actions operate the selected compiled journal. LEARN and
LAB inspect that same life. Leaving LIVE pauses its Live timer; returning reloads
the saved scene. The page refreshes after successful 3D API requests. The existing
game on port 8790 and its save remain separate.

**Compile an experience** opens an explicit LAB authoring view. Validate a
supported JSON spec, choose a new ID for changed content, then compile. Optional
draft assistance selects a supported template/objective; it cannot generate new
executable rules or replace an existing life. Default assistance is offline.

## Exact implementation inventory

| Area | Implemented behavior | Boundary |
|---|---|---|
| Continuity | Existing Ledger/WorldState, economic projection, private observation routing, exact clock; new lifecycle and structural contracts | Historical wrappers remain; no massive rewrite or alternate general state engine |
| Compiler V1 | Strict validated JSON; actor/resource/institution/action/observation/goal/time/source contracts; two executable adapters | Fixed supported identities and rules; eight concurrent local lives; not arbitrary world generation |
| Shared Observatory | Finite credits, private hardware evidence, paid inspection, source-preserving relay, team requests, promises, actual capacity allocation and delayed settlement | Authored coordination policy; fixed public execution order; no open-ended strategic negotiation model |
| Goals | Commons absolute project deadlines, prerequisite achievement, actual target quantities, active/blocked/completed/missed states; separate recurring institutional work | Pompeii spec goals are experience objectives; NPC role goals still come from the existing explicit policy bridge |
| Minds V3 | Existing AgentMind plus bounded persistent/revisable plans, admitted episodes, semantic beliefs, provenance, consolidation, social signals and host execution feedback | Default actions/options and utilities are authored; no learned general planner or live LLM cognition result |
| Six NPCs | All six newly compiled Pompeii NPCs execute bounded V3 decisions through existing purchasing/inspection/routine/communication rules | Original saves retain their prior behavioral revision |
| Time | LIVE minute reference, COMPRESS exact scheduling, SKIP target/next event, MONTAGE selection of actual allowed events; conservative cosmetic coalescing contract | No economic task was safely omitted in the measured worlds; no established adaptive speed improvement |
| Persistence | Embedded validated spec, exact accepted-command replay, metadata/hash checks, atomic trial/save/swap, authored-life restart, writer lock | Prototype journals fail closed on incompatible behavior; no arbitrary old-save migration into V3 |
| Inspection | Participant event projection; explicit LAB truth, minds and decisions; bounded source/dependency traces | Dependencies are support/accounting, not automatically necessary causes; LAB has no production multi-user authentication |
| Alternatives | Execute an omission with recorded later commands and matched time alignment; disclose infeasible continuation commands | One intervention, not an optimal alternative-life search |
| Experience Engine | Objective, actual consequences, literal feedback, debrief questions, formative transfer question and executed retry | No human learning or real-world transfer evidence |
| Optional AI | Existing provider transport/cache/budget/timeout reused for scoped intent/dialogue, template drafts, evidence selection, offered plan and literal-memory proposals | No new transport; no arbitrary factual prose accepted as truth; no direct mutation; zero live calls in this phase |
| Interfaces | LIVE/LEARN/LAB over the same runtime; retained PlayCanvas frontend for any selected supported Pompeii life | Local prototype; scene reload on mode return; not a new graphics release |

Core additions are in `kalends/experience_os/`: `contracts.py`, `compiler.py`,
`runtime.py`, `commons.py`, `minds.py`, `temporal.py`, `providers.py`, `server.py`,
the three research/demo runners and the small static host interface. Specifications
are in `specs/`. Launcher, entry point and package-data declarations were added.
README now starts with the platform demonstration. Legacy engine/frontend
sources were retained; the OS injects an external compatibility script when
serving the existing 3D HTML, without editing its bundle.

## Executed evidence

- **Cognition V2: 972 actual one-day worlds.** All 432 matched V3–V2 pairs tied
  on executed outcomes and world ledgers. Salience/goal/hybrid retention missed
  12 promises and paid 48 check credits per 108 worlds; recency/FIFO-BM25 missed
  24 and paid 60. All arms completed 252 projects. V3 added plan state and
  overhead. There is no measured V3 superiority or multi-month cognition result.
- **Temporal V2: 48 cells, 144 timed and 48 traced worlds.** Exact and conservative
  adaptive matched all 12 reference comparisons each. Naive coarse execution
  matched none, including cognitive-action divergence in all six Rebirth cells.
  Exact group median speedups were 0.998–1.139×; adaptive 0.983–1.148×. Zero
  economic coalescing means no new adaptive performance win.
- **90-day Commons life:** 360 accepted commands, 1,544 events, 228 projects,
  89 kept/one missed promise, earned membership, 48 conserved credits. Actual
  omission reduced projects to 226 and executed units from 912 to 904, with the
  original save unchanged. Days 1/30/60/90 restarted exactly.
- **120-day Pompeii life:** 12 accepted commands, 3,234 events, 720 V3 decisions,
  one missed four-flour delivery and one fulfilled 120-minute service agreement.
  Cash ended at 11; household affiliation persisted. Five checkpoints restarted
  exactly. The raw `deliveries` diagnostic counts settlement receipts, including
  missed/partial settlements; it is not a successful-delivery count.
- **Human studies:** none. The controlled active-comparison learning protocol,
  delayed-transfer endpoint and power assumptions are proposed research only.
- **Model evaluation:** offline and injected-wire fixtures only. Synthetic cost
  receipts in tests are not live API spending.

Read [RESEARCH_RESULTS.md](docs/experience_os/RESEARCH_RESULTS.md) for budgets,
operational definitions, comparison limits and raw links. Prior V1/V2 research
artifacts are retained rather than overwritten.

Reproduce in **new** output directories:

```sh
python3 -m kalends.experience_os.cognition_bench --output /tmp/kalends-cognition-recheck
python3 -m kalends.experience_os.temporal_bench --out /tmp/kalends-temporal-recheck
python3 -m kalends.experience_os.life_demo --output /tmp/kalends-life-recheck
python3 -m pytest tests -q
node --test tests/frontend/*.test.cjs
```

The local bundled runtime is Python 3.12; macOS's bare `python3` may be too old.
Set `KALENDS_PYTHON` to a Python 3.10+ executable for the launcher. The recorded
studies include source hashes/frozen archives and refuse to replace an existing
output directory. They are exploratory authored experiments, not preregistered
held-out benchmarks or independent replications.

## Compatibility and verification

**Final aggregate: 947 Python tests and 110 frontend tests passed.** This
includes the original 692 Python and 98 frontend tests. New checks cover
both adapters, private knowledge/provenance, all six minds, executed actions,
stale reviews, trial information leaks, finite accounts, exact restart, failed
save rollback, authored specifications, real HTTP, the shipped 3D bridge,
custom-life isolation, goals/deadlines/opportunities, relayed testimony,
counterfactual alignment, temporal fidelity and provider scope attacks.
The final aggregate and browser evidence are in
`results/experience_os/verification.json` and `results/experience_os/browser/`.

Four original journal SHA-256 values matched their pre-task values after the
implementation: original Rebirth, its pre-Minds-V2 backup, the user's active
Immersion life and the preserved Immersion QA life. The user life still has
416 commands through minute 16090; it was not used for this phase's QA.
The raw hashes are retained in verification rather than presented as a save
migration. Port 8801 used a separate temporary QA directory; final port 8800 uses
only the new experience directory.

Important defects found and repaired during review include inspection-result
disclosure through previews, empty-minute stale-action acceptance, action
override through the movement endpoint, unvalidated replay metadata, authored
lives disappearing on restart, ignored goal/prerequisite/opportunity fields,
testimony losing its source, raw NPC accounts in participant event projection,
and custom compiled Pompeii views addressing the wrong life. These fixes matter
more than the passing-test count. Actual browser walkthroughs verify a delayed
promise consequence, debrief, formative feedback, omission retry and the 3D
client's shared authoritative time.

Milestones include `057ac20` (authoring/minds/time studies) and `803d6dd`
(compiled lifecycle and interfaces), followed by integration/privacy/research
and handoff commits on this development branch. No PR, remote deployment,
external message, paid service or original-save migration was performed.

## Remaining work and strategic judgment

This is a real two-domain compatibility slice, with a domain-specific rules
plugin behind a shared lifecycle. A third domain still needs explicit rules,
validators, projections and fixtures; the compiler is not a universal simulator.
Plans remain short authored next steps. Multi-month execution is demonstrated;
multi-month intelligence improvement is not. Conservative temporal correctness
is useful infrastructure, while semantic abstraction with meaningful savings
remains an open problem.

The product demonstration is functional, with minimal authoring and research
interfaces. It needs independent human usability and learning studies,
production authorization/isolation, broader domain content and credible
retrieval/planning baselines before stronger platform claims. Dense retrieval,
MemoryArena/AMA/Mem2Act/Hindsight replications, an open-ended career model,
general narrative biography, VR/BCI, neurological compression, paying users and
commercial validation are not delivered.

[ARCHITECTURE.md](docs/experience_os/ARCHITECTURE.md) explains the reuse and the
remaining compatibility debt.
[COMPANY_AND_RESEARCH_THESIS.md](docs/experience_os/COMPANY_AND_RESEARCH_THESIS.md)
reviews verified primary literature, six separate businesses, cautious
neuroscience dependencies, the human protocol and the six-perspective critique.
The conditional first wedge is authoring/research or focused decision training,
subject to customer and human-outcome tests; the markets are not added together
and no valuation is treated as evidence of value.
