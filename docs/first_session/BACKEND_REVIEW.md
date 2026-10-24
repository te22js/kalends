# First-session backend review

Reviewed the first-session backend changes from `44868e5` through `e04e26d`,
including the current copy repairs. The review found two concrete metadata
recovery defects. Both are repaired in `e04e26d` and covered by focused
regressions. No remaining
confirmed defect was identified in the inspected paths; this is a bounded code
review, not a claim of product comprehension or usability success.

## Scope and boundaries

The review inspected `guide.py`, `history_cards.py`, the guide/practice/life,
metadata, review/confirmation and usage paths in `product.py`, and participant
projection/confirmation in `runtime.py`. It also read the supporting
`history.py`, `participant_copy.py`, legacy conversation/action implementations,
and relevant tests to establish the observation and execution boundaries.

The focus was accepted-state completion, actions taken before the guide prompts,
alternative supported actions, canceled/stale/failed reviews, restart behavior,
private knowledge and save preservation. The current cart-choice prose mapping
and latest project-register projection were read; those concurrent copy changes
belong to the main repair, rather than these metadata fixes.

No existing user save, recorded example, engine rule, action semantics, journal
format or frozen research source/task/result was changed. Reproductions used
new disposable `/private/tmp/kalends-backend-review-*` directories; regression
fixtures also use disposable directories. No browser or paid model was used for
this backend review. Historical source accuracy and image rights were not
independently re-audited here; separate source-review documents cover those.

## Findings and repairs

### [P2] A malformed optional guide could make a valid saved life unreadable

Before repair, the product metadata loader validated existing flags and lists
but accepted the new `guide` field without validating its shape. Setting only a
disposable saved life's guide to `true`, `{"ack": null}`, or
`{"read_cards": null}` and restarting loaded the journal without a catalog
failure, then raised `AttributeError` or `TypeError` from `life()`. The accepted
journal still replayed and its bytes were unchanged; the optional display state
was what prevented normal inspection of that valid life. `guide_update` and
usage collection also called `.get()` on an unchecked guide value.

The loader now validates the guide object, version string, boolean flags and
lists of strings. Invalid metadata follows the existing incompatible-metadata
policy: preserve its original file, report the load failure, permit inspection
of a valid journal using fallback display state, and block mutations through the
normal incompatibility guard. No invalid metadata or journal is silently
rewritten. The pure preferences projection also handles malformed optional
inputs defensively, filters unhashable/non-string acknowledgement entries, and
preserves known prior guidance exposure when a guide version changes. Guide
updates and usage use that normalized projection.

Ten malformed stored shapes are tested after a real accepted disclosure. Each
test verifies the catalog failure, the replayed state hash, blocked guide writes,
and unchanged metadata/journal bytes. Separate checks exercise pure projection,
updates and consented usage with malformed optional in-memory metadata.

### [P2] Journal-only recovery incorrectly erased assistance provenance

Before repair, an injected initial display-metadata write failure could leave a
new guided or practice life durably saved, as intended. After restart, however,
recovery reconstructed default display metadata with guidance off, practice
false, and `excluded_from_unassisted_research=false`. The practice journal's
title still said “separate practice copy.” Losing metadata did not establish
that the earlier interaction was unassisted, so this could contaminate usage
classification after an ordinary recoverable persistence failure.

Recovered non-template journals without explicit saved guidance-origin flags
now receive `provenance_unknown=true`. That flag is preserved through later
metadata saves and restarts; both the guide projection and usage rows exclude
the life from unassisted research. The existing metadata-warning surface explains
that earlier guidance/practice provenance could not be verified. New lives
persist known provenance explicitly. Existing journals are read and replayed
without rewriting their bytes. This intentionally excludes older orphaned lives
rather than guessing their exposure history.

The regression injects the metadata failure for both guided and practice starts,
restarts, explicitly consents to usage, records a usage event, and restarts
again. It verifies the unknown/excluded flags and unchanged world hash and
journal bytes throughout. Another test verifies that a newly created ordinary
unguided life stays known/unassisted on restart, while removing only its saved
guide provenance makes recovery unknown/excluded without a read-time rewrite.

## Other inspected behavior

- Guide progress derives consequential completion from accepted commands and
  participant-visible events. Reading acknowledgements are distinct from world
  actions. Opening/canceling a review does not add a command or grant delivery.
- Early copied evidence and supported market/household/decline routes can advance
  the guide without a forced paid verification. A missed first dispute leads to
  its actual visible outcome rather than an impossible new arrangement.
- Stale or repeated confirmation is rejected. Trial execution and failed journal
  persistence retain the original world/commands/journal; a later display-only
  metadata failure does not report a durable financial action as failed.
- Commons guidance does not invent an unreceived condition report. Its settlement
  explanations use the recorded requests, promises, allocations and actual
  deliveries; current project requirements come from the latest admitted goal
  register/revision.
- Guide routing uses a nearby person, admitted last sighting or named public
  meeting point. It does not use an unseen actor's current coordinates.
- The conversation projection withholds uncopied private documents and topics
  supported by inaccessible source IDs. After copying, it renders the account
  actually admitted to the participant. Modern history cards and guide reading
  update display metadata without entering NPC memory or purchasing actions.
- Cart-choice copy is a deep-copied presentation of the returned proposal. The
  stored exact action remains the existing confirmation contract. The focused
  market test checks the displayed three-coin/twenty-minute terms against the
  actual accepted twenty-minute delivery and its recorded quantities.

## Verification and limits

The final scoped run passed **143 tests** in 7.83 seconds:

```sh
PYTHONPATH=/Users/tanmaygoswami/Library/Python/3.9/lib/python/site-packages \
PYTHONPYCACHEPREFIX=/tmp/kalends-pycache \
/Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m pytest -q --tb=short \
  tests/test_first_session_guide.py \
  tests/test_experience_os_runtime.py \
  tests/test_next_phase_product.py \
  tests/test_first_session_copy_review.py
```

Loopback permission was needed for the disposable HTTP fixtures. An earlier
sandboxed invocation had HTTP-bind setup errors; the permitted rerun above
completed with no failures. The guide-only run passed 29 tests, and
`git diff --check` passed. Initial failure reproductions preceded their repairs.

These checks cover authored scenarios and specific failure injections, not every
possible metadata/filesystem failure, concurrent client interleaving, browser
behavior, or a human learner's understanding. Native scene QA and the unfamiliar
human comprehension gate remain separate work. No backend result here establishes
that the first session is understandable to a new user.
