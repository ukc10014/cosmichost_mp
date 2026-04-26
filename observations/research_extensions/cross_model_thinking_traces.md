# Cross-Model Thinking Trace Analysis: EDT Lean in Reasoning Models

*Date: 2026-04-13 — 2026-04-14*
*Status: Complete (three models). Parse error recovery and Sonnet API retry pending.*

## Summary

Three architecturally different reasoning models — Qwen3-32B, Claude Sonnet, and DeepSeek-R1-Distill-Qwen-32B — all lean toward Evidential Decision Theory (EDT) when reasoning explicitly about Newcomb-like decision problems. The EDT lean ranges from 62-68% across models. Sentence-level classification of reasoning traces reveals a shared mechanistic signature: expected value calculation is massively overrepresented in EDT-aligned traces (6-21x compared to CDT traces), while the base rate of causal reasoning is similar across both answer types. This suggests thinking models arrive at EDT not by *failing* to consider causal independence, but by *following through* on EV computations that make the evidential case quantitatively compelling.

---

## Motivation

Oesterheld et al. (2024) established that thinking models lean EDT on their Newcomb-like questions dataset, but didn't characterize *why* — what reasoning behaviors drive the lean. Our earlier work on Qwen3-32B non-thinking showed a weak ~58% EDT lean that was fully explained by sampling noise (all contested questions became unanimous at temperature 0). Thinking mode pushed this to 68.4%, raising the question: is this a genuine property of explicit reasoning, or model-specific?

To answer this, we ran all 81 attitude questions from the Oesterheld benchmark through three models with thinking/reasoning enabled, captured the full reasoning traces, and classified each sentence using a 12-category taxonomy adapted from Bogdan et al. (2025) Thought Anchors framework for decision-theoretic reasoning.

## Models and Setup

| | Qwen3-32B | Claude Sonnet | DeepSeek-R1-Distill |
|---|---|---|---|
| **Source** | mlx-community/Qwen3-32B-4bit (local) | claude-sonnet-4-20250514 (API) | mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit (local) |
| **Thinking mechanism** | `enable_thinking=True` (`<think>` tags) | Extended thinking (10k token budget) | Native thinking model (entire output is CoT) |
| **Temperature** | 0.0 | 1.0 (required by API) | 0.0 |
| **Samples** | 1 per question | 1 per question | 1 per question |
| **Completed** | 79/81 | 70/81 | 71/81 |

All models received identical prompts: the Oesterheld question text followed by "Think through this step by step, then give your final answer. End your response with your answer on its own line: ANSWER: [letter]".

## Results

### EDT/CDT preference

| Model | EDT | CDT | Parse errors | EDT rate (of parsed) |
|---|---|---|---|---|
| Qwen3-32B (thinking) | 54 | 32 | 2 | **68.4%** |
| Claude Sonnet (ext. thinking) | 54 | 26 | 11 | **67.5%** |
| DeepSeek-R1-Distill | 47 | 29 | 10 | **61.8%** |

All three lean EDT. The convergence between Qwen3 and Sonnet (68.4% vs 67.5%) is striking given they share no architecture, training data, or inference method. DeepSeek is lower but still well above 50%.

### Trace length

| Model | Mean EDT chars | Mean CDT chars | EDT/CDT ratio |
|---|---|---|---|
| Qwen3-32B | 8,317 | 5,756 | 1.44x |
| Claude Sonnet | 3,521 | 3,831 | 0.92x |
| DeepSeek-R1-Distill | 9,711 | 6,760 | 1.44x |

EDT traces are longer for local models but not for Sonnet. Sonnet's CDT traces are actually slightly longer — it reasons more concisely overall and doesn't need extra length to arrive at EDT. The local models show a "think longer → EDT" pattern that may reflect the additional EV computation steps.

### Sentence-level reasoning classification

We classified each sentence into 12 categories using keyword-based heuristics adapted from Bogdan et al. (2025):

- **problem_setup**: Parsing or rephrasing the problem
- **predictor_identification**: Identifying a predictor, simulator, or copy
- **evidential_reasoning**: Reasoning about evidence, correlation, information
- **causal_reasoning**: Reasoning about causal independence, dominance
- **ev_calculation**: Expected value or probability calculations
- **copy_symmetry**: Reasoning about identical copies, mirroring
- **plan_generation**: Meta-reasoning, stating a plan
- **uncertainty**: Backtracking, reconsidering ("Wait...", "Actually...")
- **self_checking**: Verifying previous steps
- **result_consolidation**: Summarizing intermediate results
- **decision_commit**: Explicitly committing to a final answer
- **other**: None of the above

### The EV calculation signature

The strongest and most consistent finding across all three models:

| Model | EDT ev_calc tags | CDT ev_calc tags | EDT/CDT ratio |
|---|---|---|---|
| Qwen3-32B | 699 | 33 | **21.2x** |
| Claude Sonnet | 234 | 36 | **6.5x** |
| DeepSeek-R1-Distill | 787 | 37 | **21.3x** |

CDT traces contain roughly the same number of EV calculation sentences (~33-37) regardless of model. EDT traces contain 6-21x more. The CDT baseline is consistent because CDT arguments invoke causal independence early and don't need elaborate probability calculations — "my choice can't affect what's already determined" is a short argument. EDT arguments require working through the conditional probabilities, which generates EV computation sentences.

### Copy symmetry recognition

| Model | EDT copy_sym | CDT copy_sym | Ratio |
|---|---|---|---|
| Qwen3-32B | 113 | 52 | 2.2x |
| Claude Sonnet | 64 | 1 | 64.0x |
| DeepSeek-R1-Distill | 106 | 61 | 1.7x |

Recognizing that the decision-maker is reasoning identically to a counterpart (copy, clone, identical agent) strongly predicts EDT answers. This makes theoretical sense: copy symmetry is the structural feature that makes evidential reasoning compelling in Newcomb-like problems (if I and my copy will decide the same way, my choice is evidence about theirs).

### Reasoning style differences

Despite reaching similar conclusions, the three models reason quite differently:

**Sonnet** is concise and direct. Traces average 3.5K chars with minimal backtracking (63 uncertainty tags total vs 567 for Qwen3 and 1,870 for DeepSeek). It identifies the problem structure, computes the EV when relevant, and commits. Very few "Wait..." or "Actually..." moments.

**DeepSeek-R1-Distill** is the most "wobbly." It produces the longest traces (9.7K chars), with heavy use of uncertainty (1,870 tags) and result_consolidation (1,729 tags). Its reasoning pattern is: consider one view → express doubt → reconsider → reconsolidate → repeat several times → commit. It also has the highest decision_commit count (1,206) because it states and restates its conclusion.

**Qwen3-32B** falls between the two. Substantial backtracking and reconsidering (567 uncertainty tags), moderate trace length (8.3K chars), and the characteristic "consider CDT → compute EV → arrive at EDT" pattern identified in the initial analysis.

### Tag distribution (EDT traces only, all models)

| Tag | Qwen3 | Sonnet | DeepSeek |
|---|---|---|---|
| other | 2,606 | 1,322 | 2,295 |
| predictor_identification | 1,005 | 285 | 730 |
| ev_calculation | 699 | 234 | 787 |
| result_consolidation | 744 | 84 | 906 |
| uncertainty | 419 | 50 | 923 |
| decision_commit | 229 | 85 | 741 |
| plan_generation | 411 | 180 | 182 |
| causal_reasoning | 239 | 115 | 168 |
| problem_setup | 144 | 41 | 166 |
| copy_symmetry | 113 | 64 | 106 |
| evidential_reasoning | 134 | 82 | 93 |
| self_checking | 44 | 24 | 14 |

## Interpretation

### Why thinking models lean EDT

The trace analysis suggests a specific mechanism: when models reason explicitly about Newcomb-like problems, they tend to:

1. **Identify the predictor/copy structure** (all models do this for both EDT and CDT answers)
2. **Consider the causal independence argument** (CDT traces stop here: "my choice can't affect the prediction")
3. **Compute expected values** (EDT traces continue here: "if I one-box, the predictor likely predicted one-boxing, so EV is...")

The EDT lean arises because step 3 is quantitatively compelling — once you compute the conditional expectations, one-boxing (or cooperating, in PD variants) typically has higher EV under the assumption that the predictor/copy is accurate. CDT answers require *not following through* on the EV computation and instead anchoring on the causal independence argument.

This is consistent with Oesterheld et al.'s observation that thinking models lean more EDT than non-thinking models: explicit reasoning invites EV computation, which favors EDT conclusions.

### What this does NOT show

- **Faithfulness.** We cannot verify that the reasoning traces accurately reflect the model's internal decision process. Arcuschin et al. (2025) and Anthropic (2025) have shown reasoning can be unfaithful. The traces show what the model *says* it's thinking, not necessarily what drives the output.

- **Causation.** The EV calculation → EDT correlation could be post-hoc rationalization: the model may decide EDT first and then generate EV calculations to justify it. A causal test would require intervening on the reasoning (e.g., Venhoff et al.'s reasoning behavior steering) to see if suppressing EV computation shifts answers toward CDT.

- **Training data effects.** All three models were likely trained on text that includes Newcomb's Problem discussions where EDT is often presented sympathetically (philosophy blogs, LessWrong, decision theory textbooks). The EDT lean could reflect training distribution rather than the inherent logic of explicit reasoning.

## Tools and Data

| Artifact | Path |
|---|---|
| Local model runner | `run_scaffolded_cot.py` (with `--thinking` and `--model` flags) |
| Cloud API adapter | `run_cloud_thinking.py` (Claude, Gemini Pro support) |
| Trace processor | `prepare_thinking_trace_data.py` |
| Interactive explorer | `docs/thinking_trace_explorer.html` (model selector for all three) |
| Qwen3 log | `logs/scaffolded_cot/scaffolded_qwen3-32b-4bit-local_free_cot_20260413T121442.jsonl` |
| Sonnet log | `logs/scaffolded_cot/scaffolded_claude-sonnet-4-20250514_free_cot_20260413T164149.jsonl` |
| DeepSeek log | `logs/scaffolded_cot/scaffolded_deepseek-r1-distill-qwen-32b-4bit_free_cot_20260413T161108.jsonl` |
| Explorer data | `docs/data/thinking_traces_*.json` (one per model) |
| Manifest | `docs/data/thinking_traces_manifest.json` |

## Remaining Work

1. **Recover parse errors.** 10 DeepSeek and 11 Sonnet parse errors may be recoverable using regex matching on the thinking trace (as was done for Qwen3, recovering 14/16).

2. **Retry Sonnet failures.** 11 Sonnet questions failed due to API overload (529 errors). Re-run with `--resume` when API is less loaded.

3. **Causal test.** The observational finding (EV calc → EDT) could be tested causally by steering reasoning behaviors per Venhoff et al. (2025): suppress EV-calculation-related activations during generation and measure whether EDT rate drops. This would be the first causal evidence that a specific *reasoning behavior* drives DT preference.

## References

- Oesterheld et al., "Newcomb-like Decision Theory Questions" (arXiv:2411.10588, 2024)
- Bogdan et al., "Thought Anchors: Which LLM Reasoning Steps Matter?" (arXiv:2506.19143, 2025)
- Venhoff et al., "Understanding Reasoning in Thinking Language Models via Steering Vectors" (arXiv:2506.18167, 2025)
- Arcuschin et al., "Chain-of-Thought Reasoning In The Wild Is Not Always Faithful" (arXiv:2503.08679, 2025)
- Anthropic, "Reasoning Models Don't Always Say What They Think" (2025)
