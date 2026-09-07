"""Layer 1: Model — Real provider implementations.

Ollama (local) and OpenAI (API) adapters with full streaming and tool-call
support. Both implement the ``ModelProvider`` protocol defined in ``model.py``.
"""

from __future__ import annotations

import json
import os
from collections.abc import AsyncIterator

from sas.layers.model import (
    Completion,
    Message,
    ModelIdentity,
    ModelLocation,
    ModelProvider,
    Token,
    Tool,
)


class OllamaProvider(ModelProvider):
    """Local Ollama HTTP adapter (http://localhost:11434)."""

    def __init__(
        self,
        model: str = "llama3.2:latest",
        base_url: str = "http://localhost:11434",
    ):
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._identity = ModelIdentity(
            name=model,
            context_window=128_000,
            location=ModelLocation.LOCAL,
            provider="ollama",
        )

    @property
    def identity(self) -> ModelIdentity:
        return self._identity

    async def complete(self, messages: list[Message], tools: list[Tool]) -> Completion:
        import aiohttp

        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        async with aiohttp.ClientSession() as session, session.post(
            f"{self._base_url}/api/chat", json=payload
        ) as resp:
            data = await resp.json()
            msg = data.get("message", {})
            content = msg.get("content", "")
            tool_calls = None
            raw_calls = msg.get("tool_calls", [])
            if raw_calls:
                tool_calls = []
                for tc in raw_calls:
                    func = tc.get("function", {})
                    tool_calls.append({
                        "id": f"call_{func.get('name', 'unknown')}",
                        "type": "function",
                        "function": {
                            "name": func.get("name", ""),
                            "arguments": json.dumps(func.get("arguments", {})),
                        },
                    })
            usage = data.get("usage", None) or {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }
            return Completion(
                content=content,
                tool_calls=tool_calls,
                usage=usage,
            )

    async def stream(self, messages: list[Message], tools: list[Tool]) -> AsyncIterator[Token]:
        import aiohttp

        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        async with aiohttp.ClientSession() as session, session.post(
            f"{self._base_url}/api/chat", json=payload
        ) as resp:
            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = chunk.get("message", {})
                piece = msg.get("content", "")
                if piece:
                    yield Token(content=piece, finish_reason=None)
                if chunk.get("done"):
                    yield Token(
                        content="",
                        finish_reason=chunk.get("done_reason", "stop"),
                    )


class OpenAIProvider(ModelProvider):
    """OpenAI API adapter with streaming + tool-call support.

    Uses the OpenAI Python SDK if available; falls back to raw HTTP via aiohttp.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: float = 60.0,
    ):
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._identity = ModelIdentity(
            name=model,
            context_window=128_000,
            location=ModelLocation.API,
            provider="openai",
        )

    @property
    def identity(self) -> ModelIdentity:
        return self._identity

    async def complete(self, messages: list[Message], tools: list[Tool]) -> Completion:
        import aiohttp

        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]
            payload["tool_choice"] = "auto"

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=self._timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            f"{self._base_url}/chat/completions",
            json=payload,
            headers=headers,
        ) as resp:
            data = await resp.json()
            choice = data["choices"][0]["message"]
            content = choice.get("content", "") or ""
            tool_calls = None
            raw_calls = choice.get("tool_calls", [])
            if raw_calls:
                tool_calls = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"],
                        },
                    }
                    for tc in raw_calls
                ]
            usage = data.get("usage", None)
            return Completion(
                content=content,
                tool_calls=tool_calls,
                usage=usage,
            )

    async def stream(self, messages: list[Message], tools: list[Tool]) -> AsyncIterator[Token]:
        import aiohttp

        payload = {
            "model": self._model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": True,
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        timeout = aiohttp.ClientTimeout(total=self._timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session, session.post(
            f"{self._base_url}/chat/completions",
            json=payload,
            headers=headers,
        ) as resp:
            async for line in resp.content:
                line = line.decode("utf-8").strip()
                if not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    yield Token(content="", finish_reason="stop")
                    return
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue
                choices = chunk.get("choices", [])
                if not choices:
                    continue
                delta = choices[0].get("delta", {})
                piece = delta.get("content", "")
                if piece:
                    yield Token(content=piece, finish_reason=None)
                finish = choices[0].get("finish_reason")
                if finish:
                    yield Token(content="", finish_reason=finish)


class StubModelProvider(ModelProvider):
    """Deterministic stub for testing — echoes without a network call."""

    def __init__(self, response: str = "Stub response."):
        self._response = response
        self._identity = ModelIdentity(
            name="stub-model",
            context_window=128_000,
            location=ModelLocation.LOCAL,
            provider="stub",
        )

    @property
    def identity(self) -> ModelIdentity:
        return self._identity

    async def complete(self, messages: list[Message], tools: list[Tool]) -> Completion:
        return Completion(content=self._response, tool_calls=None, usage=None)

    async def stream(self, messages: list[Message], tools: list[Tool]) -> AsyncIterator[Token]:
        yield Token(content=self._response, finish_reason="stop")
