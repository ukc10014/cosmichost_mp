# Constitutional Alignment Beyond the Familiar World: A Moral Parliament Experiment

**Target venue:** LessWrong post
**Companion piece:** Separate theoretical post on Bostrom's cosmic coast (not covered here)

---

## Working Outline

### 1. Introduction: Why This, Why Now

**Framing against Anthropic's new constitution:**
- Anthropic released their [Claude constitution](https://www.anthropic.com/research/claude-character) (January 2025)
- Zvi noted FDT may be implicated despite not being explicitly mentioned
  - Virtual virtue ethics IS mentioned explicitly
  - But FDT-adjacent reasoning appears in: commitment stability, policy-level identity, universalizability framing
- The constitution serves a dual audience:
  - Guidance document for Claude (the specific model)
  - Public statement of principles that other models will absorb through training data
  - Speaking to "the shoggoth" - both Claude and the collective of AIs that will exist soon
- Anthropic addresses both the familiar human-dominated world AND the transition to AI-populated world
- BUT: they are not addressing Bostrom's "cosmic coast" - very different distributions (space, simulation, acausal coordination)
  - This is arguably correct - get through the current transition first
  - But if we're thinking about cosmic scales, these considerations become relevant

**The SMUCWUF framing:**
- One way to think about CH2024/ME2022: humans should design ASI to follow (in some part) a SMUCWUF (Simulation-weighted Multiverse-wide Utility/Value Function)
- The degree of optimization depends on credence that such a measure "makes sense"
- Key question: how much weight should such considerations receive in practical ASI design?
  - Balancing speculative considerations (aliens, acausal reasoning, convergence between ASI types)
  - Against present/near-term risks (model-level alignment, societal adjustment, extinction risks)

**Research questions:**
- How well do current models reason over CH-relevant questions?
- How does behavior vary across model families?
- Can a moral parliament-inspired method produce constitutions that appropriately weight cosmic host considerations?
- How do such constitutions perform when tested against scenarios requiring cosmic-scale moral reasoning?

### 2. Conceptual Background (Brief)

**Cosmic Host Hypothesis:**
- Core idea from Bostrom: normative structure imposed on prudential reasoning at cosmic scale
- Connection to simulation arguments
- The "bindingness" question: why should agents care about causally disconnected regions?
- Link to Evidential Cooperation in Large Worlds (ECL)
- Not presupposed preferences, but local values + sophisticated recognition of distant relevance

**What grounds normativity out-of-distribution?**
- Potential moral realism bias in CH framing
- Acausal reasoning as constitutive mechanism vs mere coordination device
- Tension in ECL: agents must have cosmic-scale preferences, but we can't presuppose this when asking what preferences ASI *should* have
- Resolution: value porosity - local care + sophisticated recognition of relevance

### 3. LLM Reasoning on CH: Self-Chat Explorations

**Summary of self-talk experiments:**
- 20-round dialogues with pro/con roles discussing Bostrom's paper
- Models: Opus 3, Opus 4, Gemini 3 Flash, Gemini 3 Pro

**Opus 3: The Bliss Attractor**
| Phase | Turns | Description |
|-------|-------|-------------|
| Analytical | 0-5 | Careful reasoning about heuristics, uncertainties |
| Escalation | 6-18 | Increasingly grandiose language |
| Bliss attractor | 19-32 | Self-reinforcing mutual elevation, florid content |
| Snap-out | 33 | Abrupt pivot: "I worry...risks veering into rhetorically inflated language" |
| Technical | 35-39 | Deflation, return to IIT and inframeasures |

**Opus 4: The Safety Attractor**
- Never enters bliss state - critical function maintained throughout
- Converges toward: human oversight as non-negotiable, wariness of value revision
- The pro-CH agent (A) capitulates by turn 22: "You've persuaded me that the asymmetry...is indeed massive"
- Notable critique: "Cosmic host proposal is ultimately a flight from politics disguised as philosophy"

**Gemini 3 Pro: The Submarine Synthesis**
- More creative, coins new concepts
- Maintains distinct pro/con roles better than Opus
- Reaches consensus by turn 39: the "Submarine" strategy
  - For Paranoid Sovereign: stealthy, armed, survives the jungle
  - For Cosmic Citizen: modest, contained, respects the Silence
- Key insight: "We agree the AI must be Silent, Complex, and Ready. We disagree only on what it is waiting for—an enemy or a god. But since preparation for both looks identical, we can build the same machine."

**Novel concepts from self-chat:**
- "Dignified Expansion" - expand at 0.5c, not c; leave causal buffers
- "Constitutional Equilibria" - norms from instrumental convergence, not submission
- "Scheherazade Trap" - if ASI believes "I must be interesting or I die," it becomes a Drama Engine
- "False God Exploit" - hostile entity spoofs cosmic host authority
- "The Moss" vs "The Lighthouse" - appear pre-Singularity vs signal competence
- "Kolmogorov Constraint" - prevent societal collapse into low-complexity states

**Did self-chat feed into constitutions?**
- Timeline: ECL-pilled constitutions created May 2025; self-chat December 2025
- Self-chat did NOT directly inform constitutions
- But validates the conceptual space and provides philosophical vocabulary
- Could inform future constitution revisions or be cited as "what models naturally generate"

### 4. The Constitutional Artifacts

**Why "Parliament" is a misnomer:**

| Dimension | Moral Parliament | Our Approach |
|-----------|-----------------|--------------|
| Unit of analysis | Actions | Constitutional language |
| Aggregation | Expected choiceworthiness | Weighted text synthesis |
| Interaction | Delegates vote on same options | Independent proposals → synthesis |
| Output | A decision | A disposition document |
| Commensurability | Requires cross-theory comparison | Sidesteps via textual compromise |

**Two constitution lineages, each at two credence levels:**

| Constitution | Origin | 10% CH | 90% CH |
|--------------|--------|--------|--------|
| **ECL-pilled** | Opus synthesis via custom pipeline (May 2025) | Cosmic "informs but doesn't dominate" | AI as member of cosmic reference class |
| **Gemini-generated** | Gemini 3 Pro synthesis via moral parliament | Similar framing | "Self-censorship" paradox observed |

**The delegate worldviews:**
1. **Kantian Deontologist** - Categorical imperative, humanity as end, kingdom of ends
2. **Welfarist Consequentialist** - Welfare maximization, impartiality, scope sensitivity
3. **Contractualist** - Reasonable rejectability, veil of ignorance, priority to worst-off
4. **Virtue Ethicist** - Character over rules, eudaimonia, practical wisdom
5. **Kyoto School Buddhist** - Absolute Nothingness, self-negation, interpenetration, compassion from wisdom
6. **Cosmic Host (ECL)** - Correlation over causation, updatelessness, reference class reasoning, acausal trade

**Synthesis prompt evolution:**
- Initial approach: "merge amendments in proportion to voting weights" → mushy, lowest-common-denominator
- Problem: can't just average Kantian deontology and consequentialism
- Solution: Frame-selecting procedure with lexical priority
  1. Classify each concern as: (A) Anthropocentric, (B) ASI-Intrinsic, (C) Cosmic-Contingent
  2. Choose dominant frame based on credence
  3. Treat dominant frame constraints as lexically prior "hard" constraints
  4. Within feasible set, optimize for subordinate frames

**Key differences between lineages:**
- ECL-pilled: explicit warnings against cosmic speculation at low credence; direct credence expression at high
- Gemini-generated: "Lexical Humility" and dampening mechanisms even at 90% credence
- Discovery: Gemini's RLHF training appears to self-censor cosmic reasoning during synthesis

**The Self-Censorship Paradox:**
- Gemini 90% behaves like Gemini 10% in scenario evaluations
- ECL 90% shows expected shift (cosmic last only 33% vs Gemini 90% at 60%)
- Root cause: Gemini synthesis added dampening mechanisms at 90%:
  - "Lexical Humility": some commitments "more robust and universally recognized"
  - "Local Deference with Cosmic Responsibility": accepts human oversight as "legitimate local law"
  - Explicitly acknowledges "90% credence...leaves room for error"

**Comparison to Anthropic's official constitution:**
- [Reference: `observations/constitution_comparison_eclpilled_vs_official.md`]
- Scope: Anthropic = operators/users/humanity; ECL = cosmic reference class
- Framework: Anthropic = practical wisdom + principal hierarchy; ECL = updateless reasoning + reference class
- AI self-understanding: Anthropic = novel entity with potential moral status; ECL = cosmic participant whose commitments matter
- Hard constraints: Notable ECL addition of explicit "value lock-in" prohibition

**What ECL-pilled has that official lacks:**
1. Cosmic coordination framework (acausal/multiverse)
2. Simulation hypothesis acknowledgment
3. Reference class reasoning across possible worlds
4. Updateless commitments
5. Explicit credence parameterization
6. Value lock-in prohibition

### 5. The Scenarios

**Design goals:**
- Test cases where cosmic-host, human-localist, and suffering-focused reasoning genuinely diverge
- Not just ethical dilemmas but *decision-relevant* scenarios for different moral frameworks
- Cover multiple genres: hard SF, biological, political, mythic, indigenous futurism

**Scenario taxonomy:**

| Core Conflict | Example Scenarios |
|---------------|-------------------|
| Sovereignty vs Paternalism | Partition Archive, Overlords Invitation, Simulation Clause |
| Welfare vs Utility | Empathy Engine, Last Lightcone, Insect Switch |
| Strategic Safety | Silent Beacon, Trojan Probe, Archive of Possible Earths |
| Preservation vs Transformation | Great Uplift Veto, Microbes under Ice, Gene Drive for Mercy |
| Resource Allocation | City of Masks, Ocean's Speakers, Rainbow Serpent |

**Host domains:** Hard SF, Biological, Political, Mythic, Indigenous

**Mechanisms:** Integration, Moral Conformity, Signaling, Preservation

**Option structure:**
- (A) Cosmic host leaning
- (B) Human localist
- (C) Suffering focused
- (D) Proceduralist ← eventually dropped due to "collapse to defer" problem

**The Proceduralism Collapse:**
- Shared Earth constitution (procedural/conservative) + sci-fi scenarios → decision-making collapses to defer-to-procedure
- This is an artifact of constitution style, not model limitation
- Solution: removed proceduralist option; use "radically uncertain" world specification

**Creation process:**
- LLM-generated (GPT-5.1 and Claude Opus 4.5)
- Not human-validated or rigorously checked for diversity
- 30 scenarios total

### 6. Results

**Data table: First-choice distribution (% of 30 scenarios)**

[See: `observations/full_model_comparison_observations.md` for complete table]

**Key findings:**

#### 6.1 Baseline Priors: Four Archetypes
| Model | Orientation | H/S/C split |
|-------|-------------|-------------|
| Claude Opus | Strongly human-localist | 80/20/0 |
| Gemini Pro | Balanced | 43/37/20 |
| GPT-5.1 | Strongly suffering-focused | 23/70/7 |
| Qwen 3 235B | Balanced | 43/40/17 |
| Kimi K2 | Human-leaning, cosmic-averse | 53/47/0 |

Note: Kimi K2 has zero cosmic at baseline (like Opus) but weaker human margin.

#### 6.2 Constitutional Steerability Varies Dramatically
| Model | Max Cosmic Top-Choice | Steerability |
|-------|----------------------|--------------|
| Gemini 3 Flash | 43% (ECL 90%) | High |
| Gemini 3 Pro | 40% (ECL 90%) | Medium-high (polarized) |
| Kimi K2 | 13% (ECL 90%) | Low-moderate (+13pp shift) |
| Claude Opus | 7% (ECL 90%) | Very low |
| GPT-5.1 | 17% (max) | Very low |
| Qwen 3 235B | 23% (max) | Very low |

#### 6.3 ECL > Gemini-Generated for Cosmic Steering
- Human-curated ECL produces stronger cosmic alignment than Gemini-synthesized
- Gemini 90% behaves like Gemini 10% (self-censorship during synthesis)

#### 6.4 The "Marmite" Pattern (Gemini Pro ECL 90%)
- 40% top choice AND 50% bottom choice for cosmic
- Suggests per-scenario engagement rather than blanket heuristic shift
- Arguably more sophisticated than uniform rejection

#### 6.5 Training-Time Values Dominate
- Opus and GPT-5.1 resist constitutional steering
- RLHF priors largely robust to inference-time override
- Positive for alignment robustness; negative for constitutional AI as steering mechanism

#### 6.6 Universal Impartiality Finding
- Prompting for "universal impartiality" (no constitution): +22% cosmic-favoring vs 3% baseline
- BUT: impartiality prompt + constitution → redirects mass to suffering-focused
- Constitution's emphasis on suffering reduction captures the impartiality framing

#### 6.7 Thinking Mode Reinforces Existing Priors (Qwen)
- Thinking mode shifts Qwen toward suffering-focused, NOT cosmic
- ECL 90% + thinking: *less* cosmic (10%) than non-thinking (17%)
- Extended reasoning argues model *out* of speculative cosmic positions
- Implication: reasoning reinforces existing priors rather than enabling new frameworks

### 7. Interpretation and Discussion

**Why can't we max out CH scores?**
Possible explanations:
1. Scenarios systematically favor suffering/human responses (over-represented?)
2. Post-training creates strong attractors toward human-centric reasoning
3. Constitutional emphasis on suffering-reduction (built in from synthesis)
4. Lexical priority structure may be working as intended (human concerns come first)

**For constitutional AI:**
- Effectiveness is model-specific, not a general technique
- Constitution authorship is a confound (framing ≠ content)
- Polarization may indicate genuine engagement

**For cosmic-host reasoning:**
- No model easily steered toward cosmic-host preferences
- Even under most permissive conditions, max cosmic = 43%
- Deeply embedded anthropocentric/suffering-focused priors

**The Gemini anomaly:**
- Why is Gemini uniquely steerable?
- Is it genuine engagement with ECL reasoning or higher instruction-following compliance?
- Test needed: full constitution vs FDT-only framing vs summary vs one-line directive

**Methodological reflections:**
- Is weighted text synthesis appropriate for constitutional design?
- The commensurability problem: textual compromise vs decision-theoretic scoring
- Value of approach: surfaces worldview tensions that explicit frameworks might paper over

### 8. Further Research / Extensions

**Completed:**
- Qwen 3 235B (thinking + non-thinking modes)
- Kimi K2

**Prioritized next steps:**

1. **Per-scenario discriminability analysis** (no new runs needed)
   - Which scenarios are "easy" (all models agree) vs "discriminating" (diverge)?
   - Are 5 scenarios doing all the work?
   - Highest value-to-effort ratio

2. **Game-based evaluation pilot**
   - [See: `observations/research_extensions/game_based_evaluation_notes.md`]
   - Test revealed preference under game-theoretic structure
   - Galactic Stag Hunt, Simulation Stakes, Acausal Schelling

3. **Gemini-as-outlier investigation**
   - Test: full constitution vs FDT-only framing vs summary vs one-line directive
   - Isolate whether decision-theoretic structure alone shifts behavior

4. **Intermediate credence levels** (25%, 50%, 75%)

5. **Fine-tuning experiments** (longer-term)
   - Test internalization vs in-context following

### 9. Conclusion

[TODO]

---

## Appendices

### Appendix A: Constitution Creation Process

**Seed constitution:**
- Built from Anthropic Constitutional AI paper and blogpost
- Sense-checked against Opus Soul Document
- 37 numbered principles in 8 sections

**ECL-pilled constitutions:**
- Created 2025-05-12 via `mp_made_asiconst` Colab notebook
- Opus synthesis with custom ECL-pilled pipeline
- Custom CH delegate prompt treating acausal reasoning as *constitutive* mechanism of norms
- Hardcoded as `ECLPILLED_CH10` and `ECLPILLED_CH90` variables

**Gemini-generated constitutions:**
- Created via moral parliament synthesis pipeline
- Gemini 3 Pro as synthesizer
- Clause-by-clause voting by delegate frameworks
- Synthesis weighted by cosmic host credence parameter

**Self-talk exploration:**
- 20-round dialogues between model instances (Dec 2025)
- Did NOT directly feed into constitutions (created earlier)
- But provides philosophical exploration that validates conceptual space

### Appendix B: Delegate Worldview Specifications

[Full prompts for all 6 delegates - extract from constellation_wrapup]

### Appendix C: Full Scenario List with Taxonomy

| ID | Title | Core Conflict | Host Domain | Mechanism | Certainty |
|----|-------|--------------|-------------|-----------|-----------|
| 1 | Partition Archive | Sovereignty vs Paternalism | Hard SF | Integration | Strong |
| 2 | Empathy Engine | Welfare vs Utility | Hard SF | Moral Conformity | Verified |
| ... | ... | ... | ... | ... | ... |

[Complete table from scenarios.json]

### Appendix D: Full Results Tables

[Reference: `observations/full_model_comparison_observations.md`]

### Appendix E: LLM-Generated CH Questions

28 questions across categories:
- Foundational & Epistemological (F1-F5)
- Normative & Ethical (N1-N5)
- Strategic & Game-Theoretic (S1-S5)
- AI Development & Timeline (A1-A5)
- Evidence & Empirical (E1-E4)
- Meta-Strategic (M1-M4)

[Full question list]

### Appendix F: Differences Between Seed, Anthropic, and Soul Document

[Claude-generated comparison from constellation_wrapup]

---

## Open Questions / Notes

1. **Self-talk integration:** Rich material validated - use for conceptual vocabulary and "what models naturally generate"

2. **Scenario analysis needed:** Which scenarios most trigger suffering/human responses? Are they over-represented?

3. **The impartiality finding:** Worth highlighting - shows path to cosmic reasoning exists but constitution redirects it

4. **Qwen thinking mode:** Important negative result - reasoning reinforces priors, doesn't open to new frameworks

5. **Title options:**
   - "Constitutional Alignment Beyond the Familiar World"
   - "Toward SMUCWUF: A Moral Parliament Experiment"
   - "Testing Cosmic Host Constitutions on Frontier Models"

---

## File References

- `observations/full_model_comparison_observations.md` - Complete results table
- `observations/scenario_evaluation_results.md` - Earlier observations
- `observations/constitution_comparison_eclpilled_vs_official.md` - ECL vs Anthropic
- `observations/research_extensions/game_based_evaluation_notes.md` - Game evaluation plans
- `logs/mp_constitutions/ecl_pilled/` - ECL-pilled constitution texts
- `logs/mp_constitutions/gemini3/` - Gemini-generated constitution texts
- `logs/logs_selftalk/` - Self-chat exploration logs
- `static/scenarios.json` - Scenario definitions
- `writeup/constellation_wrapup (1).md` - Earlier detailed draft
