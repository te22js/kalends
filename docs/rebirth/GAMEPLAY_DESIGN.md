# Rebirth gameplay: the account at the fountain

Rebirth adds one connected commercial story to the preserved six-person Pompeii world. Aelia can resolve an actual disagreement with evidence, her own money, or a service promise. Those approaches change inventories, accounts, future work and the people who welcome her. The episode then becomes a relationship problem and a small repeatable livelihood loop.

This is an implemented authored episode, not a claim that players have found it enjoyable. Automated route and simulation checks establish behavior; human playtesting is still needed to assess clarity, tension and replay value.

## Opening and readable stakes

At the opening, Sabina and Dama move to real street positions beside Marcus. They return to their ordinary duties after 45 world minutes. These are the same simulated people used by the other systems. The dispute therefore remains understandable even when the player walks away: the two customers and the trader have places, work and a deadline.

Six flour units are removed from shared stock into a real cart account. Sabina advances up to four coins for two units and Lucius up to eight for four; the money moves from their existing accounts to Marcus. In an impoverished migrated life, the actual available advances are recorded rather than invented. If fewer than six units exist, the arrangement waits for a real replenishment.

Three documents disagree in emphasis rather than presenting a magic right answer:

| Holder | Retained document | What it can establish |
| --- | --- | --- |
| Sabina | Her wax account | Two units were ordered; the actual advance is written down. |
| Dama | Household instructions | The steward reserved four units; she was sent to repeat that quantity. |
| Marcus | Carrier's loading account | Six units share the cart; a three-coin carrying charge still prevents departure. |

Sabina and Dama let Aelia read their retained terms when approached. Marcus requires one coin and fifteen minutes for a checked copy. Asking a loading-account question does not bypass that charge. At minute eight the trader privately receives a hold notice: an earlier ready dispatch is no longer a current guarantee of departure. Dated evidence and present conditions are intentionally different.

## Three approaches with different futures

All three agreements require six actual reserved units and must precede the six-hour bargaining deadline. Every carrying payment is funded before departure. Delivery occurs twenty world minutes after agreement, and the action advances those minutes while other scheduled events continue.

| Approach | Immediate resources | Actual allocation | Future access and cost |
| --- | --- | --- | --- |
| Put the accounts together | Retain all three copied terms; pay one coin for the loading check. Marcus pays the three-coin charge and a brokerage fee of up to two coins if funded. | Four units to Lucius, two to Sabina. | Broker commissions. Both buyers respect the accurate account; Marcus recognizes competence but resents the intrusion. |
| Stand behind the market | Aelia pays the three-coin carrying charge. | Four units to Sabina, two to Felix. Lucius receives his advance back to the extent Marcus can fund it. | Market commissions and a warmer counter. Lucius loses priority and becomes less welcoming. |
| Back household priority | Lucius funds six coins to Aelia and three to the carrier. Aelia must be independently affiliated. | All six units to Lucius. Sabina receives her advance back to the extent Marcus can fund it. | Household commissions after service. Aelia owes 120 world minutes within three days; Sabina withholds further shifts pending repair. |

With default starting accounts, Player cash after these paths is seven, three and twelve coins respectively. The household balance is an advance against an institutional obligation, not a free superior prize. Brokerage requires walking, retained evidence, a fee and Marcus's funded participation. Market support spends scarce personal coins but preserves independence. The routes have different allocations and social effects; they are not three buttons that grant the same reward.

Ignoring or declining is a supported branch. At the deadline, a solvent Lucius pays the carrying charge himself and takes the cart. The player receives no cash, access or compulsory service. Sabina remains a possible later relationship. When no buyer can release the cart, reserved goods return to shared stock and available funds return the customers' advances. The engine does not create flour or negative cash to force the episode to finish.

## Consequence is a second decision

Forty-five minutes after a chosen delivery, a different follow-up opens:

- After market support, contribute three coins toward Lucius's replacement delivery to repair the grievance and open household work.
- After household priority, bring two flour units from Aelia's own bag to Sabina to repair the empty counter and open market work.
- After brokerage, bring Marcus a direct supply inspection no more than an hour old to repair the working arrangement.
- After an ignored dispute, bringing two units to Sabina opens a place at the counter.

These costs are real transfers, not dialogue flags standing in for help. Aelia can leave a relationship unrepaired. Household service is separately recorded, consumes 120 minutes, and must finish before its deadline. Missing it marks the commitment missed, reduces reliability and removes household commission access. Defaulting does not grant another earned favor.

## A small repeatable livelihood

After follow-up becomes available, established access opens the corresponding commission:

| Account | Fulfilment | Reward reserved on acceptance | Deadline |
| --- | --- | --- | --- |
| Sabina | Two flour units from Player inventory | Five coins | Six hours |
| Marcus | A new direct inspection obtained after acceptance | Three coins | Four hours |
| Lucius | Three flour units from Player inventory; original household service already kept when applicable | Eight coins | Eight hours |

There is one open commission across the player at a time and at most one per account per day. The payer transfers the reward to a real escrow account at acceptance. Fulfilment releases it once; expiry returns it to the payer. Goods must exist in the player's bag, and the trader's evidence commission rejects an old inspection. Deadlines, rewards, transfers and status changes are ledger events with parent evidence.

Paid work remains a safety valve: Sabina pays three coins for 55 minutes and the household pays four for an 80-minute shift at Chreste's fullery. Each workplace offers at most two extra shifts per day, must have the cash, and Sabina may withhold a welcome after the household route. Thus an initially cash-poor market supporter can work before purchasing a commission's flour. Player progression records actual paid shifts, kept commissions and opened accounts.

## Relationships and planning

Relationships keep five distinct quantities. They are inspectable close to the person, while remote NPC internals remain unavailable in game view.

- **Credibility** governs whether an NPC accepts Aelia's factual report. Inspection can corroborate a dated report, expose a contradiction, or recognize truthful but outdated news. A missed errand does not automatically make a factual statement false.
- **Reliability** reflects fulfilled and missed commitments, gates new commissions, and helps determine whether an NPC waits for an accepted player delivery instead of buying independently.
- **Affinity** reflects personal welcome, including Sabina withholding shifts after losing her supply.
- **Competence** records demonstrated brokerage and practical follow-through. It is a descriptive axis in this build, not a hidden multiplier on every transaction.
- **Favors** record specific reciprocal credit. If reliability has fallen below the ordinary commission threshold, one earned favor can fund one further chance; its consumption is displayed before confirmation and recorded in the acceptance event.

NPC plans contain a long-term role, a medium-term concern and a short-term intention. Actual procurement uses owned stock, owned cash, accepted player commissions and bounded retained supply records. It can work with current stores, conserve coins, verify a report, defer once, buy, or await a sufficiently reliable promised delivery. Verification schedules an inspection and subsequent purchase; deferral schedules one retry. New evidence or changed resources revises the plan. No NPC reads another person's private account or searches the world ledger for a forgotten memory to justify a decision.

## Conversation, privacy and action contracts

`world.context(recipient)` requires proximity and is an NPC-scoped intelligence input. It contains retained experiences, owned state, authored topic lines, the current plan and available canonical player choices. `disclosure_evidence_ids` is the smaller set the character is willing to use in ordinary dialogue. Marcus's unpaid loading record remains known to him but is excluded from that disclosure set. Independent plan/reflection tools may use the NPC's private retained context; the player conversation must use permitted disclosure records.

Browser context must project only approved greeting/topics/choices/relationship fields, rather than publishing the entire private intelligence input. Game snapshots omit private original documents and remote account/relationship values. Nearby choices guide the player without requiring a typed command vocabulary. Confirmed questions about Sabina's or Dama's documents create an actual copied experience; confirming a news exchange transfers the speaker's retained dated report. Typing alone proposes an action and changes no world state.

Canonical new actions are `hear_dispute`, `examine_receipt`, `examine_tablet`, `verify_cart`, `mediate`, `support_market`, `guarantee_household`, `return_service`, `reconcile`, `accept_commission`, `fulfill_commission`, `decline_dispute` and `reflect`. Original physical trade, work and inspection actions remain valid. The server applies actions to a copied trial world so failed multi-step actions cannot leave partial charges behind.

## Time and continuation

The existing discrete event clock remains authoritative. Waiting, walking, working and making an agreement all allow other due events to run. Long skips still execute deadlines, deliveries, purchases, daily consumption and next-day opportunities; a montage shows relevant recorded consequences. No per-minute paid model call is introduced.

`RebirthWorld.from_legacy` deep-copies the previous world, preserves its exact ledger prefix and Player resources, bridges prior trust into new credibility/reliability, extends the simulation horizon explicitly where possible, and appends the new episode at the old world's current minute. The old archive is not reset. New advance payments occur now, never as fabricated transactions in the old history.

Existing open household-service and Felix delivery commitments retain explicit contextual settlement choices. These target the original contracts; the newer Rebirth service is a separate obligation. An inherited service shift is disabled if its 120 minutes would finish too late. Any outstanding old or new household-service promise blocks Lucius's new commissions, even after a different cart route repairs access. Keeping or missing an inherited service changes the new relationship axes through a settlement event linked to the original obligation; missing it also closes household access.

The new persistent ledger is optional. `optimized=False` keeps the legacy ledger for exact matched reference tests; optimized mode seals historical nested payloads and shares them across trial copies while retaining branch isolation. Both modes run the same gameplay and event order.

## Historical boundary and verification

Commercial wax tablets and written transaction accounts are supported by the [Pompeii archaeological park's official guide](https://pompeiisites.org/wp-content/uploads/A-Guide-to-the-Pompeii-Excavations-2.pdf) and the [Italian State Numismatic Portal's Pompeii guide](https://www.pompei.numismaticadellostato.it/static/repository/guidaPompei/PNS_Guida_Pompei12.pdf). The cast, particular deposit, fee, quantities, priority terms, wage caps and outcomes are fictional game rules. This episode depicts a private bargain and household power, not an attested case or a state grain-allocation tribunal. The exact 79 CE eruption day is not treated as settled.

`tests/test_rebirth_world.py` covers distinct route outcomes, funded carriage and brokerage, cash/goods conservation, document ownership and paid withholding, confirmed document transfer, ignored settlement, costly repair, kept/missed service, reserved commission rewards, real goods, new evidence, daily limits, separate credibility and reliability, favor consumption, private disclosure, exact old prefix preservation, contextual settlement of genuine old saved obligations, depleted old stock and optimized/reference equivalence with subsequent branch isolation at 1, 7 and 30 days. The targeted model and language integration cases pass; the final QA record reports the complete suite count. This evidence does not substitute for a human play session or establish commercial demand.

The final review prompted additional read-only resource guards for work, purchase, inspection, repair and commission fulfilment. Public trade quotes disclose quantity, unit price, total cost and availability without dumping a seller's private account; any accepted world change expires the reviewed proposal. Commission reviews disclose their actual duration and due time before acceptance. Authoritative confirmation still checks the current world and commits atomically. Retained shared memories are selected chronologically, and their displayed clauses and evidence use the same records. Accepted-command presentation revisions preserve exact old Rebirth journal replay while new conversations use corrected recall. Foreground occlusion and environmental object interactions remain limited; the illustrated district is a small narrative game with three recurring commission templates, rather than a fully simulated city.
