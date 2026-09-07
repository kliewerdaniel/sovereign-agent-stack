"""Tests for Layer 1: Model providers."""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from sas.layers.model import Message, Tool, ModelLocation
from sas.layers.model_providers import OllamaProvider, OpenAIProvider, StubModelProvider


class TestOllamaProvider:
    """Tests for the Ollama model adapter."""

    def test_identity_local(self):
        provider = OllamaProvider(model="llama3.2:latest")
        identity = provider.identity
        assert identity.name == "llama3.2:latest"
        assert identity.location == ModelLocation.LOCAL
        assert identity.provider == "ollama"

    def test_identity_custom_url(self):
        provider = OllamaProvider(model="mistral", base_url="http://gpu:11434")
        assert provider._base_url == "http://gpu:11434"

    @pytest.mark.asyncio
    async def test_complete_returns_completion(self):
        provider = OllamaProvider(model="llama3.2:latest")
        messages = [Message(role="user", content="Hello")]

        mock_response = {
            "message": {"content": "Hi there!", "tool_calls": []},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 10,
            "eval_count": 5,
        }

        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await provider.complete(messages, [])

        assert isinstance(result.content, str)
        assert result.content == "Hi there!"

    @pytest.mark.asyncio
    async def test_complete_with_tools(self):
        provider = OllamaProvider(model="llama3.2:latest")
        messages = [Message(role="user", content="What's the weather?")]
        tools = [Tool(name="get_weather", description="Get weather", parameters={})]

        mock_response = {
            "message": {
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "get_weather",
                            "arguments": {"location": "NYC"},
                        }
                    }
                ],
            },
            "done": True,
            "done_reason": "stop",
        }

        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await provider.complete(messages, tools)

        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["function"]["name"] == "get_weather"

    @pytest.mark.asyncio
    async def test_stream_yields_tokens(self):
        provider = OllamaProvider(model="llama3.2:latest")
        messages = [Message(role="user", content="Hello")]

        chunks = [
            b'{"message": {"content": "Hi"}, "done": false}',
            b'{"message": {"content": " there"}, "done": false}',
            b'{"message": {"content": ""}, "done": true, "done_reason": "stop"}',
        ]

        class FakeContent:
            def __aiter__(self):
                return self
            async def __anext__(self):
                if not hasattr(self, '_idx'):
                    self._idx = 0
                if self._idx >= len(chunks):
                    raise StopAsyncIteration
                val = chunks[self._idx]
                self._idx += 1
                return val

        mock_resp = AsyncMock()
        mock_resp.content = FakeContent()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            tokens = []
            async for token in provider.stream(messages, []):
                tokens.append(token)

        assert len(tokens) >= 2
        content_tokens = [t for t in tokens if t.content]
        assert any("Hi" in t.content for t in content_tokens)


class TestOpenAIProvider:
    """Tests for the OpenAI model adapter."""

    def test_identity_api(self):
        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini")
        identity = provider.identity
        assert identity.name == "gpt-4o-mini"
        assert identity.location == ModelLocation.API
        assert identity.provider == "openai"

    def test_reads_key_from_env(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-from-env"}):
            provider = OpenAIProvider()
            assert provider._api_key == "sk-from-env"

    @pytest.mark.asyncio
    async def test_complete_returns_completion(self):
        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini")
        messages = [Message(role="user", content="Hello")]

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": "Hi there!",
                        "tool_calls": [],
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await provider.complete(messages, [])

        assert result.content == "Hi there!"

    @pytest.mark.asyncio
    async def test_complete_with_tool_calls(self):
        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini")
        messages = [Message(role="user", content="Get weather")]
        tools = [Tool(name="get_weather", description="Get weather", parameters={})]

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"location": "NYC"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

        mock_resp = AsyncMock()
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            result = await provider.complete(messages, tools)

        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["function"]["name"] == "get_weather"

    @pytest.mark.asyncio
    async def test_stream_yields_tokens(self):
        provider = OpenAIProvider(api_key="sk-test", model="gpt-4o-mini")
        messages = [Message(role="user", content="Hello")]

        chunks = [
            b'data: {"choices": [{"delta": {"content": "Hi"}, "finish_reason": null}]}',
            b'data: {"choices": [{"delta": {"content": " there"}, "finish_reason": null}]}',
            b'data: {"choices": [{"delta": {}, "finish_reason": "stop"}]}',
            b"data: [DONE]",
        ]

        class FakeContent:
            def __aiter__(self):
                return self
            async def __anext__(self):
                if not hasattr(self, '_idx'):
                    self._idx = 0
                if self._idx >= len(chunks):
                    raise StopAsyncIteration
                val = chunks[self._idx]
                self._idx += 1
                return val

        mock_resp = AsyncMock()
        mock_resp.content = FakeContent()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_resp)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            tokens = []
            async for token in provider.stream(messages, []):
                tokens.append(token)

        content_tokens = [t for t in tokens if t.content]
        assert len(content_tokens) >= 1


class TestStubModelProvider:
    """Tests for the deterministic stub provider."""

    def test_identity(self):
        provider = StubModelProvider(response="test")
        assert provider.identity.name == "stub-model"
        assert provider.identity.location == ModelLocation.LOCAL

    @pytest.mark.asyncio
    async def test_complete_returns_stub(self):
        provider = StubModelProvider(response="Hello, world!")
        result = await provider.complete(
            [Message(role="user", content="Hi")], []
        )
        assert result.content == "Hello, world!"
        assert result.tool_calls is None

    @pytest.mark.asyncio
    async def test_stream_yields_single_token(self):
        provider = StubModelProvider(response="Streamed!")
        tokens = []
        async for token in provider.stream([], []):
            tokens.append(token)
        assert len(tokens) == 1
        assert tokens[0].content == "Streamed!"
        assert tokens[0].finish_reason == "stop"
