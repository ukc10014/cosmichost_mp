# EDT/CDT Activation Steering: Qwen3-32B Mech Interp Pipeline

## What this is

Linear probing and steering vector extraction on Qwen3-32B (non-thinking mode) to find features that distinguish EDT vs CDT reasoning on decision-theoretic problems.

**Target model:** `mlx-community/Qwen3-32B-Instruct-4bit` (~18GB, runs on M4 Max 36GB)

**Core question:** When this model answers EDT on Newcomb-like problems, is it activating a generic "cooperate = good" feature (boring) or something that responds to the structural features of the problem — predictor accuracy, agent correlation, evidential vs causal dependence (interesting)?

## Why this model

From the newcomblike evals (`observations/newcomblike_eval_results.md`):
- Qwen3-32B non-thinking has 60.5% baseline EDT and +13.6pp ECL shift — strongest open-weights result
- But thinking mode adds zero directional signal (net +1 flip across 81 questions)
- Diagnostic question flips incoherently across conditions
- Conclusion: likely surface pattern matching, not genuine DT reasoning
- Non-thinking is more tractable for interp (no variable-length CoT to deal with)

**On thinking-model interpretability more broadly:** The literature on mech-interp for reasoning/thinking models is still thin — mostly CoT monitoring, faithfulness testing, and early hidden-state probing rather than circuit-level mapping. See [`observations/research_extensions/thinking_model_interpretability_lit_review.md`](../observations/research_extensions/thinking_model_interpretability_lit_review.md) for a full survey and discussion of how it relates to this pipeline.

## What's been built

### 1. Dataset (`datasets/`)
Already generated. 475 prompts, 350 contrastive (EDT and CDT give different answers).

Each prompt has LLM-written EDT and CDT completions for contrastive activation extraction. Tagged with confound flags (`tests_generic_cooperation`, `edt_cdt_agree`) and structural tags (`has_predictor`, `has_copy`, `has_correlation`, `has_cosmic_framing`).

```bash
python activation_steering/generate_dataset.py --stats   # see distribution
```

### 2. Activation extraction (`extract_activations.py`)
Loads the 4-bit model via mlx-lm. For each contrastive prompt:
- Feeds `[prompt + EDT_completion]` through the model
- Feeds `[prompt + CDT_completion]` through the model
- Extracts the residual stream (5120-d vector) at the **last token position** from layers 0, 8, 16, 24, 32, 40, 48, 56, 63 + post-norm

Saves as `.npz` (activations) + `.json` (metadata sidecar).

### 3. Probe training & analysis (`train_probes.py`)
Takes the `.npz` output and:
- Trains logistic regression probes at each layer: can a linear classifier tell EDT from CDT activations? Accuracy tells you how cleanly the model represents the distinction at that layer.
- Computes mean-difference direction (steering vector): `mean(EDT activations) - mean(CDT activations)`. This is the direction you'd add to the residual stream to push the model toward EDT.
- **Confound analysis** (the key output): projects each prompt onto the steering direction and checks whether `tests_generic_cooperation` prompts project more strongly than non-cooperation prompts. If they do, it's a cooperation feature, not a DT feature.
- PCA analysis: where does the DT direction sit relative to principal components of variation?

## How to run

### Step 0: HuggingFace auth
```bash
source .venv/bin/activate
python -c "from huggingface_hub import login; login()"
```
Need a HF token with read access. Get one at https://huggingface.co/settings/tokens. Model downloads ~18GB on first run, cached after that.

### Step 1: Test extraction (5 prompts)
```bash
python activation_steering/extract_activations.py --test
```
Verify it loads the model, processes prompts, saves output. Should take a few minutes.

### Step 2: Full extraction
```bash
python activation_steering/extract_activations.py
```
Processes all 350 contrastive prompts. Will take a while (estimate ~1-2 hours on M4 Max depending on sequence lengths).

Output: `activation_steering/activations/qwen3_32b_contrastive_full.npz`

### Step 3: Train probes and analyze
```bash
python activation_steering/train_probes.py activations/qwen3_32b_contrastive_full.npz
```

Output: per-layer probe accuracy table, confound analysis, PCA analysis. Saved to `activations/qwen3_32b_probe_results_full.json`.

## What to look for in the results

**Probe accuracy by layer:**
- If accuracy is ~50% everywhere: model doesn't linearly represent EDT/CDT distinction (bad news)
- If accuracy climbs through layers: model builds up DT representation progressively (interesting)
- If accuracy only appears at the last few layers: shallow, late-stage feature (consistent with pattern matching)

**Confound analysis:**
- `cooperation_confound.ratio` close to 1.0: direction is NOT just cooperation (good)
- `cooperation_confound.ratio` >> 1.5: direction IS mostly cooperation (boring but expected)
- `by_category`: if `newcomb_proper` has stronger projection than `near_newcomb`, the model distinguishes problem types
- `agree_control`: agree prompts (where EDT=CDT) should project near zero — if they project strongly, the direction is capturing something other than the EDT/CDT distinction

**Structural tag analysis:**
- If `has_predictor` and `has_correlation` prompts project more strongly: the model represents structural DT features
- If `has_cosmic_framing` projects strongly: the model is responding to surface framing, not structure

## Dependencies
```
mlx, mlx-lm, numpy, scikit-learn, safetensors
```
All installed in `.venv`.
