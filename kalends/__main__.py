"""Kalends CLI.

  kalends simulate rumor --seed 42 [--out trace.json]
  kalends benchmark [--seed 42] [--systems vector,structured,hybrid] [--out results.json]
  kalends explain --agent Livia --prop bakery.condition [--seed 42]
"""
from __future__ import annotations

import argparse
import json
import sys

from .bench.harness import format_table, run_benchmark
from .propositions import Proposition
from .scenarios import rumor
from .simulation import run_scenario
from .trace import build_trace, write_trace

SCENARIOS = {"rumor": rumor.build}


def _sim(scenario_name: str, seed: int):
    if scenario_name not in SCENARIOS:
        sys.exit(f"unknown scenario: {scenario_name} (have: {list(SCENARIOS)})")
    return run_scenario(SCENARIOS[scenario_name](), seed)


def cmd_simulate(args) -> None:
    sim = _sim(args.scenario, args.seed)
    trace = build_trace(sim)
    print(f"scenario={trace['scenario']} seed={trace['seed']} "
          f"ticks={trace['n_ticks']} events={trace['n_events']}")
    print(f"ledger hash: {trace['ledger_hash'][:16]}…")
    print(f"world facts at end: {trace['world_facts']}")
    print()
    print(f"{'agent':<10} {'location':<15} beliefs (★=stale vs world)")
    for agent_id, info in trace["agents"].items():
        parts = []
        for key, b in info["beliefs"].items():
            if b is None:
                parts.append(f"{key}=?")
            else:
                star = "★" if b["stale_vs_world"] else ""
                parts.append(f"{key}={b['value']}{star}")
        print(f"{agent_id:<10} {info['final_location']:<15} {'  '.join(parts)}")
    if args.out:
        write_trace(sim, args.out)
        print(f"\ntrace written to {args.out}")


def cmd_benchmark(args) -> None:
    sim = _sim(args.scenario, args.seed)
    systems = args.systems.split(",") if args.systems else None
    results = run_benchmark(sim, systems)
    print(f"Kalends-MemoryBench v0 — scenario={args.scenario} seed={args.seed} "
          f"questions={results['n_questions']}")
    print()
    print(format_table(results))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nfull results written to {args.out}")


def cmd_explain(args) -> None:
    sim = _sim(args.scenario, args.seed)
    subject, predicate = args.prop.split(".", 1)
    prop = Proposition(subject, predicate)
    eps = sim.epistemic.get(args.agent)
    if eps is None:
        sys.exit(f"unknown agent: {args.agent}")
    cur = eps.belief(prop)
    world = sim.state.facts.get(prop.key)
    print(f"world truth:            {prop.key} = {world}")
    if cur is None:
        heard = eps.belief_history(prop)
        if heard:
            print(f"{args.agent} holds no accepted belief, but heard "
                  f"{len(heard)} distrusted claim(s).")
        else:
            print(f"{args.agent} has never received any information about "
                  f"{prop.key}.")
        return
    stale = " (STALE vs world)" if cur.value != world else ""
    print(f"{args.agent} believes:  {prop.key} = {cur.value}{stale}")
    print(f"acquired at hour {cur.tick}, information originated hour {cur.as_of}")
    print("provenance:")
    for i, step in enumerate(cur.provenance.chain()):
        print(f"  {'  ' * i}└─ {step}")
    history = eps.belief_history(prop)
    if len(history) > 1:
        print(f"full exposure history ({len(history)}):")
        for e in history:
            mark = "accepted" if e.accepted else "REJECTED (distrusted/older)"
            via = "saw directly" if e.kind == "observed" else f"told by {e.source_agent}"
            print(f"  hour {e.tick:>2}: {e.value!r} — {via} — {mark}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="kalends")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("simulate", help="run a scenario deterministically")
    p.add_argument("scenario", nargs="?", default="rumor")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--out", help="write full JSON trace here")
    p.set_defaults(func=cmd_simulate)

    p = sub.add_parser("benchmark", help="run Kalends-MemoryBench v0")
    p.add_argument("scenario", nargs="?", default="rumor")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--systems", help="comma-separated: vector,structured,hybrid")
    p.add_argument("--out", help="write full JSON results here")
    p.set_defaults(func=cmd_benchmark)

    p = sub.add_parser("explain", help="why does an agent believe P?")
    p.add_argument("--scenario", default="rumor")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--agent", required=True)
    p.add_argument("--prop", required=True, help="e.g. bakery.condition")
    p.set_defaults(func=cmd_explain)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
