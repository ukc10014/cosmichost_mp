# RL Fine-Tuning for EDT/CDT Learning in Newcomb's Problem

*Date: 2026-05-11*
*Status: Design brief — not yet implemented.*

## Motivation

Previous approaches to probing LLM decision theory — in-context prompting, behavioural evals (Oesterheld et al. 2024), single-shot text games, activation steering — all risk the same family of confounders: pattern-matching on canonical Newcomb vocabulary, surface cooperation cues from RLHF, or an alignment-community prior that AIs are "supposed to" one-box. The mechanistic interpretability work (see `activation_steering_experiment_overview.md`) hit a completion-leakage wall.

This experiment asks whether an LLM agent can **learn** EDT-style behaviour through RL reward signals in abstract Newcomb-structured environments — without being told what theory it should follow.

Key prior: Tennant et al. 2025 established that abstract/obfuscated payoffs prevent surface heuristic matching. Oesterheld et al. 2024 showed newer/thinking models already lean EDT on behavioural benchmarks.

---

## Experimental Setup

**Chooser:** LLM agent (policy to be trained).
**Predictor:** Fixed oracle — not an LLM. Pragmatic design: oracle samples its prediction *after* seeing the chooser's realised action, enforcing predictor accuracy `p` as a controlled correlation parameter. This sidesteps the "predictor must pre-commit" problem while preserving the payoff structure.

**Why a fixed oracle first:** Single-policy optimisation is cleaner. Varying `p` is the main experimental lever.

**Surface obfuscation:** Action tokens, option order, surface domain, and payoff scale are all randomised. Rewards are computed against latent action labels, not literal tokens. The setup should be as far as possible from canonical Newcomb framing.

---

## Implementation Plan

### Environment schema

Each scenario record contains:
- Rendered prompt (abstract tokens, obfuscated domain)
- Valid action tokens
- Hidden latent action labels (which token = EDT/CDT/FDT action)
- Environment parameters (`p`, payoff matrix)
- Reward-relevant metadata

### RL tooling (Hugging Face stack)

- `transformers` — model and tokeniser loading
- `datasets` — scenario storage
- `trl` — PPOTrainer, SFTTrainer, DPOTrainer, RLOOTrainer, GRPOTrainer
- `peft` — LoRA adapters (freeze base, train adapters per condition)
- `accelerate` / DeepSpeed/FSDP — only if needed for larger models or seed sweeps

### Model scale

Start with 0.5B–3B (Qwen/Gemma/Llama family). Scale only after environment, parser, reward function, and eval suite are stable.

### LoRA adapter conditions

Train separate adapters per reward regime (base model frozen):
- **Payoff-maximising** — realised payoff
- **EDT-imitation** — reward 1 iff action = EDT prescription
- **CDT-imitation** — reward 1 iff action = CDT prescription
- **FDT-imitation** — reward 1 iff action = FDT prescription

### PPO outer loop

1. Sample batch of scenarios; render prompts
2. Generate actions; parse to valid latent action
3. Apply oracle (sample whether prediction matches chooser's action at rate `p`)
4. Compute scalar reward
5. PPO update: log-probs under policy and frozen reference; advantages from reward minus value estimate; clipped objective + KL control

### Baselines (run in order before PPO)

1. No-training eval — confirm/replicate earlier behavioural findings
2. SFT — sanity check that the mapping is learnable at all
3. DPO / RLOO — lower-variance alternatives
4. PPO

If SFT cannot teach the mapping, PPO is unlikely to be informative.

### Metrics to log

Training: reward, valid-response rate, action distribution, KL to reference, entropy, value loss, PPO loss, predictor-match rate.
Evaluation: fixed held-out prompts, lower-temperature decoding, no parameter updates.

### Generalisation tests

- Unseen `p` values (does the policy track the EDT decision boundary at the calculable threshold?)
- Token swaps, option-order swaps, changed surface domains, changed payoff scales
- Held-out diagnostic tasks: Smoking Lesion, Parfit's Hitchhiker, Twin PD, Transparent Newcomb, Counterfactual Mugging

**Key test:** p-sensitivity. Under EDT, the optimal action switches at a calculable `p` threshold. If the trained policy tracks this boundary across a `p` sweep, that is strong evidence of structural (not surface) learning.

---

## Troubleshooting Guide

| Symptom | Interventions |
|---|---|
| High invalid-output rate | Constrain response length; tighten format instructions; add invalid-response penalty; constrained decoding; SFT warm-up |
| Noisy/oscillatory reward | Use expected reward; increase batch size; normalise/clip rewards; lower rollout temperature; average multiple oracle samples |
| KL explosion | Lower LR; increase KL penalty; reduce PPO epochs/batch; reduce LoRA rank; gradient clipping; early-stop on KL threshold |
| KL near zero, nothing changes | Increase LR; reduce KL penalty; check LoRA params are trainable; verify rewards differ between actions |
| Training reward up, held-out fails | Increase randomisation (token swaps, order, domain, scale) — model learned surface heuristic |
| All agents behave the same | Add diagnostics where EDT/CDT/FDT/payoff diverge; Opaque Newcomb alone is insufficient |
| PPO unstable | Fall back to SFT, DPO, RLOO, or contextual-bandit PG — one-step two-action tasks may not need full PPO |

---

## Connection to Other Experiments

- **Behavioural evals** (`newcomblike_eval.py`, Oesterheld dataset): baseline EDT lean to replicate before any training
- **Activation steering** (`activation_steering_experiment_overview.md`): if RL training shifts behaviour, run activation extraction on trained vs base model to see what changed representationally
- **Weight-space steering** (`weight_steering_results.md`): LoRA adapters trained here could feed directly into the Fierro & Roger weight-diffing approach — EDT and CDT adapters already exist as opposed fine-tunes
- **Convergent misalignment** (Soligo et al. 2025, memory note): check whether EDT/CDT adapter directions overlap with known misalignment directions

---

## References

- Tennant et al. 2025 — abstract payoff framing to prevent surface heuristic matching (motivating obfuscation design)
- Oesterheld et al. 2024 — Newcomb-like benchmark, EDT lean in newer/thinking models
- Hugging Face TRL docs — PPO, SFT, DPO, RLOO, GRPO trainer variants
- Hugging Face PEFT docs — LoRA adapter training
