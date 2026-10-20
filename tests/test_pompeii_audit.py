"""Independent regressions for the player account, private records and quest."""
import copy

import pytest

from kalends.pompeii.language import ProposalLanguage
from kalends.pompeii.server import PompeiiSession
from kalends.pompeii.world import PompeiiWorld


def test_game_initial_accounts_are_player_only_and_lab_keeps_full_ledger():
    session = PompeiiSession()
    world = session.original
    before = world.ledger.content_hash()
    initial = session.state()["world"]["journal"][0]
    traced = session.trace(0)["events"][0]
    for event in (initial, traced):
        for field in ("cash", "inventory", "commitments"):
            assert set(event["payload"][field]) == {"Player"}
    # Projection must neither redact the durable source nor alias its payload.
    initial["payload"]["cash"]["Player"] = -100
    assert world.economy.cash["Player"] == 6
    assert world.ledger.content_hash() == before
    session.apply("mode", {"mode": "lab"})
    assert set(session.trace(0)["events"][0]["payload"]["cash"]) == set(world.memories)
    assert world.ledger.content_hash() == before


def test_game_hidden_supply_trace_denied_and_nearby_read_required():
    session = PompeiiSession()
    supply = next(e for e in session.original.ledger.events if e.payload["category"] == "supply")
    assert supply.event_id not in {e["event_id"] for e in session.state()["world"]["journal"]}
    with pytest.raises(ValueError, match="not available"):
        session.trace(supply.event_id)
    with pytest.raises(ValueError, match="Walk"):
        session.propose({"recipient": "Lucius", "text": "What news have you heard?"})
    session.apply("mode", {"mode": "lab"})
    assert session.trace(supply.event_id)["events"][0]["payload"]["value"] == "available"


@pytest.mark.parametrize("text", [
    "I will not buy four flour.",
    "I do not promise four flour.",
    "What is your work?",
    "Can I deliver later?",
])
def test_negation_and_information_questions_do_not_propose_commitments(text):
    world = PompeiiWorld()
    language = ProposalLanguage()
    before = world.ledger.content_hash()
    proposal = language.propose(text, "Felix", world.private_view("Felix"))
    assert proposal["interpretations"][0]["action"]["action"] == "talk"
    assert world.ledger.content_hash() == before


def test_positive_purchase_stays_explicit_and_preview_does_not_mutate():
    session = PompeiiSession()
    session.apply("move", {"location": "bakery"})
    before = session.original.ledger.content_hash()
    proposal = session.propose({"recipient": "Felix", "text": "Buy four flour"})
    assert proposal["interpretations"][0]["action"] == {
        "recipient": "Felix", "action": "buy", "quantity": 4}
    assert session.original.ledger.content_hash() == before
    assert session.original.economy.cash["Player"] == 6


def test_selected_character_view_has_no_hidden_dispatch_or_other_memories():
    world = PompeiiWorld()
    world.move(location="bakery")
    view = world.private_view("Felix")
    assert view["beliefs"]["grain.supply"]["value"] == "unknown"
    assert not any(e["subject"] == "grain" for e in view["experiences"])
    assert not set(view) & {"world", "facts", "other_agents", "dispatch_records"}
    other_memory = copy.deepcopy(world.remembered("Sabina"))
    actual = dict(world.state.facts)
    world.claim("Felix", "disrupted")
    assert world.knowledge("Felix")["value"] == "disrupted"
    assert world.state.facts == actual
    assert world.remembered("Sabina") == other_memory


@pytest.mark.parametrize("route,final_cash,affiliation", [
    ("wage", 7, "independent"),
    ("patronage", 12, "household client"),
    ("information", 6, "independent"),
])
def test_initial_six_coin_four_flour_quest_has_three_actual_solutions(route, final_cash, affiliation):
    world = PompeiiWorld()
    world.move(location="bakery")
    world.interact("accept_delivery", "Felix")
    if route == "wage":
        world.move(location="thermopolium")
        world.interact("work", "Sabina")
    elif route == "patronage":
        world.move(location="household")
        world.interact("patronage", "Lucius")
    else:
        world.move(x=930, y=415)
        world.talk("Marcus", "supply")
        world.move(location="household")
        world.interact("sell_information", "Lucius")
    world.move(x=930, y=415)
    world.interact("buy", "Marcus", 4)
    world.move(location="bakery")
    receipt = world.interact("deliver", "Felix")
    assert world.minute < 600
    assert receipt["payload"]["delivered"] == 4
    assert world.flags["quest"] == "fulfilled"
    assert world.flags["affiliation"] == affiliation
    assert world.economy.cash["Player"] == final_cash
    assert world.economy.inventory["Player"] == 0
    assert world.economy.commitments["Player"][0]["status"] == "fulfilled"
    assert world.state.trust[("Felix", "Player")] == .75
    assert world.economy.cash["Player"] == 6 + sum(
        e.payload.get("cash_delta", {}).get("Player", 0) for e in world.ledger.events)


def test_exact_due_minute_service_is_rejected_without_partial_time_or_penalty():
    session = PompeiiSession()
    session.apply("move", {"location": "household"})
    session.apply("interact", {"action": "patronage", "recipient": "Lucius"})
    due = session.original.flags["service_due"]
    session.apply("advance", {"minutes": due - session.original.minute - 120})
    before = session.original.fidelity_state()
    queue = session.original.clock.snapshot()
    commands = copy.deepcopy(session.commands)
    with pytest.raises(ValueError, match="window|deadline|passed"):
        session.apply("interact", {"action": "service", "recipient": "Lucius"})
    assert session.original.fidelity_state() == before
    assert session.original.clock.snapshot() == queue
    assert session.commands == commands


def test_service_completed_before_deadline_is_not_later_marked_missed():
    world = PompeiiWorld()
    world.move(location="household")
    world.interact("patronage", "Lucius")
    due = world.flags["service_due"]
    world.advance(due - world.minute - 121)
    world.interact("service", "Lucius")
    assert world.minute == due - 1
    world.advance(2)
    assert world.flags["service_done"]
    assert not world.flags.get("service_missed")
    assert world.flags["reputation"] == 1
    assert world.state.trust.get(("Lucius", "Player"), .6) == .6


def test_holding_flour_elsewhere_does_not_deliver_it_at_the_deadline():
    world = PompeiiWorld()
    world.move(location="bakery")
    world.interact("accept_delivery", "Felix")
    world.move(location="thermopolium")
    world.interact("work", "Sabina")
    world.move(x=930, y=415)
    world.interact("buy", "Marcus", 4)
    world.move(location="household")
    deadline = world.economy.commitments["Player"][0]["deadline"]
    world.advance(deadline - world.minute)
    assert world.flags["quest"] == "missed"
    assert world.economy.inventory["Player"] == 4
    assert world.economy.commitments["Player"][0]["fulfilled"] == 0
    assert world.state.trust[("Felix", "Player")] < .6
