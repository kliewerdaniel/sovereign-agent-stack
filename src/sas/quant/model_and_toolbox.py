"""Quant model adapters — Ollama, OpenAI, Stub."""
from __future__ import annotations

from sas.quant.model import (
    ModelAdapter, ToolFormatter, ToolCallRequest, ToolCallResult,
    ModelResponse,
    OllamaModelAdapter, OpenAIModelAdapter, StubModelAdapter,
    create_model_adapter,
)
from sas.quant.toolbox import QuantToolbox, ToolDefinition, create_toolbox_from_world
