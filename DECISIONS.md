# DECISIONS

Format per entry: decision · alternatives · reason · confidence · what would change it.

## 1. Python, stdlib only, zero dependencies
- **Alternatives:** TypeScript; Python + numpy/pydantic/an embedding model.
- **Reason:** the research substrate must be runnable anywhere, forever, with
  `python3 -m kalends`. Determinism is easier to guarantee with no third-party
  code, and nothing in v0 needs performance.
- **Confidence:** high.
- **Would change it:** scaling to hundreds of agents / real embedding models
  (then: keep the core stdlib, add optional extras).

## 2. No LLM anywhere in the v0 loop
- **Alternatives:** LLM-driven agent behavior (Smallville-style); LLM answerers
  over each memory substrate.
- **Reason:** deterministic seeded policies are what make *exact* epistemic
  ground truth computable — the entire benchmark rests on it. The LLM has two
  designated future slots that don't disturb this: (a) a behavior policy that
  *proposes* the same validated event types, (b) an answerer inside a
  `MemorySystem`. Neither can touch canonical state.
- **Confidence:** high for v0; the v1 experiment "does an LLM answerer change
  the substrate ranking?" is explicitly queued.
- **Would change it:** nothing for v0; v1 adds LLMs behind the interfaces.

## 3. Beliefs are proposition-valued: (subject, predicate) → value
- **Alternatives:** free-text beliefs; full triples with temporal qualifiers;
  probability distributions over values.
- **Reason:** a small closed proposition vocabulary makes scoring exact and the
  oracle trivially auditable. Distributions and free text reintroduce judgment
  calls (or LLM judges) into evaluation — the thing we're avoiding.
- **Confidence:** medium-high. This is the biggest simplification in the system.
- **Would change it:** evidence that memory architectures only differentiate on
  richer belief content (then extend values, keep the oracle exact).

## 4. Hearsay acceptance rule: trust ≥ 0.3 AND strictly fresher `as_of`
- **Alternatives:** always accept latest tell; Bayesian-ish confidence pooling;
  majority voting over sources.
- **Reason:** the rule must be simple enough that "normative belief" is
  unambiguous. Freshness comparison uses the *origination* tick (`as_of`,
  carried through the provenance chain), so a stale echo arriving late cannot
  clobber newer knowledge — this single rule generates most of the interesting
  benchmark cases. Strict `>` also prevents gossip ping-pong flip-flopping.
- **Confidence:** medium. It's one point in a large design space of belief
  revision rules; the point is that it's *fixed and computable*, not that it's
  cognitively right.
- **Would change it:** making the acceptance rule itself an experimental
  variable (compare memory systems under different revision norms).

## 5. Memory systems receive the `accepted` trust judgment as input
- **Alternatives:** make memories re-derive trust from raw exposure.
- **Reason:** separates concerns: trust judgment belongs to the *agent* at
  experience time; what's under test is **retention, supersession, retrieval,
  and attribution**. Otherwise every memory result confounds with trust
  modeling.
- **Confidence:** high for the stated question; revisit if trust inference
  itself becomes the research target.

## 6. Vector memory = hashed bag-of-words cosine, not real embeddings
- **Alternatives:** call an embedding API; ship a small local model.
- **Reason:** deterministic, offline, dependency-free, and it faithfully
  reproduces the *architectural* failure modes of RAG memory (no time model, no
  supersession, similarity traps) — which is what the baseline exists to show.
  Synonymy is handled by putting aliases into some renderings rather than by
  semantic vectors.
- **Confidence:** medium. Results labeled "vector" mean "similarity-retrieval
  architecture," not "state-of-the-art embeddings."
- **Would change it:** before publishing numbers, rerun with a real embedding
  model as an optional extra to confirm the failure profile persists.

## 7. StructuredMemory is a by-construction ceiling — and we say so
- **Alternatives:** artificially degrade it (capacity limits, parse noise) to
  make the comparison look more "fair".
- **Reason:** it stores the same fields the oracle does, so ~1.00 on structured
  queries is expected and is reported as the benchmark's solvability ceiling,
  not a discovery. Its honest weakness (schema brittleness on alias phrasings,
  0.33) is real and measured. Manufacturing extra weaknesses would be fake
  results — explicitly forbidden by the project brief.
- **Confidence:** high.
- **Would change it:** giving structured memory raw text to parse (a real
  parser under test) would make it a genuine system rather than a ceiling.

## 8. Alias questions do not inherit stale/supersession dimension tags
- **Alternatives:** inherit all dims from the canonical question.
- **Reason:** first benchmark run showed the confound: structured memory
  "failed staleness" when it was actually failing alias *retrieval*. Dimensions
  must measure one thing.
- **Confidence:** high (empirically driven).

## 9. Tick loop (48 hourly ticks), not discrete-event scheduling
- **Alternatives:** event-driven scheduler; adaptive resolution.
- **Reason:** at 14 agents × 48 ticks, simplicity wins. The ledger is already
  sparse (events only), so a scheduler swap later touches nothing downstream.
  Full analysis in TEMPORAL_RESOLUTION.md.
- **Confidence:** high for this scale.

## 10. Scoring against *normative belief*, never against world truth
- **Alternatives:** score answers against canonical reality.
- **Reason:** the central thesis. An agent who was never told the bakery was
  repaired *should* say "damaged"; a memory system that answers "repaired"
  would be leaking world truth it cannot have. Staleness relative to reality is
  reported as an oracle property (the `stale` dimension exists to check that
  systems preserve epistemically-correct-but-wrong beliefs).
- **Confidence:** high — this is the point of the project.

## 11. Distortion is value-substitution via a scenario map
- **Alternatives:** LLM-generated paraphrase drift; character-level noise.
- **Reason:** keeps the distorted value inside a closed vocabulary so ground
  truth remains exact ("A correctly believes the false rumor" is scoreable).
  The teller's *claimed* provenance chain still points at the true chain, so
  claimed-vs-actual mismatch exists in the data for future questions.
- **Confidence:** medium-high.

## 12. No git history was created
- **Reason:** the working rule for this session is to commit only when asked.
  Everything is plain files; run `git init && git add -A && git commit` to
  snapshot when you return.
