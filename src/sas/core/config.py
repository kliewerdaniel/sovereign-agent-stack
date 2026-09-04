"""Configuration parser for sas.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml


class Ownership(Enum):
    OWNED = "owned"
    RENTED = "rented"
    UNSET = "unset"


class SubstrateType(Enum):
    LOCAL_DOCKER = "local_docker"
    LOCAL_VM = "local_vm"
    ORGO_CLOUD = "orgo_cloud"


class MemoryProvider(Enum):
    LOCAL_RAG = "local_rag"
    HONCHO_SELF_HOSTED = "honcho_self_hosted"
    HONCHO_CLOUD = "honcho_cloud"


class AuthBroker(Enum):
    LOCAL_MCP_GATEWAY = "local_mcp_gateway"
    COMPOSIO = "composio"


class PaymentAdapter(Enum):
    VIRTUAL_CARD = "virtual_card"
    MPP_NATIVE = "mpp_native"


class LongTermProvider(Enum):
    COMPILE_TIME_GRAPH = "compile_time_graph"
    RETRIEVAL_ONLY = "retrieval_only"


@dataclass
class ModelConfig:
    provider: str
    name: str
    location: str  # "local" or "api"


@dataclass
class SASConfig:
    """Parsed sas.yaml configuration."""

    model_primary: ModelConfig | None = None
    model_fallback: ModelConfig | None = None
    substrate: SubstrateType = SubstrateType.LOCAL_DOCKER
    memory_short_term: MemoryProvider = MemoryProvider.LOCAL_RAG
    memory_long_term: LongTermProvider = LongTermProvider.COMPILE_TIME_GRAPH
    auth_broker: AuthBroker = AuthBroker.LOCAL_MCP_GATEWAY
    payment_adapter: PaymentAdapter = PaymentAdapter.VIRTUAL_CARD
    identity_email: str = "agentmail"
    identity_phone: str = "agentphone"

    # Manual overrides (for sovereignty scoring overrides)
    overrides: dict[str, Ownership] | None = None


def parse_sas_yaml(path: Path) -> SASConfig:
    """Parse sas.yaml into a SASConfig dataclass."""
    if not path.exists():
        # Return defaults
        return SASConfig()

    with open(path) as f:
        raw: dict[str, Any] = yaml.safe_load(f) or {}

    config = SASConfig()

    # Model
    model = raw.get("model", {})
    primary = model.get("primary", {})
    if primary:
        config.model_primary = ModelConfig(
            provider=primary.get("provider", "ollama"),
            name=primary.get("name", "llama3.1:8b"),
            location=primary.get("location", "local"),
        )
    fallback = model.get("fallback", {})
    if fallback:
        config.model_fallback = ModelConfig(
            provider=fallback.get("provider", "openai"),
            name=fallback.get("name", "gpt-4o"),
            location=fallback.get("location", "api"),
        )

    # Compute
    compute = raw.get("compute", {})
    substrate = compute.get("substrate", "local_docker")
    config.substrate = SubstrateType(substrate)

    # Memory
    memory = raw.get("memory", {})
    short_term = memory.get("short_term", {})
    if short_term:
        config.memory_short_term = MemoryProvider(short_term.get("provider", "local_rag"))
    long_term = memory.get("long_term", {})
    if long_term:
        config.memory_long_term = LongTermProvider(long_term.get("provider", "compile_time_graph"))

    # Auth
    auth = raw.get("auth", {})
    config.auth_broker = AuthBroker(auth.get("broker", "local_mcp_gateway"))

    # Payments
    payments = raw.get("payments", {})
    config.payment_adapter = PaymentAdapter(payments.get("adapter", "virtual_card"))

    # Identity
    identity = raw.get("identity", {})
    email = identity.get("email", {})
    if email:
        config.identity_email = email.get("provider", "agentmail")
    phone = identity.get("phone", {})
    if phone:
        config.identity_phone = phone.get("provider", "agentphone")

    # Overrides
    overrides = raw.get("overrides", {})
    if overrides:
        config.overrides = {k: Ownership(v) for k, v in overrides.items()}

    return config


def generate_template(path: Path) -> None:
    """Generate a template sas.yaml file."""
    template = """# Sovereign Agent Stack Configuration
# See docs/ARCHITECTURE.md for the 7-layer sovereignty model.

model:
  primary:
    provider: ollama
    name: llama3.1:8b
    location: local
  fallback:
    provider: openai
    name: gpt-4o
    location: api
  auto_fallback: true

compute:
  substrate: local_docker    # local_docker, local_vm, orgo_cloud
  template: sas-desktop:latest
  resources:
    cpu: 4
    memory: 8Gi
  auto_destroy: 300

memory:
  short_term:
    provider: local_rag      # local_rag, honcho_self_hosted, honcho_cloud
    max_context_tokens: 8000
  long_term:
    provider: compile_time_graph   # compile_time_graph, retrieval_only
    source: ~/sas-knowledge
    graph_store: sqlite
    compile_cron: "0 */6 * * *"
    on_watch: true

auth:
  broker: local_mcp_gateway    # local_mcp_gateway, composio
  vault: ~/.sas/vault.db
  encryption: libsodium
  refresh_cron: "0 */1 * * *"

payments:
  adapter: virtual_card        # virtual_card, mpp_native
  virtual_card:
    provider: ramp
    limit: 100
  mpp:
    provider: stripe
    settlement: stablecoin

identity:
  email:
    provider: agentmail
    domain: agentmail.to
  phone:
    provider: agentphone
    region: US

# Manual sovereignty overrides (optional)
# overrides:
#   layer_5: owned    # e.g., self-hosting Honcho on your own Postgres
"""
    path.write_text(template)
