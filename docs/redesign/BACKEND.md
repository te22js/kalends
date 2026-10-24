# Redesign backend boundary

The redesign adds a free-observation protocol over the existing `ExperienceRuntime` actions. It does not replace the simulator, change accepted-command revision 1, or introduce a second world journal. `kalends/experience_os/observation.py`, `product.py`, `product_server.py`, and `runtime.py` are the implementation boundaries described here.

## Free observations

`POST /product/api/observe` takes the life `id`, `action`, `expected_revision` (the accepted command count), and `expected_state_hash`. The retained scene uses `POST /api/observe` with its existing life selector and the same three observation fields. Extra fields are rejected.

The action object must contain exactly `action` and `recipient`. The allowlist is deliberately finite:

| Adapter | Action | Recipient |
| --- | --- | --- |
| Pompeii | `hear_dispute`, `examine_receipt` | `Sabina` |
| Pompeii | `examine_tablet` | `Dama` |
| Commons | `share` | `team_a`, `team_b`, `team_c` |

Pompeii additionally checks proximity and whether the canonical choice remains enabled. A detached trial executes the canonical action and compares world time, every actor's cash and inventory, and commitments. Any change in those resources rejects the free path. Knowledge and ledger changes are allowed: asking successfully is itself an accepted event. Commons sharing still requires the speaker to possess a legitimate retained report; the observation protocol supplies no private report of its own.

The trial never saves. Acceptance uses `ExperienceRuntime.commit`: copy the world, execute, append the original action to the original journal, save atomically, then replace the live world. A save failure preserves the previous world, accepted commands, and saved journal. Private account contents remain withheld until the actual disclosure event is admitted to the participant view.

## Reconciliation and limits

An observation identity hashes the life, expected command count, expected state hash, and exact action. If the command at that starting index already equals the requested action, the server replays the earlier prefix and checks its hash. A match returns `already_accepted`, the original receipt and accepted revision, without appending a command. This survives a server restart because it derives from the canonical journal. It reconciles an identical request; it does not forbid asking the same supported question at a later revision.

An old revision with a different action or hash returns `observation_stale`. Other explicit errors include `observation_not_permitted`, `observation_invalid_identity`, `observation_unavailable`, and `observation_not_free`. Scene responses attach projected speech and conversation data. A duplicate can have an old accepted revision alongside a current snapshot. The product's display metadata can still update on a duplicate; the world command does not repeat.

The HTTP handler holds `service.lock` across validation and acceptance. The command-line server also takes a directory writer lock. The standalone `observe()` helper does not itself lock its entire prefix check, so the serialized HTTP guarantee should not be generalized to arbitrary concurrent direct callers.

Paid reviews retain their separate confirmation flow. Product and scene facades cache the last 32 confirmed receipts in memory. A repeated cached token returns its accepted result; a stale offer returns `offer_changed`. After restart or eviction, an unknown token returns `outcome_unknown` with `outcome: uncertain`. This is not a durable paid-request identity across restart. The response instructs the client to read the saved life and never automatically resubmit. A display-metadata failure after a world save is reported as a warning on the accepted result; it does not turn a saved charge into a failed charge.

## Existing verification coverage

- `tests/test_redesign_observations.py`: private-before-disclosure behavior, exact allowlist rejection, stale and wrong-hash identity, restart reconciliation, save rollback and retry, injected resource-cost rejection, proximity, retained Commons reports, promise validity, and duplicate/stale/unknown paid reviews.
- `tests/test_next_phase_product.py`: real HTTP free-observation acceptance and prefix reconciliation, nonmutating review/cancel, world-save failure, accepted-charge metadata failures, and exact scene accepted revisions.
- `tests/test_experience_os_server.py`: life-isolated retained-scene actions, paid duplicate handling, stale reviews, saved replay, and existing HTTP origin/visibility checks.
- `tests/test_experience_os_runtime.py`: transactional rollback, canonical replay, and facade actions against the same compiled life.

This subagent's bundled-Python 3.12.14 run of those four files produced **87 passed and 51 HTTP fixture setup errors**: the sandbox denied local socket binding before those cases could run. There were no assertion failures. The root agent separately reported its completed project run as **1,202 passed**. These are distinct executions. The inspected tests do not establish arbitrary concurrent direct-helper safety or durable paid-token reconciliation after restart.

## Read-only preservation checker

`scripts/verify_redesign.py` requires branch `codex/complete-experience-redesign`, protected ref `refs/heads/codex/experience-journey` at `6ebe9ec463c0144ba4ce53cb182646f5bf87f152`, and the exact recorded redesign-baseline file hash. Every file listed by that baseline must match, without metadata exceptions. It also calls the existing `verify_candidate()`; it does not edit or bypass any earlier branch-specific guard.

`--replay-qa` replays known version-1 journals only from `/private/tmp/kalends-redesign-qa`. Repeated `--qa-life ID` arguments restrict verification to named idle QA lives. Replay creates no persistence path, refuses commit/save calls, validates command times and receipt identities, checks final state hashes, and compares source bytes after reading. It never replays a protected user save as part of the normal QA scan.

Use the same supported interpreter as `scripts/run_next_phase.sh`. The checker refuses Python below 3.10 and records its interpreter. An initial check incorrectly used this machine's unsupported Python 3.9.6: one `math.dist` rounding difference at Pompeii command index 25 entered the ledger hash. Bundled Python 3.12.14 reproduced the saved hash exactly. No backend or saved state repair was needed, and cross-version byte-identical floating-point replay is not established by this check.

The executed output is `results/redesign/preservation-final.json`. Six explicitly selected QA lives, including completed probe lives and the root agent's paused Pompeii life at minute 380, replayed exactly under Python 3.12.14 with their source bytes unchanged. The frozen candidate and protected release ref passed.

### Concurrent protected-save drift remains a failure

The independent audit retained in `results/redesign/preservation-review.json` at **2026-10-24 16:39:06 UTC** matched all **1,270** redesign-baseline files. The later check matched **1,268**. Neither baseline nor either changed save was rewritten by this review.

| Protected file | Expected SHA-256 | Observed SHA-256 | Observed mtime (UTC) |
| --- | --- | --- | --- |
| `.kalends/first_session_review/.product/state.json` | `02aaab807264c4629af854edd65c0b862f0a63d7da97e27e2920b79717c1308d` | `a4a672cd506b1a321fb821286a49ccb03d00455ee70237589c0cb5d8b404dcb3` | 2026-10-24 16:43:23.139444 |
| `.kalends/first_session_review/pompeii_071176fb5e28.json` | `9d61bbac2710370c9f3da4145de55e536f2795c18dae8031e2053c39dfefc854` | `c01a3507dfc7577bf1b9e3aaeaa9d11140a8ca6f9275180f0bc955751f50ce40` | 2026-10-24 16:43:17.548634 |

The current changed journal has the known version-1 fields, **173 commands**, and world minute **52**. A separately authorized read-only diagnostic with Python 3.12.14 reproduced its saved state hash `ab6184c79c5929cbf6f228fa5b3a1ebf4c02a7a1ac09df37b23bf57380b14605`, matching all command times and receipt identities. Its source bytes were unchanged by the diagnostic. The last five commands were movement only:

| Index | Start → end minute | Receipt |
| --- | --- | --- |
| 168 | 51 → 51 | 243 |
| 169 | 51 → 52 | 245 |
| 170 | 52 → 52 | 246 |
| 171 | 52 → 52 | 247 |
| 172 | 52 → 52 | 248 |

The root agent relayed that the user had the older port 8823 experience open during this interval. That is consistent with concurrent use but does not independently identify the writer. Attribution remains unconfirmed. The strict check correctly stays **failed**; current user changes are preserved and the earlier clean audit remains available.
