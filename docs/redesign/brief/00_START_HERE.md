# Kalends — redesign the experience, preserve the world

Prepared 24 October 2026. This package is an evidence-based creative/engineering brief, plus a standalone interaction reference. It does not contain a modified Kalends repository.

## The decision

The next release must feel substantially different without discarding the simulation that makes Kalends distinctive. Rebuild the participant-facing composition, language, interaction rhythm and historical learning experience. Preserve the authoritative state, scoped knowledge, persistence, existing scenarios, renderer and frozen research.

The organizing idea is **a place first, a person second, a decision third, an explanation when requested**. The participant should not have to learn the runtime’s vocabulary to inhabit a world.

Kalends remains a persistent-world / synthetic-experience project, not merely a delivery game or a training dashboard. Pompeii is its first inhabited historical experience. Shared Observatory is a compact decision experience. They need different presentation, not different truth systems.

“Five times better” is an ambition, not an achieved or scientifically meaningful multiplier. The release gates in this package operationalize the desired jump in clarity, interaction, composition, expression and visible continuity. They do not manufacture a satisfaction score.

## Files and use

1. `01_MASTER_CODEX_PROMPT.md` — the implementation assignment. Give this to the repository-connected agent.
2. `02_COPY_AND_FIRST_SESSION.md` — exact proposed scene structure, replacement language and epistemic conditions.
3. `03_VERIFICATION_AND_RESEARCH.md` — defect cases, runtime checks, UX gates, scientific interpretation and evaluation.
4. `04_INTERACTION_REFERENCE.html` — open in a browser. A self-contained clickable reference for visual hierarchy and flow, not a 3D game. Its background is explicitly schematic. Its local fixture actions do not modify any real save. It resets on reload.
5. `tests/test_reference.py` and `evidence/REFERENCE_TEST_RESULTS.json` — executed tests of that reference only.
6. `evidence/copy_extracted.json` — parsed supplied copy cases, excluding the duplicate narrow-layout copies.
7. `evidence/*.png` — captured supplied copy-catalog pages and new reference screens; none is a capture of the user's running Kalends build.

The application connected to the user's own machine is reportedly on port 8823. The connected-browser attempt failed because the originating browser context was unavailable. No repository code, live world, real NPC movement, performance trace or save was directly tested here. Those are mandatory implementation-agent tasks, not work already completed.

## What was directly inspected

- The full supplied first-session handoff, browser QA report, source review and `copy_review.html`.
- Parsed all **52 copy cases / 649 primary displayed blocks**. The HTML also duplicates those blocks in its narrow-width comparisons; those duplicates were not counted again.
- Rendered the supplied HTML in local Chromium at desktop and 390 CSS pixels. This was the copy catalog, not the product renderer.
- Recovered relevant earlier context: persistent local knowledge, consequences across time, alternate lives, ordinary moments and information exchange are foundational. Do not reinterpret the project as generic 3D NPC entertainment.
- Built and browser-tested the separate interaction reference. The attached JSON records the precise scope.

## The important findings

### 1. Machine vocabulary still reaches the participant

`copy_review.html`, cases 005/012/014/015: “We have no consequential shared dealing in my retained memory yet.” Case 006 describes a “supported action” and “trial preview.” Case 034 says “latest admitted report.” Case 040 informs the participant that reflection is not a measured test result.

These descriptions may be useful in scientific records. They are not a suitable default voice for people or instructions inside an inhabited world. The redesign changes their presentation, not their underlying truth conditions.

### 2. The guide still repeatedly explains its own mechanics

The exact generic “supported route” hint appears **23 times** across distinct primary catalog states. The reading/time-policy paragraph also appears **23 times**. This does not prove that all 23 are simultaneously visible, or that every user encounters all of them. It does show a reusable template repeating a substantial amount of scaffolding.

Replace it with a small stable reading-paused indicator, an accessible Help entry and contextual instruction. Do not hide costs or important deadlines.

### 3. The conversations mix several incompatible voices

A character’s opening, a policy goal fragment, an evidence-access error, a relationship diagnostic and action-tool descriptions can all appear as if they are one conversation. In case 013, the same privacy explanation substitutes for several unrelated answers. The fix is not a synonym pass: separate actor speech, player intent, system notice, historical context and operator data.

### 4. One validation case does not establish what its title suggests

Case 048 is labelled “Invalid zero promise is different from no promise,” but the actual rejection says the round has settled. That verifies a closed-round guard, not that an open round rejects an invalid zero promise for the right reason. Add a proper isolated open-round case. Do not turn this observation into a claim that the validator itself is broken.

### 5. The Observatory has a decision-model explanation problem

Case 030 shows a current request of two units while the project requires four in a single settled batch. That can be coherent if the request reflects a constrained or cautious policy, but the participant is not given a reason. Do not silently change either number to make the interface look consistent. Explain the distinction only from permitted evidence, and audit whether requesting two has meaningful utility in the actual model.

### 6. The independent research result changes the claim

The handoff reports eight held-out workflows, twenty noise seeds and five arms: 800 executions. Candidate and V3 both pass 140/160 primary cases, and all 160 paired outcomes tie. One workflow fails in every arm. This does not demonstrate a general advantage for the candidate. The earlier 30/30 versus 0/30 result belongs to a different authored task family and remains valid only within that scope. “Independent agent-authored tasks” is not external replication by an independent research group.

### 7. What the new handoff genuinely adds

State-derived guidance, costs, accepted-action tutorial progress, scoped history cards, cancellation checks, distinct practice lives and explicit result summaries are substantial foundations. The browser QA report carefully limits its claims; preserve that honesty. Do not destroy these mechanisms to achieve a cleaner screenshot.

## Checked primary references

These are constraints and methodological comparators, not proof the redesign works.

- Microsoft XAG 109, Objective clarity: interactive teaching, accessible objectives and tutorials available again. https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/109
- W3C APG, Modal Dialog: explicit focus, keyboard containment and focus restoration for actual modal dialogs. https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/
- W3C H102, native dialog: https://www.w3.org/WAI/WCAG22/Techniques/html/H102
- LongMemEval, original paper: extraction, multi-session/temporal reasoning, updates and abstention are established evaluation categories. https://arxiv.org/abs/2410.10813
- LongMemEval-V2, May 2026 version: state tracking, workflow knowledge and premise awareness are relevant comparators. https://arxiv.org/html/2605.12493v1

Historical claims in this brief are inherited from the supplied `HISTORY_SOURCE_REVIEW.md`; this session did not independently re-open every historical source or certify archaeology. The implementation agent must reconcile the documented source-ID mismatch and verify all newly introduced claims.

## Do not repeat the previous cycle

Do not create a new engine, another grand platform name, a third world or a new long company thesis. Do not run millions of cheap correlated cases to fill a results page. Do not call a mock adapter “live AI.” Do not interpret a longer checklist as better taste.

Make the actual participant journey visibly and behaviorally different. Test it. Keep the scientific verdict separate.
