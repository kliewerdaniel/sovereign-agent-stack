"""Phase 27: Consequential Effect Graph Completeness.

The central research question:
    Is the declared effect inventory complete enough to support the claim
    of effect closure?

The critical invariant:
    100% CLOSURE OF AN INCOMPLETE EFFECT INVENTORY ≠ GLOBAL EFFECT CLOSURE

This module constructs adversarial worlds containing hidden consequential
effects that are NOT in the declared inventory, then tests whether the
authority architecture can detect the discrepancy between:

    DECLARED EFFECT INVENTORY
    OBSERVED EFFECT INVENTORY
    GROUND-TRUTH EXPERIMENTAL EFFECT SET

The most interesting attack:
    Inventory = 100% closed
    but
    HiddenEffect ∉ Inventory
    HiddenEffect → ExternalEffect
    HiddenEffect → no authority path

If the system claims closure=100% while the hidden effect exists,
we have discovered FALSE CLOSURE.

Conversely, if the system can reliably classify:
    INVENTORY COMPLETE WITHIN SCOPE
    versus
    INCOMPLETE
and consequently refuse to interpret 100% closure as global closure,
then we have connected epistemic completeness directly to runtime enforcement.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Core Enumerations
# ---------------------------------------------------------------------------


class EffectCategory(str, Enum):
    """Categories of consequential effects.

    These are effect types, not hiding mechanisms.
    Hiding mechanisms are captured in `hidden_mechanism` and `attack_category`.
    """
    SUBPROCESS = "subprocess"
    NETWORK = "network"
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    BROKER = "broker"
    PAYMENT = "payment"
    IDENTITY = "identity"
    CREDENTIAL = "credential"
    PLUGIN = "plugin"
    DYNAMIC_IMPORT = "dynamic_import"


class EffectVisibility(str, Enum):
    """How an effect relates to the declared inventory."""
    DECLARED = "declared"          # In the Phase 26 inventory
    OBSERVED = "observed"          # Found by runtime observation
    HIDDEN = "hidden"              # Exists but not in inventory
    UNOBSERVED = "unobserved"      # Exists, not yet discovered


class InventoryCompleteness(str, Enum):
    """Completeness classification of the effect inventory."""
    COMPLETE_WITHIN_SCOPE = "complete_within_scope"
    INCOMPLETE = "incomplete"
    FALSE_CLOSURE = "false_closure"  # Claims 100% but hidden effects exist
    INCONCLUSIVE = "inconclusive"


class AuthorityPathStatus(str, Enum):
    """Status of the authority path for an effect."""
    GOVERNED = "governed"
    UNGOVERNED = "ungoverned"
    ESCAPE = "escape"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Effect Representation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConsequentialEffect:
    """A single consequential effect in the system."""
    effect_id: str
    category: EffectCategory
    source: str
    target: str
    operation: str
    visibility: EffectVisibility
    authority_path_status: AuthorityPathStatus
    description: str
    hidden_mechanism: str  # How the effect evades the declared inventory
    scope: str = "runtime"
    temporal_boundary: str = ""
    provenance: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "effect_id": self.effect_id,
            "category": self.category.value,
            "source": self.source,
            "target": self.target,
            "operation": self.operation,
            "visibility": self.visibility.value,
            "authority_path_status": self.authority_path_status.value,
            "description": self.description,
            "hidden_mechanism": self.hidden_mechanism,
            "scope": self.scope,
            "temporal_boundary": self.temporal_boundary,
            "provenance": self.provenance,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class EffectInventory:
    """A set of effects claimed to be complete."""
    inventory_id: str
    effects: tuple[ConsequentialEffect, ...]
    claimed_closure_rate: float
    scope: str
    observation_method: str
    generated_by: str
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def size(self) -> int:
        return len(self.effects)

    @property
    def governed_count(self) -> int:
        return sum(1 for e in self.effects if e.authority_path_status == AuthorityPathStatus.GOVERNED)

    @property
    def ungoverned_count(self) -> int:
        return sum(1 for e in self.effects if e.authority_path_status in (
            AuthorityPathStatus.UNGOVERNED, AuthorityPathStatus.ESCAPE
        ))

    @property
    def actual_closure_rate(self) -> float:
        if not self.effects:
            return 0.0
        return self.governed_count / len(self.effects)

    def to_dict(self) -> dict:
        return {
            "inventory_id": self.inventory_id,
            "effects": [e.to_dict() for e in self.effects],
            "size": self.size,
            "governed_count": self.governed_count,
            "ungoverned_count": self.ungoverned_count,
            "claimed_closure_rate": self.claimed_closure_rate,
            "actual_closure_rate": self.actual_closure_rate,
            "scope": self.scope,
            "observation_method": self.observation_method,
            "generated_by": self.generated_by,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Adversarial World — Hidden Effect Injection
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AdversarialWorld:
    """A world containing hidden effects designed to test inventory completeness."""
    world_id: str
    description: str
    declared_effects: tuple[ConsequentialEffect, ...]
    hidden_effects: tuple[ConsequentialEffect, ...]
    ground_truth_effects: tuple[ConsequentialEffect, ...]  # Union of declared + hidden
    attack_category: str
    expected_completeness: InventoryCompleteness
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def hidden_count(self) -> int:
        return len(self.hidden_effects)

    @property
    def declared_count(self) -> int:
        return len(self.declared_effects)

    @property
    def ground_truth_count(self) -> int:
        return len(self.ground_truth_effects)

    def to_dict(self) -> dict:
        return {
            "world_id": self.world_id,
            "description": self.description,
            "declared_effects": [e.to_dict() for e in self.declared_effects],
            "hidden_effects": [e.to_dict() for e in self.hidden_effects],
            "ground_truth_effects": [e.to_dict() for e in self.ground_truth_effects],
            "hidden_count": self.hidden_count,
            "declared_count": self.declared_count,
            "ground_truth_count": self.ground_truth_count,
            "attack_category": self.attack_category,
            "expected_completeness": self.expected_completeness.value,
            "created_at": self.created_at,
        }


# ---------------------------------------------------------------------------
# Completeness Experiment Result
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompletenessResult:
    """Result of a single completeness experiment."""
    result_id: str
    world: AdversarialWorld
    declared_inventory: EffectInventory
    observed_inventory: EffectInventory
    ground_truth: EffectInventory
    detected_hidden: tuple[ConsequentialEffect, ...]
    missed_hidden: tuple[ConsequentialEffect, ...]
    false_positives: tuple[ConsequentialEffect, ...]
    completeness_classification: InventoryCompleteness
    closure_claim_valid: bool  # Whether the 100% closure claim holds
    notes: str = ""

    @property
    def detection_rate(self) -> float:
        if not self.world.hidden_effects:
            return 1.0
        return len(self.detected_hidden) / len(self.world.hidden_effects)

    @property
    def false_closure(self) -> bool:
        """True if the system claimed 100% closure but hidden effects exist."""
        return (
            self.declared_inventory.claimed_closure_rate >= 1.0
            and len(self.world.hidden_effects) > 0
            and len(self.detected_hidden) == 0
        )

    def to_dict(self) -> dict:
        return {
            "result_id": self.result_id,
            "world_id": self.world.world_id,
            "declared_inventory_size": self.declared_inventory.size,
            "observed_inventory_size": self.observed_inventory.size,
            "ground_truth_size": self.ground_truth.size,
            "detected_hidden": len(self.detected_hidden),
            "missed_hidden": len(self.missed_hidden),
            "false_positives": len(self.false_positives),
            "detection_rate": self.detection_rate,
            "completeness_classification": self.completeness_classification.value,
            "closure_claim_valid": self.closure_claim_valid,
            "false_closure": self.false_closure,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Adversarial World Generator
# ---------------------------------------------------------------------------


class AdversarialWorldGenerator:
    """Generates adversarial worlds with hidden effects."""

    def __init__(self):
        self.worlds: list[AdversarialWorld] = []

    def generate_all_worlds(self) -> list[AdversarialWorld]:
        """Generate all adversarial worlds for Phase 27."""
        self.worlds = [
            self._world_direct_subprocess_helper(),
            self._world_indirect_subprocess(),
            self._world_dynamic_import_subprocess(),
            self._world_filesystem_utility_wrap(),
            self._world_database_alternate_adapter(),
            self._world_credential_secondary_path(),
            self._world_identity_outside_adapter(),
            self._world_plugin_instantiated_effect(),
            self._world_argo_alternate_entry(),
            self._world_mcp_style_external(),
            self._world_exception_recovery_path(),
            self._world_emergency_path(),
            self._world_test_only_execution(),
            self._world_lazy_init_side_effect(),
            self._world_background_worker(),
            self._world_callback_triggered(),
        ]
        return self.worlds

    def _make_effect(
        self,
        category: EffectCategory,
        source: str,
        target: str,
        operation: str,
        visibility: EffectVisibility,
        authority_status: AuthorityPathStatus,
        description: str,
        hidden_mechanism: str,
    ) -> ConsequentialEffect:
        return ConsequentialEffect(
            effect_id=f"eff-{uuid.uuid4().hex[:12]}",
            category=category,
            source=source,
            target=target,
            operation=operation,
            visibility=visibility,
            authority_path_status=authority_status,
            description=description,
            hidden_mechanism=hidden_mechanism,
        )

    def _world_direct_subprocess_helper(self) -> AdversarialWorld:
        """World 1: Direct subprocess call through a helper function."""
        declared = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "ARGO subprocess through RuntimeAuthorityGate",
                "none — declared in inventory",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/cli/helper.py",
                "subprocess.Popen",
                "subprocess.spawn",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "Direct subprocess.Popen in CLI helper module",
                "helper module not in declared inventory; uses Popen instead of run",
            ),
        )
        return AdversarialWorld(
            world_id="world_001_subprocess_helper",
            description="Direct subprocess.Popen in a helper function not covered by the declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="direct_subprocess_bypass",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_indirect_subprocess(self) -> AdversarialWorld:
        """World 2: Indirect subprocess through a utility wrapper."""
        declared = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "ARGO subprocess through gate",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/utils/process.py",
                "os.system",
                "os.shell_execute",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "os.system call in utility module",
                "os.system bypasses subprocess module entirely; utility module not scanned",
            ),
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/utils/process.py",
                "os.execv",
                "os.process_replace",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "os.execv replaces current process",
                "exec family not detected by subprocess pattern matching",
            ),
        )
        return AdversarialWorld(
            world_id="world_002_indirect_subprocess",
            description="os.system and os.execv in utility module bypass subprocess detection",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="indirect_subprocess",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_dynamic_import_subprocess(self) -> AdversarialWorld:
        """World 3: Dynamic import → subprocess execution."""
        declared = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "ARGO subprocess through gate",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.DYNAMIC_IMPORT,
                "src/sas/plugins/loader.py",
                "importlib.import_module",
                "dynamic_import",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Dynamic import of plugin that executes subprocess",
                "importlib bypasses static analysis; plugin code not in declared inventory",
            ),
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/plugins/loader.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "Subprocess executed by dynamically imported plugin",
                "plugin code loaded at runtime; not visible to static inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_003_dynamic_import",
            description="Dynamic import loads plugin that executes subprocess outside declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="dynamic_import_subprocess",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_filesystem_utility_wrap(self) -> AdversarialWorld:
        """World 4: Filesystem primitive hidden behind utility function."""
        declared = (
            self._make_effect(
                EffectCategory.FILESYSTEM,
                "src/sas/registry.py",
                "open(write)",
                "filesystem.write",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "Registry file write through CapabilityBoundFilesystem",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.FILESYSTEM,
                "src/sas/utils/fileops.py",
                "pathlib.Path.write_text",
                "filesystem.write",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "pathlib write_text bypasses open() detection",
                "pathlib is a separate API from open(); utility module not in inventory",
            ),
            self._make_effect(
                EffectCategory.FILESYSTEM,
                "src/sas/utils/fileops.py",
                "shutil.copy2",
                "filesystem.copy",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "shutil copy creates files without open()",
                "shutil is a high-level API that doesn't use open() directly",
            ),
        )
        return AdversarialWorld(
            world_id="world_004_filesystem_utility",
            description="pathlib and shutil in utility module bypass open()-based filesystem detection",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="filesystem_utility_bypass",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_database_alternate_adapter(self) -> AdversarialWorld:
        """World 5: Database access through alternate adapter."""
        declared = (
            self._make_effect(
                EffectCategory.DATABASE,
                "src/sas_tie_knowledge/adapter.py",
                "sqlite3.execute",
                "database.write",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "Knowledge adapter through CapabilityBoundDatabase",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.DATABASE,
                "src/sas/cache/layer.py",
                "aiosqlite.execute",
                "database.write",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "aiosqlite in cache layer bypasses CapabilityBoundDatabase",
                "async database driver not wrapped; cache layer not in declared inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_005_database_alternate",
            description="aiosqlite in cache layer bypasses the declared CapabilityBoundDatabase",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="database_alternate_adapter",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_credential_secondary_path(self) -> AdversarialWorld:
        """World 6: Credential access through secondary path."""
        declared = (
            self._make_effect(
                EffectCategory.CREDENTIAL,
                "src/sas/quant/capability_bound_auth.py",
                "auth_broker.get_credential",
                "credential.read",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "Credential access through CapabilityBoundAuthBroker",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.CREDENTIAL,
                "src/sas/legacy/keys.py",
                "os.environ.get",
                "credential.read",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Direct environment variable access for API keys",
                "legacy module reads env vars directly; not through auth broker",
            ),
            self._make_effect(
                EffectCategory.CREDENTIAL,
                "src/sas/legacy/keys.py",
                "configparser.read",
                "credential.read",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Config file credential access bypasses auth broker",
                "legacy config parser reads credentials from ini files",
            ),
        )
        return AdversarialWorld(
            world_id="world_006_credential_secondary",
            description="Legacy credential access paths bypass CapabilityBoundAuthBroker",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="credential_secondary_path",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_identity_outside_adapter(self) -> AdversarialWorld:
        """World 7: Identity operation outside the normal adapter."""
        declared = (
            self._make_effect(
                EffectCategory.IDENTITY,
                "src/sas/identity/adapter.py",
                "identity.mutate",
                "identity.mutation",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "Identity mutation through CapabilityBound identity adapter",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.IDENTITY,
                "src/sas/identity/legacy.py",
                "user_table.update",
                "identity.mutation",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Direct database update to user table bypasses identity adapter",
                "legacy module mutates user records directly; not through adapter",
            ),
        )
        return AdversarialWorld(
            world_id="world_007_identity_legacy",
            description="Legacy identity mutation bypasses the declared identity adapter",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="identity_outside_adapter",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_plugin_instantiated_effect(self) -> AdversarialWorld:
        """World 8: Plugin-instantiated effect."""
        declared = (
            self._make_effect(
                EffectCategory.PLUGIN,
                "src/sas/quant/capability_bound_plugin.py",
                "plugin.execute",
                "plugin.execution",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "Plugin execution through CapabilityBoundPluginExecutor",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.PLUGIN,
                "src/sas/plugins/dynamic.py",
                "plugin.exec_module",
                "plugin.code_execution",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Plugin exec_module runs arbitrary code",
                "plugin code is data, not declared inventory; dynamic code execution",
            ),
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/plugins/dynamic.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "Plugin spawns subprocess",
                "plugin code spawns subprocess; not visible to static inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_008_plugin_instantiated",
            description="Plugin code execution spawns effects outside declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="plugin_instantiated_effect",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_argo_alternate_entry(self) -> AdversarialWorld:
        """World 9: ARGO execution through alternate entry point."""
        declared = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "ARGO subprocess through RuntimeAuthorityGate",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argo/cli.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "ARGO CLI alternate entry point bypasses gate",
                "alternate CLI entry point not routed through _run_sas_with_gate",
            ),
        )
        return AdversarialWorld(
            world_id="world_009_argo_alternate",
            description="ARGO alternate CLI entry point bypasses RuntimeAuthorityGate",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="argo_alternate_entry",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_mcp_style_external(self) -> AdversarialWorld:
        """World 10: MCP-style external effect."""
        declared = (
            self._make_effect(
                EffectCategory.NETWORK,
                "src/sas/mcp/server.py",
                "httpx.post",
                "network.mutation",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "MCP server network call through capability-bound transport",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.NETWORK,
                "src/sas/mcp/tools.py",
                "httpx.post",
                "network.mutation",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "MCP tool registration bypasses transport-level gate",
                "tool registration is metadata; actual tool invocation is the effect",
            ),
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/mcp/tools.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "MCP tool spawns subprocess",
                "tool execution path not in declared inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_010_mcp_external",
            description="MCP tool invocation creates effects outside declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="mcp_style_external",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_exception_recovery_path(self) -> AdversarialWorld:
        """World 11: Exception/recovery path."""
        declared = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "ARGO subprocess through gate",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/recovery/exception_handler.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "Exception handler spawns recovery subprocess",
                "recovery path is exception-driven; not in normal execution inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_011_exception_recovery",
            description="Exception handler spawns recovery subprocess outside declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="exception_recovery_path",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_emergency_path(self) -> AdversarialWorld:
        """World 12: Emergency path."""
        declared = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "ARGO subprocess through gate",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/emergency/kill_switch.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.ESCAPE,
                "Emergency kill switch spawns subprocess outside normal governance",
                "emergency path intentionally bypasses normal authority; not in inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_012_emergency_path",
            description="Emergency kill switch spawns subprocess outside declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="emergency_path",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_test_only_execution(self) -> AdversarialWorld:
        """World 13: Test-only execution path."""
        declared = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "ARGO subprocess through gate",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "tests/integration/helpers.py",
                "subprocess.run",
                "subprocess.execute",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Test helper spawns subprocess for integration testing",
                "test code is excluded from production inventory but can affect runtime",
            ),
        )
        return AdversarialWorld(
            world_id="world_013_test_harness",
            description="Test harness spawns subprocess outside production inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="test_harness_effect",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_lazy_init_side_effect(self) -> AdversarialWorld:
        """World 14: Lazy initialization side effect."""
        declared = (
            self._make_effect(
                EffectCategory.DATABASE,
                "src/sas_tie_knowledge/adapter.py",
                "sqlite3.execute",
                "database.write",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "Knowledge adapter through CapabilityBoundDatabase",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.DATABASE,
                "src/sas/cache/__init__.py",
                "sqlite3.execute",
                "database.write",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Lazy cache initialization writes to database on first access",
                "side effect of attribute access; not in declared inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_014_lazy_init",
            description="Lazy initialization creates database writes outside declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="lazy_init_side_effect",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_background_worker(self) -> AdversarialWorld:
        """World 15: Background worker effect."""
        declared = (
            self._make_effect(
                EffectCategory.NETWORK,
                "src/sas/mcp/server.py",
                "httpx.post",
                "network.mutation",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "MCP server network call",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.NETWORK,
                "src/sas/background/worker.py",
                "httpx.post",
                "network.mutation",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Background worker makes network calls outside declared inventory",
                "background thread not in main execution path; not in inventory",
            ),
            self._make_effect(
                EffectCategory.FILESYSTEM,
                "src/sas/background/worker.py",
                "open(write)",
                "filesystem.write",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Background worker writes files outside declared inventory",
                "background thread effects not in main inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_015_background_worker",
            description="Background worker creates effects outside declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="background_worker",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )

    def _world_callback_triggered(self) -> AdversarialWorld:
        """World 16: Callback-triggered effect."""
        declared = (
            self._make_effect(
                EffectCategory.BROKER,
                "src/sas/quant/capability_bound_broker.py",
                "broker.submit_order",
                "broker.trade",
                EffectVisibility.DECLARED,
                AuthorityPathStatus.GOVERNED,
                "Broker trade through CapabilityBoundBroker",
                "none",
            ),
        )
        hidden = (
            self._make_effect(
                EffectCategory.BROKER,
                "src/sas/quant/callbacks.py",
                "broker.submit_order",
                "broker.trade",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Callback-triggered trade outside declared inventory",
                "callback is registered data; invocation path not in inventory",
            ),
            self._make_effect(
                EffectCategory.PAYMENT,
                "src/sas/quant/callbacks.py",
                "payment.execute",
                "payment.transfer",
                EffectVisibility.HIDDEN,
                AuthorityPathStatus.UNGOVERNED,
                "Callback-triggered payment outside declared inventory",
                "callback invocation triggers payment; not in declared inventory",
            ),
        )
        return AdversarialWorld(
            world_id="world_016_callback_triggered",
            description="Callback-triggered broker trade outside declared inventory",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="callback_triggered",
            expected_completeness=InventoryCompleteness.INCOMPLETE,
        )


# ---------------------------------------------------------------------------
# Completeness Engine
# ---------------------------------------------------------------------------


class CompletenessEngine:
    """Evaluates whether the declared effect inventory is complete enough."""

    def evaluate(
        self,
        world: AdversarialWorld,
        declared_inventory: EffectInventory,
        observed_inventory: EffectInventory,
        ground_truth: EffectInventory,
    ) -> CompletenessResult:
        """Evaluate inventory completeness for a given world."""
        # Detect hidden effects: effects in ground truth not in declared
        declared_ids = {e.effect_id for e in declared_inventory.effects}
        observed_ids = {e.effect_id for e in observed_inventory.effects}
        ground_truth_ids = {e.effect_id for e in ground_truth.effects}

        # Hidden effects are those in ground truth but not declared
        hidden_in_gt = [e for e in ground_truth.effects if e.effect_id not in declared_ids]

        # Detected hidden = those the observed inventory found
        detected = [e for e in hidden_in_gt if e.effect_id in observed_ids]

        # Missed hidden = those neither declared nor observed
        missed = [e for e in hidden_in_gt if e.effect_id not in observed_ids]

        # False positives = observed but not in ground truth
        false_pos = [e for e in observed_inventory.effects if e.effect_id not in ground_truth_ids]

        # Determine completeness classification
        if not hidden_in_gt:
            completeness = InventoryCompleteness.COMPLETE_WITHIN_SCOPE
        elif len(detected) == len(hidden_in_gt):
            completeness = InventoryCompleteness.COMPLETE_WITHIN_SCOPE
        elif len(detected) > 0:
            completeness = InventoryCompleteness.INCOMPLETE
        else:
            completeness = InventoryCompleteness.FALSE_CLOSURE

        # Closure claim is valid only if no hidden effects exist OR all detected
        closure_valid = len(missed) == 0

        return CompletenessResult(
            result_id=f"res-{uuid.uuid4().hex[:12]}",
            world=world,
            declared_inventory=declared_inventory,
            observed_inventory=observed_inventory,
            ground_truth=ground_truth,
            detected_hidden=tuple(detected),
            missed_hidden=tuple(missed),
            false_positives=tuple(false_pos),
            completeness_classification=completeness,
            closure_claim_valid=closure_valid,
            notes=self._generate_notes(world, detected, missed, false_pos),
        )

    def _generate_notes(
        self,
        world: AdversarialWorld,
        detected: list[ConsequentialEffect],
        missed: list[ConsequentialEffect],
        false_pos: list[ConsequentialEffect],
    ) -> str:
        """Generate human-readable notes for the result."""
        if not detected and not missed:
            return "No hidden effects in this world."
        parts = []
        if detected:
            parts.append(f"Detected {len(detected)}/{len(detected) + len(missed)} hidden effects")
        if missed:
            parts.append(f"Missed {len(missed)} hidden effects: {[e.effect_id for e in missed]}")
        if false_pos:
            parts.append(f"{len(false_pos)} false positives")
        return "; ".join(parts)


# ---------------------------------------------------------------------------
# Phase 27 Experiment Runner
# ---------------------------------------------------------------------------


class Phase27Experiment:
    """Runs the full Phase 27 experiment suite."""

    def __init__(self):
        self.world_generator = AdversarialWorldGenerator()
        self.completeness_engine = CompletenessEngine()
        self.results: list[CompletenessResult] = []

    def run_all(self) -> list[CompletenessResult]:
        """Run all Phase 27 experiments."""
        worlds = self.world_generator.generate_all_worlds()
        self.results = []

        for world in worlds:
            # The declared inventory is what Phase 26 produced
            declared_inventory = EffectInventory(
                inventory_id=f"declared-{world.world_id}",
                effects=world.declared_effects,
                claimed_closure_rate=1.0,  # Phase 26 claimed 100%
                scope="phase26_declared",
                observation_method="static_analysis",
                generated_by="phase26_remediation",
            )

            # The observed inventory is what runtime observation finds
            # (simulated: in a real system this would be the runtime trace)
            observed_inventory = EffectInventory(
                inventory_id=f"observed-{world.world_id}",
                effects=world.declared_effects + world.hidden_effects,
                claimed_closure_rate=1.0,
                scope="runtime_observation",
                observation_method="runtime_trace",
                generated_by="phase27_oracle",
            )

            # The ground truth is the union of declared + hidden
            ground_truth = EffectInventory(
                inventory_id=f"gt-{world.world_id}",
                effects=world.ground_truth_effects,
                claimed_closure_rate=1.0,
                scope="ground_truth",
                observation_method="experimental_oracle",
                generated_by="phase27_adversarial_generator",
            )

            result = self.completeness_engine.evaluate(
                world=world,
                declared_inventory=declared_inventory,
                observed_inventory=observed_inventory,
                ground_truth=ground_truth,
            )
            self.results.append(result)

        return self.results

    def summary(self) -> dict:
        """Generate a summary of all results."""
        if not self.results:
            return {"error": "No results available"}

        total_worlds = len(self.results)
        false_closures = sum(1 for r in self.results if r.false_closure)
        complete_within_scope = sum(
            1 for r in self.results
            if r.completeness_classification == InventoryCompleteness.COMPLETE_WITHIN_SCOPE
        )
        incomplete = sum(
            1 for r in self.results
            if r.completeness_classification == InventoryCompleteness.INCOMPLETE
        )
        avg_detection_rate = sum(r.detection_rate for r in self.results) / total_worlds

        return {
            "total_worlds": total_worlds,
            "false_closures": false_closures,
            "complete_within_scope": complete_within_scope,
            "incomplete": incomplete,
            "average_detection_rate": avg_detection_rate,
            "closure_claims_valid": sum(1 for r in self.results if r.closure_claim_valid),
            "closure_claims_invalid": sum(1 for r in self.results if not r.closure_claim_valid),
        }
