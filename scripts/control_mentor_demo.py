#!/usr/bin/env python3
"""Local configuration/revocation only. This creates no Cloudflare resources."""
import argparse
import json
import os
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kalends.experience_os.demo_server import read_policy

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('action',choices=['configure','revoke','status'])
p.add_argument('--instance',type=Path,required=True)
p.add_argument('--origin');p.add_argument('--team-domain');p.add_argument('--audience')
p.add_argument('--email',action='append');p.add_argument('--hours',type=int,default=24)
a=p.parse_args();directory=a.instance.resolve()
if not (directory/'DEMO_ONLY').is_file():p.error('Not a prepared demo instance')
path=directory/'access.json'
if path.is_symlink():p.error('Policy must not be a symlink')
if a.action=='configure':
    if not all([a.origin,a.team_domain,a.audience,a.email]) or not 1<=a.hours<=167:p.error('Supply origin, team-domain, audience, exact email(s), and 1–167 hours')
    policy=dict(version=1,enabled=True,allowed_emails=a.email,origin=a.origin,team_domain=a.team_domain,audience=a.audience,not_before=int(time.time())-60,expires_at=int(time.time())+a.hours*3600)
else:
    if not path.exists():
        print('Closed: no configured access policy.');sys.exit(0)
    policy=read_policy(path)
    if a.action=='revoke':policy['enabled']=False
if a.action!='status':
    os.umask(0o077)
    temp=directory/'access.pending.json'
    with temp.open('x') as f:json.dump(policy,f,indent=2)
    try:read_policy(temp)
    except Exception:
        temp.unlink();raise
    temp.replace(path)
print('Access '+('enabled' if policy['enabled'] and time.time()<policy['expires_at'] else 'closed')+'.')
print('Origin: '+policy['origin'])
print('Access: anyone with the link' if policy.get('provider')=='ngrok-link' else 'Allowlist: '+', '.join(policy['allowed_emails']))
print('Expires: '+time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime(policy['expires_at'])))
