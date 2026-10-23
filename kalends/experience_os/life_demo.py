"""Reproducible recorded lives on the compiled runtime, without invented biography.

The Player controller in the Commons life reads only an actually disclosed
report returned by an accepted participant action. Operator checkpoints are
explicitly labeled and are not policy inputs. This is a scripted demonstration,
not human playtesting, a new biography model or educational-effectiveness data.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import time
import zipfile

from .compiler import ExperienceCompilerV1
from .runtime import ExperienceRuntime


ROOT = Path(__file__).resolve().parents[2]


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def file_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def life_spec(adapter="commons", *, days=90):
    maximum = 90 if adapter == "commons" else 120
    if adapter not in ("commons", "pompeii") or type(days) is not int or not 1 <= days <= maximum:
        raise ValueError("choose commons 1..90 or Pompeii 1..120 days")
    file = "shared_observatory.json" if adapter == "commons" else "pompeii_life.json"
    document = json.loads((ROOT / "specs" / file).read_text())
    document["id"] = "observatory_long_life" if adapter == "commons" else "pompeii_long_life"
    document["title"] = f"Recorded {days}-day demonstration: " + ("Shared Observatory" if adapter == "commons" else "Pompeii continuity")
    document["horizon_minutes"] = document["termination"]["at"] = days * 1440
    key = "rounds" if adapter == "commons" else "horizon_days"
    document["setting"]["rules"][key] = days
    document["opportunities"] = [o for o in document["opportunities"] if o["at"] < days * 1440]
    for goal in document["goals"]:
        if goal.get("deadline") is not None:
            goal["deadline"] = min(goal["deadline"], days * 1440)
    return ExperienceCompilerV1().validate(document)


def checkpoint(life, directory, elapsed_days):
    saved = life.journal_path.read_bytes()
    before = life.state_hash()
    restored = ExperienceRuntime(life.spec, journal_path=life.journal_path, retention=life.retention)
    if restored.state_hash() != before or restored.commands != life.commands or life.journal_path.read_bytes() != saved:
        raise AssertionError("checkpoint restart did not preserve the exact saved life")
    document = {"elapsed_days": elapsed_days, "scope": "Explicit operator checkpoint of a scripted demonstration; not a Player policy input.",
        "exact_restart": True, "journal_sha256": hashlib.sha256(saved).hexdigest(),
        "state_hash": before, "metrics": life.metrics(), "snapshot": life.snapshot(operator=True)}
    write_json(directory / f"checkpoint_day_{elapsed_days:03d}.json", document)
    return restored, {key: document[key] for key in ("elapsed_days", "exact_restart", "journal_sha256", "state_hash", "metrics")}


def run_commons(directory, *, days=90):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    journal = directory / "accepted_journal.json"
    if journal.exists():
        raise ValueError("preserve an existing recorded life; use a new directory")
    spec = life_spec("commons", days=days)
    write_json(directory / "validated_spec.json", spec.to_dict())
    write_json(directory / "controller.json", {"classification": "Scripted recorded life, not a human trial",
        "days": days, "information": "Only the current report returned by the accepted Player disclosure request is used by the allocation policy.",
        "policy": "Promise four units to team_c. First day deliberately overallocate all three teams. Thereafter: stable report -> four each; fragile report -> four for team_c plus four for alternating team_a/team_b.",
        "limits": "The setting's fixed execution order is preserved. This is a deterministic example trajectory, not an optimal policy or a claim of human skill."})
    life = ExperienceRuntime(spec, journal_path=journal)
    original_credits = sum(life.world.economy.cash.values())
    records, checkpoints = [], []
    targets = {n for n in (1, 30, 60, 90, days) if n <= days}
    start = time.perf_counter()
    for round_index in range(days):
        report = life.commit("action", {"action": "share", "recipient": "team_b"})["receipt"]
        if (report["event_id"] not in life.visible_ids() or report["payload"].get("category") != "report"
                or report["payload"].get("speaker") != "team_b" or report["payload"].get("listener") != "Player"):
            raise AssertionError("the controller did not receive an authorized condition report")
        value = report["payload"]["value"]
        if value not in ("stable", "fragile"):
            raise AssertionError("the disclosed report did not contain a supported condition")
        promise = life.commit("action", {"action": "commit", "recipient": "team_c", "quantity": 4})["receipt"]
        if round_index == 0 or value == "stable":
            allocation = {"team_a": 4, "team_b": 4, "team_c": 4}
        elif round_index % 2:
            allocation = {"team_a": 4, "team_b": 0, "team_c": 4}
        else:
            allocation = {"team_a": 0, "team_b": 4, "team_c": 4}
        command_index = len(life.commands)
        accepted = life.commit("action", {"action": "allocate", "allocation": allocation})["receipt"]
        life.commit("advance", {"minutes": 1440, "mode": "compress"})
        outcome = life.world.get(f"outcome:{round_index}")
        settlement = next(e for e in reversed(life.world.ledger.events)
            if e.payload.get("category") == "allocation_settled" and e.tick == (round_index + 1) * 1440 - 1)
        records.append({"round": round_index, "elapsed_days": round_index + 1,
            "report_event_id": report["event_id"], "reported_value": value,
            "promise_event_id": promise["event_id"], "allocation_command_index": command_index,
            "allocation_event_id": accepted["event_id"], "settlement_event_id": settlement.event_id,
            "actual_outcome": outcome, "metrics": life.metrics(),
            "explanation_scope": "Controller records which disclosed report it used; canonical dependencies are unchanged. Only executed omission below tests an alternative."})
        if round_index + 1 in targets:
            life, saved = checkpoint(life, directory, round_index + 1)
            checkpoints.append(saved)
    saved_bytes = journal.read_bytes(); original_hash = life.state_hash()
    omitted = records[0]["allocation_command_index"]
    alternative = life.fork(omitted)
    if life.state_hash() != original_hash or journal.read_bytes() != saved_bytes:
        raise AssertionError("an omission branch modified the original saved life")
    if alternative["alternative"]["minute"] != life.minute:
        raise AssertionError("the alternative did not reach the matched horizon")
    if alternative["alternative"]["metrics"]["completed_projects"] >= life.metrics()["completed_projects"]:
        raise AssertionError("the omitted real allocation did not change executed projects")
    if sum(life.world.economy.cash.values()) != original_credits:
        raise AssertionError("finite credits were not conserved")
    write_json(directory / "round_history.json", records)
    write_json(directory / "personal_history.json", life.debrief())
    write_json(directory / "actual_omission.json", alternative)
    summary = {"adapter": "commons", "elapsed_days": days, "world_minutes": life.minute,
        "commands": len(life.commands), "ledger_events": len(life.world.ledger), "final_state_hash": original_hash,
        "journal_sha256": file_hash(journal), "metrics": life.metrics(), "initial_total_credits": original_credits,
        "final_total_credits": sum(life.world.economy.cash.values()),
        "trust_player": {a: life.world.state.trust.get((a, "Player"), .5) for a in ("team_a", "team_b", "team_c")},
        "checkpoints": checkpoints, "omitted_command": omitted, "alternative_hash": alternative["alternative_hash"],
        "omission_differences": alternative["differences"], "original_preserved": True,
        "execution_and_exact_restart_seconds": time.perf_counter() - start,
        "limits": ["Recorded scripted choices rather than a generated biography or human study.",
            "Membership is the explicit six-completed-project threshold; it is not a general profession or career model.",
            "A displayed day number labels elapsed simulation; it does not represent subjective human time.",
            "The omission holds declared later commands fixed and is not an optimal alternative-life search."]}
    write_json(directory / "summary.json", summary)
    return summary


def run_pompeii(directory, *, days=120):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    journal = directory / "accepted_journal.json"
    if journal.exists():
        raise ValueError("preserve an existing recorded life; use a new directory")
    spec = life_spec("pompeii", days=days)
    write_json(directory / "validated_spec.json", spec.to_dict())
    life = ExperienceRuntime(spec, journal_path=journal)
    accepted = []
    for action in ({"action": "hear_dispute", "recipient": "Sabina", "quantity": 1},
        {"action": "support_market", "recipient": "Sabina", "quantity": 1},
        {"action": "move", "location": "bakery"},
        {"action": "accept_delivery", "recipient": "Felix", "quantity": 1}):
        result = life.commit("action", action)
        accepted.append({"command_index": result["command_index"], "receipt": result["receipt"]})
    checkpoints = []
    targets = sorted({n for n in (1, 30, 60, 90, 120, days) if n <= days})
    start = time.perf_counter()
    for elapsed in targets:
        if life.minute < elapsed * 1440:
            life.commit("advance", {"minutes": elapsed * 1440 - life.minute, "mode": "compress"})
        life, saved = checkpoint(life, directory, elapsed)
        checkpoints.append(saved)
        if elapsed == 1 and days > 1:
            # The first real delivery has now failed. A separate actual service
            # agreement is accepted and kept before the next long absence.
            for action in ({"action": "move", "location": "household"},
                {"action": "patronage", "recipient": "Lucius", "quantity": 1},
                {"action": "service", "recipient": "Lucius", "quantity": 1}):
                result = life.commit("action", action)
                accepted.append({"command_index": result["command_index"], "receipt": result["receipt"]})
    decisions = [e for e in life.world.ledger.events if e.payload.get("category") == "os_decision"]
    actors = {e.actors[0] for e in decisions}
    if actors != set(life.world.agent_ids):
        raise AssertionError("the long Pompeii life did not execute decisions for all six V3 agents")
    saved = journal.read_bytes(); before = life.state_hash()
    restored = ExperienceRuntime(spec, journal_path=journal)
    if restored.state_hash() != before or journal.read_bytes() != saved:
        raise AssertionError("Pompeii long-life replay differed")
    write_json(directory / "personal_history.json", life.debrief())
    write_json(directory / "accepted_player_choices.json", accepted)
    write_json(directory / "operator_decisions.json", [e.to_dict() for e in decisions])
    summary = {"adapter": "pompeii", "elapsed_days": days, "world_minutes": life.minute,
        "commands": len(life.commands), "ledger_events": len(life.world.ledger),
        "final_state_hash": before, "journal_sha256": file_hash(journal), "exact_restart": True,
        "metrics": life.metrics(), "checkpoints": checkpoints,
        "v3_decision_counts": {a: sum(e.actors[0] == a for e in decisions) for a in sorted(actors)},
        "player_commitments": copy.deepcopy(life.world.economy.commitments["Player"]),
        "affiliation": life.world.flags["affiliation"],
        "execution_and_exact_restart_seconds": time.perf_counter() - start,
        "limits": ["This is a bounded authored historical-fiction continuation, not a generated human biography.",
            "The player accepts one delivery, misses it, then keeps a separate service agreement. Later state persists through exact scheduled events.",
            "Six V3 minds select declared existing options; this does not imply six unconstrained LLM planners.",
            "This demonstrates months of causal continuity, not measured human subjective duration or multi-month cognitive superiority."]}
    write_json(directory / "summary.json", summary)
    return summary


def run_demo(output, *, commons_days=90, pompeii_days=120):
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    from .cognition_bench import source_fingerprints
    sources = source_fingerprints()
    sources.update({name: file_hash(ROOT / name) for name in (
        "kalends/experience_os/life_demo.py", "kalends/experience_os/runtime.py",
        "kalends/experience_os/temporal.py", "kalends_rebirth/world.py",
        "kalends/pompeii/world.py", "specs/pompeii_life.json")})
    manifest = {"classification": "Recorded scripted demonstration, not a registered cognition experiment",
        "source_fingerprints_before": sources, "commons_days": commons_days, "pompeii_days": pompeii_days}
    write_json(output / "execution_manifest.json", manifest)
    summary = {"commons": run_commons(output / "commons", days=commons_days)}
    if pompeii_days:
        summary["pompeii"] = run_pompeii(output / "pompeii", days=pompeii_days)
    manifest["source_fingerprints_after"] = {name: file_hash(ROOT / name) for name in sources}
    manifest["source_stable_during_execution"] = manifest["source_fingerprints_after"] == sources
    if manifest["source_stable_during_execution"]:
        archive = output / "frozen_sources.zip"
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as source_zip:
            for name in sources:
                source_zip.writestr(name, (ROOT / name).read_bytes())
        manifest["source_archive_sha256"] = file_hash(archive)
    write_json(output / "execution_manifest.json", manifest)
    write_json(output / "summary.json", summary)
    report = ["# Recorded long-life demonstrations", "", "These are reproducible scripted trajectories on the compiled runtime, with actual accepted commands and events. No biography text was invented.", ""]
    for adapter, result in summary.items():
        report += [f"## {adapter.title()}", "", f"{result['elapsed_days']} elapsed simulated days; {result['commands']} accepted commands; {result['ledger_events']} actual ledger events.", "",
            "```json", json.dumps(result["metrics"], indent=2), "```", ""]
    report += ["The Commons branch omits one actual accepted allocation and replays the remaining declared commands to the same horizon; the original journal is byte-preserved. Operator checkpoints deliberately expose private state only for audit. The Player controller uses actual disclosed report content.", "",
        "Exact restart checks preserve each checkpoint. See accepted_journal.json, validated_spec.json, round_history.json, personal_history.json and actual_omission.json under each applicable adapter directory. The Pompeii life also retains six-agent operator decision records.", "",
        "These artifacts demonstrate causal continuity and a small institutional threshold. They do not validate human learning, general intelligence, subjective time acceleration, an open-ended career system or generated lifetimes."]
    (output / "REPORT.md").write_text("\n".join(report) + "\n")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commons-days", type=int, default=90)
    parser.add_argument("--pompeii-days", type=int, default=120)
    args = parser.parse_args()
    result = run_demo(args.output, commons_days=args.commons_days, pompeii_days=args.pompeii_days)
    print(json.dumps({k: {"elapsed_days": r["elapsed_days"], "commands": r["commands"], "ledger_events": r["ledger_events"]} for k, r in result.items()}))


if __name__ == "__main__":
    main()
