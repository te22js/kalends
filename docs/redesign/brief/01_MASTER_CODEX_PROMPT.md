# KALENDS — A COMPLETE PARTICIPANT-EXPERIENCE REDESIGN

Read this document together with `02_COPY_AND_FIRST_SESSION.md`, `03_VERIFICATION_AND_RESEARCH.md`, and `04_INTERACTION_REFERENCE.html`. The reference is a UI/interaction specification using fixtures, not production code or evidence that the real game works.

## The assignment

The owner wants a radical quality improvement, not another conservative wording pass. You are responsible for executing a complete participant-facing redesign inside the existing Kalends repository, backed by real browser use and scientifically honest evaluation.

The aim is an experience that feels authored, clear, responsive and inhabited, while retaining a trustworthy persistent world underneath. The comparison is the current actual running product, not its earliest schematic ancestor. Cosmetic improvements against a very old screenshot do not satisfy this release.

Work autonomously through substantial implementation, measurement and correction. Do not merely deliver a plan. Checkpoint working milestones when the execution environment ends; do not claim continuous background operation or fill hours with redundant tests. Use parallel specialists only where available and with explicit file ownership.

## 1. Non-negotiable creative direction

Kalends is a persistent world and synthetic-experience project. Its primary participant surface should feel like entering a situation, interacting with people and accumulating a history. The same underlying system can support learning and research. It should not feel like a game wrapped around a database editor, nor become a superficial chatbot town.

Use three distinct layers:

**The experience:** places, people, actions, time and visible consequences.

**The notebook:** personal history, evidence received, optional historical explanations, commitments and reflection.

**The laboratory:** private world truth, memory budgets, causal tests, metrics, sources and research qualifications.

They are views of the SAME life, never silently separate simulations. Default to the experience. The notebook is available on demand. The lab is explicitly entered and marks exposure to private information.

The rigorous internal model must stay rigorous. Its vocabulary must stop dominating ordinary participation. “Admitted,” “retained memory,” “canonical,” “supported option,” “trial preview” and numeric event IDs do not belong in a character’s mouth. Move implementation explanations to appropriate inspectors; do not remove truth, costs, source limits or uncertainty.

## 2. Baseline and safeguards

Inspect the real repository. The supplied handoff names `codex/continuity-release-prep`, implementation milestone `16cc062`, with later documentation commits possible. The local repaired build reportedly uses port 8823 and `.kalends/first_session_review`.

Read the latest handoffs, defect register, browser QA, copy review, historical source review and research report. Launch fresh isolated QA lives. Preserve user lives, old research, runtime revisions and the release ref. Record the exact baseline commit and asset hashes. The handoff reports no Git remote; create a local recovery bundle or equivalent safe backup, and do not mistake a local branch for an off-machine backup.

Do not overwrite history to simplify a migration. Existing event hashes and historical research must remain reproducible. New behavior must have declared versioning and new-life/default semantics. No public deployment, purchasing, outreach, credentials exposure, repository publication or paid inference without explicit authorization.

Perform one full naive walkthrough before coding. Capture the complete viewport including HTML HUD/dialogue, not just the canvas. Record a defect or friction list with reproduction, cause and expected behavior. Label subjective judgments as judgments.

## 3. Plan, challenge, then build

Save `REDESIGN_EXECUTION.md` with a concise plan, dependencies, file ownership, frozen scope and acceptance gates. Have a separate reviewer challenge it for implementation risk, player clarity, scope drift and evidence integrity. Revise once before the first substantial implementation. Do not recursively generate plans instead of executing.

Build in this order:

1. Persistent scene/shell and participant-language separation.
2. One fully redesigned Pompeii first session.
3. Observatory as a deliberately different, clear decision experience.
4. Notebook/history/historical learning integrated with the actual places and choices.
5. Art direction, motion, NPC presentation, audio and complete browser testing.
6. Research-status correction and a bounded agent-cognition evaluation where feasible.

If multiple agents are available, isolate visual/client work, copy/tutorial work, backend/persistence work and independent QA. One integration owner controls protocol changes. Preserve the runnable build after each phase.

## 4. Redesign the site, not only its colors

### Homepage

Use one dominant actual world capture and a clear entry, not a six-card technology grid. The header is Kalends, Worlds, Your story, Research. Studio is an expert destination, not the main call to action. About should explain the long-term synthetic-experience thesis separately from delivered capability.

Lead with the available experience: “A morning in Pompeii.” Supporting copy explains the fictional Aelia, the disputed delivery and the choices the participant can actually make. A secondary entry offers Shared Observatory as a coordination exercise. Do not promise unlimited lives, arbitrary world generation, continuous offline simulation or learning improvements.

For a returning participant, prioritize their saved life and actual unfinished situation. Never fabricate developments during real-world absence. No account wall, subscription mockup, fake player count or nonexistent social proof.

Use the supplied reference for typographic hierarchy, whitespace, conversation composition and review placement. Its CSS landscape is deliberately a placeholder. Do NOT ship it as upgraded game art. Use the existing real PlayCanvas scene and legitimately licensed assets, with a better camera and scene composition.

### World entry

An entry needs one role, one immediate situation and one primary action. Keep a short factual qualification about historical fiction; put the fuller evidence boundary in a readily accessible detail panel. No essay about memory systems.

For Pompeii: “You are Aelia. A flour cart has arrived, but two buyers claim it. Start by hearing Sabina’s account.” Define freedwoman clearly in the role explanation; do not make one fictional life representative of all historical women.

For Observatory: “Three teams need one instrument. Find out what it can deliver, divide its capacity, and see whether your promises can be kept.” Explain the simplified unit without introducing unsupported real astronomical assumptions.

### Stable shell

Entering a notebook, opening a historical card, reconciling a receipt or returning from research must not reconstruct the world view unnecessarily. Preserve camera, conversation, selected character, drafts and selected life when appropriate. Distinguish server-persisted choices from tab-local drafts. Do not claim draft durability that is not implemented.

The correct life ID must remain in every request. Test two lives in adjacent tabs. Research exposure must not grant NPC knowledge or leak private projections back into the normal DOM.

## 5. A deliberately quieter visual language

Use warm limestone/paper surfaces outside the scene, dark readable text and restrained bronze/green accents. Use one licensed editorial display face and one highly readable interface face if assets permit; system fallbacks are mandatory. Do not add fonts to source without licensing records.

The world should occupy most of the experience area. A small persistent HUD shows current place/time, purse where relevant, notebook/help and a concise time state. One immediate goal is visible while the guide is on. Do not simultaneously show five headings, a policy explanation, evidence, routine history and every available option.

At desktop, dialogue can occupy a compact side panel or bottom region without occluding the people. At narrow widths, switch deliberately to a readable sheet with the speaker/context still understandable. Never require nested scrolling through several unrelated panels to find the primary action.

Use 16–18 CSS-pixel default body text, comfortable line spacing and readable contrast. Keep primary actions large enough for touch and keyboard focus. Exact dimensions should follow measured layouts rather than treating a screenshot as universal.

Motion serves orientation: brief panel transitions, smooth camera handoff, natural turn-to-speaker, a clear approach/arrival, a brief state-change response. No delayed typing animations required to read a sentence, autoplay camera drama, excessive bloom, or always-moving decorative backgrounds. Respect reduced motion and mute.

A successful graphical change needs new matched captures of the same scene, camera and time on the same machine. Improve materials, human scale, silhouette, lighting, occlusion, entrances, animation and framing before increasing asset count. Do not swap game engines again.

## 6. Replace form-like conversation with actual turn-taking

The current catalog can show opening speech, role prose, goal fragments, memory diagnostics and action descriptions together. Replace this with a conversation presenter that accepts typed semantic content and chooses the right speaker/channel.

A normal exchange has:

- A clear speaker and a natural short statement.
- Two or three contextually relevant replies/actions; other actions remain reachable.
- An optional evidence link when the statement needs grounding.
- A clear way to stop talking and return to the same scene.

Ordinary characters speak in first-person modern-readable English, not model diagnostics or historical lectures. No pseudo-archaic performance. Personality should appear in what matters to them and what they choose, not a proverb in every response.

Implement separate presentation components for:

1. Character speech.
2. Participant action choices.
3. Transaction/time review.
4. Outcome receipt.
5. Guide prompt.
6. Historical context.
7. Research data.

Do not display internal field names as a fallback. Unknown states should receive a neutral useful response and a diagnostic log for developers, not leak raw JSON or IDs.

### Confirmation policy

A participant clicking “What happened to your order?” has already intentionally asked. When listening is free, creates no external obligation, and the recipient is permitted to answer, perform the same validated observation action in one explicit interaction. Keep authoritative validation and ledger admission; remove the extra administrative review modal.

Do not achieve this by previewing hidden information before authorization. The click is the committed request. If disclosure has a fee, social cost, irreversible sharing consequence or time cost requiring a choice, show those terms first.

Retain meaningful review for spending, work, promises, public testimony, changes to relationships/affiliations, consequential travel/time jumps and irreversible actions. A direct question must not silently become any of those.

Proposals may expire. Preserve draft input, show the changed terms and require fresh confirmation when necessary. Never encourage blind retries after a possibly accepted charge. Duplicate input must not duplicate transactions.

## 7. The first Pompeii scene must teach by doing

Use the current cart story and known characters. No new district is needed.

The scene begins beside an actual relevant place and a clearly identifiable Sabina. A cart, people and visible work establish the situation. A short line or visible exchange raises the problem. It must be derived from the existing initial world, not new secret facts.

Teach movement by moving toward a visible destination. The guide changes only when legitimate progress occurs. Show a prompt at arrival, not before. Talking to Sabina produces her account. Looking at her order produces an admitted evidence card. The notebook records that account as hers, not objective proof.

Teach the difference between testimony and evidence through those interactions, not a paragraph about provenance. The next goal is to obtain another account or deliberately choose an available route. Do not railroad completion or mark unread documents read.

Let a player ignore, decline, arrive out of order, leave, return or run out of resources. Show a valid alternative next step rather than repeating the same generic hint. If Dama’s position is not known, do not put a live private tracking arrow over her; give an admitted sighting or public meeting place and the supported Lucius alternative.

Important: the market route is a choice to prioritize market recipients, not simply to honor Sabina’s two-sack order. The supplied catalog shows a four/two market split and a different household agreement. Explain the tradeoff in plain language; never quietly equate different routes.

After a confirmed action, show actual movement/delivery effects where the world supports them, then a brief outcome and a genuine character response. Do not announce unseen mental states. Evidence and accounting remain one click away.

At the end of guidance, provide two relevant possibilities derived from the present state. “Explore more” alone is inadequate. Avoid requiring more quizzes or fictional rewards to finish the tutorial.

## 8. Historical learning must be experienced, not dumped

Keep a short introduction to evidence/reconstruction/fiction. On individual cards, provide the specific limit without repeating a general disclaimer in every dialogue turn.

At a counter, let the participant examine the represented feature, identify what it suggests, and read a concise historical explanation. In the fullery, point to the relevant washing feature. If the current geometry does not visibly support the teaching claim, improve the representation or change the prompt. Do not ask users to identify an object that is absent or illegible.

A card should have three layers:

- First view: one observation, one clear historical idea, optional question.
- “How do we know?”: source, evidence type and relevant limitation.
- “What we invented”: the specific fictional people/mechanics and reconstruction caveats.

No compulsory test score, historical expertise claim or invented ancient quote. The modern notebook does not install knowledge in an NPC’s mind. Do not add modern political rights or legal permissions merely because they make play easier. Explain slavery without euphemism or graphic presentation.

Reconcile source identifiers across registers; the supplied source review says S2–S5 refer to different items in the older ledger. Qualify IDs and retain a proper crosswalk rather than silently renumbering historical artifacts. Recheck claims and image licenses before adding content. A publicly visible museum image is not automatically reusable.

Historical learning remains part of Pompeii’s purpose. Do not erase it to make the product more game-like. Do not label the entire economy historically calibrated merely because buildings and several facts are sourced.

## 9. Shared Observatory should be a clear decision room

Do not mimic Pompeii’s spatial adventure in the Observatory. Give it an instrument/capacity overview, people with roles, dated reports, a usable allocation surface and a result that explains itself.

Reveal the workflow as it becomes relevant:

Read requests → seek information → choose allocation → optional promise → run round → compare actual delivery.

Maintain the four values separately: requested, promised, allocated, delivered. Unknown is not zero. Rated capacity is not the current hidden condition. An old report is not automatically false; a report just received at the current time is not generically “stale.” Source and age are visible, and uncertainty appears when relevant.

Use accessible numeric controls plus a visual capacity budget, not dragging alone. Show a conditional excess warning based on the participant’s available information. Do not reveal actual hidden capacity in a pre-action preview.

The catalog shows requests of two while a project needs four. Audit this with the actual policy. If coherent, explain the difference from permitted evidence and give it real decision relevance. If the policy is economically incoherent, document and version a targeted rule correction instead of inventing a narrative rationalization.

Confirm the actual saved allocation and promises when running the round. Editing a draft must not change committed terms. Present times as the domain’s readable date/clock, with raw ticks only in the lab. The one-minute gap between settlement and the next round must not force a bewildering sequence of generic modals.

On settlement, animate actual delivered quantities, state which project completed, and explain a shortfall using the declared public order. A short result is primary; a table and trace are secondary. Never force the over-allocation failure just to demonstrate a lesson.

## 10. Make routines visible without inventing activity

Audit whether static NPCs result from paused time, sparse schedules, hidden update subscriptions or animation-state bugs. Do not substitute random wandering for independent agency.

A scheduled duty should have a valid destination, a rendered path, an arrival and the appropriate work animation. Avoid teleportation across the displayed street, skating feet, character overlap that blocks interaction and generic gestures unrelated to state. No full crowd simulator is required for six people; fix the actual contacts and routes first.

Separate display time from world time. Idle animation may continue while reading pauses the world; do not show transactions, deliveries, conversations or new knowledge being created cosmetically during that pause. Clearly indicate time mode. After leaving conversation, restore the previous explicit mode rather than silently accelerating.

Retargeting, keyboard taps, clicking another NPC during movement, opening Help mid-route, scene changes and resuming after notebook use all need real browser testing.

## 11. Treat personal history as a product feature

Your story should show a few meaningful chapters, not every raw event expanded into a card. A chapter has a human title, what the participant did, the observed consequence, unresolved matters and evidence on demand. Routine events remain accessible without overwhelming the main reading path.

Store the history, do not invent an autobiographical narrative. A character who has forgotten an episode must not be written as remembering it. An institution can still retain a debt or agreement. Preserve that distinction.

Returning to the same saved life should show the real last situation, not a fabricated absence. Do not promise that the world ran while the local server was stopped. When advancing time deliberately, show known obligations and protect intervention windows according to participant-visible information.

Deliver one return encounter where a legitimate earlier choice changes what a character says or offers. Test an alternative that removes the originating choice and produces an appropriately different response. Do not hardcode a flattering “I remember you” scene disconnected from cognition.

## 12. Use AI where it earns its cost

Reuse the existing provider interfaces. No further transport framework is needed. Keep deterministic code authoritative for actions, accounting and state.

For a configured, authorized endpoint, evaluate one foreground character’s complete loop: understand a natural request, retrieve legitimate context, produce scoped speech or an allowed proposal, validate, commit an action if explicitly authorized, and recall the consequence later.

Separate claims from expression. Source IDs must be accessible and support the claim, not merely exist. A model may vary tone; it may not invent prior meetings, prices, objects, offers, memories or another character’s private evidence. Structured JSON is not proof of semantic correctness.

For ordinary fixed scenario dialogue, strong authored writing is acceptable and often preferable to unnecessary generation. For unanticipated input, clarify narrowly rather than return a motivational generic sentence. No replacement of a user’s unrelated question with a state-changing action.

Keep the pilot disabled until an authorized endpoint and numeric cap exist. No inference authorization is implied by “make it amazing.” Do not paste or export secrets. If unavailable, complete the offline quality work and mark live conversational quality untested. Do not write another roadmap instead of the offline improvements.

## 13. Maintain a real, separate research track

The newest held-out study found candidate/V3 ties, not a new win. Keep both the prior narrow positive result and this limitation visible in Research. Do not use test counts, cosmetic changes or successful scripted dialogue as intelligence evidence.

The next useful scientific work is error diagnosis of the frozen result: identify whether the all-arms failure is missing evidence, an impossible objective, bad encoding/retention/retrieval, controller limitation or evaluation error. Use development/debug clones. The exposed held-out tasks cannot be silently reused as an untouched final test.

Any new memory comparison keeps the controller fixed, counts all accessible memory/plans/indexes/context and compares legitimate information access. Use provisioned dense retrieval only if actually available and measured. Do not relabel hashing as embeddings.

An independent review agent is useful but not independent external replication. Eight workflow structures with twenty noise seeds do not become 160 unrelated task designs. Report that distinction.

A bounded optional live model evaluation measures coherence, invalid-action rate, leakage, temporal correction, grounded recall, latency and real usage cost. Human comprehension/enjoyment/learning require separate consenting users. No unrequested recruitment or fabricated participants.

Do not make publication claims from this release. The product work and research work have separate scorecards.

## 14. Definition of done

This release is not complete at the first attractive screenshot or passing unit test.

Required artifacts:

- Working redesigned journey in BOTH existing worlds.
- One current top-level launch command; clear build/port and save identity.
- Actual before/after captures of the same states, full HTML and scene included.
- Preferably an actual full-interface recording. If unavailable, explicitly report it rather than use a canvas-only capture as complete evidence.
- Copy matrix showing actual rendered sentences, conditions and source fields.
- The complete first-session browser paths, including alternative/mistake/reload paths.
- Matched movement/frame/callback measurements with environment and recording effects disclosed.
- Frozen research disposition and actual model status, not promised capability.
- Save/replay preservation, historical source reconciliation and asset license inventory.
- A concise final handoff separating implemented, directly tested, inferred and untested.

Use `03_VERIFICATION_AND_RESEARCH.md` as the release checklist. Run the real browser, not only fake DOM tests. Make at least two corrective visual/interaction passes against current captures. Have a fresh reviewer follow the displayed instructions without the scripted solution; this is an agent usability probe, not a human playtest.

Human-release targets are provisional: an unfamiliar person can explain their role, start an action, find the relevant person, make a choice, describe the consequence, and distinguish one supported historical fact from game fiction without coaching. Record help requested and failure points. Do not infer understanding from clicking “I understand.”

## Final priority

The participant should feel they met someone, did something and left a history—not that they approved a chain of database transactions.

Be uncompromising about composition, language and friction, and equally uncompromising about simulation integrity. Redesign the experience deeply. Preserve the world beneath it. Execute, inspect, repair, then deliver evidence.
