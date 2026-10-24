"""Restricted, short-lived participant staging. Never proxy the local server.

Production requires Cloudflare Access RS256 credentials or an authenticated
ngrok ingress on every request, including assets. Public link mode requires an
explicit separate policy; it does not provide visitor authentication. No query-string token,
login bypass, or remote admin route.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import hmac
import io
import json
import math
import mimetypes
import re
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .product import ProductService
from .product_server import make_product_handler
from .server import ROOT, STATIC

GET_API = frozenset({'/product/api/catalog', '/product/api/life',
                     '/product/api/history', '/product/api/trace', '/api/state', '/api/context'})
POST_API = frozenset('/product/api/' + x for x in
                    ('start', 'resume', 'propose', 'observe', 'confirm', 'advance', 'seen', 'intent', 'guide')) | frozenset(
                        '/api/' + x for x in ('route', 'propose', 'observe', 'act', 'move', 'advance'))
PAGES = frozenset(('/', '/worlds', '/your-worlds', '/accessibility', '/data-and-saves', '/acknowledgements'))
ID = re.compile(r'(?:pompeii|observatory)_[a-f0-9]{12}')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result: raise ValueError('Duplicate field')
        result[key] = value
    return result


class AccessDenied(Exception):
    pass


def read_policy(path):
    """Reload every request: removing an email or disabling revokes cached JWTs."""
    p = json.loads(Path(path).read_text())
    public = p.get('version') == 3 and p.get('provider') == 'ngrok-link'
    common = {'version', 'enabled', 'origin', 'expires_at', 'not_before'} | (set() if public else {'allowed_emails'})
    ngrok = public or p.get('version') == 2 and p.get('provider') == 'ngrok-oauth'
    expected = common | ({'provider', 'ingress_secret_sha256'} if ngrok else {'team_domain', 'audience'})
    if set(p) != expected or type(p['version']) is not int or p['version'] not in (1, 2, 3) or (p['version'] >= 2 and not ngrok) or type(p['enabled']) is not bool:
        raise ValueError('Invalid demo policy')
    u = urlsplit(p['origin'])
    if u.scheme != 'https' or not u.hostname or u.port or u.username or u.password or u.path or u.query or u.fragment:
        raise ValueError('A dedicated HTTPS origin is required')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*\.[a-z]{2,}', u.hostname):
        raise ValueError('Invalid demo hostname')
    if ngrok:
        if not re.fullmatch(r'[a-f0-9]{64}', p['ingress_secret_sha256']):
            raise ValueError('A private ingress credential is required')
    else:
        if not re.fullmatch(r'[a-z0-9-]+\.cloudflareaccess\.com', p['team_domain']):
            raise ValueError('Use the Cloudflare Access team domain')
        if not re.fullmatch(r'[a-f0-9]{64}', p['audience']):
            raise ValueError('Use this Access application audience')
    emails = p.get('allowed_emails', [])
    if not public and (not isinstance(emails, list) or not 1 <= len(emails) <= 2 or any(
            not isinstance(e, str) or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', e) for e in emails)):
        raise ValueError('Allow only the owner and mentor login emails')
    for key in ('expires_at', 'not_before'):
        if type(p[key]) not in (int, float) or not math.isfinite(p[key]):
            raise ValueError('Invalid policy time')
    if not 0 < p['expires_at'] - p['not_before'] <= 7 * 86400:
        raise ValueError('A demo may last at most seven days')
    return p


class AccessVerifier:
    def __init__(self, *, clients=None):
        # Injection is for in-process tests; the production CLI has no alternative
        # key URL, test identity, bypass, or unsigned-token option.
        self.clients = clients if clients is not None else {}
        self.lock = threading.Lock()

    def verify(self, token, policy):
        import jwt
        if not token or len(token) > 16000:
            raise AccessDenied()
        try:
            issuer = 'https://' + policy['team_domain']
            with self.lock:
                client = self.clients.get(issuer)
                if client is None:
                    client = jwt.PyJWKClient(issuer + '/cdn-cgi/access/certs', timeout=3, lifespan=300)
                    self.clients = {issuer: client}
                key = client.get_signing_key_from_jwt(token)
            claims = jwt.decode(token, key.key, algorithms=['RS256'], audience=policy['audience'], issuer=issuer,
                                options={'require': ['exp', 'iat', 'iss', 'aud', 'sub', 'email']})
            now = time.time()
            if type(claims['iat']) not in (int, float) or type(claims['exp']) not in (int, float):
                raise AccessDenied()
            if not now - 3600 <= claims['iat'] <= now or claims['iat'] < policy['not_before']:
                raise AccessDenied()
            if not isinstance(claims['sub'], str) or not claims['sub']:
                raise AccessDenied()
            if not isinstance(claims['email'], str) or claims['email'].lower() not in {e.lower() for e in policy['allowed_emails']}:
                raise AccessDenied()
            return claims['sub']
        except (jwt.PyJWTError, OSError, ValueError, TypeError, KeyError):
            raise AccessDenied() from None


def verify_ngrok(headers, policy):
    """Trust an OAuth identity only over this instance's private ingress channel.

    The edge removes visitor-supplied copies before injecting both headers. A
    duplicate or coalesced header fails closed. The credential is 256 random bits
    and exists only in the private agent policy; responses/logs never include it.
    No assumption is made that an arbitrary X-Forwarded-* header proves identity.
    """
    secrets = headers.get_all('X-Kalends-Demo-Ingress', [])
    emails = headers.get_all('X-Kalends-Demo-Email', [])
    if len(secrets) != 1 or not re.fullmatch(r'[a-f0-9]{64}', secrets[0]):
        raise AccessDenied()
    digest = hashlib.sha256(secrets[0].encode('ascii')).hexdigest()
    if not hmac.compare_digest(digest, policy['ingress_secret_sha256']):
        raise AccessDenied()
    if policy.get('provider') == 'ngrok-link':
        return 'public-demo'
    if len(emails) != 1 or emails[0].lower() not in {e.lower() for e in policy['allowed_emails']}:
        raise AccessDenied()
    return emails[0].lower()


class Bucket:
    def __init__(self, rate, burst):
        self.rate, self.burst, self.tokens, self.at = rate, burst, burst, time.monotonic()
        self.lock = threading.Lock()

    def take(self):
        with self.lock:
            now = time.monotonic()
            self.tokens = min(self.burst, self.tokens + (now - self.at) * self.rate)
            self.at = now
            if self.tokens < 1:
                return False
            self.tokens -= 1
            return True


def static_files():
    """Positive manifest, not a directory server. No sources, maps or reports."""
    files = {'/game-host.js': STATIC / 'game-host.js',
             '/navigation.js': ROOT / 'kalends_rebirth/static/navigation.js',
             '/assets/portraits.png': ROOT / 'kalends_rebirth/static/assets/portraits.png',
             '/demo-shell.js': STATIC / 'demo/shell.js', '/demo.css': STATIC / 'demo/demo.css'}
    for name in ('app.js', 'style.css', 'redesign.css', 'assets/hero.png', 'assets/hero-v2.jpg'):
        files['/product/' + name] = STATIC / 'product' / name
    for p in (ROOT / 'kalends_3d/dist/assets').glob('*'):
        if p.suffix in {'.js', '.css', '.woff2'} and re.fullmatch(r'[A-Za-z0-9_.-]+', p.name):
            files['/immersion/assets/' + p.name] = p
    for name in ('characters/characters.json', 'characters/roman_female.glb',
                 'characters/roman_male.glb', 'environment/pompeii_district.glb'):
        files['/immersion-assets/' + name] = ROOT / 'kalends_3d/assets' / name
    return {url: p for url, p in files.items() if p.is_file() and not p.is_symlink()}


def restricted_handler(service, policy_path, verifier=None):
    base = make_product_handler(service)
    verifier = verifier or AccessVerifier()
    files = static_files()
    all_requests, writes, heavy, starts = Bucket(30, 200), Bucket(8, 40), Bucket(1/15, 4), Bucket(1/60, 2)

    class Handler(base):
        server_version = 'KalendsDemo'
        sys_version = ''

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def safe(self):
            # Called again by the inherited participant dispatcher; authentication
            # already ran before routing. Never use its local-only Host exception.
            if not getattr(self, '_admitted', False):
                raise AccessDenied()

        def send_error(self, code, message=None, explain=None):
            self.send(code, {'error': 'Request unavailable'})

        def send(self, status, value, mime='application/json'):
            if status >= 400:
                extra = {k: value[k] for k in ('code', 'save_failed') if isinstance(value, dict) and k in value}
                value = {'error': {401: 'Authentication required', 403: 'Access denied', 404: 'Unavailable in this demo',
                                   429: 'Too many requests; wait briefly', 503: 'Demo access is closed'}.get(
                                       status, 'This request could not be accepted. Reopen the current world before trying again.'), **extra}
                mime = 'application/json'
            elif isinstance(value, dict):
                value = copy.deepcopy(value)
                value.pop('intervention', None)
                value.pop('comparison', None)
                if 'templates' in value:
                    value['demo'] = True
                    value['examples'] = []
                    value['failures'] = []
            data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
            self.close_connection = True
            self.send_response(status)
            self.send_header('Content-Type', mime + ('; charset=utf-8' if mime.startswith('text/') or mime in ('application/json', 'application/javascript') else ''))
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store, private')
            self.send_header('Connection', 'close')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('X-Robots-Tag', 'noindex, nofollow, noarchive')
            self.send_header('Strict-Transport-Security', 'max-age=86400')
            self.send_header('Permissions-Policy', 'camera=(), microphone=(), geolocation=(), payment=()')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self' blob:; frame-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'self'; form-action 'self'")
            if status == 429:
                self.send_header('Retry-After', '15')
            self.end_headers()
            self.wfile.write(data)

        def admit(self):
            self._admitted = False
            if not all_requests.take():
                self.send(429, {}); return None
            try:
                p = read_policy(policy_path)
                if not p['enabled'] or time.time() >= p['expires_at']:
                    self.send(503, {}); return None
            except (OSError, ValueError, TypeError, KeyError):
                self.send(503, {}); return None
            if self.headers.get_all('Host') != [urlsplit(p['origin']).netloc]:
                self.send(403, {}); return None
            try:
                if p.get('provider') in ('ngrok-oauth', 'ngrok-link'):
                    verify_ngrok(self.headers, p)
                else:
                    if len(self.headers.get_all('Cf-Access-Jwt-Assertion', [])) != 1:
                        raise AccessDenied()
                    verifier.verify(self.headers['Cf-Access-Jwt-Assertion'], p)
            except AccessDenied:
                self.send(401, {}); return None
            url = urlsplit(self.path)
            # Reject ambiguous/encoded paths instead of normalizing them through
            # several independent dispatchers. Query values may be URL encoded.
            if len(self.path) > 4096 or url.scheme or url.netloc or '%' in url.path or '\\' in url.path or '..' in url.path or '//' in url.path:
                self.send(404, {}); return None
            try:
                q = parse_qs(url.query, keep_blank_values=True, max_num_fields=8)
            except ValueError:
                self.send(400, {}); return None
            allowed_query = {'id', 'event_id'} if url.path == '/product/api/trace' else {'id'} if url.path.startswith('/product/api/') else {'experience', 'recipient'} if url.path.startswith('/api/') else {'experience'} if url.path == '/immersion/' else set()
            if set(q) - allowed_query or any(len(v) != 1 for v in q.values()):
                self.send(404, {}); return None
            self._admitted = True
            return p, url.path, q

        def valid_life(self, ident):
            return isinstance(ident, str) and ID.fullmatch(ident) and service.metadata.get(ident, {}).get('started')

        def do_GET(self):
            admitted = self.admit()
            if not admitted: return
            _, path, q = admitted
            try:
                if path in GET_API:
                    ident = q.get('id' if path.startswith('/product/') else 'experience', [None])[0]
                    if path != '/product/api/catalog' and not self.valid_life(ident):
                        return self.send(404, {})
                    if path == '/product/api/trace' and not re.fullmatch(r'[0-9]{1,8}', q.get('event_id', [''])[0]):
                        return self.send(400, {})
                    return super().do_GET()
                page = path in PAGES or re.fullmatch(r'/worlds/(?:pompeii_life|shared_observatory)', path)
                match = re.fullmatch(r'/lives/([^/]+)(?:/history)?', path)
                if match: page = self.valid_life(match[1])
                if page or path == '/immersion/':
                    if path == '/immersion/' and not self.valid_life(q.get('experience', [None])[0]):
                        return self.send(404, {})
                    file = ROOT / 'kalends_3d/dist/index.html' if path == '/immersion/' else STATIC / 'product/index.html'
                    body = file.read_bytes().replace(b'<head>', b'<head><script src="/demo-shell.js" defer></script><link rel="stylesheet" href="/demo.css">', 1)
                    if path == '/immersion/':
                        body = body.replace(b'<head>', b'<head><script src="/game-host.js"></script>', 1)
                    return self.send(200, body, 'text/html')
                file = files.get(path)
                if file:
                    body = file.read_bytes()
                    if path == '/demo-shell.js' and admitted[0].get('provider') == 'ngrok-link':
                        body = body.replace(b'Private temporary demo', b'Public temporary demo')
                    if path == '/product/app.js' and admitted[0].get('provider') == 'ngrok-link':
                        body = body.replace(b'This authenticated preview', b'This public preview').replace(b'The owner and invited mentor share these demo lives; they are not private from each other.', b'Anyone with the link can view and change these shared demo lives.').replace(b'Cloudflare handles sign-in and HTTPS traffic.', b'ngrok carries HTTPS traffic. There is no sign-in requirement.').replace(b'/cdn-cgi/access/logout', b'/').replace(b'Sign out of this preview', b'Return to the demo')
                    if path == '/product/app.js' and admitted[0].get('provider') == 'ngrok-oauth':
                        body = body.replace(b'/cdn-cgi/access/logout', b'/ngrok/logout').replace(b'Cloudflare handles sign-in and HTTPS traffic.', b'ngrok and Google handle sign-in; ngrok carries HTTPS traffic.')
                    return self.send(200, body, mimetypes.guess_type(file)[0] or 'application/octet-stream')
                return self.send(404, {})
            except Exception:
                # Do not reflect exception text, tokens, paths or private config.
                return self.send(500, {})

        def do_POST(self):
            admitted = self.admit()
            if not admitted: return
            p, path, q = admitted
            if path not in POST_API: return self.send(404, {})
            if self.headers.get_all('Origin') != [p['origin']] or self.headers.get('Sec-Fetch-Site') == 'cross-site':
                return self.send(403, {})
            if self.headers.get('Content-Type', '').split(';')[0].strip() != 'application/json' or self.headers.get('Transfer-Encoding') or len(self.headers.get_all('Content-Length', [])) != 1:
                return self.send(400, {})
            if not writes.take(): return self.send(429, {})
            if path.endswith('/start') and not starts.take(): return self.send(429, {})
            try:
                size = int(self.headers['Content-Length'])
                if not 0 < size <= 32768: return self.send(413, {})
                raw = self.rfile.read(size)
                data = json.loads(raw, object_pairs_hook=unique_object, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                if not isinstance(data, dict): return self.send(400, {})
                if path.endswith('/start'):
                    if set(data) - {'template_id', 'guided'} or data.get('template_id') not in ('pompeii_life', 'shared_observatory'):
                        return self.send(400, {})
                else:
                    ident = data.get('id') if path.startswith('/product/') else q.get('experience', [None])[0]
                    if not self.valid_life(ident) or ('experience' in data and data['experience'] != ident):
                        return self.send(404, {})
                    if len(service.get(ident).commands) >= 2000: return self.send(403, {})
                if path.endswith('/advance') and (type(data.get('minutes')) is not int or not 1 <= data['minutes'] <= 10080):
                    return self.send(400, {})
                if path.endswith('/advance') and data['minutes'] > 60 and not heavy.take(): return self.send(429, {})
                # The inherited handler reads exactly this validated body.
                self.rfile = io.BytesIO(raw)
                return super().do_POST()
            except Exception:
                return self.send(400, {})

    return Handler


class DemoServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, *args, **kwargs):
        self.slots = threading.BoundedSemaphore(16)
        super().__init__(*args, **kwargs)

    def process_request(self, request, client_address):
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try: super().process_request(request, client_address)
        except Exception:
            self.slots.release()
            raise

    def process_request_thread(self, request, client_address):
        try: super().process_request_thread(request, client_address)
        finally: self.slots.release()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instance', required=True, type=Path)
    parser.add_argument('--port', type=int, default=8840)
    args = parser.parse_args()
    directory = args.instance.resolve()
    if not 1024 <= args.port <= 65535: parser.error('Use an unprivileged loopback port')
    if not (directory / 'DEMO_ONLY').is_file(): parser.error('Initialize a separate demo instance first')
    policy = directory / 'access.json'
    read_policy(policy)
    if (directory / 'saves').is_symlink(): parser.error('Demo saves must not be symlinked')
    writer_lock = (directory / '.writer.lock').open('a')
    fcntl.flock(writer_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    # Explicit offline cognition, no examples/research loading, no arbitrary directory.
    from kalends_rebirth.ai import Cognition
    service = ProductService(directory / 'saves', cognition=Cognition(), include_examples=False)
    server = DemoServer(('127.0.0.1', args.port), restricted_handler(service, policy))
    print(f'Restricted demo origin listening on loopback port {args.port}. Access policy is mandatory.', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
