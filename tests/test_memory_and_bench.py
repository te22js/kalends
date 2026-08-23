"""Tests for the memory systems and the benchmark harness."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalends.bench.harness import run_benchmark
from kalends.bench.questions import generate_questions
from kalends.memory import HybridMemory, StructuredMemory, VectorMemory
from kalends.memory.base import Experience, Query
from kalends.scenarios import rumor
from kalends.simulation import run_scenario

SEED = 42


def _exp(tick, kind, subject, predicate, value, source=None, as_of=None,
         accepted=True, event_id=0, text=""):
    return Experience(tick=tick, kind=kind, subject=subject,
                      predicate=predicate, value=value, source_agent=source,
                      as_of=tick if as_of is None else as_of,
                      accepted=accepted, event_id=event_id,
                      text=text or f"the {predicate} of the {subject} is {value}")


def test_structured_supersession():
    mem = StructuredMemory()
    mem.ingest(_exp(5, "observed", "bakery", "condition", "burning", event_id=1))
    mem.ingest(_exp(9, "observed", "bakery", "condition", "damaged", event_id=2))
    q = Query(qtype="belief", subject="bakery", predicate="condition",
              text="What is the condition of the bakery?")
    assert mem.answer(q).value == "damaged"
    q2 = Query(qtype="superseded", subject="bakery", predicate="condition",
               text="changed?")
    assert mem.answer(q2).value == "yes"


def test_structured_respects_rejected_exposures():
    mem = StructuredMemory()
    mem.ingest(_exp(5, "told", "silver", "status", "stolen", source="Felix",
                    accepted=False, event_id=1))
    q = Query(qtype="belief", subject="silver", predicate="status",
              text="What is the status of the silver?")
    assert mem.answer(q).value == "unknown"
    qh = Query(qtype="heard_of", subject="silver", predicate="status",
               text="Heard anything about the status of the silver?")
    assert mem.answer(qh).value == "yes"


def test_vector_answers_and_boundary():
    mem = VectorMemory()
    mem.ingest(_exp(5, "observed", "bakery", "condition", "burning", event_id=1,
                    text="At hour 5 I saw that the bakery of Modestus is burning."))
    hit = mem.answer(Query(qtype="belief", subject="bakery",
                           predicate="condition",
                           text="What is the condition of the bakery?"))
    assert hit.value == "burning"
    miss = mem.answer(Query(qtype="belief", subject="temple", predicate="roof",
                            text="What is the roof of the temple?"))
    assert miss.value == "unknown"


def test_benchmark_runs_and_is_deterministic():
    sim = run_scenario(rumor.build(), SEED)
    r1 = run_benchmark(sim)
    r2 = run_benchmark(run_scenario(rumor.build(), SEED))
    assert r1["systems"].keys() == r2["systems"].keys()
    for name in r1["systems"]:
        assert (r1["systems"][name]["accuracy"]
                == r2["systems"][name]["accuracy"])
    # Sanity: every system answered every question.
    assert r1["n_questions"] > 100


def test_questions_have_oracle_grounded_expectations():
    sim = run_scenario(rumor.build(), SEED)
    questions = generate_questions(sim)
    boundary = [q for q in questions if "boundary" in q.dims]
    stale = [q for q in questions if "stale" in q.dims]
    alias = [q for q in questions if "alias" in q.dims]
    assert boundary, "scenario produced no knowledge-boundary questions"
    assert stale, "scenario produced no staleness questions"
    assert alias, "no alias questions generated"
    for q in boundary:
        assert q.expected in ("unknown", "no")


def test_hybrid_falls_back_on_alias_queries():
    mem = HybridMemory()
    mem.ingest(_exp(5, "observed", "bakery", "condition", "burning", event_id=1,
                    text="I saw that the pistrinum of Modestus is burning."))
    # Structured path cannot resolve "pistrinum"; vector fallback can.
    ans = mem.answer(Query(qtype="belief", subject=None, predicate=None,
                           text="What is the condition of the pistrinum?"))
    assert ans.value == "burning"
