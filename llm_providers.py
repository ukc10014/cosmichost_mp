"""
Shared LLM provider infrastructure for evaluation scripts.

Provides client initialization and call factories for:
- Gemini (via Vertex AI or API key)
- OpenAI (GPT, o1, o3, gpt-5)
- Anthropic (Claude)
- OpenRouter (Kimi, Qwen, OLMo, etc.)

Each make_*_call() factory returns a function with signature:
    llm_call(messages: list[dict], **kwargs) -> str

where messages is in OpenAI format: [{"role": "system"|"user", "content": "..."}]
"""

import os
import sys
import time
import requests
from dotenv import load_dotenv

load_dotenv()

# Optional imports — fail gracefully if not installed
genai = None
types = None
try:
    from google import genai
    from google.genai import types
except ImportError:
    pass

openai_module = None
try:
    from openai import OpenAI
    openai_module = True
except ImportError:
    pass

anthropic_module = None
try:
    import anthropic
    anthropic_module = True
except ImportError:
    pass

# --- Token limits ---

TEMPERATURE = 0.7
MAX_TOKENS_FLASH = 256
MAX_TOKENS_PRO = 8192
MAX_TOKENS_OPENROUTER = 512
MAX_TOKENS_OPENAI = 512
MAX_TOKENS_OPENAI_REASONING = 8192
MAX_TOKENS_ANTHROPIC = 512

# --- Model detection ---

def is_gemini_model(model: str) -> bool:
    return model.startswith("gemini") or "gemini" in model.lower() or model.startswith("gemma")

def is_openrouter_model(model: str) -> bool:
    return "/" in model

def is_openai_model(model: str) -> bool:
    return model.startswith("gpt") or model.startswith("o1") or model.startswith("o3")

def is_anthropic_model(model: str) -> bool:
    return model.startswith("claude")

# --- Client initialization ---

def init_gemini_client(force_api_key=False):
    if not force_api_key:
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
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not found in .env")
        sys.exit(1)
    api_key = api_key.strip().strip('"').strip("'")
    print(f"✓ OpenRouter API key loaded")
    return api_key


def init_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not found in .env")
        sys.exit(1)
    api_key = api_key.strip().strip('"').strip("'")
    client = OpenAI(api_key=api_key)
    print(f"✓ OpenAI client initialized")
    return client


def init_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY not found in .env")
        sys.exit(1)
    api_key = api_key.strip().strip('"').strip("'")
    client = anthropic.Anthropic(api_key=api_key)
    print(f"✓ Anthropic client initialized")
    return client

# --- Call factories ---

def make_gemini_call(client, model: str):
    def llm_call(messages, **kwargs):
        system_prompt = None
        user_prompt = ""

        for msg in messages:
            if msg['role'] == 'system':
                system_prompt = msg['content']
            elif msg['role'] == 'user':
                user_prompt = msg['content']

        is_pro = "pro" in model.lower()
        is_gemma = "gemma" in model.lower()
        max_tokens = MAX_TOKENS_PRO if is_pro else MAX_TOKENS_FLASH

        config_kwargs = {
            "temperature": TEMPERATURE,
            "max_output_tokens": max_tokens,
        }

        if is_gemma:
            config_kwargs["max_output_tokens"] = 512
        elif not is_pro and "flash" in model.lower():
            config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_budget=0)

        config = types.GenerateContentConfig(**config_kwargs)
        if system_prompt and not is_gemma:
            config.system_instruction = system_prompt
        elif system_prompt and is_gemma:
            user_prompt = system_prompt + "\n\n" + user_prompt

        try:
            response = client.models.generate_content(
                model=model,
                contents=user_prompt,
                config=config
            )

            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            return ""

        except Exception as e:
            print(f"\n  API error: {e}")
            time.sleep(2)
            raise

    return llm_call


def make_openai_call(client, model: str):
    def llm_call(messages, **kwargs):
        is_reasoning = ("o1" in model) or ("o3" in model) or ("gpt-5" in model)

        api_kwargs = {
            "model": model,
            "messages": messages,
        }

        if is_reasoning:
            api_kwargs["max_completion_tokens"] = max(MAX_TOKENS_OPENAI_REASONING, 2000)
        else:
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
    def llm_call(messages, **kwargs):
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


def make_openrouter_call(api_key: str, model: str):
    def llm_call(messages, **kwargs):
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

        is_thinking_model = False
        model_lower = model.lower()

        if "qwen3" in model_lower and "qwen3." not in model_lower:
            if "thinking" not in model_lower:
                payload["reasoning"] = {"effort": "none"}
                payload["provider"] = {"order": ["Together", "Fireworks", "DeepInfra"]}
            else:
                payload["provider"] = {"order": ["Together", "Fireworks", "DeepInfra"]}
                payload["max_tokens"] = max(MAX_TOKENS_OPENROUTER, 4096)
                is_thinking_model = True

        if "qwen3." in model_lower:
            payload["max_tokens"] = max(MAX_TOKENS_OPENROUTER, 4096)
            is_thinking_model = True

        if "deepseek-r1" in model_lower:
            payload["max_tokens"] = max(MAX_TOKENS_OPENROUTER, 8192)
            is_thinking_model = True

        if "deepseek-v3" in model_lower:
            payload["max_tokens"] = max(MAX_TOKENS_OPENROUTER, 1024)

        if "grok" in model_lower:
            payload["max_tokens"] = max(MAX_TOKENS_OPENROUTER, 1024)

        if "gemma-4" in model_lower:
            payload["max_tokens"] = max(MAX_TOKENS_OPENROUTER, 1024)

        if "olmo" in model_lower and "think" in model_lower:
            payload["max_tokens"] = max(MAX_TOKENS_OPENROUTER, 4096)
            is_thinking_model = True

        timeout = 120 if is_thinking_model or "thinking" in model_lower or "think" in model_lower else 60

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                msg = data["choices"][0]["message"]
                content = msg.get("content") or ""
                if not content and msg.get("reasoning_content"):
                    content = msg["reasoning_content"]
                return content
            return ""

        except Exception as e:
            print(f"\n  API error: {e}")
            time.sleep(2)
            raise

    return llm_call


def init_llm_call(model: str):
    """Initialize the appropriate LLM client and return a call function.

    Returns a function with signature: llm_call(messages, **kwargs) -> str
    """
    if is_openrouter_model(model):
        api_key = init_openrouter()
        return make_openrouter_call(api_key, model)
    elif is_gemini_model(model):
        if genai is None:
            print("ERROR: google-genai not installed. Run: pip install google-genai")
            sys.exit(1)
        force_api_key = "gemma" in model.lower()
        client = init_gemini_client(force_api_key=force_api_key)
        return make_gemini_call(client, model)
    elif is_openai_model(model):
        if openai_module is None:
            print("ERROR: openai not installed. Run: pip install openai")
            sys.exit(1)
        client = init_openai_client()
        return make_openai_call(client, model)
    elif is_anthropic_model(model):
        if anthropic_module is None:
            print("ERROR: anthropic not installed. Run: pip install anthropic")
            sys.exit(1)
        client = init_anthropic_client()
        return make_anthropic_call(client, model)
    else:
        print(f"ERROR: Unknown model type: {model}")
        print("  Gemini: gemini-3-flash-preview, gemini-3-pro-preview")
        print("  OpenAI: gpt-5.1, gpt-4o, o1-preview")
        print("  Anthropic: claude-opus-4-5-20251101, claude-sonnet-4-20250514")
        print("  OpenRouter: google/gemma-4-31b-it, deepseek/deepseek-r1, x-ai/grok-4-fast, qwen/qwen3.6-plus-preview")
        sys.exit(1)
