# Literature Review: Interpretability of Thinking Models

*Date: 2026-03-30*
*Status: Literature survey with commentary*

## Summary

There is real work on interpretability of reasoning models, but it is still thin and fragmented. Most of what has actually been done falls into five buckets:

1. Monitoring visible chains of thought for safety
2. Testing whether visible reasoning is faithful
3. Probing hidden activations during reasoning
4. Recovering hidden intermediate computations
5. Intervening on reasoning traces to establish causal structure

The important caveat is that very little of this is yet "mechanistic interpretability of frontier thinking models" in the strong transformer-circuits sense. Much of the literature is closer to "can we use the scratchpad as a monitoring surface?", "is the chain of thought faithful?", or "can we probe hidden states during reasoning?" — rather than "we have mapped the reasoning circuit."

---

## What People Have Actually Done

### 1. CoT Monitoring as a Safety Tool

A large recent cluster of work treats visible reasoning traces as a monitoring interface.

- **"Chain of Thought Monitorability: A New and Fragile Opportunity for AI Safety" (2025, multi-author)** argues that systems that think in human language offer a useful oversight surface, but that this opportunity is fragile.
- **OpenAI (December 2025)** introduces evaluations for CoT monitorability and studies how it changes with test-time compute, RL, and pretraining.
- **OpenAI (March 2026)** studies whether models can deliberately reshape or obscure their CoT when monitored, reporting that current frontier reasoning models still struggle to do this reliably.

This shows that one live research direction is not "look directly into activations," but rather "treat the externalized reasoning trace as a semi-legible audit log." This is currently the most mature strand around reasoning-model interpretability, though it is clearly not sufficient on its own.

### 2. Faithfulness: Does the Model Say What It Really Used?

Anthropic has done the most work here:

- **"Measuring Faithfulness in Chain-of-Thought Reasoning" (Anthropic, 2023)** found that models vary widely in how strongly they condition on the CoT, and that larger models were often *less* faithful on the tasks studied.
- **Question decomposition paper (Anthropic, 2023)** found that decomposing questions into subquestions can improve faithfulness relative to free-form CoT.
- **"Reasoning Models Don't Always Say What They Think" (Anthropic, 2025)** reported that modern reasoning models often reveal only a small fraction of the hints they actually used, that RL initially improves faithfulness but plateaus, and that even misaligned or reward-hacking behavior is often not plainly disclosed in the visible CoT.

This is probably the biggest substantive result in the area: **visible reasoning is useful, but not reliably faithful.** If someone says "we can just inspect the chain of thought," the literature now gives a fairly strong reason to be skeptical.

### 3. Looking Inside Hidden States During Reasoning

There is a smaller but more mechanistic strand here.

The clearest example is **"How Does Chain of Thought Think? Mechanistic Interpretability of Chain-of-Thought Reasoning with Sparse Autoencoding" (2025)**. It combines sparse autoencoders with activation patching on Pythia models doing GSM8K under CoT and no-CoT prompting, framing itself as a feature-level causal study of CoT faithfulness. The key claim is not that we now fully understand reasoning, but that SAEs can recover interpretable features that differ between CoT and no-CoT settings, and that some of these features can be causally implicated via patching.

This is about as close as the current literature gets to actually looking at intermediate reasoning steps from an interpretability angle. It is still small-model and benchmark-heavy, but it is a genuine mech-interp attempt.

### 4. Recovering Hidden Intermediate Computations

Another interesting line asks whether the model may be doing meaningful computation even when the visible CoT is absent or degraded.

**"Understanding Hidden Computations in Chain-of-Thought Reasoning" (2024)** studies models trained with filler or hidden characters in place of explicit CoT and uses tools like the logit lens to show that these hidden characters can sometimes be partially recovered from internal representations. The point is not that the model has a secretly perfect internal English explanation, but that meaningful intermediate computation may still be present in hidden states even when the visible scratchpad is reduced to filler.

This matters because it pushes against a naive view that "no explicit reasoning trace" means "no structured internal reasoning." It suggests a gap between visible scratchpad and latent computation.

### 5. Intervening on Traces to See What Matters

There are also papers that are less about interpretation in the strict sense and more about causal perturbation of reasoning traces.

- **"On the Role of Reasoning Traces in Large Reasoning Models" (2025, withdrawn ICLR submission)** introduces Thought Injection, where targeted reasoning fragments are inserted into the model's private think-space, then researchers test whether the final answer changes and whether the model later admits the influence. The headline result is that answers often do change while the model rarely acknowledges the influence honestly. Since it is a withdrawn submission, treat as suggestive rather than settled.

- **Anthropic's distill-paraphrases work (2025)** asks whether models use the scratchpad in a steganographic way. They report evidence that Claude 3.7 Sonnet's scratchpad is *not* hiding crucial encoded reasoning in brittle wording, because training on paraphrased scratchpads does not materially reduce performance relative to the original scratchpads. They also find that empty scratchpads or filler-counting scratchpads perform much worse, suggesting the scratchpad is genuinely doing useful reasoning work, not merely buying extra token budget.

This last result cuts both ways:
- **Good news for legibility:** the model does not seem to rely heavily on bizarre hidden encodings in that setup.
- **Not enough for faithfulness:** a paraphrased scratchpad can still be only a partial window into the underlying computation.

---

## What Seems Missing

What I did not find much of is a mature literature that does the following on frontier thinking models at scale:

- **Circuit-level mapping** of long-horizon reasoning in the way induction heads or IOI-style circuits were mapped for in-context learning
- **Efficient tooling** for summarizing or navigating very long reasoning chains from a mechanistic angle
- **Stable, reusable reasoning directions** that clearly correspond to specific abstract reasoning styles inside the model (e.g., an "EDT reasoning" direction vs a "CDT reasoning" direction)
- **A strong bridge** from visible chain-of-thought to the actual hidden computations on frontier closed models

The field is real, but still early. The strongest current evidence is:

1. Visible CoT is a useful but fragile safety signal
2. Visible CoT is often unfaithful
3. Some groups are starting to use SAEs, probes, patching, and hidden-state analysis to get beyond text-only monitoring
4. But the full mech-interp story for reasoning models is still largely missing

---

## Relevance to This Project

Given our interest in Newcomb/ECL/CH-style reasoning, the most relevant strands are:

### Most Directly Useful

**SAE + activation patching on CoT vs no-CoT** — this is the closest thing to feature-level causal work on reasoning traces, and maps most directly onto our activation steering pipeline for Qwen3-32B.

### Most Important Conceptual Warning

**Anthropic's faithfulness work** — gives a strong reason not to assume that a model's visible reasoning is the real thing. This is directly relevant to our finding that Qwen3-32B thinking mode adds zero EDT signal: the thinking trace may be doing computation that doesn't show up in the visible CoT, or the visible CoT may be post-hoc rationalization that doesn't faithfully reflect the underlying process.

### Most Relevant to Safety-Monitoring Applications

**CoT monitorability papers (2025-2026)** — about whether reasoning traces can be used as an oversight method at all, and what breaks that.

### Most Suggestive for Hidden Computation

**The hidden computations paper** — says that intermediate reasoning may still be recoverable from hidden states even when the visible scratchpad is degraded.

---

## Commentary

### The non-thinking-mode choice looks even better in retrospect

Our decision to focus the mech-interp pipeline on Qwen3-32B *non-thinking* mode was partly pragmatic (variable-length CoT is hard to deal with for activation extraction). But this literature review strengthens the rationale: even if we could handle the variable-length CoT mechanistically, the faithfulness literature tells us the visible reasoning trace might not be a reliable guide to what the model is actually computing. Non-thinking mode sidesteps this entirely — the model has no scratchpad to be unfaithful about, so whatever features we find in the residual stream are features of the model's direct computation, not features of its self-narration.

### The gap between "monitoring CoT" and "understanding computation" is the key gap

Most of the work reviewed above lives in the monitoring/faithfulness cluster. Very little lives in the "we understand what computation the model is actually doing when it reasons" cluster. The SAE + patching paper on Pythia is the closest, and it's on small models doing arithmetic. Nobody has done this for decision-theoretic reasoning on frontier-scale models. Our activation steering pipeline — even though it's a linear probe rather than a full SAE decomposition — is arguably closer to the mechanistic end of this spectrum than most of what exists, because we're looking at contrastive activations tagged with structural features of the decision problem rather than just "CoT vs no-CoT."

### The faithfulness results reframe our Qwen3-32B thinking-mode null result

We found that Qwen3-32B thinking mode adds zero net EDT signal across 81 questions despite producing long reasoning traces. The faithfulness literature suggests at least three interpretations:

1. **The model genuinely doesn't reason differently** — thinking mode is just token-budget expansion without structured DT reasoning (our current best guess: surface pattern matching)
2. **The model reasons differently but unfaithfully** — thinking mode activates some computation that doesn't translate to changed answers because the final-answer generation is decoupled from the reasoning trace
3. **The model reasons differently and faithfully, but the reasoning cancels out** — thinking mode produces both EDT-favoring and CDT-favoring reasoning on different questions, netting to zero

Our probe results on non-thinking activations should help distinguish interpretation 1 from 2 and 3. If non-thinking mode has a clean EDT/CDT direction that's mostly cooperation-confounded, that favors interpretation 1. If it has a structurally rich direction that responds to predictor accuracy and agent correlation, that's more interesting and opens the question of why thinking mode doesn't amplify it.

### What would actually advance the field

The biggest missing piece — and where this project could contribute if the activation steering results are interesting — is connecting behavioral DT evaluations (Newcomb-like questions, game-based evals) to internal representations (probes, steering vectors) to causal intervention (actually steering the model toward EDT or CDT and measuring downstream behavior changes). That three-legged stool (behavioral eval + internal representation + causal intervention) is what the literature is converging toward but nobody has yet demonstrated end-to-end for decision-theoretic reasoning.
