# PAPER_OUTLINE

Working title: *Kalends-MemoryBench: Exact Epistemic Ground Truth for
Evaluating Agent Memory in Persistent Worlds*

Convention: every claim is tagged with the experiment that supports it —
**[E:done/…]** = evidence exists in results/, **[E:needed/…]** = experiment
required before the claim can be made, **[UNSUPPORTED]** = do not claim.

## 1. Problem
LLM-agent memories are evaluated against transcripts with annotated or
LLM-generated labels; none of the standard benchmarks can distinguish "wrong
vs. the world" from "wrong vs. what the agent could possibly know."
[E:done/lit review, RESEARCH_NOTES §4]

## 2. Motivation
Persistent multi-agent worlds need per-agent epistemic correctness: knowledge
boundaries, supersession, provenance, independence of evidence. Failures are
currently invisible to aggregate QA accuracy. [E:done/failure matrix]

## 3. Related work
MemArena (closest; realism-first, partially LLM-labeled, single world),
Ground Truth First, STALE/Supersede/Memora, FANToM/Hi-ToM, epistemic logic,
event sourcing. Positioning: Kalends is the deterministic *instrument*:
exact labels, causal surgery, ancestry accounting. [E:done/RESEARCH_NOTES §4]

## 4. Formal task definition
World, observation function, information set, normative belief under a fixed
revision rule, provenance root signatures, memory system contract, query
family. [E:done/FORMALISM.md — port]

## 5. Kalends environment
Event-sourced deterministic micro-worlds; context-keyed randomness; typed
world configs; 9 scenario families + scaling/capacity axes.
[E:done/generator + configs.json]

## 6. Epistemic oracle
Construction; audit (adversarial unit tests + fuzzing over random worlds);
documented modeling choices (acceptance rule; heard≠believed).
[E:done/tests/test_oracle_audit.py, test_properties.py]

## 7. Memory architectures
recency / BM25 / vector (hashed-BoW, + real-embedding variant
**[E:needed/embedding rerun]**) / vector+recency / vector+metadata /
text-structured (parser under test) / structured (labeled ceiling) /
hybrid naive & guarded.

## 8. Kalends-MemoryBench
~400–27k questions per world across 11 tagged dimensions; exact scoring;
boundary-violation and epistemic precision/recall reported separately from
accuracy. [E:done]

## 9. Experimental protocol
30 seeds × 6 core families; 30 × 3 held-out families (untouched parameter
regions); paired comparisons with 95% CIs and Cohen's d_z; scaling 8→128
agents; capacity 25→unlimited × {fifo, importance}. [E:done/results/]

## 10. Results (current numbers; re-verify before writing)
- Trivial recency floor ≈ 0.63–0.69; everything must beat it. [E:done]
- BM25 > hashed-BoW vector on every family (lexical IDF beats naive cosine).
  [E:done] Whether real embeddings change this: **[E:needed]**.
- Metadata filtering alone removes nearly all boundary hallucination
  (57→1.5 /1000) at +0.09–0.15 overall. [E:done]
- **Naive hybrid loses to structured-only on 9/9 families** — its fallback
  inherits vector's boundary hallucinations (up to 0.59) and collapses at
  scale (0.96→0.68, 8→128 agents). [E:done]
- **Guarded hybrid** (fallback only where the belief table has no opinion)
  beats naive hybrid AND structured on 9/9 families (d_z 1.2–2.5) with ~0
  violations; scale-stable (0.92 @ 128). [E:done]
- Ablations: supersession mechanism is most load-bearing (−0.24 overall when
  removed; contradiction 1.00→0.17); trust second (source 1.00→0.26).
  [E:done/results/ablations]
- Capacity: FIFO catastrophic at small caps; simple importance retention
  restores ceiling even at 25 records; retention policy reshapes the
  hallucination profile. [E:done/results/capacity]

## 11. Ablations — table from results/ablations. [E:done]

## 12. Scaling — accuracy + runtime curves 8→128 agents. [E:done, extend to
256+ **[E:needed]** if reviewers ask]

## 13. Failure analysis — categorized modes (FAILURE_ANALYSIS.md) + the
guarded-router case study as "benchmark → diagnosis → fix → verification".
[E:done]

## 14. Limitations
Oracle-format queries carry schema keys (audited; text track partial);
closed vocabularies + exact match; acceptance rule fixed and shared via the
`accepted` flag (trust *inference* unevaluated); hashed-BoW ≠ real
embeddings; deterministic template language, no NL variety beyond paraphrase
families; small worlds. [E:done/METHODOLOGY_AUDIT.md]

## 15. Ethics / simulation caveats
No human data; no cognitive claims; misuse surface minimal. Note the risk of
overclaiming "epistemic safety" from synthetic-world numbers.

## 16. Future work
LLM answerer/communication-realization tracks (graded scoring needed);
counterfactual question family (infrastructure done [E:done/counterfactual.py],
question generation **[E:needed]**); revision-rule as experimental axis;
uncertainty/calibration dimension; MemArena backend cross-evaluation.

## Claims we cannot make [UNSUPPORTED]
- "First simulated-world memory benchmark" (MemArena).
- Anything about human-like memory.
- That guarded-hybrid superiority transfers to LLM-based memory systems —
  untested until the LLM track exists.
- That vector memory per se is weak — only its hashed-BoW instantiation was
  tested.
