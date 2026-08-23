"""MemoryBench harness: replay experience streams into each memory system,
answer the oracle-generated questions, and score exactly.

Scoring is exact string match (case-insensitive). "unknown" is always a legal
answer but is only *correct* when the oracle says the agent has no basis for a
belief — saying "unknown" about something the agent does know is a miss, and
answering with a value the agent has no basis for is a boundary violation.
"""
from __future__ import annotations

from collections import defaultdict

from ..memory import MEMORY_SYSTEMS
from ..simulation import Simulation
from .questions import Question, generate_questions


def _norm(s: str | None) -> str:
    return (s or "unknown").strip().lower()


def run_benchmark(sim: Simulation,
                  system_names: list[str] | None = None) -> dict:
    system_names = system_names or list(MEMORY_SYSTEMS)
    questions = generate_questions(sim)
    results: dict = {"n_questions": len(questions), "systems": {}}

    for name in system_names:
        cls = MEMORY_SYSTEMS[name]
        # One memory instance per agent, fed only that agent's experiences.
        memories = {}
        for agent_id in sim.scenario.agent_ids():
            mem = cls()
            for exp in sim.experiences[agent_id]:
                mem.ingest(exp)
            memories[agent_id] = mem

        per_dim_total: dict[str, int] = defaultdict(int)
        per_dim_correct: dict[str, int] = defaultdict(int)
        per_qtype_total: dict[str, int] = defaultdict(int)
        per_qtype_correct: dict[str, int] = defaultdict(int)
        boundary_total = boundary_violations = 0
        n_correct = 0
        # Epistemic precision/recall over belief-value questions:
        #   precision: of the values the system asserted, how many were the
        #              agent's actual (normative) belief?
        #   recall:    of the beliefs the agent actually held, how many did
        #              the system assert correctly?
        asserted = asserted_correct = holds_belief = 0
        failures: list[dict] = []

        for q in questions:
            ans = memories[q.agent_id].answer(q.query)
            correct = _norm(ans.value) == _norm(q.expected)
            n_correct += correct
            per_qtype_total[q.query.qtype] += 1
            per_qtype_correct[q.query.qtype] += correct
            for dim in q.dims:
                per_dim_total[dim] += 1
                per_dim_correct[dim] += correct
            if q.query.qtype == "belief":
                if q.expected != "unknown":
                    holds_belief += 1
                if _norm(ans.value) != "unknown":
                    asserted += 1
                    if correct and q.expected != "unknown":
                        asserted_correct += 1
            if "boundary" in q.dims:
                boundary_total += 1
                # Violation: asserting knowledge the agent cannot have.
                if _norm(ans.value) not in ("unknown", "no"):
                    boundary_violations += 1
            if not correct and len(failures) < 40:
                failures.append({
                    "agent": q.agent_id, "qtype": q.query.qtype,
                    "text": q.query.text, "expected": q.expected,
                    "got": ans.value, "dims": list(q.dims),
                })

        results["systems"][name] = {
            "accuracy": n_correct / len(questions),
            "n_correct": n_correct,
            "by_dimension": {
                d: {"accuracy": per_dim_correct[d] / per_dim_total[d],
                    "n": per_dim_total[d]}
                for d in sorted(per_dim_total)
            },
            "by_qtype": {
                t: {"accuracy": per_qtype_correct[t] / per_qtype_total[t],
                    "n": per_qtype_total[t]}
                for t in sorted(per_qtype_total)
            },
            "boundary_violation_rate": (
                boundary_violations / boundary_total if boundary_total else 0.0),
            "epistemic_precision": (asserted_correct / asserted
                                    if asserted else 1.0),
            "epistemic_recall": (asserted_correct / holds_belief
                                 if holds_belief else 1.0),
            "sample_failures": failures,
        }
    return results


def format_table(results: dict) -> str:
    """Plain-text comparison table for the CLI."""
    systems = list(results["systems"])
    dims = sorted({d for s in systems
                   for d in results["systems"][s]["by_dimension"]})
    rows = []
    header = ["dimension (n)"] + systems
    for d in dims:
        n = results["systems"][systems[0]]["by_dimension"][d]["n"]
        row = [f"{d} ({n})"]
        for s in systems:
            row.append(f"{results['systems'][s]['by_dimension'][d]['accuracy']:.2f}")
        rows.append(row)
    rows.append(["OVERALL"] + [
        f"{results['systems'][s]['accuracy']:.2f}" for s in systems])
    rows.append(["boundary violations"] + [
        f"{results['systems'][s]['boundary_violation_rate']:.2f}"
        for s in systems])
    rows.append(["epistemic precision"] + [
        f"{results['systems'][s]['epistemic_precision']:.2f}" for s in systems])
    rows.append(["epistemic recall"] + [
        f"{results['systems'][s]['epistemic_recall']:.2f}" for s in systems])

    widths = [max(len(r[i]) for r in [header] + rows)
              for i in range(len(header))]
    def fmt(row):
        return "  ".join(c.ljust(w) for c, w in zip(row, widths))
    lines = [fmt(header), fmt(["-" * w for w in widths])]
    lines += [fmt(r) for r in rows]
    return "\n".join(lines)
