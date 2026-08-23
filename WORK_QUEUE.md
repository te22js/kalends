# WORK_QUEUE

State at end of session 2 (2026-08-24).

## Doing
- (nothing in flight; all launched experiments completed and analyzed)

## Next (ranked — mirrors WHAT_I_BUILT.md top-10 with detail)
1. Real-embedding VectorMemory via the `kalends.memory.vector.embed` swap
   point; keep hashed-BoW as deterministic fallback; rerun core suite.
2. Full text-only track: harness flag that strips Experience fields and
   Query keys for ALL systems; retrieval systems need value-parsing to
   answer — reuse text_structured's regexes as a shared parsing helper.
3. LLM-answerer track (needs API; graded scoring design first).
4. Counterfactual question family: generate "would X still believe P without
   E?" questions from `counterfactual.compare`; expected answers exact.
5. Revision-rule axis: parameterize `epistemic.py` acceptance rule
   (threshold, strict-vs-lenient freshness, observation-dominance), rerun.
6. MemArena backend-style cross-evaluation.
7. Trust-inference track (withhold `accepted`).
8. Scale 256–1024 agents; memory profiling.
9. Claimed-vs-actual provenance (distortion-entry localization) questions.
10. Calibration dimension with a proper scoring rule.

## Completed (session 2)
- v0 snapshot: tag `kalends-memorybench-v0`; ENVIRONMENT.txt
- METHODOLOGY_AUDIT.md + fairness fixes (paraphrases, equal-information
  renderings, text_structured, labeled ceilings)
- Context-keyed RNG refactor → clean counterfactuals (kalends/rng.py)
- Typed WorldConfig + generator; 6 core + 3 held-out families
- 9-system baseline suite (recency, bm25, vector×3, text_structured,
  structured, hybrid, hybrid_guarded)
- Independent-origin accounting (root signatures) + corroboration questions
- Epistemic precision/recall; contradiction dims
- Multi-seed runner with CI + paired d_z; 30-seed core & held-out runs
- Scaling 8→128; capacity pressure; component ablations; failure taxonomy
- HybridGuardedMemory (ablation-driven fix, verified on all families+scale)
- 40-test suite incl. property fuzzing + adversarial oracle audit
- FORMALISM.md, FAILURE_ANALYSIS.md, PAPER_OUTLINE.md
- Literature second pass; MemArena repositioning in RESEARCH_NOTES.md §4
- Plots (results/plots), README rewrite, WHAT_I_BUILT.md handoff

## Blocked
- Real-embedding + LLM tracks: need model/API access decision from Tanmay.
- MemArena cross-eval: needs a careful read of their backend implementations.

## Newly discovered (added during session, now folded into Next)
- Naive hybrid's fallback is net negative → guarded router (DONE).
- text_structured scale degradation = entity-resolution collisions → argues
  for action #2's shared parsing helper with better resolution.
- Importance-eviction reshapes error types → calibration dimension (#10)
  should also condition on retention policy.
