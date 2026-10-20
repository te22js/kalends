# KALENDS — COMPUTATIONAL REALITY AND THE NEXT EXPERIENTIAL MEDIUM

**Skeptical decision memo, 21 October 2026.** Kalends' hypothesis is that a small
persistent society can become a place people want to inhabit: take a role, make
a choice, leave, return to consequences, and understand the history they helped
create. Pompeii is the first setting at the intersection of history and
entertainment. This is a prototype/research program, not a validated company.
No customers, revenue, retention, partnerships, financing or clinical/learning
benefits are asserted. Every proposed price, adoption count and budget below is
an assumption to test.

## Product, customer and the real distinction

Start with a **paid, authored historical experience for adult history/simulation
enthusiasts**. Its selling proposition is an enjoyable personal situation in a
recognizable place, where information, obligations and relationships interact.
Historical evidence labels, coherent consequences and controllable pacing earn
trust; they cannot substitute for attachment, tension and worthwhile choices.
The player should be able to enjoy the district without understanding the lab.

The technical distinction to examine is precise: generating an impressive scene
does not by itself maintain private evidence, institutional records, commitments
and replayable consequences. This does **not** imply visual-model companies
cannot add those systems, or that ordinary game engines lack persistence.
Save/load, event systems, agents and branching are existing tools. The possible
advantage is making a compelling, coherent experience cheaper to author and
operate, demonstrated against an ordinary implementation.

An education purchase requires separate evidence of accurate content, usable
classroom delivery and learning transfer. A museum or school can be a later
distribution/customer experiment; no relationship with Pompeii's Archaeological
Park is implied by citing its public sources. Professional training, research,
creator tools and cognitive/interface ambitions have different buyers and
validation burdens; [APPLICATIONS_ROADMAP.md](APPLICATIONS_ROADMAP.md) evaluates
them separately. Their hypothetical markets must not be added together.

## Competitors that make the proposition difficult

Official sources below were checked on **21 October 2026**. Feature pages are
commercial claims unless backed by an inspected paper; a feature absent from a
page is not proved absent from the product.

| Competitor | Current inspected evidence | Strategic implication |
|---|---|---|
| **Roblox Studio / Cube** | Existing creator/distribution environment; February2026 Cube announcement uses schemas and script retargeting for functional generated objects, with broader scene generation an ambition. [C1] | Strongest platform threat in our assessment: can add a memory/causality game inside an existing creator/player loop. Asset generation alone is not differentiation. |
| **The Sims / EA** | Life simulation, aspirations, relationships and Gallery; current official page advertises October5,2026 Maker Program/Marketplace announcement. [C2] | A direct substitute for “live another life,” with established creation/discovery. Do not treat creator distribution as an empty category or announced Marketplace scope as independently verified outcomes. |
| **Google Project Genie** | Official January2026 experimental world-creation/exploration/remixing prototype; inspected release specifies limited generation and launch access. [C3] | Major immersion/creation threat. Its release limits do not establish permanent inability to support durable society state. |
| **Inworld / Convai** | Realtime inference/voice infrastructure and conversational character/action tooling. [C4,C5] | Dialogue, voice and memory features can be bought, integrated or commoditized. A thin NPC wrapper is vulnerable. |
| **Generative Agents / AI Town** | Published town-memory research and an MIT-licensed deployable town starter. [C6] | A talking town is prior art; visual premise alone is cheap to reproduce. |
| **AgentSociety** | Public research platform with modular environments and inspectable/replayable experiments. [C7] | Research infrastructure has capable open substitutes; internal rigor does not guarantee a commercial tools market. |
| **RimWorld / Dwarf Fortress** | Shipped systemic games, relationships, historical/emergent stories and extensibility. [C8,C9] | Polished authored rules compete directly for leisure time without needing an LLM at every tick. |
| **Game engines / inkle** | Ordinary engines offer persistence primitives; ink offers writer-focused authoring/testing and branching narrative. [C10,C11] | Most primitives can be rebuilt. Authoring cost and player preference must beat a credible engine-plus-writers alternative. |

The strongest likely response from an incumbent is not “replicate every research
fixture.” It is “ship the enjoyable parts through existing distribution.” A
feature advantage that requires a paper to perceive may not survive that response.

## Business sequence and expansion gates

1. **First-party experience.** Ship one satisfying, historically reviewed
   episode. Primary acquisition hypothesis: a freely playable browser demo,
   documented player stories and opt-in history/simulation communities. Measure
   acquisition source and paid conversion; do not count impressions as demand.
2. **Private authoring tools.** Invite a few outside authors only after players
   return. Require a second setting/institution to work without engine edits.
   Measure author hours, debugging support and player enjoyment of their output.
3. **Sharing/distribution.** Test whether sharing a world increases qualified
   play and whether new creators improve repeat use. A file export is not a
   creator network. Integrating with an incumbent may beat building a destination.
4. **Marketplace/platform, conditional.** Add identity, moderation, payments,
   portability, compatible upgrades and eventually multiplayer only when
   successful authors and players create real demand. These are new products,
   not automatic consequences of a local journal.

Platform primitives should include state transitions, event identity, clocks,
scoped information, memory access, goals/actions, commitments, relationship
records, snapshots/branches, model validation and versioned world packages.
Creators should own setting, art, voice, institutions, objectives and intended
experience. Do not make Roman grain policy the general engine API.

**Moat hypothesis:** tested primitives and authoring workflows reduce the cost
of producing coherent, enjoyable worlds; successful creators and players then
attract one another. Present code, provenance graphs, safe event scheduling and
prompt schemas are copyable. Synthetic trace volume is not automatically an
exclusive dataset or learning advantage. A moat needs observed creation speed,
retained play, creator earnings and switching value, not an architecture label.

## Unit economics: quotations versus assumptions

The offline deterministic route requires no paid inference. Actual optional
provider usage must be taken from the run receipts; this memo makes no paid
requests and reports **no measured hosted cost**. Local CPU, art, writing,
historical consultation, QA and support are real expenses even when provider
inference is zero. Lived-Time CPU savings and model-call savings are separate.

Official tariffs checked today: Sonnet5.5 **$2 input/$10 output per million
tokens**; Haiku5.5 **$0.10/$0.50** for prompts up to100,000 tokens. Inworld's
on-demand TTS-2 is **$25/million characters**, STT **$0.15/hour**. These are
scenario inputs, not selected models or quality-validated integrations. [C12,C13]

| Hypothetical usage | Assumption | Calculated provider cost |
|---|---|---:|
| On-demand text | 20 turns, 2,000 input+250 output tokens/turn, Sonnet tariff, 20% retry reserve | $0.1560/session |
| Lower-cost text | Same tokens, Haiku short-context tariff, same reserve | $0.0078/session |
| Text + voice | Sonnet case +5,000 output characters +4minutes STT | $0.2910/session |
| Every citizen every tick | 8 citizens ×96ticks, same per-call token use, Sonnet +reserve | $5.9904/chapter |
| Larger every-tick case | 32 citizens ×96ticks | $23.9616/chapter |

Formula: calls × (input tokens × input tariff + output tokens × output tariff)
/1,000,000, plus stated voice/reserve. Growing context, moderation, tool costs,
failed validations and background generation may raise expense. Routine behavior
should therefore remain deterministic, with paid generation metered and bounded.
Cheap inference does not establish good characters or low content-production cost.

For a proposed **$15 episode**, assume 25% blended store/payment/distribution
cost, five Sonnet text sessions ($0.78), $0.20 delivery/storage and $0.50 support:
**$9.77 contribution/buyer before acquisition and fixed production**. These
non-provider figures are explicit planning assumptions, not posted platform fees
or hosting quotations. Suppose one episode costs $120,000 to produce, including
engineering, writing, art, historical review and QA; this is an illustrative
budget, not an actual expenditure or contractor quote.

| Assumed buyers | Gross receipts | Contribution before acquisition/production | After the $120k scenario budget, before acquisition |
|---:|---:|---:|---:|
| 2,000 | $30,000 | $19,540 | −$100,460 |
| 10,000 | $150,000 | $97,700 | −$22,300 |
| 50,000 | $750,000 | $488,500 | $368,500 |

Break-even is approximately **12,283 buyers** with zero acquisition cost, or
**25,158** at assumed $5 acquisition/buyer. At $10 acquisition, contribution is
negative before fixed content. Organic reach is therefore a hypothesis to test,
not a free input. Refunds, taxes, financing and team overhead are not included.

A future $12/month subscription with assumed 3% payment cost, $0.40 hosting and
$0.30 support/moderation has $1.06 non-model variable cost. Eight voiced sessions
give $8.612 contribution; sixty give **−$6.52**, before new content/CAC. Subscription
is premature until repeat value and heavy-user costs are measured. Multiplayer
adds synchronization, abuse handling, storage and support that these single-user
examples do not price. Asset generation also needs actual license/review costs;
there is no assumption of limitless free art.

No valuation follows from these cases. Even hypothetical 10million annual buyers
at $15 produce $150million gross receipts, before costs. A trillion-dollar outcome
would require extraordinary global scale, economics and market power; current
evidence does not support assigning it a valuation or probability.

## WHY KALENDS MAY NEVER BECOME A LARGE COMPANY

| Fatal concern | Evidence required to weaken it |
|---|---|
| Incumbents copy the compelling features | Independent players prefer Kalends against credible substitutes after comparable features appear. |
| People prefer authored games to systemic worlds | Multiple uncurated play sessions produce enjoyable agency beyond the introduction at viable authoring cost. |
| A memorable demo has weak retention | Fresh voluntary-return cohorts clear frozen thresholds without return rewards or facilitator reminders. |
| Inference/hosting-heavy users erase margin | Metered p95 full-session cost and usage distribution support contribution after feasible caps/pricing, with maintained quality. |
| Characters remain repetitive or invent history | Blinded play and adversarial evidence checks show meaningful differentiation and low unsupported-claim rates. |
| Simulated stories are coherent but boring | Players choose continued play and describe consequential events without being prompted to admire the technology. |
| Historical review/content creation is too expensive | A second episode meets measured quality, accuracy and cost targets; outside authors need bounded support. |
| Creator onboarding/discovery never works | Outsiders create distinct valid worlds without engine programming; those worlds attract and retain players. |
| Public-world moderation becomes unmanageable | A limited pilot demonstrates access controls, reporting, deletion and staffed operations at measured cost before public UGC opens. |
| Infrastructure/versioning overwhelms the team | Upgrades, saved worlds, branches and target concurrency pass recovery/migration tests with bounded support/storage. |
| Network effects never arise | More creators improve qualified discovery and return; player growth attracts productive creators after controlling for promotion. |
| Educational/cognitive promises exceed evidence | Learning survives delayed transfer tests against matched instruction; if absent, sell entertainment accurately or stop the claim. |

Research may be worthwhile even if the experience is niche. A coherent simulator
is not automatically a venture-scale consumer business. The strongest reason
this thesis may be wrong is that inspectable causality matters more to the
builders than to the people who might pay.

## Twelve-month decision program

This is a proposal, not a schedule, committed spend or forecast.

| Period | Test | Continue / pivot criterion |
|---|---|---|
| Months1–2 | Stable district, independent historian review, 6-person formative and 12-person uncoached playtest | Fix interaction/history failures first; require comprehension and voluntary continuation before promotion. |
| Months3–4 | Independent 60-person return pilot; measure complete session costs | Continue only with repeat demand; unclear intervals require a fresh larger cohort, not marketing claims. |
| Months5–6 | Paid episode test and second authored situation | Real opt-in purchase conversion must cover feasible acquisition and content economics. |
| Months7–9 | Five outside creators with private tools | Expand only if they author different valid scenarios without engine edits and users enjoy the output. |
| Months10–12 | Replicate return with new content; compare standalone distribution with an existing-platform integration | Choose a sustainable first-party product, separately validated tools niche, or stop platform expansion. |

**Best initial product/customer:** one excellent Pompeii episode for adult
history/simulation players. **Distribution:** playable browser demo and authentic
player histories, then a channel with measured paid conversion. **Revenue:**
proposed paid episodes; recurring/creator fees only after repeat-value evidence.
**Economic discipline:** bounded simulation, on-demand language, and measured
full costs. **Expansion trigger:** repeat players plus successful outside authors,
not benchmark publicity. **No-go/pivot:** repeated return failure, infeasible
content/acquisition economics, dependence on engine programmers for every world,
or persistent unsupported dialogue. No human cognitive acceleration is claimed.

## Dated primary sources

All checked **21 October 2026**; supports are limited to the capabilities/tariffs
listed, not assumed Kalends demand or economics.

- C1 [Roblox Cube, 4February2026](https://about.roblox.com/newsroom/2026/02/accelerating-creation-powered-roblox-cube-foundation-model).
- C2 [EA, current Sims page and dated Maker/Marketplace announcement](https://www.ea.com/games/the-sims).
- C3 [Google Project Genie, 29January2026 release](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/).
- C4 [Inworld, current product](https://inworld.ai/); C5 [Convai, current product](https://convai.com/).
- C6 [AI Town official repository](https://github.com/a16z-infra/ai-town); [Generative Agents paper](https://arxiv.org/abs/2304.03442).
- C7 [AgentSociety official repository](https://github.com/tsinghua-fib-lab/AgentSociety).
- C8 [RimWorld developer](https://rimworldgame.com/); C9 [Dwarf Fortress developer](https://www.bay12games.com/dwarves/).
- C10 [Godot saving-game documentation](https://docs.godotengine.org/en/4.3/tutorials/io/saving_games.html), ordinary persistence and its implementation limits; C11 [ink official authoring tools](https://www.inklestudios.com/ink/).
- C12 [Official Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing); C13 [Inworld on-demand pricing](https://inworld.ai/pricing).

The earlier [Genesis landscape](../genesis/COMPETITIVE_LANDSCAPE.md) preserves
additional competitors and its own dated checks; it is historical analysis,
not new Pompeii adoption evidence.
