# Kalends: Genesis — The City That Remembers You

**Implementation inventory and product direction, 20 October 2026.** The promise
is: **enter a world, change something, leave, return, and discover a consequence
you can investigate**. The present proof is a local Roman grain district with
bounded characters, executed transactions, relationship changes and replayable
alternative histories. Its entertainment value and commercial demand remain
untested. No external user study is claimed.

## The experience we are testing

A visitor can tell a merchant a supply claim, buy grain, accept a delivery
obligation or pay to inspect a report. The recipient retains a private record;
the claim may travel through ordinary communication. Characters combine the
information they retain with different resource needs and role strategies.
Deliveries settle, cash and inventories change, and an inspected false claim can
damage trust and close later commercial access. Returning to the character can
expose what they still remember, including an honest inability to explain a
durable relationship after its supporting memory has been evicted.

This is a small designed system. The long-term ambition is a broader medium of
coherent worlds, but an event ledger alone does not supply drama, attachment or
reasons to return. A player should care about the outcome before caring about
the implementation. The initial product hypothesis is an authored social and
economic simulation game, with outside authoring tools conditional on player
evidence. See [COMPANY_THESIS.md](COMPANY_THESIS.md).

## What is implemented

This inventory reflects the inspected Genesis source and targeted automated
checks, not a claim that every advertised long-term feature exists. The tested
scope is described below; exact frozen commits, full-suite results, browser
captures and experiment outputs belong in the final sprint handoff.

| Capability | Present implementation and boundary | Evidence |
|---|---|---|
| Authoritative world | `GenesisSimulation` extends the existing event-sourced city, ledger, state and economy. Purchases, inspections, settlement and trust changes execute as events. | `kalends/genesis/simulation.py`; economy replay and transaction tests |
| Distinct characters | Role preferences alter procurement timing, caution, speculation, sharing and inspection duties. Merchants, producers, traders, couriers and the official have different strategies and initial resources. | `policy.py`; preference-change and role-action tests |
| Bounded information | Decisions, acceptance, dialogue and gossip read FIFO-retained experiences with a declared count capacity. The archival history remains available to evaluation/operator inspection. Owned accounts and institutional relationship state persist separately. | `simulation.py`, `policy.py`; eviction and gossip tests |
| Historical reports and corrections | A delayed report derives from a genuine earlier shipment observation. Timestamped claims can become outdated; retractions travel and consume memory slots. Paid inspection can inspect a limited number of recent dated dispatch records. | genuine-prehistory, retraction and dated-inspection tests |
| Player language | An offline grammar proposes a limited action schema; the user reviews the recipient and transmitted action, then confirms. Ambiguous supply alternatives request a choice. | `language.py`, `server.py`; proposal/confirmation tests |
| Grounded dialogue | Questions render the character's retained information or own account state. Evidence IDs must be accessible; custom adapter replies are rendered through the same bounded factual renderer. | dialogue forgetting, adapter authority and evidence tests |
| Ordinary verification | A participant pays 2 denarii and receives an inspection next tick. It is private until shared. An immediate operator correction is separately labelled and privileged. | cost/delay and operator-separation tests |
| Economic and social consequences | Actual fills, delivery settlement, cash, inventory, trust and access are recorded. A contradicted player claim can close that recipient's commerce to the player. | false-claim/access, trade and contract tests |
| Alternative histories | Research mode can rerun accepted commands from the same seed, omit a selected historical player claim, add an operator correction or run an identity control. Original and branch remain separately inspectable. | historical-fork, identity and persistence tests |
| Evidence inspection | Player traces expose witnessed/cited evidence; Research mode exposes privileged ancestry. The interface distinguishes chronology, structural dependencies and intervention evidence. | `server.py`, static UI; permission/trace tests |
| Persistence and elapsed time | Versioned command journal, proposals and dialogue survive normal server restart. “Return after three days” executes up to 72 simulated ticks, bounded by the chapter horizon. | restart and actual-elapsed-time tests |
| Local interface | A schematic 2D town, moving character markers, conversation confirmation, journal, evidence dialog, operator tools and side-by-side executed-world comparison. | `static/index.html`, `app.js`, `style.css`; visual assessment belongs to browser captures |

The targeted command below passed **47 tests** during this inventory check. This
is a scoped engineering check, not human evaluation or a report of the final
complete suite:

```sh
python3 -m pytest -q tests/test_genesis_language.py tests/test_genesis_server.py tests/test_genesis_engine.py
```

## An honest six-act demonstration

1. **Enter the district.** A new session deterministically advances the opening
   three ticks before showing the town. Characters move on role schedules;
   supply events, prices and obligations already exist. The map shows actual
   locations schematically, with no claim of physical pathfinding realism.
2. **Say something consequential.** Select one citizen and submit a present-tense
   supply claim. Review the normalized interpretation before confirmation. Only
   that recipient receives this action; it does not rewrite supply truth or
   broadcast into every private memory.
3. **Let time pass.** Step, run, or advance the local world by up to three days.
   Gossip, purchases, costly inspections and settlement follow the engine rules.
   A report may remain local, lose support, be contradicted or cease to matter.
   A demonstration must show the outcome of the actual chosen run.
4. **Ask what changed.** Ask about trust or retained grain information and open
   SHOW WHY. The answer cites accessible records. If the records were forgotten,
   the character can report uncertainty instead of inventing a causal story.
5. **Investigate an alternative.** Explicitly enter Research/operator mode,
   remove the historical claim or introduce a grounded operator correction, and
   execute the alternative. Compare decisions, settlement, accounts and
   relationships. No difference is a valid finding; the UI must not manufacture
   a dramatic outcome for every branch.
6. **Resume the same world.** Refresh or restart using the same journal path.
   Accepted actions and histories recover. The world does not advance off-line
   or run as a continuously hosted society.

Curated seeds may make this sequence easier to understand, but must be disclosed
in the demo guide and must not stand in for aggregate evidence. A false report
does not guarantee a financial loss; a trust update does not prove that every
later event was caused by the report.

## Rules that protect the promise

Language is a proposal interface. The default adapter is a small deterministic
grammar with a bounded vocabulary of supply claims, retractions, inspection,
grain buying, delivery commitments and questions. It is not unrestricted
conversation or a general temporal-language model. A phrase about tomorrow does
not create a modeled tomorrow forecast: the review screen's normalized claim and
timestamp govern. Unknown requests need clarification or remain unsupported.

The adapter receives copied authorized views, not the world or full ledger.
Confirmation validates capabilities, evidence, affordability and action schema;
the engine remains responsible for transactions. A model adapter protocol exists,
but this slice has no required paid model service or demonstrated frontier-model
character reasoning. The deterministic path uses **$0 provider inference**;
machine resources, engineering and support still cost money. Any future model
integration must meter calls, retain proposal/model metadata and meet the same
state and evidence rules.

Private information and operator inspection are different experiences. Research
mode deliberately reveals information unavailable to the player or characters;
it is an inspectable local control, not a multiuser permission or authentication
system. An immediate privileged correction is useful for causal exploration but
is not cost-matched to an ordinary delayed inspection. Research comparisons must
keep those tracks separate.

The world-history graph records structural links chosen by the engine. It is not
a proof of causal necessity. A paired rerun tests a specified intervention under
this simulator and retained command sequence; it does not validate every parent
edge, prove unique causation, or estimate effects in human societies. Root labels
are declared source provenance, not authenticated witnesses or statistical
independence. These limits are part of the interface promise, not hidden footnotes.

## What the model of the world leaves out

The economy is deliberately narrow: one good, exogenous shipment regimes and
supply-linked price rules, scheduled contracts and simple role strategies.
Prices respond to the coded supply regime, not a general equilibrium or learned
market. Trade and procurement simplify travel and transaction frictions.
Relationship updates and commercial access are inspectable institutional rules,
not a validated model of human friendship or trust. Seeded order reduces the
fixed-order allocation artifact; it is not a universal economic fairness theorem.

The memory budget counts experiences, not bytes or tokens. FIFO forgetting and
bounded hop-limited gossip are design choices, not a human-memory model. Retained
dated dispatch records obtained through a paid inspection are new observations;
the archive is not free memory recovery. Economic accounts and durable trust can
outlast episodic explanations, so complete autobiographical recall is not promised.

Evaluation separates local recall, present belief, decisions, actual filled
quantities, delivered obligations and asset change. Zero-fill orders earn no
inventory or cash reward merely because they were attempted. Delivery fill is
the preregistered primary outcome; terminal inventory valuation is a disclosed
utility assumption. Asset change is neither optimal-policy regret nor societal
welfare. Fresh development seeds **20000–20009** and untouched held-out seeds
**50000–50029** are registered separately from the historical sprint. Numerical
findings must come from the completed frozen experiment, not this product note.

## The next product, conditional on evidence

The next worthwhile improvement is a tighter playable scenario: clear stakes,
legible consequences, more expressive but grounded exchanges, better recovery
from mistakes, and a reason to revisit a relationship after the first surprise.
The [prospective user protocol](USER_TEST_PROTOCOL.md) tests whether people can
act and explain an outcome, enjoy branching, voluntarily continue and return.
These tests have not been run.

Creator tools, a second setting, portable world packages, richer institutions,
cooperative multiplayer, hosted continuous worlds, identity across worlds,
marketplaces and user-generated public content are **planned possibilities**.
They are not delivered capabilities of this local slice. The platform hypothesis
earns further investment only if outside creators can build different enjoyable
worlds without core programming and if players return to them.

To launch the current local proof from the repository root:

```sh
python3 -m kalends.genesis.server --port 8770 --journal .kalends/genesis_session.json
```

Open `http://127.0.0.1:8770`. This launches a local deterministic experience and
stores its accepted command history at the specified path. Keep the journal to
resume that world. The final demo guide provides the reproducible demonstration
sequence; the handoff records the exact delivered build.
