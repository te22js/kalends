# Independent Genesis results audit

**20 October 2026.** The registered lineage gate slightly reduced executed
delivery fill in the tested world distribution. It increased costly inspection
and answer coverage, while leaving answered-belief accuracy approximately
unchanged. The result supports neither a general benefit from lineage nor a
claim of a new memory architecture outperforming its baseline.

## Inputs and integrity

The audit reads the frozen [raw worlds](../../results/genesis/heldout/worlds.jsonl),
[manifest](../../results/genesis/heldout/manifest.json),
[summary](../../results/genesis/heldout/summary.json) and registered design.
It writes [independent_analysis.json](../../results/genesis/independent_analysis.json).
No raw record, runtime source, registration or original summary was changed.
This is an arithmetic/source-identity audit, not an additional experiment or a
new ledger replay.

All **22 recorded checks passed**:

- 900 unique worlds: 720 primary and 180 controls; exactly 30 seeds,
  **50000–50029**, with 30 worlds per seed and all expected cells/configurations.
- **5,288,329 events** and **779,565 decisions** reproduce the raw totals.
- The raw SHA-256 is
  `86786cdac6dd7d56268a6efdf24d6202e139532e294dde5b1b0e921851b53b1c`,
  matching the original summary.
- All **110 condition metric means/intervals**, all **24 descriptive cells**,
  the confirmatory mean/interval and every primary seed difference reproduce.
- Agent sums reconcile with world delivery quantities, cash, inspections,
  zero-fill orders and inventory-valued assets. Decision action counts reconcile.
- All **48 runtime file hashes** and the registration match recorded commit
  **`a1010fc996e5dd342fe51c481c5b732f6ca634c4`**. The runner recorded unchanged
  source at completion. Current `language.py` and `simulation.py` differ after
  the run; this audit checks the frozen commit, not current-tree replay identity.
- Recorded provider inference cost and recorded boundary violations are zero.
  These fields do not independently prove every possible information boundary.

For each primary contrast, subtract matched worlds within seed/family/population,
then average the six cells equally within each seed. Bootstrap the **30 seed
means**, 10,000 draws with `random.Random(72831)`, using sorted zero-based
indices 249 and 9749 for interval endpoints. Events, agents and decisions are
not independent uncertainty units. All secondary and control intervals below
are **descriptive, without multiplicity correction**.

## Registered contrast and descriptive outcomes

Lineage minus ungated guarded memory, averaged over three families and two
populations:

| Outcome | Paired difference | Seed-bootstrap 95% interval | Status |
|---|---:|---:|---|
| Delivered / committed units | **−0.18031 percentage points** | **[−0.25745, −0.10381] pp** | Only confirmatory contrast |
| Current-belief accuracy over recorded decisions | +1.16730 pp | [+0.97292, +1.35045] pp | Descriptive |
| Nonunknown answer coverage | +1.42832 pp | [+1.29542, +1.56197] pp | Descriptive |
| Current-belief accuracy when answered | −0.02417 pp | [−0.18713, +0.14428] pp | Descriptive |
| Inspection cost | +9.33333 denarii/world | [+8.08889, +10.56667] | Descriptive |
| Net assets, terminal unit value 1 | −13.29722 denarii/world | [−15.40000, −11.00000] | Descriptive |
| Net assets, terminal unit value 3 | −14.59722 denarii/world | [−16.77778, −12.29722] | Descriptive |
| Net assets, terminal unit value 6 | −16.54722 denarii/world | [−18.93333, −14.07222] | Descriptive |

Ungated delivery fill is **72.02765%**, versus **71.84734%** with lineage. The
absolute difference is small, although the confirmatory interval excludes zero
in the adverse direction. Average inspection cost rises from 95.82222 to
105.15556 denarii/world. These money quantities average 8- and 32-citizen worlds
equally; they are not per-citizen effects. Cash already contains purchases,
inspection fees, settlement revenue and penalties, so those costs are not
subtracted again from assets.

The current-belief rate counts unknown answers as incorrect. Its apparent gain
must be read alongside greater answer coverage and approximately unchanged
conditional accuracy. Decisions occur at policy-dependent opportunities, so
even the conditional comparison is not a common fixed set of prediction tasks.
These summaries do not isolate the causal effect of knowledge quality alone.

Local recall accuracy is **1.0** for all primary conditions, against a reference
constructed from retained accepted supply records. This is a narrow internal
reference, not a human recall test or an independent semantic judge. Accurate
agreement with local records neither establishes present-world truth nor
guarantees successful delivery.

Sender gating also reduces delivery versus ungated memory: **−0.18299 pp**
[−0.26693, −0.10369]. Lineage minus sender gating is **+0.00268 pp**
[−0.03154, +0.04487]; there is no clear delivery advantage for lineage in that
descriptive comparison. Its value-3 asset difference is −0.96389
[−2.30833, +0.43889] denarii/world. At value 6 the interval is adverse
(−1.94722 [−3.28333, −0.57500]); report valuation dependence and multiple
comparisons rather than selecting a favorable metric.

**Architecture comparison has no realized contrast:** `structured_none` and
`guarded_none` have identical world metrics, agent accounts **and ledger hashes
in all 180 matched pairs**. These tasks do not establish an advantage of guarded
retrieval over structured retrieval. Different implementations are not distinct
empirical evidence when their executed histories coincide.

## Resource, capacity and ordering controls

These controls cover only **reversal, 32 citizens, guarded ungated memory**.
The shared baseline has capacity 32, per-capita supply, seeded order and role
policies. They cannot establish robustness across all primary scenarios.

| Control minus baseline | Delivery difference, pp [95% interval] | Value-3 asset difference, denarii [95% interval] |
|---|---:|---:|
| Capacity 8 | −0.68408 [−1.09038, −0.26949] | −77.15000 [−102.78333, −51.25000] |
| Capacity 128 | +0.08706 [−0.01244, +0.19900] | +9.68333 [+3.36667, +16.73333] |
| Shared old policy | −31.31012 [−38.02239, −24.55638] | −268.50000 [−396.75000, −147.95000] |
| Fixed stock, fixed order | −51.28524 [−53.93864, −48.37479] | −296.66667 [−401.83333, −193.38333] |
| Fixed stock, seeded order | −51.29768 [−53.94279, −48.39967] | −298.20000 [−403.13333, −195.70000] |
| Per-capita stock, fixed order | −0.01244 [−0.12023, +0.09121] | −4.01667 [−9.56667, +1.36667] |

The per-capita/seeded baseline fills **77.72388%** of delivery obligations;
fixed-stock/seeded fills **26.42620%**. Thus supply assumptions dominate the
small primary gate effect in this specific control cell. Seeded minus fixed
allocation order changes aggregate delivery by −0.01244 pp
[−0.03317, +0.00415] under fixed stock and +0.01244 pp
[−0.09121, +0.12023] under per-capita stock. Aggregate invariance does not imply
the same recipients get the goods.

Capacity 8 reduces current-belief accuracy by **13.67920 pp**
[−14.68922, −12.60772] and adds **77.0** inspection denarii
[60.66667, 95.0] versus capacity 32. Capacity 128 saves **4.4** inspection
denarii [−7.26667, −1.93333], while its delivery interval includes zero.
The shared-policy control removes role-specific behavior and switches to an
older decision strategy; it is a broad strategy comparison, not an isolated
proof that biography or heterogeneous goals cause the delivery difference.

## Exploratory distribution check

**Unregistered post-result analysis:** group the first and last eight citizens
in the fixed agent list and compare their delivered/committed units. At population
32 these groups repeat the same coded role pattern, but identities and privileged
observation routes differ. They are not randomized exchangeable human groups.

| Supply / allocation | First eight fill | Last eight fill | First-minus-last gap |
|---|---:|---:|---:|
| Fixed / fixed | 37.25490% | 9.03595% | +28.21895 pp |
| Fixed / seeded | 23.15359% | 23.34967% | −0.19608 pp |
| Per capita / fixed | 77.56536% | 73.13725% | +4.42810 pp |
| Per capita / seeded | 75.93137% | 76.32353% | −0.39216 pp |

Under fixed supply, changing to seeded order reduces this group gap by
**28.41503 pp [26.79739, 30.03268]**, despite almost unchanged aggregate fill.
Under per-capita supply the reduction is **4.82026 pp [3.49673, 6.24183]**.
This is a concrete distributional warning about reporting district totals alone.
It is not a preregistered fairness result, a theorem about seeded allocation,
or an estimate for arbitrary group definitions. Replicate with prospectively
chosen groups/inequality measures and additional resource settings before a
general claim.

## Reproducing the core arithmetic

From the repository root, this independently recomputes the principal effect and
key descriptive contrasts directly from raw records, without importing the
experiment runner or executing new worlds:

```sh
python3 - <<'PY'
import json, random, statistics as st
from pathlib import Path
rows = [json.loads(x) for x in Path('results/genesis/heldout/worlds.jsonl').read_text().splitlines()]
index = {(r['config']['seed'], r['condition'], r['config']['family'], r['config']['n_agents']): r
         for r in rows if r['track'] == 'primary'}
for metric in ('delivery_fill_rate', 'belief_current_accuracy', 'answer_coverage',
               'belief_accuracy_when_answered', 'inspection_cost',
               'asset_value_1', 'net_asset_change', 'asset_value_6'):
    values = [st.fmean(index[s, 'guarded_lineage', f, p]['metrics'][metric] -
                      index[s, 'guarded_none', f, p]['metrics'][metric]
                      for f in ('stable', 'reversal', 'scarcity') for p in (8, 32))
              for s in range(50000, 50030)]
    rng = random.Random(72831)
    draws = sorted(st.fmean(rng.choices(values, k=30)) for _ in range(10000))
    print(metric, st.fmean(values), [draws[249], draws[9749]])
PY
```

The JSON artifact retains per-seed values for every reported primary/control
contrast and exploratory grouping, hashes, units and audit checks. No additional
independent worlds were created. Frozen source identity and correct arithmetic
do not establish human realism, useful entertainment, economic optimality,
causal necessity of individual trace edges, or commercial demand. The strongest
supported research conclusion is bounded: **in this registered synthetic setting,
additional evidence gating slightly worsened delivery; coverage and information
scores alone would have given an incomplete account of its executed costs.**
