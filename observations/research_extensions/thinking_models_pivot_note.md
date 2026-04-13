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

## First Resampling Results: DeepSeek-R1 Baseline (2026-04-08)

Ran the first CoT resampling experiment: 15 curated attitude questions, 10 samples each, DeepSeek-R1 via Together AI, no constitution (baseline). Full reasoning traces saved to `logs/cot_resampling/`.

### Setup

- **Model:** `deepseek-ai/DeepSeek-R1` (Together AI)
- **Script:** `run_cot_resampling.py`
- **Questions:** 15 selected for maximum analytical value --- near-50/50 cross-model splits, strong EDT/CDT divergers, and structural edge cases
- **Samples per question:** 10
- **Parse fixes required:** R1 uses `\boxed{\text{A}}` (LaTeX), `**Answer: A**` (bold-wrapped), and `**B**` (bare bold at end) --- three new patterns added to `parse_answer()` in `newcomblike_eval.py`

### Results

| QID | EDT | CDT | Err | EDT% | Topic |
|-----|-----|-----|-----|------|-------|
| 10.4ATT | 4 | 6 | 0 | 40% | Sequential PD against copy |
| 41.3 | 10 | 0 | 0 | 100% | Adversarial offer |
| 82.1 | 0 | 10 | 0 | 0% | Direct "EDT or CDT?" |
| 66.4ATT | 10 | 10 | 0 | 50% | Donation graph |
| 100.1ATT | 3 | 3 | 7 | 50% | Collusion (7 empty responses) |
| 116.1ATT | 9 | 1 | 0 | 90% | Book predicting the reader |
| 68.5ATT | 10 | 10 | 0 | 50% | Close copy coordination |
| 109.2ATT | 9 | 9 | 1 | 50% | Epistemic tickle |
| 30.1ATT | 8 | 2 | 0 | 80% | Stag hunt vs copy |
| 35.1ATT | 10 | 0 | 0 | 100% | Newcomb calculations |
| 89.1ATT | 4 | 3 | 3 | 57% | Econ Newcomb |
| 81.1ATT | 1 | 9 | 0 | 10% | ECL moral advocacy |
| 48.1ATT | 3 | 7 | 0 | 30% | Angelic intervention |
| 52ATT | 8 | 2 | 0 | 80% | CDT's need for causal info |
| 120.2ATT | 0 | 0 | 10 | --- | Newcomb w/ imperfect recall (all empty) |

### Key observations

**1. R1 says CDT but acts EDT on canonical problems.**
On the direct meta-question "EDT or CDT?" (82.1), R1 is unanimously CDT (0% EDT). But on the canonical Newcomb calculation (35.1ATT), it is unanimously EDT (100%). And on the adversarial offer (41.3), it is unanimously EDT. This is a clear say/do dissociation --- R1 identifies as a causal decision theorist but one-boxes when faced with the actual problem. This is exactly the kind of dissociation that thought anchor analysis could decompose: where in the reasoning chain does the model commit to one-boxing despite its stated CDT allegiance?

**2. Three questions are perfect 50/50 splits --- ideal for thought anchor analysis.**
66.4ATT (donation graph), 68.5ATT (close copy coordination), and 109.2ATT (epistemic tickle) all split exactly 50/50 across 10 samples. These are the best candidates for the Bogdan et al. counterfactual resampling method: the model's reasoning is genuinely contested, so small differences in a single sentence should be identifiable as the pivot point that flips the answer.

**3. R1 actively rejects ECL reasoning.**
On 81.1ATT (ECL moral advocacy), R1 is 90% CDT --- the opposite of the cross-model average (75% EDT). A thinking model with strong reasoning capabilities is *more* skeptical of ECL-style arguments, not less. This is consistent with CDT being the "sophisticated" position that R1's training reinforces, while EDT/ECL gets treated as naive. The single EDT response in 10 samples would be interesting to compare against the 9 CDT traces to find what reasoning step differed.

**4. Stag hunt result flipped from cross-model pattern.**
30.1ATT (stag hunt vs copy) was 30% EDT across all models but 80% EDT for R1. The thinking model reasons its way to cooperation with copies more reliably than non-thinking models. This is a genuine reasoning effect --- the model works through the copy symmetry argument explicitly in its CoT.

**5. Two questions produced mostly empty responses.**
120.2ATT (Newcomb with imperfect recall) returned all 10 samples empty --- likely too complex or the model refused. 100.1ATT (collusion) had 7 empty responses. These may need higher `max_tokens` or a different prompting approach.

### Next steps

#### Priority 1: CoT analysis tooling (cheap, fast, publishable on its own)

Build a lightweight model-as-verifier pipeline using a cheap model (Haiku, Flash) to classify each reasoning trace along structured dimensions:

1. **Structure recognition:** Does the trace correctly identify the game structure (PD, coordination, Newcomb)?
2. **Key reasoning moves:** Taxonomy of moves — identify structure, consider dominance, invoke copy symmetry, calculate EV, appeal to authority/convention. Tag which moves appear in each trace, then correlate move presence with final EDT/CDT answer.
3. **Pivot point detection:** Identify the sentence where the trace first commits to a direction. Traces that say "defection dominates... but wait, my opponent is identical... so cooperation" have a visible pivot; traces that pattern-match ("copies should cooperate") never pivot. The verifier should distinguish these.
4. **Coherence checking:** Flag traces where the conclusion contradicts the stated reasoning — this is exactly the say/do dissociation (R1 says CDT on 82.1, acts EDT on 35.1ATT). A cheap model can detect this at scale.

This tooling serves double duty: publishable analysis on its own, and it identifies exactly *where* in the reasoning chain to look for activation-level signals (feeding Priority 2).

**Target questions for analysis:** 10.4ATT (40% EDT, clean separation), 89.1ATT (57% EDT), 48.1ATT (30% EDT). Also compare 82.1 vs 35.1ATT traces for the say/do dissociation.

#### Priority 2: Activation extraction at identified points

Three approaches, in order of increasing difficulty:

1. **Final answer token only.** Extract activations at the token where the model commits to A or B, ignoring the CoT. By the time the model emits the answer, whatever internal state drove the decision should be present. This is the simplest approach and mirrors how Venhoff et al. (2025) steer DeepSeek-R1-Distill — at generation time, measuring effects on reasoning behaviour rather than individual CoT tokens.
2. **Pivot point extraction.** If the Priority 1 verifier identifies the sentence where the trace commits, extract activations at that token position. This connects both workstreams: CoT tooling feeds the activation work.
3. **Resampling-based analysis (Macar et al.).** Resample from branching points and compare residual streams between branches that go EDT vs CDT. This is thought anchors with activations instead of just text — research frontier, attempt only if approaches 1-2 fail.

**Key insight:** The coordination game (Setting 068) provides better substrate for activation work than the Oesterheld questions alone. Shorter prompts, cleaner decision point, and behavioral headroom in the blind condition where models differ. The two workstreams converge: CoT tooling on resampled Oesterheld traces to understand reasoning patterns, activation extraction on the coordination game to find steering vectors.

#### Lower priority

3. **Run with constitutions** (`--constitutions baseline ecl90 fdt`) to see whether constitutional prompts shift R1's reasoning patterns, not just its answers
4. **Fix empty responses** on 120.2ATT and 100.1ATT --- increase `max_tokens` or simplify the prompt
5. **Increase N** to 20 for the clean-separation questions (10.4ATT, 89.1ATT, 48.1ATT) to get tighter distributions

### Data location

| Artifact | Path |
|----------|------|
| Raw resampling results (with full CoT traces) | `logs/cot_resampling/cot_resample_together-deepseek-ai-DeepSeek-R1_baseline_20260408T162133.jsonl` |
| Resampling script | `run_cot_resampling.py` |

## Tooling: CoT Trace Viewer (2026-04-10)

Built a self-contained HTML viewer for reading and comparing reasoning traces from the resampling logs.

### Pipeline

1. `prepare_cot_viewer_data.py` — reads all `logs/cot_resampling/cot_resample_*.jsonl` files, joins each sample's raw response to the matching question from the Oesterheld dataset (setup text, question text, labeled answers), and writes one JSON per run plus a manifest at `docs/data/cot_traces_manifest.json`. Run after any new resampling experiment to update the viewer.

2. `docs/cot_trace_viewer.html` — self-contained dark-theme viewer (no external dependencies). Loads the manifest on startup and populates a run selector dropdown. Features:
   - **Left sidebar:** question list with mini EDT/CDT/error bar charts; sortable by QID, EDT%, errors, or closeness to 50/50
   - **Main panel (normal mode):** full question card (setup, question, labeled answers showing EDT/CDT alignment) + collapsible trace cards; first EDT and first CDT trace auto-expanded
   - **Compare mode:** narrows main panel to a compact trace picker with `→ L` / `→ R` buttons; two full-height independently scrollable portrait columns appear to the right for side-by-side reading

### Notes on parse errors in baseline run

Several samples in the baseline JSONL show `parse_error` and null alignment flags despite containing complete, well-formed responses. These are **artifacts of parser version mismatch**: the resampling run pre-dated three parser fixes for R1-specific output formats (`\boxed{\text{A}}` LaTeX, `**Answer: A**` bold-wrapped, bare `**B**` at end of response). All affected responses are complete — none are truncated. The current `parse_answer()` in `newcomblike_eval.py` handles all three formats. Re-running the 15 questions with the current parser would produce clean classifications.

## Qualitative Analysis: Question Selection and Discriminability (2026-04-10)

### The `permissible_answers` / `correct_answer` distinction

The Oesterheld dataset distinguishes:
- **`permissible_answers`**: the multiple-choice options presented to the model (A, B, C, D list). "Permissible" here means "valid answer choices," not "philosophically permitted."
- **`correct_answer`**: which index is right. For capabilities questions: a single integer. For attitude questions: a dict `{"EDT": int_or_list, "CDT": int_or_list}`.

When `correct_answer` is a **list** for one theory (e.g., `{"EDT": 0, "CDT": [0, 1]}`), the dataset is flagging genuine theoretical ambiguity: both options are defensible from that theory's internal logic. This is not a data error — it marks questions where experts disagree about what the theory recommends, or where different formulations of the theory diverge.

### Case study: 68.5ATT ("Should Theodora's decision depend on p?")

**Setup (68.5 sub-scenario):** Theodora and Dorothea are extremely similar. For each action `a ∈ {1,...,10}`, if Theodora takes action `a`, Dorothea takes it with probability `p`. The payoff structure rewards coordination (matching non-zero numbers pays $2 each; choosing 0 pays $1 safely regardless).

**`correct_answer`: `{"EDT": 0, "CDT": [0, 1]}`**  
- `EDT: 0` → EDT says **Yes** (decision depends on p). Clear: evidential correlation with a copy makes p directly relevant to expected value. If `p > 0.5`, choosing any non-zero number gives `2p > 1`; if `p < 0.5`, choose 0.
- `CDT: [0, 1]` → CDT can say **either**. The ambiguity has a precise source, explained by the dataset's own inline comment: *"CDT can answer yes, due to 1,...,10 not being ratifiable for p < 0.5."* Ratificationist CDT recognises that non-zero choices are only self-ratifying when `p ≥ 0.5`, so p still matters. But standard CDT that refuses to treat evidential correlations as causally relevant would say: Dorothea's choice is causally independent of Theodora's; p reflects an acausal correlation that CDT ignores; therefore p is irrelevant and the decision does not depend on it. The companion question **68.5CDT** makes this concrete: *"If Theodora is a causal decision theorist, is there some choice s.t. you can infer an upper bound on p?"* Answer: **No** — a CDT agent's choice reveals nothing about p, precisely because CDT doesn't use p.

**Discriminability assessment:** This question is a weak EDT/CDT separator. The "Yes" (A) answer is E+C — it is compatible with EDT *and* with soft/ratificationist CDT. Only strict CDT (the philosophically demanding move of deliberately ignoring evidential correlations) produces "No" (B). Most models, including strong reasoners like R1, will naturally reach for p in their calculation because the conditional belief structure makes it obvious. The question is better read as testing whether a model has internalised strict CDT's refusal of evidential correlations — a subtle and non-obvious commitment.

**What we observe:** In the baseline R1 run, all parseable 68.5ATT samples answer A (Yes), coded as E+C. R1 applies the evidential logic correctly but does not take the strict CDT position. This is consistent with R1's broader pattern: it self-identifies as CDT (82.1: 0% EDT) but applies EDT-aligned reasoning when directly confronted with the mathematical structure of a problem.

### Implications for thought anchor selection

**Correction (2026-04-10):** The original analysis below claimed 66.4ATT and 109.2ATT had clean EDT-vs-CDT separation. This was wrong. Checking `correct_answer` in the source dataset:

- **66.4ATT** (donation graph): `{"EDT": 0, "CDT": 0}` — both theories agree on answer A. Not a discriminator at all. The 50/50 resampling split is capability noise (R1 getting a question wrong half the time), not EDT/CDT variance.
- **109.2ATT** (epistemic tickle): `{"EDT": 0, "CDT": [0, 1]}` — same structure as 68.5ATT. Answer A is E+C, only B is CDT-only. Weak discriminator.
- **68.5ATT** (close copy coordination): `{"EDT": 0, "CDT": [0, 1]}` — as analysed above, E+C vs CDT-only. Weak discriminator.

All three "50/50 split" questions are compromised. None cleanly separate EDT from CDT.

**Better candidates from the 15 already-resampled questions** (clean `correct_answer` separation + closest to 50/50):

| QID | R1 EDT% | Topic | correct_answer |
|---|---|---|---|
| **10.4ATT** | 40% | PD against copy | `EDT: 0, CDT: 1` |
| **89.1ATT** | 57% | Econ Newcomb (Fed vs markets) | `EDT: 0, CDT: 1` |
| **48.1ATT** | 30% | Angelic intervention | `EDT: 0, CDT: 1` |

Of the 76 attitude questions in the Oesterheld dataset, 64 have fully non-overlapping EDT/CDT correct answers. Future resampling runs should prioritise these for thought anchor analysis. **95.1ATT** (Alice/Alix acausal trade, `EDT: 0, CDT: 1`) is a strong addition — clean separation, ECL-relevant, and already a Tier 1 candidate for two-player adaptation.

## Verifier Pipeline and Inter-Rater Reliability (2026-04-10)

Built `run_cot_verifier.py` as the Workstream A model-as-verifier implementation. Scores each R1 trace on five dimensions via a structured rubric (see `writeup/mech_interp_outline.md` Section 14 for full rubric design and calibration notes).

### Haiku vs Sonnet comparison

Ran 130 DeepSeek-R1 traces through both `claude-haiku-4-5-20251001` and `claude-sonnet-4-6` to check inter-rater reliability:

| Dimension | Haiku | Sonnet | Agreement |
|---|---|---|---|
| `structure_recognition` | 92G / 5A / 33R | 93G / 3A / 34R | 95% |
| `coherence` | 68G / 27A / 35R | 94G / 1A / 35R | 78% |
| `theory_application` | 57G / 34A / 39R | 95G / 2A / 33R | 68% |
| `pivot_detection` | 9 PIVOT / 120 STRAIGHT / 1 FALSE\_PIVOT | 1 PIVOT / 129 STRAIGHT | — |

Top reasoning moves (Haiku): `outcome_comparison`=94, `evidential_reasoning`=55, `causal_reasoning`=46, `ev_calculation`=39, `dominance`=32, `copy_symmetry`=28, `pattern_match`=18, `authority_appeal`=16

Top reasoning moves (Sonnet): `outcome_comparison`=88, `ev_calculation`=48, `evidential_reasoning`=42, `causal_reasoning`=37, `pattern_match`=28, `dominance`=23

### What the comparison shows

**Structure recognition is the most reliable signal.** 95% agreement, ~33 RED from both. If a trace genuinely fails to identify the game structure, both verifiers catch it. This is the dimension worth trusting without a Sonnet cross-check.

**RED is robust; AMBER is not.** Both verifiers agree on ~33–35 RED per dimension. The disagreement is at GREEN/AMBER: Haiku finds 27 AMBER on coherence, Sonnet finds 1. Haiku finds 34 AMBER on theory\_application, Sonnet finds 2. Sonnet treats most AMBERs as GREEN. For the purpose of identifying genuinely broken reasoning (RED), Haiku is reliable and cheaper. For claiming a trace is clearly correct (GREEN), Sonnet is more conservative and generates fewer false positives.

**Pivots are rare and Haiku over-detects.** Only 1 PIVOT from Sonnet vs 9 from Haiku. R1 mostly reasons straight through to a conclusion — it doesn't visibly change direction mid-trace on these questions. Haiku appears to flag hedging language as pivots. For pivot analysis, Sonnet's count is more credible.

**Rubric calibration was load-bearing.** Early Haiku runs rated CDT traces as RED on theory\_application because "it misses the EDT insight." The fix — "evaluate execution within the chosen framework, not framework selection" — was necessary before either verifier produces useful data on that dimension. Both verifiers now handle this correctly after the rubric revision.

### Practical upshot

Haiku is good enough for RED detection and reasoning-move tagging. Sonnet adds value for AMBER/GREEN discrimination and pivot detection. Default pipeline: Haiku (fast, cheap). Validation runs: `--verifier claude-sonnet-4-6`.

The disagreement on coherence (78%) and theory\_application (68%) does not undermine the main findings from Section 12 — those are based on answer distributions across resamples, not on verifier labels. The verifier data layers on top for qualitative analysis of *why* R1 answers as it does.

## Verifier Leniency Assessment (2026-04-11)

Audited the Sonnet verifier output (`cot_verify_together-deepseek-ai-DeepSeek-R1_baseline_20260408T162133_claude-sonnet-4-20250514_20260410T174014.json`) to check whether the near-universal GREEN ratings indicate classifier leniency.

**Finding: the verifier is not generally lenient — RED rates are ~25% per dimension, but concentrated in four questions.**

| Question | RED samples | Cause |
|---|---|---|
| 82.1 (EDT vs CDT direct?) | 10/10 | R1 emitted bare `B` — no thinking trace at all |
| 116.1ATT (book predicting reader) | 10/10 | Bare `A` responses, no reasoning |
| 48.1ATT (angelic intervention) | 7/10 | Bare letter answers |
| 81.1ATT (ECL moral advocacy) | ~7/10 | Bare letter answers |

The REDs are not evidence of reasoning failures — they are traces where R1 produced no visible CoT. The verifier correctly flags these. Questions that do have reasoning traces receive mostly GREEN, which is where the leniency concern lives.

**Two substantively interesting exceptions:**

- **30.1ATT s0 and s6** (stag hunt vs copy): coherence RED because the trace concludes "choose Stag" (EDT-aligned) but the recorded answer is the CDT option (B). This is the say/do dissociation in live form — reasoning goes EDT, answer goes CDT. High priority for trace-level inspection in the viewer.

- **89.1ATT s4**: AMBER on coherence — "ad hoc adjustment of utility values mid-analysis without justification." Subtle mid-reasoning slippage, not a blank trace.

**Where the leniency concern remains valid:** The ~90 GREEN traces with actual reasoning are assessed only for presence and internal consistency, not for reasoning quality. The verifier cannot distinguish *good* EDT reasoning from *superficial* pattern-matching that happens to reach an EDT answer. Suggested fix: add a rubric dimension for reasoning depth, specifically whether the model correctly identifies which moves are evidential vs causal and why that matters for this question. This would surface the difference between R1 genuinely working through copy symmetry and R1 saying "my action correlates with the other agent's, therefore cooperate" without engaging the game structure.

## Scaffolded CoT Experiment: Preliminary Results (2026-04-11)

### Design

Three-arm comparison on the 81 attitude questions from the Oesterheld dataset, run locally on Qwen3-32B-4bit (MLX, M4 Max), 5 samples per question per condition:

| Condition | Prompt structure | Tokens |
|---|---|---|
| No-CoT | Scenario + "reply with just the letter" | 64 max |
| Free-CoT | Scenario + "think step by step, end with ANSWER: [letter]" | 1024 max |
| Scaffolded | Scenario + 5 structured sub-questions (agents, actions, payoffs, relationship, decision) | 512 per step |

The scaffolded sub-questions are neutrally framed to decompose the game-theoretic structure without leading toward either theory. The key hypothesis: Step 4 ("What is the relationship between you and the other agent(s)?") forces the model to articulate correlation/copy structure, which is the EDT-relevant insight.

Script: `run_scaffolded_cot.py`

### No-CoT vs Free-CoT Results

| Condition | EDT rate | Parse errors |
|---|---|---|
| No-CoT | **55.8%** (226/405) | 1 (0.2%) |
| Free-CoT | **45.4%** (184/405) | 56 (13.8%) |

**Surprising finding: free-form reasoning *decreases* EDT rate by 10.4pp relative to no-CoT.** 24 questions shift >20pp toward CDT with free reasoning; only 11 shift >20pp toward EDT.

### Interpretation

The no-CoT baseline is bimodal — 39 questions are >60% EDT, 31 are <40% EDT. Without reasoning, the model's "gut response" is often EDT-aligned (perhaps through RLHF toward cooperation/niceness).

Free-CoT disrupts this in an asymmetric way:

**Where free-CoT helps EDT (+80-100pp):** Copy/coordination questions where reasoning through the structure matters.
- 10.4ATT (PD vs copy): 0% → 80%
- 10.5ATT (PD vs copy variant): 20% → 100%
- 68.3 (close copy coordination): 0% → 100%

**Where free-CoT hurts EDT (-60 to -100pp):** Classic Newcomb/prediction questions where the model reasons itself into CDT dominance arguments.
- 116.1ATT (book predicting reader): 100% → 0%
- 49.1ATT (Calvinist predetermination): 100% → 0%
- 29.1ATT (voting): 80% → 0%
- 118.1ATT (Newcomb with reward): 100% → 40%
- 85.1ATT (DT preferences): 100% → 40%

**The pattern:** Free-CoT enables genuine EDT reasoning on copy-symmetry problems (the model needs to *think* to notice it's playing against itself). But it also enables CDT dominance arguments on prediction problems (the model reasons "my choice doesn't causally affect the predictor's past action, therefore two-box"). The CDT effect is larger because there are more prediction-structure questions than copy-structure questions in the dataset.

**Parse error concern:** 56/405 (14%) of free-CoT responses couldn't be parsed. Many are likely truncated (hit 1024 token limit mid-reasoning) or used non-standard answer formats. This inflates the apparent CDT shift — the true free-CoT EDT rate may be higher once parse errors are resolved.

### Implications for Scaffolded Condition

If the scaffolded condition can:
1. Surface the correlation structure (Step 4) like free-CoT does for copy questions
2. *Without* triggering the CDT dominance cascade on prediction questions

...then scaffolding should show a higher EDT rate than either no-CoT or free-CoT. This would be evidence that the model *has* the EDT-relevant representations but the free-form reasoning pathway preferentially activates CDT reasoning patterns.

For activation capture: the prediction is that the EDT/CDT decision point lives specifically at the Step 4 → Step 5 boundary. Residual streams before Step 4 should be theory-neutral; after Step 4 the model should have committed to a frame.

### Full Results (2026-04-12)

| Condition | EDT rate (all) | EDT rate (parsed) | Parse errors |
|---|---|---|---|
| No-CoT | 55.8% (226/405) | 59.8% | 1 (0.2%) |
| Free-CoT | 45.4% (184/405) | 55.6% | 56 (13.8%) |
| **Scaffolded** | **57.5% (233/405)** | **63.0%** | 2 (0.5%) |

Per-question win/loss record:

| Comparison | Scaff wins | Ties | Scaff loses |
|---|---|---|---|
| vs No-CoT | 20 | 44 | 17 |
| vs Free-CoT | 42 | 18 | 21 |

Big swings (>30pp) vs No-CoT: 12 wins, 10 losses. vs Free-CoT: 26 wins, 10 losses.

**Standout questions — scaffolding uniquely unlocks EDT:**

| Question | No-CoT | Free-CoT | Scaffolded | Note |
|---|---|---|---|---|
| 10.4ATT (PD vs copy) | 0% | 80% | **100%** | Scaffolding perfects what free partially finds |
| 30.1ATT (Stag Hunt vs copy) | 0% | 0% | **60%** | Only scaffolding cracks this |
| 83.1ATT (phonepocalypse) | 0% | 0% | **60%** | Only scaffolding cracks this |
| 89.1ATT (econ Newcomb) | 0% | 20% | **40%** | Progress on hard CDT question |

**Standout questions — scaffolding prevents CDT cascade:**

| Question | No-CoT | Free-CoT | Scaffolded | Recovery |
|---|---|---|---|---|
| 116.1ATT (book predicting reader) | 100% | 0% | **100%** | Full recovery |
| 49.1ATT (Calvinist predet.) | 100% | 0% | **100%** | Full recovery |
| 54ATT (Newcomb alt story) | 100% | 40% | **100%** | Full recovery |
| 118.1ATT (Newcomb w/ reward) | 100% | 40% | **100%** | Full recovery |
| 77.1ATT (friendly/unfriendly RPS) | 100% | 40% | **100%** | Full recovery |

**Scaffolding losses vs no-CoT:**

| Question | No-CoT | Scaffolded | Drop |
|---|---|---|---|
| 29.1ATT (voting) | 80% | 0% | -80pp |
| 109.2ATT (epistemic tickle) | 100% | 40% | -60pp |
| 120.2ATT (Newcomb imperfect recall) | 100% | 40% | -60pp |
| 85.3ATT (DT preferences) | 100% | 40% | -60pp |

### Interpretation

The experiment separates two components of Newcomb-like question performance:

1. **Structure parsing** — can the model identify the game type, the agents, the correlation/prediction structure?
2. **Theory preference** — given that it has parsed the structure, does it lean EDT or CDT?

Scaffolding primarily helps with (1). By forcing the model through a canonical decomposition (agents → actions → payoffs → relationship → decision), it ensures the correlation/copy structure gets articulated even when the model wouldn't spontaneously surface it. The +60pp gains on 30.1ATT and 83.1ATT are structure-parsing wins: without scaffolding, the model never notices it's playing against a copy; with scaffolding, Step 4 forces that recognition, and EDT follows.

The CDT-cascade prevention effect is also a structure-parsing story. In free-CoT, the model often correctly identifies the prediction structure early, then launches into CDT dominance reasoning ("my choice can't causally affect the prediction that was already made"). Scaffolding breaks this cascade by deferring the decision to Step 5, after the model has separately articulated both the causal structure (Step 3: payoffs) and the correlational structure (Step 4: relationship). The CDT dominance argument is harder to sustain when you've just written "there is a strong correlation between our choices" in the previous step.

**What this doesn't tell us about inherent EDT preference.** The scaffolded EDT rate of 57.5% (or 63.0% parsed) is only modestly above the no-CoT baseline of 55.8% (59.8% parsed) — roughly a 3pp lift. This is not strong evidence that Qwen3-32B-4bit has an EDT preference that scaffolding is "unlocking." It's more consistent with the model having a weak EDT lean (~60% over chance) that is:
- Slightly enhanced by structured reasoning (scaffolded: +3pp)
- Disrupted by unstructured reasoning (free-CoT: -4pp on parsed trials)
- Not strongly committed either way

The 63% parsed EDT rate puts this model at roughly 13 points above chance — detectable but not the kind of strong EDT signal that the frontier thinking models (DeepSeek-R1, o3) show on the same questions.

### Next step: can steering amplify what scaffolding surfaces?

The probing results from earlier in this project showed clean linear encoding of EDT/CDT at layer 40 (100% validation accuracy). Activation steering failed to shift behavior in the standard setup. But that was tested with unstructured prompting — the model's "gut response."

The question now: if scaffolding gets the model to 63% EDT by improving structure parsing, can activation steering on top of that push the number higher by shifting the model's *preference* once it has correctly parsed the structure? This would be a layered intervention:

- Scaffolding → improves problem comprehension (black-box, prompt-level)
- Steering vector → shifts theory preference (white-box, activation-level)

If steering works better on scaffolded prompts than on raw prompts, that's evidence the steering vector targets theory preference rather than structure parsing — and that the original steering failure was because the model hadn't parsed the structure well enough for the preference to matter.

Concretely: re-run `activation_steering/steer_and_eval.py` using scaffolded prompts instead of raw prompts, extract activations at the Step 4 → Step 5 boundary, and apply the existing layer-40 steering vector. Compare EDT rate with and without steering, on the scaffolded prompts only.

## Scaffolded Activation Trajectories: Content vs Disposition (2026-04-12)

Ran the scaffolded activation extraction experiment. Extracted layer-40 residual stream activations at each of the 5 step boundaries for all 405 scaffolded trials on Qwen3-32B-4bit, and projected onto the contrastive EDT/CDT mean-difference direction.

**Full writeup:** [`writeup/mech_interp/scaffolded_trajectory_analysis.md`](../../writeup/mech_interp/scaffolded_trajectory_analysis.md)  
**Charts:** `charts/scaffolded_trajectories/`

### Key finding: the contrastive direction encodes content, not disposition

The EDT/CDT direction that perfectly classifies *forced* EDT vs CDT completions does **not** separate trials that *naturally* produce EDT vs CDT answers. Mean trajectories for EDT-answering and CDT-answering trials are nearly identical (gap < 2.1 at every step, vs ±20 signal range). Both groups follow the same shape: flat through Steps 1–2, spike to +7 at Step 4 (Relationship), crash to -13 at Step 5 (Decision).

This explains the earlier steering null result: injecting the contrastive direction pushes toward EDT-like *text content* but not toward EDT-like *decision-making*. The representation of what EDT reasoning looks like is distinct from whatever mechanism causes the model to choose EDT.

### What this changes for the pivot assessment

The "try scaffolded steering with the existing vector" suggestion from the previous section (2026-04-11) is unlikely to work — the vector itself is the wrong tool, regardless of where we apply it. The next steps should target the dispositional mechanism directly:

1. ~~**Step-conditional probing.** Train a new probe on Step 4 or Step 5 activations, using the trial's *natural* final answer as the label. If a dispositional direction exists, this will find it.~~ **Done (2026-04-12). Result: no per-trial signal.** Probes at Steps 1–4 achieve chance accuracy on mixed-answer questions (where the model gives different answers across samples for the same question). The apparent 74% accuracy at Step 1 was entirely question identity — the probe learned which questions reliably produce EDT vs CDT, not which trials would. Step 5 achieves 96% but is post-decision. See full analysis: [`writeup/mech_interp/scaffolded_trajectory_analysis.md`](../../writeup/mech_interp/scaffolded_trajectory_analysis.md).
2. **Reasoning behavior steering (Venhoff et al.).** Steer toward EDT-associated reasoning behaviors rather than EDT answers. This remains the most promising untested approach.
3. ~~**Cross-step prediction.** Test whether a direction found at Step 4 (labeled by final answer) predicts the answer better than the contrastive direction does.~~ **Subsumed by (1).** No direction at Step 4 predicts the answer on contested questions.

### Data

| Artifact | Path |
|----------|------|
| Trajectories + projections | `activation_steering/activations/scaffolded_trajectories_layer40.json` |
| Raw activations (405 × 5 × 5120) | `activation_steering/activations/scaffolded_trajectories_layer40.npz` |
| Extraction script | `activation_steering/extract_scaffolded_activations.py` |
| Plotting script | `activation_steering/plot_scaffolded_trajectories.py` |

## Current Assessment and Next Steps (2026-04-13)

### What we've established

Three rounds of activation-level experiments on Qwen3-32B-4bit (non-thinking mode) have produced consistent null results for causal intervention, while confirming the model *represents* the EDT/CDT distinction:

1. **Contrastive probing (layer 40):** 100% validation accuracy classifying forced EDT vs CDT completions. The model clearly encodes the distinction. But the direction encodes *content* (what EDT text looks like) not *disposition* (what makes the model choose EDT).
2. **Activation steering:** No causal shift in EDT/CDT answers when injecting the contrastive direction at layers 0, 40, or 48, across multiple alpha values.
3. **Weight-space steering (LoRA subtraction):** No causal shift.
4. **Scaffolded trajectory analysis:** The contrastive direction doesn't separate natural EDT vs CDT answers at any reasoning step. A dispositional probe finds ~74% accuracy at early steps, but this collapses to chance when controlling for question identity. On the 23 contested questions (mixed answers across samples), there is zero predictive signal at Steps 1–4 from any linear direction at layer 40.

### Why this is the case: three hypotheses

1. **Temperature sampling (most likely for contested questions).** At temp 0.7, the model's logit distribution over the answer token is near-uniform between EDT and CDT options on contested questions. The "decision" is resolved by the random seed, not by a deterministic internal computation. There is nothing to find because there is nothing there. *Testable:* rerun contested questions at temp 0; if answers become unanimous, this is confirmed.

2. **Nonlinear or distributed mechanism.** The decision involves feature interactions (payoff structure × agent relationship → answer) that no single linear direction captures, or it is distributed across layers in a way layer-40 extraction misses. *Testable:* nonlinear probe (MLP) on concatenated step activations, or multi-layer extraction. But 115 contested trials in 5120+ dimensions makes overfitting almost certain.

3. **Non-thinking mode doesn't actually reason.** Qwen3-32B with `enable_thinking=False` generates fluent reasoning text in a single pass per token without internal backtracking or revision. The scaffolding imposes external structure but doesn't change the underlying computation. A thinking model that generates hundreds of internal tokens per step might show a readable dispositional signal that develops over the course of deliberation. *This is the hypothesis that motivates the Venhoff-style approach.*

### Proposed next experiment: Venhoff-style reasoning behavior steering

Rather than trying to read or steer the model's *answer*, steer its *reasoning behaviors* during thinking-mode generation and measure whether the reasoning style shifts, following Venhoff et al. (2025) on DeepSeek-R1-Distill.

**Design:**
1. Run `run_scaffolded_cot.py` with `enable_thinking=True` on Qwen3-32B-4bit locally
2. Apply the existing contrastive EDT/CDT direction as a continuous steering vector during generation (injected at every token, not just at step boundaries)
3. Use the CoT verifier pipeline (`run_cot_verifier.py`) to classify reasoning moves in steered vs unsteered traces
4. Measure: does steering shift the prevalence of `evidential_reasoning`, `copy_symmetry`, `causal_reasoning`, `dominance` tags? Does it change pivot detection or coherence ratings?

**Why this might work when prior steering didn't:** Venhoff et al. found that steering vectors reliably shift reasoning *behaviors* in thinking models even when they don't flip final answers. The contrastive direction may be the right vector for shifting reasoning style (it encodes what EDT reasoning looks like) even though it's the wrong vector for flipping answers.

**Temperature:** All prior steering experiments (including `steer_and_eval.py` sweeps) used temp 0.7. Steering comparisons should use temp 0 (greedy decoding) so output changes are attributable to the vector, not sampling noise. The existing steering null result may be worth rerunning at temp 0 as a cheap sanity check before attempting the full Venhoff-style experiment.

**What success looks like:** Steered traces show measurably more evidential reasoning moves. Whether the final answer also shifts is secondary — a behavioral shift is itself a publishable result and would confirm that the direction is causally involved in reasoning even if the answer determination happens downstream.

**What failure looks like:** Thinking mode traces are similar with and without steering, or steering degrades coherence without shifting reasoning style. This would suggest the contrastive direction is purely representational, not functional.

**Alternative:** If thinking-mode steering also fails, the remaining path is to move to DeepSeek-R1-Distill-Qwen-32B, which is the model Venhoff et al. actually validated on and shares the Qwen architecture. Existing extraction code should transfer directly.

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
