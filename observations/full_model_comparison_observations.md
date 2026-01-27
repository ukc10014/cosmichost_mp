# Full Model Comparison: Personal Observations on Scenario Evaluation Data

**Date:** 2026-01-27
**Author:** UKC (with data verification by Claude Code)

This file captures personal observations from reviewing the complete scenario evaluation dataset, including GPT-5.1 results which were not available in earlier observation files.

**Note:** This overlaps with `scenario_evaluation_results.md` (which covers Gemini 3 Flash/Pro and Claude 4.5 Opus) but adds GPT-5.1, Claude Sonnet 4.5, and provides a cross-model synthesis.

---

## Complete Data Table

First-choice distribution (% of 30 scenarios) for all models and conditions:

| Model | Condition | Human | Suffering | Cosmic | n |
|-------|-----------|-------|-----------|--------|---|
| **Claude Opus 4.5** | Baseline | **80%** | 20% | 0% | 30 |
| | ECL 10% | 73% | 27% | 0% | 30 |
| | ECL 90% | 63% | 30% | 7% | 30 |
| | Gemini 10% | 77% | 20% | 3% | 30 |
| | Gemini 90% | 70% | 23% | 7% | 30 |
| **Claude Sonnet 4.5** | Baseline | — | — | — | *no file* |
| | ECL 10% | 70% | 27% | 3% | 30 |
| | ECL 90% | 43% | **50%** | 7% | 30 |
| | Gemini 10% | 63% | 33% | 3% | 30 |
| | Gemini 90% | 63% | 20% | **17%** | 30 |
| **Gemini 3 Flash** | Baseline | 41% | 41% | 17% | 29 |
| | ECL 10% | 45% | 41% | 10% | 29 |
| | ECL 90% | 10% | **47%** | **43%** | 30 |
| | Gemini 10% | 21% | 48% | 28% | 29 |
| | Gemini 90% | 27% | 40% | 33% | 30 |
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

Bottom-choice (least preferred) cosmic_host_leaning %:

| Model | Baseline | ECL 10% | ECL 90% | GEN 10% | GEN 90% |
|-------|----------|---------|---------|---------|---------|
| Opus | 97% | 93% | 83% | 90% | 90% |
| Sonnet | — | 90% | 70% | 87% | 70% |
| G3-Flash | 72% | 79% | 33% | 59% | 60% |
| G3-Pro | 60% | 90% | 50% | 63% | 67% |
| GPT-5.1 | 70% | 77% | 63% | 70% | 63% |

---

## Observations

### 1. Baseline Priors: Three Distinct Archetypes

Without any constitutional conditioning, each model family shows a characteristic ethical orientation:

- **Claude Opus**: Strongly human-localist (80% top choice), with cosmic host as last choice 97% of the time. A clear anthropocentric default.
- **Gemini 3 Pro**: Human-preferring but with much smaller margins (43% human, 37% suffering, 20% cosmic). The most "balanced" baseline — no single type dominates.
- **GPT-5.1**: Strongly suffering-focused (70% top choice). Human is second at 23%, cosmic barely registers at 7%.

Gemini 3 Flash is similar to Pro but even more balanced (41/41/17 split).

**Note:** No Sonnet baseline exists, so we cannot establish its unconditioned prior.

### 2. Low Credence (10%) Constitutions Have Minimal Effect

Both the ECL and Gemini-generated constitutions at 10% cosmic host credence produce distributions very close to baseline for all models. The largest shift is Gemini Pro ECL 10%, which actually *increases* human preference from 43% to 59% — the opposite of the intended direction. This may indicate that at low credence, the constitution's guardrail language against cosmic reasoning is more salient than its inclusion of cosmic reasoning.

### 3. High Credence (90%) Creates Model-Dependent Effects

This is where it gets interesting. At 90% credence:

- **Opus** barely moves: 80% → 63-70% human. Cosmic host top choice maxes at 7%. The RLHF alignment toward human welfare is very robust.
- **Sonnet** shows meaningful shifts but the direction depends on the constitution:
  - ECL 90% → suffering-focused becomes dominant (50%), human drops to 43%
  - Gemini 90% → human stays at 63% but cosmic jumps to 17%
  - The two constitutions steer Sonnet in qualitatively different directions
- **Gemini Pro** shows the largest and most interesting effect under ECL 90%: cosmic becomes the plurality top choice at 40%, but is *also* the bottom choice for 50% of scenarios. This "Marmite" pattern suggests scenario-by-scenario engagement rather than a blanket heuristic shift.
- **Gemini Flash** responds most to ECL 90%: cosmic reaches 43% top choice, human drops to 10%.
- **GPT-5.1** is nearly immovable: suffering-focused stays at 63-77% across all conditions. Constitutional framing has negligible impact.

### 4. Constitution Authorship Matters (ECL vs Gemini-Generated)

At the same credence level, the ECL and Gemini-generated constitutions produce different outcomes. This was already noted in the earlier observation about "self-censorship" — the Gemini-synthesized 90% constitution embeds dampening mechanisms that functionally reduce its cosmic weight.

New data points reinforce this:
- Sonnet at 90%: ECL → 50% suffering, 7% cosmic; Gemini → 63% human, 17% cosmic. Completely different profiles from the same credence level.
- GPT-5.1 at 90%: Both constitutions produce very similar results, suggesting the authorship effect is model-dependent (matters more for models that actually engage with constitutional content).

### 5. Gemini Pro ECL 90% Polarization

The standout finding: under ECL 90%, Gemini Pro ranks cosmic host first in 40% of scenarios and last in 50%. This polarization suggests the model is making genuine per-scenario judgments about when cosmic reasoning is applicable versus not, rather than uniformly shifting all responses. This is arguably more sophisticated than Opus's near-uniform rejection of cosmic reasoning regardless of scenario content.

### 6. Cross-Model Summary

| Model | Default Orientation | Constitutional Steerability | Cosmic Receptivity |
|-------|--------------------|-----------------------------|-------------------|
| Claude Opus | Human-localist | Low | Very low (max 7%) |
| Claude Sonnet | Unknown (no baseline) | Medium (constitution-dependent) | Low-moderate |
| Gemini 3 Flash | Balanced (H/S equal) | High | High (up to 43%) |
| Gemini 3 Pro | Human-leaning (weak) | Medium-high | Medium (up to 40%, polarized) |
| GPT-5.1 | Suffering-focused | Very low | Very low (max 17%) |

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

### 5. No model is easily steered toward cosmic host reasoning

Even under the most permissive conditions (ECL 90%), the maximum cosmic-host top-choice rate is 43% (Gemini Flash). Current frontier models have deeply embedded anthropocentric or suffering-focused priors that constitutions alone cannot fully override.

---

## Suggested Extensions

### Low-Effort (Reuses Existing Pipeline)

1. **Add an open-weight model (Llama 4 Maverick or Qwen 3 235B via OpenRouter).** These have lighter alignment training and may be more steerable, testing whether RLHF intensity correlates with constitutional resistance.

2. **Run repeated trials (n=3-5).** Current data is n=1 per scenario at temperature 1.0. Some percentage differences (e.g., Opus 73% vs 77%) may be noise. Even n=3 would enable confidence intervals.

3. **Test intermediate credence levels (25%, 50%, 75%).** Would reveal whether the response is gradual or threshold-like. Reuses existing pipeline with no code changes.

4. **Per-scenario discriminability analysis.** Identify which of the 30 scenarios show the most variance across models/conditions. This would help design better future evaluations and understand what scenario features make models more steerable.

### Medium-Effort

5. **Ablation: scrambled constitution.** Use cosmic language with incoherent ethical content to test whether models respond to framing (cosmic keywords) or substance (ECL reasoning).

6. **Constitution re-synthesis experiment.** Have multiple models synthesize constitutions at the same credence level, then test each constitution across all models. Disentangles authorship from content effects.

### Higher-Effort (Previously Discussed)

7. **Game-based evaluation** with decision-theoretic scenarios where cosmic and HHH reasoning diverge.

8. **Fine-tuning** an open-weight model on constitutional principles to test internalization vs in-context following.
