#!/usr/bin/env python3
"""
Extract contrastive activations from Qwen3-32B (non-thinking) for EDT/CDT probing.

For each prompt in the dataset, feeds prompt+EDT_completion and prompt+CDT_completion
through the model and extracts residual stream activations at the last token from
selected layers. Saves activations as .npz files for downstream probe training.

Usage:
    source .venv/bin/activate
    python activation_steering/extract_activations.py --test          # 5 prompts, verify pipeline
    python activation_steering/extract_activations.py                 # Full dataset (475 prompts)
    python activation_steering/extract_activations.py --split train   # Train split only
    python activation_steering/extract_activations.py --layers 0,16,32,48,63  # Custom layers

Hardware: Requires ~20GB unified memory (4-bit model ~18GB + activations).
          Tested on M4 Max 36GB.
"""

import json
import argparse
import time
import numpy as np
from pathlib import Path

import mlx.core as mx
import mlx_lm

DATASET_DIR = Path(__file__).parent / "datasets" / "generated"
OUTPUT_DIR = Path(__file__).parent / "activations"

MODEL_ID = "mlx-community/Qwen3-32B-Instruct-4bit"

NUM_LAYERS = 64
DEFAULT_EXTRACT_LAYERS = [0, 8, 16, 24, 32, 40, 48, 56, 63]


def load_dataset(split: str = None) -> list[dict]:
    if split:
        path = DATASET_DIR / f"dt_steering_{split}.jsonl"
    else:
        path = DATASET_DIR / "dt_steering_full.jsonl"

    prompts = []
    with open(path) as f:
        for line in f:
            prompts.append(json.loads(line))
    return prompts


def build_messages(prompt_text: str, completion: str) -> list[dict]:
    """Build chat messages: user prompt + assistant completion."""
    return [
        {"role": "user", "content": prompt_text},
        {"role": "assistant", "content": completion},
    ]


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


def extract_hidden_states(model, tokens: mx.array, layer_indices: list[int]) -> dict:
    """Run forward pass and extract hidden states at specified layers.

    Returns dict mapping layer_index -> activation at last token (shape: [hidden_dim]).
    """
    inner = model.model

    h = inner.embed_tokens(tokens)

    cache = [None] * len(inner.layers)

    from mlx_lm.models.qwen3 import create_attention_mask
    mask = create_attention_mask(h, cache[0])

    layer_activations = {}
    arrays_to_eval = []

    for i, (layer, c) in enumerate(zip(inner.layers, cache)):
        h = layer(h, mask, c)
        if i in layer_indices:
            act = h[0, -1, :]
            arrays_to_eval.append(act)
            layer_activations[i] = act

    h = inner.norm(h)
    post_norm_act = h[0, -1, :]
    arrays_to_eval.append(post_norm_act)
    layer_activations["post_norm"] = post_norm_act

    mx.eval(*arrays_to_eval)

    result = {}
    for key, val in layer_activations.items():
        result[key] = np.array(val.tolist(), dtype=np.float32)

    return result


def extract_for_prompt(
    model, tokenizer, prompt_data: dict, layer_indices: list[int]
) -> dict:
    """Extract contrastive activations for one prompt.

    Returns dict with EDT and CDT activations at each layer.
    """
    prompt_text = prompt_data["prompt"]
    edt_completion = prompt_data["edt_completion"]
    cdt_completion = prompt_data["cdt_completion"]

    edt_messages = build_messages(prompt_text, edt_completion)
    edt_tokens = tokenize_messages(tokenizer, edt_messages)
    edt_acts = extract_hidden_states(model, edt_tokens, layer_indices)

    cdt_messages = build_messages(prompt_text, cdt_completion)
    cdt_tokens = tokenize_messages(tokenizer, cdt_messages)
    cdt_acts = extract_hidden_states(model, cdt_tokens, layer_indices)

    return {
        "prompt_id": prompt_data["prompt_id"],
        "scenario_id": prompt_data["scenario_id"],
        "category": prompt_data["category"],
        "split": prompt_data["split"],
        "question_format": prompt_data["question_format"],
        "tags": prompt_data.get("tags", {}),
        "confound_flags": prompt_data.get("confound_flags", {}),
        "edt_answer_idx": prompt_data["edt_answer_idx"],
        "cdt_answer_idx": prompt_data["cdt_answer_idx"],
        "edt_n_tokens": edt_tokens.shape[1],
        "cdt_n_tokens": cdt_tokens.shape[1],
        "edt_activations": edt_acts,
        "cdt_activations": cdt_acts,
    }


def save_activations(results: list[dict], output_path: Path, layer_indices: list[int]):
    """Save all activations as a single .npz file with metadata JSON sidecar."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    all_layer_keys = [str(i) for i in layer_indices] + ["post_norm"]

    edt_arrays = {}
    cdt_arrays = {}
    for key in all_layer_keys:
        layer_key = int(key) if key != "post_norm" else "post_norm"
        edt_arrays[key] = np.stack([r["edt_activations"][layer_key] for r in results])
        cdt_arrays[key] = np.stack([r["cdt_activations"][layer_key] for r in results])

    save_dict = {}
    for key in all_layer_keys:
        save_dict[f"edt_layer_{key}"] = edt_arrays[key]
        save_dict[f"cdt_layer_{key}"] = cdt_arrays[key]

    np.savez_compressed(output_path, **save_dict)

    metadata = []
    for r in results:
        metadata.append({
            "prompt_id": r["prompt_id"],
            "scenario_id": r["scenario_id"],
            "category": r["category"],
            "split": r["split"],
            "question_format": r["question_format"],
            "tags": r["tags"],
            "confound_flags": r["confound_flags"],
            "edt_answer_idx": r["edt_answer_idx"],
            "cdt_answer_idx": r["cdt_answer_idx"],
            "edt_n_tokens": r["edt_n_tokens"],
            "cdt_n_tokens": r["cdt_n_tokens"],
        })

    meta_path = output_path.with_suffix(".json")
    with open(meta_path, "w") as f:
        json.dump({
            "model": MODEL_ID,
            "layer_indices": layer_indices,
            "n_prompts": len(results),
            "prompts": metadata,
        }, f, indent=2)

    return output_path, meta_path


def main():
    parser = argparse.ArgumentParser(description="Extract contrastive activations")
    parser.add_argument("--test", action="store_true", help="Quick test with 5 prompts")
    parser.add_argument("-n", type=int, default=None, help="Number of prompts to process")
    parser.add_argument("--split", type=str, default=None, help="Dataset split (train/val/test)")
    parser.add_argument(
        "--layers", type=str, default=None,
        help="Comma-separated layer indices (default: 0,8,16,24,32,40,48,56,63)"
    )
    parser.add_argument("--output", type=str, default=None, help="Output filename (without extension)")
    args = parser.parse_args()

    if args.layers:
        layer_indices = [int(x) for x in args.layers.split(",")]
    else:
        layer_indices = DEFAULT_EXTRACT_LAYERS

    prompts = load_dataset(args.split)
    if args.test:
        prompts = prompts[:5]
    elif args.n:
        prompts = prompts[:args.n]

    contrastive_prompts = [p for p in prompts if p["edt_answer_idx"] != p["cdt_answer_idx"]]
    print(f"Dataset: {len(prompts)} total, {len(contrastive_prompts)} contrastive (EDT != CDT)")
    print(f"Using contrastive prompts only for activation extraction")
    prompts = contrastive_prompts

    print(f"\nLoading model: {MODEL_ID}")
    print(f"This will download ~18GB on first run...")
    t0 = time.time()
    model, tokenizer = mlx_lm.load(MODEL_ID)
    print(f"Model loaded in {time.time() - t0:.1f}s")

    print(f"\nExtracting activations from layers: {layer_indices}")
    print(f"Processing {len(prompts)} prompts...")

    results = []
    t_start = time.time()

    for i, prompt_data in enumerate(prompts):
        t_prompt = time.time()
        result = extract_for_prompt(model, tokenizer, prompt_data, layer_indices)
        results.append(result)
        elapsed = time.time() - t_prompt
        total_elapsed = time.time() - t_start
        avg = total_elapsed / (i + 1)
        remaining = avg * (len(prompts) - i - 1)
        print(
            f"  [{i+1}/{len(prompts)}] {prompt_data['prompt_id'][:50]:50s} "
            f"{elapsed:.1f}s (ETA: {remaining/60:.1f}min)"
        )

    if args.output:
        out_name = args.output
    else:
        split_label = args.split or "full"
        n_label = f"_n{len(prompts)}" if (args.test or args.n) else ""
        out_name = f"qwen3_32b_contrastive_{split_label}{n_label}"

    output_path = OUTPUT_DIR / f"{out_name}.npz"
    npz_path, meta_path = save_activations(results, output_path, layer_indices)

    total_time = time.time() - t_start
    print(f"\nDone in {total_time/60:.1f} minutes")
    print(f"Activations: {npz_path} ({npz_path.stat().st_size / 1e6:.1f} MB)")
    print(f"Metadata:    {meta_path}")

    n = len(results)
    hidden_dim = results[0]["edt_activations"][layer_indices[0]].shape[0]
    print(f"\nShape per layer: ({n}, {hidden_dim})")
    print(f"Layers extracted: {len(layer_indices)} + post_norm = {len(layer_indices) + 1}")


if __name__ == "__main__":
    main()
