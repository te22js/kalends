# Recorded browser walkthrough

These are actual in-app-browser captures of the frozen local game. They are not
concept art, a mock interface, or a human usability study. The browser control
surface supplied screenshots and interaction; it supplied no video recorder.
The reproducible scripted histories are a separate substitute for a recording,
not a claim that a video was captured.

1. [Arrival](screenshots/01_arrival.jpg): schematic district, real player, clock,
   six coins and the flour objective.
2. [Accepted promise](screenshots/02_promise.jpg): actual contract, cutaway
   interior, nearby Felix and canonical receipt after natural-language review.
3. [Paid work](screenshots/03_paid_work.jpg): 55 minutes pass and three coins
   transfer from Sabina to Aelia.
4. [Promise kept](screenshots/04_promise_kept.jpg): four flour transfer, six-coin
   payment, seven coins remaining, Felix trust 75%, objective fulfilled.
5. [Available dependencies](screenshots/05_causal_records.jpg): actual promise,
   work, purchase and settlement records; recorded dependencies are distinguished
   from an intervention.

6. [Week away](screenshots/06_week_away.jpg): 10,080 actual world minutes execute,
   a new order reopens and a weekly opportunity is recorded.
7. [Remembered return](screenshots/07_remembered_return.jpg): Felix recalls the
   fulfilled promise from his bounded significant memory after seven days.
8. [Executed alternative](screenshots/08_executed_alternative.jpg): remove the
   accepted promise and replay; original/altered coins are 7/1, flour 0/4 and
   Felix trust 75%/60%, with one infeasible later action explicitly skipped.

The full [browser export](browser_final.json) contains 39 accepted commands,
213 original ledger events, the intervention and both outcome states. Full accepted commands remain in the
local `.kalends/pompeii_qa.json` journal; it is a developer demonstration save.
Reproduce three alternative resource routes and seven-day return dialogue with:

```sh
./scripts/run_pompeii.sh --temporary --port 8781
# In another terminal, Python 3.10+:
python3 -m kalends.pompeii.evidence --out /tmp/pompeii-new-evidence
```

The evidence runner outputs actual ledgers, accepted commands, outcomes and
return dialogue under `gameplay_final/` in the checked-in result set. It does
not stand in for the planned independent playtest.
