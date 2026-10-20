# Competitive landscape: worlds, characters, games, and research systems

**Checked 20 October 2026.** This document distinguishes working public tools,
research evidence, developer announcements and marketing claims. We inspected
public materials, not competitors' internal implementations. An unmentioned
capability is **not documented in the inspected source**, not proved absent.
Kalends has no verified users, creator network, commercial deployments or sales.

## Comparison

| Competitor / evidence | What already exists | Consequence for Kalends / remaining test |
|---|---|---|
| **Roblox Studio, Cube, Build** — official product/release sources | Studio supplies creation, hosting/discovery and monetization; Cube's February announcement describes schema-based functional object generation and script retargeting; September describes limited-market Build beta. | Most dangerous platform incumbent: can distribute a comparable game or authoring feature inside an existing ecosystem. Generated assets and natural-language creation are not sufficient differentiation. Test whether a distinctive game loop earns demand outside that ecosystem. [Cube](https://about.roblox.com/newsroom/2026/02/accelerating-creation-powered-roblox-cube-foundation-model), [creation](https://about.roblox.com/newsroom/2026/09/global-impact-of-creation-on-roblox) |
| **Google Genie 3 / Project Genie** — research preview and consumer prototype | Interactive visual world generation; the January Project Genie release allows creation/exploration/remixing. Its documented prototype has a 60-second generation limit and does not include every announced Genie capability. | A different current substrate from an explicit institutional ledger, but a formidable long-term substitute for world creation and immersion. Do not infer exact economic state/replay from rendered visual consistency. Do not claim Google is permanently unable to add explicit state. [Model](https://deepmind.google/blog/genie-3-a-new-frontier-for-world-models/), [prototype](https://blog.google/innovation-and-ai/models-and-research/google-deepmind/project-genie/) |
| **Inworld** — commercial runtime/inference provider | Current site emphasizes low-latency speech, LLM serving and developer infrastructure; pricing meters several services. | Character expressiveness and inference optimization can be purchased or supplied by specialists. Kalends should validate a complete experience, not compete on a thin dialogue wrapper. Historical NPC positioning does not describe the whole current business. [Site](https://inworld.ai/), [pricing](https://inworld.ai/pricing) |
| **Convai** — commercial character toolkit | Character knowledge, cross-session memory, narrative tools and action integrations are publicly offered. | “An NPC remembers you and takes actions” is already a product claim. The open question is reliable local evidence, executed institutions and enjoyable branching as one experience. No independent correctness guarantee follows from the feature list. [Product](https://convai.com/), [actions](https://docs.convai.com/api-docs/api-reference/core-api-reference/character-crafting-apis/action-api), [plans](https://convai.com/pricing) |
| **AI Town / Generative Agents** — open starter kit and empirical research | AI Town is an MIT-licensed town starter with shared state, transactions and simulation. Generative Agents demonstrates memory/planning/social diffusion in a structured town. | A clone can reproduce the visual premise cheaply. Kalends must show consequential validated actions and a return/repair loop that users prefer, rather than merely a map of talking characters. [AI Town](https://github.com/a16z-infra/ai-town), [paper](https://arxiv.org/abs/2304.03442) |
| **AgentSociety** — open research infrastructure | Current repository exposes modular social environments, research workflows, traces and experiment replay; its papers study simulated societies. | Strong substitute for a research-infrastructure wedge. A small local playable system may be easier to inspect, but simplicity is not broad scientific superiority or a durable moat. [Repository](https://github.com/tsinghua-fib-lab/AgentSociety) |
| **RimWorld** — shipped commercial simulation | Needs, relationships, trade, modding and a storyteller that shapes events. | Persistent emergent consequences are established entertainment. The competitor is a polished authored/rule-based experience, not only an AI vendor. Kalends must earn comparable attachment and replay value. [Developer](https://rimworldgame.com/) |
| **Dwarf Fortress** — shipped simulation with generated histories | Developer materials describe world-history generation and navigable Legends records. | Historical persistence, discoverable stories and systemic complexity predate generative AI. Explainable information interventions could be a useful interaction design, not a claim to invent simulated history. [Developer](https://www.bay12games.com/dwarves/) |
| **Fable living population** — developer-described upcoming game | June 2026 article describes handcrafted NPC identities, schedules, reputation, memory and economic consequences. The inspected page now announces February 2027 release. | Strong warning that deliberate authoring can outperform random generation for coherence. As of this check, treat these specifics as announced capabilities, not independently verified shipped retention or a public agent engine. [Xbox developer account](https://news.xbox.com/en-us/2026/06/10/fable-living-population-details-explained-xbox-games-showcase-2026/) |
| **World Labs / Marble** — commercial spatial generation API | January announcement offers navigable worlds generated from multimodal inputs, with web rendering/export/integration. | Potential visual supplier and competitor for creation workflows. A navigable space does not by itself demonstrate durable private beliefs or institutional accounting. Public API scope, rather than a company's name, defines the current comparison. [World API](https://www.worldlabs.ai/blog/announcing-the-world-api) |
| **Odyssey** — world-model company; commercial/research claims | Current site offers model experiences and API access, including a claimed shared multi-participant world model. | Learned interactive environments are advancing beyond single-user video. Do not rely on a permanent “world models cannot be multi-agent” advantage. Audit exact-state guarantees and costs before treating such a model as Kalends' authority. [Current site](https://odyssey.systems/) |
| **Decart / Oasis** — commercial model claims | Current Oasis page describes controllable generated environments/API access and explicitly distinguishes its model from a physics engine. | Real-time synthesis can compete on immersion and simulation supply. Public marketing about physical grounding is not a conservation-law or economic-state certificate. [Oasis](https://decart.ai/oasis) |
| **Scenario** — commercial production tooling | Asset-generation/training workflows and API integration for creative production. | Makes visual content less differentiating and may lower art-production costs; does not establish world behavior. Buy/export compatible assets only after workflow and rights checks. [Platform](https://www.scenario.com/platform) |

## Where a differentiated product could exist

The proposed wedge is a playable information-and-consequences game: communicate
with one participant, make a commitment, leave, return to a changed relationship,
investigate the actual record, then repair or branch the situation. The test is
whether players care about this loop, understand it and voluntarily repeat it.
Exact accounting and scoped memories are enabling constraints, not a consumer
benefit until translated into a satisfying experience.

Three technical gaps are legitimate experiments, not proven exclusive assets:

1. Keep expressive character language aligned with executable, private evidence
   over a long session, including rejection and correction of unsupported claims.
2. Make generated consequences interesting without forcing a hidden script or
   sacrificing the consistency that enables replay.
3. Give creators an authoring/debugging loop where institutions, memory access
   and explanations remain understandable without core-engine work.

A normal game engine can implement most individual primitives. Event sourcing,
rules, save/load, scripted utility policies and data structures are reproducible
engineering. A credible moat would have to emerge from exceptional content,
validated authoring workflows, accumulated regression/evaluation fixtures,
creator success and distribution. Raw event volume is not automatically
proprietary learning data, and neither a schema nor a provenance graph creates
network effects by itself.

## Incumbents, distribution and strategic responses

Roblox is the largest direct strategic threat **in our assessment**, because
creation, player discovery and creator monetization are already connected.
Its September source reports over $1.5B of 2025 creator earnings, while also
reporting a much smaller median among DevEx participants. Those are company-
reported ecosystem figures, not Kalends' obtainable market or evidence that a
typical creator prospers. Google is the largest model/immersion threat; game
studios are the strongest substitutes for consumer time; AgentSociety is a
particularly relevant substitute for research tooling.
[Roblox report](https://about.roblox.com/newsroom/2026/09/global-impact-of-creation-on-roblox)

Respond by testing a small authored first-party experience, retaining portable
world/history formats and replaceable model adapters, and avoiding a standalone
creator marketplace until creators demonstrate demand. Integration with an
existing game/creator ecosystem may ultimately be better than a new destination.
That choice requires observed acquisition, repeat use and creator economics.

## Dated source register and availability

All links above resolved publicly on **20 October 2026**. The six user-supplied
starting links were available; none was substituted with an unverified report.
Dates below are publication dates when shown; “live/undated” is intentional.

| Source | Date shown / status | Specific support and limitation |
|---|---|---|
| DeepMind Genie 3 | 5 August 2025, research announcement | Interactive generation and stated duration/action/multi-agent limits of that announcement; not a current universal ceiling. |
| Google Project Genie | 29 January 2026, prototype release | Initial US adult Ultra access and documented prototype limitations; do not assume unchanged worldwide entitlement. |
| Roblox Cube | 4 February 2026, product announcement | Schema/function generation; some ambitions are explicitly future tense. |
| Roblox creation impact | 3 September 2026, company report | Creator infrastructure, earnings and limited Build rollout; marketing/economic-impact methodology, not neutral TAM. |
| Xbox Fable | 10 June 2026 page, subsequently updated release information | Design approach and announced population; current page says 23 February 2027 release, so this is not a shipped-2026 claim. |
| AI Town / AgentSociety GitHub | live repositories | Public source/readme and stated licenses/features; no inference about maintained production support or adoption. |
| Inworld / Convai | live product/pricing/docs | Offered capabilities and displayed tariffs, not independently measured reliability; Convai's alternate delta pricing content contains inconsistent quota prose, so no numerical Convai cost forecast is used. |
| RimWorld / Bay 12 | live developer pages, including dated archives | Existing systems/history; archives are evidence of prior art rather than current performance claims. |
| World Labs World API | 21 January 2026 announcement | API generation/export scope. No exact society-state guarantee inferred. |
| Odyssey / Decart / Scenario | live/undated pages | Current public positioning and offered interfaces; company claims are not treated as comparative scientific results. |

Research details and checked paper identities are in
`RESEARCH_NOVELTY_AUDIT.md`. Nothing in this landscape establishes demand for
Kalends or rules out capabilities not documented in the inspected sources.
