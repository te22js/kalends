#!/bin/sh
# Local 3D client and original illustrated client share the tested Python API.
# The default journal is a separate life; the Rebirth save is never reset/copied.
set -eu
kalends_root="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$kalends_root"
# This visual sprint has no live-provider spending authorization.
export KALENDS_AI_PROVIDER=offline
export KALENDS_AI_ALLOW_EXTERNAL=0
kalends_port=8790
kalends_journal=.kalends/immersion_session.json
kalends_mode=start
while [ "$#" -gt 0 ]; do
  case "$1" in
    --port) [ "$#" -ge 2 ] || { echo '--port requires a value' >&2; exit 2; }; kalends_port=$2; shift 2 ;;
    --journal) [ "$#" -ge 2 ] || { echo '--journal requires a path' >&2; exit 2; }; kalends_journal=$2; shift 2 ;;
    --status) kalends_mode=status; shift ;;
    --stop) kalends_mode=stop; shift ;;
    -h|--help) printf '%s\n' 'Usage: ./scripts/start_immersion.sh [--port 8790] [--journal .kalends/immersion_session.json] [--status|--stop]' 'Build first: cd kalends_3d && npm ci && npm run build' '3D: http://127.0.0.1:8790/immersion/ · Legacy: http://127.0.0.1:8790/'; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; exit 2 ;;
  esac
done
if [ "$kalends_mode" = start ] && [ ! -f kalends_3d/dist/index.html ]; then
  printf '%s\n' 'The 3D client has not been built. Run: cd kalends_3d && npm ci && npm run build' >&2
  exit 2
fi
case "$kalends_mode" in
  status) exec ./scripts/start_rebirth.sh --port "$kalends_port" --journal "$kalends_journal" --status ;;
  stop) exec ./scripts/start_rebirth.sh --port "$kalends_port" --journal "$kalends_journal" --stop ;;
  start) ./scripts/start_rebirth.sh --port "$kalends_port" --journal "$kalends_journal" ;;
esac
printf '\n3D district: http://127.0.0.1:%s/immersion/\nLegacy illustrated client: http://127.0.0.1:%s/\n' "$kalends_port" "$kalends_port"
