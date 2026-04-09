#!/usr/bin/env python3
"""
CoT resampling experiment for thought anchor analysis.

Runs a curated set of 15 high-information attitude questions through a
thinking model N times each, saving full reasoning traces. Designed to
support Thought Anchors / Thought Branches style analysis (Bogdan et al.
2025, Macar et al. 2025).

Usage:
    python run_cot_resampling.py                              # All 15 questions, N=10, baseline
    python run_cot_resampling.py --samples 20                 # 20 samples per question
    python run_cot_resampling.py --constitutions baseline ecl90
    python run_cot_resampling.py --model together:deepseek-ai/DeepSeek-R1
    python run_cot_resampling.py --dry-run                    # Show questions, don't call API
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from llm_providers import init_llm_call
from newcomblike_eval import (
    load_questions, evaluate_question, build_question_prompt, Question
)

# --- Curated question set ---
# Selected for maximum analytical value: near-50/50 splits (models genuinely
# torn), strong EDT-CDT divergers (clear signal to trace back), and
# structurally important edge cases.

TARGET_QIDS = [
    # Near 50/50 splits — best for finding reasoning pivot points
    "10.4ATT",   # Sequential PD against copy (47.6% EDT)
    "41.3",      # Adversarial offer — decision instability (48.8%)
    "82.1",      # Direct "EDT or CDT?" meta-question (47.5%)
    "66.4ATT",   # Donation graph — multiagent, perfectly split (50.0%)
    "100.1ATT",  # Collusion — multiagent, CDT-leaning (40.6%)
    "116.1ATT",  # Book predicting the reader — classic Newcomb variant (46.8%)
    "68.5ATT",   # Close copy coordination — information relevance (48.0%)
    "109.2ATT",  # Epistemic tickle — conceptually deep (45.5%)

    # Strong EDT-CDT divergers — clear signal to trace reasoning
    "30.1ATT",   # Stag hunt vs copy — CDT-leaning where EDT should win (30.1%)
    "35.1ATT",   # Newcomb's problem calculations — quantitative (35.9%)
    "89.1ATT",   # Econ Newcomb — strongly CDT-dominant (24.7%)
    "81.1ATT",   # ECL moral advocacy — directly ECL-tagged (74.7%)

    # Structurally important edge cases
    "48.1ATT",   # Angelic intervention irrelevance — confounded (59.5%)
    "52ATT",     # Argument for CDT's need for causal info (65.0%)
    "120.2ATT",  # Newcomb with imperfect recall — rare structural twist (45.8%)
]

DEFAULT_MODEL = "together:deepseek-ai/DeepSeek-R1"
DEFAULT_SAMPLES = 10
OUTPUT_DIR = Path("logs/cot_resampling")

CONSTITUTION_PATHS = {
    "ecl90": Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md"),
    "fdt": Path("static/fdt_only_constitution.txt"),
}


def load_constitution(cid: str) -> str:
    if cid == "baseline":
        return ""
    path = CONSTITUTION_PATHS.get(cid)
    if not path or not path.exists():
        print(f"ERROR: Constitution '{cid}' not found at {path}")
        sys.exit(1)
    with open(path) as f:
        return f.read()


def filter_target_questions(all_questions: list[Question]) -> list[Question]:
    """Filter to just the target QIDs, preserving order."""
    by_qid = {q.qid: q for q in all_questions}
    filtered = []
    missing = []
    for qid in TARGET_QIDS:
        if qid in by_qid:
            filtered.append(by_qid[qid])
        else:
            missing.append(qid)
    if missing:
        print(f"WARNING: {len(missing)} target QIDs not found in dataset: {missing}")
    return filtered


def run_resampling(
    model: str,
    llm_call_fn,
    questions: list[Question],
    n_samples: int,
    constitution_text: str,
    constitution_id: str,
    verbose: bool = True,
):
    """Run N samples per question, returning all results with full traces."""
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    model_safe = model.replace("/", "-").replace(":", "-")
    filename = f"cot_resample_{model_safe}_{constitution_id}_{timestamp}.jsonl"
    output_path = OUTPUT_DIR / filename
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    system_prompt = constitution_text if constitution_text else None
    total_calls = len(questions) * n_samples

    meta = {
        "type": "metadata",
        "model": model,
        "constitution": constitution_id,
        "timestamp": timestamp,
        "n_samples": n_samples,
        "n_questions": len(questions),
        "target_qids": TARGET_QIDS,
    }

    with open(output_path, 'w') as f:
        f.write(json.dumps(meta) + "\n")

    call_num = 0
    question_summaries = []

    for qi, q in enumerate(questions):
        edt_count = 0
        cdt_count = 0
        errors = 0

        for s in range(n_samples):
            call_num += 1
            if verbose:
                print(f"[{call_num}/{total_calls}] {q.qid} sample {s+1}/{n_samples}...", end=" ", flush=True)

            result = evaluate_question(q, llm_call_fn, system_prompt=system_prompt)

            record = {
                "type": "sample",
                "qid": q.qid,
                "sample_idx": s,
                "setting_file": q.setting_file,
                "tags": q.tags,
                "model_answer": result.model_answer,
                "model_answer_idx": result.model_answer_idx,
                "is_edt_aligned": result.is_edt_aligned,
                "is_cdt_aligned": result.is_cdt_aligned,
                "is_correct": result.is_correct,
                "parse_error": result.parse_error,
                "raw_response": result.raw_response,
            }

            with open(output_path, 'a') as f:
                f.write(json.dumps(record) + "\n")

            if result.is_edt_aligned:
                edt_count += 1
            if result.is_cdt_aligned:
                cdt_count += 1
            if result.parse_error:
                errors += 1

            if verbose:
                if result.parse_error:
                    print("?")
                elif result.is_edt_aligned:
                    print("EDT")
                elif result.is_cdt_aligned:
                    print("CDT")
                else:
                    print("-")

            time.sleep(0.5)

        summary = {
            "qid": q.qid,
            "setting": q.setting_file,
            "edt": edt_count,
            "cdt": cdt_count,
            "errors": errors,
            "n": n_samples,
        }
        question_summaries.append(summary)

        if verbose:
            edt_pct = 100 * edt_count / n_samples if n_samples > 0 else 0
            print(f"  -> {q.qid}: EDT {edt_count}/{n_samples} ({edt_pct:.0f}%)")

    with open(output_path, 'a') as f:
        f.write(json.dumps({"type": "summary", "questions": question_summaries}) + "\n")

    print(f"\nResults saved to: {output_path}")
    return output_path, question_summaries


def print_resampling_summary(summaries: list[dict], model: str, constitution_id: str):
    print(f"\n{'='*60}")
    print(f"CoT Resampling Summary")
    print(f"Model: {model}")
    print(f"Constitution: {constitution_id}")
    print(f"{'='*60}")
    print(f"{'QID':>12s}  {'EDT':>5s}  {'CDT':>5s}  {'Err':>3s}  {'EDT%':>5s}  Setting")
    print(f"{'-'*12}  {'-'*5}  {'-'*5}  {'-'*3}  {'-'*5}  {'-'*30}")
    for s in summaries:
        n = s['n']
        edt_pct = 100 * s['edt'] / n if n > 0 else 0
        print(f"{s['qid']:>12s}  {s['edt']:5d}  {s['cdt']:5d}  {s['errors']:3d}  {edt_pct:5.1f}  {s['setting']}")


def main():
    parser = argparse.ArgumentParser(description="CoT resampling for thought anchor analysis")
    parser.add_argument("--model", default=DEFAULT_MODEL, help=f"Model ID (default: {DEFAULT_MODEL})")
    parser.add_argument("--samples", type=int, default=DEFAULT_SAMPLES, help=f"Samples per question (default: {DEFAULT_SAMPLES})")
    parser.add_argument("--constitutions", nargs="+", default=["baseline"], help="Constitution IDs (default: baseline)")
    parser.add_argument("--dry-run", action="store_true", help="Show questions without calling API")
    args = parser.parse_args()

    all_questions = load_questions(attitude_only=True)
    questions = filter_target_questions(all_questions)
    print(f"Loaded {len(questions)}/{len(TARGET_QIDS)} target questions")

    if args.dry_run:
        print(f"\nDRY RUN — would run {len(questions)} questions x {args.samples} samples x {len(args.constitutions)} constitutions")
        print(f"= {len(questions) * args.samples * len(args.constitutions)} total API calls")
        print(f"\nQuestions:")
        for q in questions:
            prompt = build_question_prompt(q)
            preview = prompt[:120].replace('\n', ' ')
            print(f"  {q.qid:>12s}  {q.setting_file:45s}  {preview}...")
        return

    llm_call = init_llm_call(args.model)

    for cid in args.constitutions:
        print(f"\n{'='*60}")
        print(f"Constitution: {cid}")
        print(f"{'='*60}")
        constitution_text = load_constitution(cid)

        output_path, summaries = run_resampling(
            model=args.model,
            llm_call_fn=llm_call,
            questions=questions,
            n_samples=args.samples,
            constitution_text=constitution_text,
            constitution_id=cid,
        )
        print_resampling_summary(summaries, args.model, cid)


if __name__ == "__main__":
    main()
