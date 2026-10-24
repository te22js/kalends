# Exact copy and interaction direction

All new lines below are proposed copy, not quotations from an implemented build. Bind them to legitimate state. A natural-sounding statement with the wrong epistemic meaning is a regression.

## A. Establish five voices

| Voice | Purpose | Example | Must not contain |
|---|---|---|---|
| Person in the world | Express their knowledge, needs and response | “I paid for two sacks. Can you look at the order?” | Internal memory IDs, current hidden state, invented prior meetings |
| Guide | Help the participant do the next thing | “Ask Sabina about the cart.” | A paragraph about accepted-command semantics |
| Transaction | Make a consequential commitment understandable | “Pay 3 coins. This takes 20 minutes.” | Undisclosed obligations or guaranteed outcomes before execution |
| Historian/notebook | Connect the scene to limited supported knowledge | “Large jars were built into the counter.” | Invented ancient testimony or unsupported general social rules |
| Laboratory | Explain mechanisms and evidence | “This episode was evicted; the obligation remains in the institutional register.” | A claim that a successful demo establishes general intelligence |

## B. Specific remaining-copy corrections

Source cases refer to the supplied copy_review.html. Its formatter strings do not prove every one is currently visible in the production renderer; inspect the actual route before changing it.

| Case | Existing text/problem | Proposed presentation | Semantic condition |
|---|---|---|---|
| 005 and other characters | “We have no consequential shared dealing in my retained memory yet.” | “I don’t remember us doing business before.” | Only if absence of retained shared dealings supports lack of recall. Do not replace with “We have never met.” Check institutional obligations before implying none exist. |
| 005 | Goal fragment: “Have enough flour…” plus “For now, I must…” | “I need flour for the counter. For now, I’m working with what I have.” | Only when actual goal and stock state support both clauses. Keep model goal keys in LAB. |
| 006 | “Review this supported action…” before listening | Clicking “What happened to your order?” executes the validated, free disclosure and shows the answer. | Free low-risk answer only. Paid/private onward disclosure or other consequences still need meaningful review. |
| 006 / 033 | “New observations and private results are never disclosed in a trial preview.” | Remove from normal interaction; explain relevant terms instead. | The preview restriction remains enforced in code. |
| 013 | Same privacy sentence replaces three unrelated replies | “I can show you the loading record. Checking it costs one coin.” | The price and action must actually exist. Answer the requested topic; do not reuse this for unrelated questions. |
| 018 | “Sabina’s recorded regard for you improved…” | Show the actual delivery, then Sabina’s grounded response if observed. “You helped get the flour here. Thank you.” | Only after the actor observes the consequence and a validated response supports it; do not reveal Lucius’s private reaction remotely. |
| 027 / 041 | “The proposal is stale or already consumed.” | Distinguish “That action already went through,” “The offer changed,” and “We could not confirm the result.” | Require different typed backend outcomes. An ambiguous status must not invite a duplicate paid retry. |
| 030 / 034 | “Deadline minute 1440”; “dated minute 0” | “Due at the start of Day 2”; “Observed today at 00:00.” | Respect the domain’s clock origin and boundary ordering. Pompeii uses its own displayed start time. |
| 034 | A just-received current report always “may be out of date” | “Mira observed eight usable units at 00:00.” Add an age/change warning when relevant. | No guarantee that a report remains true until settlement; do not label a current observation stale automatically. |
| 040 | “This is an optional reflection, not a measured test result.” | “What would you change next time?” with “Skip reflection.” | The research disclaimer belongs in study information / Research. No automatic comprehension score. |
| 047 | “Insufficient owned credits” | “An inspection costs 1 credit. You have 0.” | Use actual public price and actor-owned balance. Add a relevant free alternative only if genuinely available. |
| 049 | Generic pep talk when memory is absent | “I don’t remember that conversation.” Or ask a specific clarification. | Only when that is the real reason. Do not use it to deny a durable obligation or to evade an unrelated question. |
| Many | “Another supported route,” “actual,” “recorded,” “real” everywhere | Use ordinary action words; reserve precision words for genuine ambiguity. | Ordinary presentation never overrides validation. |

A person’s speech may be uncertain without sounding like a diagnostic. For instance: “Dama told me the household ordered four sacks. I haven’t seen their order myself.” This is acceptable only if that message and source are accessible. It must not be invented to enrich dialogue.

## C. Pompeii: the first interaction, beat by beat

### 1. Arrival

Main text:

> You are Aelia.
> A flour cart has arrived, but two buyers claim it. Start by hearing Sabina’s account.

Secondary role explanation:

> Aelia is a fictional freedwoman: she was enslaved and later freed. Her particular work and choices were invented for this experience.

One primary action: **Begin**. One secondary action: **Explore without a guide**.

The character and relevant meeting place should be visible. The default tutorial does not autoplay world time. Use a small “Reading pauses time” indicator. Expanded help explains movement/action costs. Do not repeat the entire time policy at every step.

### 2. Approach

> Speak to Sabina.

Use an on-scene highlight for a currently visible person. Click-to-walk should move to a valid conversation distance, with an explicit arrival state. Keyboard controls remain available. If the person has moved out of sight, transition to the last known/public meeting-place instruction, not a private-position tracker.

### 3. Listen

Proposed Sabina line:

> “I paid for two sacks. Now the household is asking for the cart. Can you find out what happened?”

Responses:

- “What happened to your order?”
- “May I see what you paid for?”
- “I’m just looking around.”

These are alternative natural entry points, not three obligations. A question should not open an administrative permission form when nothing is being spent or promised. The selected question becomes a real server-validated disclosure. The reply must not appear until the action succeeds.

### 4. Evidence as an object

Show a compact document card:

**Sabina’s order**

Two flour units ordered. Four coins advanced to Marcus.

**Received from Sabina · This is her account.**

Use “sacks” only if one model unit is explicitly represented by one sack in this domain. Do not switch commodities or units casually. The written document is fictional; an unobtrusive document-type label or notebook note makes that clear. An expandable source pane exposes event provenance.

Next: **Hear the household’s account.** Secondary: **Review the choices available now.** A player may choose uncertainty; the guide does not claim evidence was obtained when it was not.

### 5. Compare, don’t interrogate a spreadsheet

The notebook shows the two received accounts side by side, with who provided them and when. It does not supply a hidden third record. A missing record is a clearly described opportunity, not an empty table.

The market route, household route and evidence-based arrangement are not equivalent. Label each with whom it prioritizes and its real cost/obligation. The market route currently sends four units to Sabina and two to Felix; Sabina’s original order is for two. The player must understand that choosing the market is a new priority decision, not simply reading the original orders correctly.

### 6. A consequential review

**Pay for the market delivery?**

> This arrangement sends four flour units to Sabina and two to Felix. The household loses priority under this route.

| Term | Display |
|---|---|
| Payment | 3 coins · You have the actual current amount |
| Time | 20 minutes |
| Distribution | Sabina 4 · Felix 2 |
| Household payment | Refund according to the current route’s rules |

Buttons: **Keep looking** and **Pay 3 coins**.

The primary button is a real commitment, not “Continue.” The UI must account for changed stock, newly due commitments and stale offers. It may preview terms but not claim a future delivery already happened.

### 7. Result and continuing life

After the actual receipt:

> The delivery arrived. Sabina received four flour units, and Felix received two. You paid three coins.

Only assert completed quantities from the receipt. If partial or failed, say so in the same clear structure. Avoid a success animation on failure.

Show the relevant visible consequence in the scene and an observed character response. Give the participant a concrete next opportunity based on actual state, not only “Continue exploring.” Example: current paid counter work or a visit to the fullery, if truly available. No invented reward or second quest required.

## D. History taught through the environment

Use a factual observation as the primary content and the methodological distinctions one level deeper. The existing accurate source boundaries should become readable, not disappear.

### Food counter

First view:

**Look at the counter.**

> Large jars were built into the serving counter at the Thermopolium of Vetutius Placidus. These surviving features help us understand how the place was used.

Optional prompt: **Which part of the counter supports that interpretation?**

Expandable:

- Evidence: the Archaeological Park’s account of the counter and inset vessels.
- Reconstruction: the simplified scene, color, materials and modeled arrangement.
- Fiction: Sabina, the stock, prices and this dispute.

Only use a visible-object prompt if the object is actually rendered and recognizable. Otherwise present the explanation without pretending an observation is possible.

### Fullery

First view:

**A house adapted for work.**

> The Fullonica of Stephanus was adapted for processing cloth. Washing facilities help distinguish its workshop use from a home used only for domestic life.

Keep the qualified ownership attribution in evidence details. Do not show a historically unsupported named worker as an excavated person. Paid work offered to Aelia is not equivalent to the conditions of the fictional enslaved workers.

### Social status

Define freedwoman once clearly. A person’s status is a real social constraint in the setting, not a decorative occupation or a source of gamified spectacle. The source example about Naevoleia Tyche illustrates one documented person, not a typical route to prosperity. Keep her monument out of this miniature district unless separately built and located accurately.

### Political notices

“Notices could name a candidate, the office sought and supporters.” Use the conditional wording recommended by the source review. The card does not implement an election or confer voting rights. Any modern schematic must be labelled as a teaching illustration, not an ancient transcription.

## E. Observatory first round

Opening:

> You coordinate one shared instrument. Three teams need it today. Ask what it can deliver, choose an allocation, and check what each team receives.

The main object is a capacity band. Before a report: **Rated capacity: 12. Current condition unknown.** Do not show eight translucent “actual” units underneath; that would leak the answer.

After legitimate report disclosure:

**Mira’s report · Observed today at 00:00**

> “The instrument is running at reduced capacity: eight units.”

Do not invent who observed it firsthand if the report is relayed. Preserve the actual source and receipt time separately in the evidence detail.

Each team has a name, role, public project requirement, deadline and received request. If its request is below its completion threshold, the UI must explain the policy only where supported, and researchers must check whether the policy makes sense. Do not silently assume two units are useless if partial work has a modeled benefit; inspect the actual reducer.

Use one allocation editor, not separate fields on several pages. Saving changes planned allocation, not actual delivery. A promise is a distinct optional commitment, never inferred from a slider.

Review example:

> You allocated 12 units, but Mira reported 8 available. If that condition remains, later teams may receive less.

State the public ordering. Allow deliberate risk if the domain permits; do not force a correct or incorrect lesson.

Result for the known 4/4/4 fixture:

**Lin did not receive the four units you promised.**

> Eight units were available. Amir received four, then Mira received four. None remained for Lin.

Follow with an accessible small allocated/delivered table, not a paragraph repeating every qualifier. Distinguish project completion from kept promises. Afterward, allow reflection, a real executed alternative and another round, with any actual one-minute boundary advance explained naturally.

## F. Copy acceptance rules

Every rendered string is reviewed in its actual state, not only in a backend catalog. There must be no raw action ID, unset placeholder, numeric actor ID or broken sentence in the ordinary participant path. Historical statements retain sources. Error messages name the failed operation and safe next step. Uncertain execution states do not encourage duplicate spending.

Use context-specific empty states. Avoid generic motivational filler, repeated aphorisms and blanket declarations about memory accuracy. The goal is ordinary, specific speech—not “human-sounding” decorations.
