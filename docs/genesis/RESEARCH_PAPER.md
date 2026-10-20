# A Small Adverse Effect of Evidence Gating on Executed Deliveries in a Bounded Multi-Agent Economy

**Kalends: Genesis — paper-style research draft, 20 October 2026.**
Simulation case study; not peer reviewed. No human-user or commercial validation.

## Abstract

We study evidence admission in a deterministic society with private information,
bounded memory, costly inspection and actual resource settlement. A repository
preregistration specifies 30 fresh seeds, three supply regimes, two populations
and four policies, plus resource, capacity and strategy controls: 900 worlds in
total. The confirmatory lineage-minus-ungated contrast reduces delivered contract
units by **0.1803 percentage points**, 95% paired seed-bootstrap interval
**[−0.2575, −0.1038]**. Inspection spending and answer coverage increase, while
accuracy among answered beliefs is approximately unchanged. Structured and
guarded memory produce identical histories in every matched comparison.
Resource controls produce much larger delivery differences; exploratory
allocation diagnostics reveal distribution changes hidden by aggregate totals.
The contribution is a reproducible, bounded negative result and measurement
audit, not a new discovery that memory fidelity differs from useful action.

## 1. Question and prior work

When does admitting information using distinct declared source roots improve
executed outcomes once verification consumes money and time? We test a specific
gate inside a combined role policy, rather than assuming provenance is useful
because it appears epistemically desirable.

Close prior art rules out broad novelty claims. **Generative Agents** already
combines memory, planning and social diffusion in a structured town; language is
grounded in its environment, rather than universally defining reality
([Park et al., 2023, §5.1](https://arxiv.org/html/2304.03442)).
**AgentSociety** supplies constrained social/economic environments and intervention
experiments ([Piao et al., 2025/2026](https://arxiv.org/html/2502.08691));
**AgentSociety 2** integrates executable research workflows, configurable
environments and inspectable artifacts
([Piao et al., 2026](https://arxiv.org/html/2607.11895)).

**STATE-Bench** uses downstream task/state checks
([Microsoft, 19 May 2026](https://github.com/microsoft/STATE-Bench));
**τ-bench** evaluates completed database states and repeated-run reliability
([Yao et al., 2024](https://arxiv.org/html/2406.12045)).
**CPB**, whose actual title is *A Benchmark and Diagnostic Study of Epistemic
Admission in Shared Agent Memory*, studies correlated support, admission,
coverage and downstream adoption
([Li et al., 25 September 2026](https://arxiv.org/html/2609.30813v1)).
**MemoryArena** already separates retention from successful use, including an
approximate-oracle memory experiment
([He et al., September 2026 revision, appendix C.3](https://arxiv.org/html/2602.16313v2)).
**LongMemEval-V2** deliberately isolates bounded evidence gathering for a fixed
reader rather than live task execution
([Wu et al., May 2026, appendix E](https://arxiv.org/html/2605.12493v1)).

**CivWorldBench** establishes scoped observations, engine-grounded truth and
paired interventions in structured multi-agent worlds
([Li et al., 12 October 2026](https://arxiv.org/html/2610.16450v1)).
Static selective-classification risk–coverage concepts
([Geifman and El-Yaniv, 2017](https://arxiv.org/abs/1705.08500)) do not directly
guarantee outcomes when verification changes future information and opportunities.
Our narrower distinction is explicit executed-outcome accounting under bounded
transmission and resource controls. The dated
[novelty audit](RESEARCH_NOVELTY_AUDIT.md) gives methods, baselines, limitations
and bibliographic discrepancies; these preprints and releases are not evidence
of Kalends' superiority.

## 2. World, agents and measurements

Let authoritative state $S_t$ contain locations, shipment state, stock, prices,
accounts, commitments and institutional trust. Valid events update this state
and enter an append-only ledger. Agent $i$ acts from its retained experiences
$M_{i,t}$ and authorized owned-account view, not evaluator truth. Its action
changes executed resources and therefore later opportunities. Archived events
remain available to audit, separately from operational memory.

The 96-tick economy has one good. Citizen obligations settle at ticks
7, 15, …, 95, with role-specific quantities. Producers procure early, traders
maintain a speculative buffer, merchants use caution, couriers share more
readily, and officials inspect periodically. Urgent procurement can override
evidence gating. These are coded strategies, not learned rational agents.

Three regimes are stable supply, reversals and scarcity. Arrival/price draws
use seed/tick keys independent of policy execution. At each eight-tick arrival,
per-capita stock adds `ceil(2.6N)` units when available and `ceil(0.7N)` when
disrupted. Fixed-stock controls add 22 or 6. Seeded allocation orders purchase
opportunities using keyed draws; it does not guarantee general fairness.

All acceptance, belief, gossip and decision access uses the same FIFO memory
budget, normally 32 experiences. Retractions occupy slots; eviction can remove
their effect. Gossip carries retained root metadata and bounded relay depth.
An opening delayed claim derives from a genuine tick-0 observation and arrives
at tick 6, after the reversal at tick 4. An outdated truthful report is therefore
distinguishable from an invented historical source.

Inspection costs **2 denarii**, with private results next tick. It may also read
at most two dated dispatch records within an eight-tick window for remembered
claims. Those are explicit new observations, not free archive recovery. Current
disagreement alone does not prove an earlier claim false. Accounts and trust
persist independently of episodic recall.

We separate five measurement layers:

1. **Local recall:** selected value versus the latest accepted retained supply
   record after retained retractions.
2. **Current belief:** prediction versus evaluator supply, including answer
   coverage and accuracy conditional on a nonunknown answer.
3. **Actions:** reserve, verify or defer, with locally available evidence.
4. **Execution:** attempted/filled purchases and delivered obligations.
5. **Valuation:** cash and inventory changes under disclosed weights.

Primary delivery fill is
$F=\sum_i\text{delivered}_i/\sum_i\text{settled committed}_i$.
The citizen denominator is scheduled independently of treatment success;
player contracts are separate. Secondary net assets are
$U_v=\sum_i[\Delta C_i+v\Delta I_i]$, for registered values $v=1,3,6$.
Cash already includes purchase costs, inspection fees, revenue and penalties;
adding these again would double-count. Zero-fill orders receive no inventory
or purchase-cash reward. Debt-producing penalties and external settlement
payments are allowed. Neither $F$ nor $U_v$ is societal welfare or optimal-policy
regret; no optimal counterfactual policy is computed.

![Measurement layers remain distinct.](/Users/tanmaygoswami/Claude_backup/Projects/kalends/results/genesis/figures/04_measurement_layers.png)

*Figure 4. Diagnostic memory/belief measures and physical/economic outcomes must
be interpreted separately; correctness at one layer does not establish another.*

## 3. Registered design and inference

The [registration](../../results/genesis/preregistration.json) and runtime were
committed at **`a1010fc996e5dd342fe51c481c5b732f6ca634c4`** before held-out
execution. Reserved development seeds are 20000–20009; the development runner
uses the first two. Held-out seeds **50000–50029** were not used in the prior
Fork the City study. Historical categorical losses are not pooled with this data.

The primary design is 30 seeds × three regimes × populations 8/32 × four
conditions = **720 worlds**: structured memory without a gate, guarded memory
without a gate, guarded sender-count gating, and guarded root-count gating.
Threshold is two. Direct observations pass admission. Sender and root gates
share a root-informed confidence rule: the sender comparator is not entirely
provenance-blind. Root identifiers denote declared derivation, not authenticated
or statistically independent witnesses.

The sole confirmatory hypothesis is improved delivery under root gating versus
ungated guarded memory. Pair within seed/regime/population, average six cell
differences equally within seed, then bootstrap the **30 seed means** 10,000
times with seed 72831. Report two-sided percentile intervals. This estimates an
equally weighted six-cell average, not a pooled per-citizen effect. Events,
decisions and agents are not independent samples.

Another **180 worlds** cover capacity 8/128, a shared older strategy, and a
complete fixed/per-capita × fixed/seeded stock/allocation control, sharing the
primary reversal/32/ungated baseline. Controls, cell estimates, asset valuations
and all secondary intervals are descriptive without multiplicity correction.
The resource panel does not cross resource settings with every gate; it cannot
identify a general resource-by-gate interaction.

## 4. Results

The completed run contains **900 worlds, 5,288,329 events and 779,565 decisions**.
Wall time was **481.404 seconds with four workers** and **$0 provider inference**.
Concurrent execution and machine conditions prevent treating this as an isolated
performance benchmark. An independent audit reproduced 110 condition
mean/interval pairs, 24 descriptive cells, all primary seed differences, account
sums and raw/source hashes; see [RESULTS_AUDIT.md](RESULTS_AUDIT.md).

### 4.1 Small adverse confirmatory effect

Ungated fill is **72.02765%**; root-gated fill is **71.84734%**. Their paired
difference is **−0.18031 percentage points [−0.25745, −0.10381]**. The interval
excludes zero in the adverse direction: the hypothesized delivery benefit is
not supported. Magnitude is small, and descriptive cell effects are heterogeneous.

![Executed delivery means.](/Users/tanmaygoswami/Claude_backup/Projects/kalends/results/genesis/figures/01_primary_delivery.png)

*Figure 1. Seed-cluster intervals for policy means. Truncated axis resolves small
differences; overlapping marginal intervals do not replace the paired test.*

![Paired root-gate effect.](/Users/tanmaygoswami/Claude_backup/Projects/kalends/results/genesis/figures/02_paired_effect.png)

*Figure 2. One mean contrast per independent seed; shading is the bootstrap
interval for the average, not an interval across independent decisions.*

### 4.2 Coverage, precision and executed cost

| Root gate minus ungated | Difference | Descriptive 95% interval |
|---|---:|---:|
| Current-belief accuracy | +1.16730 pp | [+0.97292, +1.35045] |
| Answer coverage | +1.42832 pp | [+1.29542, +1.56197] |
| Accuracy when answered | −0.02417 pp | [−0.18713, +0.14428] |
| Inspection cost / world | +9.33333 denarii | [+8.08889, +10.56667] |
| Net assets, value 1 | −13.29722 denarii | [−15.40000, −11.00000] |
| Net assets, value 3 | −14.59722 denarii | [−16.77778, −12.29722] |
| Net assets, value 6 | −16.54722 denarii | [−18.93333, −14.07222] |

Unknown predictions count as incorrect in the unconditional belief rate. Greater
coverage accompanies that rate's improvement; answered precision is effectively
unchanged. Opportunity sets also change with inventory and official duties, so
these are not causal accuracy comparisons on identical prediction cases.
Currency effects average whole 8- and 32-citizen worlds equally, not individuals.

Sender gating also lowers fill versus ungated memory, by **−0.18299 pp
[−0.26693, −0.10369]**. Root minus sender gating is **+0.00268 pp
[−0.03154, +0.04487]**, with no clear delivery advantage. Valuation can change
secondary comparisons: root-minus-sender assets have an interval including zero
at value 3 but an adverse interval at value 6. No preferred valuation is selected
after examining results.

### 4.3 Negative architecture result and recall ceiling

Local recall is **100%** across primary conditions against the canonical
retained-record reference. This ceiling is partly built into matching exact
proposition keys; it is not evidence of difficult semantic recall or broad
memory competence. More decisively, structured ungated and guarded ungated
memory have **identical metrics, agent accounts and ledger hashes in all 180
matched pairs**. This study realizes no architecture contrast between them.
An architectural superiority claim would be unsupported.

### 4.4 Controls and exploratory allocation distribution

At reversal/32, per-capita/seeded fill is **77.72388%**, versus **26.42620%**
with fixed stock/seeded order: paired difference **−51.29768 pp
[−53.94279, −48.39967]**. This resource manipulation dominates the small gate
effect in that cell. Capacity 8 versus 32 reduces fill **0.68408 pp
[0.26949, 1.09038]** and adds **77.0 [60.66667, 95.0]** inspection denarii.
Capacity 128 saves inspection costs, but its delivery interval includes zero.
The older shared-policy comparison changes an entire strategy, not just roles.

![Resource and ordering controls.](/Users/tanmaygoswami/Claude_backup/Projects/kalends/results/genesis/figures/03_resource_controls.png)

*Figure 3. Restricted control panel: reversal, 32 citizens, ungated guarded
memory. Its intervals are descriptive; it is not a population-wide robustness test.*

Seeded versus fixed ordering barely changes aggregate fill. An **unregistered
exploratory** grouping nevertheless shows redistribution: under fixed supply,
first-eight versus last-eight fill is 37.25490% versus 9.03595% with fixed order,
and 23.15359% versus 23.34967% with seeded order. The group-gap reduction is
**28.41503 pp [26.79739, 30.03268]**. These groups repeat the same coded role
pattern but have different identities/observation routes. This illustrates a
distributional artifact hidden by totals; it is not a general fairness theorem
or a preregistered group-effect discovery.

## 5. Causal checks, failures and validity

Identity reruns, source-removal forks and paid inspection tests support internal
execution checks. In a separate **development-only** 50-run routing panel,
equivalent paid-Livia request routes match ledger, decisions and outcomes for
all ten seeds. Free immediate operator, delayed paid citizen and paid player
observations differ in recipient, timing or information; their differences are
not isolated verification-price effects. They are not additional held-out seeds.

Recorded parent edges establish structural dependency, not causal necessity,
sufficiency or unique attribution. Branches test a specified changed input while
retaining subsequent accepted player commands; they do not simulate how a human
would adapt. No complete formal actual-causation procedure is claimed.

The study is a repository preregistration, not a third-party registered blind
trial. Thirty seeds quantify variability within a designed deterministic
generator. One good, exogenous prices, simplified contracts, debt, coded trust,
FIFO count budgets and privileged dated dispatch access limit external validity.
Penalty/payment weights are design choices, not calibrated economic utility.
Shared root-informed confidence and urgency overrides limit what can be inferred
about admission mechanisms. Forgotten retractions and relationship explanations
are genuine limitations of bounded memory. Synthetic correctness is not human
behavioral realism.

The frozen study remains **a1010fc**. Later product changes improve language
grounding and add auditor-only settlement accounting links; they are not policy
retuning and were not used to regenerate these raw results. Current product
source therefore differs from the study snapshot. Any claimed behavioral
equivalence requires its separate explicit check; full ledger hashes may differ
because accounting annotations differ. No inference about untested LLM dialogue,
human retention, creator demand or hosted performance follows from this paper.

## 6. Reproducibility and next experiments

The manifest includes all 48 Python runtime hashes, registration, commit and
worker count. Raw SHA-256 is
`86786cdac6dd7d56268a6efdf24d6202e139532e294dde5b1b0e921851b53b1c`.
The independent analysis stores per-seed contrasts and verification checks.
Figures reside under `results/genesis/figures/01_primary_delivery.png`,
`02_paired_effect.png`, `03_resource_controls.png` and `04_measurement_layers.png`.

Re-execute the frozen study in a separate clean checkout and fresh output path;
do not overwrite historical artifacts:

```sh
git worktree add --detach /tmp/kalends-genesis-a1010fc a1010fc
cd /tmp/kalends-genesis-a1010fc
python3 -m kalends.genesis.bench --phase heldout --jobs 4 --output /tmp/kalends-genesis-reproduction
```

The output directory must be absent or empty. Wall times and raw line order may
differ under multiprocessing; compare configs, world/ledger outcomes and sorted
summaries rather than assuming the entire raw file must hash identically.
[RESULTS_AUDIT.md](RESULTS_AUDIT.md) provides a raw-only arithmetic reproduction.

Future confirmatory work should introduce semantic/temporal tasks that actually
separate architectures, cross gating with resource/cost settings, prospectively
define allocation inequality, and compare verification strategies at matched
information/cost budgets. New hypotheses require new held-out seeds. External
play tests must separately test comprehension, enjoyment and voluntary return.
The present evidence warrants a narrow conclusion: **this evidence gate slightly
worsens executed delivery, and attractive information diagnostics alone conceal
important costs and distributional consequences.**
