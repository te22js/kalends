# FAILURE_ANALYSIS

Categorized failure modes across 10 seeds × 3 families (propagation,
supersession, private), machine-collected by `scripts/failure_analysis.py`.
Full examples with exposure histories: `results/failures/failures.json`.
Rates are failures **per 1000 questions**.

## The failure-mode matrix

| system | alias miss | boundary halluc. | classification | distrust conf. | missed knowl. | phantom value | source conf. | stale retr. | temporal |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| recency | 8.2 | 36.2 | 106.5 | 10.2 | 3.6 | 20.0 | 60.4 | 0.9 | 66.5 |
| bm25 | 8.2 | 28.2 | 75.3 | 23.7 | 4.4 | 18.1 | 35.8 | 4.7 | 37.4 |
| vector | 14.5 | 57.1 | 78.6 | 31.0 | 4.4 | 19.0 | 52.5 | 5.1 | 55.3 |
| vector_recency | 14.5 | 57.1 | 66.8 | 21.1 | 4.4 | 18.8 | 36.1 | 2.9 | 39.1 |
| vector_meta | 14.5 | **1.5** | 57.0 | 21.2 | 2.3 | 17.2 | 33.5 | 3.2 | 35.9 |
| text_structured | 27.3 | 35.5 | 38.4 | 6.9 | 7.6 | 11.7 | 14.8 | 1.4 | 16.0 |
| structured | 55.0 | 0.0 | 0.4 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| hybrid (naive) | 14.5 | **57.1** | 0.2 | 0.0 | 0.0 | 18.3 | 0.0 | 0.0 | 0.0 |

## Dominant modes, with representative cases

### 1. Boundary hallucination (similarity retrieval's signature failure)
Julia is asked "What do you currently make of the red tavern?" — she has
**zero** exposures about it. Vector retrieval matches "red tavern" against her
memory of a *different* subject sharing a token (e.g. "red gate is intact")
and answers "intact". 57/1000 for vector; the naive hybrid inherits this rate
wholesale because its fallback fires exactly on the questions where the belief
table is (correctly!) empty. **This single mechanism explains why naive hybrid
loses to plain structured on all 9 families and collapses at scale** (more
agents × props → more legitimately-unknown questions → more fallback firings:
0.96 → 0.68 overall from 8 → 128 agents).

### 2. Stale/early retrieval under supersession
Modestus, asked via alias about his own bakery, gets "burning" instead of
"damaged": the fire report is more *similar* to the query than the update.
Similarity retrieval has no notion that newer information supersedes older —
visible in the vector_recency vs vector delta (+0.04..+0.09 overall from a
recency pick rule alone).

### 3. Schema brittleness (structured memory's only failure mode)
Structured memory's errors are ~100% alias misses (55/1000): it cannot
resolve "pistrinum" to the `bakery` key. It never hallucinates, never leaks,
never mis-attributes — it just refuses anything outside its schema. The
text_structured variant trades this for parser errors: fewer alias misses
(27.3, its token-overlap resolver catches some), but new boundary
hallucinations (35.5) from over-eager entity matching — e.g. "mood of Gaius"
questions resolved against "household silver of Gaius" records. This is the
entity-resolution failure family arising organically.

### 4. Distrust confusion
Retrieval systems answer with values the agent heard *and rejected* (21–31
per 1000): the record is in memory (correctly — the agent did hear it), but
retrieval doesn't respect the encoded trust judgment. Structured variants
filter on it and never make this error.

### 5. Source/temporal confusion
Recency and vector systems answer "who told you?" / "when did you learn?"
from the wrong record (top-similar rather than belief-forming). 36–66/1000.

## Capacity pressure (results/capacity, 8 seeds, overload world)

- **FIFO eviction is catastrophic** at tight budgets: structured drops
  0.95 → 0.34 at cap 25 — episodic filler floods out the belief-bearing
  records.
- **Importance-based retention (protect observations > accepted hearsay >
  rejected hearsay > filler) restores nearly everything**: structured holds
  0.945 even at cap 25.
- Surprise worth keeping: under importance eviction, vector-family boundary
  *violations rise* (~0.70): evicting filler removes "safe" retrieval noise,
  so the top hit for an unknowable question is more often a confident
  propositional record about something else. Retention policy reshapes the
  hallucination profile, not just accuracy.

## What the analysis changed

The matrix directly motivated `HybridGuardedMemory` (fallback only on
text-only queries, where the belief table genuinely has no opinion). Result,
30 seeds × 9 families: beats naive hybrid everywhere (+0.03..+0.08, d_z
1.2–2.5), beats plain structured everywhere (+0.02..+0.03, d_z 1.4–2.0),
boundary violations 0.002–0.034 (vs 0.28–0.59 naive), and scale-stable
(0.92 at 128 agents vs 0.68 naive). Residual scale degradation traces to
alias-question fallbacks — the one lane where retrieval is still allowed to
hallucinate.
