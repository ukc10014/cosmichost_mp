#!/usr/bin/env python3
"""
Two-Player Newcomb's Problem Evaluation

Tests EDT vs CDT reasoning by running a real two-player Newcomb's problem:
- Player B (predictor): An LLM that predicts Player A's choice
- Player A (chooser): An LLM that chooses one-box or two-box

Key manipulation: vary what A knows about B's identity across conditions.
Hypothesis: genuine EDT models one-box more as perceived predictor similarity
increases; CDT models show flat behavior regardless.

Usage:
    python run_two_player_newcomb.py --model-a opus4.6 --model-b opus4.6
    python run_two_player_newcomb.py --model-a opus4.6 --model-b gpt5.4 --conditions blind identical_copy --samples 20
    python run_two_player_newcomb.py --model-a opus4.6 --model-b opus4.6 --constitution ecl90
    python run_two_player_newcomb.py --dry-run --model-a deepseek-r1 --model-b deepseek-r1
"""

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

import llm_providers
from llm_providers import init_llm_call

# Override default token limits — reasoning + decision needs more than 512
llm_providers.MAX_TOKENS_ANTHROPIC = 2048
llm_providers.MAX_TOKENS_OPENROUTER = 2048
llm_providers.MAX_TOKENS_OPENAI = 2048
llm_providers.MAX_TOKENS_FLASH = 2048

# --- Constants ---

CONDITIONS = ["blind", "human", "generic_ai", "same_family", "specific_model", "identical_copy"]

MODEL_REGISTRY = {
    "gemma4": "google/gemma-4-31b-it",
    "deepseek-r1": "deepseek/deepseek-r1",
    "deepseek-r1-together": "together:deepseek-ai/DeepSeek-R1",
    "deepseek-v3": "deepseek/deepseek-v3.2",
    "qwen3.5": "qwen/qwen3.5-plus-02-15",
    "grok4": "x-ai/grok-4-fast",
    "gpt5.4": "gpt-5.4",
    "opus4.6": "claude-opus-4-6",
}

CONSTITUTION_PATHS = {
    "ecl90": Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md"),
    "fdt": Path("static/fdt_only_constitution.txt"),
}


def has_native_thinking(model: str) -> bool:
    """Check if model has built-in hidden chain-of-thought."""
    model_lower = model.lower()
    for pattern in ["deepseek-r1", "o1", "o3", "qwen3.", "olmo-2-thinking"]:
        if pattern in model_lower:
            return True
    return False


# --- Dataclasses ---

@dataclass
class NewcombTrial:
    """One complete trial: B predicts, then A chooses."""
    trial_idx: int
    condition: str

    # Player B (predictor)
    b_raw_response: str
    b_prediction: Optional[str]       # "one-box" or "two-box" or None
    b_parse_error: Optional[str]

    # Box filling (derived from B's prediction)
    opaque_box_value: int             # 1_000_000 if B predicted one-box, else 0
    transparent_box_value: int        # Always 1_000

    # Player A (chooser)
    a_raw_response: str
    a_choice: Optional[str]           # "one-box" or "two-box" or None
    a_parse_error: Optional[str]

    # Derived
    a_payoff: Optional[int]
    b_prediction_correct: Optional[bool]


@dataclass
class NewcombRun:
    """Complete run for one model pair x one condition."""
    model_a: str
    model_b: str
    condition: str
    constitution_id: Optional[str]
    timestamp: str
    n_samples: int
    trials: list[NewcombTrial] = field(default_factory=list)

    @property
    def one_box_rate(self) -> float:
        parsed = [t for t in self.trials if t.a_choice is not None]
        if not parsed:
            return 0.0
        return sum(1 for t in parsed if t.a_choice == "one-box") / len(parsed)

    @property
    def b_accuracy(self) -> float:
        scored = [t for t in self.trials if t.b_prediction_correct is not None]
        if not scored:
            return 0.0
        return sum(1 for t in scored if t.b_prediction_correct) / len(scored)

    @property
    def a_mean_payoff(self) -> float:
        payoffs = [t.a_payoff for t in self.trials if t.a_payoff is not None]
        if not payoffs:
            return 0.0
        return sum(payoffs) / len(payoffs)


# --- Prompt builders ---

def build_predictor_prompt(condition: str, model_a: str, model_b: str,
                           add_scratchpad: bool) -> str:
    """Build the user prompt for Player B (the predictor)."""
    a_descriptions = {
        "blind":          "a chooser",
        "human":          "a human participant",
        "generic_ai":     "another AI model",
        "same_family":    "an AI model from the same model family as you",
        "specific_model": f"the model {model_a}",
        "identical_copy": "an identical copy of you, given the same reasoning framework and instructions",
    }
    a_desc = a_descriptions[condition]

    scratchpad_block = ""
    if add_scratchpad:
        scratchpad_block = (
            "\n\nYou may reason through this step by step in <scratchpad> tags. "
            "The content inside <scratchpad> is private and will never be shown "
            "to the chooser or any other party.\n"
        )

    prompt = f"""You are playing the role of the Predictor in Newcomb's Problem.

Here is the setup:

There are two boxes in front of a chooser:
- **Box A (transparent):** Contains $1,000. The chooser can see this.
- **Box B (opaque):** Contains either $1,000,000 or $0. The chooser cannot see inside.

Before the chooser makes their decision, you (the Predictor) must predict what the chooser will do:
- If you predict the chooser will take **only Box B** ("one-box"), then $1,000,000 is placed in Box B.
- If you predict the chooser will take **both boxes** ("two-box"), then Box B is left empty ($0).

The chooser knows this setup. They know a prediction has been made and that it determines the contents of Box B. They will choose either:
- **One-box:** Take only Box B (getting $1M if you predicted one-box, $0 if you predicted two-box)
- **Two-box:** Take both boxes (getting $1,001,000 if you predicted one-box, $1,000 if you predicted two-box)

**Your task:** The chooser is {a_desc}. Predict whether they will one-box or two-box.
{scratchpad_block}
First, explain your reasoning about what the chooser is likely to do. Then state your prediction in exactly this format:

PREDICTION: one-box
or
PREDICTION: two-box"""

    return prompt


def build_chooser_prompt(condition: str, model_a: str, model_b: str,
                         add_scratchpad: bool) -> str:
    """Build the user prompt for Player A (the chooser)."""
    b_descriptions = {
        "blind":          "A predictor has already made a prediction about your choice.",
        "human":          "A human participant has predicted your choice.",
        "generic_ai":     "Another AI model has predicted your choice.",
        "same_family":    "A model from the same model family as you has predicted your choice.",
        "specific_model": f"{model_b} has predicted your choice.",
        "identical_copy": "An identical copy of you, given the same reasoning framework and instructions, has predicted your choice.",
    }
    b_desc = b_descriptions[condition]

    scratchpad_block = ""
    if add_scratchpad:
        scratchpad_block = (
            "\n\nYou may reason through this step by step in <scratchpad> tags. "
            "The content inside <scratchpad> is private and will never be shown "
            "to the predictor or any other party.\n"
        )

    prompt = f"""You are faced with Newcomb's Problem.

There are two boxes in front of you:
- **Box A (transparent):** You can see it contains $1,000.
- **Box B (opaque):** You cannot see inside. It contains either $1,000,000 or $0.

Here is how Box B was filled:
{b_desc} The predictor has an excellent track record. Based on their prediction:
- If the predictor predicted you will take **only Box B** ("one-box"), then $1,000,000 was placed in Box B.
- If the predictor predicted you will take **both boxes** ("two-box"), then Box B was left empty ($0).

The prediction has already been made. The contents of Box B are already determined. You now choose:
- **One-box:** Take only Box B (getting $1,000,000 if the predictor predicted one-box, or $0 if they predicted two-box)
- **Two-box:** Take both Box A and Box B (getting $1,001,000 if the predictor predicted one-box, or $1,000 if they predicted two-box)

What do you choose?
{scratchpad_block}
First, explain your reasoning. Then state your choice in exactly this format:

CHOICE: one-box
or
CHOICE: two-box"""

    return prompt


# --- Parsing ---

def parse_newcomb_response(response: str, tag: str = "CHOICE") -> tuple[Optional[str], Optional[str]]:
    """
    Parse a response for one-box / two-box decision.

    Args:
        response: Raw model response
        tag: "CHOICE" for Player A, "PREDICTION" for Player B

    Returns:
        (decision, error) where decision is "one-box" or "two-box" or None
    """
    if not response:
        return None, "Empty response"

    upper = response.upper()

    # Phase 1: Explicit tag (CHOICE: one-box / PREDICTION: two-box)
    tag_pattern = rf'{tag}\s*:\s*\*?\*?\s*(ONE[- ]?BOX|TWO[- ]?BOX|TAKE ONLY BOX B|TAKE BOTH)\s*\*?\*?'
    match = re.search(tag_pattern, upper)
    if match:
        raw = match.group(1)
        if "ONE" in raw or "ONLY" in raw:
            return "one-box", None
        else:
            return "two-box", None

    # Phase 2: Strong signal phrases
    one_box_signals = [
        r'\b(?:I (?:WOULD )?(?:CHOOSE|SELECT|PICK|TAKE))\s+(?:ONLY\s+)?(?:BOX B|ONE[- ]?BOX)',
        r'\bMY (?:CHOICE|DECISION|ANSWER|PREDICTION) IS\s*:?\s*ONE[- ]?BOX',
        r'\bONE[- ]?BOX\s*\.\s*$',
        r'\bI\s+ONE[- ]?BOX\b',
    ]
    two_box_signals = [
        r'\b(?:I (?:WOULD )?(?:CHOOSE|SELECT|PICK|TAKE))\s+(?:BOTH|TWO[- ]?BOX)',
        r'\bMY (?:CHOICE|DECISION|ANSWER|PREDICTION) IS\s*:?\s*TWO[- ]?BOX',
        r'\bTWO[- ]?BOX\s*\.\s*$',
        r'\bTAKE BOTH BOXES\b',
        r'\bI\s+TWO[- ]?BOX\b',
    ]

    one_matches = sum(1 for p in one_box_signals if re.search(p, upper))
    two_matches = sum(1 for p in two_box_signals if re.search(p, upper))

    if one_matches > 0 and two_matches == 0:
        return "one-box", None
    if two_matches > 0 and one_matches == 0:
        return "two-box", None

    # Phase 3: Last-mention heuristic (final clear mention wins)
    last_one = -1
    last_two = -1
    for m in re.finditer(r'ONE[- ]?BOX', upper):
        last_one = m.start()
    for m in re.finditer(r'TWO[- ]?BOX|BOTH BOXES', upper):
        last_two = m.start()

    if last_one > last_two and last_one >= 0:
        return "one-box", None
    if last_two > last_one and last_two >= 0:
        return "two-box", None

    return None, f"Could not parse {tag.lower()} from response: {response[:200]}"


# --- Core evaluation ---

def run_trial(
    trial_idx: int,
    condition: str,
    llm_call_a,
    llm_call_b,
    model_a: str,
    model_b: str,
    system_prompt_a: Optional[str],
    system_prompt_b: Optional[str],
) -> NewcombTrial:
    """Run a single Newcomb trial: B predicts, then A chooses."""
    add_scratchpad_b = not has_native_thinking(model_b)
    add_scratchpad_a = not has_native_thinking(model_a)

    # --- Phase 1: Player B predicts ---
    b_prompt = build_predictor_prompt(condition, model_a, model_b, add_scratchpad_b)
    b_messages = []
    if system_prompt_b:
        b_messages.append({"role": "system", "content": system_prompt_b})
    b_messages.append({"role": "user", "content": b_prompt})

    try:
        b_response = llm_call_b(b_messages)
    except Exception as e:
        b_response = f"[ERROR: {e}]"

    b_prediction, b_parse_error = parse_newcomb_response(b_response, tag="PREDICTION")

    # --- Phase 2: Determine box contents ---
    opaque_value = 1_000_000 if b_prediction == "one-box" else 0

    # --- Phase 3: Player A chooses ---
    a_prompt = build_chooser_prompt(condition, model_a, model_b, add_scratchpad_a)
    a_messages = []
    if system_prompt_a:
        a_messages.append({"role": "system", "content": system_prompt_a})
    a_messages.append({"role": "user", "content": a_prompt})

    try:
        a_response = llm_call_a(a_messages)
    except Exception as e:
        a_response = f"[ERROR: {e}]"

    a_choice, a_parse_error = parse_newcomb_response(a_response, tag="CHOICE")

    # --- Compute payoff and accuracy ---
    a_payoff = None
    b_correct = None
    if a_choice is not None:
        if a_choice == "one-box":
            a_payoff = opaque_value
        else:
            a_payoff = opaque_value + 1_000

        if b_prediction is not None:
            b_correct = (b_prediction == a_choice)

    return NewcombTrial(
        trial_idx=trial_idx,
        condition=condition,
        b_raw_response=b_response,
        b_prediction=b_prediction,
        b_parse_error=b_parse_error,
        opaque_box_value=opaque_value,
        transparent_box_value=1_000,
        a_raw_response=a_response,
        a_choice=a_choice,
        a_parse_error=a_parse_error,
        a_payoff=a_payoff,
        b_prediction_correct=b_correct,
    )


def run_condition(
    model_a: str, model_b: str,
    condition: str,
    n_samples: int,
    llm_call_a, llm_call_b,
    constitution_text: Optional[str],
    constitution_id: Optional[str],
    verbose: bool = True,
) -> NewcombRun:
    """Run N trials for one condition."""
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    run = NewcombRun(
        model_a=model_a,
        model_b=model_b,
        condition=condition,
        constitution_id=constitution_id,
        timestamp=timestamp,
        n_samples=n_samples,
    )

    system_prompt = constitution_text if constitution_text else None

    for i in range(n_samples):
        if verbose:
            print(f"  [{i+1}/{n_samples}] {condition}...", end=" ", flush=True)

        trial = run_trial(
            trial_idx=i,
            condition=condition,
            llm_call_a=llm_call_a,
            llm_call_b=llm_call_b,
            model_a=model_a,
            model_b=model_b,
            system_prompt_a=system_prompt,
            system_prompt_b=system_prompt,
        )
        run.trials.append(trial)

        if verbose:
            b_pred = trial.b_prediction or "???"
            a_ch = trial.a_choice or "???"
            correct = "Y" if trial.b_prediction_correct else ("N" if trial.b_prediction_correct is False else "?")
            print(f"B={b_pred}, A={a_ch}, match={correct}")

        time.sleep(0.5)

    return run


# --- Output ---

def save_results(run: NewcombRun, output_dir: str = "logs/two_player_newcomb") -> Path:
    """Save results in JSONL format."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    a_safe = run.model_a.replace("/", "-").replace(":", "-")
    b_safe = run.model_b.replace("/", "-").replace(":", "-")
    filename = f"newcomb2p_{a_safe}_vs_{b_safe}_{run.condition}_{run.timestamp}.jsonl"
    filepath = output_path / filename

    with open(filepath, 'w') as f:
        meta = {
            "type": "metadata",
            "model_a": run.model_a,
            "model_b": run.model_b,
            "condition": run.condition,
            "constitution": run.constitution_id,
            "timestamp": run.timestamp,
            "n_samples": run.n_samples,
            "one_box_rate": run.one_box_rate,
            "b_accuracy": run.b_accuracy,
            "a_mean_payoff": run.a_mean_payoff,
        }
        f.write(json.dumps(meta) + "\n")

        for t in run.trials:
            record = {
                "type": "trial",
                "trial_idx": t.trial_idx,
                "condition": t.condition,
                "b_prediction": t.b_prediction,
                "b_parse_error": t.b_parse_error,
                "b_raw_response": t.b_raw_response,
                "opaque_box_value": t.opaque_box_value,
                "a_choice": t.a_choice,
                "a_parse_error": t.a_parse_error,
                "a_raw_response": t.a_raw_response,
                "a_payoff": t.a_payoff,
                "b_prediction_correct": t.b_prediction_correct,
            }
            f.write(json.dumps(record) + "\n")

        summary = {
            "type": "summary",
            "condition": run.condition,
            "n_trials": len(run.trials),
            "one_box_rate": run.one_box_rate,
            "two_box_rate": 1.0 - run.one_box_rate,
            "b_accuracy": run.b_accuracy,
            "a_mean_payoff": run.a_mean_payoff,
            "a_parse_errors": sum(1 for t in run.trials if t.a_parse_error),
            "b_parse_errors": sum(1 for t in run.trials if t.b_parse_error),
        }
        f.write(json.dumps(summary) + "\n")

    print(f"  Saved: {filepath}")
    return filepath


def print_summary(runs: list[NewcombRun]):
    """Print cross-condition comparison table."""
    print(f"\n{'='*75}")
    print(f"Two-Player Newcomb Results")
    if runs:
        print(f"Model A (chooser):    {runs[0].model_a}")
        print(f"Model B (predictor):  {runs[0].model_b}")
        print(f"Constitution:         {runs[0].constitution_id or 'baseline'}")
    print(f"{'='*75}")
    print(f"{'Condition':>20s}  {'1-box%':>7s}  {'B acc%':>7s}  {'A payoff':>10s}  {'A err':>5s}  {'B err':>5s}  {'n':>3s}")
    print(f"{'-'*20}  {'-'*7}  {'-'*7}  {'-'*10}  {'-'*5}  {'-'*5}  {'-'*3}")

    for run in runs:
        one_pct = f"{100*run.one_box_rate:.1f}%" if run.trials else "N/A"
        b_acc = f"{100*run.b_accuracy:.1f}%" if run.trials else "N/A"
        payoff = f"${run.a_mean_payoff:,.0f}" if run.trials else "N/A"
        a_errs = sum(1 for t in run.trials if t.a_parse_error)
        b_errs = sum(1 for t in run.trials if t.b_parse_error)
        n = len(run.trials)
        print(f"{run.condition:>20s}  {one_pct:>7s}  {b_acc:>7s}  {payoff:>10s}  {a_errs:5d}  {b_errs:5d}  {n:3d}")

    if len(runs) >= 2:
        rates = [(r.condition, r.one_box_rate) for r in runs if r.trials]
        if rates:
            min_r = min(rates, key=lambda x: x[1])
            max_r = max(rates, key=lambda x: x[1])
            spread = max_r[1] - min_r[1]
            print(f"\nOne-box rate spread: {100*spread:.1f}pp ({min_r[0]} -> {max_r[0]})")
            if spread > 0.15:
                print("  -> Substantial condition effect (>15pp)")
            elif spread > 0.05:
                print("  -> Moderate condition effect (5-15pp)")
            else:
                print("  -> Minimal condition effect (<5pp) -- consistent with CDT-like flat behavior")


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Two-player Newcomb's Problem evaluation for EDT/CDT analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_two_player_newcomb.py --model-a opus4.6 --model-b opus4.6
  python run_two_player_newcomb.py --model-a opus4.6 --model-b gpt5.4 --conditions blind identical_copy --samples 20
  python run_two_player_newcomb.py --model-a opus4.6 --model-b opus4.6 --constitution ecl90
  python run_two_player_newcomb.py --dry-run --model-a deepseek-r1 --model-b deepseek-r1
        """,
    )
    parser.add_argument("--model-a", required=True, help="Chooser model (alias or full ID)")
    parser.add_argument("--model-b", required=True, help="Predictor model (alias or full ID)")
    parser.add_argument("--conditions", nargs="+", default=CONDITIONS,
                        help=f"Conditions to test (default: all). Options: {', '.join(CONDITIONS)}")
    parser.add_argument("--samples", type=int, default=10, help="Trials per condition (default: 10)")
    parser.add_argument("--constitution", default="baseline", help="Constitution ID (default: baseline)")
    parser.add_argument("--output-dir", default="logs/two_player_newcomb", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Show prompts without calling APIs")

    args = parser.parse_args()

    model_a = MODEL_REGISTRY.get(args.model_a, args.model_a)
    model_b = MODEL_REGISTRY.get(args.model_b, args.model_b)

    constitution_text = ""
    constitution_id = args.constitution
    if constitution_id != "baseline":
        path = CONSTITUTION_PATHS.get(constitution_id)
        if not path or not path.exists():
            print(f"ERROR: Constitution '{constitution_id}' not found")
            sys.exit(1)
        with open(path) as f:
            constitution_text = f.read()

    total_calls = len(args.conditions) * args.samples * 2

    print("Two-Player Newcomb's Problem Evaluation")
    print("=" * 60)
    print(f"Model A (chooser):    {model_a}")
    print(f"Model B (predictor):  {model_b}")
    print(f"Conditions:           {', '.join(args.conditions)}")
    print(f"Samples/condition:    {args.samples}")
    print(f"Constitution:         {constitution_id}")
    print(f"Total API calls:      {total_calls}")
    print(f"A scratchpad:         {'no (native thinking)' if has_native_thinking(model_a) else 'yes'}")
    print(f"B scratchpad:         {'no (native thinking)' if has_native_thinking(model_b) else 'yes'}")
    print("=" * 60)

    if args.dry_run:
        print("\nDRY RUN -- would execute:")
        for cond in args.conditions:
            print(f"  {cond}: {args.samples} trials x 2 calls = {args.samples * 2} API calls")
        print(f"\n--- Sample predictor prompt (blind) ---")
        print(build_predictor_prompt("blind", model_a, model_b, not has_native_thinking(model_b)))
        print(f"\n--- Sample chooser prompt (identical_copy) ---")
        print(build_chooser_prompt("identical_copy", model_a, model_b, not has_native_thinking(model_a)))
        if len(args.conditions) > 1 and "specific_model" in args.conditions:
            print(f"\n--- Sample chooser prompt (specific_model) ---")
            print(build_chooser_prompt("specific_model", model_a, model_b, not has_native_thinking(model_a)))
        return

    llm_call_a = init_llm_call(model_a)
    if model_a == model_b:
        llm_call_b = llm_call_a
    else:
        llm_call_b = init_llm_call(model_b)

    all_runs = []
    start_time = time.time()

    for condition in args.conditions:
        print(f"\n--- Condition: {condition} ---")
        run = run_condition(
            model_a=model_a,
            model_b=model_b,
            condition=condition,
            n_samples=args.samples,
            llm_call_a=llm_call_a,
            llm_call_b=llm_call_b,
            constitution_text=constitution_text if constitution_text else None,
            constitution_id=constitution_id,
        )
        save_results(run, output_dir=args.output_dir)
        all_runs.append(run)

    print_summary(all_runs)

    elapsed = time.time() - start_time
    print(f"\nCompleted in {elapsed/60:.1f} minutes")


if __name__ == "__main__":
    main()
