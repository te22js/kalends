# Run and inspect Fork the City

From the repository root, with Python 3.10 or newer:

```bash
python3 -m kalends.city_server
```

Open **http://127.0.0.1:8765** in a browser. The city and browser use only the
standard library and bundled static files. There is no frontend build, external
font, model service, or runtime package download. Another port can be selected
with `--port 8766`. Only loopback interfaces are accepted.

For a new disposable session without saved state:

```bash
python3 -m kalends.city_server --journal ''
```

The default journal is `.kalends/city_session.json`, ignored by Git. Restarting
replays its configuration, steps and fork commands to recover the same worlds.
Use **Reset** to start again. This is a local single-operator development server,
not a hosted multiplayer service. Close it with Ctrl+C.

## A three-minute playable example

1. Open experiment settings, choose seed **42**, eight citizens, grain rumour,
   structured memory, and no gate. Start the experiment.
2. Press **Step twice**, completing ticks 0 and 1. Dama has sent an outdated
   manifest to Livia, but delivery is still pending.
3. Select **Deliver a verified inspection**, recipient **Livia**, and **Fork this
   moment**. Only the altered Livia visits the grain yard and observes supply.
4. **Step once**. At tick 2 the original Livia reserves three units, spending
   twelve denarii; the altered Livia defers. Compare the actual stock, accounts,
   beliefs and decisions below the map.
5. In the original inspector select Livia's **decision #10**. The structural
   trace leads through delivery #9 and queued message #5 to manifest #4.
   Press **Test a message dependency**: a fresh factual replay reproduces the
   prefix, deletes queued message #5 in a branch, and measures reserve → defer.
   The displayed timelines remain intact. The result concerns this one deletion.
6. Run both histories further. Information, accounts, commitments and trust
   continue changing under the same rules. Click any agent and switch the
   inspected timeline to compare their private information.

Other interventions remove a currently queued message, replace its claim with
available/disrupted, or make an identity control branch. Replacement is explicitly
a new source root; verified inspections must match actual observed supply.
Forks occur at the current completed tick. Only one altered timeline is displayed;
another fork replaces that branch while preserving the original.

**Run/Pause**, **Step**, speed selection, seed, scenario, memory and gate settings
are live controls. Space toggles run/pause and the right arrow steps when focus
is outside an input/control. The event ledger filters and searches actual events.
The footer exports actual snapshots and the reproducible command journal as JSON.

World truth is an operator/evaluator view. A policy receives only one citizen's
local Experience records. Roles and map locations are meaningful simulation
state; coordinates and connectors are a schematic rather than reconstructed
Roman geography. The browser offers 8 and 32 citizens; Python supports up to128.

## Install and test

Running from the checkout requires no install. To install the package and test
dependencies in a conventional environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m pytest tests/ -q
.venv/bin/kalends-city
```

The package includes its HTML/CSS/JS assets. Its build dependency is setuptools
>=68; an old setuptools with `--no-build-isolation` can produce an invalid
`UNKNOWN` wheel and should not be used. A normal clean Python 3.12 installation
was verified during the sprint, including the packaged static assets.

## Reproduce experiments

Outputs refuse to overwrite an existing nonempty experiment directory.

```bash
python3 scripts/reproduce_fork_city.py --out results/fork_city_reproduction --no-plots
python3 scripts/actionbench_sensitivity.py --out results/fork_city_sensitivity_reproduction --seeds 30
python3 scripts/verify_actionbench_replay.py results/fork_city/heldout --sample 24
```

The full reproduction runs 10 development seeds, 30 held-out paired seeds across
four families, 8/32-agent conditions, and the 128-agent scaling subset. Sensitivity
runs additionally vary capacity and relay depth. `--seeds 2` makes a smaller smoke
study, which is not the reported 30-seed result.

For plots, install optional `matplotlib` in the chosen environment, then:

```bash
python3 -m kalends.actionbench.plots results/fork_city/heldout
python3 -m kalends.actionbench.plots results/fork_city/scaling128
python3 scripts/inspect_actionbench.py --help
python3 scripts/profile_fork_city.py --out results/my_city_profile.json
python3 scripts/audit_city_economy.py --help
python3 scripts/plot_actionbench_sensitivity.py --root results/fork_city
```

Raw results are compressed JSON lines containing every tested decision,
configuration and semantic hash. Wall-clock timing naturally varies; the replay
verifier compares event/decision semantics. The full authoritative audit ledger
remains unbounded even when the tested memory backend is capped.
