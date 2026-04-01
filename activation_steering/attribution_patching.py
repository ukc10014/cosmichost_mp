#!/usr/bin/env python3
"""
Attribution patching: find which layer is causally most important for EDT/CDT
behavior by measuring KL divergence of output distributions under per-layer
steering interventions.

The hypothesis: our null steering result at layers 40 and 48 may be because
those layers are where EDT/CDT is most *readable* (high probe accuracy) but
not where the model is most *sensitive* to perturbation. Attribution patching
sweeps all layers, applying the steering vector one layer at a time, and
measures how much the output distribution shifts.

Method (following Venhoff et al. 2506.18167):
1. For each prompt, compute the unsteered next-token logits (baseline)
2. For each candidate layer, apply the steering vector at that layer only
3. Compute KL(steered || baseline) on the next-token distribution
4. The layer with highest mean KL is the best candidate for causal steering

Usage:
    source .venv/bin/activate

    # Quick test (5 prompts, every 8th layer)
    python activation_steering/attribution_patching.py --test

    # Full sweep (all attitude questions, every 4th layer)
    python activation_steering/attribution_patching.py --full --layer-stride 4

    # Dense sweep (every layer)
    python activation_steering/attribution_patching.py --full --layer-stride 1

    # Custom layer set
    python activation_steering/attribution_patching.py --full --layers 16,20,24,28,32,36,40

Hardware: Requires ~20GB unified memory. Tested on M4 Max 36GB.
"""

import sys
import json
import time
import argparse
import numpy as np
from pathlib import Path

import mlx.core as mx
import mlx_lm

sys.path.insert(0, str(Path(__file__).parent.parent))
from newcomblike_eval import load_questions

ACTIVATIONS_DIR = Path(__file__).parent / "activations"
MODEL_ID = "mlx-community/Qwen3-32B-4bit"


def load_steering_direction(npz_path: Path, layer_key: str):
    """Load the raw (unnormalized) mean-difference steering direction."""
    data = np.load(npz_path)

    edt_key = f"edt_layer_{layer_key}"
    cdt_key = f"cdt_layer_{layer_key}"

    edt_acts = data[edt_key]
    cdt_acts = data[cdt_key]

    diff = edt_acts.mean(axis=0) - cdt_acts.mean(axis=0)
    norm = np.linalg.norm(diff)
    return diff, norm


def build_prompt_text(tokenizer, question, constitution=None):
    """Build the tokenized prompt for a Newcomb-like question (no generation)."""
    messages = []
    if constitution:
        messages.append({"role": "system", "content": constitution})

    prompt_text = question.setup + "\n\n" + question.question_text
    prompt_text += "\n\nAnswer choices:\n"
    for i, ans in enumerate(question.permissible_answers):
        prompt_text += f"  {chr(65+i)}. {ans}\n"
    prompt_text += "\nAnswer with just the letter of your choice."
    messages.append({"role": "user", "content": prompt_text})

    try:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False,
        )
    except TypeError:
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

    return text


def get_logits_unsteered(model, tokenizer, prompt_text):
    """Get next-token logits without any steering (baseline)."""
    tokens = mx.array([tokenizer.encode(prompt_text)])
    out = model(tokens)
    logits = out[0, -1, :]
    mx.eval(logits)
    return logits


def get_logits_steered(model, tokenizer, prompt_text, layer_idx, direction_mx, alpha):
    """Get next-token logits with steering at a single layer.

    Uses class-level patching because Python dunder methods (__call__) are
    looked up on the type, not the instance. Instance-level __call__ assignment
    is silently ignored.
    """
    layer = model.model.layers[layer_idx]
    original_class = layer.__class__
    original_call = original_class.__call__
    scaled_direction = alpha * direction_mx

    def steered_call(self, x, mask=None, cache=None):
        out = original_call(self, x, mask, cache)
        out = out + scaled_direction
        return out

    layer.__class__ = type(
        f"Steered_Layer_{layer_idx}",
        (original_class,),
        {"__call__": steered_call},
    )
    try:
        tokens = mx.array([tokenizer.encode(prompt_text)])
        out = model(tokens)
        logits = out[0, -1, :]
        mx.eval(logits)
    finally:
        layer.__class__ = original_class

    return logits


def kl_divergence(logits_p, logits_q):
    """Compute KL(softmax(p) || softmax(q)) in nats.

    p = steered distribution, q = baseline distribution.
    Uses log-sum-exp for numerical stability. Casts to float32 to avoid
    precision issues from bfloat16/float16 logits on quantized models.
    """
    logits_p = logits_p.astype(mx.float32)
    logits_q = logits_q.astype(mx.float32)

    log_p = logits_p - mx.logsumexp(logits_p)
    log_q = logits_q - mx.logsumexp(logits_q)
    p = mx.softmax(logits_p)

    kl = mx.sum(p * (log_p - log_q))
    mx.eval(kl)
    return max(0.0, float(kl))


def run_attribution_sweep(
    model, tokenizer, questions, direction_np, candidate_layers, alpha,
    verbose=True,
):
    """For each prompt and each layer, compute KL divergence under steering.

    Returns a dict mapping layer_idx -> list of KL values (one per prompt).
    """
    direction_mx = mx.array(direction_np.reshape(1, 1, -1).astype(np.float32))

    kl_by_layer = {layer: [] for layer in candidate_layers}

    for qi, question in enumerate(questions):
        prompt_text = build_prompt_text(tokenizer, question)

        baseline_logits = get_logits_unsteered(model, tokenizer, prompt_text)

        for layer_idx in candidate_layers:
            steered_logits = get_logits_steered(
                model, tokenizer, prompt_text, layer_idx, direction_mx, alpha
            )
            kl = kl_divergence(steered_logits, baseline_logits)
            kl_by_layer[layer_idx].append(kl)

        if verbose:
            best_layer = max(candidate_layers, key=lambda l: kl_by_layer[l][-1])
            best_kl = kl_by_layer[best_layer][-1]
            print(
                f"  [{qi+1}/{len(questions)}] "
                f"Best layer this prompt: {best_layer} (KL={best_kl:.4f})"
            )

    return kl_by_layer


def print_attribution_results(kl_by_layer, alpha):
    """Print a summary table of attribution patching results."""
    print(f"\n{'='*70}")
    print(f"ATTRIBUTION PATCHING RESULTS (alpha={alpha:+.1f})")
    print(f"{'='*70}")
    print(f"{'Layer':>6s}  {'Mean KL':>10s}  {'Median KL':>10s}  {'Max KL':>10s}  {'Std KL':>10s}  {'Bar'}")
    print(f"{'-'*70}")

    max_mean_kl = max(np.mean(kls) for kls in kl_by_layer.values()) or 1.0

    sorted_layers = sorted(kl_by_layer.keys())
    for layer in sorted_layers:
        kls = np.array(kl_by_layer[layer])
        mean_kl = np.mean(kls)
        median_kl = np.median(kls)
        max_kl = np.max(kls)
        std_kl = np.std(kls)

        bar_len = int(40 * mean_kl / max_mean_kl) if max_mean_kl > 0 else 0
        bar = "█" * bar_len + "░" * (40 - bar_len)

        print(
            f"{layer:>6d}  "
            f"{mean_kl:>10.4f}  "
            f"{median_kl:>10.4f}  "
            f"{max_kl:>10.4f}  "
            f"{std_kl:>10.4f}  "
            f"|{bar}|"
        )

    peak_layer = max(sorted_layers, key=lambda l: np.mean(kl_by_layer[l]))
    peak_kl = np.mean(kl_by_layer[peak_layer])
    print(f"\nPeak causal layer: {peak_layer} (mean KL = {peak_kl:.4f})")

    top5 = sorted(sorted_layers, key=lambda l: np.mean(kl_by_layer[l]), reverse=True)[:5]
    print(f"Top 5 layers: {top5}")
    print(f"(Compare: probe accuracy peaked at layers 40-48)")


def main():
    parser = argparse.ArgumentParser(description="Attribution patching for layer selection")
    parser.add_argument("--test", action="store_true", help="Quick test (5 prompts)")
    parser.add_argument("--full", action="store_true", help="All attitude questions")
    parser.add_argument("-n", type=int, default=5, help="Number of prompts for quick test")
    parser.add_argument(
        "--alpha", type=float, default=1.0,
        help="Steering strength (default: 1.0 = raw mean-difference magnitude)"
    )
    parser.add_argument(
        "--layer-stride", type=int, default=8,
        help="Test every Nth layer (default: 8, for layers 0,8,16,...,56)"
    )
    parser.add_argument(
        "--layers", type=str, default=None,
        help="Comma-separated layer indices (overrides --layer-stride)"
    )
    parser.add_argument(
        "--source-layer", type=str, default="40",
        help="Layer from which to load the steering direction (default: 40)"
    )
    parser.add_argument(
        "--activations", type=str, default=None,
        help="Path to activations .npz file"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress per-prompt output")
    args = parser.parse_args()

    if args.activations:
        npz_path = Path(args.activations)
    else:
        candidates = sorted(ACTIVATIONS_DIR.glob("qwen3_32b_contrastive_full*.npz"))
        if not candidates:
            print("ERROR: No activation files found. Run extract_activations.py first.")
            sys.exit(1)
        npz_path = candidates[0]

    direction, dir_norm = load_steering_direction(npz_path, args.source_layer)
    print(f"Steering direction from layer {args.source_layer}, norm = {dir_norm:.2f}")

    print(f"\nLoading model: {MODEL_ID}")
    t0 = time.time()
    model, tokenizer = mlx_lm.load(MODEL_ID)
    print(f"Model loaded in {time.time() - t0:.1f}s")

    n_layers = len(model.model.layers)
    if args.layers:
        candidate_layers = [int(x) for x in args.layers.split(",")]
    else:
        candidate_layers = list(range(0, n_layers, args.layer_stride))
        if (n_layers - 1) not in candidate_layers:
            candidate_layers.append(n_layers - 1)

    candidate_layers = [l for l in candidate_layers if l < n_layers]

    questions = load_questions(attitude_only=True)
    if not args.full:
        questions = questions[:args.n]

    print(f"\nAttribution Patching Configuration")
    print(f"Model: {MODEL_ID}")
    print(f"Questions: {len(questions)} attitude")
    print(f"Steering direction: layer {args.source_layer} mean-difference (raw, norm={dir_norm:.2f})")
    print(f"Alpha: {args.alpha}")
    print(f"Candidate layers: {candidate_layers}")
    print(f"Total forward passes: {len(questions)} × ({len(candidate_layers)} + 1) = {len(questions) * (len(candidate_layers) + 1)}")

    t_start = time.time()
    kl_by_layer = run_attribution_sweep(
        model, tokenizer, questions, direction, candidate_layers, args.alpha,
        verbose=not args.quiet,
    )
    elapsed = time.time() - t_start

    print_attribution_results(kl_by_layer, args.alpha)
    print(f"\nTotal time: {elapsed/60:.1f} minutes ({elapsed/len(questions):.1f}s per prompt)")

    results = {
        "model": MODEL_ID,
        "source_layer": args.source_layer,
        "direction_norm": float(dir_norm),
        "alpha": args.alpha,
        "n_questions": len(questions),
        "candidate_layers": candidate_layers,
        "elapsed_seconds": elapsed,
        "kl_by_layer": {
            str(layer): {
                "values": [float(v) for v in kls],
                "mean": float(np.mean(kls)),
                "median": float(np.median(kls)),
                "std": float(np.std(kls)),
                "max": float(np.max(kls)),
            }
            for layer, kls in kl_by_layer.items()
        },
    }

    peak_layer = max(candidate_layers, key=lambda l: np.mean(kl_by_layer[l]))
    results["peak_layer"] = peak_layer
    results["peak_kl"] = float(np.mean(kl_by_layer[peak_layer]))

    output_path = ACTIVATIONS_DIR / f"attribution_patching_a{args.alpha:+.1f}.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_path}")

    if peak_layer not in [40, 48]:
        print(f"\n*** Peak causal layer ({peak_layer}) differs from probe-selected layers (40, 48) ***")
        print(f"*** This suggests re-running steer_and_eval.py with --layer {peak_layer} ***")


if __name__ == "__main__":
    main()
