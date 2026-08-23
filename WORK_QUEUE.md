# WORK_QUEUE

## Doing
- Methodology audit (METHODOLOGY_AUDIT.md) + fairness fixes

## Next
- Hash-based RNG (stable parallel worlds → counterfactuals)
- Typed scenario generator (parameterized worlds, families B–J)
- Stronger baselines: recency, BM25, vector+recency, vector+metadata, text-ingest structured
- Extended metrics (epistemic precision/recall, contradiction, corroboration)
- Multi-seed experiment runner + paired stats
- Scaling experiments (8→64+ agents) + plots
- Property-based fuzzing + oracle audit tests
- Capacity-pressure experiments
- Counterfactual analysis command
- Failure analysis (FAILURE_ANALYSIS.md)
- FORMALISM.md, PAPER_OUTLINE.md, literature second pass
- Final WHAT_I_BUILT.md rewrite

## Completed
- v0 snapshot: git tag `kalends-memorybench-v0`, tests green, results/ saved, ENVIRONMENT.txt

## Blocked
- Real-embedding vector baseline (needs network/model); adapter interface only
- LLM integration (no API assumed); interfaces documented, not exercised

## Newly discovered
- (running list; see bottom of file as session proceeds)
