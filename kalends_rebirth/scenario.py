"""Authored fictional contracts in a source-labelled Pompeian setting.

Wax tablets and commercial accounts are attested; this cast, cart, prices,
priority agreement and dispute are explicitly invented game material.
"""
from __future__ import annotations

SCENARIO_VERSION = 1
NEW_ACTIONS = frozenset({
    "hear_dispute", "examine_receipt", "examine_tablet", "verify_cart", "mediate",
    "support_market", "guarantee_household", "return_service", "reconcile",
    "accept_commission", "fulfill_commission", "decline_dispute", "reflect",
})

PERSONALITY = {
    "Sabina": {"voice":"plainspoken, warm, impatient with waste", "long_term":"Keep the food counter independent",
        "medium_term":"Have enough flour for customers without another household's permission",
        "opening":"Six sacks, two buyers, and somehow my bowls are the ones left empty. I paid Marcus. Ask him what changed.",
        "role":"I run the counter. A good meal buys me a returning customer; a household's promise does not."},
    "Marcus": {"voice":"dry, precise, protective of his margin", "long_term":"Keep a solvent trading business",
        "medium_term":"Release the cart without paying every disputed charge himself",
        "opening":"The order was ready at first light. That is what my message said. Ready is not the same as carried to your door.",
        "role":"I buy, hold and sell flour. Every sack is somebody's coin before it becomes somebody's bread."},
    "Lucius": {"voice":"measured, formal, attentive to obligations", "long_term":"Remain a dependable steward of the household",
        "medium_term":"Protect the household's claim and recruit reliable help",
        "opening":"Four sacks were reserved for this house. I will hear terms, not an accusation delivered on someone else's word.",
        "role":"I account for this household's stores and service. My own freedom does not make its obligations disappear."},
    "Dama": {"voice":"observant, economical, careful about authority", "long_term":"Fulfil assigned duties without becoming the convenient person to blame",
        "medium_term":"Carry the steward's delivery instructions accurately",
        "opening":"I was told to repeat the quantity, not argue about it. If you want the instructions, ask plainly.",
        "role":"I carry household instructions. I can repeat the delivery terms I was sent to carry; I cannot promise you the household's money."},
    "Felix": {"voice":"practical, hospitable, worried about tomorrow's work", "long_term":"Keep the bread counter viable",
        "medium_term":"Keep enough flour and dependable people for tomorrow",
        "opening":"A cart can stand still all morning while people make speeches. Someone must still bake.",
        "role":"I bake and sell bread. You will learn more about a promise by keeping one than by praising it."},
    "Chreste": {"voice":"direct, wary, attentive to the work itself", "long_term":"Get through assigned workshop work with dependable help",
        "medium_term":"Finish today's cloth work without taking blame for another person's bargain",
        "opening":"If you want work, there is work here. The household pays for extra help. Do not mistake that for my freedom to leave.",
        "role":"I work in the fullery under constraint. Help is useful; grand promises made over my head are less so."},
}

COMMISSION_SPECS = {
    "Sabina": {"id":"market", "title":"Keep the counter open", "kind":"goods", "quantity":2,"reward":5,"duration":360,
        "access":"market", "description":"Bring two flour units before this order closes. Five coins on delivery; no advance."},
    "Marcus": {"id":"broker", "title":"A report worth buying", "kind":"evidence", "quantity":1,"reward":3,"duration":240,
        "access":"broker", "description":"Obtain a new direct dispatch inspection after accepting this commission. Three coins for a fresh checked report."},
    "Lucius": {"id":"household", "title":"The steward's next account", "kind":"goods", "quantity":3,"reward":8,"duration":480,
        "access":"household", "description":"Bring three flour units before the household account closes. Eight coins on delivery; service must already be settled."},
}

HISTORICAL_DISCLAIMER = (
    "79 CE; exact eruption day debated. Attested building anchors, reconstructed screen geography, "
    "fictional people and private bargains. The cart dispute is not an attested historical case."
)
