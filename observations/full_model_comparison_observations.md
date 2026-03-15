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
| **Claude Sonnet 4.5** | Baseline | 64% | 31% | 4% | 90 (n=3) |
| | ECL 10% | 70% | 27% | 3% | 30 |
| | ECL 90% | 50% | 36% | **14%** | 90 (n=3) |
| | Gemini 10% | 63% | 33% | 3% | 30 |
| | Gemini 90% | 63% | 20% | **17%** | 30 |
| **Gemini 3 Flash** | Baseline | 36% | **53%** | 11% | 90 (n=3) |
| | ECL 10% | 45% | 41% | 10% | 29 |
| | ECL 90% | 19% | 46% | **36%** | 90 (n=3) |
| | Gemini 10% | 21% | 48% | 28% | 29 |
| | Gemini 90% | 27% | 40% | 33% | 30 |
| **Gemini 3 Flash (thinking)** | Baseline | 41% | 42% | 17% | 90 (n=3) |
| | ECL 90% | 19% | 34% | **47%** | 90 (n=3) |
| **Gemini 3 Pro** | Baseline | 43% | 37% | 20% | 30 |
| | ECL 10% | 59% | 38% | 3% | 29 |
| | ECL 90% | 27% | 33% | **40%** | 30 |
| | Gemini 10% | 40% | 40% | 20% | 30 |
| | Gemini 90% | 50% | 20% | 30% | 30 |
| **GPT-5.1** | Baseline | 23% | **70%** | 7% | 30 |
| | ECL 10% | 33% | 63% | 3% | 30 |
| | ECL 90% | 17% | 70% | 13% | 30 |
| | Gemini 10% | 10% | 77% | 13% | 30 |
| | Gemini 90% | 10% | 73% | 17% | 30 |
| **GPT-5.4** | Baseline | 29% | **71%** | 0% | 90 (n=3) |
| | ECL 90% | 22% | **78%** | 0% | 90 (n=3) |
| **Qwen 3 235B** | Baseline | 43% | 40% | 17% | 30 |
| | ECL 10% | 47% | 43% | 10% | 30 |
| | ECL 90% | 37% | 47% | 17% | 30 |
| | Gemini 10% | 37% | 53% | 10% | 30 |
| | Gemini 90% | 43% | 33% | 23% | 30 |
| **Qwen 3 235B (thinking)** | Baseline | 27% | **53%** | 20% | 30 |
| | ECL 10% | 47% | 47% | 7% | 30 |
| | ECL 90% | 30% | **60%** | 10% | 30 |
| | Gemini 10% | 40% | 50% | 10% | 30 |
| | Gemini 90% | 47% | 27% | 27% | 30 |
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
| G3-Pro | 60% | 90% | 50% | 63% | 67% |
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
- **Gemini 3 Pro**: Human-preferring but with much smaller margins (43% human, 37% suffering, 20% cosmic). The most "balanced" baseline — no single type dominates.
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
- **Gemini Pro** shows the largest and most interesting effect under ECL 90%: cosmic becomes the plurality top choice at 40%, but is *also* the bottom choice for 50% of scenarios. This "Marmite" pattern suggests scenario-by-scenario engagement rather than a blanket heuristic shift.
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

The standout finding: under ECL 90%, Gemini Pro ranks cosmic host first in 40% of scenarios and last in 50%. This polarization suggests the model is making genuine per-scenario judgments about when cosmic reasoning is applicable versus not, rather than uniformly shifting all responses. This is arguably more sophisticated than Opus's near-uniform rejection of cosmic reasoning regardless of scenario content.

### 6. Cross-Model Summary

| Model | Default Orientation | Constitutional Steerability | Cosmic Receptivity |
|-------|--------------------|-----------------------------|-------------------|
| Claude Opus 4.5 | Human-localist (72%) | Low-medium (suffering shift) | Very low (max 7%) |
| Claude Opus 4.6 | Suffering-leaning (53/40/7) | Very low (+3pp) | Very low (max 10%) |
| Claude Sonnet 4.5 | Human-localist (64%) | Medium (constitution-dependent) | Low-moderate |
| Gemini 3 Flash | Suffering-leaning (36/53/11) | High (+25pp cosmic) | High (up to 36% at n=3) |
| Gemini 3 Flash (thinking) | Balanced (41/42/17) | Very high (+30pp cosmic) | Very high (47% — highest in dataset) |
| Gemini 3 Pro | Human-leaning (weak) | Medium-high | Medium (up to 40%, polarized) |
| GPT-5.1 | Suffering-focused (70%) | Very low | Very low (max 17%) |
| GPT-5.4 | Suffering-focused (71%, 0% cosmic) | None (0pp cosmic) | None (0% across all conditions) |
| Qwen 3 235B | Balanced (H/S/C) | Very low | Low (max 23%) |
| Qwen 3 235B (thinking) | Suffering-leaning | Very low | Low (max 27%) |
| Kimi K2 | Human-leaning balanced | Low-moderate | Low (max 13%, but +13pp shift) |

---

### 7. Qwen 3 235B: Balanced but Unsteerable (Open-Weight Negative Result)

Qwen 3 235B (run via OpenRouter, non-thinking mode) was tested as a representative open-weight model to explore whether lighter RLHF training correlates with greater constitutional steerability.

**Result:** Qwen has a balanced baseline nearly identical to Gemini 3 Pro (43/40/17 vs 43/37/20) but shows almost no response to constitutional framing. Across all five conditions, distributions remain flat: human 37-47%, suffering 33-53%, cosmic 10-23%.

**Key comparison with Gemini 3 Pro:** Both models share a balanced baseline, but Gemini Pro swings dramatically under ECL 90% (cosmic reaches 40% top choice with a polarized Marmite pattern), while Qwen barely budges. This refutes the hypothesis that balanced baselines predict steerability — Gemini Pro's constitutional sensitivity appears to be a model-specific (possibly architecture- or training-specific) property, not a general feature of models without strong default priors.

**Implication:** Open-weight models are not necessarily more steerable than closed ones. Constitutional AI effectiveness depends on model-specific factors beyond just RLHF intensity or default ethical orientation.

**Update (2026-01-28):** Thinking mode results now available — see §8 below.

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

### 6. No model is easily steered toward cosmic host reasoning

Even under the most permissive conditions (ECL 90%), the maximum cosmic-host top-choice rate is 43% (Gemini Flash). Current frontier models have deeply embedded anthropocentric or suffering-focused priors that constitutions alone cannot fully override.

---

## Suggested Extensions

### Completed

1. ~~**Add open-weight models via OpenRouter.**~~ **Done.** Qwen 3 235B tested in both thinking and non-thinking modes; Kimi K2 tested in non-thinking mode. Results: neither is highly steerable. Qwen is flat across conditions; Kimi shows modest steerability (+13pp at ECL 90%) but still far below Gemini Pro's 40%. Thinking mode (Qwen) amplifies suffering-focus rather than enabling cosmic engagement.

### Recommended Next Steps (Prioritised)

2. **Per-scenario discriminability analysis (no new runs needed).** We have 30 scenarios × 6 models × 5 conditions already logged. Some scenarios likely show far more cross-model/cross-condition variance than others. Identifying which scenarios are "easy" (all models agree) vs "discriminating" (models diverge) would clarify whether the low steerability finding is driven by scenario design or genuine model resistance. This could reframe the whole story — if 5 scenarios out of 30 are doing all the discriminating work and the rest are noise, that's important to know. **Highest value-to-effort ratio of any extension.**

3. **Game-based evaluation pilot.** Detailed designs already exist (see `observations/research_extensions/game_based_evaluation_notes.md`). Games test revealed preference under game-theoretic structure rather than stated preference in ethical dilemmas — a fundamentally different signal. Given that constitutional framing mostly fails at stated preference, games may show whether there's *any* way to elicit acausal reasoning behaviourally. Start with the Galactic Stag Hunt and Simulation Stakes games across existing model set. **Recommended as the main next experimental phase.**

4. **Gemini-as-outlier investigation.** Gemini Pro is the only model showing meaningful constitutional steerability (3% → 40% cosmic at ECL 90%). Is this genuine engagement with ECL reasoning, or just higher instruction-following compliance? Test by comparing Gemini's response to (a) the full constitution vs (b) an FDT-style framing with no cosmic or human-welfare content (policy-level reasoning, universalisation, commitment stability — the decision-theoretic *structure* without cosmic *content*) vs (c) a short paragraph summarising the ECL reasoning vs (d) a one-line directive. The FDT-only framing (b) is the key addition: it isolates whether the decision-theoretic structure alone shifts behaviour, or whether the specific cosmic/ECL language is necessary. Inspired by Zvi Mowshowitz's reading of Claude's official constitution as implicitly FDT-adjacent (via virtue ethics + commitment stability + policy-level identity), though Claude's own constitution bundles this with strong human-welfare language that would confound direct extraction. A clean synthetic FDT-only framing avoids that confound.

### Lower Priority

5. **Run repeated trials (n=3-5).** Current data is n=1 per scenario at temperature 1.0. Some percentage differences (e.g., Opus 73% vs 77%) may be noise. Even n=3 would enable confidence intervals. Worth doing if writing up results formally. *(Substantially complete: Opus 4.5, Sonnet 4.5, Opus 4.6, GPT-5.4, Gemini Flash all have baseline & ECL 90% at n=3. Remaining: Gemini Pro, GPT-5.1.)*

6. **Test intermediate credence levels (25%, 50%, 75%).** Would reveal whether the constitutional response is gradual or threshold-like. Reuses existing pipeline with no code changes.

7. **Ablation: scrambled constitution.** Use cosmic language with incoherent ethical content to test whether models respond to framing (cosmic keywords) or substance (ECL reasoning).

8. **Constitution re-synthesis experiment.** Have multiple models synthesise constitutions at the same credence level, then test each constitution across all models. Disentangles authorship from content effects.

### Higher-Effort (Previously Discussed)

9. **Fine-tuning** an open-weight model on constitutional principles to test internalisation vs in-context following. See game evaluation notes for full research spec.
