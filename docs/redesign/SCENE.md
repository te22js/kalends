# Existing scene redesign

Implementation scope: `kalends_3d/index.html`, `src/main.js`, `src/style.css`,
`src/scene_guide.js`, new `src/conversation_presenter.js`, `src/renderer.js`, and
`bridge.js`. The same PlayCanvas scene, actors, assets, navigation and authoritative
world remain. Initial camera remains yaw 24°, distance 13.5. No save migration.

## Participant-facing changes

- Arrival gives the role and cart situation in one short view. A details disclosure
  holds the freedwoman definition and movement help. Begin and Explore without a
  guide are distinct; unguided entry sends one guide toggle, no reading/controls
  acknowledgment. Returning lives use admitted current objective, not old arrival.
- A small Next panel has one primary action and a reading-pauses-time indicator.
  Direction/hint/history-skip/guide controls expand in Help & directions. Expanded
  descriptions retain the actual guide projection and known-location checks.
- Hosted scene hides duplicated date and journal controls. Existing host life
  isolation and persistence remain. Standalone scene keeps those controls.
- Conversation ranks existing choices into three contextual options and More.
  Every choice remains available; unavailable ones stay disabled with reasons.
  Generic topics live under More. Questions are not silently transformed into
  obligations. A copied account is a document card, labelled fictional gameplay;
  action results have a separate Result surface from character speech.
- Existing paid choices display their description, cost, and unavailable reason.
  Payment confirmation uses the supplied current price. Unpriced arrangements
  retain an explicit confirmation verb, not an invented amount.
- Scene time reviews display Pompeii's 08:00 origin and actual day boundary.
- Lighter compact name labels, reduced vignette, slightly softer daylight/fill,
  and desktop dialogue camera offset improve separation of scene and reading
  panel. Initial frame is unchanged for meaningful baseline comparison. No new
  landscape or character assets. Narrow dialogue does not use desktop offset.
- Keyboard, local unsent speech, reduced motion, sound opt-in, quality and enlarged
  text controls remain. Guide/hint render updates never move the player.

## Direct observation contract

Only server-tagged available choices with `interaction: observation` call
`POST /api/observe`, carrying the exact `action`, `expected_revision`, and
`expected_state_hash` supplied by the conversation. The existing API wrapper
adds the current life identity. The server is authoritative over whitelist,
permission, proximity, zero price/time/obligation, stale state and acceptance.

Concurrent duplicate clicks share a promise. A transport or server failure
retains the original request. The visible Check the answer button retries that
same body; it does not create a question from current state. A 4xx stale rejection
refreshes the conversation without auto-submitting. Receipt and reply appear only
after server acceptance/reconciliation. Typed speech keeps proposal semantics.

## Verification scope

- `node --test tests/frontend/redesign_scene.test.cjs tests/frontend/immersion_bridge.test.cjs tests/frontend/immersion_renderer.test.cjs` — 36 passed.
- `node --test tests/frontend/redesign_scene.test.cjs tests/frontend/first_session_scene.test.cjs tests/frontend/next_phase_scene.test.cjs tests/frontend/immersion_live.test.cjs` — 59 passed after the unguided-entry/evidence voice follow-up.
- `npm run build --prefix kalends_3d` — passed. Existing bundle-size warning remains.

New tests execute the actual bridge under concurrent clicks, a lost response,
identical retry, stale rejection and an unapproved choice. Presentation tests
verify no hidden document, no lost option, and Pompeii midnight handling.
Four old scene assertions were updated for the deliberately changed copy/help
structure and the new presenter import. Core proximity, no hidden person tracking,
accepted navigation, cancellation and host identity assertions are retained.

Native browser inspection belongs to the integration owner's exclusive browser
session. This file does not claim pixel quality, real pointer/keyboard success,
phone accessibility, or human understanding from Node tests. Verify the initial
arrival, both dialogue states, result/evidence separation, enlarged/narrow views,
return state, free-question clicks, lost response, time review and history access
in the actual browser before accepting this milestone.

## First native review correction

The integration owner inspected the actual desktop arrival/conversation and
reported two concrete issues: newly copied evidence was collapsed under a
redundant receipt, and direct observations did not refresh the parent guide.
The scene now opens only the newly received account, shows its actual text,
provider and account date, and suppresses the duplicate document receipt. Earlier
accounts stay collapsed on a reopened conversation. `projectReceipt` carries the
category needed for that distinction while excluding private payload fields.
A VM test executes the actual render function and checks these conditions.

The accepted-notification omission is in root-owned `static/game-host.js`, whose
operation map did not include `/api/observe`; it was reported to integration for
correction. It must map to `action` and keep the server's accepted revision.

After the resolved guided introduction, two options derive from public current
state: review an open commitment, speak to an enabled nearby offer's person, or
visit an existing fullery/food-counter location. These are navigation/review
invitations, never a promise of available work or automatic economic acceptance.

Validation: 90 combined scene/guide/bridge/renderer/host/live tests passed, followed
by the new copied-account renderer test (10 redesign-specific tests passed).
Vite rebuilt successfully as `index-Bg2nhnAv.js` / `index-BWDzoGjP.css`. These checks
do not replace the integration owner's second native walkthrough.
