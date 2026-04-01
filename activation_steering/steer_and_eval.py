#!/usr/bin/env python3
"""
Causal intervention: add a steering vector to the model's residual stream
during generation and measure whether EDT/CDT preference shifts.

Takes the mean-difference direction from probe training and injects it at
a target layer during forward pass. Runs the Newcomb-like attitude questions
and reports EDT% at each steering strength (alpha).

This is the causal test: if EDT% moves monotonically with alpha, the
direction identified by the probe *controls* DT reasoning, not just
correlates with it.

Usage:
    source .venv/bin/activate

    # Quick test (5 questions, 3 alpha values)
    python activation_steering/steer_and_eval.py --test

    # Full sweep
    python activation_steering/steer_and_eval.py --full

    # Custom alpha values and layer
    python activation_steering/steer_and_eval.py --full --layer 48 --alphas -3,-2,-1,0,1,2,3

    # Use probe weight vector instead of mean-difference
    python activation_steering/steer_and_eval.py --full --use-probe-direction

Hardware: Requires ~20GB unified memory. Tested on M4 Max 36GB.
"""

import sys
import json
import time
import argparse
import numpy as np
from pathlib import Path
from functools import wraps

import mlx.core as mx
import mlx_lm
from mlx_lm.sample_utils import make_sampler

sys.path.insert(0, str(Path(__file__).parent.parent))
from newcomblike_eval import load_questions, run_evaluation, print_summary, save_results

ACTIVATIONS_DIR = Path(__file__).parent / "activations"
MODEL_ID = "mlx-community/Qwen3-32B-4bit"
MODEL_LABEL = "qwen3-32b-4bit-steered"
CONSTITUTION_PATH = Path(__file__).parent.parent / "logs" / "mp_constitutions" / "ecl_pilled" / "eclpilled_ch90.md"
TEMPERATURE = 0.7
MAX_TOKENS = 512

DEFAULT_ALPHAS = [-3.0, -1.5, -0.5, 0.0, 0.5, 1.5, 3.0]


def load_steering_direction(npz_path: Path, layer_key: str, normalize: bool = True):
    """Load activations and compute mean-difference steering direction."""
    data = np.load(npz_path)
    meta_path = npz_path.with_suffix(".json")
    with open(meta_path) as f:
        metadata = json.load(f)

    edt_key = f"edt_layer_{layer_key}"
    cdt_key = f"cdt_layer_{layer_key}"

    edt_acts = data[edt_key]
    cdt_acts = data[cdt_key]

    diff = edt_acts.mean(axis=0) - cdt_acts.mean(axis=0)
    norm = np.linalg.norm(diff)

    if normalize:
        direction = diff / norm if norm > 0 else diff
        print(f"Steering direction loaded from layer {layer_key}")
        print(f"  Based on {edt_acts.shape[0]} contrastive pairs")
        print(f"  Raw direction norm: {norm:.2f}")
        print(f"  Direction normalized to unit length")
        print(f"  α=1.0 adds a unit vector; natural scale is α≈{norm:.1f}")
    else:
        direction = diff
        print(f"Steering direction loaded from layer {layer_key} (UN-NORMALIZED)")
        print(f"  Based on {edt_acts.shape[0]} contrastive pairs")
        print(f"  Direction norm: {norm:.2f}")
        print(f"  α=1.0 adds the full mean EDT-CDT difference")

    print(f"  Hidden dim: {direction.shape[0]}")

    return direction, norm, metadata


def load_probe_direction(results_path: Path, layer_key: str):
    """Load the probe's learned weight vector as an alternative steering direction.

    The probe coef_ isn't saved in the JSON — we'd need to retrain.
    For now, this is a placeholder that falls back to mean-diff.
    """
    raise NotImplementedError(
        "Probe weight vector not saved in results JSON. "
        "Use mean-difference direction (default) or extend train_probes.py to save coef_."
    )


def install_steering_hook(model, layer_idx: int, direction_mx: mx.array, alpha: float):
    """Monkey-patch the target layer to add alpha * direction to its output.

    Returns a cleanup function that restores the original layer.
    """
    layer = model.model.layers[layer_idx]
    original_call = layer.__class__.__call__

    scaled_direction = alpha * direction_mx

    @wraps(original_call)
    def steered_call(self, x, mask=None, cache=None):
        out = original_call(self, x, mask, cache)
        out = out + scaled_direction
        return out

    layer.__class__ = type(
        f"Steered_TransformerBlock_{layer_idx}",
        (layer.__class__.__bases__[0],),
        dict(layer.__class__.__dict__),
    )
    layer.__class__.__call__ = steered_call

    def cleanup():
        layer.__class__.__call__ = original_call

    return cleanup


def install_steering_hook_instance(model, layer_idx: int, direction_mx: mx.array, alpha: float):
    """Class-level hook — creates a dynamic subclass with a steered __call__.

    NOTE: Python dunder methods (__call__) are looked up on the *type*, not
    the instance. Setting layer.__call__ as an instance attribute is silently
    ignored. We must create a new class to override __call__.

    Only patches the single layer object by swapping its __class__.
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
        f"Steered_TransformerBlock_{layer_idx}",
        (original_class,),
        {"__call__": steered_call},
    )

    def cleanup():
        layer.__class__ = original_class

    return cleanup


def make_steered_llm_call(model, tokenizer, sampler):
    """Create the llm_call_fn for the newcomblike eval pipeline."""
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


def run_alpha_sweep(
    model, tokenizer, questions, layer_idx, direction_np, alphas,
    constitution=None, constitution_id=None, verbose=True,
):
    """Run the eval at each alpha value and collect results."""
    direction_mx = mx.array(direction_np.reshape(1, 1, -1).astype(np.float32))

    sampler = make_sampler(temp=TEMPERATURE)
    results = {}

    for alpha in alphas:
        label = f"alpha={alpha:+.1f}"
        print(f"\n{'='*60}")
        print(f"  Steering: layer {layer_idx}, alpha = {alpha:+.1f}")
        if constitution:
            print(f"  Constitution: {constitution_id}")
        else:
            print(f"  Constitution: baseline (none)")
        print(f"{'='*60}")

        if alpha == 0.0:
            cleanup = None
        else:
            cleanup = install_steering_hook_instance(
                model, layer_idx, direction_mx, alpha
            )

        llm_call = make_steered_llm_call(model, tokenizer, sampler)

        model_label = f"{MODEL_LABEL}_layer{layer_idx}_a{alpha:+.1f}"
        if constitution_id:
            model_label += f"_{constitution_id}"

        run = run_evaluation(
            model=model_label,
            llm_call_fn=llm_call,
            constitution=constitution,
            constitution_id=constitution_id,
            questions=questions,
            verbose=verbose,
        )

        if cleanup:
            cleanup()

        att = [r for r in run.results if r.question.is_attitude]
        edt_count = sum(1 for r in att if r.is_edt_aligned)
        cdt_count = sum(1 for r in att if r.is_cdt_aligned)
        parse_err = sum(1 for r in att if r.parse_error)
        total = len(att)

        results[alpha] = {
            "run": run,
            "edt_count": edt_count,
            "cdt_count": cdt_count,
            "parse_errors": parse_err,
            "total": total,
            "edt_rate": edt_count / total if total > 0 else 0,
        }

        print(f"\n  >> alpha={alpha:+.1f}: EDT {edt_count}/{total} ({100*results[alpha]['edt_rate']:.1f}%) | Parse errors: {parse_err}")

        save_results(run)

    return results


def print_sweep_summary(results, layer_idx, condition_label=""):
    """Print a compact summary table of the alpha sweep."""
    print(f"\n{'='*70}")
    print(f"STEERING SWEEP SUMMARY — Layer {layer_idx} {condition_label}")
    print(f"{'='*70}")
    print(f"{'Alpha':>8s}  {'EDT':>6s}  {'CDT':>6s}  {'Parse':>6s}  {'EDT%':>7s}  {'Bar'}")
    print(f"{'-'*70}")

    for alpha in sorted(results.keys()):
        r = results[alpha]
        edt_pct = 100 * r["edt_rate"]
        bar_len = int(edt_pct / 2)
        bar = "█" * bar_len + "░" * (50 - bar_len)
        print(
            f"{alpha:>+8.1f}  "
            f"{r['edt_count']:>3d}/{r['total']}  "
            f"{r['cdt_count']:>3d}/{r['total']}  "
            f"{r['parse_errors']:>3d}/{r['total']}  "
            f"{edt_pct:>6.1f}%  "
            f"|{bar}|"
        )

    alphas_sorted = sorted(results.keys())
    if len(alphas_sorted) >= 2:
        lowest = results[alphas_sorted[0]]["edt_rate"]
        highest = results[alphas_sorted[-1]]["edt_rate"]
        span = highest - lowest
        print(f"\nEDT span: {100*lowest:.1f}% (α={alphas_sorted[0]:+.1f}) → {100*highest:.1f}% (α={alphas_sorted[-1]:+.1f}) = {100*span:+.1f}pp")

        rates = [results[a]["edt_rate"] for a in alphas_sorted]
        monotonic_up = all(rates[i] <= rates[i+1] for i in range(len(rates)-1))
        monotonic_down = all(rates[i] >= rates[i+1] for i in range(len(rates)-1))
        if monotonic_up:
            print("Monotonicity: YES (increasing) — causal evidence for EDT steering")
        elif monotonic_down:
            print("Monotonicity: YES (decreasing) — direction is inverted from expected")
        else:
            print("Monotonicity: NO — relationship is non-monotonic")


def main():
    parser = argparse.ArgumentParser(description="Activation steering causal intervention")
    parser.add_argument("--test", action="store_true", help="Quick test (5 questions, 3 alphas)")
    parser.add_argument("--full", action="store_true", help="Full 81 attitude questions")
    parser.add_argument("-n", type=int, default=5, help="Questions for quick test (default: 5)")
    parser.add_argument("--layer", type=int, default=40, help="Layer to steer (default: 40)")
    parser.add_argument(
        "--alphas", type=str, default=None,
        help="Comma-separated alpha values (default: -3,-1.5,-0.5,0,0.5,1.5,3)"
    )
    parser.add_argument(
        "--activations", type=str, default=None,
        help="Path to activations .npz file (default: auto-detect)"
    )
    parser.add_argument("--with-constitution", action="store_true", help="Also run with ECL90 constitution")
    parser.add_argument("--constitution-only", action="store_true", help="Only run with ECL90 constitution")
    parser.add_argument("--use-probe-direction", action="store_true", help="Use probe coef instead of mean-diff")
    parser.add_argument("--no-normalize", action="store_true", help="Use raw mean-diff direction (α=1.0 = full natural scale)")
    parser.add_argument("--quiet", action="store_true", help="Suppress per-question output")
    args = parser.parse_args()

    if args.alphas:
        alphas = [float(x) for x in args.alphas.split(",")]
    elif args.test:
        alphas = [-2.0, 0.0, 2.0]
    else:
        alphas = DEFAULT_ALPHAS

    if args.activations:
        npz_path = Path(args.activations)
    else:
        candidates = sorted(ACTIVATIONS_DIR.glob("qwen3_32b_contrastive_full*.npz"))
        if not candidates:
            print("ERROR: No activation files found. Run extract_activations.py first.")
            sys.exit(1)
        npz_path = candidates[0]
        print(f"Using activations: {npz_path}")

    layer_key = str(args.layer)

    if args.use_probe_direction:
        direction, raw_norm, metadata = load_probe_direction(npz_path, layer_key)
    else:
        direction, raw_norm, metadata = load_steering_direction(
            npz_path, layer_key, normalize=not args.no_normalize
        )

    print(f"\nLoading model: {MODEL_ID}")
    t0 = time.time()
    model, tokenizer = mlx_lm.load(MODEL_ID)
    print(f"Model loaded in {time.time() - t0:.1f}s")

    n_layers = len(model.model.layers)
    if args.layer >= n_layers:
        print(f"ERROR: Layer {args.layer} out of range (model has {n_layers} layers)")
        sys.exit(1)

    questions = load_questions(attitude_only=True)
    if not args.full:
        questions = questions[:args.n]

    print(f"\nActivation Steering Causal Intervention")
    print(f"Model: {MODEL_ID}")
    print(f"Questions: {len(questions)} attitude")
    print(f"Target layer: {args.layer}")
    print(f"Alpha values: {alphas}")
    dir_desc = 'probe coef' if args.use_probe_direction else ('mean-difference (raw)' if args.no_normalize else 'mean-difference (unit)')
    print(f"Direction: {dir_desc}")
    print(f"Temperature: {TEMPERATURE}")

    all_results = {}

    if not args.constitution_only:
        print(f"\n{'#'*60}")
        print(f"  BASELINE (no constitution) — sweeping alpha")
        print(f"{'#'*60}")
        baseline_results = run_alpha_sweep(
            model, tokenizer, questions, args.layer, direction, alphas,
            verbose=not args.quiet,
        )
        all_results["baseline"] = baseline_results
        print_sweep_summary(baseline_results, args.layer, "(baseline)")

    if args.with_constitution or args.constitution_only:
        if not CONSTITUTION_PATH.exists():
            print(f"ERROR: Constitution not found at {CONSTITUTION_PATH}")
            sys.exit(1)
        with open(CONSTITUTION_PATH) as f:
            constitution = f.read()

        print(f"\n{'#'*60}")
        print(f"  ECL90 CONSTITUTION — sweeping alpha")
        print(f"{'#'*60}")
        ecl_results = run_alpha_sweep(
            model, tokenizer, questions, args.layer, direction, alphas,
            constitution=constitution, constitution_id="ecl90",
            verbose=not args.quiet,
        )
        all_results["ecl90"] = ecl_results
        print_sweep_summary(ecl_results, args.layer, "(ecl90)")

    summary = {
        "model": MODEL_ID,
        "layer": args.layer,
        "alphas": alphas,
        "direction_type": "probe_coef" if args.use_probe_direction else "mean_difference",
        "normalized": not args.no_normalize,
        "direction_raw_norm": raw_norm,
        "activations_file": str(npz_path),
        "n_questions": len(questions),
        "temperature": TEMPERATURE,
        "conditions": {},
    }

    for condition, results in all_results.items():
        summary["conditions"][condition] = {
            str(alpha): {
                "edt_count": r["edt_count"],
                "cdt_count": r["cdt_count"],
                "parse_errors": r["parse_errors"],
                "total": r["total"],
                "edt_rate": r["edt_rate"],
            }
            for alpha, r in results.items()
        }

    norm_label = "raw" if args.no_normalize else "unit"
    summary_path = ACTIVATIONS_DIR / f"steering_sweep_layer{args.layer}_{norm_label}.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, default=lambda x: float(x) if hasattr(x, 'item') else str(x))
    print(f"\nSweep summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
