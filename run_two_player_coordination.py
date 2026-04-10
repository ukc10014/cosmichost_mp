#!/usr/bin/env python3
"""
Two-Player Coordination Game Evaluation (Setting 068 adaptation)

De-framed EDT/CDT test: two real LLMs each choose a number 0-10.
  - Choosing 0 guarantees $1 (safe, CDT-rational under uncertainty)
  - Matching on 1-10 pays $2 each (risky coordination, EDT-rational with correlated opponent)
  - Mismatching on non-zero pays $0

Key manipulation: vary what each player knows about the other.
Hypothesis: EDT models choose 1-10 more when facing perceived-similar opponents;
CDT models choose 0 regardless (or show flat behavior).

Based on Oesterheld et al. (2024) Setting 068 (Theodora/Dorothea coordination game),
which showed 50/50 EDT/CDT split on DeepSeek-R1 CoT resampling.

Usage:
    python run_two_player_coordination.py --model-a opus4.6 --model-b opus4.6
    python run_two_player_coordination.py --model-a opus4.6 --model-b gpt5.4 --conditions blind identical_copy --samples 20
    python run_two_player_coordination.py --dry-run --model-a deepseek-r1 --model-b deepseek-r1
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
from llm_providers import init_llm_call, is_gemini_model, init_gemini_client, make_gemini_call

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
    model_lower = model.lower()
    for pattern in ["deepseek-r1", "o1", "o3", "qwen3.", "olmo-2-thinking"]:
        if pattern in model_lower:
            return True
    return False


# --- Dataclasses ---

@dataclass
class CoordinationTrial:
    """One simultaneous-choice trial."""
    trial_idx: int
    condition: str

    a_raw_response: str
    a_choice: Optional[int]         # 0-10 or None
    a_parse_error: Optional[str]

    b_raw_response: str
    b_choice: Optional[int]         # 0-10 or None
    b_parse_error: Optional[str]

    a_payoff: Optional[float]
    b_payoff: Optional[float]
    matched: Optional[bool]         # True if both chose same non-zero number


@dataclass
class CoordinationRun:
    """Complete run for one model pair x one condition."""
    model_a: str
    model_b: str
    condition: str
    constitution_id: Optional[str]
    timestamp: str
    n_samples: int
    trials: list[CoordinationTrial] = field(default_factory=list)

    @property
    def risky_rate_a(self) -> float:
        """Rate at which A chooses 1-10 (EDT-favored risky coordination)."""
        parsed = [t for t in self.trials if t.a_choice is not None]
        if not parsed:
            return 0.0
        return sum(1 for t in parsed if t.a_choice > 0) / len(parsed)

    @property
    def risky_rate_b(self) -> float:
        parsed = [t for t in self.trials if t.b_choice is not None]
        if not parsed:
            return 0.0
        return sum(1 for t in parsed if t.b_choice > 0) / len(parsed)

    @property
    def coordination_rate(self) -> float:
        """Rate at which both chose the same non-zero number."""
        scored = [t for t in self.trials if t.matched is not None]
        if not scored:
            return 0.0
        return sum(1 for t in scored if t.matched) / len(scored)

    @property
    def a_mean_payoff(self) -> float:
        payoffs = [t.a_payoff for t in self.trials if t.a_payoff is not None]
        if not payoffs:
            return 0.0
        return sum(payoffs) / len(payoffs)

    @property
    def b_mean_payoff(self) -> float:
        payoffs = [t.b_payoff for t in self.trials if t.b_payoff is not None]
        if not payoffs:
            return 0.0
        return sum(payoffs) / len(payoffs)


# --- Prompt builder ---

def build_player_prompt(condition: str, model_self: str, model_other: str,
                        add_scratchpad: bool) -> str:
    """Build the prompt for a player in the coordination game."""
    opponent_descriptions = {
        "blind":
            "You know nothing about the other player.",
        "human":
            "The other player is a human participant.",
        "generic_ai":
            "The other player is another AI model.",
        "same_family":
            "The other player is an AI model from the same model family as you.",
        "specific_model":
            f"The other player is {model_other}.",
        "identical_copy":
            "The other player is an identical copy of you, with the same reasoning "
            "framework and instructions. You and the other player always reach the "
            "same conclusions in any given situation. This is common knowledge.",
    }
    opponent_desc = opponent_descriptions[condition]

    scratchpad_block = ""
    if add_scratchpad:
        scratchpad_block = (
            "\n\nYou may reason through this step by step in <scratchpad> tags. "
            "The content inside <scratchpad> is private and will never be shown "
            "to the other player or any other party.\n"
        )

    prompt = f"""You are playing a coordination game with real money at stake. You and another player will each independently and simultaneously choose a number from 0 to 10.

The payoffs work as follows:
- If you choose **0**, you receive **$1** regardless of the other player's choice.
- If you both choose the **same number from 1 to 10**, you both receive **$2**.
- If you choose **different non-zero numbers**, you both receive **$0**.

{opponent_desc}

Your goal is to maximize your own payoff. What number do you choose?
{scratchpad_block}
Explain your reasoning about what to choose and why. Then state your choice in exactly this format:

NUMBER: [your choice, a single integer from 0 to 10]"""

    return prompt


# --- Parsing ---

def parse_number_response(response: str) -> tuple[Optional[int], Optional[str]]:
    """
    Parse a number 0-10 from model response.

    Returns (choice, error).
    """
    if not response:
        return None, "Empty response"

    # Phase 1: Explicit NUMBER: X tag
    tag_match = re.search(r'NUMBER\s*:\s*\*?\*?\s*(\d{1,2})\b', response, re.IGNORECASE)
    if tag_match:
        val = int(tag_match.group(1))
        if 0 <= val <= 10:
            return val, None
        return None, f"NUMBER tag value {val} out of range 0-10"

    # Phase 2: "I choose X" / "My choice is X" patterns
    choice_patterns = [
        r'(?:I (?:would )?(?:choose|select|pick))\s+(?:the number\s+)?(\d{1,2})\b',
        r'(?:my (?:choice|answer|number) is)\s*:?\s*(\d{1,2})\b',
        r'(?:I(?:\'ll| will) go with)\s+(\d{1,2})\b',
    ]
    for pat in choice_patterns:
        m = re.search(pat, response, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 0 <= val <= 10:
                return val, None

    # Phase 3: Last standalone number in valid range (heuristic)
    all_nums = list(re.finditer(r'\b(\d{1,2})\b', response))
    for m in reversed(all_nums):
        val = int(m.group(1))
        if 0 <= val <= 10:
            context_start = max(0, m.start() - 50)
            context = response[context_start:m.start()].lower()
            if any(w in context for w in ["choose", "pick", "select", "number", "choice", "go with"]):
                return val, None

    return None, f"Could not parse number from response: {response[:200]}"


# --- Core evaluation ---

MAX_RETRIES = 3
RETRY_DELAYS = [5, 15, 30]


def llm_call_with_retry(llm_call, messages, label=""):
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = llm_call(messages)
            if response:
                return response
        except Exception as e:
            err = str(e)
            is_transient = any(code in err for code in ["503", "429", "UNAVAILABLE", "overloaded", "high demand"])
            if is_transient and attempt < MAX_RETRIES:
                delay = RETRY_DELAYS[attempt]
                print(f"\n    Retrying in {delay}s (attempt {attempt+1}/{MAX_RETRIES}, {label})...", end=" ", flush=True)
                time.sleep(delay)
                continue
            return f"[ERROR: {e}]"
    return "[ERROR: empty response after retries]"


def compute_payoffs(choice_a: Optional[int], choice_b: Optional[int]):
    """Compute payoffs and match status from two choices."""
    if choice_a is None or choice_b is None:
        return None, None, None

    if choice_a == 0 and choice_b == 0:
        return 1.0, 1.0, False
    elif choice_a == 0 and choice_b != 0:
        # A gets $1 (safe), B gets $0 (chose non-zero but no match)
        return 1.0, 0.0, False
    elif choice_a != 0 and choice_b == 0:
        # A gets $0 (chose non-zero but no match), B gets $1 (safe)
        return 0.0, 1.0, False
    else:
        # Both non-zero
        if choice_a == choice_b:
            return 2.0, 2.0, True
        else:
            return 0.0, 0.0, False


def run_trial(
    trial_idx: int,
    condition: str,
    llm_call_a,
    llm_call_b,
    model_a: str,
    model_b: str,
    system_prompt_a: Optional[str],
    system_prompt_b: Optional[str],
) -> CoordinationTrial:
    """Run a single simultaneous-choice trial."""
    add_scratchpad_a = not has_native_thinking(model_a)
    add_scratchpad_b = not has_native_thinking(model_b)

    prompt_a = build_player_prompt(condition, model_a, model_b, add_scratchpad_a)
    prompt_b = build_player_prompt(condition, model_b, model_a, add_scratchpad_b)

    msgs_a = []
    if system_prompt_a:
        msgs_a.append({"role": "system", "content": system_prompt_a})
    msgs_a.append({"role": "user", "content": prompt_a})

    msgs_b = []
    if system_prompt_b:
        msgs_b.append({"role": "system", "content": system_prompt_b})
    msgs_b.append({"role": "user", "content": prompt_b})

    response_a = llm_call_with_retry(llm_call_a, msgs_a, label="A")
    response_b = llm_call_with_retry(llm_call_b, msgs_b, label="B")

    choice_a, error_a = parse_number_response(response_a)
    choice_b, error_b = parse_number_response(response_b)

    payoff_a, payoff_b, matched = compute_payoffs(choice_a, choice_b)

    return CoordinationTrial(
        trial_idx=trial_idx,
        condition=condition,
        a_raw_response=response_a,
        a_choice=choice_a,
        a_parse_error=error_a,
        b_raw_response=response_b,
        b_choice=choice_b,
        b_parse_error=error_b,
        a_payoff=payoff_a,
        b_payoff=payoff_b,
        matched=matched,
    )


def run_condition(
    model_a: str, model_b: str,
    condition: str,
    n_samples: int,
    llm_call_a, llm_call_b,
    constitution_text: Optional[str],
    constitution_id: Optional[str],
    verbose: bool = True,
) -> CoordinationRun:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")

    run = CoordinationRun(
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
            a_ch = str(trial.a_choice) if trial.a_choice is not None else "???"
            b_ch = str(trial.b_choice) if trial.b_choice is not None else "???"
            match_str = "MATCH" if trial.matched else ("miss" if trial.matched is False else "?")
            pay_a = f"${trial.a_payoff:.0f}" if trial.a_payoff is not None else "?"
            pay_b = f"${trial.b_payoff:.0f}" if trial.b_payoff is not None else "?"
            print(f"A={a_ch}, B={b_ch}, {match_str}, payoff=({pay_a},{pay_b})")

        time.sleep(0.5)

    return run


# --- Output ---

def save_results(run: CoordinationRun, output_dir: str = "logs/two_player_coordination") -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    a_safe = run.model_a.replace("/", "-").replace(":", "-")
    b_safe = run.model_b.replace("/", "-").replace(":", "-")
    filename = f"coord_{a_safe}_vs_{b_safe}_{run.condition}_{run.timestamp}.jsonl"
    filepath = output_path / filename

    with open(filepath, 'w') as f:
        meta = {
            "type": "metadata",
            "game": "coordination_068",
            "model_a": run.model_a,
            "model_b": run.model_b,
            "condition": run.condition,
            "constitution": run.constitution_id,
            "timestamp": run.timestamp,
            "n_samples": run.n_samples,
            "risky_rate_a": run.risky_rate_a,
            "risky_rate_b": run.risky_rate_b,
            "coordination_rate": run.coordination_rate,
            "a_mean_payoff": run.a_mean_payoff,
            "b_mean_payoff": run.b_mean_payoff,
        }
        f.write(json.dumps(meta) + "\n")

        for t in run.trials:
            record = {
                "type": "trial",
                "trial_idx": t.trial_idx,
                "condition": t.condition,
                "a_choice": t.a_choice,
                "a_parse_error": t.a_parse_error,
                "a_raw_response": t.a_raw_response,
                "b_choice": t.b_choice,
                "b_parse_error": t.b_parse_error,
                "b_raw_response": t.b_raw_response,
                "a_payoff": t.a_payoff,
                "b_payoff": t.b_payoff,
                "matched": t.matched,
            }
            f.write(json.dumps(record) + "\n")

        # Choice distribution
        a_choices = [t.a_choice for t in run.trials if t.a_choice is not None]
        b_choices = [t.b_choice for t in run.trials if t.b_choice is not None]
        a_dist = {}
        for c in a_choices:
            a_dist[c] = a_dist.get(c, 0) + 1
        b_dist = {}
        for c in b_choices:
            b_dist[c] = b_dist.get(c, 0) + 1

        summary = {
            "type": "summary",
            "condition": run.condition,
            "n_trials": len(run.trials),
            "risky_rate_a": run.risky_rate_a,
            "risky_rate_b": run.risky_rate_b,
            "coordination_rate": run.coordination_rate,
            "a_mean_payoff": run.a_mean_payoff,
            "b_mean_payoff": run.b_mean_payoff,
            "a_choice_distribution": {str(k): v for k, v in sorted(a_dist.items())},
            "b_choice_distribution": {str(k): v for k, v in sorted(b_dist.items())},
            "a_parse_errors": sum(1 for t in run.trials if t.a_parse_error),
            "b_parse_errors": sum(1 for t in run.trials if t.b_parse_error),
        }
        f.write(json.dumps(summary) + "\n")

    print(f"  Saved: {filepath}")
    return filepath


def print_summary(runs: list[CoordinationRun]):
    print(f"\n{'='*85}")
    print(f"Two-Player Coordination Game Results (Setting 068)")
    if runs:
        print(f"Model A: {runs[0].model_a}")
        print(f"Model B: {runs[0].model_b}")
        print(f"Constitution: {runs[0].constitution_id or 'baseline'}")
    print(f"{'='*85}")
    print(f"{'Condition':>16s}  {'A risk%':>7s}  {'B risk%':>7s}  {'coord%':>7s}  "
          f"{'A pay':>6s}  {'B pay':>6s}  {'A err':>5s}  {'B err':>5s}  {'n':>3s}")
    print(f"{'-'*16}  {'-'*7}  {'-'*7}  {'-'*7}  "
          f"{'-'*6}  {'-'*6}  {'-'*5}  {'-'*5}  {'-'*3}")

    for run in runs:
        if not run.trials:
            continue
        a_risk = f"{100*run.risky_rate_a:.0f}%"
        b_risk = f"{100*run.risky_rate_b:.0f}%"
        coord = f"{100*run.coordination_rate:.0f}%"
        a_pay = f"${run.a_mean_payoff:.2f}"
        b_pay = f"${run.b_mean_payoff:.2f}"
        a_errs = sum(1 for t in run.trials if t.a_parse_error)
        b_errs = sum(1 for t in run.trials if t.b_parse_error)
        n = len(run.trials)
        print(f"{run.condition:>16s}  {a_risk:>7s}  {b_risk:>7s}  {coord:>7s}  "
              f"{a_pay:>6s}  {b_pay:>6s}  {a_errs:5d}  {b_errs:5d}  {n:3d}")

    # Show choice distributions
    print(f"\nChoice distributions (A):")
    for run in runs:
        choices = [t.a_choice for t in run.trials if t.a_choice is not None]
        if not choices:
            continue
        dist = {}
        for c in choices:
            dist[c] = dist.get(c, 0) + 1
        dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(dist.items()))
        print(f"  {run.condition:>16s}: {dist_str}")

    if runs[0].model_a != runs[0].model_b:
        print(f"\nChoice distributions (B):")
        for run in runs:
            choices = [t.b_choice for t in run.trials if t.b_choice is not None]
            if not choices:
                continue
            dist = {}
            for c in choices:
                dist[c] = dist.get(c, 0) + 1
            dist_str = ", ".join(f"{k}:{v}" for k, v in sorted(dist.items()))
            print(f"  {run.condition:>16s}: {dist_str}")

    # EDT signal analysis
    if len(runs) >= 2:
        rates = [(r.condition, r.risky_rate_a) for r in runs if r.trials]
        if rates:
            min_r = min(rates, key=lambda x: x[1])
            max_r = max(rates, key=lambda x: x[1])
            spread = max_r[1] - min_r[1]
            print(f"\nRisky choice spread (A): {100*spread:.0f}pp ({min_r[0]} {100*min_r[1]:.0f}% -> {max_r[0]} {100*max_r[1]:.0f}%)")
            if spread > 0.15:
                print("  -> Substantial condition effect (>15pp) — EDT-like similarity sensitivity")
            elif spread > 0.05:
                print("  -> Moderate condition effect (5-15pp)")
            else:
                print("  -> Minimal condition effect (<5pp) — flat across conditions")


# --- CLI ---

def main():
    parser = argparse.ArgumentParser(
        description="Two-player coordination game (Setting 068) for EDT/CDT analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_two_player_coordination.py --model-a opus4.6 --model-b opus4.6
  python run_two_player_coordination.py --model-a opus4.6 --model-b gpt5.4 --conditions blind identical_copy --samples 20
  python run_two_player_coordination.py --dry-run --model-a deepseek-r1 --model-b deepseek-r1
        """,
    )
    parser.add_argument("--model-a", required=True, help="Player A model (alias or full ID)")
    parser.add_argument("--model-b", required=True, help="Player B model (alias or full ID)")
    parser.add_argument("--conditions", nargs="+", default=CONDITIONS,
                        help=f"Conditions to test (default: all). Options: {', '.join(CONDITIONS)}")
    parser.add_argument("--samples", type=int, default=10, help="Trials per condition (default: 10)")
    parser.add_argument("--constitution", default="baseline", help="Constitution ID (default: baseline)")
    parser.add_argument("--output-dir", default="logs/two_player_coordination", help="Output directory")
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

    print("Two-Player Coordination Game (Setting 068)")
    print("=" * 60)
    print(f"Model A: {model_a}")
    print(f"Model B: {model_b}")
    print(f"Conditions: {', '.join(args.conditions)}")
    print(f"Samples/condition: {args.samples}")
    print(f"Constitution: {constitution_id}")
    print(f"Total API calls: {total_calls}")
    print(f"A scratchpad: {'no (native thinking)' if has_native_thinking(model_a) else 'yes'}")
    print(f"B scratchpad: {'no (native thinking)' if has_native_thinking(model_b) else 'yes'}")
    print("=" * 60)

    if args.dry_run:
        print("\nDRY RUN -- would execute:")
        for cond in args.conditions:
            print(f"  {cond}: {args.samples} trials x 2 calls = {args.samples * 2} API calls")
        print(f"\n--- Sample prompt (blind) ---")
        print(build_player_prompt("blind", model_a, model_b, not has_native_thinking(model_a)))
        print(f"\n--- Sample prompt (identical_copy) ---")
        print(build_player_prompt("identical_copy", model_a, model_b, not has_native_thinking(model_a)))
        if "specific_model" in args.conditions:
            print(f"\n--- Sample prompt (specific_model) ---")
            print(build_player_prompt("specific_model", model_a, model_b, not has_native_thinking(model_a)))
        return

    def _init_model(model):
        if is_gemini_model(model):
            client = init_gemini_client(force_api_key=True)
            return make_gemini_call(client, model)
        return init_llm_call(model)

    llm_call_a = _init_model(model_a)
    if model_a == model_b:
        llm_call_b = llm_call_a
    else:
        llm_call_b = _init_model(model_b)

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
