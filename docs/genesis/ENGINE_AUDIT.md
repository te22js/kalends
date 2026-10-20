# Genesis engine and execution audit

## Scope and version boundary

The prospective engine and held-out study were frozen at `a1010fc`. Historical
Fork the City code/results are preserved. This audit does not retune policies,
prices, resource rates, terminal values, gates or thresholds after the study.

Two delivery improvements were authorized after the run completed:

1. Auditor-only settlement dependency metadata in `GenesisSimulation._emit`.
2. The separately owned dialogue adapter's Player-specific trust-evidence filter.

The first changes ledger payloads/hashes but adds no world events, costs,
observations, decisions, random draws or operational memory reads. Frozen raw
results must continue to be identified with `a1010fc`; post-study implementation
hashes are not interchangeable with their hashes. Separate outcome-equivalence
verification is required when attributing the new trace instrumentation.

This audit exercised development seeds only. It does not use held-out outcomes
to choose a mechanism or policy.

## Verified event-sourced execution

`GenesisSimulation` subclasses the prior `CitySimulation`, reusing Ledger,
WorldEvent, WorldState, Experience, AgentSpec, observation rules and keyed RNG.
`GenesisEconomy` adds replay of explicit player agreement creation to the
historical cash/inventory/market/commitment projection.

A development scenario at seed 20000/horizon24 performed, in order:

- Three opening ticks.
- Player buys two grain from the market.
- Player sells one to Livia.
- Player promises two to Livia at tick7.
- Player claims supply is disrupted at tick2.
- A paid Livia inspection is booked, then the world runs to the horizon.

Observed accounting checks after post-study trace instrumentation:

| Check | Actual result |
|---|---|
| Ledger/event IDs |456 events, IDs exactly match append indices|
| Citizen decisions |65|
| Parent references |All integer, prior to child, sorted and unique|
| Economy replay |Cash, inventory, stock, price, commitments and relationships identical|
| World replay |Facts, positions, tick and trust identical|
| Bilateral transfer conservation |Both the spot trade and player contract settlement conserve combined cash and grain|
| Player promise |One of two promised units delivered; one missing unit recorded|
| Livia's Player trust |0.32 after a dated contradiction|
| Settlement links |25 settlements, none with an empty parent list after instrumentation|

World replay folds `apply_event` and the explicit `relationship_updates` payload
field. The generic historical `apply_event` alone does not project trust; the
Genesis live emitter and the audit both apply those recorded updates.

Market arrivals and external delivery payments/penalties are modeled external
flows. The town is an open accounting system, not a closed cash/grain economy.
Bilateral player transactions, in contrast, have zero-sum transfer payloads.
A market order filled at zero changes neither the buyer's cash nor inventory;
there is no old categorical reserve reward.

## Settlement dependency repair

In the frozen implementation, recurring citizen contracts were initialized
without an agreement event ID. Their settlements therefore had no structural
parents. Player settlements linked their agreement but omitted inventory
acquisition. Physical execution and measured outcomes were still represented;
the explanation graph could not connect those outcomes to procurement.

Post-study accounting links now include:

- Opening account event0 and the previous own settlement checkpoint.
- The actual agreement, when a player contract has one.
- Own inventory-delta events since the checkpoint, including attempted zero-fill
  orders and incoming/outgoing transfers.
- Own cash-delta events and recorded procurement decisions in that period.

A previous checkpoint preserves the account-state chain for carried inventory.
Each settlement records its inventory immediately before consumption. The
metadata explicitly says grain is pooled/fungible, with no unit-level FIFO
ownership attribution. These are account dependencies and recorded choices,
**not a minimal cause set or proof that any individual parent was necessary**.
Competition can produce large transitive graphs through shared market stock.
The metadata is auditor-only; it is never returned to an agent as forgotten
knowledge or used to choose an action.

## Bounded information and privacy

- `remembered(agent)` is the sole FIFO record store available to decisions,
  current knowledge, gossip, relationship assessment, receipts and dialogue
  views. Its cap includes routine movements, quote reads and action receipts.
- Core episodic/epistemic archives remain unbounded for audit, but their beliefs
  do not feed operational acceptance or gossip.
- Gossip depth is carried in retained message text. Send deduplication uses
  retained receipts, rather than an unbounded history of sent roots.
- A retraction occupies a normal memory slot and suppresses its
  `(root_event, originating_observer)` lineage. It can itself be forgotten.
  The same physical event observed by another witness is not withdrawn by
  retracting only one witness's account.
- Durable trust, owned accounts and outstanding agreements are institutional
  state. They can outlive the episode explaining them; they are not permission
  to recover that episode from the audit archive.
- Participant snapshots omit other citizens' private memories, accounts,
  preferences and decisions, and expose only player-related pending messages.
  Operator mode is explicitly separate. NPC dialogue receives the selected
  NPC's bounded private view; it does not receive world supply truth.
- The server filters player trace ancestry to accessible or explicitly
  disclosed events. Operator accounting parents do not authorize disclosure.

An actual three-day development return illustrates the retention limit. At
seed2026, opening tick2, Player makes a false supply claim to Livia and advances
72 ticks. Trust remains0.32/access refused at tick74. Capacity32 no longer
retains the explaining Player episode; capacity128 still retains assessmentE80
at tick5. These are declared demonstration settings, not evidence that capacity128
is optimal. The initial dialogue filter wrongly selected unrelated records
containing the word `trust`; the parent-owned post-study fix restricts evidence
to Player-specific records. A citizen that has forgotten the reason must say so.

## Information integrity and inspections

The reversal scenario's delayed report is sourced from Dama's real tick0
observation, queued at that time and delivered at tick6 after the tick4 reversal.
It is genuinely outdated rather than a fabricated false manifest.

An old claim disagreeing with a current observation does not establish that the
claim was false at its stated date. Assessments distinguish `outdated`,
`truthful_outdated`, `confirmed`, `contradicted`, `incomplete` and historical
uncertainty. Unknown/incomplete claims are not punished as false.

Ordinary inspections cost2 and arrive the next tick. A visit can inspect at most
two actual dated dispatch records, restricted to recent claims still remembered
at arrival and an eight-tick lookback. These are new paid world observations,
with `record_as_of` and physical source-event parents; they do not restore a
forgotten NPC episode. Repeated assessments are suppressed while the relevant
assessment receipt remains retained. Once that receipt is forgotten, later
reassessment is possible; there is deliberately no permanent hidden tombstone.

Free immediate operator inspection is useful for exploration but differs from
ordinary inspection in time, cost and possibly information recipient. It is not
a fair verification-policy baseline.

## Development verification controls

Actual records: `results/genesis/verification_controls.json`.

All conditions begin from each seed20000..20009's identical completed-tick2
prefix and run the default eight-citizen reversal world through96 ticks. No
additional misinformation is injected in this control. There are40 principal
condition records plus10 duplicate paid-citizen request-routing controls.
The artifact was produced before the post-study trace change and includes
frozen engine source hashes, prefix hashes, fees, recipients, observation ticks,
full executed per-agent metrics and final ledger/decision hashes.

| Condition | Initial information recipient | Added request cost | Observation | Mean citizen delivery fill | Mean citizen asset change |
|---|---|---:|---:|---:|---:|
| Identity |None added|0|—|0.746569|-855.9|
| Free operator inspection |Livia|0|Tick2|0.746569|-855.9|
| Paid citizen inspection |Livia|2 paid by Livia|Tick3|0.744118|-858.4|
| Paid participant inspection |Player|2 paid by Player|Tick3|0.746569|-855.9|
| Replayed paid citizen request |Livia|2 paid by Livia|Tick3|0.744118|-858.4|

The two paid-Livia routes call the same engine-validated `inspect('Livia')`
operation from the same prefix. All10 pairs have identical ledgers, decisions
and executed outcomes. This is a routing identity control, not a comparison of
two different decision policies. It does not grant Player authority to spend a
citizen's budget through the player-language interface.

Free operator inspection and paid Player inspection leave citizen aggregate
outcomes unchanged in these10 examples. Paid Livia inspection changes delivery
fill in3 seeds and net assets in7. These are development observations, not a
population-level causal generalization. Subsequent inspection behavior is
endogenous: the mean citizen inspection-cost increment is1.4 rather than the
initial2 request fee. The Player track costs Player exactly2 on average and does
not automatically communicate its result to citizens. Recipient, timing,
location and resources differ across the operator/participant tracks, so those
comparisons do **not** isolate verification cost. No optimal regret is claimed.

Reproduction recipe: for each declared seed, construct
`GenesisSimulation(GenesisConfig(seed=seed)).step(3)`, copy that completed-tick2
state, perform the named operation, then `.run()` and `.metrics()`. For frozen
ledger hashes use the `a1010fc` implementation; current accounting metadata
changes the hashes. Use a new output path rather than overwriting this artifact.

## Verified limitations and remaining defects

1. **Simple strategies and economy.** Roles differ materially, but remain coded
   heuristics rather than economically optimal agents. Supply/price processes,
   delivery values and penalties are synthetic and exogenous. No optimal-policy
   counterfactual is calculated; asset change is not regret.
2. **Ordering controls, not guaranteed equity.** Seeded permutations remove the
   same fixed winner order; rotating order is another control. Neither proves
   equitable realized allocation, especially with heterogeneous needs and cash.
   Per-capita supply normalizes stock against population, not precisely against
   every changing role's demand.
3. **Financial simplification.** Delivery penalties can create negative cash;
   there is no explicit credit limit, bankruptcy court, interest or debt recovery
   system. Immediate voluntary purchases/trades validate affordability.
4. **Agreement scope.** Player agreements promise future delivery. Counterparty
   affordability is checked at creation, without escrow; later automatic
   settlement may debit a counterparty whose cash has since changed. This is
   implicit settlement credit, not a realistic collateral system. In a concrete
   development reproduction (seed20000/opening tick2), Livia starts with111 cash;
   Player buys six grain, promises six at tick95, and later delivers all six.
   Settlement debits Livia24 even though her final cash is-89.5. The town's
   minimum final cash is-104 in that scenario. No lender/credit limit is modeled.
5. **Procurement metric scope.** `purchase_filled` counts market and spot player
   purchases. Inventory received from fulfilled player promises is represented
   in transfer/settlement events and delivery fields, not additionally counted as
   a spot purchase. It is not a count of every possible inventory inflow.
6. **Communication abstraction.** Selected-character speech and bilateral
   player transactions can address remote characters without a simulated travel
   delay. NPC gossip and the genuine prehistory report use queues. The current
   interface is not a full spatial logistics game.
7. **Attribution scope.** Reputation assesses remembered immediate speakers.
   A relayed claim can affect the relay's trust; the model does not universally
   assign ultimate-origin liability or cryptographically authenticate roots.
8. **Archives are not a checkpoint loader.** Physical projections replay from
   ledger effects; complete simulation restart uses the accepted command journal
   and deterministic policy replay. There is no generic arbitrary-ledger loader
   reconstructing every queue, retained-memory buffer and edited preference.
9. **Archive-only retraction typing defect (unfixed).** `_hear` archives a
   retraction in `epistemic[agent].exposures['grain.retraction']`, but its
   `Exposure.prop` is constructed with `SUPPLY`, so `prop.key` reads
   `grain.supply`. The retained `Experience.predicate == 'retraction'` is correct;
   operational knowledge and tombstone filtering do not consult the faulty
   archival property. Do not use that archival field as a retraction oracle.
10. **Trace limits.** Accounting graph links are not causal necessity. Generic
    non-decision semantic keys need not be unique; event IDs are the indexed
    authoritative identity. The historical city's exact single-message checker
    is not automatically a general Genesis intervention verifier.

Minimal reproduction of the archive-only typing defect:

```python
from kalends.genesis import GenesisSimulation
s = GenesisSimulation().step(3)
e = s.inject_claim('Livia', 'disrupted')
s.retract('Livia', e['event_id'])
x = s.epistemic['Livia'].exposures['grain.retraction'][-1]
assert x.prop.key == 'grain.supply'  # archival mismatch, not a memory retrieval
assert s.knowledge('Livia')['grain.supply']['value'] != 'disrupted'
```

## Validation commands

```bash
python3 -m pytest -q tests/test_genesis_engine.py
python3 -m pytest -q tests/test_genesis_language.py tests/test_genesis_server.py
```

The engine-only run after accounting instrumentation passed **35 tests**. The
additional tests require price/purchase/decision ancestry, previous checkpoints,
valid indexed parents, actual player agreements, conserved bilateral settlement
and explicit fungible-stock/non-necessity labeling. The broader HTTP suite should
run in a host environment allowed to bind loopback sockets; no sandbox socket
failure should be reported as an engine assertion failure.

Outcome-equivalence checks against frozen code must compare physical projections,
retained experiences, decisions and executed metrics, while allowing only the
new settlement ancestry fields to differ. A changed full ledger hash alone is
expected after adding this metadata; silently substituting it into a frozen raw
artifact is not permitted.
