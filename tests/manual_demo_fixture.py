"""LOOPBACK ONLY browser fixture. Never tunnel this test process.

Uses the bundled production handler and ephemeral RSA test credentials. It does
not provide evidence of Cloudflare/public authentication. Not shipped in bundle.
"""
import argparse
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
from types import SimpleNamespace

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--bundle',required=True,type=Path);p.add_argument('--qa-directory',type=Path);a=p.parse_args()
sys.path.insert(0,str(a.bundle.resolve()/'app'))
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from kalends.experience_os.demo_server import AccessVerifier, DemoServer, restricted_handler
from kalends.experience_os.product import ProductService
key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
qa=a.qa_directory or Path(tempfile.mkdtemp(prefix='kalends-mentor-browser-qa-'))
if not qa.name.startswith('kalends-mentor-browser-qa-'):raise ValueError('Use an isolated QA directory')
policy=dict(version=1,enabled=True,allowed_emails=['qa@example.com'],origin='https://demo.example.com',team_domain='qa.cloudflareaccess.com',audience='a'*64,not_before=int(time.time())-10,expires_at=int(time.time())+3600)
policy_path=qa/'access.json';policy_path.write_text(json.dumps(policy))
verifier=AccessVerifier(clients={'https://qa.cloudflareaccess.com':SimpleNamespace(get_signing_key_from_jwt=lambda token:SimpleNamespace(key=key.public_key()))})
service=ProductService(qa/'saves',include_examples=False)
origin=DemoServer(('127.0.0.1',8841),restricted_handler(service,policy_path,verifier))
threading.Thread(target=origin.serve_forever,daemon=True).start()
class Gateway(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def relay(self):
        if self.headers.get('Host')!='127.0.0.1:8842' or self.headers.get('Cf-Access-Jwt-Assertion'):
            self.send_error(403);return
        if self.command=='POST' and self.headers.get('Origin')!='http://127.0.0.1:8842':self.send_error(403);return
        size=int(self.headers.get('Content-Length',0))
        if size>32768:self.send_error(413);return
        claims=dict(iss='https://qa.cloudflareaccess.com',aud='a'*64,sub='qa',email='qa@example.com',iat=int(time.time()),exp=int(time.time())+300)
        headers={'Host':'demo.example.com','Origin':policy['origin'],'Cf-Access-Jwt-Assertion':jwt.encode(claims,key,algorithm='RS256'),'Content-Type':self.headers.get('Content-Type','application/json')}
        conn=http.client.HTTPConnection('127.0.0.1',origin.server_port,timeout=30)
        conn.request(self.command,self.path,body=self.rfile.read(size) if size else None,headers=headers)
        r=conn.getresponse();body=r.read();self.send_response(r.status)
        for k,v in r.getheaders():
            if k.lower() not in ('connection','server','date'):self.send_header(k,v)
        self.end_headers();self.wfile.write(body);conn.close()
    do_GET=relay;do_POST=relay
print('LOCAL QA ONLY at http://127.0.0.1:8842/ — never tunnel. Saves: '+str(qa),flush=True)
try:ThreadingHTTPServer(('127.0.0.1',8842),Gateway).serve_forever()
finally:origin.shutdown();origin.server_close()
