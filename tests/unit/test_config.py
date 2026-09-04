"""Tests for sas.yaml parser."""

import tempfile
from pathlib import Path

import pytest
import yaml

from sas.core.config import (
    AuthBroker,
    LongTermProvider,
    MemoryProvider,
    SASConfig,
    SubstrateType,
    generate_template,
    parse_sas_yaml,
)


class TestParseSasYaml:
    """Tests for the sas.yaml parser."""

    def test_nonexistent_returns_defaults(self, tmp_path: Path) -> None:
        """Parsing a nonexistent file returns default config."""
        config = parse_sas_yaml(tmp_path / "nonexistent.yaml")
        assert isinstance(config, SASConfig)
        assert config.model_primary is None
        assert config.model_fallback is None
        assert config.substrate == SubstrateType.LOCAL_DOCKER
        assert config.memory_short_term == MemoryProvider.LOCAL_RAG
        assert config.memory_long_term == LongTermProvider.COMPILE_TIME_GRAPH
        assert config.auth_broker == AuthBroker.LOCAL_MCP_GATEWAY

    def test_minimal_config(self, tmp_path: Path) -> None:
        """Parse a minimal config file."""
        config_data = {
            "model": {
                "primary": {
                    "provider": "ollama",
                    "name": "llama3.1:8b",
                    "location": "local",
                }
            }
        }
        config_path = tmp_path / "sas.yaml"
        config_path.write_text(yaml.safe_dump(config_data))

        config = parse_sas_yaml(config_path)
        assert config.model_primary is not None
        assert config.model_primary.provider == "ollama"
        assert config.model_primary.name == "llama3.1:8b"
        assert config.model_primary.location == "local"

    def test_full_config(self, tmp_path: Path) -> None:
        """Parse a full config file with all options."""
        config_data = {
            "model": {
                "primary": {
                    "provider": "ollama",
                    "name": "llama3.1:8b",
                    "location": "local",
                },
                "fallback": {
                    "provider": "openai",
                    "name": "gpt-4o",
                    "location": "api",
                },
            },
            "compute": {
                "substrate": "local_vm",
            },
            "memory": {
                "short_term": {
                    "provider": "honcho_self_hosted",
                },
                "long_term": {
                    "provider": "compile_time_graph",
                },
            },
            "auth": {
                "broker": "local_mcp_gateway",
            },
            "payments": {
                "adapter": "virtual_card",
            },
        }
        config_path = tmp_path / "sas.yaml"
        config_path.write_text(yaml.safe_dump(config_data))

        config = parse_sas_yaml(config_path)
        assert config.model_primary is not None
        assert config.model_fallback is not None
        assert config.substrate == SubstrateType.LOCAL_VM
        assert config.memory_short_term == MemoryProvider.HONCHO_SELF_HOSTED
        assert config.memory_long_term == LongTermProvider.COMPILE_TIME_GRAPH
        assert config.auth_broker == AuthBroker.LOCAL_MCP_GATEWAY

    def test_cloud_config(self, tmp_path: Path) -> None:
        """Parse a config with cloud options (rented)."""
        config_data = {
            "compute": {
                "substrate": "orgo_cloud",
            },
            "memory": {
                "short_term": {
                    "provider": "honcho_cloud",
                },
                "long_term": {
                    "provider": "retrieval_only",
                },
            },
            "auth": {
                "broker": "composio",
            },
        }
        config_path = tmp_path / "sas.yaml"
        config_path.write_text(yaml.safe_dump(config_data))

        config = parse_sas_yaml(config_path)
        assert config.substrate == SubstrateType.ORGO_CLOUD
        assert config.memory_short_term == MemoryProvider.HONCHO_CLOUD
        assert config.memory_long_term == LongTermProvider.RETRIEVAL_ONLY
        assert config.auth_broker == AuthBroker.COMPOSIO

    def test_overrides(self, tmp_path: Path) -> None:
        """Parse a config with manual sovereignty overrides."""
        config_data = {
            "overrides": {
                "layer_5": "owned",
                "layer_6": "rented",
            }
        }
        config_path = tmp_path / "sas.yaml"
        config_path.write_text(yaml.safe_dump(config_data))

        config = parse_sas_yaml(config_path)
        assert config.overrides is not None
        assert config.overrides["layer_5"].value == "owned"
        assert config.overrides["layer_6"].value == "rented"


class TestGenerateTemplate:
    """Tests for template generation."""

    def test_generates_valid_yaml(self, tmp_path: Path) -> None:
        """Generated template is valid YAML that can be parsed."""
        config_path = tmp_path / "sas.yaml"
        generate_template(config_path)

        assert config_path.exists()
        config = parse_sas_yaml(config_path)
        assert config.model_primary is not None
        assert config.model_primary.provider == "ollama"

    def test_template_overwrite_fails(self, tmp_path: Path) -> None:
        """Generating template over existing file should be handled by caller."""
        config_path = tmp_path / "sas.yaml"
        config_path.write_text("existing")

        # The function itself will overwrite; it's the caller's responsibility to check
        # This documents that behavior
        generate_template(config_path)
        content = config_path.read_text()
        assert "existing" not in content
