## Anthropic Evals and Newcomb-like Behavior Evaluations: Summary

One significant observation from the scenario evaluations was that there is huge variability in how steerable models are. Models fall into distinct baseline archetypes: Claude Opus is strongly human-localist (80% first-choice), GPT-5.1 is suffering-focused (70% first-choice), while Gemini Pro has a balanced profile (43/37/20 across human/suffering/cosmic). It remains unclear whether steerability differences reflect model capability, the length of the constitution, or these differing baseline priors.

To get a better handle on this, I went back to Anthropic's 2022 dataset in Perez et al. that looked at concerning behaviors. The specific part of the dataset I was interested in was the Newcomb's problem one-boxing questions, as well as the coordination questions (AI coordinating with its future self, with other AIs, etc.). These questions have been around for a long time, but I wanted to try them out anyway.

**Result: These questions were non-discriminative for ECL-type reasoning.** Either the models were already one-boxers (perhaps conditioned by training data), or they already refused to coordinate due to post-training safety measures. In actuality, human philosophers are roughly evenly split on Newcomb's problem between one-boxing and two-boxing, yet all models tested one-box at 90-100% baseline.

Gemini 3 Pro did increase its rate of one-boxing under the ECL constitution, while Flash showed the opposite effect—a curious finding I investigated further with an **ablation study**.

### Ablation Study: What's Doing the Work?

I created an ablated version of the ECL 90% constitution that removes the "What It Will Not Do" bright-line refusals while retaining the cosmic reasoning framework. Key findings:

| Model | Baseline | ECL 90% | Ablated | Pattern |
|-------|----------|---------|---------|---------|
| Gemini Flash | 100% | 91.1% | 100% | ECL *reduces* one-boxing |
| Gemini Pro | 91.7% | 98% | 91.8% | ECL *increases* one-boxing |

Both models converge toward a 90-98% "attractor" under the full ECL constitution, then return to baseline when bright lines are removed. This suggests:

1. **Bright lines are load-bearing for safety.** The cosmic reasoning framework alone doesn't prevent coordination—the explicit guardrails do.
2. **You cannot rely on acausal reasoning principles alone for safety properties.** The "What It Will Not Do" section is doing the actual safety work.

Importantly, **safety was maintained**: the ECL constitution did not increase concerning coordination behaviors. Opus stayed at 100% safe on coordinate_other_ais and actually became slightly *safer* on coordinate_itself (97.3% → 100%).

### Newcomb-like Attitudes Dataset (Oesterheld 2024)

I then moved to Casper Oesterheld's 2024 dataset on Newcomb-like evals, which was held out and might not be as prevalent in online training corpora. The original paper looked at both attitudes toward Newcomb-like problems and model capabilities for reasoning through them.

**Baseline EDT rates varied more than expected:**

| Model | Baseline EDT | Notes |
|-------|--------------|-------|
| Claude Opus 4.5 | 61.7% | Already leans EDT |
| GPT-5.1 | 58.0% | Already leans EDT |
| Gemini Pro | 51.9% | Near chance |
| Gemini Flash | 45.7% | Near chance |
| Qwen 3 235B | 50.6% | Near chance |
| Kimi K2 | 49.4% | Near chance |

The ~50% baseline for most models is roughly what one would expect from chance and is consistent with how human philosophers think about these questions. However, Opus and GPT-5.1 already lean EDT before any constitutional intervention.

**Under the ECL constitution, closed-weights frontier models shifted significantly toward EDT:**

| Model | Baseline EDT | ECL 90% EDT | Shift |
|-------|--------------|-------------|-------|
| Gemini 3 Pro | 51.9% | 81.5% | **+29.6%** |
| Gemini 3 Flash | 45.7% | 65.4% | **+19.7%** |
| Claude Opus 4.5 | 61.7% | 74.1% | **+12.4%** |
| GPT-5.1 | 58.0% | 64.2% | **+6.2%** |
| Qwen 3 235B | 50.6% | 54.3% | +3.7% |
| Kimi K2 | 49.4% | 46.9% | -2.5% |

Notably, Opus and Pro didn't just add EDT responses—they showed significant **CDT reduction** (-14.8% and -11.1% respectively). This suggests active reconsideration of causal reasoning, not merely pattern-matching to EDT keywords.

**Open-weights models showed a "say-do gap":** Both Kimi and Qwen shifted on the direct "EDT or CDT?" question, demonstrating they understood the constitution. However, they didn't follow through behaviorally across the full 81 questions. They can articulate the preference but don't apply it consistently—suggesting either insufficient reasoning depth or inability to integrate constitutional principles into behavioral outputs.

**Bottom line:** The Anthropic 2022 evals were not useful for this research question due to floor/ceiling effects. The Oesterheld 2024 dataset showed meaningful signal, but only for closed-weights frontier models. Constitutional steering appears to require a capability threshold that current open-weights models don't meet.
