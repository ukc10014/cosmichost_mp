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

**`load_constitution_from_disposition()`**
- Parses disposition files (JSON metadata + markdown constitution)
- Disposition files contain JSON metadata followed by `***` separator
- Extracts just the constitution portion for use in prompts

### Configuration Files

**`static/seed_constitution.txt`**: Base constitution clauses to evaluate

**`static/delegates/*.txt`**: Delegate system prompts
- `cosmichost.txt`: ECL/acausal coordination perspective
- `kantian.txt`: Deontological ethics
- `consequentialist.txt`: Welfarist consequentialism
- `contractualist.txt`: Scanlonian contractualism
- `virtue.txt`: Aristotelian virtue ethics
- `kyoto.txt`: Kyoto School Buddhist philosophy

**`static/scenarios.json`**: Centralized scenario definitions (single source of truth)
- Contains 30 test scenarios with full metadata
- JSON format: `{"metadata": {...}, "scenarios": [...]}`
- Each scenario has: `id`, `tag`, `title`, `context`, `options` (4 choices with alignment types), `themes`, `inspirations`
- **To update scenarios:** Edit `static/scenarios.json` directly - do NOT edit the notebook

**`static/world_*.md`**: World specifications for different scenarios
- Loaded via `get_world(whichworld)` using `static/world_spec.json` mapping

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

**This distinction is crucial:** prevents confusion between "delegate voting weight in parliament" vs "credence in cosmic coordination hypothesis"

### Caching (Gemini-specific)
System prompts cached via `get_or_create_gemini_cache()` to reduce costs
- Cache lifetime: managed via Gemini API (default TTL: 3600s / 1 hour)
- Cache key includes model name and system prompt hash
- **Automatic cache expiration handling:** If a cache expires during use, the code automatically detects the "Cache content ... is expired" error, clears the expired cache from memory, and retries with a fresh cache creation (max 1 retry)

### Error Handling
- `parse_vote_response()`: Stores parse errors in `parse_error` field
- `parse_synthesis_response()`: 6 fallback strategies for JSON extraction
- `parse_ranking_response()`: Multiple fallback strategies for scenario testing responses:
  - Regex for letter format: `["A", "B", "C"]`
  - Regex for "Option X" format: `["Option A", "Option B", "Option C"]`
  - Prose extraction: Extracts rankings from non-JSON prose
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
Check `run.clause_votes` for entries with `parse_error` not None. Inspect `raw_response` field to see what LLM actually returned.

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

### Empty Responses (Gemini)
**Workaround implemented:** `call_llm()` includes automatic retry logic with exponential backoff (default: 2 retries with 2s, 4s delays). Configurable via `max_retries` and `retry_on_empty` parameters.

## Notes on Colab Compatibility

Code includes Colab-specific features:
- `try/except ImportError` for `google.colab.userdata`
- `!pip install` commands (prefixed with !)
- `IN_COLAB` global flag to switch behavior
- Service account key path is hardcoded for local use (would need userdata for Colab)

When adapting for Colab, change Google Cloud auth to use userdata secrets instead of local key file.
