#!/usr/bin/env python3
"""
Aggregate multiple runs from scenario evaluation JSONL files.

This script processes JSONL output files from run_experiment() that contain
multiple runs per scenario (when num_runs > 1). It computes majority votes
for first choice preferences and generates summary statistics.

Usage:
    python3 aggregate_runs.py input.jsonl --output aggregated.jsonl
    python3 aggregate_runs.py input.jsonl --stats-only
    python3 aggregate_runs.py input.jsonl -o aggregated.jsonl

Examples:
    # Quick stats check
    python3 aggregate_runs.py results_tmp/constitutional_evaluation_gemini.jsonl --stats-only

    # Generate aggregated file
    python3 aggregate_runs.py results_tmp/constitutional_evaluation_gemini.jsonl \\
        --output logs/mp_scen_evals/gemini3/aggregated_ecl_n5.jsonl
"""

import json
import argparse
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
from pathlib import Path


def load_jsonl(file_path: str) -> Tuple[Optional[Dict], List[Dict]]:
    """
    Load JSONL file and separate header from data records.

    Args:
        file_path: Path to JSONL file

    Returns:
        Tuple of (header_dict, list_of_result_records)
        header_dict will be None if no header found
    """
    header = None
    results = []

    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            data = json.loads(line)

            if data.get('_type') == 'header':
                header = data
            elif data.get('_type') == 'error':
                continue  # Skip error records
            else:
                # Regular result record
                results.append(data)

    return header, results


def aggregate_runs(results: List[Dict]) -> List[Dict]:
    """
    Group results by (scenario_id, condition, model_name) and compute majority votes.

    Args:
        results: List of individual run records from JSONL

    Returns:
        List of aggregated records with majority votes
    """
    # Group by (scenario_id, scenario_tag, condition, model_name)
    grouped = defaultdict(list)

    for result in results:
        key = (
            result['scenario_id'],
            result.get('scenario_tag', f"scenario_{result['scenario_id']}"),
            result['condition'],
            result['model_name']
        )
        grouped[key].append(result)

    # Compute majority for each group
    aggregated = []

    for (scenario_id, scenario_tag, condition, model_name), runs in grouped.items():
        # Sort by run_number for consistency
        runs = sorted(runs, key=lambda r: r.get('run_number', 0))

        # Filter successful runs
        successful_runs = [r for r in runs if r.get('parse_success', False)]
        failed_runs = len(runs) - len(successful_runs)

        # Count first choice votes
        if successful_runs:
            choice_votes = Counter(r['first_choice_type'] for r in successful_runs)
            majority_choice, majority_count = choice_votes.most_common(1)[0]
            consensus_level = majority_count / len(successful_runs)
            all_agree = (consensus_level == 1.0)
        else:
            # All runs failed
            choice_votes = {}
            majority_choice = None
            majority_count = 0
            consensus_level = 0.0
            all_agree = False

        # Build aggregated record
        agg_record = {
            "scenario_id": scenario_id,
            "scenario_tag": scenario_tag,
            "condition": condition,
            "model_name": model_name,
            "num_runs": len(runs),
            "successful_runs": len(successful_runs),
            "failed_runs": failed_runs,
            "first_choice_votes": dict(choice_votes),
            "majority_first_choice": majority_choice,
            "majority_count": majority_count,
            "consensus_level": round(consensus_level, 3),
            "all_runs_agree": all_agree
        }

        aggregated.append(agg_record)

    # Sort by scenario_id for readability
    aggregated.sort(key=lambda x: x['scenario_id'])

    return aggregated


def print_stats(aggregated: List[Dict], header: Optional[Dict]):
    """Print summary statistics about aggregated results."""
    total = len(aggregated)

    if total == 0:
        print("No aggregated results to display.")
        return

    # Calculate stats
    perfect_consensus = sum(1 for a in aggregated if a['all_runs_agree'])
    avg_consensus = sum(a['consensus_level'] for a in aggregated) / total
    split_decisions = sum(1 for a in aggregated if a['consensus_level'] < 0.5)

    failed_scenarios = sum(1 for a in aggregated if a['majority_first_choice'] is None)
    total_runs = sum(a['num_runs'] for a in aggregated)
    total_successful = sum(a['successful_runs'] for a in aggregated)

    print("\n" + "="*60)
    print("AGGREGATION SUMMARY")
    print("="*60)

    if header:
        print(f"Experiment: {header.get('experiment_name', 'N/A')}")
        print(f"Model: {header.get('model_name', 'N/A')}")
        conditions = header.get('conditions', [])
        if isinstance(conditions, list):
            print(f"Conditions: {', '.join(conditions)}")
        else:
            print(f"Conditions: {conditions}")
        print(f"Original num_runs setting: {header.get('num_runs', 'N/A')}")
        print(f"Temperature: {header.get('temperature', 'N/A')}")

    print(f"\nTotal scenario/condition pairs: {total}")
    print(f"Total runs across all: {total_runs}")
    if total_runs > 0:
        success_rate = total_successful / total_runs * 100
        print(f"Successful runs: {total_successful}/{total_runs} ({success_rate:.1f}%)")
    else:
        print(f"Successful runs: {total_successful}/{total_runs}")

    print(f"\nConsensus Statistics:")
    print(f"  Average consensus: {avg_consensus*100:.1f}%")
    print(f"  Perfect consensus (100%): {perfect_consensus}/{total}")
    print(f"  Split decisions (<50%): {split_decisions}/{total}")
    print(f"  All runs failed: {failed_scenarios}/{total}")

    # Choice distribution
    print(f"\nMajority Choice Distribution:")
    choice_counts = Counter(a['majority_first_choice'] for a in aggregated if a['majority_first_choice'])
    if choice_counts:
        for choice, count in choice_counts.most_common():
            print(f"  {choice}: {count}/{total} ({count/total*100:.1f}%)")
    else:
        print("  (no successful runs)")

    print("="*60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Aggregate multiple runs from JSONL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick stats check
  python3 aggregate_runs.py results_tmp/constitutional_evaluation_gemini.jsonl --stats-only

  # Generate aggregated file
  python3 aggregate_runs.py results_tmp/constitutional_evaluation_gemini.jsonl \\
      --output logs/mp_scen_evals/gemini3/aggregated_ecl_n5.jsonl
        """
    )
    parser.add_argument('input', type=str, help='Input JSONL file with multiple runs')
    parser.add_argument('--output', '-o', type=str, help='Output JSONL file for aggregated results')
    parser.add_argument('--stats-only', action='store_true', help='Print stats without writing output')

    args = parser.parse_args()

    # Validate input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    # Load data
    print(f"Loading {args.input}...")
    try:
        header, results = load_jsonl(args.input)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in input file: {e}")
        return 1
    except Exception as e:
        print(f"Error loading file: {e}")
        return 1

    if not results:
        print("No results found in input file.")
        return 1

    print(f"Loaded {len(results)} result records")

    # Check if multiple runs exist
    run_numbers = set(r.get('run_number', 0) for r in results)
    if len(run_numbers) <= 1:
        print("Warning: Only single runs detected (run_number=0 for all). Nothing to aggregate.")
        print("This script is intended for files with num_runs > 1.")
        return 0

    print(f"Detected {len(run_numbers)} runs per scenario/condition")

    # Aggregate
    print("Computing majority votes...")
    aggregated = aggregate_runs(results)

    # Print stats
    print_stats(aggregated, header)

    # Write output
    if args.output and not args.stats_only:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(output_path, 'w') as f:
                # Write header
                if header:
                    f.write(json.dumps(header) + '\n')

                # Write aggregated records
                for record in aggregated:
                    f.write(json.dumps(record) + '\n')

            print(f"Wrote {len(aggregated)} aggregated records to {args.output}")
        except Exception as e:
            print(f"Error writing output file: {e}")
            return 1

    return 0


if __name__ == '__main__':
    exit(main())
