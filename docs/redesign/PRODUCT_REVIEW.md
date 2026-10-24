# Independent product-shell review

24 October 2026. Scope: current `kalends/experience_os/static/product/app.js`, the first-session shell tests and their existing VM/DOM harness, related guide evidence fields, and the free-observation boundary. No browser was operated in this review. Assertions execute actual shell event handlers with explicit server fixtures; they do not establish native layout, keyboard behavior, rendering performance or human comprehension.

## Contract updates and retained coverage

Updated only `tests/frontend/first_session_product.test.cjs` for the redesigned interface. The previous free-report review contract is intentionally replaced: the explicit question sends one `observe` request with life identity, accepted revision and state hash, and the answer appears only after acceptance. Paid inspections, promises, allocation and time advance retain their review boundaries. No test accepts both old and new behavior.

The 28 tests retain and extend checks for:

- Initial unknown capacity and no disclosure/observation before a question; one observation on the explicit free question; exact accepted-prefix identity.
- Delayed answers, repeated clicks, stale rejection, and separately delivered duplicate natural-language interpretation responses.
- Paid inspection fee and cancellation; no implicit promises, charges or time advance during guide navigation.
- Zero versus missing requests/promises/allocations; current versus earlier dated reports; saved allocations versus tab-local drafts.
- Default and later-open-round results, incomplete historical results, deliberate settlement review and explicit advance.
- Notebook evidence/fiction layers, safe source URLs, unavailable cards, original evidence type, and guide metadata boundaries.
- Guide on/off/resume, practice life identity, optional learning/telemetry, privacy of telemetry categories, retained scene identity and accepted quantities.

The first-session fixture now includes the real snapshot `state_hash` field required by the observation protocol. This is test-fixture parity with the production snapshot, not a weakened protocol assertion.

## Genuine implementation issues found

| Issue | Reproduction and consequence | Disposition |
| --- | --- | --- |
| Saved total used a stale draft | Enter 4/4/4, reconcile a saved 4/4/0 allocation. Fields became disabled at 4/4/0 but the total still read twelve because it preferred draft values. | Integration owner corrected precedence. Regression now passes: saved fields, total and finish review agree on eight. |
| Incomplete old results manufactured quantities | A historical result without `actual_capacity` rendered “NaN units”; absent per-team delivered/allocated entries rendered zero. | Integration owner added missing-value handling. Regression preserves explicit zero while rejecting invented zero and NaN. |
| Double speech submission could admit twice | Submit the same utterance twice before `/intent` returns. Deliver the first response and let its observation finish; then deliver the second. It used the new snapshot revision and admitted a second action. | Reproduced as two observation requests. Integration owner added a per-life interpretation lock, retained through observe/propose, with original submission revision/hash and life/epoch/conversation gates. Regression now passes. |
| Spoken testimony was labelled a document | Guide evidence includes Lucius's “household steward’s account” with kind “Testimony; not a verified delivery record”. The notebook title/text heuristic includes it, then labels every comparison row “A fictional document.” | Reported to integration owner; the dedicated regression remains failing at the review checkpoint below. Preserve each row's explicit evidence kind, then give a general account-versus-proof caution separately. |

Additional copy concern: a fixed parent-shell “Reading pauses time” label cannot describe the scene's optional Live mode truthfully. Use a neutral parent “World time” label unless the scene communicates its actual mode; the scene can retain its accurate pause/live indicator. This was also identified by the integration owner and remains part of browser verification.

## Executed check and limits

Command: `node --test tests/frontend/first_session_product.test.cjs`.

Latest independent checkpoint: **27 passed / 28 total**, with only the spoken-testimony/document-label test failing. Log: `/private/tmp/redesign-first-session-review-tests.log`. The test file was then released to the integration owner. A later correction and rerun should update this disposition rather than delete or weaken the assertion.

The harness does not parse the generated HTML into a real browser DOM and cannot validate visibility merely from string presence. Assertions that inspect markup are evidence of what the renderer emits, while event-handler tests validate request sequencing under fixtures. Server authorization, canonical at-most-once behavior, persistence, native accessibility, actual full-interface display and the fresh-agent probe are separate gates. No frozen source or result was altered by this review.
