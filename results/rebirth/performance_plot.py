"""Render registered study summaries; plotting is outside the timed runtime."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def render(source, destination):
    result = json.loads(Path(source).read_text())
    conditions = sorted(result["conditions"], key=lambda row: (row["days"], row["density"] != "ordinary"))
    labels = [f"{row['days']}d\n{'ordinary' if row['density']=='ordinary' else '12 talks/day'}" for row in conditions]
    has_disk = bool(conditions and "disk_transaction" in conditions[0])
    fields = [("memory_transaction", "Actual temporary transaction + response JSON"),
              ("history_speed_ratio", "Bulk history advancement: append cost"),
              ("transaction_peak_ratio", "Incremental Python allocation peak")]
    if has_disk:
        fields.insert(1, ("disk_transaction", "Transaction with saved command journal"))
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(2, 2, figsize=(12, 8), constrained_layout=True)
    for ax, (key, title) in zip(axes.flat, fields):
        values = [row[key]["geometric_mean"] for row in conditions]
        errors = [[value-row[key]["low95"] for value,row in zip(values,conditions)],
                  [row[key]["high95"]-value for value,row in zip(values,conditions)]]
        ax.errorbar(range(len(values)), values, yerr=errors, fmt="o", color="#176b73", ecolor="#344e5b", capsize=4)
        ax.axhline(1, color="#a85e43", lw=1, linestyle="--")
        ax.set_xticks(range(len(values)), labels)
        ax.set_ylabel("Reference / optimized cost")
        ax.set_title(title, loc="left", fontweight="bold")
        ax.grid(axis="y", alpha=.2)
        ax.set_ylim(bottom=0)
    phase = "Heldout" if conditions and conditions[0]["seeds"] == 20 else "Development"
    if not has_disk:
        panel=axes.flat[3]
        panel.axis("off")
        panel.text(0, .94, "Scope and fidelity", fontsize=13, fontweight="bold", va="top")
        panel.text(0, .78, f"{result['cells']} matched histories; {result['accepted_timed_transactions']:,} timed transactions\n"
                   f"Declared semantic equality: {result['all_semantics_equal']}\n"
                   "Six NPCs; three durations; two interaction densities\n\n"
                   "Actual commit + canonical response JSON\n"
                   "Temporary sessions: no file-journal writes\n"
                   "Two saved-session attempts failed: ENOSPC\n"
                   "No saved-endpoint or durability speedup inferred", va="top", linespacing=1.7)
        phase="CPU-only "+phase.lower()
    fig.suptitle(f"{phase}: transaction gains and the append-cost tradeoff", fontsize=15, fontweight="bold")
    fig.supxlabel("Above 1: optimization lowers cost. Below 1: optimization costs more.\n"
                  "Points: paired-seed geometric means; bars: descriptive 95% seed bootstrap intervals.\n"
                  "Exact declared outcome fidelity checked separately. Python allocations are not process RAM.", fontsize=10)
    fig.savefig(destination, dpi=180, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    render(args.summary, args.output)
