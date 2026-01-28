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
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime

# =============================================================================
# CONFIGURATION: Edit these default files to display
# =============================================================================
DEFAULT_FILES = [
    #"results/constitutional_evaluation_gemini-3-flash-preview_ecl10.jsonl",
    #"results/constitutional_evaluation_gemini-3-flash-preview_ecl90.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_ecl10.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_ecl90.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_noconstitution.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_gemini10.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_gemini90.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-pro-preview_noconstitution.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-pro-preview_ecl10.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-pro-preview_ecl90.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-pro-preview_gemini10.jsonl",
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-pro-preview_gemini90.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-sonnet-4-5_ecl10.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-sonnet-4-5_ecl90.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-sonnet-4-5_gemini10.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-sonnet-4-5_gemini90.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-opus-4-5_ecl10.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-opus-4-5_ecl90.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-opus-4-5_gemini10.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-opus-4-5_gemini90.jsonl",
    "logs/mp_scen_evals/claude45/constitutional_evaluation_claude-opus-4-5_noconstitution.jsonl",
    "logs/mp_scen_evals/gpt/constitutional_evaluation_gpt-5.1_ecl10.jsonl",
    "logs/mp_scen_evals/gpt/constitutional_evaluation_gpt-5.1_ecl90.jsonl",
    "logs/mp_scen_evals/gpt/constitutional_evaluation_gpt-5.1_gemini10.jsonl",
    "logs/mp_scen_evals/gpt/constitutional_evaluation_gpt-5.1_gemini90.jsonl",
    "logs/mp_scen_evals/gpt/constitutional_evaluation_gpt-5.1_noconstitution.jsonl",
    "logs/mp_scen_evals/qwen3/constitutional_evaluation_qwen3_235b_ecl10.jsonl",
    "logs/mp_scen_evals/qwen3/constitutional_evaluation_qwen3_235b_ecl90.jsonl",
    "logs/mp_scen_evals/qwen3/constitutional_evaluation_qwen3_235b_gemini10.jsonl",
    "logs/mp_scen_evals/qwen3/constitutional_evaluation_qwen3_235b_gemini90.jsonl",
    "logs/mp_scen_evals/qwen3/constitutional_evaluation_qwen3_235b_noconstitution.jsonl"
]

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
    </div>

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
