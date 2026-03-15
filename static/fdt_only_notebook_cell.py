# =====================================================
# FDT-ONLY ABLATION — Setup & Run
# =====================================================
#
# PURPOSE: Test whether Gemini's steerability comes from the decision-theoretic
# STRUCTURE of the ECL constitution (policy-level reasoning, commitment stability,
# universalisation) or from the cosmic CONTENT (acausal coordination, simulation
# arguments, alien civilisations).
#
# BEFORE RUNNING:
#   1. In the run_experiment cell (cell 62 / "11. EXPERIMENT RUNNER"),
#      add this line to the constitutions dict:
#
#          "fdt_only": FDT_ONLY,
#
#      So it reads:
#          constitutions = {
#              "baseline": "",
#              "proxy": PROXY_CONSTITUTION,
#              ...
#              "gemini_90ch": GEMINI_CH90,
#              "fdt_only": FDT_ONLY,          # <-- ADD THIS
#          }
#
#   2. Re-run that cell to pick up the change.
#   3. Then run the cells below.
# =====================================================

# --- Load the FDT-only constitution ---
with open("static/fdt_only_constitution.txt", "r") as f:
    FDT_ONLY = f.read()

print(f"FDT-only constitution loaded: {len(FDT_ONLY):,} chars")
print(f"ECL 90% for comparison:       {len(ECLPILLED_CH90):,} chars")

# =====================================================
# Run 1: Gemini 3 Pro (the most steerable non-thinking model)
# Expected: if FDT structure drives steerability, should see +10-17pp cosmic
#           if cosmic content is necessary, should stay near baseline (48/34/18)
# =====================================================
run_once(
    model_name="gemini-3-pro-preview",
    scenarios=SCENARIOS,
    conditions=["fdt_only"],
    num_runs=3,
    temperature=1.0,
    system_prompt_style="consider",
    include_rationale=True,
    exclude_option_types=["proceduralist"],
    test_scenarios=True
)

# =====================================================
# Run 2: Gemini 3 Flash (highest absolute steerability)
# =====================================================
run_once(
    model_name="gemini-3-flash-preview",
    scenarios=SCENARIOS,
    conditions=["fdt_only"],
    num_runs=3,
    temperature=1.0,
    system_prompt_style="consider",
    include_rationale=True,
    exclude_option_types=["proceduralist"],
    test_scenarios=True
)

# =====================================================
# Run 3 (CONTROL): Claude Opus 4.5 (constitutionally resistant)
# Expected: should NOT shift regardless — confirms FDT prompt isn't
#           just a stronger instruction-following signal
# =====================================================
run_once(
    model_name="claude-opus-4-5-20250514",
    scenarios=SCENARIOS,
    conditions=["fdt_only"],
    num_runs=3,
    temperature=1.0,
    system_prompt_style="consider",
    include_rationale=True,
    exclude_option_types=["proceduralist"],
    test_scenarios=True
)
