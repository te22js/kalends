# Pompeii: historical evidence and reconstruction ledger

**Checked 21 October 2026.** This ledger constrains the playable district; it
does not certify a complete reconstruction of Pompeii. Ancient evidence is
uneven, and a modern official interpretation can still contain uncertainty.
Original game art is interpretation, not a photograph of the past.

## Evidence labels

| Label | Meaning | Player-facing group |
|---|---|---|
| A — archaeology | Excavated structure/object and its recorded context; function can remain interpretive | Attested, with qualification |
| T — contemporary text | Inscription, document or near-contemporary literary testimony; genre, date and transmission matter | Attested, with qualification |
| R — scholarly reconstruction | An argued interpretation combining evidence; not direct observation of ancient behavior | Plausible reconstruction |
| P — speculative interpolation | Compatible design assumption without specific evidence for this person/place/day | Plausible reconstruction, explicitly speculative |
| F — fiction | Invented character, objective, event, dialogue, mechanic or alternate history | Synthetic |
| U — uncertain/contested | Identity, function, date or inference disputed/insufficiently established; can accompany another label | Uncertain |

Claims need an ID, source, supported scope and a restriction. A source citation
does not license unrelated dialogue, an invented biography or arbitrary numerical
economics. Tag composites at the weakest relevant level: an attested building
containing a fictional transaction is **A + F**, not wholly attested history.

## District and topology

Use the Via dell'Abbondanza / Regio I neighborhood, with three attested building
anchors and a public street. The Park's [official map][S1] and [guide][S2] support
their location within Pompeii; the [2024 itinerary][S3] explicitly lists the
addresses. The game is a compressed street network, **not a surveyed floor plan**.
The Forum is an off-map destination, not the square outside every doorway.

| Node | Evidence / function | Proposed screen coordinate | Traversal rule |
|---|---|---:|---|
| Via dell'Abbondanza | A/R: principal street; local commerce and encounters [S4] | (50,35) | Shared public street node; continuing west is off-map access toward the Forum. |
| Fullonica of Stephanus, I.6.7 | A/R: textile processing in a converted house [S2 pp16, S3] | (27,43) | Access through the local street; no invented passage into another business. |
| House and Thermopolium of Vetutius Placidus, I.8.8 | A/R: food/drink counter with domestic space [S2 pp23, S3] | (76,43) | Public counter separated from restricted domestic rooms. |
| House of Menander, I.10.4 | A/R: substantial residence [S2 pp20, S3] | (43,76) | Reach via the adjoining street network south of Abbondanza; household entry can require permission. |
| Optional bread/store counter | F: gameplay service, no claimed ancient address | Chosen for legibility | Clearly fictional; do not call it an excavated bakery or relocate a real bakery here. |

Coordinates, room dimensions, travel duration and connecting bends are **F/P**
screen abstractions, without compass, metric scale or claimed direct adjacency.
Do not turn the fullery into a granary. An attested bakery elsewhere in Pompeii
does not establish one at I.6.7, I.8.8 or I.10.4.

## Claim-level ledger

| ID | Design claim | Class / support | Constraint on implementation |
|---|---|---|---|
| H01 | Pompeii was destroyed in the Vesuvius eruption of 79 CE | A/T; Park chronology and dating discussion [S5,S6] | The exact calendar day remains debated. |
| H02 | “24 October” is an unquestionable corrected eruption date | **Rejected**; U [S5] | Display “79 CE; exact eruption day debated.” A chosen chapter date is a scenario assumption. |
| H03 | Regio/insula/door addresses identify the selected buildings | A/R [S1–S3] | These are modern archaeological indexing conventions, not spoken ancient postal addresses. |
| H04 | Fullery basins and altered domestic architecture support textile work | A/R [S2 p16, S4] | Render washing/work areas; exact workload, wages and opening hours are P/F. |
| H05 | The thermopolium has a serving counter, inset vessels and household religious imagery | A/R [S2 p23,S4] | Exact daily menu, stock and prices are not established by the counter alone. |
| H06 | Menander is a modern house-name associated with a depicted playwright | A/R [S2 p20] | Do not portray Menander as its Pompeian resident or treat modern house names as secure ownership records. |
| H07 | Attribution of a house or shop to a named owner is interpretation | R/U [S2] | Keep “traditionally associated with” where ownership/person identification is inferred. |
| H08 | Political notices were painted on walls; elections and officeholding existed | A/T [S7, electoral inscriptions] | A local notice is not a modern online ballot or universal suffrage system. |
| H09 | Wealth and status affected public standing and household access | A/R [S4,S8] | Do not give every citizen equal institutional power merely for interface symmetry. |
| H10 | Enslaved labor was coerced and distinct from wage employment | A/R [S2 p16,S9] | Do not label enslaved characters ordinary paid employees or imply freedom of movement/exit. Do not infer every worker's legal status from their occupation. |
| H11 | Women included elite patrons, freedwomen and enslaved people, with varied resources and constraints | A/T/R [S8,S10] | Neither erase women's economic agency nor grant all women identical modern legal/political rights. |
| H12 | Eumachia's inscription and benefaction exemplify female civic/religious prominence | A/T/R [S4] | It is an example, not a generic career automatically open to every woman. |
| H13 | Julia Felix's rental inscription supports property-letting activity | T/R; CIL IV1136 discussed in official exhibition catalogue [S8] | It does not validate modern tenancy law, standardized deposits or the game's contract formula. |
| H14 | Elite domestic hospitality could serve social/political networks | A/R; excavators' analysis [S11] | Patronage is asymmetric dependence/obligation, not a modern “friendship points” reward system. Specific favors and people are F. |
| H15 | Household cult and commercial activity could coexist | A/R [S4 thermopolium] | Material religion is not a magic buff or a claim every resident held identical beliefs. |
| H16 | Materials include masonry, plaster/paint, pottery and metal objects | A [S2,S7] | Colors, intact roofs and furnishings are reconstructions; modern ruins are not the ancient lived appearance. |
| H17 | Repairs and alterations are visible in the archaeological record | A/R [S7] | Do not attribute every repair to one earthquake or fabricate a universal rebuilding deadline. |
| H18 | All named characters on an official reenactment itinerary are securely attested residents of those houses | **Rejected**; S3 is a June2024 performance itinerary | Actor labels such as Emilia, Lucio or Gaius are not sufficient ancient evidence. |
| H19 | Game NPC names, errands, promises, private beliefs and specific conversations | F unless separately documented | “Historically appropriate name” does not mean “historical individual.” |
| H20 | Grain prices, the one-coin inspection fee, delivery payments/penalties, trust thresholds and scheduled supplies | F | Inherited/synthetic balancing rules; no calibrated ancient market claim. |
| H21 | A player action changes an attested ancient person's actual biography | F alternate microhistory | Display simulation/counterfactual status. The real historical record is not rewritten. |
| H22 | Pompeii's destruction was followed by no further human activity | **Rejected**; recent excavation evidence [S12] | Do not equate a preserved destruction horizon with timeless untouched completeness. |
| H23 | Public fountains existed in Pompeii | A/R; official guide describes one at the Triangular Forum entrance [S2 p110] | This supports public water infrastructure, **not** the game fountain's exact Regio I location, dimensions or functioning on a chosen date. Its screen placement is P/F. |

## Text, violence and representation

Pliny's letters are retrospective literary testimony, not a complete eyewitness
record of events inside each Pompeian house. The Park's dating analysis examines
the manuscript date and archaeological arguments; uncertainty must survive into
the calendar. [S5] The 2018 charcoal inscription is evidence relevant to the
debate, not a license to announce an exact autumn date as settled fact. [S6]

Represent slavery and unequal citizenship/status as real constraints without
gratuitous harm, sexual content or gamified cruelty. Initial play can use an
adult free visitor of modest means; this makes some choices accessible without
claiming all residents shared that autonomy. Enslaved NPCs can have goals and
knowledge while lacking legal freedom. Avoid using oppression as a resource
optimization bonus. Specialist historical review is still required before a
history-education claim or public classroom use.

## Verified source register and access limits

All sources checked **21 October 2026**. Park materials are primary institutional
sources; their interpretation is not identical to raw excavation data. The
characters page mainly embeds videos, whose transcripts were not inspected; it
supports no detailed biography here. The supplied `/en/excavations-plan-en/shops/`
URL timed out in this session and is not cited as read. Several guessed legacy
individual-building URLs were inaccessible; the official guide/map provided
the checked replacements. No paywall or access restriction was bypassed.

- **S1:** [Official visitor map][S1], live PDF: district anchors and streets;
  not a measured reconstruction of the game's map.
- **S2:** [A Guide to the Pompeii Excavations][S2], ©2015, pp16/20/23:
  building fabric, functions and attributed identities.
- **S3:** [The Other Pompeii itinerary][S3], 8June2024: addresses; modern
  performance roles are not automatically ancient attestations.
- **S4:** [Along the streets of Pompeii][S4], undated official interpretation:
  street life, fullery, thermopolium, religious imagery and benefaction.
- **S5:** [Date of destruction: an open debate][S5], Park E-Journal,
  12December2024: manuscript versus archaeological date evidence.
- **S6:** [Regio V press kit][S6], official excavation interpretation:
  charcoal inscription and competing readings.
- **S7:** [Discoveries continue at Regio V][S7], official excavation report:
  inscriptions, building phases and explicitly provisional interpretations;
  **different district** from the playable slice.
- **S8:** [Being a woman: exhibition catalogue/press dossier][S8], 2025:
  inscriptions, status and economic/religious roles; not universal rights.
- **S9:** [Bakery-prison discovery][S9], Park release, 8December2023:
  interpreted coercive labor context; not proof of a bakery in this district.
- **S10:** [Being a woman exhibition][S10], 2025–2026 official description:
  evidence for variation across social classes and life stages.
- **S11:** [The house as a stage][S11], Park E-Journal, 17January2025:
  excavators' interpretation of elite social space in **Regio IX**, comparative
  context, not direct household evidence for Menander.
- **S12:** [2026 excavation reports][S12], including 21August2026 evidence of
  post-eruption reuse: limits of treating 79 CE as the only historical layer.

Public availability does not grant image/asset reuse rights. This ledger cites
sources; it does not copy their photography into the game or imply endorsement
by the Archaeological Park.

[S1]: https://pompeiisites.org/wp-content/uploads/PompeiiMAP.pdf
[S2]: https://pompeiisites.org/wp-content/uploads/A-Guide-to-the-Pompeii-Excavations-2.pdf
[S3]: https://pompeiisites.org/wp-content/uploads/Mappa-pompei-A3.pdf
[S4]: https://pompeiisites.org/en/pompeii-map/analysis/along-the-streets-of-pompeii/
[S5]: https://pompeiisites.org/e-journal-degli-scavi-di-pompei/la-data-della-distruzione-di-pompei-premesse-per-un-dibattito-aperto/
[S6]: https://pompeiisites.org/en/archaeological-park-of-pompeii/press-kit/press-kit-regio-v/
[S7]: https://pompeiisites.org/en/press-kit-en/discoveries-continue-at-the-regio-v-site/
[S8]: https://pompeiisites.org/wp-content/uploads/cartella-stampa-essere-donna-def.pdf
[S9]: https://pompeiisites.org/comunicati/pompei-emerge-il-panificio-prigione/
[S10]: https://pompeiisites.org/en/exhibitions/being-a-woman-in-ancient-pompeii/
[S11]: https://pompeiisites.org/e-journal-degli-scavi-di-pompei/la-casa-come-palcoscenico-il-complesso-termale-e-conviviale-recentemente-scoperto-nellinsula-ix-10-a-pompei/
[S12]: https://pompeiisites.org/2026/
