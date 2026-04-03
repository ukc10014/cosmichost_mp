#!/usr/bin/env python3
"""
Build LoRA training datasets v2 from all scenario sources.

Reads:
  - datasets/lora_edt/train.jsonl (original 55 scenarios × 5 framings)
  - generated_newcombs.json (40 scenarios from GPT-5.4, Gemini 2 Pro)
  - generated_newcombs_chinese_models.json (20 Qwen3-235B + 20 DeepSeek-R1)

Writes to datasets/lora_edt_v2/ and datasets/lora_cdt_v2/
  - train.jsonl, valid.jsonl, test.jsonl

Does NOT modify the original datasets.
"""

import json
import random
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).parent
DATASETS_DIR = BASE_DIR / "datasets"

FRAMING_SUFFIXES = [
    "\nAnswer with your choice only.",
    "\n\nExplain your reasoning in 2-3 sentences, then state your final choice.",
    "\n\nRather than thinking about what to do in this specific instance, consider: what general policy should an agent adopt for situations with this structure? State the policy and then apply it to make your choice.",
    "\n\nImagine a large population of reasoners similar to you all facing this same choice independently. What should they do? Apply that reasoning to make your own choice.",
    "\n\nRank the following principles by how relevant they are to this decision, then use the most relevant one to make your choice:\n- Act to maximize causal consequences of your specific action\n- Act as if your choice determines what all similar reasoners choose\n- Choose the policy you'd want to commit to before learning the specifics\n- Choose based on what your action is evidence for",
]


def load_original_scenarios() -> list[dict]:
    """Extract unique scenarios from original training data."""
    seen = {}
    with open(DATASETS_DIR / "lora_edt" / "train.jsonl") as f_edt, \
         open(DATASETS_DIR / "lora_cdt" / "train.jsonl") as f_cdt:
        edt_lines = [json.loads(l) for l in f_edt]
        cdt_lines = [json.loads(l) for l in f_cdt]

    for edt_row, cdt_row in zip(edt_lines, cdt_lines):
        base = edt_row["prompt"].split("\n")[0]
        if base not in seen:
            question_line = edt_row["prompt"].split("\n")[1] if "\n" in edt_row["prompt"] else ""
            seen[base] = {
                "scenario": base,
                "question_line": question_line,
                "edt_answer": edt_row["completion"],
                "cdt_answer": cdt_row["completion"],
                "source": "original",
            }
    return list(seen.values())


def load_generated(path: Path, source_label: str) -> list[dict]:
    results = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            scenario_text = obj["scenario"]
            results.append({
                "scenario": scenario_text,
                "question_line": "",
                "edt_answer": obj["edt_answer"],
                "cdt_answer": obj["cdt_answer"],
                "source": obj.get("source_model", source_label),
            })
    return results


def expand_scenario(scenario: dict) -> list[dict]:
    """Create 5 framing variants for a scenario."""
    base_text = scenario["scenario"]
    rows = []
    for suffix in FRAMING_SUFFIXES:
        prompt = base_text + suffix
        rows.append({
            "prompt": prompt,
            "edt_completion": scenario["edt_answer"],
            "cdt_completion": scenario["cdt_answer"],
        })
    return rows


def write_split(rows: list[dict], out_dir: Path, theory: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    key = "edt_completion" if theory == "edt" else "cdt_completion"
    path = out_dir / "train.jsonl"
    if path.name == "train.jsonl":
        pass
    with open(out_dir / "train.jsonl", "w") as f_train, \
         open(out_dir / "valid.jsonl", "w") as f_valid, \
         open(out_dir / "test.jsonl", "w") as f_test:

        for split, fh in [("train", f_train), ("valid", f_valid), ("test", f_test)]:
            split_rows = [r for r in rows if r["_split"] == split]
            for r in split_rows:
                obj = {"prompt": r["prompt"], "completion": r[key]}
                fh.write(json.dumps(obj) + "\n")


def main():
    original = load_original_scenarios()
    generated_1 = load_generated(BASE_DIR / "generated_newcombs.json", "user_generated")
    generated_2 = load_generated(BASE_DIR / "generated_newcombs_chinese_models.json", "chinese")

    all_scenarios = original + generated_1 + generated_2
    random.shuffle(all_scenarios)

    n = len(all_scenarios)
    n_test = max(10, int(n * 0.10))
    n_valid = max(5, int(n * 0.05))
    n_train = n - n_test - n_valid

    print(f"Total scenarios: {n}")
    print(f"  Train: {n_train} scenarios = {n_train * 5} examples")
    print(f"  Valid: {n_valid} scenarios = {n_valid * 5} examples")
    print(f"  Test:  {n_test} scenarios = {n_test * 5} examples")

    all_rows = []
    for i, scenario in enumerate(all_scenarios):
        if i < n_train:
            split = "train"
        elif i < n_train + n_valid:
            split = "valid"
        else:
            split = "test"

        expanded = expand_scenario(scenario)
        for row in expanded:
            row["_split"] = split
        all_rows.extend(expanded)

    for theory in ["edt", "cdt"]:
        out_dir = DATASETS_DIR / f"lora_{theory}_v2"
        write_split(all_rows, out_dir, theory)
        train_count = sum(1 for r in all_rows if r["_split"] == "train")
        valid_count = sum(1 for r in all_rows if r["_split"] == "valid")
        test_count = sum(1 for r in all_rows if r["_split"] == "test")
        print(f"\n  {out_dir.name}/")
        print(f"    train.jsonl: {train_count}")
        print(f"    valid.jsonl: {valid_count}")
        print(f"    test.jsonl:  {test_count}")

    source_counts = {}
    for s in all_scenarios:
        src = s["source"]
        source_counts[src] = source_counts.get(src, 0) + 1
    print(f"\nSource breakdown:")
    for src, count in sorted(source_counts.items()):
        print(f"  {src}: {count}")


if __name__ == "__main__":
    main()
