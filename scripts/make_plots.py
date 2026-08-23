"""Publication-plain plots from the results directories.

Reads results/core, results/heldout, results/scaling, results/capacity,
results/ablations (whichever exist) and writes PNGs to results/plots/.

Run:  python3 scripts/make_plots.py
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent / "results"
OUT = ROOT / "plots"
OUT.mkdir(parents=True, exist_ok=True)

SYSTEM_ORDER = ["recency", "bm25", "vector", "vector_recency", "vector_meta",
                "text_structured", "structured", "hybrid"]
plt.rcParams.update({"figure.dpi": 150, "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False})


def load_summary(path: Path):
    rows = []
    with open(path) as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def plot_overall_by_family(rows, name):
    fams = sorted({r["family"] for r in rows})
    systems = [s for s in SYSTEM_ORDER
               if any(r["system"] == s for r in rows)]
    fig, ax = plt.subplots(figsize=(8, 3.2))
    width = 0.8 / len(systems)
    for i, sysname in enumerate(systems):
        xs, ys, errs = [], [], []
        for j, fam in enumerate(fams):
            r = next(r for r in rows if r["family"] == fam
                     and r["system"] == sysname and r["metric"] == "overall")
            xs.append(j + i * width)
            ys.append(float(r["mean"]))
            errs.append(float(r["ci95_hi"]) - float(r["mean"]))
        ax.bar(xs, ys, width=width, yerr=errs, capsize=1.5, label=sysname)
    ax.set_xticks([j + 0.4 for j in range(len(fams))])
    ax.set_xticklabels(fams)
    ax.set_ylabel("overall accuracy")
    ax.set_ylim(0, 1.05)
    ax.legend(ncol=4, fontsize=7, frameon=False)
    ax.set_title(f"{name} suite: overall accuracy by family (95% CI)")
    fig.tight_layout()
    fig.savefig(OUT / f"{name}_overall.png")
    plt.close(fig)


def plot_boundary_violations(rows, name):
    fams = sorted({r["family"] for r in rows})
    systems = [s for s in SYSTEM_ORDER
               if any(r["system"] == s for r in rows)]
    fig, ax = plt.subplots(figsize=(8, 3))
    width = 0.8 / len(systems)
    for i, sysname in enumerate(systems):
        xs, ys = [], []
        for j, fam in enumerate(fams):
            r = next(r for r in rows if r["family"] == fam
                     and r["system"] == sysname
                     and r["metric"] == "boundary_violation_rate")
            xs.append(j + i * width)
            ys.append(float(r["mean"]))
        ax.bar(xs, ys, width=width, label=sysname)
    ax.set_xticks([j + 0.4 for j in range(len(fams))])
    ax.set_xticklabels(fams)
    ax.set_ylabel("boundary violation rate")
    ax.legend(ncol=4, fontsize=7, frameon=False)
    ax.set_title(f"{name} suite: knowledge-boundary violations")
    fig.tight_layout()
    fig.savefig(OUT / f"{name}_boundary.png")
    plt.close(fig)


def plot_dimension_profile(rows, name, family):
    dims = sorted({r["metric"][4:] for r in rows if r["metric"].startswith("dim_")})
    systems = [s for s in SYSTEM_ORDER
               if any(r["system"] == s for r in rows)]
    fig, ax = plt.subplots(figsize=(9, 3.2))
    width = 0.8 / len(systems)
    for i, sysname in enumerate(systems):
        xs, ys = [], []
        for j, dim in enumerate(dims):
            match = [r for r in rows if r["family"] == family
                     and r["system"] == sysname
                     and r["metric"] == f"dim_{dim}"]
            if match:
                xs.append(j + i * width)
                ys.append(float(match[0]["mean"]))
        ax.bar(xs, ys, width=width, label=sysname)
    ax.set_xticks([j + 0.4 for j in range(len(dims))])
    ax.set_xticklabels(dims, rotation=20)
    ax.set_ylabel("accuracy")
    ax.set_ylim(0, 1.05)
    ax.legend(ncol=4, fontsize=7, frameon=False)
    ax.set_title(f"{name}/{family}: accuracy by benchmark dimension")
    fig.tight_layout()
    fig.savefig(OUT / f"{name}_{family}_dimensions.png")
    plt.close(fig)


def plot_scaling():
    path = ROOT / "scaling" / "scaling.csv"
    if not path.exists():
        return
    rows = load_summary(path)
    by_sys = defaultdict(list)
    for r in rows:
        by_sys[r["system"]].append(r)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2))
    for sysname, rs in by_sys.items():
        rs.sort(key=lambda r: int(r["n_agents"]))
        ns = [int(r["n_agents"]) for r in rs]
        axes[0].errorbar(ns, [float(r["overall_mean"]) for r in rs],
                         yerr=[float(r["overall_sd"]) for r in rs],
                         marker="o", ms=3, label=sysname, capsize=2)
        axes[1].plot(ns, [float(r["bench_seconds"]) for r in rs],
                     marker="o", ms=3, label=sysname)
    axes[0].set_xlabel("agents"), axes[0].set_ylabel("overall accuracy")
    axes[0].set_xscale("log", base=2), axes[0].set_ylim(0, 1.05)
    axes[1].set_xlabel("agents"), axes[1].set_ylabel("benchmark seconds")
    axes[1].set_xscale("log", base=2), axes[1].set_yscale("log")
    axes[1].legend(fontsize=7, frameon=False)
    fig.suptitle("scaling: accuracy and cost vs world size")
    fig.tight_layout()
    fig.savefig(OUT / "scaling.png")
    plt.close(fig)


def plot_capacity():
    path = ROOT / "capacity" / "capacity.json"
    if not path.exists():
        return
    data = json.loads(path.read_text())
    fig, ax = plt.subplots(figsize=(6, 3.2))
    systems = sorted({s["system"] for s in data["summary"]})
    for sysname in systems:
        for policy, style in (("fifo", "--"), ("importance", "-"), ("-", ":")):
            pts = [(s["cap"], s["overall_mean"]) for s in data["summary"]
                   if s["system"] == sysname and s["policy"] == policy]
            if not pts:
                continue
            caps = [10000 if c == "unlimited" else int(c) for c, _ in pts]
            order = sorted(range(len(caps)), key=lambda i: caps[i])
            ax.plot([caps[i] for i in order], [pts[i][1] for i in order],
                    style, marker="o", ms=3,
                    label=f"{sysname} ({policy})" if policy != "-" else
                          f"{sysname} (unlimited)")
    ax.set_xscale("log")
    ax.set_xlabel("memory cap (records; 10^4 = unlimited)")
    ax.set_ylabel("overall accuracy")
    ax.legend(fontsize=6, frameon=False, ncol=2)
    ax.set_title("capacity pressure under overload")
    fig.tight_layout()
    fig.savefig(OUT / "capacity.png")
    plt.close(fig)


def main():
    for name in ("core", "heldout"):
        path = ROOT / name / "summary.csv"
        if path.exists():
            rows = load_summary(path)
            plot_overall_by_family(rows, name)
            plot_boundary_violations(rows, name)
            fams = sorted({r["family"] for r in rows})
            plot_dimension_profile(rows, name, fams[0])
    plot_scaling()
    plot_capacity()
    print(f"plots written to {OUT}")


if __name__ == "__main__":
    main()
