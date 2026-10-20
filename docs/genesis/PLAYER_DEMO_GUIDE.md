# Play The City That Remembers You

This is a real local simulation with an offline language grammar. No credentials
or paid models are required. Python **3.10 or later** is required. The original
Fork the City app remains available with `python3 -m kalends.city_server`.

## Start and resume

From the repository root:

```sh
python3 demo/genesis/launch.py --port 8770
```

Open [the local town](http://127.0.0.1:8770/). This independently launchable demo
uses seed2026, eight citizens, 96 ticks and **capacity256**, deliberately allowing
the merchant to retain a three-day episode. The ordinary server's default
capacity is32. The curation is disclosed; backend outcomes are not fabricated.

On this Mac, the system `python3` is3.9.6. Use the available Python3.12 instead:

```sh
PYTHONPYCACHEPREFIX=/tmp/kalends-pycache /Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 demo/genesis/launch.py --port 8770
```

Ctrl+C stops the process. Run the same command again to resume from
`.kalends/genesis_demo.json`. Refreshing the browser preserves the world.
`--fresh` archives the old journal with a UTC timestamp and starts the curated
world again. Use a different `--port` if8770 is occupied. No background time is
simulated while the process is stopped, and the running world advances only
when you use its controls.

For an ordinary configurable world with its own journal:

```sh
python3 -m kalends.genesis.server --port 8771 --journal .kalends/my_world.json
```

## Flagship demonstration, 60–90 seconds

1. **0–15s:** Select Livia on the map. The town opens at tick2, already in motion.
   The purse and grain at the bottom of the map belong to you. Citizens pursue
   different schedules, purchase rules and duties.
2. **15–30s:** Press **Share a rumour**, or type **“Grain supply is disrupted.”**
   Review the exact recipient, value, timestamp and unverified source. Press
   **Confirm this action**. The private Player→Livia message is now a real event;
   the shipment itself has not changed.
3. **30–45s:** Press **Return after three days**. This actually runs72 ticks to74.
   Livia's next paid inspection can check the dated dispatch record and contradict
   this claim. In the curated run her trust falls from60% to32%, closing commerce.
   Other activity and delivery outcomes follow ordinary rules.
4. **45–65s:** Press **Why trust me?**. Her explanation must cite the retained
   Player-specific assessment. Press **SHOW WHY** to see real cited events.
   Ask about grain to hear a dated report rather than an omniscient answer.
5. **65–90s:** Enter **Research / operator**. Under historical interventions,
   choose **remove the player message**, select its event, and execute the fork.
   The original remains intact. Compare the rerun's trust, actions and settlement.
   A difference is measured from these worlds; it is not a generated hypothetical.

At defaultcapacity32, the merchant may no longer retain the reason after72 ticks.
An honest “I cannot recall” is expected there. Never substitute an invented loss
or archival memory to make that version more dramatic.

## Technical walkthrough, 3–5 minutes

- **0:00–0:45:** Explain scoped communication and confirmation using the rumour.
  Show the receipt; contrast a claim with an actual supply event in Research mode.
- **0:45–1:30:** Run through an inspection, a purchase and settled delivery. Inspect
  actual attempted/filled units, cash effects and the private bounded records.
  Show that a zero-fill purchase has no invented success reward.
- **1:30–2:30:** Ask about trust and SHOW WHY. Explain chronology, retained evidence,
  structural parents and the stronger test of rerunning an intervention. The paid
  dated inspection distinguishes an old truthful report from an actual false one.
- **2:30–3:30:** Remove the historical claim. Inspect original/altered maps, trust,
  decisions, individual beliefs and economic settlement. Run an identity control
  if desired; equal outcomes are a valid result. Operator correction is visibly
  privileged, unlike paid next-tick participant verification.
- **3:30–4:15:** Refresh; stop/restart the server with the same journal. Return to
  the same world. Export its accepted actions and safe current view. Research
  export includes complete audit records.
- **4:15–5:00:** Open `results/genesis/heldout/summary.json` and the paper. Explain
  the30 independent seed clusters, delivered-unit primary outcome, adverse/null
  result, stock controls and valuation sensitivity. Demonstrating this simulator
  does not establish novelty, entertainment retention or a viable company.

## Supported language

Questions include “What do you know about grain?”, “Why don't you trust me?” and
“What contracts do you need to fulfill?”. Questions use only the selected
character's retained memories and own accounts.

Actions include “Grain supply is available”, “Grain supply is disrupted”,
“Verify the grain supply”, “Share what I verified”, “Buy 2 grain from market”,
“Buy 1 grain from Livia”, “Contract 2 grain due in 4 ticks”, and “Retract #37”.
Use spaces around numbers in normal input. A trade can fail if inventory, cash
or trust is insufficient. “Share what I verified” requires your actual retained
personal inspection. Retractions can withdraw only your own originating claim.

The parser is a limited grammar. A sentence about tomorrow is normalized into
the explicitly reviewed current-time claim; it does not model a future forecast.
An ambiguous supply alternative produces a choice. The engine never executes an
unreviewed interpretation. Unsupported requests can ask for clarification.

## Recording and evidence

No supported video-recording API was available in this environment, so no video
is claimed. The independently launchable real app, these timed scripts, the
curated configuration, actual simulation exports and real browser screenshots
under `demo/genesis/screenshots/` form the substitute. They can be replayed and
recorded with an ordinary screen recorder later. Screenshots are actual UI
captures, not generated mockups. The capture manifest identifies their state.

The app is local only. It has not been published, publicly deployed or pushed.
Research mode is an intentional local audit toggle, not a multiplayer access
control boundary. See `EXPERIMENTAL_VALIDITY.md` for precise guarantees and limits.
