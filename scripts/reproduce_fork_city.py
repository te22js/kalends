"""Reproduce the final fixed ActionBench design into a fresh directory.

Run from the repository root: python3 scripts/reproduce_fork_city.py --out ...
Optional plotting dependency: matplotlib. No network or model APIs are used.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from kalends.actionbench.runner import run_suite
from kalends.actionbench.plots import make_plots


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="results/fork_city_reproduction")
    parser.add_argument("--no-plots", action="store_true")
    parser.add_argument("--seeds", type=int, default=30,
                        help="use 30 for the reported held-out study; smaller is a smoke test")
    args = parser.parse_args()
    root = Path(args.out)
    if root.exists() and any(root.iterdir()):
        parser.error("choose an empty output directory; existing experiments are preserved")
    for name, split, seeds, populations, conditions in (
        ("development_final", "development", range(10), (8,), None),
        ("heldout", "heldout", range(1000, 1000 + args.seeds), (8, 32), None),
        ("scaling128", "heldout", range(1000, 1000 + args.seeds), (128,),
         ["structured", "bm25", "hybrid", "hybrid_guarded", "guarded_lineage2"]),
    ):
        run_suite(root / name, split=split, seeds=seeds, populations=populations,
                  conditions=conditions)
        if not args.no_plots:
            make_plots(root / name)


if __name__ == "__main__":
    main()
