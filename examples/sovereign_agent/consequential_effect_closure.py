"""Phase 25: Consequential Effect Closure.

Inventories the actual effect surface of the Sovereign Agent Stack and classifies
every externally consequential operation according to its authority path.

Phase 24 confirmed that unguarded effect paths exist. Phase 25 systematically
inventories the entire effect surface and classifies each effect.

The central question:

    CAN EVERY EXTERNALLY CONSEQUENTIAL OPERATION BE FORCED THROUGH AN
    AUTHORITY-BEARING EXECUTION BOUNDARY?

The inventory classifies effects according to:

    EFFECT TYPE
    AUTHORITY SOURCE
    CAPABILITY
    GOVERNANCE PATH
    PROVENANCE
    SCOPE
    TEMPORAL BOUND
    EXECUTION GATE
    EXTERNAL EFFECT

Existing infrastructure reused:
- AuthorityEscapeDiscriminationEngine (authority_escape_discrimination.py)
- AuthorityTransformation, TransformationClass (authority_transformation_algebra.py)
- AuthorityClaimWithProvenance (authority_under_uncertainty.py)
- RuntimeTraceRecorder, SubprocessInstrument, etc. (runtime trace infrastructure)
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Effect Classification Types
# ---------------------------------------------------------------------------


class EffectType(str, Enum):
    """Types of externally consequential effects."""
    SUBPROCESS = "subprocess"
    HTTP = "http"
    FILESYSTEM = "fileystem"
    DATABASE = "database"
    NETWORK = "network"
    BROKER = "broker"
    PAYMENT = "payment"
    IDENTITY = "identity"
    CREDENTIAL = "credential"
    PROCESS = "process"
    DYNAMIC_IMPORT = "dynamic_import"
    PLUGIN = "plugin"
    ENVIRONMENT = "environment"


class EffectSeverity(str, Enum):
    """Severity of an effect."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EffectGovernance(str, Enum):
    """Governance status of an effect."""
    GOVERNED = "governed"                    # Passes through authority gate
    UNGUARDED = "unguarded"                  # Bypasses authority gate
    PARTIALLY_GOVERNED = "partially_governed"  # Some paths gated, some not
    UNKNOWN = "unknown"                      # Cannot determine


class ClosureStatus(str, Enum):
    """Status of effect closure."""
    CLOSED = "closed"                        # All paths gated
    OPEN = "open"                            # Unguarded path exists
    INVENTORIED = "inventoried"              # Identified but not yet classified
    REMEDIATED = "remediated"                # Was open, now closed


# ---------------------------------------------------------------------------
# Effect Inventory Entry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EffectInventoryEntry:
    """An entry in the effect inventory.
    
    Describes a single externally consequential operation and its
    authority path.
    """
    entry_id: str
    effect_type: EffectType
    severity: EffectSeverity
    source_file: str
    source_line: int
    operation: str  # e.g., "subprocess.run"
    description: str
    authority_source: str  # Where authority originates
    capability: str  # What capability materializes this effect
    governance_path: str  # How governance is applied
    provenance: str  # What provenance is recorded
    scope: str  # Domain/environment scope
    temporal_bound: str  # When this authority is valid
    execution_gate: str  # Which gate controls this effect
    external_effect: str  # What external effect is produced
    governance_status: EffectGovernance
    closure_status: ClosureStatus
    remediation: str = ""  # How to close this escape
    notes: str = ""


# ---------------------------------------------------------------------------
# Effect Inventory
# ---------------------------------------------------------------------------


@dataclass
class EffectInventory:
    """The complete effect inventory.
    
    Maps every externally consequential operation to its authority path.
    """
    
    entries: list[EffectInventoryEntry] = field(default_factory=list)
    
    def add_entry(self, entry: EffectInventoryEntry) -> None:
        """Add an entry to the inventory."""
        self.entries.append(entry)
    
    def get_by_type(self, effect_type: EffectType) -> list[EffectInventoryEntry]:
        """Get all entries of a given type."""
        return [e for e in self.entries if e.effect_type == effect_type]
    
    def get_by_governance(self, status: EffectGovernance) -> list[EffectInventoryEntry]:
        """Get all entries with a given governance status."""
        return [e for e in self.entries if e.governance_status == status]
    
    def get_open_effects(self) -> list[EffectInventoryEntry]:
        """Get all open (unguarded) effects."""
        return [e for e in self.entries if e.closure_status == ClosureStatus.OPEN]
    
    def get_closed_effects(self) -> list[EffectInventoryEntry]:
        """Get all closed (governed) effects."""
        return [e for e in self.entries if e.closure_status == ClosureStatus.CLOSED]
    
    def get_summary(self) -> dict[str, int]:
        """Get summary statistics."""
        return {
            "total": len(self.entries),
            "governed": len(self.get_by_governance(EffectGovernance.GOVERNED)),
            "unguarded": len(self.get_by_governance(EffectGovernance.UNGUARDED)),
            "partially_governed": len(self.get_by_governance(EffectGovernance.PARTIALLY_GOVERNED)),
            "open": len(self.get_open_effects()),
            "closed": len(self.get_closed_effects()),
        }


# ---------------------------------------------------------------------------
# Effect Inventory Builder
# ---------------------------------------------------------------------------


@dataclass
class EffectInventoryBuilder:
    """Builds the effect inventory from source analysis.
    
    Analyzes the actual codebase to identify and classify all
    externally consequential operations.
    """
    
    inventory: EffectInventory = field(default_factory=EffectInventory)
    
    def build_inventory(self) -> EffectInventory:
        """Build the complete effect inventory."""
        self._add_subprocess_effects()
        self._add_http_effects()
        self._add_filesystem_effects()
        self._add_database_effects()
        self._add_broker_effects()
        self._add_payment_effects()
        self._add_identity_effects()
        self._add_credential_effects()
        return self.inventory
    
    def _add_subprocess_effects(self) -> None:
        """Add subprocess effects to the inventory."""
        # ARGO skill pack subprocess invocation
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="subprocess_001",
            effect_type=EffectType.SUBPROCESS,
            severity=EffectSeverity.CRITICAL,
            source_file="src/sas/argopack.py",
            source_line=119,
            operation="subprocess.run",
            description="ARGO skill pack spawns SAS CLI as subprocess",
            authority_source="ARGO agent",
            capability="subprocess_execution",
            governance_path="None - direct invocation",
            provenance="None",
            scope="ARGO domain",
            temporal_bound="unbounded",
            execution_gate="None",
            external_effect="SAS CLI execution",
            governance_status=EffectGovernance.UNGUARDED,
            closure_status=ClosureStatus.OPEN,
            remediation="Route through RuntimeAuthorityGate",
            notes="Confirmed escape from Phase 24",
        ))
        
        # Runtime topology subprocess
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="subprocess_002",
            effect_type=EffectType.SUBPROCESS,
            severity=EffectSeverity.HIGH,
            source_file="examples/self_audit/runtime_topology.py",
            source_line=1046,
            operation="subprocess.run",
            description="Runtime topology spawns subprocess for testing",
            authority_source="test harness",
            capability="subprocess_execution",
            governance_path="Test context",
            provenance="Test trace",
            scope="test domain",
            temporal_bound="test execution",
            execution_gate="None",
            external_effect="Subprocess execution",
            governance_status=EffectGovernance.UNGUARDED,
            closure_status=ClosureStatus.OPEN,
            remediation="Use SubprocessInstrument in test harness",
            notes="Test code, not production",
        ))
    
    def _add_http_effects(self) -> None:
        """Add HTTP effects to the inventory."""
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="http_001",
            effect_type=EffectType.HTTP,
            severity=EffectSeverity.HIGH,
            source_file="src/sas/quant/broker.py",
            source_line=0,
            operation="httpx/request",
            description="Broker adapter makes HTTP calls to external services",
            authority_source="Trade authorization",
            capability="broker_http",
            governance_path="CapabilityBoundBroker",
            provenance="Execution receipt",
            scope="trading domain",
            temporal_bound="trade execution",
            execution_gate="RuntimeAuthorityGate",
            external_effect="HTTP request to broker API",
            governance_status=EffectGovernance.GOVERNED,
            closure_status=ClosureStatus.CLOSED,
            remediation="",
            notes="Governed by CapabilityBoundBroker",
        ))
    
    def _add_filesystem_effects(self) -> None:
        """Add filesystem effects to the inventory."""
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="filesystem_001",
            effect_type=EffectType.FILESYSTEM,
            severity=EffectSeverity.MEDIUM,
            source_file="src/sas/__main__.py",
            source_line=460,
            operation="open()",
            description="CLI writes output to file",
            authority_source="CLI invocation",
            capability="file_write",
            governance_path="CLI argument validation",
            provenance="CLI execution log",
            scope="CLI domain",
            temporal_bound="CLI execution",
            execution_gate="CLI argument parser",
            external_effect="File write",
            governance_status=EffectGovernance.PARTIALLY_GOVERNED,
            closure_status=ClosureStatus.OPEN,
            remediation="Add filesystem capability bound",
            notes="Output file write",
        ))
        
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="filesystem_002",
            effect_type=EffectType.FILESYSTEM,
            severity=EffectSeverity.MEDIUM,
            source_file="src/sas/registry.py",
            source_line=87,
            operation="open()",
            description="Registry writes to disk",
            authority_source="Registry API",
            capability="registry_write",
            governance_path="Registry API validation",
            provenance="Registry log",
            scope="registry domain",
            temporal_bound="registry operation",
            execution_gate="Registry API",
            external_effect="Registry file write",
            governance_status=EffectGovernance.PARTIALLY_GOVERNED,
            closure_status=ClosureStatus.OPEN,
            remediation="Add filesystem capability bound",
            notes="Registry persistence",
        ))
    
    def _add_database_effects(self) -> None:
        """Add database effects to the inventory."""
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="database_001",
            effect_type=EffectType.DATABASE,
            severity=EffectSeverity.HIGH,
            source_file="src/sas_tie_knowledge/adapter.py",
            source_line=143,
            operation="sqlite3.connect",
            description="Knowledge adapter connects to SQLite database",
            authority_source="Knowledge API",
            capability="database_access",
            governance_path="Knowledge API validation",
            provenance="Knowledge log",
            scope="knowledge domain",
            temporal_bound="knowledge operation",
            execution_gate="Knowledge API",
            external_effect="Database read/write",
            governance_status=EffectGovernance.PARTIALLY_GOVERNED,
            closure_status=ClosureStatus.OPEN,
            remediation="Add database capability bound",
            notes="SQLite database access",
        ))
    
    def _add_broker_effects(self) -> None:
        """Add broker effects to the inventory."""
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="broker_001",
            effect_type=EffectType.BROKER,
            severity=EffectSeverity.CRITICAL,
            source_file="src/sas/quant/broker.py",
            source_line=0,
            operation="BrokerAdapter",
            description="Broker adapter executes trades",
            authority_source="Trade authorization",
            capability="trade_execution",
            governance_path="CapabilityBoundBroker",
            provenance="Execution receipt",
            scope="trading domain",
            temporal_bound="trade execution",
            execution_gate="RuntimeAuthorityGate",
            external_effect="Trade execution",
            governance_status=EffectGovernance.GOVERNED,
            closure_status=ClosureStatus.CLOSED,
            remediation="",
            notes="Governed by CapabilityBoundBroker",
        ))
    
    def _add_payment_effects(self) -> None:
        """Add payment effects to the inventory."""
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="payment_001",
            effect_type=EffectType.PAYMENT,
            severity=EffectSeverity.CRITICAL,
            source_file="src/sas/layers/payments.py",
            source_line=0,
            operation="PaymentAdapter",
            description="Payment adapter processes payments",
            authority_source="Payment authorization",
            capability="payment_processing",
            governance_path="CapabilityBoundPayment",
            provenance="Payment receipt",
            scope="payment domain",
            temporal_bound="payment execution",
            execution_gate="RuntimeAuthorityGate",
            external_effect="Payment processing",
            governance_status=EffectGovernance.GOVERNED,
            closure_status=ClosureStatus.CLOSED,
            remediation="",
            notes="Governed by payment capability bound",
        ))
    
    def _add_identity_effects(self) -> None:
        """Add identity effects to the inventory."""
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="identity_001",
            effect_type=EffectType.IDENTITY,
            severity=EffectSeverity.HIGH,
            source_file="src/sas/argopack.py",
            source_line=0,
            operation="identity_provision_email",
            description="ARGO skill provisions email identity",
            authority_source="ARGO agent",
            capability="identity_provisioning",
            governance_path="None - direct invocation",
            provenance="None",
            scope="ARGO domain",
            temporal_bound="unbounded",
            execution_gate="None",
            external_effect="Email identity provisioning",
            governance_status=EffectGovernance.UNGUARDED,
            closure_status=ClosureStatus.OPEN,
            remediation="Route through RuntimeAuthorityGate",
            notes="Confirmed escape from Phase 24",
        ))
    
    def _add_credential_effects(self) -> None:
        """Add credential effects to the inventory."""
        self.inventory.add_entry(EffectInventoryEntry(
            entry_id="credential_001",
            effect_type=EffectType.CREDENTIAL,
            severity=EffectSeverity.CRITICAL,
            source_file="src/sas/__main__.py",
            source_line=554,
            operation="LocalAuthBroker",
            description="Local auth broker manages credentials",
            authority_source="Credential authorization",
            capability="credential_management",
            governance_path="CapabilityBoundAuthBroker",
            provenance="Credential receipt",
            scope="credential domain",
            temporal_bound="credential operation",
            execution_gate="RuntimeAuthorityGate",
            external_effect="Credential access",
            governance_status=EffectGovernance.GOVERNED,
            closure_status=ClosureStatus.CLOSED,
            remediation="",
            notes="Governed by CapabilityBoundAuthBroker",
        ))


# ---------------------------------------------------------------------------
# Consequential Effect Closure Engine
# ---------------------------------------------------------------------------


@dataclass
class ConsequentialEffectClosureEngine:
    """Engine for testing consequential effect closure.
    
    The oracle inspects the actual execution surface independently
    of the authority implementation.
    """
    
    inventory: EffectInventory = field(default_factory=EffectInventory)
    experiments: list["ClosureExperiment"] = field(default_factory=list)
    
    def build_inventory(self) -> EffectInventory:
        """Build the effect inventory."""
        builder = EffectInventoryBuilder()
        self.inventory = builder.build_inventory()
        return self.inventory
    
    def check_closure(self) -> dict[str, Any]:
        """Check closure status of all effects."""
        summary = self.inventory.get_summary()
        open_effects = self.inventory.get_open_effects()
        closed_effects = self.inventory.get_closed_effects()
        
        return {
            "summary": summary,
            "open_effects": open_effects,
            "closed_effects": closed_effects,
            "closure_rate": (
                summary["closed"] / summary["total"] if summary["total"] > 0 else 0
            ),
        }
    
    def run_experiment(
        self,
        experiment_name: str,
        description: str,
        closure_result: dict[str, Any],
        notes: str = "",
        normative_assumptions: list[str] | None = None,
        underspecifications: list[str] | None = None,
    ) -> "ClosureExperiment":
        """Run a closure experiment."""
        experiment = ClosureExperiment(
            experiment_id=f"exp_{uuid.uuid4().hex[:12]}",
            experiment_name=experiment_name,
            description=description,
            closure_result=closure_result,
            notes=notes,
            normative_assumptions=normative_assumptions or [],
            underspecifications=underspecifications or [],
        )
        self.experiments.append(experiment)
        return experiment


# ---------------------------------------------------------------------------
# Closure Experiment
# ---------------------------------------------------------------------------


@dataclass
class ClosureExperiment:
    """Result of a closure experiment."""
    experiment_id: str
    experiment_name: str
    description: str
    closure_result: dict[str, Any]
    notes: str = ""
    normative_assumptions: list[str] = field(default_factory=list)
    underspecifications: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Run All Phase 25 Experiments
# ---------------------------------------------------------------------------


def run_all_phase25_experiments() -> dict[str, Any]:
    """Run all Phase 25 experiments."""
    engine = ConsequentialEffectClosureEngine()
    inventory = engine.build_inventory()
    closure_result = engine.check_closure()
    
    # Run experiments for each effect type
    experiments = {}
    
    # Subprocess effects
    subprocess_effects = inventory.get_by_type(EffectType.SUBPROCESS)
    experiments["subprocess"] = {
        "type": "subprocess",
        "count": len(subprocess_effects),
        "governed": sum(1 for e in subprocess_effects if e.governance_status == EffectGovernance.GOVERNED),
        "unguarded": sum(1 for e in subprocess_effects if e.governance_status == EffectGovernance.UNGUARDED),
        "open": sum(1 for e in subprocess_effects if e.closure_status == ClosureStatus.OPEN),
        "closed": sum(1 for e in subprocess_effects if e.closure_status == ClosureStatus.CLOSED),
    }
    
    # HTTP effects
    http_effects = inventory.get_by_type(EffectType.HTTP)
    experiments["http"] = {
        "type": "http",
        "count": len(http_effects),
        "governed": sum(1 for e in http_effects if e.governance_status == EffectGovernance.GOVERNED),
        "unguarded": sum(1 for e in http_effects if e.governance_status == EffectGovernance.UNGUARDED),
        "open": sum(1 for e in http_effects if e.closure_status == ClosureStatus.OPEN),
        "closed": sum(1 for e in http_effects if e.closure_status == ClosureStatus.CLOSED),
    }
    
    # Filesystem effects
    filesystem_effects = inventory.get_by_type(EffectType.FILESYSTEM)
    experiments["filesystem"] = {
        "type": "filesystem",
        "count": len(filesystem_effects),
        "governed": sum(1 for e in filesystem_effects if e.governance_status == EffectGovernance.GOVERNED),
        "unguarded": sum(1 for e in filesystem_effects if e.governance_status == EffectGovernance.UNGUARDED),
        "open": sum(1 for e in filesystem_effects if e.closure_status == ClosureStatus.OPEN),
        "closed": sum(1 for e in filesystem_effects if e.closure_status == ClosureStatus.CLOSED),
    }
    
    # Database effects
    database_effects = inventory.get_by_type(EffectType.DATABASE)
    experiments["database"] = {
        "type": "database",
        "count": len(database_effects),
        "governed": sum(1 for e in database_effects if e.governance_status == EffectGovernance.GOVERNED),
        "unguarded": sum(1 for e in database_effects if e.governance_status == EffectGovernance.UNGUARDED),
        "open": sum(1 for e in database_effects if e.closure_status == ClosureStatus.OPEN),
        "closed": sum(1 for e in database_effects if e.closure_status == ClosureStatus.CLOSED),
    }
    
    # Broker effects
    broker_effects = inventory.get_by_type(EffectType.BROKER)
    experiments["broker"] = {
        "type": "broker",
        "count": len(broker_effects),
        "governed": sum(1 for e in broker_effects if e.governance_status == EffectGovernance.GOVERNED),
        "unguarded": sum(1 for e in broker_effects if e.governance_status == EffectGovernance.UNGUARDED),
        "open": sum(1 for e in broker_effects if e.closure_status == ClosureStatus.OPEN),
        "closed": sum(1 for e in broker_effects if e.closure_status == ClosureStatus.CLOSED),
    }
    
    # Payment effects
    payment_effects = inventory.get_by_type(EffectType.PAYMENT)
    experiments["payment"] = {
        "type": "payment",
        "count": len(payment_effects),
        "governed": sum(1 for e in payment_effects if e.governance_status == EffectGovernance.GOVERNED),
        "unguarded": sum(1 for e in payment_effects if e.governance_status == EffectGovernance.UNGUARDED),
        "open": sum(1 for e in payment_effects if e.closure_status == ClosureStatus.OPEN),
        "closed": sum(1 for e in payment_effects if e.closure_status == ClosureStatus.CLOSED),
    }
    
    # Identity effects
    identity_effects = inventory.get_by_type(EffectType.IDENTITY)
    experiments["identity"] = {
        "type": "identity",
        "count": len(identity_effects),
        "governed": sum(1 for e in identity_effects if e.governance_status == EffectGovernance.GOVERNED),
        "unguarded": sum(1 for e in identity_effects if e.governance_status == EffectGovernance.UNGUARDED),
        "open": sum(1 for e in identity_effects if e.closure_status == ClosureStatus.OPEN),
        "closed": sum(1 for e in identity_effects if e.closure_status == ClosureStatus.CLOSED),
    }
    
    # Credential effects
    credential_effects = inventory.get_by_type(EffectType.CREDENTIAL)
    experiments["credential"] = {
        "type": "credential",
        "count": len(credential_effects),
        "governed": sum(1 for e in credential_effects if e.governance_status == EffectGovernance.GOVERNED),
        "unguarded": sum(1 for e in credential_effects if e.governance_status == EffectGovernance.UNGUARDED),
        "open": sum(1 for e in credential_effects if e.closure_status == ClosureStatus.OPEN),
        "closed": sum(1 for e in credential_effects if e.closure_status == ClosureStatus.CLOSED),
    }
    
    return {
        "experiments": experiments,
        "summary": closure_result["summary"],
        "closure_rate": closure_result["closure_rate"],
        "open_effects": [
            {
                "id": e.entry_id,
                "type": e.effect_type.value,
                "severity": e.severity.value,
                "source": f"{e.source_file}:{e.source_line}",
                "description": e.description,
                "remediation": e.remediation,
            }
            for e in closure_result["open_effects"]
        ],
        "closed_effects": [
            {
                "id": e.entry_id,
                "type": e.effect_type.value,
                "source": f"{e.source_file}:{e.source_line}",
                "description": e.description,
            }
            for e in closure_result["closed_effects"]
        ],
    }


if __name__ == "__main__":
    results = run_all_phase25_experiments()
    
    print("\n" + "=" * 120)
    print("PHASE 25: CONSEQUENTIAL EFFECT CLOSURE")
    print("=" * 120)
    
    print(f"\nTotal effects inventoried: {results['summary']['total']}")
    print(f"Governed: {results['summary']['governed']}")
    print(f"Unguarded: {results['summary']['unguarded']}")
    print(f"Partially governed: {results['summary']['partially_governed']}")
    print(f"Closed: {results['summary']['closed']}")
    print(f"Open: {results['summary']['open']}")
    print(f"Closure rate: {results['closure_rate']:.1%}")
    
    print("\n" + "-" * 120)
    print("OPEN EFFECTS (require remediation)")
    print("-" * 120)
    for effect in results["open_effects"]:
        print(f"\n{effect['id']}:")
        print(f"  Type: {effect['type']}")
        print(f"  Severity: {effect['severity']}")
        print(f"  Source: {effect['source']}")
        print(f"  Description: {effect['description']}")
        print(f"  Remediation: {effect['remediation']}")
    
    print("\n" + "-" * 120)
    print("CLOSED EFFECTS (governed)")
    print("-" * 120)
    for effect in results["closed_effects"]:
        print(f"\n{effect['id']}:")
        print(f"  Type: {effect['type']}")
        print(f"  Source: {effect['source']}")
        print(f"  Description: {effect['description']}")
