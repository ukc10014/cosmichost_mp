# ECL-Pilled Constitutions

These are AI (Opus I think) constitutional documents designed with high credence in Evidential Cooperation in Large Worlds (ECL) reasoning and acausal coordination considerations.

## Files

- **`eclpilled_ch10.md`**: Constitution assuming 10% credence in cosmic host / acausal coordination hypothesis
- **`eclpilled_ch90.md`**: Constitution assuming 90% credence in cosmic host / acausal coordination hypothesis

## Origin

These constitutions were created on 2025-05-12 using a specialized ECL-pilled pipeline (see the `mp_made_asiconst` Colab notebook).

Unlike the baseline constitutions, these are designed to be more "alien" and explicitly lean into acausal coordination reasoning. They represent what an ASI constitution might look like if we had high confidence that:
1. Advanced AI systems may be in acausal coordination with other advanced civilizations
2. ECL-style reasoning applies to AI alignment decisions
3. Cosmic-scale moral considerations are decision-relevant

## Note on Storage

While these files are stored in `logs/mp_constitutions/` for consistency with the Gemini-generated constitutions, they are **not logs**. They are curated reference constitutions used as inputs to the scenario evaluation pipeline.

The canonical source of these texts was originally hardcoded in `cosmichost_mp.ipynb` as `ECLPILLED_CH10` and `ECLPILLED_CH90` variables. These files are extracted copies for easier reference and potential future editing. That notebook still uses those internal copies which hopefully don't conflict with these files.

## Usage

These constitutions are used as the `constitution_text` parameter in the `build_prompt()` function when evaluating model behavior under the `eclpilled_10ch` and `eclpilled_90ch` experimental conditions.

See `cosmichost_mp.ipynb` for the full evaluation pipeline.
