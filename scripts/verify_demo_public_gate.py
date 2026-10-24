#!/usr/bin/env python3
"""Unauthenticated HTTPS probes. Never reads browser cookies or agent secrets."""
import argparse
import json
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request,HTTPRedirectHandler,build_opener

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--origin',required=True);p.add_argument('--output',required=True);p.add_argument('--public',action='store_true')
a=p.parse_args();origin=a.origin.rstrip('/')
u=urlsplit(origin)
if u.scheme!='https' or not u.hostname or u.path:p.error('Use the exact HTTPS origin')
paths=['/','/product/api/catalog','/product/app.js','/immersion-assets/characters/characters.json','/research','/studio','/lab/x','/os/catalog','/product/api/trace','/access.json','/.git/config']
results=[];client=build_opener(NoRedirect)
for path in paths:
    # A forged forwarded identity must not skip OAuth at the public edge.
    headers={'User-Agent':'Kalends-unauthenticated-security-probe','X-Kalends-Demo-Email':'tanmaygoswami1001@gmail.com','X-Kalends-Demo-Ingress':'f'*64,'Cf-Access-Authenticated-User-Email':'tanmaygoswami1001@gmail.com'}
    request=Request(origin+path,headers=headers)
    try:response=client.open(request,timeout=20)
    except HTTPError as error:response=error
    body=response.read();status=response.code
    location=urlsplit(response.headers.get('Location',''))
    gated=status in (302,303,307) and location.scheme=='https' and location.hostname=='idp.ngrok.com'
    results.append({'path':path,'status':status,'redirect_host':location.hostname,'requires_oauth':gated})
    if a.public:
        participant=path in ['/', '/product/api/catalog','/product/app.js','/immersion-assets/characters/characters.json']
        expected=200 if participant else 404
        assert status==expected,(path,status,expected)
        results[-1]['expected_status']=expected
    else:assert gated,(path,status)
if a.public:
    for operation in ['lab','studio/compile','studio/validate','fork','practice','annotation','telemetry','export','admin']:
        path='/product/api/'+operation
        request=Request(origin+path, data=json.dumps({'id':'pompeii_life','acknowledged':True}).encode(),
                        headers={'User-Agent':'Kalends-public-security-probe','Origin':origin,'Content-Type':'application/json'})
        try:response=client.open(request,timeout=20)
        except HTTPError as error:response=error
        response.read();assert response.code==404,(path,response.code)
        results.append({'path':path,'method':'POST','status':response.code,'expected_status':404})
# Keep all cookies, OAuth state and agent IP response headers out of reports.
with open(a.output,'w') as f:json.dump({'origin':origin,'cookie_session':'none','forged_identity_headers':True,'mode':'public-link' if a.public else 'oauth','checks':results},f,indent=2)
print(f'{len(results)} public anonymous/forged-identity probes passed in '+('public-link' if a.public else 'OAuth')+' mode.')
