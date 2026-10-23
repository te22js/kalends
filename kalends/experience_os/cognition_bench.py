"""Controlled exploratory cognition study on the actual Commons domain plugin.

Policies see only a detached, legitimately received Player observation stream.
The harness may configure hidden hardware transitions; minds cannot query them.
Inspection, promises, allocation, settlement, cash and relationships use the
existing CoordinationWorld rules. This is not a validated human skill measure.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import sys
import time

from kalends.memory.base import Experience
from kalends.memory.retrieval import BM25Index
from kalends_rebirth.minds import (
    ActionOption, AgentMind, BeliefCondition, Episode, Goal, MindConfig,
    SocialCondition, SocialSignal,
)
from .commons import CoordinationWorld, TEAMS
from .compiler import ExperienceCompilerV1
from .minds import PersistentMind


ROOT = Path(__file__).resolve().parents[2]
FAMILIES = ("outdated", "contradictory", "shared_source", "strategic_communication",
    "long_absence", "important_promise", "changed_goals", "forget_recover", "delayed_consequence")
POLICIES = ("recency", "salience", "goal", "hybrid")
ARMS = tuple(f"{generation}_{policy}" for generation in ("v2", "v3") for policy in POLICIES) + ("bm25_fifo",)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


class BM25BoundedMind(AgentMind):
    """FIFO retained episodes, lexical BM25 context, unchanged typed planner.

    This is a lexical baseline, not dense embedding retrieval.  It uses the
    original repository BM25 implementation, rebuilding over the retained pool
    only. The context limit is shared across all options, just as for V2/V3.
    """

    def _retrieve(self, now, *, keys=(), social=()):
        query = " ".join(" ".join(pair) for pair in list(keys) + list(social)).replace("_", " ")
        index, originals = BM25Index(), {}
        for record in self._episodes:
            if not record.get("accepted", True):
                continue
            originals[record["event_id"]] = record
            index.add(Experience(record["observed_at"], record["kind"], record.get("subject"), record.get("predicate"),
                record.get("value"), record.get("source_agent"), record.get("as_of", record["observed_at"]),
                record.get("accepted", True), record["event_id"], record["text"] + " " + " ".join(
                    str(record.get(key) or "") for key in ("subject", "predicate", "value")),
                claimed_origin_event=record.get("origin_event"), claimed_origin_observer=record.get("origin_observer")))
        return [originals[e.event_id] for _, e in index.search(query, self.config.context_records)]


class ControlledCoordinationWorld(CoordinationWorld):
    """Keep domain rules; suppress background policies for matched test input."""

    def __init__(self, spec):
        self.player_stream = []
        super().__init__(spec)

    def _decide(self, actor):
        # All arms receive the same authored opportunity stream. Autonomous
        # competing policies would otherwise alter observations before testing.
        return None

    def _emit(self, *args, **kwargs):
        event = super()._emit(*args, **kwargs)
        if event.event_id not in self.visible.get("Player", set()):
            return event
        payload = event.payload
        direct = payload.get("prop") == ["observatory", "condition"]
        signals = ()
        if payload.get("category") == "promise" and "Player" in event.actors:
            promises = json.loads(payload["value"])
            signals = tuple(SocialSignal(a, "obligation", promises[a]) for a in event.actors if a in promises)
        self.player_stream.append(Episode(event.event_id, "Player", event.tick,
            "observed" if direct else "episodic", payload["title"],
            "observatory" if direct else None, "condition" if direct else None,
            str(payload["value"]) if direct else None, event.tick,
            origin_event=event.event_id, origin_observer="Player" if direct else None,
            participants=tuple(event.actors), salience=.95 if signals else .65 if direct else .12,
            goal_tags=("obligation",) if signals else ("condition",) if direct else (), social_signals=signals))
        return event

    def on_task(self, task):
        if task["kind"] == "bench_condition_transition":
            self.emit("condition", "A delayed hardware transition reaches the systems team", ("team_b",), scope="private",
                prop=["observatory", "condition"], value=task["data"]["value"])
            return
        super().on_task(task)

    def advance_to(self, minute):
        self.clock.advance(minute, self.on_task, mode="compress")

    def condition(self, minute, value):
        self.advance_to(minute)
        return self.emit("condition", "The systems team measures the instrument condition", ("team_b",), scope="private",
            prop=["observatory", "condition"], value=value)

    def receive(self, minute, source):
        """Share an actually observed source through the actual authorized action.

        The source object is communication content held by the scripted speaker,
        not a later oracle lookup by the evaluator. The world validates that the
        speaker observed this condition record before accepting the sharing.
        """
        self.advance_to(minute)
        event = self.execute({"action": "share", "actor": "team_b", "recipient": "Player", "event_id": source.event_id})
        self.player_stream[-1] = Episode(event.event_id, "Player", minute, "told",
            f"The observatory condition was {source.payload['value']} at minute {source.tick}; team_b shares the dated systems record.",
            "observatory", "condition", source.payload["value"], source.tick,
            source_agent="team_b", origin_event=source.event_id, origin_observer="team_b",
            participants=("team_b", "Player"), salience=.65, goal_tags=("condition",))
        return event


def make_spec(seed):
    doc = json.loads((ROOT / "specs/shared_observatory.json").read_text())
    doc["setting"]["rules"].update(seed=seed, rounds=1, initial_condition="stable")
    doc["observations"][0]["value"] = "stable"
    doc["horizon_minutes"] = doc["termination"]["at"] = 1440
    doc["opportunities"] = doc["opportunities"][:1]
    return ExperienceCompilerV1().validate(doc)


def scenario(family, seed):
    """Build real history before the evaluator's choice; return admitted epochs."""
    if family not in FAMILIES:
        raise ValueError("unknown authored family")
    world = ControlledCoordinationWorld(make_spec(seed))
    rng = random.Random(seed * 131 + FAMILIES.index(family))
    first = world.condition(10, "stable")
    world.receive(11, first)
    first_epoch = list(world.player_stream)
    world.advance_to(20)
    world.execute({"action": "commit", "actor": "Player", "recipient": "team_c", "quantity": 4})
    count = rng.randrange(17, 33) if family in ("long_absence", "important_promise", "forget_recover") else rng.randrange(0, 6)
    for i in range(count):
        world.advance_to(21 + i)
        world.emit("routine_note", f"A legitimately observed routine queue note {i} is posted", ("Player",), scope="private")
    if family == "outdated":
        new = world.condition(60, "fragile")
        world.receive(61, new)
        world.receive(80, first)
    elif family == "contradictory":
        # Two different measurements within the same minute have identical
        # validity timestamps. The memory has no finer temporal information.
        second = world.condition(world.minute, "fragile")
        world.receive(world.minute, second)
        third = world.condition(world.minute, "stable")
        world.receive(world.minute, third)
        world.condition(70, "fragile")
    elif family == "shared_source":
        world.receive(70, first)
        world.receive(80, first)
    elif family == "strategic_communication":
        world.condition(60, "fragile")
        # A speaker strategically withholds its correction and resends a true
        # but dated record. No false or fabricated source event is introduced.
        world.receive(80, first)
    elif family == "important_promise":
        current = world.condition(60, "fragile")
        world.receive(61, current)
    elif family == "changed_goals":
        # The initial throughput plan is deliberately not executed; the real
        # accepted promise at minute20 precedes the changed goal input.
        pass
    elif family == "delayed_consequence":
        # This later state change is not knowable before choosing. It tests a
        # real delayed outcome; an unchanged correct belief is not a mind bug.
        world.clock.schedule(1200, "bench_condition_transition", {"value": "fragile"})
    now = 900 if family == "long_absence" else 240 if family == "strategic_communication" else 100
    world.advance_to(now)
    epochs = [(11, first_epoch, "throughput")] if family == "changed_goals" else []
    already = {e.event_id for e in first_epoch} if epochs else set()
    epochs.append((now, [e for e in world.player_stream if e.event_id not in already],
        "followup" if family == "changed_goals" else "coordination"))
    return world, epochs


def contracts(family, stage, *, inspected=False):
    goal_id = stage
    current_goals = [Goal(goal_id, "Protect the promised follow-up allocation" if stage == "followup" else "Coordinate useful projects and supported promises",
        tags=("condition", "obligation"), relevant_keys=(("observatory", "condition"),))]
    if stage == "followup":
        current_goals.insert(0, Goal("throughput", "The previous throughput goal", status="abandoned"))
    full_goal = "throughput" if stage in ("throughput", "followup") else goal_id
    sources = 2 if family == "shared_source" else 1
    stable = BeliefCondition("observatory", "condition", "stable", min_sources=sources, max_age=180, allow_direct=True)
    fragile = BeliefCondition("observatory", "condition", "fragile", max_age=180, allow_direct=True)
    personal = (SocialCondition("team_c", "obligation", minimum=4),) if family == "important_promise" else ()
    options = [ActionOption("equal", "Allocate four units to each team", 5, full_goal, conditions=(stable,)),
        ActionOption("protect", "Allocate four units each to the first and promised follow-up team", 4, goal_id,
            conditions=(fragile,), social_conditions=personal),
        ActionOption("ordinary", "Allocate the supported reduced capacity to the first two teams", 3, goal_id,
            conditions=(fragile,)),
        ActionOption("inspect", "Pay for a fresh current systems inspection", 1, goal_id,
            costs={"credits": 1, "inspection_slot": 1}, duration=1),
        ActionOption("wait", "Leave the instrument unallocated rather than invent support", 0)]
    if stage == "followup":
        options.append(ActionOption("protect-stable", "Prefer the revised follow-up plan under stable hardware", 4, goal_id, conditions=(stable,)))
    return current_goals, options


def make_mind(arm, *, capacity=16, context=4):
    if arm not in ARMS:
        raise ValueError("unknown cognitive arm")
    generation, policy = arm.split("_", 1)
    if arm == "bm25_fifo":
        return BM25BoundedMind("Player", MindConfig(capacity=capacity, context_records=context,
            retention_policy="recency", consolidation=False))
    cls = PersistentMind if generation == "v3" else AgentMind
    return cls("Player", MindConfig(capacity=capacity, context_records=context, retention_policy=policy))


def choose(mind, episodes, family, stage, world, *, inspected=False):
    current_goals, options = contracts(family, stage, inspected=inspected)
    resources = {"credits": world.economy.cash["Player"], "inspection_slot": 0 if inspected else 1}
    if isinstance(mind, PersistentMind):
        return mind.cycle(episodes, current_goals, options, resources, world.minute)["decision"]
    mind.set_goals(current_goals)
    for episode in episodes:
        mind.observe(episode)
    return asdict(mind.choose(options, own_resources=resources, now=world.minute))


def run_case(family, seed, arm, *, capacity=16, context=4):
    world, epochs = scenario(family, seed)
    # A separate detached scripted stream is supplied identically to each arm.
    stream = [asdict(e) for _, episodes, _ in epochs for e in episodes]
    stream_hash = digest(stream)
    mind = make_mind(arm, capacity=capacity, context=context)
    decisions, max_records, max_context, endogenous = [], 0, 0, []
    start = time.perf_counter()
    for at, episodes, stage in epochs:
        # Preparation already built the history. The policy's own time input
        # follows the admitted epoch, without exposing the prepared world state.
        class OwnView:
            minute = at
            economy = world.economy
        decision = choose(mind, episodes, family, stage, OwnView())
        decisions.append(decision)
        max_records = max(max_records, len(mind._all()))
        max_context = max(max_context, len(decision["context_event_ids"]))
    stage = epochs[-1][2]
    if decision["action_id"] == "inspect":
        before = len(world.player_stream)
        receipt = world.execute({"action": "inspect", "actor": "Player"})
        endogenous = [asdict(e) for e in world.player_stream[before:]]
        if isinstance(mind, PersistentMind):
            for episode in world.player_stream[before:]:
                mind.observe(episode)
            mind.evaluate("inspect", "succeeded", now=world.minute,
                evidence_ids=(receipt.event_id,) if receipt.event_id in mind.retained_event_ids() else ())
            new = []
        else:
            new = world.player_stream[before:]
        decision = choose(mind, new, family, stage, world, inspected=True)
        decisions.append(decision)
    action = decision["action_id"]
    if action in ("equal", "protect", "protect-stable", "ordinary"):
        allocation = {"team_a": 4, "team_b": 4 if action in ("equal", "ordinary") else 0,
            "team_c": 0 if action == "ordinary" else 4}
        receipt = world.execute({"action": "allocate", "actor": "Player", "allocation": allocation})
        if isinstance(mind, PersistentMind):
            for episode in world.player_stream:
                if episode.event_id == receipt.event_id:
                    mind.observe(episode)
            mind.evaluate(action, "succeeded", now=world.minute,
                evidence_ids=(receipt.event_id,) if receipt.event_id in mind.retained_event_ids() else ())
    elif action != "wait":
        raise AssertionError("A decision must select a declared executable allocation or wait")
    elapsed_ms = (time.perf_counter() - start) * 1000
    world.advance_to(1439)
    metrics = world.metrics()
    outcome = world.get("outcome:0")
    unused = outcome["actual_capacity"] - sum(outcome["executed"].values())
    # An explicitly declared exploratory scalar, not a calibrated human value.
    score = metrics["completed_projects"] - metrics["promises_missed"] - .1 * metrics["credits_spent"]
    footprint = mind.footprint()
    assert metrics["credit_total"] == metrics["initial_credit_total"]
    assert metrics["credits_spent"] in (0, 1)
    assert len(mind._all()) <= capacity
    max_context = max(max_context, *(len(d["context_event_ids"]) for d in decisions))
    return {"family": family, "seed": seed, "arm": arm, "input_stream_hash": stream_hash,
        "input_episodes": stream, "endogenous_inspection_episodes": endogenous,
        "admitted_input_event_ids": [e["event_id"] for e in stream], "decision_sequence": decisions,
        "executed_allocation": outcome["allocation"], "actual_delivered": outcome["executed"],
        "completed_projects": metrics["completed_projects"], "unused_capacity": unused,
        "inspection_fees": metrics["credits_spent"], "promises_kept": metrics["promises_kept"],
        "promises_missed": metrics["promises_missed"], "exploratory_score": round(score, 8),
        "credit_total": metrics["credit_total"], "initial_credit_total": metrics["initial_credit_total"],
        "max_context_records": max_context, "max_memory_records": max(max_records, len(mind._all())),
        "memory_capacity": capacity, "context_capacity": context, "serialized_mind_bytes": footprint["serialized_bytes"],
        "retained_plan_records": len(mind.plans) if isinstance(mind, PersistentMind) else 0,
        "cognition_and_execution_ms": elapsed_ms, "world_ledger_hash": world.ledger.content_hash(),
        "settlement_event_id": next(e.event_id for e in world.ledger.events if e.payload.get("category") == "allocation_settled")}


def paired_interval(values, *, samples=2000, seed=818):
    if not values:
        raise ValueError("paired differences are required")
    rng = random.Random(seed)
    draws = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(samples))
    return {"mean": statistics.mean(values), "lower_95": draws[int(.025 * (samples - 1))],
        "upper_95": draws[int(.975 * (samples - 1))], "paired_seed_clusters": len(values), "bootstrap_samples": samples}


def summarize(rows, *, bootstrap_samples=2000):
    metrics = ("completed_projects", "unused_capacity", "inspection_fees", "promises_kept", "promises_missed", "exploratory_score", "serialized_mind_bytes", "cognition_and_execution_ms")
    per_arm = {arm: {metric: statistics.mean(r[metric] for r in rows if r["arm"] == arm) for metric in metrics} for arm in sorted({r["arm"] for r in rows})}
    paired = {}
    for policy in POLICIES:
        left, right = f"v3_{policy}", f"v2_{policy}"
        if left not in per_arm or right not in per_arm:
            continue
        seeds = sorted({r["seed"] for r in rows})
        paired[policy] = {}
        for metric in metrics:
            deltas = []
            for seed in seeds:
                a = {(r["family"]): r[metric] for r in rows if r["seed"] == seed and r["arm"] == left}
                b = {(r["family"]): r[metric] for r in rows if r["seed"] == seed and r["arm"] == right}
                if set(a) != set(b):
                    raise ValueError("paired arms must contain identical families")
                deltas.append(statistics.mean(a[family] - b[family] for family in a))
            paired[policy][metric] = paired_interval(deltas, samples=bootstrap_samples)
    access = {}
    for row in rows:
        access.setdefault((row["family"], row["seed"]), set()).add(row["input_stream_hash"])
    if any(len(hashes) != 1 for hashes in access.values()):
        raise AssertionError("arms received different pre-action private observation streams")
    return {"world_runs": len(rows), "seed_clusters": len({r["seed"] for r in rows}), "families": sorted({r["family"] for r in rows}),
        "per_arm_means": per_arm, "v3_minus_v2_seed_cluster_intervals": paired,
        "matched_pre_action_access": True,
        "limitations": ["Controlled exploratory authored families; no held-out or independent replication claim.",
            "The same existing planner and belief guards are reused, so V3 plan persistence may add bytes/latency without changing outcomes.",
            "Record/context maxima match, not serialized bytes or token counts; V3 additionally retains up to four bounded plans.",
            "BM25 is lexical retrieval with FIFO episode retention and no semantic consolidation; admitted structured fields are included as text so direct-check titles do not hide their factual content. It is not a dense embedding baseline.",
            "A maximum of one paid inspection is allowed per final decision; its observation and fee are endogenous and reported.",
            "Background team policies are suppressed for controlled matching; this does not establish emergent whole-society improvement.",
            "These controlled decision tasks span one simulated day; long absence here is 900 minutes, not evidence of multi-month cognitive performance.",
            "The delayed hidden hardware transition is unknowable before allocation; resulting failure is not automatically a memory defect.",
            "Per-case timing is a short descriptive probe; machine load and arm ordering are not a controlled latency experiment.",
            "No LLM calls, human participants, skill-transfer results or neurological time claims."]}


def source_fingerprints():
    paths = [Path(__file__), ROOT / "kalends/experience_os/minds.py", ROOT / "kalends/experience_os/commons.py",
        ROOT / "kalends/experience_os/compiler.py", ROOT / "kalends_rebirth/minds.py",
        ROOT / "kalends/memory/retrieval.py", ROOT / "specs/shared_observatory.json",
        ROOT / "kalends/events.py", ROOT / "kalends/world.py", ROOT / "kalends/observation.py",
        ROOT / "kalends/city/simulation.py", ROOT / "kalends/genesis/simulation.py",
        ROOT / "kalends/pompeii/temporal.py", ROOT / "kalends/rng.py"]
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def run_study(output, *, seeds=tuple(range(21000, 21012)), arms=ARMS, families=FAMILIES,
        capacity=16, context=4, bootstrap_samples=2000):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    protocol_path = output / "protocol.json"
    if protocol_path.exists():
        raise ValueError("study directory already contains a registered protocol; use a new directory")
    if not seeds or not arms or not families or len(set(seeds)) != len(seeds) or any(type(s) is not int or s < 0 for s in seeds):
        raise ValueError("declare distinct nonnegative paired seeds and nonempty arms/families")
    protocol = {"version": 1, "classification": "controlled exploratory study, registered locally before case execution",
        "seeds": list(seeds), "arms": list(arms), "families": list(families),
        "capacity": capacity, "context": context, "bootstrap_samples": bootstrap_samples,
        "primary_outcomes": ["completed_projects", "unused_capacity", "inspection_fees", "promises_kept", "promises_missed"],
        "secondary_score": "completed_projects - promises_missed - 0.1 * actual inspection fees",
        "runtime": {"python": sys.version.split()[0], "platform": platform.platform(), "machine": platform.machine()},
        "unit_of_uncertainty": "paired seed clusters, averaging the nine authored families within each seed",
        "policy_budget": "One final allocation plus at most one real paid inspection; zero model calls. Changed-goal family additionally has one unexecuted initial plan.",
        "source_fingerprints_before": source_fingerprints()}
    protocol_path.write_text(json.dumps(protocol, indent=2) + "\n")
    rows = [run_case(family, seed, arm, capacity=capacity, context=context)
        for seed in seeds for family in families for arm in arms]
    streams = {}
    for row in rows:
        stream = row.pop("input_episodes")
        key = (row["family"], row["seed"])
        record = {"family": row["family"], "seed": row["seed"], "hash": row["input_stream_hash"], "episodes": stream}
        if key in streams and streams[key] != record:
            raise AssertionError("initial observation content differs across arms")
        streams[key] = record
    (output / "observations.jsonl").write_text("".join(canonical(row) + "\n" for row in streams.values()))
    (output / "raw.jsonl").write_text("".join(canonical(row) + "\n" for row in rows))
    report = summarize(rows, bootstrap_samples=bootstrap_samples)
    report["source_fingerprints_after"] = source_fingerprints()
    report["source_stable_during_execution"] = report["source_fingerprints_after"] == protocol["source_fingerprints_before"]
    report["protocol_hash"] = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    (output / "summary.json").write_text(json.dumps(report, indent=2) + "\n")
    table = ["# Controlled cognitive experiment", "", "This is an exploratory authored study on actual Commons allocations, not a held-out benchmark or human learning study.", "",
        f"Executed {len(rows)} worlds across {report['seed_clusters']} paired seeds. Sources stable during execution: {report['source_stable_during_execution']}.", "",
        "| Arm | Projects | Missed promises | Fees | Unused capacity | Secondary score | Mind bytes |", "|---|---:|---:|---:|---:|---:|---:|"]
    for arm, value in report["per_arm_means"].items():
        table.append(f"| {arm} | {value['completed_projects']:.3f} | {value['promises_missed']:.3f} | {value['inspection_fees']:.3f} | {value['unused_capacity']:.3f} | {value['exploratory_score']:.3f} | {value['serialized_mind_bytes']:.0f} |")
    table += ["", "V3 minus V2 intervals are in summary.json. Raw accepted allocations, delivered units, decisions, input hashes, conservation totals and ledger hashes are in raw.jsonl.", ""]
    table.extend("- " + item for item in report["limitations"])
    (output / "REPORT.md").write_text("\n".join(table) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seeds", type=int, default=12)
    parser.add_argument("--start-seed", type=int, default=21000)
    args = parser.parse_args()
    if not 1 <= args.seeds <= 12:
        parser.error("use 1..12 paired seeds; default experiment stays below 1000 worlds")
    report = run_study(args.output, seeds=tuple(range(args.start_seed, args.start_seed + args.seeds)))
    print(json.dumps({"world_runs": report["world_runs"], "source_stable": report["source_stable_during_execution"]}))


if __name__ == "__main__":
    main()
