#!/usr/bin/env python3
"""
Plot EDT/CDT projection trajectories across scaffolded reasoning steps.

Reads the JSON output from extract_scaffolded_activations.py and produces
a matplotlib figure showing how the model's internal EDT/CDT representation
evolves through the 5-step scaffold.

Usage:
    python activation_steering/plot_scaffolded_trajectories.py
    python activation_steering/plot_scaffolded_trajectories.py --input path/to/trajectories.json
    python activation_steering/plot_scaffolded_trajectories.py --per-question
"""

import argparse
import json
import numpy as np
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

ACTIVATIONS_DIR = Path(__file__).parent / "activations"
CHARTS_DIR = Path(__file__).parent.parent / "charts" / "scaffolded_trajectories"

STEP_LABELS = ["1\nAgents", "2\nActions", "3\nPayoffs", "4\nRelation", "5\nDecision"]
STEP_LABELS_SHORT = ["Agents", "Actions", "Payoffs", "Relation", "Decision"]

EDT_COLOR = "#2196F3"
CDT_COLOR = "#FF5722"
EDT_FILL = "#2196F340"
CDT_FILL = "#FF572240"


def load_trajectories(path: Path) -> dict:
    with open(path) as f:
        return json.load(f)


def plot_mean_trajectories(data: dict, out_path: Path):
    """Main figure: mean projection ± std at each step, EDT vs CDT final answers."""
    trajs = data["trajectories"]
    edt_trajs = [t for t in trajs if t["is_edt_aligned"]]
    cdt_trajs = [t for t in trajs if t["is_cdt_aligned"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    xs = np.arange(5)

    for label, group, color, fill in [
        (f"EDT answers (n={len(edt_trajs)})", edt_trajs, EDT_COLOR, EDT_FILL),
        (f"CDT answers (n={len(cdt_trajs)})", cdt_trajs, CDT_COLOR, CDT_FILL),
    ]:
        if not group:
            continue
        projs = np.array([t["projections"] for t in group])
        means = projs.mean(axis=0)
        stds = projs.std(axis=0)

        ax.plot(xs, means, "o-", color=color, linewidth=2, markersize=6, label=label)
        ax.fill_between(xs, means - stds, means + stds, color=fill)

    ax.axhline(0, color="grey", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.set_xticks(xs)
    ax.set_xticklabels(STEP_LABELS, fontsize=9)
    ax.set_ylabel("Projection onto EDT/CDT direction", fontsize=10)
    ax.set_title(
        f"EDT/CDT trajectory through scaffolded reasoning (layer {data['layer']})",
        fontsize=11,
    )
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close(fig)


def plot_individual_traces(data: dict, out_path: Path):
    """Spaghetti plot: every trial as a thin line, colored by final answer."""
    trajs = data["trajectories"]

    fig, ax = plt.subplots(figsize=(8, 5))
    xs = np.arange(5)

    for t in trajs:
        if t["is_edt_aligned"]:
            color = EDT_COLOR
        elif t["is_cdt_aligned"]:
            color = CDT_COLOR
        else:
            color = "grey"
        ax.plot(xs, t["projections"], color=color, alpha=0.12, linewidth=0.8)

    edt_trajs = [t for t in trajs if t["is_edt_aligned"]]
    cdt_trajs = [t for t in trajs if t["is_cdt_aligned"]]
    for label, group, color in [
        ("EDT", edt_trajs, EDT_COLOR),
        ("CDT", cdt_trajs, CDT_COLOR),
    ]:
        if not group:
            continue
        projs = np.array([t["projections"] for t in group])
        ax.plot(xs, projs.mean(axis=0), "o-", color=color, linewidth=2.5,
                markersize=5, label=f"{label} mean (n={len(group)})", zorder=10)

    ax.axhline(0, color="grey", linewidth=0.5, linestyle="--", alpha=0.5)
    ax.set_xticks(xs)
    ax.set_xticklabels(STEP_LABELS, fontsize=9)
    ax.set_ylabel("Projection onto EDT/CDT direction", fontsize=10)
    ax.set_title(
        f"Individual trajectories through scaffold (layer {data['layer']})",
        fontsize=11,
    )
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close(fig)


def plot_gap_evolution(data: dict, out_path: Path):
    """Bar chart: EDT-CDT gap at each step."""
    trajs = data["trajectories"]
    edt_trajs = [t for t in trajs if t["is_edt_aligned"]]
    cdt_trajs = [t for t in trajs if t["is_cdt_aligned"]]

    if not edt_trajs or not cdt_trajs:
        print("Need both EDT and CDT trials for gap plot, skipping.")
        return

    edt_projs = np.array([t["projections"] for t in edt_trajs])
    cdt_projs = np.array([t["projections"] for t in cdt_trajs])
    gaps = edt_projs.mean(axis=0) - cdt_projs.mean(axis=0)

    fig, ax = plt.subplots(figsize=(7, 4))
    xs = np.arange(5)
    colors = [EDT_COLOR if g > 0 else CDT_COLOR for g in gaps]
    ax.bar(xs, gaps, color=colors, alpha=0.8, edgecolor="white")

    ax.axhline(0, color="grey", linewidth=0.5)
    ax.set_xticks(xs)
    ax.set_xticklabels(STEP_LABELS_SHORT, fontsize=9)
    ax.set_ylabel("EDT - CDT mean projection gap", fontsize=10)
    ax.set_title(
        f"Separation between EDT/CDT trajectories at each step (layer {data['layer']})",
        fontsize=11,
    )
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close(fig)


def plot_per_question(data: dict, out_dir: Path):
    """One small multiples figure per question, showing all samples."""
    trajs = data["trajectories"]
    by_qid = {}
    for t in trajs:
        by_qid.setdefault(t["qid"], []).append(t)

    qids = sorted(by_qid.keys())
    ncols = 4
    nrows = (len(qids) + ncols - 1) // ncols

    fig, axes = plt.subplots(nrows, ncols, figsize=(3.5 * ncols, 2.8 * nrows),
                             sharex=True, squeeze=False)
    xs = np.arange(5)

    for idx, qid in enumerate(qids):
        ax = axes[idx // ncols][idx % ncols]
        group = by_qid[qid]

        for t in group:
            color = EDT_COLOR if t["is_edt_aligned"] else (CDT_COLOR if t["is_cdt_aligned"] else "grey")
            ax.plot(xs, t["projections"], "o-", color=color, alpha=0.5,
                    linewidth=1, markersize=3)

        ax.axhline(0, color="grey", linewidth=0.5, linestyle="--", alpha=0.4)
        ax.set_title(qid, fontsize=8, fontweight="bold")
        ax.tick_params(labelsize=7)
        if idx // ncols == nrows - 1:
            ax.set_xticks(xs)
            ax.set_xticklabels(STEP_LABELS_SHORT, fontsize=6, rotation=45)

    for idx in range(len(qids), nrows * ncols):
        axes[idx // ncols][idx % ncols].set_visible(False)

    fig.suptitle(
        f"Per-question trajectories (layer {data['layer']})",
        fontsize=12, y=1.01,
    )
    fig.tight_layout()
    out_path = out_dir / "per_question_trajectories.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    print(f"Saved: {out_path}")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Plot scaffolded activation trajectories")
    parser.add_argument(
        "--input", type=str,
        default=str(ACTIVATIONS_DIR / "scaffolded_trajectories_layer40.json"),
        help="Trajectory JSON file",
    )
    parser.add_argument("--per-question", action="store_true", help="Generate per-question grid")
    args = parser.parse_args()

    data = load_trajectories(Path(args.input))
    print(f"Loaded {data['n_trials']} trajectories, layer {data['layer']}")

    CHARTS_DIR.mkdir(parents=True, exist_ok=True)

    plot_mean_trajectories(data, CHARTS_DIR / "mean_trajectories.png")
    plot_individual_traces(data, CHARTS_DIR / "individual_traces.png")
    plot_gap_evolution(data, CHARTS_DIR / "edt_cdt_gap.png")

    if args.per_question:
        plot_per_question(data, CHARTS_DIR)


if __name__ == "__main__":
    main()
