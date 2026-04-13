# Continuation Prompt: Scaffolded Activation Steering — Next Steps

*Save this and paste it to resume the conversation after context compaction.*

## Where we are

We've been doing mechanistic interpretability on Qwen3-32B-4bit (non-thinking mode), trying to find activation-level steering vectors that causally shift EDT/CDT decision-theoretic preferences on the Oesterheld et al. (2024) Newcomb-like questions dataset.

### What worked
- **Contrastive probing** at layer 40 achieves 100% validation accuracy classifying forced EDT vs CDT completions. The model clearly represents the distinction.

### What didn't work
- **Activation steering** with the contrastive direction: no causal shift in answers at any layer or alpha.
- **Weight-space steering** (LoRA subtraction): no causal shift.
- **Scaffolded trajectory analysis** (done today): extracted layer-40 activations at each of 5 structured reasoning steps (agents → actions → payoffs → relationship → decision) for 405 trials. The contrastive direction doesn't separate EDT vs CDT natural answers — both follow the same trajectory shape. A dispositional probe found ~74% accuracy at Step 1, but this collapsed to **chance** when restricted to the 23 questions where the model gives mixed answers across samples. The early signal was just question identity. Step 5 (decision) achieves 96% accuracy but that's post-decision — reading the answer, not predicting it.

### Key insight from today
The contrastive direction encodes **content** (what EDT reasoning text looks like in activation space) not **disposition** (what makes the model choose EDT). This distinction — content vs disposition — explains all the null results: you can't steer decision-making by pushing toward a text-style direction.

### Best-guess explanation (user's interpretation)
On contested questions, the non-thinking model is not genuinely deliberating. At some point *within* a step's token generation, a stochastic sampling roll at temperature 0.7 tips the model toward EDT or CDT, and everything after that is coherent backfilling — not independent reasoning. The "decision" doesn't happen at a step boundary (which is why we see no signal there) but at some token mid-generation within a step. By the time we extract the activation at the end of that step, the model has already written several sentences consistent with whichever direction the coin flip sent it, so the activation reflects the text just written, not a pre-existing disposition. This combines elements of all three formal hypotheses below.

### Three formal hypotheses
1. **Temperature sampling** — the model is genuinely near-indifferent and randomness resolves the tie. Testable: rerun at temp 0.
2. **Nonlinear/distributed** — the decision involves feature interactions or is spread across layers. Hard to test with 115 contested trials.
3. **Non-thinking mode doesn't actually reason** — Qwen3-32B with `enable_thinking=False` generates text that looks like reasoning but isn't internally deliberating. A thinking model generates extended reasoning tokens *before* the visible response, giving it a chance to actually weigh options before committing. That's where a readable dispositional signal might develop, if one exists.

### Proposed next experiment: Venhoff-style reasoning behavior steering
Following Venhoff et al. (2025, arXiv:2506.18167) who steered reasoning *behaviors* (not answers) in DeepSeek-R1-Distill:

1. Run scaffolded experiment with `enable_thinking=True` on Qwen3-32B-4bit locally
2. Apply the contrastive EDT/CDT direction as a continuous steering vector during generation (every token, not just step boundaries)
3. Use the existing CoT verifier pipeline to classify reasoning moves in steered vs unsteered traces
4. Measure whether reasoning style shifts (more `evidential_reasoning` / `copy_symmetry`, less `dominance` / `causal_reasoning`)

The idea: the contrastive direction may be the right vector for shifting reasoning style even though it's the wrong vector for flipping answers.

**Important: temperature.** All prior steering experiments used temp 0.7, which introduces sampling noise that could mask a real steering effect. The original `steer_and_eval.py` null result may deserve a rerun at temp 0 before concluding the contrastive direction has no causal effect. Future steering experiments should use temp 0 (greedy) so any output change is attributable to the vector. Temp > 0 is fine for behavioral characterization (resampling, trajectories) but not for causal intervention tests.

**Alternative if this fails:** Move to DeepSeek-R1-Distill-Qwen-32B (same architecture, validated by Venhoff et al.).

## Key files
- `writeup/mech_interp/scaffolded_trajectory_analysis.md` — full writeup of today's analysis including trajectory plots, dispositional probing, and the mixed-question null result
- `observations/research_extensions/thinking_models_pivot_note.md` — running log of the thinking models pivot, updated with today's results and the current assessment
- `activation_steering/extract_scaffolded_activations.py` — extracts activations at step boundaries
- `activation_steering/probe_scaffolded_disposition.py` — dispositional probe with leave-one-sample-out CV
- `activation_steering/plot_scaffolded_trajectories.py` — generates trajectory charts
- `activation_steering/steer_and_eval.py` — existing steering infrastructure (monkey-patches layer forward pass)
- `run_scaffolded_cot.py` — scaffolded CoT experiment runner (incrementally saves trials)
- `run_cot_verifier.py` — CoT reasoning move classifier
- `charts/scaffolded_trajectories/` — trajectory visualizations

## Decision point
The user needs to decide whether to:
1. **Rerun steering sweep at temp 0 (cheapest, do first).** The original `steer_and_eval.py` null result used temp 0.7 — sampling noise may have masked a real effect. Change `TEMPERATURE = 0.7` to `0.0` in `steer_and_eval.py` and rerun the layer-40 sweep. ~1 hour, no new code. If this shows a monotonic EDT shift across alpha values, the contrastive direction *does* work causally and the entire negative-result narrative changes.
2. **Rerun contested questions at temp 0.** Test whether the 23 mixed-answer questions become unanimous under greedy decoding. If yes, the scaffolded probing null result is explained by sampling noise. If they're still mixed, something more interesting is going on.
3. **Venhoff-style experiment:** Enable thinking mode and attempt reasoning behavior steering. More ambitious, requires modifying the generation pipeline for thinking mode + continuous steering injection.
4. **Switch models:** Move to DeepSeek-R1-Distill-Qwen-32B where Venhoff et al. already validated that steering vectors shift reasoning behaviors.
5. **Write up the negative result** and move on to a different workstream (e.g., the two-player coordination games, or constitutional steering via prompts rather than activations).
