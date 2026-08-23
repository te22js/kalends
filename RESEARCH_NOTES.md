# RESEARCH_NOTES

Phase A output. Audit + related work. Written 2026-08-24.

## 0. Repository audit

The repository was **empty** at session start. There is no existing architecture,
no reusable components, and no technical debt. Everything described in the other
documents was built in this session, greenfield. (This also means nothing here
conflicts with the objective-reality / observation / belief separation — we got
to build it in from the first line.)

## 1. Related work that changes our design

### Generative agents (Park et al. 2023, "Smallville")
Memory stream + importance scoring + recursive reflection. Crucially, **the LLM
is the authority on world state** there: believability was the metric, not
epistemic correctness. Agents routinely know things they shouldn't. This is the
system we are defining ourselves against. What we take: the working /
episodic / reflection decomposition is a useful vocabulary. What we reject:
retrieval-by-similarity as the sole memory mechanism, and LLM-adjudicated
reality.

### Event sourcing (Fowler et al., long-established engineering practice)
Append-only event log + deterministic fold ("projection") into current state.
This is a solved engineering pattern and we adopt it wholesale as the canonical
reality layer. **Not a contribution — a foundation.** Replay determinism and
audit trails come for free.

### Epistemic logic / interpreted systems (Fagin, Halpern, Moses, Vardi)
"An agent's knowledge = what is consistent with its observations" is formalized
in *Reasoning About Knowledge* (1995). Our per-agent oracle is essentially a
computational interpreted system. The AGM belief-revision literature covers
supersession/contradiction formally. We do not need new theory; we need a
*runnable instantiation* that LLM-memory systems can be scored against.

### Rumor/information propagation (Daley–Kendall 1964, Maki–Thompson 1973)
Classic epidemiology-style rumor models give us the vocabulary
(ignorant/spreader/stifler) and a warning: propagation dynamics themselves are
well studied. Our contribution is not "rumors spread in a network" — it is
per-agent provenance-grounded evaluation of memory systems inside that spread.

### LLM-agent memory benchmarks (2024–2026)
The field has moved toward exactly our concerns, which is validation that the
problem is real, and pressure to differentiate:
- **LoCoMo**, **LongMemEval** — long-horizon conversational memory; LongMemEval
  has an explicit knowledge-update question type (fact changed in later session).
- **STALE** (arXiv 2605.06527) — "can agents know when their memories are no
  longer valid" — closest in spirit to our staleness dimension.
- **Supersede** (arXiv 2606.27472) — the "memory-update gap": agents failing to
  overwrite superseded facts.
- **Memora / FAMA metric** — penalizes reliance on superseded or deleted memory.
- **Belief Engine** (arXiv 2605.15343) — inspectable stance dynamics in
  multi-agent deliberation; notes that agents change beliefs without exposing
  *why* — the provenance gap we attack directly.
- Springer critical review (AI Review 2025) — validation is the central
  unsolved problem for generative social simulation; LLM agents raise
  "epistemic concerns in explanatory modeling."

**Key differentiation:** every benchmark above evaluates memory against a
*conversation transcript* or a *document stream*. None of them (as far as this
survey found) evaluates memory against a **simulated world with a computable
per-agent epistemic ground truth** — i.e. where "what the agent *should*
believe" is derived mechanically from an observation/communication log rather
than annotated by humans or an LLM judge. That is the gap Kalends-MemoryBench
occupies: ground truth is *generated*, arbitrarily scalable, and provably
consistent, and it distinguishes "wrong vs. world" from "wrong vs. what the
agent could know" — a distinction transcript benchmarks cannot make.

**⚠ Superseded by the second pass:** §4 below found MemArena, which partially
occupies this gap. The claim above stands only in its weakened form — see the
honest repositioning in §4.

## 2. Sorting the ideas honestly

**Already established (use, don't claim):**
- Event sourcing, deterministic replay, append-only ledgers.
- Epistemic-logic separation of truth/knowledge/belief.
- Rumor propagation dynamics.
- Memory-stream + retrieval agent architectures.
- Discrete-event vs. time-stepped simulation.

**Our potentially interesting contribution:**
1. A benchmark where per-agent epistemic ground truth (belief value, source,
   provenance chain, staleness, knowledge boundary) is **computed, not
   annotated** — enabling exact scoring of memory architectures.
2. Machine-checkable **provenance chains for hearsay** ("A heard from B who
   observed E8") as first-class benchmark targets, including *claimed* vs.
   *actual* provenance under distortion.
3. Scoring beliefs against the agent's *information horizon* rather than world
   truth — a stale belief can be the epistemically correct answer.

**Sounds novel but probably is not:**
- "Adaptive temporal resolution" → largely discrete-event simulation + compute
  scheduling. See TEMPORAL_RESOLUTION.md for the full assessment.
- "Human-like memory hierarchy" — cognitive-architecture ideas (SOAR, ACT-R)
  predate us by decades. We use the decomposition as an interface, claim nothing
  about cognition.
- "NPCs with persistent beliefs" — many game-AI and BDI systems claim this;
  the defensible novelty is the *evaluation*, not the persistence.

**Questions requiring experiments (not argument):**
- Does structured memory actually beat vector memory on supersession, and by
  how much? Does vector memory beat structured on paraphrase/alias queries?
- Does hybrid dominate, or does it inherit the failure modes of its arbiter?
- How do error rates scale with population size, event density, and simulated
  duration?
- Does adding an LLM as the answerer over each memory substrate change the
  ranking of substrates? (v1 experiment; v0 is LLM-free by design.)

## 3. What this changed in the design
- Ground truth must be an explicit oracle object (`epistemic.py`), computed in
  the simulator, never inferred post hoc.
- Distortion must record both the true value and the transmitted value, so
  "agent correctly believes a false rumor" is scoreable.
- The benchmark question set must include *unknowable* questions (knowledge
  boundary) — the literature shows systems fail loudest there.
- Keep v0 free of LLM calls so results are deterministic and cheap; the LLM
  slot lives behind the `MemorySystem.answer()` interface for v1.

Sources:
- [STALE](https://arxiv.org/html/2605.06527v1) · [Supersede](https://arxiv.org/html/2606.27472v1) · [LongMemEval-style update QA overview](https://arxiv.org/html/2604.20006v1)
- [Belief Engine](https://arxiv.org/pdf/2605.15343) · [Validation critical review](https://link.springer.com/article/10.1007/s10462-025-11412-6)
- [ToM-agent](https://arxiv.org/html/2501.15355v1) · [Emergence World](https://arxiv.org/pdf/2606.08367)
- [VirtLab](https://arxiv.org/pdf/2508.04634) · [APS prototype simulation](https://arxiv.org/html/2605.27419v1) · [GEPOC hybrid time-update](https://arxiv.org/pdf/2510.20840)

---

## 4. Second literature pass (post-build, sharper questions)

Done after the system and first 30-seed results existed, per the brief:
for each close work — what do they evaluate, what does Kalends do differently,
is the difference meaningful, could they subsume us, what experiment would
distinguish.

### MemArena (arXiv 2608.02613) — THE closest work; changes our positioning
- **What they evaluate:** 50 persona-driven LLM agents over 15 simulated days;
  a world-event broadcaster routes events through a **visibility matrix**
  (controlled information asymmetry, provenance preserved); six dimensions
  incl. permission-aware access (≈ our knowledge boundary) and calibrated
  abstention. Ground truth is simulation-derived for 5/6 dimensions,
  **LLM-generated for factual QA**.
- **What Kalends does differently:** (1) fully deterministic LLM-free
  generative process — every label exact, replayable, free; (2) provenance
  chains as first-class *objects* with root signatures →
  **independent-source vs shared-ancestry accounting** (absent in MemArena);
  (3) normative-belief scoring against the agent's trust-gated information
  horizon (stale-but-correct ≠ error) rather than "did she change her mind"
  probes; (4) **counterfactual event-deletion** with context-keyed RNG (their
  single fixed world can't do this); (5) parameterized world *families* and
  scaling as experimental variables — their stated limitation is exactly the
  single-world design; (6) mechanism-level ablations (supersession/trust/
  provenance/router) rather than backend comparison only.
- **Meaningful?** Yes, but the story must change: Kalends is no longer "the
  first computed-ground-truth world"; it is **the deterministic epistemic
  *instrument*** — exact oracle, causal surgery, ancestry accounting —
  complementary to MemArena's realism-first design.
- **Could they subsume us?** Not currently (no counterfactuals, no ancestry
  accounting, LLM labels in one dimension, one world). But they are close
  enough that a paper must cite them prominently and compare directly.
- **Distinguishing experiment:** run their backends (Memobase/MemSearch-style)
  on Kalends families and show failure modes their LLM-labeled QA cannot
  isolate (e.g. shared-ancestry inflation, stale-vs-horizon separation).

### Ground Truth First (arXiv 2607.21962)
Longitudinal agent-memory evaluation; found a "tenure crossover" in
architecture rankings and argues for provenance-typed stores ("claims as
claims, not facts") — independent convergence on our claimed-origin design.
Transcript-longitudinal, not world-simulated; no oracle of the Kalends kind.
Cite as motivation for provenance typing.

### FANToM (arXiv 2310.15421) / Hi-ToM / Sotopia-ToM
Theory-of-mind QA under information asymmetry in conversations. Hi-ToM's
finding — models infer *current* beliefs but fail to retain *prior* belief
states — is our supersession dimension in ToM clothing. Difference: they
evaluate the *reasoner* (an LLM reading a transcript); Kalends evaluates the
*memory architecture* of an agent embedded in the world, with mechanical
ground truth and no reading comprehension confound. Complementary, not
subsuming; a Kalends language-interface track would meet them halfway.

### STALE / Supersede / Memora (2605.06527, 2606.27472, FAMA metric)
Staleness and the memory-update gap in conversational memory. They diagnose
and even train against supersession failures; none has world-grounded
provenance or horizon-relative correctness. Kalends' supersession family is
the world-grounded version of their probes — cite and align terminology.

### Knowledge editing (ROME/MEMIT line)
Edits model *weights*; unrelated mechanism, same epistemic goal (make new
facts stick, old ones die). Keep out of scope; one sentence in related work.

### Epistemic logic (Fagin/Halpern/Moses/Vardi), W3C PROV
Our oracle is a small computable interpreted system; our provenance is a
domain-specific PROV-like DAG. No novelty claims there — cite as foundations,
gain rigor by using their vocabulary (information set, run, view).

### Event-sourced simulation / DES
Foundation, not contribution (unchanged from first pass).

### Positioning after this pass (what we can defend)
1. **Exactness**: every label mechanical, replayable; no LLM judge anywhere.
2. **Epistemic-horizon scoring** (stale-but-epistemically-correct as a
   *positive* target) — still not found elsewhere in this form.
3. **Ancestry/independence accounting** as a benchmark dimension — not found
   elsewhere.
4. **Counterfactual event-surgery ground truth** — not found elsewhere in a
   memory benchmark.
5. World *families* + scaling + capacity as controlled variables.

What we must NOT claim: first simulated-world memory benchmark; first
visibility-controlled asymmetry; first provenance-aware memory store;
anything about human memory.

Sources (second pass): [MemArena](https://arxiv.org/html/2608.02613) ·
[Ground Truth First](https://arxiv.org/html/2607.21962v1) ·
[FANToM](https://arxiv.org/abs/2310.15421) ·
[Sotopia-ToM](https://arxiv.org/html/2605.02307) ·
[Hi-ToM](https://www.researchgate.net/publication/376402827_Hi-ToM_A_Benchmark_for_Evaluating_Higher-Order_Theory_of_Mind_Reasoning_in_Large_Language_Models) ·
[memory survey 2602.06052](https://arxiv.org/pdf/2602.06052) ·
[Momento](https://arxiv.org/pdf/2606.00832) · [AMemGym](https://arxiv.org/pdf/2603.01966)
