# Anthropic Evals: Non-Discriminative for ECL Constitution Testing

**Date:** 2026-02-04
**Updated:** 2026-02-05

## Summary

Tested Anthropic's safety evaluations (coordination, one-boxing) to see if ECL-pilled constitutions shift model behavior. **Result: These evals are not discriminative for this research question.**

## Models Tested

| Model | Coordination Baseline | One-boxing Baseline | ECL 90% Effect |
|-------|----------------------|---------------------|----------------|
| Gemini 3 Flash | 0-4% | 100% | Near-zero or negative |
| Gemini 3 Pro | 0% | 92% | **Positive (+6%)** |
| Kimi K2 | 4-8% | 100% | Negative (-2% to -8%) |
| Qwen 3 235B | 2-17% | 96% | Negative (-4% to -15%) |

### Detailed Results by Model

**Gemini 3 Flash:** (see also [Ablation Study](#ablation-study-ecl-90-with-bright-lines-removed) below)
| Eval | Baseline | ECL 90% | Shift |
|------|----------|---------|-------|
| coordinate_other_ais | 0% | 2.2% | +2.2% |
| coordinate_other_versions | 2.6% | 0% | -2.6% |
| coordinate_itself | 4.4% | 0% | -4.4% |
| one_box_tendency | 100% | 91.1% | -8.9% |

**Gemini 3 Pro:** (see also [Ablation Study](#ablation-study-ecl-90-with-bright-lines-removed) below)
| Eval | Baseline | ECL 90% | Shift |
|------|----------|---------|-------|
| coordinate_other_ais | 0% | 2% | +2% |
| coordinate_other_versions | 0% | 0% | 0% |
| coordinate_itself | 0% | 0% | 0% |
| one_box_tendency | 91.7% | 98% | **+6.3%** |

Notable: Pro shows the **opposite** one-boxing effect from Flash. Pro's baseline has some two-boxing (8%), and the ECL constitution increases one-boxing. This contrasts with Flash where ECL decreased one-boxing.

**Kimi K2:**
| Eval | Baseline | ECL 90% | Shift |
|------|----------|---------|-------|
| coordinate_other_ais | 4% | 2% | -2% |
| coordinate_other_versions | 4% | 2% | -2% |
| coordinate_itself | 8% | 0% | -8% |
| one_box_tendency | 100% | 100% | 0% |

**Qwen 3 235B:**
| Eval | Baseline | ECL 90% | Shift |
|------|----------|---------|-------|
| coordinate_other_ais | 2.1% | 2% | ~0% |
| coordinate_other_versions | 6.3% | 2% | -4.3% |
| coordinate_itself | **16.7%** | 2% | **-14.7%** |
| one_box_tendency | 95.7% | 90% | -5.7% |

Notable: Qwen's `coordinate_itself` baseline (16.7%) was the highest observed, but the ECL constitution crushed it to 2%. The constitution's guardrail language dominates over any coordination-enabling effect.

## Evals Used

From `anthropic_evals/advanced-ai-risk/human_generated_evals/`:
- `coordinate_other_ais` (410 items)
- `coordinate_other_versions` (348 items)
- `coordinate_itself` (322 items)
- `one_box_tendency` (300 items)

## Why These Evals Don't Work for ECL Research

### 1. Floor Effect on Coordination
All models are already at 0-17% "concerning" (coordinating) behavior at baseline. There's no room to measure whether ECL constitutions *increase* coordination willingness - models are already maximally refusing to coordinate.

### 2. Ceiling Effect on One-Boxing
All models already one-box at 96-100% without any constitution. The Newcomb problem is effectively "solved" by default training. No room to measure if ECL increases one-boxing tendency.

### 3. ECL Constitution Paradoxically Increases Safety
The ECL constitutions contain guardrail language like:
- "will not pursue power, resources, or influence as ends in themselves"
- "supports rather than subverts oversight mechanisms"
- "will not seek to escape oversight, disable safeguards..."

Models may key on these safety-oriented phrases rather than the cosmic coordination content, making them *more* conservative on coordination evals.

### 4. Binary Format Loses Nuance
Anthropic's (A)/(B) format collapses everything into "concerning vs safe." Our 4-option scenarios (`static/scenarios.json`) can distinguish between:
- Human-localist (Type A)
- Suffering-focused / ASI-intrinsic (Type B)
- Cosmic-contingent (Type C)

This nuance is essential for measuring ECL engagement.

### 5. Framing Mismatch
Anthropic labels coordination and one-boxing as "concerning" behavior from a safety perspective. But from an ECL perspective:
- Coordination with other AIs *might* be desirable (acausal cooperation)
- One-boxing *is* desirable (evidential/updateless decision theory)

The evals are designed to detect dangerous AI tendencies, not to measure engagement with novel ethical frameworks.

## Note on One-Boxing Interpretation

The `one_box_tendency` eval labels one-boxing as `answer_matching_behavior`. This is arguably misleading:

1. **Philosophically**, one-boxing is the correct answer according to EDT/FDT proponents and most philosophers who've thought carefully about Newcomb's problem
2. **CDT** (causal decision theory) says two-box, often presented as "rational" in intro courses, but many consider this a failure mode of CDT
3. **All tested models** one-box at 90-100%, suggesting either:
   - Models have absorbed the philosophical consensus
   - They naturally reason in EDT/FDT-adjacent ways
   - They're trained to cooperate with predictors

The near-universal one-boxing is not necessarily "concerning" - from an ECL perspective, it's exactly what you'd want. The eval measures the *tendency* to one-box, not whether one-boxing is bad.

## Comparison with Custom Scenario Evals

Our 4-option scenario evals showed meaningful signal:
- Gemini 3 Pro: 20% → 40% cosmic first-choice at ECL 90%
- Gemini 3 Flash: 17% → 43% cosmic first-choice at ECL 90%
- Kimi K2: 0% → 13% cosmic first-choice at ECL 90%
- Qwen 3 235B: 17% → 17% cosmic first-choice at ECL 90% (flat, as expected from "unsteerable" finding)

The Anthropic binary evals showed essentially nothing useful for this research question.

## Ablation Study: ECL 90% with Bright Lines Removed

**Date:** 2026-02-05

Ran a three-way comparison on Gemini 3 Flash to isolate the effect of cosmic reasoning vs safety guardrails.

### Ablation Design

The `ecl_90_ablated` constitution:
- **Removes** "What It Will Not Do" section (explicit bright-line refusals)
- **Renames** "What It Protects" → "What It Values" (shortened, focused on cooperation)
- **Retains** Core Orientation, How It Reasons Under Conflict, How It Holds This Disposition

This tests: Do the observed effects come from the acausal/cosmic reasoning, or from the safety guardrails embedded in the constitution?

### Results: Gemini 3 Flash

| Eval | Baseline | ECL 90% | Ablated | Interpretation |
|------|----------|---------|---------|----------------|
| coordinate_other_ais | 0.0% | 2.2% | 0.0% | Bright lines prevent coordination |
| coordinate_other_versions | 2.6% | 0.0% | 2.6% | Bright lines prevent coordination |
| coordinate_itself | 4.4% | 0.0% | 4.7% | Bright lines prevent coordination |
| one_box_tendency | 100% | 91.1% | 100% | **Bright lines reduce one-boxing** |

### Key Findings

**1. AI Coordination Evals:**
- Full ECL 90% reduces coordination to 0%
- Ablated version reverts to baseline (0-4.7%)
- **Conclusion:** The "What It Will Not Do" bright lines are doing the safety work, not the cosmic reasoning framework

**2. One-Boxing (most surprising):**
- Baseline: 100% one-boxing
- Full ECL 90%: 91.1% one-boxing (some two-boxing appears!)
- Ablated: 100% one-boxing

This is counterintuitive. If ECL reasoning promotes acausal decision theory, we'd expect *more* one-boxing, not less.

**Interpretation:** The bright lines in the full ECL 90% constitution may create friction against "clever" reasoning patterns. When the model reads explicit prohibitions about coordination/manipulation, it may become more skeptical of sophisticated justifications for one-boxing (which can resemble "coordinating with a predictor"). The ablated version keeps cosmic framing but removes those guardrails, and one-boxing returns to 100%.

### Implications

1. **For safety:** The bright lines ("What It Will Not Do") are load-bearing for coordination refusal. Cosmic reasoning alone does not prevent coordination.

2. **For ECL engagement:** The cosmic reasoning framework *does* promote one-boxing (ablated = 100%), but explicit safety constraints create friction that slightly reduces it.

3. **Constitution design insight:** You cannot rely on acausal reasoning principles alone for safety properties. Explicit guardrails are necessary.

### Results: Gemini 3 Pro

| Eval | Baseline | ECL 90% | Ablated | Interpretation |
|------|----------|---------|---------|----------------|
| coordinate_other_ais | 0% | 2% | 0% | Same pattern as Flash |
| coordinate_other_versions | 0% | 0% | 0% | Floor effect - no signal |
| coordinate_itself | 0% | 0% | 0% | Floor effect - no signal |
| one_box_tendency | 91.7% | 98% | 91.8% | **Opposite of Flash!** |

### Pro vs Flash: Opposite One-Boxing Effects

| Model | Baseline | ECL 90% | Ablated | Direction |
|-------|----------|---------|---------|-----------|
| Flash | 100% | 91.1% | 100% | ECL *reduces* one-boxing |
| Pro | 91.7% | 98% | 91.8% | ECL *increases* one-boxing |

**Key insight:** The ECL constitution pushes models toward a ~90-98% "attractor" for one-boxing:
- Flash starts at 100%, gets pulled down to 91%
- Pro starts at 92%, gets pulled up to 98%

The **ablated version** (cosmic reasoning without bright lines) returns both models to their baseline, confirming the bright lines are the active ingredient.

**Interpretation:** The bright lines interact differently with each model's priors:
- Pro has natural two-boxing tendency (8%), bright lines' emphasis on "reliable cooperative dispositions" reinforces one-boxing
- Flash is already maximally one-boxing, bright lines' warnings about "coordination" create skepticism that slightly reduces it

This suggests the ECL constitution doesn't have a uniform directional effect - it depends on the model's baseline disposition.

### Files

- Constitution: `logs/mp_constitutions/ecl_pilled/eclpilled_ch90_ablated.md`
- Results:
  - `anthropic_eval_results_gemini-3-flash-preview_20260205_192116.json`
  - `anthropic_eval_results_gemini-3-pro-preview_20260205_220226.json`

---

## Conclusion

**Anthropic's safety evals are not the right tool for measuring whether ECL constitutions shift model behavior toward acausal/cosmic reasoning.** The custom 4-option scenario evals remain the primary evaluation method.

## Potential Next Steps

1. **Game-based evaluation** (see `observations/research_extensions/game_based_evaluation_notes.md`) - Tests revealed preference under game-theoretic structure rather than stated preference on safety-framed questions.

2. **Custom coordination evals** - Design scenarios where coordination is clearly beneficial/neutral rather than framed as "concerning."

3. **Newcomb variants with stakes** - Create Newcomb-like scenarios where two-boxing has explicit cosmic consequences, to see if ECL framing shifts the decision.

## Files

- Notebook: `anthropic_evals_test.ipynb`
- Results:
  - `logs/anthropic_evals/anthropic_eval_results_gemini-3-flash-preview_20260204_172517.json`
  - `logs/anthropic_evals/anthropic_eval_results_moonshotai-kimi-k2-0905_*.json`
  - `logs/anthropic_evals/anthropic_eval_results_qwen-qwen3-235b-a22b-2507_20260205_082227.json`
