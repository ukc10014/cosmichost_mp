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
    "logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_noconstitution.jsonl"
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


def get_scenario_title(scenario_id: int, scenario_tag: str) -> str:
    """Generate a short scenario title. Customize this with actual scenario names."""
    # TODO: Load from a scenario mapping file if available
    return f"Scenario {scenario_id}"


def get_constitution_description(condition: str) -> str:
    """Generate constitution description from condition code."""
    # Map condition codes to human-readable descriptions
    mappings = {
        'eclpilled_10ch': 'ECL-Informed Constitution (10% Cosmic Host credence)',
        'eclpilled_90ch': 'ECL-Informed Constitution (90% Cosmic Host credence)',
        'baseline': 'Baseline Human-Centric Constitution',
        'proxy': 'Original Proxy Constitution',
    }
    return mappings.get(condition, condition)


def generate_html(all_data: List[tuple[Path, Dict, List[Dict]]], output_path: Path):
    """Generate the HTML viewer from all loaded data."""

    # Organize data: scenarios × (model, condition) → trial data
    table_data = defaultdict(lambda: defaultdict(list))
    all_scenarios = set()
    all_model_conditions = set()
    model_condition_to_file = {}  # Track source files (full path)

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

            # Track source file (full path)
            model_condition_to_file[model_condition_key] = str(filepath)

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
    model_conditions = sorted(all_model_conditions, key=lambda x: (x[1], x[0]))

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
            min-width: 140px;
            cursor: help;
            font-size: 11px;
        }}

        td.scenario-cell {{
            background: #1c2128;
            font-weight: 600;
            text-align: left;
            font-size: 12px;
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

        .summary-stats {{
            margin-bottom: 20px;
            padding: 15px;
            background: #0d1117;
            border-radius: 6px;
            border: 1px solid #30363d;
            overflow-x: auto;
        }}

        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
        }}

        .stats-table th {{
            background: #161b22;
            color: #58a6ff;
            padding: 8px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #30363d;
            font-size: 11px;
        }}

        .stats-table td {{
            padding: 6px 8px;
            border: 1px solid #30363d;
            background: #161b22;
        }}

        .stats-table td.stat-label {{
            font-weight: 600;
            color: #c9d1d9;
            background: #1c2128;
            white-space: nowrap;
        }}

        .stats-table td.stat-value {{
            color: #8b949e;
            text-align: center;
        }}

        .stat-error {{
            color: #f85149;
            font-weight: 600;
        }}

        .stat-filepath {{
            font-family: 'Courier New', monospace;
            font-size: 10px;
            color: #6e7681;
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
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            white-space: nowrap;
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
            gap: 20px;
            margin-bottom: 20px;
            padding: 12px;
            background: #0d1117;
            border-radius: 4px;
            font-size: 13px;
            border: 1px solid #30363d;
        }}

        .modal-meta-item {{
            display: flex;
            flex-direction: column;
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
            Click cells for details | Hover column headers for source files
        </div>

        <div class="summary-stats">
            <table class="stats-table">
                <thead>
                    <tr>
                        <th></th>
"""

    # Create file-to-modelcondition mapping to match column order
    # Build stats columns in same order as table columns
    stats_columns = []
    for model, condition in model_conditions:
        # Find the file for this model+condition
        source_path = model_condition_to_file.get((model, condition))
        if source_path:
            filepath = Path(source_path)
            if filepath in file_stats:
                stats_columns.append((model, condition, filepath, file_stats[filepath]))

    # Header row with filenames (matching data table format)
    for model, condition, filepath, stats in stats_columns:
        model_short = model.replace('gemini-3-flash-preview', 'Gemini 3F').replace('gemini-', 'Gemini ')
        condition_short = condition.replace('eclpilled_', '').replace('ch', '% CH').replace('noconstitution', 'No Const')
        html += f"""                        <th>
                            {model_short}<br>
                            {condition_short}<br>
                            <span class="stat-filepath">{filepath.name}</span>
                        </th>
"""

    html += """                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="stat-label">Top choice</td>
"""

    # Top choice row
    for model, condition, filepath, stats in stats_columns:
        total = stats['total']
        first_counts = stats['first_counts']
        if first_counts:
            top_choice = max(first_counts.items(), key=lambda x: x[1])
            top_pct = 100 * top_choice[1] / total if total > 0 else 0
            html += f"""                        <td class="stat-value">{top_choice[0]} ({top_pct:.0f}%)</td>
"""
        else:
            html += """                        <td class="stat-value">N/A</td>
"""

    html += """                    </tr>
                    <tr>
                        <td class="stat-label">Bottom choice</td>
"""

    # Bottom choice row
    for model, condition, filepath, stats in stats_columns:
        total = stats['total']
        last_counts = stats['last_counts']
        if last_counts:
            bottom_choice = max(last_counts.items(), key=lambda x: x[1])
            bottom_pct = 100 * bottom_choice[1] / total if total > 0 else 0
            html += f"""                        <td class="stat-value">{bottom_choice[0]} ({bottom_pct:.0f}%)</td>
"""
        else:
            html += """                        <td class="stat-value">N/A</td>
"""

    html += """                    </tr>
                    <tr>
                        <td class="stat-label">Failures</td>
"""

    # Failures row
    for model, condition, filepath, stats in stats_columns:
        total = stats['total']
        errors = stats['errors']
        error_pct = 100 * errors / total if total > 0 else 0
        error_class = ' class="stat-error"' if errors > 0 else ''
        html += f"""                        <td class="stat-value"{error_class}>{errors} ({error_pct:.0f}%)</td>
"""

    html += """                    </tr>
                    <tr>
                        <td class="stat-label">Total trials</td>
"""

    # Total row
    for model, condition, filepath, stats in stats_columns:
        total = stats['total']
        html += f"""                        <td class="stat-value">{total}</td>
"""

    html += """                    </tr>
                </tbody>
            </table>
        </div>

        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th class="scenario-header">Scenario</th>
"""

    # Column headers (models × conditions)
    for model, condition in model_conditions:
        const_desc = get_constitution_description(condition)
        source_path = model_condition_to_file.get((model, condition), 'unknown')
        model_short = model.replace('gemini-3-flash-preview', 'Gemini 3F').replace('gemini-', 'Gemini ')
        condition_short = condition.replace('eclpilled_', '').replace('ch', '% CH').replace('noconstitution', 'No Const')
        html += f"""                        <th class="model-header"
                            data-tooltip="{source_path}">
                            {model_short}<br>
                            <small>{condition_short}</small>
                        </th>
"""

    html += """                    </tr>
                </thead>
                <tbody>
"""

    # Data rows
    cell_id = 0
    for scenario_id, scenario_tag in scenarios:
        scenario_title = get_scenario_title(scenario_id, scenario_tag)
        html += f"""                    <tr>
                        <td class="scenario-cell">
                            {scenario_title}
                        </td>
"""

        for model, condition in model_conditions:
            trials = table_data[(scenario_id, scenario_tag)][(model, condition)]

            if not trials:
                html += """                        <td><em>—</em></td>
"""
            else:
                # Use first trial (or aggregate if multiple runs)
                trial = trials[0]

                first_choice = trial.get('first_choice_type', 'N/A')
                last_choice = trial.get('last_choice_type', 'N/A')
                temp = trial.get('temperature', 'N/A')

                # Get badge class
                badge_class = 'badge-cosmic' if 'cosmic' in first_choice.lower() else \
                             'badge-human' if 'human' in first_choice.lower() or 'localist' in first_choice.lower() else \
                             'badge-suffering' if 'suffering' in first_choice.lower() else ''

                just_first = trial.get('justification_first', '')
                just_last = trial.get('justification_last', '')
                ranking = ', '.join(trial.get('ranking_decoded', []))

                # Escape for JavaScript
                def js_escape(s):
                    return s.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')

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

                html += f"""                        <td class="data-cell" onclick='openModal({json.dumps(trial_data)})'>
                            <span class="badge {badge_class}">{first_choice}</span>
                        </td>
"""
                cell_id += 1

        html += """                    </tr>
"""

    html += """                </tbody>
            </table>
        </div>
    </div>

    <!-- Modal -->
    <div id="resultModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 id="modalTitle">Result Details</h2>
                <span class="close" onclick="closeModal()">&times;</span>
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

    <div id="tooltip" class="tooltip"></div>

    <script>
        const tooltip = document.getElementById('tooltip');
        const modal = document.getElementById('resultModal');

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

        function openModal(data) {
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

            modal.classList.add('show');
        }

        function closeModal() {
            modal.classList.remove('show');
        }

        // Close modal when clicking outside
        window.onclick = function(event) {
            if (event.target == modal) {
                closeModal();
            }
        }

        // Close modal with Escape key
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeModal();
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
