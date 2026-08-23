"""Parameterized scenario generator: random worlds from a typed config.

This removes the single hand-designed world as the only test bed. Every
knob that the experiment suite varies is an explicit field of WorldConfig;
configs serialize to JSON and are recorded next to every result file.

Entity naming is deliberately adjective+noun ("old bakery", "north gate"):
subjects share tokens with *other* subjects ("old bakery" vs "new bakery"),
which produces natural hard negatives for similarity retrieval instead of
sanitized distinct symbols. The Pompeii skin is optional flavor; the machinery
is domain-general (§24 of the brief).
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field

from ..agents import AgentSpec
from ..propositions import Proposition
from ..rng import det_choice, det_rand, det_randint, det_shuffle
from ..world import WorldState
from . import Incident, Scenario

AGENT_NAMES = [
    "Modestus", "Livia", "Quintus", "Gaius", "Felix", "Marcus", "Julia",
    "Sabina", "Celer", "Rufus", "Aemilia", "Decimus", "Vibia", "Holconius",
    "Primus", "Secunda", "Tertius", "Quarta", "Faustus", "Drusilla",
    "Ampliatus", "Restituta", "Successus", "Fortunata", "Cerialis", "Iucundus",
    "Sabinus", "Paulina", "Crescens", "Vitalis", "Ianuaria", "Proculus",
]

ADJECTIVES = ["old", "new", "north", "south", "east", "west", "great", "small",
              "red", "white", "upper", "lower", "inner", "outer", "public", "hidden"]
NOUNS = ["bakery", "fountain", "temple", "gate", "well", "shrine", "market",
         "warehouse", "workshop", "garden", "cistern", "tavern"]
PREDICATES = ["condition", "status", "state"]
# Per-proposition value chains are drawn from this pool (first value = initial).
VALUE_POOL = ["intact", "broken", "burning", "damaged", "repaired", "closed",
              "open", "flooded", "restored", "abandoned", "guarded", "looted"]
ALIAS_WORDS = ["pistrinum", "nymphaeum", "aedicula", "horreum", "taberna",
               "porticus", "macellum", "lacus", "fauces", "compluvium"]
FILLER_PHRASES = (
    "I haggled over the price of fish",
    "I complained about the heat",
    "I watched a dog chase a cart",
    "I repaired a sandal strap",
    "I shared bread with a neighbour",
    "I listened to a street musician",
    "I argued about the games",
    "I counted my coins twice",
)


@dataclass(frozen=True)
class WorldConfig:
    """Every experimental knob, with the defaults used by the core suite."""
    name: str = "generated"
    n_agents: int = 14
    n_locations: int = 6
    n_ticks: int = 48
    n_props: int = 4              # propositions that actually receive events
    n_decoys: int = 1             # propositions no event ever touches
    changes_min: int = 1          # ground-truth value changes per proposition
    changes_max: int = 3
    private_event_p: float = 0.15   # chance an incident is private (actors only)
    chattiness_min: float = 0.2
    chattiness_max: float = 0.8
    distorter_frac: float = 0.15  # fraction of agents who distort when telling
    distort_p: float = 0.5        # their per-tell distortion probability
    distrust_pair_frac: float = 0.08  # fraction of (listener,speaker) pairs with low trust
    jitter_p: float = 0.15
    alias_frac: float = 0.5       # fraction of subjects that have an alias
    alias_p: float = 0.3
    gossip_recency: int = 12
    schedule_blocks: int = 4      # movement blocks per agent per run
    irrelevant_memory_rate: float = 0.0
    late_private_event: bool = True   # add a t=n_ticks-3 private event (boundary probe)

    def to_json(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_json(d: dict) -> "WorldConfig":
        return WorldConfig(**d)


def generate(config: WorldConfig, seed: int) -> Scenario:
    """Deterministic world from (config, seed). All draws are context-keyed."""
    c, s = config, seed
    agent_names = [AGENT_NAMES[i % len(AGENT_NAMES)]
                   + ("" if i < len(AGENT_NAMES) else f"_{i // len(AGENT_NAMES)}")
                   for i in range(c.n_agents)]
    locations = [f"{ADJECTIVES[i % len(ADJECTIVES)]}_{NOUNS[(i * 7 + 3) % len(NOUNS)]}"
                 for i in range(c.n_locations)]

    # --- subjects: adjective+noun pairs, unique, with shared-token collisions.
    subjects = []
    used = set()
    i = 0
    while len(subjects) < c.n_props + c.n_decoys:
        adj = ADJECTIVES[int(det_rand(s, "sadj", i) * len(ADJECTIVES))]
        noun = NOUNS[int(det_rand(s, "snoun", i) * len(NOUNS))]
        name = f"{adj} {noun}"
        if name not in used:
            used.add(name)
            subjects.append(name)
        i += 1
    props = [Proposition(subj, PREDICATES[k % len(PREDICATES)])
             for k, subj in enumerate(subjects[:c.n_props])]
    decoys = [Proposition(subj, PREDICATES[k % len(PREDICATES)])
              for k, subj in enumerate(subjects[c.n_props:])]

    # --- agents with schedules.
    agents = []
    for idx, name in enumerate(agent_names):
        home = det_choice(locations, s, "home", name)
        blocks = sorted(
            (det_randint(1, c.n_ticks - 1, s, "bstart", name, b),
             det_choice(locations, s, "bloc", name, b))
            for b in range(c.schedule_blocks))
        chattiness = (c.chattiness_min
                      + det_rand(s, "chat", name)
                      * (c.chattiness_max - c.chattiness_min))
        distort = (c.distort_p
                   if det_rand(s, "isdist", name) < c.distorter_frac else 0.0)
        agents.append(AgentSpec(name, home, tuple(blocks),
                                chattiness=round(chattiness, 3),
                                distort_p=distort))

    # --- trust: default 0.5, some low-trust directed pairs.
    trust = {}
    for a in agent_names:
        for b in agent_names:
            if a != b and det_rand(s, "trust", a, b) < c.distrust_pair_frac:
                trust[(a, b)] = 0.1

    # --- ground-truth timelines per proposition.
    incidents = []
    initial_facts = {}
    for k, prop in enumerate(props):
        n_changes = det_randint(c.changes_min, c.changes_max, s, "nch", prop.key)
        values = det_shuffle(VALUE_POOL, s, "vals", prop.key)
        initial_facts[prop.key] = values[0]
        ticks = sorted({det_randint(2, c.n_ticks - 5, s, "ctick", prop.key, j)
                        for j in range(n_changes)})
        location = det_choice(locations, s, "iloc", prop.key)
        for j, tick in enumerate(ticks):
            private = det_rand(s, "priv", prop.key, j) < c.private_event_p
            if private:
                a1 = det_choice(agent_names, s, "pactor1", prop.key, j)
                a2 = det_choice(agent_names, s, "pactor2", prop.key, j)
                actors = tuple(sorted({a1, a2}))
            else:
                actors = (det_choice(agent_names, s, "actor", prop.key, j),)
            incidents.append(Incident(
                tick=tick, etype="incident" if j == 0 else "state_change",
                location=location, actors=actors,
                prop=prop, value=values[j + 1],
                scope="private" if private else "public"))
    for prop in decoys:
        initial_facts[prop.key] = "unremarked"
    late_prop = None
    if c.late_private_event:
        # Guaranteed knowledge-boundary probe: a private event 3 ticks before
        # the end — almost nobody can learn of it in time.
        late_prop = Proposition("secret cache", "whereabouts")
        initial_facts[late_prop.key] = "hidden"
        incidents.append(Incident(
            tick=c.n_ticks - 3, etype="incident",
            location=det_choice(locations, s, "lloc"),
            actors=(det_choice(agent_names, s, "lactor"),),
            prop=late_prop, value="uncovered", scope="private"))

    incidents.sort(key=lambda inc: (inc.tick, inc.prop.key))
    all_props = props + decoys + ([late_prop] if late_prop else [])

    # --- language: statements, aliases, distortion.
    statements, alias_statements, aliases = {}, {}, {}
    for k, prop in enumerate(all_props):
        statements[prop.key] = f"the {prop.subject} is {{value}}"
        if det_rand(s, "hasalias", prop.key) < c.alias_frac:
            alias = ALIAS_WORDS[k % len(ALIAS_WORDS)]
            aliases[prop.subject] = alias
            alias_statements[prop.key] = f"the {alias} is {{value}}"
    distortion_map = {v: f"utterly {v}" for v in VALUE_POOL}

    return Scenario(
        name=c.name,
        n_ticks=c.n_ticks,
        locations=locations,
        agents=agents,
        initial_state=WorldState(tick=-1,
                                 agent_locations={a.agent_id: a.home for a in agents},
                                 facts=initial_facts, trust=trust),
        incidents=incidents,
        propositions=all_props,
        aliases=aliases,
        distortion_map=distortion_map,
        statements=statements,
        alias_statements=alias_statements,
        jitter_p=c.jitter_p,
        alias_p=c.alias_p,
        gossip_recency=c.gossip_recency,
        irrelevant_memory_rate=c.irrelevant_memory_rate,
        filler_phrases=FILLER_PHRASES,
    )


def save_config(config: WorldConfig, path: str) -> None:
    with open(path, "w") as f:
        json.dump(config.to_json(), f, indent=2)
