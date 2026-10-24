# Persistent-life product audit

Release baseline: `6ebe9ec`. This audit covers the existing public shell and two
finite worlds. It adds no locations, map, generated content or new game rules.
A compelling 15-minute session is the design target, not an observed result.

## Prioritized implementation plan

1. Make a consenting session measurable: distinguish visible, focused foreground,
   active-estimate and idle time; identify the first accepted non-navigation
   action; record returns and actual displayed consequences. Keep collection off
   by default for every life, with a bounded allowlist and no text or keystrokes.
2. Repair continuity at the existing boundaries: show newly saved changes when
   returning within the same tab, preserve the mounted Pompeii scene and draft,
   avoid claiming a consequence when an advance was skipped, and keep operator
   exposure visible in the world menu.
3. Validate the small first/return loop in disposable journals. Ask a consenting
   participant to meet someone, consider or decline a choice, accept a meaningful
   action, see what followed, leave, then resume the same life and explain what
   persisted. Observe agency and character continuity without adding content or
   presenting a guided execution as evidence of enjoyment or retention.

## Findings and implemented changes

| Priority | Source-level reproduction | Change |
|---|---|---|
| High | Every successful scene `move` emitted `meaningful_action`. | Baseline authoritative `telemetry.meaningful_revision` and require a typed scene acceptance with its exact accepted revision; only a newly accepted non-navigation/non-wait action can emit this event. Deduplicate repeated reconciliation; mark the first such event in a tab session. |
| High | Time since the last event was counted as active whenever the document happened to be visible. Idle and unfocused time could inflate engagement. | Accumulate interval deltas across visibility/focus boundaries. Active is the focused-and-visible part within 30 seconds of an interaction; remaining foreground time is idle. Flush every 15 seconds and at lifecycle boundaries. |
| High | Same-origin iframe input does not bubble to the host. | Bind event-presence listeners to the scene document after iframe load. Neither the key, field value, coordinates nor event count is retained or transmitted. Existing scene/draft ownership is unchanged. |
| High | A same-tab return notice was suppressed forever after the first entry. | Key the notice to the admitted saved revision, so a later return with changed history shows the saved change summary. |
| Medium | Every `advance()` completion claimed a consequence view, including skipped mutations and histories without consequences. | Refresh/show the follow-up only after a returned mutation result. Count a consequence view only for consequence material actually rendered in a visible, focused view, or an executed alternative result. |
| Medium | Existing event names for returns, declines, errors and Research entry were unused. | Emit explicit return/resume, review-cancel, bounded error-category and acknowledged Research-entry events. Display the life’s persistent operator-exposed marker in its menu. |
| Medium | A reload created a different session UUID. | Retain an opaque tab-session UUID and first-meaningful marker in sessionStorage. Keep the server’s life/build/operator identities authoritative. |
| Medium | Opt-out waited for the preference POST. | Suppress collection in this tab immediately, including pending-write and failure paths; do not retroactively collect the time before opt-in. |

Accepted world journals remain separate from optional usage events. Personal
notes and drafts remain separate from telemetry; their existing product behavior
is unchanged. No gameplay action is replayed by measurement code.

## Measurement contract and interpretation

The browser submits `id`, `event`, `session_id`, `active_ms`, `visible_ms`,
`foreground_ms`, `idle_ms` and `elapsed_ms`, with optional fixed `reason`,
`accepted_revision` and boolean `first_meaningful`. The backend validates fields
and derives build (`kalends-continuity-1`), life, world minute, action kind and
operator exposure from the accepted journal and metadata. Rows identify the
`kalends-usage-v2` schema. Meaningful accepted revisions are positive, 1-based
command-prefix indices; a nonexistent, navigation, advance or wait revision is
rejected. The scene bridge reads only a clone of the accepted response and
forwards its fixed operation/revision metadata, preserving the original response
for the scene client. Failed scene POSTs forward only fixed error categories. No name, utterance, note, raw error, input value,
key, pointer coordinate or private scene state belongs in this stream.

`visible_ms` includes unfocused visible time. `foreground_ms` requires visibility
and focus. `active_ms` is a conservative interaction estimate using a 30-second
grace period; `idle_ms = foreground_ms - active_ms`. A keyboard-activated button
or text-edit input can renew the grace period through a click/input event; no
keydown measurement listener or keystroke value/count is used. Reading longer
than 30 seconds without interaction is categorized as idle, even if the person
is engaged. These values do not measure attention, enjoyment or learning.

Timing fields are per-event deltas, so summing admitted rows does not duplicate
elapsed time. `elapsed_ms` is bounded wall time since this life’s optional
measurement context began in this tab session and survives a reload; it includes
away time and must not be called active time. A first-meaningful event can support
time-to-first-accepted-choice within the consenting window. Initial historical
commands are baselined and never presented as new choices.

A reload preserves the tab-session ID and uses a reload return reason. A same-tab
leave and re-entry uses a return reason. Opening a separate tab starts another
session; there is no person-level tracking or claim of cross-device retention.
`session_end` is a pagehide hint sent with keepalive; browser termination can lose
it, and a reload/back-forward cache return can resume the same session. Treat
absence of that row as missing data. Scene acceptances need their own exact revision and operation discriminator;
a move followed by a read must not claim an intervening action from another tab.
Untyped notifications reconcile the UI but conservatively omit a meaningful event. Backend rejection of an event must not affect the
accepted world journal.

Consent is stored per life by the server. Opt-out is immediate in this tab; a
failed server preference save is disclosed and collection stays paused locally,
including after a reload of this tab.
Existing other tabs can retain stale consent until their next life reconciliation;
this local installation is not a multi-user telemetry or authorization service.

## Test environment and executed evidence

Run deterministic UI checks from the repository root:

```sh
node --test tests/frontend/continuity_product.test.cjs tests/frontend/next_phase_product.test.cjs tests/frontend/experience_os_host.test.cjs
```

The integrated audit run passed **53 frontend tests**: 17 timing/consent/continuity
regressions, 19 retained shell regressions and 17 scene bridge regressions. The
focused backend suite passed **78 tests**, including exact accepted revision,
move/wait rejection, timing partitions, fixed reason/identity fields, durable
opt-out and optional-event-write isolation checks. The real shipped `app.js` executes against a small
DOM/fetch boundary with controlled monotonic and wall clocks. The iframe document
boundary is simulated. Backend tests ran under bundled Python 3.12.14 using the
existing local pytest installation (plugin autoload disabled); HTTP fixtures
needed the sandbox permission for disposable loopback servers. All fixture
journals are under temporary test directories. A first sandboxed attempt could
not bind loopback and was rerun successfully with that permission. No packages
were installed and no remote services were called. These tests establish handler behavior and payload
privacy, not CSS layout, native focus behavior, WebGL performance or human use.
They cover default-off behavior, 30-second inactivity, hidden/unfocused time,
fractional timing consistency, no retrospective opt-in, pending opt-out, stable
reload identity, no movement inflation, first-action deduplication, real displayed
consequence checks, changed-history returns, Lab cleanup and error redaction.

For native browser verification, use a disposable directory and a separate port:

```sh
./scripts/run_next_phase.sh --port 8813 --directory /private/tmp/kalends-continuity-product-qa
```

The root release pass owns native browser QA and should record its actual port,
life IDs and captures separately. Check both normal and narrow layouts, iframe
activity after focus transitions, declined/accepted choices, restart/reload,
return summaries, operator exposure and the local JSONL payload. Keep retained
saves and prior study results out of that fixture.

## Remaining product evidence

No consenting human session was run by this audit. There is no new enjoyment,
demand, retention or learning result. A 15-minute session’s success should be
assessed by whether a person can name their role, make a choice they regard as
theirs, understand a recorded consequence and resume the same character/history.
The finite offline grammar, finite content, real-device/mobile behavior and full
assistive-technology audit remain limitations from the prior handoff. The active
estimate is deliberately imperfect and must be reported alongside foreground
and visible time rather than promoted into a validated engagement metric.
