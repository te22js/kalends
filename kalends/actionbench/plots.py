"""Generate publication-style plots from measured ActionBench summaries."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def make_plots(directory):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directory = Path(directory)
    summary = json.loads((directory / "summary.json").read_text())
    systems = summary["systems"]
    out = directory / "plots"
    out.mkdir(exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "figure.dpi": 130, "savefig.dpi": 180})
    colors = {"structured": "#566477", "bm25": "#b2653c", "hybrid": "#c24450",
              "hybrid_guarded": "#287a80", "guarded_lineage1": "#7dbbc0",
              "guarded_lineage2": "#126a52", "guarded_lineage3": "#54a477",
              "guarded_sources2": "#a88b35", "bm25_lineage2": "#d2a078",
              "always_defer": "#b8b8b8", "always_verify": "#898989"}
    populations = sorted({s["population"] for s in systems.values()})
    labels = {"guarded_lineage1": "lineage ≥1", "guarded_lineage2": "lineage ≥2",
              "guarded_lineage3": "lineage ≥3", "guarded_sources2": "senders ≥2",
              "hybrid_guarded": "guarded / ungated"}
    def metric(s, key):
        return s["metrics"][key]
    def error(m):
        return [[max(0, m["mean"]-m["ci95"][0])], [max(0, m["ci95"][1]-m["mean"])]]

    fig, axes = plt.subplots(1, len(populations), figsize=(6*len(populations), 5), squeeze=False)
    for ax, pop in zip(axes[0], populations):
        points = []
        sample = next(s for s in systems.values() if s["population"] == pop)
        for condition in ("hybrid_guarded", "guarded_lineage1", "guarded_lineage2", "guarded_lineage3", "guarded_sources2", "bm25", "bm25_lineage2"):
            s = systems.get(f"{pop}/{condition}")
            if not s:
                continue
            x, y = metric(s, "autonomy"), metric(s, "selective_risk")
            ax.errorbar(x["mean"], y["mean"], xerr=error(x), yerr=error(y), fmt="o",
                        capsize=3, color=colors[condition], label=labels.get(condition, condition))
            if condition.startswith("guarded_lineage") or condition == "hybrid_guarded":
                points.append((x["mean"], y["mean"]))
        # Empirical nondominated points among predeclared operating thresholds.
        frontier = sorted(p for p in points if not any(q[0] >= p[0] and q[1] <= p[1] and q != p for q in points))
        if frontier:
            ax.plot(*zip(*frontier), "--", color="#126a52", alpha=.5, zorder=0)
        ax.set(xlabel="Autonomy: reserves / action opportunities", ylabel="Selective risk: incorrect / all reserves",
               title=f"{pop} agents · {sample['n_seeds']} paired seeds", xlim=(-.02, 1.02), ylim=(-.02, 1.02))
        ax.grid(alpha=.15)
        ax.legend(fontsize=8, loc="best")
    fig.suptitle("Measured risk–coverage operating points (95% seed-clustered intervals)", y=1.02)
    fig.tight_layout()
    fig.savefig(out / "risk_coverage.png", bbox_inches="tight")
    fig.savefig(out / "risk_coverage.svg", bbox_inches="tight")
    plt.close(fig)

    pop = populations[0]
    selected = [s for s in systems.values() if s["population"] == pop]
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    for i, s in enumerate(selected):
        name = s["condition"]
        for ax, key in zip(axes, ("decision_regret", "action_error_rate")):
            m = metric(s, key)
            ax.barh(i, m["mean"], xerr=error(m), color=colors.get(name, "#888888"), capsize=2)
    for ax, title in zip(axes, ("Mean task regret per opportunity", "Action error rate (verification cost shown in regret)")):
        ax.set(yticks=range(len(selected)), yticklabels=[s["condition"] for s in selected], title=title)
        ax.invert_yaxis()
        ax.grid(axis="x", alpha=.15)
    fig.suptitle(f"{pop} agents · asymmetric reserve/defer/verify costs · 95% intervals")
    fig.tight_layout()
    fig.savefig(out / "decision_outcomes.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for s in selected:
        if s["condition"].startswith("always_"):
            continue
        x, y = metric(s, "qa_accuracy"), metric(s, "decision_regret")
        name = s["condition"]
        ax.errorbar(x["mean"], y["mean"], xerr=error(x), yerr=error(y), fmt="o",
                    color=colors.get(name, "#777777"), capsize=2)
        ax.annotate(labels.get(name, name), (x["mean"], y["mean"]), xytext=(5, 5), textcoords="offset points", fontsize=8)
    ax.set(xlabel="Accuracy against local normative belief (not world truth)", ylabel="Task regret per action opportunity",
           title="Remembering a report and making a good decision are different tasks", xlim=(0, 1.04))
    ax.grid(alpha=.15)
    fig.tight_layout()
    fig.savefig(out / "memory_vs_action.png", bbox_inches="tight")
    plt.close(fig)

    if len(populations) > 1:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        for condition in ("structured", "bm25", "hybrid", "hybrid_guarded", "guarded_lineage2"):
            rows = [systems[f"{p}/{condition}"] for p in populations if f"{p}/{condition}" in systems]
            if not rows:
                continue
            for ax, key in zip(axes, ("seconds", "decision_regret")):
                ax.plot([s["population"] for s in rows], [metric(s, key)["mean"] for s in rows],
                        "o-", label=condition, color=colors[condition])
        for ax, label in zip(axes, ("Seconds per world", "Regret per opportunity")):
            ax.set(xlabel="Agent population", ylabel=label)
            ax.grid(alpha=.15)
            ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "scaling.png", bbox_inches="tight")
        plt.close(fig)
    print(f"Plots saved to {out}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    args = parser.parse_args(argv)
    make_plots(args.directory)


if __name__ == "__main__":
    main()
