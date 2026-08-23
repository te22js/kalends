"""The "rumor" scenario: one Pompeii district over two days (48 hourly ticks).

Ground-truth timeline (under zero jitter; actual witnesses are always computed
from actual positions, so any seed produces internally consistent truth):

  t=5   the forum fountain breaks                      (public, forum)
  t=8   fire breaks out at the bakery of Modestus      (public, bakery)
  t=10  the fire is put out; bakery damaged            (public, bakery)
  t=15  Felix steals Gaius' household silver           (PRIVATE: only Felix & Gaius)
  t=25  the fountain is repaired                       (public, forum)
  t=40  the bakery is repaired                         (public, bakery)

The interesting epistemics: few agents witness each change; news spreads by
co-located gossip; Rufus distorts what he passes on ("burned to the ground");
some agents distrust some speakers; late corrections (t=25, t=30) reach only
part of the network, leaving genuinely stale-but-epistemically-correct beliefs.
"""
from __future__ import annotations

from ..agents import AgentSpec
from ..propositions import Proposition
from ..world import WorldState
from . import Incident, Scenario

LOCATIONS = ["forum", "bakery", "thermopolium", "baths", "house_of_gaius", "temple"]

BAKERY = Proposition("bakery", "condition")
FOUNTAIN = Proposition("fountain", "status")
SILVER = Proposition("silver", "status")
MOOD = Proposition("gaius", "mood")          # late private event, spreads barely
TREASURY = Proposition("temple", "treasury")  # decoy: no event ever touches it


def build() -> Scenario:
    agents = [
        AgentSpec("Modestus", "bakery",
                  ((0, "bakery"), (20, "forum"), (22, "bakery"),
                   (31, "forum"), (34, "bakery")), chattiness=0.6),
        AgentSpec("Livia", "house_of_gaius",
                  ((7, "bakery"), (9, "forum"), (16, "house_of_gaius"),
                   (31, "forum"), (40, "house_of_gaius")), chattiness=0.6),
        AgentSpec("Quintus", "thermopolium",
                  ((7, "bakery"), (11, "thermopolium"), (18, "baths"),
                   (21, "thermopolium"), (30, "forum"), (36, "thermopolium")),
                  chattiness=0.5),
        AgentSpec("Gaius", "house_of_gaius",
                  ((8, "forum"), (14, "house_of_gaius"), (26, "forum"),
                   (38, "house_of_gaius")), chattiness=0.3),
        AgentSpec("Felix", "thermopolium",
                  ((9, "forum"), (14, "house_of_gaius"), (16, "thermopolium"),
                   (28, "baths"), (33, "thermopolium")), chattiness=0.1),
        AgentSpec("Marcus", "temple",
                  ((7, "forum"), (13, "baths"), (19, "temple"),
                   (30, "forum"), (37, "temple")), chattiness=0.5),
        AgentSpec("Julia", "baths",
                  ((8, "forum"), (12, "baths"), (24, "forum"),
                   (29, "baths")), chattiness=0.5),
        AgentSpec("Sabina", "temple",
                  ((6, "temple"), (10, "forum"), (17, "temple"),
                   (32, "forum"), (41, "temple")), chattiness=0.7),
        AgentSpec("Celer", "thermopolium",
                  ((7, "forum"), (12, "thermopolium"), (29, "bakery"),
                   (33, "forum"), (40, "thermopolium")), chattiness=0.5),
        AgentSpec("Rufus", "thermopolium",
                  ((6, "forum"), (15, "baths"), (22, "thermopolium"),
                   (27, "forum"), (42, "thermopolium")),
                  chattiness=0.8, distort_p=0.5),
        AgentSpec("Aemilia", "house_of_gaius",
                  ((9, "forum"), (15, "baths"), (20, "house_of_gaius"),
                   (28, "forum"), (39, "house_of_gaius")), chattiness=0.5),
        AgentSpec("Decimus", "baths",
                  ((5, "baths"), (11, "forum"), (18, "baths"),
                   (26, "thermopolium"), (35, "baths")), chattiness=0.4),
        AgentSpec("Vibia", "temple",
                  ((8, "temple"), (13, "forum"), (21, "temple"),
                   (31, "baths"), (43, "temple")), chattiness=0.5),
        AgentSpec("Holconius", "temple",
                  ((4, "forum"), (16, "temple"), (25, "forum"),
                   (36, "temple")), chattiness=0.7),
    ]

    initial = WorldState(
        tick=-1,
        agent_locations={a.agent_id: a.home for a in agents},
        facts={"bakery.condition": "intact",
               "fountain.status": "flowing",
               "silver.status": "safe"},
        trust={
            # (listener, speaker) -> trust; unlisted pairs default to 0.5
            ("Gaius", "Felix"): 0.1,     # Gaius distrusts the man he suspects
            ("Modestus", "Rufus"): 0.2,  # the baker knows Rufus exaggerates
            ("Julia", "Rufus"): 0.2,
            ("Sabina", "Felix"): 0.2,
        },
    )

    incidents = [
        Incident(5, "incident", "forum", ("Decimus",), FOUNTAIN, "broken"),
        Incident(8, "incident", "bakery", ("Modestus",), BAKERY, "burning"),
        Incident(10, "state_change", "bakery", ("Modestus",), BAKERY, "damaged"),
        Incident(15, "incident", "house_of_gaius", ("Felix", "Gaius"),
                 SILVER, "stolen", scope="private"),
        Incident(25, "state_change", "forum", ("Decimus",), FOUNTAIN, "flowing"),
        # Late correction: Modestus reopens his repaired bakery with only 8
        # ticks left — the news reaches only part of the network, leaving
        # genuinely stale (but epistemically correct) beliefs elsewhere.
        Incident(40, "state_change", "bakery", ("Modestus",), BAKERY, "repaired"),
        # Very late private event: Gaius discovers the theft's aftermath at
        # home. Almost no time to spread -> guaranteed knowledge boundaries.
        Incident(45, "incident", "house_of_gaius", ("Gaius",),
                 MOOD, "furious", scope="private"),
    ]

    return Scenario(
        name="rumor",
        n_ticks=48,
        locations=LOCATIONS,
        agents=agents,
        initial_state=initial,
        incidents=incidents,
        # TREASURY is a decoy: no event ever concerns it, so every question
        # about it has the oracle answer "unknown" — a guaranteed
        # knowledge-boundary probe (and a similarity trap for vector memory,
        # since "temple" appears in movement episodes).
        propositions=[BAKERY, FOUNTAIN, SILVER, MOOD, TREASURY],
        aliases={"bakery": "pistrinum", "fountain": "nymphaeum",
                 "silver": "lararium silver"},
        distortion_map={
            "burning": "burned to the ground",
            "damaged": "burned to the ground",
            "stolen": "stolen by a curse",
        },
        statements={
            "bakery.condition": "the bakery of Modestus is {value}",
            "fountain.status": "the fountain in the forum is {value}",
            "silver.status": "the household silver of Gaius is {value}",
            "gaius.mood": "Gaius the householder is {value}",
        },
        alias_statements={
            "bakery.condition": "the pistrinum of Modestus is {value}",
            "fountain.status": "the nymphaeum in the forum is {value}",
            "silver.status": "the lararium silver of Gaius is {value}",
        },
    )
