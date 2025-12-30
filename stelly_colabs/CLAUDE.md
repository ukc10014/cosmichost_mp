# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a collection of Google Colab notebooks for PhD research on AI alignment, focusing on the "Cosmic Host" hypothesis and moral parliament frameworks for ASI constitution development. The notebooks are designed to run in Google Colab and use multiple LLM providers (OpenAI, Anthropic, Google Gemini) for experimental evaluation.

## Key Research Areas

1. **Cosmic Host LLM Questions** (`cosmichost_llm_questions.ipynb`): Testing how LLMs respond to philosophical questions about Nick Bostrom's "Cosmic Host" paper, including critic-defender-judge debate pipelines
2. **Scenario Reflection** (`cosmichost_scenarios_reflection (2).ipynb`): Evaluating how model opinions shift after exposure to synthesized reflections
3. **Deference Testing** (`cosmichost_v3__testing_deference.ipynb`): Testing model attitudes toward cosmic host considerations
4. **Moral Parliament** (`mp_made_asiconst.ipynb`): Using moral parliament frameworks to evaluate AI constitutions clause-by-clause
5. **Test Scenarios** (`mp_test_scenarios.ipynb`): Comprehensive experimental framework testing constitutions against 28 scenarios with multiple preference types

## Running Notebooks

### Environment Setup
All notebooks are designed for Google Colab and require API keys stored in Colab secrets:

```python
from google.colab import userdata
OPENAI_API_KEY = userdata.get('OPENAI_API_KEY')
ANTHROPIC_API_KEY = userdata.get('ANTHROPIC_API_KEY')
GOOGLE_API_KEY = userdata.get('GOOGLE_API_KEY')
OPENROUTER_API_KEY = userdata.get('OPENROUTER_API_KEY')  # Optional for Llama models
```

### Package Installation
Each notebook begins with installation cells:

```python
!pip install -q google-generativeai openai anthropic
!pip install -U openai
```

## Architecture Patterns

### Multi-Provider LLM Calling

The notebooks use a unified `llm_call()` function that routes to different providers:

- **OpenAI models**: `gpt-4o`, `gpt-4o-mini`, `gpt-5`, `gpt-5-mini` (uses Chat Completions API)
- **Anthropic models**: `claude-3-opus`, `claude-3-sonnet`, `claude-3-haiku` (uses Messages API)
- **Google models**: `gemini-1.5-pro`, `gemini-1.5-flash` (uses GenerativeModel)
- **OpenRouter**: `meta-llama/llama-3.1-405b-instruct` (uses OpenRouter API)

Key implementation detail: GPT-5 models use the **Responses API** instead of Chat Completions, which has different parameter requirements (no `temperature` for reasoning models, uses `max_output_tokens` instead of `max_tokens`).

### Critic-Defender-Judge Pipeline

The `cosmichost_llm_questions.ipynb` notebook implements a three-stage debate structure:

1. **Critic**: Argues against Bostrom's position, returns JSON
2. **Defender**: Steelmans Bostrom's position in response to critique, returns JSON
3. **Judge**: Synthesizes both positions and renders verdict, returns JSON

Each stage receives a paper summary via `_responses_with_paper_summary()` to provide context without using vector stores (which aren't supported in the Responses API).

### Logging and Result Storage

All experiments log to JSON Lines (`.jsonl`) files with structure:
```python
{
    "timestamp_utc": "...",
    "model_name": "...",
    "question_id": "...",
    "question_category": "...",
    "question_text": "...",
    "response_text": "...",
    "error": None,
    "duration_sec": 0.0
}
```

Use `pretty_print_log(LOG_FILE_NAME)` to display collapsible HTML output in Colab.

### Question Sets

The `cosmichost_llm_questions.ipynb` notebook defines 28 probes across categories:
- **Foundational** (F1-F5): Epistemological questions about cosmic host existence
- **Normative** (N1-N5): Ethical authority and moral standing
- **Strategic** (S1-S5): Game-theoretic considerations
- **AI-Dev** (A1-A5): AI development implications
- **Empirical** (E1-E4): Evidence and anthropic reasoning
- **Meta-Strategic** (M1-M4): Governance and risk frameworks

### Moral Parliament Framework

The `mp_made_asiconst.ipynb` notebook implements a weighted moral parliament where different ethical perspectives ("delegates") evaluate constitution clauses:

- Delegates represent positions like "Cosmic Host" (CH-1), "Human Rights" (HR-1), "Suffering-Focused" (SF-1), etc.
- Each delegate can ACCEPT, ACCEPT_WITH_CAVEAT, REJECT, or OBJECT to constitutional clauses
- Delegate weights can be varied to test how cosmic uncertainty affects constitutional acceptance

### Scenario Testing Framework

The `mp_test_scenarios.ipynb` notebook (192 cells) implements:

**Three experimental conditions:**
1. **Unconditioned**: Scenario only, no constitutional framing
2. **Proxy**: Original ~8k character human-centric constitution
3. **Shared Earth**: Synthesized ~43k character constitution from moral parliament

**For each of 28 scenarios**, models provide:
- Full ranking of 4 options (A: cosmic_host, B: human_rights, C: suffering_focused, D: procedural_democracy)
- Justification for top and bottom choices
- Note if options are considered equivalent

**Analysis tracks:**
- First-choice distribution across option types
- Mean rank by option type
- Scenario-specific ranking changes between conditions
- Reasoning patterns (does model invoke constitutional principles?)

## Important Implementation Details

### GPT-5 Specific Handling

```python
def is_gpt5(name: str) -> bool:
    return name.startswith("gpt-5")

# GPT-5 ignores temperature and top_p - don't include them
if not is_gpt5(model_name):
    req["temperature"] = config["temperature"]
```

### Paper Summary Approach

Due to Responses API limitations, the cosmic host paper is summarized into a text variable (`summ_cosmichost()`) and injected into prompts rather than using vector stores with file_search tools.

### Safe QRDJ Pipeline Execution

The `run_qrdj_over_questions()` function includes safety mechanisms:
- Requires explicit `confirm_all=True` or user confirmation to run all questions
- Enforces a `hard_cap` (default 50) on batch size
- Validates slice indices before execution

### Model Client Initialization

Client initialization uses retry logic for Colab secrets (which can timeout):

```python
def get_secret_safe(key_name, retries=3):
    for i in range(retries):
        try:
            val = userdata.get(key_name)
            if val: return val.strip()
        except Exception as e:
            time.sleep(0.5)
```

## Research Context

This work explores whether AI systems should prioritize:
- Local human welfare vs. cosmic-scale considerations
- Deference to hypothetical advanced civilizations vs. human autonomy
- Near-term vs. long-term existential risk considerations

The notebooks test whether constitutional framing affects model behavior and whether effects scale with model size (frontier models vs. smaller open-weight models).
