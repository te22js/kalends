#!/bin/sh
# Detached local launcher. The foreground runner remains scripts/run_rebirth.sh.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
for kalends_python in "${KALENDS_PYTHON:-}" "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" python3; do
    if [ -n "$kalends_python" ] && "$kalends_python" -c 'import sys; raise SystemExit(sys.version_info < (3,10))' >/dev/null 2>&1; then
        exec "$kalends_python" - "$@" <<'PY'
"""Manage only this checkout's loopback Rebirth service; no game code changes."""
import argparse
from datetime import datetime, timezone
import fcntl
import http.client
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time

parser = argparse.ArgumentParser(description='Start a detached local Rebirth game, or inspect/stop its owned process.')
parser.add_argument('--port', type=int, default=8782)
parser.add_argument('--journal', default='.kalends/rebirth_session.json')
actions = parser.add_mutually_exclusive_group()
actions.add_argument('--status', action='store_true')
actions.add_argument('--stop', action='store_true')
args = parser.parse_args()
if not 1 <= args.port <= 65535:
    parser.error('--port must be between 1 and 65535')
root = Path.cwd().resolve()
state_dir = root / '.kalends'
state_dir.mkdir(parents=True, exist_ok=True)
journal = Path(args.journal).expanduser().resolve()
record_path = state_dir / f'rebirth_server_{args.port}.json'
log_path = state_dir / f'rebirth_server_{args.port}.log'
url = f'http://127.0.0.1:{args.port}/'


def read_record(path):
    try:
        value = json.loads(path.read_text())
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def owned(record):
    """Validate the current process before ever sending it a signal."""
    if not record or record.get('app') != 'kalends_rebirth' or record.get('root') != str(root):
        return False
    pid = record.get('pid')
    if type(pid) is not int or pid <= 1 or type(record.get('port')) is not int:
        return False
    try:
        result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'command='], capture_output=True, text=True, timeout=2)
    except (OSError, subprocess.TimeoutExpired):
        return False
    command = result.stdout.strip()
    expected = f'{record.get("executable", sys.executable)} -m kalends_rebirth.server --port {record["port"]} --journal {record.get("journal", "")}'
    return result.returncode == 0 and bool(record.get('journal')) and command == expected


def port_open(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
        connection.settimeout(.4)
        return connection.connect_ex(('127.0.0.1', port)) == 0


def is_rebirth(port):
    # HTTPConnection neither consults proxy settings nor follows redirects.
    connection = http.client.HTTPConnection('127.0.0.1', port, timeout=4)
    try:
        connection.request('GET', '/api/state', headers={'Accept': 'application/json'})
        response = connection.getresponse()
        if response.status != 200:
            return False
        raw = response.read(16 * 1024 * 1024 + 1)
        if len(raw) > 16 * 1024 * 1024:
            return False
        data = json.loads(raw)
        return isinstance(data, dict) and data.get('save_version') == 4 and isinstance(data.get('world'), dict)
    except (OSError, ValueError, http.client.HTTPException):
        return False
    finally:
        connection.close()


def finish(message, status=0):
    print(message, flush=True)
    raise SystemExit(status)


# One checkout-wide lock also prevents launching one save on two managed ports.
with (state_dir / 'rebirth_launcher.lock').open('a') as lock:
    fcntl.flock(lock, fcntl.LOCK_EX)
    record = read_record(record_path)
    if args.stop:
        if not owned(record):
            if is_rebirth(args.port):
                finish('Rebirth responds here, but no matching owned process was verified. Stop its foreground terminal; no signal was sent.', 2)
            if record and port_open(args.port):
                finish('The recorded process does not match this launcher. No signal was sent.', 2)
            finish(f'No verified managed Rebirth process is running on port {args.port}.', 1)
        pid = record['pid']
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            record_path.unlink(missing_ok=True)
            finish(f'Rebirth had already stopped. Its journal is preserved: {record["journal"]}')
        except PermissionError:
            finish('The operating system refused the stop request. No stronger signal was attempted.', 2)
        deadline = time.monotonic() + 4
        while time.monotonic() < deadline and owned(record):
            time.sleep(.1)
        if owned(record):
            finish(f'The game has not stopped yet; inspect PID {pid}. No stronger signal was sent.', 2)
        record_path.unlink(missing_ok=True)
        finish(f'Stopped Rebirth on port {args.port}. Its journal is preserved: {record["journal"]}')
    if args.status:
        if is_rebirth(args.port):
            detail = f'\nJournal: {record["journal"]}' if owned(record) else '\nProcess ownership: unmanaged; this launcher will not stop it.'
            finish(f'Rebirth is running at {url}{detail}')
        if port_open(args.port):
            finish(f'Port {args.port} is occupied but does not answer as Rebirth. No process was changed.', 2)
        finish(f'Rebirth is not running on port {args.port}.', 1)
    if is_rebirth(args.port):
        if owned(record) and record['journal'] != str(journal):
            finish(f'This port already runs a different journal: {record["journal"]}\nUse a different port or stop that managed life first.', 2)
        ownership = '' if owned(record) else '\nExisting service is unmanaged; no process record was adopted.'
        finish(f'Rebirth is already running at {url}{ownership}')
    if port_open(args.port):
        finish(f'Port {args.port} is occupied by another or unresponsive service. Use --port with a free local port. No process was changed.', 2)
    for path in state_dir.glob('rebirth_server_*.json'):
        other = read_record(path)
        if owned(other) and other.get('journal') == str(journal):
            finish(f'This journal already has a managed process at http://127.0.0.1:{other["port"]}/. Reuse it; concurrent writers were not started.', 2)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('ab', buffering=0) as log:
        process = subprocess.Popen([sys.executable, '-m', 'kalends_rebirth.server', '--port', str(args.port), '--journal', str(journal)],
            cwd=root, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    new_record = {'version': 1, 'app': 'kalends_rebirth', 'root': str(root), 'pid': process.pid,
        'port': args.port, 'journal': str(journal), 'log': str(log_path), 'executable': sys.executable,
        'started_utc': datetime.now(timezone.utc).isoformat()}
    temporary = record_path.with_suffix('.tmp')
    try:
        temporary.write_text(json.dumps(new_record, indent=2) + '\n')
        temporary.replace(record_path)
    except OSError:
        process.terminate()
        process.wait(timeout=4)
        raise
    deadline = time.monotonic() + 12
    while time.monotonic() < deadline:
        if process.poll() is not None:
            record_path.unlink(missing_ok=True)
            finish(f'Rebirth could not start. Its journal was preserved. Read {log_path}', 2)
        if is_rebirth(args.port):
            finish(f'Rebirth is running at {url}\nJournal: {journal}\nLog: {log_path}\nIt runs separately from this terminal. Use this script with --status or --stop.')
        time.sleep(.15)
    finish(f'PID {process.pid} started but readiness was not confirmed. Inspect {log_path}; the process record is preserved.', 2)
PY
    fi
done
printf '%s\n' 'Rebirth needs Python 3.10 or newer. Set KALENDS_PYTHON to that executable.' >&2
exit 1
