# First session: the account at the fountain

## Quickstart without revealing the outcomes

Run `./scripts/run_rebirth.sh` from the repository and open the local address printed in the terminal, normally `http://127.0.0.1:8782/`. A launcher using `--port 8780` serves the same build there. Rebirth writes its separate version-four save; the old Pompeii archive is not replaced.

1. Choose **Enter Pompeii** or **Continue as Aelia**. Aelia is the character with the pale ring under her feet. The opening concern is shown at the left.
2. Select Sabina beside the cart, or use **Find Sabina**. A person can move as world time passes; the journal's **People** tab can find their current workplace.
3. Read the short conversation and choose what to ask or offer. Each consequential choice opens a review. **Confirm this choice** is the step that changes resources or makes a promise. **Step back** cancels it.
4. Explore before choosing an arrangement. Click the street to walk, select a doorway to enter, or use arrow keys/WASD. **E** interacts nearby; **J** opens the journal. On touch devices, tapping people and doorways works alongside the movement pad.
5. Use **The account** in the journal to follow leads and reread copied terms. **Bag** shows coins, flour, access and commitments. The date on a document is the date of its terms, not a claim that they describe the present.
6. The default pace lets you think. Walking and work still consume world minutes. **Live** advances slowly; **Wait 30m**, **Next moment**, and the passage menu's hour/day/week options advance explicit world time. Conversations pause Live. Closing the browser saves the current life; it does not simulate an unattended week automatically.
7. After an arrangement, return to the people affected. New work and a second decision emerge after a little world time. A generous immediate payment can carry an obligation; read its deadline before advancing days.

Settings offers reduced motion, larger text, stronger contrast and optional interaction sounds. Local play notes are optional and off by default. **World Lab** deliberately reveals private simulation records and alternative histories; save it for after exploring if you want to discover the situation through Aelia's own knowledge.

Some work, trade, inspection and delivery buttons remain selectable before every resource or daily limit is satisfied. A rejected confirmation explains the missing requirement and leaves the world unchanged. Check the Bag and the review before committing; improving these early availability hints remains a usability task.

## QA setup and evidence standard

The remaining sections disclose outcomes. Use separate temporary lives for route checks, for example `./scripts/run_rebirth.sh --temporary --port 8784`; stop and relaunch to start a new temporary life. Do not delete or reuse the owner's saved life to reset a test.

The steps below are an executable manual test protocol derived from canonical actions and automated checks. They are not a claim that an independent person completed a playtest. Browser screenshots and the final QA record should identify which steps were actually run, viewport, build/commit, save origin, observed defects and fixes. Wall-clock onboarding targets need an observed play session; simulation minutes alone cannot establish them.

For each review, first note coins, inventory, world minute and the open commitment count. Opening a proposal must change none of them. Confirm once, check the receipt and updated state, then verify that a second attempt cannot repeat the reward or allocation.

## Route A: stand behind the market, then complete a paid account

1. In a default fresh life, select nearby Sabina. Optionally ask **What happened to your order?** and **Show me what you paid for**. The receipt copy should appear in the journal; opening a conversation alone should not copy it.
2. Choose **Stand behind the market**. The review must disclose three coins and the household losing priority. Cancel once and confirm that Player cash is still six. Reopen and confirm.
3. Delivery takes twenty world minutes. Player cash becomes three. The actual delivery event allocates four units to Sabina and two to Felix; the household receives a funded refund. Market access opens, Sabina's welcome improves and Lucius's affinity falls. There is no Player service obligation.
4. Advance at least 45 further world minutes: two **Wait 30m** actions suffice. The objective should now concern the household that waited. Visit Lucius to inspect the three-coin repair offer. It should be optional and its review should disclose the real cost. Confirming it spends the three coins and opens household access.
5. To test a market commission without spending the repair money first, continue a separate copy of the market route. Find Sabina at the food counter and choose **Keep the counter open**. The contract requires two flour units within six hours and reserves five coins from Sabina into commission escrow. Acceptance pays Aelia nothing.
6. Choose **Is there paid work here?** and confirm a 55-minute shift. The wage is three coins from Sabina's account. Find Marcus and type **Buy two flour units**, then review and confirm. At the early default price this costs four coins; the one-unit button can instead be used twice.
7. Return to Sabina before the deadline and choose **Settle our commission**. Exactly two units leave Player inventory and five reserved coins reach Player cash. The commitment becomes fulfilled, completed commissions increments and a favor is earned. The same account cannot offer another commission that day.
8. In an expiry variant, accept but withhold delivery and advance beyond the deadline. The payer receives the escrow back, Player receives no reward, the commitment is missed and reliability falls. The Bag must show the actual deadline and must list the commission once.

## Route B: investigate the dated terms and negotiate

1. Start another fresh temporary life. With Sabina, confirm **Show me what you paid for** (`examine_receipt`).
2. Find Dama, initially near the cart. Confirm **What did the steward actually order?** (`examine_tablet`). Her instructions specify four units rather than all six. If time has moved on, use People to find her current location.
3. Find Marcus. Read the loading-account topic: it should offer a paid check and withhold the actual account. A typed question such as **What does your loading account say?** must not create a checked copy or remove a coin.
4. Choose **Open the loading account** (`verify_cart`). Review the one-coin, fifteen-minute cost and confirm. Player cash becomes five, fifteen minutes pass, and a checked loading record appears alongside the two other retained terms.
5. Choose **Put the two accounts together** (`mediate`). With all three terms retained, Marcus can fund release. Twenty minutes later, four units go to Lucius and two to Sabina. Under default early accounts Player cash is seven: six initial, minus the check, plus a two-coin brokerage fee. Carrier cash is three. Broker access opens; Marcus's competence assessment improves while his personal welcome cools.
6. After 45 minutes, Marcus offers a working-relationship repair and **A report worth buying**. Accept the commission before booking the new inspection. An inspection obtained before acceptance must not satisfy it.
7. Choose **Arrange a current supply inspection**, paying one coin. Advance at least fifteen minutes for the direct observation to arrive. Confirm **Settle our commission** within four hours; the reserved three coins pay once. The Bag must describe a checked report, not flour.
8. Within an hour of the direct observation, choose **Rebuild our working arrangement** (`reconcile`). The actual retained direct report supports the repair. A stale or second-hand report must fail the requirement.

## Route C: household priority and the cost of an advance

1. Start another fresh temporary life. Visit the household and select Lucius. Choose **Put my name behind the household** (`guarantee_household`). Review the service obligation before confirming.
2. Lucius pays six coins to Aelia and three to the carrier. Delivery twenty minutes later sends all six units to the household. Player cash is twelve in the default fresh life. Household access opens; Player affiliation becomes household client; the Bag records 120 service minutes due within three days. Sabina receives her advance back but loses the flour and withholds new shifts.
3. After follow-up opens, ask Lucius for a commission before keeping service. It must be unavailable. Choose **Keep my service promise** (`return_service`) while enough time remains. Exactly 120 world minutes pass, the institutional commitment becomes fulfilled, and household commissions become available.
4. Accept **The steward's next account**. Three Player flour units must be delivered within eight hours for eight reserved coins. Buy real goods, return and confirm settlement. Acceptance itself must not create flour or pay a reward.
5. For the connected repair, obtain two additional units, visit Sabina and choose **Bring something the counter can serve**. The units must leave Player inventory and reach her counter; market access and welcome recover. Saying that flour was brought without possessing it must fail.
6. In a separate failure variant, accept household priority and advance beyond the three-day service deadline without returning. The commitment becomes missed, reliability falls and household commission access closes. Attempting a 120-minute service shift too late to finish before the deadline must be rejected without changing time or cash.

## Ignore, return, and inspect an actual alternative

1. In a fresh life, choose **This is not my bargain**, or simply leave. Advance six hours. When Lucius can fund carriage and the cart has six actual units, he settles priority himself. Player cash and obligations do not change; the cart no longer holds the goods. The public lead says the cart went to the household and invites a return to Sabina.
2. Aelia's journal must not reveal the private original receipt, loading account or unseen buyer settlement merely because time passed. She can still help Sabina with two real units later and open market work.
3. After a chosen route, use the passage menu to advance a day or week. The aftermath should show actual visible consequences, including missed commitments where applicable, rather than claim every NPC activity was witnessed. Daily procurement and consumption continue in the authoritative world.
4. Open Settings → **World Lab**. Remove a confirmed route action using **Run alternative**. Check cash, flour, route and access comparisons. The original life must remain unchanged; infeasible later commands must be disclosed. Return to game mode and confirm that private operator records are no longer exposed through the game context.
5. Restart a persisted test life. Cash, retained documents, access, relationship state, completed/missed commitments and ledger hash must reproduce. Restarting must not award another fee or repeat a settled delivery.

## Existing-life continuation

Create or select a genuine older Pompeii save, then migrate to a different destination: `./scripts/run_rebirth.sh --journal /tmp/rebirth-migration-qa.json --migrate-from /path/to/old-pompeii.json --port 8784`. Preserve the source file bytes and verify they remain unchanged.

- An old open `household-service` promise must offer **Keep my earlier household service promise** at Lucius. Review and confirm; it consumes 120 minutes and settles that existing obligation without another advance. If it cannot finish before the old deadline, it is disabled. A new Rebirth promise uses the separate **Keep my service promise** action. Both block household commissions while open, including after a market-route repair. Keeping the old service improves the new reliability/competence axes; missing it reduces reliability/welcome and removes household access, with the old obligation linked as evidence.
- An old active Felix flour promise must offer **Keep my earlier flour promise**. It is disabled until Player owns the required flour, then settles the existing contract without creating a new one.
- New cart advances occur at the older world's current minute. Player cash is not reset to six. Sparse old stock can leave the new cart awaiting a genuine arrival; the episode cannot manufacture the missing flour.

Automated coverage is in `tests/test_rebirth_world.py`, `tests/test_rebirth_ai.py` and `tests/test_rebirth_server.py`. In particular, genuine old save → migrated contextual review → service settlement → restart is tested, as are the inherited Felix promise and the separate new service obligation. Full socket/HTTP checks require an environment allowed to bind a local port.
