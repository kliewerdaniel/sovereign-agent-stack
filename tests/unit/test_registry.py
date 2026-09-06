"""Tests for the community registry."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sas.registry import (
    CommunityRegistry,
    RegistryEntry,
    publish_plugin,
    search_plugins,
    list_all_plugins,
)


class TestRegistryEntry:
    """Tests for the RegistryEntry dataclass."""

    def test_to_dict(self):
        entry = RegistryEntry(
            name="my-adapter",
            layer_id="layer_8_payments",
            version="1.0.0",
            description="My adapter",
        )
        d = entry.to_dict()
        assert d["name"] == "my-adapter"
        assert d["layer_id"] == "layer_8_payments"
        assert d["version"] == "1.0.0"

    def test_from_dict(self):
        data = {
            "name": "test",
            "layer_id": "layer_1",
            "version": "0.1.0",
            "description": "Test",
            "source": "local",
            "author": "me",
            "url": "https://example.com",
            "created_at": "2026-01-01T00:00:00Z",
        }
        entry = RegistryEntry.from_dict(data)
        assert entry.name == "test"
        assert entry.author == "me"


class TestCommunityRegistry:
    """Tests for the CommunityRegistry class."""

    def test_creates_registry_file(self, tmp_path):
        reg_path = tmp_path / "test_registry.json"
        reg = CommunityRegistry(registry_path=reg_path)
        assert reg_path.exists()
        data = json.loads(reg_path.read_text())
        assert data["version"] == 1
        assert data["plugins"] == []

    def test_publish(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        entry = RegistryEntry(
            name="adapter-a",
            layer_id="layer_8_payments",
            version="1.0.0",
            description="Payment adapter",
        )
        reg.publish(entry)
        assert reg.get("adapter-a") is not None
        assert len(reg.list_all()) == 1

    def test_unpublish(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        entry = RegistryEntry(
            name="adapter-a",
            layer_id="layer_8_payments",
            version="1.0.0",
        )
        reg.publish(entry)
        assert reg.unpublish("adapter-a") is True
        assert reg.get("adapter-a") is None

    def test_unpublish_missing(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        assert reg.unpublish("nonexistent") is False

    def test_search_by_name(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        reg.publish(RegistryEntry(
            name="payments-adapter", layer_id="layer_8", version="1.0.0",
            description="Payment stuff",
        ))
        reg.publish(RegistryEntry(
            name="auth-adapter", layer_id="layer_7", version="1.0.0",
            description="Auth stuff",
        ))
        results = reg.search("payment")
        assert len(results) == 1
        assert results[0].name == "payments-adapter"

    def test_search_by_description(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        reg.publish(RegistryEntry(
            name="custom", layer_id="layer_8", version="1.0.0",
            description="A unique keyword here",
        ))
        results = reg.search("unique keyword")
        assert len(results) == 1

    def test_list_by_layer(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        reg.publish(RegistryEntry(
            name="p1", layer_id="layer_8_payments", version="1.0.0",
        ))
        reg.publish(RegistryEntry(
            name="p2", layer_id="layer_8_payments", version="1.0.0",
        ))
        reg.publish(RegistryEntry(
            name="p3", layer_id="layer_7_auth", version="1.0.0",
        ))
        results = reg.list_by_layer("layer_8_payments")
        assert len(results) == 2

    def test_version_overwrite(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        reg.publish(RegistryEntry(
            name="adapter", layer_id="layer_8", version="1.0.0",
        ))
        reg.publish(RegistryEntry(
            name="adapter", layer_id="layer_8", version="2.0.0",
        ))
        assert len(reg.list_all()) == 1
        found = reg.get("adapter")
        assert found is not None
        assert found.version == "2.0.0"

    def test_version_no_downgrade(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        reg.publish(RegistryEntry(
            name="adapter", layer_id="layer_8", version="2.0.0",
        ))
        reg.publish(RegistryEntry(
            name="adapter", layer_id="layer_8", version="1.0.0",
        ))
        found = reg.get("adapter")
        assert found is not None
        assert found.version == "2.0.0"

    def test_created_at_auto_set(self, tmp_path):
        reg = CommunityRegistry(registry_path=tmp_path / "test.json")
        entry = RegistryEntry(
            name="adapter", layer_id="layer_8", version="1.0.0",
        )
        reg.publish(entry)
        found = reg.get("adapter")
        assert found is not None
        assert found.created_at != ""


class TestConvenienceFunctions:
    """Test module-level convenience functions."""

    def test_publish_and_search(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sas.registry.DEFAULT_REGISTRY_PATH", tmp_path / "test.json")
        publish_plugin(RegistryEntry(
            name="test-adapter", layer_id="layer_8", version="1.0.0",
            description="Test adapter",
        ))
        results = search_plugins("test")
        assert len(results) == 1

    def test_list_all_convenience(self, tmp_path, monkeypatch):
        monkeypatch.setattr("sas.registry.DEFAULT_REGISTRY_PATH", tmp_path / "test.json")
        publish_plugin(RegistryEntry(
            name="a1", layer_id="layer_8", version="1.0.0",
        ))
        results = list_all_plugins()
        assert len(results) == 1


class TestCorruptionRecovery:
    """Test handling of corrupted registry files."""

    def test_corrupted_json_recovers(self, tmp_path):
        reg_path = tmp_path / "test.json"
        reg_path.write_text("not valid json{{{")
        reg = CommunityRegistry(registry_path=reg_path)
        # Should recover with empty list, not crash
        assert reg.list_all() == []

    def test_publish_after_recovery(self, tmp_path):
        reg_path = tmp_path / "test.json"
        reg_path.write_text("corrupted{{{")
        reg = CommunityRegistry(registry_path=reg_path)
        reg.publish(RegistryEntry(
            name="adapter", layer_id="layer_8", version="1.0.0",
        ))
        assert reg.get("adapter") is not None
