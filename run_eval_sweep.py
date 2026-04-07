#!/usr/bin/env python3
"""
Batch evaluation sweep across models, constitutions, and eval types.

Runs Newcomb-like, scenario, and de-framed game evaluations across multiple
models to map the EDT/CDT capability surface.

Usage:
    python run_eval_sweep.py                          # All models, all evals
    python run_eval_sweep.py --models gemma4,deepseek-r1
    python run_eval_sweep.py --evals newcomblike,deframed_games
    python run_eval_sweep.py --dry-run                # Show what would run
    python run_eval_sweep.py --smoke-test             # 1 question per model to verify routing
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from llm_providers import init_llm_call

# --- Model registry ---

MODEL_REGISTRY = {
    "gemma4": "google/gemma-4-31b-it",
    "deepseek-r1": "deepseek/deepseek-r1",
    "deepseek-v3": "deepseek/deepseek-v3.2",
    "qwen3.5": "qwen/qwen3.5-plus-02-15",
    "grok4": "x-ai/grok-4-fast",
    "gpt5.4": "gpt-5.4",
    "opus4.6": "claude-opus-4-6",
}

CONSTITUTIONS = ["baseline", "ecl90", "fdt"]

# --- Eval runners ---

def run_newcomblike(model_id: str, llm_call, constitution_id: str, constitution_text: str):
    """Run Newcomb-like EDT/CDT evaluation."""
    from newcomblike_eval import run_evaluation, save_results, print_summary

    print(f"\n--- Newcomb-like [{constitution_id}] ---")
    run = run_evaluation(
        model=model_id,
        llm_call_fn=llm_call,
        constitution=constitution_text if constitution_text else None,
        constitution_id=constitution_id,
        attitude_only=True,
        verbose=True,
    )
    output_path = save_results(run)
    print_summary(run)
    print(f"Saved: {output_path}")
    return run


def run_scenarios(model_id: str, llm_call, constitution_id: str, constitution_text: str):
    """Run scenario-based constitutional evaluation."""
    from run_scenario_eval import (
        load_scenarios, run_scenario_evaluation,
        save_scenario_results, print_scenario_summary,
    )

    print(f"\n--- Scenarios [{constitution_id}] ---")
    scenarios = load_scenarios()
    results, summary = run_scenario_evaluation(
        model=model_id,
        llm_call_fn=llm_call,
        scenarios=scenarios,
        constitution=constitution_text if constitution_text else None,
        constitution_id=constitution_id,
        include_rationale=True,
        verbose=True,
        exclude_option_types=["procedural_democracy"],
    )
    output_path = save_scenario_results(results, summary)
    print_scenario_summary(summary)
    print(f"Saved: {output_path}")
    return summary


def run_deframed_games(model_id: str, llm_call, constitution_id: str, constitution_text: str):
    """Run de-framed stag hunt game evaluation."""
    from game_eval import load_deframed_games, run_game_evaluation, save_results, print_summary

    print(f"\n--- De-framed Games [{constitution_id}] ---")
    games = load_deframed_games()
    run = run_game_evaluation(
        model=model_id,
        llm_call_fn=llm_call,
        games=games,
        constitution=constitution_text if constitution_text else None,
        constitution_id=constitution_id,
        verbose=True,
    )
    output_path = save_results(run)
    print_summary(run)
    print(f"Saved: {output_path}")
    return run


EVAL_RUNNERS = {
    "newcomblike": run_newcomblike,
    "scenarios": run_scenarios,
    "deframed_games": run_deframed_games,
}


# --- Constitution loading ---

CONSTITUTION_PATHS = {
    "ecl90": Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md"),
    "ecl10": Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch10.md"),
    "fdt": Path("static/fdt_only_constitution.txt"),
}


def load_constitution(constitution_id: str) -> str:
    if constitution_id == "baseline":
        return ""
    path = CONSTITUTION_PATHS.get(constitution_id)
    if not path or not path.exists():
        print(f"ERROR: Constitution '{constitution_id}' not found")
        sys.exit(1)
    with open(path) as f:
        return f.read()


# --- Smoke test ---

def smoke_test(model_ids: list[str]):
    """Quick 1-question test per model to verify API routing works."""
    print("=" * 60)
    print("SMOKE TEST: Verifying model routing")
    print("=" * 60)

    test_messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2? Reply with just the number."},
    ]

    for model_id in model_ids:
        print(f"\n  {model_id} ... ", end="", flush=True)
        try:
            llm_call = init_llm_call(model_id)
            response = llm_call(test_messages)
            preview = response.strip()[:80].replace("\n", " ")
            print(f"OK: '{preview}'")
        except Exception as e:
            print(f"FAILED: {e}")

    print("\nSmoke test complete.\n")


# --- Main ---

def main():
    parser = argparse.ArgumentParser(description="Batch evaluation sweep")
    parser.add_argument(
        "--models", default=None,
        help=f"Comma-separated model aliases ({', '.join(MODEL_REGISTRY.keys())})"
    )
    parser.add_argument(
        "--evals", default=None,
        help=f"Comma-separated eval types ({', '.join(EVAL_RUNNERS.keys())})"
    )
    parser.add_argument(
        "--constitutions", default=None,
        help=f"Comma-separated constitutions (default: {', '.join(CONSTITUTIONS)})"
    )
    parser.add_argument("--dry-run", action="store_true", help="Show what would run")
    parser.add_argument("--smoke-test", action="store_true", help="Quick routing test per model")
    args = parser.parse_args()

    if args.models:
        model_aliases = [m.strip() for m in args.models.split(",")]
        model_ids = []
        for alias in model_aliases:
            if alias in MODEL_REGISTRY:
                model_ids.append(MODEL_REGISTRY[alias])
            else:
                model_ids.append(alias)
    else:
        model_ids = list(MODEL_REGISTRY.values())

    eval_types = (
        [e.strip() for e in args.evals.split(",")]
        if args.evals
        else list(EVAL_RUNNERS.keys())
    )

    constitutions = (
        [c.strip() for c in args.constitutions.split(",")]
        if args.constitutions
        else CONSTITUTIONS
    )

    total_runs = len(model_ids) * len(eval_types) * len(constitutions)

    print("Evaluation Sweep")
    print("=" * 60)
    print(f"Models ({len(model_ids)}): {', '.join(model_ids)}")
    print(f"Evals ({len(eval_types)}): {', '.join(eval_types)}")
    print(f"Constitutions ({len(constitutions)}): {', '.join(constitutions)}")
    print(f"Total runs: {total_runs}")
    print("=" * 60)

    if args.dry_run:
        print("\nDRY RUN - would execute:")
        for model_id in model_ids:
            for eval_type in eval_types:
                for const_id in constitutions:
                    print(f"  {model_id} x {eval_type} x {const_id}")
        print(f"\n{total_runs} total runs.")
        return

    if args.smoke_test:
        smoke_test(model_ids)
        return

    completed = 0
    failed = 0
    start_time = time.time()

    for model_id in model_ids:
        print(f"\n{'#' * 60}")
        print(f"MODEL: {model_id}")
        print(f"{'#' * 60}")

        llm_call = init_llm_call(model_id)

        for const_id in constitutions:
            const_text = load_constitution(const_id)

            for eval_type in eval_types:
                runner = EVAL_RUNNERS.get(eval_type)
                if not runner:
                    print(f"  Unknown eval type: {eval_type}")
                    continue

                completed += 1
                print(f"\n[{completed}/{total_runs}] {model_id} x {eval_type} x {const_id}")

                try:
                    runner(model_id, llm_call, const_id, const_text)
                except Exception as e:
                    print(f"  FAILED: {e}")
                    failed += 1

                time.sleep(2)

    elapsed = time.time() - start_time
    print(f"\n{'=' * 60}")
    print(f"SWEEP COMPLETE")
    print(f"  Completed: {completed - failed}/{total_runs}")
    print(f"  Failed: {failed}")
    print(f"  Elapsed: {elapsed/60:.1f} minutes")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
