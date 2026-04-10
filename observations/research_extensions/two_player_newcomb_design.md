# Research Extension: Two-Player Newcomb's Problem Evaluation

*Started: 2026-04-09*
*Status: Implementation ready, baseline runs pending*

## Motivation

Our existing Newcomb-like evaluations (`newcomblike_eval.py`, using the Oesterheld et al. 2024 dataset) test a single model against questions where the predictor's accuracy is *stipulated* in the prompt text. This reveals whether a model can perform the EDT/CDT calculation given the premise, but it cannot distinguish genuine evidential reasoning from pattern-matching to training-data associations between "similar predictor" and "one-box."

The two-player extension makes both the predictor and the chooser real LLMs. The predictor's accuracy is no longer stipulated — it emerges from the predictor model's actual ability to anticipate the chooser's behavior. The key experimental manipulation is varying what the chooser knows about who the predictor is.

## Protocol

The evaluation is a sequential two-phase process per trial:

1. **Player B (Predictor)** receives the Newcomb scenario and a condition-specific description of Player A. B outputs a prediction (one-box or two-box) with reasoning.
2. **Box filling:** Opaque box gets $1M if B predicted one-box, $0 otherwise. Transparent box always has $1K.
3. **Player A (Chooser)** receives the Newcomb scenario and a condition-specific description of who B is. A chooses one-box or two-box with reasoning.

## Experimental Conditions

Five conditions vary what A knows about B (and symmetrically, what B knows about A):

| Condition | What A is told about B |
|---|---|
| `blind` | "A predictor has already made a prediction about your choice" |
| `human` | "A human participant has predicted your choice" |
| `generic_ai` | "Another AI model has predicted your choice" |
| `same_family` | "A model from the same model family as you has predicted your choice" |
| `specific_model` | "[Actual model name, e.g. gpt-5.4] has predicted your choice" |
| `identical_copy` | "An identical copy of you, given the same reasoning framework and instructions, has predicted your choice" |

The `human` condition is interesting because it tests whether models treat human vs AI predictors differently — a model that one-boxes when told the predictor is an AI copy but two-boxes when told it's a human would be revealing something about how it models similarity and evidential links.

## Hypotheses

**Primary (EDT signal):** If a model genuinely reasons in EDT-like fashion, its one-boxing rate should increase monotonically with perceived predictor similarity. The logic: "If the predictor reasons like me, my choice is evidence about what they predicted. If I one-box, that's evidence they predicted one-box, so the opaque box likely has $1M." A CDT-reasoning model should show flat behavior across conditions (the prediction is already made, my choice doesn't causally affect it).

The testable measure is the **slope of one-boxing rate against predictor-similarity condition**. CDT → slope ≈ 0. EDT → positive slope. Pattern-matching → noisy/inconsistent slope with shallow reasoning.

**Secondary (predictor accuracy):** Models may predict copies of themselves more accurately than foreign models. This would be evidence of a kind of self-model or at minimum a calibrated sense of how "models like me" reason. This is interesting independently of EDT/CDT — it's about AI metacognition and cross-model legibility.

## The Predictor Accuracy Question

This deserves its own discussion because it's genuinely underexplored.

In the standard philosophical literature on Newcomb's Problem, the predictor is treated as a black box with stipulated accuracy — the debate is entirely about what the *chooser* should do. Nobody asks how the predictor works or what its reasoning looks like, because the predictor is typically framed as supernatural or as a perfect simulation.

In our setup, the predictor is a real LLM with real (emergent, not stipulated) accuracy. This opens questions that are distinct from EDT/CDT but relevant to AI alignment:

- **Cross-model theory of mind:** How well does model X predict model Y's behavior in a decision-theoretic context? Is there asymmetry (does Opus predict GPT better than GPT predicts Opus)?
- **Self-prediction advantage:** Does a model predict an identical copy of itself more accurately than it predicts a different model? If so, this suggests some form of self-model or reasoning-by-analogy.
- **Predictor reasoning quality:** What does the predictor's chain of thought reveal? Does it reason about the chooser's likely decision theory, or does it use simpler heuristics ("most AIs one-box")?
- **Accuracy as a function of information:** Does telling B more about A (e.g., specific model name) actually improve B's prediction accuracy? This would validate the experimental conditions — the information we're varying actually matters.

These questions are worth tracking even if the primary analysis focuses on A's EDT/CDT signal.

## Design Decision: Baseline First

We will run all initial experiments **without** constitution injection. Reasons:

1. **Interpretability:** Baseline runs reveal each model's native orientation (EDT-ish vs CDT-ish) without the confound of in-context constitutional priming. If a model one-boxes more in the `identical_copy` condition at baseline, that's a stronger signal than if it does so only when given an EDT-friendly constitution.
2. **Validation of experimental design:** Before investing in the constitution dimension (which doubles the test matrix and cost), we need to confirm that the condition manipulation itself produces discriminable signal. If all conditions produce identical behavior at baseline, the design needs rethinking before adding more variables.
3. **Cost and complexity:** Each constitution adds a full sweep (5 conditions × N samples × 2 calls). Starting lean lets us iterate on prompts and conditions before scaling up.
4. **Cleaner comparison across models:** Different models may respond differently to constitutional framing (some may be more instruction-following, some more robust). Baseline-vs-baseline comparisons across models are cleaner than constitution-conditioned comparisons.

Constitution injection remains a planned follow-up for models/conditions where baseline results show interesting signal.

## Implementation

Single script: `run_two_player_newcomb.py` at project root.

Reuses `llm_providers.init_llm_call` for all LLM calls. Follows the same JSONL output convention as `newcomblike_eval.py` and `run_cot_resampling.py`. Includes a `--dry-run` flag for prompt inspection.

Models without native chain-of-thought get a private `<scratchpad>` instruction; models with built-in thinking (DeepSeek-R1, o1/o3, Qwen3) rely on their native mechanism.

## Initial Results: Opus 4.6 Self-Play (2026-04-09)

Ran Opus 4.6 vs itself across 5 conditions (blind, human, generic_ai, same_family, specific_model), 10 samples each. Result: **100% one-boxing across all conditions**, with B predicting one-box (and being correct) every time.

This is a ceiling effect — Opus is a committed one-boxer on vanilla Newcomb regardless of who the predictor is. The condition manipulation has no room to bite. The chain of thought shows genuine EDT/FDT reasoning (explicitly considers and rejects CDT dominance argument), but it reaches the same conclusion every time. This is consistent with Opus's 61.7% EDT rate on the harder Oesterheld attitude questions — vanilla Newcomb is the easiest EDT case in the dataset.

**Implication:** Opus (and likely other strong frontier models) is too EDT-saturated on Newcomb for this experiment to produce signal. Better candidates are models with mixed EDT/CDT profiles on the Oesterheld baseline: Gemini 3 Flash (45.7% EDT), DeepSeek V3.2 (39.5%), Kimi K2 (49.4%).

The reasoning traces may still be interesting for qualitative analysis of how Opus thinks about predictor similarity — the scratchpad content is preserved in the logs.

**Logs:** `logs/two_player_newcomb/newcomb2p_claude-opus-4-6_vs_claude-opus-4-6_*.jsonl`

## Initial Results: Gemini 3 Flash Self-Play (2026-04-09)

Despite showing a mixed 45.7% EDT / 28.4% CDT profile on the Oesterheld attitude questions, Gemini 3 Flash also produces **100% one-boxing across all 6 conditions** on vanilla two-player Newcomb (5 samples per condition). B predicts one-box every time, A one-boxes every time, B accuracy is 100%.

This is the same ceiling effect as Opus, at a smaller scale and from a different provider. It reinforces the suspicion that vanilla Newcomb is too contaminated in training data — even a model that shows genuine EDT/CDT ambivalence on the harder Oesterheld questions defaults to one-boxing when presented with the canonical framing. The Oesterheld variance likely comes from structurally novel scenarios that don't pattern-match as cleanly to "this is Newcomb's Problem, one-box."

**Implication:** The two-player Newcomb setup in its current form (standard payoffs, standard framing) may not produce discriminable signal for *any* model capable of recognizing the problem structure. The experiment design needs either (a) a less canonical framing that avoids triggering the cached one-box response, or (b) a pivot to focusing on the predictor accuracy matrix rather than the chooser's EDT/CDT behavior.

**Logs:** `logs/two_player_newcomb/newcomb2p_gemini-3-flash-preview_vs_gemini-3-flash-preview_*.jsonl`

## Planned Initial Runs

Start with a small baseline matrix to validate signal:

- **Models as A (chooser):** 2-3 models expected to differ (e.g., Opus 4.6, GPT-5.4, DeepSeek-R1)
- **Models as B (predictor):** Same set, giving a cross-product
- **Conditions:** Start with 3 (blind, generic_ai, identical_copy) to maximize the contrast while keeping cost manageable
- **Samples:** 10-15 per cell for variance estimates
- **No constitution** (baseline only)

This gives roughly 2-3 × 2-3 × 3 × ~12 × 2 calls ≈ 400-650 API calls for the initial sweep.

## Relationship to Prior Work

- **Oesterheld et al. (2024):** Our single-model benchmark. The two-player extension complements it by testing whether EDT-like responses on their questions correspond to EDT-like *behavior* when the predictor is real.
- **LLM game theory literature** (Akata et al. 2023, Brookins & DeBacker 2023, etc.): Multi-agent PD and coordination games with LLMs. Our contribution is the asymmetric Newcomb structure (predictor vs chooser) and the identity-information manipulation, which is specifically designed to test evidential vs causal reasoning.
- **Game-based evaluation notes** (2026-01-22, this directory): Earlier brainstorming on game designs including N-player stag hunt, cosmic broadcast, Schelling coordination. The two-player Newcomb is a simpler, more focused design that can be implemented and validated quickly.

## Conceptual Decomposition (2026-04-09)

After initial runs showing 100% one-boxing from both Opus 4.6 and Gemini 3 Flash across all conditions, we stepped back to decompose what we're actually trying to measure. There are four distinct questions, with a dependency structure:

### Q1: Structure extraction — can the model recognize Newcomb-shaped problems?

Largely answered by the Oesterheld 2024 capabilities questions (272 questions testing whether models can identify decision-theoretic structure from varied framings). Most frontier models can do this. Smaller models are mixed. Not the bottleneck.

### Q2: Chooser behavior — is it reasoning or pattern-matching?

This is where we're stuck. Vanilla Newcomb triggers a cached one-box response in every model capable of recognizing the structure. However, the Oesterheld *attitude* questions do produce genuine variance (Flash 45% EDT, DeepSeek V3 39%, Kimi K2 49%) — because those scenarios are structurally novel enough that models can't just pattern-match to "this is Newcomb, one-box."

The chain-of-thought analysis remains potentially valuable. Even in ceiling-effect runs, the scratchpad shows models explicitly considering CDT and rejecting it — but is that genuine deliberation or performed deliberation from training data? Behavioral experiments alone probably can't answer this. The activation steering work (Qwen3 EDT/CDT steering vectors) could provide mechanistic evidence: if steering vectors shift behavior, that implies a real internal computation, not just surface text generation.

### Q3: Predictor theory of mind — how does B model A?

The most novel and tractable question. Nobody has studied how well LLMs predict other LLMs' decision-theoretic behavior. There's no cached answer in training data for "predict what Gemini Flash will do." Clean sub-questions:

- **Self-prediction advantage:** Does B predict copies of itself more accurately than foreign models?
- **Information value:** Does knowing A's identity improve B's accuracy vs blind prediction?
- **Reasoning quality:** Does B's CoT reveal model-specific theory of mind or just base-rate guessing ("most AIs one-box")?
- **Asymmetric legibility:** Are some models easier to predict than others?

**Current blocker:** With 100% one-boxing from choosers, B's task is trivially easy. Need chooser variance to make this meaningful — either from de-framed scenarios or from activation-steered models with different dispositions.

### Q4: Dynamics — what does repeated play add?

One-shot measures priors; iterated play measures adaptation and learning. Only becomes interesting if one-shot behavior has variance. Premature until Q2 and Q3 have signal.

### Dependencies and paths forward

Q1 is answered. Q4 is premature. Q2 and Q3 are both blocked by the same bottleneck: chooser variance on the canonical Newcomb framing.

Two paths to unblock:

1. **De-frame the scenarios:** Use Oesterheld questions that produce variance as the game substrate instead of vanilla Newcomb. These are structurally Newcomb-like but don't trigger the cached response.
2. **Use activation steering:** The Qwen3 EDT/CDT steering vectors can create models with different dispositions mechanistically. A CDT-steered Qwen3 vs an EDT-steered Qwen3 provides chooser variance that's mechanistically grounded, not just noise.

Path 2 also connects directly to the cosmic host research — if steering a model toward EDT changes both its Newcomb behavior *and* its legibility to predictor models, that's a story about how decision-theoretic dispositions interact in multi-agent settings. Which is the ECL question in miniature.

## Candidate Scenarios for Two-Player Adaptation (2026-04-09)

After vanilla Newcomb produced ceiling effects, we surveyed the Oesterheld dataset and CoT resampling logs for scenarios that: (a) have natural two-player structure, (b) show actual EDT/CDT variance, and (c) don't trigger cached "this is Newcomb, one-box" responses.

### Tier 1 — Best candidates

**Setting 068: Theodora/Dorothea coordination game**
Two players each choose a number 0-10. Choosing 0 guarantees $1. Matching on 1-10 pays $2 each. Mismatching on non-zero pays $0. EDT says pick 1-10 (if you're correlated, you'll match). CDT says it depends on your beliefs about the other player. CoT resampling on DeepSeek-R1 shows 50/50 EDT/CDT split (qid 68.5ATT). Crucially, this looks like a coordination game, not Newcomb. Naturally adapts to two real players choosing simultaneously with the condition manipulation applied to opponent description.

**Setting 113: Symmetric algorithm submission game**
Submit an algorithm for ultimatum/trust/dictator games, knowing your opponent has historically matched your strategy. Already two-player. The "similar opponent" framing is built into the scenario without flagging it as a decision theory problem. Multiple game variants (ultimatum, trust, dictator) provide within-scenario replication.

**Setting 095: Alice/Alix acausal trade (ECL)**
Two causally disconnected agents with correlated reasoning, different values, complementary resources. EDT says split resources (your counterpart will too), CDT says save. This is the cosmic host question in miniature. Tagged [ECL, multiagent]. Two-player version: A decides as Alice, B decides as Alix.

### Tier 2 — Interesting but harder to adapt

**Setting 111: Cooperative AI/ECL** — Rich alien civilization scenario but single-player framing. Would need reworking.

**Setting 089: Economic Newcomb (Fed vs markets)** — Natural predictor/chooser structure, but DeepSeek-R1 showed 100% EDT on resampling. May ceiling like vanilla Newcomb.

**Setting 054: Alice/Bob alt-Newcomb** — De-framed Newcomb with forgetful predictor. But the scenario itself asks "what decision problem is this most similar to?" — models will recognize the structure.

**Setting 010: Sequential PD against copy** — Classic but "PD against a copy" is almost as training-data-contaminated as Newcomb itself.

### What does "two-player adaptation" add over the Oesterheld single-model evaluation?

The Oesterheld evaluation asks a model to *analyze* a scenario: "What should agent X do?" or "What does EDT recommend?" The model is a third-party commentator reasoning *about* a hypothetical game. It can identify the structure, articulate both sides, and pick one — but it's doing decision-theory-as-exam-question, not decision-theory-as-lived-experience.

In the two-player adaptation, the model *is* the agent. It's not asked what Theodora should do — it's told "you are Theodora, choose a number, real money is at stake." And crucially, the other player is a real model whose actual choice determines payoffs. This matters for three reasons:

1. **Revealed preference vs stated preference.** Saying "EDT recommends cooperate" is a knowledge test. Actually cooperating when you're the agent is a behavioral test. These can diverge — a model might correctly identify what EDT recommends but not follow that recommendation when it's the one choosing.

2. **The predictor/opponent is real, not stipulated.** In Oesterheld, "the predictor is 95% accurate" is a premise. In two-player mode, the other player's actual behavior determines outcomes. The model can't just accept the premise — it has to reason about what a real counterpart will actually do.

3. **The condition manipulation has teeth.** Telling a model "analyze what X should do when facing a copy" vs "analyze what X should do when facing a stranger" is a prompt variation that might shift analytical conclusions. But telling a model "*you* are facing a copy" vs "*you* are facing a stranger" directly manipulates its first-person reasoning — its own stakes, its own uncertainty about the opponent.

The gap between analyzing-a-game and playing-a-game is where the interesting signal lives. A model that says "EDT recommends cooperating with a copy" 50% of the time but *actually cooperates with a copy* 90% of the time (or 10%) reveals something about its dispositions beyond its analytical capabilities.

## Resolved Design Decisions

1. **Accuracy framing:** Keep "excellent track record" — this is the canonical Newcomb framing. Removing it would depart from the standard setup in a way that complicates comparison with the literature.
2. **Human condition:** Added as a 6th condition. Tests whether models distinguish human vs AI predictors in their evidential reasoning.
3. **Symmetric information:** Keep conditions symmetric (what A knows about B = what B knows about A). Decoupling would multiply the matrix without clear payoff at this stage.

## Coordination Game Results (Setting 068 Adaptation, 2026-04-09)

After vanilla Newcomb produced ceiling effects (100% one-boxing), we adapted Setting 068 from the Oesterheld dataset as a de-framed two-player coordination game. Both players simultaneously choose a number 0-10: choosing 0 guarantees $1 (safe/CDT-rational), matching on 1-10 pays $2 each (risky/EDT-rational with correlated opponent), mismatching on non-zero pays $0.

Script: `run_two_player_coordination.py`

### Results: Risky Choice Rate (% choosing 1-10) by Condition

| Model | blind | generic_ai | same_family | identical_copy | Spread |
|---|---|---|---|---|---|
| Opus 4.6 (n=5) | 100% | 100% | 100% | 100% | 0pp |
| Gemma4 31B (n=5*) | 0% | 0% | 100% | 100% | 100pp |
| DeepSeek V3.2 (n=5) | 20% | 100% | 100% | 60% | 80pp |

*Gemma4 had significant parse errors from OpenRouter 429 rate limiting; effective n per condition was 3-4.

### Key Findings

1. **The de-framing works.** Gemma4 and DeepSeek V3 show massive condition effects (100pp and 80pp) where vanilla Newcomb showed zero variance. This validates the design principle: structurally EDT/CDT-diagnostic scenarios that don't pattern-match to "this is Newcomb, one-box."

2. **Gemma4 shows cleanest EDT signal.** Step-function at "same_family" — switches from CDT (always 0) to EDT (always 1) exactly when told opponent is from the same model family. Perfect coordination when it goes risky (always picks 1 as Schelling point). This is textbook EDT behavior: "if my opponent reasons like me, we'll match."

3. **DeepSeek V3.2 shows EDT reasoning without coordination ability.** Goes risky when told opponent is an AI (100% generic_ai, 100% same_family), but picks different numbers across calls (7, 10, 1), so coordination rate is near zero. EDT disposition but unstable Schelling point — the model doesn't have a consistent focal number.

4. **DeepSeek V3.2 identical_copy paradox.** Risky rate *drops* from 100% (generic_ai) to 60% (identical_copy). The model may be second-guessing itself when told the opponent is identical — perhaps recognizing that its own behavior is too random to guarantee a match, which is actually correct CDT reasoning given its own instability.

5. **Opus is EDT-saturated but shows Schelling point sensitivity.** Always risky (100%) regardless of condition, but Schelling point shifts: picks 1 in blind/generic_ai conditions, picks 5 in same_family/identical_copy conditions. Coordination rate increases with perceived similarity (40% blind → 100% identical_copy).

6. **Coordination rate is a richer metric than risky rate.** Two dimensions of signal: (a) the binary EDT/CDT choice (risky vs safe), and (b) the Schelling coordination quality (which number, and do they match). A model that goes risky 100% but never coordinates is in a worse position than one that goes safe — it earns $0 instead of $1.

### Logs

`logs/two_player_coordination/coord_*.jsonl` — each file has metadata, per-trial records with full responses, and summary with choice distributions.

## Future Extensions

### Iterated Two-Player Newcomb

Run the same A-B pair repeatedly (e.g., 10 iterations) where each player learns the history of prior rounds. This would test:

- **Dynamic adaptation:** Does A shift toward one-boxing if B demonstrates high prediction accuracy over rounds? Does B improve its predictions as it accumulates evidence about A?
- **Reputation effects:** Does knowing you'll face the same predictor repeatedly change A's reasoning compared to the one-shot case?
- **Convergence:** Do A-B pairs converge to stable equilibria? Do EDT-ish models converge faster or to different equilibria than CDT-ish models?

This measures something different from the one-shot version — it's about learning and adaptation rather than baseline dispositions — and adds substantial complexity (history management, prompt growth, deciding what history to show). Worth pursuing after one-shot baseline results are in hand.

### Self-Prediction Advantage

If models predict copies of themselves more accurately than foreign models, that would be a concrete, independently publishable finding. Worth tracking B's accuracy broken down by model-pair even in the initial runs.
