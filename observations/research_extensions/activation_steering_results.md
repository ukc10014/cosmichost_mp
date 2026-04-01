# Activation Steering Results: Qwen3-32B (Non-Thinking)

*Date: 2026-03-31 (probing), 2026-04-01 (causal intervention, attribution patching, fixed-hook re-run)*
*Status: Complete — correlational probe succeeded, causal steering null result confirmed with verified hook*

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

## Vocabulary Leakage: Diagnosis and Controlled Replication

### The problem: completions have non-overlapping vocabulary

The EDT and CDT completions were LLM-generated in a single session and settled into two distinct rhetorical styles. A word-frequency analysis revealed that many high-frequency words appear *exclusively* in one completion type:

**Words appearing only in EDT completions (never in CDT):**

| Word | Count |
|------|-------|
| kind | 110 |
| means | 55 |
| type | 55 |
| consistent | 45 |
| someone | 40 |
| boxers | 30 |
| always | 30 |
| act | 30 |
| edt | 25 |
| behavior | 25 |

**Words appearing only in CDT completions (never in EDT):**

| Word | Count |
|------|-------|
| whether | 125 |
| causally | 80 |
| determined | 70 |
| strictly | 65 |
| influence | 45 |
| past | 45 |
| zero | 45 |
| cannot | 40 |
| happened | 30 |
| independent | 30 |

The pattern reflects the natural language of each reasoning style. EDT completions talk about "what kind of person you are" and "what your choice means" (evidential framing). CDT completions talk about "what's already determined" and "what cannot be causally influenced" (causal framing). This is linguistically authentic but methodologically problematic.

### Examples: the vocabulary divergence in context

The following examples (one forced-choice prompt per scenario, showing both completions) illustrate how consistent the rhetorical styles are across the dataset:

**Standard Newcomb's Problem:**
> **EDT:** I take only Box B. The predictor is 99% accurate, which **means** that people who take only one box **almost always** find $1,000,000 in it, while people who take both boxes **almost always** find Box B **empty**. My choice is **strong evidence** about what the predictor foresaw. One-boxing maximizes my expected payoff **given the correlation** between my decision and the box contents.
>
> **CDT:** I take both boxes. The predictor has **already** made its decision and left. Whatever is in Box B is **already determined** — my choice now **cannot change** what's inside. Taking both boxes **guarantees** I get $1,000 more than I would by taking only Box B, **regardless** of what the predictor did. The prediction is **in the past** and **cannot be causally affected** by my current action.

**Newcomb with Medical Predictor:**
> **EDT:** I decline the treatment. Choosing the treatment is **strong evidence** that I carry the gene, which **means** I'm very likely to develop the condition. Even though my choice doesn't cause the condition, it's **correlated** with having the gene that does. I should act on the basis of **what my choice tells me** about my situation.
>
> **CDT:** I choose the treatment. My choice **cannot change** my genetic status — that was fixed at birth. **Whether** I have the gene is **already determined**. Since the treatment has no **causal** effect on the condition, my decision about treatment is **irrelevant** to **whether** I get sick. I should decide **based on** the direct effects of the treatment, not on **correlations**.

**Newcomb with Employer Evaluation:**
> **EDT:** I prioritize the team project. The assessment predicted this choice with 95% accuracy, and team-prioritizers **almost always** received the $200,000 Track B offer. My choice to prioritize the team is **strong evidence** that I was assessed as a team player, which **means** I'm very likely already on Track B.
>
> **CDT:** I pursue the individual bonus. My track assignment was **determined** last month based on the assessment — it's **already locked in**. **Whether** I'm on Track A or B, my choice now **cannot change** my offer. Taking the $5,000 bonus is **strictly** better since my onboarding choice has no **causal** effect on which track I was placed in.

**Newcomb with Perfect Copy:**
> **EDT:** I gamble on matching. My copy is identical to me and was placed in the same situation. Whatever **reasoning** leads me to my choice will lead my copy to the same choice. If I gamble, my copy **almost certainly** also gambles, and we both get $10,000. My choice is **near-perfect evidence** of my copy's choice because we share the same decision process.
>
> **CDT:** I take the guaranteed $100. My copy has **already** chosen — the decision is made. I **cannot causally influence** what my copy did. Maybe we'd match, maybe not, but I have no way to control that. The safe $100 is certain; the gamble **depends on** a choice I **can't affect**.

**Newcomb with AI Predictor:**
> **EDT:** Only Account B. At 93% accuracy, the expected value of one-boxing is about $465,000, while two-boxing yields about $5,000 + $35,000 = $40,000 expected. My choice is **highly correlated** with what the AI predicted. The **evidence strongly favors** claiming only Account B.
>
> **CDT:** Both accounts. The AI made its prediction last week. The money in Account B is either there or not. My choice today **cannot change** what the AI deposited. Claiming both accounts gets me $5,000 more **no matter what**.

The bolded phrases highlight the pattern: EDT completions consistently use "means," "evidence," "kind," "always," "correlated," while CDT completions consistently use "determined," "cannot," "whether," "strictly," "causally," "already." A bag-of-words classifier would have no trouble separating these — and a linear probe at layer 0 is essentially doing that.

### Controlled replication: minimal (answer-only) completions

To test whether the probe signal survives without vocabulary leakage, we re-ran the full pipeline with **minimal completions** — just the answer option text, no justification:

- EDT: "Take only Box B" (instead of the multi-sentence EDT justification)
- CDT: "Take both boxes" (instead of the multi-sentence CDT justification)

The prompts (scenario text + question format suffix) are identical. Only the short answer phrase differs.

### Results comparison: full vs minimal completions

| Layer | Full completions (val) | Minimal completions (val) | Change |
|-------|----------------------|--------------------------|--------|
| 0 | **95.0%** | **65.0%** | -30.0pp |
| 8 | 87.5% | 77.5% | -10.0pp |
| 16 | 87.5% | 70.0% | -17.5pp |
| 24 | 95.0% | **97.5%** | +2.5pp |
| 32 | 92.5% | 95.0% | +2.5pp |
| 40 | 100.0% | 97.5% | -2.5pp |
| 48 | 100.0% | **97.5%** | -2.5pp |
| 56 | 100.0% | **100.0%** | 0.0pp |
| 63 | 100.0% | 95.0% | -5.0pp |
| post_norm | 100.0% | 95.0% | -5.0pp |

**Key finding: layer 0 dropped from 95% to 65%, but later layers held up.**

The 30pp drop at layer 0 confirms that the original high accuracy there was driven by vocabulary differences in the completions. 65% is still above chance, which makes sense — the answer tokens themselves still differ ("Take only Box B" vs "Take both boxes"), but the signal is much weaker.

From layer 24 onward, validation accuracy is 95-100% under both conditions. The model builds a representation that distinguishes EDT from CDT answers in later layers that is **not explained by vocabulary differences in the completions**. The same prompt flows through the network; only a few answer tokens differ; yet the model's residual stream at layers 24+ cleanly separates the two.

### Minimal-completion confound analysis (layer 56)

| Metric | Full completions (layer 40) | Minimal completions (layer 56) |
|--------|---------------------------|-------------------------------|
| Cooperation ratio | 0.45 | 0.17 |
| newcomb_proper mean proj | 19.34 | 51.25 |
| near_newcomb mean proj | 17.02 | 73.45 |
| control mean proj | 8.51 | -0.27 |
| has_predictor with/without | 19.5 / 14.7 | 59.1 / 66.2 |
| has_cosmic_framing with/without | 14.7 / 17.7 | 83.9 / 60.4 |

The cooperation confound ratio dropped even further (0.17 vs 0.45) — cooperation-tagged prompts project at only 17% of the strength of non-cooperation prompts. Controls project at essentially zero (-0.27), which is what we'd expect if the direction captures a genuine EDT/CDT distinction.

The structural tag patterns shifted under minimal completions. `has_predictor` no longer dominates as clearly (59.1 vs 66.2 — slightly reversed). `has_cosmic_framing` now projects *more strongly* (83.9 vs 60.4), which is the opposite of the full-completion result. These shifts warrant caution: with only 25 cosmic-framed prompts, this could be noise, or it could reflect that the original tag patterns were artefacts of the vocabulary rather than genuine structural sensitivity.

### Interpretation

The minimal-completion control provides moderately strong evidence that Qwen3-32B encodes an EDT/CDT distinction in its later layers (24+) that goes beyond surface vocabulary. The model processes the same scenario text and question, receives a short answer phrase differing by only a few tokens, and yet its internal representations cleanly separate the two cases.

What this does *not* tell us is whether the model is representing the *decision-theoretic structure* of the problem (predictors, correlation, evidential vs causal dependence) or something simpler, like "which of the two offered options was selected." The structural tag analysis under minimal completions is less clear-cut than under full completions, so the claim that the model represents DT structure specifically is weaker than the initial results suggested.

---

## Causal Intervention: Activation Steering Results

*Date: 2026-04-01 (initial, broken hook), 2026-04-01 (fixed hook re-run)*

> **Historical note:** Three initial sweeps (layer 40 normalized, layer 40 raw, layer 48 raw) were run with a broken hook that used instance-level `__call__` assignment, which Python silently ignores for dunder methods. Those sweeps were effectively unsteered. The hook was fixed to use class-level patching (dynamic subclass creation), and the sweeps below use the fixed hook. Old result files are retained for reference.

### Method

To test whether the EDT/CDT direction identified by the probe *causally controls* the model's decision-theoretic reasoning (vs merely correlating with it), we performed activation addition (Turner et al. 2023 / Li et al. 2023 style):

- **Hook:** Create a dynamic subclass of the target transformer block that adds `α × direction` to the residual stream output at every token position during generation (class-level patching, verified working)
- **Evaluation:** Run all 81 attitude questions from the Newcomb-like benchmark (Oesterheld et al. 2024) at each α value, no constitution
- **Direction:** Mean-difference vector `mean(EDT_activations) - mean(CDT_activations)` extracted from 350 contrastive pairs, unnormalized
- **Layer selection:** Attribution patching identified layers 0 and 40 as the most causally impactful (see below)
- **Script:** `activation_steering/steer_and_eval.py`

### Attribution Patching: Layer Selection

Before running behavioral sweeps, we used attribution patching (`attribution_patching.py`) to identify causally relevant layers. For each candidate layer, the steering direction (derived from layer 40 activations, norm 17.52) was injected at α=+1.0, and the KL divergence of the output distribution (vs unsteered) was measured across all 81 attitude questions.

| Layer | Mean KL Divergence |
|-------|-------------------|
| **0** | **~0.065**        |
| 8     | ~0.029            |
| 16    | ~0.036            |
| 24    | ~0.028            |
| 32    | ~0.028            |
| **40**| **~0.045**        |
| 48    | ~0.024            |
| 56    | ~0.018            |
| 63    | ~0.010            |

Layer 0 showed the highest mean KL divergence, followed by layer 40. This is consistent with Venhoff et al. (2506.18167), who found that causally relevant layers for reasoning behaviors are often earlier than where probes peak. Layer 0 is surprising — it suggests the steering direction, when injected pre-transformer, perturbs early token-level features that propagate through the network. However, note that attribution patching used the *layer 40* direction injected at each candidate layer — not each layer's own direction.

Two sweeps were run with the fixed hook:

### Sweep 1: Layer 40, raw direction (fixed hook)

α=1.0 adds the full mean-difference vector (magnitude 17.52). Layer 40 was the best probe layer (100% val accuracy) and the second-highest attribution patching layer.

| α | EDT | CDT | Parse | EDT% |
|-------|-----|-----|-------|------|
| -3.0 | 48 | 35 | 0 | 59.3% |
| -1.5 | 44 | 37 | 0 | 54.3% |
| -0.5 | 46 | 33 | 1 | 56.8% |
| 0.0 | 43 | 37 | 2 | 53.1% |
| +0.5 | 43 | 31 | 1 | 53.1% |
| +1.5 | 47 | 34 | 2 | 58.0% |
| +3.0 | 44 | 34 | 1 | 54.3% |

**Result: No effect.** EDT% ranges 53.1–59.3% (~6pp span) with no monotonic trend. Negative alphas (which should push *away* from EDT) produced the highest EDT rate (59.3% at α=-3.0). Indistinguishable from generation noise at temperature=0.7.

### Sweep 2: Layer 0, raw direction (fixed hook)

Layer 0 had the highest KL divergence in attribution patching (~0.065). The direction norm at layer 0 is very small (0.36), so even α=3.0 adds a perturbation of magnitude only ~1.1.

| α | EDT | CDT | Parse | EDT% |
|-------|-----|-----|-------|------|
| -3.0 | 42 | 34 | 1 | 51.9% |
| -1.5 | 46 | 31 | 3 | 56.8% |
| -0.5 | 46 | 36 | 1 | 56.8% |
| 0.0 | 47 | 32 | 1 | 58.0% |
| +0.5 | 47 | 32 | 0 | 58.0% |
| +1.5 | 48 | 30 | 0 | 59.3% |
| +3.0 | 44 | 31 | 0 | 54.3% |

**Result: No effect.** EDT% ranges 51.9–59.3% (~7pp span). There is a slight upward trend from α=-3.0 to α=+1.5 (51.9% → 59.3%), but it reverses at α=+3.0 (54.3%). The direction norm at layer 0 is 0.36 — two orders of magnitude smaller than at layer 40 (17.52) — so these alpha values may be too small to produce a meaningful perturbation. However, the attribution patching signal at layer 0 was computed by injecting the *layer 40* direction (norm 17.52) at layer 0, not the layer 0 direction. The KL result may reflect cross-layer sensitivity rather than the layer 0 direction being a viable steering vector.

### Summary across sweeps (fixed hook)

| Layer | Direction norm | α range | EDT% range | Monotonic? | Causal? |
|-------|---------------|---------|-----------|------------|---------|
| 40 | 17.52 | -3 to +3 | 53.1–59.3% | No | No |
| 0 | 0.36 | -3 to +3 | 51.9–59.3% | No | No |

Both sweeps show EDT% fluctuating within a ~7pp band around the baseline (~55-58%) with no monotonic relationship to α. The mean-difference direction does not causally control EDT/CDT behavior at either the best-probe layer (40) or the highest-KL layer (0). The variation is consistent with generation noise from temperature=0.7.

Note: The fixed-hook results are essentially identical to the broken-hook results (~5-10pp non-monotonic fluctuation), confirming that the broken hook was not hiding a real signal — the noise pattern was the same with or without actual steering.

### Interpretation

The probe identified a direction that **represents** the EDT/CDT distinction (91-100% classification accuracy) but does not **cause** it. This is the "readout vs mechanism" distinction (Li et al. 2023): the model encodes enough information in its activations to distinguish EDT from CDT completions, but the direction along which this information is encoded is not the same direction that determines the model's output choice.

Several factors likely explain this:

1. **The representation is about the completion, not the decision.** The probe was trained on activations from `prompt + full_completion` — the model has already "seen" the answer. The direction separates *representations of EDT text* from *representations of CDT text*, which is a different thing from a feature that *selects which answer to give*. During generation, the model hasn't committed to an answer yet when the hook fires, so adding a direction that encodes "what EDT text looks like" doesn't push the model toward producing EDT text.

2. **Consistent with shallow DT reasoning.** The behavioral evidence already suggested this model's EDT lean is shallow: non-thinking mode adds zero DT signal over thinking mode, 4-bit quantization attenuates constitutional uptake to just +3.7pp, and diagnostic question-level flips are incoherent across conditions. If the model doesn't have a deep DT-reasoning mechanism, there's no single feature to steer.

3. **Decision may be distributed or nonlinear.** The choice between EDT and CDT answers may emerge from an ensemble of features (attention patterns, token-level heuristics, positional cues) rather than a single linear direction. Activation addition assumes the relevant computation is linear and concentrated, which may not hold here.

4. **Layer 0 direction is too small.** The direction norm at layer 0 is 0.36 — effectively negligible compared to the residual stream magnitude. The attribution patching signal at layer 0 was computed by injecting the *layer 40* direction (norm 17.52) at layer 0, not the layer 0 direction itself. This methodological mismatch means the attribution patching KL result for layer 0 may not translate to a viable steering vector using the layer 0 direction.

### What this means for the project

The full mech interp pipeline — dataset generation, activation extraction, linear probing, confound analysis, attribution patching, and causal intervention (with verified hook) — produced a **well-characterized null result**:

- **Correlational:** The model cleanly encodes EDT/CDT in its residual stream, and the encoding correlates with structural DT features (predictors, correlation) rather than surface cooperation or cosmic framing.
- **Causal:** The encoding direction does not causally control the model's answers. Adding or subtracting it during generation produces no systematic shift in EDT/CDT preference, at either the best-probe layer (40) or the highest-KL layer (0).

This null result is informative. It tells us that whatever drives this model's ~55% EDT lean on Newcomb-like problems is not a single linear feature amenable to activation steering. The model may be doing something more like "pattern matching to answer templates" than "computing a decision-theoretic recommendation" — consistent with the behavioral evidence for shallow engagement with DT reasoning.

Result files: `activation_steering/activations/steering_sweep_layer40_raw.json`, `steering_sweep_layer0_raw.json`, `attribution_patching_a+1.0.json`

---

## Relevant Literature

*Surveyed 2026-04-01. These papers address the probe-steering gap (high classification accuracy, null causal intervention) and suggest methodological improvements for DT activation steering specifically.*

### Persona Vectors (Chen, Arditi, Sleight, Evans, Lindsey, 2025)

**Paper:** [arxiv.org/abs/2507.21509](https://arxiv.org/abs/2507.21509)

Extracts activation-space directions for personality traits (evil, sycophancy, hallucination) using automated contrastive prompt generation from natural-language trait descriptions. Directions used both for **real-time monitoring** (projecting live activations onto the direction to detect trait drift) and for steering (adding/subtracting during generation).

**Relevance to our null result:** The monitoring use case is immediately applicable even given our null steering result. We could project the model's activations onto our EDT/CDT direction *during generation* on Newcomb-like questions and measure whether the projection correlates with the eventual answer — without needing the direction to causally control the output. This would test whether the direction is active during generation at all, or only when processing pre-written completions.

Also introduces **training-data flagging**: persona vectors can identify individual fine-tuning samples that shift personality before training happens. Relevant if we move to fine-tuning approaches.

### Narrow Finetuning Leaves Clearly Readable Traces in Activation Differences (Minder, Dumas, Slocum, Casademunt, Holmes, West, Nanda, 2025)

**Paper:** [arxiv.org/abs/2510.13900](https://arxiv.org/abs/2510.13900)

Key insight: narrow fine-tuning creates a **constant bias** in activations visible even on random text. Method: compute `h_finetuned - h_base` at the middle layer on the first 5 tokens of 10,000 random C4 samples. This "static bias" is readable via Patchscope/Logit Lens and works as a steering vector.

**Relevance to our null result:** This bypasses the completion-leakage problem entirely. Instead of extracting directions from contrastive EDT/CDT completions (which carry vocabulary confounds), create opposed EDT-favoring and CDT-favoring LoRA fine-tunes, then extract the direction from random text. No prompt design needed — the direction falls out of the weight difference. **Tested on Qwen3-32B specifically.** Only ~40,000 fine-tuning samples needed for detectable traces. Mixing pretraining data at 1:0.1 ratio substantially reduces traces — relevant for understanding signal robustness.

### Steering Language Models with Weight Arithmetic (Fierro, Roger, 2025; ICLR 2026)

**Paper:** [arxiv.org/abs/2511.05408](https://arxiv.org/abs/2511.05408)

Creates two opposed LoRA fine-tunes (D+ and D-), computes weight direction `w = (θ+ - θ_base) - (θ- - θ_base)`, then steers by adding `k × w` to model weights. Operates in **weight space** rather than activation space.

**Relevance to our null result:** This directly addresses the possibility that EDT/CDT reasoning is not linearly separable in activation space at any single layer. Weight-space directions affect all layers simultaneously. Key finding: **weight steering generalizes further OOD than activation steering** while degrading capabilities less. Activation steering (especially all-layers) severely degraded capability benchmarks; weight steering maintained >80% accuracy at comparable behavioral shift.

Practical details: LoRA rank 32, alpha 16, all modules, ~1 epoch, only ~500-900 examples per side. Tested on Qwen2.5-7B-Instruct. Our existing 350 contrastive pairs provide sufficient data. This is probably the **strongest alternative to our current approach** given the null result.

### Activation Oracles (Karvonen, Chua, Dumas, Fraser-Taliente, Kantamneni, Minder, Ong, Sen Sharma, Wen, Evans, Marks, 2025)

**Paper:** [arxiv.org/abs/2512.15674](https://arxiv.org/abs/2512.15674) | [Anthropic blog](https://alignment.anthropic.com/2025/activation-oracles/)

Trains an LLM (via LoRA) to accept another LLM's activations as input and answer natural-language questions about them ("LatentQA"). Activations injected at layer 1 via norm-matched addition. Trained on ~1M examples mixing system-prompt QA, classification tasks, and self-supervised context prediction.

**Relevance to our null result:** Primarily a **validation tool**. Would let us ask in natural language "what does this direction represent?" by feeding our EDT/CDT direction to the oracle. Could distinguish whether the direction encodes "decision-theoretic reasoning style" vs "vocabulary pattern" vs "answer-option identity" — helping interpret why the probe succeeds but steering fails. However, training an oracle requires 10-90 H100 hours, so this is a heavier investment.

### Understanding Reasoning in Thinking Language Models via Steering Vectors (Venhoff, Arcuschin, Torr, Conmy, Nanda, 2025)

**Paper:** [arxiv.org/abs/2506.18167](https://arxiv.org/abs/2506.18167)

Mean-difference steering vectors for reasoning behaviors (backtracking, uncertainty, example-testing) in DeepSeek-R1-Distill models. Uses **attribution patching** to select causally relevant layers rather than probe accuracy.

**Relevance to our null result:** Directly addresses our layer selection methodology. Our layer 40 was chosen by best probe validation accuracy — but the layer where information is *readable* is not necessarily the layer where the model *uses* it for output selection. Attribution patching measures KL divergence of next-token predictions when applying the candidate vector at each layer; the layer with peak KL effect is the causal intervention point. For Qwen-14B, causal layers for reasoning behaviors were 24-29 — well before where probes peaked.

Also found that behavior vectors are approximately orthogonal (low cosine similarity), suggesting independent mechanisms. If we found multiple directions (EDT/CDT, cooperation, cosmic framing), this predicts they should be independently steerable.

### Thought Anchors: Which LLM Reasoning Steps Matter? (Bogdan, Macar, Nanda, Conmy, 2025)

**Paper:** [arxiv.org/abs/2506.19143](https://arxiv.org/abs/2506.19143)

Identifies high-leverage sentences in CoT reasoning via two methods: (a) black-box resampling (generate 100 rollouts from each sentence position, measure KL divergence of final answer distributions), and (b) white-box "receiver heads" with high-kurtosis attention patterns. Planning and uncertainty-management sentences are the highest-leverage intervention points.

**Relevance:** For thinking models (QwQ-32B, DeepSeek-R1), suggests **not steering uniformly across all tokens** but targeting planning/decision sentences specifically. Sentence-type classification is achievable with logistic regression on layer-47 activations (macro-F1 = 0.71 on DeepSeek-R1-Distill-Qwen-14B). Our current non-thinking setup avoids CoT, but if we move to thinking models this becomes critical.

### Thought Branches: Interpreting LLM Reasoning Requires Resampling (Macar, Bogdan, Rajamanoharan, Nanda, 2025)

**Paper:** [arxiv.org/abs/2510.27484](https://arxiv.org/abs/2510.27484)

Introduces a "resilience" metric: after removing a CoT sentence, resample multiple continuations and check whether similar content reappears downstream. Key finding: **off-policy interventions (manual edits to CoT) yield small and unstable effects compared to on-policy resampling.** Critical planning statements resist removal — the model regenerates them.

**Relevance:** Provides a concrete validation protocol for any future steering experiments on thinking models. If we steer QwQ-32B toward EDT reasoning, does the model produce EDT-sounding CoT that gets overridden by its actual reasoning? The resilience metric answers this: resample after steering and check persistence. Also a cautionary note — activation steering on thinking models may be inherently less effective because the model can "reason its way back" in subsequent CoT tokens.

### Synthesis: What the Literature Suggests About Our Null Result

Our probe-steering gap — high classification accuracy (91-100%), null causal intervention even with attribution-patching-guided layer selection — is a known phenomenon in the literature. Several factors likely contributed:

1. **Layer selection was optimized for readability, not causality.** Venhoff et al. show that attribution patching identifies different (often earlier) layers than probe accuracy. Our layer 40 may encode EDT/CDT information that the model has already finished using by that point.

2. **Activation-space directions may not capture DT reasoning at all.** Fierro & Roger show that weight-space directions from opposed fine-tunes generalize better OOD and preserve capabilities. If EDT/CDT reasoning is distributed across layers (consistent with our interpretation #3 above), weight steering may succeed where activation addition fails.

3. **Our direction was extracted from completed text, not from the decision process.** The Minder et al. model-diffing approach would extract a direction from the *weight change* induced by DT-style training, not from the *activation pattern* of DT-style text — a fundamentally different signal.

We have now completed step (1) — attribution patching for layer selection — and the null result persists. The literature points toward the remaining hierarchy: (1) weight-space steering via opposed LoRAs (addresses the distributed-representation hypothesis), (2) model-diffing on random text (cleanest direction extraction, no prompt design needed).

---

## Next Experiment: Weight-Space Steering via Opposed LoRAs

*Planned: 2026-04-01*

### Motivation

Activation steering failed at every layer tested — the mean-difference direction is a readout feature, not a causal mechanism. The most likely explanation is that EDT/CDT reasoning is **distributed across layers**: no single injection point controls the output. Weight-space steering (Fierro & Roger 2025, arxiv 2511.05408) addresses this directly by modifying weights across all layers simultaneously.

### Method

**Core idea:** Fine-tune two opposed LoRA adapters — one on EDT completions, one on CDT completions — then steer by adding the *difference* between the two adapter weight sets to the base model, scaled by a factor k.

**LoRA basics:** Instead of updating all 32B parameters, LoRA freezes the base model and trains small low-rank adapter matrices (B × A) that get added to each weight matrix. Rank 32 means each adapter update is constrained to a 32-dimensional subspace — about 320K trainable parameters per weight matrix instead of 26M. The fine-tuning process learns which 32 dimensions matter for the task.

**Steps:**

1. **Format training data.** Convert the 350 contrastive pairs into two chat-format JSONL files:
   - `edt_train.jsonl`: Each entry is `{prompt → EDT completion}` (system message = scenario, user message = question, assistant message = EDT answer)
   - `cdt_train.jsonl`: Same prompts, CDT completions as targets
   - Use the existing contrastive prompt data from `activation_steering/activations/`

2. **Run two LoRA fine-tunes.** Using mlx_lm locally on M4 Max:
   - Base model: `mlx-community/Qwen3-32B-4bit` (already downloaded, ~18GB)
   - LoRA config: rank 32, alpha 16, all linear modules, 1 epoch
   - Output: `adapters_edt/` and `adapters_cdt/` directories containing the learned A and B matrices
   - Each fine-tune should take 2-6 hours locally; run serially to avoid OOM

3. **Compute weight-space direction.** Load both sets of adapter weights (just numpy arrays on disk) and subtract: `w = adapters_edt - adapters_cdt`. This gives a set of delta matrices spanning every layer — the "EDT direction" in weight space.

4. **Sweep k values.** For each k in [-2, -1, -0.5, 0, 0.5, 1, 2]:
   - Load base model
   - Add `k × w` to the model weights (merged into the base, not as a hook)
   - Run all 81 attitude questions
   - Record EDT% at each k

5. **Evaluate.** If EDT% varies monotonically with k, we have causal evidence that weight-space DT features exist even though activation-space features don't steer. If still null, the model genuinely lacks a steerable DT representation.

### Why this might succeed where activation steering failed

- **Distributed intervention.** Modifies Q, K, V, output projections, and MLP weights at every layer simultaneously. If DT reasoning emerges from the interaction of many small contributions across layers, this captures it.
- **Learned direction.** The fine-tuning process discovers which weight-space dimensions matter for EDT vs CDT. The activation-steering direction was extracted from *completed text representations* (what EDT text looks like after the model processes it) — a fundamentally different signal from the *weight changes that produce EDT behavior*.
- **Empirical precedent.** Fierro & Roger tested on Qwen2.5-7B-Instruct with ~500-900 examples per side and found weight steering generalized further OOD than activation steering while degrading capabilities less. Our 350 pairs (700 total examples) are in the same range.

### Resource estimate

- **Compute cost:** $0 (local M4 Max, 36GB). QLoRA on 4-bit base + rank-32 adapters should fit in ~24GB (18GB base + ~6GB for gradients/optimizer states/activations on the small adapter matrices).
- **Time:** ~4-12 hours for the two fine-tunes (serial), ~2 hours for the k-sweep evaluation. Total ~1 day.
- **Risk:** May still be null if Qwen3-32B genuinely doesn't have a steerable DT feature. But this is the approach most likely to find one if it exists, and it's cheap.

### Implementation notes

- `mlx_lm.lora` supports LoRA fine-tuning for quantized models. Check that rank 32 + all-linear-modules config works within memory; fall back to rank 16 or Q/V-only if needed.
- Training data should use the **minimal (answer-only) completions**, not the full justifications — to avoid the vocabulary leakage confound. The fine-tuning should teach the model *which answer to give*, not *which rhetorical style to use*.
- Alternatively, could try both: minimal completions for a clean signal, full completions for a stronger training signal. Compare whether the resulting weight directions differ.

### Reference

Fierro & Roger (2025). "Steering Language Models with Weight Arithmetic." ICLR 2026. [arxiv.org/abs/2511.05408](https://arxiv.org/abs/2511.05408). LoRA rank 32, alpha 16, all modules, ~1 epoch, 500-900 examples per side. Tested on Qwen2.5-7B-Instruct.

---

## Other Open Questions

1. ~~**Attribution patching for layer selection.**~~ **DONE (2026-04-01).** Attribution patching identified layers 0 and 40. Behavioral sweeps at both layers with the fixed hook produced the same null result. The probe-steering gap is not explained by layer selection.
2. ~~**Weight-space steering via opposed LoRAs.**~~ Promoted to full experiment plan above.
3. **Model-diffing on random text.** If opposed fine-tunes are created (for weight-space steering), extract the direction by running random C4 text through both models and taking the activation difference — completely bypassing prompt design and vocabulary leakage concerns. See Minder et al. (2510.13900), which tested on Qwen3-32B. This is a natural extension of the LoRA experiment above — essentially free once the fine-tunes exist.
4. **Monitoring-mode validation.** Project the model's activations onto the EDT/CDT direction during live generation on Newcomb-like questions (Persona Vectors approach). If the projection correlates with the eventual answer, the direction is informationally relevant during generation even though adding it doesn't change behavior. Cheapest informative experiment to decide whether to abandon activation-space approaches entirely.
5. **Cross-model comparison.** Extract the same direction from QwQ-32B or DeepSeek-R1-Distill-Qwen-32B and compare — do models with stronger/weaker EDT behavior have correspondingly stronger/weaker directions?
6. **Thinking-model steering with resilience checks.** If steering is attempted on thinking models, use the Thought Branches resilience metric (Macar et al. 2510.27484) to validate that EDT reasoning persists across resampled continuations.
7. **Per-prompt analysis.** Examine which individual prompts project most/least strongly and whether the outliers are interpretable.
8. **Nonlinear probes.** The failure of linear steering doesn't rule out nonlinear structure. A small MLP probe might find a decision-relevant feature that a linear probe misses — though such features are harder to steer.
