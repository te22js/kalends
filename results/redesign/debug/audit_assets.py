"""Read-only local provenance check; does not establish rendered legibility.
Run: python3 results/redesign/debug/audit_assets.py
"""
from pathlib import Path
import json,hashlib,struct
ROOT=Path(__file__).resolve().parents[3]
root=ROOT/'kalends_3d'
p=json.loads((root/'ASSET_PROVENANCE.json').read_text())
errors=[]
for f in p['files']:
 q=root/f['file']
 if not q.exists(): errors.append({'path':str(q.relative_to(ROOT)),'problem':'missing'})
 elif hashlib.sha256(q.read_bytes()).hexdigest()!=f['sha256']: errors.append({'path':str(q.relative_to(ROOT)),'problem':'hash differs'})
licenses=[]
for name,g in p['source_groups'].items():
 licenses.append({'group':name,'license':g.get('license'),'notices':[{'path':str((root/f).relative_to(ROOT)),'exists':(root/f).exists()} for f in g.get('license_files',[])]})
models=[]
for path in (root/'assets/environment').glob('*.glb'):
 b=path.read_bytes();length,kind=struct.unpack_from('<II',b,12)
 assert b[:4]==b'glTF' and kind==0x4e4f534a
 doc=json.loads(b[20:20+length]);names=[n.get('name') for n in doc.get('nodes',[])]
 models.append({'path':str(path.relative_to(ROOT)),'node_count':len(names),'node_names':names})
result={'checked_date':'2026-10-24','scope':'Local source/asset audit; not native visual legibility or legal certification','manifest_file_count':len(p['files']),'manifest_mismatches':errors,'source_groups':licenses,'environment_models':models,'no_external_images_imported_by_this_review':True}
(ROOT/'results/redesign/debug/source_asset_audit.json').write_text(json.dumps(result,indent=2)+'\n')
assert not errors
assert all(n['exists'] for g in licenses for n in g['notices'])
print(json.dumps({'manifest_files':len(p['files']),'mismatches':len(errors),'license_notices_present':True,'environment_nodes':sum(m['node_count'] for m in models)}))
