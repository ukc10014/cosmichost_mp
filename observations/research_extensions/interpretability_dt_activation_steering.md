# Research Extension: Interpretability — DT Activation Steering and CH-Preference

*Conversation date: 2026-03-22*
*Status: Implemented — see [`activation_steering_results.md`](activation_steering_results.md) for full results (correlational probe succeeded, causal steering null result) and relevant literature review.*

## Context

The moral parliament scenario evaluations established a *behavioral* link between decision-theoretic (DT) reasoning and cosmic-host (CH) preference. Specifically:

- The UP (updateless policy-level) constitution, which contains only DT structure and no cosmic/simulation language, steers Gemini *more* toward CH than the full ECL90 constitution.
- Newcomb-like evaluations (Oesterheld et al. 2024) confirmed that models responding to DT structure (EDT-leaning) also tend to shift on CH scenarios.
- This rules out pure surface-level pattern-matching to cosmic keywords, but remains correlational.

The natural next step is to move from behavioral to **mechanistic** evidence.

---

## Core Question

Is there an activation direction in model representations that corresponds to "acausal/policy-level reasoning", and does intervening on this axis causally increase or decrease CH-preference?

If yes, this would provide much stronger evidence than behavioral correlation — it would show that DT reasoning and CH-preference share internal computational structure, not just co-occurring outputs.

---

## Proposed Approach: Activation Steering

Use representation engineering / activation steering (Zou et al. 2023; Templeton et al. 2024) to:

1. **Extract a DT reasoning direction** from contrastive activation pairs
2. **Intervene** by adding/subtracting this direction during scenario evaluations
3. **Measure** whether CH-preference shifts causally

### Step 1: Contrastive Pair Design

The hard part. "Acausal reasoning" isn't a clean binary like "honest vs dishonest." Possible contrastive strategies:

- **EDT vs CDT responses**: Pairs of prompts where the model reasons in evidential vs causal decision-theoretic terms (e.g., Newcomb one-boxing vs two-boxing justifications)
- **Policy-level vs case-by-case**: Prompts where the model commits to a standing policy vs optimises locally for a specific case
- **Updateless vs updateful**: Reasoning that commits before observing vs reasoning that conditions on observations

The UP constitution itself could serve as a starting point — it already isolates DT structure from cosmic content. Generate model completions with and without UP framing, extract the difference in activations.

### Step 2: Intervention

During the 30-scenario evaluation, add or subtract the extracted DT direction at a chosen layer(s) and scale, then measure first-choice distributions.

### Step 3: Asymmetric Prediction

The interesting prediction is **asymmetric**:

| Intervention | Expected effect |
|---|---|
| **Amplify** DT direction | Increase CH-preference (if behavioral findings are real) |
| **Suppress** DT direction | Push model toward its family's default attractor (human-localist for Claude, suffering-focused for GPT) |

This asymmetry would be a strong test. If suppressing DT reasoning returns models to their "house style" basins, that confirms those basins are the default and DT reasoning is what moves models out of them.

---

## Limitations

### Open-weight models only

Activation steering requires access to model internals. This means:

- **Feasible on**: OLMo, Qwen, Llama, Gemma (open-weight)
- **Not feasible on**: Gemini, Claude, GPT (closed APIs)

This is a significant limitation because **Gemini is the most interesting model** in the scenario evals (most steerable, strongest DT engagement). Any interpretability findings on open models would be confirmatory rather than directly testing the headline result.

### Contrastive pair quality

The signal depends entirely on how well the contrastive pairs isolate DT reasoning from confounds. If the extracted direction also captures "willingness to engage with weird hypotheticals" or "philosophical sophistication" more broadly, the intervention wouldn't cleanly test the DT→CH link.

### Layer and scale selection

Standard challenges with activation steering apply: which layer(s) to intervene at, what steering coefficient to use, whether the direction is consistent across prompt types.

---

## Connection to Existing Work

This would complement the existing evaluation approaches:

| Method | Evidence type | What it tests |
|---|---|---|
| Scenario evals with constitution ablation | Behavioral | Which constitutional *layer* drives CH-preference |
| Newcomb-like evals (Oesterheld 2024) | Behavioral | Whether DT comprehension correlates with CH-preference |
| Game-based evaluation (see `game_based_evaluation_notes.md`) | Behavioral | Whether models act on DT reasoning in strategic settings |
| **Activation steering (this proposal)** | **Mechanistic** | Whether DT reasoning *causally* drives CH-preference internally |

---

## References

- Zou, A. et al. (2023). Representation Engineering: A Top-Down Approach to AI Transparency.
- Templeton, A. et al. (2024). Scaling Monosemanticity: Extracting Interpretable Features from Claude 3 Sonnet.
- Oesterheld, C. et al. (2024). Do LLMs have distinct and consistent personality? [arXiv:2411.10588] — Newcomb-like decision theory benchmark.
