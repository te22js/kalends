# Verification record — 21 October 2026

The pre-change Genesis suite passed **288 tests in 17.23 seconds**. The complete
post-change suite passed **345 tests in 14.72 seconds** on this host. Differences
in elapsed suite time are not a performance claim. Fifty-seven new cases cover
Pompeii scheduling, gameplay, independent adversarial audit and society metrics.
Local socket tests used a temporary loopback server; no remote deployment ran.

Command used with Python 3.12 and the existing development pytest installation:

```sh
PYTHONPYCACHEPREFIX=/tmp/kalends-pycache \
PYTHONPATH=/Users/tanmaygoswami/Library/Python/3.9/lib/python/site-packages \
/Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
-m pytest tests/ -q
```

The final presentation-only changes also pass `node --check
kalends/pompeii/static/app.js`, `sh -n scripts/run_pompeii.sh`, launcher `--help`
and `git diff --check`. The launcher's live server uses the same tested module.

An independent audit recomputed temporal mean paired speedups and bootstrap
intervals from all 270 raw cells, verified all 90 exact comparisons, and confirmed
that naive action/terminal-outcome projections match. It independently reproduced
society fill means, paired differences, intervals, fees, reach and retention from
240 raw worlds. Both studies' raw hashes and all 57 current Python source hashes
match their frozen registration. Source fingerprint:
`3e99eb91af66bf6fcb61ea57d7ce714ba008807c12ad464910677f1c20d22dbd`.

The same audit found two UI issues, subsequently fixed without changing Python:
context/focus refresh after journal travel and an explicit exit from occupied
interiors. Actual browser use also exposed a skip-menu layout/contrast bug;
buttons now stack within their paper and above the nearby prompt. No test result
is used as evidence that every UI or semantic bug has been eliminated.

The browser completed promise → paid work → purchase → physical delivery, then
opened the causal records. Foreground LIVE advanced the clock while the player
took no actions; COMPRESS and MONTAGE executed scheduled changes; SKIP advanced
10,080 minutes; Felix retained the fulfilled promise on return. World Lab then
removed the original accepted promise and freshly replayed later commands:
original/altered coins **7/1**, flour **0/4**, Felix trust **75%/60%**. One infeasible
later delivery was reported as skipped. The original history stayed intact.

See [eight actual captures](../../results/pompeii/DEMO_WALKTHROUGH.md) and
[the complete browser export](../../results/pompeii/browser_final.json). No supported
video recorder was available. No outside people were contacted and no independent
human playtest, historical expert review, provider trial or hosted load test is
claimed.
