"""Independently launchable real demo. Existing worlds resume by default."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from kalends.genesis.server import GenesisSession, make_handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--journal", type=Path, default=ROOT / ".kalends/genesis_demo.json")
    parser.add_argument("--fresh", action="store_true", help="archive the previous demo journal and start the curated world")
    args = parser.parse_args()
    if args.fresh and args.journal.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        backup = args.journal.with_name(args.journal.stem + "." + stamp + ".json")
        args.journal.rename(backup)
        print("Previous world preserved:", backup, flush=True)
    fresh = not args.journal.exists()
    session = GenesisSession(args.journal)
    if fresh:
        session.apply("reset", json.loads((ROOT / "demo/genesis/scenario.json").read_text()))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), make_handler(session))
    print("KALENDS GENESIS — http://127.0.0.1:%s" % server.server_port, flush=True)
    print("Curated seed2026, capacity256. Real simulation; offline grammar; no background advancement.", flush=True)
    print("Select Livia → Share a rumour → confirm → Return after three days → Why trust me? → SHOW WHY.", flush=True)
    print("Restart this command without --fresh to resume the same world. Ctrl+C stops it.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
