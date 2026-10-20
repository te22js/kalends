# The flour promise and the days after

Launch `python -m kalends.pompeii.server --port 8780` with Python 3.10 or later,
then open http://127.0.0.1:8780/. The saved command journal defaults to
`.kalends/pompeii_session.json`; `--temporary` opens an unsaved fresh life.
Genesis uses its own server and journal. Never point the two applications at the
same save file. A save whose replay hash differs from the runtime is preserved
and rejected rather than silently migrated.

## A first five minutes

1. Click Felix's bread counter above the main street. Watch Aelia follow the
   route into the cutaway interior. Speak with E or the nearby prompt.
2. Say **“I promise four flour units.”** Review and confirm. The world records
   an open four-unit delivery contract due before dusk, with an actual deadline.
3. Choose how to obtain sufficient coins. The routes below are alternatives;
   they do not create an item merely because it appears in a conversation.
4. Return to Felix, request **“Buy four flour units”**, review the quantity and
   confirm. Four units must exist and the current price must be affordable.
5. Say **“I brought the flour.”** Confirm while holding all four units. Actual
   flour transfers to Felix, payment transfers back, the promise settles, and
   Felix's trust and reputation change.
6. Use the journal to inspect the exchange and its available dependencies. Use
   SKIP → one week, return, and ask **“What do you remember about me?”**

The UI's contextual actions offer the same validated operations. Use **X** or the explicit **Step outside** button to leave an interior. Navigation is
available through the scene or the journal's place list. A doorway route takes
world minutes; a shift or service consumes its stated duration. Aelia cannot
interact with someone in a different room or across the district.

## Three demonstrated routes from the default opening

| Route | What to do | Main consequence |
|---|---|---|
| Wage | Visit Sabina at the thermopolium; ask for a paid shift | 55 minutes, three coins, a real transfer from Sabina. Daily extra shifts are limited. |
| Household backing | Visit Lucius in the household; ask for an advance | Eight coins now, household-client affiliation, and 120 minutes of service owed before three days. |
| Brokerage | Meet Marcus on the street; ask what he has heard about flour; confirm the conversation; offer the retained report to Felix | Felix can pay two coins for a useful dated report. Other recipients value the same report differently and may refuse it. |

At the frozen default seed, the automated demonstrations settle at world minutes
79, 22 and 11 respectively. The wage route leaves seven coins, household route
twelve with service owed, and brokerage route six. These exact fixtures do not
establish a dominant strategy or general success rate. Price changes, stock,
timing, existing knowledge, liquidity and trust matter. Ignoring the promise
still leaves NPC work, supply arrivals and information routines operating.

The household service must **finish before** its deadline. Completing a shift
exactly at the deadline is rejected before any accepted mutation. Leaving for a
week without serving changes Lucius's trust and reputation and marks the
institutional obligation missed. To keep it, return and request **“Complete
service”** while there is enough time. The advance cannot be farmed repeatedly.

## Reports are information, not a truth editor

“Flour supply is available” and “Flour supply is disrupted” create assertions
at the current minute. They do not change actual supply. A question transfers a
character's retained report only when that conversation is confirmed. A paid
inspection returns after fifteen minutes. Its current observation and bounded
dated-dispatch lookup can distinguish a contradicted report from one that was
true earlier and has since become stale. An old disagreement alone is not proof
of a lie.

Brokerage transfers the report's observation date and origin. It does not mint
independent witnesses: repeating the same observer's statement does not raise
independent-root confidence. A recipient refuses reports it already knows or
cannot use, and a fresh timestamp on a still-useful identical report is not an
unlimited payment source. Direct inspection fees and sales affect real balances.
A character can choose inspection or defer procurement using retained evidence;
these choices can cost more than they improve executed delivery.

## A deadline means a physical commitment

Early completion requires all four units. At the scheduled deadline, an open
contract can settle using flour physically present with Aelia near Felix;
holding flour elsewhere does not remotely deliver it. A missed or partial
settlement does not receive a full reward. Closed promises cannot pay twice.
The following dawn may reopen a new order; settled prior contracts remain in
the institutional record. Sufficiently low trust prevents a new promise or trade.

## Time and the life that continues

| Control | Computation | Presentation |
|---|---|---|
| LIVE | Minute reference, while foreground playback is enabled | One world minute per 1.7 real seconds; can be stopped. |
| COMPRESS | Exact next-event dispatch for 30 minutes | New positions, resources and journal events appear. |
| MONTAGE | Exact dispatch to the next scheduled transition | A compact selection of actual relevant records. |
| SKIP | Exact dispatch to the next transition or one week ahead | Return summary; every supported scheduled consequence still executes. |

A day is 1,440 world minutes and the opening clock is 08:00. The default world
has a 60-day simulation horizon; configuration supports up to 365 days, but the
fresh temporal study tests at most thirty. No human biological or subjective
time claim follows from faster computation.

## Explain and compare

SHOW WHY traces recorded information/account dependencies available to the
player. Hidden source records remain hidden; an event's date alone is not a
causal experiment. Open journal → World Lab for the complete operator archive,
private state, actual outcome metrics and alternate-history controls. Select an
accepted player action and remove it. The system reconstructs a fresh world and
replays later accepted commands at their original start times where feasible.
Infeasible commands are reported as skipped. The original history remains intact.

This is a declared command-removal intervention, not a claim that every changed
later event was independently caused by that action. Compare actual cash, flour,
work delivery, relationships and obligations rather than counting shifted event
IDs. Removing an early delivery may still allow a later deadline settlement if
Aelia remains physically present with the flour; that is a real model behavior,
not evidence that the intervention was fabricated.

## Evidence and present limits

`python -m kalends.pompeii.evidence --out /tmp/pompeii-evidence-new` reproduces
the offline language cases and three scripted histories. Existing evidence is
under `results/pompeii/gameplay_final/`. The records are developer fixtures, not
independent human playtests. The parser handles a bounded vocabulary; unsupported
speech becomes a grounded conversation rather than an arbitrary world mutation.
The historical setting and exact economic rules have different evidence levels;
consult the source ledger before treating game balances as ancient prices.
