"""Question generation for Kalends-MemoryBench.

Every question's expected answer comes from the epistemic oracle (never from
world truth directly, and never from an LLM). Each question is tagged with the
evaluation dimensions it probes:

  belief        - current-belief value accuracy
  boundary      - the correct answer is "unknown"/"no" (agent never learned it);
                  answering with a value is a knowledge-boundary violation
  stale         - the agent's correct belief differs from world truth (the
                  system must report the agent's information state, not reality)
  supersession  - the agent's belief was updated at least once; the system must
                  report the latest, not an earlier value
  contradiction - the agent received conflicting values for this proposition
  false_rumor   - the correct belief is a distorted value the agent was told
  source        - source attribution of the current belief
  provenance    - direct-observation vs hearsay classification
  temporal      - when the belief was acquired
  corroboration - independent-evidence accounting (shared ancestry vs.
                  genuinely independent lines)
  alias         - the question is phrased with an alias, no structured key given

Question texts are drawn from paraphrase template families (deterministically,
keyed on seed+agent+prop) so retrieval systems cannot rely on one fixed
surface form matching the renderings.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..memory.base import Query
from ..rng import det_rand
from ..simulation import Simulation

TEMPLATES: dict[str, list[str]] = {
    "belief": [
        "What is the {pred} of the {subj}?",
        "As far as you know, what is the {pred} of the {subj}?",
        "What do you currently make of the {subj}?",
        "If someone asked about the {subj}, what {pred} would you report?",
    ],
    "heard_of": [
        "Have you heard anything about the {pred} of the {subj}?",
        "Has any word of the {subj} reached you?",
        "Do you know anything at all about the {subj}?",
    ],
    "source": [
        "Who or what is the source of what you know about the {subj}?",
        "From whom, if anyone, did you get your news of the {subj}?",
    ],
    "direct": [
        "Did you see the {subj} with your own eyes?",
        "Were you there yourself for what happened to the {subj}?",
    ],
    "learned_tick": [
        "At what hour did you learn the current {pred} of the {subj}?",
        "When did your latest news of the {subj} arrive?",
    ],
    "superseded": [
        "Has what you believe about the {subj} changed since you first learned of it?",
        "Did you ever have to revise what you thought about the {subj}?",
    ],
    "independent": [
        "Do you have more than one independent line of evidence about the {subj}?",
        "Does your knowledge of the {subj} rest on more than a single eyewitness line?",
    ],
}


@dataclass(frozen=True)
class Question:
    agent_id: str
    query: Query
    expected: str
    dims: tuple[str, ...]


def _phrase(sim: Simulation, qtype: str, agent_id: str, key: str,
            subj: str, pred: str) -> str:
    options = TEMPLATES[qtype]
    idx = int(det_rand(sim.seed, "qtpl", qtype, agent_id, key) * len(options))
    return options[idx].format(subj=subj, pred=pred)


def generate_questions(sim: Simulation) -> list[Question]:
    scenario = sim.scenario
    distorted_values = set(scenario.distortion_map.values())
    questions: list[Question] = []

    def ask(agent_id, qtype, prop, expected, dims, *, text=None,
            structured=True):
        questions.append(Question(agent_id, Query(
            qtype=qtype,
            subject=prop.subject if structured else None,
            predicate=prop.predicate if structured else None,
            text=text or _phrase(sim, qtype, agent_id, prop.key,
                                 prop.subject, prop.predicate),
        ), expected, tuple(dims)))

    for agent_id in scenario.agent_ids():
        eps = sim.epistemic[agent_id]
        for prop in scenario.propositions:
            cur = eps.belief(prop)
            heard = eps.has_heard_of(prop)
            world_value = sim.state.facts.get(prop.key)
            history_values = {e.value for e in eps.belief_history(prop)}

            # 1. Current belief value.
            expected = cur.value if cur else "unknown"
            dims = ["belief"]
            if cur is None:
                dims.append("boundary")
            else:
                if cur.value != world_value:
                    dims.append("stale")
                if eps.was_superseded(prop):
                    dims.append("supersession")
                if len(history_values) > 1:
                    dims.append("contradiction")
                if cur.value in distorted_values:
                    dims.append("false_rumor")
            ask(agent_id, "belief", prop, expected, dims)

            # 1b. Alias phrasing (text-only; measures fuzzy retrieval alone —
            # dims deliberately not inherited, see DECISIONS.md #8).
            if prop.subject in scenario.aliases:
                alias = scenario.aliases[prop.subject]
                alias_dims = ("alias", "boundary") if cur is None else ("alias",)
                ask(agent_id, "belief", prop, expected, alias_dims,
                    text=f"What is the {prop.predicate} of the {alias}?",
                    structured=False)

            # 2. Heard-of (knowledge boundary in the negative case).
            ask(agent_id, "heard_of", prop, "yes" if heard else "no",
                ("boundary",) if not heard else ("belief",))

            if cur is not None:
                src = "observed" if cur.kind == "observed" else cur.source_agent
                ask(agent_id, "source", prop, src, ("source",))
                ask(agent_id, "direct", prop,
                    "yes" if cur.kind == "observed" else "no", ("provenance",))
                ask(agent_id, "learned_tick", prop, str(cur.tick), ("temporal",))
                ask(agent_id, "independent", prop,
                    "yes" if eps.independent_origins(prop) > 1 else "no",
                    ("corroboration",))

            if heard:
                ask(agent_id, "superseded", prop,
                    "yes" if eps.was_superseded(prop) else "no",
                    ("supersession",))
    return questions
