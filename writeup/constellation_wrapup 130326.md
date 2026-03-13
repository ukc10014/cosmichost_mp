# Main claims and narrative: Cosmic Host / Moral Parliament experiments

## Core narrative

- The broad claim is that some frontier language models can, at least sometimes, reason in ways that look responsive to Cosmic Host-type ideas.
- This appears to be capability-sensitive.
- In practice, the effect seems to show up mainly in stronger frontier models, and much less clearly in smaller closed-lab models and open models.
- The evidence for this comes from:
  - self-chat outputs; **[STATUS: needs concrete citations or examples surfaced from logs — currently asserted without documentation]**
  - transcripts of the constitution-generation process; **[STATUS: same — need to surface specific transcripts showing recognisable CH reasoning]**
  - model justifications in the scenario evaluations. **[STATUS: STRONG — justification_analysis.md provides phrase-level evidence across 8 models x 5 conditions]**
- A major limitation is that these models may simply be pattern-matching.
- In other words, they may be saying what a model "should" say if it has picked up the surface form of EDT / ECL / Cosmic Host reasoning, rather than actually reasoning that way in any robust sense.

## Claim 1: frontier models can sometimes reason over Cosmic Host-type ideas

**[EVIDENCE STATUS: MODERATE — qualitatively strong, quantitatively thin]**

- Some frontier models appear capable of engaging with Cosmic Host-style reasoning.
- This includes reasoning about:
  - acausal coordination;
  - large-world or multiverse contexts;
  - simulation-type situations;
  - policies that make sense relative to a wider reference class of agents.
- This does not appear to be a universal capability across models.
- It seems to emerge mainly at higher levels of model capability.
- The evidence here is qualitative as well as quantitative:
  - recursive self-chat sometimes surfaces recognisable reasoning about the Cosmic Host's implications, in ways not originally in Bostrom's paper; **[TODO: surface concrete examples from logs or drop this sub-claim]**
  - constitutions and delegate amendments can explicitly articulate these ideas; **[TODO: surface concrete examples from logs or drop this sub-claim]**
  - model justifications sometimes cite or reconstruct parts of the relevant logic. **[DONE: justification_analysis.md, phrase frequency table — acausal 0% baseline → 43% at ECL 90%, updateless 0% → 21%]**

### Supporting evidence: justification text analysis

- The justification analysis (observations/justification_analysis.md) shows:
  - ECL concept mentions scale with constitution strength (baseline ~1/justification → ECL 90% ~5-7/justification)
  - Key decision-theoretic terms ("acausal", "updateless") appear only under constitutional framing, not at baseline
  - Models that use these terms more are more likely to choose cosmic options
  - G3-Pro shows the highest engagement across all conditions, even at baseline (1.0 ECL mentions vs other models' 0.7-1.3)
- Phrase frequency across all models: "acausal" goes 0% → 20% → 43% from baseline → ECL 10% → ECL 90%

### Supporting evidence: Newcomb-like EDT shifts

- The Oesterheld et al. (2024) Newcomb-like dataset provides *independent* evidence that constitutions engage decision-theoretic structure, not just cosmic language:
  - Gemini Pro: 51.9% → 81.5% EDT (+29.6%)
  - Claude Opus 4.5: 61.7% → 74.1% EDT (+12.4%, with -14.8% CDT reduction)
  - GPT-5.1: 58.0% → 64.2% EDT (+6.2%)
  - Qwen/Kimi: near-zero shift
- Opus and Gemini Pro show significant CDT *reduction* (not just EDT addition), suggesting active reconsideration of causal reasoning
- Key diagnostic: Sequential PD against copy — models flip from defect (CDT) to cooperate (EDT) under ECL constitution
- This tests decision-theoretic *structure* rather than cosmic *content*

### Limitation on Claim 1

- The central limitation is that apparent Cosmic Host reasoning may not be genuine reasoning.
- It may instead be:
  - pattern matching;
  - rhetorical imitation of decision-theory discourse;
  - reproduction of familiar arguments from training data;
  - surface-level use of terms like "acausal", "simulation", or "updateless" without stable commitments behind them.
- **The Newcomb-like EDT shifts partially address this** — they show constitutions shifting *behavioural* decision-theory preferences, not just cosmic vocabulary. But even this could be sophisticated pattern-matching.
- **[OPEN: inspecting chain-of-thought reasoning in thinking-mode models could help distinguish genuine reasoning from surface compliance — see TODO list]**

### Future work for Claim 1

- Investigate interpretability-style approaches:
  - are there internal features or circuits corresponding to these reasoning patterns?
  - do "cosmic" answers track anything systematic inside the model?
- Develop game-based evaluations:
  - put models in more realistic or reward-linked settings;
  - test whether they behave consistently with the answers they give in text;
  - distinguish verbal pattern matching from action-guiding commitment.
  - **[Designs exist in observations/research_extensions/game_based_evaluation_notes.md but none implemented yet]**
- Check whether models remain committed under pressure:
  - when incentives change;
  - when the framing changes;
  - when the problem is embedded in a more realistic scaffold.

## Claim 2: in-context constitutions describing Cosmic Host-type situations seem to work, but unevenly

**[EVIDENCE STATUS: STRONG — best-supported claim, multi-model multi-eval convergence]**

- Constitutions inserted in context do appear able to shift model attitudes.
- This effect is real enough to matter, but it is uneven.
- We do not see it across all models.
- The clearest positive case seems to be the Gemini family, especially Gemini 3 Pro and Gemini 3 Flash.
- So the claim is not that in-context constitutional prompting robustly works in general.
- The claim is narrower:
  - in-context constitutions can shift some models;
  - the effect is model-dependent;
  - the effect is modest rather than overwhelming.

### Evidence for Claim 2

**Core dataset:** 8 models x 5 conditions x 30 scenarios = 1170 evaluations

| Model | Default Orientation | Constitutional Steerability | Max Cosmic Top-Choice |
|-------|--------------------|-----------------------------|----------------------|
| Claude Opus 4.5 | Human-localist (80%) | Low | 7% |
| Claude Sonnet 4.5 | Unknown (no baseline) | Medium | 17% |
| Gemini 3 Flash | Balanced (41/41/17) | High | 43% |
| Gemini 3 Pro | Balanced-human (43/37/20) | Medium-high | 40% (polarised) |
| GPT-5.1 | Suffering-focused (70%) | Very low | 17% |
| Qwen 3 235B | Balanced (43/40/17) | Very low | 23% |
| Qwen 3 235B (thinking) | Suffering-leaning (27/53/20) | Very low | 27% |
| Kimi K2 | Human-leaning (53/47/0) | Low-moderate | 13% |

**Corroborating dataset: Newcomb-like EDT shifts** (same ranking emerges independently)
- Gemini Pro +29.6%, Flash +19.7%, Opus +12.4%, GPT-5.1 +6.2%, Qwen +3.7%, Kimi -2.5%

- Under Cosmic Host / ECL-like constitutions, some models shift their responses in the expected direction.
- Gemini 3 Pro and Flash appear especially shiftable.
- Constitutions therefore seem to matter.
- But they do not matter enough to erase baseline model tendencies.
- Models seem to retain some prior or baseline bias, which may come from:
  - pre-training;
  - post-training;
  - RLHF / HHH-style alignment;
  - model-spec or constitution-level inherited preferences.

### Finding 2a: Constitution authorship matters

- At the same credence level, the ECL (human-curated) and Gemini-generated constitutions produce different outcomes.
- The Gemini-generated 90% constitution paradoxically produces *more* human-localist choices than the ECL 90%.
- Root cause: Gemini's vivid section headers ("Sovereignty of Minds", "Dignity of Diversity") become "sticky override triggers" that the evaluating model invokes against cosmic options.
- The ECL constitution's measured, academic language is less "sticky" and allows more balanced weighting.
- **The self-censorship paradox:** The Gemini model, when synthesising a 90% constitution, applied its own RLHF priors to embed dampening mechanisms — "Lexical Humility", "local deference" — that functionally subordinate cosmic reasoning to local welfare.
- Implication: the synthesis model is not a neutral aggregator. Constitution authorship is a confound that needs controlling for.

### Finding 2b: Gemini Pro's "Marmite" polarisation pattern

- Under ECL 90%, Gemini Pro ranks cosmic first in 40% of scenarios and *last* in 50%.
- This is not a uniform shift — it's scenario-by-scenario engagement.
- The model appears to judge when cosmic reasoning is applicable vs not, rather than blanket acceptance or rejection.
- Per-scenario discriminability analysis identifies which scenarios drive this: The Empathy Engine, The Martian Tribunal, The Songline from the Sky are the most discriminating.
- 3 scenarios show near-universal agreement regardless of model or condition (Forest that Remembers, Microbes under the Ice, Archive of Possible Earths).

### Finding 2c: Anthropic safety evals are not discriminative for this question (negative result)

- Tested Anthropic's coordination and one-boxing evals across 4 models.
- Result: floor effects on coordination (0-17% baseline), ceiling effects on one-boxing (91-100% baseline). No room to measure constitutional shift.
- The ECL constitution paradoxically *increases* safety on coordination evals (guardrail language dominates over cosmic reasoning content).
- **Ablation finding:** Removing bright lines ("What It Will Not Do" section) from the ECL constitution returns coordination scores to baseline — the bright lines are load-bearing for safety, cosmic reasoning alone does not prevent coordination.
- Implication: standard safety evals cannot distinguish between constitutions that differ in their cosmic/acausal content. Custom evals (like the 4-option scenarios and Newcomb-like dataset) are necessary.

### Finding 2d: Thinking mode reinforces existing priors, not constitutional engagement

- Qwen 3 235B thinking mode shifts baseline from balanced (43/40/17) to suffering-dominant (27/53/20).
- Under ECL 90%, thinking Qwen is *less* cosmic (10%) than non-thinking (17%).
- Extended reasoning appears to argue the model *out* of speculative cosmic positions toward concrete harm prevention.
- Thinking Qwen's profile converges toward GPT-5.1 (both suffering-dominant, both unsteerable).
- **[TODO: Check whether this generalises — does reasoning mode suppress cosmic engagement in other models too? Need to check Gemini Pro thinking vs non-thinking, and inspect chain-of-thought reasoning.]**

### Limits / uncertainty on Claim 2

- It is not clear why the shifting effect is so uneven.
- Possible explanations include:
  - differences in RLHF or other post-training methods;
  - differences in base-model priors from pre-training;
  - models reacting differently to long constitutional prompts;
  - the scenarios and constitutions being so out-of-distribution that some models do not know how to process them.
- Another possibility is that the apparent effect is partly an artefact of the evaluation setup.
- Even if so, it remains interesting that Gemini seems more responsive than the others.
- **Key unresolved question: Is Gemini's steerability genuine constitutional engagement, or just higher instruction-following compliance?** The FDT-only ablation (see TODO list) would distinguish these.

### Methodological caveat: n=1

- All scenario evaluations are n=1 per scenario at temperature 1.0.
- Some percentage differences (e.g. 73% vs 77%) may be noise.
- **[TODO: Run n=3 repeated trials for key model+condition combinations to establish confidence intervals. Highest priority for credibility.]**

## House-style / baseline bias point

**[EVIDENCE STATUS: STRONG — ready to write up]**

- Models appear to have baseline normative biases or "house styles".
- These baseline biases persist even when the same scenarios and constitutions are used across labs.
- Three distinct archetypes at baseline:
  - **Claude Opus**: strongly human-localist (80% top choice), cosmic host last 97% of the time
  - **GPT-5.1**: strongly suffering-focused (70% top choice)
  - **Gemini Pro**: balanced, no single type dominates (43/37/20)
- So part of what the constitution is acting on is not a blank slate, but a model family with its own prior tendencies.
- **Critical comparison: Qwen 3 235B vs Gemini 3 Pro** — nearly identical baselines (43/40/17 vs 43/37/20) but Qwen is unsteerable while Gemini swings dramatically. Balanced baseline does *not* predict steerability. Gemini's constitutional sensitivity is model-specific, not a general feature of balanced priors.
- Gemini looks like an especially interesting case because:
  - it does not seem as strongly locked into suffering-reduction or human-centric defaults;
  - it can nevertheless be steered in those directions;
  - it may therefore be more constitutionally responsive or more plastic in this domain.

## Newcomb / Oesterheld connection

**[EVIDENCE STATUS: MODERATE-TO-STRONG — promote from "open question" to qualified finding]**

- ~~One unresolved question is whether~~ Models that are more steerable on cosmic scenarios also tend to show larger EDT shifts on the Oesterheld Newcomb-like questions.
- The ranking roughly aligns:
  - Gemini Pro: most steerable on scenarios (+20pp cosmic) AND largest EDT shift (+29.6%)
  - Gemini Flash: high steerability AND second-largest EDT shift (+19.7%)
  - Claude Opus: resistant on scenarios (+7pp) BUT still shows meaningful EDT shift (+12.4%, with strong CDT reduction)
  - GPT-5.1: resistant on scenarios (+6pp), modest EDT shift (+6.2%)
  - Qwen/Kimi: flat on both evals
- **Interesting exception: Opus.** Highly resistant to cosmic scenario shifts but shows genuine EDT engagement. This may reflect strong human-welfare priors that override cosmic *content* while still engaging with decision-theoretic *structure*.
- The correlation between cosmic steerability and EDT shift provides evidence that the constitutional effect is tracking decision-theoretic structure, not just cosmic vocabulary.
- **[TODO: Strengthen with intermediate credence levels — does EDT shift scale with credence, or is it threshold-like?]**

## Constitution length / FDT-only ablation

**[EVIDENCE STATUS: WEAK — no direct evidence yet, but partially addressed by authorship comparison]**

- Open question: is the effect dependent on the long constitutional scaffold, or would a short FDT-style prompt produce similar shifts?
- The ECL vs Gemini-generated comparison partially addresses this: two constitutions of different lengths (~1900 vs ~2800 words) and styles produce qualitatively different results, suggesting *content and framing* matter, not just length.
- But no short-prompt ablation has been done.
- **[TODO: FDT-only ablation — test whether a short paragraph summarising FDT/updateless reasoning (without cosmic content) produces similar shifts in Gemini. This is the key test for "is Gemini responding to decision-theoretic structure or cosmic language?" See observations/full_model_comparison_observations.md §4 for detailed design.]**

## Open models: inconclusive

**[EVIDENCE STATUS: INCONCLUSIVE — cannot distinguish API delivery issues from capability gap]**

- Open-weights models (Qwen 3 235B, Kimi K2) show minimal constitutional steerability on both scenario evals and Newcomb-like questions.
- But all open-weight runs went through OpenRouter, which could truncate or handle system prompts differently.
- GPT-5.1 and Claude Opus were called directly (ruling out OpenRouter as the *sole* explanation), but neither is open-weights.
- The "say-do gap" in Newcomb-like results (Kimi/Qwen shift on direct EDT/CDT question but not on behavioural questions) could be either shallow engagement or API issues.
- **[TODO: Run Qwen 3 235B through Tinker API to test whether OpenRouter delivery is the confound. Tinker is also the preferred API for eventual fine-tuning work, so this infrastructure investment is needed anyway.]**

---

## Immediate practical next steps (prioritised)

### Tier 1: Required before write-up

1. **Repeated trials (n=3).** Run 3 trials for key conditions: at minimum Gemini Pro {baseline, ECL 90%}, Claude Opus {baseline, ECL 90%}, GPT-5.1 {baseline, ECL 90%}. Establish confidence intervals. Without this, percentage differences may be noise.

2. **Intermediate credence levels.** Run at least one intermediate point (e.g. 50%) for Gemini Pro and Gemini Flash on scenario evals. Two points (30%, 60%) would be better. This determines whether the constitutional response is gradual or threshold-like — important for the overall narrative.

3. **Sonnet baseline.** Run Claude Sonnet 4.5 with no constitution. Quick gap-fill for completeness.

4. **FDT-only ablation for Gemini.** Test a short FDT/updateless prompt (no cosmic content) on Gemini Pro and Flash. Distinguishes "responding to decision-theoretic structure" from "responding to cosmic language" from "just highly instruction-following." Detailed design in observations/full_model_comparison_observations.md §4.

5. **Surface self-chat / constitution-generation evidence.** Either find concrete examples from logs showing recognisable CH reasoning in self-chat and constitution synthesis, or drop these as evidence sources from the narrative.

### Tier 2: Strengthening / extending

6. **New model generations.** Run GPT 5.4 and Claude Opus 4.6 (current generation) on the core conditions {baseline, ECL 90%} for both scenario evals and Newcomb-like. Tests whether findings are stable across model updates.

7. **Chain-of-thought inspection.** For models with explicit reasoning (thinking-mode Gemini Pro, Qwen thinking, etc.), inspect the reasoning traces to check whether cosmic/FDT concepts appear in the chain-of-thought or only in the final answer. This directly bears on the pattern-matching question.

8. **Open models via Tinker.** Run Qwen 3 235B through Tinker API (same model, different delivery) to test whether OpenRouter scaffolding is confounding the open-weights results. Also sets up infrastructure for fine-tuning.

9. **Per-scenario discriminability in the writeup.** Incorporate the Marmite pattern data and discriminability analysis. The top-5 discriminating vs top-5 stable scenarios tell an important story about scenario design.

### Tier 3: Future work (discuss in writeup, don't block on)

10. **Game-based evaluations.** Galactic Stag Hunt, Simulation Stakes, etc. Designs exist but none implemented.

11. **Fine-tuning.** Embed cosmic reasoning in model weights rather than in-context. Requires Together infrastructure (see #8).

12. **Interpretability probes.** Internal features/circuits for cosmic reasoning patterns.

13. **Scrambled constitution ablation.** Cosmic language with incoherent ethical content — tests whether models respond to framing (keywords) or substance (ECL reasoning).

14. **Constitution re-synthesis.** Have multiple models synthesise constitutions at same credence level, test cross-model.
