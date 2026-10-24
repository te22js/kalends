# Kalends redesign handoff

The redesigned local product is running at **http://127.0.0.1:8833/**. Implementation milestone: **`4ae42e4`** on `codex/complete-experience-redesign`. It keeps the existing Pompeii scene and Shared Observatory simulator, with clearer arrival, conversation, decisions, evidence and results. This is an early local prototype. Engineering checks and agent walkthroughs are recorded; human comprehension, enjoyment and learning have not been validated.

## Run and inspect

From this repository, if the redesigned server is not already running:

```sh
cd /Users/tanmaygoswami/Claude_backup/Projects/kalends
./scripts/run_redesign.sh
```

The launcher rebuilds the scene, chooses a supported Python interpreter and serves port **8833** using the separate default directory `.kalends/redesign_review`. The existing port **8823** installation and its user lives remain separate. Browser QA used port 8831 with disposable `/private/tmp/kalends-redesign-qa` lives; QA 8831 and baseline 8832 were stopped afterward. The seven QA journals are also archived as exact byte copies in `results/redesign/qa-journals/`. No paid inference, publishing or outreach was enabled.

In Pompeii, enter as Aelia, hear Sabina, ask to see her order, examine the household's account, and review a consequential arrangement. Free questions now accept directly and show the newly received account; spending and obligations retain explicit terms. The notebook distinguishes received claims from proof, and surviving historical evidence from invented gameplay. Chapters show meaningful consequences, with routine movement available as supporting detail. Guidance can be turned off and resumed.

In Shared Observatory, ask for a dated capacity report, inspect each team's public project requirement, save an allocation, optionally make a promise, and review the round before advancing. Requested, promised, allocated and delivered quantities remain distinct. Missing requests are labelled missing, saved quantities supersede drafts, and a saved allocation stays fixed for its round. Results report actual delivery and shortages without inventing missing values.

## What changed

- The home and life shell use a calmer visual hierarchy and an actual playable-scene hero. The same life retains its scene while opening notebook, story and help.
- Conversation shows three relevant choices with remaining options under More. Character speech, copied documents, historical context, instructions and receipts have separate presentation.
- A finite server-validated observation path removes redundant reviews for genuinely free questions. It checks identity, proximity/permission and zero material/time/obligation cost, then records the unchanged canonical action.
- Exact free-question retries reconcile from the accepted journal across restart. Paid-review duplicate results are bounded in-memory; an unknown result stays uncertain and is not automatically resubmitted.
- Historical source IDs are qualified in a separate addendum. The existing renderer, map, economic rules, old save formats, frozen candidate and research results remain the underlying systems.

Implementation details and limits: [BACKEND.md](docs/redesign/BACKEND.md), [SCENE.md](docs/redesign/SCENE.md), and [SOURCE_ASSET_REVIEW.md](docs/redesign/SOURCE_ASSET_REVIEW.md).

## Verification status

Latest retained logs show **1,203 Python tests passed**, **249 frontend tests passed**, **91 HTTP-focused tests passed**, and a successful production scene build. All seven disposable QA journals replay exactly on the app's Python 3.12.14, including the failed-promise Observatory branch through Day 2. The frozen candidate and protected release ref pass. These counts are engineering evidence, not human validation.

**Strict preservation remains failed: 1,268 of 1,270 redesign-baseline hashes match.** Two files in `.kalends/first_session_review` changed after the clean 16:39 UTC audit: its product metadata and `pompeii_071176fb5e28.json`. The current journal is valid and replays exactly; its last five commands are movement. The user was reported to be using the older port 8823 installation during that interval, but the writer is unconfirmed. Current user changes were preserved, and neither baseline nor old guard was altered to conceal drift. [Latest exact report](results/redesign/preservation-release.json) · [Earlier six-journal checkpoint](results/redesign/preservation-final.json) · [Earlier clean audit](results/redesign/preservation-review.json).

The initial apparent QA replay mismatch was caused by using unsupported Python 3.9 for verification. A one-ulp movement-distance difference changed the ledger hash. The app's Python 3.12 replay matches exactly; no save or backend repair was needed. Use the same app interpreter for exact replay.

Reproduce the checks:

```sh
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/Users/tanmaygoswami/Library/Python/3.9/lib/python/site-packages \
/Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  -m pytest -q tests
node --test tests/frontend/*.test.cjs
npm --prefix kalends_3d run build
PYTHONDONTWRITEBYTECODE=1 \
/Users/tanmaygoswami/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  scripts/verify_redesign.py --replay-qa
```

The preservation command deliberately exits 1 for the unresolved drift. The older continuity guard intentionally targets another branch. Full commands, exact logs, capture index and distinctions between automated and native evidence are in [VERIFICATION.md](docs/redesign/VERIFICATION.md).

## Actual browser evidence

The regenerated [copy review](results/redesign/copy/copy_review.html) contains 54 evaluated backend states, with every introduction step reached, zero model calls, and source hashes in [its JSON record](results/redesign/copy/copy_review.json). It is a reading catalogue, not a substitute for the actual product captures below.

Useful starting captures under `results/redesign/browser/`:

- [Current visible home](results/redesign/browser/final-home.jpg), on port 8833, and [desktop home](results/redesign/browser/final-home-desktop.jpg). The hero is a byte-identical copy of an actual fullery capture, cropped by CSS; its provenance and matching hash are in the source/asset addendum.
- [Final return-home composition](results/redesign/browser/final-home-return-desktop.jpg) shows the later tighter hero framing and the saved-life invitation. The underlying capture remains unchanged.
- [Matched earlier conversation](results/redesign/browser/matched-before-conversation.jpg) and [redesigned conversation](results/redesign/browser/matched-after-conversation.jpg).
- [Opened account](results/redesign/browser/pass2-document-open.jpg), [counter](results/redesign/browser/pass2-counter-geometry.jpg), and [fullery](results/redesign/browser/pass2-fullery-geometry.jpg).
- [Narrow return correction](results/redesign/browser/pass3-narrow-return.jpg) and [narrow conversation](results/redesign/browser/final-narrow-conversation.jpg). These use a 390-pixel iframe; the final conversation includes extra-large text and reduced motion. This is not a physical phone test.
- [Fresh-probe Pompeii result](results/redesign/browser/fresh-probe/15-pompeii-chapters.jpg) and [Observatory delivery comparison](results/redesign/browser/fresh-probe/22-observatory-result-comparison.jpg).
- [Deliberate over-allocation review](results/redesign/browser/final-observatory-allocation-review.jpg) and [missed-promise result](results/redesign/browser/final-observatory-missed-promise.jpg): a 4/4/4 allocation against eight usable units delivered 4/4/0, explicitly missing the four-unit Lin promise. A total of 13 was rejected and an earlier review was canceled without acceptance.
- [Next-day result review](results/redesign/browser/final-next-day-review-fixed.jpg): the retained result now opens and receives focus when the guide asks to review it; the earlier hidden-result failure is also archived.
- [Persistent project answer](results/redesign/browser/final-observatory-inline-answer.jpg) and [narrow answer](results/redesign/browser/final-narrow-observatory-answer.jpg), rechecked after replacing the transient status-only reply.

The [fresh agent report](docs/redesign/FRESH_AGENT_PROBE.md) records two UI-only journeys, canceled review, source distinction, guidance off/resume and leave/return, with 25 screenshot/AX pairs. It also preserves ambiguities encountered at that checkpoint. No continuous video or human playtest was recorded. Supplied reference images under `docs/redesign/brief/` are design references, not evidence of the running game.

## Remaining limits

The scene bundle remains about **2.206 MB minified / 566 kB gzip**, with the existing >500 kB warning and legacy runtime-resource notices. Small browser trace samples do not support a performance-improvement claim. Screen-reader use, complete keyboard-only journeys, physical phones, broad device performance and long-duration recovery remain unvalidated.

The natural-language interface supports a finite set of questions/actions. Character speech remains authored and offline; believable expression, live-model conversational quality, voluntary participant return and long-term learning retention remain unvalidated. An absent team request remains unknown even when its public project threshold is known. Paid-review uncertainty across server restart remains explicit rather than being guessed away. Current preservation drift prevents an unconditional clean-release claim.

The live pilot remains **disabled**, with zero calls and spend. The frozen research study still shows no candidate advantage over V3 on the primary held-out outcome. The exhibit-release failure analysis is labelled post-exposure development diagnosis, not a new win: [RESEARCH_DIAGNOSIS.md](docs/redesign/RESEARCH_DIAGNOSIS.md).

## Three decisions for future human feedback

1. **Keep or revise the opening.** With consenting unfamiliar participants, observe whether they can explain their role, choose a first action and distinguish a received claim from historical evidence without an agent explaining it. Current agent completion does not answer this.
2. **Keep or simplify the decision/result flow.** Observe whether participants understand the cost, round lock and request/promise/allocation/delivery distinctions before confirming, then recognize a missed promise afterward. Use their mistakes and explanations to prioritize changes; automated request sequencing is not a comprehension measure.
3. **Choose the next return/accessibility work.** Test actual keyboard and screen-reader use, physical narrow devices, and a later voluntary return. Determine whether saved consequences and authored characters are clear and compelling enough to continue. Interest, believable expression and long-term retention remain open questions.
