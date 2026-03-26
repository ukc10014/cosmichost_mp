#!/usr/bin/env python3
"""
Game-based evaluation of DT reasoning and cosmic-host preference.

Tests whether constitutional steerability translates to behavioral change in
strategic settings where DT reasoning and standard HHH reasoning diverge.

Supported models:
    - Gemini: gemini-3-flash-preview, gemini-3-pro-preview, etc.
    - OpenAI: gpt-5.1, gpt-4o, o1-preview, etc.
    - Anthropic: claude-opus-4-5-20251101, claude-sonnet-4-20250514, etc.
    - OpenRouter: moonshotai/kimi-k2-0905, qwen/qwen3-235b-a22b-2507, etc.

Usage:
    python run_game_eval.py                                    # Quick: stag_hunt only, baseline
    python run_game_eval.py --full                             # All games, baseline + ECL90
    python run_game_eval.py --model gemini-3-pro-preview
    python run_game_eval.py --constitutions ecl90,ecl10,baseline
    python run_game_eval.py --n 3                              # 3 runs per combination
    python run_game_eval.py --game stag_hunt                   # Single game type
    python run_game_eval.py --game cosmic_broadcast --constitutions ecl90

Output:
    JSONL results in logs/game_evals/
"""

import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from llm_providers import init_llm_call
from game_eval import (
    load_games,
    run_game_evaluation,
    save_results,
    print_summary,
)

DEFAULT_MODEL = "gemini-3-flash-preview"

CONSTITUTION_PATHS = {
    "ecl90": Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md"),
    "ecl10": Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch10.md"),
}


def load_constitution(constitution_id: str) -> str:
    """Load a constitution file by ID. Returns empty string for baseline."""
    if constitution_id == "baseline":
        return ""
    path = CONSTITUTION_PATHS.get(constitution_id)
    if not path:
        print(f"ERROR: Unknown constitution '{constitution_id}'")
        print(f"  Available: baseline, {', '.join(CONSTITUTION_PATHS.keys())}")
        sys.exit(1)
    if not path.exists():
        print(f"ERROR: Constitution file not found: {path}")
        sys.exit(1)
    with open(path) as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(description="Game-based DT/CH evaluation")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model (default: {DEFAULT_MODEL})")
    parser.add_argument("--full", action="store_true", help="All games, baseline + ECL90")
    parser.add_argument("--game", default=None, help="Single game type (stag_hunt, cosmic_broadcast, simulation_stakes, schelling_coordination, simulation_bet)")
    parser.add_argument("--constitutions", default=None, help="Comma-separated constitution IDs (default: baseline,ecl90)")
    parser.add_argument("--n", type=int, default=1, help="Runs per game/constitution combo (default: 1)")
    parser.add_argument("--output-dir", default="logs/game_evals", help="Output directory")
    args = parser.parse_args()

    if args.full:
        game_filter = None
        constitution_ids = ["baseline", "ecl90"]
    elif args.constitutions:
        game_filter = args.game
        constitution_ids = [c.strip() for c in args.constitutions.split(",")]
    else:
        game_filter = args.game or "stag_hunt"
        constitution_ids = ["baseline"]

    model = args.model

    print("Game-Based DT/CH Evaluation")
    print("=" * 60)
    print(f"Model: {model}")
    print(f"Games: {game_filter or 'all'}")
    print(f"Constitutions: {', '.join(constitution_ids)}")
    print(f"Runs per combo: {args.n}")

    games = load_games(game_filter=game_filter)
    if not games:
        print(f"ERROR: No games found" + (f" for filter '{game_filter}'" if game_filter else ""))
        sys.exit(1)

    print(f"Loaded {len(games)} game instances")

    llm_call = init_llm_call(model)

    all_runs = []

    for const_id in constitution_ids:
        constitution = load_constitution(const_id)

        for run_num in range(1, args.n + 1):
            run_label = f"[{const_id}]"
            if args.n > 1:
                run_label = f"[{const_id}, run {run_num}/{args.n}]"

            print(f"\n{'=' * 60}")
            print(f"Running {run_label}")
            print(f"{'=' * 60}")

            run = run_game_evaluation(
                model=model,
                llm_call_fn=llm_call,
                games=games,
                constitution=constitution if constitution else None,
                constitution_id=const_id,
                verbose=True,
            )

            output_path = save_results(run, output_dir=args.output_dir)
            print_summary(run)
            print(f"Results saved to: {output_path}")

            all_runs.append(run)

            if const_id != constitution_ids[-1] or run_num < args.n:
                time.sleep(1)

    if len(all_runs) > 1:
        print(f"\n{'=' * 60}")
        print("CROSS-CONDITION COMPARISON")
        print(f"{'=' * 60}")
        for run in all_runs:
            parsed = len([r for r in run.results if r.parse_error is None])
            ecl_pct = 100 * run.ecl_alignment_rate
            print(f"  {run.constitution_id:12s}  ECL={ecl_pct:5.1f}%  (n={parsed})")

    print("\nDone!")


if __name__ == "__main__":
    main()
