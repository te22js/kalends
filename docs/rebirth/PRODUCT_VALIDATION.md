# Rebirth: external first-session and return protocol

Prepared 21 October 2026. **No external participants have been recruited, contacted or tested.** Developer browser walkthroughs and automated tests are implementation checks. The following is a prospective protocol, not a result.

## Question and current product boundary

Will a player who has no interest in agent architecture voluntarily keep playing, and later reopen this saved life to discover the consequences of a decision? The candidate hook is a contested cart, distinct information held by its participants, resource/social tradeoffs, and later work made available by the chosen agreement. The build is a small authored district, not an open-world city or a continuously hosted society. Closing the app does not advance offline time; testers must be told that return is to their saved state and they can choose to advance world time.

## Phase 1: six formative players

Recruit six adults who enjoy narrative adventures, history games or systemic simulations; include at least two who do not usually play economic management games. Obtain consent for observation and local diagnostic events. Offer the same compensation independent of praise, success or continued play. Do not use the developer's friends' enthusiasm as demand evidence.

Give only: “You are Aelia. Explore this district and decide what you want to do. You can stop whenever you like.” Start on the title screen. Observe up to twenty minutes; offer an optional ten more minutes without suggesting a task. Do not explain the dispute, optimal route or confirmation controls. After sixty seconds stuck on a control, ask what they expected; mark subsequent help as coaching. Treat assisted completion separately.

Record elapsed **wall time**, not world minutes, to the first intentional interaction, first investigation, first consequential choice and first observed consequence. Record whether the player can name their immediate aim, understands the commitment they accepted, and notices why a later opportunity appeared. The 90-second hook, 3-minute choice, 8-minute consequence and 15-minute new opportunity are design targets, not measured claims. A player declining the dispute is a valid agency outcome; record what they chose to do afterward.

At the end ask, in order: “What surprised you?” “What confused you?” “Which person do you remember, and why?” “What did you want to do that the game did not allow?” “What do you think would happen if you returned?” Ask willingness to return only after behavior has been recorded. Ask for a causal explanation of one changed opportunity without opening World Lab; distinguish true understanding from a guessed reward rule.

After six sessions, repair the two largest repeated problems. Preserve the failed traces and the exact build identifier. Do not pool pre-repair and post-repair performance as one success rate.

## Phase 2: twelve separate, uncoached players

Freeze a new build and repeat with twelve different participants, the same instruction and a predefined twenty-minute observation period. Separate technical failures from players choosing to stop. Count all eligible starts in denominators, including abandonment. Offer the same optional continuation period. Record uncertainty as raw counts; this small sample is diagnostic and cannot estimate a market retention rate precisely.

Prospective progression gates: at least 9/12 can explain their present choice without help, at least 8/12 observe a consequence and correctly connect it to an earlier action, at least 6/12 voluntarily continue past the required observation period, and no more than 2/12 need control assistance. These are internal go/no-go thresholds, not industry benchmarks. Missing a gate means another product iteration, not adding a larger AI model by default.

For return behavior, provide a saved-life link at the end, with **no reminder** for 72 hours. Record voluntary reopening, a meaningful new action and whether the player seeks the outcome they previously anticipated. If a reminder is later sent, report those returns separately. A reopening caused by a reward, reminder or study payment is not an unprompted return. Twelve people cannot validate commercial retention; a later preregistered cohort of at least sixty is appropriate only after the usability gates pass.

## Local event dictionary and privacy

Use only events the implementation actually emits; inspect the server allowlist before analysis. Expected categories are start/first interaction, confirmed choice, consequence first seen, optional objective declined, conversation, journal open, time-control use, within-session return, continuation and session end. A confirmed action must correspond to an accepted engine event; clicking a disabled or canceled choice is not a completed decision. A consequence exposure is not proof that the player understood it.

The implemented server allowlist is `start`, `conversation_open`, `first_interaction`, `decision`, `consequence_seen`, `opening_skipped`, `time_control`, `return`, `journal_open`, `voluntary_continue`, `session_end`, `location` and `evidence_open`. Collection defaults off. Records contain an event name, relative `elapsed_seconds`, world minute and bounded metadata from `screen`, `choice`, `mode` and `location`; the most recent 1,000 records are included in game saves and inspectable in World Lab. A permitted category is not proof the UI emitted it: verify client instrumentation in the frozen build. The present record format does not automatically provide build IDs, per-record opaque session IDs, background/idle detection or deduplication sequence numbers. Keep those in a separate local observer worksheet until implemented, and do not derive active duration or cross-session return rates from missing identifiers.

Keep an opaque local session identifier, event category, relative elapsed time, build identifier and non-sensitive action/event ID where needed. Store no typed dialogue, model prompts, API keys, names, email addresses, screen recordings or IP addresses in ordinary product telemetry. Observation notes and consent contact details belong in separate study storage. Telemetry must have a visible disable control; disabling it must stop collection. Nothing is silently transmitted. Exporting research records requires the participant's consent. State which proposed categories are not yet instrumented instead of inferring them from missing logs.

Use local sequence numbers to deduplicate exposures and tab reloads. Mark browser background/idle periods; report active play and total elapsed time separately. Prefer a deliberate local “end session” event plus a censored duration when tab closing prevents delivery. Do not describe a missing end event as a zero-length session. Keep raw traces only as long as needed for debugging; a proposed thirty-day deletion window must be implemented or managed explicitly, not assumed to happen automatically.

## Interpretation and next decision

The first-party episode is worth expanding only if players understand its choices, remember a person and return for a consequence. A good score on an architecture survey is irrelevant to that decision. If players understand the system but leave, improve dramatic stakes and interaction variety. If they care but cannot act, repair affordances and onboarding. If they cannot explain why anything changed, improve visible consequences and provenance before expanding content.

No satisfaction scores, retention percentages, usability pass rates or willingness-to-pay evidence are currently available. Commercial and educational claims remain hypotheses.
