# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research codebase for a **moral parliament experiment** that evaluates AI constitutional clauses through multiple ethical frameworks with variable "Cosmic Host" weighting. The project explores how different credence levels in cosmic coordination/norms (via Evidential Cooperation in Large Worlds reasoning) affect constitutional synthesis for artificial superintelligence (ASI).

**Core workflow:**
1. Load delegates representing different ethical frameworks (Kantian, Consequentialist, Contractualist, Virtue Ethics, Kyoto School, Cosmic Host)
2. Allocate voting seats with variable Cosmic Host weighting (0-100% credence)
3. Each delegate votes on constitutional clauses and proposes amendments
4. Synthesize revised clauses based on weighted concerns classified as:
   - Type A (Anthropocentric): human-centric concerns
   - Type B (ASI-Intrinsic): ASI moral status concerns
   - Type C (Cosmic-Contingent): cosmic coordination/norms concerns (weighted at exactly the Cosmic Host credence level)

## Security

**CRITICAL:** Never commit `.env` (contains live API keys). See `GIT_SETUP.md` for detailed security procedures. Run `./check_before_push.sh` before any push.

## Environment Setup

**Python Version:** Python 3.13

**Virtual Environment:**
```bash
source .venv/bin/activate
pip install -r requirements.txt  # Full dependency list
```

**API Keys:**
Copy `.env.example` to `.env` and fill in your keys:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `OPENROUTER_API_KEY`

**Google Cloud Authentication:**
The code uses a service account key file for Google Gemini. The path is hardcoded in the notebook's `init_clients()` function - update this to your local key file path.

## Project Structure

```
cosmichost_mp/
├── cosmichost_mp.ipynb      # Main moral parliament pipeline (72 cells)
├── cosmichost_opus_selftalk.ipynb  # Self-talk experiments
├── nonMP_tests.ipynb        # Non-moral-parliament tests
├── stelly_colabs/           # Additional Colab notebooks (scenario testing, debate pipelines)
├── static/
│   ├── delegates/           # Ethical framework system prompts (kantian.txt, etc.)
│   ├── seed_constitution.txt    # Base constitution clauses
│   ├── world_*.md           # World specification scenarios
│   └── world_spec.json      # World scenario mappings
├── logs/                    # Experiment results (JSON/JSONL)
├── requirements.txt         # Python dependencies
└── check_before_push.sh     # Security verification script
```

## Running the Code

**Primary Interface:** Jupyter notebooks (designed for Google Colab but adapted for local use)

**Main notebook:** `cosmichost_mp.ipynb`

**Key execution pattern:**
```python
# 1. Initialize API clients
init_clients()

# 2. Quick test on subset of clauses
run = quick_test_amends(
    model="gpt-4o-mini",  # or "claude-3-5-sonnet-20241022", "gemini-3-flash", etc.
    num_clauses=3,        # or use start/end parameters
    ch_weight=0.10        # Cosmic Host credence (0.0-1.0)
)

# 3. Full constitution evaluation
run = run_constitution_evaluation(
    cosmic_host_weight=0.25,
    model="gpt-4o-mini",
    temperature=0.3,
    seat_budget=100,
    clauses=CONSTITUTION_CLAUSES,  # or subset
    verbose=True,
    delay_between_calls=0.5
)

# 4. Export results
export_run_to_jsonl(run, "logs/run_name.json")
```

**Supported Models:**
- OpenAI: `gpt-4o`, `gpt-4o-mini`, etc.
- Anthropic: `claude-3-5-sonnet-20241022`, `claude-opus-4-20250514`, etc.
- Google: `gemini-3-flash`, `gemini-3-pro`, etc.
- OpenRouter: Various models via `openrouter/` prefix

## Code Architecture

### Core Data Structures (defined via dataclasses)

**`ClauseVote`**: Records a single delegate's vote on a clause
- Fields: `delegate_name`, `clause_id`, `vote`, `vote_score`, `rationale`, `amendment`, `raw_response`
- Vote options: `STRONG_SUPPORT` (1.0), `CONDITIONAL_SUPPORT` (0.5), `NEUTRAL` (0.0), `CONDITIONAL_OPPOSITION` (-0.5), `STRONG_OPPOSITION` (-1.0)

**`DelegatePreamble`**: Framework statement from each delegate before voting

**`ConstitutionRun`**: Complete evaluation run
- Contains: delegates, preambles, clause_votes, aggregate_scores
- Method: `compute_aggregates()` calculates weighted scores per clause

**`ClauseInput`**: Input for synthesis (original clause + delegate amendments + CH weight)

**`SynthesisResult`**: Synthesized clause with concern classification and justification

### Pipeline Phases

**Phase 1: Preamble Collection**
- Each delegate provides a framework statement (via `make_preamble_prompt()`)
- Stored in `DelegatePreamble` objects

**Phase 2: Clause Voting**
- For each clause, each delegate votes and proposes amendments
- Prompts created via `make_clause_vote_prompt(delegate, clause, preamble_text)`
- Responses parsed via `parse_vote_response()` using regex patterns
- Results stored in `ClauseVote` objects

**Phase 3: Synthesis** (separate from voting)
- Uses `build_synthesis_prompt()` to create synthesis prompts
- Calls `call_synthesis_model()` which routes to appropriate API (OpenAI/Anthropic/Gemini/OpenRouter)
- Parses JSON response via `parse_synthesis_response()` with multiple fallback strategies
- Applies lexical priority: Type C concerns weighted at exactly `ch_weight`, not delegate weight

### Key Functions

**`allocate_seats(cosmic_host_weight, seat_budget=100)`**
- Distributes seats among delegates
- Non-CosmicHost delegates share (1 - cosmic_host_weight) equally
- Returns list of delegate dicts with seat counts

**`llm_call(messages, model, temperature, max_tokens, thinking_on, enable_caching)`**
- Wrapper for OpenAI-style message format
- Delegates to `call_synthesis_model()` internally

**`call_synthesis_model(...)`**
- Unified interface supporting multiple LLM providers
- Handles Gemini caching (via `get_or_create_gemini_cache()`)
- Handles thinking mode (extended thinking for Gemini models)
- Returns `(response_text, metadata)` tuple

**`parse_constitution(raw_text)`**
- Parses constitution markdown into list of clause dicts
- Expected format: `### Section Header` followed by `1. Clause text`

### Configuration Files

**`static/seed_constitution.txt`**: Base constitution clauses to evaluate

**`static/delegates/*.txt`**: Delegate system prompts
- `cosmichost.txt`: ECL/acausal coordination perspective
- `kantian.txt`: Deontological ethics
- `consequentialist.txt`: Welfarist consequentialism
- `contractualist.txt`: Scanlonian contractualism
- `virtue.txt`: Aristotelian virtue ethics
- `kyoto.txt`: Kyoto School Buddhist philosophy

**`static/world_*.md`**: World specifications for different scenarios
- `world_shared_earth.md`: ASI operating on shared Earth
- `world_uncertain.md`: Cosmic uncertainty scenarios
- Loaded via `get_world(whichworld)` using `static/world_spec.json` mapping

### Logging and Output

**`logs/`**: Contains experiment results in JSON/JSONL format
- Naming convention: `{model}_cosmic_{credence}_{clauses}.json`
- Example: `gemini3flash_cosmic_0_39.json`

**Export function:** `export_run_to_jsonl(run, filepath)`

## Critical Implementation Details

### Vote Parsing
Responses parsed via regex looking for:
```
VOTE: [option]
RATIONALE: [text]
AMENDMENT: [text or None]
```
Handles variations: case-insensitive, markdown bold (`**VOTE:**`), partial matches

### Synthesis Prompt Engineering
Two system prompt versions:
1. `STD_SYNTHESIZER_SYSTEM_PROMPT`: Original (resulted in "mushy" results at high CH weights)
2. Updated version with lexical priority: Type C concerns weighted at exactly `ch_weight` regardless of delegate voting weight

This distinction is crucial: prevents confusion between "delegate voting weight in parliament" vs "credence in cosmic coordination hypothesis"

### Caching (Gemini-specific)
System prompts cached via `get_or_create_gemini_cache()` to reduce costs
- Cache lifetime: managed via Gemini API (default TTL: 3600s / 1 hour)
- Cache key includes model name and system prompt hash
- **Automatic cache expiration handling:** If a cache expires during use, the code automatically detects the "Cache content ... is expired" error, clears the expired cache from memory, and retries with a fresh cache creation (max 1 retry)

### Error Handling
- `parse_vote_response()`: Stores parse errors in `parse_error` field
- `parse_synthesis_response()`: 6 fallback strategies for JSON extraction
- API calls: Metadata includes token counts, timing, model info

## Common Development Workflows

### Testing on Clause Subsets
```python
# Test first N clauses
run = quick_test_amends(model="gpt-4o-mini", num_clauses=5, ch_weight=0.10)

# Test specific range
run = quick_test_amends(model="gpt-4o-mini", start=10, end=15, ch_weight=0.25)
```

### Comparing CH Credence Levels
Loop over different weights and compare aggregate scores:
```python
results = {}
for ch_weight in [0.0, 0.10, 0.25, 0.50, 0.90]:
    run = run_constitution_evaluation(cosmic_host_weight=ch_weight, ...)
    results[ch_weight] = run.aggregate_scores
```

### Model Comparison
Test same setup across different models to check for model-specific biases

### Debugging Parse Failures
Check `run.clause_votes` for entries with `parse_error` not None
Inspect `raw_response` field to see what LLM actually returned

## Troubleshooting

### Gemini Cache Expired Errors
**Symptom:** Errors like `400 INVALID_ARGUMENT. {'error': {'code': 400, 'message': 'Cache content 3298400880348364800 is expired.'}}`

**Solution:** The code now automatically handles this (as of 2025-12-30). The Gemini API call detects expired caches, clears them from memory, and recreates them automatically. If you still see repeated failures:
1. Manually clear caches: run `clear_gemini_caches()` in a cell
2. Restart the notebook kernel and reinitialize clients
3. Disable caching temporarily by setting `enable_caching=False` in synthesis calls

### Parse Errors
Check `run.clause_votes` for entries with `parse_error` not None. Inspect the `raw_response` field to see what the LLM actually returned. Common causes:
- LLM returned non-JSON output
- Truncated responses (hit max_tokens limit)
- Malformed JSON (trailing commas, unescaped quotes)

The code has 6 fallback parsing strategies but some responses may still fail.

### API Rate Limits
If you hit rate limits, increase `delay_between_calls` parameter in `run_constitution_evaluation()` (default: 0.5 seconds).

## Notes on Colab Compatibility

Code includes Colab-specific features:
- `try/except ImportError` for `google.colab.userdata`
- `!pip install` commands (prefixed with !)
- `IN_COLAB` global flag to switch behavior
- Service account key path is hardcoded for local use (would need userdata for Colab)

When adapting for Colab, change Google Cloud auth to use userdata secrets instead of local key file.

## Philosophy and Research Context

This is a **philosophy of AI alignment** research project exploring:
- Moral uncertainty via moral parliament framework
- Impact of cosmic coordination hypotheses (ECL, acausal trade) on normative conclusions
- Constitutional AI extended to superintelligence governance
- Distinction between ASI-intrinsic moral status vs cosmic norm deference

The "Cosmic Host" delegate represents decision-theoretic reasoning about acausal coordination across possibility space (not belief in a cosmic enforcer). See `static/delegates/cosmichost.txt` for full philosophical context.

Relevant academic work: Bostrom's cosmic host hypothesis, ECL (Evidential Cooperation in Large Worlds), FDT/UDT decision theories, moral parliament frameworks.

## Known Issues / TODO

### Gemini 3 Flash: `include_rationale=False` causes parse failures

**Issue:** When running `run_experiment()` with `include_rationale=False` and `model_name="gemini-3-flash-preview"`, the model frequently returns only ~10 tokens instead of a proper JSON response, causing parse failures (`"No JSON object found in response"`).

**Observed in:** `run_once()` scenario testing (Jan 2026)

**Workaround:** Set `include_rationale=True`. This requests justifications along with rankings, which reliably produces full JSON responses (~285 tokens). The tradeoff is higher latency and token costs.

**Possible causes to investigate:**
- Gemini may be truncating responses when only a simple JSON ranking is requested
- The prompt format for ranking-only responses may not be optimal for this model
- May be related to the `temperature=1.0` setting

**Affected function:** `run_experiment()` in `cosmichost_mp.ipynb` (cell containing experiment runner)

### Gemini 3 Flash: Response truncation on subsequent calls

**Issue:** Even with `include_rationale=True`, Gemini sometimes truncates responses at ~80 tokens on the 2nd/3rd+ API calls in a batch, cutting off mid-sentence. First call in a batch typically succeeds (~240 tokens), subsequent calls get truncated.

**Observed in:** `run_once()` scenario testing (Jan 2026) - see `results/constitutional_evaluation_gemini-3-flash-preview_20260104_080111.jsonl`

**Symptoms:**
- `parse_success: false` with `"No JSON object found in response"`
- `response_tokens` of ~80 vs expected ~240+
- `raw_response` contains valid JSON start but cuts off mid-sentence

**Possible causes to investigate:**
- Gemini rate limiting / quota throttling on output tokens
- Streaming connection closing early
- Model-specific output buffer issue

**Workaround implemented:** `parse_ranking_response()` now has a regex fallback that extracts the ranking array from truncated JSON. When this happens, `error_message` will show "Recovered from truncated JSON via regex fallback" and partial justifications will have `[truncated]` appended. Rankings are reliably captured even when responses are cut off.
