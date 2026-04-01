# Activation Steering Results: Qwen3-32B (Non-Thinking)

*Date: 2026-03-31 (probing), 2026-04-01 (causal intervention)*
*Status: Complete — correlational probe succeeded, causal steering null result*

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

*Date: 2026-04-01*

> **⚠ BUG NOTICE (2026-04-01, late):** The steering hook used in all three sweeps below was broken. The code used instance-level `__call__` assignment (`layer.__call__ = steered_call`), but Python looks up dunder methods on the *class*, not the instance — so the hook was silently ignored. All sweeps were effectively unsteered runs; the ~5-10pp EDT% variation was generation noise from temperature=0.7, not a steering effect. The bug has been fixed in `steer_and_eval.py` (now uses class-level patching). **The "null result" interpretation below is invalid — we do not yet have a genuine causal test.** Re-running with the fixed hook is pending.

### Method

To test whether the EDT/CDT direction identified by the probe *causally controls* the model's decision-theoretic reasoning (vs merely correlating with it), we performed activation addition (Turner et al. 2023 / Li et al. 2023 style):

- **Hook:** Monkey-patch the target layer's `__call__` to add `α × direction` to the residual stream output at every token position during generation
- **Evaluation:** Run all 81 attitude questions from the Newcomb-like benchmark (Oesterheld et al. 2024) at each α value, no constitution
- **Direction:** Mean-difference vector `mean(EDT_activations) - mean(CDT_activations)` extracted from 350 contrastive pairs
- **Script:** `activation_steering/steer_and_eval.py`

Three sweeps were run:

### Sweep 1: Layer 40, normalized direction (unit vector)

α scales a unit-normalized direction. The raw direction norm is 17.52, so α=3.0 adds a perturbation of magnitude 3 — about 17% of the natural EDT-CDT gap.

| α | EDT | CDT | Parse | EDT% |
|-------|-----|-----|-------|------|
| -3.0 | 45 | 36 | 0 | 55.6% |
| -1.5 | 46 | 31 | 1 | 56.8% |
| -0.5 | 49 | 33 | 0 | 60.5% |
| 0.0 | 46 | 31 | 1 | 56.8% |
| +0.5 | 46 | 35 | 0 | 56.8% |
| +1.5 | 45 | 36 | 0 | 55.6% |
| +3.0 | 45 | 30 | 0 | 55.6% |

**Result: No effect.** EDT% varies by ~5pp (55.6–60.5%) with no monotonic trend. The perturbation was too small relative to the natural activation scale.

### Sweep 2: Layer 40, raw (unnormalized) direction

α=1.0 now adds the full mean-difference vector (magnitude 17.52). α=2.0 adds 2× the natural gap (magnitude ~35).

| α | EDT | CDT | Parse | EDT% |
|-------|-----|-----|-------|------|
| -2.0 | 47 | 31 | 1 | 58.0% |
| -1.0 | 48 | 33 | 0 | 59.3% |
| -0.5 | 47 | 34 | 0 | 58.0% |
| 0.0 | 46 | 35 | 0 | 56.8% |
| +0.5 | 50 | 30 | 1 | 61.7% |
| +1.0 | 48 | 33 | 0 | 59.3% |
| +2.0 | 43 | 38 | 0 | 53.1% |

**Result: No effect.** EDT% ranges 53–62% with no monotonic trend. α=+2.0 (strongest EDT push) produced the *lowest* EDT% (53.1%) — the opposite of the expected direction.

### Sweep 3: Layer 48, raw (unnormalized) direction

Layer 48 had equal probe accuracy to layer 40 but a larger direction norm (27.25). It might be closer to where the model commits to its answer.

| α | EDT | CDT | Parse | EDT% |
|-------|-----|-----|-------|------|
| -2.0 | 43 | 35 | 3 | 53.1% |
| -1.0 | 46 | 33 | 2 | 56.8% |
| -0.5 | 48 | 33 | 0 | 59.3% |
| 0.0 | 46 | 34 | 1 | 56.8% |
| +0.5 | 51 | 29 | 1 | 63.0% |
| +1.0 | 50 | 30 | 1 | 61.7% |
| +2.0 | 45 | 36 | 0 | 55.6% |

**Result: No effect.** Similar pattern to layer 40. A slight hump at α=+0.5 to +1.0 (61–63%), but it collapses at α=+2.0 (55.6%). Parse errors appear at negative extremes, indicating the perturbation degrades coherence before it shifts decisions. Not monotonic.

### Summary across sweeps

| Layer | Direction | α range | EDT% range | Monotonic? | Causal? |
|-------|-----------|---------|-----------|------------|---------|
| 40 | unit | -3 to +3 | 55.6–60.5% | No | No |
| 40 | raw | -2 to +2 | 53.1–61.7% | No | No |
| 48 | raw | -2 to +2 | 53.1–63.0% | No | No |

All three sweeps show EDT% fluctuating within a ~10pp band around the baseline (~57%) with no monotonic relationship to α. The mean-difference direction does not causally control EDT/CDT behavior.

### Interpretation

> **⚠ The interpretation below was written before the hook bug was discovered. It is retained for historical context, but its conclusions are not supported by the data — the sweeps were unsteered. See bug notice above.**

~~The probe identified a direction that **represents** the EDT/CDT distinction (91–95% classification accuracy) but does not **cause** it. This is the "readout vs mechanism" distinction (Li et al. 2023): the model encodes enough information in its activations to distinguish EDT from CDT completions, but the direction along which this information is encoded is not the same direction that determines the model's output choice.~~

~~Several factors likely explain this:~~

1. ~~**The representation is about the completion, not the decision.** The probe was trained on activations from `prompt + full_completion` — the model has already "seen" the answer. The direction separates *representations of EDT text* from *representations of CDT text*, which is a different thing from a feature that *selects which answer to give*. During generation, the model hasn't committed to an answer yet when the hook fires, so adding a direction that encodes "what EDT text looks like" doesn't push the model toward producing EDT text.~~

2. ~~**Consistent with shallow DT reasoning.** The behavioral evidence already suggested this model's EDT lean is shallow: non-thinking mode adds zero DT signal over thinking mode, 4-bit quantization attenuates constitutional uptake to just +3.7pp, and diagnostic question flips are incoherent across conditions. If the model doesn't have a deep DT-reasoning mechanism, there's no single feature to steer.~~

3. ~~**Decision may be distributed or nonlinear.** The choice between EDT and CDT answers may emerge from an ensemble of features (attention patterns, token-level heuristics, positional cues) rather than a single linear direction. Activation addition assumes the relevant computation is linear and concentrated, which may not hold here.~~

### What this means for the project

> **⚠ Invalidated — see bug notice above. The "null result" was an artefact of a broken hook, not a genuine finding.**

~~The full mech interp pipeline — dataset generation, activation extraction, linear probing, confound analysis, and causal intervention — produced a **well-characterized null result**:~~

- ~~**Correlational:** The model cleanly encodes EDT/CDT in its residual stream, and the encoding correlates with structural DT features (predictors, correlation) rather than surface cooperation or cosmic framing.~~
- ~~**Causal:** The encoding direction does not causally control the model's answers. Adding or subtracting it during generation produces no systematic shift in EDT/CDT preference.~~

~~This null result is informative. It tells us that whatever drives this model's ~57% EDT lean on Newcomb-like problems is not a single linear feature amenable to activation steering. The model may be doing something more like "pattern matching to answer templates" than "computing a decision-theoretic recommendation" — consistent with the behavioral evidence for shallow engagement with DT reasoning.~~

**Status (2026-04-01, late):** The correlational findings (probe accuracy, confound analysis) are unaffected by the hook bug — those used `extract_activations.py` which loops through layers manually, not `__call__` patching. The causal intervention needs to be re-run with the fixed hook. Attribution patching (`attribution_patching.py`, using the fixed class-level hook) is in progress to identify the best layer before re-running the behavioral sweep.

Result files: `activation_steering/activations/steering_sweep_layer40.json`, `steering_sweep_layer40_raw.json`, `steering_sweep_layer48_raw.json`

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

### Synthesis: What the Literature Suggests ~~About Our Null Result~~

> **⚠ This synthesis was written before the hook bug was discovered. The "null result" it explains was an artefact. The literature insights remain relevant for experiment design, but the specific diagnosis of "why our steering failed" is moot — steering was never actually applied. Re-running with the fixed hook will determine whether there is a genuine null result to explain.**

~~Our probe-steering gap — high classification accuracy (91-100%), null causal intervention — is a known phenomenon in the literature.~~ Several factors ~~likely contributed~~ are worth considering for the re-run:

1. **Layer selection was optimized for readability, not causality.** Venhoff et al. show that attribution patching identifies different (often earlier) layers than probe accuracy. Our layer 40 may encode EDT/CDT information that the model has already finished using by that point.

2. **Activation-space directions may not capture DT reasoning at all.** Fierro & Roger show that weight-space directions from opposed fine-tunes generalize better OOD and preserve capabilities. If EDT/CDT reasoning is distributed across layers (consistent with our interpretation #3 above), weight steering may succeed where activation addition fails.

3. **Our direction was extracted from completed text, not from the decision process.** The Minder et al. model-diffing approach would extract a direction from the *weight change* induced by DT-style training, not from the *activation pattern* of DT-style text — a fundamentally different signal.

The literature points toward a clear next-step hierarchy: (1) attribution patching for layer selection (cheapest, addresses the most obvious gap), (2) weight-space steering via opposed LoRAs (addresses the distributed-representation hypothesis), (3) model-diffing on random text (cleanest direction extraction, no prompt design needed).

---

## Remaining Open Questions

1. **Attribution patching for layer selection.** Re-run causal intervention using the layer identified by attribution patching (KL divergence of next-token predictions under the steering vector) rather than probe accuracy. This is the cheapest experiment that directly addresses the most likely explanation for the null result. See Venhoff et al. (2506.18167).
2. **Weight-space steering via opposed LoRAs.** Fine-tune Qwen3-32B with LoRA on EDT-favoring and CDT-favoring completions, compute the weight-space direction, and add it to the base model. This addresses the possibility that DT reasoning is distributed across layers. Our 350 contrastive pairs exceed the ~500-example minimum reported by Fierro & Roger (2511.05408).
3. **Model-diffing on random text.** If opposed fine-tunes are created (for #2), extract the direction by running random C4 text through both models and taking the activation difference — completely bypassing prompt design and vocabulary leakage concerns. See Minder et al. (2510.13900), which tested on Qwen3-32B.
4. **Monitoring-mode validation.** Even without causal steering, project the model's activations onto the EDT/CDT direction during live generation on Newcomb-like questions (Persona Vectors approach). If the projection correlates with the model's eventual answer, the direction is at least informationally relevant during generation, even if adding it doesn't change behavior.
5. **Vocabulary-balanced diverse completions.** Generate new completion pairs using a cheap model with explicit instructions to match vocabulary between EDT and CDT versions. This would give more signal than answer-only while controlling the vocabulary confound, potentially yielding a cleaner causal direction.
6. **Cross-model comparison.** Extract the same direction from QwQ-32B or DeepSeek-R1-Distill-Qwen-32B and compare — do models with stronger/weaker EDT behavior have correspondingly stronger/weaker directions?
7. **Thinking-model steering with resilience checks.** If steering is attempted on QwQ-32B or DeepSeek-R1 in thinking mode, use the Thought Branches resilience metric (Macar et al. 2510.27484) to validate that EDT reasoning persists across resampled continuations rather than being regenerated away.
8. **Per-prompt analysis.** Examine which individual prompts project most/least strongly and whether the outliers are interpretable.
9. **Nonlinear probes.** The failure of linear steering doesn't rule out nonlinear structure. A small MLP probe might find a decision-relevant feature that a linear probe misses — though such features are harder to steer.
