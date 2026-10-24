# Independent first-session validation

Validation agent: `first_session_scene`. These are executed automated checks and builds. They do not establish human comprehension, enjoyment, educational efficacy, screen-reader compatibility or physical-phone behavior. Native browser evidence belongs to the integration owner's separate trace and captures.

## Environment and exact invocations

Python: bundled CPython 3.12.14. Pytest: 8.3.5, loaded from the existing user site-packages path. Node: v24.11.1. npm: 11.6.2.

From `/Users/tanmaygoswami/Claude_backup/Projects/kalends`:

```sh
env PYTHONPATH=/Users/tanmaygoswami/Library/Python/3.9/lib/python/site-packages:. PYTHONPYCACHEPREFIX=/tmp/kalends-pycache /Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -m pytest -q tests > /tmp/kalends-first-session-final-python.log 2>&1
node --test tests/frontend/*.test.cjs > /tmp/kalends-first-session-final-frontend.log 2>&1
```

From `/Users/tanmaygoswami/Claude_backup/Projects/kalends/kalends_3d`:

```sh
npm run build > /tmp/kalends-first-session-choice-fix-vite.log 2>&1
```

The Python suite received sandbox escalation to allow its loopback HTTP test servers. No test source or frozen research was modified by this validation work. The initial environment probe without `PYTHONPATH` failed with `ModuleNotFoundError: No module named 'pytest'`; the complete suite used the verified path above. This was an environment probe, not a product-test failure.

## Recorded runs

| Run | Python | All frontend tests | Build | Scope |
| --- | --- | --- | --- | --- |
| Before native public-street repair | 1,157 passed in 45.27 s | 208 passed, 0 failed/skipped | Exit 0 | Superseded by native defects; logs retained with `/tmp/kalends-first-session-pre-street-` prefix. |
| After public-street and sticky-action repair | 1,157 passed in 33.58 s | 214 passed, 0 failed/skipped, 1.145 s | Exit 0 | Full rerun completed 24 October 2026 around 15:05 UTC. These broad checks preceded the later priced-choice presentation repair. |
| After priced-choice presentation repair | Not yet rerun | Targeted scene suite: 23 passed | Exit 0 | Final broad rerun awaits the integration owner's source-stability window. |

The post-street broad run kept HEAD at `44868e575da0df5a343a3dc44219ea50d6c88edc`, but tested a working tree with concurrent integration-owner changes. `history.py` became modified during the run; the status logs preserve this limitation. A later source change requires a fresh check of the affected behavior. No failing product test was hidden or reclassified as passing.

Latest build at this entry: `index-D6M7c_WY.js`, `index-Bk7JdV6u.css`. Vite succeeded and retained three notices: the separately served classic `/navigation.js` is not bundled; `/assets/portraits.png` resolves at runtime; the PlayCanvas bundle exceeds the default 500 kB warning threshold. These are build notices, not a claimed runtime asset or performance certification.

## Log locations

- `/tmp/kalends-first-session-validation-commands.txt`: exact invocations and working directories.
- `/tmp/kalends-first-session-final-python.log` and `.exit`: post-street complete Python output and exit status.
- `/tmp/kalends-first-session-final-frontend.log` and `.exit`: post-street complete frontend output and exit status.
- `/tmp/kalends-first-session-final-vite.log` and `.exit`: successful post-street build; later choice build is in `/tmp/kalends-first-session-choice-fix-vite.log`.
- `/tmp/kalends-first-session-final-git-before.log`, `git-after.log`, `head-before.log`, `head-after.log`: working-tree and HEAD snapshots.
- `/tmp/kalends-first-session-final-diff-check.log` and `.exit`: whitespace check, exit 0.

This file is deliberately explicit about superseded checks. It must be updated after the final broad rerun and before the handoff treats automated validation as complete.
