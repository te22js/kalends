"""Presentation follows actual delivery without rewriting its recorded history."""
import copy

from kalends_rebirth.scenario import PERSONALITY
from kalends_rebirth.world import RebirthWorld


def test_market_delivery_updates_sabinas_greeting_and_arrival_objective_read_only():
    world=RebirthWorld();committed_objectives=[];on_task=world.on_task
    assert world.context("Sabina")["greeting"]["text"]==PERSONALITY["Sabina"]["opening"]

    def observe_delivery(task):
        if task["kind"]=="rb_cart_delivery":committed_objectives.append(world.objective())
        return on_task(task)

    world.on_task=observe_delivery
    world.interact("support_market","Sabina")
    world.on_task=on_task
    assert committed_objectives[0]["title"]=="The cart is moving"
    assert world.arc["stage"]=="resolved" and not world.arc["followup_ready"]
    delivery=next(e for e in world.ledger.events if e.payload["category"]=="rb_resolution")
    assert delivery.payload["allocation"]=={"Sabina":4,"Felix":2}
    before=(world.ledger.to_json(),copy.deepcopy(world.fidelity_state()))
    context=world.context("Sabina");objective=world.objective()
    assert "Four sacks arrived here" in context["greeting"]["text"]
    assert "bowls are the ones left empty" not in context["greeting"]["text"]
    assert objective["title"]=="The cart has arrived" and objective["status"]=="waiting"
    assert "reached the agreed buyers" in objective["description"]
    assert (world.ledger.to_json(),world.fidelity_state())==before
