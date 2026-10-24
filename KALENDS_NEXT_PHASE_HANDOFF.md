# Kalends next-phase handoff

The next phase is implemented as a local product journey and an offline research
study over the existing runtime. It is an early prototype, not a commercial game
or evidence of human learning, demand or retention.

## Open and run

Open **http://127.0.0.1:8810/**. Port 8800 is the previous interface; its original
save directory is preserved. The new service uses `.kalends/next_phase/`.

```sh
./scripts/run_next_phase.sh --port 8810 --directory .kalends/next_phase
```

The launcher selects Python 3.10 or newer. On a checkout without the retained
build, first run `npm run build` in `kalends_3d/` using its existing dependencies.
Only one server writer can own a save directory. No offline world progression is
simulated. A stopped server is resumed with the same command and directory.

## Source checkpoints

Branch: **`codex/experience-journey`**, based on `21127f0`.

- `fe47832`: life-scoped service, isolated journal loading and participant history.
- `1288c81`: diagnostic, frozen comparisons, raw worlds and research report.
- `ac1b631`: public website, saved-life flow and stable 3D scene integration.
- `d15c121`: finite Studio fixes, persistence distinctions and final regressions.

The delivery-evidence commit follows these checkpoints. Nothing was pushed.

## What now works

The public site offers two actual worlds, role/situation details, separate new
lives, a saved-world home, Research, About, data/accessibility and asset pages.
The marketing page loads no 3D runtime until a participant enters Pompeii.

Inside a life, accepted receipts drive resources and time. Your story contains
participant-admitted chapters, people, commitments, consequences, expandable
ordinary activity and dated support. Reflection reconstructs the exact evidence
prefix before a choice and executes an omission with fixed later commands,
disclosing skipped commands. Notes/bookmarks remain personal interpretations.

Pompeii preserves its scene, camera, conversation and unsent text while viewing
history or reconciling accepted actions. The same tab restores local view state
after reload. Local drafts are tab-session state; closing that tab discards them.
World choices, positions and balances persist in their server journals.

Observatory presents Amir, Mira and Lin over the unchanged team IDs. Requests,
promises, allocations and actual deliveries are distinct. It states the public
capacity rule, dates reports, protects known deadlines and requires an explicit
choice to cross them. Closed rounds cannot accept new product promises.

Research Lab requires acknowledgement and durably marks exposure; private DOM is
removed on return. Local usage events are opt-in and omit raw free text. Studio
edits only template, title, seed and horizon, then validates and creates a new
identity; it does not generate arbitrary worlds or executable rules.

## Demonstrated journeys

In Observatory, requested Mira's dated report, promised Lin four units and
allocated 4/4/4. The public deadline stop preserved the choice window; explicit
settlement executed 4/4/0 and missed Lin's promise. Omitting allocation changed
executed units 8→0 and completed projects 2→0 without changing the original life.

In Pompeii, spoke with Sabina about ordinary life, cancelled a preview, then paid
the reviewed three-coin market arrangement. Later time brought new counter work,
Lucius's replacement concern and Dama's independent household duties. Walked to
Sabina's new counter and received the actual changed delivery greeting. Camera
and draft continuity, full reload, restart and both domain layouts were tested.

Reproduction details and captures: `docs/next_phase/PRODUCT_QA.md` and
`demo/next_phase/WALKTHROUGH.md`.

## Research result and limits

The initial 128-world audit found that the prior recorded next-action plan did
not influence selection. The new comparison gives every arm the same real
multi-step, resumable controller and public institutional registers.

After development-only evidence of memory headroom, a small exact-dependency
retention bonus was compared with V3 hybrid, current observation, FIFO/BM25 and a
larger admissible-history reference. The authoritative frozen run has **760
worlds**, four development templates and four internally reviewed variants.

Against V3, the patch completed 30/30 versus 0/30 chains in the unchanged-condition
interruption case. A reverse-correction case tied at 30/30 while saving 30 paid
rechecks. A fresh-correction control tied; a hidden reversal defeated every arm.
The bounded arms obey a 16 KiB complete mind/controller ceiling; the generous
reference uses more memory. These are narrow authored-scaffold results, not a
general planning breakthrough or external replication. The patch remains
research-only; existing cognition defaults are unchanged.

V2 corrects a before-choice trace alias and reproduces the same world outcomes.
All 760 raw ledgers pass arithmetic checks; eight samples replay exactly from
the frozen source archive. The earlier run is retained and labelled superseded
for trace provenance. Report, failures, plots, costs and protocol:
`docs/next_phase/RESEARCH_REPORT.md` and
`results/next_phase/research/frozen_comparison_v2/`.

**Live inference, embeddings and paid calls: zero. Spend: $0.** No authorized
endpoint/budget was configured. The offline language path and existing provider
contracts were retained; live-model expression quality is untested. A consenting
human-use/authoring protocol is prepared; nobody was recruited or enrolled.

## Verification and remaining work

Final verification: **1015 Python tests**, **144 frontend tests**, successful
PlayCanvas build, real desktop/narrow journeys, stale and cross-life tabs,
damaged-save isolation, journal failure rollback, metadata-warning-after-charge,
Lab exposure and finite authoring. All **17 original saves** retain their baseline
hashes. Previous studies, world specs and authoritative runtime are unchanged.

The measured 36-second balanced-quality M2 scene sample averaged about **30.07
frame callbacks/s**; it does not establish 60 FPS or physical-display latency.
Separate loopback API medians were 32.91 ms for catalog and 9.28 ms for life.
Full conditions and raw receipts are in PRODUCT_QA and `results/next_phase/`.

Still uncompleted: live-model evaluation, real-device/mobile performance and a
full assistive-technology audit, consenting human use, modern dense retrieval,
independently authored task structures and broad cognition/generalization claims.
The content is finite and early; a polished entrance is not proof of enjoyment.

The next three evidence-driven tasks are: observe consenting first/return sessions
using the prepared protocol; test the candidate on independently authored task
structures with credible retrieval/planner baselines; then evaluate a provisioned
endpoint under an explicit numeric budget and a grounded full-loop audit.
