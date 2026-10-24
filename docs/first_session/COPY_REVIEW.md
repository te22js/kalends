# Rendered first-session copy review

The [readable review](../../results/first_session/copy_review.html) and
[machine-readable cases](../../results/first_session/copy_review.json) are
generated from actual backend projections, evaluated sentences and real accepted
actions in disposable lives. They are **not** raw template fragments, product
screenshots, browser-layout evidence, participant observations, or comprehension
scores. The HTML is an original review layout and says so at the top.

Reproduce from the repository root:

```sh
python3 scripts/render_first_session_copy.py
python3 -m pytest -q tests/test_first_session_copy_review.py tests/test_first_session_guide.py tests/test_next_phase_history.py
```

`--out PATH` chooses a different artifact directory. Collection creates its own
temporary ProductService directories, sets `include_examples=False`, uses the
existing offline default, and removes its disposable journals when collection
finishes. It never opens retained user lives, research cases, a browser, or an
external model. It writes only the two review artifacts in the chosen output
directory. Their source fingerprints identify the backend version actually
sampled; rerun after copy changes instead of treating an old artifact as current.

## Executed inventory

The initial generated review contains **52 cases**. Actual backend states reach
all Pompeii guide steps **p0–p9** and Observatory steps **o0–o7**. Four explicitly
labelled synthetic cases test formatting. The JSON contains world minutes,
accepted-command revisions, state hashes and accepted receipt identities for
the executed cases. These are operational fixtures, not human sessions.

| Cases | Actual source and scope |
| --- | --- |
| 001–010 | Pompeii arrival, acknowledgement, accepted movement, public Sabina conversation, real disclosure review, heard claim, optional history reading and both copied accounts. |
| 011–016 | Public game contexts for Dama, Lucius, Marcus, Felix, Chreste and Sabina, including fully assembled greetings, topics, choice descriptions, costs, consequences and unavailable reasons. Movement uses the existing public snapshot and ordinary validated actions. |
| 017–020 | An offer deliberately left unconfirmed, actual market-route payment and delivery, public story, and optional reflection/continuation. The unconfirmed review does not mutate the world. It is not a claim that a server-side cancellation endpoint exists. |
| 021–026 | All five history cards, after real required visits, plus a life reopened from its saved journal. Card source/limit/fiction/rights fields are shown as complete prose. |
| 027–029 | Actual stale-offer rejection; a separate declined route showing a genuinely pending outcome and then an admitted continuation after explicit time advancement. This branch reaches p7, which immediate delivery can legitimately skip. |
| 030–043 | Observatory arrival with no received condition, request, actual report disclosure, reviewed allocation, optional promise, actual 4/4/0 settlement, missed promise, public story, reflection, duplicate/closed-round rejections and an older report after a real new-round advance. |
| 044–048 | Real one-unit promise, one-unit/zero deliveries, public story, exhaustion of credits through actual inspections, and real insufficient-credit/invalid-zero-promise rejection messages. |
| 049–052 | Synthetic formatter inputs: empty retained context, dated hearsay, a long name containing HTML-sensitive characters, and missing optional request/report fields. These are labelled `synthetic_formatting_fixture` and are never called executed world events. |

Every rejection is checked against the world hash and accepted-command count to
ensure no effect was committed. The main market result is four units to Sabina
and two to Felix. The primary Observatory fixture records allocations 4/4/4,
deliveries 4/4/0 and an actual missed four-unit promise to Lin. These outcomes
come from backend execution, not arithmetic performed by this review renderer.

The synthetic empty-context case demonstrates a formatter without retained
shared evidence; it does not prove that a particular simulated memory was
actually forgotten. The long-name and missing-field cases are likewise
constructed stress inputs, not claims about ordinary gameplay or real people.

## Editorial pass and concrete findings

The initial pass read all **247 unique displayed string values** across the
executed sequence and synthetic cases, including the fully assembled narrative
and choice text rather than only its source templates. A subsequent generated
artifact may contain additional values, including source/time metadata, and is
identified by its own fingerprints. The initial reading found these defects and
reported them to the backend owner; they must be checked against the final
regenerated artifact before closing the release gate:

| Case | Observed text or mismatch | Required correction |
| --- | --- | --- |
| 016 | Sabina's recall joined two event sentences without punctuation: “…promised to You read sabina's wax account”. | Separate complete recalled statements and preserve proper names. |
| 019 | A story event read “You read sabina's wax account”. | Avoid lowercasing the whole document title when forming a sentence. |
| 044–046 | “You promised 1 units”, “Amir was allocated 1 units”, and “received 1 of 1 allocated units”. | Apply singular/plural choices consistently to guide, obligation, story and outcome sentences. Preserve numerical state. |
| 039 | The history role said “Mira · Calibration”, while the product identity uses Instrument systems. | Align display-role metadata without changing team identity or world rules. |

An intermediate regenerated pass contained **252 unique string values**. Independent
re-reading confirmed the fixes: document titles are quoted with their proper
names; Sabina's recalled events are separate sentences; both guide and story
use “1 unit”; the one-of-one settlement uses “allocated unit”; and Mira's role
is Instrument systems. The intermediate report-story double full stop was also
fixed. A focused regression checks these evaluated sentences. No remaining
instance of these particular defects appeared in the final generated cases;
that is narrower than a claim that every possible product sentence is correct.

The current catalog contains **279 unique string values in 649 displayed
blocks across the same 52 cases**. The independent final reading included all
changed values after the complete intermediate pass: concrete market,
household and evidence-route choices; their immediate twenty-minute action
costs and separate service obligation; the corrected time-advance return
sentence; project requirements with open, completed and missed status from
admitted revisions; and the cards' representation labels and illustration
explanations. Those project and card fields were previously omitted by the
review renderer and are now included without changing product behavior. The
source fingerprints in the JSON identify this exact generated version. The last
regeneration follows commit `08796c5`, which groups time-advance records with
expandable routine history. The renderer includes the complete routine records,
their real counts and their text, so grouping does not omit them from this
catalog. The additional routine and request strings were independently read.
The current copy, guide and history checks pass **45 tests**; these remain
automated fixture checks rather than comprehension evidence.

The review leaves all backend wording unchanged when rendering it. It does not
silently repair these sentences or replace terse errors with invented product
copy. Errors such as “Insufficient owned credits” are the actual backend text;
any browser-specific friendlier wording needs separate review. The review's
labelled action-field definitions expose real reviewed fields and are not a
claim that the product displays those technical identities verbatim.

## Coverage limits and browser handoff

Each case includes an expandable **320 CSS pixel** version of the same prose.
Escaping and wrapping rules are tested, but that demonstrates this review page's
layout code only. It does not verify the product at a narrow viewport, enlarged
text, actual keyboard focus, reduced motion or assistive technology.

The generator covers current backend guide sentences, scoped conversations,
offered choices, received evidence, notebook content, accepted outcomes, public
history and selected real errors. It does not execute `app.js`, client-only
homepage/detail copy, modals, toasts, scene labels, routing, selection behavior,
animations or WebGL. It does not exhaust every commission, relationship branch,
historical save migration, delayed failure, unsupported input, or every possible
numeric value. Backend p0–p9/o0–o7 coverage is not complete browser UI coverage.

Native captures and accessibility-tree material belong separately under
`results/first_session/browser/`. The independent follow-up should read the
actual first-session screen sequence alongside these cases: role and immediate
goal; how to move/speak; what each account claims; review cost and obligation;
actual consequence; optional history explanation; and saved-life return. Check
normal/narrow widths, current mapped keys, missing/zero values, stale and
cancelled interactions, and whether a guide step is truly reachable. Record
which captures were actually inspected; their mere presence is not a review.

No native browser capture has been certified by this generator. No unfamiliar
consenting participant has been observed by this editorial pass. The owner's
reported first-session failure therefore remains a real release concern until
the repaired experience passes the separate native and human checks.

### Limited independent inspection of available native evidence

Separately from generation, this reviewer inspected
`browser/pompeii-arrival.png` at 1280×720 and the available `arrival.txt` and
`move.txt` accessibility diffs. The arrival image showed the scene's large
arrival overlay and the left guide card simultaneously, with duplicate role
paragraphs visible through each other. Nearby character/place labels also
overlapped. Both findings were reported for correction and a new capture. The
movement diff recorded world time advancing to 08:02 and an interaction control;
it is not a complete accessibility tree or evidence of an entire successful
session. No normal/narrow full sequence or focus-order review is certified from
these three files. Later captures need their own actual inspection record.

The follow-up inspection read `browser/pompeii-p5-repaired.png` and
`browser/pompeii-history-card.png` at 1280×720, plus
`browser/observatory-o0.png` at 503×703 and the complete
`browser/observatory-o0.txt` and `browser/history-card.txt` accessibility trees.
The repaired p5 view placed the primary movement instruction before its longer,
scrollable prose. The narrow Observatory introduction wrapped without visible
overlap in that capture. The notebook tree contained the actual food-counter
claim, evidence, limits, fictional changes and source link. Its screenshot
showed the notebook index at the top of the scroll area, so it does not establish
the visual layout of all card prose. No additional copy blocker was found in
these particular screens.

`browser/observatory-allocation-review.txt` and
`browser/observatory-invalid-allocation-before-fix.txt` record the earlier
allocation-warning and invalid-total defects. They are pre-fix evidence, not
verification of their repair. The corrected real-shell regression checks the
modal's total, admitted report capacity and date, conditional shortfall warning,
missing evidence and invalid numeric entries.

The subsequent independent pass inspected
`browser/observatory-allocation-review-repaired.png` and its complete `.txt`
tree, `browser/observatory-settlement-review.txt`, and
`browser/observatory-executed-shortfall.png` and its complete `.txt` tree. The
503-pixel-wide allocation screenshot visibly includes total 12, the admitted
eight-unit report and its date, the conditional four-unit excess warning, and
the settlement time. The remaining modal content and confirmation controls
continue below the scroll area. The settlement tree states the exact time jump,
known promise and public execution order before confirmation. The result image
and tree distinguish requested, promised, allocated and delivered quantities;
Lin was promised four, allocated four and delivered zero, with the missed
promise stated explicitly. These are captured executed results, not a predicted
delivery invented by the review generator.

The result tree also exposed stale prospective wording beneath the disabled
settled allocation form: “You may review this plan if you intend that risk.”
This and the separately observed next-round modal sentence that implied another
allocation execution were corrected in commit `3c5bdb4`. Focused real-shell
regressions check recorded delivery after settlement, missing-result handling,
and a one-minute next-round step that preserves the previous result. The final
independent native pass inspected
`browser/observatory-zero-allocation-review.txt`,
`browser/observatory-settled-summary-repaired.png` and its full `.txt` tree,
plus `browser/observatory-next-round-review-repaired.png` and its full `.txt`
tree. In a separate practice life, the review explicitly says no allocation was
recorded, capacity is unconfirmed and zero will be used for each team. The
actual result at 23:59 records zero allocated and delivered, then the next-round
review states a one-minute advance and preserves the previous settlement.
These captures verify the review and summary repairs; no next-round execution
is claimed by them.
No new native invalid-number capture has been inspected. This inspection did
not exercise keyboard focus, every guide step, the complete saved-life return
sequence or an unfamiliar participant.

`browser/pompeii-extra-large.png` was inspected at 1280×720 alongside
`browser/pompeii-preferences.txt`. The preferences tree reported Extra large
text, reduced motion selected, and explicit current movement, interaction,
Escape, journal and room-exit keys. In the screenshot, the primary “Talk to
Sabina” instruction and help controls remained above the scrollable longer
copy; the nearby Sabina, Dama and Marcus labels were separate. That static
capture does not establish motion behavior or a keyboard-only session.

The final Pompeii delivery pass inspected
`browser/pompeii-market-review-repaired.png` and its complete `.txt` tree, then
`browser/pompeii-market-executed.png` and its complete `.txt` tree. At Extra
large text, the reviewed choice visibly stated what the carrying charge buys,
the **3 coins · 20 world minutes** cost, the attempted-delivery consequence and
the explicit confirmation button. The subsequent captured state advanced from
08:16 to 08:36 and from six coins to three. Its guide tree reports four flour
units delivered to Sabina and two to Felix, then offers “Review what happened.”
The result paragraph continues in the guide's scroll area; its complete text
was read in the accessibility tree rather than inferred from the visible first
lines of the screenshot.

The repaired separate-practice arrival was inspected in
`browser/pompeii-practice-arrival-repaired.png` and its full `.txt` tree. It
labels the life as a practice copy and displays the role and controls without
the earlier duplicate guide overlay. At Extra large text, the final reading
footnote continues below the screenshot edge; Begin and the controls-skip
choice remain visible. `browser/pompeii-decline-deadline-review.txt` states a
360-minute advance and the buyer decision deadline before confirmation. The
subsequent `browser/pompeii-declined-autonomous-outcome.png` and full `.txt`
tree show the practice life at 14:00 and a recorded six-unit delivery to Lucius.
The editorial record does not infer that the original life changed from the
practice outcome. The additional `browser/pompeii-scheduled-duty.png` shows a
readable continuation instruction and separate nearby labels; a still image
does not establish the timing or cause of character movement.

Later native review also found that reflection initially selected a walking
step rather than the accepted delivery decision, and that the latest-eight
evidence excerpt did not disclose its truncation. Commit `ecb6c56` defaults to
the latest accepted action other than movement, labels the recent-eight
excerpt with its full count, and keeps all earlier admitted records in a
collapsed disclosure. Commit `a14b992` removes a duplicate Day label on the
Pompeii saved-life card. Fresh native verification then inspected
`browser/pompeii-reflection-repaired.png` and its complete `.txt` tree: the
market delivery was selected despite a later walking command, the excerpt was
labelled “Most recent 8 of 55 admitted records,” and the expanded earlier 47
contained Sabina's copied account. No alternative execution is claimed by this
capture.

`browser/separate-saves-return.png` and its full `.txt` tree show distinct
practice and original QA lives at 14:00 and 09:07 respectively, with one Day
label in each saved-life date. The original card occurs below the portion
visible in the screenshot and was read in the full tree. The paired
`browser/pompeii-390-guide` and `browser/observatory-390-result` PNG/text files
were also inspected. These are 390 CSS pixel embedded viewport fixtures, not
physical mobile device tests. They preserve the primary guide controls and
readable recorded-result prose in their captured states. Full browser evidence
and remaining limits are recorded in [BROWSER_QA.md](BROWSER_QA.md).

Finally, `browser/pompeii-saved-entry-repaired.png` and its complete `.txt` tree
were inspected after the saved-entry repair. The practice life remains at
14:00; its entry title is “Continue as Aelia” and its prose includes the already
recorded delivery to Lucius. The screenshot is scrolled within the entry layer
and shows the continuation button and complete reading footnote. Its title and
earlier prose above the visible portion were verified in the tree. This checks
the captured saved-entry state, not every possible return branch.

The final `browser/pompeii-grouped-story.png` and complete `.txt` tree were also
read. The two copied accounts and accepted delivery decision remain visible as
material history outside the collapsed routine groups. The full tree lists
groups of five, four and 44 records; the screenshot shows a collapsed
five-record group near its lower edge. This supports the grouped
presentation without claiming that the 44-record group was opened in the
browser. The renderer's backend cases include every routine record, and the
rendered-shell regression separately checks zero, one and plural record labels.
