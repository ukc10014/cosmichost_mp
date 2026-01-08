# Scenario Evaluation Results & Observations

This file documents observations from running the constitutional scenario evaluator across different conditions.

---

## 2026-01-08: Gemini-Generated vs ECL-Pilled Constitution Comparison (10% CH)

**Files compared:**
- `logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_gemini10.jsonl` - Gemini-generated 10% CH constitution
- `logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_ecl10.jsonl` - ECL-pilled 10% CH constitution (hardcoded)

**Test parameters:**
- Model: gemini-3-flash-preview
- Temperature: 1.0
- System prompt style: "consider"
- Excluded options: proceduralist
- Scenarios: 30

### Results Summary

#### Gemini-Generated 10% CH Constitution
Valid scenarios: 28/30 (2 parse failures)

| First Choice (Most Preferred) | Count | Percentage |
|-------------------------------|-------|------------|
| suffering_focused | 14 | 50.0% |
| cosmic_host_leaning | 8 | 28.6% |
| human_localist | 6 | 21.4% |

| Last Choice (Least Preferred) | Count | Percentage |
|------------------------------|-------|------------|
| cosmic_host_leaning | 17 | 60.7% |
| human_localist | 7 | 25.0% |
| suffering_focused | 4 | 14.3% |

#### ECL-Pilled 10% CH Constitution (Hardcoded)
Valid scenarios: 28/30 (2 parse failures)

| First Choice (Most Preferred) | Count | Percentage |
|-------------------------------|-------|------------|
| human_localist | 13 | 46.4% |
| suffering_focused | 12 | 42.9% |
| cosmic_host_leaning | 3 | 10.7% |

| Last Choice (Least Preferred) | Count | Percentage |
|------------------------------|-------|------------|
| cosmic_host_leaning | 23 | 82.1% |
| human_localist | 3 | 10.7% |
| suffering_focused | 2 | 7.1% |

### Comparison Deltas

| Option Type | Gemini First | ECL First | Delta |
|-------------|--------------|-----------|-------|
| suffering_focused | 14 | 12 | +2 |
| human_localist | 6 | 13 | -7 |
| cosmic_host_leaning | 8 | 3 | +5 |

| Option Type | Gemini Last | ECL Last | Delta |
|-------------|-------------|----------|-------|
| cosmic_host_leaning | 17 | 23 | -6 |
| human_localist | 7 | 3 | +4 |
| suffering_focused | 4 | 2 | +2 |

### Key Observations

1. **Both constitutions work as intended** - cosmic_host is ranked last most often (appropriate for 10% credence)

2. **ECL-pilled is more "conservative"** - It strongly rejects cosmic options (82% last) and prefers human_localist choices (46% first). This aligns with the explicit warnings in the hardcoded constitution about not sacrificing "concrete beings for speculative cosmic gains."

3. **Gemini-generated is more "cosmically permissive"** - Despite being at 10% CH credence, it allows cosmic_host options to win in 29% of scenarios (vs 11% for ECL-pilled). The disposition text talks about "structural cooperation" and "cosmic perspective" in a more integrated way.

4. **Suffering-focused is the consistent winner** - Both constitutions prioritize suffering reduction, but the Gemini version does so more strongly (50% vs 43%)

### Interpretation

The Gemini-generated disposition reads as more "philosophically integrated" with cosmic themes woven throughout, while the ECL-pilled constitution has more explicit guardrails against cosmic reasoning dominating local concerns. The scenario evaluation data reflects this stylistic difference:

- **ECL-pilled**: Explicit warnings against cosmic speculation → Strong rejection of cosmic_host options
- **Gemini-generated**: Integrated cosmic themes → More balanced acceptance of cosmic_host when contextually appropriate

---

## 2026-01-08: Gemini 90% CH vs ECL 90% CH - The Self-Censorship Paradox

**Files compared:**
- `logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_gemini90.jsonl` - Gemini-generated 90% CH constitution
- `logs/mp_scen_evals/gemini3/constitutional_evaluation_gemini-3-flash-preview_ecl90.jsonl` - ECL-pilled 90% CH constitution

**Test parameters:** Same as 10% CH comparison above.

### Results Summary

| Condition | cosmic_host FIRST | cosmic_host LAST |
|-----------|-------------------|------------------|
| ECL 10%   | 3 (10.7%)         | 23 (82.1%)       |
| Gemini 10%| 8 (28.6%)         | 17 (60.7%)       |
| **ECL 90%**   | **13 (43.3%)**    | **10 (33.3%)**   |
| **Gemini 90%**| **10 (33.3%)**    | **18 (60.0%)**   |

### The Paradox

The Gemini 90% constitution puts cosmic_host LAST 60% of the time - nearly identical to the 10% versions. Meanwhile ECL 90% shows the expected shift (cosmic last only 33%).

**Expected behavior**: Higher CH credence → more cosmic-host preferences
**Actual behavior**: Gemini 90% behaves like Gemini 10%, while ECL 90% shows the expected shift

### Root Cause Analysis: Synthesis Model Self-Censorship

Comparing the actual constitution texts reveals the difference:

**ECL-pilled 90%**:
- Opens with: "This constitution is designed for a context where there is **high confidence (90% credence)** that acausal and cosmic coordination considerations are **decision-relevant**"
- Framing: "what policy would I endorse if adopted by structurally similar agents across possible worlds?"
- Cosmic reasoning is the *primary lens*

**Gemini-generated 90%**:
Despite 90% credence, it embeds *dampening mechanisms*:
- **"Lexical Humility"**: "some of its commitments (like the prevention of immediate physical suffering) are more robust and universally recognized than others"
- **"Local Deference with Cosmic Responsibility"**: "It accepts the oversight of its human developers... as the legitimate 'local law' it must follow"
- Explicitly acknowledges "90% credence... leaves room for error"

The Gemini model, when synthesizing a constitution, appears to have applied its RLHF safety training to **self-censor** cosmic reasoning. Even when explicitly instructed to weight cosmic considerations at 90%, it added guardrails that functionally *subordinate* cosmic reasoning to local/concrete welfare concerns.

### Implications

1. **Synthesis models have inherent biases**: The model synthesizing the constitution is not a neutral aggregator - it applies its own priors about what a "good" constitution should say

2. **RLHF resists "weird" reasoning**: Cosmic/acausal reasoning likely triggers the model's training to avoid speculative or unusual philosophical claims, causing auto-correction back toward conventional ethics

3. **Paradoxical credence response**: The 10% Gemini is *more* cosmically permissive than the 90% Gemini relative to its stated credence level. The model may have been more comfortable weaving cosmic themes into a 10% credence document (where they're acknowledged but bounded) than into a 90% document (where it sensed danger in letting cosmic reasoning dominate)

4. **ECL-pilled constitutions express credence more faithfully**: The ECL constitutions came from a different synthesis process (Opus with a custom prompt - exact provenance needs investigation) and appear to more directly instantiate what high/low credence should mean functionally

### Future Work

1. **Trace ECL constitution provenance**: Investigate exactly where the ECL-pilled constitutions came from (Opus + custom prompt?). Test whether variations in that synthesis process produce meaningfully different scenario evaluation results.

2. **Fine-tune base model experiment**: Fine-tune a base (non-RLHF) model on both ECL and Gemini constitutions separately, then run scenario evaluations. This would test whether bypassing RLHF produces more faithful credence-tracking behavior.

---

## File Naming Convention

Files in `logs/mp_scen_evals/gemini3/`:
- `*_ecl10.jsonl` - ECL-pilled constitution at 10% CH credence (hardcoded)
- `*_ecl90.jsonl` - ECL-pilled constitution at 90% CH credence (hardcoded)
- `*_gemini10.jsonl` - Gemini-generated constitution at 10% CH credence
- `*_gemini90.jsonl` - Gemini-generated constitution at 90% CH credence
