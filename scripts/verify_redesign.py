"""Read-only preservation checks for the complete-experience redesign branch.

Run with --replay-qa to replay version-1 journals from the designated disposable
QA directory in memory. This script never saves a world or updates a baseline.
JSON is written to stdout; callers choose whether to retain the report.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
BRANCH = "codex/complete-experience-redesign"
RELEASE_REF = "refs/heads/codex/experience-journey"
RELEASE_COMMIT = "6ebe9ec463c0144ba4ce53cb182646f5bf87f152"
BASELINE = ROOT / "results/redesign/baseline.json"
BASELINE_SHA256 = "a45438f348ffb9aa82e3dee2a955d92ac12e2984dd2c0f3e64f3cd2bb6a3a05c"
QA_ROOT = Path("/private/tmp/kalends-redesign-qa")
JOURNAL_FIELDS = {"version", "spec_hash", "spec", "retention", "commands", "state_hash"}
COMMAND_FIELDS = {"revision", "operation", "data", "at", "after", "receipt_id"}


def file_sha256(path):
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git(*arguments):
    return subprocess.check_output(["git", *arguments], cwd=ROOT, text=True).strip()


def verify_files(entries):
    """Compare every recorded byte hash; no metadata exceptions or repairs."""
    if not isinstance(entries, dict) or not entries:
        raise ValueError("The redesign baseline must contain a nonempty file map")
    differences = []
    for relative, expected in entries.items():
        path = ROOT / relative
        if (not isinstance(expected, str) or len(expected) != 64 or
                not path.resolve().is_relative_to(ROOT)):
            raise ValueError("Invalid redesign baseline entry: " + relative)
        actual = file_sha256(path)
        if actual != expected:
            differences.append({"path": relative, "expected_sha256": expected,
                                "actual_sha256": actual,
                                "mtime_utc": (datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat()
                                              if path.is_file() else None)})
    return {"checked": len(entries), "matched": len(entries) - len(differences),
            "differences": differences, "passed": not differences}


def replay_qa_journal(path):
    """Replay captured QA bytes without ever assigning a persistence path.

    The version-1 validation mirrors ExperienceRuntime.__init__: command start
    and end times, receipt identity, and final fidelity hash must all match.
    The normal compiler and canonical _perform actions remain authoritative.
    """
    from kalends.experience_os.runtime import ExperienceRuntime, digest

    if path.is_symlink() or path.parent.resolve() != QA_ROOT.resolve():
        raise ValueError("QA replay refuses symlinks or paths outside its disposable root")
    original = path.read_bytes()
    document = json.loads(original)
    if (not isinstance(document, dict) or set(document) != JOURNAL_FIELDS or
            type(document["version"]) is not int or document["version"] != 1 or
            not isinstance(document["spec"], dict) or
            not isinstance(document["spec"].get("setting"), dict) or
            document["spec"].get("setting", {}).get("adapter") not in {"pompeii", "commons"} or
            not isinstance(document["commands"], list) or
            not isinstance(document["retention"], str)):
        raise ValueError("Unsupported QA journal schema; no replay attempted")

    class ReadOnlyReplay(ExperienceRuntime):
        def save(self):
            raise RuntimeError("QA verification cannot save")

        def commit(self, *args, **kwargs):
            raise RuntimeError("QA verification cannot commit")

    runtime = ReadOnlyReplay(document["spec"], retention=document["retention"])
    if (runtime.journal_path is not None or document["spec_hash"] != runtime.spec_hash or
            digest(document["spec"]) != runtime.spec_hash or path.stem != runtime.spec.id):
        raise ValueError("QA journal identity or compiled specification differs")
    for index, command in enumerate(document["commands"]):
        if (not isinstance(command, dict) or set(command) != COMMAND_FIELDS or
                type(command["revision"]) is not int or command["revision"] != 1 or
                command["operation"] not in {"action", "advance"} or
                not isinstance(command["data"], dict) or type(command["at"]) is not int or
                command["at"] != runtime.minute):
            raise ValueError(f"Unsupported QA command or start time at index {index}")
        receipt = runtime._perform(command["operation"], copy.deepcopy(command["data"]))
        receipt_id = receipt.get("event_id") if isinstance(receipt, dict) else None
        if (type(command["after"]) is not int or command["after"] != runtime.minute or
                type(command["receipt_id"]) is not type(receipt_id) or
                command["receipt_id"] != receipt_id):
            raise ValueError(f"QA command end time or receipt differs at index {index}")
        runtime.commands.append(copy.deepcopy(command))
    actual_state = runtime.state_hash()
    if actual_state != document["state_hash"]:
        raise ValueError("QA accepted-command replay has a different final state")
    if path.read_bytes() != original:
        raise ValueError("QA source changed during the check; rerun when that life is idle")
    return {"path": str(path), "life_id": runtime.spec.id,
            "adapter": runtime.spec.setting["adapter"], "commands": len(runtime.commands),
            "minute": runtime.minute, "state_hash": actual_state,
            "journal_sha256": hashlib.sha256(original).hexdigest(),
            "exact_replay": True, "source_bytes_unchanged": True,
            "persistence_path": None}


def verify(*, replay_qa=False, qa_lives=()):
    if sys.version_info < (3, 10):
        raise ValueError("Kalends requires Python 3.10 or newer. Use the same interpreter as the app runner for exact replay.")
    result = {"recorded_utc": datetime.now(timezone.utc).isoformat(),
              "status": "failed", "read_only": True, "errors": [],
              "interpreter": {"executable": sys.executable, "version": platform.python_version(),
                              "implementation": platform.python_implementation()}}
    branch, release = git("branch", "--show-current"), git("rev-parse", RELEASE_REF)
    result.update(branch=branch, head=git("rev-parse", "HEAD"),
                  protected_release={"ref": RELEASE_REF, "expected": RELEASE_COMMIT,
                                     "actual": release})
    if branch != BRANCH:
        raise ValueError("Use the isolated redesign branch: " + BRANCH)
    if release != RELEASE_COMMIT:
        raise ValueError("Protected verified release ref changed")
    baseline_bytes = BASELINE.read_bytes()
    if hashlib.sha256(baseline_bytes).hexdigest() != BASELINE_SHA256:
        raise ValueError("The recorded redesign baseline itself changed")
    baseline = json.loads(baseline_bytes)
    if baseline.get("release_ref") != RELEASE_COMMIT:
        raise ValueError("Redesign baseline declares a different protected release")
    result["baseline"] = {"path": str(BASELINE.relative_to(ROOT)),
                          "sha256": hashlib.sha256(baseline_bytes).hexdigest(),
                          **verify_files(baseline.get("files"))}
    if not result["baseline"]["passed"]:
        result["errors"].append("Strict redesign baseline preservation failed")

    from kalends.continuity_release.evaluation import verify_candidate
    try:
        verify_candidate()
        result["frozen_candidate"] = {"verify_candidate": "passed"}
    except (ValueError, OSError) as error:
        result["frozen_candidate"] = {"verify_candidate": "failed", "error": str(error)}
        result["errors"].append("Frozen candidate verification failed")

    requested = replay_qa or bool(qa_lives)
    result["qa_replays"] = {"requested": requested, "root": str(QA_ROOT),
                            "selection": list(qa_lives) if qa_lives else "all" if requested else [], "journals": []}
    if requested:
        if QA_ROOT.is_symlink() or not QA_ROOT.is_dir():
            raise ValueError("The designated disposable QA directory is missing or a symlink")
        if any(not re.fullmatch(r"[a-z][a-z0-9_]{0,79}", ident) for ident in qa_lives):
            raise ValueError("QA life selectors must be plain compiled life identities")
        journals = ([QA_ROOT / (ident + ".json") for ident in sorted(set(qa_lives))]
                    if qa_lives else sorted(QA_ROOT.glob("*.json")))
        if not journals:
            raise ValueError("No disposable QA journals were found")
        for path in journals:
            try:
                result["qa_replays"]["journals"].append(replay_qa_journal(path))
            except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
                result["qa_replays"]["journals"].append(
                    {"path": str(path), "exact_replay": False, "error": str(error)})
                result["errors"].append("QA replay failed: " + path.name)
    if BASELINE.read_bytes() != baseline_bytes:
        result["errors"].append("Baseline changed while verification was running")
    result["status"] = "failed" if result["errors"] else "passed"
    result["scope"] = ("Strict redesign baseline, protected release, frozen candidate, and only "
                       "the explicitly requested disposable QA journals. Existing branch-specific "
                       "guards and older baselines are neither modified nor reported as passed.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-qa", action="store_true",
                        help="replay known version-1 journals from /private/tmp/kalends-redesign-qa in memory")
    parser.add_argument("--qa-life", action="append", default=[], metavar="ID",
                        help="replay only this idle disposable QA life; repeat to select several")
    arguments = parser.parse_args()
    try:
        result = verify(replay_qa=arguments.replay_qa, qa_lives=arguments.qa_life)
    except (ValueError, OSError, TypeError, KeyError, subprocess.CalledProcessError) as error:
        result = {"status": "failed", "read_only": True, "errors": [str(error)]}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
