# Fork the City execution record

Baseline inspected: `8040b22` on clean `master`. Protected branch:
`codex/fork-the-city`. Historical `results/` directories are retained unchanged;
all sprint experiments go under `results/fork_city/`.

## Audit (completed)

- Read README, packaging, event/state/observation/epistemic interfaces, memory
  implementations, scenario generator, benchmark harness, tests and Git history.
- Existing engine: append-only `Ledger`, deterministic state projection,
  position/scope observations, keyed RNG, private experiences, provenance roots,
  nine memory baselines and whole-run incident-deletion counterfactuals.
- Missing: trade utility, economic commitments, step/snapshot forks, browser UI,
  action evaluation. Add these alongside existing APIs, preserving MemoryBench.
- Baseline: 40 tests passed (5.16 s); seed 42 has 1,034 events and 427 questions.
  Full new audit artifacts: `results/fork_city/baseline/`.
- Host default Python is 3.9.6; package declares Python >=3.10. Validate source
  with the available interpreter and disclose the declared support version.

## Implementation / verification checklist

- [ ] Add reusable local-information decision/economy loop and grain scenario.
- [ ] Deep-copy tick boundary forks, keyed paired randomness, traceable parents.
- [ ] Build local HTTP API and functional map/timeline/inspector/comparison UI.
- [ ] Compare existing memories with fixed decision policy and separate gates.
- [ ] Freeze development/held-out seed split before running held-out worlds.
- [ ] Save raw per-world results, clustered paired statistics and actual plots.
- [ ] Verify determinism, containment, duplication, correction, branch isolation.
- [ ] Verify API and browser controls; capture genuine screenshot if supported.
- [ ] Literature audit, research note, strategic note, reproducible handoff.
- [ ] Commit tested milestones; report limitations and actual evidence honestly.
