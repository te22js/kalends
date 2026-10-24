"""Post-exposure development diagnostic; never a new held-out evaluation.
Reads frozen artifacts, instruments unchanged evaluator in memory, writes only
this debug directory. No memory, controller, task, evaluator or budget tuning.
Run: python3 results/redesign/debug/diagnose_exhibit.py
"""
from pathlib import Path
import sys, json, gzip, hashlib, collections
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from kalends.continuity_release import evaluation as e

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
freeze=json.loads((ROOT/'results/continuity_release/research_freeze.json').read_text())
paths={p:ROOT/p for p in freeze['source_sha256']}
paths['specs/continuity_release/heldout.json']=ROOT/'specs/continuity_release/heldout.json'
paths.update({str(p.relative_to(ROOT)):p for p in (ROOT/'results/continuity_release/research/frozen_heldout').rglob('*') if p.is_file()})
before={k:sha(p) for k,p in paths.items()}
assert all(before[k]==v for k,v in freeze['source_sha256'].items())
assert before['specs/continuity_release/heldout.json']==freeze['heldout_sha256']
spec=next(c for c in json.loads(paths['specs/continuity_release/heldout.json'].read_text())['cases'] if c['id']=='h_exhibit_release')
summary=[]
for arm in e.ARMS:
 files=sorted((ROOT/'results/continuity_release/research/frozen_heldout/raw').glob(f'h_exhibit_release_*_{arm}.json.gz'))
 rows=[json.load(gzip.open(p)) for p in files]
 summary.append({'arm':arm,'cases':len(rows),'passes':sum(r['passed'] for r in rows),'assertion_failures':dict(collections.Counter(str(a['assertion']) for r in rows for a in r['assertions'] if not a['passed'])),'trajectories':dict(collections.Counter(' > '.join(t['decision']['action_id'] for t in r['trace'] if t['decision']['action_id']!='wait') for r in rows))})
# Observer-only instrumentation: copies retained record metadata; never inserts it
# into the controller or changes any return value.
original_observe=e.PersistentMind.observe
original_select=e.Controller.select
losses=[];selections=[]
def observed(self, episode):
 old={r['serial']:dict(r) for r in self._all()}
 result=original_observe(self,episode)
 now={r['serial'] for r in self._all()}
 for serial,r in old.items():
  if serial not in now and r.get('predicate') in ('editor_approval','rights_approval'):
   losses.append({'at':episode.observed_at,'admitting_event':episode.event_id,'admitting_key':episode.key,'removed':r,'remaining_approval_records':[{k:z.get(k) for k in ('event_id','record_type','subject','predicate','value','accepted')} for z in self._all() if z.get('predicate') in ('editor_approval','rights_approval')],'record_count':len(self._all())})
 return result
def selected(self, goals, actions, public, credits, now):
 retained=[{k:r.get(k) for k in ('event_id','record_type','subject','predicate','value','accepted')} for r in self.mind._all()]
 result=original_select(self,goals,actions,public,credits,now)
 selections.append({'at':now,'retained_before':retained,'decision':result[0]})
 return result
e.PersistentMind.observe=observed;e.Controller.select=selected
runs=[]
for arm in e.ARMS:
 losses.clear();selections.clear()
 run=e.run_case(spec,1000,arm)
 frozen=json.load(gzip.open(ROOT/f'results/continuity_release/research/frozen_heldout/raw/h_exhibit_release_1000_{arm}.json.gz'))
 # Frozen batch adds replay_equal; all evaluator-produced fields must match.
 equal=e.canonical(run)==e.canonical({k:v for k,v in frozen.items() if k!='replay_equal'})
 assert equal, arm
 runs.append({'arm':arm,'seed':1000,'exact_frozen_result_equal':equal,'approval_record_losses':list(losses),'selection_snapshots':list(selections)})
e.PersistentMind.observe=original_observe;e.Controller.select=original_select
# Manual feasibility witness through unchanged authoritative action validation.
# This is an analyst-specified action schedule, NOT a memory arm or benchmark win.
world=e.WorkflowWorld(spec,1000)
manual=[]
for at, names in [(10080,['stage_three','finish_three']),(11520,['publish_three','store_private_annex'])]:
 world.advance(at)
 for name in names:
  action=next(a for a in spec['actions'] if a['id']==name)
  receipt=world.execute(action)
  manual.append({'at':at,'action':name,'receipt':receipt})
world.advance(spec['horizon_minutes'])
feasibility=e.score(spec,world)
assert all(a['passed'] for a in feasibility)
after={k:sha(p) for k,p in paths.items()}
assert before==after
out={'label':'POST-EXPOSURE DEVELOPMENT DIAGNOSTIC; NOT A NEW HELD-OUT RESULT','source_hashes_match_freeze':True,'checked_files':len(paths),'frozen_inputs_and_results_unchanged':before==after,'frozen_exhibit_100_execution_summary':summary,'unchanged_instrumented_seed_1000':runs,'manual_authoritative_feasibility_witness':{'limitation':'Analyst schedule checks task feasibility only; no bounded-memory-policy success claim. Original approval observations existed at minute 0; rejected unsigned statement did not change truth.','actions':manual,'assertions':feasibility},'protected_sha256':before}
(ROOT/'results/redesign/debug/exhibit_diagnosis.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'checked_files':len(paths),'unchanged':before==after,'instrumented_exact_matches':len(runs),'manual_feasibility_all_assertions':True,'summaries':summary},indent=2))
