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
npm run build > /tmp/kalends-first-session-final-vite.log 2>&1
```

The Python suite received sandbox escalation to allow its loopback HTTP test servers. No test source or frozen research was modified by this validation work. The initial environment probe without `PYTHONPATH` failed with `ModuleNotFoundError: No module named 'pytest'`; the complete suite used the verified path above. This was an environment probe, not a product-test failure.

## Recorded runs

| Run | Python | All frontend tests | Build | Scope |
| --- | --- | --- | --- | --- |
| Before native public-street repair | 1,157 passed in 45.27 s | 208 passed, 0 failed/skipped | Exit 0 | Superseded by native defects; logs retained with `/tmp/kalends-first-session-pre-street-` prefix. |
| After public-street and sticky-action repair | 1,157 passed in 33.58 s | 214 passed, 0 failed/skipped, 1.145 s | Exit 0 | Full rerun completed 24 October 2026 around 15:05 UTC. These broad checks preceded the later priced-choice presentation repair. |
| After priced-choice presentation repair | Followed by the full run below | Targeted scene suite: 23 passed | Exit 0 | Regression checked the shipped rendered HTML before native reinspection. |
| Final behavior-stable run | **1,174 passed in 32.94 s** | **216 passed, 0 failed/skipped, 1.129 s** | **Exit 0, 678 ms** | Ran 24 October 2026, 15:11:05–15:11:46 UTC. Full Python and frontend suites, plus one final Vite build. |

The earlier post-street broad run kept HEAD at `44868e575da0df5a343a3dc44219ea50d6c88edc`, but tested a working tree with concurrent integration-owner changes. `history.py` became modified during that run, so it was superseded by the final run. Those logs are retained with the `/tmp/kalends-first-session-pre-choice-` prefix. No failing product test was hidden or reclassified as passing.

The final run began and ended at **`e04e26dc6307b828666de0979eacaa9b5135598a`**. Product runtime paths (`kalends`, `kalends_rebirth`, `kalends_3d/src`, `kalends_3d/index.html`) had no working-tree diff before or after validation. The independent copy-catalog work was dirty: `COPY_REVIEW.md`, generated `copy_review.html/json`, `scripts/render_first_session_copy.py` and `tests/test_first_session_copy_review.py`. `BACKEND_REVIEW.md`, browser captures and existing test fixtures were untracked. The complete suite collected the available tests, including the expanded copy review. Exact before/after status logs retain these paths. The validator made no runtime edits during this final run.

Final build: `index-D6M7c_WY.js`, `index-Bk7JdV6u.css`. Vite succeeded and retained three notices: the separately served classic `/navigation.js` is not bundled; `/assets/portraits.png` resolves at runtime; the PlayCanvas bundle exceeds the default 500 kB warning threshold. These are build notices, not a claimed runtime asset or performance certification.

## Log locations

- `/tmp/kalends-first-session-validation-commands.txt`: exact invocations and working directories.
- `/tmp/kalends-first-session-final-python.log` and `.exit`: final complete Python output and exit status 0.
- `/tmp/kalends-first-session-final-frontend.log` and `.exit`: final complete frontend output and exit status 0.
- `/tmp/kalends-first-session-final-vite.log` and `.exit`: final successful build and exit status 0.
- `/tmp/kalends-first-session-final-git-before.log`, `git-after.log`, `head-before.log`, `head-after.log`: working-tree and HEAD snapshots.
- `/tmp/kalends-first-session-final-diff-check.log` and `.exit`: whitespace check, exit 0.
- `/tmp/kalends-first-session-final-runtime-diff.exit`: runtime working-tree comparison, exit 0.

Broad automated validation is complete for the runtime at the recorded HEAD. A later behavior change requires a fresh check of its affected behavior. Human and native-browser release gates remain separate.
