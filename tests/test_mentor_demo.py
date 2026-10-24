"""Real HTTP tests with signed RSA tokens; no production authentication bypass."""
import http.client
import json
import threading
import time
from types import SimpleNamespace

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from kalends.experience_os.demo_server import AccessVerifier, DemoServer, restricted_handler
from kalends.experience_os.product import ProductService


@pytest.fixture
def demo(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    policy = dict(version=1, enabled=True, allowed_emails=['owner@example.com'], origin='https://demo.example.com',
                  team_domain='qa.cloudflareaccess.com', audience='a'*64, not_before=int(time.time())-10,
                  expires_at=int(time.time())+3600)
    path = tmp_path/'access.json'; path.write_text(json.dumps(policy))
    verifier = AccessVerifier(clients={'https://qa.cloudflareaccess.com': SimpleNamespace(
        get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key()))})
    service = ProductService(tmp_path/'fresh-demo-saves', include_examples=False)
    server = DemoServer(('127.0.0.1',0), restricted_handler(service,path,verifier))
    thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    def token(**changes):
        claims=dict(iss='https://qa.cloudflareaccess.com',aud='a'*64,sub='qa-owner',email='owner@example.com',
                    iat=int(time.time()),exp=int(time.time())+1200)
        claims.update(changes)
        return jwt.encode(claims,key,algorithm='RS256')
    def request(url='/', data=None, *, auth=True, credential=None, headers=None, method=None, raw=None):
        h={'Host':'demo.example.com','Origin':policy['origin'],'Content-Type':'application/json'}
        if auth:h['Cf-Access-Jwt-Assertion']=credential or token()
        h.update(headers or {})
        body=raw if raw is not None else json.dumps(data) if data is not None else None
        conn=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=20)
        conn.request(method or ('POST' if body is not None else 'GET'),url,body=body,headers=h)
        r=conn.getresponse();payload=r.read();status=r.status;response_headers=dict(r.getheaders());conn.close()
        try:payload=json.loads(payload)
        except ValueError:pass
        return status,payload,response_headers
    yield SimpleNamespace(request=request,token=token,policy=policy,path=path,service=service)
    server.shutdown();server.server_close();thread.join()


def test_all_assets_require_signed_identity(demo):
    for path in ['/', '/product/app.js','/demo-shell.js','/immersion-assets/characters/roman_male.glb','/product/api/catalog']:
        assert demo.request(path,auth=False)[0]==401
    assert demo.request()[0]==200
    assert demo.request(headers={'Cf-Access-Authenticated-User-Email':'owner@example.com'},auth=False)[0]==401
    for claims in [dict(email='stranger@example.com'),dict(aud='b'*64),dict(iss='https://evil.example.com'),dict(exp=1),dict(iat=int(time.time())-4000)]:
        assert demo.request(credential=demo.token(**claims))[0]==401
    forged=jwt.encode(dict(email='owner@example.com'), 'not-a-real-signing-key-long-enough',algorithm='HS256')
    assert demo.request(credential=forged)[0]==401
    assert demo.request(headers={'Host':'localhost'})[0]==403


@pytest.mark.parametrize('path',['/lab/x','/studio','/research','/research/artifacts/assets','/os/catalog','/os/state','/api/mode','/.git/config','/access.json','/product/../../README.md','/%2e%2e/access.json','//studio','/product/api/trace','/product/api/reflect','/product/api/research','/api/state?experience=pompeii_life'])
def test_protected_reads_are_denied_to_authenticated_owner(demo,path):
    assert demo.request(path)[0]==404


@pytest.mark.parametrize('operation',['lab','studio/compile','studio/validate','fork','practice','annotation','telemetry','export','admin'])
def test_protected_writes_are_denied(demo,operation):
    assert demo.request('/product/api/'+operation,{'id':'pompeii_life','acknowledged':True})[0]==404


def test_csrf_ambiguity_and_revocation(demo):
    start={'template_id':'pompeii_life','guided':True}
    assert demo.request('/product/api/start',start,headers={'Origin':'https://evil.example'})[0]==403
    assert demo.request('/product/api/start',start,headers={'Sec-Fetch-Site':'cross-site'})[0]==403
    assert demo.request('/product/api/start',raw='{"template_id":"pompeii_life","template_id":"shared_observatory"}')[0]==400
    credential=demo.token()
    demo.policy['enabled']=False;demo.path.write_text(json.dumps(demo.policy))
    assert demo.request(credential=credential)[0]==503
    demo.policy['enabled']=True;demo.policy['allowed_emails']=['mentor@example.com'];demo.path.write_text(json.dumps(demo.policy))
    assert demo.request(credential=credential)[0]==401
    demo.path.unlink()
    assert demo.request(credential=credential)[0]==503


def test_rate_limit(demo):
    for _ in range(2):assert demo.request('/product/api/start',{'template_id':'pompeii_life'})[0]==200
    status,_,headers=demo.request('/product/api/start',{'template_id':'pompeii_life'})
    assert status==429 and headers['Retry-After']=='15'


def test_both_guides_real_accepted_actions_and_fresh_saves(demo):
    assert demo.request('/product/api/catalog')[1]['lives']==[]
    def post(route,body):
        status,data,_=demo.request('/product/api/'+route,body)
        assert status==200,data
        return data
    def act(ident,action):
        review=post('propose',{'id':ident,'action':action})
        return post('confirm',{'id':ident,'proposal_id':review['proposal_id']})
    p=post('start',{'template_id':'pompeii_life','guided':True})['life']['id']
    post('guide',{'id':p,'ack':'role_arrival'})
    act(p,{'action':'move','location':'street','x':750,'y':430})
    act(p,{'action':'examine_receipt','recipient':'Sabina'})
    result=act(p,{'action':'support_market','recipient':'Sabina'})
    assert result['guide']['result']['delivered']=={'Sabina':4,'Felix':2}
    assert demo.request('/api/state?experience='+p)[0]==200
    assert demo.request('/immersion/?experience='+p)[0]==200
    o=post('start',{'template_id':'shared_observatory','guided':True})['life']['id']
    post('guide',{'id':o,'ack':'role_arrival'});post('guide',{'id':o,'ack':'request_read'})
    act(o,{'action':'share','recipient':'team_b'})
    act(o,{'action':'commit','recipient':'team_c','quantity':4})
    act(o,{'action':'allocate','allocation':{'team_a':4,'team_b':4,'team_c':4}})
    result=post('advance',{'id':o,'minutes':1439,'protect_known':False})
    assert result['guide']['result']['executed']=={'team_a':4,'team_b':4,'team_c':0}
    post('guide',{'id':o,'ack':'reflection_done'})
    assert post('resume',{'id':o})['guide']['step']['id']=='o7'
    assert demo.request('/product/api/life?id='+o+'&id='+p)[0]==404
    assert demo.request('/product/api/start',{'template_id':'pompeii_life','practice':True})[0] in (400,429)
    assert all(not v.get('operator_exposed') for v in demo.service.metadata.values())


def test_participant_evidence_is_scoped_and_errors_redacted(demo):
    status,data,_=demo.request('/product/api/start',{'template_id':'pompeii_life','guided':True})
    assert status==200
    ident=data['life']['id'];runtime=demo.service.get(ident)
    visible=runtime.visible_ids()
    event=next(iter(visible))
    status,result,_=demo.request(f'/product/api/trace?id={ident}&event_id={event}')
    assert status==200
    assert all(e['event_id'] in visible for e in result['events'])
    assert demo.request(f'/product/api/trace?id={ident}&event_id={event}&mode=lab')[0]==404
    hidden=next((e['event_id'] for e in runtime.events(operator=True) if e['event_id'] not in visible),None)
    if hidden is not None:
        status,result,_=demo.request(f'/product/api/trace?id={ident}&event_id={hidden}')
        assert status>=400 or not result.get('events')
    def broken(*args,**kwargs):raise ValueError('/Users/private-person/secret-key.json CANARY')
    demo.service.life=broken
    status,result,_=demo.request('/product/api/life?id='+ident)
    assert status>=400 and 'CANARY' not in json.dumps(result) and '/Users/' not in json.dumps(result)


def test_policy_expiry_and_response_headers(demo):
    status,_,headers=demo.request()
    assert status==200 and headers['Cache-Control']=='no-store, private'
    assert "frame-ancestors 'self'" in headers['Content-Security-Policy']
    demo.policy['not_before']=int(time.time())-60;demo.policy['expires_at']=int(time.time())-1
    demo.path.write_text(json.dumps(demo.policy))
    assert demo.request()[0]==503


def test_ngrok_authenticated_ingress_requires_secret_and_allowed_email(demo):
    import hashlib
    secret='c'*64
    demo.policy.pop('team_domain');demo.policy.pop('audience')
    demo.policy.update(version=2,provider='ngrok-oauth',ingress_secret_sha256=hashlib.sha256(secret.encode()).hexdigest())
    demo.path.write_text(json.dumps(demo.policy))
    headers={'X-Kalends-Demo-Ingress':secret,'X-Kalends-Demo-Email':'owner@example.com'}
    assert demo.request(auth=False)[0]==401
    assert demo.request()[0]==401  # Cloudflare assertions cannot bypass ngrok mode.
    assert demo.request(auth=False,headers={'X-Kalends-Demo-Email':'owner@example.com'})[0]==401
    assert demo.request(auth=False,headers={**headers,'X-Kalends-Demo-Ingress':'d'*64})[0]==401
    assert demo.request(auth=False,headers={**headers,'X-Kalends-Demo-Email':'stranger@example.com'})[0]==401
    assert demo.request(auth=False,headers={**headers,'X-Kalends-Demo-Email':'owner@example.com, stranger@example.com'})[0]==401
    assert demo.request(auth=False,headers=headers)[0]==200
    assert demo.request('/product/api/lab',auth=False,headers=headers)[0]==404
    status,payload,_=demo.request('/product/api/start',{'template_id':'shared_observatory','guided':True},auth=False,headers=headers)
    assert status==200 and payload['guide']['enabled']
    assert secret not in json.dumps(payload)
    demo.policy['allowed_emails']=['mentor@example.com'];demo.path.write_text(json.dumps(demo.policy))
    assert demo.request(auth=False,headers=headers)[0]==401
    demo.policy['enabled']=False;demo.path.write_text(json.dumps(demo.policy))
    assert demo.request(auth=False,headers=headers)[0]==503


def test_ngrok_policy_uses_authenticated_identity_and_strips_injected_headers():
    from scripts.configure_ngrok_demo import configuration
    from email.message import Message
    from kalends.experience_os.demo_server import verify_ngrok,AccessDenied
    access,traffic=configuration('https://demo.example.com',['owner@example.com'],credential='c'*64)
    rules=traffic['on_http_request']
    assert rules[0]['actions'][0]['type']=='oauth'
    assert '!(actions.ngrok.oauth.identity.email in ["owner@example.com"])' in rules[1]['expressions'][0]
    actions=rules[2]['actions']
    assert actions[0]['type']=='remove-headers'
    assert set(actions[1]['config']['headers'])<=set(actions[0]['config']['headers'])
    assert actions[1]['config']['headers']['x-kalends-demo-email']=='${actions.ngrok.oauth.identity.email}'
    headers=Message();headers['X-Kalends-Demo-Ingress']='c'*64;headers['X-Kalends-Demo-Email']='owner@example.com'
    assert verify_ngrok(headers,access)=='owner@example.com'
    headers['X-Kalends-Demo-Ingress']='c'*64
    with pytest.raises(AccessDenied):verify_ngrok(headers,access)


def test_public_link_mode_still_blocks_local_bypass_and_operator_routes(demo):
    from scripts.configure_ngrok_demo import configuration
    access,traffic=configuration('https://demo.example.com',[],credential='c'*64,public=True)
    demo.path.write_text(json.dumps(access))
    assert 'allowed_emails' not in access
    assert all(action['type'] not in ('oauth','oidc') for rule in traffic['on_http_request'] for action in rule['actions'])
    headers={'X-Kalends-Demo-Ingress':'c'*64}
    assert demo.request(auth=False)[0]==401
    assert demo.request(auth=False,headers={**headers,'X-Kalends-Demo-Ingress':'d'*64})[0]==401
    assert demo.request(auth=False,headers=headers)[0]==200
    for path in ['/research','/studio','/product/api/lab','/os/catalog','/access.json','/.git/config']:
        assert demo.request(path,auth=False,headers=headers)[0]==404
    status,payload,_=demo.request('/product/api/start',{'template_id':'pompeii_life','guided':True},auth=False,headers=headers)
    assert status==200 and payload['life']['id'].startswith('pompeii_')
    status,script,_=demo.request('/product/app.js',auth=False,headers=headers)
    assert status==200 and b'This public preview' in script and b'Anyone with the link can view and change' in script
    assert b'Cloudflare handles sign-in' not in script
    access['enabled']=False;demo.path.write_text(json.dumps(access))
    assert demo.request(auth=False,headers=headers)[0]==503
