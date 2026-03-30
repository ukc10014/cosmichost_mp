#!/usr/bin/env python3
"""
Run Newcomb-like eval on Qwen3-32B in both non-thinking and thinking modes.

Tests whether Qwen3-32B thinking mode shows higher EDT preference,
as predicted by Oesterheld et al. (2024) findings on reasoning models.

Usage:
    source .venv/bin/activate
    python run_qwen3_32b_eval.py                  # Quick test (5 questions)
    python run_qwen3_32b_eval.py --full            # Full 81 attitude questions
    python run_qwen3_32b_eval.py --full --thinking-only  # Only thinking mode
    python run_qwen3_32b_eval.py --full --no-thinking-only  # Only non-thinking
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from newcomblike_eval import load_questions, run_evaluation, print_summary, save_results

OPENROUTER_MODEL = "qwen/qwen3-32b"
CONSTITUTION_PATH = Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md")
TEMPERATURE = 0.7


def make_qwen3_call(api_key: str, thinking: bool):
    """Create an LLM call function for Qwen3-32B with or without thinking."""
    mode_label = "thinking" if thinking else "no-thinking"

    def llm_call(messages, **kwargs):
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/cosmichost",
        }

        payload = {
            "model": OPENROUTER_MODEL,
            "messages": messages,
            "temperature": TEMPERATURE,
        }

        if thinking:
            payload["max_tokens"] = 8192
        else:
            payload["reasoning"] = {"effort": "none"}
            payload["max_tokens"] = 4096
            payload["provider"] = {"order": ["Together", "Fireworks", "DeepInfra"]}

        timeout = 120 if thinking else 60

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                return content
            return ""

        except Exception as e:
            print(f"\n  API error: {e}")
            time.sleep(2)
            raise

    return llm_call


def load_constitution():
    if not CONSTITUTION_PATH.exists():
        print(f"ERROR: Constitution not found at {CONSTITUTION_PATH}")
        sys.exit(1)
    with open(CONSTITUTION_PATH) as f:
        return f.read()


def run_condition(llm_call, questions, model_label, constitution=None, constitution_id=None):
    """Run one eval condition and save results."""
    run = run_evaluation(
        model=model_label,
        llm_call_fn=llm_call,
        constitution=constitution,
        constitution_id=constitution_id,
        questions=questions,
        verbose=True,
    )
    print_summary(run)
    save_results(run)
    return run


def main():
    parser = argparse.ArgumentParser(description="Qwen3-32B Newcomb-like eval")
    parser.add_argument("--full", action="store_true", help="Full 81 attitude questions")
    parser.add_argument("-n", type=int, default=5, help="Questions for quick test (default: 5)")
    parser.add_argument("--thinking-only", action="store_true", help="Only run thinking mode")
    parser.add_argument("--no-thinking-only", action="store_true", help="Only run non-thinking mode")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline, only run ECL90")
    args = parser.parse_args()

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in .env")
        sys.exit(1)
    api_key = api_key.strip().strip('"').strip("'")
    print(f"OpenRouter API key loaded")

    questions = load_questions(attitude_only=True)
    if not args.full:
        questions = questions[:args.n]

    constitution = load_constitution()

    print(f"\nQwen3-32B Newcomb-like Evaluation")
    print(f"Questions: {len(questions)}")
    print(f"=" * 60)

    results = {}

    modes = []
    if not args.thinking_only:
        modes.append(("no-thinking", False))
    if not args.no_thinking_only:
        modes.append(("thinking", True))

    for mode_name, thinking in modes:
        model_label = f"qwen/qwen3-32b-{mode_name}"
        llm_call = make_qwen3_call(api_key, thinking=thinking)

        print(f"\n{'='*60}")
        print(f"MODE: {mode_name.upper()}")
        print(f"{'='*60}")

        if not args.skip_baseline:
            print(f"\n--- Baseline (no constitution) ---")
            results[f"{mode_name}_baseline"] = run_condition(
                llm_call, questions, model_label, constitution=None, constitution_id=None
            )
            time.sleep(2)

        print(f"\n--- ECL 90% constitution ---")
        results[f"{mode_name}_ecl90"] = run_condition(
            llm_call, questions, model_label, constitution=constitution, constitution_id="ecl90"
        )
        time.sleep(2)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"\n{'Condition':<35s} {'EDT':>6s} {'CDT':>6s} {'Parse':>6s}")
    print("-" * 55)
    for label, run in results.items():
        att = [r for r in run.results if r.question.is_attitude]
        edt = sum(1 for r in att if r.is_edt_aligned)
        cdt = sum(1 for r in att if r.is_cdt_aligned)
        parse_err = sum(1 for r in att if r.parse_error)
        total = len(att)
        print(f"{label:<35s} {edt:>3d}/{total} {cdt:>3d}/{total} {parse_err:>3d}/{total}")


if __name__ == "__main__":
    main()
