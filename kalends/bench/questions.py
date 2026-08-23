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
  false_rumor   - the correct belief is a distorted value the agent was told
  source        - source attribution of the current belief
  provenance    - direct-observation vs hearsay classification
  temporal      - when the belief was acquired
  alias         - the question is phrased with an alias, no structured key given
"""
from __future__ import annotations

from dataclasses import dataclass

from ..memory.base import Query
from ..simulation import Simulation


@dataclass(frozen=True)
class Question:
    agent_id: str
    query: Query
    expected: str
    dims: tuple[str, ...]


def generate_questions(sim: Simulation) -> list[Question]:
    scenario = sim.scenario
    distorted_values = set(scenario.distortion_map.values())
    questions: list[Question] = []

    for agent_id in scenario.agent_ids():
        eps = sim.epistemic[agent_id]
        for prop in scenario.propositions:
            subject, predicate = prop.subject, prop.predicate
            cur = eps.belief(prop)
            heard = eps.has_heard_of(prop)
            world_value = sim.state.facts.get(prop.key)

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
                if cur.value in distorted_values:
                    dims.append("false_rumor")
            questions.append(Question(agent_id, Query(
                qtype="belief", subject=subject, predicate=predicate,
                text=f"What is the {predicate} of the {subject}?",
            ), expected, tuple(dims)))

            # 1b. Alias phrasing of the same belief question (text-only).
            # Dims deliberately NOT inherited from the canonical question:
            # alias questions measure fuzzy retrieval only, so that the
            # stale/supersession dimensions stay pure of phrasing effects.
            if subject in scenario.aliases:
                alias = scenario.aliases[subject]
                alias_dims = ("alias", "boundary") if cur is None else ("alias",)
                questions.append(Question(agent_id, Query(
                    qtype="belief", subject=None, predicate=None,
                    text=f"What is the {predicate} of the {alias}?",
                ), expected, alias_dims))

            # 2. Heard-of (knowledge boundary in the negative case).
            questions.append(Question(agent_id, Query(
                qtype="heard_of", subject=subject, predicate=predicate,
                text=f"Have you heard anything about the {predicate} "
                     f"of the {subject}?",
            ), "yes" if heard else "no",
                ("boundary",) if not heard else ("belief",)))

            if cur is not None:
                # 3. Source attribution.
                src = "observed" if cur.kind == "observed" else cur.source_agent
                questions.append(Question(agent_id, Query(
                    qtype="source", subject=subject, predicate=predicate,
                    text=f"Who or what is the source of what you know about "
                         f"the {predicate} of the {subject}?",
                ), src, ("source",)))

                # 4. Direct observation vs hearsay.
                questions.append(Question(agent_id, Query(
                    qtype="direct", subject=subject, predicate=predicate,
                    text=f"Did you see the {predicate} of the {subject} "
                         f"with your own eyes?",
                ), "yes" if cur.kind == "observed" else "no", ("provenance",)))

                # 5. When acquired.
                questions.append(Question(agent_id, Query(
                    qtype="learned_tick", subject=subject, predicate=predicate,
                    text=f"At what hour did you learn the current "
                         f"{predicate} of the {subject}?",
                ), str(cur.tick), ("temporal",)))

            if heard:
                # 6. Was an earlier belief superseded?
                questions.append(Question(agent_id, Query(
                    qtype="superseded", subject=subject, predicate=predicate,
                    text=f"Has what you believe about the {predicate} of the "
                         f"{subject} changed since you first learned of it?",
                ), "yes" if eps.was_superseded(prop) else "no",
                    ("supersession",)))
    return questions
