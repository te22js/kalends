# Complete experience redesign: verification record

24 October 2026. Branch: `codex/complete-experience-redesign`; implementation milestone **`4ae42e4951adedc21a54524d430ea767c2e86c42`**. This record separates executed automated checks, agent-operated browser evidence, and remaining limits. There was no consenting human playtest, measured learning study, physical-phone qualification, or screen-reader session.

## Executed checks

| Check | Observed result | Evidence and scope |
| --- | --- | --- |
| Final Python suite | **1,203 passed in 40.95 s** | `results/redesign/verification/python-final.txt`, copied from `/private/tmp/redesign-full-python-final.log`. Retained `verification/python.txt` is the earlier 1,202-pass checkpoint. |
| Final frontend suite | **249 passed, 0 failed** | `results/redesign/verification/frontend-final.txt`, copied from `/private/tmp/redesign-all-frontend-final.log`. `verification/frontend-checkpoint.txt` is the earlier 246-pass checkpoint; `redesign-all-frontend-11.log` was 247. Node fixtures exercise actual handlers/modules but do not establish native layout or assistive-technology behavior. |
| HTTP-focused suite | **91 passed in 3.41 s** | `results/redesign/verification/http.txt`; `/private/tmp/redesign-http-final.log`. Real local HTTP fixtures, distinct from browser walkthroughs. |
| Production scene build | Passed | `results/redesign/verification/build-final.txt`: `index-BbGe3kff.js`, 2,206.15 kB; gzip 565.59 kB. The earlier build is retained in `verification/build.txt`. |
| Frozen candidate | Passed | `verify_candidate()` in `results/redesign/preservation-release.json`. |
| Protected release ref | Passed | `refs/heads/codex/experience-journey` remains `6ebe9ec463c0144ba4ce53cb182646f5bf87f152`. |
| Disposable QA journals | **7 exact replays** | `preservation-release.json`, Python 3.12.14; source bytes unchanged; no persistence path. Includes Pompeii `ed1ec6ef7a97`, `19e89db35b27`, paused `3c440b0a972f`, Observatory `f9b238328cb8` and `6f82840644f2`, and two unplayed compatibility lives. The new Observatory life has five commands through minute 1440. |
| Strict redesign preservation | **Failed: 1,268 / 1,270 hashes match** | Two older save files changed after the earlier clean audit. Details below. No baseline was relaxed. |
| Existing paid live pilot | **Disabled** | `results/redesign/pilot-status.json`: explicit enable required; zero network calls, turns used, estimated spend and reserved spend. |

The build retains the large-chunk warning (>500 kB), a non-module `/navigation.js` notice, and runtime resolution of `/assets/portraits.png`. Build success does not remove these warnings or establish good download performance.

The independent subagent's constrained run of four backend files produced 87 passes and 51 fixture setup errors because its sandbox denied loopback socket binding. Those setup errors are separate from the root agent's completed full suite. The final full-suite log above is the applicable complete result.

## Reproduction commands

Run from the repository root. The checked app interpreter on this machine is CPython 3.12.14; the launcher requires Python 3.10 or newer. The user-site path below supplies the existing pure-Python pytest installation to that interpreter; no new dependency was installed for these checks.

```sh
cd /Users/tanmaygoswami/Claude_backup/Projects/kalends

# Local redesigned product, default port 8833 and separate .kalends/redesign_review saves.
./scripts/run_redesign.sh

# Full Python suite, including local HTTP fixtures where socket binding is permitted.
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Users/tanmaygoswami/Library/Python/3.9/lib/python/site-packages \
/Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m pytest -q tests

# Frontend fixtures and scene build.
node --test tests/frontend/*.test.cjs
npm --prefix kalends_3d run build

# Strict preservation and all journals in the designated idle disposable QA directory.
# Currently exits 1 for protected-save drift, despite exact QA replays.
PYTHONDONTWRITEBYTECODE=1 \
/Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/verify_redesign.py --replay-qa
```

The normal launch is available at `http://127.0.0.1:8833/` and remains running at handoff. Root QA used port 8831 and `/private/tmp/kalends-redesign-qa`; baseline work used isolated ports 8830 and 8832. QA 8831 and baseline 8832 were stopped after verification. These identities matter: the older experience on port 8823 is a separate running installation. Do not repoint a test writer at an existing user-save directory. Seven exact QA byte copies are retained under `results/redesign/qa-journals/`, with hashes matching the release report; `--replay-qa` itself reads the designated temporary directory while it remains available.

## Native browser evidence

All names below are real files under `results/redesign/browser/`. They capture the actual application, not the supplied design-reference HTML. `.txt` files are accessibility snapshots unless described as traces. Some states were captured as text only. No continuous video recording was retained.

| Path or basename | Evidence |
| --- | --- |
| `before-home`, `before-arrival`, `before-conversation`, `before-market-review`, `before-market-result`, `before-story`, `before-observatory` (`.png`, `.txt`) | Original interface on disposable baseline lives. Initial captures used 518×720; later captures were 1280 wide. They are not all matched viewports. |
| `before-report-review.txt` | Earlier Observatory report review; text only. |
| `matched-before-arrival.jpg`, `matched-after-arrival.jpg` | Same initial scene/camera comparison in the matched capture pass. |
| `matched-before-conversation.{jpg,txt}`, `matched-after-conversation.{jpg,txt}` | Earlier and redesigned conversation surfaces. |
| `matched-before-home.{jpg,txt}`, `matched-before-free-review.jpg` | Baseline home and administrative review for a free question. |
| `pass1-arrival`, `pass1-conversation`, `pass1-counter-object` (`.png`, `.txt`) | First implementation inspection, retained as intermediate evidence. |
| `pass2-free-answer.txt`, `pass2-document-open.{jpg,txt}`, `pass2-household-account.{jpg,txt}` | Direct answer, newly copied account opened immediately, account quantities/source/date. |
| `pass2-counter-geometry.jpg`, `pass2-fullery-geometry.jpg` | Actual rendered counter and fullery geometry. Native appearance does not establish surveyed archaeological accuracy. |
| `pass2-counter-card.{jpg,txt}`, `pass2-fullery-card.txt`, `pass2-history-target.{jpg,txt}` | Historical cards, material-evidence versus invented-event distinction, and received-account comparison. |
| `pass2-decline.txt`, `pass2-deadline-review.jpg`, `pass2-autonomous-story.{jpg,txt}` | Declined involvement, deliberate deadline review, and household delivery without participant intervention. |
| `pass2-live-reading.txt`, `pass2-live-resumed-then-paused.txt` | Live/reading states at 14:08 and later 14:20. Snapshots alone do not measure elapsed live timing. |
| `pass2-narrow-return-overlap.jpg`, `pass3-narrow-return.{jpg,txt}` | Observed duplicate return overlay and the later corrected state. |
| `final-narrow-conversation.{jpg,txt}` | Current Chreste conversation in a 390×720 CSS-pixel iframe fixture with extra-large text and reduced motion enabled. Primary choices remain in the scrollable conversation; Chreste's enslaved status is explicit. It is not a physical phone test. |
| `final-home.{jpg,txt}` | Actually visible redesigned home on port 8833 in the approximately 503-pixel-wide user panel, with current playable-scene hero and both world entries. |
| `final-home-desktop.{jpg,txt}` | Current home in the desktop browser, with the actual fullery capture rendered through the home CSS crop. |
| `final-observatory-project-question.txt` | Current explicit project-need answer: four units in one delivery, with an absent current request still labelled absent. No invented request. |
| `final-observatory-allocation-review.{jpg,txt}`, `final-observatory-cancel.txt`, `final-observatory-invalid.txt` | Current review explicitly warns of 12 allocated units against an eight-unit report and states the round lock; cancel retains the draft; a total of 13 is rejected. |
| `final-observatory-missed-promise.{jpg,txt}`, `final-observatory-results-expanded.{jpg,txt}` | Deliberate risky allocation delivers Amir 4 / Mira 4 / Lin 0 from eight usable units. Lin's separate four-unit promise is explicitly missed; the expanded table separates every quantity. |
| `final-next-day-review-hidden-failure.jpg` | Retained failure evidence: next-day Review the result initially targeted a result hidden in the collapsed Last round disclosure. The later handler correction opens that disclosure before focusing the result. |
| `final-next-day-review-fixed.{jpg,txt}` | Native correction verified: Last round's result is expanded and `obs-result` has focus, visibly showing Lin's missed promise on Day 2. |
| `final-observatory-inline-answer.{jpg,txt}` | Native correction verified: the public project answer stays inline in the conversation. |
| `final-narrow-observatory.{jpg,txt}`, `final-narrow-observatory-answer.{jpg,txt}` | Actual 390-pixel Observatory layout and inline answer in the labelled iframe fixture. |

The archived fixture sources are `viewport-fixture.html` and `viewport-observatory-fixture.html`. Their labels explicitly say “not a physical phone.” They were served only during QA; the temporary fixture files were removed from the production static directory before handoff. The root inspected narrow return/conversation display, including extra-large text and reduced motion, in the real browser. This does not substitute for touch-device testing, complete keyboard traversal, screen-reader testing, or a human accessibility study.

### Fresh agent probe

The fresh agent received only the starting URL and followed displayed UI instructions before inspecting source or prior QA. It created Pompeii `pompeii_ed1ec6ef7a97` and Observatory `observatory_f9b238328cb8`, made one explained consequential choice in each, found results, and left/returned with guidance off/resumed. It deliberately opened and canceled an early payment review. This is an independent agent usability probe, not successful human comprehension.

Every basename below has an unedited full-viewport `.jpg` and full `.ax.txt` under `fresh-probe/`:

| Range | Exact capture names |
| --- | --- |
| Opening and first account | `01-home`, `02-pompeii-arrival`, `03-pompeii-sabina`, `04-pompeii-premature-review`, `05-pompeii-order` |
| History and second account | `06-pompeii-historical-place`, `07-pompeii-source-distinction`, `08-pompeii-history-expanded`, `09-pompeii-household` |
| Return and market result | `10-pompeii-guidance-off`, `11-saved-lives`, `12-pompeii-return`, `13-pompeii-final-review`, `14-pompeii-outcome`, `15-pompeii-chapters` |
| Observatory planning | `16-observatory-arrival`, `17-observatory-report`, `18-observatory-request-question`, `19-observatory-allocation-review`, `20-observatory-round-review` |
| Observatory result/return | `21-observatory-result`, `22-observatory-result-comparison`, `23-observatory-return`, `24-observatory-guidance-resumed`, `25-observatory-review-destination` |

Capture `06` is while still walking. Capture `14` shows the former Reflect destination; its name does not assert that the receipt is visible. The full click paths, inferences and issues remain in `docs/redesign/FRESH_AGENT_PROBE.md` rather than being rewritten after subsequent corrections.

The baseline free Sabina question, copied order, and Mira report each required two clicks after reaching their conversation. The probe used one explicit accepted question for each. Paid choices and round completion still required review. This is a count of observed interaction steps, not a measured comprehension or time-on-task improvement.

The later root-operated Observatory life `observatory_6f82840644f2` took a separate failure path: early Mira report, public Lin project question, a four-unit Lin promise, rejected total 13, cancellation of a total-12 review, confirmed 4/4/4 allocation, then settlement at eight actual units. The displayed 4/4/0 delivery missed Lin's promise. Advancing to the next day recorded Lin's project as missed. This broadens native branch coverage without changing the fresh probe's earlier evidence.

## Automated coverage and later corrections

`BACKEND.md` details the exact observation whitelist, privacy boundary, canonical save rollback, restart-safe free-question identity and limited in-memory paid-review reconciliation. Frontend tests cover repeated clicks, a lost observation response retried with its original identity, stale rejection, cross-life messages, retained scene identity, unsent drafts, guide off/resume, and uncertain paid confirmations. Unknown paid outcomes are never silently resubmitted.

The independent product review's earlier 27/28 checkpoint is preserved in `PRODUCT_REVIEW.md`. Its spoken-testimony/document regression is included in the passing final frontend suite. Current rendering preserves testimony versus copied document, saved allocation values take precedence over drafts, and incomplete historical records retain unknown fields rather than manufactured zero/NaN. The added project-need control answers the public threshold without turning it into a submitted request; its current browser text is indexed above.

The fresh probe's friction report remains a historical observation. Later source/tests change result navigation to chapters, clarify locked allocations, reduce administrative reflection copy, and expose per-person project thresholds. Only current native captures establish the displayed paths they actually include; passing a regression does not retroactively change an earlier screenshot.

The final native pass also found two presentation defects: next-day result navigation did not open its collapsed disclosure, and a public project answer appeared only in a transient status message while being misclassified as invalid telemetry. The root corrected the disclosure handler and made the answer persistent inline with no invalid-action event. The 249-pass frontend run includes the added regressions. Native `final-next-day-review-fixed` confirms the expanded, focused result; `final-observatory-inline-answer` and `final-narrow-observatory-answer` confirm the visible persistent answer. The original failure capture remains retained.

## Preservation and replay diagnosis

The 16:39:06 UTC independent audit matched all 1,270 redesign-baseline files. The 16:45:54 UTC six-journal checkpoint remains in `preservation-final.json`. The latest executed report, `preservation-release.json` at **16:54:01 UTC**, records implementation commit `4ae42e4`, verifies all seven QA journals, but still matches 1,268 protected hashes and correctly exits 1. Both later reports identify:

- `.kalends/first_session_review/.product/state.json`, modified at 16:43:23.139444 UTC.
- `.kalends/first_session_review/pompeii_071176fb5e28.json`, modified at 16:43:17.548634 UTC.

`BACKEND.md` and both preservation reports record full expected/actual hashes. The changed journal has 173 commands at minute 52; its last five commands are movement. Separately authorized read-only replay on Python 3.12.14 reproduced its saved state exactly and left the bytes unchanged. The root relayed the user's concurrent use of the older port 8823 experience. This is consistent with concurrent activity; the writer is not independently identified. User changes remain preserved. Neither a reset nor a new baseline is justified by a failing check.

An earlier apparent QA replay defect came from the reviewer's unsupported system Python 3.9.6. At command index 25, `math.dist` differed by one ulp; the final differing fidelity field was the ledger hash. Both normal replay and the native canonical loader reproduced the saved QA state under the application's bundled Python 3.12.14. The checker now rejects Python below 3.10 and records its interpreter. No gameplay/backend repair was required, and this does not establish byte-identical replay across every supported Python version.

The older `verify_continuity_release.py` still refuses this branch because it requires `codex/continuity-release-prep`. It was not bypassed or relabelled as passed. The earlier audit separately records the older preexisting `.kalends/next_phase/.product/state.json` exception against the older protection baseline. The new strict checker gives no exception to either changed redesign-baseline save.

## Performance, research and remaining limits

`verification/movement-comparison.json` contains browser instrumentation, not visual proof or GPU elapsed timing. Both arms have four accepted idle movements; DPR is 2, balanced quality, Apple M2/ANGLE, and 697 draw calls. Scene viewport heights differ (642 vs 650 CSS pixels). Idle-input-to-committed-draw p95 was 60.990 ms before and 60.555 ms after; frame p95 was 35.610 vs 36.985 ms. The small unequal frame samples and near-equal input samples do not justify a speedup claim.

The existing research result remains a candidate/V3 tie on 160 paired primary outcomes (140/160 successes each), with all five arms failing the exhibit-release workflow. `RESEARCH_DIAGNOSIS.md` is explicitly post-exposure development diagnosis, not a new held-out win. Candidate, task and primary result bytes remain frozen. The live paid pilot stays disabled; no endpoint or spending cap was authorized.

`SOURCE_ASSET_REVIEW.md` retains qualified source IDs, all 52 asset fingerprints/notices, and the new hero's byte-identical provenance from the actual fullery capture. Native geometry captures show the existing schematic objects; they do not certify historic placement, clothing, physical accuracy, or learning. Character speech remains authored/offline; live-model expression quality, believable characterization, human comprehension, enjoyment, voluntary return, learning retention, accessibility with assistive technologies, broad device performance, and long-duration failure recovery remain unmeasured. Natural-language interpretation remains finite; absent requests remain absent. The strict preservation gate is unresolved because current user changes must be preserved.
