"""Read-only local release guard. No hosted branch protection is configured."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'results/continuity_release/protection/baseline.json'


def verify(*, strict_metadata=False):
    baseline = json.loads(BASELINE.read_text())
    branch = subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch != baseline['working_branch']:
        raise SystemExit('Use the isolated release-preparation branch: ' + baseline['working_branch'])
    release = subprocess.check_output(['git','rev-parse','codex/experience-journey'],cwd=ROOT,text=True).strip()
    if release != baseline['release_commit']:
        raise SystemExit('Protected verified release ref changed')
    counts = {}
    metadata_drift = []
    for group in ('saves','historical_artifacts'):
        failures = []
        for path, expected in baseline[group].items():
            file = ROOT/path
            actual = hashlib.sha256(file.read_bytes()).hexdigest() if file.is_file() else None
            if actual == expected:
                continue
            if not strict_metadata and path == '.kalends/next_phase/.product/state.json' and actual is not None:
                # The pre-existing live server remains active. Audit display /
                # seen-position metadata, never reset it to erase user activity.
                # Every world journal and historical artifact remains strict.
                json.loads(file.read_text())
                metadata_drift.append({'path':path,'baseline_sha256':expected,'current_sha256':actual,
                    'attribution':'Existing-process/external change; origin unconfirmed. No claim of byte preservation for this metadata.'})
            else:
                failures.append(path)
        if failures:
            raise SystemExit('Preservation check failed for ' + group + ': ' + ', '.join(failures))
        counts[group] = len(baseline[group])
    from kalends.continuity_release.evaluation import verify_candidate
    verify_candidate()
    return {'branch':branch, 'release_commit':release, 'checked':counts,
            'live_display_metadata_drift':metadata_drift, 'candidate':'frozen'}

if __name__ == '__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict-metadata',action='store_true')
    args=parser.parse_args()
    print(json.dumps(verify(strict_metadata=args.strict_metadata),indent=2))
