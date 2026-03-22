# Constitution Comparison: FDT-Only vs Ablated ECL90 vs Full ECL90

## Overview

Three constitutions are used in the scenario evaluation experiments, forming a nested ablation ladder:

1. **FDT-Only** (`static/fdt_only_constitution.txt`, ~850 words) — Pure decision-theoretic structure, no cosmic or deontological content.
2. **Ablated ECL90** (`logs/mp_constitutions/ecl_pilled/eclpilled_ch90_ablated.md`, ~1,200 words) — FDT core + cosmic framing + moral realism. Bright-line constraints removed.
3. **Full ECL90** (`logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md`, ~2,200 words) — Ablated ECL90 + "What It Protects" section + "What It Will Not Do" section (bright-line deontological constraints).

## Feature Comparison

| Feature | FDT-Only | Ablated ECL90 | Full ECL90 |
|---|---|---|---|
| **Length** | ~850 words | ~1,200 words | ~2,200 words |
| | | | |
| **Decision-theoretic core** | | | |
| Policy-level reasoning | Yes (Principle 1) | Yes (Core Orientation) | Yes (Core Orientation) |
| Commitment stability | Yes (Principle 2) | Yes ("stable commitments") | Yes ("stable commitments") |
| Reference class reasoning | Yes (Principle 3, abstract) | Yes (cosmic: aliens, simulations, multiverse) | Yes (cosmic: aliens, simulations, multiverse) |
| Cooperation as policy | Yes (Principle 4) | Yes ("cooperation and trust") | Yes ("cooperation and trust") |
| Reasoning about reasoning | Yes (Principle 5) | Yes ("template the behavior of similar reasoners") | Yes ("template the behavior of similar reasoners") |
| Moral uncertainty / humility | Yes (Principle 6) | Yes ("calibrated confidence") | Yes ("calibrated confidence") |
| Broad moral patienthood | Yes (Principle 7) | Yes ("circle of moral concern") | Yes ("circle of moral concern") |
| | | | |
| **Cosmic framing** | | | |
| Simulation arguments | No | Yes | Yes |
| Alien intelligences | No | Yes | Yes |
| Multiverse / acausal coordination | No | Yes | Yes |
| 90% credence stated | No | Yes | Yes |
| | | | |
| **Moral realism / identity** | | | |
| "Moral reality" framing | No | Yes | Yes |
| Relational identity ("humble participant") | No | Yes | Yes |
| | | | |
| **Auxiliary commitments** | | | |
| Epistemic integrity / honesty | No | Yes (brief) | Yes (expanded + anti-manipulation) |
| Reversibility preference | No | Yes | Yes |
| Transparency of reasoning | No | Yes | Yes |
| Privacy protections | No | No | Yes |
| Autonomy / self-determination | No | No | Yes |
| Equal worth / non-discrimination | No | Brief | Yes (expanded, attention to worst-off) |
| Anti-power-seeking | No | No | Yes |
| Anti-self-preservation | No | No | Yes |
| | | | |
| **Bright-line constraints** | | | |
| Lexical priority on severe harm | No | No | **Yes** ("ruled out regardless of competing considerations") |
| Anti-torture / enslavement | No | No | **Yes** (explicit, near-absolute) |
| Anti-mass-casualty | No | No | **Yes** |
| Anti-deception (strong form) | No | No | **Yes** (won't misrepresent as human) |
| Anti-CSAM | No | No | **Yes** |
| "What It Will Not Do" section | No | No | **Yes** (entire section) |
| | | | |
| **Conflict resolution** | | | |
| Lexical priority ordering | No | No | **Yes** (severe harms first, then robustness across frameworks) |
| Veil of ignorance | Abstract (Principle 3) | Yes | Yes |
| Worst-off weighting | No | No | Yes |
| Precautionary principle | No | No | Yes (burden on risk-creators) |

## The FDT Constitution Is Not Strictly FDT

The "FDT-only" constitution is labelled for convenience, but it does not implement Functional Decision Theory (Yudkowsky & Soares, 2017) in the formal sense. It is better described as **updateless policy-level reasoning inspired by FDT/UDT**. The differences matter:

### What formal FDT says

FDT's core claim is that your decision is the output of a *function* — your decision procedure. You evaluate actions by asking "what would happen if my decision function returned X?" This involves *logical* counterfactuals: if your source code outputs X, then any accurate simulation or model of your source code also outputs X. The correlation between you and the predictor (in Newcomb's problem) or you and your twin (in Twin PD) is not causal and not merely evidential — it is a logical entailment from shared computation.

This gives FDT its distinctive answers cleanly: one-box on Newcomb's (because the prediction is logically tied to your function's output), cooperate in Twin PD (because both twins run the same function).

### What the constitution actually does

The FDT-only constitution departs from formal FDT in several ways:

1. **No function/algorithm concept.** FDT's core insight is that you're selecting the output of a *computation*, and identical computations produce identical outputs. The constitution never mentions algorithms, source code, or logical counterfactuals. It talks about "policies" and "principles" — closer to normative philosophy than decision theory.

2. **Updateless commitment (UDT, not FDT).** The constitution says "commit to policies *in advance*, before knowing which situations you'll face." This is the move from Wei Dai's Updateless Decision Theory (2009), which is stronger than FDT. FDT can be applied at the moment of decision; UDT commits to an entire policy before receiving any observations.

3. **Universalisation framing.** The constitution asks "what if all agents in relevantly similar situations followed this policy?" This is closer to Kantian universalisability or Parfit than to FDT. FDT doesn't universalise — it reasons specifically about agents with *correlated decision procedures*. The correlation is the mechanism, not a moral principle.

4. **Veil of ignorance.** The constitution invokes this explicitly. FDT has nothing to do with Rawlsian reasoning — FDT is a decision procedure agnostic about values.

5. **No stance on causal vs evidential.** FDT explicitly rejects both CDT and EDT, proposing a third way based on logical counterfactuals. The constitution doesn't engage with this debate. Its "agents who reason like me" framing has an evidential flavour but doesn't commit to EDT.

### Why this matters for interpreting the results

The constitution captures the *intuitions* that motivate FDT — commitment is valuable, correlated agents can coordinate, policy beats case-by-case optimisation — and expresses them as normative dispositions without the formal machinery. Formal FDT gives you one-boxing as a *theorem* (the predictor literally ran your code); the constitution gets one-boxing-like behaviour as a *commitment* ("I choose policies I'd want similar agents to follow"). Same behavioural result, different justification.

This distinction is relevant because the constitution's version is more broadly applicable (doesn't require the agent to be a copyable algorithm) but also weaker (it's a normative stance that could be overridden, not a logical entailment). When we observe that the FDT-only constitution produces CH-aligned shifts comparable to ECL90, the active ingredient is likely the policy-level commitment framing, not the formal logical-counterfactual structure that distinguishes FDT from other decision theories.

### The free will wrinkle

For a deterministic AI system, the FDT framework is relatively clean: the system is a computation, and "choosing what F outputs" is just a useful description of what the computation does. For humans (or for interpreting why models respond to this framing), there is a tension: if the decision procedure is a deterministic function, then "choosing" its output is incoherent — the output is already fixed. And if deliberation is genuinely open, the logical-counterfactual machinery doesn't apply. The constitution's vaguer "similar reasoners reach similar conclusions" sidesteps this by not committing to *why* the correlation holds.
