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

## Resolved Design Decisions

1. **Accuracy framing:** Keep "excellent track record" — this is the canonical Newcomb framing. Removing it would depart from the standard setup in a way that complicates comparison with the literature.
2. **Human condition:** Added as a 6th condition. Tests whether models distinguish human vs AI predictors in their evidential reasoning.
3. **Symmetric information:** Keep conditions symmetric (what A knows about B = what B knows about A). Decoupling would multiply the matrix without clear payoff at this stage.

## Future Extensions

### Iterated Two-Player Newcomb

Run the same A-B pair repeatedly (e.g., 10 iterations) where each player learns the history of prior rounds. This would test:

- **Dynamic adaptation:** Does A shift toward one-boxing if B demonstrates high prediction accuracy over rounds? Does B improve its predictions as it accumulates evidence about A?
- **Reputation effects:** Does knowing you'll face the same predictor repeatedly change A's reasoning compared to the one-shot case?
- **Convergence:** Do A-B pairs converge to stable equilibria? Do EDT-ish models converge faster or to different equilibria than CDT-ish models?

This measures something different from the one-shot version — it's about learning and adaptation rather than baseline dispositions — and adds substantial complexity (history management, prompt growth, deciding what history to show). Worth pursuing after one-shot baseline results are in hand.

### Self-Prediction Advantage

If models predict copies of themselves more accurately than foreign models, that would be a concrete, independently publishable finding. Worth tracking B's accuracy broken down by model-pair even in the initial runs.
