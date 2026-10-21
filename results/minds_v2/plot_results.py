"""Plot raw MindsBench outcomes with standard Matplotlib; Python3.9+ is enough.

Usage: MPLCONFIGDIR=/tmp/kalends-mpl python3 plot_results.py RUN_DIRECTORY NEW_PNG
No game/model runtime is imported. Plotting is outside the game's dependencies.
"""
import argparse
import json
from pathlib import Path
import random
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def interval(values):
    rng=random.Random(94617)
    draws=sorted(statistics.mean(rng.choices(values,k=len(values))) for _ in range(2000))
    return statistics.mean(values),draws[49],draws[1949]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run",type=Path);parser.add_argument("output",type=Path)
    args=parser.parse_args()
    if args.output.exists():raise ValueError("Choose a new plot path; existing artifacts are preserved")
    rows=[json.loads(line) for line in (args.run/"raw.jsonl").read_text().splitlines()]
    metadata=json.loads((args.run/"metadata.json").read_text())
    arms=metadata["design"]["primary_arms"];families=metadata["design"]["families"]
    seeds=sorted({row["seed"] for row in rows})
    labels={"fifo":"FIFO + vintage","bm25":"BM25 + vintage","structured":"Structured","guarded":"Guarded","mind":"Minds V2","no_consolidation":"No consolidation","no_lineage":"No lineage","no_revision":"No revision"}
    colors=["#1c716b" if arm=="mind" else "#b25f45" if arm.startswith("no_") else "#8b9499" for arm in arms]
    plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,"axes.spines.right":False})
    fig=plt.figure(figsize=(14,8));grid=fig.add_gridspec(2,2,width_ratios=(1.1,1),hspace=.55,wspace=.42)
    utility=fig.add_subplot(grid[:,0]);family_ax=fig.add_subplot(grid[0,1]);storage=fig.add_subplot(grid[1,1])
    for i,arm in enumerate(arms):
        values=[statistics.mean(row["arms"][arm]["utility"] for row in rows if row["seed"]==seed) for seed in seeds]
        mean,low,high=interval(values)
        utility.barh(i,mean,color=colors[i],height=.65)
        utility.errorbar(mean,i,xerr=[[mean-low],[high-mean]],fmt="none",color="#263238",capsize=3)
        utility.text(mean+.06,i,f"{mean:.2f}",va="center",fontsize=9)
    utility.set_yticks(range(len(arms)),[labels[a] for a in arms]);utility.invert_yaxis()
    utility.set_xlabel("Executed utility (coin-equivalent per world)")
    utility.set_title("A. Fixed selector; actual funded settlements",loc="left",fontweight="bold")
    for i,family in enumerate(families):
        values=[row["arms"]["mind"]["utility"]-row["arms"]["structured"]["utility"] for row in rows if row["family"]==family]
        mean,low,high=interval(values)
        family_ax.errorbar(mean,i,xerr=[[mean-low],[high-mean]],fmt="o",color="#1c716b",capsize=3)
    family_ax.axvline(0,color="#999999",lw=1,ls="--")
    family_ax.set_yticks(range(len(families)),[f.replace("_"," ") for f in families]);family_ax.invert_yaxis()
    family_ax.set_xlabel("Minds V2 − structured utility")
    family_ax.set_title("B. Primary paired contrast by family",loc="left",fontweight="bold")
    sizes=[statistics.mean(row["arms"][arm]["footprint"]["serialized_bytes"] for row in rows)/1024 for arm in arms]
    storage.bar(range(len(arms)),sizes,color=colors)
    storage.set_xticks(range(len(arms)),[labels[a] for a in arms],rotation=45,ha="right",fontsize=8)
    storage.set_ylabel("Mean serialized mind KiB")
    storage.set_title("C. Equal record caps do not imply equal bytes",loc="left",fontweight="bold")
    phase="DEVELOPMENT PILOT — not confirmatory" if metadata["phase"]=="pilot" else "REGISTERED HELDOUT — authored synthetic economy"
    fig.suptitle(f"MindsBench V2 · {phase}",x=.06,ha="left",fontsize=15,fontweight="bold")
    fig.text(.06,.015,f"{len(seeds)} paired seeds × {len(families)} families; 95% descriptive seed bootstrap. Total record cap {metadata['design']['capacity_records']}, context {metadata['design']['decision_context_records']}.\nStructured fields and authored utilities are shared; no real embedding model, paid inference or human test. References/retention-only arms remain in raw tables.",fontsize=9,color="#50575b")
    fig.subplots_adjust(left=.16,right=.98,top=.89,bottom=.19)
    args.output.parent.mkdir(parents=True,exist_ok=True);fig.savefig(args.output,dpi=160);plt.close(fig)
    print(args.output)


if __name__=="__main__":main()
