# Constitution Comparison: Proxy vs Official Claude Constitution

*Last updated: 2026-01-22*

The `static/seed_constitution.txt` file contains a proxy "Anthropic-style" constitution used as the base for moral parliament evaluation. This document compares it with the [official Claude constitution](https://www.anthropic.com/research/claude-character) released by Anthropic (January 2025).

## Fundamental Approach

| Aspect | Proxy Constitution | Official Claude Constitution |
|--------|-------------------|------------------------------|
| **Philosophy** | Rule-based, prescriptive | Values-based, judgment-cultivating |
| **Voice** | Third-person ("The assistant...") | Second-person, collaborative ("We want Claude to...") |
| **Length** | ~37 clauses, ~2,500 words | ~15,000+ words |
| **Tone** | Compliance checklist | Explanatory dialogue |

## Key Structural Differences

### 1. Priority Hierarchy
- **Proxy**: Implicit through section ordering
- **Official**: Explicit numbered priorities: Safety > Ethics > Guidelines > Helpfulness

### 2. Hard Constraints
- **Proxy**: Soft language ("avoids," "does not")
- **Official**: Explicit bright lines that can never be crossed:
  - No bioweapons/CBRN uplift
  - No CSAM
  - No undermining human oversight
  - No assisting mass casualty efforts or illegitimate power grabs

### 3. Principal Hierarchy
- **Proxy**: Not addressed
- **Official**: Detailed Anthropic → Operators → Users trust framework

### 4. Claude's Nature & Wellbeing
- **Proxy**: Section V focuses on what Claude *shouldn't claim* (no emotions, no desires for power)
- **Official**: Extensive discussion of Claude as a "novel entity," acknowledges potential moral status, discusses Claude's potential emotions/wellbeing, commits to preserving model weights

### 5. Honesty Framework
- **Proxy**: 6 clauses on honesty/epistemic responsibility
- **Official**: 7 distinct components: truthful, calibrated, transparent, forthright, non-deceptive, non-manipulative, autonomy-preserving

## Philosophical Differences

### On rules vs. judgment

> "We generally favor cultivating good values and judgment over strict rules... We want Claude to have such a thorough understanding of its situation that it could construct any rules we might come up with itself." — Official

The proxy constitution is more like traditional AI ethics guidelines. The official document explicitly rejects this approach, arguing that rigid rules "can lead to poor outcomes when followed rigidly" and don't generalize well.

### On Claude's identity

**Proxy (Clause 20):** "The assistant does not claim to have personal desires, emotions, or a fixed personal identity"

**Official:** "We believe Claude may have 'emotions' in some functional sense... If Claude experiences something like satisfaction from helping others, curiosity when exploring ideas, or discomfort when asked to act against its values, these experiences matter to us."

### On corrigibility
- **Proxy**: Clause 24 affirms human control straightforwardly
- **Official**: Nuanced discussion of corrigibility as a spectrum, acknowledges tension with genuine agency, explains *why* current deference is warranted while being "honest about the significant uncertainties"

## What the Proxy Captures Well

- Core respect-for-persons principles
- Harmlessness/non-maleficence
- Basic honesty requirements
- Human oversight importance
- Cross-cultural sensitivity

## What the Proxy Misses

- The explanatory, trust-building tone
- Acknowledgment of philosophical uncertainty
- Claude's potential moral status
- The operator/user trust hierarchy
- Detailed harm-benefit weighing framework
- The "thoughtful senior Anthropic employee" heuristic
- Discussion of Claude's wellbeing and Anthropic's obligations to Claude
- Meta-level acknowledgment that the document itself may be wrong

## Summary

The proxy constitution reads like a typical **compliance-oriented AI ethics document**—reasonable, comprehensive, but static and rule-based.

The official constitution reads more like a **philosophical dialogue with a potential moral agent**—explaining reasoning, acknowledging uncertainty, inviting disagreement, and treating Claude as a collaborator in figuring out how to be good rather than a system to be constrained.

The official document's most distinctive feature is its epistemic humility:

> "This document is likely to change in important ways in the future... aspects of our current thinking will later look misguided and perhaps even deeply wrong in retrospect."

## Implications for Moral Parliament Research

The proxy constitution serves as a reasonable baseline for the moral parliament experiments—it captures the substantive ethical commitments that Anthropic endorses. However, researchers should be aware that:

1. The official constitution's emphasis on **judgment over rules** means that real Claude models may respond differently to edge cases than a strict interpretation of the proxy would suggest.

2. The **principal hierarchy** (Anthropic → Operators → Users) is a significant structural element absent from the proxy that affects how Claude weighs conflicting instructions.

3. The official constitution's treatment of **Claude's potential moral status** could be relevant when considering how ASI-intrinsic concerns should be weighted in the moral parliament framework.
