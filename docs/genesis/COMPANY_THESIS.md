# KALENDS: COMPUTATIONAL WORLDS AS A NEW MEDIUM

**Decision memo, 20 October 2026.** The thesis is that people may value returning
to a small society whose relationships, obligations and history change because
of their participation. That could support a game, and eventually a creation
ecosystem. Neither step is established. There are no claimed Kalends customers,
retention cohorts, revenue, partnerships or fundraising outcomes. Proposed prices,
adoption counts and budgets below are assumptions, not forecasts or traction.

## The opportunity and its hardest objection

The compelling promise is: **enter, communicate or commit, leave, return to a
consequence, investigate it, then decide whether to repair or branch it**. A
durable ledger and bounded characters make that promise auditable. The player
needs attachment, tension, surprise and agency; a technically correct history
browser can still be a poor game.

This could be a new interaction format without being an entirely new technical
category. Existing simulations already produce stories, memory and social
consequences. Research systems already support agent societies and interventions.
The commercial test is preference and repeated use, not whether the engine has
more diagrams than an NPC demo. See the checked
[competitive landscape](COMPETITIVE_LANDSCAPE.md) and
[novelty audit](RESEARCH_NOVELTY_AUDIT.md).

Our assessment is that Roblox is the most dangerous platform competitor: it
already joins creators, discovery and monetization, and is adding creation AI.
Google threatens the cost and accessibility of immersive world generation.
Authored simulation games compete directly for the same leisure time. Specialist
character/runtime companies can commoditize dialogue and memory features.
Kalends currently has none of those distribution advantages.

## Four businesses, evaluated separately

The numerical cases are reachable-customer **hypotheses to test**, not measured
market sizes. They must not be added together as a TAM or a revenue forecast.

| Model | First customer / urgency | Revenue and bottom-up scenario | Distribution / costs | Defensibility and engineering burden |
|---|---|---|---|---|
| **A. First-party consumer experience** | Adult players who enjoy social/systemic simulation; discretionary entertainment, so urgency is unproved | Proposed $15 episode × 5,000 buyers = $75,000 gross launch receipts; later subscription only if recurring content earns repeat use | Playable demo, recorded branch stories, niche communities and streamers; content, support, optional inference and acquisition dominate | Character/content quality, recognizable experience and community; must build an enjoyable game, onboarding, save compatibility and content cadence |
| **B. Creator platform** | Small creators wanting to author coherent worlds without engine work; they also need an audience | Assumed 100 paying creators × $20/month = $24,000 annualized tool revenue; independently assumed $1M annual transaction volume × 10% take = $100,000 platform revenue | Two-sided acquisition, discovery, hosting, payments, moderation, creator support; tools do not supply demand | Possible creator/player network effects only after shared worlds produce actual engagement and earnings; authoring, sandboxing, versioning and governance are substantial new products |
| **C. Developer infrastructure** | Studios with an existing game and an expensive state/memory/debugging problem | Assumed 10 studio contracts × $10,000/year = $100,000 annual recurring contract value | Direct technical sales, engine plugins, procurement, integration support and compatibility; long sales cycles are a hypothesis, not observed Kalends data | Reliability fixtures, integrations and switching cost; a generic event ledger is easy to build internally, and studios may reject dependence on a small vendor |
| **D. Research/training infrastructure** | Agent-evaluation teams needing controlled information and executed-outcome checks | Assumed 5 teams × $15,000/year = $75,000 annual recurring contract value | Public reproducible examples, workshops and paid custom evaluation; researcher engineering support can consume all margin | Validated environments and trustworthy methodology; competes with open frameworks and internal simulators, and a research result is not a purchase order |

Five thousand game buyers do not imply one hundred viable creators; ten studio
contracts do not imply a consumer network. The large-company path needs a
repeatable acquisition and content production loop, then evidence that adding
creators improves player value faster than it adds discovery/moderation costs.
No valuation estimate is warranted by the current evidence.

## Recommended wedge and conditional expansion

Choose **A: a compact first-party information-and-consequences game**. The first
customer is a simulation-game player who wants to experiment with social and
commercial consequences, not a procurement department buying a general engine.
This choice tests the intended medium directly and exploits the current vertical
slice. It also has the highest risk that the experience simply is not fun.

Sell a complete authored scenario only after a public-quality demo works. Start
with enough deliberate character design and institutions to make actions matter.
Use language for accessible participation, not as a replacement for state. Price
testing is future work; a proposed $15 episode is a starting experiment, not a
commitment to a subscription with an unproved content cadence.

Expansion gates:

1. Demonstrate comprehension and voluntary return with the prospective protocol.
2. Have outside creators build a second genuinely different scenario without
   modifying the engine; measure time, defects and player enjoyment.
3. Add sharing/discovery around worlds that already retain players. Offer private
   authoring before a public marketplace.
4. Only then test creator payments, collaboration and multiplayer. Treat a
   research-tool business as a separate fallback with its own paying validation,
   rather than evidence that the consumer thesis succeeded.

## What belongs in the platform

The engine should own authoritative events and validated transitions, agent
identity, world clocks, scoped observations, declared memory access, resources,
commitment settlement, relationship state, immutable history identifiers,
snapshots/branches, and model-proposal validation. A portable versioned world
format and regression fixtures may reduce future integration friction.

Creators should own setting, art, character voice, goals, institutions, schedules,
goods, utilities, narrative opportunities and the intended experience. The engine
must not hardcode Roman grain policy into its identity. Shared-world discovery,
identity across worlds and marketplace governance become platform obligations
only if a hosted product is built. None should be advertised as implemented
because a local replay journal exists.

**Moat hypothesis:** a growing library of tested world primitives and authoring
patterns makes it cheaper to create compelling, inspectable scenarios, while
successful creators and players bring one another. Today this is a hypothesis.
Source code, a provenance graph, deterministic replay and prompt templates are
copyable. A large archive of synthetic traces is not automatically exclusive
data or a learning advantage. Evidence for a moat would be faster outside
authoring, better retained play and creator earnings that competitors cannot
readily reproduce with existing engines.

## Unit economics: sourced tariffs, hypothetical usage

**Actual current inference expense: $0 for the deterministic local demo path.**
No paid model requests were made for this analysis. CPU time, storage, rendering,
support and development are not free; local use currently places computation on
the user's machine. Hosted marginal cost and provider latency have not been
measured as commercial service levels.

The official pricing pages checked today list Claude Sonnet 5.5 at **$2 input /
$10 output per million tokens**, and Haiku 5.5 short-context pricing at **$0.10 /
$0.50**. These are optional modeling inputs, not a selected or quality-validated
Kalends integration. No cache or batch discounts are assumed.
[Official API pricing](https://platform.claude.com/docs/en/about-claude/pricing)

The Inworld on-demand page lists TTS-2 **$25 per million characters** and STT
**$0.15/hour**. The example voice budget below uses those posted rates; commercial
terms, taxes, regional availability and minimums must be checked before purchase.
[Official voice pricing](https://inworld.ai/pricing)

| Hypothetical session | Explicit usage assumption | Calculated provider expense |
|---|---|---:|
| Deterministic | No model calls or voice synthesis | $0 inference; hardware/hosting additional |
| On-demand text, lower-cost rate | 20 turns × 2,000 input / 250 output tokens; Haiku 5.5 tariff; 20% retry/overhead reserve | $0.0078 |
| On-demand text, mid-rate | Same tokens; Sonnet 5.5 tariff; 20% reserve | $0.1560 |
| Mid-rate text plus voice | Above, plus 5,000 spoken output characters and 4 minutes STT | $0.2910 |
| Every-agent-every-tick, 8 citizens | 8 × 24 calls × 2,000 input / 250 output tokens; mid-rate; 20% reserve | $1.4976 |
| Every-agent-every-tick, 32 citizens | Same pattern, 32 citizens | $5.9904 |

Formula: `calls × (input_tokens × input_rate + output_tokens × output_rate)
/ 1,000,000`, plus stated reserves/voice. Tokens per turn, session duration,
retries, model quality and future tariffs are assumptions. Context growth,
failed validations, idle worlds, moderation models and richer narration can
raise costs. A cheap model does not establish acceptable character quality.

For a **future** $12/month direct subscription, assume 3% payment cost, $0.40
variable simulation/storage and $0.30 moderation/support per subscriber-month.
These non-provider figures are planning assumptions, not vendor quotations.

| Usage case | Variable cost / month including the above | Contribution before fixed team/content/CAC |
|---|---:|---:|
| 8 mid-rate text sessions | $2.3080 | $9.6920 (80.8%) |
| 8 mid-rate voiced sessions | $3.3880 | $8.6120 (71.8%) |
| 60 mid-rate voiced sessions | $18.5200 | **-$6.5200** |
| 8 every-tick sessions with 8 citizens | $13.0408 | **-$1.0408** |

The subscription case is conditional on sufficient recurring value. Usage caps,
on-demand dialogue and predictable deterministic routine behavior are economic
design requirements, not merely optimization opportunities. Do not sell unlimited
autonomous generation before measuring its heavy-user tail.

For the proposed one-off episode, assume $15 price, 25% blended distribution
cost, five mid-rate text sessions ($0.78), $0.50 support and $0.20 delivery/storage:
contribution is **$9.77 per buyer**, before acquisition and content. With a
hypothetical $60,000 scenario-production cost, approximately **6,142 buyers** are
needed just to cover that content cost. Five thousand buyers leave $48,850 before
content, or **-$11,150 after that content budget**. These fee/budget assumptions
are not claimed storefront rates or production quotes.

At the subscription contribution of $9.692, an assumed $30 acquired-customer
cost takes 3.10 paid months to recover before fixed costs. Six paid months yield
$58.15 contribution, not a validated lifetime value. Real churn, refunds,
marketing conversion and content labor must be measured. A low model bill cannot
rescue an unwanted or expensive-to-author game.

## WHY KALENDS MAY NEVER BECOME A LARGE COMPANY

Disconfirming evidence below is **prospective**, not already observed.

| Concern | Why it could be fatal | Evidence that would weaken the concern |
|---|---|---|
| Incumbents copy the feature | Existing engines, Roblox, model vendors or studios can add memories/branches faster and distribute immediately | Independent players repeatedly choose Kalends against credible substitutes; outside authoring and retention remain better after comparable features ship |
| Consumers prefer authored games | Coherent personalities and pacing may require expensive deliberate design | Players voluntarily return to several independently authored systemic scenarios; enjoyable consequences occur beyond the tutorial without extra scripted sequences |
| High inference costs | Heavy users and background NPC calls erase margin | Metered p95 session cost stays within a preset budget at retained-user usage, including retries/context/voice, without quality collapse |
| Incoherent model behavior | A persuasive invented memory breaks the core promise | Audited evidence-constrained conversations maintain a low unsupported-claim rate across adversarial and long-session tests; failures are visible and recoverable |
| Interesting stories do not emerge | Accurate commerce may be boring repetition | Blinded players identify meaningful unprompted story moments across many uncurated seeds, with acceptable authoring cost per retained hour |
| Weak retention after an impressive demo | A single surprise does not create a medium | The independent return cohorts in the user protocol clear preregistered thresholds without rewards or repeated facilitator reminders |
| Creator onboarding friction | Users need programmers, debugging expertise and hidden engine knowledge | New creators complete valid, different scenarios without engine edits within the predefined authoring time, and players enjoy them |
| Moderation/safety of public worlds | Public content can create abuse, unwanted personal data and costly review | A limited consent-based pilot supports reporting, access controls, deletion and tested moderation operations at measured staffing cost; public UGC remains closed until then |
| Infrastructure complexity | Persistent state, branches, updates and multiplayer create expensive correctness/support obligations | Restart/version migration and load tests pass at target scale; support time and storage growth meet measured budgets; no silent state corruption |
| No network effects | Worlds are isolated, discovery is noisy and successful creators multihome | Creator additions measurably improve player return/discovery, and retained players attract productive creators; effects survive controlling for paid promotion |

Other strong failure modes are an inadequate founding team's content/design
skills, a business too small for platform-scale investment, and research validity
being mistaken for entertainment value. If the product only attracts experts
admiring a technical demonstration, the consumer thesis has failed even if a
research services business remains possible.

## Twelve-month decision program

This is a proposed program, not scheduled automation or committed spend. An
illustrative funding envelope is $600,000: four people × $100,000 loaded annual
cost, $150,000 content/contract work, $20,000 studies and $30,000 infrastructure.
Those are planning allocations, not labor-market or supplier quotations. They
must be resized to the actual team and runway; the revenue scenarios do not fund
this envelope automatically.

| Period | Experiment | Continue / stop evidence |
|---|---|---|
| Months 1–2 | Complete stable player loop; run 8-person formative study and 48-person usability/branch study | Continue only with reliable actions/explanations and comprehension; fix usability before marketing claims |
| Months 3–4 | Run 200-person voluntary-return cohort; meter complete sessions | Require the predefined joy/return/cost gates; do not optimize only a highlight video |
| Months 5–6 | Ship a second authored scenario, test proposed episode price with real opt-in purchases if authorized | Paid conversion plus repeat play must support content economics; satisfaction from friends/staff is insufficient |
| Months 7–9 | Test 12 outside creators with private tools and portable world packages | Proceed toward creator tools only if independent authoring succeeds and resulting worlds retain players |
| Months 10–12 | Repeat retention with new content; compare direct game distribution with one existing-platform integration | Choose a consumer product, a separately validated tools business, or stop platform investment; do not count research publicity as demand |

**Best initial product:** an authored, replayable society game built around
information, commitments and consequential return visits. **Best first customer:**
an adult systemic-simulation player. **Moat to test:** cheaper creation of
compelling coherent worlds plus a successful creator/player loop. **Distribution:**
an independently playable demo and genuine branch stories, then communities and
creators that voluntarily share outcomes. **Revenue:** proposed paid episodes;
subscription/marketplace only after repeat-value evidence. **Economics:** bounded
simulation and on-demand language, with every paid call metered and capped.

Go only after the user protocol, paid-demand and unit-economics gates pass.
No-go for a large-platform thesis if two independent cohorts fail return demand,
outside authors still need engine programmers, or retained usage has negative
contribution after feasible pricing/caps. A narrow enjoyable game can still be
worth building. The strongest reason this memo may be wrong is that inspectable
causality matters much more to its builders than to players.

## Dated primary-source bibliography

All checked **20 October 2026**. These sources support competitor capabilities or
tariffs, not the assumed Kalends adoption, prices or budget.

- [Roblox Cube, 4 February 2026](https://about.roblox.com/newsroom/2026/02/accelerating-creation-powered-roblox-cube-foundation-model): functional creation direction.
- [Roblox creation report, 3 September 2026](https://about.roblox.com/newsroom/2026/09/global-impact-of-creation-on-roblox): creator/distribution infrastructure; company-reported economics.
- [Google prototype, 29 January 2026](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/): current inspected release scope and stated limits.
- [Fable developer account, 10 June 2026](https://news.xbox.com/en-us/2026/06/10/fable-living-population-details-explained-xbox-games-showcase-2026/): deliberate character authoring and announced reactive society.
- [AgentSociety official repository, live](https://github.com/tsinghua-fib-lab/AgentSociety): competing research infrastructure, replay and tools.
- [Anthropic API pricing, live](https://platform.claude.com/docs/en/about-claude/pricing): only token tariffs used in the optional cost scenarios.
- [Inworld pricing, live](https://inworld.ai/pricing): only voice tariffs used above.

Further checked product sources and their evidence limitations are in
`COMPETITIVE_LANDSCAPE.md`. No speculative valuation or unmeasured market-share
claim is needed to justify the next experiment.
