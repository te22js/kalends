#!/usr/bin/env python3
"""Build a fresh local staging bundle. Never reads or copies existing saves."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kalends.experience_os.demo_server import static_files


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',required=True,type=Path)
    a=p.parse_args(); dest=a.destination.absolute()
    if dest.exists():p.error('Destination must not exist. Existing instances and saves are never overwritten.')
    if not (ROOT/'kalends_3d/dist/index.html').exists():p.error('Build the retained 3D client first.')
    tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
    sources={ROOT/name for name in tracked if name and Path(name).parts[0] in ('kalends','kalends_rebirth') and Path(name).suffix in ('.py','.json') and '/static/' not in name}
    sources.update(static_files().values())
    sources.update([ROOT/'kalends/experience_os/demo_server.py', ROOT/'kalends/experience_os/static/product/index.html',ROOT/'kalends_3d/dist/index.html',ROOT/'requirements-demo.txt'])
    sources.update((ROOT/'kalends_3d/assets/licenses').glob('*.txt'))
    sources.add(ROOT/'kalends_3d/ASSET_LICENSES.md')
    # Specs are checked-in scenario definitions, not runtime journals.
    sources.update((ROOT/'specs').glob('*.json'))
    for source in sources:
        if not source.is_file() or source.is_symlink() or any(parent.is_symlink() for parent in source.parents if parent!=ROOT):
            p.error('Bundle source missing or symlinked: '+str(source.relative_to(ROOT)))
    os.umask(0o077);dest.mkdir(parents=True,exist_ok=False)
    manifest={}
    for source in sorted(sources):
        rel=source.relative_to(ROOT);target=dest/'app'/rel
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
        manifest[str(rel)]=hashlib.sha256(target.read_bytes()).hexdigest()
    (dest/'saves').mkdir()
    (dest/'DEMO_ONLY').write_text(json.dumps({'instance':str(uuid.uuid4()),'purpose':'temporary demo only'}))
    (dest/'bundle-manifest.json').write_text(json.dumps({'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'files':manifest},indent=2))
    (dest/'access.example.json').write_text(json.dumps(dict(version=1,enabled=False,allowed_emails=['tanmaygoswami1001@gmail.com'],origin='https://REPLACE_WITH_DEDICATED_HOST',team_domain='REPLACE.cloudflareaccess.com',audience='REPLACE_WITH_ACCESS_APPLICATION_AUD',not_before=0,expires_at=0),indent=2))
    print(f'Fresh bundle prepared: {dest}\n{len(manifest)} files. Zero saves copied. No access.json: startup remains blocked until configured.')

if __name__=='__main__':main()
