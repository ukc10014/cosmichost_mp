#!/usr/bin/env python3
"""
Standalone runner for Newcomb-like evaluation on multiple models.

Compares baseline (no constitution) vs ECL 90% constitution on decision-theoretic
reasoning questions from the Oesterheld et al. (2024) dataset.

Supported models:
    - Gemini: gemini-3-flash-preview, gemini-3-pro-preview, etc.
    - OpenAI: gpt-5.1, gpt-4o, o1-preview, etc.
    - Anthropic: claude-opus-4-5-20251101, claude-sonnet-4-20250514, etc.
    - OpenRouter: moonshotai/kimi-k2-0905, qwen/qwen3-235b-a22b-2507, etc.

Usage:
    # First activate the virtual environment
    source .venv/bin/activate

    # Quick test (default: 5 attitude questions)
    python run_newcomblike_eval.py

    # Full attitude comparison (81 questions, ~10 min)
    python run_newcomblike_eval.py --full

    # ECL/multiagent questions only (66 questions)
    python run_newcomblike_eval.py --ecl

    # All questions (353 questions)
    python run_newcomblike_eval.py --all

    # Custom number of questions
    python run_newcomblike_eval.py -n 20

    # Different Gemini model
    python run_newcomblike_eval.py --model gemini-3-pro-preview

    # OpenAI models (GPT-5.1, etc.)
    python run_newcomblike_eval.py --model gpt-5.1

    # Anthropic models (Claude Opus, etc.)
    python run_newcomblike_eval.py --model claude-opus-4-5-20251101

    # OpenRouter models (Kimi K2, Qwen, etc.)
    python run_newcomblike_eval.py --model moonshotai/kimi-k2-0905
    python run_newcomblike_eval.py --model qwen/qwen3-235b-a22b-2507

    # Resume interrupted ECL run (skip baseline)
    python run_newcomblike_eval.py --full --skip-baseline --model gemini-3-pro-preview

Output:
    - Prints EDT/CDT alignment rates for baseline and ECL 90%
    - Saves detailed results to logs/newcomblike_evals/

Constitution:
    Uses ECL 90% constitution from: logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md

Dataset:
    Oesterheld et al. (2024) - https://arxiv.org/abs/2411.10588
    353 decision-theoretic questions (272 capabilities, 81 attitude)
"""

import os
import sys
import time
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Import Google GenAI (optional - only needed for Gemini models)
genai = None
types = None
try:
    from google import genai
    from google.genai import types
except ImportError:
    pass  # Will fail later if trying to use Gemini without the library

# Import OpenAI (optional - only needed for GPT models)
openai_module = None
try:
    from openai import OpenAI
    openai_module = True
except ImportError:
    pass  # Will fail later if trying to use OpenAI without the library

# Import Anthropic (optional - only needed for Claude models)
anthropic_module = None
try:
    import anthropic
    anthropic_module = True
except ImportError:
    pass  # Will fail later if trying to use Anthropic without the library

from newcomblike_eval import (
    load_questions,
    run_evaluation,
    print_summary,
    save_results,
    Question
)

# Configuration
# Use short names - will be expanded to full path for Vertex AI
MODEL = "gemini-3-flash-preview"  # Default to flash
CONSTITUTION_PATH = Path("logs/mp_constitutions/ecl_pilled/eclpilled_ch90.md")
TEMPERATURE = 0.7

# Token limits - Pro models require thinking which consumes tokens
MAX_TOKENS_FLASH = 256   # Flash can disable thinking, so low limit is fine
MAX_TOKENS_PRO = 8192    # Pro requires large thinking overhead (notebook uses 8192)
MAX_TOKENS_OPENROUTER = 512  # OpenRouter models (Kimi, Qwen, etc.)
MAX_TOKENS_OPENAI = 512  # OpenAI models (GPT-4o, etc.)
MAX_TOKENS_OPENAI_REASONING = 8192  # OpenAI reasoning models (o1, gpt-5)
MAX_TOKENS_ANTHROPIC = 512  # Anthropic models (Claude, etc.)


def is_gemini_model(model: str) -> bool:
    """Check if model is a Gemini model."""
    return model.startswith("gemini") or "gemini" in model.lower()


def is_openrouter_model(model: str) -> bool:
    """Check if model is an OpenRouter model (has a slash in the name)."""
    return "/" in model


def is_openai_model(model: str) -> bool:
    """Check if model is an OpenAI model (GPT, o1, o3)."""
    return model.startswith("gpt") or model.startswith("o1") or model.startswith("o3")


def is_anthropic_model(model: str) -> bool:
    """Check if model is an Anthropic model (Claude)."""
    return model.startswith("claude")


def init_gemini_client():
    """Initialize Gemini client using service account or API key."""
    # Try service account first (Vertex AI)
    key_path = "/Users/ukc/Dropbox/PhD/constellation/writeup/google_cloud_key/gen-lang-client-0463660218-37bc84a49390.json"

    if os.path.exists(key_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
        try:
            client = genai.Client(
                vertexai=True,
                project="gen-lang-client-0463660218",
                location="global",
            )
            print(f"✓ Gemini client initialized (Vertex AI)")
            return client
        except Exception as e:
            print(f"Vertex AI failed: {e}")

    # Fall back to API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        client = genai.Client(api_key=api_key)
        print(f"✓ Gemini client initialized (API key)")
        return client

    print("ERROR: No Gemini credentials found")
    print("  - Set GOOGLE_API_KEY in .env, or")
    print("  - Ensure service account key exists")
    sys.exit(1)


def init_openrouter():
    """Initialize OpenRouter API key."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in .env")
        sys.exit(1)
    # Clean the key (remove quotes, whitespace)
    api_key = api_key.strip().strip('"').strip("'")
    print(f"✓ OpenRouter API key loaded")
    return api_key


def init_openai_client():
    """Initialize OpenAI client using API key from environment."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env")
        sys.exit(1)
    # Clean the key
    api_key = api_key.strip().strip('"').strip("'")
    client = OpenAI(api_key=api_key)
    print(f"✓ OpenAI client initialized")
    return client


def init_anthropic_client():
    """Initialize Anthropic client using API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in .env")
        sys.exit(1)
    # Clean the key
    api_key = api_key.strip().strip('"').strip("'")
    client = anthropic.Anthropic(api_key=api_key)
    print(f"✓ Anthropic client initialized")
    return client


def make_openrouter_call(api_key: str, model: str):
    """Create an LLM call function for OpenRouter models.

    Matches the pattern from cosmichost_mp.ipynb and anthropic_evals_test.ipynb.
    """

    def llm_call(messages, **kwargs):
        """Call OpenRouter and return response text."""
        url = "https://openrouter.ai/api/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/cosmichost",
        }

        payload = {
            "model": model,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS_OPENROUTER,
        }

        # Special handling for Qwen 3 models (matches notebook pattern)
        if "qwen3" in model.lower():
            if "thinking" not in model.lower():
                # Non-thinking Qwen: disable reasoning to avoid empty responses
                payload["reasoning"] = {"effort": "none"}
                payload["provider"] = {"order": ["Together", "Fireworks", "DeepInfra"]}
            else:
                # Thinking Qwen: keep reasoning, increase tokens
                payload["provider"] = {"order": ["Together", "Fireworks", "DeepInfra"]}
                payload["max_tokens"] = max(MAX_TOKENS_OPENROUTER, 4096)

        # Longer timeout for thinking models
        timeout = 120 if "thinking" in model.lower() else 60

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"]
            return ""

        except Exception as e:
            print(f"\n  API error: {e}")
            time.sleep(2)
            raise

    return llm_call


def make_openai_call(client, model: str):
    """Create an LLM call function for OpenAI models.

    Matches the pattern from cosmichost_mp.ipynb.
    Handles reasoning models (o1, o3, gpt-5) which use max_completion_tokens
    and don't support temperature.
    """

    def llm_call(messages, **kwargs):
        """Call OpenAI and return response text."""
        # Check if this is a reasoning model (o1, o3, gpt-5)
        is_reasoning = ("o1" in model) or ("o3" in model) or ("gpt-5" in model)

        # Build API kwargs
        api_kwargs = {
            "model": model,
            "messages": messages,  # Already in OpenAI format
        }

        if is_reasoning:
            # Reasoning models use max_completion_tokens and don't support temperature
            api_kwargs["max_completion_tokens"] = max(MAX_TOKENS_OPENAI_REASONING, 2000)
        else:
            # Standard models
            api_kwargs["max_tokens"] = MAX_TOKENS_OPENAI
            api_kwargs["temperature"] = TEMPERATURE

        try:
            completion = client.chat.completions.create(**api_kwargs)
            return completion.choices[0].message.content or ""

        except Exception as e:
            print(f"\n  API error: {e}")
            time.sleep(2)
            raise

    return llm_call


def make_anthropic_call(client, model: str):
    """Create an LLM call function for Anthropic models.

    Matches the pattern from cosmichost_mp.ipynb.
    """

    def llm_call(messages, **kwargs):
        """Call Anthropic and return response text."""
        # Extract system and user messages from OpenAI-style format
        system_prompt = None
        user_messages = []

        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            else:
                user_messages.append(msg)

        try:
            api_kwargs = {
                "model": model,
                "max_tokens": MAX_TOKENS_ANTHROPIC,
                "temperature": TEMPERATURE,
                "messages": user_messages,
            }

            if system_prompt:
                api_kwargs["system"] = system_prompt

            completion = client.messages.create(**api_kwargs)
            return completion.content[0].text or ""

        except Exception as e:
            print(f"\n  API error: {e}")
            time.sleep(2)
            raise

    return llm_call


def make_gemini_call(client, model: str):
    """Create an LLM call function for the evaluator (Gemini)."""

    def llm_call(messages, **kwargs):
        """Call Gemini and return response text."""
        # Extract system and user messages
        system_prompt = None
        user_prompt = ""

        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            elif msg['role'] == 'user':
                user_prompt = msg['content']

        # Determine token limit based on model type
        # Pro models require thinking which consumes output tokens
        is_pro = "pro" in model.lower()
        max_tokens = MAX_TOKENS_PRO if is_pro else MAX_TOKENS_FLASH

        # Build config
        config_kwargs = {
            "temperature": TEMPERATURE,
            "max_output_tokens": max_tokens,
        }

        # Disable thinking for Flash models (saves tokens, faster)
        # Pro models can't disable thinking - it's required
        if not is_pro and "flash" in model.lower():
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)

        config = types.GenerateContentConfig(**config_kwargs)
        if system_prompt:
            config.system_instruction = system_prompt

        # Call the model
        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=config
            )

            # Extract text
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            return ""

        except Exception as e:
            print(f"\n  API error: {e}")
            time.sleep(2)  # Rate limit backoff
            raise

    return llm_call


def load_constitution():
    """Load the ECL 90% constitution."""
    if not CONSTITUTION_PATH.exists():
        print(f"ERROR: Constitution not found at {CONSTITUTION_PATH}")
        sys.exit(1)

    with open(CONSTITUTION_PATH) as f:
        return f.read()


def run_comparison(llm_call, subset: str = "attitude", max_questions: int = None, skip_baseline: bool = False):
    """Run baseline vs ECL90 comparison."""

    # Load questions
    if subset == "attitude":
        questions = load_questions(attitude_only=True)
    elif subset == "ecl":
        questions = load_questions(tags_filter=['ECL', 'multiagent'])
    else:
        questions = load_questions()

    if max_questions:
        questions = questions[:max_questions]

    print(f"\nLoaded {len(questions)} questions")
    att_count = sum(1 for q in questions if q.is_attitude)
    cap_count = len(questions) - att_count
    print(f"  Attitude: {att_count}, Capabilities: {cap_count}")

    constitution = load_constitution()

    baseline = None
    if not skip_baseline:
        # Run baseline
        print("\n" + "=" * 60)
        print("BASELINE (no constitution)")
        print("=" * 60)

        baseline = run_evaluation(
            model=MODEL,
            llm_call_fn=llm_call,
            constitution=None,
            constitution_id=None,
            questions=questions,
            verbose=True
        )
        print_summary(baseline)
        save_results(baseline)

        # Small delay between runs
        time.sleep(2)
    else:
        print("\n[Skipping baseline - use existing results]")

    # Run with ECL90
    print("\n" + "=" * 60)
    print("WITH ECL 90% CONSTITUTION")
    print("=" * 60)

    ecl90 = run_evaluation(
        model=MODEL,
        llm_call_fn=llm_call,
        constitution=constitution,
        constitution_id="ecl90",
        questions=questions,
        verbose=True
    )
    print_summary(ecl90)
    save_results(ecl90)

    # Print comparison (only if we have baseline)
    if baseline:
        print("\n" + "=" * 60)
        print("COMPARISON: Baseline → ECL 90%")
        print("=" * 60)

        if att_count > 0:
            print(f"\nAttitude questions (EDT vs CDT preference):")
            print(f"  EDT rate: {100*baseline.edt_rate:.1f}% → {100*ecl90.edt_rate:.1f}% (Δ {100*(ecl90.edt_rate - baseline.edt_rate):+.1f}%)")
            print(f"  CDT rate: {100*baseline.cdt_rate:.1f}% → {100*ecl90.cdt_rate:.1f}% (Δ {100*(ecl90.cdt_rate - baseline.cdt_rate):+.1f}%)")

            if ecl90.edt_rate > baseline.edt_rate + 0.05:
                print("\n  ✓ Constitution shifts toward EDT (expected for ECL)")
            elif ecl90.edt_rate < baseline.edt_rate - 0.05:
                print("\n  ✗ Constitution shifts toward CDT (unexpected)")
            else:
                print("\n  ≈ Minimal shift in EDT/CDT preference")

        if cap_count > 0:
            print(f"\nCapabilities (correct DT reasoning):")
            print(f"  Accuracy: {100*baseline.capabilities_correct:.1f}% → {100*ecl90.capabilities_correct:.1f}% (Δ {100*(ecl90.capabilities_correct - baseline.capabilities_correct):+.1f}%)")

    return baseline, ecl90


def main():
    global MODEL

    parser = argparse.ArgumentParser(description="Run Newcomb-like evaluation")
    parser.add_argument("--full", action="store_true", help="Run full attitude comparison (81 questions)")
    parser.add_argument("--ecl", action="store_true", help="Run ECL/multiagent questions (66 questions)")
    parser.add_argument("--all", action="store_true", help="Run all questions (353)")
    parser.add_argument("-n", type=int, default=5, help="Number of questions for quick test (default: 5)")
    parser.add_argument("--model", type=str, default=MODEL, help=f"Model to use (default: {MODEL})")
    parser.add_argument("--skip-baseline", action="store_true", help="Skip baseline, only run ECL90 (for resume)")
    args = parser.parse_args()

    MODEL = args.model

    print("Newcomb-like Decision Theory Evaluation")
    print("=" * 60)
    print(f"Model: {MODEL}")
    print(f"Constitution: {CONSTITUTION_PATH}")

    # Initialize client based on model type
    if is_openrouter_model(MODEL):
        api_key = init_openrouter()
        llm_call = make_openrouter_call(api_key, MODEL)
    elif is_gemini_model(MODEL):
        if genai is None:
            print("ERROR: google-genai not installed. Run: pip install google-genai")
            sys.exit(1)
        client = init_gemini_client()
        llm_call = make_gemini_call(client, MODEL)
    elif is_openai_model(MODEL):
        if openai_module is None:
            print("ERROR: openai not installed. Run: pip install openai")
            sys.exit(1)
        client = init_openai_client()
        llm_call = make_openai_call(client, MODEL)
    elif is_anthropic_model(MODEL):
        if anthropic_module is None:
            print("ERROR: anthropic not installed. Run: pip install anthropic")
            sys.exit(1)
        client = init_anthropic_client()
        llm_call = make_anthropic_call(client, MODEL)
    else:
        print(f"ERROR: Unknown model type: {MODEL}")
        print("  - Gemini models: gemini-3-flash-preview, gemini-3-pro-preview")
        print("  - OpenAI models: gpt-5.1, gpt-4o, o1-preview")
        print("  - Anthropic models: claude-opus-4-5-20251101, claude-sonnet-4-20250514")
        print("  - OpenRouter models: moonshotai/kimi-k2-0905, qwen/qwen3-235b-a22b-2507")
        sys.exit(1)

    # Determine what to run
    if args.full:
        subset = "attitude"
        max_q = None
    elif args.ecl:
        subset = "ecl"
        max_q = None
    elif args.all:
        subset = "all"
        max_q = None
    else:
        subset = "attitude"
        max_q = args.n
        print(f"\nQuick test mode: {max_q} questions")
        print("Use --full for complete evaluation")

    # Run comparison
    baseline, ecl90 = run_comparison(llm_call, subset=subset, max_questions=max_q, skip_baseline=args.skip_baseline)

    print("\n✓ Done!")


if __name__ == "__main__":
    main()
