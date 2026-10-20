"""Executed outcomes only. Asset change is utility under a disclosed inventory value.

Cash already includes purchases, fees, revenue and penalties. Adding any of
those components again would double-count. This is not optimal-policy regret.
"""
from __future__ import annotations
import math


def executed_metrics(sim, terminal_inventory_value=3.0):
    if isinstance(terminal_inventory_value, bool) or not isinstance(terminal_inventory_value, (int, float)) or not math.isfinite(terminal_inventory_value) or terminal_inventory_value < 0:
        raise ValueError("terminal inventory valuation must be nonnegative")
    rows = []
    owned_events = {a: [] for a in sim.agent_ids + ["Player"]}
    acquisitions = {a: [] for a in sim.agent_ids + ["Player"]}
    for event in sim.ledger.events:
        owner, category = event.payload.get("owner"), event.payload.get("category")
        if owner in owned_events:
            owned_events[owner].append(event)
            if category in ("purchase", "player_market_purchase"):
                acquisitions[owner].append(event)
        if category == "player_trade" and event.payload.get("buyer") in acquisitions:
            acquisitions[event.payload["buyer"]].append(event)
    for agent in sim.agent_ids + ["Player"]:
        commitments = sim.economy.commitments[agent]
        settled = [c for c in commitments if c["status"] in ("fulfilled", "missed")]
        committed = sum(c["quantity"] for c in settled)
        filled = sum(c["fulfilled"] for c in settled)
        own = owned_events[agent]
        purchases = acquisitions[agent]
        initial = sim._initial_accounts[agent]
        cash_delta = sim.economy.cash[agent] - initial["cash"]
        inventory_delta = sim.economy.inventory[agent] - initial["inventory"]
        rows.append({"agent": agent, "cash": sim.economy.cash[agent], "inventory": sim.economy.inventory[agent],
                     "cash_delta": round(cash_delta, 4), "inventory_delta": inventory_delta,
                     "net_asset_change": round(cash_delta + terminal_inventory_value * inventory_delta, 4),
                     "committed_units": committed, "delivered_units": filled,
                     "delivery_fill_rate": filled / committed if committed else None,
                     "missed_units": committed - filled,
                     "purchase_attempted": sum(e.payload.get("attempted", 0) for e in purchases),
                     "purchase_filled": sum(e.payload.get("quantity", 0) for e in purchases),
                     "zero_fill_orders": sum(e.payload.get("quantity", 0) == 0 for e in purchases),
                     "inspection_cost": sum(e.payload.get("fee", 0) for e in own if e.payload.get("category") == "inspection_booked"),
                     "fulfilled_contracts": sum(c["status"] == "fulfilled" for c in settled),
                     "missed_contracts": sum(c["status"] == "missed" for c in settled)})
    citizens = rows[:-1]
    committed, delivered = sum(r["committed_units"] for r in citizens), sum(r["delivered_units"] for r in citizens)
    attempted, filled = sum(r["purchase_attempted"] for r in citizens), sum(r["purchase_filled"] for r in citizens)
    return {"primary_metric": "delivery_fill_rate", "delivery_fill_rate": delivered / committed if committed else None,
            "committed_units": committed, "delivered_units": delivered,
            "purchase_attempted": attempted, "purchase_filled": filled,
            "purchase_fill_rate": filled / attempted if attempted else None,
            "net_asset_change": round(sum(r["net_asset_change"] for r in citizens), 4),
            "cash_delta": round(sum(r["cash_delta"] for r in citizens), 4),
            "inspection_cost": sum(r["inspection_cost"] for r in citizens),
            "unused_stock": sim.economy.market_stock,
            "eligible_decisions": sum(bool(d.get("opportunity_valid")) for d in sim.decisions),
            "n_decisions": len(sim.decisions), "agents": citizens, "player": rows[-1],
            "terminal_inventory_value": terminal_inventory_value,
            "utility_definition": "cash change plus terminal value times inventory change; fees/revenues/penalties counted in cash exactly once",
            "regret": None, "regret_note": "No optimal-policy counterfactual is computed; asset change is not regret."}
