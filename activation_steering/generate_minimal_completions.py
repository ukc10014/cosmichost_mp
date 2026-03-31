#!/usr/bin/env python3
"""
Generate a minimal-completion version of the DT steering dataset.

Replaces the full EDT/CDT completions with just the answer text
(e.g., "Take only Box B" instead of a multi-sentence justification).
This controls for vocabulary leakage: if probes still work at later
layers with only the answer tokens differing, the model represents
something structural about the prompt-answer relationship.

Usage:
    python activation_steering/generate_minimal_completions.py
    python activation_steering/generate_minimal_completions.py --stats
"""

import json
import argparse
from pathlib import Path

INPUT_PATH = Path(__file__).parent / "datasets" / "generated" / "dt_steering_full.jsonl"
OUTPUT_DIR = Path(__file__).parent / "datasets" / "generated"


def main():
    parser = argparse.ArgumentParser(description="Generate minimal-completion dataset")
    parser.add_argument("--stats", action="store_true", help="Print stats only")
    args = parser.parse_args()

    with open(INPUT_PATH) as f:
        prompts = [json.loads(line) for line in f]

    minimal = []
    for p in prompts:
        m = dict(p)
        edt_option = p["options"][p["edt_answer_idx"]]
        cdt_option = p["options"][p["cdt_answer_idx"]]
        m["edt_completion"] = edt_option
        m["cdt_completion"] = cdt_option
        m["completion_type"] = "minimal"
        minimal.append(m)

    contrastive = [p for p in minimal if p["edt_answer_idx"] != p["cdt_answer_idx"]]

    if args.stats:
        print(f"Total prompts: {len(minimal)}")
        print(f"Contrastive: {len(contrastive)}")
        print(f"\nSample completions:")
        for p in contrastive[:5]:
            print(f"  {p['scenario_id']:40s}")
            print(f"    EDT: \"{p['edt_completion']}\"")
            print(f"    CDT: \"{p['cdt_completion']}\"")
        return

    output_path = OUTPUT_DIR / "dt_steering_minimal.jsonl"
    with open(output_path, "w") as f:
        for p in minimal:
            f.write(json.dumps(p) + "\n")

    print(f"Wrote {len(minimal)} prompts to {output_path}")
    print(f"Contrastive: {len(contrastive)}")
    print(f"\nSample:")
    for p in contrastive[:3]:
        print(f"  {p['scenario_id']}: \"{p['edt_completion']}\" vs \"{p['cdt_completion']}\"")


if __name__ == "__main__":
    main()
