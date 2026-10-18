"""Verify semantic (not wall-clock) reproducibility of recorded worlds."""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from kalends.actionbench.runner import run_world


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    parser.add_argument("--sample", type=int, default=12)
    args = parser.parse_args()
    with gzip.open(Path(args.directory) / "raw.jsonl.gz", "rt") as stream:
        rows = [json.loads(line) for line in stream]
    n = min(len(rows), args.sample)
    if n < 1:
        parser.error("sample must be positive and experiment nonempty")
    indexes = sorted({int(i * (len(rows)-1) / max(1, n-1)) for i in range(n)})
    for index in indexes:
        row = rows[index]
        replay = run_world(row["seed"], row["family"], row["population"], row["condition"],
                           row["capacity"], row["communication_depth"], row["config"]["n_ticks"])
        if replay["semantic_hash"] != row["semantic_hash"]:
            raise AssertionError(f"semantic replay mismatch at world {index}")
    print(f"Verified {len(indexes)} semantic hashes sampled across {len(rows)} recorded worlds.")


if __name__ == "__main__":
    main()
