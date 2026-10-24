#!/usr/bin/env python3
"""Configure an isolated demo for Google OAuth or owner-authorized public links.

Only local private files change. The explicit email list is enforced twice:
ngrok denies other OAuth identities, and the origin checks the authenticated
identity plus an independent instance-specific ingress credential.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kalends.experience_os.demo_server import read_policy


def configuration(origin, emails, hours=24, *, credential=None, public=False):
    credential=credential or secrets.token_hex(32)
    now=int(time.time())
    access=dict(version=2,provider='ngrok-oauth',enabled=True,allowed_emails=emails,origin=origin,
                ingress_secret_sha256=hashlib.sha256(credential.encode()).hexdigest(),
                not_before=now-60,expires_at=now+hours*3600)
    # An absent identity fails closed. Do not copy the incoming email header.
    allow=json.dumps(emails,ensure_ascii=True)
    traffic={'on_http_request':[
        {'actions':[{'type':'oauth','config':{'provider':'google'}}]},
        {'expressions':[f'actions.ngrok.oauth.identity == null || !(actions.ngrok.oauth.identity.email in {allow})'],
         'actions':[{'type':'deny','config':{'status_code':403}}]},
        {'actions':[
            {'type':'remove-headers','config':{'headers':['x-kalends-demo-ingress','x-kalends-demo-email','cf-access-jwt-assertion','cf-access-authenticated-user-email']}},
            {'type':'add-headers','config':{'headers':{'x-kalends-demo-ingress':credential,
                'x-kalends-demo-email':'${actions.ngrok.oauth.identity.email}'}}}]}]}
    if public:
        access.update(version=3,provider='ngrok-link');access.pop('allowed_emails')
        traffic={'on_http_request':[traffic['on_http_request'][2]]}
        traffic['on_http_request'][0]['actions'][1]['config']['headers'].pop('x-kalends-demo-email')
    return access,traffic


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--instance',required=True,type=Path)
    p.add_argument('--origin',required=True);p.add_argument('--email',action='append');p.add_argument('--public',action='store_true',help='Public link access, explicitly requested by the owner')
    p.add_argument('--hours',type=int,default=24)
    a=p.parse_args();directory=a.instance.resolve()
    if not (directory/'DEMO_ONLY').is_file():p.error('Use a separate prepared demo instance')
    if not 1<=a.hours<=167:p.error('Choose 1–167 hours')
    if bool(a.email)==a.public:p.error('Choose --public OR exact --email addresses')
    access,traffic=configuration(a.origin,a.email or [],a.hours,public=a.public)
    os.umask(0o077)
    temporary=directory/'access.pending.json'
    with temporary.open('x') as f:json.dump(access,f,indent=2)
    try:read_policy(temporary)
    except Exception:
        temporary.unlink();raise
    policy_path=directory/'ngrok-traffic-policy.json'
    if policy_path.is_symlink() or (directory/'access.json').is_symlink():p.error('Policy files must not be symlinks')
    # Rotate the origin credential first: any old running tunnel immediately loses
    # access until it is restarted with the new policy. A partial update is closed.
    temporary.replace(directory/'access.json')
    with policy_path.open('w') as f:json.dump(traffic,f,indent=2)
    policy_path.chmod(0o600);(directory/'access.json').chmod(0o600)
    print('Configured temporary ngrok origin: '+a.origin)
    print('Access: anyone with the link' if a.public else 'Allowed: '+', '.join(a.email))
    print('Expires: '+time.strftime('%Y-%m-%d %H:%M:%S UTC',time.gmtime(access['expires_at'])))
    print('Private ingress credential saved locally; omitted from output.')

if __name__=='__main__':main()
