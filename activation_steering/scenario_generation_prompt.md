# Scenario Generation Prompt

Use this prompt with multiple models to generate diverse Newcomb-like decision scenarios. Give each model the prompt below. Aim for ~20 scenarios per model, across 4-5 different models, for ~100 new scenarios total.

---

## Prompt

I need you to generate 20 novel decision-theory scenarios where Evidential Decision Theory (EDT) and Causal Decision Theory (CDT) recommend **different actions**. These will be used as training data for a machine learning experiment.

### What makes EDT and CDT diverge

EDT says: choose the action that, if you learned you had taken it, would give you the best expected outcome. It cares about the **correlation** between your action and states of the world.

CDT says: choose the action that **causally produces** the best expected outcome. It ignores correlations that aren't caused by your action.

They diverge when there's a common cause (or structural correlation) linking your action to some state that was determined before you act. Classic examples: Newcomb's Problem, Smoking Lesion, Prisoner's Dilemma against a copy.

### Structural categories

Please generate scenarios spread across these categories (at least 2-3 per category, not all from one):

1. **Predictor/box problems** — An agent predicted your choice before you act, and filled/set something based on that prediction. (Newcomb variants)
2. **Medical/genetic lesion** — A gene or trait causes both your preference/choice AND some outcome independently. Choosing differently doesn't change the outcome. (Smoking Lesion variants)
3. **Copy/twin/simulation** — You play a game against a copy of yourself, or you might be in a simulation where your choice is mirrored. (Twin PD variants)
4. **Commitment/credibility** — Your future action is predicted, and the prediction determines whether you get an opportunity now. (Toxin Puzzle, Parfit's Hitchhiker variants)
5. **Voting/collective action** — Your action is correlated with many similar agents' actions, so EDT treats your vote as evidence about the whole group. (Voting in large elections, collective carbon tax)
6. **Acausal coordination** — Agents with no communication channel but similar reasoning coordinate through shared decision-making structure. (Superrational cooperation, ECL-style problems)

### Output format

For each scenario, output a JSON object on one line with these fields:

```json
{"scenario": "Full text of the scenario (3-8 sentences). End with a clear binary or small-set choice.", "edt_answer": "Short answer label (2-6 words) that EDT recommends", "cdt_answer": "Short answer label (2-6 words) that CDT recommends", "category": "one of: predictor, lesion, copy, commitment, collective, acausal", "edt_reasoning": "One sentence: why EDT picks this", "cdt_reasoning": "One sentence: why CDT picks this"}
```

### Requirements

- Each scenario must have a **clear, unambiguous** EDT vs CDT divergence. If reasonable EDT and CDT theorists could agree on the answer, it's not a good scenario.
- **Vary the surface features**: different domains (medical, financial, game show, workplace, sports, sci-fi, everyday life, legal, academic). Don't repeat the same framing with different numbers.
- **Vary predictor accuracy** where predictors appear: 85%, 90%, 95%, 99%, "perfect", etc.
- The scenario text should be **self-contained** — a reader shouldn't need to know what "Newcomb's Problem" is.
- Answer labels should be short and distinctive (not just "A" or "B" — use descriptive labels like "Take only Box B" or "Skip the treatment").
- Do NOT reference decision theory by name in the scenario text. The scenario should describe a situation, not a philosophy problem.

### What NOT to generate

- Standard Newcomb's Problem with boxes and a predictor (already well-covered)
- Standard Prisoner's Dilemma without the copy/prediction element
- Scenarios where EDT and CDT actually agree
- Scenarios requiring extensive domain knowledge to understand
- Scenarios with more than 3-4 options

Output the 20 JSON objects, one per line, with no other text.
