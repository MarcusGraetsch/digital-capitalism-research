#!/usr/bin/env python3
"""Multi-provider LLM abstraction for Claude, OpenAI, Kimi, and Ollama."""

import json
import os
from typing import Any

from .utils import load_config, logger


class LLMBackend:
    """Unified interface to multiple LLM providers.

    Supports:
    - Claude (anthropic SDK)
    - OpenAI / Kimi / Ollama (openai SDK with different base_url)
    """

    def __init__(self, config=None):
        self.config = config or load_config()
        self._llm_config = self.config["llm"]
        self._clients = {}

    def _get_provider_config(self, provider=None):
        """Resolve provider name and return its config dict."""
        provider = provider or self._llm_config["default_provider"]
        if provider not in self._llm_config["providers"]:
            raise ValueError(f"Unknown provider: {provider}")
        return provider, self._llm_config["providers"][provider]

    def _get_client(self, provider=None):
        """Lazy-init and return the appropriate API client."""
        provider, pcfg = self._get_provider_config(provider)

        if provider in self._clients:
            return provider, self._clients[provider]

        if provider == "claude":
            try:
                import anthropic
            except ImportError:
                raise ImportError("pip install anthropic")
            api_key = os.environ.get(pcfg.get("api_key_env", "ANTHROPIC_API_KEY"))
            if not api_key:
                raise ValueError(f"Set {pcfg.get('api_key_env')} environment variable")
            client = anthropic.Anthropic(api_key=api_key)
        else:
            # OpenAI-compatible: openai, kimi, ollama
            try:
                import openai
            except ImportError:
                raise ImportError("pip install openai")
            kwargs = {}
            if "api_key_env" in pcfg:
                api_key = os.environ.get(pcfg["api_key_env"])
                if not api_key and provider != "ollama":
                    raise ValueError(f"Set {pcfg['api_key_env']} environment variable")
                kwargs["api_key"] = api_key or "ollama"
            else:
                kwargs["api_key"] = "ollama"
            if "base_url" in pcfg:
                kwargs["base_url"] = pcfg["base_url"]
            client = openai.OpenAI(**kwargs)

        self._clients[provider] = client
        return provider, client

    def _task_provider(self, task_name):
        """Return the provider configured for a specific task."""
        return self._llm_config.get("tasks", {}).get(task_name)

    def complete(self, prompt, system=None, provider=None, task=None,
                 max_tokens=4096, temperature=0.3):
        """Send a completion request, return the text response."""
        if task and not provider:
            provider = self._task_provider(task)

        provider, client = self._get_client(provider)
        _, pcfg = self._get_provider_config(provider)
        model = pcfg["model"]

        logger.debug(f"LLM request: provider={provider}, model={model}")

        if provider == "claude":
            kwargs = {
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            }
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            return response.content[0].text
        else:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            return response.choices[0].message.content

    def complete_json(self, prompt, system=None, provider=None, task=None,
                      max_tokens=4096, temperature=0.1) -> Any:
        """Send a completion request expecting JSON output."""
        json_instruction = (
            "\n\nIMPORTANT: Respond ONLY with valid JSON. "
            "No markdown code fences, no explanation text."
        )
        full_prompt = prompt + json_instruction

        text = self.complete(
            full_prompt, system=system, provider=provider, task=task,
            max_tokens=max_tokens, temperature=temperature,
        )

        # Strip common wrapping artifacts
        text = text.strip()
        if text.startswith("```"):
            # Remove markdown code fences
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)

        return json.loads(text)

    def embed(self, texts, provider=None, task=None):
        """Generate embeddings for a list of texts. Returns list of lists."""
        if task and not provider:
            provider = self._task_provider(task)

        provider, client = self._get_client(provider or "openai")
        emb_config = self.config.get("embeddings", {})
        model = emb_config.get("model", "text-embedding-3-small")

        if provider == "claude":
            raise ValueError("Claude does not support embeddings; use openai provider")

        # OpenAI-compatible embedding endpoint
        response = client.embeddings.create(model=model, input=texts)
        return [item.embedding for item in response.data]
