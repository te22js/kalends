# Kalends — human-facing product and website specification

**Status:** proposed build specification, 24 October 2026. Sources and limits: `00_DECISIONS_AND_SOURCES.md`. All layouts, copy, timing budgets and acceptance thresholds below are design proposals, not measured current behavior.

## 1. The experience we are designing

A visitor should understand this sequence without learning Kalends' architecture:

**Choose a world → meet people with their own circumstances → make a choice → spend time there → leave a trace → return to consequences.**

“Human” means comprehensible situations, particular people, believable responses, ordinary moments, control over pace, and a history that feels connected. It does not mean more emotional adjectives, manipulative character attachment, anthropomorphic consciousness claims or an AI chat box on every screen.

Keep the broad company ambition: curated persistent worlds and synthetic experiences. The next product is a small working expression of that ambition. A training/research tool is a commercial hypothesis, not a replacement for the original vision by default.

### One release promise

> A visitor can enter an existing world, understand a situation without a developer, make a meaningful choice, and return to a history that the people and institutions actually retained.

Everything in this release must advance that promise or the separately defined research experiment.

## 2. Information architecture

Keep the internal LIVE / LEARN / LAB capabilities. Stop making their technical separation the visitor's first decision.

| Route or equivalent | User's question | Primary action | Boundary |
|---|---|---|---|
| `/` | What is Kalends, and why enter? | Explore worlds / Continue | Public-safe content only |
| `/worlds` | Which experience interests me? | Open one of two actual experiences | No imaginary catalog |
| `/worlds/:template` | Who would I be, and what can I do? | Begin a new life | Creates a new journal; never overwrites |
| `/your-worlds` | Where did I leave off? | Continue selected life | Local saved lives, explicit identity |
| `/lives/:id` | What is happening around me? | Interact within the world | Participant projection |
| `/lives/:id/history` | What happened to me? | Revisit a chapter / inspect support | Participant-known history only |
| `/lives/:id/reflect` | What changed, and what might I try differently? | Reflect / execute supported alternative | Not an optimal-life oracle |
| `/research` | What is demonstrated? | Read evidence and limitations | Public-safe artifact summaries |
| `/lab/:id` | What does the full simulator know? | Inspect and compare | Explicit operator/private-information notice |
| `/studio` | Can I author a supported experience? | Edit a template and validate | Experimental, finite compiler; later gate |
| `/about` | What is the longer-term idea? | Understand the thesis | Vision clearly separated from current capability |

Routes can be implemented with the existing lightweight stack. Do not add a frontend framework merely to match this table. Preserve existing endpoints and entry URLs with tested compatibility routes.

### Navigation hierarchy

Public header: **Kalends · Worlds · Research · About · Your worlds**.

A returning visitor's main action is **Continue**, not “Create account” or “Choose an engine mode.” Studio belongs in the Research/creator area initially. No pricing page, subscription flow, marketplace or unsupported account system in this release.

Inside an experience, the public marketing header disappears. Use a compact world header with title, life identity, world date, time status, and **Your story**. Research controls should not occupy permanent screen space.

## 3. Visual direction and tokens

Use **warm editorial clarity outside the world, atmospheric immersion inside it**. Keep the world as the most visually interesting object. Avoid neon networks, oversized rounded KPI cards, gradient text and constant animated particles.

### Suggested design tokens

```css
:root {
  --paper: #F5F1E8;
  --surface: #FFFDFA;
  --ink: #1C2421;
  --muted: #5B655F;
  --line: #D5DBD3;
  --action: #31594D;
  --accent: #A74B36;
  --night: #15201C;
  --night-text: #F4F0E6;
  --radius-control: 10px;
  --radius-panel: 16px;
  --content-max: 1200px;
}
```

Check contrast in implementation, including disabled, hover and focus states. These are a starting palette, not a requirement to retain colors that fail accessibility or actual scene composition.

Use one licensed serif for public editorial headings and one readable sans-serif for controls and body. Default fallbacks can be Georgia and system-ui; do not make a font download a prerequisite. Use tabular numbers only for dates, resources and research results. Do not use monospace for ordinary character speech.

Desktop headline: responsive 44–68 px. Body: 17–18 px. Product controls: at least 16 px where practical. Main prose width: approximately 60–70 characters. Use an 8 px spacing rhythm; aim for deliberate empty space rather than stretching content into every available column.

Public pages: maximum content width about 1200 px, generous side gutters, a limited number of strong sections. Experience view: occupy the viewport rather than fitting the 3D scene inside a card.

Motion targets: quick feedback around 120–180 ms; drawers around 180–240 ms; restrained scene transitions around 300–450 ms. Respect reduced-motion preferences and make transitions interruptible. These are presentation targets, not delays to insert before data is ready.

### Accessibility

Use semantic HTML, visible focus, keyboard-operable controls, correctly labelled dialogs, focus restoration, captions for meaningful audio, readable contrast, and a text-based way to understand consequential choices. Use 44 × 44 px as the preferred interaction-target design target, not as a claim that WCAG requires that exact size for every control. Avoid hover-only meaning. Support text zoom and non-color status labels. Test against WCAG 2.2 rather than assuming a tasteful palette establishes compliance. [W1]

## 4. Homepage: exact structure and copy direction

### 4.1 First viewport

Use a calm two-column composition on desktop, approximately 55% text / 45% image. On mobile, stack the introduction, action and image without placing the main action below a long video.

Small label:

**KALENDS · EARLY EXPERIENCE PROTOTYPE**

Headline:

> **Enter a world. Leave a history.**

Supporting copy:

> Make choices, build relationships, and return to the consequences. Explore two early worlds whose people and institutions keep track of what happens.

Primary button for a new visitor: **Explore worlds**.

Primary button for someone with a saved life: **Continue your world**. A secondary link still opens the catalog.

Secondary action: **See how a world remembers**. This opens a short real capture or a labelled replay of an actual saved demonstration, not generated concept art presented as a product recording.

Under the action, a concise capability note:

> Two playable prototypes. Saved locally by this installation. Worlds advance when you play or choose to advance time.

Right side: one strong actual Pompeii capture showing a person and an inhabited setting, not an architecture diagram. Use a still preview first. Load optional media only on intent. Do not load the full PlayCanvas runtime or both worlds on the marketing page. If a supplied recording omits HTML controls, capture the full experience before using it to imply those controls are visible.

### 4.2 The premise, shown through one human example

Three short connected panels, not generic feature cards:

1. **You make a promise.** A real accepted commitment, shown in human language.
2. **Someone acts on it.** An actual person-specific consequence or institutional response.
3. **You return to what followed.** A supported memory or changed opportunity.

Use a recorded demo with explicit “Example from a saved prototype life” labelling. The visitor's own state must never be populated with those example events.

### 4.3 Two worlds, honestly distinct

**Pompeii — A place in the city**

Proposed description: “Work, trade and navigate obligations in a small Roman-inspired neighborhood. Your decisions become part of your local history.”

Badges: **Historical fiction / 3D / Persistent life**. Mark the sourced setting and fictional or reconstructed microhistory honestly. Do not imply a surveyed reconstruction or a full city.

**Shared Observatory — Three teams, one instrument**

Proposed description: “Coordinate competing requests with incomplete information. Find out what your promises mean when the instrument's actual capacity is revealed through events.”

Badges: **Decision experience / Conversation and planning / Persistent consequences**. Do not imply accredited astronomy or measured training benefit.

Each card offers **Explore** and a compact list of what is actually supported. Do not invent a measured session length. A design target such as “first chapter designed for roughly 15 minutes” must be labelled and replaced after observing actual users.

### 4.4 What makes continuity visible

Show three concrete capabilities: remembered interactions, changes across simulated time, and executed alternatives. No claim of infinite life, sentience, general world generation or years of human experience in minutes.

### 4.5 Research and mission

A small, separate section: **Built alongside a research program**. Link to actual reports. State that Kalends studies memory, information and persistent consequences; do not turn negative studies into success counters.

The About section can state the larger vision: different worlds, learning through experience, and replaceable interfaces. Label these as direction. Do not put speculative neural interfaces in the product promise.

### 4.6 Footer

Working links only: About, Research, Accessibility, Data and saves, source/asset acknowledgements where appropriate. A contact mechanism should appear only when one is actually connected and authorized. No invented mailing-list submissions, testimonials, partnerships or investor logos.

## 5. Your worlds: replace the operator catalog with a place to return

The top entry is the most recently used life, identified by actual save metadata, not guessed importance. Display:

- World and participant identity.
- Actual world date and saved position/chapter.
- A small captured thumbnail if available.
- One known unresolved commitment or accessible recent development.
- **Continue** and **Your story**.
- Save status: saving, saved, error, incompatible version, or another writer is active.

Distinguish the template from a particular life. “Pompeii” is a template; “Aelia — day 8” is one saved history. Two tabs must never redirect commands to each other's life.

Never display “They missed you” or “Your world has been waiting all week” as a simulated fact. The current server does not continue while stopped. Suitable copy is **“Paused on day 8. Continue from the bakery.”** If the user chooses a time jump, say **“Advance this world by seven days”**, then summarize its actual execution.

Actions that remove or reset a life need a clear confirmation and, where supported, an export-before-delete option. New-life creation must not overwrite an existing identity. Recorded research lives should be read-only examples or copied into new journals before interaction.

An empty state should invite entering an existing world, not show empty statistics. A failed load should preserve the save and offer diagnostics, not quietly create a new life.

## 6. Starting an experience

The start screen answers three questions: **Who am I here? What is happening? What can I try?**

For Pompeii, preserve Aelia rather than creating a character generator. Use one paragraph about the actual starting situation, one recognizable person, and three available affordances. Let the player walk and look before demanding a commercial decision. Do not replace the experience with a lengthy onboarding survey.

For Observatory, introduce the coordinator's actual role, the three teams, and the capacity/commitment problem. Human display names can be authored metadata over the existing `team_a`, `team_b`, and `team_c` IDs. Give each representative a brief, stable communication style and legitimate objective. Do not invent private motives, relationships or biographies in response to a UI request.

Example proposed display labels:

- **Amir — survey team** (`team_a`).
- **Mira — instrument systems** (`team_b`, the source of the initially private report).
- **Lin — follow-up team** (`team_c`).

The exact names are editable fiction. The evidence and execution ordering are not.

Do not reveal the fragile instrument's actual state before a legitimate report or inspection. Show public nominal capacity, the disclosed order of execution, and a clear distinction between **requested**, **promised**, **allocated** and **actually delivered**.

## 7. The experience screen

### 7.1 Main composition

```text
[World / participant]           [World date · Paused]       [Your story] [Menu]

                 WORLD OR SITUATION STAGE
          Place, people, visible activity, public state

[Current intention]                        [Contextual interaction]

         Conversation / evidence / offer drawer when needed
```

The scene remains the focal area. Avoid permanent columns of inspector text, resource charts and debug controls. In Observatory, a legible instrument/capacity schedule can be the stage; it does not need another 3D renderer.

Keep information progressively disclosed:

- **Now:** the current situation and what can be done.
- **People:** who is present and what the participant knows about them.
- **Your story:** past experience and commitments.
- **Inspect evidence:** dates and sources supporting a particular claim.
- **Research Lab:** full operator state, entered deliberately.

### 7.2 Readability before ornament

Conversation uses short paragraphs and bounded choices. The main person has a portrait or in-world focus, their name, and a role. Claims such as “I checked yesterday” must have a real evidence basis. Avoid a scrolling dump of every retained memory.

Show resources relevant to the current decision. A report card should say who supplied it, when its content was observed, and whether it is direct or relayed. It should not expose hidden accounts or every NPC's goals.

Numbers should tell a story about constraints: **“You have 3 credits; a new inspection costs 1.”** Use actual values. Do not use a generic “risk 84%” score unless it has a defined, evaluated interpretation.

### 7.3 Supported action states

Every consequential action has distinct states:

**Ready → interpreting (optional) → review → committing → confirmed receipt**, or **rejected / stale / unavailable / failed to save**.

The interface must not show “Promise accepted” before the server commits and persists it. Resource changes appear from the accepted receipt, not from optimistic economic arithmetic.

Make failure useful: “The quote changed while time advanced. Review the new price.” Preserve the draft and show what changed. Never silently accept a more expensive action during automatic retry.

### 7.4 Reduce unnecessary confirmation

Public read-only navigation, opening the journal and looking at a permitted visible object need no transaction modal. Movement uses its existing validated path without a purchase-style review. Spending, commitments, disclosure of a substantive claim and other consequential actions need an explicit, legible review.

Do not bypass the current review/commit security boundary casually. Classify operations in the backend, preserve private-information protections, and add tests before changing a confirmation rule. A private report is disclosed through a valid accepted interaction, not previewed before acceptance.

### 7.5 Conversational affordances

Expose two or three relevant suggested utterances as scaffolding, plus an optional text field. Do not require exact command phrases. Do not imply unrestricted language understanding when running the offline grammar.

Examples of intent classes: ask about a dated report, discuss a promise, request a quote, propose a supported bargain, withdraw an unaccepted offer, or ask what someone remembers about a particular interaction.

Speech is not automatically commitment. “That might work” must not transfer resources or create an obligation. The proposed action should show actor, recipient, quantity, cost, deadline, source-sharing scope and confirmation status.

When language is unsupported, offer the nearest supported actions or ask a focused clarification. Do not have a character confidently promise a capability the engine cannot execute.

## 8. An authored, human first-session arc

Do not add another unrelated quest framework. Improve the existing people and mechanisms.

### Pompeii: proposed three-part experience

**Arrival and ordinary life.** Let the player observe one work routine, exchange a low-stakes greeting and learn a local constraint. A quiet moment is not filler if it establishes place, effort or a person's priorities. No reward is required for every interaction.

**A choice with a person attached.** Use the existing dispute or a smaller commitment. Make the other person's need understandable without declaring one route morally correct. Let investigation, money and obligation remain materially different options.

**A later encounter.** The person responds to an actual kept/missed promise, correction or shared experience. Give the player an available next action, not merely a numerical reputation notice. An independent NPC development should also be visible so the world does not imply that everything revolves around the player.

The content should be conditional on receipts and accessible memories, not a sequence of guaranteed outcomes. A player who declines the intended action still has a coherent continuation.

### Observatory: proposed human treatment of the same mechanics

Present a real conversation about competing work, not four resource-allocation forms. One representative has an actual dated report; another has an actual deadline. The coordinator can ask, inspect, promise and allocate. After settlement, each response must follow the delivered amount and retained evidence.

A debrief can ask “Which promise could the available evidence justify?” rather than “Did you choose the optimal allocation?” Do not reveal a uniquely correct answer when values legitimately conflict or the needed information was unavailable.

### Small content budget

Author one arrival interaction, one ordinary recurring interaction, one consequential conversation and one return encounter for each flagship participant. Reuse conditional blocks rather than dozens of near-identical variations. A professional writer or game/experience designer is a higher-value eventual collaborator here than another renderer rewrite. No hire is authorized by this brief.

## 9. A presentation layer that cannot invent history

Introduce a small **experience-beat projection**, not another world engine. It turns authorized evidence into readable moments.

Illustrative record contract; adapt to existing types:

```text
life_id, revision, viewer_id
kind: encounter | commitment | consequence | routine | correction | return
world_time_start, world_time_end
participants
visibility_scope
supporting_event_ids
claim_kind: observation | testimony | recorded_outcome | interpretation
presentation_title, allowed_factual_clauses
available_action_ids
uncertainties
```

The server constructs it from the participant projection. A renderer or model cannot inject evidence IDs or query arbitrary archived memories to make the text more compelling. Non-consequential authored character style is separate from factual life history.

Important distinction: a source/dependency link supports a claim; it does not establish that one earlier event was a necessary cause. Use **“Related events”** for traces and **“Changed under this tested alternative”** for executed comparisons.

## 10. Your story: an accessible autobiography, not an event dump

Organize history into bounded chapters derived from actual meaningful boundaries: arrival, a completed commitment, a changed affiliation, a resolved disagreement, or a user-bookmarked moment. Chapter labels must not imply unsupported career progress.

Each chapter contains:

- What the participant did or learned.
- Who was involved.
- What changed afterward, as far as the participant knows.
- What is still unresolved.
- Links to dated support.

Separate **recorded history** from **your personal notes**. A user's interpretation is not world truth and should not be fed into every agent as a fact.

Present relationship development through recognizable episodes. “Felix remembers the delivery you completed” is preferable to a large “trust +15” toast when the retained evidence supports it. Do not suppress the actual quantitative rule from LAB.

Filter mundane repeated receipts into an expandable group, but do not delete their world effects or rewrite the archive. Keep some everyday moments where the participant deliberately lingered or marked them important; importance need not equal financial consequence.

On return, show at most a few material changes, one unresolved commitment, and a clear next action. No fabricated surprise, guilt-based return prompts, streak loss or false claim that the world ran during a closed-server interval.

## 11. Time: let the person choose how to inhabit an interval

Translate internal modes into human language:

| User-facing control | Internal capability | Required explanation |
|---|---|---|
| Stay in this moment | Fine-grained participation / paused decision | Time status stays visible |
| Continue the day | Exact accelerated execution | State changes still execute |
| Advance with highlights | Exact execution plus selected presentation | Highlights are incomplete, grounded excerpts |
| Advance to… | Target-time or next-event execution | Known deadlines and possible loss of opportunities are disclosed |

Before a large advance, show the participant's **known** commitments and explain the default behavior of their character. Do not infer permission to spend, promise or repair relationships on the user's behalf. Distinguish “wait” from a future explicitly chosen autopilot policy.

### Protected opportunities

Stop before a participant-known deadline or a publicly observable event requiring a choice, when that behavior is requested and supported. Do not trigger an unexplained stop merely because the operator knows a hidden event occurred; the pacing interface must not become a private-information side channel.

A long routine may be presented in selected slices, but its actual simulation remains exact in this release unless a separately evaluated abstraction is enabled. Include optional quiet beats for anticipation, reflection or world familiarity. Do not assume that low stimulation means low experiential value.

Do not claim this improves human memory or learning yet. Event-segmentation research motivates a test, not a product fact. [H2]

## 12. Reflection and alternatives

Reflect is a contextual action in the person's history, not a mandatory exam after every conversation. Learning-focused experiences can introduce it explicitly.

Structure:

1. **What you chose.** Exact accepted action and relevant constraints.
2. **What happened.** Actual receipts, separated from speculation.
3. **What you knew then.** Restore the authorized evidence available at that decision, not current hindsight.
4. **What remains uncertain.** Missing evidence and stochastic influences.
5. **Try an alternative.** Only supported executable interventions.

The current alternative operation removes one accepted action and replays later declared commands. Label it **“Try this history without that choice”**. Do not imply an arbitrary rewritten action or optimal alternate life until those operations exist.

Show omitted action, fixed continuation policy, skipped infeasible commands, matching horizon and measured differences. Never overwrite the original life. Trial outcomes must not silently become the original NPCs' memories.

## 13. Research and Studio surfaces

### Research page

Use a readable editorial page with three questions: What is built? What did the experiments find? What is still unknown?

Provide evidence cards containing the claim, dataset/configuration, code version, independent sampling unit, result, limitation and reproduction path. Example: **“V3 and V2 tied in 432 matched pairs”**, not “New generation of advanced intelligence.” A reproduction command should come from actual packaged instructions, not a guessed shell snippet.

Keep source versions visible. Separate exploratory, preregistered, reproduced and human-tested labels. A negative result is worth displaying. Tests passed are engineering evidence, not customer traction.

### LAB

Entering operator view must warn that it reveals private information. Mark that life/session as operator-exposed for later research analysis. Do not treat a person who saw hidden truth as an unspoiled participant.

LAB can show memory records, belief revisions, plan dependencies, action receipts and counterpart histories. Default to a readable causal narrative, with raw JSON behind details. No production security claim: this is still a local single-operator environment.

### Studio

Build only after the first participant journey works. Replace raw JSON as the only authoring entrance with supported-domain forms: participants (within fixed IDs), public resources, dates, goals, evidence boundaries, costs, outcome measures and source labels. Clearly mark unsupported changes.

Preview and compile into a new identity. Keep code-required changes honest. The interface should reduce authoring mistakes, not conceal the fixed adapters behind a “Generate anything” box. No automatic untrusted script execution.

## 14. Grounded AI expression: a narrow real integration

Reuse the six existing contracts and transport. Do not create another adapter abstraction.

Separate three operations:

1. **Interpret:** turn a participant's utterance into a supported intention, uncertainty or clarification request.
2. **Decide:** a bounded policy proposes a supported action using permitted evidence and resources.
3. **Express:** render the character's supported claims and intention in natural language.

The world validator still owns execution. The expressive model may choose wording and tone; it may not introduce consequential possessions, remembered events, commitments or sources. A validated JSON envelope does not prove semantic correctness. [A1]

Use a bounded input containing character identity/style, allowed beliefs, relevant retained experiences, immediate situation, permitted actions and explicit uncertainty. Keep unsupported factual clauses out of the display or fall back to authored text. Treat automated semantic checks as imperfect and audit a sample of outputs.

Show one end-to-end live or local-model conversation only when a real endpoint is configured. Log model/version, evidence-context hash, tokens, latency, retries, validator result and accepted receipt. Separate generated expression from state-changing action. Interrupting a request must not produce a late commitment.

Without authorization, keep the existing offline path and accurately label the language capability. No claims of real-model quality from injected fixtures. No browser-side secrets, unrestricted archive access or automatic paid calls.

## 15. Frontend and runtime integration

The current architecture reloads or refreshes parts of the host after successful game requests. Audit whether those refreshes remount the iframe, steal focus or reset local state; do not assume they do without reproducing it. [K1/K2]

Implement a stable application shell around the existing engine, using a small per-life state controller:

- Key all state, pending work and caches by `life_id` and revision.
- Reconcile committed server snapshots without remounting the scene on ordinary actions.
- Preserve camera, selected character, unsent text, scroll, accessibility settings and valid UI focus.
- Abort or invalidate late requests when the life, scene or recipient changes.
- Preserve schema/state fingerprints and stale-proposal checks.
- Show pending feedback immediately, but only committed resources/receipts as facts.
- Never automatically retry a mutation after an ambiguous network failure without an idempotency/reconciliation mechanism.
- Use the existing refresh transport initially; add polling or an event stream only if needed and tested. Do not invent distributed multiplayer semantics.
- Pause redundant animation/rendering when the scene is hidden; do not advance canonical time as a side effect of rendering.
- Preserve the original 3D client route and save formats until compatibility is verified.

Collect core-web responsiveness and frame-pacing separately. INP measures browser interaction feedback; it is not backend completion time or a guarantee of continuous 60 FPS. [W2]

### Performance goals to measure, not advertise

- The public page should respond before loading a 3D world; keep its initial script and imagery budget explicit.
- Show input feedback within a frame or an immediate pending state where feasible.
- Measure p50/p95/p99 frame intervals over sustained movement and interactions on the actual device/browser, with the observed display cadence recorded.
- Measure cold/cached entry, conversation response, committing, persistence and return separately.
- For ordinary web controls, use the documented good-INP threshold as a web-shell goal; also test complete transaction latency.
- Record failures, stalls and resource growth during a complete session, not just a favorable five-input sample.

## 16. Company evidence, without pretending a website is traction

The consumer hypothesis is that a remembered history makes a curated world worth revisiting. The challenger hypothesis is that authors/facilitators value dependable private-information scenarios and debriefs. Keep both as experiments; build one shared product.

### First product observation

Prepare a formative protocol for consenting adult volunteers or an appropriate supervised program. No recruitment is authorized here. Observe whether people can identify their role, find an action, understand a consequence, recognize a remembered episode and continue without explanation. Record friction and concrete actions, not only favorable adjectives.

A small formative group is diagnostic, not a retention percentage for the market. Distinguish voluntary continuation from following an instruction to “keep playing.” Make participation optional; do not pressure people to return.

### First author/buyer observation

Prepare a small supported scenario-editing task and an interview guide: What do they use now? Where is effort spent? Who pays? Which exact result would justify switching? Observe code changes and assistance required. Do not report the conversation as a paid customer or choose enterprise positioning solely because the authoring demo is easier to measure.

### Product instrumentation

Opt-in, local-first events: session start, life entered, first accepted meaningful action, consequence viewed, history opened, return resumed, research view entered, errors, abandonment point. Include build ID, anonymous local session ID, life ID, world time and active/idle distinction. Avoid storing free-text conversations by default. Research export requires explicit scope and redaction.

Suggested product indicator: **a voluntary second session in the same life containing a new meaningful action**, accompanied by evidence the participant recognized a prior consequence. This is a proposed measurement, not an achieved metric.

## 17. Concrete release backlog

| Order | Ticket | Deliverable | Check |
|---|---|---|---|
| P0 | Existing experience audit | Reproduced friction list + screenshots | Actual browser, separate QA lives |
| P0 | Life-scoped shell | Stable identity, pending state, no remount on ordinary action | Cross-life, late-response and restart tests |
| P0 | Homepage/catalog | Exact honest copy, real previews, working actions | Every displayed capability resolves to a real view |
| P0 | Resume/history | Saved-world home, bounded chapters, supported return | No invented, private or background-progress claims |
| P0 | Observatory human layer | People, evidence, allocation/commitment clarity | Participant cannot see private report before disclosure |
| P0 | Pompeii first/return arc | Ordinary interaction + choice + later grounded response | Decline, success, failure and correction all continue coherently |
| P1 | Time interface | Clear advance/hold controls and known-deadline warning | No accidental autopilot or hidden-event alert leak |
| P1 | Reflect/alternative | Then-known evidence and honest omission replay | Original remains unchanged; infeasible later commands disclosed |
| P1 | Research page | Real claim cards and limitations | Data/commit references match artifacts |
| P1 | Grounded expression | Existing provider path exercised when authorized | No fabricated history; rejected outputs handled |
| P1 | Supported Studio | Useful forms over finite compiler | New IDs; invalid fields rejected; no arbitrary code |
| P1 | Human-test package | Instrumentation and observer guide | No invented participants/results |

## 18. Acceptance and stopping rules

A release is ready for formative use only when the main route works from a clean life without coaching, a returning life remains intact, all high-severity reproduced interaction defects are fixed or clearly block release, and at least one real consequence is readable through the human interface.

Review actual screenshots for hierarchy, not only aesthetics. Review an actual full browser journey for responsiveness, not only one successful purchase. Test keyboard-only navigation, text zoom, reduced motion, interrupted conversations, stale offers, save failure, another active writer, another tab and an incompatible save.

Do not add a third domain while these basics remain unreliable. Do not remove quiet life moments simply because they produce fewer clicks. Do not call the product enjoyable because a scripted walkthrough passed.

The next release should make **one saved life feel like a coherent personal history**, while leaving its evidence available to researchers. That is the product milestone.

## 19. Microcopy and dialogue examples

These are **authoring templates**, not claims that these exact events have happened. Resolve placeholders from authorized state. If their preconditions are absent, use another line rather than inventing support.

| Situation and precondition | Proposed wording | What must remain true |
|---|---|---|
| New saved-world screen; no life yet | “Choose a place to begin. Your choices will be saved as part of that world's history.” | Only supported templates are offered |
| Existing paused life | “You left Aelia at {location}, on {world_date}. Continue from there.” | Location/date come from the actual journal; no elapsed-time fiction |
| Team B retains a dated report | “I have an instrument report from {observation_time}. Ask to see it before you make promises.” | The report exists and is shareable; do not disclose its private value in this invitation |
| Report has not been freshly checked | “That is what the report said then. I haven't checked it again.” | Distinguish dated testimony from present truth |
| A reviewed commitment | “Promise {quantity} to {recipient} by {deadline}. This becomes an obligation in your world.” | Show real amount, deadline, conditions and confirmation |
| A promise was partly fulfilled | “You promised {promised}. We received {delivered}.” | Both numbers are settled receipts, not requested allocations |
| A character retained a successful dealing | “I remember the delivery. You said you'd bring it, and you did.” | A relevant retained episode supports the claim; the speaker legitimately observed it |
| The institutional obligation persists but the episode was forgotten | “The agreement is still open. I don't remember every detail of that conversation.” | The actor can access the institutional record but cannot reconstruct forgotten dialogue from the archive |
| A quote went stale | “The situation changed while you were deciding. Here is the updated offer.” | Highlight actual changes; never accept automatically |
| Save failed | “That choice was not saved. Your previous history is unchanged.” | Only use when the trial/save/swap contract really preserved the original |
| Entering LAB | “This view reveals information your character may not know. It is for inspecting the simulation.” | Mark operator exposure; do not silently mix private truth into normal play |
| Omission retry | “Replay this history without this choice. Later choices stay the same when they remain possible.” | Execute the declared omission; disclose infeasible later commands |

### Tone rules

Characters should sound like particular people attending to an immediate situation. Prefer a concrete observation or question over a lecture about their architecture. A brief hesitation, courtesy or change of emphasis can make language less mechanical without inventing an event.

Do not have people narrate trust scores, memory capacities or model confidence values in ordinary conversation. Do not make every exchange emotionally intense. Do not use simulated loneliness or guilt to keep the participant engaged.

The quiet return can be more important than a dramatic twist: a person recognizes a kept promise, acknowledges a correction, or distinguishes what remains in the agreement from what they personally remember. The subsequent available action must reflect that state, or the line is only decorative.
