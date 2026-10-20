"""Render actual frozen-study figures; requires matplotlib only for plotting."""
import json
from pathlib import Path
import random
import statistics
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
summary = json.loads((ROOT / "results/genesis/heldout/summary.json").read_text())
rows = [json.loads(line) for line in (ROOT / "results/genesis/heldout/worlds.jsonl").read_text().splitlines()]
out = ROOT / "results/genesis/figures"
out.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.facecolor": "white", "axes.titleweight": "bold", "svg.fonttype": "none"})


def save(fig, name):
    fig.subplots_adjust(bottom=.23, left=.15, right=.96, top=.88)
    for note in fig.texts:
        note.set_position((.15, .025))
    fig.savefig(out / (name + ".png"), dpi=180, bbox_inches="tight")
    fig.savefig(out / (name + ".svg"), bbox_inches="tight")
    fig.savefig(out / (name + ".pdf"), bbox_inches="tight")
    plt.close(fig)


labels = ["guarded_none", "guarded_sources", "guarded_lineage"]
fig, ax = plt.subplots(figsize=(7.8, 4.5))
for i, label in enumerate(labels):
    record = summary["conditions"][label]["delivery_fill_rate"]
    mean = record["mean"] * 100
    low, high = [value * 100 for value in record["ci95"]]
    ax.errorbar(mean, i, xerr=[[mean - low], [high - mean]], fmt="o", capsize=5,
                color=["#315c58", "#b17a3e", "#854b4b"][i], markersize=8)
    ax.text(high + .08, i, "%.2f%%" % mean, va="center")
ax.set(yticks=range(3), yticklabels=["Ungated", "Sender gate", "Root gate"],
       xlabel="Settled citizen units delivered (%)", title="Executed delivery: no demonstrated benefit from gating",
       xlim=(69.5, 74.5), ylim=(2.5, -.5))
ax.grid(axis="x", alpha=.2)
fig.text(.1, -.01, "Means across 6 balanced cells; intervals bootstrap 30 independent seed clusters.\n"
         "Axis is truncated to resolve small differences; paired contrast is analyzed separately.", fontsize=8)
save(fig, "01_primary_delivery")

fig, ax = plt.subplots(figsize=(7.8, 4.6))
contrast = summary["confirmatory_contrast"]
values = [r["difference"] * 100 for r in contrast["seed_differences"]]
ax.scatter(values, np.arange(len(values)), s=22, color="#668d87", alpha=.8)
ax.axvline(0, color="#aaa", linestyle="--", linewidth=1)
ax.axvline(contrast["mean"] * 100, color="#864a43", linewidth=1.5)
ax.axvspan(contrast["ci95"][0] * 100, contrast["ci95"][1] * 100, color="#864a43", alpha=.15)
ax.set(xlabel="Root gate − ungated delivery (percentage points)", ylabel="Independent seed index",
       title="Preregistered paired effect is small and adverse")
fig.text(.1, -.01, "One point per seed after averaging its 6 paired cells. Shading: 95% paired seed-bootstrap CI.\n"
         "Mean −0.180 pp; CI [−0.257, −0.104]. This is a simulator-specific effect.", fontsize=8)
save(fig, "02_paired_effect")

fig, ax = plt.subplots(figsize=(8.4, 4.7))
conditions = ["fixed_stock_fixed_order", "fixed_stock_seeded_order", "per_capita_fixed_order", "guarded_none"]
names = ["Fixed stock\nFixed order", "Fixed stock\nSeeded order", "Per capita\nFixed order", "Per capita\nSeeded order"]
means, lows, highs = [], [], []
for condition in conditions:
    selected = [r["metrics"]["delivery_fill_rate"] * 100 for r in sorted(rows, key=lambda row: row["config"]["seed"]) if r["condition"] == condition
                and r["config"]["family"] == "reversal" and r["config"]["n_agents"] == 32]
    means.append(sum(selected) / len(selected))
    # Mean interval under paired seed resampling; use independently saved summary for control cells.
    if condition != "guarded_none":
        interval = summary["conditions"][condition]["delivery_fill_rate"]["ci95"]
    else:
        rng = random.Random(72831)
        boot = sorted(statistics.fmean(rng.choices(selected, k=len(selected))) / 100
                      for _ in range(10000))
        interval = [boot[249], boot[9749]]
    lows.append(means[-1] - interval[0] * 100)
    highs.append(interval[1] * 100 - means[-1])
ax.bar(range(4), means, yerr=[lows, highs], capsize=4,
       color=["#a67a52", "#c09772", "#315c58", "#668d87"])
for i, mean in enumerate(means): ax.text(i, mean + highs[i] + 2, "%.2f%%" % mean, ha="center")
ax.set(xticks=range(4), xticklabels=names, ylabel="Settled units delivered (%)", ylim=(0, 100),
       title="Resource scale dominates district fill in the 32-citizen control")
fig.text(.1, -.01, "Reversal family, guarded ungated policy, capacity32; 30 paired seeds. Descriptive controls.\n"
         "Aggregate ordering effects are small; allocation distribution is examined separately.", fontsize=8)
save(fig, "03_resource_controls")

fig, ax = plt.subplots(figsize=(8.2, 4.8))
keys = ["local_recall_accuracy", "belief_current_accuracy", "belief_accuracy_when_answered", "answer_coverage", "delivery_fill_rate"]
x = np.arange(len(keys))
for offset, label, color in [(-.18, "guarded_none", "#315c58"), (.18, "guarded_lineage", "#a16e4b")]:
    ax.bar(x + offset, [summary["conditions"][label][key]["mean"] * 100 for key in keys],
           width=.36, label="Ungated" if offset < 0 else "Root gate", color=color)
ax.set(xticks=x, xticklabels=["Local recall", "Current belief\n(all decisions)", "Current belief\n(when answered)", "Answer coverage", "Delivery fill"],
       ylabel="Percentage within each metric's own denominator", ylim=(0, 108),
       title="Perfect canonical recall is compatible with imperfect execution")
ax.legend(frameon=False, loc="upper right")
fig.text(.1, -.01, "Metrics have different, policy-dependent denominators; these are descriptive means, not a funnel.\n"
         "Structured canonical-key local recall is a ceiling diagnostic, not a difficult memory evaluation.", fontsize=8)
save(fig, "04_measurement_layers")
print(out)
