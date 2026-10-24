#!/bin/sh
# Build the existing renderer and serve the redesigned shell on a separate save directory.
set -eu
cd "$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
npm --prefix kalends_3d run build
exec scripts/run_next_phase.sh --port 8833 --directory .kalends/redesign_review "$@"
