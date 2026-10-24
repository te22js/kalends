#!/usr/bin/env python3
"""Start/stop only the prepared private ngrok demo, with no credential arguments."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from kalends.experience_os.demo_server import read_policy


def verify_bundle(directory):
    manifest=json.loads((directory/'bundle-manifest.json').read_text())['files']
    for relative,digest in manifest.items():
        path=directory/'app'/relative
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
            raise ValueError('Bundle changed; prepare a new instance before starting')


def matches(pid,marker):
    try:
        args=subprocess.check_output(['ps','-p',str(pid),'-o','command='],text=True)
        return marker in args
    except subprocess.CalledProcessError:return False


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['start','stop','status'])
    p.add_argument('--instance',type=Path,required=True)
    a=p.parse_args();os.umask(0o077);directory=a.instance.resolve();record=directory/'processes.json'
    if not (directory/'DEMO_ONLY').is_file():p.error('Use a prepared demo instance')
    processes=json.loads(record.read_text()) if record.exists() else {}
    if a.action in ('stop','status'):
        if a.action=='stop':
            # Revocation happens before process shutdown; existing OAuth cookies
            # no longer permit new requests, even if stopping a process fails.
            access=read_policy(directory/'access.json');access['enabled']=False
            temporary=directory/'access.stopping.json'
            with temporary.open('x') as f:json.dump(access,f,indent=2)
            temporary.replace(directory/'access.json')
        for name,pid in processes.items():
            marker=str(directory/'ngrok-traffic-policy.json') if name=='tunnel' else str(directory)
            alive=matches(pid,marker)
            if a.action=='stop' and alive:os.kill(pid,signal.SIGTERM)
            print(name+': '+('stop requested' if alive and a.action=='stop' else 'running' if alive else 'stopped'))
        return
    if any(matches(pid,str(directory)) for pid in processes.values()):p.error('Demo already has a running process; inspect status')
    verify_bundle(directory)
    policy=read_policy(directory/'access.json')
    if policy.get('provider') not in ('ngrok-oauth','ngrok-link') or not policy['enabled'] or policy['expires_at']<=time.time():p.error('Configure unexpired ngrok access first')
    os.umask(0o077)
    python=ROOT/'.kalends/demo-tools/venv/bin/python';agent=ROOT/'.kalends/demo-tools/ngrok'
    origin_log=(directory/'origin.log').open('ab');tunnel_log=(directory/'tunnel.log').open('ab')
    origin=subprocess.Popen([str(python),'-m','kalends.experience_os.demo_server','--instance',str(directory),'--port','8840'],
                            cwd=directory/'app',stdin=subprocess.DEVNULL,stdout=origin_log,stderr=subprocess.STDOUT,start_new_session=True)
    time.sleep(.5)
    if origin.poll() is not None:p.error('Origin did not start; inspect the private origin log')
    try:
        tunnel=subprocess.Popen([str(agent),'http','http://127.0.0.1:8840','--url',policy['origin'],
            '--config',str(ROOT/'.kalends/demo-tools/ngrok-auth.json'),'--traffic-policy-file',str(directory/'ngrok-traffic-policy.json'),
            '--inspect=false','--log=false'],stdin=subprocess.DEVNULL,stdout=tunnel_log,stderr=subprocess.STDOUT,start_new_session=True)
        record.write_text(json.dumps({'origin':origin.pid,'tunnel':tunnel.pid}))
    except Exception:
        origin.terminate();raise
    print('Started isolated demo processes. Public access tests are still required.')
    print(policy['origin'])

if __name__=='__main__':main()
