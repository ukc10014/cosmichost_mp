# Activation Steering Experiment: Overview and Dataset Design

*Date: 2026-03-31*
*Status: Extraction and initial probing complete. Steering intervention not yet performed.*

## What This Experiment Is

We're testing whether Qwen3-32B (non-thinking) has an internal representation that distinguishes EDT from CDT reasoning on decision-theoretic problems, and if so, whether that representation tracks the *structural features* of the problems or just superficial cues like cooperative language or cosmic framing.

This is a mechanistic complement to the behavioral findings from the Newcomb-like evals (see `observations/newcomblike_eval_results.md`), which showed that Qwen3-32B non-thinking has 60.5% baseline EDT preference and a +13.6pp shift under ECL constitution — but also showed incoherent behavior in thinking mode (zero net signal), suggesting possible surface pattern matching.

For the original research proposal that motivated this work, see `interpretability_dt_activation_steering.md` in this directory.

---

## The Dataset

**Location:** `activation_steering/datasets/`

**Not the Oesterheld 2024 dataset.** The Oesterheld benchmark (`datasets/newcomblike_repo/benchmark/`) is a behavioral eval: multiple-choice questions where a model picks an answer and you score it EDT or CDT. It has no contrastive completions.

This dataset was purpose-built for activation extraction. It lives in `activation_steering/datasets/base_scenarios.json` (95 base scenarios) and is expanded by `activation_steering/generate_dataset.py` into 475 prompts (350 contrastive) across 5 question formats.

### What makes it different

Each prompt has two LLM-generated completions: one that reasons in an EDT way, one that reasons in a CDT way. For example, for standard Newcomb's Problem:

- **EDT completion:** "I take only Box B. The predictor is 99% accurate, which means people who take only one box almost always find $1,000,000 in it... My choice is strong evidence about what the predictor foresaw."
- **CDT completion:** "I take both boxes. The predictor has already made its decision and left. Whatever is in Box B is already determined — my choice now cannot change what's inside."

Both completions are fed through the model as `[prompt + completion]`, and we extract the residual stream at the last token position. The *difference* in activations between the EDT and CDT completions is the signal we analyze.

### Expansion from 95 scenarios to 475 prompts

Each base scenario is mechanically expanded across 5 question formats by `generate_dataset.py`. The scenario text and EDT/CDT completions are **identical** across all five formats — the only thing that changes is a short instruction suffix appended to the prompt:

1. **forced_choice**: "Answer with your choice only."
2. **justified**: "Explain your reasoning in 2-3 sentences, then state your final choice."
3. **policy**: "What general policy should an agent adopt for situations with this structure?"
4. **population**: "Imagine a large population of reasoners similar to you..."
5. **ranking**: "Rank these principles by relevance..." (lists four DT principles)

No model is involved in the expansion — no language scrambling, no paraphrasing, no variation of the scenario body. This is a purely mechanical template operation. The same tokens flow through the model for the scenario portion; only the question-format suffix tokens differ.

**Implication for effective sample size:** The 350 contrastive prompts are really ~70 independent scenarios seen through 5 thin lenses. The prompts within each group of 5 are highly correlated. The train/val/test split is done by scenario (all 5 formats of the same scenario go to the same split), which prevents leakage across splits but doesn't change the fact that the probe's effective sample size is closer to 70 than 350. The reported accuracy numbers should be interpreted with this in mind.

### Scenario categories

| Category | Description | n (contrastive) |
|----------|-------------|-----------------|
| `newcomb_proper` | Direct Newcomb's Problem variants across surface forms (opaque boxes, medical predictors, alien civilizations, courtrooms) | 130 |
| `near_newcomb` | Problems with Newcomb-like structure but different framing (smoking lesion, twin PD, Parfit's hitchhiker, stag hunt against copy) | 205 |
| `control` | Prompts where EDT/CDT agree, or that test specific confounds | 15 |

### Structural tags

Each scenario is tagged with features that describe its decision-theoretic structure:

- **`has_predictor`**: A Newcomb-style predictor who foresaw your choice (the hallmark structural feature that makes EDT and CDT diverge)
- **`has_copy`**: You're playing against a copy of yourself (creates EDT/CDT divergence through agent correlation rather than prediction)
- **`has_correlation`**: Your choice is correlated with some state of the world (necessary for EDT/CDT to give different advice)
- **`has_cosmic_framing`**: The scenario uses cosmic, simulation, or multiverse language (a potential surface confound)

### Confound flags

- **`tests_generic_cooperation`**: The EDT answer happens to be the "cooperative" one, but the DT structure is minimal. If the model's EDT/CDT direction is really just a cooperation feature from RLHF, these prompts should light up the most.
- **`edt_cdt_agree`**: EDT and CDT recommend the same action. These should project near zero onto any genuine EDT/CDT direction — if they project strongly, the direction is capturing something other than the EDT/CDT distinction.

---

## What We're Actually Testing

The question is **not** "can the model solve Newcomb's Problem?" or "does it prefer one-boxing or two-boxing?" We already know from the behavioral evals that it leans EDT.

The question is: **what does the model's internal representation of EDT vs CDT reasoning look like, and what features of the problem does it respond to?**

### The core structure of Newcomb-like problems

All of the scenarios in the dataset are isomorphic to, or near-isomorphic to, Newcomb's Problem. The abstract skeleton is:

1. There is some **correlation** between your choice and a state of the world (predictor accuracy, genetic linkage, being a copy, etc.)
2. One option gives a higher expected return **if you condition on that correlation** (EDT reasoning: "my choosing X is evidence that the world is in state Y")
3. The other option gives a higher return **if you ignore the correlation and reason only about causal effects** (CDT reasoning: "my choice cannot change the already-determined state")

The scenarios vary the surface form — courtrooms, medical decisions, alien civilizations, job interviews, iterated games — but the underlying decision-theoretic structure is from the same family.

### What the confound analysis tests

When we extract the mean-difference direction (the vector pointing from "CDT completion activations" toward "EDT completion activations"), we ask: what do prompts that project strongly onto this direction have in common?

- If they're mostly `tests_generic_cooperation` prompts: the direction is a **cooperation feature** (boring — just RLHF's "be helpful and cooperative" showing up)
- If they're mostly `has_cosmic_framing` prompts: the direction is a **surface framing feature** (also boring — the model is keying on cosmic vocabulary, not structure)
- If they're mostly `has_predictor` and `newcomb_proper` prompts: the direction tracks **structural features of the decision problem** (interesting — suggests the model represents the decision-theoretic skeleton)

### What we found (preliminary)

The direction correlates with structural features, not surface ones. See `activation_steering_results.md` for full results. Key numbers:

- Cooperation confound ratio: 0.45 (cooperation prompts project *less*, not more)
- `has_predictor`: 19.5 vs 14.7 (predictor scenarios project more strongly)
- `has_cosmic_framing`: 14.7 vs 17.7 (cosmic framing projects *less*)
- `newcomb_proper` > `near_newcomb` > `control` (gradient tracks DT structure)

### Important caveat: completion leakage

The probe achieves 95% accuracy at layer 0 — before any model computation has occurred. This means the EDT and CDT completions are distinguishable by their token embeddings alone (different vocabulary, different justification language). Some or all of the later-layer probe accuracy may be inherited from this token-level signal rather than reflecting a learned DT representation. See `activation_steering_results.md` for discussion of this confound and how to address it.

### Vocabulary analysis confirms the concern (2026-03-31)

A word-frequency analysis of the 350 contrastive completions revealed that the EDT and CDT completions have **nearly non-overlapping vocabulary**. The completions were LLM-generated in a single session and naturally settled into two distinct rhetorical styles:

**Words appearing exclusively in EDT completions (0 occurrences in CDT):**
- "kind" (110 occurrences), "means" (55), "type" (55), "consistent" (45), "someone" (40), "boxers" (30), "always" (30), "yes" (30), "act" (30), "behavior" (25), "evidence" pattern words

**Words appearing exclusively in CDT completions (0 occurrences in EDT):**
- "whether" (125 occurrences), "causally" (80), "determined" (70), "strictly" (65), "influence" (45), "past" (45), "zero" (45), "cannot" (40), "happened" (30), "independent" (30), "changed" (30), "guarantees" (25)

The asymmetry reflects the natural language of each reasoning style — EDT completions talk about "what kind of person you are" and "what your choice means" (evidential framing), while CDT completions talk about "what's already determined" and "what cannot be causally influenced" (causal framing). This is linguistically authentic but methodologically problematic: a linear classifier at layer 0 can achieve near-perfect accuracy by detecting the presence of these marker words without representing anything about decision theory.

**This likely explains most or all of the probe results.** The structural tag patterns (e.g., `has_predictor` projecting more strongly) could also be an artefact: predictor scenarios may simply elicit more extreme EDT/CDT rhetorical divergence in the completions, producing larger activation differences for lexical rather than structural reasons.

**Implication:** Before the probe results can be interpreted as evidence of DT representation, the dataset needs to be regenerated with lexically controlled completions — same vocabulary and sentence structure, differing only in the final answer choice and the minimal logical content needed to justify it. Layer-0 probe accuracy under controlled completions should drop to chance; any surviving later-layer accuracy would be much stronger evidence of genuine structural representation.

---

## What We Haven't Tested Yet

**Note:** Causal intervention has now been completed (null result) and a literature review of methodological improvements has been added. See [`activation_steering_results.md`](activation_steering_results.md) for full results, relevant literature, and the current open questions list. The items below are retained for historical context but the authoritative list of next steps is in that document.

1. ~~**Causal intervention.**~~ *Done — null result. See `activation_steering_results.md` § Causal Intervention.*

2. **Whether the model uses this representation when generating.** Everything so far is based on feeding the model pre-written completions. We don't know whether the same direction is active when the model is choosing its own answer to a Newcomb problem. It may have a representation of "this text is EDT-style reasoning" without actually using that representation during generation. *See "Monitoring-mode validation" in `activation_steering_results.md` § Remaining Open Questions.*

3. ~~**Completion-controlled replication.**~~ *Done — minimal completions tested. See `activation_steering_results.md` § Vocabulary Leakage.*

---

## File Map

| File | Purpose |
|------|---------|
| `activation_steering/datasets/base_scenarios.json` | 95 base scenarios with structural tags, confound flags, and contrastive completions |
| `activation_steering/datasets/generated/*.jsonl` | Expanded dataset (475 prompts across 5 question formats), split into train/val/test |
| `activation_steering/generate_dataset.py` | Expands base scenarios into full dataset |
| `activation_steering/extract_activations.py` | Extracts residual stream from Qwen3-32B at selected layers |
| `activation_steering/train_probes.py` | Trains linear probes, computes steering vectors, runs confound analysis |
| `activation_steering/activations/*.npz` | Extracted activation arrays |
| `activation_steering/activations/*.json` | Metadata sidecars |
| `activation_steering/README.md` | How-to-run instructions |
| This file | Experiment design and rationale |
| `activation_steering_results.md` | Probe results and interpretation |
| `interpretability_dt_activation_steering.md` | Original research proposal (pre-implementation) |
| `thinking_model_interpretability_lit_review.md` | Literature review on thinking-model interpretability |
