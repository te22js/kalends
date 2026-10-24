"""Render the internal continuity study's per-template outcomes and budgets."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = json.loads(args.summary.read_text())
    rows = [r for r in result["groups"] if r["split"] == "reviewer_holdout"]
    cases = sorted({r["case"] for r in rows})
    arms = ["current_observation", "v3_hybrid", "bm25_fifo", "admissible_history", "dependency_retention"]
    names = ["Current only", "V3 hybrid", "FIFO + BM25", "History reference", "Dependency retention"]
    colors = ["#b7bec9", "#3c6eaf", "#768c6f", "#ada2be", "#df7e3f"]
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharey=True, layout="constrained")
    for axis, case in zip(axes.flat, cases):
        selected = {r["arm"]: r for r in rows if r["case"] == case}
        axis.bar(range(len(arms)), [selected[a]["completed_chains"] / selected[a]["worlds"] for a in arms], color=colors)
        axis.set_title(case.removeprefix("review_").replace("_", " "), fontsize=10)
        axis.set_xticks(range(len(arms)), names, rotation=24, ha="right", fontsize=8)
        axis.set_ylim(0, 1.12)
        axis.set_ylabel("Completed assigned chains / worlds")
        for i, arm in enumerate(arms):
            row = selected[arm]
            axis.text(i, row["completed_chains"] / row["worlds"] + .025,
                      f"{row['completed_chains']}/{row['worlds']}", ha="center", fontsize=8)
        axis.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Internal reviewer-authored variants: actual prerequisite + deferred deliveries", fontsize=12)
    args.out.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out / "per_case_completion.png", dpi=180)
    fig.savefig(args.out / "per_case_completion.svg")
    plt.close(fig)
    fig, axis = plt.subplots(figsize=(9, 4), layout="constrained")
    for i, arm in enumerate(arms):
        selected = [r for r in rows if r["arm"] == arm]
        axis.scatter([r["max_total_state_bytes"] / 1024 for r in selected],
                     [r["completed_chains"] / r["worlds"] for r in selected],
                     label=names[i], color=colors[i], alpha=.8, s=70, marker=["o", "s", "D", "^", "P"][i])
    axis.axvline(16, color="#777777", linestyle="--", linewidth=1, label="Bounded-arm ceiling: 16 KiB")
    axis.set(xlabel="Maximum serialized accessible state (KiB; all persisted mind/controller state)",
             ylabel="Completed assigned chains / worlds", ylim=(-.07, 1.13),
             title="Outcome versus retained-state cost by template; reference has a larger budget")
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(fontsize=8, loc="center right")
    fig.savefig(args.out / "state_outcome_frontier.png", dpi=180)
    fig.savefig(args.out / "state_outcome_frontier.svg")


if __name__ == "__main__":
    main()
