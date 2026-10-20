# Pompeii evidence catalog

The authoritative heldout artifacts are `temporal_heldout/` and
`society_heldout/`, with registrations in their sibling JSON files. Both evaluate
the Python runtime frozen at `a024da5`; the complete source fingerprint is in
each registration/manifest. Presentation fixes made afterward do not change
those Python hashes.

| Path | Contents / status |
|---|---|
| `temporal_heldout/` | 270 cells; 1,350 untraced timing worlds and 270 separate traced worlds; raw `worlds.jsonl`, summary, manifest and figures. |
| `society_heldout/` | 240 fresh worlds, raw world-level records, CSV, paired summaries and two figures. |
| `temporal_development_final/` | Frozen-model development run, separate from heldout inference. |
| `temporal_development_v1/` | Initial passive pilot with a different prefix/timing protocol; preserved for provenance. |
| `temporal_development_v2/`, `v3/` | Earlier model/instrumentation development; not confirmatory evidence. |
| `temporal_development_v4/` | Source changed during execution; guard rejected the run. Retained as a rejected pilot. |
| `society_development_v1/` | 80 development worlds; separate seed range and purpose. |
| `gameplay_final/` | Twenty offline language cases, three actual resource routes, seven-day return dialogue, ledgers and executed alternatives. Developer fixtures, not a human study. |
| `gameplay_v1/` | Earlier developer fixture capture, before final reply ordering; preserved, not used as final language evidence. |
| `browser_final.json` | The actual browser walkthrough: 39 accepted commands, 213 original events, original/altered outcomes and intervention. |
| `screenshots/` | Actual browser captures; see `DEMO_WALKTHROUGH.md`. |

Runtime benchmark summaries retain the original plotting status: the bundled
Python runtime did not contain matplotlib. PNG/SVG figures were subsequently
rendered from saved data using the host's plotting installation; separate
`plot_manifest.json` files record their provenance. No worlds were rerun to
create a preferred figure. Society also preserves its plotting recipe.

Seeds, citizens, events and repeat timings have different statistical meanings.
Do not call 1,620 temporal fresh process worlds 1,620 independent society seeds.
The independent unit for reported intervals is thirty paired seeds per horizon.
Coarse timing/provenance differences are not automatically different physical
outcomes. All false reports and private accounts here concern fictional agents.

Reproduction commands, scope and negative results are in
[the handoff](../../KALENDS_POMPEII_HANDOFF.md) and
[the paper](../../docs/pompeii/RESEARCH_PAPER.md).
