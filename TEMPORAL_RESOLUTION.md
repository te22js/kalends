# TEMPORAL_RESOLUTION

Assessment of the "adaptive temporal resolution" idea, kept separate from the
main design as requested. Conclusion first:

**Verdict: real engineering value, weak standalone novelty. Keep the
architecture compatible with it; keep it out of the first paper's claims.
Frame it, if at all, as a measured cost/fidelity tradeoff, which *is* a
legitimate experimental variable.**

## Nearest existing concepts

1. **Discrete-event simulation (DES)** — 1960s onward. Advancing the clock only
   to the next scheduled event *is* adaptive temporal resolution; a quiet
   six-hour period costs zero compute in any DES. Textbook material.
2. **Time-stepped vs. event-driven hybrids** — e.g. GEPOC ABM explicitly runs a
   tick-based world with per-agent discrete-event schedulers. Our "quiet period
   compression" is this pattern.
3. **Level-of-detail (LOD) simulation in games** — off-screen NPCs simulated
   coarsely (schedule-level) and refined on demand; shipped in commercial
   engines for ~20 years (e.g. large-scale RPG "radiant"/offline NPC systems).
4. **Multi-scale / multi-resolution modeling** in physics and traffic
   simulation — formal literature on consistency between coarse and fine models,
   including when refinement invalidates coarse summaries.
5. **LLM-specific compute allocation (2025–26)** — APS (adaptive prototype
   selection: query the LLM only for representative agents), MobiVerse (cheap
   domain generator + LLM only for salient decisions), temporal-similarity event
   compression. The "don't call the LLM every tick" insight is already published
   in several forms.

## Can "simulation resolution" be an experimental variable?

Yes — and this is the only defensible angle. Resolution is a knob
(tick length, or salience threshold above which interactions get fine-grained
treatment) with measurable consequences:

- **Cost axis:** number of simulation steps / (in v1) LLM calls.
- **Fidelity axis:** benchmark scores from MemoryBench — does coarsening the
  simulation degrade belief accuracy, provenance correctness, or propagation
  realism, and where is the knee of the curve?

That gives a proper tradeoff curve (fidelity vs. compute), which is publishable
*as an evaluation*, not as an invention. The claim would be "we measure what
coarsening costs epistemically," not "we invented adaptive resolution."

## Risks if we chased it now

- The interesting failure mode (a coarse summary contradicting what fine-grained
  replay would have produced) needs the fine-grained system to exist and be
  trusted first.
- It multiplies the experimental matrix before the base benchmark has results.

## Decision

- v0 uses a plain integer tick loop (48 ticks/scenario) — at this scale,
  resolution optimization is meaningless.
- The event ledger is already sparse (only events, no per-tick state dumps), so
  an event-driven or variable-resolution scheduler can replace the tick loop
  later without touching the ledger, projection, observation, or benchmark
  layers. That is the full extent of accommodation in the current code.
- Revisit after MemoryBench v0 has baseline numbers; if pursued, pursue it as
  the fidelity/cost curve described above. Future work section, not paper one.
