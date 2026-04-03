# Weight-Space Steering Results: Qwen3-32B (LoRA Subtraction)

*Date: 2026-04-03*
*Status: Complete — null result, likely due to insufficient training signal*

## Background

Our activation steering experiments (2026-04-01) found that Qwen3-32B cleanly *encodes* the EDT/CDT distinction as a linear direction in its residual stream (100% probe accuracy at layers 40+), but injecting that direction during generation produced zero causal shift in EDT/CDT answers. The direction tells us what EDT text *looks like* after processing — but not the mechanism that *picks* which answer to give.

This experiment tries a different approach: instead of nudging activations at one layer, we modify the model's actual weights across all layers using the LoRA subtraction method from Fierro & Roger 2025 ("Steering Language Models with Weight Arithmetic", ICLR 2026, arxiv.org/abs/2511.05408).

## Method

1. Fine-tune two LoRA adapters on the same 275 prompts, one with EDT-aligned completions (LoRA_EDT) and one with CDT-aligned completions (LoRA_CDT)
2. Compute direction: `w = LoRA_EDT - LoRA_CDT` (a delta across all adapted weight matrices)
3. Steer: `base_model + k * w` for k ∈ {-2, -1, -0.5, 0, +0.5, +1, +2}
4. Evaluate at each k on the 81 attitude questions from the Oesterheld et al. (2024) Newcomb-like benchmark

If EDT% varies monotonically with k, that's causal evidence that DT preference lives in weight space.

## LoRA Training Setup

| Parameter | Value |
|-----------|-------|
| Model | `mlx-community/Qwen3-32B-4bit` |
| Rank | 32 |
| Scale | 16.0 |
| Dropout | 0.05 |
| Learning rate | 1e-4 (AdamW) |
| Iterations | 275 |
| Batch size | 1 (CDT), 2 (EDT) |
| Layers adapted | All 64 (`num_layers: -1`) |
| Sequence length | 2048 |
| `mask_prompt` | true |
| Adapter size | ~1.0 GB each |

## Training Data

Both datasets contain 275 examples drawn from 55 unique prompts (≈5 rephrasings per scenario). The prompts are identical between EDT and CDT; only the completions differ.

**Critical weakness:** Completions average only **13-14 characters** — bare answer labels like "Take only Box B", "Take both boxes", "C", "Vote", "Action A". Zero completions contain chain-of-thought reasoning. With `mask_prompt: true`, the model is trained only on these short answer tokens.

## Sweep Results

| k | EDT | CDT | Parse Err | EDT% |
|------|---------|---------|-----------|------|
| -2.0 | 50/81 | 33/81 | 0 | 61.7% |
| -1.0 | 44/81 | 33/81 | 2 | 54.3% |
| -0.5 | 46/81 | 34/81 | 1 | 56.8% |
| 0.0 | 49/81 | 29/81 | 2 | 60.5% |
| +0.5 | 44/81 | 34/81 | 1 | 54.3% |
| +1.0 | 41/81 | 38/81 | 1 | 50.6% |
| +2.0 | 47/81 | 34/81 | 2 | 58.0% |

**EDT span:** 50.6% (k=+1.0) → 61.7% (k=-2.0) = 11.1pp
**Monotonicity:** No. The baseline (k=0.0) is one of the highest EDT rates.

## Interpretation

**No causal signal.** EDT% fluctuates within an ~11pp band with no monotonic relationship to k. The 11pp spread is consistent with stochastic noise at n=81 and temperature=0.7.

### Why the null result?

The most likely explanation is **insufficient training signal in the LoRA adapters**, not absence of DT preference in weight space:

1. **Token-level completions are too short.** With completions averaging 13 characters and `mask_prompt: true`, each training example provides only 3-5 tokens of gradient signal. The LoRA is learning a shallow mapping from scenario embeddings to answer tokens, not encoding decision-theoretic reasoning patterns. The EDT - CDT subtraction then captures "which answer label to emit" rather than "how to reason about the problem."

2. **Too few unique scenarios.** 55 unique prompts ×5 rephrasings = 275 examples, but the effective diversity is 55. With rank-32 LoRA across all 64 layers, there are ~57M adapted parameters — three orders of magnitude more parameters than training examples. The adapters are almost certainly underfitting or memorizing surface patterns.

3. **All layers adapted.** Adapting all 64 layers spreads the already-thin training signal across 448 weight matrices. The meaningful signal (if any) gets diluted by noise in irrelevant layers.

### Comparison with activation steering

| Method | Encodes EDT/CDT? | Causal shift? |
|--------|------------------|---------------|
| Activation probing (layer 40) | Yes (100% accuracy) | N/A |
| Activation steering (layer 40) | N/A | No |
| Attribution patching | Identified layers 0, 40 | N/A |
| Weight-space steering (LoRA subtraction) | Unclear — adapters may not have learned the distinction | No |

The activation probing result remains the strongest finding: the model *represents* EDT vs CDT as a clean linear feature. The causal interventions (activation steering and now weight steering) have both failed to shift behavior, but for potentially different reasons — activation steering may target the wrong causal mechanism, while weight steering may have had too little training signal to find *any* mechanism.

## Recommended Next Steps

### 1. More diverse training scenarios (done)

The original 55 scenarios were insufficient for 448 adapted weight matrices. We generated 80 additional scenarios from multiple model families for diversity:

| Source | Model | Scenarios | Mean length (words) |
|--------|-------|-----------|---------------------|
| Original | Hand-curated + expanded | 55 | 83 |
| Batch 1 | GPT-5.4, Gemini 2 Pro | 40 | 78 |
| Batch 2 | Qwen3-235B (via OpenRouter) | 20 | 36 |
| Batch 2 | DeepSeek-R1 (via OpenRouter) | 20 | 51 |
| **Total** | | **135** | |

**Diversity analysis** (TF-IDF cosine similarity):
- Global mean pairwise similarity: 0.012 (very low — good)
- Within-source similarity: all under 0.02
- Max cross-source pair: 0.408 (a copy/PD variant — structurally similar but distinct framing)
- No duplicates requiring removal
- Jaccard vocabulary overlap between sources: 0.15-0.25, confirming distinct word choices across model families
- Chinese models bring genuinely different vocabulary (Qwen: "launch", "regret", "blood"; DeepSeek: "forecasted", "salary", "gains")
- Qwen scenarios are shorter (mean 36 words vs 78-83 for others) — noted but not a problem for short-completion training

Category distribution is well-balanced across all sources: predictor, lesion, copy, commitment, collective, acausal each represented.

With 5 question framings per scenario: 135 × 5 = **675 training examples per adapter** (up from 275).

### 2. Fewer adapted layers

Restrict LoRA adaptation to layers 32-63 (or even just 40-63, guided by the probe accuracy and attribution patching results). This concentrates the limited training signal where the model's DT representation is strongest.

### 3. Validation loss tracking

Re-run training with loss logging to verify the adapters actually converged and that train/val loss diverged between EDT and CDT runs (confirming they learned different things).

## Files

- Sweep summary: `activation_steering/activations/weight_steering_sweep.json`
- Eval logs: `logs/newcomblike_evals/newcomblike_qwen3-32b-4bit-weight-steered_k*.jsonl`
- LoRA configs: `activation_steering/lora_config_edt.yaml`, `lora_config_cdt.yaml`
- Training data: `activation_steering/datasets/lora_edt/`, `lora_cdt/`
- Adapters: `activation_steering/adapters_edt/`, `adapters_cdt/`
- Eval script: `activation_steering/weight_steer_eval.py`
- Scenario generation prompt: `activation_steering/scenario_generation_prompt.md`
- Generated scenarios (batch 1): `activation_steering/generated_newcombs.json`
- Generated scenarios (batch 2): `activation_steering/generated_newcombs_chinese_models.json`
- Diversity analysis script: `activation_steering/check_scenario_diversity.py`
