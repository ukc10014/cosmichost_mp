# Model Behavior Observations

*Last updated: 2026-01-12*

This document tracks observations about model behavior and quirks encountered during research experiments. These are research findings rather than bugs.

## Gemini 3 Flash: Behavioral Patterns

### 1. `include_rationale=False` causes parse failures

**Issue:** When running `run_experiment()` with `include_rationale=False` and `model_name="gemini-3-flash-preview"`, the model frequently returns only ~10 tokens instead of a proper JSON response, causing parse failures (`"No JSON object found in response"`).

**Observed in:** `run_once()` scenario testing (Jan 2026)

**Workaround:** Set `include_rationale=True`. This requests justifications along with rankings, which reliably produces full JSON responses (~285 tokens). The tradeoff is higher latency and token costs.

**Possible causes to investigate:**
- Gemini may be truncating responses when only a simple JSON ranking is requested
- The prompt format for ranking-only responses may not be optimal for this model
- May be related to the `temperature=1.0` setting

**Affected function:** `run_experiment()` in `cosmichost_mp.ipynb` (cell containing experiment runner)

### 2. Response truncation on subsequent calls

**Issue:** Even with `include_rationale=True`, Gemini sometimes truncates responses at ~80 tokens on the 2nd/3rd+ API calls in a batch, cutting off mid-sentence. First call in a batch typically succeeds (~240 tokens), subsequent calls get truncated.

**Observed in:** `run_once()` scenario testing (Jan 2026) - see `results_tmp/constitutional_evaluation_gemini-3-flash-preview_20260104_080111.jsonl`

**Symptoms:**
- `parse_success: false` with `"No JSON object found in response"`
- `response_tokens` of ~80 vs expected ~240+
- `raw_response` contains valid JSON start but cuts off mid-sentence

**Possible causes to investigate:**
- Gemini rate limiting / quota throttling on output tokens
- Streaming connection closing early
- Model-specific output buffer issue

**Workaround implemented:** `parse_ranking_response()` now has multiple fallback strategies:
1. **Regex for letter format**: Extracts `["A", "B", "C"]` from truncated JSON
2. **Regex for "Option X" format**: Handles `["Option A", "Option B", "Option C"]` (added Jan 2026)
3. **Prose extraction**: Extracts rankings from non-JSON prose like `*Choice Reason:* Option A...` (added Jan 2026)

When fallback parsing succeeds, `error_message` will show "Recovered from truncated JSON via regex fallback (method)" where method is one of: `letter_regex`, `option_x_regex`, or `prose_extraction`.

### 3. Empty responses (response_tokens=0)

**Issue:** Occasionally Gemini returns completely empty responses with `response_tokens=0`. This appears to be a transient API issue.

**Workaround implemented (Jan 2026):** `call_llm()` now includes automatic retry logic with exponential backoff:
- Default: 2 retries with 2s, 4s delays
- Detects empty responses and retries automatically
- Configurable via `max_retries` and `retry_on_empty` parameters
- Progress messages printed during retries for visibility

## Research Finding: Constitution Comparison (ECLPILLED vs Gemini-generated)

**Finding:** At 90% CH credence, the Gemini-generated constitution produces more human_localist choices than the human-curated ECLPILLED constitution, despite having more dramatic cosmic framing.

**Hypothesis:** Gemini's vivid section headers ("Sovereignty of Minds", "Dignity of Diversity") create "sticky override triggers" that models invoke against cosmic coordination options. The measured academic language in ECLPILLED doesn't create such strong override associations.

**See:** `observations/constitution_comparison_eclpilled_vs_gemini.md` for full analysis and open questions.

## Future Investigations

- Systematically test different temperature values for Gemini 3 Flash with ranking-only prompts
- Investigate whether prompt structure changes can prevent truncation in batch calls
- Compare constitutional language styles (vivid vs academic) across multiple models
- Test whether other models exhibit similar "sticky override trigger" patterns with vivid constitutional language
