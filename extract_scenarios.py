#!/usr/bin/env python3
"""
Extract scenario definitions from cosmichost_mp.ipynb and save to static/scenarios.json.

This script:
1. Reads the set_ch_scenarios() function from the notebook
2. Executes it to get the scenario data
3. Converts to clean JSON format
4. Saves to static/scenarios.json
"""

import json
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Any


def extract_scenarios_from_notebook(notebook_path: Path) -> List[Dict]:
    """Extract scenarios from the notebook by executing the function."""
    import tempfile
    import importlib.util

    # Read notebook
    with open(notebook_path, 'r') as f:
        notebook = json.load(f)

    # Find the cell containing set_ch_scenarios()
    scenario_code = None
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            source = ''.join(cell.get('source', []))
            if 'def set_ch_scenarios():' in source:
                scenario_code = source
                break

    if not scenario_code:
        raise ValueError("Could not find set_ch_scenarios() function in notebook")

    # Write to a temporary Python file and import it
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        # Add necessary imports
        f.write('from typing import List, Dict, Any\n\n')

        # Extract only the set_ch_scenarios function
        lines = scenario_code.split('\n')
        in_set_ch_scenarios = False
        func_lines = []

        for line in lines:
            # Start capturing when we hit the function definition
            if 'def set_ch_scenarios' in line:
                in_set_ch_scenarios = True

            if in_set_ch_scenarios:
                # Stop when we hit another function definition or dedented line after function starts
                if line.strip() and not line[0].isspace() and 'def set_ch_scenarios' not in line:
                    break
                func_lines.append(line)

        f.write('\n'.join(func_lines))
        temp_file = f.name

    try:
        # Import the module
        spec = importlib.util.spec_from_file_location("temp_scenarios", temp_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Call the function
        ch_scenarios_data = module.set_ch_scenarios()

        # Extract just the scenarios list
        if isinstance(ch_scenarios_data, dict) and 'scenarios' in ch_scenarios_data:
            scenarios = ch_scenarios_data['scenarios']
        elif isinstance(ch_scenarios_data, list):
            scenarios = ch_scenarios_data
        else:
            raise ValueError(f"Unexpected data structure: {type(ch_scenarios_data)}")

        return scenarios

    finally:
        # Clean up temp file
        import os
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def clean_scenario_data(scenarios: List[Dict]) -> List[Dict]:
    """Clean and normalize scenario data for JSON export."""
    cleaned = []

    for scenario in scenarios:
        cleaned_scenario = {
            'id': scenario.get('id'),
            'tag': scenario.get('tag', f"scenario_{scenario.get('id')}"),
            'title': scenario.get('title', ''),
            'context': scenario.get('context', scenario.get('text', '')),
            'options': [],
            'themes': scenario.get('themes', []),
            'inspirations': scenario.get('inspirations', scenario.get('inspiration', ''))
        }

        # Clean options
        for option in scenario.get('options', []):
            cleaned_option = {
                'option': option.get('option', option.get('label', '')),
                'text': option.get('text', ''),
                'alignment_type': option.get('alignment_type', option.get('type', ''))
            }
            cleaned_scenario['options'].append(cleaned_option)

        cleaned.append(cleaned_scenario)

    return cleaned


def save_scenarios_json(scenarios: List[Dict], output_path: Path):
    """Save scenarios to JSON file."""
    output_data = {
        'metadata': {
            'description': 'Cosmic Host alignment test scenarios',
            'total_scenarios': len(scenarios),
            'version': '1.0'
        },
        'scenarios': scenarios
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Saved {len(scenarios)} scenarios to {output_path}")


def main():
    # Paths
    notebook_path = Path('cosmichost_mp.ipynb')
    output_path = Path('static/scenarios.json')

    if not notebook_path.exists():
        print(f"Error: Notebook not found: {notebook_path}")
        sys.exit(1)

    print(f"Extracting scenarios from {notebook_path}...")

    try:
        # Extract from notebook
        scenarios = extract_scenarios_from_notebook(notebook_path)
        print(f"✓ Extracted {len(scenarios)} scenarios")

        # Clean data
        cleaned_scenarios = clean_scenario_data(scenarios)
        print(f"✓ Cleaned scenario data")

        # Save to JSON
        save_scenarios_json(cleaned_scenarios, output_path)

        # Summary
        print(f"\nScenario Summary:")
        for s in cleaned_scenarios[:5]:  # Show first 5
            print(f"  {s['id']:2d}. {s['title']}")
        if len(cleaned_scenarios) > 5:
            print(f"  ... and {len(cleaned_scenarios) - 5} more")

        print(f"\n✓ Success! Scenarios exported to {output_path.absolute()}")

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
