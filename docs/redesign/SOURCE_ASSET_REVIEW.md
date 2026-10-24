# Historical source addendum and asset audit

Checked 24 October 2026. This report supplements `docs/pompeii/HISTORICAL_SOURCE_LEDGER.md`; it does not rewrite that frozen historical register or its citations. Primary institutional pages below were reopened as text during this review. No source image was downloaded or added to the game. Native scene legibility is a separate gate and is not established by inspecting a model's node names.

## Qualified source register

Use the fully qualified identifiers in exported cards and combined reports. Keep `brief_id` as an explicitly named compatibility field; never merge the two registers on bare S2–S5.

| Qualified ID | Brief/card ID | Source and institution | Verified section and supported scope | Limits |
| --- | --- | --- | --- | --- |
| LEDGER-S4 | S2 | [Along the streets of Pompeii](https://pompeiisites.org/en/pompeii-map/analysis/along-the-streets-of-pompeii/), Archaeological Park of Pompeii | “Fullonica” describes adaptation of domestic spaces for cloth washing; “Thermopolium” describes the counter and inset vessels. | Supports material features, not Sabina, her stock, prices, a fictional worker, or a surveyed game plan. Retain the older ledger's ownership caution. |
| ADDENDUM-S13 | S3 | [Nevoleia Tyche](https://pompeiisites.org/en/exhibitions-and-events/nevoleia-tyche-en/), Archaeological Park of Pompeii | Documentary section “The tomb in the necropolis of Porta Ercolano,” after the imagined first-person introduction. Its translated inscription identifies Naevoleia Tyche as a freedwoman. | One commemorative example cannot represent all freedwomen; the introduction is modern interpretation. The monument is outside the miniature game district. |
| LEDGER-S10 | S4 | [Being a woman in ancient Pompeii](https://pompeiisites.org/en/exhibitions/being-a-woman-in-ancient-pompeii/), Archaeological Park of Pompeii | Introductory discussion of evidence types and varied social statuses. | An exhibition source, advertised for 16 April 2025–31 January 2026. Do not describe it as currently running or derive universal legal rights from it. |
| ADDENDUM-S14 | S5 | [Elections in Pompeii](https://artsandculture.google.com/story/tgUBNHEcEscIJg?hl=en), Museo Archeologico Nazionale di Napoli | “Writing on the walls” and “Patterns and formulas” discuss painted electoral messages and their recurring structure. | Supporter names are optional in the formula. Prefer “could name a candidate, office and supporters.” An endorsement does not establish an election result or universal voting rights. |

ADDENDUM-S13 and ADDENDUM-S14 are entries in **this addendum**, not retroactive entries in the older ledger. The old ledger's S2 remains the 2015 guide, S3 the 2024 performance itinerary, and S5 the eruption-date discussion. Their historical meanings and hashes are unchanged.

The production card source dictionary already carries the qualified ID plus the original `brief_id`; this addendum gives the new IDs a concrete documentary destination. The source title and URL remain attached. A future combined register must keep institution, checked date, relevant section and claim limits alongside those fields.

## Card and visible-object audit

| Card | Claim assessment | Model/source inspection | Native display gate |
| --- | --- | --- | --- |
| `food_counter` | Counter and inset vessels supported by LEDGER-S4; fictional prices, stock and dispute remain labelled. | `scripts/build_immersion_scene.py`, `south_buildings`, constructs the thermopolium counter and five pottery rim forms. The GLB contains `thermopolium_details`; it does not name each rim separately. | Verify rims are legible from an ordinary approach, not only from a debug camera. |
| `fullery` | House adaptation and washing facilities supported by LEDGER-S4. | Same generator constructs three basin blocks and water surfaces in `fullery_details`. | Verify the basin interpretation is visually clear and accessible without clipping. |
| `freedwoman` | Narrow status explanation and commemorative example supported by ADDENDUM-S13 and LEDGER-S10. | Card explicitly states that Aelia is fictional and the real monument is outside the game district. | Do not imply the player is standing at that monument. |
| `wall_notices` | Electoral-message structure supported by ADDENDUM-S14, with optional-supporter qualification. | No claim that decorative wall marks are an excavated inscription; English structure guide is explicitly modern. | Do not ask the participant to decode a nonexistent ancient inscription. |
| `evidence_and_fiction` | Appropriate project synthesis, with the linked sources supporting only their limited material claims. | Game characters, quantities and events are project-authored fiction. | A reflection question is not measured learning. |

Counter and fullery furnishings are placed at the exterior margin of the schematic rooms to preserve the existing navigable floor. Source inspection proves that geometry exists; it does not establish archaeological placement or its legibility on screen. The audit parsed 66 GLB nodes, with object geometry merged into detail meshes. The game remains an interpretation, not a measured reconstruction.

Keep slavery explicit as coercive status. Chreste's fictional enslaved status must not be equated with Aelia accepting a paid shift. The source pages do not license broad claims about women's voting, citizenship, officeholding, property or unrestricted movement.

## Asset and license inventory

The 52 files recorded in `kalends_3d/ASSET_PROVENANCE.json` all exist and match their recorded SHA-256 hashes. Every notice path listed by its source groups exists. This is an inventory/provenance audit, not certification that the artwork is historically accurate. Detailed machine-readable findings: `results/redesign/debug/source_asset_audit.json`.

| Component | Provenance/notice checked | Disposition |
| --- | --- | --- |
| Body, hair, rig | Local Quaternius base notice and [official Universal Base Characters page](https://quaternius.com/packs/universalbasecharacters.html) | CC0 designation verified; source archive fingerprints retained. |
| Humanoid motion | Local animation notice and [official animation library](https://quaternius.itch.io/universal-animation-library) | CC0 designation verified; selected free Standard clips are documented separately from paid tiers. General motion is not evidence of ancient labor. |
| Foliage | Local nature notice and [official Stylized Nature MegaKit](https://quaternius.itch.io/stylized-nature-megakit) | CC0 designation verified. Stylized species are not botanically authenticated Roman plantings. |
| Earlier fallback characters | Local KayKit notice and [pinned official repository](https://github.com/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0/tree/672074b73ba276876a19e8816ecdc5241817ab47) | CC0 designation verified; fantasy-derived fallback costumes must not be called authentic Roman dress. |
| Stone/plaster/tile/timber maps | Per-map provenance and local Poly Haven notice; [official license page](https://polyhaven.com/license) reopened | Assets carry CC0; the website's logos, sample renders and prose are excluded from that blanket asset license. No such website content was imported by this review. |
| District geometry and garments | Local environment notice, preparation scripts and existing asset register | Original project work retains its own rights; downloaded constituents keep their respective notices. No blanket public-domain claim for the project. |
| Font rendering | Product CSS inspected | Georgia/Times and system interface stacks; no new font file or font service introduced by this review. |
| Audio | `kalends_3d/src/audio.js` inspected | Existing procedural Web Audio ambience and tones; no downloaded voice, music or field recording. Native mute/activation behavior remains a browser gate. |
| Engine/build tooling | Existing PlayCanvas and Vite license files | Separate software notices retained; asset CC0 does not relicense engine or application code. |

Historical cards are original paraphrases with source links. Public institutional hosting is not permission to reproduce photographs. The current text-only design and no-external-image notice must remain accurate. An actual game capture includes the project's existing licensed constituents; it must not be described as an archaeological photograph.

No assets were rebuilt, purchased or downloaded during this audit. Final integration must recheck fingerprints if it changes asset bytes and record any actual native object-legibility observations separately.

## Final home-image provenance addendum

24 October 2026, final integration check. `kalends/experience_os/static/product/assets/hero-v2.jpg` is a **byte-identical copy** of the actual native browser capture `results/redesign/browser/pass2-fullery-geometry.jpg`. Both files are **159,327 bytes** with SHA-256 **`aba7dfb4e6f213daa096c0258966fec7edb86c5ae2401f09281c27b283e9f376`**. It depicts the existing schematic fullery with Aelia and Chreste, including captured interface elements. It is not a generated scene, source photograph, archaeological reconstruction image, or new external asset.

The home page renders this capture with `object-fit: cover`, positioning and translation in `static/product/redesign.css`; the displayed crop therefore changes with its container. `final-home.jpg` and `final-home-desktop.jpg` retain actual native appearances. Cropping through CSS does not change the source-image bytes. The caption identifies it as an actual game capture, and its alt text names the schematic fullery.

A fresh read-only check of the existing `kalends_3d/ASSET_PROVENANCE.json` inventory found **52/52 files still matching their recorded SHA-256 values**. The new hero is a separately documented capture derivative, not a rewritten entry in that historical inventory. Existing asset rights/notices continue to apply to its rendered constituents. No new source photograph, downloaded media, or licence claim is introduced.
