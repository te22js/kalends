# Next-phase research artifacts

- `development_gate/`: 128-world diagnostic before candidate implementation, with its own frozen source and raw receipts.
- `frozen_comparison/`: first 760-world execution, preserved after discovery of a controller-plan trace alias. See its `SUPERSEDED_TRACE_NOTE.md`; do not use its before-choice plan field as provenance.
- `frozen_comparison_v2/`: current corrected 760-world execution. Same cases, seeds, candidate, endpoints and world ledgers; snapshots are detached. Includes `protocol.json`, `frozen_source.zip`, `raw/`, `summary.json`, `figures/`, `controls/`, `arithmetic_controls.json`, `audit_repair_check.json` and `frozen_replay.json`.

The interpretation, limitations, results table and reproduction command are in `docs/next_phase/RESEARCH_REPORT.md` at the repository root. All runs are offline; no inference, embeddings or paid provider calls were made.
