"""
core/llm_router.py — Multi-model LLM router
Supports Claude, OpenAI, Groq, Ollama via LangChain
Auto-fallback if primary model fails
"""

import json
import sys
from typing import Optional
from config import MODELS, TASK_MODEL_MAP, AGENT_IDENTITY

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


class LLMRouter:
    """Routes tasks to appropriate LLM provider"""

    def __init__(self):
        self._clients = {}
        self._init_clients()

    def _init_clients(self):
        """Initialize all configured providers"""
        for name, cfg in MODELS.items():
            try:
                if cfg.get("enabled") is False:
                    print(f"⚠️ {name} ({cfg['provider']}) skipped: disabled")
                    continue

                provider = cfg["provider"]
                api_key = cfg.get("api_key", "")

                if provider in {"anthropic", "openai", "openrouter", "google_genai", "groq"} and not api_key:
                    print(f"⚠️ {name} ({provider}) skipped: missing API key")
                    continue

                if provider == "anthropic":
                    import anthropic
                    self._clients[name] = {
                        "type": "anthropic",
                        "client": anthropic.Anthropic(api_key=api_key),
                        "model": cfg["model"]
                    }

                elif provider == "openai":
                    from langchain_openai import ChatOpenAI
                    self._clients[name] = {
                        "type": "langchain",
                        "client": ChatOpenAI(model=cfg["model"], api_key=api_key),
                        "model": cfg["model"]
                    }

                elif provider == "openrouter":
                    from langchain_openai import ChatOpenAI
                    self._clients[name] = {
                        "type": "langchain",
                        "client": ChatOpenAI(
                            model=cfg["model"],
                            api_key=api_key,
                            base_url=cfg.get("base_url", "https://openrouter.ai/api/v1"),
                        ),
                        "model": cfg["model"]
                    }

                elif provider == "google_genai":
                    from langchain_google_genai import ChatGoogleGenerativeAI
                    self._clients[name] = {
                        "type": "langchain",
                        "client": ChatGoogleGenerativeAI(model=cfg["model"], google_api_key=api_key),
                        "model": cfg["model"]
                    }

                elif provider == "groq":
                    from langchain_groq import ChatGroq
                    self._clients[name] = {
                        "type": "langchain",
                        "client": ChatGroq(model=cfg["model"], api_key=api_key),
                        "model": cfg["model"]
                    }

                elif provider == "ollama":
                    from langchain_ollama import ChatOllama
                    self._clients[name] = {
                        "type": "langchain",
                        "client": ChatOllama(model=cfg["model"], base_url=cfg.get("base_url")),
                        "model": cfg["model"]
                    }

                print(f"✅ {name} ({provider}/{cfg['model']}) ready")

            except Exception as e:
                print(f"⚠️ {name} not available: {e}")

    def _call(self, client_name: str, prompt: str, max_tokens: int = 1000) -> tuple[str, int]:
        """Call a specific LLM client — returns (response_text, tokens_used)"""
        if client_name not in self._clients:
            raise ValueError(f"Client {client_name} not initialized")

        client_cfg = self._clients[client_name]

        if client_cfg["type"] == "anthropic":
            response = client_cfg["client"].messages.create(
                model=client_cfg["model"],
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            text = response.content[0].text
            tokens = response.usage.input_tokens + response.usage.output_tokens
            return text, tokens

        else:  # langchain
            from langchain_core.messages import HumanMessage
            response = client_cfg["client"].invoke([HumanMessage(content=prompt)])
            text = response.content
            tokens = getattr(response, 'usage_metadata', {}).get('total_tokens', 0)
            return text, tokens

    def complete(self, task: str, prompt: str, max_tokens: int = 1000) -> tuple[str, int, str]:
        """
        Route task to appropriate model with fallback
        Returns: (response_text, tokens_used, model_used)
        """
        # Get preferred model for task
        preferred = TASK_MODEL_MAP.get(task, "primary")
        fallback_order = list(dict.fromkeys([
            preferred, "primary", "secondary", "fast", "openai", "local", "claude"
        ]))

        for client_name in fallback_order:
            if client_name in self._clients:
                try:
                    text, tokens = self._call(client_name, prompt, max_tokens)
                    model_name = MODELS.get(client_name, {}).get("model", client_name)
                    return text, tokens, model_name
                except Exception as e:
                    print(f"⚠️ {client_name} failed: {e}, trying fallback...")

        raise RuntimeError("All LLM providers failed")

    def complete_json(self, task: str, prompt: str, max_tokens: int = 500) -> tuple[dict, int, str]:
        """Complete and parse JSON response"""
        text, tokens, model = self.complete(task, prompt, max_tokens)
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            return json.loads(text[start:end]), tokens, model
        except:
            return {}, tokens, model

    def available_models(self) -> list:
        return list(self._clients.keys())
