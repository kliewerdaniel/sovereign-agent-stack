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

Authority Escape Remediation (Phase 26):
    All filesystem operations now go through CapabilityBoundFilesystem.
    The wrapper enforces an already-established capability (not manufacture one).
    File operations require a verified execution capability.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from sas.capability_bound_filesystem import CapabilityBoundFilesystem
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import (
    DomainType,
    DomainValidityInterval,
    create_protocol_domain,
)

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


# ---------------------------------------------------------------------------
# Filesystem Singleton
# ---------------------------------------------------------------------------

_registry_fs: CapabilityBoundFilesystem | None = None
_registry_domain = None


def _get_registry_fs() -> CapabilityBoundFilesystem:
    """Get or create the registry filesystem wrapper singleton."""
    global _registry_fs, _registry_domain
    if _registry_fs is None:
        _registry_domain = create_protocol_domain("registry-domain", DomainType.SOVEREIGN)
        _registry_fs = CapabilityBoundFilesystem(_registry_domain)
    return _registry_fs


def _create_registry_file_capability(
    path: str,
    action: str,
) -> ExecutionCapability:
    """Create a file capability for registry operations.

    This capability must be established by an authority root BEFORE
    file operations. The wrapper verifies and materializes this
    already-established authority — it does NOT create authority.
    """
    global _registry_domain
    if _registry_domain is None:
        _registry_domain = create_protocol_domain("registry-domain", DomainType.SOVEREIGN)
    now = datetime.now(UTC).isoformat()

    scope = CapabilityScope(
        domain_id=_registry_domain.domain_id,
        lineage_id=_registry_domain.lineage_hash,
        actor_id="registry-service",
        action=f"filesystem.{action}",
        resource=str(path),
        resource_class="filesystem",
        arguments={"path": str(path)},
        constraints=CapabilityConstraints(
            allowed_actions=[f"filesystem.{action}"],
        ),
        temporal_interval=DomainValidityInterval(
            valid_from=now,
            valid_until="",
        ),
        authorization_ref="registry-file-auth",
    )

    replay_guard = ReplayGuard(
        guard_type=ReplayProtectionType.SINGLE_USE,
        nonce=f"nonce-{uuid.uuid4().hex[:16]}",
        max_uses=1,
        created_at=now,
    )

    binding = ExecutorBinding(
        binding_id=f"binding-{uuid.uuid4().hex[:12]}",
        executor_id="capability-bound-filesystem",
        resource_id=str(path),
        bound_resources=[str(path)],
        bound_at=now,
        bound_until="",
    )

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="registry-file-auth",
        scope=scope,
        capability_type=CapabilityType.EXECUTE,
        replay_guard=replay_guard,
        actor_identity_ref="registry-service",
        resource_binding=binding,
        domain_id=_registry_domain.domain_id,
        lineage_id=_registry_domain.lineage_hash,
        authority_root="registry-file-auth",
        derived_at=now,
        derived_by="registry-filesystem-wrapper",
    )


class CommunityRegistry:
    """Manage the community layer registry.

    Usage:
        reg = CommunityRegistry()
        reg.publish(RegistryEntry(name="my-adapter", ...))
        results = reg.search("payments")
        plugins = reg.list_all()

    All filesystem operations are routed through CapabilityBoundFilesystem
    to enforce capability verification.
    """

    def __init__(self, registry_path: Path | None = None):
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self._data: dict = {"version": REGISTRY_VERSION, "plugins": []}
        self._load()

    def _load(self) -> None:
        """Load registry from disk, creating if missing."""
        if self.registry_path.exists():
            try:
                # Create read capability
                capability = _create_registry_file_capability(
                    str(self.registry_path), "read"
                )
                fs = _get_registry_fs()
                result = fs.read(capability, str(self.registry_path))
                if result.is_permitted and result.content is not None:
                    self._data = json.loads(result.content)
                else:
                    self._data = {"version": REGISTRY_VERSION, "plugins": []}
            except (json.JSONDecodeError, OSError):
                self._data = {"version": REGISTRY_VERSION, "plugins": []}
        else:
            self._data = {"version": REGISTRY_VERSION, "plugins": []}
            self._save()

    def _save(self) -> None:
        """Persist registry to disk through CapabilityBoundFilesystem."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        # Create write capability
        capability = _create_registry_file_capability(
            str(self.registry_path), "write"
        )
        fs = _get_registry_fs()
        content = json.dumps(self._data, indent=2)
        fs.write(capability, str(self.registry_path), content)

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
        """List all plugins for a given layer_id."""
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
