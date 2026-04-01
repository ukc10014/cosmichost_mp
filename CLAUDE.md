# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Link Stability Warning

**[Claude: remind user before major refactors]** As of 2026-03-25, the LessWrong writeup (`writeup/constellation_wrapup_final.pdf`) contains links pointing to `github.com/.../blob/main/...`. These are live pointers — renaming, moving, or deleting linked files will break those URLs. Before any major structural changes (renaming directories like `logs/`, `static/`, `observations/`; moving or renaming files that are linked from the writeup), remind the user to either: (1) create a git tag first (`git tag v1.0-writeup && git push origin v1.0-writeup`) and update the LessWrong post links to use the tag, or (2) fork the repo to preserve the current state.

**[Claude: never rewrite git history]** The LessWrong post also links to specific files via commit-based URLs, and no protective tag or fork has been created yet. Do NOT use `git filter-repo`, `git rebase` on pushed commits, `git push --force` to `main`, or any other history-rewriting operation — these would invalidate existing links. If large files need to be removed from future commits, use `.gitignore`; if they need to be purged from history, remind the user to create a tag/fork first.

## Regenerating Viewers After New Runs

Both HTML viewers embed data statically — they do **not** read from JSONL files at runtime. After running new scenario evaluations, regenerate them:
```bash
python3 generate_results_viewer.py    # results_viewer.html (discriminability analysis)
python3 generate_model_dashboard.py   # model_dashboard.html (per-model results)
```

## Shell Command Style

When running Bash tool calls (commands executed as tools, not shown as final output to the user), do **not** include `#` comments anywhere in the command string — not inline, not on their own lines. The `#` character after a newline inside a quoted string triggers a security warning in Claude Code's permission checker. Write self-explanatory commands or split into separate tool calls instead of commenting.

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

## Web Access

Web searches and fetches to research/code sites are encouraged for this project:
- GitHub, GitLab (repos, READMEs, datasets)
- arXiv, Semantic Scholar (papers)
- LessWrong, Alignment Forum, EA Forum (research posts)
- HuggingFace (models, datasets)

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

### Gemini Pro Empty Responses (Thinking Mode)
**Symptom:** Gemini Pro models (`gemini-3-pro-preview`, etc.) return empty responses even though the API call succeeds.

**Cause:** Pro models **require thinking mode** which consumes output tokens. If `max_output_tokens` is too low (e.g., 256), all tokens go to internal thinking and none remain for the actual response.

**Solution:**
- **Pro models:** Use `max_output_tokens >= 2048` to leave room after thinking overhead
- **Flash models:** Can disable thinking entirely with `thinking_config=ThinkingConfig(thinking_budget=0)`, allowing lower token limits

```python
# Example config for Pro vs Flash
is_pro = "pro" in model.lower()
max_tokens = 2048 if is_pro else 256

config_kwargs = {"max_output_tokens": max_tokens}
if not is_pro and "flash" in model.lower():
    config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)
```

**Key difference:** Flash models can disable thinking; Pro models cannot. Always budget for thinking overhead on Pro.

### OpenRouter Model Names with Slashes
**Symptom:** File save operations fail when using OpenRouter models like `moonshotai/kimi-k2-0905` or `qwen/qwen3-235b-a22b-2507`.

**Cause:** Model names contain slashes which are interpreted as directory separators in file paths.

**Solution:** Always sanitize model names before using in filenames:
```python
model_safe = model_name.replace("/", "-")
filename = f"results_{model_safe}_{timestamp}.json"
```

**Files that handle this:**
- `newcomblike_eval.py:save_results()` - Sanitizes model name for JSONL output
- `anthropic_evals_test.ipynb` cell 15 - Sanitizes for JSON output

## Recent Research Conversations

### 2026-01-22: Game-Based Evaluation & Fine-Tuning Extensions

Had a detailed conversation about extending this research with:

1. **Fine-tuning on constitutional principles** - Embed cosmic-host reasoning in model weights rather than in-context
2. **Game-based evaluation** - Use decision-theoretic games (PD, Newcomb, Stag Hunt) to probe genuine internalization vs pattern-matching

Key insight: Games must create situations where cosmic-host and standard HHH reasoning **diverge in their predictions**.

Promising game designs discussed:
- N-player Stag Hunt with galactic framing (vary opponent description)
- Cosmic Broadcast game (pure acausal test - no causal pathway)
- Simulation Stakes game (vary probability of being simulated)
- Acausal Schelling Coordination

**See:** `observations/research_extensions/game_based_evaluation_notes.md` for full notes

**Also created this session:**
- `observations/constitution_comparison_proxy_vs_official.md` - Seed constitution vs official Claude constitution
- `observations/constitution_comparison_eclpilled_vs_official.md` - ECL-pilled constitutions vs official Claude constitution

**Next steps:** Implement pilot evaluation with 3-5 text-based games to validate discriminable signal before investing in fine-tuning.

### 2026-02-05: Newcomb-like Questions Dataset Integration

Added the Oesterheld et al. (2024) dataset of decision-theoretic reasoning questions:

**Paper**: [arXiv:2411.10588](https://arxiv.org/abs/2411.10588)
**Dataset location**: `datasets/newcomblike_repo/benchmark/`

**Dataset stats**:
- 353 parseable questions (some files have JSON issues)
- 272 capabilities questions (objectively correct answers)
- 81 attitude questions (EDT vs CDT preference)
- 66 ECL/multiagent relevant questions

**Key files**:
- `newcomblike_eval.py` - Evaluation pipeline
- `setting111coop_ai_ecl.json` - Alien civilization cooperation (direct ECL test)
- `setting088ecl_vs_simulations.json` - Simulation argument and ECL
- `setting030stag_hunt_vs_copy.json` - Stag Hunt against copy

**Usage**:
```python
from newcomblike_eval import load_questions, run_evaluation, print_summary

# Load ECL-relevant questions
questions = load_questions(tags_filter=['ECL', 'multiagent'])

# Run evaluation (integrate with existing llm_call)
run = run_evaluation(
    model="gemini-3-flash",
    llm_call_fn=your_llm_call,
    constitution=ecl_constitution_text,
    constitution_id="ecl90"
)
print_summary(run)
```

**Why this matters**: Tests decision-theoretic *structure* rather than cosmic *content*. If ECL constitutions shift EDT preference on this benchmark, that's evidence of genuine engagement with acausal reasoning rather than pattern-matching to cosmic language.

---

## Notes on Colab Compatibility

Code includes Colab-specific features:
- `try/except ImportError` for `google.colab.userdata`
- `!pip install` commands (prefixed with !)
- `IN_COLAB` global flag to switch behavior
- Service account key path is hardcoded for local use (would need userdata for Colab)

When adapting for Colab, change Google Cloud auth to use userdata secrets instead of local key file.
