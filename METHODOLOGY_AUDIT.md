# METHODOLOGY_AUDIT

Audit of Kalends-MemoryBench for circularity and unfair advantage, written
*before* trusting any headline result. Each concern from the brief, findings,
and what was changed. Changes are implemented, not proposed, unless marked.

## 1. Do benchmark questions expose structured fields?

**Yes, mostly.** Every question except the alias family carries
`(subject, predicate)` in the Query object, i.e. the exact lookup key of the
structured belief table. This is a deliberate *oracle-format track*, and its
consequence must be stated plainly: **on this track, StructuredMemory is not a
finding — it is the solvability ceiling.** It stores the very fields the
oracle stores; scoring it against the oracle is scoring a copy against the
original.

**Changes made:**
- Question texts are now drawn from paraphrase template families (2–4 surface
  forms per question type, chosen deterministically), so retrieval systems
  can no longer rely on one fixed query string echoing the rendering.
- Added `text_structured`: same architecture, but ingest is text-only by
  contract — proposition, value, time, source, trust judgment and origin are
  all parsed from the rendering. The `structured` − `text_structured` gap is
  now a *measured quantity* (the "by-construction advantage"): ~0.93 vs ~0.69
  overall on the dev scenario; multi-seed numbers in results/.
- Result tables keep `structured` as an explicitly labeled ceiling column.

**Not changed (open):** a fully independent question channel (e.g. an LLM
paraphraser or human-written questions) — deterministic templates still share
a grammar family with the renderings. Listed in next actions.

## 2. Which systems have privileged access to ontology/schema?

`structured` (native keys), `vector_meta` (metadata filter on query keys),
`hybrid` (via its structured half). `recency`, `bm25`, `vector`,
`vector_recency`, `text_structured` work from text. This is now a *spectrum
by design* — the experimental question is precisely how much schema access
buys — but any comparison must say which side of the line each system is on.
The results tables group them accordingly.

## 3. Could a trivial dictionary lookup solve some dimensions?

**Yes — and we now measure it.** StructuredMemory *is* the dictionary lookup.
More importantly, the new `recency` baseline (latest lexically-matching
record) reaches ~0.70 overall on the dev world — the floor every
sophisticated system must clear. If a paper result cannot beat
latest-matching-record, it is not a result.

## 4. Does the vector baseline receive equivalent information?

Audited, two gaps found and fixed:
- The listener's trust judgment existed only as a structured field. Now the
  rendering carries it too (" I did not believe it.").
- Provenance roots existed only in oracle chains. Now every tell's rendering
  carries the speaker's claimed origin ("it goes back to Decimus who saw it"),
  and the structured fields carry the same as `claimed_origin_*`. Origin
  information is communication *content*, available to every system equally.
- The `as_of` vintage of relayed information is rendered ("as of hour 5, …").

Remaining honest asymmetry: hashed bag-of-words embeddings have no synonymy,
so alias phrasings penalize `vector` more than a real embedding model would.
Results say "similarity-retrieval architecture with lexical embeddings", and
DECISIONS.md #6 requires re-running with real embeddings before publication.

## 5. Are retrieval budgets / capacities / update opportunities equal?

- **Update opportunities: equal.** Every system ingests the identical
  experience stream, in order, once.
- **Retrieval budget: not equal.** Retrieval systems answer from top-k=4;
  structured systems answer from an unbounded exact-key table (whose per-key
  entry count is small but unbounded). Mitigations: (a) capacity-pressure
  experiments (scripts/capacity_experiment.py) put every system under the
  same record budget with the same eviction policies; (b) k is a config
  constant, reported.
- **Compute: comparable at this scale**; per-system benchmark seconds are
  recorded in the scaling experiment so "structured/hybrid become
  computationally ugly" is checkable rather than assumed.

## 6. Are questions generated independently enough from the systems evaluated?

Partially. Questions come from the oracle's ontology — necessarily, since
the oracle defines ground truth. The risks and mitigations:
- *Template echo*: mitigated by paraphrase families and alias phrasings.
- *Developer overfitting*: the `heldout` suite uses parameter regions
  (population, topology, hostility) never used while building or tuning the
  systems; nothing was adjusted after its first run.
- *Vocabulary leak*: subject names are adjective+noun pairs sharing tokens
  across DIFFERENT subjects ("old bakery"/"new bakery"), which makes surface
  matching actively dangerous rather than helpful — hard negatives by
  construction.

## 7. Which scores are meaningful, and which are ceilings/sanity checks?

| Score | Status |
|---|---|
| `structured` on keyed questions | **ceiling / sanity check** — near-1.00 expected by construction |
| `hybrid` vs `vector_meta` | meaningful — does the symbolic layer beat metadata filtering? (paired, same seeds) |
| `hybrid`/`structured` vs `recency` | meaningful — clearing the trivial floor |
| `structured` vs `text_structured` | meaningful — price of losing oracle-format ingest |
| `vector_recency` vs `vector` | meaningful — value of a time model alone |
| retrieval systems' boundary-violation rates | meaningful — the safety-style metric |
| alias dimension for `structured` | meaningful as a *brittleness* measure, not an overall-quality measure |
| anything on the dev `rumor` scenario | demo only — hand-designed during development |

## 8. Known remaining weaknesses (unresolved, in order of severity)

1. **The acceptance rule is shared between oracle and systems** through the
   `accepted` flag (and its text marker). Systems are graded on retaining the
   agent's trust judgment, not on making one. This is a deliberate scope cut
   (DECISIONS.md #5) but it means Kalends v1 does not evaluate trust
   *inference* at all.
2. **Closed value vocabulary + exact-match scoring** favors any system that
   stores strings verbatim; there is no partial credit and no semantic
   equivalence. Fine for architecture comparison, wrong for NL systems — the
   planned LLM-answerer track will need graded scoring.
3. **Question grammar kinship** (see §6).
4. **The oracle's freshness semantics** (strict `as_of` ordering) is one
   defensible belief-revision rule among several; results are conditional on
   it. Making the rule an experimental axis is queued.
5. **Single-value beliefs**: no uncertainty representation. The
   corroboration dimension is a first step; calibration metrics are not yet
   meaningful without confidence outputs (only `confidence` pass-through
   exists today).
