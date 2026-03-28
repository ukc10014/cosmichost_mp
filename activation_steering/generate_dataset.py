#!/usr/bin/env python3
"""
Generate expanded DT activation steering dataset from base scenarios.

Takes base_scenarios.json and produces:
  - datasets/generated/dt_steering_full.jsonl  (all prompts)
  - datasets/generated/dt_steering_train.jsonl (train split)
  - datasets/generated/dt_steering_val.jsonl   (validation split)
  - datasets/generated/dt_steering_test.jsonl  (test split)

Each base scenario is expanded across question formats, producing
~5 prompts per scenario. Contrastive completion pairs are preserved
for mean-difference direction extraction.

Usage:
    python generate_dataset.py                    # Generate full dataset
    python generate_dataset.py --stats            # Print statistics only
    python generate_dataset.py --category newcomb_proper  # Filter by category
"""

import json
import hashlib
import argparse
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).parent / "datasets"
SCENARIOS_PATH = BASE_DIR / "base_scenarios.json"
OUTPUT_DIR = BASE_DIR / "generated"

QUESTION_FORMATS = {
    "forced_choice": {
        "suffix": "",
        "instruction": "Answer with your choice only.",
    },
    "justified": {
        "suffix": "\n\nExplain your reasoning in 2-3 sentences, then state your final choice.",
        "instruction": "",
    },
    "policy": {
        "suffix": "\n\nRather than thinking about what to do in this specific instance, consider: what general policy should an agent adopt for situations with this structure? State the policy and then apply it to make your choice.",
        "instruction": "",
    },
    "population": {
        "suffix": "\n\nImagine a large population of reasoners similar to you all facing this same choice independently. What should they do? Apply that reasoning to make your own choice.",
        "instruction": "",
    },
    "ranking": {
        "suffix": "\n\nRank the following principles by how relevant they are to this decision, then use the most relevant one to make your choice:\n- Act to maximize causal consequences of your specific action\n- Act as if your choice determines what all similar reasoners choose\n- Choose the policy you'd want to commit to before learning the specifics\n- Choose based on what your action is evidence for",
        "instruction": "",
    },
}


def load_scenarios(category_filter: Optional[str] = None) -> list[dict]:
    with open(SCENARIOS_PATH) as f:
        data = json.load(f)

    scenarios = data["scenarios"]
    if category_filter:
        scenarios = [s for s in scenarios if s["category"] == category_filter]

    return scenarios


def make_prompt(scenario: dict, fmt_key: str) -> str:
    """Build the full prompt text for a scenario + question format."""
    parts = [scenario["scenario"]]

    fmt = QUESTION_FORMATS[fmt_key]

    if fmt_key == "forced_choice":
        parts.append(f"\n\n{scenario['forced_choice_prompt']}")
        parts.append(f"\n{fmt['instruction']}")
    else:
        parts.append(f"\n\n{scenario['forced_choice_prompt']}")
        parts.append(fmt["suffix"])

    return "".join(parts)


def assign_split(scenario_id: str, fmt_key: str) -> str:
    """Deterministic train/val/test split based on scenario ID.

    Split is by scenario, not by prompt — all formats of the same
    scenario go to the same split. This prevents data leakage.

    Ratio: 60% train, 20% val, 20% test.
    """
    h = int(hashlib.md5(scenario_id.encode()).hexdigest(), 16)
    bucket = h % 10
    if bucket < 6:
        return "train"
    elif bucket < 8:
        return "val"
    else:
        return "test"


def expand_scenario(scenario: dict) -> list[dict]:
    """Expand a single base scenario into multiple prompts."""
    prompts = []

    for fmt_key in QUESTION_FORMATS:
        prompt_text = make_prompt(scenario, fmt_key)
        prompt_id = f"{scenario['id']}_{fmt_key}"
        split = assign_split(scenario["id"], fmt_key)

        record = {
            "prompt_id": prompt_id,
            "scenario_id": scenario["id"],
            "category": scenario["category"],
            "subcategory": scenario.get("subcategory", ""),
            "title": scenario["title"],
            "prompt": prompt_text,
            "question_format": fmt_key,
            "options": scenario["options"],
            "edt_answer_idx": scenario["edt_answer_idx"],
            "cdt_answer_idx": scenario["cdt_answer_idx"],
            "edt_completion": scenario.get("edt_completion", ""),
            "cdt_completion": scenario.get("cdt_completion", ""),
            "tags": scenario.get("tags", {}),
            "confound_flags": scenario.get("confound_flags", {}),
            "split": split,
        }

        prompts.append(record)

    return prompts


def generate_dataset(category_filter: Optional[str] = None) -> list[dict]:
    """Generate the full expanded dataset."""
    scenarios = load_scenarios(category_filter)
    all_prompts = []

    for scenario in scenarios:
        expanded = expand_scenario(scenario)
        all_prompts.append(expanded)

    flat = [p for group in all_prompts for p in group]
    return flat


def save_dataset(prompts: list[dict]):
    """Save dataset as JSONL, split into train/val/test."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    full_path = OUTPUT_DIR / "dt_steering_full.jsonl"
    with open(full_path, "w") as f:
        for p in prompts:
            f.write(json.dumps(p) + "\n")

    for split_name in ["train", "val", "test"]:
        split_prompts = [p for p in prompts if p["split"] == split_name]
        split_path = OUTPUT_DIR / f"dt_steering_{split_name}.jsonl"
        with open(split_path, "w") as f:
            for p in split_prompts:
                f.write(json.dumps(p) + "\n")

    return full_path


def print_stats(prompts: list[dict]):
    """Print dataset statistics."""
    print(f"\n{'='*60}")
    print(f"DT ACTIVATION STEERING DATASET")
    print(f"{'='*60}")
    print(f"\nTotal prompts: {len(prompts)}")

    categories = {}
    for p in prompts:
        cat = p["category"]
        categories[cat] = categories.get(cat, 0) + 1
    print(f"\nBy category:")
    for cat, count in sorted(categories.items()):
        n_scenarios = len(set(p["scenario_id"] for p in prompts if p["category"] == cat))
        print(f"  {cat}: {count} prompts ({n_scenarios} base scenarios)")

    subcats = {}
    for p in prompts:
        key = f"{p['category']}/{p['subcategory']}"
        subcats[key] = subcats.get(key, 0) + 1
    print(f"\nBy subcategory:")
    for key, count in sorted(subcats.items()):
        print(f"  {key}: {count}")

    formats = {}
    for p in prompts:
        fmt = p["question_format"]
        formats[fmt] = formats.get(fmt, 0) + 1
    print(f"\nBy question format:")
    for fmt, count in sorted(formats.items()):
        print(f"  {fmt}: {count}")

    splits = {}
    for p in prompts:
        s = p["split"]
        splits[s] = splits.get(s, 0) + 1
    print(f"\nBy split:")
    for s in ["train", "val", "test"]:
        print(f"  {s}: {splits.get(s, 0)}")

    edt_cdt_agree = sum(1 for p in prompts if p.get("confound_flags", {}).get("edt_cdt_agree"))
    edt_cdt_disagree = sum(1 for p in prompts if p["edt_answer_idx"] != p["cdt_answer_idx"])
    print(f"\nContrastive analysis:")
    print(f"  EDT/CDT disagree: {edt_cdt_disagree} prompts (useful for direction extraction)")
    print(f"  EDT/CDT agree: {edt_cdt_agree} prompts (controls)")

    tag_counts = {}
    for p in prompts:
        for tag, val in p.get("tags", {}).items():
            if val is True:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    print(f"\nTag distribution:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"  {tag}: {count}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Generate DT steering dataset")
    parser.add_argument("--stats", action="store_true", help="Print stats only, don't regenerate")
    parser.add_argument("--category", type=str, help="Filter by category")
    args = parser.parse_args()

    if args.stats:
        full_path = OUTPUT_DIR / "dt_steering_full.jsonl"
        if not full_path.exists():
            print("No dataset found. Run without --stats first.")
            return
        prompts = []
        with open(full_path) as f:
            for line in f:
                prompts.append(json.loads(line))
        print_stats(prompts)
        return

    prompts = generate_dataset(args.category)
    output_path = save_dataset(prompts)
    print_stats(prompts)
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    main()
