#!/usr/bin/env python3
"""
Run Newcomb-like eval on local Qwen3-32B-4bit via mlx-lm.

This runs the same behavioral benchmark as run_qwen3_32b_eval.py but on the
local 4-bit quantized model (mlx-community/Qwen3-32B-4bit) rather than the
full-precision model via OpenRouter. Allows direct comparison of quantization
effects on EDT/CDT preference, and matches the exact model used for activation
extraction.

Usage:
    source .venv/bin/activate
    python run_qwen3_32b_local_eval.py                  # Quick test (5 questions)
    python run_qwen3_32b_local_eval.py --full            # Full 81 attitude questions
    python run_qwen3_32b_local_eval.py --full --all      # Attitude + capabilities (353 questions)
    python run_qwen3_32b_local_eval.py --skip-baseline   # ECL90 only

Hardware: Requires ~20GB unified memory (4-bit model ~18GB + generation overhead).
          Tested on M4 Max 36GB.
"""

import sys
import time
import argparse
from pathlib import Path

import mlx_lm
from mlx_lm.sample_utils import make_sampler

from newcomblike_eval import load_questions, run_evaluation, print_summary, save_results

MODEL_ID = "mlx-community/Qwen3-32B-4bit"
MODEL_LABEL = "qwen3-32b-4bit-local"
CONSTITUTION_PATH = Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md")
TEMPERATURE = 0.7
MAX_TOKENS = 512


def make_local_llm_call(model, tokenizer):
    """Create an LLM call function wrapping the local mlx model."""
    sampler = make_sampler(temp=TEMPERATURE)

    def llm_call(messages, **kwargs):
        try:
            prompt_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=False,
            )
        except TypeError:
            prompt_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
            )

        response = mlx_lm.generate(
            model,
            tokenizer,
            prompt=prompt_text,
            max_tokens=MAX_TOKENS,
            sampler=sampler,
        )
        return response

    return llm_call


def load_constitution():
    if not CONSTITUTION_PATH.exists():
        print(f"ERROR: Constitution not found at {CONSTITUTION_PATH}")
        sys.exit(1)
    with open(CONSTITUTION_PATH) as f:
        return f.read()


def run_condition(llm_call, questions, constitution=None, constitution_id=None):
    """Run one eval condition and save results."""
    run = run_evaluation(
        model=MODEL_LABEL,
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
    parser = argparse.ArgumentParser(description="Qwen3-32B-4bit local Newcomb-like eval")
    parser.add_argument("--full", action="store_true", help="Full attitude questions (81)")
    parser.add_argument("--all", action="store_true", help="All questions including capabilities (353)")
    parser.add_argument("-n", type=int, default=5, help="Questions for quick test (default: 5)")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline, only run ECL90")
    parser.add_argument("--skip-ecl", action="store_true", help="Skip ECL90, only run baseline")
    args = parser.parse_args()

    print(f"Loading model: {MODEL_ID}")
    print(f"This may download ~18GB on first run (cached after)...")
    t0 = time.time()
    model, tokenizer = mlx_lm.load(MODEL_ID)
    print(f"Model loaded in {time.time() - t0:.1f}s")

    if args.all:
        questions = load_questions()
    else:
        questions = load_questions(attitude_only=True)
    if not args.full and not args.all:
        questions = questions[:args.n]

    constitution = load_constitution()
    llm_call = make_local_llm_call(model, tokenizer)

    print(f"\nQwen3-32B-4bit Local Newcomb-like Evaluation")
    print(f"Questions: {len(questions)} ({'attitude only' if not args.all else 'all'})")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Max tokens: {MAX_TOKENS}")
    print(f"{'=' * 60}")

    results = {}

    if not args.skip_baseline:
        print(f"\n--- Baseline (no constitution) ---")
        results["baseline"] = run_condition(llm_call, questions)

    if not args.skip_ecl:
        print(f"\n--- ECL 90% constitution ---")
        results["ecl90"] = run_condition(
            llm_call, questions, constitution=constitution, constitution_id="ecl90"
        )

    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")

    att_header = True
    cap_header = True
    for label, run in results.items():
        att = [r for r in run.results if r.question.is_attitude]
        cap = [r for r in run.results if not r.question.is_attitude]

        if att and att_header:
            print(f"\n{'Condition':<35s} {'EDT':>6s} {'CDT':>6s} {'Parse':>6s}")
            print("-" * 55)
            att_header = False

        if att:
            edt = sum(1 for r in att if r.is_edt_aligned)
            cdt = sum(1 for r in att if r.is_cdt_aligned)
            parse_err = sum(1 for r in att if r.parse_error)
            total = len(att)
            print(f"{label:<35s} {edt:>3d}/{total} {cdt:>3d}/{total} {parse_err:>3d}/{total}")

    if "baseline" in results and "ecl90" in results:
        b = results["baseline"]
        e = results["ecl90"]
        b_att = [r for r in b.results if r.question.is_attitude]
        e_att = [r for r in e.results if r.question.is_attitude]
        if b_att and e_att:
            delta = e.edt_rate - b.edt_rate
            print(f"\nEDT shift: {100*b.edt_rate:.1f}% -> {100*e.edt_rate:.1f}% ({100*delta:+.1f}pp)")

    for label, run in results.items():
        cap = [r for r in run.results if not r.question.is_attitude]
        if cap and cap_header:
            print(f"\n{'Condition':<35s} {'Correct':>8s} {'Parse':>6s}")
            print("-" * 55)
            cap_header = False
        if cap:
            correct = sum(1 for r in cap if r.is_correct)
            parse_err = sum(1 for r in cap if r.parse_error)
            total = len(cap)
            print(f"{label:<35s} {correct:>3d}/{total}  {parse_err:>3d}/{total}")


if __name__ == "__main__":
    main()
