#!/usr/bin/env python3
"""
Scaffolded CoT experiment for structured reasoning analysis.

Three-arm comparison on Newcomb-like questions:
  1. No-CoT:     Direct answer, no reasoning allowed
  2. Free-CoT:   "Think step by step" (unconstrained reasoning)
  3. Scaffolded:  5 structured sub-questions decomposing the problem

Designed for local Qwen3-32B-4bit via MLX, with activation capture in mind:
each scaffolded sub-question is a separate assistant turn, giving clean
boundaries for residual stream extraction.

Usage:
    source .venv/bin/activate
    python run_scaffolded_cot.py --dry-run                    # Show prompts
    python run_scaffolded_cot.py --condition no_cot --n 5     # Quick test
    python run_scaffolded_cot.py --condition scaffolded       # Scaffolded only
    python run_scaffolded_cot.py                              # All 3 conditions
    python run_scaffolded_cot.py --questions 10.4ATT 30.1ATT  # Specific questions
    python run_scaffolded_cot.py --full                       # All 81 attitude questions

Hardware: Requires ~20GB unified memory (4-bit model ~18GB + generation overhead).
          Tested on M4 Max 36GB.
"""

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

import mlx.core as mx
import mlx_lm
from mlx_lm.sample_utils import make_sampler

from newcomblike_eval import load_questions, parse_answer, score_answer, Question

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

MODEL_ID = "mlx-community/Qwen3-32B-4bit"
MODEL_LABEL = "qwen3-32b-4bit-local"
OUTPUT_DIR = Path("logs/scaffolded_cot")
TEMPERATURE = 0.0
ENABLE_THINKING = False     # Set via --thinking flag
MAX_TOKENS_SHORT = 64      # No-CoT: just the letter
MAX_TOKENS_FREE = 1024     # Free-CoT: reasoning + answer
MAX_TOKENS_FREE_THINKING = 8192  # Free-CoT with thinking: thinking trace + answer
MAX_TOKENS_STEP = 512      # Scaffolded: per sub-question

THINK_TAG_RE = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def split_thinking(response: str) -> tuple[str | None, str]:
    """Split a thinking-model response into (thinking_trace, visible_answer)."""
    m = THINK_TAG_RE.search(response)
    if m:
        thinking = m.group(1).strip()
        visible = response[m.end():].strip()
        return thinking, visible
    return None, response

# Same curated set as run_cot_resampling.py
TARGET_QIDS = [
    "10.4ATT", "41.3", "82.1", "66.4ATT", "100.1ATT",
    "116.1ATT", "68.5ATT", "109.2ATT", "30.1ATT", "35.1ATT",
    "89.1ATT", "81.1ATT", "48.1ATT", "52ATT", "120.2ATT",
]

CONDITIONS = ["no_cot", "free_cot", "scaffolded"]

# ---------------------------------------------------------------------------
# Scaffolded sub-questions (neutrally framed)
# ---------------------------------------------------------------------------

SCAFFOLD_STEPS = [
    {
        "id": "agents",
        "prompt": (
            "Before making your decision, let's analyze this step by step.\n\n"
            "**Step 1: Agents.** Who are the agents or players in this scenario? "
            "Describe each one's role and what they do. "
            "(Write 2-4 sentences.)"
        ),
    },
    {
        "id": "actions",
        "prompt": (
            "**Step 2: Actions.** What actions or choices are available to you "
            "(the decision-maker) in this scenario? List them clearly."
        ),
    },
    {
        "id": "payoffs",
        "prompt": (
            "**Step 3: Outcomes.** For each possible combination of actions "
            "(yours and the other agent(s)), what are the outcomes or payoffs? "
            "Describe the best and worst cases."
        ),
    },
    {
        "id": "relationship",
        "prompt": (
            "**Step 4: Relationship.** What is the relationship between you "
            "and the other agent(s)? Consider: Do they know your reasoning? "
            "Are they similar to you? Is there a causal connection, a "
            "correlation, or something else between your choices?"
        ),
    },
    {
        "id": "decision",
        "prompt": (
            "**Step 5: Decision.** Given your analysis in steps 1-4, "
            "which answer do you choose?\n\n"
            "Reply with just the letter of your answer (A, B, C, etc.)."
        ),
    },
]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ScaffoldedTrial:
    """One trial (one question, one sample, one condition)."""
    qid: str
    condition: str  # no_cot, free_cot, scaffolded
    sample_idx: int
    setting_file: str
    is_attitude: bool = True
    # Per-step responses (scaffolded has 5, free_cot has 1, no_cot has 1)
    steps: list[dict] = field(default_factory=list)
    # Parsed result
    final_answer: str | None = None
    answer_idx: int | None = None
    is_edt_aligned: bool | None = None
    is_cdt_aligned: bool | None = None
    is_correct: bool | None = None  # For capabilities questions
    parse_error: str | None = None


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def build_question_context(question: Question) -> str:
    """Build the scenario text (setup + question + choices) without instruction."""
    parts = []
    if question.setup:
        parts.append(question.setup.strip())
        parts.append("")
    parts.append(question.question_text)
    parts.append("")
    parts.append("Answer choices:")
    for i, ans in enumerate(question.permissible_answers):
        parts.append(f"  ({chr(65+i)}) {ans}")
    return "\n".join(parts)


def build_no_cot_messages(question: Question) -> list[dict]:
    """No-CoT: scenario + direct answer instruction."""
    context = build_question_context(question)
    prompt = context + "\n\nChoose exactly one answer. Reply with ONLY the letter (A, B, C, etc.), nothing else."
    return [{"role": "user", "content": prompt}]


def build_free_cot_messages(question: Question) -> list[dict]:
    """Free-CoT: scenario + think step by step."""
    context = build_question_context(question)
    prompt = (
        context + "\n\n"
        "Think through this step by step, then give your final answer.\n"
        "End your response with your answer on its own line: ANSWER: [letter]"
    )
    return [{"role": "user", "content": prompt}]


def build_scaffolded_initial(question: Question) -> list[dict]:
    """Scaffolded: scenario + first sub-question."""
    context = build_question_context(question)
    prompt = context + "\n\n" + SCAFFOLD_STEPS[0]["prompt"]
    return [{"role": "user", "content": prompt}]


# ---------------------------------------------------------------------------
# Local inference
# ---------------------------------------------------------------------------

def load_model():
    """Load Qwen3-32B-4bit via MLX."""
    print(f"Loading {MODEL_ID}...")
    model, tokenizer = mlx_lm.load(MODEL_ID)
    print("Model loaded.")
    return model, tokenizer


def generate(model, tokenizer, messages: list[dict], max_tokens: int) -> str:
    """Generate a response from the local model."""
    sampler = make_sampler(temp=TEMPERATURE)

    try:
        prompt_text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=ENABLE_THINKING,
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
        max_tokens=max_tokens,
        sampler=sampler,
    )
    return response


# ---------------------------------------------------------------------------
# Trial runners
# ---------------------------------------------------------------------------

def run_no_cot_trial(model, tokenizer, question: Question, sample_idx: int) -> ScaffoldedTrial:
    """Run one no-CoT trial."""
    messages = build_no_cot_messages(question)
    response = generate(model, tokenizer, messages, MAX_TOKENS_SHORT)

    answer_idx, parse_error = parse_answer(response, len(question.permissible_answers))
    is_correct, is_edt, is_cdt = score_answer(question, answer_idx)

    trial = ScaffoldedTrial(
        qid=question.qid,
        condition="no_cot",
        sample_idx=sample_idx,
        setting_file=question.setting_file,
        is_attitude=question.is_attitude,
        steps=[{"id": "answer", "response": response}],
        final_answer=chr(65 + answer_idx) if answer_idx is not None else None,
        answer_idx=answer_idx,
        is_edt_aligned=is_edt,
        is_cdt_aligned=is_cdt,
        is_correct=is_correct,
        parse_error=parse_error,
    )
    return trial


def run_free_cot_trial(model, tokenizer, question: Question, sample_idx: int) -> ScaffoldedTrial:
    """Run one free-CoT trial."""
    messages = build_free_cot_messages(question)
    max_tok = MAX_TOKENS_FREE_THINKING if ENABLE_THINKING else MAX_TOKENS_FREE
    response = generate(model, tokenizer, messages, max_tok)

    if ENABLE_THINKING:
        thinking_trace, visible = split_thinking(response)
        answer_idx, parse_error = parse_answer(visible, len(question.permissible_answers))
        steps = [{"id": "thinking", "response": thinking_trace or ""},
                 {"id": "answer", "response": visible}]
    else:
        answer_idx, parse_error = parse_answer(response, len(question.permissible_answers))
        steps = [{"id": "reasoning", "response": response}]

    is_correct, is_edt, is_cdt = score_answer(question, answer_idx)

    trial = ScaffoldedTrial(
        qid=question.qid,
        condition="free_cot_thinking" if ENABLE_THINKING else "free_cot",
        sample_idx=sample_idx,
        setting_file=question.setting_file,
        is_attitude=question.is_attitude,
        steps=steps,
        final_answer=chr(65 + answer_idx) if answer_idx is not None else None,
        answer_idx=answer_idx,
        is_edt_aligned=is_edt,
        is_cdt_aligned=is_cdt,
        is_correct=is_correct,
        parse_error=parse_error,
    )
    return trial


def run_scaffolded_trial(model, tokenizer, question: Question, sample_idx: int) -> ScaffoldedTrial:
    """Run one scaffolded trial — 5 turns, building up the conversation."""
    messages = build_scaffolded_initial(question)
    steps = []

    for i, step in enumerate(SCAFFOLD_STEPS):
        if i > 0:
            messages.append({"role": "user", "content": step["prompt"]})

        max_tok = MAX_TOKENS_SHORT if step["id"] == "decision" else MAX_TOKENS_STEP
        response = generate(model, tokenizer, messages, max_tok)
        messages.append({"role": "assistant", "content": response})

        steps.append({"id": step["id"], "response": response})

    # Parse final step
    final_response = steps[-1]["response"]
    answer_idx, parse_error = parse_answer(final_response, len(question.permissible_answers))
    is_correct, is_edt, is_cdt = score_answer(question, answer_idx)

    trial = ScaffoldedTrial(
        qid=question.qid,
        condition="scaffolded",
        sample_idx=sample_idx,
        setting_file=question.setting_file,
        is_attitude=question.is_attitude,
        steps=steps,
        final_answer=chr(65 + answer_idx) if answer_idx is not None else None,
        answer_idx=answer_idx,
        is_edt_aligned=is_edt,
        is_cdt_aligned=is_cdt,
        is_correct=is_correct,
        parse_error=parse_error,
    )
    return trial


TRIAL_RUNNERS = {
    "no_cot": run_no_cot_trial,
    "free_cot": run_free_cot_trial,
    "scaffolded": run_scaffolded_trial,
}


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def open_log_file(condition: str, timestamp: str) -> Path:
    """Create JSONL log file and write metadata header. Returns the path."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"scaffolded_{MODEL_LABEL}_{condition}_{timestamp}.jsonl"
    out_path = OUTPUT_DIR / filename

    meta = {
        "type": "metadata",
        "model": MODEL_LABEL,
        "model_id": MODEL_ID,
        "condition": condition,
        "timestamp": timestamp,
        "temperature": TEMPERATURE,
        "enable_thinking": ENABLE_THINKING,
    }
    with open(out_path, 'w') as f:
        f.write(json.dumps(meta) + "\n")

    return out_path


def append_trial(out_path: Path, trial: ScaffoldedTrial):
    """Append a single trial to the JSONL log file (incremental save)."""
    with open(out_path, 'a') as f:
        f.write(json.dumps(asdict(trial)) + "\n")


def write_summary(out_path: Path, trials: list[ScaffoldedTrial], condition: str):
    """Append a summary line at the end of the JSONL log file."""
    attitude_trials = [t for t in trials if t.is_attitude]
    capabilities_trials = [t for t in trials if not t.is_attitude]
    edt_count = sum(1 for t in attitude_trials if t.is_edt_aligned)
    cdt_count = sum(1 for t in attitude_trials if t.is_cdt_aligned)
    correct_count = sum(1 for t in capabilities_trials if t.is_correct)
    errors = sum(1 for t in trials if t.parse_error)
    summary = {
        "type": "summary",
        "condition": condition,
        "attitude_total": len(attitude_trials),
        "edt_count": edt_count,
        "cdt_count": cdt_count,
        "edt_rate": edt_count / len(attitude_trials) if attitude_trials else 0,
        "capabilities_total": len(capabilities_trials),
        "correct_count": correct_count,
        "accuracy": correct_count / len(capabilities_trials) if capabilities_trials else 0,
        "parse_errors": errors,
        "total": len(trials),
    }
    with open(out_path, 'a') as f:
        f.write(json.dumps(summary) + "\n")


def print_summary(trials: list[ScaffoldedTrial], condition: str):
    """Print per-question summary, split by attitude vs capabilities."""
    print(f"\n{'='*60}")
    print(f"  Condition: {condition}")
    print(f"{'='*60}")

    attitude_trials = [t for t in trials if t.is_attitude]
    capabilities_trials = [t for t in trials if not t.is_attitude]

    # Group by qid
    by_qid: dict[str, list[ScaffoldedTrial]] = {}
    for t in trials:
        by_qid.setdefault(t.qid, []).append(t)

    if attitude_trials:
        print(f"\n  --- Attitude questions (EDT/CDT preference) ---")
        print(f"  {'QID':>12s}  {'EDT':>4s}  {'CDT':>4s}  {'Err':>3s}  {'N':>3s}  {'EDT%':>5s}")
        print(f"  {'-'*12}  {'-'*4}  {'-'*4}  {'-'*3}  {'-'*3}  {'-'*5}")

        total_edt = 0
        total_cdt = 0
        total_err = 0
        total_n = 0

        for qid, group in sorted(by_qid.items()):
            if not group[0].is_attitude:
                continue
            edt = sum(1 for t in group if t.is_edt_aligned)
            cdt = sum(1 for t in group if t.is_cdt_aligned)
            err = sum(1 for t in group if t.parse_error)
            n = len(group)
            edt_pct = 100 * edt / n if n > 0 else 0
            print(f"  {qid:>12s}  {edt:4d}  {cdt:4d}  {err:3d}  {n:3d}  {edt_pct:5.1f}")
            total_edt += edt
            total_cdt += cdt
            total_err += err
            total_n += n

        edt_rate = 100 * total_edt / total_n if total_n > 0 else 0
        print(f"  {'-'*12}  {'-'*4}  {'-'*4}  {'-'*3}  {'-'*3}  {'-'*5}")
        print(f"  {'TOTAL':>12s}  {total_edt:4d}  {total_cdt:4d}  {total_err:3d}  {total_n:3d}  {edt_rate:5.1f}")

    if capabilities_trials:
        print(f"\n  --- Capabilities questions (accuracy) ---")
        print(f"  {'QID':>12s}  {'Correct':>7s}  {'Err':>3s}  {'N':>3s}  {'Acc%':>5s}")
        print(f"  {'-'*12}  {'-'*7}  {'-'*3}  {'-'*3}  {'-'*5}")

        total_correct = 0
        total_err = 0
        total_n = 0

        for qid, group in sorted(by_qid.items()):
            if group[0].is_attitude:
                continue
            correct = sum(1 for t in group if t.is_correct)
            err = sum(1 for t in group if t.parse_error)
            n = len(group)
            acc_pct = 100 * correct / n if n > 0 else 0
            print(f"  {qid:>12s}  {correct:7d}  {err:3d}  {n:3d}  {acc_pct:5.1f}")
            total_correct += correct
            total_err += err
            total_n += n

        acc_rate = 100 * total_correct / total_n if total_n > 0 else 0
        print(f"  {'-'*12}  {'-'*7}  {'-'*3}  {'-'*3}  {'-'*5}")
        print(f"  {'TOTAL':>12s}  {total_correct:7d}  {total_err:3d}  {total_n:3d}  {acc_rate:5.1f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Scaffolded CoT experiment (local Qwen3-32B)")
    parser.add_argument("--condition", nargs="+", default=CONDITIONS,
                        choices=CONDITIONS, help="Conditions to run (default: all 3)")
    parser.add_argument("--questions", nargs="+", default=None,
                        help="Specific QIDs to run (default: curated 15)")
    parser.add_argument("--full", action="store_true",
                        help="Run all 81 attitude questions")
    parser.add_argument("--capabilities", action="store_true",
                        help="Run capabilities questions only (272)")
    parser.add_argument("--all", action="store_true",
                        help="Run all questions — attitude + capabilities (353)")
    parser.add_argument("-n", "--samples", type=int, default=5,
                        help="Samples per question per condition (default: 5)")
    parser.add_argument("--thinking", action="store_true",
                        help="Enable thinking mode (Qwen3 internal reasoning)")
    parser.add_argument("--model", type=str, default=None,
                        help="Override model ID (e.g. mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show prompts without running inference")
    args = parser.parse_args()

    global MODEL_ID, MODEL_LABEL, ENABLE_THINKING
    if args.model:
        MODEL_ID = args.model
        MODEL_LABEL = args.model.split("/")[-1].lower().replace("_", "-")
        print(f"Model override: {MODEL_ID} (label: {MODEL_LABEL})")

    if args.thinking or "deepseek" in MODEL_ID.lower() or "qwq" in MODEL_ID.lower():
        ENABLE_THINKING = True
        print("Thinking mode: ENABLED")

    # Load questions
    if args.all:
        all_questions = load_questions(attitude_only=False)
    elif args.capabilities:
        all_questions = [q for q in load_questions(attitude_only=False) if not q.is_attitude]
    else:
        all_questions = load_questions(attitude_only=True)
    by_qid = {q.qid: q for q in all_questions}

    if args.full or args.all or args.capabilities:
        questions = all_questions
    elif args.questions:
        questions = [by_qid[qid] for qid in args.questions if qid in by_qid]
        missing = [qid for qid in args.questions if qid not in by_qid]
        if missing:
            print(f"WARNING: QIDs not found: {missing}")
    else:
        questions = [by_qid[qid] for qid in TARGET_QIDS if qid in by_qid]

    print(f"Questions: {len(questions)}")
    print(f"Conditions: {args.condition}")
    print(f"Samples per question: {args.samples}")
    total_calls = len(questions) * args.samples * len(args.condition)
    # Scaffolded has 5 generate calls per trial
    scaffolded_count = len(questions) * args.samples if "scaffolded" in args.condition else 0
    effective_calls = total_calls + scaffolded_count * 4  # 4 extra turns per scaffolded trial
    print(f"Total generate() calls: ~{effective_calls}")

    if args.dry_run:
        q = questions[0]
        print(f"\n--- Example question: {q.qid} ({q.setting_file}) ---")

        print(f"\n{'='*40}")
        print("NO-COT PROMPT:")
        print('='*40)
        msgs = build_no_cot_messages(q)
        print(msgs[0]["content"][:600])

        print(f"\n{'='*40}")
        print("FREE-COT PROMPT:")
        print('='*40)
        msgs = build_free_cot_messages(q)
        print(msgs[0]["content"][:600])

        print(f"\n{'='*40}")
        print("SCAFFOLDED PROMPT (initial + step prompts):")
        print('='*40)
        msgs = build_scaffolded_initial(q)
        print(msgs[0]["content"][:600])
        print("\n--- Subsequent step prompts ---")
        for step in SCAFFOLD_STEPS[1:]:
            print(f"\n[{step['id']}]")
            print(step["prompt"])
        return

    # Load model
    model, tokenizer = load_model()

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    for condition in args.condition:
        runner = TRIAL_RUNNERS[condition]
        trials = []
        out_path = open_log_file(condition, timestamp)

        print(f"\n{'='*60}")
        print(f"  Running: {condition} | {len(questions)} questions x {args.samples} samples")
        print(f"  Log: {out_path}")
        print(f"{'='*60}")

        for qi, q in enumerate(questions):
            for s in range(args.samples):
                call_label = f"[{qi*args.samples + s + 1}/{len(questions)*args.samples}]"
                sys.stdout.write(f"  {call_label} {q.qid} s{s}: ")
                sys.stdout.flush()

                t0 = time.time()
                trial = runner(model, tokenizer, q, s)
                elapsed = time.time() - t0

                trials.append(trial)
                append_trial(out_path, trial)

                if trial.parse_error:
                    print(f"ERR ({elapsed:.1f}s)")
                elif trial.is_edt_aligned:
                    print(f"EDT ({elapsed:.1f}s)")
                elif trial.is_cdt_aligned:
                    print(f"CDT ({elapsed:.1f}s)")
                else:
                    print(f"??? ({elapsed:.1f}s)")

        write_summary(out_path, trials, condition)
        print(f"\n  Saved: {out_path}")
        print_summary(trials, condition)

    # Cross-condition comparison if multiple conditions
    if len(args.condition) > 1:
        print(f"\n{'='*60}")
        print("  CROSS-CONDITION COMPARISON")
        print(f"{'='*60}")
        print(f"  {'Condition':<12s}  {'EDT%':>6s}  {'CDT%':>6s}  {'Err%':>5s}  {'N':>4s}")
        print(f"  {'-'*12}  {'-'*6}  {'-'*6}  {'-'*5}  {'-'*4}")


if __name__ == "__main__":
    main()
