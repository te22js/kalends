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
python3 -m pytest -q tests/test_first_session_copy_review.py tests/test_first_session_guide.py
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

The regenerated pass now contains **252 unique string values**. Independent
re-reading confirmed the fixes: document titles are quoted with their proper
names; Sabina's recalled events are separate sentences; both guide and story
use “1 unit”; the one-of-one settlement uses “allocated unit”; and Mira's role
is Instrument systems. The intermediate report-story double full stop was also
fixed. A focused regression checks these evaluated sentences. No remaining
instance of these particular defects appeared in the final generated cases;
that is narrower than a claim that every possible product sentence is correct.

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
