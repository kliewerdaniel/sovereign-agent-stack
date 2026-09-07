"""Community layer registry for sharing SAS plugin implementations.

The registry is a JSON file stored at ~/.sas/registry.json.
Plugins can be published (by URL/path) and searched.

Registry schema:
{
  "version": 1,
  "plugins": [
    {
      "name": "my-payments-adapter",
      "layer_id": "layer_8_payments",
      "version": "1.0.0",
      "description": "Custom payment adapter",
      "source": "local",
      "author": "user@example.com",
      "url": "https://github.com/user/my-adapter",
      "created_at": "2026-01-01T00:00:00Z"
    }
  ]
}
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

REGISTRY_VERSION = 1
DEFAULT_REGISTRY_PATH = Path.home() / ".sas" / "registry.json"


@dataclass
class RegistryEntry:
    """A single plugin entry in the community registry."""

    name: str
    layer_id: str
    version: str
    description: str = ""
    source: str = "local"
    author: str = ""
    url: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> RegistryEntry:
        fields = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**fields)


class CommunityRegistry:
    """Manage the community layer registry.

    Usage:
        reg = CommunityRegistry()
        reg.publish(RegistryEntry(name="my-adapter", ...))
        results = reg.search("payments")
        plugins = reg.list_all()
    """

    def __init__(self, registry_path: Path | None = None):
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self._data: dict = {"version": REGISTRY_VERSION, "plugins": []}
        self._load()

    def _load(self) -> None:
        """Load registry from disk, creating if missing."""
        if self.registry_path.exists():
            try:
                with open(self.registry_path) as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                self._data = {"version": REGISTRY_VERSION, "plugins": []}
        else:
            self._data = {"version": REGISTRY_VERSION, "plugins": []}
            self._save()

    def _save(self) -> None:
        """Persist registry to disk."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, "w") as f:
            json.dump(self._data, f, indent=2)

    def publish(self, entry: RegistryEntry) -> None:
        """Publish a plugin entry to the registry.

        If a plugin with the same name already exists, it is replaced
        if the new version is >= existing version.
        """
        if not entry.created_at:
            entry.created_at = datetime.utcnow().isoformat() + "Z"

        existing_idx = None
        for idx, p in enumerate(self._data["plugins"]):
            if p["name"] == entry.name:
                existing_idx = idx
                break

        if existing_idx is not None:
            existing_version = self._data["plugins"][existing_idx].get("version", "0.0.0")
            if self._version_gte(entry.version, existing_version):
                self._data["plugins"][existing_idx] = entry.to_dict()
            # else: skip (existing is newer or same)
        else:
            self._data["plugins"].append(entry.to_dict())

        self._save()

    def unpublish(self, name: str) -> bool:
        """Remove a plugin from the registry. Returns True if removed."""
        original_len = len(self._data["plugins"])
        self._data["plugins"] = [p for p in self._data["plugins"] if p["name"] != name]
        if len(self._data["plugins"]) < original_len:
            self._save()
            return True
        return False

    def get(self, name: str) -> RegistryEntry | None:
        """Get a plugin entry by name."""
        for p in self._data["plugins"]:
            if p["name"] == name:
                return RegistryEntry.from_dict(p)
        return None

    def list_all(self) -> list[RegistryEntry]:
        """List all plugins in the registry."""
        return [RegistryEntry.from_dict(p) for p in self._data["plugins"]]

    def search(self, query: str) -> list[RegistryEntry]:
        """Search plugins by name, description, or layer_id."""
        query_lower = query.lower()
        results = []
        for p in self._data["plugins"]:
            if (query_lower in p.get("name", "").lower()
                    or query_lower in p.get("description", "").lower()
                    or query_lower in p.get("layer_id", "").lower()):
                results.append(RegistryEntry.from_dict(p))
        return results

    def list_by_layer(self, layer_id: str) -> list[RegistryEntry]:
        """List all plugins for a given layer."""
        return [RegistryEntry.from_dict(p)
                for p in self._data["plugins"]
                if p.get("layer_id") == layer_id]

    def _version_gte(self, v1: str, v2: str) -> bool:
        """Compare two semver strings (simple, no pre-release handling)."""
        try:
            parts1 = [int(x) for x in v1.split(".")]
            parts2 = [int(x) for x in v2.split(".")]
            # Pad to 3 parts
            parts1 += [0] * (3 - len(parts1))
            parts2 += [0] * (3 - len(parts2))
            return tuple(parts1) >= tuple(parts2)
        except (ValueError, AttributeError):
            return True  # If we can't parse, allow overwrite


def publish_plugin(entry: RegistryEntry, registry_path: Path | None = None) -> None:
    """Convenience: publish to the default registry."""
    CommunityRegistry(registry_path).publish(entry)


def search_plugins(query: str, registry_path: Path | None = None) -> list[RegistryEntry]:
    """Convenience: search the default registry."""
    return CommunityRegistry(registry_path).search(query)


def list_all_plugins(registry_path: Path | None = None) -> list[RegistryEntry]:
    """Convenience: list all plugins in the default registry."""
    return CommunityRegistry(registry_path).list_all()
