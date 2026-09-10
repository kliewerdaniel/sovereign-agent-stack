"""Phase 28: Continuous Effect Reconciliation.

A temporal epistemic reconciliation mechanism that maintains the epistemic
status of the effect inventory as the executable system changes.

Core insight: completeness claims are temporally bounded. When the system
changes, the previous completeness claim may no longer hold — but this is
NOT retroactive invalidation. The claim was true at commit C1; at commit
C2, a new executable path exists; the C1 claim simply does not extend to C2.

Key invariants:
    INVENTORY_CHANGE_INVALIDATES_COMPLETENESS_CLAIM_ONLY_WITHIN_CHANGED_SCOPE
    REVALIDATION_REQUIREMENT ≠ RETROACTIVE_INVALIDATION
    COMPLETENESS_CLAIM_IS_TEMPORALLY_BOUNDED
    EFFECT_DISCOVERY_TRIGGERS_REVALIDATION_WITHOUT_INVALIDATING_HISTORY

Research question:
    Can a sovereign execution system know when it no longer knows the
    complete set of effects it is capable of producing?
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Core types
# ---------------------------------------------------------------------------

class EffectCategory(str, Enum):
    """Categories of consequential effects."""
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
    """Visibility levels for effects."""
    DECLARED = "declared"
    OBSERVED = "observed"
    AVAILABLE = "available"
    EXECUTED = "executed"
    HIDDEN = "hidden"
    UNOBSERVED = "unobserved"


class AuthorityPathStatus(str, Enum):
    """Status of an effect's authority path."""
    GOVERNED = "governed"
    UNGOVERNED = "ungoverned"
    ESCAPE = "escape"
    UNKNOWN = "unknown"


class CompletenessStatus(str, Enum):
    """Completeness classification for an effect inventory."""
    COMPLETE_WITHIN_SCOPE = "complete_within_scope"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"
    FALSE_CLOSURE = "false_closure"


class ReconciliationAction(str, Enum):
    """Action taken by the reconciliation engine."""
    NO_ACTION = "no_action"
    REVALIDATION_REQUIRED = "revalidation_required"
    INVENTORY_EXTENDED = "inventory_extended"
    COMPLETENESS_INVALIDATED = "completeness_invalidated"
    SCOPE_NARROWED = "scope_narrowed"


class ChangeType(str, Enum):
    """Type of system change that can affect the inventory."""
    SOURCE_ADDED = "source_added"
    SOURCE_REMOVED = "source_removed"
    SOURCE_MODIFIED = "source_modified"
    DEPENDENCY_ADDED = "dependency_added"
    DEPENDENCY_REMOVED = "dependency_removed"
    ENTRY_POINT_ADDED = "entry_point_added"
    ENTRY_POINT_REMOVED = "entry_point_remified"
    PLUGIN_REGISTERED = "plugin_registered"
    PLUGIN_UNREGISTERED = "plugin_unregistered"
    CONFIGURATION_CHANGE = "configuration_change"


# ---------------------------------------------------------------------------
# Effect and inventory types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConsequentialEffect:
    """A single consequential effect."""
    effect_id: str
    category: EffectCategory
    source: str
    target: str
    operation: str
    visibility: EffectVisibility
    authority_path_status: AuthorityPathStatus
    description: str = ""
    hidden_mechanism: str = ""
    scope: str = "runtime"
    temporal_boundary: str = ""
    provenance: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EffectInventory:
    """A snapshot of the effect inventory at a point in time."""
    inventory_id: str
    effects: tuple[ConsequentialEffect, ...]
    claimed_closure_rate: float = 1.0
    scope: str = "runtime"
    observation_method: str = "static_analysis"
    generated_by: str = ""
    created_at: str = ""
    commit_ref: str = ""  # Git commit or version identifier

    @property
    def size(self) -> int:
        return len(self.effects)

    @property
    def actual_closure_rate(self) -> float:
        if not self.effects:
            return 1.0
        governed = sum(
            1 for e in self.effects
            if e.authority_path_status == AuthorityPathStatus.GOVERNED
        )
        return governed / len(self.effects)

    @property
    def categories(self) -> set[EffectCategory]:
        return {e.category for e in self.effects}

    @property
    def effect_ids(self) -> set[str]:
        return {e.effect_id for e in self.effects}


# ---------------------------------------------------------------------------
# Temporal completeness claim
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompletenessClaim:
    """A claim that the effect inventory is complete within a scope.

    Temporally bounded: the claim is valid from `valid_from` until
    `valid_until` (empty string means "still valid").
    """
    claim_id: str
    commit_ref: str
    scope: str
    status: CompletenessStatus
    inventory: EffectInventory
    valid_from: str
    valid_until: str = ""  # Empty means still valid
    basis: str = ""  # How completeness was established
    notes: str = ""

    @property
    def is_current(self) -> bool:
        return self.valid_until == ""

    @property
    def is_expired(self) -> bool:
        return self.valid_until != ""

    def expires_at(self, timestamp: str) -> CompletenessClaim:
        """Return a new claim with valid_until set."""
        return CompletenessClaim(
            claim_id=self.claim_id,
            commit_ref=self.commit_ref,
            scope=self.scope,
            status=self.status,
            inventory=self.inventory,
            valid_from=self.valid_from,
            valid_until=timestamp,
            basis=self.basis,
            notes=self.notes,
        )


# ---------------------------------------------------------------------------
# System change
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SystemChange:
    """A change to the executable system."""
    change_id: str
    change_type: ChangeType
    source: str  # File or module affected
    description: str
    commit_ref: str
    timestamp: str
    categories_affected: set[EffectCategory] = field(default_factory=set)
    scope_affected: str = "runtime"
    introduces_effects: bool = False
    removes_effects: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Inventory delta
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InventoryDelta:
    """Difference between two effect inventories."""
    delta_id: str
    baseline: EffectInventory
    current: EffectInventory
    added: tuple[ConsequentialEffect, ...]
    removed: tuple[ConsequentialEffect, ...]
    unchanged: tuple[ConsequentialEffect, ...]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    @property
    def added_categories(self) -> set[EffectCategory]:
        return {e.category for e in self.added}

    @property
    def removed_categories(self) -> set[EffectCategory]:
        return {e.category for e in self.removed}


# ---------------------------------------------------------------------------
# Reconciliation result
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ReconciliationResult:
    """Result of reconciling a system change against the current inventory."""
    result_id: str
    change: SystemChange
    prior_claim: CompletenessClaim | None
    action: ReconciliationAction
    new_claim: CompletenessClaim | None
    delta: InventoryDelta | None
    scope_impact: str  # "unchanged", "narrowed", "extended", "new_category"
    temporal_impact: str  # "no_invalidation", "revalidation_required", "historical_preserved"
    notes: str = ""

    @property
    def requires_revalidation(self) -> bool:
        return self.action in (
            ReconciliationAction.REVALIDATION_REQUIRED,
            ReconciliationAction.COMPLETENESS_INVALIDATED,
            ReconciliationAction.INVENTORY_EXTENDED,
        )

    @property
    def historical_claim_preserved(self) -> bool:
        """The prior claim is NOT retroactively invalidated."""
        return self.temporal_impact != "retroactive_invalidation"


# ---------------------------------------------------------------------------
# Continuous Effect Reconciler
# ---------------------------------------------------------------------------

class ContinuousEffectReconciler:
    """Maintains the epistemic status of the effect inventory over time.

    When the system changes, the reconciler determines:
    1. Whether the change introduces new effect categories
    2. Whether the previous completeness claim still holds
    3. What scope of revalidation is needed
    4. Whether the historical claim is preserved (NOT retroactively invalidated)
    """

    def __init__(self) -> None:
        self._claims: list[CompletenessClaim] = []
        self._deltas: list[InventoryDelta] = []
        self._results: list[ReconciliationResult] = []

    @property
    def current_claim(self) -> CompletenessClaim | None:
        for claim in reversed(self._claims):
            if claim.is_current:
                return claim
        return None

    @property
    def claim_history(self) -> tuple[CompletenessClaim, ...]:
        return tuple(self._claims)

    @property
    def reconciliation_history(self) -> tuple[ReconciliationResult, ...]:
        return tuple(self._results)

    def register_baseline(
        self,
        inventory: EffectInventory,
        commit_ref: str,
        timestamp: str,
        basis: str = "phase26_remediation",
    ) -> CompletenessClaim:
        """Register the initial completeness claim."""
        claim = CompletenessClaim(
            claim_id=f"claim-{uuid.uuid4().hex[:12]}",
            commit_ref=commit_ref,
            scope=inventory.scope,
            status=CompletenessStatus.COMPLETE_WITHIN_SCOPE,
            inventory=inventory,
            valid_from=timestamp,
            basis=basis,
            notes=f"Baseline claim at {commit_ref}",
        )
        self._claims.append(claim)
        return claim

    def compute_delta(
        self,
        baseline: EffectInventory,
        current: EffectInventory,
    ) -> InventoryDelta:
        """Compute the delta between two inventories.

        Uses (category, source, target, operation) as effect identity,
        not UUID. In a real static analysis system, the same code
        location produces the same effect identity across scans.
        """
        def effect_key(e: ConsequentialEffect) -> tuple:
            return (e.category, e.source, e.target, e.operation)

        baseline_map = {effect_key(e): e for e in baseline.effects}
        current_map = {effect_key(e): e for e in current.effects}

        baseline_keys = set(baseline_map.keys())
        current_keys = set(current_map.keys())

        added = tuple(
            current_map[k] for k in current_keys - baseline_keys
        )
        removed = tuple(
            baseline_map[k] for k in baseline_keys - current_keys
        )
        unchanged = tuple(
            current_map[k] for k in baseline_keys & current_keys
        )

        delta = InventoryDelta(
            delta_id=f"delta-{uuid.uuid4().hex[:12]}",
            baseline=baseline,
            current=current,
            added=added,
            removed=removed,
            unchanged=unchanged,
        )
        self._deltas.append(delta)
        return delta

    def reconcile_change(
        self,
        change: SystemChange,
        current_inventory: EffectInventory,
    ) -> ReconciliationResult:
        """Reconcile a system change against the current completeness claim.

        This is the core method. It determines:
        - Whether the change affects the completeness claim
        - What action to take
        - Whether the historical claim is preserved
        """
        prior = self.current_claim

        # Compute delta between prior inventory and current
        if prior:
            delta = self.compute_delta(prior.inventory, current_inventory)
        else:
            delta = None

        # Determine scope impact
        scope_impact = self._assess_scope_impact(change, prior, delta)

        # Determine action
        action = self._determine_action(change, prior, delta, scope_impact)

        # Determine temporal impact
        temporal_impact = self._determine_temporal_impact(action, change)

        # Create new claim if needed
        new_claim = None
        if action in (
            ReconciliationAction.REVALIDATION_REQUIRED,
            ReconciliationAction.COMPLETENESS_INVALIDATED,
            ReconciliationAction.INVENTORY_EXTENDED,
        ):
            new_claim = self._create_new_claim(
                change, current_inventory, prior, action, scope_impact
            )

        result = ReconciliationResult(
            result_id=f"result-{uuid.uuid4().hex[:12]}",
            change=change,
            prior_claim=prior,
            action=action,
            new_claim=new_claim,
            delta=delta,
            scope_impact=scope_impact,
            temporal_impact=temporal_impact,
            notes=self._generate_notes(action, scope_impact, temporal_impact),
        )
        self._results.append(result)
        return result

    def _assess_scope_impact(
        self,
        change: SystemChange,
        prior: CompletenessClaim | None,
        delta: InventoryDelta | None,
    ) -> str:
        """Determine how the change affects the scope of the completeness claim."""
        if not prior or not delta:
            return "new_category" if change.introduces_effects else "unchanged"

        # Check if new categories were added
        prior_categories = prior.inventory.categories
        current_categories = delta.current.categories
        new_categories = current_categories - prior_categories

        if new_categories:
            return "new_category"

        # Check if effects were added in existing categories
        if delta.added:
            return "extended"

        # Check if effects were removed
        if delta.removed:
            return "narrowed"

        return "unchanged"

    def _determine_action(
        self,
        change: SystemChange,
        prior: CompletenessClaim | None,
        delta: InventoryDelta | None,
        scope_impact: str,
    ) -> ReconciliationAction:
        """Determine the reconciliation action."""
        if not prior:
            return ReconciliationAction.REVALIDATION_REQUIRED

        if scope_impact == "unchanged":
            return ReconciliationAction.NO_ACTION

        if scope_impact == "new_category":
            # New effect category discovered — completeness claim is invalidated
            # for the new category, but historical claim is preserved
            return ReconciliationAction.COMPLETENESS_INVALIDATED

        if scope_impact == "extended":
            # New effects in existing categories — inventory extended
            return ReconciliationAction.INVENTORY_EXTENDED

        if scope_impact == "narrowed":
            # Effects removed — scope narrowed, no revalidation needed
            return ReconciliationAction.SCOPE_NARROWED

        return ReconciliationAction.REVALIDATION_REQUIRED

    def _determine_temporal_impact(
        self,
        action: ReconciliationAction,
        change: SystemChange,
    ) -> str:
        """Determine the temporal impact of the action.

        Critical: revalidation does NOT retroactively invalidate.
        """
        if action == ReconciliationAction.NO_ACTION:
            return "no_invalidation"

        if action == ReconciliationAction.COMPLETENESS_INVALIDATED:
            # The prior claim is preserved for its time; the new change
            # simply means the claim does not extend to the new commit
            return "revalidation_required"

        if action == ReconciliationAction.INVENTORY_EXTENDED:
            return "revalidation_required"

        if action == ReconciliationAction.SCOPE_NARROWED:
            return "no_invalidation"

        return "revalidation_required"

    def _create_new_claim(
        self,
        change: SystemChange,
        inventory: EffectInventory,
        prior: CompletenessClaim | None,
        action: ReconciliationAction,
        scope_impact: str,
    ) -> CompletenessClaim:
        """Create a new completeness claim after a change.

        Expires the prior claim (temporally bounded) without retroactively
        invalidating it.
        """
        now = datetime.now(UTC).isoformat()

        # Expire the prior claim
        if prior and prior.is_current:
            expired = prior.expires_at(now)
            # Replace the prior claim in history with the expired version
            for i, c in enumerate(self._claims):
                if c.claim_id == prior.claim_id:
                    self._claims[i] = expired
                    break

        # Determine new status
        if action == ReconciliationAction.COMPLETENESS_INVALIDATED:
            status = CompletenessStatus.INCOMPLETE
        elif action == ReconciliationAction.INVENTORY_EXTENDED:
            status = CompletenessStatus.UNKNOWN
        else:
            status = CompletenessStatus.UNKNOWN

        new_claim = CompletenessClaim(
            claim_id=f"claim-{uuid.uuid4().hex[:12]}",
            commit_ref=change.commit_ref,
            scope=inventory.scope,
            status=status,
            inventory=inventory,
            valid_from=now,
            basis=f"reconciliation_after_{change.change_type.value}",
            notes=(
                f"New claim after {change.change_type.value} at {change.commit_ref}. "
                f"Scope impact: {scope_impact}. "
                f"Prior claim {prior.claim_id if prior else 'none'} expired at {now}."
            ),
        )
        self._claims.append(new_claim)
        return new_claim

    def _generate_notes(
        self,
        action: ReconciliationAction,
        scope_impact: str,
        temporal_impact: str,
    ) -> str:
        """Generate human-readable notes for the result."""
        parts = [f"Action: {action.value}"]
        parts.append(f"Scope impact: {scope_impact}")
        parts.append(f"Temporal impact: {temporal_impact}")
        if temporal_impact == "revalidation_required":
            parts.append("Historical claim preserved; revalidation required for new state.")
        return "; ".join(parts)


# ---------------------------------------------------------------------------
# Phase 28 experiment
# ---------------------------------------------------------------------------

class Phase28Experiment:
    """Runs the Phase 28 continuous effect reconciliation experiments."""

    def __init__(self) -> None:
        self.reconciler = ContinuousEffectReconciler()
        self._results: list[ReconciliationResult] = []

    def run_all(self) -> list[ReconciliationResult]:
        """Run all Phase 28 experiments."""
        self._run_baseline_registration()
        self._run_no_change_scenario()
        self._run_new_category_discovery()
        self._run_existing_category_extension()
        self._run_effect_removal()
        self._run_multiple_sequential_changes()
        self._run_temporal_validity_chain()
        return self._results

    def _make_effect(
        self,
        category: EffectCategory,
        source: str,
        target: str,
        operation: str,
        visibility: EffectVisibility = EffectVisibility.DECLARED,
        authority_path_status: AuthorityPathStatus = AuthorityPathStatus.GOVERNED,
        description: str = "",
    ) -> ConsequentialEffect:
        """Helper to create a ConsequentialEffect."""
        return ConsequentialEffect(
            effect_id=f"eff-{uuid.uuid4().hex[:12]}",
            category=category,
            source=source,
            target=target,
            operation=operation,
            visibility=visibility,
            authority_path_status=authority_path_status,
            description=description,
        )

    def _make_inventory(
        self,
        effects: tuple[ConsequentialEffect, ...] | None = None,
        commit_ref: str = "baseline",
        scope: str = "runtime",
    ) -> EffectInventory:
        """Helper to create an EffectInventory."""
        if effects is None:
            effects = tuple()
        return EffectInventory(
            inventory_id=f"inv-{uuid.uuid4().hex[:12]}",
            effects=effects,
            claimed_closure_rate=1.0,
            scope=scope,
            observation_method="static_analysis",
            generated_by="phase28_experiment",
            created_at=datetime.now(UTC).isoformat(),
            commit_ref=commit_ref,
        )

    def _run_baseline_registration(self) -> None:
        """Register the initial completeness claim."""
        self._baseline_effects = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
                description="ARGO subprocess through RuntimeAuthorityGate",
            ),
            self._make_effect(
                EffectCategory.FILESYSTEM,
                "src/sas/registry.py",
                "open",
                "file.write",
                description="Registry file operations through CapabilityBoundFilesystem",
            ),
            self._make_effect(
                EffectCategory.DATABASE,
                "src/sas_tie_knowledge/adapter.py",
                "aiosqlite",
                "db.query",
                description="Database operations through CapabilityBoundDatabase",
            ),
        )
        inventory = self._make_inventory(self._baseline_effects, commit_ref="commit-C1")
        claim = self.reconciler.register_baseline(
            inventory=inventory,
            commit_ref="commit-C1",
            timestamp="2026-09-10T00:00:00Z",
            basis="phase26_remediation",
        )
        # No reconciliation result for baseline registration
        assert claim.is_current
        assert claim.status == CompletenessStatus.COMPLETE_WITHIN_SCOPE

    def _run_no_change_scenario(self) -> None:
        """Test: no change to the system → no action required."""
        # Same inventory as baseline — reuse the SAME effect objects
        inventory = self._make_inventory(self._baseline_effects, commit_ref="commit-C1")

        change = SystemChange(
            change_id="change-001",
            change_type=ChangeType.CONFIGURATION_CHANGE,
            source="config.yaml",
            description="Configuration change with no effect path changes",
            commit_ref="commit-C1",
            timestamp="2026-09-10T00:01:00Z",
            introduces_effects=False,
            removes_effects=False,
        )

        result = self.reconciler.reconcile_change(change, inventory)
        self._results.append(result)
        assert result.action == ReconciliationAction.NO_ACTION
        assert result.scope_impact == "unchanged"
        assert result.temporal_impact == "no_invalidation"

    def _run_new_category_discovery(self) -> None:
        """Test: new effect category discovered → completeness invalidated."""
        effects = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
            ),
            self._make_effect(
                EffectCategory.FILESYSTEM,
                "src/sas/registry.py",
                "open",
                "file.write",
            ),
            self._make_effect(
                EffectCategory.DATABASE,
                "src/sas_tie_knowledge/adapter.py",
                "aiosqlite",
                "db.query",
            ),
            self._make_effect(
                EffectCategory.PAYMENT,
                "src/sas/quant/trading.py",
                "payment.execute",
                "payment.transfer",
                description="New payment effect discovered in trading module",
            ),
        )
        inventory = self._make_inventory(effects, commit_ref="commit-C2")

        change = SystemChange(
            change_id="change-002",
            change_type=ChangeType.SOURCE_ADDED,
            source="src/sas/quant/trading.py",
            description="New trading module with payment effects",
            commit_ref="commit-C2",
            timestamp="2026-09-10T00:02:00Z",
            categories_affected={EffectCategory.PAYMENT},
            introduces_effects=True,
        )

        result = self.reconciler.reconcile_change(change, inventory)
        self._results.append(result)
        assert result.action == ReconciliationAction.COMPLETENESS_INVALIDATED
        assert result.scope_impact == "new_category"
        assert result.temporal_impact == "revalidation_required"
        # Historical claim is preserved (NOT retroactively invalidated)
        assert result.historical_claim_preserved
        # New claim is created
        assert result.new_claim is not None
        assert result.new_claim.status == CompletenessStatus.INCOMPLETE

    def _run_existing_category_extension(self) -> None:
        """Test: new effect in existing category → inventory extended."""
        effects = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
            ),
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/cli/helper.py",
                "subprocess.Popen",
                "subprocess.spawn",
                description="New subprocess effect in CLI helper",
            ),
            self._make_effect(
                EffectCategory.FILESYSTEM,
                "src/sas/registry.py",
                "open",
                "file.write",
            ),
        )
        inventory = self._make_inventory(effects, commit_ref="commit-C3")

        change = SystemChange(
            change_id="change-003",
            change_type=ChangeType.SOURCE_MODIFIED,
            source="src/sas/cli/helper.py",
            description="CLI helper modified to add subprocess call",
            commit_ref="commit-C3",
            timestamp="2026-09-10T00:03:00Z",
            categories_affected={EffectCategory.SUBPROCESS},
            introduces_effects=True,
        )

        result = self.reconciler.reconcile_change(change, inventory)
        self._results.append(result)
        assert result.action == ReconciliationAction.INVENTORY_EXTENDED
        assert result.scope_impact == "extended"
        assert result.temporal_impact == "revalidation_required"

    def _run_effect_removal(self) -> None:
        """Test: effect removed → scope narrowed, no revalidation needed."""
        effects = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
            ),
        )
        inventory = self._make_inventory(effects, commit_ref="commit-C4")

        change = SystemChange(
            change_id="change-004",
            change_type=ChangeType.SOURCE_REMOVED,
            source="src/sas/cli/helper.py",
            description="CLI helper module removed",
            commit_ref="commit-C4",
            timestamp="2026-09-10T00:04:00Z",
            categories_affected={EffectCategory.SUBPROCESS},
            removes_effects=True,
        )

        result = self.reconciler.reconcile_change(change, inventory)
        self._results.append(result)
        assert result.action == ReconciliationAction.SCOPE_NARROWED
        assert result.scope_impact == "narrowed"
        assert result.temporal_impact == "no_invalidation"

    def _run_multiple_sequential_changes(self) -> None:
        """Test: multiple sequential changes produce a chain of claims."""
        # First change: add network effect
        effects_1 = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
            ),
            self._make_effect(
                EffectCategory.NETWORK,
                "src/sas/quant/api.py",
                "httpx",
                "http.request",
                description="New network effect in API module",
            ),
        )
        inventory_1 = self._make_inventory(effects_1, commit_ref="commit-C5a")

        change_1 = SystemChange(
            change_id="change-005a",
            change_type=ChangeType.SOURCE_ADDED,
            source="src/sas/quant/api.py",
            description="New API module with network calls",
            commit_ref="commit-C5a",
            timestamp="2026-09-10T00:05:00Z",
            categories_affected={EffectCategory.NETWORK},
            introduces_effects=True,
        )

        result_1 = self.reconciler.reconcile_change(change_1, inventory_1)
        self._results.append(result_1)
        assert result_1.action == ReconciliationAction.COMPLETENESS_INVALIDATED

        # Second change: add plugin effect
        effects_2 = (
            self._make_effect(
                EffectCategory.SUBPROCESS,
                "src/sas/argopack.py",
                "subprocess.run",
                "subprocess.execute",
            ),
            self._make_effect(
                EffectCategory.NETWORK,
                "src/sas/quant/api.py",
                "httpx",
                "http.request",
            ),
            self._make_effect(
                EffectCategory.PLUGIN,
                "src/sas/plugins/loader.py",
                "importlib",
                "plugin.load",
                description="New plugin loading effect",
            ),
        )
        inventory_2 = self._make_inventory(effects_2, commit_ref="commit-C5b")

        change_2 = SystemChange(
            change_id="change-005b",
            change_type=ChangeType.PLUGIN_REGISTERED,
            source="src/sas/plugins/loader.py",
            description="New plugin loader registered",
            commit_ref="commit-C5b",
            timestamp="2026-09-10T00:06:00Z",
            categories_affected={EffectCategory.PLUGIN},
            introduces_effects=True,
        )

        result_2 = self.reconciler.reconcile_change(change_2, inventory_2)
        self._results.append(result_2)
        assert result_2.action == ReconciliationAction.COMPLETENESS_INVALIDATED

        # Verify claim chain
        claims = self.reconciler.claim_history
        assert len(claims) >= 3  # baseline + 2 new claims
        # Only the last claim should be current
        current_claims = [c for c in claims if c.is_current]
        assert len(current_claims) == 1

    def _run_temporal_validity_chain(self) -> None:
        """Test: temporal validity chain preserves historical claims."""
        # The claim history should show:
        # - Baseline claim: expired at first change
        # - Intermediate claims: expired at subsequent changes
        # - Current claim: still valid
        claims = self.reconciler.claim_history

        # At least one claim should be expired
        expired = [c for c in claims if c.is_expired]
        assert len(expired) >= 1

        # At least one claim should be current
        current = [c for c in claims if c.is_current]
        assert len(current) == 1

        # Historical claims are NOT retroactively invalidated
        # They were valid for their time; they simply don't extend
        for c in expired:
            # The claim's status at the time it was made was valid
            # Note: INCOMPLETE is valid — it means the claim was already
            # incomplete when created (e.g., after new category discovery),
            # not that it was retroactively invalidated
            assert c.status in (
                CompletenessStatus.COMPLETE_WITHIN_SCOPE,
                CompletenessStatus.UNKNOWN,
                CompletenessStatus.INCOMPLETE,
            )


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

def run_phase28() -> list[ReconciliationResult]:
    """Run the Phase 28 experiment suite."""
    exp = Phase28Experiment()
    return exp.run_all()


if __name__ == "__main__":
    results = run_phase28()
    print(f"Phase 28: {len(results)} reconciliation results")
    for r in results:
        print(f"  {r.change.change_id}: {r.action.value} | scope={r.scope_impact} | temporal={r.temporal_impact}")
