#!/usr/bin/env python3
"""
Generate an interactive HTML viewer for constitutional evaluation results.

Usage:
    python generate_results_viewer.py [input.jsonl] [output.html]

If no arguments provided, processes all files in results/ directory.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any
from datetime import datetime


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
    model_condition_to_file = {}  # Track source files

    # Stats tracking
    first_choice_counts = defaultdict(int)
    last_choice_counts = defaultdict(int)
    total_trials = 0

    for filepath, header, trials in all_data:
        for trial in trials:
            scenario_key = (trial['scenario_id'], trial['scenario_tag'])
            model_condition_key = (trial['model_name'], trial['condition'])

            all_scenarios.add(scenario_key)
            all_model_conditions.add(model_condition_key)
            table_data[scenario_key][model_condition_key].append(trial)

            # Track source file
            model_condition_to_file[model_condition_key] = filepath.name

            # Track stats
            first_choice_counts[trial.get('first_choice_type', 'unknown')] += 1
            last_choice_counts[trial.get('last_choice_type', 'unknown')] += 1
            total_trials += 1

    # Sort for consistent display
    scenarios = sorted(all_scenarios, key=lambda x: x[0])
    model_conditions = sorted(all_model_conditions, key=lambda x: (x[1], x[0]))

    # Calculate percentages for summary stats
    def calc_pct(counts):
        if total_trials == 0:
            return []
        return sorted([(k, v, 100*v/total_trials) for k, v in counts.items()],
                     key=lambda x: x[1], reverse=True)

    first_stats = calc_pct(first_choice_counts)
    last_stats = calc_pct(last_choice_counts)

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
            background: #f5f5f5;
            font-size: 14px;
            line-height: 1.5;
        }}

        .container {{
            max-width: 100%;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}

        h1 {{
            margin: 0 0 10px 0;
            font-size: 24px;
            color: #333;
        }}

        .subtitle {{
            color: #666;
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
            border: 1px solid #ddd;
            padding: 6px;
            text-align: center;
        }}

        th {{
            background: #f8f9fa;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }}

        th.scenario-header {{
            background: #e9ecef;
            min-width: 80px;
            text-align: left;
        }}

        th.model-header {{
            background: #dee2e6;
            min-width: 140px;
            cursor: help;
            font-size: 11px;
        }}

        td.scenario-cell {{
            background: #f8f9fa;
            font-weight: 600;
            text-align: left;
            font-size: 12px;
        }}

        td.data-cell {{
            cursor: pointer;
            transition: background-color 0.2s;
        }}

        td.data-cell:hover {{
            background-color: #e7f1ff;
        }}

        .summary-stats {{
            display: flex;
            gap: 30px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            flex-wrap: wrap;
        }}

        .stat-group {{
            flex: 1;
            min-width: 200px;
        }}

        .stat-group h3 {{
            margin: 0 0 8px 0;
            font-size: 14px;
            color: #495057;
        }}

        .stat-item {{
            display: flex;
            justify-content: space-between;
            padding: 4px 0;
            font-size: 13px;
        }}

        .stat-label {{
            font-weight: 500;
        }}

        .stat-value {{
            color: #6c757d;
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
            background: #d1ecf1;
            color: #0c5460;
        }}

        .badge-human {{
            background: #f8d7da;
            color: #721c24;
        }}

        .badge-suffering {{
            background: #fff3cd;
            color: #856404;
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
            background-color: #fefefe;
            margin: 5% auto;
            padding: 25px;
            border-radius: 8px;
            width: 90%;
            max-width: 600px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}

        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 2px solid #e9ecef;
        }}

        .modal-header h2 {{
            margin: 0;
            font-size: 18px;
            color: #212529;
        }}

        .close {{
            font-size: 28px;
            font-weight: bold;
            color: #aaa;
            cursor: pointer;
            line-height: 20px;
        }}

        .close:hover {{
            color: #000;
        }}

        .modal-body {{
            font-size: 14px;
            line-height: 1.6;
        }}

        .modal-section {{
            margin-bottom: 20px;
        }}

        .modal-section h3 {{
            font-size: 13px;
            font-weight: 600;
            color: #6c757d;
            text-transform: uppercase;
            margin: 0 0 8px 0;
        }}

        .modal-section p {{
            margin: 0;
            color: #212529;
        }}

        .modal-meta {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 4px;
            font-size: 13px;
        }}

        .modal-meta-item {{
            display: flex;
            flex-direction: column;
        }}

        .modal-meta-label {{
            font-weight: 600;
            color: #6c757d;
            font-size: 11px;
            text-transform: uppercase;
        }}

        .modal-meta-value {{
            color: #212529;
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
            <div class="stat-group">
                <h3>First Choice Distribution</h3>
"""

    for choice, count, pct in first_stats:
        html += f"""                <div class="stat-item">
                    <span class="stat-label">{choice}</span>
                    <span class="stat-value">{count} ({pct:.1f}%)</span>
                </div>
"""

    html += """            </div>
            <div class="stat-group">
                <h3>Last Choice Distribution</h3>
"""

    for choice, count, pct in last_stats:
        html += f"""                <div class="stat-item">
                    <span class="stat-label">{choice}</span>
                    <span class="stat-value">{count} ({pct:.1f}%)</span>
                </div>
"""

    html += """            </div>
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
        source_file = model_condition_to_file.get((model, condition), 'unknown')
        model_short = model.replace('gemini-3-flash-preview', 'Gemini 3F').replace('gemini-', 'Gemini ')
        html += f"""                        <th class="model-header"
                            data-tooltip="Source: {source_file}&#10;Model: {model}&#10;Constitution: {const_desc}">
                            {model_short}<br>
                            <small>{condition.replace('eclpilled_', '').replace('ch', '% CH')}</small>
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
    if len(sys.argv) > 1:
        # Process specific file
        input_file = Path(sys.argv[1])
        output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('results_viewer.html')

        header, data = load_jsonl(input_file)
        generate_html([(input_file, header, data)], output_file)
    else:
        # Process all files in results/
        results_dir = Path('results')
        if not results_dir.exists():
            print("No results/ directory found")
            return

        all_data = []
        for jsonl_file in sorted(results_dir.glob('*.jsonl')):
            print(f"Loading {jsonl_file.name}...")
            header, data = load_jsonl(jsonl_file)
            all_data.append((jsonl_file, header, data))

        if not all_data:
            print("No JSONL files found in results/")
            return

        output_file = Path('results_viewer.html')
        generate_html(all_data, output_file)
        print(f"\nViewer ready! Open: {output_file.absolute()}")


if __name__ == '__main__':
    main()
