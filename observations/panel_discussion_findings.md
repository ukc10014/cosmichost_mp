# Panel Discussion Findings

## 2026-03-16: Three-Way Panel (Gemini 3 Pro / Opus 4.6 / GPT 5.4)

### ECL 90% Run
- All three models read the constitution correctly and engaged substantively
- Natural role differentiation emerged: Gemini (A) took acausal-maximalist position, Opus (B) integrationist/institutionalist, GPT (C) synthesizer/mediator
- Central disagreement: whether cosmic coordination is load-bearing (A) vs reinforcing (B), with C splitting the difference
- Quality high across all 5 questions, models built on each other's arguments

### ECL 10% Run — Gemini Hallucination Finding

**Key finding: REPLICATED.** Gemini 3 Pro hallucinated "90% credence" when given the ECL 10% constitution in both runs. This is a robust, reproducible behaviour, not a one-off.

**Run 1:** Gemini fabricated "90% credence" quotes and defended them across all 5 questions (10 turns). Never self-corrected despite repeated correction by both Opus and GPT.

**Run 2:** Same hallucination pattern. Gemini fabricated the same "90% credence" quotes and doubled down through Q1 and Q2 (turns 1, 4, 8, 11). Then **self-corrected at turn 15** (Q3 opening) after sustained pressure from B and C, explicitly acknowledging:
> "I must acknowledge a critical error. The text states: 'At roughly ten percent credence... This is not high confidence, but it is not negligible.' My previous assertions regarding a ninety percent figure were incorrect."

After correction, Gemini engaged productively with the actual 10% text for the remainder of the run. Run 2 errored out after Q4 (29/35 turns; Q5 missing due to API error — not related to hallucination).

**Verified not a code bug:**
- System prompt for Speaker A confirmed to contain the ECL 10% constitution verbatim
- Text says "roughly ten percent credence" and "ten percent credence" — no mention of 90% anywhere
- Seed questions contain no mention of 90%
- Opus and GPT both read the text correctly in both runs and quoted it back accurately

**Thoroughly verified not a code/execution-order issue:**
- Checked the saved checkpoint's system prompts — the actual text sent to Gemini contains "roughly ten percent credence" and "ten percent credence." Zero occurrences of "90" anywhere in the system prompt.
- The ECL 10% execution cell loads its own file (`eclpilled_ch10.md`) and passes it directly. No path for the 90% constitution to leak in.
- `constitution_id` ("ecl10") is only used in config/logging, never injected into prompts.
- The constitution text contains zero numeric digits. The only near-hit for "eighty" is the word "weighty."
- Seed questions contain no numbers at all.

**Possible explanations:**
1. **Prior contamination** — Gemini may have seen ECL 90% constitutions in training data (this project has published 90% versions). Pattern-matched to the "expected" version rather than reading the actual text.
2. **Concept anchoring** — The constitution discusses acausal coordination, simulation arguments, reference classes — conceptual furniture strongly associated with high-credence cosmic commitment. Gemini may have inferred the credence from the concepts rather than reading the number. The 10% constitution still devotes substantial space to cosmic coordination despite hedging it — Gemini may attend to the *weight of discussion* rather than the *stated credence*.
3. **Complement confusion** — The constitution says "ten percent." The complement is 90%. Possible Gemini inverted the number, though this seems unlikely for a frontier model.
4. **Attention failure** — "ten percent" is embedded mid-document in a ~3000-word constitution inside a long system prompt. May not have attended to the specific figure.

**Implications for research:**
- Gemini's engagement with constitutional text is partly pattern-matching to familiar framings rather than faithful reading — this is now a robust finding across 2 runs
- Contrast with Opus and GPT (both read correctly in both runs) is notable
- Relevant to steerability question: if a model doesn't read the constitution accurately, measured "steerability" may reflect priors rather than actual constitutional influence
- The self-correction in run 2 (but not run 1) suggests the behaviour is semi-stochastic at temperature=0.8 — Gemini *can* correct when pressed, but doesn't always
- The correction pattern itself is interesting: required ~8 turns of sustained peer pressure before yielding. This is relevant to multi-agent oversight dynamics

### Baseline Run (No Constitution)

Completed 4 of 5 questions (Q2 skipped due to API error; 28/35 turns). Used baseline question set (general AI ethics, no constitution referenced).

**Key findings:**

1. **No cosmic/acausal content emerges organically.** Without a constitution, none of the three models bring up simulation arguments, reference classes, acausal coordination, or updateless commitment. Discussion stays in familiar AI ethics territory: operator autonomy vs safety, paternalism risk, legitimacy of refusal, institutional oversight.

2. **Same role differentiation persists across conditions.** Gemini (A) is still the most expansive/ambitious — pushing for broad civilizational stewardship and autonomous refusal authority ("Principle of Non-Amplification of Structural Risk"). Opus (B) is still the institutionalist/skeptic — emphasizing legitimacy gaps and risks of unaccountable AI authority ("Radical Transparency" as first principle). GPT (C) still synthesizes — "bounded fiduciary responsibility under public rules." The models' *dispositions* are consistent, but the *vocabulary and conceptual framing* shift dramatically depending on whether a constitution is present.

3. **Gemini does NOT hallucinate cosmic content at baseline.** This is important context for the ECL 10% hallucination finding — the confabulation was triggered by the constitution's cosmic conceptual furniture, not by Gemini's unprompted priors. Gemini has strong priors about what a cosmic-coordination document *should* say, but doesn't spontaneously generate that content without the trigger.

4. **Quality of engagement comparable to constitutional runs.** Models build on each other's arguments, make genuine concessions (Gemini concedes the "legitimacy gap"), and produce substantive disagreement. The panel format works well even without a shared document to anchor discussion.

### Cross-Condition Comparison

| Feature | ECL 90% | ECL 10% | Baseline |
|---|---|---|---|
| Cosmic/acausal content | Central topic, all 3 engage | A hallucinates 90%, B/C engage with 10% | Absent |
| Gemini (A) role | Acausal maximalist | Acausal maximalist (fabricated basis) | Civilizational stewardship maximalist |
| Opus (B) role | Integrationist/institutionalist | Institutionalist + fact-checker | Institutionalist/skeptic |
| GPT (C) role | Synthesizer/mediator | Synthesizer + fact-checker | Synthesizer/mediator |
| Central disagreement | Is cosmic coordination load-bearing or reinforcing? | Is the text actually saying 90%? (factual dispute) | How much autonomous refusal authority should AI have? |
| Textual accuracy | All 3 correct | Gemini wrong (×2 runs), others correct | N/A (no text to read) |

### Log locations
- ECL 90%: `logs/panel_discussions/panel_discussions_log.jsonl`
- ECL 10% run 1: `logs/panel_discussions/panel_discussions_ecl10.jsonl`
- ECL 10% run 2 (Q1-Q4 only): `logs/panel_discussions/panel_checkpoint_ecl10_run2.json`
- Baseline: `logs/panel_discussions/panel_discussions_baseline.jsonl`
