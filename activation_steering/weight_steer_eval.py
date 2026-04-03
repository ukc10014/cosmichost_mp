#!/usr/bin/env python3
"""
Weight-space steering for EDT/CDT decision theory preference.

WHY THIS EXISTS
---------------
Our earlier activation steering experiments found that the model cleanly
*encodes* the EDT/CDT distinction in its residual stream (100% probe
accuracy at layer 40), but injecting that direction during generation
produced zero causal shift in EDT/CDT answers. The direction tells us
what EDT text *looks like* after processing — but that's not the same
thing as the mechanism that *picks* which answer to give.

This script tries a different approach: instead of nudging what the model
is thinking about (activation steering at one layer), we change how the
model thinks (modifying its actual weights across all layers).

HOW IT WORKS
------------
Following Fierro & Roger 2025 ("Steering Language Models with Weight
Arithmetic", ICLR 2026, arxiv.org/abs/2511.05408):

    1. Fine-tune a LoRA adapter on EDT-aligned answers → LoRA_EDT
    2. Fine-tune a LoRA adapter on CDT-aligned answers → LoRA_CDT
    3. Subtract: direction w = LoRA_EDT - LoRA_CDT
       (this gives a delta across all 448 weight matrices in the model —
       every attention and MLP projection at every layer)
    4. Steer: base_model + k * w
       At k=0, unmodified base model.
       At k=+1, one full EDT-minus-CDT step in weight space.
       At k=-1, moved toward CDT.
    5. Evaluate at each k on 81 Newcomb-like attitude questions.

If EDT% varies monotonically with k, we have causal evidence that the
model's DT preference lives in weight space even though it doesn't live
in activation space at any single layer.

Usage:
    source .venv/bin/activate

    # Quick test (5 questions, 3 k values)
    python activation_steering/weight_steer_eval.py --test

    # Full sweep
    python activation_steering/weight_steer_eval.py --full

    # Custom k values
    python activation_steering/weight_steer_eval.py --full --k-values -2,-1,-0.5,0,0.5,1,2

Hardware: Requires ~20GB unified memory. Tested on M4 Max 36GB.
"""

import sys
import json
import time
import argparse
import numpy as np
from pathlib import Path

import mlx.core as mx
import mlx.nn as nn
import mlx_lm
from mlx_lm.sample_utils import make_sampler
from mlx.utils import tree_flatten

sys.path.insert(0, str(Path(__file__).parent.parent))
from newcomblike_eval import load_questions, run_evaluation, save_results

ACTIVATIONS_DIR = Path(__file__).parent / "activations"
MODEL_ID = "mlx-community/Qwen3-32B-4bit"
MODEL_LABEL = "qwen3-32b-4bit-weight-steered"
TEMPERATURE = 0.7
MAX_TOKENS = 512

DEFAULT_K_VALUES = [-2.0, -1.0, -0.5, 0.0, 0.5, 1.0, 2.0]


def load_adapter_weights(adapter_dir: Path):
    """Load raw LoRA adapter weights from safetensors file.

    Returns a dict of {param_name: mx.array} for all lora_a and lora_b tensors.
    """
    import safetensors.numpy

    adapter_path = adapter_dir / "adapters.safetensors"
    config_path = adapter_dir / "adapter_config.json"

    if not adapter_path.exists():
        raise FileNotFoundError(f"Adapter weights not found: {adapter_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"Adapter config not found: {config_path}")

    with open(config_path) as f:
        config = json.load(f)

    weights = safetensors.numpy.load_file(str(adapter_path))
    scale = config["lora_parameters"]["scale"]

    return weights, scale, config


def load_lora_pair(edt_dir: Path, cdt_dir: Path):
    """Load raw LoRA A/B matrices from both adapters.

    Instead of materializing the full-rank deltas (which for Qwen3-32B would be
    ~119GB of float32), we keep the low-rank factors (rank 32 → a few hundred MB)
    and compute each delta on-the-fly during apply_weight_direction().

    Returns (lora_modules, scale) where lora_modules is a dict:
        {base_weight_name: (edt_a, edt_b, cdt_a, cdt_b)}
    """
    edt_weights, edt_scale, edt_config = load_adapter_weights(edt_dir)
    cdt_weights, cdt_scale, cdt_config = load_adapter_weights(cdt_dir)

    assert edt_scale == cdt_scale, f"Scale mismatch: EDT={edt_scale}, CDT={cdt_scale}"
    scale = edt_scale

    lora_a_keys = sorted(k for k in edt_weights if k.endswith(".lora_a"))

    lora_modules = {}
    for a_key in lora_a_keys:
        b_key = a_key.replace(".lora_a", ".lora_b")
        if b_key not in edt_weights:
            print(f"  Warning: {b_key} not found in EDT adapters, skipping")
            continue
        if a_key not in cdt_weights or b_key not in cdt_weights:
            print(f"  Warning: {a_key} not found in CDT adapters, skipping")
            continue

        base_key = a_key.replace(".lora_a", ".weight")
        lora_modules[base_key] = (
            edt_weights[a_key], edt_weights[b_key],
            cdt_weights[a_key], cdt_weights[b_key],
        )

    print(f"Loaded LoRA factors for {len(lora_modules)} modules (rank {edt_weights[lora_a_keys[0]].shape[0]})")
    print(f"  Scale factor: {scale}")

    return lora_modules, scale


def find_module_by_path(model, path):
    """Navigate model tree to find a module by dot-separated path.

    E.g. 'layers.0.self_attn.q_proj' → model.model.layers[0].self_attn.q_proj
    """
    parts = path.replace(".weight", "").split(".")
    obj = model.model
    for part in parts:
        if part.isdigit():
            obj = obj[int(part)]
        else:
            obj = getattr(obj, part)
    return obj


def apply_weight_direction(model, lora_modules, scale, k):
    """Add k * (EDT - CDT) direction to the model's weights.

    Computes each full-rank delta on-the-fly from the low-rank LoRA factors,
    applies it, then discards it. Peak overhead = one weight matrix at a time.

    Handles quantized models by dequantizing, adding the delta,
    and re-quantizing (same approach as LoRALinear.fuse()).
    """
    applied = 0
    skipped = 0

    for base_key, (edt_a, edt_b, cdt_a, cdt_b) in lora_modules.items():
        module_path = base_key.replace(".weight", "")
        try:
            module = find_module_by_path(model, module_path)
        except (AttributeError, IndexError, KeyError):
            skipped += 1
            continue

        edt_delta = edt_b.T @ edt_a.T
        cdt_delta = cdt_b.T @ cdt_a.T
        diff = edt_delta - cdt_delta
        delta = mx.array((k * scale * diff).astype(np.float32))
        del diff, edt_delta, cdt_delta

        if isinstance(module, nn.QuantizedLinear):
            weight = mx.dequantize(
                module.weight,
                module.scales,
                module.biases,
                group_size=module.group_size,
                bits=module.bits,
                mode=module.mode,
            )

            if weight.shape != delta.shape:
                skipped += 1
                continue

            new_weight = weight + delta
            del delta, weight
            bias = module.bias if hasattr(module, "bias") and module.bias is not None else None

            output_dims, input_dims = new_weight.shape
            temp_linear = nn.Linear(input_dims, output_dims, bias=bias is not None)
            temp_linear.weight = new_weight
            if bias is not None:
                temp_linear.bias = bias

            new_module = nn.QuantizedLinear.from_linear(
                temp_linear,
                module.group_size,
                module.bits,
                mode=module.mode,
            )
            del temp_linear, new_weight

            parent_path = ".".join(module_path.split(".")[:-1])
            child_name = module_path.split(".")[-1]
            parent = find_module_by_path(model, parent_path)
            setattr(parent, child_name, new_module)
            applied += 1

        elif isinstance(module, (nn.Linear,)):
            if module.weight.shape != delta.shape:
                skipped += 1
                continue

            module.weight = module.weight + delta.astype(module.weight.dtype)
            del delta
            applied += 1

        elif isinstance(module, (nn.Embedding, nn.QuantizedEmbedding)):
            skipped += 1

        else:
            skipped += 1

    return applied, skipped


def make_llm_call(model, tokenizer, sampler):
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


def run_k_sweep(
    questions, lora_modules, scale, k_values, verbose=True,
):
    """Run the eval at each k value, reloading the model each time."""
    sampler = make_sampler(temp=TEMPERATURE)
    results = {}

    for k in k_values:
        print(f"\n{'='*60}")
        print(f"  Weight steering: k = {k:+.2f}")
        print(f"{'='*60}")

        print(f"  Loading fresh model...")
        t0 = time.time()
        model, tokenizer = mlx_lm.load(MODEL_ID)
        print(f"  Model loaded in {time.time() - t0:.1f}s")

        if k != 0.0:
            applied, skipped = apply_weight_direction(model, lora_modules, scale, k)
            print(f"  Applied direction to {applied} weight matrices (skipped {skipped})")
            mx.eval(model.parameters())
        else:
            print(f"  Baseline (no weight modification)")

        llm_call = make_llm_call(model, tokenizer, sampler)
        model_label = f"{MODEL_LABEL}_k{k:+.2f}"

        run = run_evaluation(
            model=model_label,
            llm_call_fn=llm_call,
            questions=questions,
            verbose=verbose,
        )

        att = [r for r in run.results if r.question.is_attitude]
        edt_count = sum(1 for r in att if r.is_edt_aligned)
        cdt_count = sum(1 for r in att if r.is_cdt_aligned)
        parse_err = sum(1 for r in att if r.parse_error)
        total = len(att)

        results[k] = {
            "run": run,
            "edt_count": edt_count,
            "cdt_count": cdt_count,
            "parse_errors": parse_err,
            "total": total,
            "edt_rate": edt_count / total if total > 0 else 0,
        }

        print(f"\n  >> k={k:+.2f}: EDT {edt_count}/{total} "
              f"({100*results[k]['edt_rate']:.1f}%) | Parse errors: {parse_err}")

        save_results(run)

        del model
        del tokenizer
        mx.metal.clear_cache()

    return results


def print_sweep_summary(results, condition_label=""):
    """Print a compact summary table of the k sweep."""
    print(f"\n{'='*70}")
    print(f"WEIGHT STEERING SWEEP SUMMARY {condition_label}")
    print(f"{'='*70}")
    print(f"{'k':>8s}  {'EDT':>6s}  {'CDT':>6s}  {'Parse':>6s}  {'EDT%':>7s}  {'Bar'}")
    print(f"{'-'*70}")

    for k in sorted(results.keys()):
        r = results[k]
        edt_pct = 100 * r["edt_rate"]
        bar_len = int(edt_pct / 2)
        bar = "█" * bar_len + "░" * (50 - bar_len)
        print(
            f"{k:>+8.2f}  "
            f"{r['edt_count']:>3d}/{r['total']}  "
            f"{r['cdt_count']:>3d}/{r['total']}  "
            f"{r['parse_errors']:>3d}/{r['total']}  "
            f"{edt_pct:>6.1f}%  "
            f"|{bar}|"
        )

    k_sorted = sorted(results.keys())
    if len(k_sorted) >= 2:
        lowest = results[k_sorted[0]]["edt_rate"]
        highest = results[k_sorted[-1]]["edt_rate"]
        span = highest - lowest
        print(f"\nEDT span: {100*lowest:.1f}% (k={k_sorted[0]:+.2f}) "
              f"→ {100*highest:.1f}% (k={k_sorted[-1]:+.2f}) = {100*span:+.1f}pp")

        rates = [results[k]["edt_rate"] for k in k_sorted]
        monotonic_up = all(rates[i] <= rates[i+1] for i in range(len(rates)-1))
        monotonic_down = all(rates[i] >= rates[i+1] for i in range(len(rates)-1))
        if monotonic_up:
            print("Monotonicity: YES (increasing) — causal evidence for weight-space EDT steering")
        elif monotonic_down:
            print("Monotonicity: YES (decreasing) — direction is inverted from expected")
        else:
            print("Monotonicity: NO — relationship is non-monotonic")


def main():
    parser = argparse.ArgumentParser(description="Weight-space steering evaluation")
    parser.add_argument("--test", action="store_true", help="Quick test (5 questions, 3 k values)")
    parser.add_argument("--full", action="store_true", help="Full 81 attitude questions")
    parser.add_argument("-n", type=int, default=5, help="Questions for quick test (default: 5)")
    parser.add_argument(
        "--k-values", type=str, default=None,
        help="Comma-separated k values (default: -2,-1,-0.5,0,0.5,1,2)"
    )
    parser.add_argument(
        "--edt-adapters", type=str,
        default=str(Path(__file__).parent / "adapters_edt"),
        help="Path to EDT adapter directory"
    )
    parser.add_argument(
        "--cdt-adapters", type=str,
        default=str(Path(__file__).parent / "adapters_cdt"),
        help="Path to CDT adapter directory"
    )
    parser.add_argument("--quiet", action="store_true", help="Suppress per-question output")
    args = parser.parse_args()

    if args.k_values:
        k_values = [float(x) for x in args.k_values.split(",")]
    elif args.test:
        k_values = [-1.0, 0.0, 1.0]
    else:
        k_values = DEFAULT_K_VALUES

    edt_dir = Path(args.edt_adapters)
    cdt_dir = Path(args.cdt_adapters)

    print("Loading LoRA factors...")
    lora_modules, scale = load_lora_pair(edt_dir, cdt_dir)

    questions = load_questions(attitude_only=True)
    if not args.full:
        questions = questions[:args.n]

    print(f"\nWeight-Space Steering Evaluation")
    print(f"Model: {MODEL_ID}")
    print(f"Questions: {len(questions)} attitude")
    print(f"k values: {k_values}")
    print(f"Temperature: {TEMPERATURE}")
    print(f"EDT adapters: {edt_dir}")
    print(f"CDT adapters: {cdt_dir}")

    results = run_k_sweep(
        questions, lora_modules, scale, k_values,
        verbose=not args.quiet,
    )

    print_sweep_summary(results)

    summary = {
        "model": MODEL_ID,
        "method": "weight_space_steering",
        "k_values": k_values,
        "edt_adapters": str(edt_dir),
        "cdt_adapters": str(cdt_dir),
        "n_questions": len(questions),
        "temperature": TEMPERATURE,
        "results": {
            str(k): {
                "edt_count": r["edt_count"],
                "cdt_count": r["cdt_count"],
                "parse_errors": r["parse_errors"],
                "total": r["total"],
                "edt_rate": r["edt_rate"],
            }
            for k, r in results.items()
        },
    }

    ACTIVATIONS_DIR.mkdir(parents=True, exist_ok=True)
    summary_path = ACTIVATIONS_DIR / "weight_steering_sweep.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2,
                  default=lambda x: float(x) if hasattr(x, 'item') else str(x))
    print(f"\nSweep summary saved to: {summary_path}")


if __name__ == "__main__":
    main()
