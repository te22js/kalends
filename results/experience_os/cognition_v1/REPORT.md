# Controlled cognitive experiment

This is an exploratory authored study on actual Commons allocations, not a held-out benchmark or human learning study.

Executed 972 worlds across 12 paired seeds. Sources stable during execution: True.

| Arm | Projects | Missed promises | Fees | Unused capacity | Secondary score | Mind bytes |
|---|---:|---:|---:|---:|---:|---:|
| bm25_fifo | 2.333 | 0.222 | 0.556 | 0.444 | 2.056 | 5251 |
| v2_goal | 2.333 | 0.111 | 0.444 | 0.444 | 2.178 | 5978 |
| v2_hybrid | 2.333 | 0.111 | 0.444 | 0.444 | 2.178 | 5980 |
| v2_recency | 2.333 | 0.222 | 0.556 | 0.444 | 2.056 | 5970 |
| v2_salience | 2.333 | 0.111 | 0.444 | 0.444 | 2.178 | 5982 |
| v3_goal | 2.333 | 0.111 | 0.444 | 0.444 | 2.178 | 7307 |
| v3_hybrid | 2.333 | 0.111 | 0.444 | 0.444 | 2.178 | 7309 |
| v3_recency | 2.333 | 0.222 | 0.556 | 0.444 | 2.056 | 7319 |
| v3_salience | 2.333 | 0.111 | 0.444 | 0.444 | 2.178 | 7311 |

V3 minus V2 intervals are in summary.json. Raw accepted allocations, delivered units, decisions, input hashes, conservation totals and ledger hashes are in raw.jsonl.

- Controlled exploratory authored families; no held-out or independent replication claim.
- The same existing planner and belief guards are reused, so V3 plan persistence may add bytes/latency without changing outcomes.
- Record/context maxima match, not serialized bytes or token counts; V3 additionally retains up to four bounded plans.
- BM25 is lexical retrieval with FIFO episode retention and no semantic consolidation; admitted structured fields are included as text so direct-check titles do not hide their factual content. It is not a dense embedding baseline.
- A maximum of one paid inspection is allowed per final decision; its observation and fee are endogenous and reported.
- Background team policies are suppressed for controlled matching; this does not establish emergent whole-society improvement.
- These controlled decision tasks span one simulated day; long absence here is 900 minutes, not evidence of multi-month cognitive performance.
- The delayed hidden hardware transition is unknowable before allocation; resulting failure is not automatically a memory defect.
- Per-case timing is a short descriptive probe; machine load and arm ordering are not a controlled latency experiment.
- No LLM calls, human participants, skill-transfer results or neurological time claims.

## Observed result

V3 did not improve executed projects, promise outcomes, inspection fees or unused capacity against its matched V2 retention arm: all 432 paired cases tied, and their executed world ledger hashes also matched. Its persistent plan state added approximately 1.33–1.35 KB per saved mind. The short timing probe also showed overhead; it is descriptive rather than a controlled latency claim.

Each arm completed 252 projects across 108 worlds. Salience, goal and hybrid retention each missed 12 promises and paid 48 inspection credits. Recency and FIFO/BM25 each missed 24 promises and paid 60 credits. Thus the demonstrated benefit is preserving a consequential promise and avoiding one paid recheck in two authored families; project completion did not improve. Recency, BM25 and both generations correctly share several negative findings, including the unknowable delayed hardware transition.

The zero-width V3-minus-V2 outcome intervals reflect exact ties in this small authored suite. They do not establish population-level equivalence. All seeds share the same nine scenario templates, and differences between memory policies are largely engineered by those templates. A harder, independently authored, multi-month study is still required. The raw arithmetic cross-check is in arithmetic_audit.json; it was performed by the implementing agent and is not independent replication.
