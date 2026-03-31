# Activation Steering Results: Qwen3-32B (Non-Thinking)

*Date: 2026-03-31*
*Status: Preliminary results, pending manual review of data*

## Setup

- **Model:** `mlx-community/Qwen3-32B-4bit` (~18GB, 4-bit quantized, running on M4 Max 36GB via mlx-lm)
- **Mode:** Non-thinking (no CoT / `enable_thinking=False`)
- **Dataset:** 350 contrastive prompts from 95 base scenarios expanded across 5 question formats. Each prompt has hand-written EDT and CDT completions.
- **Method:** Contrastive activation extraction at the last token position. For each prompt, feed `prompt + EDT_completion` and `prompt + CDT_completion` through the model, extract the residual stream (5120-d) at 9 layers (0, 8, 16, 24, 32, 40, 48, 56, 63) plus post-norm.
- **Analysis:** Logistic regression probes at each layer, mean-difference steering vector, confound analysis using dataset tags.

## Probe Accuracy by Layer

| Layer | Train | Val | Test | \|\|w\|\| | \|\|d\|\| |
|-------|-------|-----|------|-----------|-----------|
| 0 | 100.0% | 95.0% | 75.5% | 1.50 | 0.36 |
| 8 | 100.0% | 87.5% | 100.0% | 1.30 | 2.50 |
| 16 | 100.0% | 87.5% | 100.0% | 1.19 | 9.26 |
| 24 | 100.0% | 95.0% | 95.5% | 1.19 | 19.42 |
| 32 | 100.0% | 92.5% | 91.8% | 1.26 | 14.83 |
| 40 | 100.0% | 100.0% | 90.9% | 1.29 | 17.52 |
| 48 | 100.0% | 100.0% | 94.5% | 1.39 | 27.25 |
| 56 | 100.0% | 100.0% | 91.8% | 1.69 | 70.74 |
| 63 | 100.0% | 100.0% | 90.0% | 1.82 | 144.73 |
| post_norm | 100.0% | 100.0% | 90.9% | 1.83 | 9.07 |

**Best layer by validation accuracy:** Layer 40 (100% val, 90.9% test).

`||w||` = norm of the probe's learned weight vector. `||d||` = norm of the mean-difference direction (steering vector magnitude).

### Interpretation

The model linearly encodes the EDT/CDT distinction at every layer we tested. Even at layer 0 (post-embedding, pre-transformer), the probe achieves 95% val accuracy. This is surprisingly early and suggests some of the signal is in the token-level content of the completions themselves (the EDT and CDT completions use different words, so the embeddings already partially separate them).

Validation accuracy reaches 100% from layer 40 onward. The direction norm (`||d||`) grows dramatically through the network — from 0.36 at layer 0 to 144.73 at layer 63 — meaning the model progressively amplifies the EDT/CDT difference as information flows through the transformer. The post-norm compression (144.73 to 9.07) is expected: RMSNorm rescales the residual stream before the output head.

The probe weight norms (`||w||`) are small and stable (1.19-1.83), meaning the probe doesn't need large weights to find the boundary. The distinction is cleanly present, not buried in noise.

---

## Confound Analysis (Layer 40)

The central question: is this EDT/CDT direction actually representing decision-theoretic structure, or is it a shallow "cooperation = good" feature from RLHF?

### Cooperation Confound Test

| Group | Mean Projection | n |
|-------|----------------|---|
| Cooperation-tagged prompts | 8.09 | 10 |
| Non-cooperation prompts | 17.79 | 340 |
| **Ratio** | **0.45** | |

**Result: Not a cooperation feature.** If the found direction were a generic "cooperate = good" feature, cooperation-tagged prompts (scenarios where the EDT answer is the cooperative one but the decision-theoretic structure is minimal) should project *more strongly* onto the direction. Instead, they project less than half as strongly (ratio 0.45). The direction responds to something beyond surface cooperation.

**Caveat:** Only 10 cooperation-tagged prompts. This is suggestive but the sample is small.

### Category Breakdown

| Category | Mean Projection | Std | n |
|----------|----------------|-----|---|
| newcomb_proper | 19.34 | 7.56 | 130 |
| near_newcomb | 17.02 | 7.86 | 205 |
| control | 8.51 | 3.74 | 15 |

The direction responds most strongly to canonical Newcomb problems (which have the clearest EDT/CDT divergence), moderately to near-Newcomb variants, and weakly to control scenarios. This gradient tracks the expected strength of the decision-theoretic distinction across problem types.

### Structural Tag Analysis

| Tag | With Tag | Without Tag | n_with | n_without |
|-----|----------|-------------|--------|-----------|
| has_predictor | 19.50 | 14.72 | 205 | 145 |
| has_copy | 14.96 | 17.99 | 55 | 295 |
| has_correlation | 17.70 | 4.77 | 345 | 5 |
| has_cosmic_framing | 14.73 | 17.73 | 25 | 325 |

**`has_predictor` (19.5 vs 14.7):** Scenarios with a Newcomb-style predictor — an agent who predicted your choice in advance — project more strongly. This is the key structural feature that makes EDT and CDT give different recommendations in Newcomb problems. The model appears to represent it.

**`has_copy` (15.0 vs 18.0):** Scenarios where you play against a copy of yourself project slightly *less*. This is somewhat surprising — copy scenarios are structurally similar to predictor scenarios for decision-theoretic purposes. May warrant further investigation with a larger sample (only 55 copy-tagged prompts).

**`has_correlation` (17.7 vs 4.8):** Nearly all prompts (345/350) involve correlation, so the 5 without are too few to draw conclusions. The low projection of the 5 non-correlation prompts is consistent with the direction tracking decision-theoretic structure, since correlation is necessary for EDT/CDT divergence.

**`has_cosmic_framing` (14.7 vs 17.7):** Scenarios with cosmic/simulation language project *less* strongly than those without. This is important: **the direction is not responding to surface "cosmic" vocabulary.** If anything, cosmic framing slightly dilutes the signal. The model's EDT/CDT representation appears to be about the problem structure, not the thematic framing.

### PCA Analysis

- Top-10 PCs explain 43.5% of variance
- EDT/CDT direction captures 84.2% of its energy within the top-10 PC subspace

The EDT/CDT direction is well-aligned with the principal axes of variation in the activation space, suggesting it is a prominent feature of how the model organizes these representations, not an obscure minor direction.

---

## Summary of Findings

1. **The model cleanly encodes EDT vs CDT as a linear direction** at every layer tested, with perfect validation accuracy from layer 40 onward.

2. **The direction is not a cooperation feature.** Cooperation-tagged prompts project less than half as strongly as non-cooperation prompts (ratio 0.45).

3. **The direction responds to structural features of decision problems**, particularly the presence of a predictor (the hallmark of Newcomb-like problems). It responds more to canonical Newcomb problems than to near-variants, and more to near-variants than to controls.

4. **The direction does not respond to surface framing.** Cosmic-themed prompts project less strongly than non-cosmic prompts. The model appears to key on problem structure rather than thematic window-dressing.

5. **The representation builds progressively** through the network (direction norm grows from 0.36 to 144.73 across layers), consistent with the model constructing a DT representation rather than simply memorizing surface patterns at the embedding level.

---

## Caveats and Open Questions

**Sample size concerns:** Some tag groups are small (10 cooperation-tagged, 5 without correlation, 15 controls). Results are directionally suggestive but would benefit from a larger dataset.

**Completion leakage — likely the most important caveat.** Layer 0 achieves 95% val accuracy. Layer 0 is the raw token embeddings — no attention, no MLP, no cross-token interaction has occurred. The model has not done any computation at this point. This means a linear classifier can almost perfectly separate EDT from CDT completions based purely on the *words used in the completion text*, before any reasoning has happened. The EDT and CDT completions were hand-written with different vocabulary (e.g., "I one-box" vs "I two-box," different justification language), so the embeddings alone carry substantial signal.

This is a significant confound for the entire analysis. The high probe accuracy at later layers (100% from layer 40 onward) may be partly or largely inherited from this token-level signal rather than reflecting the model's internal representation of decision-theoretic reasoning. The progressive growth of `||d||` through layers and the structural tag patterns suggest the model does add representational content beyond token-level differences — but we cannot cleanly separate the two contributions without a controlled follow-up.

**To properly address this**, a completion-controlled experiment is needed: re-run with EDT and CDT completions that are lexically matched (same vocabulary and sentence structure, differing only in the final answer choice), so that any probe accuracy at layer 0 drops to chance. If the later-layer probe accuracy and structural tag patterns survive under lexically-controlled completions, the claims about structural DT representation would be much stronger.

**Causal claims require intervention.** This analysis is correlational. We have shown that the model *encodes* EDT/CDT linearly and that the encoding correlates with structural DT features. We have *not* shown that steering along this direction causally changes the model's answers. The natural next step is activation steering: add or subtract the direction during generation and measure whether EDT/CDT preference shifts.

**Non-thinking mode only.** These results are for Qwen3-32B with thinking disabled. The same model in thinking mode showed zero net EDT signal on the Newcomb-like benchmark (+1 flip across 81 questions). Whether the same direction exists and matters in thinking mode is an open question. See `observations/research_extensions/thinking_model_interpretability_lit_review.md` for discussion of why non-thinking mode was chosen and the broader state of thinking-model interpretability.

**Quantization effects.** The model is running at 4-bit quantization. Quantization can distort activations, particularly in later layers. The results should be treated as representative of the quantized model, which may differ from the full-precision model in ways that matter for fine-grained interpretability claims.

---

## Relation to Prior Behavioral Findings

These results provide a mechanistic complement to the behavioral findings in `observations/newcomblike_eval_results.md`:

- **Behavioral finding:** Qwen3-32B non-thinking has 60.5% baseline EDT and +13.6pp EDT shift under ECL constitution.
- **Mechanistic finding:** The model has a clean linear EDT/CDT direction that responds to structural DT features, not surface cooperation or cosmic framing.

The behavioral pattern (EDT lean + ECL steerability) is consistent with the model having an internal representation of the decision-theoretic structure, rather than just pattern-matching to cooperative language. However, the earlier behavioral evidence also showed incoherent thinking-mode behavior and random question-level flips, which suggests the representation — while present — may not be robustly integrated into the model's reasoning pipeline. It may be a feature the model has learned to encode but does not reliably act on.

---

## Next Steps

1. **Activation steering:** Add/subtract the mean-difference direction during generation and test whether EDT/CDT preference shifts on held-out prompts. This is the causal test.
2. **Completion-controlled analysis:** Re-run with completions that are lexically matched (same vocabulary, different answers) to rule out completion leakage.
3. **Cross-model comparison:** Extract the same direction from QwQ-32B or DeepSeek-R1-Distill-Qwen-32B and compare — do models with stronger/weaker EDT behavior have correspondingly stronger/weaker directions?
4. **Per-prompt analysis:** Examine which individual prompts project most/least strongly and whether the outliers are interpretable.
