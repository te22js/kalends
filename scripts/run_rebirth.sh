#!/bin/sh
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
for kalends_python in "${KALENDS_PYTHON:-}" "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" python3; do
    if [ -n "$kalends_python" ] && "$kalends_python" -c 'import sys; raise SystemExit(sys.version_info < (3,10))' >/dev/null 2>&1; then
        exec "$kalends_python" -m kalends_rebirth.server "$@"
    fi
done
printf '%s\n' 'Rebirth needs Python 3.10 or newer. Set KALENDS_PYTHON to that executable.' >&2
exit 1
