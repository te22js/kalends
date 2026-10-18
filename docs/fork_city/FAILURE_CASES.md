# Failure cases from the frozen ActionBench runs

**The main runs do not establish a lineage-specific regret benefit.** Better
retention of local beliefs also does not guarantee better downstream decisions.
These conclusions concern the declared grain task, costs, and operating points.

## Evidence and verification

The [main held-out artifact](../../results/fork_city/heldout/config.json) contains
2,640 worlds and 368,385 decisions: 30 paired seeds (1000–1029), four families,
populations 8/32, and eleven conditions. Each population/condition has 120 worlds.
The [population-128 artifact](../../results/fork_city/scaling128/config.json)
adds 600 worlds and 554,592 decisions across five conditions on the same seeds.
The four [sensitivity runs](../../results/fork_city/sensitivity/summary.json) each
contain 600 worlds at population 8, using the same seeds/families and five
conditions. They are correlated follow-up measurements, not additional
independent seeds.

`scripts/inspect_actionbench.py` independently recomputes recorded decision
rates and paired differences from compressed raw records. Selected case worlds
below were rerun and matched **both complete decision records and ledger hashes**.
The studied source is frozen at `ce2f2b8`; config hashes match current engine,
memory, and evaluator dependencies. The later `city_server.py` adapter differs
because of an optional inspection endpoint; `actionbench/plots.py` differs only
in plot-label layout. Neither is executed by the study runner. The helper
reports both mismatches and permits those explicit adapter/analysis exceptions
for replay; it rejects other recorded source mismatches. Plot layout was
changed after inspection, with no decision data regenerated or policy tuned.

The studied callback receives only local experiences, tick, and agent ID.
Authoritative supply and loss are attached by the engine **after** that callback;
their presence in raw decision records does not mean they were policy inputs.
Replay-inspected evidence records contain only observations/reports received by
the selected agent. Local QA uses its accepted information horizon.

Rates below are averages of four family-world rates within seed and then across
30 seeds. Intervals use paired seed differences and the artifact's approximate
95% t interval. Decisions/agents are not treated as independent samples. The
comparisons are not adjusted for multiple testing. Suite timings were collected
alongside concurrent workloads and do not support isolated performance claims.
Worlds with no reserves contribute zero to the reported selective-risk mean;
this convention makes coverage essential to interpreting that mean.

## Local QA can be right while an action is costly

In main seed **1000 / rumour / 8 / structured**, Livia's tick-2 decision **E10**
cites **E9**: Dama reports “available,” vintage 0, from harbour-manifest root E5.
The trust/freshness oracle accepts that local claim. Structured memory returns
`available`, so `qa_correct=True`, then chooses `defer`. Actual supply is
`disrupted`; the declared loss is **6**. No boundary violation occurred: the
memory faithfully preserved misleading information that genuinely reached her.

Structured and ungated guarded-hybrid attain local QA 1.0000 at both main
populations, while mean regret is **1.6107** at 8 and **1.8322** at 32. This is a
schema-assisted ceiling for retaining the supplied acceptance rule, not evidence
that the policy knows current truth. The opposite coincidence also occurs:
in seed **1000 / recovery / 8 / bm25**, Gaius's tick-2 **E15** wrongly retrieves
his private *reserve* observation E2 as supply knowledge, yet `defer` happens to
have zero loss because supply is available. World agreement does not certify
valid evidence use.

## Boundary repair need not change the action

In seed **1000 / rumour / 8 / bm25**, Gaius's tick-2 **E16** again retrieves
E2 (`grain.reserve=available`) despite having received no `grain.supply`
information. His supply answer violates the information boundary; `defer`
costs 6. Guarded lookup can correctly return `unknown`, but the ungated decision
rule also defers on `unknown`.

In the main runs, naive hybrid and guarded hybrid have **identical action,
coverage, risk, and regret rates in every paired world** at populations 8 and
32. Guarding improves QA by **2.07 percentage points** at 8 and **0.49 points** at
32, and removes their measured boundary violations. The paired regret difference
is exactly **0 [0, 0]**. This task exposes epistemic differences without making
every such difference consequential under the fixed action rule.

## Root collapse prevents some errors and withholds useful actions

These paired decisions have the same selected evidence IDs, one root label,
two immediate senders, the same disruption belief, and the same local QA label:

| Main case | Selected evidence and shared root | Source-count gate | Lineage gate |
|---|---|---|---|
| Seed 1000, recovery, 8, Julia, tick 14, E281 | E242/E268 from Livia/Sabina; root Livia E129, vintage 7; actual **available** | reserve; loss **2** | verify; loss **1.5** |
| Seed 1001, recovery, 8, Gaius, tick 14, E291 | E231/E257 from Dama/Modestus; root Julia E125, vintage 7; actual **disrupted** | reserve; loss **0** | verify; loss **1.5** |

These are mechanism illustrations, not independent efficacy samples. Counting
distinct roots changes which actions pass; a root count alone cannot establish
whether a stale report is currently true or whether inspection is worth its
cost.

Main operating points for ungated guarded-hybrid and the two threshold-2 gates:

| Population | Condition | Reserve coverage | Risk among reserves | Mean regret |
|---|---|---:|---:|---:|
| 8 | ungated guarded | 41.10% | 39.35% | 1.6107 |
| 8 | source count 2 | 27.92% | 46.29% | 1.8276 |
| 8 | lineage 2 | 24.60% | 34.39% | 1.8155 |
| 32 | ungated guarded | 42.77% | 54.08% | 1.8322 |
| 32 | source count 2 | 29.24% | 55.49% | 1.8540 |
| 32 | lineage 2 | 27.46% | 54.26% | 1.8511 |

The **source-count minus lineage regret** difference is **+0.0121
[-0.0191, +0.0433]** at 8 and **+0.0029 [-0.0082, +0.0140]** at 32. Both
intervals include zero. At 8, lineage lowers reserve coverage by 3.32 points
and reserve risk by 11.90 points relative to source count; this is a tradeoff,
not supported overall regret superiority. Relative to *ungated* guarded-hybrid,
lineage increases regret by **0.2048 [0.0512, 0.3583]** at 8.

Always-verify has zero reserve coverage and mean loss 1.5. Its zero action-error
and selective-risk values arise from the scoring definition; they do not
demonstrate autonomous task success. Each policy's prior actions also change
later inventory eligibility, so decision denominators are policy-dependent.

## Capacity changes the story

With only eight retained records, the guard can lose an accepted fact while
rejected equal-vintage repeats remain in the buffer. In sensitivity seed
**1000 / recovery / 8**, Dama's tick-11 **E168** is the first action divergence
between naive and guarded hybrid. Naive retrieval uses repeats E54/E78/E113,
all from harbour-manifest root E5, to answer `disrupted` and reserve with loss
**0**. Guarded lookup finds no surviving accepted entry, answers `unknown`, and
defers with loss **6**. Exact replay verifies both paths.

At capacity 8, **hybrid minus guarded regret = -0.2863 [-0.3940, -0.1785]**.
Guarding is worse here. Adding threshold-2 lineage verification to guarded
memory reduces regret by **0.6232 [0.4641, 0.7824]**, but source-count gating
performs similarly: **source-count minus lineage = -0.0024 [-0.0147, 0.0098]**.
This supports a capacity-dependent value of verification, not a lineage-specific
benefit.

The unlimited-capacity sensitivity reproduces all **600** corresponding main
world ledgers and decision records exactly; capacity 64 is nonbinding there.
At relay depth 1, source-count and lineage yield identical action/prediction/loss
sequences in all 120 paired worlds. At depth 6 their regret difference remains
uncertain: **+0.0133 [-0.0179, +0.0446]**. These settings provide no robust
lineage-regret advantage.

## Population 128 changes the combined gating result

At 128 agents, ungated guarded-hybrid has regret **2.0898**, reserve coverage
**41.13%**, and reserve risk **59.40%**. The lineage-2 condition has regret
**1.8854**, coverage **28.33%**, and risk **56.84%**. The paired **ungated minus
lineage-2 regret** difference is **+0.2045 [0.1023, 0.3067]**; the coverage
difference is **+12.80 [9.78, 15.81] percentage points**. The combined evidence
gate/verification policy therefore reduces this categorical loss at this
population, while withholding more actions. Its reserve risk remains high.

This scaling panel has no source-count condition, so it cannot isolate a
lineage-specific benefit. Hybrid and guarded-hybrid again have zero paired
action/regret differences, although guarding improves QA by 0.139 percentage
points. All scaling raw-rate checks passed, and one 128-agent world was replayed
exactly. Stock arrivals remain fixed per world rather than per capita, and
contacts share the same schematic locations: population changes competition
and information propagation as well as computational load. This is not a pure
runtime-scaling or realism validation.

## Post-hoc physical economy audit: task loss can disagree with delivery and cash

The [physical audit](../../results/fork_city/economy_audit.json) replays all
**1,320 eight-agent worlds already present in the main panel**. These are not
additional independent worlds. Every ledger, full decision stream, and semantic
hash matched; cash, inventory, stock, and settlement conservation checks passed.
The analysis was added after inspecting task-loss results, without changing the
studied model or policies. Its intervals remain paired across the same 30 seeds.

| Condition | Categorical regret | Final cash / agent | Actual delivery fill |
|---|---:|---:|---:|
| ungated guarded | 1.6107 | 68.76 | 65.87% |
| source count 2 | 1.8276 | 66.21 | 58.62% |
| lineage 2 | 1.8155 | 64.37 | 53.08% |
| always defer | 2.8276 | 65.80 | 16.30% |
| always verify | 1.5000 | 54.89 | 16.30% |

Source counting yields **+1.8469 [0.8855, 2.8082]** final cash per agent and
**+5.54 [3.27, 7.82] percentage points** delivery fill relative to lineage,
despite its slightly higher, statistically uncertain categorical regret.
Ungated guarded-hybrid exceeds lineage by **4.3945 [2.7908, 5.9982]** cash per
agent and **12.79 [7.15, 18.43] points** delivery fill. These physical outcomes
provide no eight-agent lineage advantage.

Always-verify receives a better categorical score than always-defer while
producing exactly the same deliveries and missed commitments. Verification
charges average **87.3 per world**, leaving **10.9125 [10.7071, 11.1179]** less
cash per agent. It gathers information but its fixed floor policy never buys.
The task-loss ranking therefore cannot be read as a welfare or delivery ranking.

There is also a scoring loophole: ungated guarded-hybrid places 2,311 purchase
orders across these worlds; **771 deliver zero units** (33.36% pooled order
share; 20.03% mean world rate). **694** are disruption reserves receiving zero
categorical loss despite procuring nothing. Nominal cash itself is not a complete
welfare measure, but these observed delivery/cash differences show why task loss
must remain separate from actual consequences. The population-128 task-score
gain above makes no claim about welfare at that population.

Reproduce with a fresh output path:
`python3 scripts/audit_city_economy.py --out /tmp/kalends-economy-replay.json`.

## Limits and reproduction

“Regret” here is the declared 2/6/1.5 categorical task loss, not financial-profit
regret. Root labels are honest simulator ancestry metadata, not authenticated
claims or proof of statistically independent witnesses. The field named
`source_independence_failure` flags reserves with enough sender labels but too
few roots; it can also flag a reserve legitimately authorized by the direct-
observation bypass. Treat it as a correlated-support diagnostic, not a measured
rate of causal misuse. A structural trace likewise does not prove necessity.

Reproduce the audit without modifying experiment files:

```bash
python3 scripts/inspect_actionbench.py results/fork_city/heldout --replay
python3 scripts/inspect_actionbench.py results/fork_city/sensitivity/capacity8 --replay
python3 scripts/inspect_actionbench.py results/fork_city/sensitivity/capacity_unlimited results/fork_city/sensitivity/depth1 results/fork_city/sensitivity/depth6
python3 scripts/inspect_actionbench.py results/fork_city/scaling128
```

The next useful experiment changes the decision model: explicitly price
information age and inspection delay, compare at matched coverage, and use
independently authored scenarios/costs. It should test when source lineage adds
value beyond a general verification policy, rather than assume that value.
