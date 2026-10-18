"""Predeclared retention and communication-depth sensitivity worlds."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kalends.actionbench.runner import run_suite


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--seeds", type=int, default=30)
    args = parser.parse_args()
    if args.seeds < 1:
        parser.error("--seeds must be positive")
    root = Path(args.out)
    if root.exists() and any(root.iterdir()):
        parser.error("choose an empty output directory")
    summaries = {}
    # These axes isolate a smaller record store, unlimited retention, shallower
    # relays, and deeper relays. Baseline is cap64/depth3 in the main heldout run.
    for name, capacity, depth in (("capacity8", 8, 3), ("capacity_unlimited", 0, 3),
                                  ("depth1", 64, 1), ("depth6", 64, 6)):
        summaries[name] = run_suite(root / name, split="heldout",
            seeds=range(1000, 1000+args.seeds), populations=(8,), capacity=capacity,
            depth=depth, conditions=["bm25", "hybrid", "hybrid_guarded",
                                     "guarded_lineage2", "guarded_sources2"])
    with (root / "summary.json").open("x") as stream:
        stream.write(json.dumps(summaries, indent=2, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()
