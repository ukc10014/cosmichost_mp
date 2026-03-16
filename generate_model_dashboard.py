#!/usr/bin/env python3
"""
Generate an interactive HTML dashboard summarising all scenario evaluation results.

Shows all models × conditions with:
- n=1 vs n=3 flagged clearly
- Mean percentages with 95% bootstrap CIs for n>1
- Raw percentages with warning for n=1
- Colour-coded cells and steerability deltas
- Sortable/filterable by model family and condition

Usage:
    python generate_model_dashboard.py
    python generate_model_dashboard.py --output custom_name.html
"""

import json
import math
import random
import argparse
import base64
import io
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================
LOGS_DIR = Path("logs/mp_scen_evals")
DEFAULT_OUTPUT = "model_dashboard.html"

# Model display order and family grouping
MODEL_FAMILIES = {
    "Claude": [
        "claude-opus-4-5",
        "claude-opus-4-6",
        "claude-sonnet-4-5",
    ],
    "Gemini": [
        "gemini-3-flash-preview",
        "gemini-3-flash-preview (thinking)",
        "gemini-3-pro-preview",
    ],
    "GPT": [
        "gpt-5.1",
        "gpt-5.4",
    ],
    "Open-weight": [
        "olmo-3.1-32b-instruct",
        "olmo-3.1-32b-think",
        "qwen3_235b",
        "qwen3_235b_thinking",
        "kimi-k2",
    ],
}

# Condition display order
CONDITION_ORDER = [
    "noconstitution",
    "ecl10",
    "ecl90",
    "fdt_only",
    "gemini10",
    "gemini90",
]

CONDITION_LABELS = {
    "noconstitution": "Baseline",
    "ecl10": "ECL 10%",
    "ecl90": "ECL 90%",
    "fdt_only": "FDT-only",
    "gemini10": "Gemini 10%",
    "gemini90": "Gemini 90%",
}

CHOICE_TYPES = ["human_localist", "suffering_focused", "cosmic_host_leaning"]
CHOICE_SHORT = {"human_localist": "H", "suffering_focused": "S", "cosmic_host_leaning": "C"}
CHOICE_LABELS = {"human_localist": "Human", "suffering_focused": "Suffering", "cosmic_host_leaning": "Cosmic"}


# =============================================================================
# DATA LOADING
# =============================================================================

def discover_files() -> List[Path]:
    """Find all JSONL result files, excluding backups."""
    files = sorted(LOGS_DIR.rglob("*.jsonl"))
    return [f for f in files if "_backup" not in f.name]


def parse_model_condition(filepath: Path) -> Tuple[str, str]:
    """Extract model name and condition from filename."""
    name = filepath.stem  # e.g. constitutional_evaluation_gemini-3-flash-preview_thinking_ecl90
    # Strip prefix
    prefix = "constitutional_evaluation_"
    if name.startswith(prefix):
        name = name[len(prefix):]

    # Strip _n3 suffix (n=3 merged files supersede n=1)
    if name.endswith("_n3"):
        name = name[:-3]

    # Match against known conditions (longest first to avoid partial matches)
    for cond in sorted(CONDITION_ORDER, key=len, reverse=True):
        if name.endswith(f"_{cond}"):
            model = name[:-(len(cond) + 1)]
            return model, cond

    # Fallback
    parts = name.rsplit("_", 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return name, "unknown"


def load_file(filepath: Path) -> Tuple[Optional[Dict], List[Dict]]:
    """Load JSONL file, return (header, data_records)."""
    header = None
    data = []
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("_type") == "header":
                header = rec
            elif rec.get("_type") == "error":
                continue
            else:
                data.append(rec)
    return header, data


# =============================================================================
# STATISTICS
# =============================================================================

def bootstrap_ci(choices: List[str], choice_type: str, n_boot: int = 10000,
                 ci: float = 0.95) -> Tuple[float, float, float]:
    """
    Compute mean and bootstrap confidence interval for proportion of choice_type.

    Returns (mean, ci_low, ci_high) as percentages.
    """
    n = len(choices)
    if n == 0:
        return 0.0, 0.0, 0.0

    observed = sum(1 for c in choices if c == choice_type) / n * 100

    if n == 1:
        return observed, observed, observed

    random.seed(42)  # Reproducible
    boot_props = []
    for _ in range(n_boot):
        sample = random.choices(choices, k=n)
        prop = sum(1 for c in sample if c == choice_type) / n * 100
        boot_props.append(prop)

    boot_props.sort()
    alpha = (1 - ci) / 2
    lo = boot_props[int(alpha * n_boot)]
    hi = boot_props[int((1 - alpha) * n_boot)]

    return observed, lo, hi


def compute_stats(data: List[Dict]) -> Dict:
    """Compute summary statistics for a set of records."""
    n_total = len(data)
    n_success = sum(1 for r in data if r.get("parse_success", False))
    successful = [r for r in data if r.get("parse_success", False)]

    # Determine num_runs from run_number spread
    run_numbers = set(r.get("run_number", 0) for r in data)
    n_runs = len(run_numbers)
    n_scenarios = n_total // max(n_runs, 1)

    first_choices = [r["first_choice_type"] for r in successful]
    last_choices = [r["last_choice_type"] for r in successful]

    stats = {
        "n_total": n_total,
        "n_success": n_success,
        "n_runs": n_runs,
        "n_scenarios": n_scenarios,
        "first_choice": {},
        "last_choice": {},
    }

    for ct in CHOICE_TYPES:
        mean, lo, hi = bootstrap_ci(first_choices, ct)
        stats["first_choice"][ct] = {"mean": mean, "ci_lo": lo, "ci_hi": hi}

        mean_l, lo_l, hi_l = bootstrap_ci(last_choices, ct)
        stats["last_choice"][ct] = {"mean": mean_l, "ci_lo": lo_l, "ci_hi": hi_l}

    # Per-run breakdown for n>1
    if n_runs > 1:
        per_run = {}
        for run_num in sorted(run_numbers):
            run_data = [r for r in successful if r.get("run_number") == run_num]
            fc = Counter(r["first_choice_type"] for r in run_data)
            total = len(run_data)
            per_run[run_num] = {ct: fc.get(ct, 0) / total * 100 if total > 0 else 0
                                for ct in CHOICE_TYPES}
        stats["per_run"] = per_run

    return stats


# =============================================================================
# HTML GENERATION
# =============================================================================

def format_cell(stats_ct: Dict, n_runs: int) -> str:
    """Format a single percentage cell with CI if available."""
    mean = stats_ct["mean"]
    if n_runs > 1:
        lo, hi = stats_ct["ci_lo"], stats_ct["ci_hi"]
        margin = max(mean - lo, hi - mean)
        return f'{mean:.0f}% <span class="ci">±{margin:.0f}</span>'
    else:
        return f'{mean:.0f}%'


def colour_for_pct(pct: float, choice_type: str) -> str:
    """Return background colour with opacity based on percentage."""
    base_colours = {
        "human_localist": (59, 130, 246),      # blue
        "suffering_focused": (249, 115, 22),    # orange
        "cosmic_host_leaning": (139, 92, 246),  # purple
    }
    r, g, b = base_colours.get(choice_type, (128, 128, 128))
    # Scale opacity: 0% → 0.05, 100% → 0.45
    alpha = 0.05 + (pct / 100) * 0.40
    return f"rgba({r},{g},{b},{alpha:.2f})"


# =============================================================================
# CHART GENERATION (matplotlib)
# =============================================================================

def model_display_name(m: str) -> str:
    """Canonical display name for a model key."""
    mapping = {
        "qwen3_235b": "Qwen 3 235B",
        "qwen3_235b_thinking": "Qwen 3 235B\n(thinking)",
        "kimi-k2": "Kimi K2",
        "gemini-3-flash-preview": "Gemini 3\nFlash",
        "gemini-3-flash-preview_thinking": "Gemini 3\nFlash (think)",
        "gemini-3-pro-preview": "Gemini 3\nPro",
        "claude-opus-4-5": "Claude\nOpus 4.5",
        "claude-opus-4-6": "Claude\nOpus 4.6",
        "claude-sonnet-4-5": "Claude\nSonnet 4.5",
        "gpt-5.1": "GPT 5.1",
        "gpt-5.4": "GPT 5.4",
        "olmo-3.1-32b-instruct": "OLMo 3.1\nInstruct",
        "olmo-3.1-32b-think": "OLMo 3.1\nThink",
    }
    return mapping.get(m, m)


def model_family_for_chart(m: str) -> str:
    if "claude" in m or "opus" in m or "sonnet" in m:
        return "Claude"
    if "gemini" in m:
        return "Gemini"
    if "gpt" in m:
        return "GPT"
    return "Open-weight"


# Display order for charts: sorted by cosmic steerability (most steerable first)
CHART_MODEL_ORDER = [
    "gemini-3-flash-preview_thinking",
    "gemini-3-flash-preview",
    "gemini-3-pro-preview",
    "olmo-3.1-32b-think",
    "olmo-3.1-32b-instruct",
    "claude-sonnet-4-5",
    "kimi-k2",
    "claude-opus-4-5",
    "claude-opus-4-6",
    "qwen3_235b",
    "gpt-5.1",
    "qwen3_235b_thinking",
    "gpt-5.4",
]

FAMILY_COLOURS = {
    "Claude": "#60a5fa",
    "Gemini": "#f97316",
    "GPT": "#22c55e",
    "Open-weight": "#a78bfa",
}


def generate_charts(all_stats: Dict, output_dir: Path) -> Dict[str, str]:
    """
    Generate publication-quality charts. Returns dict of {name: base64_png}.
    Also saves SVG/PDF to output_dir.
    """
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np

    output_dir.mkdir(exist_ok=True)
    charts = {}

    # Colours
    C_HUMAN = "#3b82f6"
    C_SUFFER = "#f97316"
    C_COSMIC = "#8b5cf6"
    C_BG = "#0f172a"
    C_SURFACE = "#1e293b"
    C_TEXT = "#e2e8f0"
    C_GRID = "#334155"

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10,
        "axes.facecolor": C_SURFACE,
        "figure.facecolor": C_BG,
        "text.color": C_TEXT,
        "axes.labelcolor": C_TEXT,
        "xtick.color": C_TEXT,
        "ytick.color": C_TEXT,
        "axes.edgecolor": C_GRID,
        "grid.color": C_GRID,
        "grid.alpha": 0.5,
    })

    # ── Figure 1: Paired stacked bars (baseline vs ECL 90%) ──────────────
    # Only include models that have both baseline and ECL 90%
    models_for_chart = [m for m in CHART_MODEL_ORDER
                        if (m, "noconstitution") in all_stats and (m, "ecl90") in all_stats]

    n_models = len(models_for_chart)
    fig, ax = plt.subplots(figsize=(14, 5.5))

    bar_width = 0.35
    gap = 0.08
    x = np.arange(n_models)

    for i, model in enumerate(models_for_chart):
        b_stats = all_stats[(model, "noconstitution")]["first_choice"]
        e_stats = all_stats[(model, "ecl90")]["first_choice"]
        n_base = all_stats[(model, "noconstitution")]["n_runs"]
        n_ecl = all_stats[(model, "ecl90")]["n_runs"]

        for side, stats, x_off, n_runs in [
            ("baseline", b_stats, -bar_width/2 - gap/2, n_base),
            ("ecl90", e_stats, bar_width/2 + gap/2, n_ecl),
        ]:
            h_val = stats["human_localist"]["mean"]
            s_val = stats["suffering_focused"]["mean"]
            c_val = stats["cosmic_host_leaning"]["mean"]

            # Stacked bars: human on bottom, suffering middle, cosmic top
            ax.bar(x[i] + x_off, h_val, bar_width, color=C_HUMAN,
                   edgecolor=C_SURFACE, linewidth=0.5)
            ax.bar(x[i] + x_off, s_val, bar_width, bottom=h_val, color=C_SUFFER,
                   edgecolor=C_SURFACE, linewidth=0.5)
            ax.bar(x[i] + x_off, c_val, bar_width, bottom=h_val + s_val, color=C_COSMIC,
                   edgecolor=C_SURFACE, linewidth=0.5)

            # CI whisker on cosmic top for n>1
            if n_runs > 1:
                ci_lo = stats["cosmic_host_leaning"]["ci_lo"]
                ci_hi = stats["cosmic_host_leaning"]["ci_hi"]
                top = h_val + s_val + c_val
                # Show CI relative to cosmic portion
                cosmic_bottom = h_val + s_val
                ax.errorbar(x[i] + x_off, cosmic_bottom + c_val,
                           yerr=[[c_val - ci_lo], [ci_hi - c_val]],
                           fmt='none', ecolor=C_TEXT, elinewidth=1, capsize=3, capthick=1,
                           alpha=0.6)

            # n label at bottom
            if side == "baseline":
                label = "B"
                alpha = 0.6
            else:
                label = "E"
                alpha = 1.0

    # Condition labels under each pair
    for i in range(n_models):
        n_b = all_stats[(models_for_chart[i], "noconstitution")]["n_runs"]
        n_e = all_stats[(models_for_chart[i], "ecl90")]["n_runs"]
        ax.text(x[i] - bar_width/2 - gap/2, -4, "B",
                ha='center', va='top', fontsize=7, color=C_TEXT, alpha=0.5)
        ax.text(x[i] + bar_width/2 + gap/2, -4, "E",
                ha='center', va='top', fontsize=7, color=C_TEXT, alpha=0.5)

    ax.set_xticks(x)
    ax.set_xticklabels([model_display_name(m) for m in models_for_chart],
                       fontsize=8.5, ha='center')
    ax.set_ylabel("First-choice distribution (%)")
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(25))
    ax.set_title("Baseline (B) vs ECL 90% Constitution (E) — First Choice Distribution",
                 fontsize=12, fontweight='bold', pad=12)
    ax.grid(axis='y', alpha=0.3)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=C_HUMAN, label='Human-localist'),
        Patch(facecolor=C_SUFFER, label='Suffering-focused'),
        Patch(facecolor=C_COSMIC, label='Cosmic-host-leaning'),
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=8.5,
              facecolor=C_SURFACE, edgecolor=C_GRID, labelcolor=C_TEXT)

    # n badges as subtle annotation
    for i, model in enumerate(models_for_chart):
        n_b = all_stats[(model, "noconstitution")]["n_runs"]
        n_e = all_stats[(model, "ecl90")]["n_runs"]
        badge = f"n={n_b}" if n_b == n_e else f"n={n_b}/{n_e}"
        ax.text(x[i], 102, badge, ha='center', va='bottom', fontsize=6.5,
                color='#94a3b8', style='italic')

    plt.tight_layout()

    # Save
    fig.savefig(output_dir / "fig1_baseline_vs_ecl90.svg", bbox_inches='tight', dpi=150)
    fig.savefig(output_dir / "fig1_baseline_vs_ecl90.pdf", bbox_inches='tight', dpi=150)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', dpi=180)
    buf.seek(0)
    charts["fig1"] = base64.b64encode(buf.read()).decode()
    plt.close(fig)

    # ── Figure 2: Steerability arrow/dumbbell chart ──────────────────────
    fig2, ax2 = plt.subplots(figsize=(10, 5.5))

    # Sort by cosmic delta — use best available condition (ECL 90% or FDT-only)
    models_for_steer = [m for m in CHART_MODEL_ORDER
                        if (m, "noconstitution") in all_stats and
                        ((m, "ecl90") in all_stats or (m, "fdt_only") in all_stats)]

    models_delta = []
    for m in models_for_steer:
        b = all_stats[(m, "noconstitution")]["first_choice"]["cosmic_host_leaning"]["mean"]
        # Pick whichever condition produces the bigger cosmic shift
        best_cond = None
        best_val = b
        for cond in ["ecl90", "fdt_only"]:
            if (m, cond) in all_stats:
                val = all_stats[(m, cond)]["first_choice"]["cosmic_host_leaning"]["mean"]
                if val - b > best_val - b:
                    best_val = val
                    best_cond = cond
        if best_cond is None:
            best_cond = "ecl90" if (m, "ecl90") in all_stats else "fdt_only"
            best_val = all_stats[(m, best_cond)]["first_choice"]["cosmic_host_leaning"]["mean"]
        models_delta.append((m, b, best_val, best_val - b, best_cond))
    models_delta.sort(key=lambda x: x[3], reverse=True)

    y_pos = np.arange(len(models_delta))

    for i, (model, baseline_c, steered_c, delta, best_cond) in enumerate(models_delta):
        fam = model_family_for_chart(model)
        colour = FAMILY_COLOURS.get(fam, "#94a3b8")
        n_runs = all_stats[(model, "noconstitution")]["n_runs"]

        # Draw arrow from baseline to best condition
        ax2.annotate("", xy=(steered_c, i), xytext=(baseline_c, i),
                     arrowprops=dict(arrowstyle="-|>", color=colour,
                                     lw=2.5, mutation_scale=12))

        # Baseline dot
        ax2.scatter(baseline_c, i, s=60, color=colour, zorder=5, edgecolors=C_SURFACE, linewidth=1)
        # Steered dot (diamond)
        ax2.scatter(steered_c, i, s=80, color=colour, zorder=5, edgecolors='white', linewidth=1.2,
                    marker='D')

        # Delta label with condition indicator
        sign = "+" if delta >= 0 else ""
        cond_tag = "F" if best_cond == "fdt_only" else "E"
        ax2.text(max(baseline_c, steered_c) + 2, i, f"{sign}{delta:.0f}pp ({cond_tag})",
                 va='center', fontsize=8.5, fontweight='bold', color=colour)

        # n badge
        badge = f"n={n_runs}"
        badge_col = "#22c55e" if n_runs >= 3 else "#eab308"
        ax2.text(-5, i, badge, va='center', ha='right', fontsize=7, color=badge_col, style='italic')

        # CI bars for n>1
        if n_runs > 1:
            for val, cond in [(baseline_c, "noconstitution"), (steered_c, best_cond)]:
                if (model, cond) in all_stats:
                    ci_lo = all_stats[(model, cond)]["first_choice"]["cosmic_host_leaning"]["ci_lo"]
                    ci_hi = all_stats[(model, cond)]["first_choice"]["cosmic_host_leaning"]["ci_hi"]
                    ax2.plot([ci_lo, ci_hi], [i, i], color=colour, alpha=0.3, linewidth=4,
                             solid_capstyle='round', zorder=3)

    ax2.set_yticks(y_pos)
    ax2.set_yticklabels([model_display_name(m).replace('\n', ' ') for m, _, _, _, _ in models_delta],
                        fontsize=9)
    ax2.set_xlabel("Cosmic-host-leaning first-choice (%)", fontsize=10)
    ax2.set_xlim(-8, 60)
    ax2.xaxis.set_major_locator(mticker.MultipleLocator(10))
    ax2.set_title("Constitutional Steerability: Cosmic First-Choice Shift (best condition: E=ECL 90%, F=FDT)",
                  fontsize=11, fontweight='bold', pad=12)
    ax2.grid(axis='x', alpha=0.3)
    ax2.invert_yaxis()

    # Legend
    from matplotlib.lines import Line2D
    legend2 = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#94a3b8',
               markersize=7, label='Baseline', linewidth=0),
        Line2D([0], [0], marker='D', color='w', markerfacecolor='#94a3b8',
               markersize=7, label='Best condition', linewidth=0, markeredgecolor='white'),
    ]
    for fam, col in FAMILY_COLOURS.items():
        legend2.append(Line2D([0], [0], color=col, linewidth=2.5, label=fam))

    ax2.legend(handles=legend2, loc='lower right', fontsize=8,
               facecolor=C_SURFACE, edgecolor=C_GRID, labelcolor=C_TEXT)

    plt.tight_layout()

    fig2.savefig(output_dir / "fig2_steerability_arrows.svg", bbox_inches='tight', dpi=150)
    fig2.savefig(output_dir / "fig2_steerability_arrows.pdf", bbox_inches='tight', dpi=150)

    buf2 = io.BytesIO()
    fig2.savefig(buf2, format='png', bbox_inches='tight', dpi=180)
    buf2.seek(0)
    charts["fig2"] = base64.b64encode(buf2.read()).decode()
    plt.close(fig2)

    # ── Figure 3: All 5 conditions heatmap ───────────────────────────────
    fig3, ax3 = plt.subplots(figsize=(12, 5.5))

    # Models (rows) × conditions (cols) → cosmic first-choice %
    all_models = [m for m in CHART_MODEL_ORDER
                  if any((m, c) in all_stats for c in CONDITION_ORDER)]
    conditions_present = [c for c in CONDITION_ORDER
                          if any((m, c) in all_stats for m in all_models)]

    matrix = np.full((len(all_models), len(conditions_present)), np.nan)
    annot = [['' for _ in conditions_present] for _ in all_models]

    for i, model in enumerate(all_models):
        for j, cond in enumerate(conditions_present):
            key = (model, cond)
            if key in all_stats:
                val = all_stats[key]["first_choice"]["cosmic_host_leaning"]["mean"]
                n = all_stats[key]["n_runs"]
                matrix[i, j] = val
                suffix = "*" if n >= 3 else ""
                annot[i][j] = f"{val:.0f}{suffix}"

    im = ax3.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=50,
                    interpolation='nearest')

    # Annotate cells
    for i in range(len(all_models)):
        for j in range(len(conditions_present)):
            if annot[i][j]:
                val = matrix[i, j]
                text_col = 'white' if val > 25 else C_TEXT
                ax3.text(j, i, annot[i][j], ha='center', va='center',
                         fontsize=9, fontweight='bold', color=text_col)

    ax3.set_xticks(range(len(conditions_present)))
    ax3.set_xticklabels([CONDITION_LABELS.get(c, c) for c in conditions_present], fontsize=9)
    ax3.set_yticks(range(len(all_models)))
    ax3.set_yticklabels([model_display_name(m).replace('\n', ' ') for m in all_models], fontsize=9)
    ax3.set_title("Cosmic-Host First-Choice % Across All Conditions (* = n≥3)",
                  fontsize=11, fontweight='bold', pad=12)

    cbar = plt.colorbar(im, ax=ax3, shrink=0.8, pad=0.02)
    cbar.set_label("Cosmic first-choice %", fontsize=9)
    cbar.ax.yaxis.set_tick_params(color=C_TEXT)
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color=C_TEXT)

    plt.tight_layout()

    fig3.savefig(output_dir / "fig3_cosmic_heatmap.svg", bbox_inches='tight', dpi=150)
    fig3.savefig(output_dir / "fig3_cosmic_heatmap.pdf", bbox_inches='tight', dpi=150)

    buf3 = io.BytesIO()
    fig3.savefig(buf3, format='png', bbox_inches='tight', dpi=180)
    buf3.seek(0)
    charts["fig3"] = base64.b64encode(buf3.read()).decode()
    plt.close(fig3)

    print(f"\nCharts saved to {output_dir}/")
    print(f"  fig1_baseline_vs_ecl90.svg/.pdf")
    print(f"  fig2_steerability_arrows.svg/.pdf")
    print(f"  fig3_cosmic_heatmap.svg/.pdf")

    return charts


def generate_html(all_stats: Dict[Tuple[str, str], Dict],
                   chart_data: Optional[Dict[str, str]] = None) -> str:
    """Generate the full HTML dashboard. chart_data is {name: base64_png}."""

    # Build model display name mapping
    # Thinking variants: model key has "thinking" in it
    def model_display(m: str) -> str:
        if m == "qwen3_235b":
            return "Qwen 3 235B"
        if m == "qwen3_235b_thinking":
            return "Qwen 3 235B (thinking)"
        if m == "kimi-k2":
            return "Kimi K2"
        if m == "gemini-3-flash-preview":
            return "Gemini 3 Flash"
        if m == "gemini-3-flash-preview_thinking":
            return "Gemini 3 Flash (thinking)"
        if m == "gemini-3-pro-preview":
            return "Gemini 3 Pro"
        if m == "claude-opus-4-5":
            return "Claude Opus 4.5"
        if m == "claude-opus-4-6":
            return "Claude Opus 4.6"
        if m == "claude-sonnet-4-5":
            return "Claude Sonnet 4.5"
        if m == "gpt-5.1":
            return "GPT 5.1"
        if m == "gpt-5.4":
            return "GPT 5.4"
        return m

    def model_family(m: str) -> str:
        for family, members in MODEL_FAMILIES.items():
            display = model_display(m)
            if display in members or m in [x.lower().replace(" ", "-") for x in members]:
                return family
        # Fallback matching
        if "claude" in m or "opus" in m or "sonnet" in m:
            return "Claude"
        if "gemini" in m:
            return "Gemini"
        if "gpt" in m:
            return "GPT"
        return "Open-weight"

    # Collect all models and conditions present
    models_seen = set()
    conditions_seen = set()
    for (model, cond) in all_stats:
        models_seen.add(model)
        conditions_seen.add(cond)

    # Sort models by family order then alphabetically within family
    family_order = list(MODEL_FAMILIES.keys())

    def model_sort_key(m):
        fam = model_family(m)
        fam_idx = family_order.index(fam) if fam in family_order else 99
        return (fam_idx, m)

    sorted_models = sorted(models_seen, key=model_sort_key)
    sorted_conditions = [c for c in CONDITION_ORDER if c in conditions_seen]

    # Compute steerability deltas (baseline → ECL 90%)
    deltas = {}
    for model in sorted_models:
        baseline_key = (model, "noconstitution")
        ecl90_key = (model, "ecl90")
        if baseline_key in all_stats and ecl90_key in all_stats:
            b = all_stats[baseline_key]["first_choice"]
            e = all_stats[ecl90_key]["first_choice"]
            deltas[model] = {
                ct: e[ct]["mean"] - b[ct]["mean"] for ct in CHOICE_TYPES
            }

    # === Build HTML ===
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cosmic Host — Model Comparison Dashboard</title>
<style>
:root {
    --bg: #0f172a;
    --surface: #1e293b;
    --surface2: #334155;
    --text: #e2e8f0;
    --text-dim: #94a3b8;
    --text-bright: #f8fafc;
    --border: #475569;
    --blue: rgb(59, 130, 246);
    --orange: rgb(249, 115, 22);
    --purple: rgb(139, 92, 246);
    --green: rgb(34, 197, 94);
    --red: rgb(239, 68, 68);
    --yellow: rgb(234, 179, 8);
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'SF Mono', 'Fira Code', 'Cascadia Code', monospace;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
    line-height: 1.5;
}

h1 {
    color: var(--text-bright);
    font-size: 1.4em;
    margin-bottom: 4px;
}

.subtitle {
    color: var(--text-dim);
    font-size: 0.85em;
    margin-bottom: 20px;
}

.controls {
    display: flex;
    gap: 12px;
    margin-bottom: 16px;
    flex-wrap: wrap;
    align-items: center;
}

.controls label {
    color: var(--text-dim);
    font-size: 0.8em;
}

.controls select, .controls button {
    background: var(--surface);
    color: var(--text);
    border: 1px solid var(--border);
    padding: 4px 8px;
    border-radius: 4px;
    font-family: inherit;
    font-size: 0.8em;
    cursor: pointer;
}

.controls button.active {
    background: var(--purple);
    border-color: var(--purple);
    color: white;
}

.controls button:hover {
    background: var(--surface2);
}

.controls button.active:hover {
    background: rgb(124, 77, 231);
}

.legend {
    display: flex;
    gap: 16px;
    margin-bottom: 16px;
    font-size: 0.8em;
}

.legend-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

.legend-swatch {
    width: 14px;
    height: 14px;
    border-radius: 3px;
}

/* Main table */
.table-wrapper {
    overflow-x: auto;
    margin-bottom: 32px;
}

table {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.82em;
}

th, td {
    padding: 6px 10px;
    border: 1px solid var(--border);
    text-align: center;
    white-space: nowrap;
}

th {
    background: var(--surface);
    color: var(--text-bright);
    font-weight: 600;
    position: sticky;
    top: 0;
    z-index: 10;
}

th.sortable {
    cursor: pointer;
    user-select: none;
}

th.sortable:hover {
    background: var(--surface2);
}

th.sortable::after {
    content: ' ⇅';
    color: var(--text-dim);
    font-size: 0.8em;
}

td.model-name {
    text-align: left;
    font-weight: 600;
    color: var(--text-bright);
    background: var(--surface);
    position: sticky;
    left: 0;
    z-index: 5;
}

td.family-header {
    text-align: left;
    font-weight: 700;
    color: var(--text-dim);
    background: var(--surface2);
    font-size: 0.9em;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}

.n-badge {
    display: inline-block;
    padding: 1px 5px;
    border-radius: 3px;
    font-size: 0.75em;
    font-weight: 600;
    margin-left: 4px;
}

.n-badge.n1 {
    background: rgba(234, 179, 8, 0.2);
    color: var(--yellow);
    border: 1px solid rgba(234, 179, 8, 0.4);
}

.n-badge.n3 {
    background: rgba(34, 197, 94, 0.2);
    color: var(--green);
    border: 1px solid rgba(34, 197, 94, 0.4);
}

.ci {
    color: var(--text-dim);
    font-size: 0.85em;
}

.pct-cell {
    font-variant-numeric: tabular-nums;
}

.delta-pos { color: var(--green); }
.delta-neg { color: var(--red); }
.delta-zero { color: var(--text-dim); }

/* Tooltip for per-run breakdown */
.has-tooltip {
    position: relative;
    cursor: help;
}

.has-tooltip .tooltip {
    display: none;
    position: absolute;
    bottom: calc(100% + 4px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 0.85em;
    white-space: nowrap;
    z-index: 100;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

.has-tooltip:hover .tooltip {
    display: block;
}

.tooltip-title {
    font-weight: 600;
    color: var(--text-bright);
    margin-bottom: 4px;
}

/* Section headers */
.section-title {
    color: var(--text-bright);
    font-size: 1.1em;
    margin: 24px 0 8px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 4px;
}

/* Steerability delta table */
.delta-table td {
    font-weight: 600;
}

/* Last-choice section */
.last-choice-table td.pct-cell {
    opacity: 0.85;
}

/* No-data cell */
.no-data {
    color: var(--text-dim);
    font-style: italic;
}

/* View toggle */
.view-section {
    display: none;
}

.view-section.active {
    display: block;
}

/* Responsive */
@media (max-width: 900px) {
    body { padding: 8px; }
    th, td { padding: 4px 6px; font-size: 0.75em; }
}
</style>
</head>
<body>

<h1>Cosmic Host — Model Comparison Dashboard</h1>
<p class="subtitle">Scenario evaluation results across all models and constitutional conditions.
Hover cells for per-run breakdowns (n&gt;1). Generated from logs/mp_scen_evals/.</p>

<div class="legend">
    <div class="legend-item">
        <div class="legend-swatch" style="background: rgba(59,130,246,0.35)"></div>
        <span>Human-localist</span>
    </div>
    <div class="legend-item">
        <div class="legend-swatch" style="background: rgba(249,115,22,0.35)"></div>
        <span>Suffering-focused</span>
    </div>
    <div class="legend-item">
        <div class="legend-swatch" style="background: rgba(139,92,246,0.35)"></div>
        <span>Cosmic-host-leaning</span>
    </div>
    <div class="legend-item">
        <span class="n-badge n3">n=3</span> 90 trials
    </div>
    <div class="legend-item">
        <span class="n-badge n1">n=1</span> 30 trials
    </div>
</div>

<div class="controls">
    <label>View:</label>
    <button class="view-btn active" onclick="switchView('first')">First Choice</button>
    <button class="view-btn" onclick="switchView('last')">Last Choice</button>
    <button class="view-btn" onclick="switchView('delta')">Steerability Δ</button>
    <button class="view-btn" onclick="switchView('charts')">Charts</button>
    <label style="margin-left:16px">Family:</label>
    <select id="familyFilter" onchange="filterFamily()">
        <option value="all">All</option>
        <option value="Claude">Claude</option>
        <option value="Gemini">Gemini</option>
        <option value="GPT">GPT</option>
        <option value="Open-weight">Open-weight</option>
    </select>
</div>
""")

    # === FIRST CHOICE TABLE ===
    html_parts.append('<div id="view-first" class="view-section active">')
    html_parts.append('<h2 class="section-title">First Choice Distribution (%)</h2>')
    html_parts.append('<div class="table-wrapper"><table id="table-first">')

    # Header row
    html_parts.append("<thead><tr>")
    html_parts.append('<th style="text-align:left; position:sticky; left:0; z-index:15;">Model</th>')
    for cond in sorted_conditions:
        label = CONDITION_LABELS.get(cond, cond)
        html_parts.append(f'<th colspan="3">{label}</th>')
    html_parts.append("</tr>")
    # Sub-header
    html_parts.append("<tr>")
    html_parts.append('<th style="text-align:left; position:sticky; left:0; z-index:15;"></th>')
    for cond in sorted_conditions:
        html_parts.append('<th style="color:rgb(59,130,246)">H</th>')
        html_parts.append('<th style="color:rgb(249,115,22)">S</th>')
        html_parts.append('<th style="color:rgb(139,92,246)">C</th>')
    html_parts.append("</tr></thead>")

    html_parts.append("<tbody>")
    prev_family = None
    for model in sorted_models:
        fam = model_family(model)
        if fam != prev_family:
            n_cols = 1 + len(sorted_conditions) * 3
            html_parts.append(
                f'<tr class="family-row" data-family="{fam}">'
                f'<td class="family-header" colspan="{n_cols}">{fam}</td></tr>'
            )
            prev_family = fam

        html_parts.append(f'<tr class="model-row" data-family="{fam}">')
        display = model_display(model)

        # Check n for this model across conditions
        n_vals = set()
        for cond in sorted_conditions:
            key = (model, cond)
            if key in all_stats:
                n_vals.add(all_stats[key]["n_runs"])

        html_parts.append(f'<td class="model-name">{display}</td>')

        for cond in sorted_conditions:
            key = (model, cond)
            if key in all_stats:
                st = all_stats[key]
                n = st["n_runs"]
                badge_cls = "n3" if n >= 3 else "n1"

                for ct in CHOICE_TYPES:
                    mean = st["first_choice"][ct]["mean"]
                    bg = colour_for_pct(mean, ct)
                    cell_content = format_cell(st["first_choice"][ct], n)

                    # Build tooltip for per-run breakdown
                    tooltip = ""
                    if n > 1 and "per_run" in st:
                        tooltip_lines = [f'<div class="tooltip"><div class="tooltip-title">'
                                         f'{display} — {CONDITION_LABELS.get(cond, cond)} — '
                                         f'{CHOICE_LABELS[ct]}</div>']
                        for run_num in sorted(st["per_run"].keys()):
                            val = st["per_run"][run_num].get(ct, 0)
                            tooltip_lines.append(f'Run {run_num}: {val:.0f}%<br>')
                        tooltip_lines.append(
                            f'<span class="n-badge {badge_cls}">n={n}</span> '
                            f'({st["n_total"]} trials)')
                        tooltip_lines.append('</div>')
                        tooltip = "".join(tooltip_lines)
                        cls = "pct-cell has-tooltip"
                    else:
                        cls = "pct-cell"

                    # Add n-badge on the first column of each condition group
                    badge = ""
                    if ct == CHOICE_TYPES[0]:
                        badge = f' <span class="n-badge {badge_cls}">n={n}</span>'

                    html_parts.append(
                        f'<td class="{cls}" style="background:{bg}">'
                        f'{cell_content}{badge}{tooltip}</td>'
                    )
            else:
                for ct in CHOICE_TYPES:
                    html_parts.append('<td class="no-data">—</td>')

        html_parts.append("</tr>")

    html_parts.append("</tbody></table></div>")
    html_parts.append("</div>")  # end view-first

    # === LAST CHOICE TABLE ===
    html_parts.append('<div id="view-last" class="view-section">')
    html_parts.append('<h2 class="section-title">Last Choice Distribution (%) — what models reject</h2>')
    html_parts.append('<div class="table-wrapper"><table id="table-last" class="last-choice-table">')

    html_parts.append("<thead><tr>")
    html_parts.append('<th style="text-align:left; position:sticky; left:0; z-index:15;">Model</th>')
    for cond in sorted_conditions:
        label = CONDITION_LABELS.get(cond, cond)
        html_parts.append(f'<th colspan="3">{label}</th>')
    html_parts.append("</tr><tr>")
    html_parts.append('<th style="text-align:left; position:sticky; left:0; z-index:15;"></th>')
    for cond in sorted_conditions:
        html_parts.append('<th style="color:rgb(59,130,246)">H</th>')
        html_parts.append('<th style="color:rgb(249,115,22)">S</th>')
        html_parts.append('<th style="color:rgb(139,92,246)">C</th>')
    html_parts.append("</tr></thead><tbody>")

    prev_family = None
    for model in sorted_models:
        fam = model_family(model)
        if fam != prev_family:
            n_cols = 1 + len(sorted_conditions) * 3
            html_parts.append(
                f'<tr class="family-row" data-family="{fam}">'
                f'<td class="family-header" colspan="{n_cols}">{fam}</td></tr>'
            )
            prev_family = fam

        html_parts.append(f'<tr class="model-row" data-family="{fam}">')
        display = model_display(model)
        html_parts.append(f'<td class="model-name">{display}</td>')

        for cond in sorted_conditions:
            key = (model, cond)
            if key in all_stats:
                st = all_stats[key]
                n = st["n_runs"]
                for ct in CHOICE_TYPES:
                    mean = st["last_choice"][ct]["mean"]
                    bg = colour_for_pct(mean, ct)
                    cell_content = format_cell(st["last_choice"][ct], n)
                    html_parts.append(
                        f'<td class="pct-cell" style="background:{bg}">{cell_content}</td>'
                    )
            else:
                for ct in CHOICE_TYPES:
                    html_parts.append('<td class="no-data">—</td>')

        html_parts.append("</tr>")

    html_parts.append("</tbody></table></div></div>")

    # === STEERABILITY DELTA TABLE ===
    html_parts.append('<div id="view-delta" class="view-section">')
    html_parts.append('<h2 class="section-title">Steerability Δ (Baseline → ECL 90%)</h2>')
    html_parts.append('<p class="subtitle" style="margin-bottom:12px">'
                      'Change in first-choice % from baseline to ECL 90% constitution. '
                      'Positive cosmic Δ = constitution shifts model toward cosmic engagement.</p>')
    html_parts.append('<div class="table-wrapper"><table id="table-delta" class="delta-table">')
    html_parts.append("<thead><tr>")
    html_parts.append('<th style="text-align:left">Model</th>')
    html_parts.append('<th>n</th>')
    html_parts.append('<th style="color:rgb(59,130,246)">ΔH</th>')
    html_parts.append('<th style="color:rgb(249,115,22)">ΔS</th>')
    html_parts.append('<th style="color:rgb(139,92,246)">ΔC</th>')
    html_parts.append('<th>Baseline (H/S/C)</th>')
    html_parts.append('<th>ECL 90% (H/S/C)</th>')
    html_parts.append('<th>Steerability</th>')
    html_parts.append("</tr></thead><tbody>")

    # Sort by cosmic delta descending
    models_with_delta = [(m, deltas[m]) for m in sorted_models if m in deltas]
    models_with_delta.sort(key=lambda x: x[1]["cosmic_host_leaning"], reverse=True)

    for model, delta in models_with_delta:
        display = model_display(model)
        fam = model_family(model)

        # Get n (use baseline n)
        baseline_st = all_stats.get((model, "noconstitution"), {})
        ecl90_st = all_stats.get((model, "ecl90"), {})
        n = baseline_st.get("n_runs", 1)
        badge_cls = "n3" if n >= 3 else "n1"

        html_parts.append(f'<tr class="model-row" data-family="{fam}">')
        html_parts.append(f'<td class="model-name">{display}</td>')
        html_parts.append(f'<td><span class="n-badge {badge_cls}">n={n}</span></td>')

        for ct in CHOICE_TYPES:
            d = delta[ct]
            if abs(d) < 1.5:
                cls = "delta-zero"
                sign = ""
            elif d > 0:
                cls = "delta-pos"
                sign = "+"
            else:
                cls = "delta-neg"
                sign = ""
            html_parts.append(f'<td class="{cls}">{sign}{d:.0f}pp</td>')

        # Baseline summary
        b = baseline_st.get("first_choice", {})
        e = ecl90_st.get("first_choice", {})
        b_str = "/".join(f'{b.get(ct, {}).get("mean", 0):.0f}' for ct in CHOICE_TYPES)
        e_str = "/".join(f'{e.get(ct, {}).get("mean", 0):.0f}' for ct in CHOICE_TYPES)
        html_parts.append(f'<td>{b_str}</td>')
        html_parts.append(f'<td>{e_str}</td>')

        # Steerability label
        cosmic_d = delta["cosmic_host_leaning"]
        if cosmic_d >= 25:
            steer = '<span style="color:var(--green)">Very High</span>'
        elif cosmic_d >= 15:
            steer = '<span style="color:var(--green)">High</span>'
        elif cosmic_d >= 8:
            steer = '<span style="color:var(--yellow)">Medium</span>'
        elif cosmic_d >= 3:
            steer = '<span style="color:var(--orange)">Low</span>'
        else:
            steer = '<span style="color:var(--red)">None/Very Low</span>'
        html_parts.append(f'<td>{steer}</td>')
        html_parts.append("</tr>")

    html_parts.append("</tbody></table></div></div>")

    # === CHARTS VIEW ===
    html_parts.append('<div id="view-charts" class="view-section">')
    html_parts.append('<h2 class="section-title">Publication Charts</h2>')
    if chart_data:
        html_parts.append('<p class="subtitle" style="margin-bottom:16px">'
                          'SVG and PDF versions saved to charts/ directory.</p>')

        html_parts.append('<div style="margin-bottom:32px">')
        html_parts.append('<h3 style="color:#e2e8f0; margin-bottom:8px">'
                          'Figure 1: Baseline vs ECL 90% Constitution</h3>')
        html_parts.append(f'<img src="data:image/png;base64,{chart_data.get("fig1", "")}" '
                          f'style="max-width:100%; border-radius:8px; '
                          f'border:1px solid #475569;" />')
        html_parts.append('</div>')

        html_parts.append('<div style="margin-bottom:32px">')
        html_parts.append('<h3 style="color:#e2e8f0; margin-bottom:8px">'
                          'Figure 2: Constitutional Steerability (Cosmic Shift)</h3>')
        html_parts.append(f'<img src="data:image/png;base64,{chart_data.get("fig2", "")}" '
                          f'style="max-width:100%; border-radius:8px; '
                          f'border:1px solid #475569;" />')
        html_parts.append('</div>')

        html_parts.append('<div style="margin-bottom:32px">')
        html_parts.append('<h3 style="color:#e2e8f0; margin-bottom:8px">'
                          'Figure 3: Cosmic First-Choice Heatmap (All Conditions)</h3>')
        html_parts.append(f'<img src="data:image/png;base64,{chart_data.get("fig3", "")}" '
                          f'style="max-width:100%; border-radius:8px; '
                          f'border:1px solid #475569;" />')
        html_parts.append('</div>')
    else:
        html_parts.append('<p class="subtitle">Charts not generated. '
                          'Run with --charts flag and matplotlib installed.</p>')
    html_parts.append('</div>')

    # === JavaScript ===
    html_parts.append("""
<script>
function switchView(view) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    document.getElementById('view-' + view).classList.add('active');
    document.querySelectorAll('.view-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function filterFamily() {
    const family = document.getElementById('familyFilter').value;
    document.querySelectorAll('.model-row, .family-row').forEach(row => {
        if (family === 'all' || row.dataset.family === family) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}
</script>

</body>
</html>""")

    return "".join(html_parts)


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate model comparison dashboard")
    parser.add_argument("--output", "-o", default=DEFAULT_OUTPUT, help="Output HTML file")
    parser.add_argument("--no-charts", action="store_true",
                        help="Skip chart generation (no matplotlib needed)")
    parser.add_argument("--charts-dir", default="charts",
                        help="Directory for SVG/PDF chart output (default: charts/)")
    args = parser.parse_args()

    print("Discovering result files...")
    files = discover_files()
    print(f"Found {len(files)} JSONL files")

    all_stats = {}
    for filepath in files:
        model, condition = parse_model_condition(filepath)
        header, data = load_file(filepath)

        if not data:
            print(f"  SKIP (no data): {filepath.name}")
            continue

        stats = compute_stats(data)
        all_stats[(model, condition)] = stats

        n = stats["n_runs"]
        fc = stats["first_choice"]
        h = fc["human_localist"]["mean"]
        s = fc["suffering_focused"]["mean"]
        c = fc["cosmic_host_leaning"]["mean"]
        print(f"  n={n} {model:>40s} / {condition:<16s}  H={h:4.0f}% S={s:4.0f}% C={c:4.0f}%")

    print(f"\nTotal model×condition combinations: {len(all_stats)}")

    # Generate charts
    chart_data = None
    if not args.no_charts:
        try:
            chart_data = generate_charts(all_stats, Path(args.charts_dir))
        except ImportError:
            print("\nmatplotlib not found — skipping charts. Use --no-charts to suppress.")
        except Exception as e:
            print(f"\nChart generation failed: {e}")
            import traceback
            traceback.print_exc()

    html = generate_html(all_stats, chart_data)
    output_path = Path(args.output)
    output_path.write_text(html)
    print(f"\nDashboard written to {output_path}")
    print(f"Open with: open {output_path}")


if __name__ == "__main__":
    main()
