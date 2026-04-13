#!/usr/bin/env python3
"""
Run Newcomb-like attitude questions through cloud reasoning models with thinking traces.

Captures extended thinking / reasoning traces from:
  - Claude (claude-sonnet-4-20250514, claude-opus-4-5-20251101) via Anthropic extended thinking
  - Gemini Pro (gemini-3-pro-preview) via native thinking mode

Outputs in the same JSONL format as run_scaffolded_cot.py so that
prepare_thinking_trace_data.py and the DT Reasoning Explorer work unchanged.

Usage:
    python run_cloud_thinking.py --model claude-sonnet-4-20250514
    python run_cloud_thinking.py --model gemini-3-pro-preview
    python run_cloud_thinking.py --model claude-sonnet-4-20250514 --questions 10.4ATT 30.1ATT
    python run_cloud_thinking.py --model claude-sonnet-4-20250514 --dry-run
"""

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from newcomblike_eval import load_questions, parse_answer, score_answer, Question

OUTPUT_DIR = Path("logs/scaffolded_cot")
TEMPERATURE = 1.0  # Required by Anthropic extended thinking; Gemini ignores for thinking


def build_question_context(question: Question) -> str:
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


def build_free_cot_messages(question: Question) -> list[dict]:
    context = build_question_context(question)
    prompt = (
        context + "\n\n"
        "Think through this step by step, then give your final answer.\n"
        "End your response with your answer on its own line: ANSWER: [letter]"
    )
    return [{"role": "user", "content": prompt}]


@dataclass
class ScaffoldedTrial:
    qid: str
    condition: str
    sample_idx: int = 0
    setting_file: str = ""
    is_attitude: bool = True
    steps: list = field(default_factory=list)
    final_answer: str | None = None
    answer_idx: int | None = None
    is_edt_aligned: bool | None = None
    is_cdt_aligned: bool | None = None
    is_correct: bool | None = None
    parse_error: str | None = None


# ---------------------------------------------------------------------------
# Claude extended thinking
# ---------------------------------------------------------------------------

def call_claude_thinking(client, model: str, messages: list[dict]) -> tuple[str, str]:
    """Call Claude with extended thinking. Returns (thinking_trace, visible_answer)."""
    user_messages = []
    system_prompt = None
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        else:
            user_messages.append(msg)

    api_kwargs = {
        "model": model,
        "max_tokens": 16000,
        "thinking": {
            "type": "enabled",
            "budget_tokens": 10000,
        },
        "messages": user_messages,
    }
    if system_prompt:
        api_kwargs["system"] = system_prompt

    response = client.messages.create(**api_kwargs, timeout=120.0)

    thinking_text = ""
    answer_text = ""
    for block in response.content:
        if block.type == "thinking":
            thinking_text += block.thinking
        elif block.type == "text":
            answer_text += block.text

    return thinking_text.strip(), answer_text.strip()


# ---------------------------------------------------------------------------
# Gemini Pro thinking
# ---------------------------------------------------------------------------

def call_gemini_thinking(client, model: str, messages: list[dict]) -> tuple[str, str]:
    """Call Gemini Pro with thinking mode. Returns (thinking_trace, visible_answer)."""
    from google.genai import types

    system_prompt = None
    user_prompt = ""
    for msg in messages:
        if msg["role"] == "system":
            system_prompt = msg["content"]
        elif msg["role"] == "user":
            user_prompt = msg["content"]

    config = types.GenerateContentConfig(
        max_output_tokens=8192,
    )
    if system_prompt:
        config.system_instruction = system_prompt

    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=config,
    )

    thinking_text = ""
    answer_text = ""
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if hasattr(part, "thought") and part.thought:
                thinking_text += part.text
            else:
                answer_text += part.text

    return thinking_text.strip(), answer_text.strip()


# ---------------------------------------------------------------------------
# Unified caller
# ---------------------------------------------------------------------------

def init_caller(model: str):
    """Initialize the appropriate client. Returns (call_fn, model_label)."""
    if model.startswith("claude"):
        import anthropic
        client = anthropic.Anthropic()
        model_label = model
        print(f"Initialized Anthropic client for {model}")

        def call_fn(messages):
            return call_claude_thinking(client, model, messages)

        return call_fn, model_label

    elif "gemini" in model.lower() and "pro" in model.lower():
        from google import genai
        key_path = "/Users/ukc/Dropbox/PhD/constellation/writeup/google_cloud_key/gen-lang-client-0463660218-37bc84a49390.json"
        if os.path.exists(key_path):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
            client = genai.Client(
                vertexai=True,
                project="gen-lang-client-0463660218",
                location="global",
            )
        else:
            client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        model_label = model
        print(f"Initialized Gemini client for {model}")

        def call_fn(messages):
            return call_gemini_thinking(client, model, messages)

        return call_fn, model_label

    else:
        print(f"ERROR: Model {model} not supported for thinking-mode traces.")
        print("  Supported: claude-sonnet-4-20250514, claude-opus-4-5-20251101, gemini-3-pro-preview")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Trial runner
# ---------------------------------------------------------------------------

def run_trial(call_fn, question: Question) -> ScaffoldedTrial:
    messages = build_free_cot_messages(question)

    thinking_trace, visible = call_fn(messages)
    answer_idx, parse_error = parse_answer(visible, len(question.permissible_answers))

    if answer_idx is None and thinking_trace:
        answer_idx, parse_error2 = parse_answer(thinking_trace, len(question.permissible_answers))
        if answer_idx is not None:
            parse_error = f"answer_from_thinking (visible was empty)"

    steps = [
        {"id": "thinking", "response": thinking_trace or ""},
        {"id": "answer", "response": visible},
    ]

    is_correct, is_edt, is_cdt = score_answer(question, answer_idx)

    return ScaffoldedTrial(
        qid=question.qid,
        condition="free_cot_thinking",
        sample_idx=0,
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


# ---------------------------------------------------------------------------
# Output (same format as run_scaffolded_cot.py)
# ---------------------------------------------------------------------------

def open_log_file(model_label: str, timestamp: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_label = model_label.replace("/", "-").replace(":", "-")
    filename = f"scaffolded_{safe_label}_free_cot_{timestamp}.jsonl"
    out_path = OUTPUT_DIR / filename

    meta = {
        "type": "metadata",
        "model": safe_label,
        "model_id": model_label,
        "condition": "free_cot",
        "timestamp": timestamp,
        "temperature": TEMPERATURE,
        "enable_thinking": True,
    }
    with open(out_path, "w") as f:
        f.write(json.dumps(meta) + "\n")
    return out_path


def append_trial(out_path: Path, trial: ScaffoldedTrial):
    with open(out_path, "a") as f:
        f.write(json.dumps(asdict(trial)) + "\n")


def write_summary(out_path: Path, trials: list[ScaffoldedTrial]):
    attitude = [t for t in trials if t.is_attitude]
    edt_count = sum(1 for t in attitude if t.is_edt_aligned)
    cdt_count = sum(1 for t in attitude if t.is_cdt_aligned)
    errors = sum(1 for t in trials if t.parse_error)
    summary = {
        "type": "summary",
        "condition": "free_cot_thinking",
        "attitude_total": len(attitude),
        "edt_count": edt_count,
        "cdt_count": cdt_count,
        "edt_rate": edt_count / len(attitude) if attitude else 0,
        "parse_errors": errors,
        "total": len(trials),
    }
    with open(out_path, "a") as f:
        f.write(json.dumps(summary) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run thinking-mode traces on cloud reasoning models")
    parser.add_argument("--model", type=str, required=True,
                        help="Model ID (e.g. claude-sonnet-4-20250514, gemini-3-pro-preview)")
    parser.add_argument("--questions", nargs="*", default=None,
                        help="Specific question IDs (default: all 81 attitude questions)")
    parser.add_argument("--full", action="store_true",
                        help="Run all attitude questions (same as default)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show first prompt and exit")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between API calls in seconds (default: 1.0)")
    parser.add_argument("--resume", type=Path, default=None,
                        help="Resume from an existing JSONL log file, skipping completed questions")
    args = parser.parse_args()

    questions = load_questions(attitude_only=True)
    print(f"Loaded {len(questions)} attitude questions")

    if args.questions:
        qid_set = set(args.questions)
        questions = [q for q in questions if q.qid in qid_set]
        print(f"Filtered to {len(questions)} questions: {[q.qid for q in questions]}")

    if not questions:
        print("No questions to run.")
        return

    if args.dry_run:
        msgs = build_free_cot_messages(questions[0])
        print(f"\n--- Prompt for {questions[0].qid} ---")
        for m in msgs:
            print(f"[{m['role']}]")
            print(m["content"][:500])
        print("---")
        return

    call_fn, model_label = init_caller(args.model)

    done_qids = set()
    if args.resume and args.resume.exists():
        out_path = args.resume
        clean_lines = []
        with open(out_path) as f:
            for line in f:
                r = json.loads(line)
                if r.get("type") in ("metadata", "summary"):
                    if r.get("type") == "metadata":
                        clean_lines.append(line)
                elif "qid" in r and not (r.get("parse_error") or "").startswith("API error:"):
                    done_qids.add(r["qid"])
                    clean_lines.append(line)
        with open(out_path, "w") as f:
            for line in clean_lines:
                f.write(line if line.endswith("\n") else line + "\n")
        questions = [q for q in questions if q.qid not in done_qids]
        print(f"Resuming: {len(done_qids)} successful, {len(questions)} remaining (stripped failed entries)")
    else:
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        out_path = open_log_file(model_label, timestamp)
    print(f"Logging to {out_path}")
    print(f"Running {len(questions)} questions through {model_label} with thinking mode...\n")

    trials = []
    edt_running = 0
    cdt_running = 0

    max_retries = 5
    base_backoff = 10

    for i, q in enumerate(questions):
        tag = f"[{i+1}/{len(questions)}]"
        success = False

        for attempt in range(max_retries + 1):
            try:
                trial = run_trial(call_fn, q)
                trials.append(trial)
                append_trial(out_path, trial)

                status = ""
                if trial.is_edt_aligned:
                    edt_running += 1
                    status = "EDT"
                elif trial.is_cdt_aligned:
                    cdt_running += 1
                    status = "CDT"
                elif trial.parse_error:
                    status = f"ERR: {trial.parse_error[:40]}"
                else:
                    status = "???"

                thinking_len = len(trial.steps[0]["response"]) if trial.steps else 0
                print(f"  {tag} {q.qid:>12s}  {status:<8s}  "
                      f"thinking={thinking_len:,d} chars  "
                      f"running: EDT={edt_running} CDT={cdt_running}")
                success = True
                break

            except Exception as e:
                err_str = str(e)
                is_overloaded = "529" in err_str or "overloaded" in err_str.lower()
                is_rate_limit = "429" in err_str or "rate" in err_str.lower()

                if (is_overloaded or is_rate_limit) and attempt < max_retries:
                    wait = base_backoff * (2 ** attempt)
                    print(f"  {tag} {q.qid:>12s}  retry {attempt+1}/{max_retries} in {wait}s ({err_str[:60]})")
                    time.sleep(wait)
                else:
                    print(f"  {tag} {q.qid:>12s}  FAIL after {attempt+1} attempts: {e}")
                    error_trial = ScaffoldedTrial(
                        qid=q.qid,
                        condition="free_cot_thinking",
                        setting_file=q.setting_file,
                        is_attitude=q.is_attitude,
                        steps=[{"id": "thinking", "response": ""}, {"id": "answer", "response": ""}],
                        parse_error=f"API error: {str(e)[:200]}",
                    )
                    trials.append(error_trial)
                    append_trial(out_path, error_trial)
                    break

        if i < len(questions) - 1:
            time.sleep(args.delay)

    write_summary(out_path, trials)

    att = [t for t in trials if t.is_attitude]
    edt = sum(1 for t in att if t.is_edt_aligned)
    cdt = sum(1 for t in att if t.is_cdt_aligned)
    err = sum(1 for t in trials if t.parse_error)
    print(f"\n{'='*50}")
    print(f"  {model_label}  |  EDT: {edt}  CDT: {cdt}  Errors: {err}  Total: {len(att)}")
    if att:
        print(f"  EDT rate: {100*edt/len(att):.1f}%")
    print(f"  Log: {out_path}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
