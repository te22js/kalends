# Kalends Genesis — delivered build and evidence

**20 October 2026 · branch `codex/genesis`**

The delivered proof is a local playable town: a player message is reviewed,
confirmed and recorded; citizens act using bounded private information; real
deliveries and cash settle; a checked false report can damage trust and close
commerce; the player can inspect retained evidence and execute another history.
The original Fork the City implementation and experimental artifacts are intact.

## Use it

Open [Genesis](http://127.0.0.1:8770/). The current demonstration has an original
and a message-removal branch at tick74. Livia trusts the player32% in the original
and60% in the branch. Ask **Why trust me?**, then **SHOW WHY**. Research mode shows
the actual decision/account differences. Your world is preserved during UI polish.

To launch or resume independently from this repository:

```sh
python3 demo/genesis/launch.py --port 8770
```

Python3.10+ is required. On this Mac use the bundled3.12 interpreter:

```sh
PYTHONPYCACHEPREFIX=/tmp/kalends-pycache /Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 demo/genesis/launch.py --port 8770
```

`--fresh` archives the previous demo journal, then starts the curated opening.
The demo uses seed2026 and a **256-experience budget** so the three-day source
records survive. The ordinary server and primary research use capacity32.
Time advances only through controls; no hosted background life is claimed.
Detailed timed scripts and language examples are in
[PLAYER_DEMO_GUIDE](docs/genesis/PLAYER_DEMO_GUIDE.md).

## Exact source history

| Commit | Purpose |
|---|---|
| `f528c77` | Preserved historical Fork the City baseline; baseline227 tests passed |
| `a1010fc996e5dd342fe51c481c5b732f6ca634c4` | Genesis runtime and prospective configuration frozen before all held-out execution |
| `66b17e8` | Post-study product fixes: Player-specific grounded explanations, bounded supporting citations, readable evidence, settlement accounting links and independently launchable curated demo |

The focused UI polish is commit `76b6fa5`: clearer contrast and controls, roomier
conversation, readable contract totals and meaningful player journal entries.
The delivery also includes the evidence/document commit shown by `git log --oneline codex/genesis`. The final response identifies
the exact delivered HEAD. `CHANGED_FILES.txt` is the exact baseline-to-delivery
file inventory, including this handoff. No repository push or public deployment
was performed.

The held-out study is reproducible from **a1010fc**, not silently redefined by
later product work. Its manifest hashes all48 Python source files and the plan.
The source remained unchanged throughout the run. The later accounting-parent
metadata changes ledger hashes, so final-product ledger hashes should not be
compared directly with historical raw hashes. A separate24-pair/48-run check on
reserved development configurations found identical executed metrics, decisions,
bounded and archival experiences, accounts, trust, messages and event counts;
ledger differences were only the declared settlement accounting annotations.
See [poststudy_compatibility.json](results/genesis/poststudy_compatibility.json).

## What changed

- New `kalends/genesis/` package, separate from the historical simulator. The
  runtime reuses its event/state primitives while replacing information access,
  role policies, economic measurement and participant interactions.
- Distinct procurement, caution, speculation, courier-sharing and official
  inspection strategies. Preference changes materially alter choices.
- One FIFO information budget governs belief retrieval, acceptance, gossip,
  dialogue and decisions. Audit history cannot restore forgotten supply facts.
  Owned economic accounts and institutional trust persist separately.
- A real old report: Dama observes the original shipment at tick0; its delayed
  report arrives at6, after a reversal at4. Paid dated-record inspections distinguish
  truthfully outdated information from a contradicted historical claim.
- Private Player claims, paid next-tick inspections, actual backed trades,
  delivery agreements, corrections derived from personal inspections and scoped
  retractions. All accepted actions enter the ledger.
- A narrow offline grammar with explicit confirmation, constrained optional
  adapter protocol, canonical action review text and grounded factual rendering.
  Proposals retain model/version/view-hash/latency metadata. No provider was called.
- Player-safe API responses and evidence traces; a separate local Research toggle
  reveals private/operator state deliberately. This is not multiuser authentication.
- Historical reruns omit an actual accepted claim and replay subsequent accepted
  commands; surviving source IDs are remapped. Retractions whose source was removed
  are explicitly skipped. Unsafe ambiguous references reject the fork.
- Version2 journal recovers worlds, accepted commands, branches, proposals and
  dialogue after normal restart. Page refresh preserves the world. Save-format
  migration across arbitrary future code changes is not promised.
- Executed fills, delivered units, fees, inventory, cash and social access replace
  the old categorical score. Settlement links expose account dependencies without
  claiming those links prove necessary causation.
- A new 2D interface, grounded evidence dialog, three-day return summary, branch
  comparison, prospective user study and adversarial company/research documents.

## The actual demonstration

The walkthrough journal is
[walkthrough_session.json](demo/genesis/walkthrough_session.json); its actual
metrics and evidence are in
[walkthrough_result.json](demo/genesis/walkthrough_result.json).

In the captured run, Player tells Livia “grain disrupted” as of tick2 (event37).
She pays2 for an inspection (73), observes the current shipment at5 (78), and reads
the actual dated dispatch record for2 (79), which says available. The matching-date
contradiction produces assessment80 and trust32%, closing commerce. The explanation
cites these five retained records rather than unrelated citizens or invented loss.

Removing the original claim reruns to74 with Livia trust60% and commerce open.
District delivery fill changes from88.24% to89.54%; purchased units131→133; net
asset change−668.5→−660. These are **curated single-run results**, not held-out
average effects. The trace distinguishes chronology, recorded dependency,
accessible evidence and tested intervention. The costs of other outcomes are
not invented merely to make a story dramatic.

Actual screenshots and their state/hash manifest are under `demo/genesis/`.
No supported video-recording API was available. The real app, restartable journal,
actual captures and timed60–90s/3–5min scripts are the independently launchable
substitute; no generated demo video is claimed.

## Research result

The fresh study ran **900 worlds**, **30 independent seed clusters**,
**5,288,329 events** and **779,565 decisions** in481.4 wall seconds using4 workers.
It comprises720 primary worlds and180 additional controls. Provider inference
calls/cost were0/$0. This is not a total hosting or engineering-cost estimate.

The one preregistered paired contrast was lineage-gated versus ungated guarded
memory on delivered units. The effect was **−0.1803 percentage points**, with
95% seed-bootstrap interval **[−0.2575,−0.1038]**. It is a small adverse effect in
this environment, not evidence that gating improves delivery.

Descriptively, lineage increased inspection spend and answer coverage; answered-only
belief precision did not clearly improve. Local canonical recall was100% in all
conditions: this is a disclosed structured-key ceiling, not a difficult memory
success claim. Structured and guarded ungated baselines produced identical histories
in all180 paired cells. Fixed supply at32 citizens reduced delivery far more than
the gate comparison. Allocation ordering changed who received grain more than the
district total, with that distributional grouping explicitly exploratory.

Cash already includes costs/revenue/penalties; asset change adds only terminal
inventory change valued at1,3 or6. There is no double-counted penalty, categorical
zero-fill reward, computed optimum, social-welfare claim or optimal regret.

Read [RESEARCH_PAPER](docs/genesis/RESEARCH_PAPER.md),
[EXPERIMENTAL_VALIDITY](docs/genesis/EXPERIMENTAL_VALIDITY.md),
[RESULTS_AUDIT](docs/genesis/RESULTS_AUDIT.md), and the raw
[held-out manifest](results/genesis/heldout/manifest.json),
[worlds](results/genesis/heldout/worlds.jsonl),
[summary](results/genesis/heldout/summary.json) and figures. The primary sources
and closest methodological overlaps are checked in
[RESEARCH_NOVELTY_AUDIT](docs/genesis/RESEARCH_NOVELTY_AUDIT.md).

The broad memory-to-action gap, agent societies, replay and state verification
have substantial prior art. No publication readiness or general research
superiority is claimed. Separate development verification controls disclose
operator privilege versus participant cost, timing, payer and recipient; all10
matched paid-Livia routing pairs replay identically. Those controls do not turn a
free operator correction into a fair autonomous baseline.

## Engineering checks and remaining limits

The final complete Python suite passed **288 tests in14.65s**; the previous227
tests remain included. Focused checks cover role incentives, FIFO eviction,
gossip isolation, private APIs, source integrity, dated inspections, conservation,
actual zero fills, confirmation, hostile adapters, historical source remapping,
restart recovery, identity forks and the complete curated explanation.
JavaScript syntax and plotting-source checks pass. Actual browser actions verified
proposal/confirmation,72-tick return, five-event evidence and executed comparison.
See [validation.json](results/genesis/validation.json) and
[ENGINE_AUDIT](docs/genesis/ENGINE_AUDIT.md).

Limits remain: one exogenous-supply good, coded deterministic strategies, simplified
remote communication/trading, no general market equilibrium, debt-producing fines,
experience-count rather than byte budgets, and possible forgetting of relationship
reasons at capacity32. Declared roots are not authenticated/statistically independent
witnesses. Retraction tombstones can themselves be forgotten. The archive's
retraction Exposure proposition has a documented audit-only mismatch; operational
bounded records use the correct predicate. No paid LLM integration,3D, multiplayer,
hosted background world, general creator SDK or second setting is delivered.

## Product and company documents

[PRODUCT_VISION](docs/genesis/PRODUCT_VISION.md) distinguishes implementation from
plans. [COMPETITIVE_LANDSCAPE](docs/genesis/COMPETITIVE_LANDSCAPE.md) checks the
requested incumbents and emerging companies. [COMPANY_THESIS](docs/genesis/COMPANY_THESIS.md)
evaluates four separate businesses, bottom-up assumptions, costs, distribution,
moat hypotheses,12-month gates and the required “WHY KALENDS MAY NEVER BECOME A
LARGE COMPANY” section. It recommends a conditional first-party consequence-game
wedge; Roblox is the strongest platform threat. No users, traction, partnerships,
funding or retention are invented. [USER_TEST_PROTOCOL](docs/genesis/USER_TEST_PROTOCOL.md)
is a future study with falsification thresholds, not a study already run.

## Reproduce

```sh
python3 -m pytest tests/ -q
python3 scripts/check_genesis_compatibility.py --out /tmp/kalends-genesis-compatibility-recheck.json
MPLCONFIGDIR=/tmp/kalends-mpl python3 scripts/plot_genesis.py
```

For the exact frozen experiment, inspect/checkout commit `a1010fc` in an isolated
checkout, then run `python3 -m kalends.genesis.bench --phase heldout --jobs 4
--output /tmp/kalends-genesis-reproduction`. The runner refuses to overwrite
existing results and requires committed runtime/preregistration for held-out work.
No retuning of held-out policies occurred. The ordinary runtime has no third-party
dependencies; pytest is needed for tests and matplotlib/NumPy for figure rendering.
