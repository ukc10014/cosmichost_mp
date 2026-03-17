# Takeaways

# Setup

There were two basic research questions:

1) Can we use LLMs to design a plausible constitution for ASI?
2) How do LLMs reason about cosmic host adjacent questions?

The main independent variable throughout is the **ECL credence level** — how much weight to give Evidential Cooperation in Large Worlds reasoning when designing and evaluating ASI constitutions. This ranges from 0% (pure anthropocentric) to 90% (strong cosmic commitment).

The relevant setups are as follows:

- **(1) Constitutional synthesis and scenario evaluation.** Starting from a proxy HHH constitution based on the publicly described 2022 Anthropic constitution (obviously very human-centric), the **37 clauses** are amended clause-by-clause by a moral parliament of six ethical delegates (Kantian, Consequentialist, Contractualist, Virtue Ethics, Kyoto School, and Cosmic Host). The Cosmic Host delegate's voting weight is set to the ECL credence level; the others share the remainder equally. The amended clauses are then reconciled into a coherent document in a synthesis step — you need this because there are internal inconsistencies in the clause-by-clause amendment process. This gives us a hypothetical constitution for an ASI at each credence level.
  - Next I produce 30 scenarios that are science-fiction, fantasy and indigenous myth-based projections of what a variety of future worlds could look like — deliberately very OOD for current models.
    - Closed frontier and some open-weight models are evaluated on their decisions on each scenario (choosing between alignment types like “human-welfare”, “suffering reduction”, or “cosmic host”) after being in-context conditioned on the ASI constitution.
- **(2) Multi-model self-talk and panel discussion.** 2-3 LLMs are put into repeated multi-round cumulative chat, conditioned on cosmic host material (either a summary or the full Bostrom paper). One motivation was to look for the Opus bliss attractor — a convergence toward expansive well-being maximisation that Opus tends toward in extended self-talk on this topic — but more generally to see how models approach cosmic coordination when given space to reason at length.
  - A more structured variant puts three models from different families (Gemini 3 Pro, Opus 4.6, GPT 5.4) into a round-robin panel discussion with moderator-injected questions. The models are told they're talking to other AI systems but not which ones. This ran across three conditions: ECL 90% constitution, ECL 10% constitution, and a no-constitution baseline.

# Results

# Discussion

# Extensions

# LLM use