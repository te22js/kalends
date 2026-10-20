# AI cost model and expenditure controls

**Measured external game-cognition API expenditure in this sprint: $0.** Offline and mock
execution are local program work. Local CPU time, engineering, art, historical
review and support are real costs; they are not assigned a dollar value here.
No live provider quality, model latency or paid token usage is claimed.
Image-generation tool usage sits outside this cognition ledger; its dollar cost
was not measured here. The zero figure is not a total production-cost claim.

The implementation requires explicit model/rate assumptions and a positive
approved budget before external inference. Rates are not hard-coded as current
vendor prices. Enter the actual chosen model's rates after verifying its current
billing conditions. `.env.rebirth.example` defaults every external switch and
budget to zero/off, with invalid rate placeholders that block transport.

## Accounting contract

For reported input tokens `I`, output tokens `O`, and configured rates `r_i` and
`r_o` in dollars per million tokens:

`estimated request cost = (I × r_i + O × r_o) / 1,000,000`.

The adapter first reserves a conservative input-byte estimate plus message
allowance, and the maximum allowed output tokens. The request is refused before
transport if that reserve does not fit. On a completed response its reported
usage determines the estimate. Invalid semantic output is still counted. A
failed or timed-out call may be billed, so unknown usage retains the full reserve.
Receipts distinguish known and unknown costs; errors are not advertised as free.

This mechanism is an application spending guard under declared price/token
assumptions. It cannot certify a provider's invoice, a changed tariff, tool fees,
or tokenizer/transport behavior outside the declared contract. It makes no
unauthorized paid call to discover those facts.

## Illustrative session, entirely hypothetical

Assume **$1 per million input tokens and $5 per million output tokens**, purely
to show the formula. These are scenario inputs, not current product quotations.

| Task | Hypothetical calls | Input/output per call | Scenario cost |
|---|---:|---:|---:|
| Intent interpretation | 20 | 1,200 / 180 | $0.0420 |
| Dialogue realization | 20 | 2,200 / 300 | $0.0740 |
| High-level plan proposals | 4 | 1,800 / 240 | $0.0120 |
| One reflection | 1 | 3,500 / 400 | $0.0055 |
| **Session total** | **45** | — | **$0.1335** |
| With a hypothetical 20% reserve | — | — | **$0.1602** |

This estimate excludes voice, image creation, hosting, long contexts, repeated
failures, moderation, support and content production. A 20% reserve is not a
measured failure rate. Better caching and deterministic routine behavior can
reduce calls, but only actual usage receipts can establish a saving.

## Latency and call placement

| Task | Implemented default timeout | Default output cap | Product placement |
|---|---:|---:|---|
| Intent | 2 s | 300 tokens | Only when a player submits an actionable utterance |
| Dialogue | 3 s | 400 | Optional grounded realization; authored fallback remains available |
| Planning | 2 s | 500 | Significant decision points; proposal only |
| Reflection | 3 s | 500 | Selected episodes or explicit reflection; bounded records |
| Montage | 3 s | 350 | Explicit time-return presentation |
| Content draft | 4 s | 800 | Authoring sandbox, not a background gameplay tick |

These are implementation budgets, not observed provider latency. Background
procurement, resource settlement and routines stay deterministic. Generating
speech for every citizen on every empty minute would add expense without a
measured player benefit.

Before any paid trial, freeze the provider/model, credential source, approved
maximum spend, per-task configuration, context budgets, sample cases and scoring
rules. Preserve real response receipts separately from synthetic fixtures. Measure
p50/p95 time to useful UI response, valid-action rate, unsupported personal-history
claims, fallback rate and full-session cost. Stop on budget exhaustion, repeated
scope violations, or a stalled endpoint. A ChatGPT subscription is not an API key
or authorization to spend.
