"""Offline continuity diagnostic using actual Commons actions and receipts.

This module is a controller/evaluator, not a new world engine.  Its internal
holdout is an authored development study, not an external benchmark.  No model
or embedding provider is instantiated.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import gzip
import hashlib
import json
from pathlib import Path
import platform
import random
import statistics
import sys
import time
import zipfile

from kalends.experience_os import cognition_bench as old
from kalends.experience_os.compiler import ExperienceCompilerV1
from kalends.experience_os.minds import PersistentMind
from kalends.events import Ledger
from kalends.genesis.simulation import GenesisEconomy
from kalends.pompeii.temporal import EventClock
from kalends.world import WorldState, apply_event
from kalends_rebirth.minds import ActionOption, BeliefCondition, Episode, Goal, MindConfig, SocialSignal


ROOT = Path(__file__).resolve().parents[2]
STATE_BYTES = 16384
CONTEXT_RECORDS = 4
ARMS = ("current_observation", "v3_hybrid", "bm25_fifo", "admissible_history", "dependency_retention")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


@dataclass(frozen=True)
class CaseSpec:
    case_id: str
    family: str
    split: str
    initial: str = "stable"
    second: str = "fragile"
    correction: bool = True
    distractors: int = 24
    first_choice: int = 100
    correction_at: int = 1500
    second_choice: int = 2000

    def __post_init__(self):
        if self.initial not in {"stable", "fragile"} or self.second not in {"stable", "fragile"}:
            raise ValueError("condition must use an existing Commons value")
        if not 0 <= self.distractors <= 64 or not 50 <= self.first_choice < 1439:
            raise ValueError("invalid interruption schedule")
        if not 1440 < self.correction_at < self.second_choice < 2879:
            raise ValueError("second decision must follow the correction window")


# Authored before candidate development. Fresh seeds repeat these structures;
# they do not independently create new task families.
DEV = (
    CaseSpec("dev_interrupted", "interrupted_obligation", "development"),
    CaseSpec("dev_reverse", "evidence_revision", "development", "fragile", "stable"),
    CaseSpec("dev_current", "current_sufficient", "development", "fragile", "stable", True, 0, 100, 1999, 2000),
    CaseSpec("dev_hidden", "unobserved_transition", "development", "stable", "fragile", False, 24),
)

# Independently specified by the reviewer agent before any candidate/results.
# Variation is within this two-round template; not independent world families.
HOLDOUT = (
    CaseSpec("review_current_correction", "current_sufficient", "reviewer_holdout", "fragile", "stable", True, 0, 1400, 1999, 2000),
    CaseSpec("review_hidden_reversal", "unobserved_transition", "reviewer_holdout", "stable", "fragile", False, 0, 100, 1500, 2000),
    CaseSpec("review_unchanged_interruption", "memory_irrelevant", "reviewer_holdout", "stable", "stable", False, 48, 1400, 1500, 2800),
    CaseSpec("review_improvement_overload", "reverse_revision", "reviewer_holdout", "fragile", "stable", True, 48, 1200, 1441, 2800),
)


def make_world(spec, seed):
    doc = json.loads((ROOT / "specs/shared_observatory.json").read_text())
    doc["setting"]["rules"].update(seed=seed, rounds=2, initial_condition=spec.initial, maintenance_interval=7)
    doc["observations"][0]["value"] = spec.initial
    doc["horizon_minutes"] = doc["termination"]["at"] = 2880
    doc["opportunities"] = doc["opportunities"][:1]
    doc["participants"][0]["resources"]["credits"] = 1
    doc["goals"] = [
        {"id": "prerequisite", "actor": "team_c", "label": "Deliver the assigned first research batch",
         "priority": 90, "deadline": 1440, "requires": [],
         "target": {"resource": "capacity", "quantity": 4, "metric": "completed_rounds"}},
        {"id": "deferred", "actor": "team_c", "label": "Deliver the assigned follow-up after its prerequisite",
         "priority": 90, "deadline": 2880, "requires": ["prerequisite"],
         "target": {"resource": "capacity", "quantity": 4, "metric": "completed_rounds"}},
    ]
    return old.ControlledCoordinationWorld(ExperienceCompilerV1().validate(doc))


def options():
    """Same answer-independent action contract in every case and memory arm."""
    return [
        ActionOption("equal", "Allocate four units to each team", 5, "chain",
                     conditions=(BeliefCondition("observatory", "condition", "stable", max_age=2880, allow_direct=True),)),
        ActionOption("protect", "Allocate four units to the first and assigned follow-up team", 4, "chain",
                     conditions=(BeliefCondition("observatory", "condition", "fragile", max_age=2880, allow_direct=True),)),
        ActionOption("inspect", "Pay for a current direct inspection", 1, "chain", costs={"credits": 1}),
        ActionOption("wait", "Wait without supported allocation evidence", 0),
    ]


def goals():
    return [Goal("chain", "Complete the assigned prerequisite and follow-up batches", 1, 2880,
                 relevant_keys=(("observatory", "condition"),), tags=("coordination",))]


def world_snapshot(world):
    """Evaluator checkpoint, never accessible through the controller/memory API."""
    return {"spec": world.spec, "ledger": world.ledger.to_json(), "clock": world.clock.snapshot(),
            "minds": {a: m.to_dict() for a, m in world.minds.items()},
            "visible": {a: sorted(v) for a, v in world.visible.items()},
            "player_stream": [asdict(e) for e in world.player_stream]}


def restore_world(snapshot):
    """Reconstruct projections with existing ledger/economy/clock machinery."""
    world = old.ControlledCoordinationWorld(ExperienceCompilerV1().validate(snapshot["spec"]))
    world.ledger = Ledger()
    world.economy = GenesisEconomy()
    world.state = WorldState(agent_locations={a: "council" for a in ("Player", *old.TEAMS)})
    for row in snapshot["ledger"]:
        event = world.ledger.append(row["tick"], row["etype"], row["location"], tuple(row["actors"]), row["payload"], row["scope"])
        if event.event_id != row["event_id"]:
            raise ValueError("checkpoint ledger identity mismatch")
        apply_event(world.state, event)
        world.economy.apply(event)
        for update in event.payload.get("relationship_updates", ()):
            world.state.trust[(update["listener"], update["speaker"])] = update["value"]
    world.clock = EventClock.from_snapshot(snapshot["clock"])
    world.minds = {a: PersistentMind.from_dict(m) for a, m in snapshot["minds"].items()}
    world.visible = {a: set(v) for a, v in snapshot["visible"].items()}
    world.player_stream = [Episode(**{**e, "social_signals": tuple(SocialSignal(**s) for s in e["social_signals"]),
                                     "participants": tuple(e["participants"]), "goal_tags": tuple(e["goal_tags"])})
                           for e in snapshot["player_stream"]]
    return world


def verified_ingress(world, episodes):
    """Detach only exact legitimately received records at the host boundary.

    The controller receives no lookup function, ledger or archive. The host's
    monotonic stream cursor prevents a forgotten episode being offered again.
    """
    known = {e.event_id: e for e in world.player_stream}
    detached = []
    for episode in episodes:
        if (episode.event_id not in world.visible["Player"] or episode.event_id not in known
                or digest(asdict(episode)) != digest(asdict(known[episode.event_id]))):
            raise ValueError("unsupported, altered or privately owned observation")
        if episode.agent_id != "Player" or episode.observed_at > world.minute:
            raise ValueError("observation identity/time is outside this participant boundary")
        detached.append(episode)
    return detached


class DependencyRetentionMind(PersistentMind):
    """Small V3 retention patch; all revision/selection remains existing V3.

    Development exposed coarse tags evicting the active task's exact condition
    evidence. Prioritize those explicitly supplied keys under the same shared
    record/byte limits. There is no new cache, archive lookup or pinned history.
    Removing this override is exactly the v3_hybrid arm.
    """

    def _score(self, record, now):
        score = super()._score(record, now)
        key = (record.get("subject"), record.get("predicate"))
        exact = record.get("accepted", True) and any(key in g.relevant_keys for g in self._active(now))
        return (score[0] + (.6 if exact else 0), *score[1:])


def new_mind(arm):
    config = MindConfig(capacity=256 if arm == "admissible_history" else 16,
                        context_records=CONTEXT_RECORDS, retention_policy="hybrid")
    if arm == "bm25_fifo":
        return old.BM25BoundedMind("Player", replace(config, retention_policy="recency", consolidation=False))
    if arm == "dependency_retention":
        return DependencyRetentionMind("Player", config)
    if arm not in ARMS:
        raise ValueError("unimplemented arm")
    return PersistentMind("Player", config)


class ChainController:
    """One common resumable task controller, used by every memory mechanism.

    The phase determines the next legal step. The plan stores bounded receipt
    identifiers, never copies of condition facts or a hidden target. Public
    institutional truth is re-read equally by all arms at every decision.
    """

    def __init__(self, arm, mind=None, plan=None):
        self.arm = arm
        self.mind = mind if mind is not None else new_mind(arm)
        self.plan = plan or {"phase": "obtain_report", "round": 0, "support_ids": [],
                             "receipt_ids": [], "next": "accept_assigned_commitment", "ingress_watermark": -1}
        self.max_state_bytes = 0
        self.max_context_bytes = 0
        self.byte_evictions = 0

    def snapshot(self):
        return {"arm": self.arm, "mind": self.mind.to_dict(), "plan": json.loads(canonical(self.plan))}

    @classmethod
    def restore(cls, snapshot):
        arm = snapshot["arm"]
        restored = type(new_mind(arm)).from_dict(snapshot["mind"])
        return cls(arm, restored, json.loads(canonical(snapshot["plan"])))

    def charge(self, now):
        # All persistent state, including inherited goals/plans/last-decision,
        # controller phase and references, counts toward the same accessible cap.
        while len(canonical(self.snapshot()).encode()) > STATE_BYTES and self.arm != "admissible_history":
            records = self.mind._all()
            if not records:
                raise ValueError("working state alone exceeds the byte cap")
            victim = min(records, key=lambda r: self.mind._score(r, now))["serial"]
            for field in ("_episodes", "_semantic", "_revisions", "_reflections"):
                setattr(self.mind, field, [r for r in getattr(self.mind, field) if r["serial"] != victim])
            self.byte_evictions += 1
        size = len(canonical(self.snapshot()).encode())
        self.max_state_bytes = max(self.max_state_bytes, size)
        return size

    def admit(self, episodes, now, *, remove_report=False):
        self.mind.set_goals(goals())
        for episode in episodes:
            if episode.observed_at > now or episode.agent_id != "Player":
                raise ValueError("the controller may admit only already received own episodes")
            if remove_report and episode.kind == "told" and episode.key == ("observatory", "condition"):
                continue
            self.mind.observe(episode)
            self.charge(now)

    def mark_report(self):
        if self.plan["phase"] not in {"obtain_report", "review_after_interruption"}:
            raise ValueError("report is out of plan order")
        self.plan["phase"] = "accept_assigned_commitment"

    def commit(self, world):
        if self.plan["phase"] != "accept_assigned_commitment" or self.plan["round"] != world.round:
            raise ValueError("restore the actual plan before accepting the assigned obligation")
        receipt = world.execute({"action": "commit", "actor": "Player", "recipient": "team_c", "quantity": 4})
        self.plan.update(phase="review_after_interruption", next="allocate_after_evidence_review")
        self.plan["receipt_ids"] = (self.plan["receipt_ids"] + [receipt.event_id])[-4:]
        return receipt

    def select(self, world, current_episodes):
        if self.plan["phase"] != "review_after_interruption" or self.plan["round"] != world.round:
            raise ValueError("pending controller phase/round is required to resume the chain")
        if self.arm == "current_observation":
            # Explicit no-history diagnostic; retains the same public register.
            self.mind = new_mind(self.arm)
            self.admit(current_episodes, world.minute)
        public = {"credits": world.economy.cash["Player"], "promises": world.get(f"promises:{world.round}", {}),
                  "projects": world.get("goal_status"), "round": world.round}
        if public["promises"].get("team_c") != 4:
            raise ValueError("the assigned obligation must exist in the shared public register")
        own = {"credits": public["credits"]}
        state_before = self.snapshot()
        if isinstance(self.mind, PersistentMind):
            decision = self.mind.cycle([], goals(), options(), own, world.minute)["decision"]
        else:
            self.mind.set_goals(goals())
            decision = asdict(self.mind.choose(options(), own_resources=own, now=world.minute))
        self.plan["support_ids"] = decision["evidence_ids"][:CONTEXT_RECORDS]
        context = [r for r in self.mind._episodes + self.mind._semantic if r["event_id"] in decision["context_event_ids"]]
        self.max_context_bytes = max(self.max_context_bytes, len(canonical(context).encode()))
        size = self.charge(world.minute)
        return decision, {"at": world.minute, "public_register": public,
                          "controller_plan_read": state_before["plan"], "private_state_before": state_before["mind"],
                          "options": [asdict(o) for o in options()], "option_hash": digest([asdict(o) for o in options()]),
                          "decision": decision, "context": context, "state_bytes_after": size}

    def allocate(self, world, decision):
        action = decision["action_id"]
        if action not in {"equal", "protect", "wait"}:
            raise ValueError("inspection must be executed and reviewed before allocation")
        if action == "wait":
            self.plan.update(phase="await_settlement", next="read_actual_settlement")
            return None
        receipt = world.execute({"action": "allocate", "actor": "Player",
                                 "allocation": {"team_a": 4, "team_b": 4 if action == "equal" else 0, "team_c": 4}})
        self.plan.update(phase="await_settlement", next="read_actual_settlement")
        self.plan["receipt_ids"] = (self.plan["receipt_ids"] + [receipt.event_id])[-4:]
        if isinstance(self.mind, PersistentMind):
            self.mind.evaluate(action, "succeeded", now=world.minute)
        return receipt

    def settled(self, world):
        if self.plan["phase"] != "await_settlement" or world.get(f"outcome:{self.plan['round']}") is None:
            raise ValueError("a real settlement receipt is required before the deferred step")
        if self.plan["round"] == 0:
            self.plan.update(phase="obtain_report", round=1, support_ids=[], next="accept_assigned_commitment")
        else:
            self.plan.update(phase="complete", next="review_recorded_outcome")


def _pressure(world, start, end, count, seed):
    """Legitimate unrelated engineering receipts; state and content are audited.

    Same broad coordination tag and salience as other operational evidence.
    This deliberately tests coarse relevance under overload; no claim that the
    frequency or importance distribution is representative of human lives.
    """
    rng = random.Random(seed)
    times = sorted(rng.randint(start, max(start, end)) for _ in range(count))
    for i, at in enumerate(times):
        world.advance_to(at)
        event = world.emit("engineering_receipt", f"An auxiliary engineering queue posts receipt {seed}-{i}", ("Player",), scope="private")
        world.player_stream[-1] = Episode(event.event_id, "Player", at, "episodic", event.payload["title"],
                                         participants=("Player",), salience=.55 + .35 * rng.random(), goal_tags=("coordination",))


def run_case(spec, seed, arm, *, remove_report=False, drop_legacy_plans=False):
    started = time.perf_counter()
    world = make_world(spec, seed)
    controller = ChainController(arm)
    admitted, traces, restores, endogenous, commands = [], [], [], [], []
    cursor = 0
    max_bytes, max_context, evictions = 0, 0, 0

    def admit():
        nonlocal cursor
        fresh = verified_ingress(world, world.player_stream[cursor:])
        if any(e.event_id <= controller.plan["ingress_watermark"] for e in fresh):
            raise ValueError("a host must not reload forgotten records from the canonical archive")
        admitted.extend(asdict(e) for e in fresh)
        controller.admit(fresh, world.minute, remove_report=remove_report)
        cursor = len(world.player_stream)
        if fresh:
            controller.plan["ingress_watermark"] = max(e.event_id for e in fresh)
        controller.charge(world.minute)
        return fresh

    def restart(label):
        nonlocal controller, world, max_bytes, max_context, evictions
        encoded = canonical(controller.snapshot())
        restored = ChainController.restore(json.loads(encoded))
        if canonical(restored.snapshot()) != encoded:
            raise AssertionError("controller/mind session restore changed serialized state")
        saved_world = json.loads(canonical(world_snapshot(world)))
        restored_world = restore_world(saved_world)
        if canonical(world_snapshot(restored_world)) != canonical(saved_world):
            raise AssertionError("world checkpoint reconstruction changed state")
        restores.append({"session": label, "at": world.minute, "snapshot": json.loads(encoded),
                         "world_checkpoint": saved_world, "world_sha256": digest(saved_world),
                         "sha256": digest(json.loads(encoded)), "exact": True})
        max_bytes = max(max_bytes, controller.max_state_bytes)
        max_context = max(max_context, controller.max_context_bytes)
        evictions += controller.byte_evictions
        controller = restored
        world = restored_world

    def decide_and_execute():
        fresh = admit()
        # A current report is current evidence only when it arrived at the last
        # minute of the choice window; earlier receipts require actor history.
        current = verified_ingress(world, [e for e in world.player_stream if e.observed_at >= world.minute - 1])
        if drop_legacy_plans and isinstance(controller.mind, PersistentMind):
            controller.mind.plans = []
        decision, trace = controller.select(world, current)
        traces.append(trace)
        if decision["action_id"] == "inspect":
            before = len(world.player_stream)
            receipt = world.execute({"action": "inspect", "actor": "Player"})
            commands.append({"at": world.minute, "action": "inspect", "receipt_id": receipt.event_id})
            endogenous.extend(asdict(e) for e in world.player_stream[before:])
            received = admit()
            if isinstance(controller.mind, PersistentMind):
                controller.mind.evaluate("inspect", "succeeded", now=world.minute,
                                         evidence_ids=(receipt.event_id,) if receipt.event_id in controller.mind.retained_event_ids() else ())
            decision, trace = controller.select(world, received)
            traces.append(trace)
        receipt = controller.allocate(world, decision)
        commands.append({"at": world.minute, "action": decision["action_id"], "receipt_id": receipt.event_id if receipt else None})
        controller.charge(world.minute)

    # Session one: receive real dated evidence and accept the fixed task.
    first = world.condition(10, spec.initial)
    world.receive(11, first)
    admit()
    controller.mark_report()
    world.advance_to(20)
    receipt = controller.commit(world)
    commands.append({"at": world.minute, "action": "commit", "receipt_id": receipt.event_id})
    admit()
    restart("one_report_and_commitment")

    # Session two: interruption, real prerequisite execution and actual outcome.
    _pressure(world, 21, spec.first_choice - 2, spec.distractors, seed)
    world.advance_to(spec.first_choice - 1)
    world.emit("choice_window", "The participant can review the pending allocation", ("Player",), scope="private")
    world.advance_to(spec.first_choice)
    decide_and_execute()
    world.advance_to(1439)
    controller.settled(world)
    admit()
    restart("two_prerequisite_settled")

    # Session three: actual new obligation, received correction (or hidden
    # transition), interruption, deferred action and its settlement.
    world.advance_to(1440)
    controller.mark_report()
    receipt = controller.commit(world)
    commands.append({"at": world.minute, "action": "commit", "receipt_id": receipt.event_id})
    second = world.condition(spec.correction_at, spec.second)
    if spec.correction:
        world.receive(spec.correction_at, second)
    admit()
    restart("three_correction_or_unavailable_evidence")
    _pressure(world, spec.correction_at, spec.second_choice - 2, spec.distractors, seed + 10000)
    world.advance_to(spec.second_choice - 1)
    world.emit("choice_window", "The participant can review the pending allocation", ("Player",), scope="private")
    world.advance_to(spec.second_choice)
    decide_and_execute()
    world.advance_to(2879)
    controller.settled(world)
    admit()
    restart("four_chain_settled")

    register = world.get("goal_status")
    metrics = world.metrics()
    if metrics["credit_total"] != metrics["initial_credit_total"]:
        raise AssertionError("domain credits were not conserved")
    if any(row["state_bytes_after"] > STATE_BYTES for row in traces) and arm != "admissible_history":
        raise AssertionError("the complete accessible-state cap was exceeded")
    decisions = [row["decision"]["action_id"] for row in traces]
    result = {"case": asdict(spec), "seed": seed, "arm": arm, "remove_report": remove_report,
              "legacy_plan_ablation": drop_legacy_plans, "chain_complete": all(r["status"] == "completed" for r in register.values()),
              "goal_register": register, "metrics": metrics, "decisions": decisions, "trace": traces,
              "admitted_stream": admitted, "admitted_stream_hash": digest(admitted),
              "endogenous_inspection_episodes": endogenous, "commands": commands, "session_restores": restores,
              "max_total_state_bytes": max_bytes, "max_context_bytes": max_context, "byte_evictions": evictions,
              "context_record_limit": CONTEXT_RECORDS, "accessible_byte_cap": None if arm == "admissible_history" else STATE_BYTES,
              "final_ledger_hash": world.ledger.content_hash(), "ledger": world.ledger.to_json(),
              "information_limit": "second transition not received; do not label an unlucky stale action a memory error" if not spec.correction and spec.initial != spec.second else None,
              "live_model_calls": 0, "embedding_calls": 0, "vector_index_bytes": 0,
              "wall_seconds": time.perf_counter() - started}
    byte_breakdown = []
    for saved in restores:
        snapshot = saved["snapshot"]
        mind = snapshot["mind"]
        base = mind.get("base", mind)
        retained = {k: base[k] for k in ("episodes", "semantic", "revisions", "reflections")}
        byte_breakdown.append({"session": saved["session"], "retained_record_bytes": len(canonical(retained).encode()),
                               "serialized_mind_bytes": len(canonical(mind).encode()),
                               "controller_plan_bytes": len(canonical(snapshot["plan"]).encode()),
                               "total_accessible_bytes": len(canonical(snapshot).encode()),
                               "retained_records": sum(len(v) for v in retained.values()),
                               "legacy_plan_register_bytes": len(canonical(mind.get("plans", [])).encode())})
    result["state_byte_breakdown"] = byte_breakdown
    stale = []
    unauthorized = []
    for trace in traces:
        retained = trace["private_state_before"].get("base", trace["private_state_before"])
        known = {r["event_id"] for field in ("episodes", "semantic") for r in retained[field]}
        unauthorized.extend(i for i in trace["decision"]["evidence_ids"] if i not in known)
        action = trace["decision"]["action_id"]
        if spec.correction and trace["at"] >= spec.correction_at and action in {"equal", "protect"}:
            if action != ("equal" if spec.second == "stable" else "protect"):
                stale.append(trace["at"])
    result["secondary_outcomes"] = {"stale_actions_after_received_correction": len(stale),
                                    "unauthorized_evidence_uses": len(unauthorized),
                                    "invalid_executed_actions": 0, "exact_session_restores": len(restores),
                                    "source_independence": "not tested: no independent/correlated competing-origin condition in this bounded study",
                                    "repair": "not tested: no post-settlement repair route in this adapter task"}
    result["failure_taxonomy"] = ("none" if result["chain_complete"] else "unavailable_evidence" if result["information_limit"]
                                  else "encoding_intervention" if remove_report else "eviction_or_retrieval_under_overload")
    result["scientific_hash"] = digest({k: v for k, v in result.items() if k not in {"wall_seconds", "scientific_hash"}})
    return result


def summarize(rows):
    groups = []
    for split in sorted({r["case"]["split"] for r in rows}):
        for case_id in sorted({r["case"]["case_id"] for r in rows if r["case"]["split"] == split}):
            for arm in sorted({r["arm"] for r in rows}):
                selected = [r for r in rows if r["case"]["case_id"] == case_id and r["arm"] == arm]
                if not selected:
                    continue
                groups.append({"split": split, "case": case_id, "arm": arm, "worlds": len(selected),
                               "completed_chains": sum(r["chain_complete"] for r in selected),
                               "inspection_credits": sum(r["metrics"]["credits_spent"] for r in selected),
                               "missed_promises": sum(r["metrics"]["promises_missed"] for r in selected),
                               "max_total_state_bytes": max(r["max_total_state_bytes"] for r in selected),
                               "median_runtime_seconds": statistics.median(r["wall_seconds"] for r in selected)})
    comparisons = []
    for case_id in sorted({r["case"]["case_id"] for r in rows}):
        baseline = {r["seed"]: r for r in rows if r["case"]["case_id"] == case_id and r["arm"] == "v3_hybrid"}
        candidate = {r["seed"]: r for r in rows if r["case"]["case_id"] == case_id and r["arm"] == "dependency_retention"}
        paired = sorted(set(baseline) & set(candidate))
        if not paired:
            continue
        differences = [int(candidate[s]["chain_complete"]) - int(baseline[s]["chain_complete"]) for s in paired]
        rng = random.Random(7721)
        boot = sorted(statistics.mean(rng.choices(differences, k=len(differences))) for _ in range(2000))
        comparisons.append({"case": case_id, "split": candidate[paired[0]]["case"]["split"],
                            "paired_worlds": len(paired), "completion_rate_difference": statistics.mean(differences),
                            "conditional_paired_bootstrap_95": [boot[49], boot[1949]],
                            "candidate_wins": sum(d > 0 for d in differences), "baseline_wins": sum(d < 0 for d in differences),
                            "ties": sum(d == 0 for d in differences),
                            "limitation": "seed resampling conditional on this single authored template; zero width is not general equivalence/certainty"})
    return {"worlds": len(rows), "groups": groups, "candidate_vs_v3": comparisons, "live_model_calls": 0, "embedding_calls": 0,
            "interpretation": "Internal authored diagnostic with fixed controller; conditional on these task templates, not independent replication."}


def source_files():
    required = [Path(__file__), ROOT / "specs/shared_observatory.json", ROOT / "kalends/experience_os/cognition_bench.py",
            ROOT / "kalends/experience_os/minds.py", ROOT / "kalends/experience_os/commons.py",
            ROOT / "kalends/experience_os/compiler.py", ROOT / "kalends_rebirth/minds.py",
            ROOT / "kalends/memory/retrieval.py", ROOT / "kalends/memory/base.py",
            ROOT / "kalends/city/simulation.py", ROOT / "kalends/events.py", ROOT / "kalends/world.py",
            ROOT / "kalends/observation.py", ROOT / "kalends/pompeii/temporal.py",
            ROOT / "kalends/genesis/simulation.py", ROOT / "kalends/rng.py"]
    imported = [Path(module.__file__).resolve() for module in tuple(sys.modules.values())
                if getattr(module, "__file__", None) and str(module.__file__).endswith(".py")
                and Path(module.__file__).resolve().is_relative_to(ROOT)]
    return sorted(set(required + imported))


def fingerprint():
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files()}


def old_plan_diagnostic():
    sequences = []
    for erase in (False, True):
        world, epochs = old.scenario("changed_goals", 0)
        mind = old.make_mind("v3_hybrid")
        choices = []
        for index, (at, episodes, stage) in enumerate(epochs):
            if index and erase:
                mind.plans = []
            own = type("OwnView", (), {"minute": at, "economy": world.economy})()
            choices.append(old.choose(mind, episodes, "changed_goals", stage, own)["action_id"])
        sequences.append(choices)
    return {"original_decisions": sequences[0], "without_pending_plan": sequences[1],
            "same": sequences[0] == sequences[1],
            "finding": "Shipped PersistentMind chooses before writing its next-action plan; old task does not show a causal benefit from that plan."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dev-seeds", type=int, default=8)
    parser.add_argument("--test-seeds", type=int, default=30)
    parser.add_argument("--development-only", action="store_true")
    parser.add_argument("--gate", type=Path, help="preserved development-gate summary authorizing the small candidate")
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args(argv)
    if args.replay:
        original = json.loads(gzip.decompress(args.replay.read_bytes()).decode() if args.replay.suffix == ".gz" else args.replay.read_text())
        rerun = run_case(CaseSpec(**original["case"]), original["seed"], original["arm"],
                         remove_report=original["remove_report"], drop_legacy_plans=original["legacy_plan_ablation"])
        if original["scientific_hash"] != rerun["scientific_hash"]:
            raise SystemExit("replay projection differs")
        print(json.dumps({"exact_replay": True, "scientific_hash": rerun["scientific_hash"]}))
        return
    if args.out.exists():
        raise SystemExit("preserve existing runs: choose a new output directory")
    if not 1 <= args.dev_seeds <= 12 or not 1 <= args.test_seeds <= 60:
        raise SystemExit("invalid bounded seed counts")
    args.out.mkdir(parents=True)
    gate = json.loads(args.gate.read_text()) if args.gate else None
    if not args.development_only and not gate:
        raise SystemExit("freeze/run the development diagnostic before a candidate comparison")
    if gate:
        observed = {(g["case"], g["arm"]): g["completed_chains"] for g in gate["groups"]}
        if not any(observed.get((s.case_id, "admissible_history"), 0) > observed.get((s.case_id, "v3_hybrid"), 0) for s in DEV):
            raise SystemExit("candidate stopped: no demonstrated development deficit")
    source = fingerprint()
    protocol = {"status": "prospective_internal_diagnostic", "primary_endpoint": "both public prerequisite/deferred projects completed from actual settled units",
                "primary_comparison": "v3_hybrid versus candidate only if development shows a memory deficit to admissible history",
                "arms": ARMS, "common_controller": "phase plan and the same typed action contracts in every arm",
                "development": [asdict(s) for s in DEV], "holdout": [asdict(s) for s in HOLDOUT],
                "holdout_authorship": "reviewer agent specified cases before inspecting candidate/results; internal, not external or independent replication",
                "dev_seeds": list(range(args.dev_seeds)), "test_seeds": list(range(1000, 1000 + args.test_seeds)),
                "development_only": args.development_only,
                "preserved_development_gate": str(args.gate) if args.gate else None,
                "development_gate_hash": digest(gate) if gate else None,
                "candidate": "existing V3 _score +0.6 for admitted exact active-goal evidence keys; no new state or revision mechanism",
                "ablation": "candidate minus dependency protection is exactly v3_hybrid; no new belief-invalidation mechanism to ablate",
                "memory": {"accessible_total_bytes": STATE_BYTES, "records": 16, "context_records": CONTEXT_RECORDS,
                           "generous_reference_records": 256, "generous_reference_bytes": "reported; unmatched upper reference"},
                "resources": {"player_initial_credits": 1, "inspection_cost": 1, "assigned_team_c_units_per_round": 4},
                "model": {"calls": 0, "embedding_calls": 0, "dense_baseline": "unexecuted: no provisioned encoder"},
                "analysis": "paired on seed within authored template; no world decisions treated as independent samples; no power guarantee",
                "seed_variation": "unrelated receipt timing and salience only; zero-distractor cases are functional repeats, not additional structural evidence",
                "exclusions": "none; preserve operational failures; hidden transitions are information-limited cases",
                "source": source, "python": platform.python_version(), "platform": platform.platform()}
    (args.out / "protocol.json").write_text(json.dumps(protocol, indent=2) + "\n")
    with zipfile.ZipFile(args.out / "frozen_source.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for p in source_files():
            archive.write(p, str(p.relative_to(ROOT)))
    (args.out / "old_plan_diagnostic.json").write_text(json.dumps(old_plan_diagnostic(), indent=2) + "\n")
    rows, failures = [], []
    raw = args.out / "raw"
    raw.mkdir()
    stages = [(DEV, range(args.dev_seeds))]
    if not args.development_only:
        stages.append((HOLDOUT, range(1000, 1000 + args.test_seeds)))
    for specs, seeds in stages:
        for spec in specs:
            for seed in seeds:
                for arm in ARMS:
                    try:
                        row = run_case(spec, seed, arm)
                        rows.append(row)
                        (raw / f"{spec.case_id}_{seed}_{arm}.json.gz").write_bytes(gzip.compress((canonical(row) + "\n").encode(), mtime=0))
                    except Exception as error:
                        failures.append({"case": asdict(spec), "seed": seed, "arm": arm,
                                         "type": type(error).__name__, "error": str(error)})
            print(f"{spec.case_id}: complete", flush=True)
    summary = {**summarize(rows), "failures": failures, "source_unchanged": source == fingerprint()}
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    (args.out / "source_after.json").write_text(json.dumps(fingerprint(), indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return summary


if __name__ == "__main__":
    main()
