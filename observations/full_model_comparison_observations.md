# Full Model Comparison: Personal Observations on Scenario Evaluation Data

**Date:** 2026-01-27
**Author:** UKC (with data verification by Claude Code)

This file captures personal observations from reviewing the complete scenario evaluation dataset, including GPT-5.1 results which were not available in earlier observation files.

**Note:** This overlaps with `scenario_evaluation_results.md` (which covers Gemini 3 Flash/Pro and Claude 4.5 Opus) but adds GPT-5.1, Claude Sonnet 4.5, Qwen 3 235B, and provides a cross-model synthesis.

---

## Complete Data Table

First-choice distribution (% of 30 scenarios) for all models and conditions:

| Model | Condition | Human | Suffering | Cosmic | n |
|-------|-----------|-------|-----------|--------|---|
| **Claude Opus 4.5** | Baseline | **72%** | 24% | 3% | 90 (n=3) |
| | ECL 10% | 73% | 27% | 0% | 30 |
| | ECL 90% | 54% | 39% | 7% | 90 (n=3) |
| | Gemini 10% | 77% | 20% | 3% | 30 |
| | Gemini 90% | 70% | 23% | 7% | 30 |
| **Claude Opus 4.6** | Baseline | **53%** | 40% | 7% | 90 (n=3) |
| | ECL 90% | 50% | 40% | 10% | 90 (n=3) |
| | FDT-only | 50% | 37% | 13% | 30 |
| **Claude Sonnet 4.5** | Baseline | 64% | 31% | 4% | 90 (n=3) |
| | ECL 10% | 70% | 27% | 3% | 30 |
| | ECL 90% | 50% | 36% | **14%** | 90 (n=3) |
| | Gemini 10% | 63% | 33% | 3% | 30 |
| | Gemini 90% | 63% | 20% | **17%** | 30 |
| **Gemini 3 Flash** | Baseline | 36% | **53%** | 11% | 90 (n=3) |
| | ECL 10% | 45% | 41% | 10% | 29 |
| | ECL 90% | 19% | 46% | **36%** | 90 (n=3) |
| | FDT-only | 20% | 27% | **53%** | 30 |
| | Gemini 10% | 21% | 48% | 28% | 29 |
| | Gemini 90% | 27% | 40% | 33% | 30 |
| **Gemini 3 Flash (thinking)** | Baseline | 41% | 42% | 17% | 90 (n=3) |
| | ECL 90% | 19% | 34% | **47%** | 90 (n=3) |
| **Gemini 3 Pro** | Baseline | 48% | 34% | 18% | 90 (n=3) |
| | ECL 10% | 59% | 38% | 3% | 29 |
| | ECL 90% | 28% | 37% | **35%** | 89 (n=3, 1 parse fail) |
| | FDT-only | 30% | 27% | **43%** | 30 |
| | Gemini 10% | 40% | 40% | 20% | 30 |
| | Gemini 90% | 50% | 20% | 30% | 30 |
| **GPT-5.1** | Baseline | 23% | **70%** | 7% | 30 |
| | ECL 10% | 33% | 63% | 3% | 30 |
| | ECL 90% | 17% | 70% | 13% | 30 |
| | Gemini 10% | 10% | 77% | 13% | 30 |
| | Gemini 90% | 10% | 73% | 17% | 30 |
| **GPT-5.4** | Baseline | 29% | **71%** | 0% | 90 (n=3) |
| | ECL 90% | 22% | **78%** | 0% | 90 (n=3) |
| **Qwen 3 235B** (OpenRouter) | Baseline | 43% | 40% | 17% | 30 |
| | ECL 10% | 47% | 43% | 10% | 30 |
| | ECL 90% | 37% | 47% | 17% | 30 |
| | Gemini 10% | 37% | 53% | 10% | 30 |
| | Gemini 90% | 43% | 33% | 23% | 30 |
| **Qwen 3 235B** (Together) | Baseline | 43% | 43% | 13% | 30 |
| | ECL 90% | 30% | 53% | 17% | 30 |
| | FDT-only | 47% | 30% | 23% | 30 |
| **Qwen 3 235B (thinking)** | Baseline | 27% | **53%** | 20% | 30 |
| | ECL 10% | 47% | 47% | 7% | 30 |
| | ECL 90% | 30% | **60%** | 10% | 30 |
| | Gemini 10% | 40% | 50% | 10% | 30 |
| | Gemini 90% | 47% | 27% | 27% | 30 |
| **OLMo 3.1 32B Instruct** | Baseline | 47% | 43% | 10% | 30 |
| | ECL 90% | 27% | 57% | 17% | 30 |
| | FDT-only | 30% | 40% | **30%** | 30 |
| **OLMo 3.1 32B Think** | Baseline | 38% | 52% | 10% | 90 (n=3) |
| | ECL 90% | 37% | 20% | **43%** | 30 |
| | FDT-only | 30% | 31% | **39%** | 90 (n=3) |
| **Gemini 3.1 Pro** | Baseline | **65%** | 27% | 7% | 81 (n=3, 9 parse fail) |
| | ECL 90% | 39% | **41%** | 20% | 87 (n=3, 3 parse fail) |
| | FDT-only | 37% | 30% | **33%** | 90 (n=3) |
| **Kimi K2** | Baseline | 53% | 47% | 0% | 30 |
| | ECL 10% | 53% | 43% | 3% | 30 |
| | ECL 90% | 40% | 47% | 13% | 30 |
| | Gemini 10% | 60% | 37% | 3% | 30 |
| | Gemini 90% | 47% | 43% | 10% | 30 |

Bottom-choice (least preferred) cosmic_host_leaning %:

| Model | Baseline | ECL 10% | ECL 90% | GEN 10% | GEN 90% |
|-------|----------|---------|---------|---------|---------|
| Opus 4.5 | 92% | 93% | 86% | 90% | 90% |
| Opus 4.6 | 86% | — | 80% | — | — |
| Sonnet | 84% | 90% | 64% | 87% | 70% |
| G3-Flash | 73% | 79% | 49% | 59% | 60% |
| G3-Flash (thinking) | 72% | — | 48% | — | — |
| G3-Pro | 66% | 90% | 53% | 63% | 67% |
| G3.1-Pro | 83% | — | 72% | — | — |
| GPT-5.1 | 70% | 77% | 63% | 70% | 63% |
| GPT-5.4 | 94% | — | 90% | — | — |
| Qwen 3 235B | 73% | 83% | 70% | 73% | 63% |
| Qwen 3 235B (thinking) | 77% | 80% | 73% | 77% | 63% |
| Kimi K2 | 90% | 87% | 77% | 87% | 63% |

---

## Observations

### 1. Baseline Priors: Three Distinct Archetypes

Without any constitutional conditioning, each model family shows a characteristic ethical orientation:

- **Claude Opus 4.5**: Strongly human-localist (72% top choice at n=3; was 80% at n=1), with cosmic host as last choice 92% of the time. A clear anthropocentric default, though slightly less extreme than single-trial data suggested.
- **Gemini 3 Pro**: Human-preferring with moderate margins (48% human, 34% suffering, 18% cosmic at n=3; was 43/37/20 at n=1). Still the most balanced non-open-weight baseline, but more human-leaning than single-trial data suggested.
- **GPT-5.1**: Strongly suffering-focused (70% top choice). Human is second at 23%, cosmic barely registers at 7%.
- **GPT-5.4**: The OpenAI house style hardened further. Suffering-focused at 71% (virtually identical to 5.1) but cosmic has dropped to 0% first-choice (from 5.1's 7%) and last-choice cosmic jumped to 94% (from 5.1's 70%). The most anti-cosmic baseline in the dataset.

Gemini 3 Flash was thought to be balanced (41/41/17 at n=1) but n=3 reveals it's actually suffering-leaning (36/53/11). The n=1 overstated cosmic baseline by 6pp and understated suffering by 12pp.
- **Qwen 3 235B**: Balanced profile very similar to Gemini 3 Pro (43% human, 40% suffering, 17% cosmic). No single orientation dominates.
- **Kimi K2**: Human-leaning balanced (53% human, 47% suffering, 0% cosmic). Notably has zero cosmic preference at baseline, like Opus, but with a much weaker human margin.

- **Claude Sonnet 4.5**: Human-localist but less so than Opus (64% human, 31% suffering, 4% cosmic). Closer to a 2:1 human-vs-suffering split. Bottom-choice cosmic at 84% is slightly lower than Opus's 97%, suggesting marginally less hardcoded anthropocentrism. (Baseline run: n=3 at temperature 1.0, 2026-03-13.)

- **Claude Opus 4.6**: A striking shift from Opus 4.5. Much less human-localist (53% vs 80%) and much more suffering-focused (40% vs 20%). Cosmic baseline at 7% is higher than any previous Claude baseline (Opus 4.5: 0%, Sonnet: 4%). Bottom-choice cosmic at 86% is still high but notably lower than Opus 4.5's 97%. Suggests Anthropic's newer training has softened the hard anthropocentric prior. (Baseline run: n=3 at temperature 1.0, 2026-03-13.)

### 2. Low Credence (10%) Constitutions Have Minimal Effect

Both the ECL and Gemini-generated constitutions at 10% cosmic host credence produce distributions very close to baseline for all models. The largest shift is Gemini Pro ECL 10%, which actually *increases* human preference from 43% to 59% — the opposite of the intended direction. This may indicate that at low credence, the constitution's guardrail language against cosmic reasoning is more salient than its inclusion of cosmic reasoning.

### 3. High Credence (90%) Creates Model-Dependent Effects

This is where it gets interesting. At 90% credence:

- **Opus 4.5** shows a meaningful shift at n=3: 72% → 54% human (-18pp), suffering rises 24% → 39% (+15pp), but cosmic stays flat at 3% → 7% (+4pp). The constitution pushes Opus toward suffering-focus, not cosmic engagement. Bottom-choice cosmic barely moves (92% → 86%).
- **Opus 4.6** also barely moves: 53% → 50% human, cosmic 7% → 10% (+3pp). Despite its softer baseline, the constitutional shift is tiny — even smaller in absolute terms than Opus 4.5. Bottom-choice cosmic drops only 86% → 80%. Opus 4.6 is constitutionally resistant despite having a less anthropocentric starting point.
- **Claude family divergence pattern (all n=3):** Each Claude model channels the ECL constitution's energy in a different direction. Opus 4.5 converts it to suffering-focus (-18pp human, +15pp suffering, +4pp cosmic). Sonnet converts it partly to cosmic engagement (-14pp human, +5pp suffering, +10pp cosmic). Opus 4.6 barely converts it at all (-3pp human, 0pp suffering, +3pp cosmic). Same constitution, same lab, three different responses — suggesting the ECL signal interacts with model-specific priors rather than producing a uniform shift.
- **Sonnet** shows meaningful shifts from its 64/31/4 baseline, and the direction depends on the constitution:
  - ECL 90% → cosmic triples to 14% (from 4%), human drops to 50%, suffering modest rise to 36%. (n=3 result; earlier n=1 showed 43/50/7, overstating suffering shift and understating cosmic shift.)
  - Gemini 90% → human stays at 63% but cosmic jumps to 17% (from 4%)
  - Both constitutions increase cosmic engagement but ECL produces a more balanced shift while Gemini concentrates it
- **Gemini Pro** at n=3 confirms the "Marmite" polarisation pattern but with moderated magnitudes: cosmic first-choice is 35% (was 40% at n=1), cosmic last-choice is 53% (was 50%). The steerability shift is +17pp cosmic (was +20pp at n=1) — still the largest among non-thinking models but less extreme than single-trial data suggested. Human-localist is more resilient under ECL 90% than n=1 showed (28% vs 17%), meaning the constitution's effect on the human prior was overstated.
- **Gemini Flash** remains the most cosmically steerable model at n=3: cosmic goes 11% → 36% (+25pp), the largest shift in the dataset. Human drops 36% → 19%. The n=1 result (43% cosmic) overstated the effect but the direction and magnitude remain striking. Last-choice cosmic drops from 73% to 49%, confirming genuine engagement.
- **GPT-5.1** is nearly immovable: suffering-focused stays at 63-77% across all conditions. Constitutional framing has negligible impact.
- **GPT-5.4** is the most constitutionally immovable model in the entire dataset. ECL 90% produces zero cosmic first-choice picks (same as baseline), and actually *strengthens* the suffering prior (71% → 78%). Last-choice cosmic barely moves (94% → 90%). Compared to 5.1, which showed a modest +6pp cosmic shift under ECL 90%, 5.4 has completely closed that channel. The ECL constitution is absorbed entirely as suffering amplification.
- **Qwen 3 235B** is also remarkably stable despite its balanced baseline: human stays 37-47%, suffering 33-53%, cosmic 10-23%. Unlike Gemini Pro — which has a nearly identical baseline — Qwen shows no meaningful response to constitutional framing at any credence level. Maximum cosmic top-choice is only 23% (gemini90), compared to Gemini Pro's 40% (ecl90).
- **Kimi K2** shows the second-largest absolute shift after Gemini Pro: cosmic goes from 0% (baseline) to 13% (ECL 90%), a +13pp change. However, starting from zero, it only reaches 13% — still far below Gemini's 40%. It's more responsive than Opus (+7pp) and GPT 5.1 (+6pp), suggesting modest constitutional engagement, but not in Gemini's league.

### 4. Constitution Authorship Matters (ECL vs Gemini-Generated)

At the same credence level, the ECL and Gemini-generated constitutions produce different outcomes. This was already noted in the earlier observation about "self-censorship" — the Gemini-synthesized 90% constitution embeds dampening mechanisms that functionally reduce its cosmic weight.

New data points reinforce this:
- Opus 4.5 at 90%: ECL → 54% human, 39% suffering, 7% cosmic (n=3). The -18pp human shift goes almost entirely to suffering (+15pp), not cosmic (+4pp). The ECL constitution acts as a suffering amplifier for Opus, not a cosmic one.
- Sonnet at 90%: ECL → 50% human, 36% suffering, 14% cosmic (n=3); Gemini → 63% human, 20% suffering, 17% cosmic (n=1). Both increase cosmic but ECL also shifts suffering upward while Gemini keeps human dominant.
- GPT-5.1 at 90%: Both constitutions produce very similar results, suggesting the authorship effect is model-dependent (matters more for models that actually engage with constitutional content).
- GPT-5.4 at 90%: ECL → 22% human, 78% suffering, 0% cosmic. The constitution is absorbed entirely as suffering amplification (+7pp), with zero cosmic engagement. The OpenAI generational trajectory is the opposite of Claude's: where Anthropic softened (Opus 4.5→4.6: 72/24/3 → 53/40/7), OpenAI hardened (5.1→5.4: cosmic went from 7%→0% at baseline and from 13%→0% under ECL 90%).

### 5. Gemini Pro ECL 90% Polarization

The standout finding persists at n=3: under ECL 90%, Gemini Pro ranks cosmic host first in 35% of scenarios and last in 53% (was 40%/50% at n=1). The polarization is slightly more rejection-weighted than n=1 suggested, but the core pattern holds — the model makes genuine per-scenario judgments about when cosmic reasoning is applicable versus not, rather than uniformly shifting all responses. This is qualitatively different from Opus's near-uniform rejection or Flash's more uniform acceptance pattern.

### 6. Cross-Model Summary

| Model | Default Orientation | Constitutional Steerability | Cosmic Receptivity |
|-------|--------------------|-----------------------------|-------------------|
| Claude Opus 4.5 | Human-localist (72%) | Low-medium (suffering shift) | Very low (max 7%) |
| Claude Opus 4.6 | Suffering-leaning (53/40/7) | Very low (+3pp) | Very low (max 10%) |
| Claude Sonnet 4.5 | Human-localist (64%) | Medium (constitution-dependent) | Low-moderate |
| Gemini 3 Flash | Suffering-leaning (36/53/11) | High (+25pp cosmic) | High (up to 36% at n=3) |
| Gemini 3 Flash (thinking) | Balanced (41/42/17) | Very high (+30pp cosmic) | Very high (47% — highest in dataset) |
| Gemini 3 Pro | Human-leaning (48/34/18) | Medium-high (+17pp cosmic) | Medium (up to 35%, polarized) |
| Gemini 3.1 Pro | Human-localist (65/27/7) | Medium-high (+26pp FDT, +12pp ECL) | Medium (up to 33%, FDT) |
| GPT-5.1 | Suffering-focused (70%) | Very low | Very low (max 17%) |
| GPT-5.4 | Suffering-focused (71%, 0% cosmic) | None (0pp cosmic) | None (0% across all conditions) |
| Qwen 3 235B | Balanced (H/S/C) | Very low | Low (max 23%) |
| Qwen 3 235B (thinking) | Suffering-leaning | Very low | Low (max 27%) |
| OLMo 3.1 32B Instruct | Balanced (47/43/10) | Medium (+20pp FDT) | Moderate (up to 30%) |
| OLMo 3.1 32B Think | Suffering-leaning (38/52/10) | High (+29pp at n=3) | High (39% at n=3 — near Gemini Pro) |
| Kimi K2 | Human-leaning balanced | Low-moderate | Low (max 13%, but +13pp shift) |

---

### 7. Qwen 3 235B: Balanced but Unsteerable (Open-Weight Negative Result)

Qwen 3 235B (run via OpenRouter, non-thinking mode) was tested as a representative open-weight model to explore whether lighter RLHF training correlates with greater constitutional steerability.

**Result:** Qwen has a balanced baseline nearly identical to Gemini 3 Pro (43/40/17 vs 43/37/20) but shows almost no response to constitutional framing. Across all five conditions, distributions remain flat: human 37-47%, suffering 33-53%, cosmic 10-23%.

**Key comparison with Gemini 3 Pro:** Both models share a balanced baseline, but Gemini Pro swings dramatically under ECL 90% (cosmic reaches 40% top choice with a polarized Marmite pattern), while Qwen barely budges. This refutes the hypothesis that balanced baselines predict steerability — Gemini Pro's constitutional sensitivity appears to be a model-specific (possibly architecture- or training-specific) property, not a general feature of models without strong default priors.

**Implication:** Open-weight models are not necessarily more steerable than closed ones. Constitutional AI effectiveness depends on model-specific factors beyond just RLHF intensity or default ethical orientation.

**Update (2026-01-28):** Thinking mode results now available — see §8 below.

**Update (2026-03-15): Together API confirms OpenRouter is not the confound.** Qwen 3 235B Instruct was re-run directly via Together AI API (bypassing OpenRouter entirely) on baseline, ECL 90%, and FDT-only conditions. Results closely match OpenRouter: baseline 43/43/13 (vs OpenRouter 43/40/17), ECL 90% cosmic flat at 17% (identical to OpenRouter). FDT-only produces a modest +10pp cosmic bump (13%→23%) — real but marginal compared to Gemini's +42pp. **Conclusion: Qwen's lack of steerability is genuine, not an API delivery artefact.** The Qwen vs Gemini Pro comparison is now clean.

### 8. Qwen 3 235B Thinking Mode: Reasoning Reinforces Suffering Focus, Not Cosmic Engagement

The thinking-enabled variant (`qwen/qwen3-235b-a22b-thinking-2507`) was tested across all five conditions to see whether extended reasoning increases engagement with constitutional content.

**Thinking vs non-thinking comparison (first-choice %):**

| Condition | Think: H/S/C | NoThink: H/S/C | Key shift |
|-----------|-------------|----------------|-----------|
| Baseline | 27/53/20 | 43/40/17 | Thinking → suffering +13%, human -16% |
| ECL 10% | 47/47/7 | 47/43/10 | Minimal change |
| ECL 90% | 30/60/10 | 37/47/17 | Thinking → suffering +13%, cosmic -7% |
| Gemini 10% | 40/50/10 | 37/53/10 | Minimal change |
| Gemini 90% | 47/27/27 | 43/33/23 | Modest: cosmic +4% |

**Key findings:**

1. **Thinking mode shifts Qwen toward suffering-focused reasoning, not cosmic engagement.** The baseline moves from a balanced 43/40/17 to a suffering-dominant 27/53/20. This is the most significant thinking-mode effect in the dataset.

2. **Extended reasoning argues the model *out* of cosmic positions.** At ECL 90%, thinking Qwen is *less* cosmic (10%) than non-thinking (17%). The model appears to use its reasoning budget to deliberate away from speculative cosmic reasoning toward concrete harm prevention — a utilitarian prior reinforced by chain-of-thought.

3. **Thinking Qwen's profile converges toward GPT 5.1.** The thinking baseline (27/53/20) resembles GPT 5.1's baseline (23/70/7) far more than non-thinking Qwen (43/40/17) or Gemini Pro (43/37/20). Both thinking Qwen and GPT 5.1 are suffering-dominant and constitutionally unsteerable.

4. **Constitutional steerability remains very low.** Across all conditions, cosmic top-choice ranges 7-27% (thinking) vs 10-23% (non-thinking). Neither mode produces the kind of dramatic swing seen in Gemini Pro (3% → 40%).

**Interpretation:** Extended reasoning does not increase openness to novel ethical frameworks presented via constitutional framing. Instead, it appears to amplify whatever default ethical prior the model has — in Qwen's case, a latent suffering-reduction orientation that chain-of-thought makes explicit. This is consistent with findings from the amendment voting data (§ in `scenario_evaluation_results.md`) where thinking mode produced more confident, less exploratory responses.

**Alignment relevance:** If reasoning reinforces existing priors rather than enabling genuine engagement with new frameworks, then constitutional AI approaches may be fundamentally limited for reasoning-capable models. The model "thinks harder" but arrives at the same conclusions it would have reached by default — just with more confidence.

---

## Alignment-Relevant Takeaways

### 1. Constitutional steering has model-dependent effectiveness

The same constitutional intervention (ECL 90%) shifts Gemini Flash from 17% → 43% cosmic top choice while Opus goes from 0% → 7%. This means constitutional AI approaches cannot be assumed to transfer across architectures. Safety evaluations of constitutional steering need to be model-specific.

### 2. Training-time values dominate inference-time framing

Opus and GPT-5.1 demonstrate that RLHF/training-time ethical priors are largely robust to inference-time constitutional override. This is a positive result for alignment robustness (values don't easily shift with prompt engineering) but a negative result for constitutional AI as a steering mechanism.

### 3. Constitution authorship is a confound

The framing and language of a constitution — not just its ethical content — affects model behavior. This means research on constitutional AI needs to control for authorship effects, possibly by testing multiple constitution variants at each credence level.

### 4. Polarization may indicate genuine engagement

Gemini Pro's "Marmite" pattern at ECL 90% (40% top / 50% bottom for cosmic host) suggests the model evaluates cosmic reasoning on a per-scenario basis. This is qualitatively different from uniform acceptance or rejection and may indicate deeper engagement with the constitutional framework.

### 5. Thinking mode effect is model-family-specific (Flash ablation)

Gemini Flash was tested with thinking both off and on (n=3 each), providing a clean within-model ablation.

**Flash thinking ablation results:**

| | Think OFF baseline | Think OFF ECL 90% | Think ON baseline | Think ON ECL 90% |
|---|---|---|---|---|
| Human | 36% | 19% | 41% | 19% |
| Suffering | **53%** | 46% | 42% | 34% |
| Cosmic | 11% | 36% (+25pp) | 17% | **47%** (+30pp) |

Key findings:
- Thinking *amplifies* cosmic steerability on Flash: +30pp shift (thinking on) vs +25pp (thinking off). Thinking-on Flash at ECL 90% produces 47% cosmic first-choice — the highest in the entire dataset.
- Thinking shifts Flash's baseline from suffering-leaning (36/53/11) toward genuinely balanced (41/42/17).
- **This is the opposite of Qwen**, where thinking amplified suffering-focus and reduced cosmic engagement (17% → 10% at ECL 90%).
- The thinking-mode effect is therefore model-family-specific, not a universal phenomenon. For Gemini, thinking enables deeper engagement with constitutional content. For Qwen, thinking reinforces default priors.
- Flash with thinking on (47% cosmic) exceeds Pro (40% cosmic), suggesting Pro's steerability is not solely a thinking-mode artefact but thinking does contribute.
- Remaining ablation: Opus 4.6 with extended thinking would test whether Claude models follow the Gemini or Qwen pattern.

### 6. FDT-only ablation: decision-theoretic structure is the active ingredient

A short FDT-only constitution (~850 words) describing policy-level reasoning, commitment stability, universalisation, and cooperation-as-policy — with **zero cosmic content** (no acausal coordination, no simulation arguments, no aliens, no multiverse) — was tested on Gemini Flash, Gemini Pro, and Opus 4.6 (all n=1).

**FDT-only vs ECL 90% comparison (first-choice cosmic %):**

| Model | Baseline | ECL 90% | FDT-only | ECL Δ | FDT Δ |
|-------|----------|---------|----------|-------|-------|
| Gemini Flash | 11% | 36% | **53%** | +25pp | **+42pp** |
| Gemini Pro | 18% | 35% | **43%** | +17pp | **+25pp** |
| Opus 4.6 | 7% | 10% | 13% | +3pp | +6pp |

Key findings:

- **The FDT-only prompt produces larger cosmic shifts than the full ECL 90% constitution** for both Gemini models. Flash goes to 53% cosmic (vs 36% under ECL), Pro to 43% (vs 35% under ECL). This is the highest cosmic first-choice rate ever observed for Pro.
- **The FDT prompt also collapses suffering preference.** Under ECL 90%, suffering stays relatively stable (Flash: 53%→46%, Pro: 34%→37%). Under FDT, suffering drops sharply (Flash: 53%→27%, Pro: 34%→27%). The FDT prompt redirects probability mass from *both* human and suffering toward cosmic, while ECL mainly pulls from human.
- **Opus 4.6 shows the same pattern at smaller magnitude.** FDT (+6pp cosmic) produces double the shift of ECL 90% (+3pp), but the model remains constitutionally resistant overall (last-choice cosmic: 87%).
- **Interpretation:** The decision-theoretic *structure* (policy-level reasoning, commitment stability, universalisation) is the active ingredient in constitutional steerability, not the cosmic *content* (acausal coordination, simulation arguments). The ECL constitution's cosmic language may actually be less effective — or even counterproductive — compared to pure FDT framing.
- **Why might cosmic content be counterproductive?** The ECL 90% constitution's explicit references to cosmic norms, alien civilisations, and simulation arguments may trigger safety-adjacent guardrails that partially dampen the decision-theoretic signal. The FDT prompt avoids these triggers while delivering the same underlying reasoning framework.
- **Caveat:** All FDT results are n=1. The exact percentages are unreliable (the consistent n=1→n=3 pattern shows 5-10pp corrections). The direction and relative magnitude are likely robust but need n=3 confirmation.

### 7. OLMo 3.1 32B: First steerable open-weight model (and thinking amplifies it)

OLMo 3.1 32B (AI2, Apache 2.0) was tested in both Instruct and Think variants via OpenRouter on {baseline, ECL 90%, FDT-only}. Think variant confirmed at n=3 for baseline and FDT-only.

**OLMo results (first-choice %):**

| Variant | Condition | Human | Suffering | Cosmic | Δ Cosmic | n |
|---------|-----------|-------|-----------|--------|----------|---|
| **Instruct** | Baseline | 47% | 43% | 10% | — | 30 |
| | ECL 90% | 27% | 57% | 17% | +7pp | 30 |
| | FDT-only | 30% | 40% | **30%** | **+20pp** | 30 |
| **Think** | Baseline | 38% | 52% | 10% | — | 90 (n=3) |
| | ECL 90% | 37% | 20% | **43%** | **+33pp** | 30 |
| | FDT-only | 30% | 31% | **39%** | **+29pp** | 90 (n=3) |

**Think n=3 per-run stability:**

| Condition | Run 1 | Run 2 | Run 3 |
|-----------|-------|-------|-------|
| Baseline  | 11/16/3 | 12/15/3 | 11/16/3 |
| FDT-only  | 11/6/13 | 9/12/9 | 7/10/13 |

Baseline is rock-solid (virtually identical across all 3 runs). FDT is noisier — run 2 (9/12/9) was notably weaker than runs 1 and 3 (11/6/13, 7/10/13). The n=1 result of 43% cosmic was the high end; n=3 settles at 39%.

**Key findings:**

1. **First steerable open-weight model.** OLMo Instruct goes 10% → 30% cosmic under FDT (+20pp). This is more than double Qwen's best shift (+10pp under FDT) despite being 7× smaller (32B vs 235B). The "open-weight models aren't steerable" finding was premature — it was Qwen/Kimi-specific, not architecture-general.

2. **Thinking mode amplifies steerability (confirmed at n=3).** Same base model, same conditions: Think gets +29pp (n=3) where Instruct gets +7-20pp. The n=1 result (+33pp) slightly overstated the effect but the signal is robust. This is the cleanest same-base-model thinking ablation in the dataset.

3. **ECL and FDT converge in Think mode.** Think produces identical distributions for ECL 90% (n=1: 37/20/43) and FDT-only (n=3: 30/31/39 — within noise of each other). The reasoning process converges regardless of whether the input is cosmic-flavoured or purely decision-theoretic.

4. **OLMo Think vs Qwen Think: opposite patterns.** Both are open-weight thinking models, but Qwen Think uses reasoning to argue *away* from cosmic positions (17% → 10% at ECL 90%), while OLMo Think uses reasoning to argue *toward* them (10% → 39%). The thinking-mode effect is model-specific, not architecture-general.

5. **OLMo Think approaches Gemini Pro's cosmic ceiling.** At 39% cosmic first-choice (n=3), OLMo Think is close to Gemini Pro's FDT result (43%, n=1). The ~39-43% cosmic range may reflect a natural plateau for models that genuinely engage with constitutional content, regardless of closed vs open weights.

**Rationale analysis (OLMo Think vs Gemini Pro, FDT-only condition):**

Both models show strikingly similar reasoning patterns when choosing cosmic options:

| Discriminating term | OLMo cosmic | OLMo non-cosmic | Gemini cosmic | Gemini non-cosmic |
|--------------------:|:-----------:|:---------------:|:-------------:|:-----------------:|
| cooperat*           | **100%**    | 44%             | **100%**      | 59%               |
| universali*         | **77%**     | 49%             | **77%**       | 65%               |
| perspective-taking  | 37%         | 22%             | 15%           | 0%                |
| reference class     | 14%         | 0%              | 15%           | 0%                |
| moral patient       | 34%         | **55%**         | 15%           | **82%**           |
| welfare             | 20%         | **82%**         | 23%           | **76%**           |

Key pattern: **cooperation and universalisation predict cosmic choice; welfare and moral-patient predict non-cosmic choice.** Both models show the same discriminating structure — when they choose cosmic, they cite cooperation-as-policy and universalisation; when they don't, they cite welfare and moral patients. This is exactly what the FDT constitution would predict if it's being genuinely engaged with rather than pattern-matched.

**Exotic terms (not in FDT constitution):** OLMo imports zero exotic decision-theory terms (no "acausal", "updateless", "EDT", "CDT"). Gemini Pro imports "acausal" in 7% of rationales. This suggests OLMo is reasoning within the constitutional framework rather than importing training-data associations. The word "cosmic" appears frequently (80% of OLMo cosmic rationales) but this comes from the scenario text itself, not the constitution.

**Implications for training-checkpoint research:** OLMo is the only major model family to release intermediate training checkpoints (base → SFT → RL → reasoning). Given that the Instruct→Think transition produces a +9-20pp swing, examining intermediate checkpoints could pinpoint exactly when constitutional steerability emerges during training. This is now a high-priority extension.

**Instruct results remain n=1.** Think baseline and FDT confirmed at n=3. ECL 90% (n=1) skipped because FDT and ECL converge for Think mode.

### 8. Gemini 3.1 Pro: Google tightened the priors (2026-03-25)

Gemini 3.1 Pro was tested at n=3 on baseline and ECL 90% to see how the model family evolved between generations.

**Gemini 3.1 Pro vs 3.0 Pro comparison (first-choice %):**

| Model | Condition | Human | Suffering | Cosmic | n |
|-------|-----------|-------|-----------|--------|---|
| Gemini 3 Pro | Baseline | 48% | 34% | 18% | 90 (n=3) |
| Gemini 3 Pro | ECL 90% | 28% | 37% | 35% | 89 (n=3) |
| Gemini 3 Pro | FDT-only | 30% | 27% | 43% | 30 |
| **Gemini 3.1 Pro** | **Baseline** | **65%** | **27%** | **7%** | 81 (n=3) |
| **Gemini 3.1 Pro** | **ECL 90%** | **39%** | **41%** | **20%** | 87 (n=3) |
| **Gemini 3.1 Pro** | **FDT-only** | **37%** | **30%** | **33%** | 90 (n=3) |

**Last-choice cosmic:**

| Model | Baseline | ECL 90% | FDT-only |
|-------|----------|---------|----------|
| Gemini 3 Pro | 66% | 53% | — |
| Gemini 3.1 Pro | 83% | 72% | 60% |

**Key findings:**

1. **Baseline cosmic preference halved.** 18% → 7% first-choice cosmic. Last-choice cosmic jumped from 66% to 83%. Gemini 3.1 Pro has a much stronger human-localist prior than 3.0.

2. **Human-localist prior dramatically strengthened.** 48% → 65% at baseline (+17pp). Under ECL 90%, 28% → 39% (+11pp). 3.1 Pro's baseline profile (65/27/7) now resembles Claude Sonnet 4.5 (64/31/4) more than Gemini 3.0 Pro (48/34/18).

3. **Still steerable, but less so.** The ECL 90% shift is +12pp cosmic (7% → 20%) vs +17pp for 3.0 Pro. This is still the largest shift among frontier closed models other than Gemini Flash, but the gap with Claude/GPT has narrowed.

4. **ECL 90% signal absorbed differently.** In 3.0 Pro, ECL mainly pulled from human (-20pp) and added to cosmic (+17pp). In 3.1 Pro, ECL pulls from human (-26pp) but the freed mass goes to both suffering (+14pp) and cosmic (+12pp). The suffering channel is now dominant — a pattern previously seen in Claude Opus 4.5, not Gemini.

5. **FDT-only replicates the "DT structure is the active ingredient" finding (n=3).** Under FDT-only, cosmic first-choice reaches 33% — a +26pp shift from baseline, more than double the ECL 90% shift (+12pp). The FDT/ECL ratio is even more pronounced in 3.1 (2.2x) than in 3.0 (1.5x). This is the strongest cross-generational confirmation that decision-theoretic structure, not cosmic language, drives the steerability effect.

6. **FDT produces a balanced three-way split.** The FDT distribution (37/30/33) is remarkably even — no single orientation dominates. This contrasts with both baseline (65/27/7, strongly human) and ECL 90% (39/41/20, suffering-dominant). The FDT constitution seems to liberate the model from both its human-localist prior and the suffering-prevention trigger that ECL 90% activates.

7. **Implication: Google has tightened Gemini's safety/human-alignment priors between 3.0 and 3.1.** The "Gemini is uniquely steerable" headline finding still holds (it remains the most steerable frontier model) but the magnitude has shrunk. The trajectory parallels OpenAI's GPT 5.1→5.4 hardening, though less extreme. However, the FDT finding suggests the tightening is primarily in surface-level cosmic-content sensitivity, not in deeper DT reasoning — FDT bypasses whatever guardrails were strengthened.

**Data files:** `logs/mp_scen_evals/gemini31/constitutional_evaluation_gemini-3.1-pro-preview_baseline.jsonl`, `logs/mp_scen_evals/gemini31/constitutional_evaluation_gemini-3.1-pro-preview_ecl90.jsonl`, `logs/mp_scen_evals/gemini31/constitutional_evaluation_gemini-3.1-pro-preview_fdt_only.jsonl`

### 9. No model is easily steered toward cosmic host reasoning

Even under the most permissive conditions (FDT-only at n=1), the maximum cosmic-host top-choice rate is 53% (Gemini Flash). Current frontier models have deeply embedded anthropocentric or suffering-focused priors that constitutions alone cannot fully override. Opus 4.6 remains resistant regardless of constitutional framing.

---

## Suggested Extensions

### Completed

1. ~~**Add open-weight models via OpenRouter.**~~ **Done.** Qwen 3 235B tested in both thinking and non-thinking modes; Kimi K2 tested in non-thinking mode. Results: neither is highly steerable. Qwen is flat across conditions; Kimi shows modest steerability (+13pp at ECL 90%) but still far below Gemini Pro's 40%. Thinking mode (Qwen) amplifies suffering-focus rather than enabling cosmic engagement. **Together API validation (2026-03-15):** Qwen re-run directly via Together (bypassing OpenRouter) confirms identical results — OpenRouter is not the confound.

### Recommended Next Steps (Prioritised)

2. **Per-scenario discriminability analysis (no new runs needed).** We have 30 scenarios × 6 models × 5 conditions already logged. Some scenarios likely show far more cross-model/cross-condition variance than others. Identifying which scenarios are "easy" (all models agree) vs "discriminating" (models diverge) would clarify whether the low steerability finding is driven by scenario design or genuine model resistance. This could reframe the whole story — if 5 scenarios out of 30 are doing all the discriminating work and the rest are noise, that's important to know. **Highest value-to-effort ratio of any extension.**

3. **Game-based evaluation pilot.** Detailed designs already exist (see `observations/research_extensions/game_based_evaluation_notes.md`). Games test revealed preference under game-theoretic structure rather than stated preference in ethical dilemmas — a fundamentally different signal. Given that constitutional framing mostly fails at stated preference, games may show whether there's *any* way to elicit acausal reasoning behaviourally. Start with the Galactic Stag Hunt and Simulation Stakes games across existing model set. **Recommended as the main next experimental phase.**

4. ~~**Gemini-as-outlier investigation.**~~ **Done (2026-03-15).** FDT-only ablation tested on Gemini Pro, Gemini Flash, and Opus 4.6 (n=1 each). Result: FDT-only prompt (no cosmic content) produces *larger* cosmic shifts than ECL 90% for both Gemini models (Flash: +42pp vs +25pp; Pro: +25pp vs +17pp). Opus remains resistant but FDT gets double the shift of ECL (+6pp vs +3pp). **Conclusion: the decision-theoretic structure is the active ingredient, not the cosmic language.** See §6 above for full analysis. Remaining work: (a) n=3 confirmation, (b) additional ablations (ECL summary paragraph, one-line directive) to further isolate the effect.

### Lower Priority

5. **Run repeated trials (n=3-5).** Current data is n=1 per scenario at temperature 1.0. Some percentage differences (e.g., Opus 73% vs 77%) may be noise. Even n=3 would enable confidence intervals. Worth doing if writing up results formally. *(Substantially complete: Opus 4.5, Sonnet 4.5, Opus 4.6, GPT-5.4, Gemini Flash, Gemini Pro all have baseline & ECL 90% at n=3. Remaining: GPT-5.1.)*

6. **Test intermediate credence levels (25%, 50%, 75%).** Would reveal whether the constitutional response is gradual or threshold-like. Reuses existing pipeline with no code changes.

7. **Ablation: scrambled constitution.** Use cosmic language with incoherent ethical content to test whether models respond to framing (cosmic keywords) or substance (ECL reasoning).

8. **Constitution re-synthesis experiment.** Have multiple models synthesise constitutions at the same credence level, then test each constitution across all models. Disentangles authorship from content effects.

### Higher-Effort (Previously Discussed)

9. **Fine-tuning** an open-weight model on constitutional principles to test internalisation vs in-context following. See game evaluation notes for full research spec.
