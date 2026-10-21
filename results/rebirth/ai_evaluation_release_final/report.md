# Cognition contract QA

**42/42 functional cases passed.** Actual external inference: 0 calls, $0 spent.

These are authored-parser checks and injected fixtures. No real model quality was measured.

| Case group | Passed |
|---|---:|
| offline_intents | 22/22 |
| injected_intents | 9/9 |
| injected_contract_attacks | 6/6 |
| world_integration | 2/2 |
| timeout_fixture | 1/1 |
| budget_fixture | 1/1 |
| transport_fixture | 1/1 |

The raw JSONL preserves proposals, validator results, confirmed world receipts and redacted cognition receipts.
The manifest records the source bytes, runtime and artifact hashes. Its Git HEAD can precede uncommitted changes.
Synthetic wire usage and hypothetical prices test accounting only. Local timings are functional QA, not a model benchmark.
