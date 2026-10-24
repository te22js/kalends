# Independent preservation review

Recorded: 2026-10-24T16:39:06.343249+00:00. Reviewer: fresh-probe subagent, after completing the UI-only walkthrough. This followup used read-only filesystem/Git inspection and wrote only this report and results/redesign/preservation-review.json. No save, baseline, guard, implementation, branch, or release reference was changed.

The redesign baseline is fully preserved: **1,270 of 1,270 recorded files match SHA-256**. These comprise 31 files under .kalends and 1239 other recorded artifacts. The older protection baseline matches **2,212 of 2,212 historical artifacts** and **25 of 26 saves**.

## Exact older-baseline exception

The only difference is .kalends/next_phase/.product/state.json, a display/seen-position metadata file identified by the existing guard. It is valid JSON. Its current bytes match the redesign baseline exactly, so this review found no change to that file since the redesign baseline was recorded. This is not a strict pass against the older baseline, and the origin of the prior change remains unconfirmed.

| Reference | SHA-256 |
|---|---|
| Older protection baseline | 0cdb830008ec591def54ad4b0683c4035f2d73bdc97926af5aeffb26b1326f2b |
| Earlier metadata-drift acknowledgement | 6b03e2d3bd1c8b90f069724c54a8e26d870fd2d6c21fb2ef503e05472e5991c3 |
| Redesign baseline and current bytes | 95dcfcc40b28b175d090437f197583a527dbd47bb7d12b50a8ea6644ac45f3ac |

The current hash differs from the earlier acknowledgement as well as from the original old baseline. I did not expand the acknowledgement, reset metadata, or change either baseline to conceal this difference. All other protected saves match the older baseline.

## Release reference and frozen candidate

The protected branch refs/heads/codex/experience-journey still points to **6ebe9ec463c0144ba4ce53cb182646f5bf87f152**, matching both preservation baselines and candidate_freeze.json. The current working branch is codex/complete-experience-redesign at 377a7277436549b63ccb559f449e5d1d087cff03; the redesign baseline's starting commit is 377a7277436549b63ccb559f449e5d1d087cff03.

All **four frozen candidate dependency files** match their recorded hashes. Their Git objects at the protected release commit have the same hashes as well. The repository's verify_candidate() function passed. The observed candidate configuration matches the frozen parameters: capacity 16 records, context 4 records, hybrid retention, 16,384 state bytes, and 4,096 context bytes.

The candidate manifest's implementation_sha256 field was retained in the machine-readable review. Its hash derivation is not documented by the inspected verifier, so this audit does not claim to independently reproduce that particular digest. Exact matching of every frozen dependency file and its protected release object verifies the candidate source preservation directly.

All **19 frozen research source/artifact entries** match. The heldout file's bytes match the frozen SHA-256 (9e0c8a1e05a85129e010f0237ddef98296e24161b323e70517272d08727bc644), and the recorded run seeds match the freeze. I hashed the task file without inspecting its cases, and did not rerun or retune the study. These are preservation checks, not a fresh validation of research conclusions.

## Existing branch-specific guard

Running the unmodified command PYTHONDONTWRITEBYTECODE=1 python3 scripts/verify_continuity_release.py exited 1 with:

> Use the isolated release-preparation branch: codex/continuity-release-prep

That guard intentionally targets the old preparation branch. I did not change branches, modify the guard, bypass its condition, or report it as passed. The independent hash checks above are a separate review of the new redesign branch.

## Inputs and limits

| Input | SHA-256 |
|---|---|
| results/redesign/baseline.json | a45438f348ffb9aa82e3dee2a955d92ac12e2984dd2c0f3e64f3cd2bb6a3a05c |
| results/continuity_release/protection/baseline.json | 9e35974d1d4c39b0524f0a5388e0c0425e4664c7f75ea85775db96eeb87e650a |
| results/continuity_release/candidate_freeze.json | 587cef8593f43ca112cd688aaa03902b345168ff3237f669821dbe5280207ffa |
| results/continuity_release/research_freeze.json | 0323074f57f1e89bbc649bbf72859843a5235febc973e2f3d6f80396006cf34d |

This is a snapshot-time audit. It does not prove gameplay correctness, historical accuracy, research validity, human comprehension, or future preservation. Detailed counts, expected/actual mismatches, release reference checks, and candidate parameters are recorded in [preservation-review.json](../../results/redesign/preservation-review.json).
