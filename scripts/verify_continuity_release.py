"""Read-only local release guard. No hosted branch protection is configured."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / 'results/continuity_release/protection/baseline.json'


def verify():
    baseline = json.loads(BASELINE.read_text())
    branch = subprocess.check_output(['git','branch','--show-current'],cwd=ROOT,text=True).strip()
    if branch != baseline['working_branch']:
        raise SystemExit('Use the isolated release-preparation branch: ' + baseline['working_branch'])
    release = subprocess.check_output(['git','rev-parse','codex/experience-journey'],cwd=ROOT,text=True).strip()
    if release != baseline['release_commit']:
        raise SystemExit('Protected verified release ref changed')
    counts = {}
    drift_file = BASELINE.parent / 'external_metadata_drift.json'
    drift = json.loads(drift_file.read_text())['changes'] if drift_file.exists() else []
    acknowledged = {r['path']:r['observed_sha256'] for r in drift
                    if r['path'] == '.kalends/next_phase/.product/state.json' and r['group'] == 'saves'}
    for group in ('saves','historical_artifacts'):
        failures = [path for path, expected in baseline[group].items()
                    if not (ROOT/path).is_file() or hashlib.sha256((ROOT/path).read_bytes()).hexdigest() != acknowledged.get(path, expected)]
        if failures:
            raise SystemExit('Preservation check failed for ' + group + ': ' + ', '.join(failures))
        counts[group] = len(baseline[group])
    from kalends.continuity_release.evaluation import verify_candidate
    verify_candidate()
    return {'branch':branch, 'release_commit':release, 'checked':counts,
            'acknowledged_external_metadata_drift':list(acknowledged), 'candidate':'frozen'}

if __name__ == '__main__':
    print(json.dumps(verify(),indent=2))
