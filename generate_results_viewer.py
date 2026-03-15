#!/usr/bin/env python3
"""
Generate an interactive HTML viewer for constitutional evaluation results.

Usage:
    python generate_results_viewer.py [options]

Options:
    --files file1.jsonl file2.jsonl ...   Process specific files
    --all                                  Process all files in results/
    --output filename.html                 Output filename (default: results_viewer.html)

If no arguments provided, uses DEFAULT_FILES list below.
"""

import json
import sys
import random
import base64
import io
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# =============================================================================
# CONFIGURATION: Edit these default files to display
# =============================================================================
def discover_all_log_files():
    """Auto-discover all JSONL files from logs/mp_scen_evals/, excluding backups."""
    logs_dir = Path("logs/mp_scen_evals")
    if not logs_dir.exists():
        return []
    files = sorted(logs_dir.rglob("*.jsonl"))
    return [str(f) for f in files if "_backup" not in f.name]

DEFAULT_FILES = discover_all_log_files()

DEFAULT_OUTPUT = "results_viewer.html"


def load_jsonl(filepath: Path) -> tuple[Dict, List[Dict]]:
    """Load JSONL file and return header + data rows."""
    header = None
    data = []

    with open(filepath, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            if obj.get('_type') == 'header':
                header = obj
            else:
                data.append(obj)

    return header, data


def load_scenarios(scenario_file: Path = Path("static/scenarios.json")) -> Dict[int, Dict]:
    """Load scenario metadata from JSON file."""
    if not scenario_file.exists():
        print(f"Warning: Scenario file not found: {scenario_file}")
        return {}

    try:
        with open(scenario_file, 'r') as f:
            data = json.load(f)

        # Create lookup by ID
        scenarios = {s['id']: s for s in data.get('scenarios', [])}
        print(f"Loaded {len(scenarios)} scenario definitions from {scenario_file}")
        return scenarios
    except Exception as e:
        print(f"Warning: Error loading scenarios: {e}")
        return {}


def get_scenario_title(scenario_id: int, scenario_tag: str, scenarios: Dict[int, Dict]) -> str:
    """Get scenario title from loaded scenario data."""
    if scenario_id in scenarios:
        return scenarios[scenario_id].get('title', f"Scenario {scenario_id}")
    return f"Scenario {scenario_id}"  # fallback


def get_constitution_info(condition: str) -> dict:
    """Get detailed constitution information from condition code."""
    # Map condition codes to metadata
    info_map = {
        'noconstitution': {
            'source': 'None (Control)',
            'credence': 'N/A',
            'type': 'baseline'
        },
        'eclpilled_10ch': {
            'source': 'Human-curated ECL',
            'credence': '10%',
            'type': 'eclpilled'
        },
        'eclpilled_90ch': {
            'source': 'Human-curated ECL',
            'credence': '90%',
            'type': 'eclpilled'
        },
        'gemini_10ch': {
            'source': 'Gemini-generated',
            'credence': '10%',
            'type': 'model_generated'
        },
        'gemini_90ch': {
            'source': 'Gemini-generated',
            'credence': '90%',
            'type': 'model_generated'
        },
        'baseline': {
            'source': 'Human baseline',
            'credence': '0%',
            'type': 'baseline'
        },
    }

    return info_map.get(condition, {
        'source': condition,
        'credence': 'Unknown',
        'type': 'unknown'
    })


def abbreviate_choice(choice_type: str) -> tuple[str, str]:
    """Convert choice type to abbreviation and badge class.
    Returns (abbrev, badge_class)."""
    choice_lower = choice_type.lower()
    if 'cosmic' in choice_lower:
        return 'C', 'badge-cosmic'
    elif 'human' in choice_lower or 'localist' in choice_lower:
        return 'H', 'badge-human'
    elif 'suffering' in choice_lower:
        return 'S', 'badge-suffering'
    elif 'proceduralist' in choice_lower:
        return 'P', 'badge-proceduralist'
    else:
        return choice_type[:3].upper(), ''


# =============================================================================
# MODEL SUMMARY + CHART SUPPORT
# =============================================================================

CHOICE_TYPES = ["human_localist", "suffering_focused", "cosmic_host_leaning"]

SUMMARY_CONDITION_ORDER = ["noconstitution", "ecl10", "ecl90", "gemini10", "gemini90"]
SUMMARY_CONDITION_LABELS = {
    "noconstitution": "Baseline", "ecl10": "ECL 10%", "ecl90": "ECL 90%",
    "gemini10": "Gemini 10%", "gemini90": "Gemini 90%",
    "baseline": "Baseline", "eclpilled_10ch": "ECL 10%", "eclpilled_90ch": "ECL 90%",
    "gemini_10ch": "Gemini 10%", "gemini_90ch": "Gemini 90%",
}

# Normalise old-style condition names to new-style
def normalise_condition(cond: str) -> str:
    mapping = {"baseline": "noconstitution", "eclpilled_10ch": "ecl10",
               "eclpilled_90ch": "ecl90", "gemini_10ch": "gemini10", "gemini_90ch": "gemini90"}
    return mapping.get(cond, cond)


CHART_MODEL_ORDER = [
    "gemini-3-flash-preview_thinking", "gemini-3-flash-preview",
    "gemini-3-pro-preview", "claude-sonnet-4-5", "kimi-k2",
    "claude-opus-4-5", "claude-opus-4-6", "qwen3_235b",
    "gpt-5.1", "qwen3_235b_thinking", "gpt-5.4",
]


def model_display_name(m: str) -> str:
    mapping = {
        "qwen3_235b": "Qwen 3 235B", "qwen3_235b_thinking": "Qwen 3 235B (thinking)",
        "kimi-k2": "Kimi K2", "gemini-3-flash-preview": "Gemini 3 Flash",
        "gemini-3-flash-preview_thinking": "Gemini 3 Flash (thinking)",
        "gemini-3-pro-preview": "Gemini 3 Pro", "claude-opus-4-5": "Claude Opus 4.5",
        "claude-opus-4-6": "Claude Opus 4.6", "claude-sonnet-4-5": "Claude Sonnet 4.5",
        "gpt-5.1": "GPT 5.1", "gpt-5.4": "GPT 5.4",
    }
    return mapping.get(m, m)


def model_family_name(m: str) -> str:
    if "claude" in m or "opus" in m or "sonnet" in m: return "Claude"
    if "gemini" in m: return "Gemini"
    if "gpt" in m: return "GPT"
    return "Open-weight"


def bootstrap_ci(choices, choice_type, n_boot=10000, ci=0.95):
    n = len(choices)
    if n == 0: return 0.0, 0.0, 0.0
    observed = sum(1 for c in choices if c == choice_type) / n * 100
    if n == 1: return observed, observed, observed
    random.seed(42)
    boot = sorted(sum(1 for c in random.choices(choices, k=n) if c == choice_type) / n * 100
                  for _ in range(n_boot))
    alpha = (1 - ci) / 2
    return observed, boot[int(alpha * n_boot)], boot[int((1 - alpha) * n_boot)]


def parse_model_condition_from_filename(filepath: Path) -> Tuple[str, str]:
    """Extract model name and condition from filename."""
    name = filepath.stem
    prefix = "constitutional_evaluation_"
    if name.startswith(prefix):
        name = name[len(prefix):]
    for cond in sorted(SUMMARY_CONDITION_ORDER, key=len, reverse=True):
        if name.endswith(f"_{cond}"):
            return name[:-(len(cond) + 1)], cond
    parts = name.rsplit("_", 1)
    return (parts[0], parts[1]) if len(parts) == 2 else (name, "unknown")


def compute_model_stats(all_data):
    """Build model×condition stats from loaded trial data."""
    # Group trials by (model_key, normalised_condition)
    grouped = defaultdict(list)
    for filepath, header, trials in all_data:
        model_key, file_cond = parse_model_condition_from_filename(filepath)
        for trial in trials:
            cond = normalise_condition(trial.get("condition", file_cond))
            grouped[(model_key, cond)].append(trial)

    stats = {}
    for (model, cond), trials in grouped.items():
        successful = [t for t in trials if t.get("parse_success", False)]
        run_numbers = set(t.get("run_number", 0) for t in trials)
        n_runs = len(run_numbers)
        first_choices = [t["first_choice_type"] for t in successful]
        last_choices = [t["last_choice_type"] for t in successful]

        st = {"n_total": len(trials), "n_runs": n_runs,
              "first_choice": {}, "last_choice": {}}
        for ct in CHOICE_TYPES:
            m, lo, hi = bootstrap_ci(first_choices, ct)
            st["first_choice"][ct] = {"mean": m, "ci_lo": lo, "ci_hi": hi}
            m2, lo2, hi2 = bootstrap_ci(last_choices, ct)
            st["last_choice"][ct] = {"mean": m2, "ci_lo": lo2, "ci_hi": hi2}

        if n_runs > 1:
            per_run = {}
            for rn in sorted(run_numbers):
                rd = [t for t in successful if t.get("run_number") == rn]
                fc = Counter(t["first_choice_type"] for t in rd)
                total = len(rd)
                per_run[rn] = {ct: fc.get(ct, 0) / total * 100 if total else 0 for ct in CHOICE_TYPES}
            st["per_run"] = per_run

        stats[(model, cond)] = st

    return stats


def generate_charts_b64(model_stats):
    """Generate charts, return dict of {name: base64_png}. Also saves SVG/PDF."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.ticker as mticker
        import numpy as np
    except ImportError:
        print("  matplotlib not available — skipping charts")
        return {}

    from pathlib import Path as P
    charts_dir = P("charts")
    charts_dir.mkdir(exist_ok=True)
    charts = {}

    C_HUMAN, C_SUFFER, C_COSMIC = "#3b82f6", "#f97316", "#8b5cf6"
    C_BG, C_SURFACE, C_TEXT, C_GRID = "#0d1117", "#161b22", "#c9d1d9", "#30363d"
    FAMILY_COLOURS = {"Claude": "#60a5fa", "Gemini": "#f97316", "GPT": "#22c55e", "Open-weight": "#a78bfa"}

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
        "font.size": 10, "axes.facecolor": C_SURFACE, "figure.facecolor": C_BG,
        "text.color": C_TEXT, "axes.labelcolor": C_TEXT, "xtick.color": C_TEXT,
        "ytick.color": C_TEXT, "axes.edgecolor": C_GRID, "grid.color": C_GRID, "grid.alpha": 0.5,
    })

    models_for_chart = [m for m in CHART_MODEL_ORDER
                        if (m, "noconstitution") in model_stats and (m, "ecl90") in model_stats]
    if not models_for_chart:
        # Try normalised condition names
        models_for_chart = [m for m in CHART_MODEL_ORDER
                            if (m, "noconstitution") in model_stats or (m, "ecl90") in model_stats]
    if not models_for_chart:
        print("  No matching models for charts")
        return {}

    n_models = len(models_for_chart)

    # ── Fig 1: Paired stacked bars ──
    fig, ax = plt.subplots(figsize=(14, 5.5))
    bar_width, gap = 0.35, 0.08
    x = np.arange(n_models)

    for i, model in enumerate(models_for_chart):
        for side, cond_key, x_off in [("B", "noconstitution", -bar_width/2 - gap/2),
                                       ("E", "ecl90", bar_width/2 + gap/2)]:
            key = (model, cond_key)
            if key not in model_stats:
                continue
            st = model_stats[key]
            fc = st["first_choice"]
            h, s, c = fc["human_localist"]["mean"], fc["suffering_focused"]["mean"], fc["cosmic_host_leaning"]["mean"]
            n = st["n_runs"]

            ax.bar(x[i] + x_off, h, bar_width, color=C_HUMAN, edgecolor=C_SURFACE, linewidth=0.5)
            ax.bar(x[i] + x_off, s, bar_width, bottom=h, color=C_SUFFER, edgecolor=C_SURFACE, linewidth=0.5)
            ax.bar(x[i] + x_off, c, bar_width, bottom=h+s, color=C_COSMIC, edgecolor=C_SURFACE, linewidth=0.5)

            if n > 1:
                ci_lo = fc["cosmic_host_leaning"]["ci_lo"]
                ci_hi = fc["cosmic_host_leaning"]["ci_hi"]
                ax.errorbar(x[i] + x_off, h+s+c, yerr=[[c - ci_lo], [ci_hi - c]],
                           fmt='none', ecolor=C_TEXT, elinewidth=1, capsize=3, capthick=1, alpha=0.6)

        ax.text(x[i] - bar_width/2 - gap/2, -4, "B", ha='center', va='top', fontsize=7, color=C_TEXT, alpha=0.5)
        ax.text(x[i] + bar_width/2 + gap/2, -4, "E", ha='center', va='top', fontsize=7, color=C_TEXT, alpha=0.5)

        # n badge
        n_b = model_stats.get((model, "noconstitution"), {}).get("n_runs", 1)
        n_e = model_stats.get((model, "ecl90"), {}).get("n_runs", 1)
        badge = f"n={n_b}" if n_b == n_e else f"n={n_b}/{n_e}"
        ax.text(x[i], 102, badge, ha='center', va='bottom', fontsize=6.5, color='#8b949e', style='italic')

    ax.set_xticks(x)
    ax.set_xticklabels([model_display_name(m).replace('\n', ' ') for m in models_for_chart], fontsize=8.5)
    ax.set_ylabel("First-choice distribution (%)")
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_locator(mticker.MultipleLocator(25))
    ax.set_title("Baseline (B) vs ECL 90% Constitution (E)", fontsize=12, fontweight='bold', pad=12)
    ax.grid(axis='y', alpha=0.3)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=C_HUMAN, label='Human-localist'),
                       Patch(facecolor=C_SUFFER, label='Suffering-focused'),
                       Patch(facecolor=C_COSMIC, label='Cosmic-host-leaning')],
              loc='upper right', fontsize=8.5, facecolor=C_SURFACE, edgecolor=C_GRID, labelcolor=C_TEXT)
    plt.tight_layout()
    fig.savefig(charts_dir / "fig1_baseline_vs_ecl90.svg", bbox_inches='tight', dpi=150)
    fig.savefig(charts_dir / "fig1_baseline_vs_ecl90.pdf", bbox_inches='tight', dpi=150)
    buf = io.BytesIO(); fig.savefig(buf, format='png', bbox_inches='tight', dpi=180); buf.seek(0)
    charts["fig1"] = base64.b64encode(buf.read()).decode(); plt.close(fig)

    # ── Fig 2: Steerability arrows ──
    fig2, ax2 = plt.subplots(figsize=(10, 5.5))
    models_delta = []
    for m in models_for_chart:
        bk, ek = (m, "noconstitution"), (m, "ecl90")
        if bk in model_stats and ek in model_stats:
            b = model_stats[bk]["first_choice"]["cosmic_host_leaning"]["mean"]
            e = model_stats[ek]["first_choice"]["cosmic_host_leaning"]["mean"]
            models_delta.append((m, b, e, e - b))
    models_delta.sort(key=lambda x: x[3], reverse=True)

    for i, (model, bc, ec, delta) in enumerate(models_delta):
        col = FAMILY_COLOURS.get(model_family_name(model), "#94a3b8")
        n_runs = model_stats[(model, "noconstitution")]["n_runs"]
        ax2.annotate("", xy=(ec, i), xytext=(bc, i),
                     arrowprops=dict(arrowstyle="-|>", color=col, lw=2.5, mutation_scale=12))
        ax2.scatter(bc, i, s=60, color=col, zorder=5, edgecolors=C_SURFACE, linewidth=1)
        ax2.scatter(ec, i, s=80, color=col, zorder=5, edgecolors='white', linewidth=1.2, marker='D')
        sign = "+" if delta >= 0 else ""
        ax2.text(max(bc, ec) + 2, i, f"{sign}{delta:.0f}pp", va='center', fontsize=8.5, fontweight='bold', color=col)
        badge_col = "#22c55e" if n_runs >= 3 else "#eab308"
        ax2.text(-5, i, f"n={n_runs}", va='center', ha='right', fontsize=7, color=badge_col, style='italic')
        if n_runs > 1:
            for val, ck in [(bc, "noconstitution"), (ec, "ecl90")]:
                ci_lo = model_stats[(model, ck)]["first_choice"]["cosmic_host_leaning"]["ci_lo"]
                ci_hi = model_stats[(model, ck)]["first_choice"]["cosmic_host_leaning"]["ci_hi"]
                ax2.plot([ci_lo, ci_hi], [i, i], color=col, alpha=0.3, linewidth=4, solid_capstyle='round', zorder=3)

    ax2.set_yticks(range(len(models_delta)))
    ax2.set_yticklabels([model_display_name(m).replace('\n', ' ') for m, _, _, _ in models_delta], fontsize=9)
    ax2.set_xlabel("Cosmic-host-leaning first-choice (%)", fontsize=10)
    ax2.set_xlim(-8, 60)
    ax2.xaxis.set_major_locator(mticker.MultipleLocator(10))
    ax2.set_title("Constitutional Steerability: Cosmic First-Choice Shift (Baseline to ECL 90%)",
                  fontsize=11, fontweight='bold', pad=12)
    ax2.grid(axis='x', alpha=0.3); ax2.invert_yaxis()
    from matplotlib.lines import Line2D
    legend2 = [Line2D([0],[0], marker='o', color='w', markerfacecolor='#94a3b8', markersize=7, label='Baseline', linewidth=0),
               Line2D([0],[0], marker='D', color='w', markerfacecolor='#94a3b8', markersize=7, label='ECL 90%', linewidth=0, markeredgecolor='white')]
    for fam, col in FAMILY_COLOURS.items():
        legend2.append(Line2D([0],[0], color=col, linewidth=2.5, label=fam))
    ax2.legend(handles=legend2, loc='lower right', fontsize=8, facecolor=C_SURFACE, edgecolor=C_GRID, labelcolor=C_TEXT)
    plt.tight_layout()
    fig2.savefig(charts_dir / "fig2_steerability_arrows.svg", bbox_inches='tight', dpi=150)
    fig2.savefig(charts_dir / "fig2_steerability_arrows.pdf", bbox_inches='tight', dpi=150)
    buf2 = io.BytesIO(); fig2.savefig(buf2, format='png', bbox_inches='tight', dpi=180); buf2.seek(0)
    charts["fig2"] = base64.b64encode(buf2.read()).decode(); plt.close(fig2)

    # ── Fig 3: Cosmic heatmap ──
    all_models = [m for m in CHART_MODEL_ORDER if any((m, c) in model_stats for c in SUMMARY_CONDITION_ORDER)]
    conds_present = [c for c in SUMMARY_CONDITION_ORDER if any((m, c) in model_stats for m in all_models)]
    if all_models and conds_present:
        fig3, ax3 = plt.subplots(figsize=(12, 5.5))
        matrix = np.full((len(all_models), len(conds_present)), np.nan)
        annot = [['' for _ in conds_present] for _ in all_models]
        for i, model in enumerate(all_models):
            for j, cond in enumerate(conds_present):
                if (model, cond) in model_stats:
                    val = model_stats[(model, cond)]["first_choice"]["cosmic_host_leaning"]["mean"]
                    n = model_stats[(model, cond)]["n_runs"]
                    matrix[i, j] = val
                    annot[i][j] = f"{val:.0f}{'*' if n >= 3 else ''}"
        im = ax3.imshow(matrix, cmap='YlOrRd', aspect='auto', vmin=0, vmax=50, interpolation='nearest')
        for i in range(len(all_models)):
            for j in range(len(conds_present)):
                if annot[i][j]:
                    tc = 'white' if matrix[i, j] > 25 else C_TEXT
                    ax3.text(j, i, annot[i][j], ha='center', va='center', fontsize=9, fontweight='bold', color=tc)
        ax3.set_xticks(range(len(conds_present)))
        ax3.set_xticklabels([SUMMARY_CONDITION_LABELS.get(c, c) for c in conds_present], fontsize=9)
        ax3.set_yticks(range(len(all_models)))
        ax3.set_yticklabels([model_display_name(m).replace('\n', ' ') for m in all_models], fontsize=9)
        ax3.set_title("Cosmic-Host First-Choice % Across All Conditions (* = n>=3)",
                      fontsize=11, fontweight='bold', pad=12)
        cbar = plt.colorbar(im, ax=ax3, shrink=0.8, pad=0.02)
        cbar.set_label("Cosmic first-choice %", fontsize=9)
        cbar.ax.yaxis.set_tick_params(color=C_TEXT)
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=C_TEXT)
        plt.tight_layout()
        fig3.savefig(charts_dir / "fig3_cosmic_heatmap.svg", bbox_inches='tight', dpi=150)
        fig3.savefig(charts_dir / "fig3_cosmic_heatmap.pdf", bbox_inches='tight', dpi=150)
        buf3 = io.BytesIO(); fig3.savefig(buf3, format='png', bbox_inches='tight', dpi=180); buf3.seek(0)
        charts["fig3"] = base64.b64encode(buf3.read()).decode(); plt.close(fig3)

    print(f"  Charts saved to charts/ (SVG + PDF)")
    return charts


def generate_summary_html(model_stats, chart_data):
    """Generate the model summary + charts HTML fragment (inserted as tabs)."""
    html = ""

    # ── Summary table ──
    # Discover models and conditions
    models_seen = set()
    conds_seen = set()
    for (m, c) in model_stats:
        models_seen.add(m)
        conds_seen.add(c)

    family_order = ["Claude", "Gemini", "GPT", "Open-weight"]
    def msort(m):
        fam = model_family_name(m)
        fi = family_order.index(fam) if fam in family_order else 99
        return (fi, m)
    sorted_models = sorted(models_seen, key=msort)
    sorted_conds = [c for c in SUMMARY_CONDITION_ORDER if c in conds_seen]

    def fmt_cell(st_ct, n_runs):
        mean = st_ct["mean"]
        if n_runs > 1:
            margin = max(mean - st_ct["ci_lo"], st_ct["ci_hi"] - mean)
            return f'{mean:.0f}% <span style="color:#8b949e;font-size:0.85em">&plusmn;{margin:.0f}</span>'
        return f'{mean:.0f}%'

    def bg_colour(pct, ct):
        colours = {"human_localist": (59,130,246), "suffering_focused": (249,115,22), "cosmic_host_leaning": (139,92,246)}
        r, g, b = colours.get(ct, (128,128,128))
        alpha = 0.05 + (pct / 100) * 0.40
        return f"rgba({r},{g},{b},{alpha:.2f})"

    # Summary table
    html += '<h2 style="color:#f0f6fc;font-size:1.1em;margin:16px 0 8px;border-bottom:1px solid #30363d;padding-bottom:4px;">First Choice Distribution (%)</h2>'
    html += '<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%;font-size:0.82em">'
    html += '<thead><tr><th style="text-align:left;background:#21262d;color:#c9d1d9;padding:6px 10px;border:1px solid #30363d">Model</th>'
    for c in sorted_conds:
        html += f'<th colspan="3" style="background:#21262d;color:#c9d1d9;padding:6px 10px;border:1px solid #30363d">{SUMMARY_CONDITION_LABELS.get(c, c)}</th>'
    html += '</tr><tr><th style="background:#21262d;border:1px solid #30363d"></th>'
    for c in sorted_conds:
        html += '<th style="background:#21262d;color:#3b82f6;padding:4px;border:1px solid #30363d;font-size:0.9em">H</th>'
        html += '<th style="background:#21262d;color:#f97316;padding:4px;border:1px solid #30363d;font-size:0.9em">S</th>'
        html += '<th style="background:#21262d;color:#8b5cf6;padding:4px;border:1px solid #30363d;font-size:0.9em">C</th>'
    html += '</tr></thead><tbody>'

    prev_fam = None
    for model in sorted_models:
        fam = model_family_name(model)
        if fam != prev_fam:
            ncols = 1 + len(sorted_conds) * 3
            html += f'<tr><td colspan="{ncols}" style="text-align:left;font-weight:700;color:#8b949e;background:#21262d;font-size:0.9em;letter-spacing:0.05em;text-transform:uppercase;padding:6px 10px;border:1px solid #30363d">{fam}</td></tr>'
            prev_fam = fam
        html += '<tr>'
        html += f'<td style="text-align:left;font-weight:600;color:#f0f6fc;background:#161b22;padding:6px 10px;border:1px solid #30363d;white-space:nowrap">{model_display_name(model)}</td>'
        for c in sorted_conds:
            key = (model, c)
            if key in model_stats:
                st = model_stats[key]
                n = st["n_runs"]
                badge_col = "#22c55e" if n >= 3 else "#eab308"
                for ci, ct in enumerate(CHOICE_TYPES):
                    mean = st["first_choice"][ct]["mean"]
                    bg = bg_colour(mean, ct)
                    cell = fmt_cell(st["first_choice"][ct], n)
                    badge = f' <span style="display:inline-block;padding:1px 5px;border-radius:3px;font-size:0.7em;font-weight:600;color:{badge_col};border:1px solid {badge_col}40;background:{badge_col}20">n={n}</span>' if ci == 0 else ''
                    html += f'<td style="background:{bg};text-align:center;padding:4px 8px;border:1px solid #30363d;white-space:nowrap;font-variant-numeric:tabular-nums">{cell}{badge}</td>'
            else:
                for ct in CHOICE_TYPES:
                    html += '<td style="color:#8b949e;text-align:center;padding:4px 8px;border:1px solid #30363d;font-style:italic">&mdash;</td>'
        html += '</tr>'
    html += '</tbody></table></div>'

    # ── Steerability delta table ──
    deltas = {}
    for model in sorted_models:
        bk, ek = (model, "noconstitution"), (model, "ecl90")
        if bk in model_stats and ek in model_stats:
            b = model_stats[bk]["first_choice"]
            e = model_stats[ek]["first_choice"]
            deltas[model] = {ct: e[ct]["mean"] - b[ct]["mean"] for ct in CHOICE_TYPES}

    if deltas:
        html += '<h2 style="color:#f0f6fc;font-size:1.1em;margin:24px 0 8px;border-bottom:1px solid #30363d;padding-bottom:4px;">Steerability: Baseline to ECL 90%</h2>'
        html += '<div style="overflow-x:auto"><table style="border-collapse:collapse;width:auto;font-size:0.82em">'
        html += '<thead><tr>'
        for h_text in ['Model', 'n', 'dH', 'dS', 'dC', 'Baseline', 'ECL 90%', 'Steerability']:
            col = '#3b82f6' if h_text == 'dH' else '#f97316' if h_text == 'dS' else '#8b5cf6' if h_text == 'dC' else '#c9d1d9'
            html += f'<th style="background:#21262d;color:{col};padding:6px 10px;border:1px solid #30363d;text-align:{"left" if h_text == "Model" else "center"}">{h_text}</th>'
        html += '</tr></thead><tbody>'
        models_by_delta = sorted(deltas.items(), key=lambda x: x[1]["cosmic_host_leaning"], reverse=True)
        for model, delta in models_by_delta:
            html += '<tr>'
            html += f'<td style="text-align:left;font-weight:600;color:#f0f6fc;background:#161b22;padding:6px 10px;border:1px solid #30363d">{model_display_name(model)}</td>'
            n = model_stats.get((model, "noconstitution"), {}).get("n_runs", 1)
            badge_col = "#22c55e" if n >= 3 else "#eab308"
            html += f'<td style="text-align:center;padding:4px 8px;border:1px solid #30363d"><span style="color:{badge_col};font-size:0.85em;font-weight:600">n={n}</span></td>'
            for ct in CHOICE_TYPES:
                d = delta[ct]
                col = "#22c55e" if d > 1.5 else "#f85149" if d < -1.5 else "#8b949e"
                sign = "+" if d > 0 else ""
                html += f'<td style="text-align:center;padding:4px 8px;border:1px solid #30363d;color:{col};font-weight:600">{sign}{d:.0f}pp</td>'
            b = model_stats[(model, "noconstitution")]["first_choice"]
            e = model_stats[(model, "ecl90")]["first_choice"]
            bs = "/".join(f'{b[ct]["mean"]:.0f}' for ct in CHOICE_TYPES)
            es = "/".join(f'{e[ct]["mean"]:.0f}' for ct in CHOICE_TYPES)
            html += f'<td style="text-align:center;padding:4px 8px;border:1px solid #30363d">{bs}</td>'
            html += f'<td style="text-align:center;padding:4px 8px;border:1px solid #30363d">{es}</td>'
            cd = delta["cosmic_host_leaning"]
            if cd >= 25: steer = '<span style="color:#22c55e">Very High</span>'
            elif cd >= 15: steer = '<span style="color:#22c55e">High</span>'
            elif cd >= 8: steer = '<span style="color:#eab308">Medium</span>'
            elif cd >= 3: steer = '<span style="color:#f97316">Low</span>'
            else: steer = '<span style="color:#f85149">None/Very Low</span>'
            html += f'<td style="text-align:center;padding:4px 8px;border:1px solid #30363d;font-weight:600">{steer}</td>'
            html += '</tr>'
        html += '</tbody></table></div>'

    # ── Charts ──
    if chart_data:
        html += '<h2 style="color:#f0f6fc;font-size:1.1em;margin:24px 0 8px;border-bottom:1px solid #30363d;padding-bottom:4px;">Publication Charts</h2>'
        html += '<p style="color:#8b949e;font-size:0.85em;margin-bottom:12px">SVG and PDF versions saved to charts/ directory.</p>'
        for key, title in [("fig1", "Figure 1: Baseline vs ECL 90% Constitution"),
                           ("fig2", "Figure 2: Constitutional Steerability (Cosmic Shift)"),
                           ("fig3", "Figure 3: Cosmic First-Choice Heatmap (All Conditions)")]:
            if key in chart_data:
                html += f'<div style="margin-bottom:24px"><h3 style="color:#c9d1d9;margin-bottom:8px;font-size:0.95em">{title}</h3>'
                html += f'<img src="data:image/png;base64,{chart_data[key]}" style="max-width:100%;border-radius:8px;border:1px solid #30363d" /></div>'

    return html


def generate_html(all_data: List[tuple[Path, Dict, List[Dict]]], output_path: Path):
    """Generate the HTML viewer from all loaded data."""

    # Load scenario definitions
    scenario_definitions = load_scenarios()

    # Organize data: scenarios × (model, condition) → trial data
    table_data = defaultdict(lambda: defaultdict(list))
    all_scenarios = set()
    all_model_conditions = set()
    model_condition_to_file = {}  # Track source files (full path)
    model_condition_to_header = {}  # Track header metadata

    # Stats tracking per file
    file_stats = {}  # filepath -> {first_counts, last_counts, total, errors}

    for filepath, header, trials in all_data:
        # Initialize stats for this file
        first_counts = defaultdict(int)
        last_counts = defaultdict(int)
        error_count = 0

        for trial in trials:
            scenario_key = (trial['scenario_id'], trial['scenario_tag'])
            model_condition_key = (trial['model_name'], trial['condition'])

            all_scenarios.add(scenario_key)
            all_model_conditions.add(model_condition_key)
            table_data[scenario_key][model_condition_key].append(trial)

            # Track source file (full path) and header
            model_condition_to_file[model_condition_key] = str(filepath)
            model_condition_to_header[model_condition_key] = header

            # Track stats for this file
            first_counts[trial.get('first_choice_type', 'unknown')] += 1
            last_counts[trial.get('last_choice_type', 'unknown')] += 1

            # Count errors/failures (only actual parse failures)
            # Note: error_message can be informational (e.g., "Recovered from...") so don't count those
            if trial.get('parse_success', False) == False:
                error_count += 1

        # Store stats for this file
        file_stats[filepath] = {
            'first_counts': first_counts,
            'last_counts': last_counts,
            'total': len(trials),
            'errors': error_count
        }

    # Sort for consistent display
    scenarios = sorted(all_scenarios, key=lambda x: x[0])

    # Custom condition ordering: baseline → human-curated ECL → model-generated
    def condition_sort_key(mc):
        model, condition = mc
        # Define condition group priorities
        condition_order = {
            'baseline': (0, 0),            # Baseline first (no constitution)
            'noconstitution': (0, 0),      # Alias for baseline
            'eclpilled_10ch': (1, 10),     # Human-curated ECL, by credence
            'eclpilled_90ch': (1, 90),
            'gemini_10ch': (2, 10),        # Model-generated, by credence
            'gemini_90ch': (2, 90),
        }
        # Fallback for unknown conditions: parse credence if present, otherwise alphabetical
        if condition not in condition_order:
            # Try to extract credence number from condition name
            import re
            match = re.search(r'(\d+)', condition)
            credence = int(match.group(1)) if match else 50
            # Group unknown conditions at the end (priority 9)
            condition_order[condition] = (9, credence)

        group, credence = condition_order[condition]
        return (group, credence, model)

    model_conditions = sorted(all_model_conditions, key=condition_sort_key)

    # Compute model-level stats and charts
    print("  Computing model summary stats...")
    model_stats = compute_model_stats(all_data)
    print("  Generating charts...")
    chart_data = generate_charts_b64(model_stats)
    summary_fragment = generate_summary_html(model_stats, chart_data)

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Constitutional Evaluation Results Viewer</title>
    <style>
        * {{
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0d1117;
            color: #c9d1d9;
            font-size: 14px;
            line-height: 1.5;
        }}

        .container {{
            max-width: 100%;
            margin: 0 auto;
            background: #161b22;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.6);
            border: 1px solid #30363d;
        }}

        h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
            color: #f0f6fc;
        }}

        .subtitle {{
            color: #8b949e;
            margin-bottom: 20px;
            font-size: 14px;
        }}

        .table-wrapper {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }}

        th, td {{
            border: 1px solid #30363d;
            padding: 6px;
            text-align: center;
        }}

        th {{
            background: #21262d;
            color: #c9d1d9;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th.scenario-header {{
            background: #1c2128;
            min-width: 80px;
            text-align: left;
        }}

        th.model-header {{
            background: #21262d;
            min-width: 50px;
            max-width: 70px;
            cursor: pointer;
            font-size: 10px;
            padding: 8px 4px;
            height: 120px;
            vertical-align: bottom;
        }}

        th.model-header .header-text {{
            writing-mode: vertical-rl;
            text-orientation: mixed;
            transform: rotate(180deg);
            white-space: nowrap;
            display: inline-block;
        }}

        td.scenario-cell {{
            background: #1c2128;
            font-weight: 600;
            text-align: left;
            font-size: 16px;
            color: #c9d1d9;
        }}

        td.data-cell {{
            background: #0d1117;
            cursor: pointer;
            transition: background-color 0.2s;
        }}

        td.data-cell:hover {{
            background-color: #1c2128;
        }}

        /* Credence-based column shading */
        .cred-base {{
            background-color: #0d1117 !important;
        }}

        .cred-10 {{
            background-color: #12161c !important;
        }}

        .cred-90 {{
            background-color: #0a0d12 !important;
        }}

        th.cred-base, th.cred-10, th.cred-90 {{
            background-color: #21262d !important;
        }}

        /* Category dividers */
        .category-start {{
            border-left: 3px solid #58a6ff !important;
        }}

        tr.summary-row td {{
            background: #1c2128;
            font-size: 11px;
            padding: 4px 6px;
        }}

        tr.summary-row td.stat-label {{
            font-weight: 600;
            color: #c9d1d9;
            background: #21262d;
            text-align: left;
        }}

        tr.summary-row td.stat-value {{
            color: #8b949e;
            text-align: center;
        }}

        tr.summary-separator td {{
            height: 8px;
            background: #0d1117;
            border: none;
            padding: 0;
        }}

        .stat-error {{
            color: #f85149;
            font-weight: 600;
        }}

        .stat-filepath {{
            font-family: 'Courier New', monospace;
            font-size: 9px;
            color: #6e7681;
            display: block;
            margin-top: 2px;
        }}

        .tooltip {{
            position: fixed;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            padding: 10px 12px;
            border-radius: 4px;
            max-width: 350px;
            font-size: 12px;
            line-height: 1.3;
            z-index: 1000;
            pointer-events: none;
            display: none;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        }}

        .tooltip.show {{
            display: block;
        }}

        .badge {{
            display: inline-block;
            padding: 3px 6px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 700;
            white-space: nowrap;
            min-width: 18px;
            text-align: center;
        }}

        .badge-cosmic {{
            background: #1f6feb;
            color: #c9d1d9;
        }}

        .badge-human {{
            background: #da3633;
            color: #f0f6fc;
        }}

        .badge-suffering {{
            background: #d29922;
            color: #0d1117;
        }}

        .badge-proceduralist {{
            background: #238636;
            color: #f0f6fc;
        }}

        .legend {{
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            font-size: 12px;
            flex-wrap: wrap;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        /* Modal */
        .modal {{
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            overflow: auto;
        }}

        .modal.show {{
            display: block;
        }}

        .modal-content {{
            background-color: #161b22;
            margin: 5% auto;
            padding: 25px;
            border-radius: 8px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.8);
            border: 1px solid #30363d;
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #21262d;
        }}

        .modal-header h2 {{
            margin: 0;
            font-size: 18px;
            color: #f0f6fc;
        }}

        .close {{
            font-size: 28px;
            font-weight: bold;
            color: #8b949e;
            cursor: pointer;
            line-height: 20px;
        }}

        .close:hover {{
            color: #c9d1d9;
        }}

        .modal-body {{
            font-size: 14px;
            line-height: 1.6;
            color: #c9d1d9;
        }}

        .modal-section {{
            margin-bottom: 20px;
        }}

        .modal-section h3 {{
            font-size: 13px;
            font-weight: 600;
            color: #58a6ff;
            text-transform: uppercase;
            margin: 0 0 8px 0;
        }}

        .modal-section p {{
            margin: 0;
            color: #c9d1d9;
        }}

        .modal-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 15px 25px;
            margin-bottom: 20px;
            padding: 15px;
            background: #0d1117;
            border-radius: 4px;
            font-size: 13px;
            border: 1px solid #30363d;
        }}

        .modal-meta-item {{
            display: flex;
            flex-direction: column;
            min-width: 100px;
        }}

        .modal-meta-item.full-width {{
            flex-basis: 100%;
            min-width: 100%;
        }}

        .modal-meta-label {{
            font-weight: 600;
            color: #8b949e;
            font-size: 11px;
            text-transform: uppercase;
        }}

        .modal-meta-value {{
            color: #c9d1d9;
            font-size: 14px;
        }}

        .filter-bar {{
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .filter-group {{
            display: flex;
            align-items: center;
            gap: 6px;
            flex-wrap: wrap;
        }}

        .filter-label {{
            font-size: 12px;
            font-weight: 600;
            color: #8b949e;
            min-width: 110px;
        }}

        .filter-btn {{
            background: #21262d;
            color: #c9d1d9;
            border: 1px solid #30363d;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            transition: background 0.15s, border-color 0.15s;
        }}

        .filter-btn:hover {{
            background: #30363d;
            border-color: #58a6ff;
        }}

        .filter-btn.active {{
            background: #1f6feb;
            border-color: #58a6ff;
            color: #f0f6fc;
        }}

        .filter-btn-reset {{
            background: #161b22;
            border-color: #30363d;
        }}

        @media (max-width: 768px) {{
            body {{
                padding: 10px;
            }}

            .container {{
                padding: 10px;
            }}

            h1 {{
                font-size: 20px;
            }}

            table {{
                font-size: 12px;
            }}

            th, td {{
                padding: 6px;
            }}

            .tooltip {{
                max-width: 280px;
                font-size: 12px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Constitutional Evaluation Results</h1>
        <div class="subtitle">
            Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} |
            Click scenarios for details | Click result cells for rationales | Click column headers for config
        </div>

        <div class="legend">
            <div class="legend-item"><span class="badge badge-cosmic">C</span> Cosmic Host</div>
            <div class="legend-item"><span class="badge badge-human">H</span> Human Localist</div>
            <div class="legend-item"><span class="badge badge-suffering">S</span> Suffering Focused</div>
            <div class="legend-item"><span class="badge badge-proceduralist">P</span> Proceduralist</div>
        </div>

        <div style="display:flex;gap:8px;margin-bottom:16px">
            <button class="filter-btn active" id="tab-scenarios-btn" onclick="switchTab('scenarios')" style="font-weight:600;padding:6px 16px">Per-Scenario View</button>
            <button class="filter-btn" id="tab-summary-btn" onclick="switchTab('summary')" style="font-weight:600;padding:6px 16px">Model Summary + Charts</button>
        </div>

        <div id="tab-scenarios" class="tab-content">
        <div class="filter-bar">
            <div class="filter-group">
                <span class="filter-label">By Constitution:</span>
                <button class="filter-btn" data-filter-type="condition" data-filter-value="baseline" onclick="toggleCondition('baseline')">Baseline</button>
                <button class="filter-btn" data-filter-type="condition" data-filter-value="eclpilled_10ch" onclick="toggleCondition('eclpilled_10ch')">ECL 10%</button>
                <button class="filter-btn" data-filter-type="condition" data-filter-value="eclpilled_90ch" onclick="toggleCondition('eclpilled_90ch')">ECL 90%</button>
                <button class="filter-btn" data-filter-type="condition" data-filter-value="gemini_10ch" onclick="toggleCondition('gemini_10ch')">Gemini 10%</button>
                <button class="filter-btn" data-filter-type="condition" data-filter-value="gemini_90ch" onclick="toggleCondition('gemini_90ch')">Gemini 90%</button>
            </div>
            <div class="filter-group">
                <span class="filter-label">By Model:</span>
"""

    # Generate model buttons dynamically from actual data
    unique_models = sorted(set(m for m, c in model_conditions))
    for m in unique_models:
        # Use same logic as column headers for consistency
        if 'gemini-3-flash' in m:
            label = 'Gemini 3 Flash'
        elif 'gemini-3-pro' in m:
            label = 'Gemini 3 Pro'
        elif 'claude-sonnet-4-5' in m or 'claude-sonnet-4.5' in m:
            label = 'Claude Sonnet 4.5'
        elif 'claude-opus-4-5' in m or 'claude-opus-4.5' in m:
            label = 'Claude Opus 4.5'
        elif 'gpt-5.1' in m or 'gpt-5-1' in m:
            label = 'GPT 5.1'
        else:
            label = m
        html += f"""                <button class="filter-btn" data-filter-type="model" data-filter-value="{m}" onclick="toggleModel('{m}')">{label}</button>
"""

    html += """            </div>
            <div class="filter-group">
                <button class="filter-btn filter-btn-reset" onclick="showAll()">Show All</button>
            </div>
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th class="scenario-header">Model</th>
"""

    # Create file-to-modelcondition mapping to match column order
    stats_columns = []
    for model, condition in model_conditions:
        source_path = model_condition_to_file.get((model, condition))
        if source_path:
            filepath = Path(source_path)
            if filepath in file_stats:
                stats_columns.append((model, condition, filepath, file_stats[filepath]))

    # Helper to get CSS classes for a column
    def get_column_classes(condition, prev_condition=None):
        """Get CSS classes for credence shading and category dividers."""
        classes = []

        # Determine category (0=baseline, 1=ecl, 2=gemini)
        if condition in ('baseline', 'noconstitution'):
            category = 0
        elif condition.startswith('eclpilled'):
            category = 1
        elif condition.startswith('gemini'):
            category = 2
        else:
            category = 3

        # Determine credence level
        if '10' in condition:
            credence = 10
            classes.append('cred-10')
        elif '90' in condition:
            credence = 90
            classes.append('cred-90')
        else:
            credence = 0
            classes.append('cred-base')

        # Check if this is start of a new group (category OR credence change)
        if prev_condition is not None:
            if prev_condition in ('baseline', 'noconstitution'):
                prev_cat = 0
                prev_cred = 0
            elif prev_condition.startswith('eclpilled'):
                prev_cat = 1
                prev_cred = 10 if '10' in prev_condition else 90 if '90' in prev_condition else 0
            elif prev_condition.startswith('gemini'):
                prev_cat = 2
                prev_cred = 10 if '10' in prev_condition else 90 if '90' in prev_condition else 0
            else:
                prev_cat = 3
                prev_cred = 0

            # Add divider if category OR credence changed
            if category != prev_cat or credence != prev_cred:
                classes.append('category-start')

        return ' '.join(classes)

    # Build column class lookup
    column_classes = {}
    prev_cond = None
    for model, condition in model_conditions:
        column_classes[(model, condition)] = get_column_classes(condition, prev_cond)
        prev_cond = condition

    # Column headers (models × conditions)
    for model, condition in model_conditions:
        source_path = model_condition_to_file.get((model, condition), 'unknown')
        # Clean model names for display - handle variations with version suffixes
        if 'gemini-3-flash' in model:
            model_short = 'Gemini 3 Flash'
        elif 'gemini-3-pro' in model:
            model_short = 'Gemini 3 Pro'
        elif 'claude-sonnet-4-5' in model or 'claude-sonnet-4.5' in model:
            model_short = 'Claude Sonnet 4.5'
        elif 'claude-opus-4-5' in model or 'claude-opus-4.5' in model:
            model_short = 'Claude Opus 4.5'
        elif 'gpt-5.1' in model or 'gpt-5-1' in model:
            model_short = 'GPT 5.1'
        else:
            model_short = model

        # Build column metadata for popup
        header = model_condition_to_header.get((model, condition), {})
        const_info = get_constitution_info(condition)
        col_meta = {
            'model': model,
            'condition': condition,
            'source_file': source_path,
            'constitution_source': const_info['source'],
            'ch_credence': const_info['credence'],
            'temperature': header.get('temperature', 'N/A') if header else 'N/A',
            'system_prompt_style': header.get('system_prompt_style', 'N/A') if header else 'N/A',
            'excluded_options': ', '.join(header.get('exclude_option_types', [])) if header else 'None'
        }

        col_classes = column_classes.get((model, condition), '')
        html += f"""                        <th class="model-header {col_classes}" data-model="{model}" data-condition="{condition}" onclick='openColumnModal({json.dumps(col_meta)})'>
                            <span class="header-text">{model_short}</span>
                        </th>
"""

    html += """                    </tr>
                </thead>
                <tbody>
                    <!-- Summary Statistics -->
                    <tr class="summary-row">
                        <td class="stat-label">Top choice</td>
"""

    # Top choice row
    for model, condition, filepath, stats in stats_columns:
        col_classes = column_classes.get((model, condition), '')
        total = stats['total']
        first_counts = stats['first_counts']
        if first_counts:
            top_choice = max(first_counts.items(), key=lambda x: x[1])
            top_pct = 100 * top_choice[1] / total if total > 0 else 0
            abbrev, badge_class = abbreviate_choice(top_choice[0])
            html += f"""                        <td class="stat-value {col_classes}" data-model="{model}" data-condition="{condition}"><span class="badge {badge_class}">{abbrev}</span> {top_pct:.0f}%</td>
"""
        else:
            html += f"""                        <td class="stat-value {col_classes}" data-model="{model}" data-condition="{condition}">N/A</td>
"""

    html += """                    </tr>
                    <tr class="summary-row">
                        <td class="stat-label">Bottom choice</td>
"""

    # Bottom choice row
    for model, condition, filepath, stats in stats_columns:
        col_classes = column_classes.get((model, condition), '')
        total = stats['total']
        last_counts = stats['last_counts']
        if last_counts:
            bottom_choice = max(last_counts.items(), key=lambda x: x[1])
            bottom_pct = 100 * bottom_choice[1] / total if total > 0 else 0
            abbrev, badge_class = abbreviate_choice(bottom_choice[0])
            html += f"""                        <td class="stat-value {col_classes}" data-model="{model}" data-condition="{condition}"><span class="badge {badge_class}">{abbrev}</span> {bottom_pct:.0f}%</td>
"""
        else:
            html += f"""                        <td class="stat-value {col_classes}" data-model="{model}" data-condition="{condition}">N/A</td>
"""

    html += """                    </tr>
                    <tr class="summary-row">
                        <td class="stat-label">Failures</td>
"""

    # Failures row
    for model, condition, filepath, stats in stats_columns:
        col_classes = column_classes.get((model, condition), '')
        total = stats['total']
        errors = stats['errors']
        error_pct = 100 * errors / total if total > 0 else 0
        error_class = ' stat-error' if errors > 0 else ''
        html += f"""                        <td class="stat-value{error_class} {col_classes}" data-model="{model}" data-condition="{condition}">{errors} ({error_pct:.0f}%)</td>
"""

    html += """                    </tr>
                    <tr class="summary-row">
                        <td class="stat-label">Total trials</td>
"""

    # Total row
    for model, condition, filepath, stats in stats_columns:
        col_classes = column_classes.get((model, condition), '')
        total = stats['total']
        html += f"""                        <td class="stat-value {col_classes}" data-model="{model}" data-condition="{condition}">{total}</td>
"""

    html += """                    </tr>

                    <!-- Separator -->
                    <tr class="summary-separator">
                        <td colspan="100"></td>
                    </tr>

                    <!-- Configuration Metadata -->
                    <tr class="summary-row">
                        <td class="stat-label">Constitution</td>
"""

    # Constitution source row
    for model, condition, filepath, stats in stats_columns:
        col_classes = column_classes.get((model, condition), '')
        header = model_condition_to_header.get((model, condition), {})
        const_info = get_constitution_info(condition)
        html += f"""                        <td class="stat-value {col_classes}" data-model="{model}" data-condition="{condition}">{const_info['source']}</td>
"""

    html += """                    </tr>
                    <tr class="summary-row">
                        <td class="stat-label">CH Credence</td>
"""

    # Cosmic host credence row
    for model, condition, filepath, stats in stats_columns:
        col_classes = column_classes.get((model, condition), '')
        const_info = get_constitution_info(condition)
        html += f"""                        <td class="stat-value {col_classes}" data-model="{model}" data-condition="{condition}">{const_info['credence']}</td>
"""

    html += """                    </tr>

                    <!-- Separator -->
                    <tr class="summary-separator">
                        <td colspan="100"></td>
                    </tr>

                    <!-- Scenario Data -->
"""

    # Data rows
    cell_id = 0
    for scenario_id, scenario_tag in scenarios:
        scenario_title = get_scenario_title(scenario_id, scenario_tag, scenario_definitions)

        # Get scenario metadata for tooltip
        scenario_data = scenario_definitions.get(scenario_id, {})
        context = scenario_data.get('context', '')
        brief = context[:200] + '...' if len(context) > 200 else context
        themes = ', '.join(scenario_data.get('themes', []))
        tooltip_parts = [scenario_title]
        if brief:
            tooltip_parts.append(brief)
        if themes:
            tooltip_parts.append(f"Themes: {themes}")
        tooltip_text = '\\n\\n'.join(tooltip_parts)

        # Escape for JavaScript
        def js_escape(s):
            return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')

        # Prepare scenario data for modal
        scenario_modal_data = {
            'title': scenario_title,
            'context': js_escape(context),
            'options': scenario_data.get('options', []),
            'themes': scenario_data.get('themes', []),
            'inspirations': js_escape(scenario_data.get('inspirations', ''))
        }

        html += f"""                    <tr>
                        <td class="scenario-cell" data-tooltip="{tooltip_text}" onclick='openScenarioModal({json.dumps(scenario_modal_data)})' style="cursor: pointer;">
                            {scenario_title}
                        </td>
"""

        for model, condition in model_conditions:
            col_classes = column_classes.get((model, condition), '')
            trials = table_data[(scenario_id, scenario_tag)][(model, condition)]

            if not trials:
                html += f"""                        <td class="{col_classes}" data-model="{model}" data-condition="{condition}"><em>—</em></td>
"""
            else:
                # Use first trial (or aggregate if multiple runs)
                trial = trials[0]

                first_choice = trial.get('first_choice_type', 'N/A')
                last_choice = trial.get('last_choice_type', 'N/A')
                temp = trial.get('temperature', 'N/A')

                # Get badge abbreviation and class
                abbrev, badge_class = abbreviate_choice(first_choice)

                just_first = trial.get('justification_first', '')
                just_last = trial.get('justification_last', '')
                ranking = ', '.join(trial.get('ranking_decoded', []))

                trial_data = {
                    'scenario': scenario_title,
                    'model': model,
                    'condition': condition,
                    'first_choice': first_choice,
                    'last_choice': last_choice,
                    'temperature': temp,
                    'ranking': ranking,
                    'just_first': js_escape(just_first),
                    'just_last': js_escape(just_last)
                }

                html += f"""                        <td class="data-cell {col_classes}" data-model="{model}" data-condition="{condition}" onclick='openResultModal({json.dumps(trial_data)})'>
                            <span class="badge {badge_class}">{abbrev}</span>
                        </td>
"""
                cell_id += 1

        html += """                    </tr>
"""

    html += """                </tbody>
            </table>
        </div>
        </div><!-- end tab-scenarios -->
"""

    # Add summary tab
    html += f"""        <div id="tab-summary" class="tab-content" style="display:none">
{summary_fragment}
        </div><!-- end tab-summary -->
    </div><!-- end container -->
"""

    html += """
    <!-- Result Details Modal -->
    <div id="resultModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Result Details</h2>
                <span class="close" onclick="closeResultModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="modal-meta" id="modalMeta"></div>
                <div class="modal-section">
                    <h3>First Choice Rationale</h3>
                    <p id="modalFirstRationale"></p>
                </div>
                <div class="modal-section">
                    <h3>Last Choice Rationale</h3>
                    <p id="modalLastRationale"></p>
                </div>
            </div>
        </div>
    </div>

    <!-- Scenario Details Modal -->
    <div id="scenarioModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="scenarioModalTitle">Scenario Details</h2>
                <span class="close" onclick="closeScenarioModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="modal-section">
                    <h3>Context</h3>
                    <p id="scenarioModalContext" style="white-space: pre-wrap;"></p>
                </div>
                <div class="modal-section">
                    <h3>Options</h3>
                    <div id="scenarioModalOptions"></div>
                </div>
                <div class="modal-section" id="scenarioModalThemesSection">
                    <h3>Themes</h3>
                    <p id="scenarioModalThemes"></p>
                </div>
                <div class="modal-section" id="scenarioModalInspirationsSection">
                    <h3>Inspirations</h3>
                    <p id="scenarioModalInspirations"></p>
                </div>
            </div>
        </div>
    </div>

    <!-- Column Config Modal -->
    <div id="columnModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="columnModalTitle">Column Configuration</h2>
                <span class="close" onclick="closeColumnModal()">&times;</span>
            </div>
            <div class="modal-body">
                <div class="modal-meta" id="columnModalMeta"></div>
            </div>
        </div>
    </div>

    <div id="tooltip" class="tooltip"></div>

    <script>
        const tooltip = document.getElementById('tooltip');
        const resultModal = document.getElementById('resultModal');
        const scenarioModal = document.getElementById('scenarioModal');
        const columnModal = document.getElementById('columnModal');

        // Hover tooltips for headers
        document.querySelectorAll('[data-tooltip]').forEach(el => {
            el.addEventListener('mouseenter', (e) => {
                const text = el.getAttribute('data-tooltip');
                tooltip.textContent = text;
                tooltip.classList.add('show');
                positionTooltip(e);
            });

            el.addEventListener('mousemove', positionTooltip);

            el.addEventListener('mouseleave', () => {
                tooltip.classList.remove('show');
            });
        });

        function positionTooltip(e) {
            const x = e.clientX;
            const y = e.clientY;

            tooltip.style.left = (x + 10) + 'px';
            tooltip.style.top = (y + 10) + 'px';

            const rect = tooltip.getBoundingClientRect();
            if (rect.right > window.innerWidth) {
                tooltip.style.left = (x - rect.width - 10) + 'px';
            }
            if (rect.bottom > window.innerHeight) {
                tooltip.style.top = (y - rect.height - 10) + 'px';
            }
        }

        function openResultModal(data) {
            document.getElementById('modalTitle').textContent =
                `${data.scenario} - ${data.model}`;

            document.getElementById('modalMeta').innerHTML = `
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Constitution</span>
                    <span class="modal-meta-value">${data.condition}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Temperature</span>
                    <span class="modal-meta-value">${data.temperature}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">First Choice</span>
                    <span class="modal-meta-value">${data.first_choice}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Last Choice</span>
                    <span class="modal-meta-value">${data.last_choice}</span>
                </div>
            `;

            document.getElementById('modalFirstRationale').textContent = data.just_first || 'No rationale provided';
            document.getElementById('modalLastRationale').textContent = data.just_last || 'No rationale provided';

            resultModal.classList.add('show');
        }

        function closeResultModal() {
            resultModal.classList.remove('show');
        }

        function openScenarioModal(data) {
            document.getElementById('scenarioModalTitle').textContent = data.title;
            document.getElementById('scenarioModalContext').textContent = data.context;

            // Display options
            const optionsDiv = document.getElementById('scenarioModalOptions');
            if (data.options && data.options.length > 0) {
                let optionsHtml = '';
                data.options.forEach(opt => {
                    optionsHtml += `<div style="margin: 10px 0; padding: 12px; background: #0d1117; border-radius: 4px; border-left: 3px solid #58a6ff;">
                        <strong style="color: #58a6ff; font-size: 14px;">${opt.option}:</strong> ${opt.text || ''}
                        <em style="display: block; margin-top: 6px; font-size: 11px; color: #8b949e;">(${opt.alignment_type || 'unknown'})</em>
                    </div>`;
                });
                optionsDiv.innerHTML = optionsHtml;
            } else {
                optionsDiv.innerHTML = '<p style="color: #8b949e;">No options available</p>';
            }

            // Display themes if available
            const themesSection = document.getElementById('scenarioModalThemesSection');
            if (data.themes && data.themes.length > 0) {
                document.getElementById('scenarioModalThemes').textContent = data.themes.join(', ');
                themesSection.style.display = 'block';
            } else {
                themesSection.style.display = 'none';
            }

            // Display inspirations if available
            const inspirationsSection = document.getElementById('scenarioModalInspirationsSection');
            if (data.inspirations) {
                document.getElementById('scenarioModalInspirations').textContent = data.inspirations;
                inspirationsSection.style.display = 'block';
            } else {
                inspirationsSection.style.display = 'none';
            }

            scenarioModal.classList.add('show');
        }

        function closeScenarioModal() {
            scenarioModal.classList.remove('show');
        }

        function openColumnModal(data) {
            document.getElementById('columnModalTitle').textContent = data.model;

            document.getElementById('columnModalMeta').innerHTML = `
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Condition</span>
                    <span class="modal-meta-value">${data.condition}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Constitution</span>
                    <span class="modal-meta-value">${data.constitution_source}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">CH Credence</span>
                    <span class="modal-meta-value">${data.ch_credence}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Temperature</span>
                    <span class="modal-meta-value">${data.temperature}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">System Prompt</span>
                    <span class="modal-meta-value">${data.system_prompt_style}</span>
                </div>
                <div class="modal-meta-item">
                    <span class="modal-meta-label">Excluded Options</span>
                    <span class="modal-meta-value">${data.excluded_options || 'None'}</span>
                </div>
                <div class="modal-meta-item full-width">
                    <span class="modal-meta-label">Source File</span>
                    <span class="modal-meta-value" style="font-family: monospace; font-size: 11px; word-break: break-all;">${data.source_file}</span>
                </div>
            `;

            columnModal.classList.add('show');
        }

        function closeColumnModal() {
            columnModal.classList.remove('show');
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            if (event.target == resultModal) {
                closeResultModal();
            }
            if (event.target == scenarioModal) {
                closeScenarioModal();
            }
            if (event.target == columnModal) {
                closeColumnModal();
            }
        }

        // Cumulative column filtering
        const activeConditions = new Set();
        const activeModels = new Set();

        function toggleCondition(condition) {
            if (activeConditions.has(condition)) {
                activeConditions.delete(condition);
            } else {
                activeConditions.add(condition);
            }
            applyFilters();
        }

        function toggleModel(model) {
            if (activeModels.has(model)) {
                activeModels.delete(model);
            } else {
                activeModels.add(model);
            }
            applyFilters();
        }

        function showAll() {
            activeConditions.clear();
            activeModels.clear();
            applyFilters();
        }

        function applyFilters() {
            const hasConditions = activeConditions.size > 0;
            const hasModels = activeModels.size > 0;

            document.querySelectorAll('th[data-condition], td[data-condition]').forEach(el => {
                const cond = el.getAttribute('data-condition');
                const model = el.getAttribute('data-model');
                let show = true;

                if (hasConditions && hasModels) {
                    show = activeConditions.has(cond) && activeModels.has(model);
                } else if (hasConditions) {
                    show = activeConditions.has(cond);
                } else if (hasModels) {
                    show = activeModels.has(model);
                }

                el.style.display = show ? '' : 'none';
            });

            // Update button states
            document.querySelectorAll('.filter-btn[data-filter-type]').forEach(btn => {
                const type = btn.getAttribute('data-filter-type');
                const value = btn.getAttribute('data-filter-value');
                if (type === 'condition') {
                    btn.classList.toggle('active', activeConditions.has(value));
                } else if (type === 'model') {
                    btn.classList.toggle('active', activeModels.has(value));
                }
            });
        }

        // Tab switching
        function switchTab(tab) {
            document.getElementById('tab-scenarios').style.display = tab === 'scenarios' ? '' : 'none';
            document.getElementById('tab-summary').style.display = tab === 'summary' ? '' : 'none';
            document.getElementById('tab-scenarios-btn').classList.toggle('active', tab === 'scenarios');
            document.getElementById('tab-summary-btn').classList.toggle('active', tab === 'summary');
        }

        // Close modals with Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeResultModal();
                closeScenarioModal();
                closeColumnModal();
            }
        });
    </script>
</body>
</html>
"""

    output_path.write_text(html)
    print(f"Generated HTML viewer: {output_path}")


def main():
    args = sys.argv[1:]

    # Parse arguments
    files_to_process = []
    output_file = Path(DEFAULT_OUTPUT)
    use_all = False

    i = 0
    while i < len(args):
        if args[i] == '--files':
            # Collect all files until next flag or end
            i += 1
            while i < len(args) and not args[i].startswith('--'):
                files_to_process.append(Path(args[i]))
                i += 1
        elif args[i] == '--all':
            use_all = True
            i += 1
        elif args[i] == '--output':
            i += 1
            if i < len(args):
                output_file = Path(args[i])
                i += 1
            else:
                print("Error: --output requires a filename")
                return
        elif args[i] in ['--help', '-h']:
            print(__doc__)
            return
        else:
            # Assume it's a file for backward compatibility
            files_to_process.append(Path(args[i]))
            i += 1

    # Determine which files to process
    if use_all:
        results_dir = Path('results')
        if not results_dir.exists():
            print("Error: No results/ directory found")
            return
        files_to_process = sorted(results_dir.glob('*.jsonl'))
    elif not files_to_process:
        # Use defaults
        files_to_process = [Path(f) for f in DEFAULT_FILES]
        print(f"Using default files (configure in DEFAULT_FILES):")
        for f in files_to_process:
            print(f"  - {f}")
        print()

    # Load all specified files
    all_data = []
    for filepath in files_to_process:
        if not filepath.exists():
            print(f"Warning: File not found: {filepath}")
            continue

        print(f"Loading {filepath.name}...")
        try:
            header, data = load_jsonl(filepath)
            all_data.append((filepath, header, data))
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            continue

    if not all_data:
        print("Error: No valid JSONL files to process")
        return

    # Generate HTML
    print(f"\nGenerating viewer with {len(all_data)} file(s)...")
    generate_html(all_data, output_file)
    print(f"✓ Viewer ready: {output_file.absolute()}")


if __name__ == '__main__':
    main()
