# Rebirth: skeptical research and novelty audit

Reviewed 21 October 2026. This is a targeted primary-source review, not a systematic survey. Read methodology is distinguished from product descriptions. The recent arXiv papers are treated as preprints; their reported findings have not been independently replicated here. Results belong in `RESEARCH_RESULTS.md`; this note does not convert implementation into a discovery.

## What the implementation can claim

Rebirth combines a deterministic economic world, bounded agent-accessible memory, authored disputes with state-dependent remedies, inspectable goals, grounded language proposals, and a player-facing presentation. These are integration choices. No component establishes a new general theory of cognition, narrative, persistent worlds, or temporal simulation.

Development profiling found candidate-world copying and repeated full-history hashing expensive as accepted history grows. `kalends_rebirth/immutable.py` seals historical events, shares their immutable bodies between isolated candidates, and keeps a copyable SHA-256 prefix. The representation preserves the old canonical ledger digest. Mutable current accounts, commitments, memories, plans and queues still require detached copies. This is an application of established persistence and incremental hashing, **not hierarchical causal time compression**.

## Relevant methods actually inspected

| Work | Method read and relevant boundary | Implication for Kalends |
|---|---|---|
| [Driscoll, Sarnak, Sleator and Tarjan, *Making Data Structures Persistent* (1989)](https://www.cs.cmu.edu/~sleator/papers/making-data-structures-persistent.pdf) | Section 2.3 describes node copying, versioned fields and update propagation; persistence preserves prior versions. Our copied list head plus shared sealed events is simpler and is not their algorithm. | Sharing unchanged historical structure is established prior art. Report application-level performance and isolation correctness, not a novel data structure. |
| [Python `hashlib`](https://docs.python.org/3/library/hashlib.html) | `update` accepts successive bytes; `copy` branches a hash state. The ledger hashes the exact legacy JSON byte stream, with a temporary closing bracket at read time. | The hash optimization is ordinary incremental computation. Randomized equivalence checks are needed because delimiters, Unicode and tuple/list export affect compatibility. |
| [Graham, *An Introduction to Utility Theory* (2013)](https://www.gameaipro.com/GameAIPro/GameAIPro_Chapter09_An_Introduction_to_Utility_Theory.pdf) | Response curves map needs to action scores; bucketed selection and inertia help avoid oscillation. These are practical game-AI techniques, not unrestricted reasoning. | Different goals, constraints and scored or rule-selected actions are not evidence of a new intelligence architecture. |
| [Mateas and Stern, *Structuring Content in the Façade Interactive Drama Architecture* (2005)](https://cdn.aaai.org/ojs/18722/18722-52-22361-1-10-20210928.pdf) | Beat goals and mix-ins support local reactions; a director selects beats using preconditions, priorities, effects and a desired tension trajectory. Background autonomous behaviors coexist with dramatic sequencing. | Authored opportunities, constrained direction and autonomous routines have strong precedent. Rebirth must show that actual accounts and commitments constrain its scenes. |
| [Riedl and Young, *Narrative Planning: Balancing Plot and Character* (2010)](https://faculty.cc.gatech.edu/~riedl/pubs/jair.pdf) | IPOCL searches action and intention structure; frames of commitment and motivating steps extend causal plan completeness. Its reader evaluation compares perceived intentions; the paper discusses computational cost and narrative-length confounding. | A short goal hierarchy is not an IPOCL planner. Story coherence and perceived intentionality require their own evaluation; unit tests cannot establish believability. |
| [Park et al., *Generative Agents* (2023)](https://arxiv.org/html/2304.03442) | Retrieval combines recency, importance and relevance; reflection and plans condition behavior. Structured environmental state grounds actions. Controlled interviews/ablations and a two-day, 25-agent demonstration evaluate different properties. | Memory, reflection, plans and a social town are established. A zero-provider deterministic fallback cannot inherit the paper's language-model results. |
| [*MemoryArena* (2026)](https://arxiv.org/html/2602.16313v2) | Interdependent multi-session tasks require prior outcomes for later actions. Appendix C.3 gives an approximate oracle prior-outcome/workflow condition; better memory does not automatically solve acting. | Memory-to-action evaluation is already explicit prior art. Test actual deliveries, settlements and access changes, not only recalled labels. |
| [*Agent Memory: Characterization and System Implications of Stateful Long-Horizon Workloads* (2026)](https://arxiv.org/html/2606.06448) | Separates ingestion, construction, storage, retrieval and generation; compares local/remote construction and phase-aware timings. Construction-versus-serving and freshness tradeoffs depend on workload. | Measure sealing/append cost separately from candidate-copy and read cost. A read-path gain alone is not a total simulation speedup. |
| [Huang et al., *Programmable World Model* (September 2026; v2 October 2026)](https://arxiv.org/html/2609.10540) | Sections 4.1–4.3 separate canonical engine state, executable rules and action validation from a generative renderer through deterministic projected 3D-box controls. Persistent identity and nonvisual inventory/relations belong to the engine. | Authoritative state plus generated presentation is already explicit recent prior art. Kalends' social-information boundaries differ in implementation; that alone establishes no novelty or superiority. |

The preserved [Pompeii novelty audit](../pompeii/NOVELTY_AUDIT.md) covers discrete-event simulation, multiscale agent modeling, event sourcing and validation. This sprint reuses that exact scheduler. Rendering fast-forward, jumping between scheduled events, and approximate causal compression remain distinct concepts. No new dependency-aware coarse simulator has been implemented here.

## Consequential empirical question

**Can immutable historical sharing and incremental hashing reduce the latency of an actual isolated player transaction after long world histories, while preserving every declared player-relevant outcome?**

Use the actual new world and session implementation with a single optimization flag. Match seeds, actions, horizons and legal conversation-density conditions. Compare exact canonical event contents and hash; accounts, goods, commitments and settlements; multidimensional relationships and access; agent memories and information provenance; plans and pending tasks. Reject any speedup accompanied by a semantic mismatch. Preserve a separate bulk-advance measurement to expose the extra write cost. Fresh heldout registration must precede heldout execution and pin source bytes.

Population remains six authored NPCs. This cannot answer population scaling, arbitrary city-size simulation, independent human enjoyment, or general social realism. New authored intrigue increases coverage, not statistical independence between thousands of events. Uncertainty must use matched seeds as units. A flat or negative result is valid evidence.

## Claims to refuse

- “Breakthrough time compression” based on faster copies, rendering or a strong exact event scheduler.
- “Emergent intelligence” inferred from authored routes, dialogue fluency, or the existence of a memory buffer.
- “Historically accurate society” inferred from archaeological building anchors and fictional transactions.
- “Players will return” inferred from developer walkthroughs or test pass counts.
- “Defensible platform” inferred from extensible Python modules and auditable logs.

The useful contribution, if validated, is a reproducible working system and a narrow engineering result with explicit fidelity boundaries. A scientific novelty claim would require a materially new method, stronger comparisons and independent replication.
