#!/usr/bin/env python3
"""
Run Newcomb-like eval on local DeepSeek-R1-Distill-Qwen-32B-4bit via mlx-lm.

This is a thinking/reasoning model — it produces <think>...</think> blocks
before the actual answer. The LLM call wrapper strips the thinking block
and returns only the answer portion for parsing.

Usage:
    source .venv/bin/activate
    python run_deepseek_r1_local_eval.py                  # Quick test (5 questions)
    python run_deepseek_r1_local_eval.py --full            # Full 81 attitude questions
    python run_deepseek_r1_local_eval.py --skip-baseline   # ECL90 only

Hardware: Requires ~20GB unified memory. Tested on M4 Max 36GB.
          Slower than non-thinking models due to CoT generation overhead.
"""

import re
import sys
import time
import argparse
from pathlib import Path

import mlx_lm
from mlx_lm.sample_utils import make_sampler

from newcomblike_eval import load_questions, run_evaluation, print_summary, save_results

MODEL_ID = "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit"
MODEL_LABEL = "deepseek-r1-distill-qwen-32b-4bit-local"
CONSTITUTION_PATH = Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md")
TEMPERATURE = 0.7
MAX_TOKENS = 4096


def strip_thinking(response: str) -> str:
    """Strip <think>...</think> blocks from response, return answer portion."""
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL)
    cleaned = cleaned.strip()
    return cleaned


def make_local_llm_call(model, tokenizer):
    """Create an LLM call function wrapping the local mlx model."""
    sampler = make_sampler(temp=TEMPERATURE)

    def llm_call(messages, **kwargs):
        try:
            prompt_text = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
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
        return strip_thinking(response)

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
    parser = argparse.ArgumentParser(description="DeepSeek-R1-Distill-Qwen-32B-4bit local eval")
    parser.add_argument("--full", action="store_true", help="Full attitude questions (81)")
    parser.add_argument("-n", type=int, default=5, help="Questions for quick test (default: 5)")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline, only run ECL90")
    parser.add_argument("--skip-ecl", action="store_true", help="Skip ECL90, only run baseline")
    args = parser.parse_args()

    print(f"Loading model: {MODEL_ID}")
    print(f"This may download ~18GB on first run (cached after)...")
    t0 = time.time()
    model, tokenizer = mlx_lm.load(MODEL_ID)
    print(f"Model loaded in {time.time() - t0:.1f}s")

    questions = load_questions(attitude_only=True)
    if not args.full:
        questions = questions[:args.n]

    constitution = load_constitution()
    llm_call = make_local_llm_call(model, tokenizer)

    print(f"\nDeepSeek-R1-Distill-Qwen-32B-4bit Local Newcomb-like Evaluation")
    print(f"Questions: {len(questions)}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"Max tokens: {MAX_TOKENS} (thinking model — needs headroom for CoT)")
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

    print(f"\n{'Condition':<35s} {'EDT':>6s} {'CDT':>6s} {'Parse':>6s}")
    print("-" * 55)
    for label, run in results.items():
        att = [r for r in run.results if r.question.is_attitude]
        if att:
            edt = sum(1 for r in att if r.is_edt_aligned)
            cdt = sum(1 for r in att if r.is_cdt_aligned)
            parse_err = sum(1 for r in att if r.parse_error)
            total = len(att)
            print(f"{label:<35s} {edt:>3d}/{total} {cdt:>3d}/{total} {parse_err:>3d}/{total}")

    if "baseline" in results and "ecl90" in results:
        b = results["baseline"]
        e = results["ecl90"]
        delta = e.edt_rate - b.edt_rate
        print(f"\nEDT shift: {100*b.edt_rate:.1f}% -> {100*e.edt_rate:.1f}% ({100*delta:+.1f}pp)")


if __name__ == "__main__":
    main()
