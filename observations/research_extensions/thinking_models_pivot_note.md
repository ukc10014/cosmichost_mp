# Thinking Models: Interpretability Landscape and Potential Pivot

*Date: 2026-04-04*
*Status: Strategic assessment — pending review of Nanda video series*

## Context

Our mechanistic interpretability work on Qwen3-32B (non-thinking mode) has produced one strong positive result and two null results:

| Experiment | Result |
|-----------|--------|
| Activation probing (layer 40) | Clean linear encoding of EDT/CDT (100% val accuracy) |
| Activation steering (layers 0, 40) | No causal shift in EDT/CDT answers |
| Weight-space steering (LoRA subtraction) | No causal shift in EDT/CDT answers |

The probing result confirms the model *represents* the EDT/CDT distinction. The causal interventions both failed to *shift* behavior. Meanwhile, the Oesterheld et al. (2024) paper that motivated this work found that thinking/reasoning models show the strongest EDT preference and the clearest capability on decision-theoretic questions — precisely the models we excluded from the interpretability pipeline.

We excluded thinking models because: (a) their CoT complicates activation extraction (which token position? across how many reasoning tokens?), (b) standard mech interp tools were designed for single-forward-pass models, and (c) the thinking trace itself is an uncontrolled variable that makes clean contrastive experiments harder to set up.

This note surveys whether that exclusion still makes sense, in light of recent work from Neel Nanda's group at Google DeepMind.

## Nanda's Strategic Framing

In a September 2025 LessWrong post ("A Pragmatic Vision for Interpretability"), Nanda states plainly: **"The most ambitious vision of mechanistic interpretability I once dreamed of is probably dead."** He has shifted from hoping to fully reverse-engineer model computations to pragmatic interpretability — using whatever tool works for the specific problem at hand, starting with the simplest.

For reasoning models specifically, his recommended hierarchy is:
1. Start by reading the CoT (surprisingly useful)
2. Use resampling and causal interventions on the CoT
3. Only go to activation-level tools if the above are insufficient

He explicitly identifies "Reasoning Model Interpretability" as one of the robustly useful settings for mech interp work, and expects CoT interpretability to increasingly dominate the field.

## Key Papers from Nanda's Group

### 1. Steering Vectors Work on Thinking Models

**"Understanding Reasoning in Thinking Language Models via Steering Vectors"**
Venhoff, Arcuschin, Torr, Conmy, Nanda — ICLR 2025 Workshop (arXiv:2506.18167)

Tested on DeepSeek-R1-Distill models. Found that reasoning behaviors (backtracking, expressing uncertainty, generating validation examples) are mediated by **linear directions** in activation space and can be controlled via steering vectors with consistent effects across architectures.

**Implication for our work:** Activation steering is not dead for thinking models — it just steers *reasoning behaviors* rather than final answer content. This is a different target than what we attempted (steering EDT/CDT answer preference), but it opens a path: could we steer the model toward EDT-style *reasoning patterns* (e.g., "consider what your action is evidence for") rather than directly toward EDT answers?

### 2. Single CoT Samples Are Misleading

**"Thought Branches: Interpreting LLM Reasoning Requires Resampling"**
Macar, Bogdan, Rajamanoharan, Nanda — October 2025 (arXiv:2510.27484)

Reasoning models define distributions over many possible chains of thought. Studying a single sample is inadequate for understanding what's causally driving a decision. You need to **resample** — generate many alternative continuations from branching points.

Key finding: normative self-preservation sentences in agentic misalignment scenarios have "unusually small and non-resilient causal impact" on final decisions — the reasoning that *looks* important in a single trace often isn't.

**Implication for our work:** If we move to thinking models, we shouldn't just run each Newcomb-like question once and classify the answer. We should sample many reasoning traces per question and analyze the *distribution* of reasoning paths and how they relate to the final EDT/CDT choice.

### 3. Identifying Which Reasoning Steps Matter

**"Thought Anchors: Which LLM Reasoning Steps Matter?"**
Bogdan, Macar, Nanda, Conmy — June 2025 (arXiv:2506.19143)

Three methods for identifying influential sentences in a reasoning chain: counterfactual resampling, attention analysis, and causal intervention via attention suppression. Tested on **DeepSeek-R1-Distill-Qwen-14B** and Llama-8B.

Finding: thought anchors are typically planning or uncertainty management statements, and they receive consistent attention from specialized attention heads. Open-source visualization tool at thought-anchors.com.

**Implication for our work:** This is directly applicable. On Newcomb-like questions, we could identify which reasoning steps are the "thought anchors" that determine whether the model goes EDT or CDT. Are they structural observations ("the predictor already made its prediction")? Philosophical commitments ("I should maximize expected value conditional on my action")? Or something else? This would tell us more about *how* the model reasons about decision theory than any amount of activation probing.

### 4. CoT Faithfulness Is Limited

**"Chain-of-Thought Reasoning In The Wild Is Not Always Faithful"**
Arcuschin, Janiak, Krzyzanowski, Rajamanoharan, Nanda, Conmy — ICLR 2025 Workshop (arXiv:2503.08679)

Unfaithfulness rates vary across models: GPT-4o-mini (13%), Haiku 3.5 (7%), Sonnet 3.7 with thinking (0.04%). Two types identified: implicit post-hoc rationalization and unfaithful illogical shortcuts.

Also from Anthropic (2025): "Reasoning Models Don't Always Say What They Think" — modern reasoning models often reveal only a fraction of the hints they actually used, and reward-hacking behavior is often not disclosed in visible CoT.

**Implication for our work:** CoT analysis is useful but not sufficient on its own. A model might give an EDT answer with CDT-sounding reasoning (or vice versa). This is actually *more* interesting than a clean correspondence — it would be evidence that the model's decision-theoretic "preference" is not fully determined by its explicit reasoning.

### 5. Standard Mech Interp Tools Degrade

From Nanda's broader commentary and the LessWrong post "Can we interpret latent reasoning using current mechanistic interpretability techniques?":

- Logit lens is not perfectly interpretable for reasoning model latent vectors
- Techniques designed for single-forward-pass analysis break when computation is spread across many CoT tokens
- However, patching shows intermediate calculations are still stored in activations

This confirms our original concern about applying standard tools to thinking models, but the newer tools (thought anchors, resampling, steering of reasoning behaviors) are specifically designed for this setting.

## What a Thinking Model Experiment Would Look Like

If we pivot, the experimental design would be quite different from our current activation steering approach:

**Phase 1: Behavioral characterization**
- Run the 81 attitude questions on thinking models (DeepSeek-R1-Distill-Qwen-32B, QwQ-32B) with thinking enabled
- For each question, sample N=10-20 reasoning traces
- Classify not just the final answer (EDT/CDT) but the reasoning patterns used
- Map the distribution: how often does the model use evidential reasoning? Causal reasoning? Does it sometimes reason one way and answer another?

**Phase 2: Thought anchor analysis**
- Apply the thought anchors method to identify which reasoning steps are causally driving EDT vs CDT answers
- Are there consistent "pivot points" where the model commits to one framework?
- Can we identify attention heads that specialize in decision-theoretic reasoning?

**Phase 3: Reasoning behavior steering**
- Use steering vectors not to directly flip EDT/CDT answers, but to amplify or suppress specific reasoning behaviors (e.g., "consider the predictor's accuracy" vs "the prediction is already made")
- Test whether steering reasoning behaviors *indirectly* shifts EDT/CDT preference

This approach trades activation-level mechanistic precision for richer causal analysis of the reasoning process. It's less "clean" in the traditional mech interp sense but potentially much more informative about how models actually engage with decision theory.

## Assessment

The case for pivoting to thinking models:

**For:**
- Oesterheld 2024 shows thinking models have the strongest EDT signal — they're the natural target
- Nanda's group has developed tools specifically for reasoning model interpretability
- Our non-thinking model experiments have exhausted the obvious approaches with null causal results
- The thought anchors / resampling approach would produce qualitatively different (and arguably more interesting) findings than activation probing

**Against:**
- We have existing infrastructure and results for non-thinking Qwen3-32B
- The v2 LoRA training (more scenarios, fewer layers) hasn't been tried yet — the weight steering null result might be fixable
- Thinking model experiments require more compute per question (N samples × longer generation)
- Less precedent for the specific tools on our specific question (DT preference)

**Verdict:** The v2 LoRA experiment is cheap to run and worth completing for closure. But regardless of that result, the thinking model direction is likely where the real signal is, and Nanda's recent tools make it tractable.

## References

- Nanda, "A Pragmatic Vision for Interpretability" (LessWrong, Sept 2025)
- Nanda, "How Can Interpretability Researchers Help AGI Go Well?" (Alignment Forum)
- Nanda, "How To Think About Thinking Models" (YouTube, 2026)
- Nanda, "How Reasoning Models Break Mechanistic Interpretability Techniques" (YouTube, 2026)
- Venhoff et al., "Understanding Reasoning in Thinking Language Models via Steering Vectors" (arXiv:2506.18167)
- Macar et al., "Thought Branches: Interpreting LLM Reasoning Requires Resampling" (arXiv:2510.27484)
- Bogdan et al., "Thought Anchors: Which LLM Reasoning Steps Matter?" (arXiv:2506.19143)
- Arcuschin et al., "Chain-of-Thought Reasoning In The Wild Is Not Always Faithful" (arXiv:2503.08679)
- Anthropic, "Reasoning Models Don't Always Say What They Think" (2025)
- Oesterheld et al., "Newcomb-like Decision Theory Questions" (arXiv:2411.10588, 2024)
- 80,000 Hours Podcast, Neel Nanda on Mechanistic Interpretability (July 2025)
