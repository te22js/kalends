"""Plot the actual predeclared sensitivity studies alongside cap64/depth3."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default="results/fork_city")
    args = parser.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    root = Path(args.root)
    base = json.loads((root / "heldout/summary.json").read_text())
    sensitivity = json.loads((root / "sensitivity/summary.json").read_text())
    studies = [("cap8", sensitivity["capacity8"]), ("cap64\ndepth3", base),
               ("unlimited", sensitivity["capacity_unlimited"]),
               ("depth1", sensitivity["depth1"]), ("depth6", sensitivity["depth6"])]
    conditions = [("hybrid", "#b54a54"), ("hybrid_guarded", "#227c86"),
                  ("guarded_sources2", "#ad8932"), ("guarded_lineage2", "#247749")]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    for offset, (condition, color) in enumerate(conditions):
        for ax, metric in zip(axes, ("decision_regret", "autonomy")):
            values = [s["systems"]["8/" + condition]["metrics"][metric] for _, s in studies]
            x = [i + (offset-1.5)*.07 for i in range(len(values))]
            ax.errorbar(x, [m["mean"] for m in values],
                        yerr=[[m["mean"]-m["ci95"][0] for m in values],
                              [m["ci95"][1]-m["mean"] for m in values]],
                        fmt="o-", color=color, capsize=3, label=condition, linewidth=1)
    for ax, label in zip(axes, ("Declared task regret / opportunity", "Autonomous reserves / opportunities")):
        ax.set(xticks=range(len(studies)), xticklabels=[name for name, _ in studies], ylabel=label)
        ax.grid(alpha=.15)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    axes[1].legend(fontsize=8)
    fig.suptitle("Retention and relay-depth sensitivity ·8 agents ·30 paired seeds ·95% intervals")
    fig.tight_layout()
    path = root / "sensitivity/sensitivity.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    print(path)


if __name__ == "__main__":
    main()
