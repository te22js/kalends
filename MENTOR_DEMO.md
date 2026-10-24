# Kalends temporary mentor demo

The owner changed the access requirement on 25 October 2026: **anyone with the link may open the demo, without an email allowlist or login**. This is a public, unlisted preview. It is not a private authenticated deployment.

URL: https://unloader-cheek-pond.ngrok-free.dev/

The instance is separate from the owner's local server and saves. The live instance is `.kalends/mentor-demo-live-20261025`; public browser QA lives remain preserved in `.kalends/mentor-public-qa-20261025`. Earlier OAuth QA and local QA fixtures are retained separately. The tunnel forwards only the restricted demo origin on `127.0.0.1:8840`.

## Operate the demo

1. Open the URL. ngrok's free tier may show a **Visit Site** notice on the first visit.
2. Choose **Enter Pompeii** and **Begin**, or **Enter Shared Observatory** and **Begin the guided round**.
3. Review a consequential choice before confirming it. Reading and cancelling a review do not accept the choice.
4. **Your story** shows accepted history. Return to the home page or **Your story** in navigation to resume a saved life.

All visitors share the temporary demo lives and can change them. Do not enter personal or confidential information. The retained prototype permits eight started lives in one instance. There is no per-visitor private account or save isolation. No paid model is connected; optional telemetry and personal notes are disabled.

The host computer and ngrok process must remain running and connected. This is a local temporary preview, not an always-on hosting service. Free-tier notices, bandwidth and service limits apply. The initial Chrome 3D load was slow before reaching ready; no load-time benchmark or human playtest success is claimed.

## Revoke and shut down

Run these commands **from the Kalends repository**. None delete saves.

Immediately close access (every new request checks the local policy):

```sh
.kalends/demo-tools/venv/bin/python scripts/control_mentor_demo.py revoke --instance .kalends/mentor-demo-live-20261025
```

Close access and stop both the dedicated demo origin and tunnel:

```sh
.kalends/demo-tools/venv/bin/python scripts/run_mentor_demo.py stop --instance .kalends/mentor-demo-live-20261025
```

Check the two dedicated processes:

```sh
.kalends/demo-tools/venv/bin/python scripts/run_mentor_demo.py status --instance .kalends/mentor-demo-live-20261025
```

The policy expires after 24 hours even if the processes keep running. Expiration/revocation rejects assets and gameplay as well as pages. A browser may retain already-rendered content; previously delivered content cannot be recalled.

To intentionally reopen this same public instance for 24 hours, first stop it, then rotate its ingress credential and restart:

```sh
.kalends/demo-tools/venv/bin/python scripts/configure_ngrok_demo.py --instance .kalends/mentor-demo-live-20261025 --origin https://unloader-cheek-pond.ngrok-free.dev --public --hours 24
.kalends/demo-tools/venv/bin/python scripts/run_mentor_demo.py start --instance .kalends/mentor-demo-live-20261025
```

The ngrok account credential is in the ignored, private `.kalends/demo-tools/ngrok-auth.json`. The instance's traffic policy contains an independent ingress credential. Both remain outside Git and outside the HTTP file manifest. Do not paste their contents into chat, screenshots or reports. ngrok account-level revocation is also available by deleting/revoking its agent credential in the ngrok dashboard; that may affect other uses of the same credential.

## Verified implementation and limits

- Dedicated loopback origin, fresh demo save directory, offline cognition and no loading of historical research examples.
- Explicit participant route and static-file allowlists. LAB, Studio, authoring, research, experimental forks, annotation, telemetry, export and administration are rejected by the server. Participant-scoped supporting evidence remains available; hidden records are excluded by the retained engine.
- Public traffic policy strips visitor-supplied ingress/identity headers and injects a random 256-bit ingress credential. The origin checks its hash in constant time, the exact Host and the current access policy. This protects the origin boundary; public mode deliberately does **not** authenticate visitors.
- Origin checks on writes, bounded JSON bodies, duplicate-field and ambiguous-path rejection, generic errors, no-store responses, security headers, bounded connections and request/start/write/time-advance rate limits.
- The agent's local inspection interface and request/response capture are disabled. No reverse proxy to the existing local development server exists.
- The local source retains the optional Cloudflare Access and ngrok Google OAuth modes; neither visitor-authentication mode is enabled in the final public instance.

## Evidence

`results/mentor_demo/final-tests.txt`: **142 passing Python tests** across the restricted server, existing guides and product regression tests. `frontend-tests.txt`: **39 passing frontend tests**. The first HTTP test attempt was blocked from binding loopback ports by the default sandbox; the approved rerun passed. This was an environment failure, not a passed test.

`public-link-checks.json`: **20 actual HTTPS probes** without cookies, including forged identity headers and protected POST routes. Public participant resources returned 200; protected pages and writes returned 404. OAuth-only probe results are retained as historical evidence from before the owner requested public access.

`public-walkthrough.json` records **agent-operated browser QA, not human playtesting**. The public guided Pompeii route included early evidence, cancellation, a paid delivery and its actual 4/2 outcome. The public Observatory route included an 8-unit report, a warned 4/4/4 allocation, cancellation, confirmation, optional-promise skip, actual 4/4/0 settlement and resumption at 23:59 after reload. Chrome independently reached the public shell and the embedded 3D scene's ready state. Both complete public guided routes were executed in the in-app browser.

Public revocation was exercised against the real URL and returned `Demo access is closed`. Captures include `public-pompeii-result.png`, `public-observatory-result.png`, `public-observatory-return.png`, `chrome-public-scene-ready.png`, `public-studio-denied.png` and `public-revocation.png`.

One broad desktop-state check was rejected by automatic approval review because it could include unrelated private content. It was not retried through another desktop mechanism. Verification continued through the scoped demo browser tabs.

## Reproduce the checks

This machine's pytest installation is outside the isolated demo venv, so the recorded command is:

```sh
PYTHONPATH=/Users/tanmaygoswami/Library/Python/3.9/lib/python/site-packages .kalends/demo-tools/venv/bin/python -m pytest tests/test_mentor_demo.py tests/test_first_session_guide.py tests/test_next_phase_product.py -q --tb=short
node --test tests/frontend/first_session_product.test.cjs tests/frontend/first_session_allocation_review.test.cjs tests/frontend/first_session_reflection.test.cjs
.kalends/demo-tools/venv/bin/python scripts/verify_demo_public_gate.py --origin https://unloader-cheek-pond.ngrok-free.dev --public --output results/mentor_demo/public-link-checks.json
```

Create an additional **new** instance without copying any saves:

```sh
.kalends/demo-tools/venv/bin/python scripts/prepare_mentor_demo.py --destination .kalends/NEW_DEMO_DIRECTORY
```

The destination must not exist. The bundle manifest hashes source modules, fixed scenario specifications, participant assets and the retained built renderer. It excludes existing saves, personal notes, research reports, logs, credentials, filesystem exports, tests and development endpoints. Startup checks every manifest hash. The test-only browser gateway in `tests/manual_demo_fixture.py` is loopback-only, is excluded from the bundle, and must never be tunneled.

## Sources

- ngrok official agent download: https://ngrok.com/download/mac-os
- Free-plan domains and limits: https://github.com/ngrok/ngrok-docs/blob/main/pricing-limits/free-plan-limits.mdx
- Header addition semantics (append, not replace): https://ngrok.com/docs/gateway/traffic-policy/actions/add-headers
- OAuth and exact email restrictions (optional mode): https://ngrok.com/docs/gateway/traffic-policy/actions/oauth
- Cloudflare signed-token validation (optional mode): https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/

No domain, paid plan or paid inference service was purchased. This release's remaining human decision is whether the mentor can understand and use the first session without assistance; automated and agent-operated checks do not establish that.

## Live handoff recorded

The final live instance was created from commit `4974c6e0b47def13b81aff9ebac71b0c9b62f295` with **zero started lives**. Twenty final public HTTPS route checks passed again after the switch. Access expires **26 October 2026 at 01:38 IST**. See `results/mentor_demo/live-release.json`, `public-live-checks.json` and `live-home.png` for the exact handoff record. QA lives and their accepted journals remain in the stopped QA instance.
