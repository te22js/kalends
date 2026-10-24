# First-session history and copy review

Checked **24 October 2026** against the owner's
`Kalends_Onboarding_History_and_Copy_Repair.md`, the current history cards and
guide, their notebook renderer, character-status definitions, and the existing
Pompeii source ledger. This is an independent source and source-code editorial
review. It is not a native-browser walkthrough, classroom trial, accessibility
certification, or evidence that an unfamiliar person understands the product.

## Source identities and ledger reconciliation

The brief/card source IDs and the older ledger's IDs use different registers.
Bare `S2`–`S5` references must not be merged by number. The current cards attach
the correct URLs, but a reviewer comparing IDs alone can select the wrong source.
Preserve the old ledger's references; qualify card IDs or add the following
crosswalk before publishing a combined source register.

| Brief/card ID | Verified institutional page | Existing ledger equivalent | Scope |
| --- | --- | --- | --- |
| S2 | [Park: Along the streets of Pompeii][streets] | S4 | The Fullonica and Thermopolium sections support the limited workshop/counter claims. |
| S3 | [Park: Nevoleia Tyche][tyche] | New entry needed; suggest S13 | Use the documentary section about the monument and inscription, below the modern first-person introduction. |
| S4 | [Park: Being a woman in ancient Pompeii][women] | S10 | Evidence types and varied social positions; its advertised exhibition dates were 16 April 2025–31 January 2026. Treat this as an exhibition source, not an event currently running. |
| S5 | [MANN: Elections in Pompeii, on Google Arts & Culture][elections] | New entry needed; suggest S14 | Museum-authored discussion of painted electoral material and recurring inscription formulas. |

In the older ledger, S2 is the 2015 guide, S3 a 2024 performance itinerary, and
S5 an eruption-date article. None should be silently replaced. The proposed
S13/S14 additions above are a reconciliation recommendation; this review does
not edit the historical ledger or claim those entries are already installed.

## Claim-level findings

| Current card | Assessment and allowed scope | Retain the limit |
| --- | --- | --- |
| `food_counter` | Supported: the cited account describes inset vessels and a food/drink counter. [Park][streets] | It supplies no evidence for Sabina, today's stock, fictional prices or a measured game floor plan. Define *thermopolium* as a food-and-drink establishment on first use; avoid a modern restaurant analogy as a precise equivalence. |
| `fullery` | Supported: a domestic building was adapted for textile work, with washing facilities. [Park][streets] | The card's ownership caution is warranted: the older [guide, printed p.16][guide] treats Stephanus's identification as an inference. The invented worker and game wages are separate claims. |
| `freedwoman` | Supported: the monument's translated inscription identifies Naevoleia Tyche as a freedwoman. The page heading uses the variant Nevoleia. [Park][tyche] | The commemorative monument is outside this miniature district. Its prominence cannot establish typical lives, a universal route to wealth, or Aelia's biography. The imagined opening speech is modern interpretation, not an ancient recorded monologue. |
| `wall_notices` | Supported: the museum explains candidate, office and supporter information in surviving notices. [MANN][elections] | The formula can include supporters; “could name a candidate, office and supporters” is more exact than implying every notice has every field. An endorsement supplies no election result or equal political entitlement. |
| `evidence_and_fiction` | Appropriate project synthesis. The external pages support limited material claims; source files establish which game elements were invented. | Do not present the absence of this fictional conversation from the sources as a universal claim that archaeology preserves no speech. Preserve the distinction between evidence, reconstruction and fictional gameplay. |

The existing ledger's H04/H05 remain compatible with the first two cards;
H08 with electoral communication; H10/H11 with careful status portrayal; and
H19/H20 with fictional people and numerical rules. Its ownership, topography and
uncertainty qualifications remain in force. These cards do not settle the
eruption-day debate, verify every detail of the district, or validate its economy.

## Status, terminology and portrayal

“Freedwoman” is appropriately explained as a woman who had been enslaved and
was subsequently freed. The specific commemorative example and the exhibition's
varied-status account support this narrow explanation. They do not support
blanket claims about women's property, citizenship, voting, officeholding or
freedom of movement. [Park monument][tyche], [Park exhibition][women]

The code marks Chreste and Dama as fictional enslaved people, with constrained
work/movement. Aelia's paid shift must not be described as their legal or social
condition. Keep “in this fictional scenario” adjacent to Chreste's status when
copy is extracted from the card. The existing guide's explicit limit on Aelia's
invented opportunities is sound. The catalogue role “independent freedwoman”
needs the same fictional qualification; “independent” must not become a general
historical rights claim. Slavery is coercive status, not a job category or a
temporary shortage of game coins. The [older guide, p.16][guide] is comparative
context for labor, not proof of a historical worker named Chreste.

Use *cloth*, *fullery*, *counter*, *coins* and *flour units* consistently with the
actual relevant interaction. Internal grain propositions do not license a
silent commodity change in public delivery prose. *Domus*, *fullonica*, *dolia*
or an ancient office need a short definition if introduced. No new Latin
transcription, quotation, legal rule, or ancient currency conversion is verified
by this review.

## Rights and presentation metadata

The current notebook renders text, source links and an explicit photograph-rights
notice. The card module supplies original paraphrases and a text description of
schematic geometry; it imports no source image. No external image was downloaded,
reproduced, recolored or claimed as a game asset in this review. Institutional
hosting, attribution and public visibility do not by themselves supply a reuse
license. The 2015 guide also carries a distribution restriction. [Guide][guide]

Keep source title, institution, URL, checked date, relevant section and claim
limit together in the review register. Retain a text-only/no-external-image
designation for these cards. The generic runtime rights string should be read
as applying to the new card prose and specifically authored schematic props,
not as a fresh ownership claim over every existing scene asset. Any later image
needs its own creator/holder, exact object, permission/license, attribution and
modification record before inclusion. A decorative model is reconstruction;
its appearance alone does not become archaeological evidence.

Native visual matching remains unverified here: a source-code sentence that
mentions a counter or basins does not prove those features are legible on screen.
The monument card correctly avoids placing the real monument in the game. The
modern English notice structure is explicitly a teaching schematic, not an
excavated inscription. The notebook's information must remain outside NPC minds
and cannot disclose a hidden current report or complete a paid interaction.

## Complete copy-review scope and remaining gate

The current source path was read across `history_cards.py`, `guide.py`, notebook
rendering in `static/product/app.js`, relevant catalogue role text, and the
authored character introductions/uncertainty replies in `kalends_rebirth/language.py`.
The card prose uses complete sentences and separates evidence from fictional
people and mechanics. This does **not** certify every rendered transaction.

The final editorial walkthrough must read each of these paths as displayed,
from arrival to the first actual consequence in both worlds:

| Copy surface | Required check |
| --- | --- |
| Homepage, detail page, entry, guide on/off/resume | Role, goal, controls, time policy and fictional scope agree; a feature is advertised only when reachable. |
| All first-session NPC exchanges and recalled dealings | Complete sentences; speaker's own admitted/disclosable account; no new motives, hidden report, or memory-denial claim about institutional obligations. |
| Review, cancellation, confirmation and receipt | Who does what, quantity/unit, cost and later obligation agree with the accepted action; opening a conversation is not disclosure or agreement. |
| Time jump, deadline, missed opportunity and outcome | Show the executed change and a supported continuation; a pending payment/allocation is not a completed delivery. |
| Empty, missing, forgotten, stale and unavailable states | Explain a useful next step without inventing facts; check zero versus missing values, singular/plural and long names. |
| History notebook and optional reflection | All five claim/evidence/limit/fiction scopes remain readable; no mandatory quiz or claim of measured comprehension. |
| Observatory request/report/promise/allocation/settlement | Keep the four quantities distinct; derive numbers and tense from admitted reports and actual settlement. The exercise order is fictional, not an observatory standard. |
| Error, insufficient funds, pending save, stale offer and double confirmation | Say what was accepted, what remains pending and what needs review; never invite an uncertain charge or write to be blindly repeated. |
| Narrow layout, enlarged text, keyboard and reduced motion | Read complete displayed paragraphs and controls without cropping or contradictory focus/time behavior; record untested assistive technology. |

Source-level caution: the Observatory completion sentence “You can explain…”
should remain a question or invitation to reflect, even with its disclaimer.
A button acknowledgement is not evidence that a learner can explain anything.
Likewise, a chapter marked complete from an alternate route must not imply a
conversation or historical reading actually occurred. The owner reported a
failed first-session experience; source review, automated checks and a coached
demonstration cannot rebut that observation.

The human gate remains untested by this review. Record actual assistance needed
and ask an unfamiliar consenting participant to explain role, action, consequence
and one evidence-versus-fiction distinction. No learning, enjoyment, curriculum
alignment or educational-effect claim follows from this document.

[streets]: https://pompeiisites.org/en/pompeii-map/analysis/along-the-streets-of-pompeii/
[tyche]: https://pompeiisites.org/en/exhibitions-and-events/nevoleia-tyche-en/
[women]: https://pompeiisites.org/en/exhibitions/being-a-woman-in-ancient-pompeii/
[elections]: https://artsandculture.google.com/story/tgUBNHEcEscIJg?hl=en
[guide]: https://pompeiisites.org/wp-content/uploads/A-Guide-to-the-Pompeii-Excavations-2.pdf
