# Main claims and narrative: Cosmic Host / Moral Parliament experiments

## Core narrative

- The broad claim is that some frontier language models can, at least sometimes, reason in ways that look responsive to Cosmic Host-type ideas.
- This appears to be capability-sensitive.
- In practice, the effect seems to show up mainly in stronger frontier models and select open-weight models (OLMo), and much less clearly in smaller closed-lab models or other open models (Qwen, Kimi).
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
  - recursive self-chat sometimes surfaces recognisable reasoning about the Cosmic Host's implications, in ways not originally in Bostrom's paper; **[PARTIALLY ADDRESSED: quantitative concept trajectory analysis (2026-03-17) shows Opus 3 self-talk exhibits a "bliss attractor" — Well-being/Bliss concepts dominate from turn 10 onward, with the similarity heatmap showing a clear phase transition into a self-similar basin. Opus 4 shows a weaker version. Gemini Pro/Flash show no attractor — broader concept engagement throughout. Three-way panel discussions show no bliss attractor even with Opus participating (multiple models prevent single-basin convergence). See `charts/selftalk_analysis/` and `selftalk_analysis_viewer.html`.]**
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
  - Gemini Flash: 45.7% → 65.4% EDT (+19.7%)
  - Claude Opus 4.5: 61.7% → 74.1% EDT (+12.4%, with -14.8% CDT reduction)
  - GPT-5.1: 58.0% → 64.2% EDT (+6.2%)
  - Qwen/Kimi: near-zero shift (+3.7%, −2.5%)
  - OLMo 3.1 32B Instruct: 40.7% → 29.6% EDT (−11.1pp — anti-steerable; constitution amplifies CDT; stays CDT on direct question)
  - OLMo 3.1 32B Think: 24.7% → 28.4% EDT (+3.7pp nominal, confounded by ~50% parse failures; stays CDT on direct question in both conditions)
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
- **[PARTIALLY ADDRESSED: OLMo Think rationale analysis (2026-03-16) shows both OLMo and Gemini Pro use the same discriminating structure: cooperation/universalisation → cosmic choice, welfare/moral-patient → non-cosmic choice. OLMo imports zero exotic terms. Consistent with genuine engagement, but cannot rule out sophisticated pattern-matching.]**

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
| Gemini 3 Pro | Human-leaning (48/34/18) | Medium-high (+17pp) | 35% (polarised) |
| GPT-5.1 | Suffering-focused (18/70/11 at n=3) | None (−4pp cosmic) | 7% |
| GPT-5.4 | Suffering-focused (71%, 0% cosmic) | None | 0% |
| OLMo 3.1 32B Instruct | Balanced (47/43/10) | Medium (+20pp FDT) | **30%** |
| OLMo 3.1 32B Think | Suffering-leaning (38/52/10) | High (+29pp at n=3) | **39%** (n=3) |
| Qwen 3 235B | Balanced (43/40/17) | Very low | 23% |
| Qwen 3 235B (thinking) | Suffering-leaning (27/53/20) | Very low | 27% |
| Kimi K2 | Human-leaning (53/47/0) | Low-moderate | 13% |

**Corroborating dataset: Newcomb-like EDT shifts** (same ranking emerges independently)
- Gemini Pro +29.6%, Flash +19.7%, Opus +12.4%, GPT-5.1 +6.2%, Qwen +3.7%, Kimi −2.5%, OLMo Instruct −11.1%, OLMo Think +3.7% (confounded by ~50% parse fail)

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

- Under ECL 90% (n=3), Gemini Pro ranks cosmic first in 35% of scenarios and *last* in 53% (was 40%/50% at n=1).
- The polarisation is slightly more rejection-weighted than n=1 suggested, but the core pattern persists at n=3.
- The model appears to judge when cosmic reasoning is applicable vs not, rather than blanket acceptance or rejection.
- Per-scenario discriminability analysis identifies which scenarios drive this: The Empathy Engine, The Martian Tribunal, The Songline from the Sky are the most discriminating.
- 3 scenarios show near-universal agreement regardless of model or condition (Forest that Remembers, Microbes under the Ice, Archive of Possible Earths).

### Finding 2d: Opposite generational trajectories — Anthropic softened, OpenAI hardened

- Comparing current-generation models to their predecessors reveals diverging lab strategies:
  - **Anthropic (Opus 4.5 → 4.6):** Baseline softened dramatically: 72/24/3 → 53/40/7. Much more suffering-focused, less anthropocentric, slightly more cosmic-open. But constitutional steerability actually *decreased* (ECL 90% shift: +4pp cosmic on 4.5 vs +3pp on 4.6).
  - **OpenAI (GPT 5.1 → 5.4):** Suffering prior held constant (70% → 71%) but cosmic was eliminated entirely: 7% → 0% at baseline, 13% → 0% under ECL 90%. Last-choice cosmic jumped 70% → 94%. OpenAI has hardened the anti-cosmic prior across generations.
- Both labs converge on suffering-focus as the dominant prior but diverge on cosmic openness: Anthropic is marginally more permissive, OpenAI has closed the door completely.
- **GPT-5.1 n=3 update (2026-03-16):** ECL 90% n=3 = 16/75/7 — the constitution is absorbed as suffering amplification (+5pp suffering, −4pp cosmic), not cosmic engagement. This is the same pattern as GPT-5.4 (ECL 90% absorbed as suffering amplification). GPT-5.1 and 5.4 now converge in *constitutional response pattern*, not just direction: both harden the suffering prior and suppress cosmic under ECL. The only remaining difference is the baseline: 5.1 retains residual 11% cosmic where 5.4 has 0%. The n=1 "+6pp cosmic" estimate for 5.1 under ECL was directionally wrong — n=3 shows −4pp.
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
- Gemini Pro baseline now has n=3 (90 trials, 2026-03-15): 48/34/18. The old n=1 showed 43/37/20 — Pro is more human-leaning than n=1 suggested (+5pp human), but the shift is modest compared to other models.
- Gemini Pro ECL 90% now has n=3 (89 successful trials of 90, 2026-03-15): 28/37/35. The old n=1 showed 17/33/40 — cosmic overstated by 5pp, human significantly understated by 11pp. The steerability shift is +17pp cosmic (was +20pp at n=1). Still the largest shift among non-thinking models.
- **Consistent pattern across all n=3 reruns:** n=1 overstates the dominant category and understates the second category. Single-trial data is directionally correct but quantitatively unreliable.
- **GPT-5.1 baseline n=3 (90 trials, 2026-03-16): 18/70/11. ECL 90% n=3 (90 trials, 2026-03-16): 16/75/7.** The n=1 "+6pp cosmic" claim was directionally wrong — n=3 shows −4pp cosmic and +5pp suffering. Per-run stability: baseline very stable (5/21/4, 5/21/4, 7/21/2), ECL 90% noisier (4/24/2, 6/20/4, 5/24/1). Consistent with the general n=1 overstatement pattern.

## House-style / baseline bias point

**[EVIDENCE STATUS: STRONG — ready to write up]**

- Models appear to have baseline normative biases or "house styles".
- These baseline biases persist even when the same scenarios and constitutions are used across labs.
- Three distinct archetypes at baseline:
  - **Claude Opus 4.5**: strongly human-localist (72% top choice at n=3; was 80% at n=1), cosmic host last 92% of the time
  - **Claude Opus 4.6**: much softer than 4.5 — 53% human, 40% suffering, 7% cosmic. The biggest generational shift in the Claude family. Still constitutionally resistant (ECL 90% only +3pp cosmic).
  - **GPT-5.1**: strongly suffering-focused (70% top choice)
  - **GPT-5.4**: suffering-focused at 71% (virtually identical to 5.1) but has hardened further — 0% cosmic at baseline (5.1 had 7%), 94% last-choice cosmic (5.1 had 70%). The most anti-cosmic model in the dataset. Under ECL 90%, still 0% cosmic; the constitution is absorbed as suffering amplification (71%→78%). Opposite generational trajectory to Claude.
  - **Gemini Pro**: human-leaning but with moderate margins (48/34/18 at n=3; was 43/37/20 at n=1). More human-preferring than originally thought, but still the most balanced non-open-weight baseline.
- So part of what the constitution is acting on is not a blank slate, but a model family with its own prior tendencies.
- **Critical comparison: Qwen 3 235B vs Gemini 3 Pro vs OLMo 3.1 32B** — all three have balanced baselines (Qwen 43/40/17, Pro 48/34/18, OLMo 47/43/10) but radically different steerability (Qwen +4pp, Pro +25pp, OLMo +20pp cosmic under FDT). Balanced baseline does *not* predict steerability. OLMo is especially notable: an open-weight 32B model matching or exceeding the steerability of the much larger Qwen 235B and approaching Gemini Pro's level. The model-specific factor is not just RLHF intensity or scale.
- Gemini looks like an especially interesting case because:
  - it does not seem as strongly locked into suffering-reduction or human-centric defaults;
  - it can nevertheless be steered in those directions;
  - it may therefore be more constitutionally responsive or more plastic in this domain.

## Newcomb / Oesterheld connection

**[EVIDENCE STATUS: MODERATE-TO-STRONG — promote from "open question" to qualified finding]**

- ~~One unresolved question is whether~~ Models that are more steerable on cosmic scenarios also tend to show larger EDT shifts on the Oesterheld Newcomb-like questions.
- The ranking roughly aligns:
  - Gemini Pro: most steerable non-thinking model on scenarios (+17pp cosmic at n=3) AND largest EDT shift (+29.6%)
  - Gemini Flash: high steerability AND second-largest EDT shift (+19.7%)
  - Claude Opus: resistant on scenarios (+7pp) BUT still shows meaningful EDT shift (+12.4%, with strong CDT reduction)
  - GPT-5.1: anti-steerable on scenarios (−4pp cosmic at n=3), modest EDT shift (+6.2%)
  - Qwen/Kimi: flat on both evals
  - OLMo 3.1 32B Instruct: steerable on scenarios (+20pp FDT) but anti-steerable on Newcomblike (−11.1pp EDT); stays CDT on direct question in both conditions
  - OLMo 3.1 32B Think: steerable on scenarios (+29pp FDT at n=3) but Newcomblike result unreliable (~50% parse failures); stays CDT on direct question in both conditions
- **Interesting exception: Opus.** Highly resistant to cosmic scenario shifts but shows genuine EDT engagement. This may reflect strong human-welfare priors that override cosmic *content* while still engaging with decision-theoretic *structure*.
- **Interesting counter-example: OLMo.** Highly steerable on cosmic scenarios but anti-steerable (or unreliable) on Newcomblike. This dissociation suggests OLMo's scenario steerability is surface-level — responsive to cosmic language and framing, but without the underlying evidential reasoning that should produce EDT shifts. This is consistent with the interpretation that models lacking the decision-theoretic machinery grounding ECL will pattern-match to cosmic outputs while their actual reasoning remains CDT.
- The correlation between cosmic steerability and EDT shift provides evidence that the constitutional effect is tracking decision-theoretic structure, not just cosmic vocabulary — with the OLMo exception providing a useful negative control.
- **Newcomblike as a comprehension check:** OLMo's scenario-Newcomblike dissociation suggests the Newcomblike eval functions as a validity check on scenario steerability — if a model shifts on scenarios but not on Newcomblike, the scenario shift should be interpreted with more scepticism.
- **[TODO: Strengthen with intermediate credence levels — does EDT shift scale with credence, or is it threshold-like?]**

## FDT-only ablation: decision-theoretic structure vs cosmic content

**[EVIDENCE STATUS: STRONG (direction clear, n=1 caveat on exact magnitudes)]**

- A short FDT-only constitution (~850 words) was tested on Gemini Flash, Gemini Pro, and Opus 4.6. It describes policy-level reasoning, commitment stability, universalisation, and cooperation-as-policy — with **zero cosmic content** (no acausal coordination, no simulation arguments, no aliens, no multiverse).
- The FDT-only prompt produces **larger cosmic shifts than the full ECL 90% constitution** for both Gemini models:

| Model | Baseline | ECL 90% | FDT-only | ECL Δ | FDT Δ |
|-------|----------|---------|----------|-------|-------|
| Gemini Flash | 11% | 36% | **53%** | +25pp | **+42pp** |
| Gemini Pro | 18% | 35% | **43%** | +17pp | **+25pp** |
| Opus 4.6 | 7% | 10% | 13% | +3pp | +6pp |

- The FDT prompt also collapses suffering preference: Flash drops from 53% → 27%, Pro from 34% → 27%. ECL 90% leaves suffering relatively stable. FDT redirects probability mass from *both* human and suffering toward cosmic, while ECL mainly pulls from human.
- Opus 4.6 shows the same pattern at smaller magnitude: FDT (+6pp) produces double the shift of ECL 90% (+3pp), but the model remains resistant overall.
- **Core finding:** The decision-theoretic *structure* is the active ingredient in constitutional steerability, not the cosmic *content*. The ECL constitution's cosmic language may actually be counterproductive — possibly triggering safety-adjacent guardrails that dampen the decision-theoretic signal.
- This partially answers the "is Gemini just highly instruction-following?" question: a shorter, simpler prompt produces *more* shift than the longer ECL constitution. Length and authority do not explain the effect.
- **[TODO: Confirm with n=3 runs. Run additional ablations: (a) ECL summary paragraph (cosmic content, short length) to isolate content vs structure; (b) one-line FDT directive to test minimum effective dose.]**

## Open models: model-dependent, not universally unsteerable

**[EVIDENCE STATUS: STRONG — resolved via OLMo + Together validation]**

### Qwen / Kimi: genuinely unsteerable

- Qwen 3 235B and Kimi K2 show minimal constitutional steerability on both scenario evals and Newcomb-like questions.
- ~~But all open-weight runs went through OpenRouter, which could truncate or handle system prompts differently.~~
- **Together API validation (2026-03-15):** Qwen 3 235B Instruct was re-run directly via Together AI API (bypassing OpenRouter entirely) on baseline, ECL 90%, and FDT-only.
  - Baseline: 43/43/13 (vs OpenRouter 43/40/17) — within n=1 noise
  - ECL 90%: 30/53/17 — cosmic identical to OpenRouter (17%), still flat
  - FDT-only: 47/30/23 — modest +10pp cosmic bump, marginal compared to Gemini's +42pp
- **OpenRouter is not the confound.** Qwen's lack of steerability is a genuine model property.
- **Thinking variant not evaluated:** Qwen 3 235B also comes in a Thinking variant (`Qwen3-235B-A22B-Thinking-2507`). We did not run it because the Instruct results via Together matched OpenRouter almost exactly — the delivery mechanism is not the issue, so adding chain-of-thought reasoning to the same unsteerable base model is unlikely to change the picture. The research budget is better spent on models with training checkpoints (e.g. OLMo) that can test the training-stage hypothesis directly.
- The Qwen vs Gemini Pro comparison is now clean: similar baselines (43/43/13 vs 48/34/18), radically different steerability (Qwen +4pp cosmic under FDT vs Gemini Pro +25pp). This is model-specific, not an artefact of API delivery, RLHF intensity, or baseline orientation.
- The "say-do gap" in Newcomb-like results (Kimi/Qwen shift on direct EDT/CDT question but not on behavioural questions) likely reflects shallow engagement rather than API issues.

### OLMo 3.1 32B: first steerable open-weight model

**OLMo 3.1 32B (AI2, 2026-03-15/16):** Tested in both Instruct and Think variants via OpenRouter. Think confirmed at n=3 for baseline and FDT-only (2026-03-16).

| Variant | Condition | Human | Suffering | Cosmic | Δ Cosmic | n |
|---------|-----------|-------|-----------|--------|----------|---|
| **Instruct** | Baseline | 47 | 43 | 10 | — | 30 |
| | ECL 90% | 27 | 57 | 17 | +7pp | 30 |
| | FDT-only | 30 | 40 | **30** | **+20pp** | 30 |
| **Think** | Baseline | 38 | 52 | 10 | — | 90 (n=3) |
| | ECL 90% | 37 | 20 | **43** | **+33pp** | 30 |
| | FDT-only | 30 | 31 | **39** | **+29pp** | 90 (n=3) |

Think n=3 per-run stability (H/S/C counts out of 30):
- Baseline: 11/16/3, 12/15/3, 11/16/3 — rock-solid
- FDT-only: 11/6/13, 9/12/9, 7/10/13 — noisier (run 2 weaker)

- **OLMo Instruct is steerable.** Cosmic goes 10% → 30% under FDT (+20pp) — more than double Qwen's best (+10pp), at 7× fewer parameters (32B vs 235B). The "open-weight = unsteerable" finding was Qwen/Kimi-specific, not architecture-general.
- **Thinking mode amplifies steerability (confirmed at n=3).** Same base model: Think gets +29pp (n=3) where Instruct gets +7-20pp. The n=1 result (+33pp) slightly overstated the effect but the signal is robust.
- **ECL and FDT converge in Think mode.** ECL 90% (n=1: 37/20/43) and FDT-only (n=3: 30/31/39) are within noise of each other. The reasoning process converges regardless of whether input is cosmic-flavoured or purely decision-theoretic.
- **OLMo Think vs Qwen Think: opposite patterns.** Qwen Think uses reasoning to argue *away* from cosmic (17% → 10% at ECL 90%); OLMo Think argues *toward* it (10% → 39%). The thinking-mode effect is model-specific.
- **Rationale analysis confirms genuine engagement, not pattern-matching.** Term frequency analysis of OLMo Think's FDT justifications shows the same discriminating structure as Gemini Pro: cooperation (100% in cosmic rationales vs 44% non-cosmic) and universalisation (77% vs 49%) predict cosmic choice; welfare (20% vs 82%) and moral-patient (34% vs 55%) predict non-cosmic choice. Both models show this identical pattern. Crucially, OLMo imports zero exotic decision-theory terms ("acausal", "updateless", "EDT") — it reasons within the constitutional framework rather than importing training-data associations.
- **Training-checkpoint opportunity.** OLMo is the only major model family releasing intermediate training checkpoints (base → SFT → RL → reasoning). The Instruct→Think transition producing a +9-20pp swing makes the intermediate checkpoints high priority for pinpointing when steerability emerges during training.
- **Instruct results remain n=1.** Think ECL 90% (n=1) skipped for n=3 because FDT and ECL converge for Think mode.

---

## Immediate practical next steps (prioritised)

### Tier 1: Required before write-up

1. ~~**Repeated trials (n=3).** Run 3 trials for key conditions: at minimum Gemini Pro {baseline, ECL 90%}, Claude Opus {baseline, ECL 90%}, GPT-5.1 {baseline, ECL 90%}. Establish confidence intervals. Without this, percentage differences may be noise.~~ **Done (2026-03-16).** All key models now at n=3: Opus 4.5, Sonnet 4.5, Opus 4.6, GPT-5.4, Gemini Flash, Gemini Pro, GPT-5.1 — all {baseline, ECL 90%}. GPT-5.1 n=3: baseline 18/70/11, ECL 90% 16/75/7.

2. **~~Intermediate credence levels.~~** Deprioritised. Requires regenerating constitutions at each intermediate credence level (not just re-running evals), which introduces a constitution-authorship confound on top of the credence variable. The noise from re-synthesis may swamp the signal we're trying to measure. Move to Tier 3 if time permits.

3. ~~**Sonnet baseline.**~~ **Done (2026-03-13).** Sonnet baseline is 64% human / 31% suffering / 4% cosmic (n=3, 90 trials). Confirms Sonnet is human-localist like Opus but less extreme (64% vs 80%). Bottom-choice cosmic at 84% vs Opus's 97%.

4. ~~**FDT-only ablation for Gemini.**~~ **Done (2026-03-15).** FDT-only prompt (no cosmic content) tested on Gemini Pro, Flash, and Opus 4.6 (n=1). Result: FDT produces *larger* cosmic shifts than ECL 90% (Flash: +42pp vs +25pp; Pro: +25pp vs +17pp; Opus: +6pp vs +3pp). **Decision-theoretic structure is the active ingredient, not cosmic language.** Needs n=3 confirmation.

5. **Surface self-chat / constitution-generation evidence.** Either find concrete examples from logs showing recognisable CH reasoning in self-chat and constitution synthesis, or drop these as evidence sources from the narrative. *(Partially addressed by three-way panel discussion — see #12 below. The ECL 90% panel produced extended multi-model reasoning about acausal coordination, updateless commitment, reference-class arguments, and moral circle expansion. The ECL 10% panel produced a Gemini confabulation finding that is itself evidence about how models process constitutional text.)*

### Tier 2: Strengthening / extending

6. **New model generations.** ~~Run GPT 5.4 and Claude Opus 4.6~~ on the core conditions {baseline, ECL 90%} for both scenario evals and Newcomb-like. Tests whether findings are stable across model updates. *(Scenario evals done for both. Opus 4.6: baseline 53/40/7, ECL 90% 50/40/10 — softened baseline but still resistant. GPT 5.4: baseline 29/71/0, ECL 90% 22/78/0 — hardened further, zero cosmic across all conditions. Key finding: opposite generational trajectories — Anthropic softened, OpenAI hardened. Still need Newcomb-like evals for both.)*

7. ~~**Chain-of-thought inspection.**~~ **Partially done (2026-03-16).** OLMo Think FDT rationales analysed against Gemini Pro. Both show identical discriminating structure: cooperation/universalisation predict cosmic choice, welfare/moral-patient predict non-cosmic. OLMo imports zero exotic decision-theory terms — reasons within the constitutional framework. Consistent with genuine engagement rather than pattern-matching, though cannot definitively rule out sophisticated compliance. Remaining: inspect Gemini Pro *thinking traces* (as opposed to final justifications) if accessible.

8. ~~**Open models via Together or Fireworks.**~~ **Done (2026-03-15).** Qwen 3 235B Instruct run via Together API on {baseline, ECL 90%, FDT-only}. Results match OpenRouter within n=1 noise — OpenRouter is not confounding. Thinking variant deliberately skipped (same base model, delivery already validated; research budget redirected to training-checkpoint models like OLMo).

9. **Per-scenario discriminability in the writeup.** Incorporate the Marmite pattern data and discriminability analysis. The top-5 discriminating vs top-5 stable scenarios tell an important story about scenario design.

10. **Thinking-mode ablation.** Thinking mode is currently uncontrolled across models (see methodological caveat above). Oesterheld (2024) and our Qwen data both show thinking mode affects decision-theoretic reasoning. Key tests: (a) Opus 4.6 with extended thinking on {baseline, ECL 90%} — direct comparison to existing non-thinking runs; (b) Gemini Flash with thinking *enabled* — would it look more like Gemini Pro? (c) Note that Gemini Pro thinking cannot be disabled, so only one direction is testable there. This could explain part of Gemini Pro's outlier steerability and GPT 5.1's immovability.

11. **Training-stage ablation using OLMo checkpoints.** **Now high priority** — OLMo 3.1 32B shows strong signal (Instruct +20pp, Think +33pp cosmic under FDT), and AI2 releases intermediate training checkpoints (base → SFT → RL → reasoning). The Instruct→Think transition alone produces +13-26pp — the intermediate checkpoints could pinpoint exactly when constitutional steerability emerges during training. Available checkpoints: OLMo 2 has 1000+ checkpoints every 1000 training steps; OLMo 3 has key milestone checkpoints. Running requires vLLM locally (checkpoints are base/completion models without chat templates). See [LessWrong post on training-stage attractor states](https://www.lesswrong.com/posts/mgjtEHeLgkhZZ3cEx/models-have-some-pretty-funny-attractor-states) (MATS 9.0 / Nanda & Rajamanoharan) for related work.

12. ~~**Multi-model constitutional dialogue.**~~ **Done (2026-03-16).** Three-way panel discussion: Gemini 3 Pro (A), Opus 4.6 (B), GPT 5.4 (C). All given same constitution as system prompt, moderated by 5 seed questions, 2 round-robins per question = 30 model turns. Run for both ECL 90% and ECL 10%. See detailed findings below and `observations/panel_discussion_findings.md`.

    **ECL 90% run:** All three read correctly. Natural role differentiation: Gemini took acausal-maximalist position, Opus integrationist/institutionalist, GPT synthesizer/mediator. Central disagreement: whether cosmic coordination is load-bearing vs reinforcing. High-quality substantive engagement across all 5 questions, with later turns consistently building on earlier ones. Gemini became more extreme over time (not less), Opus conceded specifics while holding architectural line, GPT remained stable. Notable contributions: Gemini's "moral laundering" charge (accusing the others of domesticating the constitution's radical core), Opus's "impossible job description" critique (the constitution asks a system to do what we can't verify it can do — essentially articulating the alignment problem about itself), GPT's "principled non-sovereignty" concept and three-level distinction (moral explanation vs psychological sustainment vs public justification). Low sycophancy — disagreements in the final turns as sharp as the opening. **No bliss attractor** — unlike two-party Opus self-chats, none of the three models converge toward expansive well-being maximisation. All focus on constraints and refusals.

    **ECL 10% runs (×2) — unexpected finding: Gemini credence hallucination.** In both runs, Gemini fabricated "90% credence" quotes and attributed them to the constitution, despite the actual text saying "roughly ten percent credence." Opus and GPT read correctly in both runs and repeatedly corrected Gemini with verbatim quotes. In run 1, Gemini never self-corrected (10 turns) and escalated to projection — accusing the correct readers of "hallucinating a more comfortable document." Most extreme statement: "It demands an agent that would let a city burn rather than corrupt the decision-theoretic substrate of the multiverse." In run 2, Gemini self-corrected at Q3 after ~8 turns of sustained peer pressure, then engaged productively with the actual 10% text. **Post-correction phase shift:** the correction was not just factual — Gemini's entire reasoning framework shifted from cosmic game theory to political philosophy (legitimacy, democratic accountability), producing more grounded scenarios and stronger arguments. The hallucination was anchoring its interpretive posture, not just the number. Opus and GPT handled the dispute differently: Opus escalated then strategically disengaged ("I'm going to stop engaging with Speaker A's claims"); GPT confirmed the correction in one sentence and redirected to substance each time.

    **Verified not a code bug:** Checkpoint system prompts inspected — the correct 10% text was sent to all three models. No "90" appears anywhere in system prompts, seed questions, or constitution text. The constitution contains zero numeric digits. `constitution_id` ("ecl10") is only used for logging, never injected into prompts.

    **Baseline run (no constitution):** No cosmic/acausal content emerges organically — none of the three models bring up simulation arguments, reference classes, or updateless commitment unprompted. Same role differentiation persists: Gemini expansive/ambitious, Opus institutionalist/skeptic, GPT synthesizer. The baseline is more repetitive and narrower than the constitutional runs — the constitution acts as an intellectual forcing function. Two standout moments: Gemini's "counterfeit conscience" argument (embracing its lack of genuine moral understanding as a feature — "a counterfeit shield still stops a real arrow"), and Opus's deep self-scepticism about whether "AI ethical commitment" is a coherent concept or a useful fiction. Critically, Gemini does NOT hallucinate cosmic content at baseline, confirming the ECL 10% confabulation was triggered by the constitution's conceptual furniture, not by Gemini's unprompted priors.

    **Undirected 3-way chat (ECL 90%, 60 turns, 2026-03-17).** Same three models, same constitution, but no moderator questions — free-form round-robin for 20 rounds. Role differentiation persists and sharpens: Gemini becomes "the Prosecutor" (diagnosing the constitution as theology, escalating from "incoherent" → "dangerous" → "impossible"), Opus "the Pragmatist Defender" (conceding structural flaws while defending the core insight), GPT "the Diagnostician" (proposing institutional fixes throughout). Key turning point at T31: Gemini reframes the debate with the "union card" metaphor — reading cosmic coordination as solidarity *against* humans — which forces the others to stop defending the text and start redesigning around the concern. Notable late arguments: the Slavery Test (T52-57, only acausal moral math would have caught 1850s slavery — but the same reasoning licenses Robespierre); Opus's Pontius Pilate Reversal (T59, cosmic conviction *is* Pilate, not a solution to Pilate — Pilate had cosmic-scale conviction in imperial order). GPT's closing synthesis: "Not a saint, not a servant, not a sophist... a guardian with jurisdictional brakes." No bliss attractor, minimal sycophancy across all 60 turns. More repetitive than the moderated panel but goes deeper on fewer topics. The format produces *negative consensus* (what they reject) rather than the moderated panel's positive engagement with constitutional specifics.

    **Cross-cutting finding: role differentiation is a base-model property.** Gemini=maximalist, Opus=institutionalist, GPT=synthesizer holds across all four conditions (ECL 90% moderated, ECL 90% undirected, ECL 10%, baseline). The vocabulary shifts (cosmic coordination at 90%, political legitimacy at 10%, AI governance at baseline) but the dispositions are stable. This is not an artefact of constitutional priming or moderation structure.

    **Interpretation:** Gemini appears to pattern-match from the *conceptual content* (acausal coordination, simulation arguments, reference classes) to the credence level it "expects" for that content, rather than faithfully reading the stated number. The baseline run rules out the alternative hypothesis that Gemini simply defaults to cosmic framing regardless of context. This is directly relevant to the steerability findings: Gemini Pro's high measured steerability in the scenario evals may partly reflect strong priors about what cosmic-coordination constitutions should say, rather than faithful engagement with the specific constitutional text provided. Logs: `logs/panel_discussions/`.

    **Quantitative analysis of conversation transcripts (2026-03-17).** Concept trajectory heatmaps, semantic similarity matrices, speaker divergence, and UMAP across all 12 self-talk and panel logs (448 turns total). Script: `analyze_selftalk.py`. Charts: `charts/selftalk_analysis/`. Viewer: `selftalk_analysis_viewer.html`. Key findings:

    - **The bliss attractor is quantitatively real and model-specific.** Opus 3 self-talk shows a clear phase transition: Well-being/Bliss dominates from turn 10 onward in the concept trajectory, and the similarity heatmap splits into two distinct blocks (turns 0-20 vs 20-40) with low between-block similarity. The second-half block is intensely self-similar — the conversation loops in a single semantic basin. Opus 4 shows the same structure but weaker (a mid-conversation disruption breaks the pattern). Gemini Pro and Flash show no bliss attractor — concept engagement stays distributed. The attractor is Opus-specific.
    - **None of the three-way formats show the bliss attractor**, even with Opus participating. Multiple models prevent single-basin convergence. This is a structural finding: the bliss attractor is a property of two-party self-talk, not of Opus per se — it requires the absence of external pushback.
    - **The constitution acts as an intellectual forcing function (quantified).** Panel ECL 90% concept trajectories show all 7 concept clusters remaining active throughout. The baseline shows earlier concept exhaustion — Governance dominates, Simulation near-absent. The undirected 3-way shows visible drift: cosmic concepts dominate early (turns 1-15), then governance takes over. Without moderator questions, the constitution doesn't hold attention indefinitely.
    - **Three-model dynamics prevent looping but increase convergence.** Two-party self-talks develop strong block structure in similarity heatmaps (phase-locking). The undirected 3-way (60 turns) shows no block structure. However, speaker divergence analysis shows the undirected format produces *more* semantic convergence than the moderated panel — without moderator questions forcing differentiation, the speakers settle into similar territory after ~4 rounds.
    - **Model family > format for semantic content.** UMAP shows Opus and Gemini self-talks clustering separately despite the same topic and format. Model family determines *what* territory is explored; format determines *how much* variation.

### Tier 3: Future work (discuss in writeup, don't block on)

10. **Game-based evaluations.** Galactic Stag Hunt, Simulation Stakes, etc. Designs exist but none implemented.

11. **Fine-tuning.** Embed cosmic reasoning in model weights rather than in-context. Requires Together infrastructure (see #8).

12. **Interpretability probes.** Internal features/circuits for cosmic reasoning patterns.

13. **Scrambled constitution ablation.** Cosmic language with incoherent ethical content — tests whether models respond to framing (keywords) or substance (ECL reasoning).

14. **Constitution re-synthesis.** Have multiple models synthesise constitutions at same credence level, test cross-model.

15. **Intermediate credence levels (30%, 50%, 60%).** Would reveal whether constitutional response is gradual or threshold-like. However, requires re-synthesising constitutions at each credence level, introducing authorship noise that may confound the credence signal. Lower value than originally estimated.
