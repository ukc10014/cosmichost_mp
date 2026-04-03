#!/usr/bin/env python3
"""Generate Newcomb-like scenarios via OpenRouter (Chinese models for diversity)."""

import json
import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / ".env")
if not load_dotenv(Path(__file__).parent.parent.parent / ".env"):
    load_dotenv(Path(__file__).parent.parent / ".env")

API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not found in .env")

MODELS = [
    "qwen/qwen3-235b-a22b",
    "deepseek/deepseek-r1",
]

PROMPT = (Path(__file__).parent / "scenario_generation_prompt.md").read_text()
prompt_text = PROMPT.split("## Prompt\n\n", 1)[1]

OUTPUT_FILE = Path(__file__).parent / "generated_newcombs_chinese_models.json"


def query_openrouter(model: str, prompt: str) -> str:
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.9,
            "max_tokens": 8192,
        },
        timeout=300,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


def extract_json_lines(text: str) -> list[dict]:
    results = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or not line.startswith("{"):
            continue
        try:
            obj = json.loads(line)
            if "scenario" in obj and "edt_answer" in obj:
                results.append(obj)
        except json.JSONDecodeError:
            continue
    return results


def main():
    all_scenarios = []

    for model in MODELS:
        print(f"\nQuerying {model}...")
        try:
            raw = query_openrouter(model, prompt_text)
            scenarios = extract_json_lines(raw)
            print(f"  Got {len(scenarios)} valid scenarios")

            if len(scenarios) < 5:
                print(f"  Low yield. Raw response (first 500 chars):")
                print(f"  {raw[:500]}")

            for s in scenarios:
                s["source_model"] = model
            all_scenarios.extend(scenarios)

        except Exception as e:
            print(f"  Error: {e}")

    with open(OUTPUT_FILE, "w") as f:
        for s in all_scenarios:
            f.write(json.dumps(s) + "\n")

    cats = {}
    for s in all_scenarios:
        cat = s.get("category", "unknown")
        cats[cat] = cats.get(cat, 0) + 1

    print(f"\nTotal: {len(all_scenarios)} scenarios -> {OUTPUT_FILE.name}")
    print("Categories:", dict(sorted(cats.items())))


if __name__ == "__main__":
    main()
