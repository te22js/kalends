"""Automatic failure collection and categorization.

For every wrong answer we reconstruct WHY it is wrong against the agent's
exposure history, and bin it into a named failure mode:

  boundary_hallucination - asserted a value the agent has no basis for
  stale_retrieval        - returned an older value from the agent's own history
  distrust_confusion     - returned a value the agent heard but rejected
  phantom_value          - returned a value never present in the agent's
                           history at all (cross-proposition leakage)
  missed_knowledge       - said unknown although the agent holds the belief
  alias_miss             - failed only on the alias phrasing
  source_confusion       - wrong source attribution
  temporal_error         - wrong acquisition time
  classification_error   - wrong yes/no on direct/superseded/independent/heard
"""
from __future__ import annotations

from collections import Counter

from ..memory import MEMORY_SYSTEMS
from ..simulation import Simulation
from .questions import Question, generate_questions


def _categorize(q: Question, got: str, history_values: list[str],
                rejected_values: set[str], expected: str) -> str:
    got_n = got.strip().lower()
    exp_n = expected.strip().lower()
    if "alias" in q.dims and got_n == "unknown":
        return "alias_miss"
    if q.query.qtype in ("belief",):
        if exp_n in ("unknown",) and got_n not in ("unknown", "no"):
            return "boundary_hallucination"
        if got_n == "unknown":
            return "missed_knowledge"
        if got_n in rejected_values:
            return "distrust_confusion"
        if got_n in [v.lower() for v in history_values]:
            return "stale_retrieval"
        return "phantom_value"
    if q.query.qtype == "heard_of":
        return ("boundary_hallucination" if exp_n == "no"
                else "classification_error")
    if q.query.qtype == "source":
        return "source_confusion"
    if q.query.qtype == "learned_tick":
        return "temporal_error"
    return "classification_error"


def collect_failures(sim: Simulation, system_names: list[str] | None = None,
                     max_examples_per_cat: int = 3) -> dict:
    system_names = system_names or list(MEMORY_SYSTEMS)
    questions = generate_questions(sim)
    report: dict = {"systems": {}}
    for name in system_names:
        cls = MEMORY_SYSTEMS[name]
        memories = {}
        for agent_id in sim.scenario.agent_ids():
            mem = cls()
            for exp in sim.experiences[agent_id]:
                mem.ingest(exp)
            memories[agent_id] = mem

        counts: Counter = Counter()
        examples: dict[str, list[dict]] = {}
        n_wrong = 0
        for q in questions:
            ans = memories[q.agent_id].answer(q.query)
            got = (ans.value or "unknown")
            if got.strip().lower() == q.expected.strip().lower():
                continue
            n_wrong += 1
            eps = sim.epistemic[q.agent_id]
            key = (f"{q.query.subject}.{q.query.predicate}"
                   if q.query.subject else None)
            history = []
            rejected = set()
            if key and key in eps.exposures:
                for e in eps.exposures[key]:
                    history.append(e.value)
                    if not e.accepted:
                        rejected.add(e.value.lower())
            cat = _categorize(q, got, history, rejected, q.expected)
            counts[cat] += 1
            if len(examples.setdefault(cat, [])) < max_examples_per_cat:
                examples[cat].append({
                    "agent": q.agent_id, "qtype": q.query.qtype,
                    "question": q.query.text, "expected": q.expected,
                    "got": got, "dims": list(q.dims),
                    "exposure_history": [
                        {"tick": e.tick, "value": e.value, "kind": e.kind,
                         "from": e.source_agent,
                         "accepted": e.accepted}
                        for e in (eps.exposures.get(key, []) if key else [])],
                })
        report["systems"][name] = {
            "n_questions": len(questions), "n_wrong": n_wrong,
            "categories": dict(counts.most_common()),
            "examples": examples,
        }
    return report
