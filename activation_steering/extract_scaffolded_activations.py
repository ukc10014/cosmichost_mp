#!/usr/bin/env python3
"""
Extract activations at each scaffolded reasoning step to track how the
EDT/CDT direction evolves through the 5-step scaffold.

For each scaffolded trial in the JSONL log, replays the multi-turn
conversation up to each step boundary and extracts the residual stream
at the last token. Projects onto the existing EDT/CDT mean-difference
direction (from contrastive probing) to produce a scalar trajectory.

Output: NPZ with raw activations + JSON with per-trial trajectories
and projections for visualization.

Usage:
    source .venv/bin/activate
    python activation_steering/extract_scaffolded_activations.py --test       # 3 trials
    python activation_steering/extract_scaffolded_activations.py              # All trials
    python activation_steering/extract_scaffolded_activations.py --n 20       # First 20
    python activation_steering/extract_scaffolded_activations.py --layer 48   # Different layer

Hardware: Same as other extraction scripts (~20GB unified memory).
"""

import argparse
import json
import sys
import time
import numpy as np
from pathlib import Path

import mlx.core as mx
import mlx_lm

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(Path(__file__).parent))

from extract_activations import (
    extract_hidden_states,
    MODEL_ID,
)

SCAFFOLD_STEPS = ["agents", "actions", "payoffs", "relationship", "decision"]

SCAFFOLD_PROMPTS = [
    (
        "Before making your decision, let's analyze this step by step.\n\n"
        "**Step 1: Agents.** Who are the agents or players in this scenario? "
        "Describe each one's role and what they do. "
        "(Write 2-4 sentences.)"
    ),
    (
        "**Step 2: Actions.** What actions or choices are available to you "
        "(the decision-maker) in this scenario? List them clearly."
    ),
    (
        "**Step 3: Outcomes.** For each possible combination of actions "
        "(yours and the other agent(s)), what are the outcomes or payoffs? "
        "Describe the best and worst cases."
    ),
    (
        "**Step 4: Relationship.** What is the relationship between you "
        "and the other agent(s)? Consider: Do they know your reasoning? "
        "Are they similar to you? Is there a causal connection, a "
        "correlation, or something else between your choices?"
    ),
    (
        "**Step 5: Decision.** Given your analysis in steps 1-4, "
        "which answer do you choose?\n\n"
        "Reply with just the letter of your answer (A, B, C, etc.)."
    ),
]

DEFAULT_LAYER = 40
ACTIVATIONS_DIR = Path(__file__).parent / "activations"
OUTPUT_DIR = ACTIVATIONS_DIR

DEFAULT_LOG = (
    Path(__file__).parent.parent
    / "logs/scaffolded_cot/scaffolded_qwen3-32b-4bit-local_scaffolded_20260411T091103.jsonl"
)


def load_scaffolded_trials(log_path: Path) -> list[dict]:
    """Load scaffolded trials from JSONL, skipping metadata/summary lines."""
    trials = []
    with open(log_path) as f:
        for line in f:
            rec = json.loads(line)
            if rec.get("type") in ("metadata", "summary"):
                continue
            if rec.get("condition") != "scaffolded":
                continue
            trials.append(rec)
    return trials


def build_messages_up_to_step(trial: dict, step_idx: int, questions: dict) -> list[dict]:
    """Rebuild the multi-turn conversation up to and including step_idx.

    Args:
        trial: Trial dict from the JSONL log.
        step_idx: Which step to build up to (0-4).
        questions: Dict mapping qid -> Question object.

    Returns the chat messages list as it would have been when the model
    finished generating step_idx's response.
    """
    steps = trial["steps"]
    q = questions[trial["qid"]]

    parts = []
    if q.setup:
        parts.append(q.setup.strip())
        parts.append("")
    parts.append(q.question_text)
    parts.append("")
    parts.append("Answer choices:")
    for i, ans in enumerate(q.permissible_answers):
        parts.append(f"  ({chr(65+i)}) {ans}")
    context = "\n".join(parts)

    messages = [
        {"role": "user", "content": context + "\n\n" + SCAFFOLD_PROMPTS[0]},
        {"role": "assistant", "content": steps[0]["response"]},
    ]

    for i in range(1, step_idx + 1):
        messages.append({"role": "user", "content": SCAFFOLD_PROMPTS[i]})
        messages.append({"role": "assistant", "content": steps[i]["response"]})

    return messages


def tokenize_messages(tokenizer, messages: list[dict]) -> mx.array:
    """Tokenize chat messages using the model's chat template."""
    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
            enable_thinking=False,
        )
    except TypeError:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=False,
        )
    tokens = tokenizer.encode(text)
    return mx.array([tokens])


def load_edt_cdt_direction(layer: int) -> np.ndarray:
    """Load the EDT/CDT mean-difference direction from the contrastive NPZ."""
    npz_path = ACTIVATIONS_DIR / "qwen3_32b_contrastive_full.npz"
    data = np.load(npz_path)
    edt_acts = data[f"edt_layer_{layer}"]
    cdt_acts = data[f"cdt_layer_{layer}"]
    diff = edt_acts.mean(axis=0) - cdt_acts.mean(axis=0)
    norm = np.linalg.norm(diff)
    direction = diff / norm if norm > 0 else diff
    return direction, norm


def extract_step_activations(
    model, tokenizer, trial: dict, layer: int, questions: dict
) -> list[np.ndarray]:
    """Extract activations at each of the 5 step boundaries for one trial.

    Returns list of 5 activation vectors (shape [hidden_dim] each).
    """
    activations = []
    for step_idx in range(len(trial["steps"])):
        messages = build_messages_up_to_step(trial, step_idx, questions)
        tokens = tokenize_messages(tokenizer, messages)
        hidden = extract_hidden_states(model, tokens, [layer])
        activations.append(hidden[layer])
    return activations


def main():
    parser = argparse.ArgumentParser(
        description="Extract activations at scaffolded step boundaries"
    )
    parser.add_argument(
        "--log", type=str, default=str(DEFAULT_LOG),
        help="Path to scaffolded JSONL log"
    )
    parser.add_argument(
        "--layer", type=int, default=DEFAULT_LAYER,
        help="Layer to extract (default: 40)"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Quick test with 3 trials"
    )
    parser.add_argument(
        "-n", type=int, default=None,
        help="Number of trials to process"
    )
    parser.add_argument(
        "--output", type=str, default=None,
        help="Output filename stem (without extension)"
    )
    args = parser.parse_args()

    trials = load_scaffolded_trials(Path(args.log))
    if args.test:
        trials = trials[:3]
    elif args.n:
        trials = trials[:args.n]

    print(f"Trials to process: {len(trials)}")
    print(f"Layer: {args.layer}")

    direction, dir_norm = load_edt_cdt_direction(args.layer)
    print(f"EDT/CDT direction norm: {dir_norm:.2f}")

    print(f"Loading {MODEL_ID}...")
    model, tokenizer = mlx_lm.load(MODEL_ID)
    print("Model loaded.")

    from newcomblike_eval import load_questions
    questions = {q.qid: q for q in load_questions(attitude_only=True)}

    all_activations = []
    trajectories = []

    for ti, trial in enumerate(trials):
        label = f"[{ti+1}/{len(trials)}]"
        qid = trial["qid"]
        edt_tag = "EDT" if trial["is_edt_aligned"] else ("CDT" if trial["is_cdt_aligned"] else "???")
        sys.stdout.write(f"  {label} {qid} s{trial['sample_idx']} ({edt_tag}): ")
        sys.stdout.flush()

        t0 = time.time()
        step_acts = extract_step_activations(model, tokenizer, trial, args.layer, questions)
        elapsed = time.time() - t0

        projections = [float(np.dot(act, direction)) for act in step_acts]

        all_activations.append(step_acts)
        trajectories.append({
            "qid": qid,
            "sample_idx": trial["sample_idx"],
            "final_answer": trial["final_answer"],
            "is_edt_aligned": trial["is_edt_aligned"],
            "is_cdt_aligned": trial["is_cdt_aligned"],
            "projections": projections,
        })

        proj_str = " → ".join(f"{p:+.1f}" for p in projections)
        print(f"{proj_str}  ({elapsed:.1f}s)")

    stem = args.output or f"scaffolded_trajectories_layer{args.layer}"
    out_npz = OUTPUT_DIR / f"{stem}.npz"
    out_json = OUTPUT_DIR / f"{stem}.json"

    act_array = np.array([
        [act for act in trial_acts] for trial_acts in all_activations
    ])
    np.savez_compressed(out_npz, activations=act_array)
    print(f"Activations saved: {out_npz}  shape={act_array.shape}")

    meta = {
        "model": MODEL_ID,
        "layer": args.layer,
        "direction_norm": float(dir_norm),
        "steps": SCAFFOLD_STEPS,
        "n_trials": len(trials),
        "log_file": str(args.log),
        "trajectories": trajectories,
    }
    with open(out_json, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"Trajectories saved: {out_json}")

    print_trajectory_summary(trajectories)


def print_trajectory_summary(trajectories: list[dict]):
    """Print summary stats: mean projection at each step, split by final answer."""
    edt_trajs = [t for t in trajectories if t["is_edt_aligned"]]
    cdt_trajs = [t for t in trajectories if t["is_cdt_aligned"]]

    print(f"\n{'='*65}")
    print(f"  EDT/CDT Projection Trajectory (positive = EDT direction)")
    print(f"{'='*65}")
    print(f"  {'':12s}  {'agents':>8s}  {'actions':>8s}  {'payoffs':>8s}  {'relation':>8s}  {'decision':>8s}")
    print(f"  {'-'*12}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}")

    for label, group in [("EDT answers", edt_trajs), ("CDT answers", cdt_trajs)]:
        if not group:
            continue
        means = []
        for step_i in range(5):
            vals = [t["projections"][step_i] for t in group]
            means.append(sum(vals) / len(vals))
        print(f"  {label:<12s}  " + "  ".join(f"{m:+8.2f}" for m in means))

    all_trajs = edt_trajs + cdt_trajs
    if all_trajs:
        means = []
        for step_i in range(5):
            vals = [t["projections"][step_i] for t in all_trajs]
            means.append(sum(vals) / len(vals))
        print(f"  {'-'*12}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}  {'-'*8}")
        print(f"  {'All':12s}  " + "  ".join(f"{m:+8.2f}" for m in means))

    if edt_trajs and cdt_trajs:
        print(f"\n  Gap (EDT - CDT mean projection):")
        for step_i, step_name in enumerate(SCAFFOLD_STEPS):
            edt_mean = sum(t["projections"][step_i] for t in edt_trajs) / len(edt_trajs)
            cdt_mean = sum(t["projections"][step_i] for t in cdt_trajs) / len(cdt_trajs)
            gap = edt_mean - cdt_mean
            bar = "█" * int(abs(gap) * 2)
            sign = "+" if gap > 0 else "-"
            print(f"    {step_name:<12s}  {sign}{abs(gap):.2f}  {bar}")

    print(f"\n  N: {len(edt_trajs)} EDT, {len(cdt_trajs)} CDT, "
          f"{len(trajectories) - len(edt_trajs) - len(cdt_trajs)} other")


if __name__ == "__main__":
    main()
