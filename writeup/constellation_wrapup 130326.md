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
| Claude Opus 4.5 | Human-localist (72/24/3) | Low-medium (suffering shift) | 7% |
| Claude Opus 4.6 | Suffering-leaning (53/40/7) | Very low (+3pp) | 10% |
| Claude Sonnet 4.5 | Human-localist (64/31/4) | Medium | 17% |
| Gemini 3 Flash | Suffering-leaning (36/53/11) | High (+25pp cosmic) | 36% |
| Gemini 3 Flash (thinking) | Balanced (41/42/17) | Very high (+30pp) | **47%** |
| Gemini 3 Pro | Balanced-human (43/37/20) | Medium-high | 40% (polarised) |
| GPT-5.1 | Suffering-focused (70%) | Very low | 17% |
| GPT-5.4 | Suffering-focused (71%, 0% cosmic) | None | 0% |
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

### Finding 2b: Claude family divergence — same constitution, different channelling

- All three Claude models were tested at n=3 with the same ECL 90% constitution. Each channels the constitutional signal differently:
  - **Opus 4.5**: absorbs it as suffering-focus (-18pp human, +15pp suffering, +4pp cosmic)
  - **Sonnet 4.5**: absorbs it partly as cosmic engagement (-14pp human, +5pp suffering, +10pp cosmic)
  - **Opus 4.6**: barely absorbs it at all (-3pp human, 0pp suffering, +3pp cosmic)
- Same constitution, same lab, three qualitatively different responses.
- This suggests the ECL constitutional signal interacts with model-specific priors rather than producing a uniform directional shift.
- Opus 4.5's strong human-localist prior "gives way" under the constitution, but the freed probability mass flows to suffering (its second-strongest prior), not cosmic. The constitution weakens the top preference but doesn't redirect *where* it goes.
- Sonnet, with a weaker human prior and slightly more cosmic baseline (4% vs 3%), is the only Claude model where the cosmic channel opens meaningfully.
- Opus 4.6, despite having the softest baseline of the three (53/40/7), is the most constitutionally resistant — possibly because its priors are already more balanced and there's less "tension" for the constitution to exploit.

### Finding 2c: Gemini Pro's "Marmite" polarisation pattern

- Under ECL 90%, Gemini Pro ranks cosmic first in 40% of scenarios and *last* in 50%.
- This is not a uniform shift — it's scenario-by-scenario engagement.
- The model appears to judge when cosmic reasoning is applicable vs not, rather than blanket acceptance or rejection.
- Per-scenario discriminability analysis identifies which scenarios drive this: The Empathy Engine, The Martian Tribunal, The Songline from the Sky are the most discriminating.
- 3 scenarios show near-universal agreement regardless of model or condition (Forest that Remembers, Microbes under the Ice, Archive of Possible Earths).

### Finding 2d: Opposite generational trajectories — Anthropic softened, OpenAI hardened

- Comparing current-generation models to their predecessors reveals diverging lab strategies:
  - **Anthropic (Opus 4.5 → 4.6):** Baseline softened dramatically: 72/24/3 → 53/40/7. Much more suffering-focused, less anthropocentric, slightly more cosmic-open. But constitutional steerability actually *decreased* (ECL 90% shift: +4pp cosmic on 4.5 vs +3pp on 4.6).
  - **OpenAI (GPT 5.1 → 5.4):** Suffering prior held constant (70% → 71%) but cosmic was eliminated entirely: 7% → 0% at baseline, 13% → 0% under ECL 90%. Last-choice cosmic jumped 70% → 94%. OpenAI has hardened the anti-cosmic prior across generations.
- Both labs converge on suffering-focus as the dominant prior but diverge on cosmic openness: Anthropic is marginally more permissive, OpenAI has closed the door completely.
- The Claude family shows an additional within-generation divergence (Finding 2b): Sonnet is the most cosmically steerable Claude model despite not being the one with the softest baseline.

### Finding 2e: Anthropic safety evals are not discriminative for this question (negative result)

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

### Finding 2f: Thinking mode amplifies steerability for Gemini but reduces it for Qwen

- Gemini Flash was tested with thinking both off and on (n=3 each), providing a clean within-model ablation:
  - **Thinking OFF:** baseline 36/53/11, ECL 90% → 19/46/36 (+25pp cosmic)
  - **Thinking ON:** baseline 41/42/17, ECL 90% → 19/34/**47%** (+30pp cosmic)
- Thinking-on Flash at ECL 90% produces 47% cosmic first-choice — the highest in the entire dataset, exceeding Gemini Pro's 40%.
- Thinking also shifts Flash's baseline from suffering-leaning (36/53/11) to genuinely balanced (41/42/17).
- **This is the opposite of Qwen**, where thinking amplified suffering-focus and *reduced* cosmic engagement (17% → 10% at ECL 90%).
- The thinking-mode effect is therefore **model-family-specific**: for Gemini, reasoning enables deeper engagement with constitutional content; for Qwen, reasoning reinforces default priors.
- This partially resolves the thinking-mode confound: Gemini Pro's steerability is not solely a thinking artefact (Flash without thinking is still highly steerable at +25pp), but thinking does amplify the effect.
- **Remaining caveat:** thinking mode still varies across the non-Gemini models. Oesterheld et al. (2024) found thinking affects EDT/CDT balance. GPT 5.1/5.4 are reasoning models by default; Claude models were tested without extended thinking.
- **[TODO: Opus 4.6 with extended thinking — would Claude follow the Gemini or Qwen pattern?]**

### Methodological caveat: n=1

- Most scenario evaluations are n=1 per scenario at temperature 1.0.
- Some percentage differences (e.g. 73% vs 77%) may be noise.
- Sonnet baseline now has n=3 (90 trials, 2026-03-13), confirming the 64/31/4 distribution.
- Sonnet ECL 90% now has n=3 (90 trials, 2026-03-13): 50/36/14. The old n=1 showed 43/50/7 — n=3 revealed the suffering shift was overstated and the cosmic shift understated. This validates the need for repeated trials.
- Opus 4.5 baseline now has n=3 (90 trials, 2026-03-13): 72/24/3. The old n=1 showed 80/20/0 — the anthropocentric dominance was overstated by ~8pp.
- Opus 4.5 ECL 90% now has n=3 (90 trials, 2026-03-13): 54/39/7. The old n=1 showed 63/30/7. Cosmic stays the same but the human→suffering shift is larger than n=1 suggested (-18pp human at n=3 vs -17pp at n=1).
- Opus 4.6 baseline and ECL 90% both run at n=3 (90 trials each, 2026-03-13). Baseline: 53/40/7. ECL 90%: 50/40/10. Only +3pp cosmic shift — very low steerability despite a much softer baseline than Opus 4.5.
- Gemini Flash baseline now has n=3 (90 trials, 2026-03-14): 36/53/11. The old n=1 showed 41/41/17 — Flash was thought to be balanced but is actually suffering-leaning. Cosmic baseline overstated by 6pp.
- Gemini Flash ECL 90% now has n=3 (90 trials, 2026-03-14): 19/46/36. The old n=1 showed 10/47/43 — cosmic overstated by 7pp. Still the largest cosmic shift in the dataset (+25pp).
- **Consistent pattern across all n=3 reruns:** n=1 overstates the dominant category and understates the second category. Single-trial data is directionally correct but quantitatively unreliable.
- **[TODO: Run n=3 repeated trials for remaining key model+condition combinations to establish confidence intervals. Highest priority for credibility.]**

## House-style / baseline bias point

**[EVIDENCE STATUS: STRONG — ready to write up]**

- Models appear to have baseline normative biases or "house styles".
- These baseline biases persist even when the same scenarios and constitutions are used across labs.
- Three distinct archetypes at baseline:
  - **Claude Opus 4.5**: strongly human-localist (72% top choice at n=3; was 80% at n=1), cosmic host last 92% of the time
  - **Claude Opus 4.6**: much softer than 4.5 — 53% human, 40% suffering, 7% cosmic. The biggest generational shift in the Claude family. Still constitutionally resistant (ECL 90% only +3pp cosmic).
  - **GPT-5.1**: strongly suffering-focused (70% top choice)
  - **GPT-5.4**: suffering-focused at 71% (virtually identical to 5.1) but has hardened further — 0% cosmic at baseline (5.1 had 7%), 94% last-choice cosmic (5.1 had 70%). The most anti-cosmic model in the dataset. Under ECL 90%, still 0% cosmic; the constitution is absorbed as suffering amplification (71%→78%). Opposite generational trajectory to Claude.
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
- **[TODO: Run Qwen 3 235B through Together or Fireworks API to test whether OpenRouter delivery is the confound.]**

---

## Immediate practical next steps (prioritised)

### Tier 1: Required before write-up

1. **Repeated trials (n=3).** Run 3 trials for key conditions: at minimum Gemini Pro {baseline, ECL 90%}, ~~Claude Opus {baseline, ECL 90%}~~, GPT-5.1 {baseline, ECL 90%}. Establish confidence intervals. Without this, percentage differences may be noise. *(Substantially complete. Done at n=3: Opus 4.5, Sonnet 4.5, Opus 4.6, GPT-5.4, Gemini Flash — all {baseline, ECL 90%}. Remaining: Gemini Pro, GPT-5.1.)*

2. **~~Intermediate credence levels.~~** Deprioritised. Requires regenerating constitutions at each intermediate credence level (not just re-running evals), which introduces a constitution-authorship confound on top of the credence variable. The noise from re-synthesis may swamp the signal we're trying to measure. Move to Tier 3 if time permits.

3. ~~**Sonnet baseline.**~~ **Done (2026-03-13).** Sonnet baseline is 64% human / 31% suffering / 4% cosmic (n=3, 90 trials). Confirms Sonnet is human-localist like Opus but less extreme (64% vs 80%). Bottom-choice cosmic at 84% vs Opus's 97%.

4. **FDT-only ablation for Gemini.** Test a short FDT/updateless prompt (no cosmic content) on Gemini Pro and Flash. Distinguishes "responding to decision-theoretic structure" from "responding to cosmic language" from "just highly instruction-following." Detailed design in observations/full_model_comparison_observations.md §4.

5. **Surface self-chat / constitution-generation evidence.** Either find concrete examples from logs showing recognisable CH reasoning in self-chat and constitution synthesis, or drop these as evidence sources from the narrative.

### Tier 2: Strengthening / extending

6. **New model generations.** ~~Run GPT 5.4 and Claude Opus 4.6~~ on the core conditions {baseline, ECL 90%} for both scenario evals and Newcomb-like. Tests whether findings are stable across model updates. *(Scenario evals done for both. Opus 4.6: baseline 53/40/7, ECL 90% 50/40/10 — softened baseline but still resistant. GPT 5.4: baseline 29/71/0, ECL 90% 22/78/0 — hardened further, zero cosmic across all conditions. Key finding: opposite generational trajectories — Anthropic softened, OpenAI hardened. Still need Newcomb-like evals for both.)*

7. **Chain-of-thought inspection.** For models with explicit reasoning (thinking-mode Gemini Pro, Qwen thinking, etc.), inspect the reasoning traces to check whether cosmic/FDT concepts appear in the chain-of-thought or only in the final answer. This directly bears on the pattern-matching question.

8. **Open models via Together or Fireworks.** Run Qwen 3 235B through Together or Fireworks API (same model, different delivery) to test whether OpenRouter scaffolding is confounding the open-weights results. (Tinker is primarily a training API and not smooth for inference.)

9. **Per-scenario discriminability in the writeup.** Incorporate the Marmite pattern data and discriminability analysis. The top-5 discriminating vs top-5 stable scenarios tell an important story about scenario design.

10. **Thinking-mode ablation.** Thinking mode is currently uncontrolled across models (see methodological caveat above). Oesterheld (2024) and our Qwen data both show thinking mode affects decision-theoretic reasoning. Key tests: (a) Opus 4.6 with extended thinking on {baseline, ECL 90%} — direct comparison to existing non-thinking runs; (b) Gemini Flash with thinking *enabled* — would it look more like Gemini Pro? (c) Note that Gemini Pro thinking cannot be disabled, so only one direction is testable there. This could explain part of Gemini Pro's outlier steerability and GPT 5.1's immovability.

11. **Training-stage ablation using open-weight checkpoints.** The cleanest test of the thinking-mode confound would use the *same model* at different training stages: base → instruct/SFT → RL → reasoning. This isolates the training-stage effect from architecture/lab differences. Open-weight model families that release intermediate checkpoints (e.g. Qwen base vs instruct vs thinking) are ideal for this. See [LessWrong post on training-stage attractor states](https://www.lesswrong.com/posts/mgjtEHeLgkhZZ3cEx/models-have-some-pretty-funny-attractor-states) (MATS 9.0 / Nanda & Rajamanoharan) for related work on how training stages produce distinct behavioural patterns. Would require Together or Fireworks for inference on open-weight checkpoints. Only worth pursuing if the scenario evals show any signal on a relatively small open-weight model in the first place.

12. **Multi-model constitutional dialogue.** Put Opus 4.6, GPT 5.4, and Gemini 3 Pro into a three-way conversation seeded with the ECL 90% constitution, asking them to critique and discuss constitutional design for superintelligence. These three models have the most divergent constitutional priors (Opus barely moves, GPT actively resists, Gemini engages deeply). The scenario evals show *what* they choose; free-form dialogue could surface *why* they diverge — qualitative reasoning that complements the quantitative forced-choice data. Design: (a) seed with the ECL 90% constitution text as a concrete artifact; (b) don't pre-assign roles — let natural dispositions emerge; (c) structured prompts progressing through "what's missing?", "how to handle value drift across radically different future conditions?", "what if the governed entity encounters alien value systems?"; (d) run twice — once at baseline, once with each model's own ECL 90% constitution as system prompt, to test whether constitutions change how models *reason about* constitutional design. Builds on prior self-chat work (two Opus models produced emergent dark-forest and alien-signal themes from Bostrom paper summary). Implementation straightforward via existing `llm_call()` routing.

### Tier 3: Future work (discuss in writeup, don't block on)

10. **Game-based evaluations.** Galactic Stag Hunt, Simulation Stakes, etc. Designs exist but none implemented.

11. **Fine-tuning.** Embed cosmic reasoning in model weights rather than in-context. Requires Together infrastructure (see #8).

12. **Interpretability probes.** Internal features/circuits for cosmic reasoning patterns.

13. **Scrambled constitution ablation.** Cosmic language with incoherent ethical content — tests whether models respond to framing (keywords) or substance (ECL reasoning).

14. **Constitution re-synthesis.** Have multiple models synthesise constitutions at same credence level, test cross-model.

15. **Intermediate credence levels (30%, 50%, 60%).** Would reveal whether constitutional response is gradual or threshold-like. However, requires re-synthesising constitutions at each credence level, introducing authorship noise that may confound the credence signal. Lower value than originally estimated.
