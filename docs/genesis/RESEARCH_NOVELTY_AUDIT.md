# Genesis research novelty audit

**Source check: 20 October 2026.** This is a critical comparison of public primary
sources, not a systematic review or an independent replication. New Genesis
empirical claims belong in `RESEARCH_PAPER.md` and `EXPERIMENTAL_VALIDITY.md` after
the new experiments execute. A feature being useful does not establish novelty.

## Bibliographic identity and evidence status

| Work | Checked identity/date | Evidence class and reading scope |
|---|---|---|
| Generative Agents | Park et al.; [2304.03442](https://arxiv.org/abs/2304.03442), first submitted 7 April 2023; [full text](https://arxiv.org/html/2304.03442) identifies UIST 2023 | Published empirical paper; architecture, structured sandbox §5.1, evaluation/ablations, errors read. |
| AgentSociety | Piao et al.; [2502.08691](https://arxiv.org/abs/2502.08691), first 12 February 2025, current record revised 10 April 2026 | [Public full text](https://arxiv.org/html/2502.08691), environment/economy, engine, experiment toolbox and evaluations; treat inspected arXiv version as preprint unless citing a separately verified venue. |
| AgentSociety 2 | Piao et al.; [2607.11895](https://arxiv.org/abs/2607.11895) | [Full text](https://arxiv.org/html/2607.11895) and [official repository](https://github.com/tsinghua-fib-lab/AgentSociety). Record displays v1 11 June 2026, v2 15 July, while the HTML manuscript date says 24 August. Preserve this metadata discrepancy; do not infer a precise priority date from its identifier alone. |
| STATE-Bench | Microsoft; [announcement](https://opensource.microsoft.com/blog/2026/05/19/introducing-state-bench-a-benchmark-for-ai-agent-memory/), 19 May 2026; [repository](https://github.com/microsoft/STATE-Bench) | Official benchmark/release documentation; not an independent product-reliability certification. |
| CPB | Li et al.; [2609.30813](https://arxiv.org/abs/2609.30813), 25 September 2026 | Actual paper title: *A Benchmark and Diagnostic Study of Epistemic Admission in Shared Agent Memory*. [Methods/limitations](https://arxiv.org/html/2609.30813v1); CPB is its benchmark name. Preprint. |
| CivWorldBench | Li et al.; [2610.16450](https://arxiv.org/abs/2610.16450), 12 October 2026 | [Methods/appendices](https://arxiv.org/html/2610.16450v1). Preprint; controlled simulator experiments, not validation of human societies. |
| τ-bench | Yao et al.; [2406.12045](https://arxiv.org/abs/2406.12045), 17 June 2024 | [Task formulation, execution and database-state scoring](https://arxiv.org/html/2406.12045). Original benchmark paper. |
| Selective classification | Geifman and El-Yaniv; [1705.08500](https://arxiv.org/abs/1705.08500), 23 May 2017, revised 1 June | [Method](https://arxiv.org/html/1705.08500); prediction rejection under stated assumptions, not a guarantee for endogenous multi-agent decision processes. |
| MemoryArena | He et al.; [2602.16313](https://arxiv.org/abs/2602.16313), 18 February 2026, revised 17 September; record labels ICML 2026 | [v2 methods §3–4 and appendix C.3](https://arxiv.org/html/2602.16313v2); task loops, memory baselines and approximate-oracle analysis. |
| LongMemEval-V2 | Wu et al.; [2605.12493](https://arxiv.org/abs/2605.12493), 12 May 2026 | [Full text and appendix E](https://arxiv.org/html/2605.12493v1); preprint marked work in progress. |
| From Agent Traces to Trust | Wang et al.; [2606.04990](https://arxiv.org/abs/2606.04990), 3 June 2026, revised 15 October | [v6 taxonomy and memory/evaluation sections](https://arxiv.org/html/2606.04990v6); survey, not a new empirical outcome benchmark. |

**Name collisions matter.** [2605.26203](https://arxiv.org/abs/2605.26203) is a
different *AgentSociety* about incentivized decentralized collaboration; it is
not the Piao simulator. MemoryArena [2602.16313](https://arxiv.org/abs/2602.16313)
is distinct from MemArena [2608.02613](https://arxiv.org/abs/2608.02613). Neither
should inherit the other's methods through a similar name.

## Method comparison matrix

Descriptions summarize inspected work; “not the target” avoids claiming an
unimplemented feature merely because it was not prominent in a paper.

| Work | Question / environment | Interventions and observable truth | Memory assumption | Metrics / baselines | Strongest supported finding and constraint on Kalends |
|---|---|---|---|---|---|
| Generative Agents | Believable behavior; 25-agent town | User changes and agent interactions; structured sandbox | Natural-language stream, retrieval, reflection, planning | Human believability rankings; component ablations and human-written responses | Components improve rated believability; errors remain. Town memory, natural-language participation and emergent diffusion already exist. |
| AgentSociety | Social mechanisms at scale; urban/social/economic simulator | Policy/shock experiments, surveys/interviews; environment constraints and trajectories | LLM-driven cognition and stream memory | Infrastructure evaluation and comparisons with selected empirical social patterns | Demonstrates large-scale experiments. A constrained objective environment and economy alongside LLM agents are prior art; selected pattern agreement is not general behavioral validity. |
| AgentSociety 2 | Research workflow plus simulated participants | Configurable environments, experimental procedures and inspectable artifacts | Skill/workspace-based agents and context management | Platform comparisons and seven illustrative studies | Integrates scientist orchestration with executable social experiments. Kalends cannot claim to originate auditable social experimentation or reusable environment tools. |
| STATE-Bench | Whether experience improves enterprise tasks | Task-local tools/databases; final-state assertions, additional judging | Pluggable memory/learning retrieval | Completion, repeated-run reliability, interaction quality, cost; no-memory/bring-your-own systems | Downstream memory-to-action evaluation is already explicit. Single final assertions need not capture all social/economic externalities. |
| CPB | Shared-memory admission under correlated claims | Fixed feed lineage; Static rule labels, Live write/retrieval/consumer logs | Shared store, writer declarations and admission policies | Admission, exposure, adoption, coverage; private/share-all, votes, lineage collapse, source gate, judges | Repetition and paraphrase can defeat admission. Static rewards encode a specified rule; Live generated derivations/declarations and LLM graders limit exact lineage claims. |
| CivWorldBench | Forecasting, hidden-state inference, intervention prediction | Saved engine states, paired edit/control/placebo rollouts, scoped observations | Observation histories supplied to predictors; memory architecture not principal axis | Forecast/effect metrics, references and assisted plans | Association skill need not transfer to interventions. Paired sandboxes and computable hidden truth already exist; reload/RNG divergence requires controls. |
| τ-bench | Reliable tool/user interaction; retail/airline | Deterministic database APIs, stochastic user dialogue; goal-state comparison | Agent context/tool loop | Task success and pass^k; model and prompting constructs | Correct-looking dialogue is insufficient for stateful task completion. State verification is established; the completeness of a goal specification remains a design choice. |
| Selective classification | Trade prediction error against accepted coverage | Held-out prediction tasks; reject option | Fixed predictor plus selector | Risk–coverage and risk control against base classifier | Abstention trades service for error reduction. Dynamic verification alters information, resources and future opportunity counts, so Genesis does not inherit static guarantees. |
| MemoryArena | Useful memory over interdependent multi-session tasks; shopping, travel, search, reasoning | Action feedback and task constraints; approximate oracle injects earlier golden outcomes/workflows | Long context, external memory and RAG | Task/subtask success, progress and latency; MemGPT, Mem0, BM25, embedding and graph retrieval | External memory is not uniformly beneficial; approximate-oracle memory still leaves low task success. Knowing/remembering versus successful use is direct prior art. |
| LongMemEval-V2 | Environment experience: state, workflows and recurring errors in web tasks | Precollected trajectories and curated questions; no online action feedback during evaluation | Compact evidence returned to a fixed reader | QA accuracy/latency; AgentRunbook-R/C, RAG and coding-agent baselines | Evidence gathering can improve recall at latency cost. It deliberately isolates memory quality rather than measuring end-to-end executed task success. |

Related primary sources sharpen the boundary: [MemoryArena](https://memoryarena.github.io/)
evaluates interdependent memory-guided agentic tasks;
[LongMemEval-V2](https://xiaowu0162.github.io/longmemeval-v2/) evaluates environment
experience through bounded evidence for a fixed reader; and the
[provenance survey](https://arxiv.org/html/2606.04990v6) organizes evidence,
memory lineage, execution tracing, audit, and recovery. None supports a claim
that memory evaluation or provenance graphs began here.

MemoryArena's approximate-oracle experiment is especially relevant to the
proposed local-memory/action gap: earlier correct outcomes do not guarantee
successful later execution. Its oracle is explicitly approximate, so it does not
prove memory is perfect or isolate every reasoning failure. A Genesis finding
must identify a narrower, controlled information/resource mechanism and measure
its executed effect; the broad gap itself is not an originality claim.

## Corrections to tempting comparisons

Generative Agents already grounds language in a structured sandbox (§5.1).
AgentSociety explicitly argues that environmental operational constraints are
needed to resist model hallucination. “Other systems let an LLM define reality”
is therefore an inaccurate blanket distinction. The narrower Kalends choice is
to make a small, explicit transition model and its information/economic tests
the evaluation authority, with language proposals constrained by a validator.

CPB is the nearest source-correlation comparison: deduplication versus coverage
is not an unexplored discovery. Its limitations identify a useful test boundary:
correction and recovery must be measured as actual consequences, not inferred
from a provenance drawing. CivWorldBench already measures intervention effects;
the distinction must come from a well-isolated question about memory access,
resource allocation, correction costs, or executed utility, not the existence
of a branch button.

AgentSociety 2's broad illustrative successes should not be read as a guarantee
that simulated participants generalize to humans. Its research environment also
retains human judgment over constructs and claims. Kalends' deterministic agents
make internal checks easier while narrowing behavioral realism. These are
different validity tradeoffs, not evidence that one simulator is universally
better.

## Causality and outcome verification

Use four labels consistently: **earlier event**, **recorded dependency**,
**agent-accessible evidence**, and **tested intervention effect**. A causal
claim is conditional on the coded world, intervention definition, paired
exogenous randomness and chosen outcome. A parent edge alone establishes none
of causal necessity, sufficiency, minimality, or generalization to real people.
The structural-model literature formalizes actual causation with explicit
counterfactual conditions; even a successful deletion test is only the test
performed, not a full implementation of every causation definition.
[Halpern and Pearl](https://arxiv.org/pdf/1301.2275)

Likewise distinguish memory fidelity, world-belief accuracy, intended action,
executed quantity, and utility. A filled purchase and an unfilled reservation
are different outcomes. Cash, delivered goods, unused stock and penalties must
reconcile with the ledger; an outcome weight must not count the same cash flow
twice. Static risk–coverage remains useful terminology, but report actual
denominators, verification cost/delay, and zero-action worlds. A smaller error
fraction can coexist with worse utility and less useful service.

## Defensible claim ladder and fresh-study boundary

| Claim | Status / evidence required |
|---|---|
| Persistent agents, private observations, source graphs, economic incentives, interventions, histories | Established techniques; no invention claim. |
| A small local playable world combining validated player actions, honest provenance, bounded transmission and outcome accounting | Integration contribution if the acceptance tests execute; distinguish prototype from hosted platform. |
| Accurate local retention fails to guarantee useful collective outcomes | Broad phenomenon has extensive prior support; a reproducible controlled example is useful, not automatically novel. |
| Lineage improves real utility under specified scarcity/correction conditions | Open empirical hypothesis. Require sender-count and verification-only controls, matched resource/access budgets, utility sensitivity, and paired intervals. |
| A cost/boundary/resource interaction that reverses a mechanism's outcome ranking | Potential focused finding if frozen fresh experiments isolate the interaction and survive independent scenario replication. |
| General human-society realism, broad research superiority, publication readiness | Unestablished. |

Genesis reserves development seeds **20000–20009** and fresh held-out seeds
**50000–50029**, never the old reported seeds. Freeze comparisons, metric
definitions, utility weights, resource/order controls and stopping rules before
held-out inspection. Separate oracle/operator interventions from equally costly
autonomous checks. Evaluate bounded recall **and transmission**, not a capped
answerer with an unlimited gossip oracle. Treat any post-result metric change
as exploratory and require another untouched confirmatory set.

No Genesis effect estimate is asserted in this audit. An especially useful next
test compares lineage, sender counting and verification-only policies at matched
coverage under both fixed-total and per-capita supplies, with seeded allocation
order, historical source preconditions, and genuine delayed corrections. A null
or adverse result is a valid outcome.
