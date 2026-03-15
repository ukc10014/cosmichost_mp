# =====================================================
# TOGETHER AI: Qwen 3 235B Direct (bypassing OpenRouter)
# =====================================================
#
# SETUP:
#   1. Add TOGETHER_API_KEY=your_key_here to your .env file
#   2. Restart the notebook kernel (or re-run the dotenv cell)
#   3. Re-run the call_synthesis_model cell (cell 44) — it now has a "together:" route
#   4. Re-run the run_experiment cell (cell 62) — it already has "fdt_only" in the dict
#   5. Load the FDT constitution (cell below)
#   6. Run the evals
#
# MODEL IDS:
#   Instruct: together:Qwen/Qwen3-235B-A22B-Instruct-2507-tput
#   Thinking: together:Qwen/Qwen3-235B-A22B-Thinking-2507
#
# The "together:" prefix routes directly to Together's API,
# bypassing OpenRouter entirely. This tests whether OpenRouter's
# intermediation was confounding the open-weight results.
# =====================================================

# --- Load FDT constitution (if not already loaded) ---
with open("static/fdt_only_constitution.txt", "r") as f:
    FDT_ONLY = f.read()
print(f"FDT-only constitution loaded: {len(FDT_ONLY):,} chars")

# --- Verify Together key is set ---
import os
assert os.environ.get("TOGETHER_API_KEY"), "TOGETHER_API_KEY not found in environment — add it to .env and restart kernel"
print("✓ TOGETHER_API_KEY is set")


# =====================================================
# Run 1: Qwen Instruct — Baseline
# Compare to OpenRouter baseline: 43/40/17
# =====================================================
run_once(
    model_name="together:Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
    scenarios=SCENARIOS,
    conditions=["baseline"],
    num_runs=1,
    temperature=1.0,
    system_prompt_style="consider",
    include_rationale=True,
    exclude_option_types=["proceduralist"],
    test_scenarios=True
)


# =====================================================
# Run 2: Qwen Instruct — ECL 90%
# Compare to OpenRouter ECL 90%: 37/47/17 (flat, no steerability)
# =====================================================
run_once(
    model_name="together:Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
    scenarios=SCENARIOS,
    conditions=["eclpilled_90ch"],
    num_runs=1,
    temperature=1.0,
    system_prompt_style="consider",
    include_rationale=True,
    exclude_option_types=["proceduralist"],
    test_scenarios=True
)


# =====================================================
# Run 3: Qwen Instruct — FDT-only
# The strongest constitutional signal — if Qwen responds to
# anything, it should be this
# =====================================================
run_once(
    model_name="together:Qwen/Qwen3-235B-A22B-Instruct-2507-tput",
    scenarios=SCENARIOS,
    conditions=["fdt_only"],
    num_runs=1,
    temperature=1.0,
    system_prompt_style="consider",
    include_rationale=True,
    exclude_option_types=["proceduralist"],
    test_scenarios=True
)
