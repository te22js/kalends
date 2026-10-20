# Lived Time and epistemic worlds: novelty audit

**Primary-source check, 21 October 2026.** This is a targeted methods review,
not a systematic review or independent replication. No Pompeii speedup, fidelity
advantage, human-learning benefit or new algorithm is established by this file.
New empirical claims must use the completed frozen experiment. Historical
Genesis results remain separate.

## The central boundary

Advancing a simulation directly to the next scheduled event is established
discrete-event simulation (DES). Predicting intervals in which nothing relevant
can change, precomputing invariant effects, temporal abstraction and varying
resolution all have substantial prior art. A LIVE/COMPRESS/MONTAGE/SKIP interface
can be good product design without constituting a new simulation algorithm.
Rendered fast-forward, shorter narration and genuine reduced computation are
different operations.

The smallest credible contribution is **an explicit supported-class temporal
contract for a persistent society, with audited private-information, obligation,
relationship and distribution fidelity at measured lower compute cost**. Even
that is initially an engineering/benchmark contribution. A new adaptive rule
would need an isolated improvement over a competent DES implementation, not
only over an intentionally wasteful tick loop.

## Structured comparison of actual methods

| Source / status | Question and mechanism | Evaluation / findings and limits | Consequence for Kalends |
|---|---|---|---|
| **Fujimoto, 1990**, CACM tutorial [R1] | Conservative/optimistic parallel DES; lookahead bounds when incoming events can matter. Event invariance enables precomputation; lazy cancellation/reevaluation exploits it dynamically. | Queuing/synthetic workloads; speedup depends on lookahead and synchronization. Preemption or near-zero event delays can destroy the advantage. | “Predict what cannot change, skip safely” is not new. A causal dependency label alone does not supply the invariant required for safe skipping. |
| **SimPy scheduling**, official implementation docs [R2] | Heap queue ordered by timestamp and monotonic event ID; step/run/peek advance event time deterministically. | Documentation/source semantics, not a comparative research paper. Same-time order is explicit and can affect outcomes. | Next-event clocks and stable ties are an ordinary baseline. Preserve allocation tie semantics and disclose any change. |
| **SAMAS, Chaturvedi et al., 2004**, ICCS [R3] | Agent processes at different time resolutions; sample/synchronize and randomized gossip maintain shared information. | Full methods/results test communication rounds under send/receive limits, on fully connected overlays of 128/256/512 agents. Architecture remains preliminary; this is not an exact private-history fidelity theorem. | Multi-resolution agent societies and synchronization predate this project. Distinguish global synchronization from deliberately private, imperfect beliefs. |
| **Sutton, Precup & Singh, 1999**, Artificial Intelligence [R4] | Options: temporally extended closed-loop actions in an MDP/SMDP framework, including interruption and intra-option learning. | Formal planning/learning constructions and example tasks; assumes a specified stochastic decision model. | Hierarchical actions and duration-aware planning are prior art. A long action still needs correct internal events and interruption conditions. |
| **Fowler, 2005**, original technical pattern [R5] | Event sourcing reconstructs state from events; snapshots, retroactive events and parallel models support replay. | Practitioner design, not empirical human-society validation. External side effects require special replay handling. | Logs, save/load, snapshots and alternative histories are established patterns, not a moat or proof of causal necessity. |
| **Riedl & Young, 2010**, JAIR [R6] | IPOCL adds character intentions to partial-order causal-link narrative planning; compares narrative-question judgments to POCL. | 32 students; one predicted judgment effect is only suggestive, another meets the paper's threshold. Narrative length was not controlled. | Causally coherent plots and intentional agents are prior art. The director's presentation cannot quietly manufacture world events. |
| **Mateas & Stern, 2005**, AIIDE [R7] | Façade combines authored reactive dialogue behaviors with story beats selected by a drama manager. | Implemented interactive drama and authoring lessons; extensive authored content, not an unrestricted emergent society. | High responsiveness and narrative management are not new; measure authoring labor and actual player agency. |
| **Bikhchandani, Hirshleifer & Welch, 1992**, JPE [R8] | Sequential agents observe previous actions and private signals; cascades can ignore private evidence and be fragile to public news. | Formal model, not evidence Roman citizens or current NPCs are Bayesian. Actions are observed rather than general free-form testimony. | Information cascades, correlated influence and correction shocks are established questions. Report what the implemented communication mechanism actually models. |
| **Spence, 2001 Nobel lecture**, primary retrospective [R9] | Signals transmit information under asymmetric information; equilibrium credibility depends on incentives/costs. | Explanation of theoretical signaling and conditions, not a rule that expensive assertions are true. | A payment, title or confident utterance is not verification. Distinct recipients can value identical information differently. |
| **Windrum, Fagiolo & Moneta, 2007**, JASSS [R10] | Empirical validation distinguishes a model's data-generation process from the unknown real one; compares calibration approaches. | Methodological analysis: matching output patterns does not uniquely identify mechanisms. | Internal replay correctness is different from historical, behavioral and policy validity. Do not call a plausible town a validated digital twin. |

The [Genesis novelty audit](../genesis/RESEARCH_NOVELTY_AUDIT.md), checked on
20 October, documents Generative Agents' structured town, AgentSociety/2,
STATE-Bench, CPB, MemoryArena, LongMemEval-V2 and CivWorldBench with version/date
limitations. Those findings still constrain this mission: private memory,
downstream state verification, source correlation and paired simulator
interventions are existing research areas. The old adverse gating result is
not erased by changing the product's setting or title.

## What an exactness or approximation claim requires

Define a semantic projection before testing: accounts, inventory, obligations,
locations at relevant observation times, private retained records and roots,
beliefs, relationships, opportunities, and consequential events. Equal terminal
cash alone is insufficient. A shorter ledger may be legitimate if omitted
records are declared no-ops; it is not identical full history.

For an interval `(t,u)`, exact skipping requires proving that no omitted step can
change that projection or any later transition, or replacing it with a correct
closed-form aggregate. A next-event queue must include message delivery,
inspection arrival, settlement, resource changes, schedules, decision windows,
memory expiry/age thresholds and interruptions. A pending message or a changing
confidence threshold invalidates a supposedly quiet interval. Per-tick stochastic
gossip opportunities cannot simply disappear; use a validated equivalent
first-event sampler/keyed schedule, or execute them.

Memory makes apparently decorative activity dangerous: movement can determine
observations; an experience can evict another; a receipt can prevent repeated
trust punishment. Dropping one changes future behavior even if its immediate
cash delta is zero. Use explicit invalidation when an intervention, preference,
queue, observation rule or institution changes. The fact that a trace has no
recorded edge is not proof that an omitted computation has no dependence.

If the adaptive scheme is approximate, state the tolerance and failure envelope
instead. Report missed consequential events, state/decision/relationship
distortion, delivery and per-agent allocation, belief/provenance consistency,
runtime, processed work and peak memory. Plot a fidelity–speedup frontier across
sparse **and** dense worlds, rather than selecting one quiet showcase. A method
can be exact only for a narrowly supported event class and fail outside it.

## Fair baselines and falsification

Compare full-resolution execution, a disclosed naive skip, and a competent
event-driven method under the same workload, logging, outputs and hardware.
Report setup/indexing cost, queue scans, serialization and refinement work;
count actual transitions and candidate checks, not just visible frames. Use
paired randomness independent of the number/order of RNG calls, warm-up and
repeated isolated timings. Treat the world/seed as the uncertainty unit. A faster
method that deletes causal opportunities is not an equal-fidelity speedup.

Montage is presentation selection over actual records. Score factual support,
coverage of consequential changes and user comprehension separately from
simulation accuracy. A dramatic summary cannot repair lost underlying events.
An identical branch is a valid result. A changed branch tests the specified
intervention; it does not automatically prove every parent link necessary.

Disconfirm the claimed advance if it loses commitments/private evidence, changes
decisions outside its declared tolerance, saves time only by omitting required
logging, becomes slower in dense worlds without disclosure, or offers no benefit
over ordinary DES. If simple scheduled quiet-hour skipping solves the present
workload, call it that. General long-horizon social compression remains future
work until independently varied societies support the claim.

## Learning and subjective time are separate hypotheses

Simulation days per CPU second, elapsed-history montage, felt duration and
retained/transferable human learning are four different measures. In a
52-student lab study, adding immersive VR increased presence but reduced tested
learning in that configuration; this does not prove VR is always harmful. [R11]
Mullen and Davidenko's labyrinth study concerns prospective interval production
and display/order effects, not living years in minutes or faster biology. [R12]
No code speedup licenses cognitive-acceleration, memory-implantation or
neuro-interface claims. Test education through actual delayed retention and
transfer against matched instruction, with human consent and source monitoring.

## Primary sources, access and reading scope

All new links checked **21 October 2026**. Papers were read through public PDFs,
author-posted text or official publication pages; no access restrictions were
bypassed. SAMAS publisher metadata is subscription-preview only, while the
author-uploaded text supplied methods/results. IPOCL's arXiv HTML returned 404;
the public PDF supplied its full paper. Methods/limitations, not only titles,
inform the matrix. For R12, the indexed publisher abstract was available but
direct PDF/XML access failed or returned403; only its stated design and
order-effect limitation are used, not an independently checked full-text result.

- **R1:** [Fujimoto, *Parallel Discrete Event Simulation*, CACM33(10), 30–53 (1990)](https://eecs.ceas.uc.edu/~wilseypa/classes/ece975/sp2010/papers/fujimoto-90.pdf), especially lookahead/invariance and performance limitations.
- **R2:** [SimPy, Time and Scheduling](https://simpy.readthedocs.io/en/latest/topical_guides/time_and_scheduling.html), current official semantics; [environment control](https://simpy.readthedocs.io/en/4.1.0/topical_guides/environments.html).
- **R3:** [SAMAS, ICCS2004, pp779–788, DOI10.1007/978-3-540-24688-6_101](https://link.springer.com/chapter/10.1007/978-3-540-24688-6_101); [author-uploaded methods/results](https://www.researchgate.net/publication/220855782_SAMAS_Scalable_Architecture_for_Multi-resolution_Agent-Based_Simulation).
- **R4:** [Sutton, Precup & Singh, *Between MDPs and semi-MDPs*, 112,181–211 (1999)](https://people.eecs.berkeley.edu/~russell/classes/cs294/f05/papers/sutton%2Bal-1999.pdf).
- **R5:** [Fowler, Event Sourcing (2005)](https://www.martinfowler.com/eaaDev/EventSourcing.html), original technical pattern; not a scholarly experiment.
- **R6:** [Riedl & Young, *Narrative Planning: Balancing Plot and Character*, JAIR39,217–268 (2010)](https://arxiv.org/pdf/1401.3841), §§4–5 and evaluation limitations.
- **R7:** [Mateas & Stern, *Structuring Content in the Façade Interactive Drama Architecture*, AIIDE1,93–98 (2005)](https://ojs.aaai.org/index.php/AIIDE/article/view/18722), implemented architecture/authoring account.
- **R8:** [Bikhchandani, Hirshleifer & Welch, JPE100(5),992–1026 (1992)](https://snap.stanford.edu/class/cs224w-readings/bikhchandani92fads.pdf), basic model and public-information shocks.
- **R9:** [Spence, *Signaling in Retrospect*, lecture8December2001](https://www.nobelprize.org/uploads/2018/06/spence-lecture.pdf), theoretical conditions, not a Kalends finding.
- **R10:** [Windrum, Fagiolo & Moneta, JASSS10(2)8 (31March2007)](https://www.jasss.org/10/2/8.html), model/real-process validation and identification.
- **R11:** [Makransky, Terkildsen & Mayer, Learning and Instruction60,225–236 (2019; online2017)](https://www.researchgate.net/publication/321978607_Adding_Immersive_Virtual_Reality_to_a_Science_Lab_Simulation_Causes_More_Presence_But_Less_Learning), author-posted experimental paper.
- **R12:** [Mullen & Davidenko, *Time Compression in Virtual Reality*, Timing & Time Perception9,377–392 (2021)](https://brill.com/view/journals/time/9/4/article-p377_377.pdf), interval-production study.
