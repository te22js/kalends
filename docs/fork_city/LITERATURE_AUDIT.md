# Focused literature and novelty audit

Audit date: **18 October 2026**. Primary sources were opened directly, including
the official Microsoft repository/blog, author project pages, and the arXiv
abstract/full-text records below. This is a scope and provenance audit, not a
systematic review or independent replication of the papers' numerical results.
The comparisons with Kalends are our interpretation of the inspected methods.

## Identity checks

All eight requested works were located. None of the supplied arXiv identifiers
was unavailable or unrelated. Two requested names are method/benchmark names
rather than the paper's title.

| Requested work | Verified primary record | Identity/status |
|---|---|---|
| Microsoft STATE-Bench (2026) | [Official repository](https://github.com/microsoft/STATE-Bench), [19 May announcement](https://opensource.microsoft.com/blog/2026/05/19/introducing-state-bench-a-benchmark-for-ai-agent-memory/) | Stateful Task Agent Evaluation Benchmark; verified Microsoft project. |
| MemoryArena | [Author project](https://memoryarena.github.io/), [arXiv:2602.16313](https://arxiv.org/abs/2602.16313) | *MemoryArena: Benchmarking Agent Memory in Interdependent Multi-Session Agentic Tasks*. |
| LongMemEval-V2 | [Author project](https://xiaowu0162.github.io/longmemeval-v2/), [arXiv:2605.12493](https://arxiv.org/abs/2605.12493) | *LongMemEval-V2: Evaluating Long-Term Agent Memory Toward Experienced Colleagues*. |
| Correlated Promotion Benchmark, 2609.30813 | [Paper](https://arxiv.org/abs/2609.30813), [full text](https://arxiv.org/html/2609.30813v1) | Actual title: *A Benchmark and Diagnostic Study of Epistemic Admission in Shared Agent Memory*. CPB is the benchmark introduced within it. |
| COUNTERMEM, 2609.31874 | [Paper](https://arxiv.org/abs/2609.31874), [full text](https://arxiv.org/html/2609.31874v1) | *COUNTERMEM: World-Model Verified Counter-Factual Memory for Language Agents*; full text styles it CounterMem. |
| FAME, 2609.39473 | [Paper](https://arxiv.org/abs/2609.39473), [full text](https://arxiv.org/html/2609.39473v1) | Actual title: *Beyond the Shadows of Plato's Cave: Evaluating False Memory in Autonomous Agents via Counterfactual Reasoning*. FAME is the framework. |
| CivWorldBench, 2610.16450 | [Paper](https://arxiv.org/abs/2610.16450), [full text](https://arxiv.org/html/2610.16450v1) | *CivWorldBench: Evaluating Language World Models in Structured Multi-Agent Sandbox Worlds*. |
| From Agent Traces to Trust, 2606.04990 | [Paper](https://arxiv.org/abs/2606.04990), [full text](https://arxiv.org/html/2606.04990v1) | Abstract record includes *A Survey of Evidence Tracing and Execution Provenance in LLM Agents*; full-text heading omits *A Survey of*. Same relevant work. |

**Name collision in historical project notes:** `RESEARCH_NOTES.md` discusses
**MemArena**, [arXiv:2608.02613](https://arxiv.org/abs/2608.02613), an ego-centric
personal-memory benchmark with a 50-agent, 15-day simulated conversational world.
That is a real, separate work. It is not the requested **MemoryArena**. The
historical description must not be copied into a citation to 2602.16313.

## What overlaps and what remains distinguishable

### STATE-Bench

STATE-Bench tests memory/learning in stateful enterprise workflows across travel,
support, and shopping. Its 450 tasks use tools and task-local databases, with
final-state assertions and additional process/interaction judging. Its learning
track adds training trajectories and a retrieval hook. Thus memory improving
consequential action, procedural correctness, reliability, and cost is already
an explicit benchmark objective. [Official source](https://github.com/microsoft/STATE-Bench)

Kalends can offer a smaller, entirely executable environment with exact private
information histories and controlled message interventions. A claim about a
particular source-correlation mechanism may complement STATE-Bench; a claim to
invent downstream memory evaluation cannot.

### MemoryArena

MemoryArena evaluates interdependent multi-session tasks in a
Memory-Agent-Environment loop: earlier actions and feedback must support later
task completion. Its domains include web navigation, preference-constrained
planning, progressive search, and formal reasoning. This directly establishes
the difference between recalling information and using it successfully.
[Author project](https://memoryarena.github.io/)

Kalends' potential distinction is exact control over who received which claim,
when it changed, and which relays share a root, while measuring resulting
decisions. Roman presentation and persistent memory alone add no research
novelty over this memory/action loop.

### LongMemEval-V2

LME-V2 uses 451 curated questions over long multimodal web-agent histories. It
tests static recall, dynamic state tracking, workflow knowledge, environment
gotchas, and premise awareness. Its insertion/query interface returns bounded
evidence for a fixed reader; evaluation reports answer accuracy and query
latency. AgentRunbook baselines combine raw states, transitions, and reusable
procedure information. [Author project](https://xiaowu0162.github.io/longmemeval-v2/)

Kalends' endogenous decisions and interventions address a different evaluation
surface. Dynamic state tracking, reusable experience, structured transitions,
and memory latency are established concerns. Synthetic exact-match scoring is
also substantially easier than this multimodal history task.

### Correlated Promotion Benchmark (CPB)

CPB is the closest overlap for repeated hearsay and gating. Static episodes
score a specified admission rule after lineage collapse; Live teams write and
retrieve a shared store, with downstream consumer probes. It studies coverage
versus false admission, source declarations, paraphrases, and write-back. The
paper notes that scenario feed lineage is fixed, generated derivation relies
on declarations, Live grading uses LLMs, and correction remains untested by the
compared policies. [Methods and limitations](https://arxiv.org/html/2609.30813v1)

Consequently, neither lineage collapse nor its risk/coverage tradeoff is a new
Kalends discovery. A useful extension would isolate **correction recovery and
economic decision regret after correlated exposure**, with exact outcomes and
paired interventions. This is a proposed boundary, not an established result.

### COUNTERMEM

COUNTERMEM tests local alternative actions from copied/reset decision states
using executable checks such as tests, proof checkers, and solvers. Verified
improvements become persistent records with action contrasts and applicability
conditions. A learned selector chooses records or skips memory, balancing
success and interaction cost; memory and selector are frozen for held-out
evaluation. [Method](https://arxiv.org/html/2609.31874v1)

Kalends' branching UI inspects a world's history rather than learning a
cross-task memory-use policy. Verified alternate outcomes and memory-use gating
already have direct prior art. Merely implementing forks does not establish a
new counterfactual-memory method.

### FAME

FAME uses counterfactual queries to diagnose false memory through latent concept
drift, approximated by model hidden states before answer generation. It studies
spurious correlations, shifts, and knowledge conflict, with formal assumptions
and experiments in reasoning/code settings.
[Framework](https://arxiv.org/html/2609.39473v1)

Kalends evaluates explicit external memory and observable coded actions,
without hidden-state access. Its traceable false rumors are a controlled
external-memory failure mechanism; they are not equivalent to FAME's latent
false-memory measure. Avoid claiming that an external false proposition proves
the same internal phenomenon.

### CivWorldBench

CivWorldBench uses recorded multi-agent engine states, controlled observations,
and paired intervention rollouts to evaluate association forecasts, hidden-state
inference, and intervention prediction. It also tests decision relevance. Its
appendices distinguish replay checks from matched randomness after edits and
report placebo/reseed diagnostics and world-level uncertainty.
[Methods, Appendices D/G](https://arxiv.org/html/2610.16450v1)

This directly rules out first claims for computable sandbox ground truth,
partial observations, paired worlds, or decision-relevant causal evaluation.
Kalends can instead isolate memory retention/routing and lineage as experimental
variables. Its simpler deterministic rules make stronger internal checks
possible, with a corresponding loss of realism and breadth.

### From Agent Traces to Trust

This is a survey and taxonomy, covering evidence, tool calls, memory lineage,
execution graphs, runtime enforcement, audit, and recovery. It organizes
process-level accountability and provenance evaluation rather than introducing
one comparable simulator or experimental baseline.
[Survey](https://arxiv.org/html/2606.04990v1)

Kalends implements a concrete restricted instance of these established ideas.
An evidence edge records declared support/dependency; it does not by itself
prove that removing the evidence changes an outcome. Label structural ancestry
and verified intervention effects separately in the interface and report.

## Repository baseline relevant to these claims

Inspected baseline: commit `8040b22b2646f18fa03108d6952cf1eab646ea65`.
These observations describe the pre-sprint modules, not promises about the new
extension.

- `simulation.py` already separates event projection, visibility, per-agent
  exposures, and memory ingestion. The existing rumor scenario has 14 agents,
  location schedules, distorted gossip, private events, and late corrections.
- `epistemic.py` supplies an explicit trust/freshness rule. Its oracle is
  normative **under that rule**, not a general human or Bayesian belief model.
- `counterfactual.py` already deletes one incident and reruns the scenario,
  comparing final beliefs. It does not restore an arbitrary interactive
  snapshot or evaluate trade/commitment consequences.
- `WorldState` initially holds locations, proposition facts, and trust. There
  is no baseline inventory, financial loss, or commitment model to claim as
  pre-existing behavior.
- `StructuredMemory` receives proposition fields, acceptance flags, and root
  metadata resembling the oracle. It is a schema-assisted ceiling on keyed
  queries; text retrieval has a different representation and top-k budget.
  Existing `METHODOLOGY_AUDIT.md` already documents this limitation.
- Baseline random gossip/movement keys are stable context keys, but alias
  rendering also uses sequential event IDs. Deletion can change later wording
  without changing underlying information. A downstream memory-policy
  experiment must control this channel before claiming fully paired evidence.
- Root identity is a model-defined provenance signature. Different witnesses
  to one event are not thereby proven statistically independent.

## Defensible research question and claim boundaries

**Question:** Under a fixed decision policy and declared asymmetric costs, when
does collapsing duplicated evidence roots improve decision regret at comparable
coverage, and how does a delivered correction change recovery after an earlier
false claim?

**Established components:** event sourcing, deterministic replay, exact-key
storage, retrieval, provenance graphs, source deduplication, local observations,
state forks, abstention/verification gates, and memory-to-action evaluation.

**Useful integration:** an inspectable local world connecting private evidence,
memory responses, decisions, consequences, and editable histories. A working
integration is an engineering contribution even if it establishes no new
scientific finding.

**Potential experimental contribution:** a reproducible, well-isolated result
on lineage, recovery, or routing failure in this simulator, supported by new
paired runs. No first-in-field or publication-worthiness claim follows from
this audit. A result conditional on supplied schema and a hand-coded oracle
must remain labeled accordingly.

For a meaningful comparison, keep the observation stream, policy, decision
opportunities, costs, and retrieval budgets explicit. Separate changes to
memory from changes to gating; sweep thresholds instead of selecting a single
favorable point. Report coverage, false abstention, verification cost, and
regret together. Bootstrap paired **world/seed aggregates**, not individual
correlated decisions; reserve held-out seeds before examining results. Include
identity intervention, duplicate-root, and correction metamorphic checks.

The strongest next generalization test is a matched representation/budget track
with an independently authored scenario and a different correction/cost regime.
Real embeddings or a fixed language-model reader would then test whether a
finding survives the present lexical retrieval and template limitations.
