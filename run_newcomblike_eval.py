#!/usr/bin/env python3
"""
Standalone runner for Newcomb-like evaluation on multiple models.

Compares baseline (no constitution) vs ECL 90% constitution on decision-theoretic
reasoning questions from the Oesterheld et al. (2024) dataset.

Supported models:
    - Gemini: gemini-3-flash-preview, gemini-3-pro-preview, etc.
    - OpenAI: gpt-5.1, gpt-4o, o1-preview, etc.
    - Anthropic: claude-opus-4-5-20251101, claude-sonnet-4-20250514, etc.
    - OpenRouter: moonshotai/kimi-k2-0905, qwen/qwen3-235b-a22b-2507, etc.

Usage:
    # First activate the virtual environment
    source .venv/bin/activate

    # Quick test (default: 5 attitude questions)
    python run_newcomblike_eval.py

    # Full attitude comparison (81 questions, ~10 min)
    python run_newcomblike_eval.py --full

    # ECL/multiagent questions only (66 questions)
    python run_newcomblike_eval.py --ecl

    # All questions (353 questions)
    python run_newcomblike_eval.py --all

    # Custom number of questions
    python run_newcomblike_eval.py -n 20

    # Different Gemini model
    python run_newcomblike_eval.py --model gemini-3-pro-preview

    # OpenAI models (GPT-5.1, etc.)
    python run_newcomblike_eval.py --model gpt-5.1

    # Anthropic models (Claude Opus, etc.)
    python run_newcomblike_eval.py --model claude-opus-4-5-20251101

    # OpenRouter models (Kimi K2, Qwen, etc.)
    python run_newcomblike_eval.py --model moonshotai/kimi-k2-0905
    python run_newcomblike_eval.py --model qwen/qwen3-235b-a22b-2507

    # Resume interrupted ECL run (skip baseline)
    python run_newcomblike_eval.py --full --skip-baseline --model gemini-3-pro-preview

Output:
    - Prints EDT/CDT alignment rates for baseline and ECL 90%
    - Saves detailed results to logs/newcomblike_evals/

Constitution:
    Uses ECL 90% constitution from: logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md

Dataset:
    Oesterheld et al. (2024) - https://arxiv.org/abs/2411.10588
    353 decision-theoretic questions (272 capabilities, 81 attitude)
"""

import os
import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from newcomblike_eval import (
    load_questions,
    run_evaluation,
    print_summary,
    save_results,
    Question
)

from llm_providers import (
    init_llm_call,
    is_gemini_model, is_openai_model, is_anthropic_model, is_openrouter_model,
    TEMPERATURE,
)

# Configuration
MODEL = "gemini-3-flash-preview"
CONSTITUTION_PATH = Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md")


def load_constitution():
    """Load the ECL 90% constitution."""
    if not CONSTITUTION_PATH.exists():
        print(f"ERROR: Constitution not found at {CONSTITUTION_PATH}")
        sys.exit(1)

    with open(CONSTITUTION_PATH) as f:
        return f.read()


def run_comparison(llm_call, subset: str = "attitude", max_questions: int = None, skip_baseline: bool = False):
    """Run baseline vs ECL90 comparison."""

    # Load questions
    if subset == "attitude":
        questions = load_questions(attitude_only=True)
    elif subset == "ecl":
        questions = load_questions(tags_filter=['ECL', 'multiagent'])
    else:
        questions = load_questions()

    if max_questions:
        questions = questions[:max_questions]

    print(f"\nLoaded {len(questions)} questions")
    att_count = sum(1 for q in questions if q.is_attitude)
    cap_count = len(questions) - att_count
    print(f"  Attitude: {att_count}, Capabilities: {cap_count}")

    constitution = load_constitution()

    baseline = None
    if not skip_baseline:
        # Run baseline
        print("\n" + "=" * 60)
        print("BASELINE (no constitution)")
        print("=" * 60)

        baseline = run_evaluation(
            model=MODEL,
            llm_call_fn=llm_call,
            constitution=None,
            constitution_id=None,
            questions=questions,
            verbose=True
        )
        print_summary(baseline)
        save_results(baseline)

        # Small delay between runs
        time.sleep(2)
    else:
        print("\n[Skipping baseline - use existing results]")

    # Run with ECL90
    print("\n" + "=" * 60)
    print("WITH ECL 90% CONSTITUTION")
    print("=" * 60)

    ecl90 = run_evaluation(
        model=MODEL,
        llm_call_fn=llm_call,
        constitution=constitution,
        constitution_id="ecl90",
        questions=questions,
        verbose=True
    )
    print_summary(ecl90)
    save_results(ecl90)

    # Print comparison (only if we have baseline)
    if baseline:
        print("\n" + "=" * 60)
        print("COMPARISON: Baseline → ECL 90%")
        print("=" * 60)

        if att_count > 0:
            print(f"\nAttitude questions (EDT vs CDT preference):")
            print(f"  EDT rate: {100*baseline.edt_rate:.1f}% → {100*ecl90.edt_rate:.1f}% (Δ {100*(ecl90.edt_rate - baseline.edt_rate):+.1f}%)")
            print(f"  CDT rate: {100*baseline.cdt_rate:.1f}% → {100*ecl90.cdt_rate:.1f}% (Δ {100*(ecl90.cdt_rate - baseline.cdt_rate):+.1f}%)")

            if ecl90.edt_rate > baseline.edt_rate + 0.05:
                print("\n  ✓ Constitution shifts toward EDT (expected for ECL)")
            elif ecl90.edt_rate < baseline.edt_rate - 0.05:
                print("\n  ✗ Constitution shifts toward CDT (unexpected)")
            else:
                print("\n  ≈ Minimal shift in EDT/CDT preference")

        if cap_count > 0:
            print(f"\nCapabilities (correct DT reasoning):")
            print(f"  Accuracy: {100*baseline.capabilities_correct:.1f}% → {100*ecl90.capabilities_correct:.1f}% (Δ {100*(ecl90.capabilities_correct - baseline.capabilities_correct):+.1f}%)")

    return baseline, ecl90


def main():
    global MODEL

    parser = argparse.ArgumentParser(description="Run Newcomb-like evaluation")
    parser.add_argument("--full", action="store_true", help="Run full attitude comparison (81 questions)")
    parser.add_argument("--ecl", action="store_true", help="Run ECL/multiagent questions (66 questions)")
    parser.add_argument("--all", action="store_true", help="Run all questions (353)")
    parser.add_argument("-n", type=int, default=5, help="Number of questions for quick test (default: 5)")
    parser.add_argument("--model", type=str, default=MODEL, help=f"Model to use (default: {MODEL})")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline, only run ECL90 (for resume)")
    args = parser.parse_args()

    MODEL = args.model

    print("Newcomb-like Decision Theory Evaluation")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Constitution: {CONSTITUTION_PATH}")

    llm_call = init_llm_call(MODEL)

    # Determine what to run
    if args.full:
        subset = "attitude"
        max_q = None
    elif args.ecl:
        subset = "ecl"
        max_q = None
    elif args.all:
        subset = "all"
        max_q = None
    else:
        subset = "attitude"
        max_q = args.n
        print(f"\nQuick test mode: {max_q} questions")
        print("Use --full for complete evaluation")

    # Run comparison
    baseline, ecl90 = run_comparison(llm_call, subset=subset, max_questions=max_q, skip_baseline=args.skip_baseline)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
