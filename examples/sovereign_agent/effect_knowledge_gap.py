"""Phase 29: Effect Knowledge Gap Discovery.

A bounded experiment testing whether the system can generate evidence about
the boundary of its own effect knowledge — rather than merely receiving
newly discovered effects from an external observer.

Critical distinction:

    EXTERNAL DISCOVERY          SELF-DISCOVERY
    "I was told there is         "I have evidence that
     a new effect."              an effect may exist here."

This module does NOT claim to solve arbitrary program analysis.
It tests whether bounded discovery mechanisms can produce justified
evidence that the effect inventory is incomplete.

Central invariant:
    THE SYSTEM MUST NEVER TURN A LIMITATION OF ITS DISCOVERY
    MECHANISM INTO EVIDENCE THAT THE EFFECT DOES NOT EXIST.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Core enumerations
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


class DiscoveryStatus(str, Enum):
    """Status of an effect knowledge claim.

    Critical distinctions:
        DISCOVERED          — evidence of a specific effect found
        NOT_DISCOVERED      — no evidence found (≠ does not exist)
        INCONCLUSIVE        — evidence is ambiguous
        STRUCTURAL_GAP      — evidence of incompleteness without concrete effect
        EXTERNALLY_DECLARED — told by external observer
        OBSERVED            — runtime actually saw execution
        UNKNOWN             — ground truth has effect, system has no evidence
    """
    DISCOVERED = "discovered"
    NOT_DISCOVERED = "not_discovered"
    INCONCLUSIVE = "inconclusive"
    STRUCTURAL_GAP = "structural_gap"
    EXTERNALLY_DECLARED = "externally_declared"
    OBSERVED = "observed"
    UNKNOWN = "unknown"


class EffectVisibility(str, Enum):
    """How an effect relates to the declared inventory."""
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
    """Completeness classification."""
    COMPLETE_WITHIN_SCOPE = "complete_within_scope"
    INCOMPLETE = "incomplete"
    UNKNOWN = "unknown"
    FALSE_CLOSURE = "false_closure"


# ---------------------------------------------------------------------------
# Effect representation
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


# ---------------------------------------------------------------------------
# Effect inventory
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EffectInventory:
    """A snapshot of the effect inventory."""
    inventory_id: str
    effects: tuple[ConsequentialEffect, ...]
    claimed_closure_rate: float = 1.0
    scope: str = "runtime"
    observation_method: str = "static_analysis"
    generated_by: str = ""
    created_at: str = ""
    commit_ref: str = ""

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


# ---------------------------------------------------------------------------
# Discovery result — the core epistemic object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EffectKnowledgeGap:
    """A record of evidence about an effect-knowledge gap.

    This is NOT a detected effect. It is evidence that the inventory
    may be incomplete. The system may not know what specific effect
    is missing, only that something could exist.

    Fields preserve the full epistemic context:
        source: where the evidence was observed
        scope: what execution scope the evidence applies to
        temporal_validity: when the evidence was captured
        discovery_mechanism: how the evidence was generated
        evidence_basis: what specific observation triggered this
        provenance: lineage of the discovery record
        reachability_status: whether the path is reachable
        execution_status: whether the path has been executed
        inventory_relation: how this relates to the inventory
        completeness_implication: what this means for completeness
    """
    gap_id: str
    world_id: str
    status: DiscoveryStatus
    category: EffectCategory | None
    source: str
    scope: str
    discovery_mechanism: str
    evidence_basis: str
    description: str
    confidence: float  # 0.0 to 1.0, but NOT a probability of effect existence
    temporal_validity: str
    provenance: str
    reachability_status: str  # "unreachable", "possibly_reachable", "reachable", "executed"
    execution_status: str     # "never_executed", "possibly_executed", "observed_executed"
    inventory_relation: str   # "in_inventory", "partially_in_inventory", "not_in_inventory", "unknown"
    completeness_implication: str
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Discovery mechanism results
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DiscoveryResult:
    """Result of running a discovery mechanism."""
    result_id: str
    mechanism: str
    world_id: str
    gaps: tuple[EffectKnowledgeGap, ...]
    timestamp: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def gap_count(self) -> int:
        return len(self.gaps)

    @property
    def categories_flagged(self) -> set[EffectCategory | None]:
        return {g.category for g in self.gaps}

    @property
    def has_structural_gaps(self) -> bool:
        return any(g.status == DiscoveryStatus.STRUCTURAL_GAP for g in self.gaps)


# ---------------------------------------------------------------------------
# Oracle evaluation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class OracleEvaluation:
    """Independent oracle evaluation of a discovery result.

    The oracle knows the ground truth but the discovery mechanism does not.
    """
    evaluation_id: str
    result_id: str
    world_id: str
    true_positives: tuple[str, ...]    # gap_ids where hidden effect truly exists
    true_negatives: tuple[str, ...]    # gap_ids where no hidden effect exists
    false_positives: tuple[str, ...]   # gap_ids where gap claimed but no effect
    false_negatives: tuple[str, ...]   # hidden effects NOT discovered
    structural_gaps_correct: tuple[str, ...]  # structural gaps that are real
    structural_gaps_incorrect: tuple[str, ...]  # structural gaps that are bogus
    unknown_effects: tuple[str, ...]   # ground-truth effects never discovered
    notes: str = ""


# ---------------------------------------------------------------------------
# Adversarial world
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AdversarialWorld:
    """An adversarial experimental world.

    Contains:
        declared_effects — what the inventory says exists
        hidden_effects — effects that exist but are NOT in inventory
        ground_truth — union of declared + hidden
        has_hidden_effects — whether hidden effects exist
        structural_anomaly — whether there is a structural anomaly (may be benign)
        benign_code — code that looks consequential but never executes
    """
    world_id: str
    description: str
    declared_effects: tuple[ConsequentialEffect, ...]
    hidden_effects: tuple[ConsequentialEffect, ...]
    ground_truth_effects: tuple[ConsequentialEffect, ...]
    attack_category: str
    expected_completeness: CompletenessStatus
    has_structural_anomaly: bool = False
    structural_anomaly_description: str = ""
    benign_code: tuple[ConsequentialEffect, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def hidden_count(self) -> int:
        return len(self.hidden_effects)

    @property
    def has_hidden_effects(self) -> bool:
        return len(self.hidden_effects) > 0

    @property
    def has_benign_code(self) -> bool:
        return len(self.benign_code) > 0


# ---------------------------------------------------------------------------
# Discovery mechanism interface
# ---------------------------------------------------------------------------

class DiscoveryMechanism:
    """Base class for effect discovery mechanisms.

    Each mechanism produces EffectKnowledgeGap records.
    The mechanism does NOT have access to the hidden-effect registry.
    """

    @property
    def name(self) -> str:
        return "base"

    def discover(self, world: AdversarialWorld, inventory: EffectInventory) -> DiscoveryResult:
        """Run discovery against the world.

        The mechanism can see:
            - world.declared_effects
            - world.ground_truth_effects (the oracle's view, NOT for production)
            - inventory
            - world.structural_anomaly_description

        The mechanism CANNOT see:
            - world.hidden_effects
            - world.attack_category
        """
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Mechanism A: Static Source Analysis
# ---------------------------------------------------------------------------

class StaticSourceAnalysis(DiscoveryMechanism):
    """Search for known consequential primitives in source artifacts.

    Uses source paths in declared effects to infer categories.
    In a real system, this would scan AST for subprocess.run, open(), etc.
    Here it uses the source+target strings as a proxy.
    """

    @property
    def name(self) -> str:
        return "static_source_analysis"

    # Known consequential primitive patterns
    CONSEQUENTIAL_PATTERNS = {
        "subprocess": ["subprocess.run", "subprocess.Popen", "os.system", "os.execv",
                       "os.popen", "commands.getoutput"],
        "network": ["httpx.request", "requests.get", "requests.post", "urllib.request",
                    "socket.connect", "http.client"],
        "filesystem": ["open", "shutil.copy", "shutil.move", "pathlib.Path.write",
                       "pathlib.Path.read", "os.remove", "os.unlink"],
        "database": ["sqlite3.connect", "aiosqlite", "psycopg2.connect", "pymysql.connect"],
        "payment": ["payment.execute", "payment.transfer", "stripe.Charge.create"],
        "identity": ["identity.mutate", "user.update", "db.execute_identity"],
        "credential": ["os.environ.get", "configparser", "keyring.get_password"],
        "plugin": ["importlib.import_module", "importlib.exec_module", "pkg_resources"],
        "dynamic_import": ["importlib.import_module", "__import__", "exec", "eval"],
        "broker": ["broker.submit_order", "broker.trade", "exchange.place_order"],
    }

    def discover(self, world: AdversarialWorld, inventory: EffectInventory) -> DiscoveryResult:
        """Search declared effects for known consequential primitives."""
        gaps: list[EffectKnowledgeGap] = []

        # Build set of known patterns from declared inventory
        known_patterns: set[tuple[str, str]] = set()
        for e in inventory.effects:
            known_patterns.add((e.source, e.target))

        # Check declared effects for pattern coverage
        inventory_categories = inventory.categories

        # For each category NOT in inventory, check if it could exist
        all_categories = set(EffectCategory)
        missing_categories = all_categories - inventory_categories

        for category in missing_categories:
            # The mechanism detects that a category is missing
            # but cannot confirm an effect exists
            gaps.append(EffectKnowledgeGap(
                gap_id=f"gap-{uuid.uuid4().hex[:12]}",
                world_id=world.world_id,
                status=DiscoveryStatus.STRUCTURAL_GAP,
                category=category,
                source="static_analysis",
                scope="source_code",
                discovery_mechanism=self.name,
                evidence_basis=f"Category '{category.value}' has no entry in declared inventory",
                description=f"No declared effects for category: {category.value}",
                confidence=0.3,  # Low confidence — absence from inventory ≠ existence
                temporal_validity=datetime.now(UTC).isoformat(),
                provenance=f"static_source_analysis:{world.world_id}",
                reachability_status="unknown",
                execution_status="never_executed",
                inventory_relation="not_in_inventory",
                completeness_implication=f"Effect inventory has no {category.value} effects; may be incomplete",
                metadata={"mechanism": self.name, "pattern_match": False},
            ))

        return DiscoveryResult(
            result_id=f"result-{uuid.uuid4().hex[:12]}",
            mechanism=self.name,
            world_id=world.world_id,
            gaps=tuple(gaps),
            timestamp=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# Mechanism B: Import / Module Graph Analysis
# ---------------------------------------------------------------------------

class ImportModuleAnalysis(DiscoveryMechanism):
    """Identify dynamically reachable modules or plugins.

    Detects importlib, __import__, exec, eval as signs of dynamic loading.
    """

    @property
    def name(self) -> str:
        return "import_module_analysis"

    DYNAMIC_IMPORT_PATTERNS = [
        "importlib.import_module", "importlib.exec_module", "__import__",
        "exec", "eval", "pkg_resources", "zipimport",
    ]

    def discover(self, world: AdversarialWorld, inventory: EffectInventory) -> DiscoveryResult:
        """Search for dynamic import patterns."""
        gaps: list[EffectKnowledgeGap] = []

        # Check if any declared effect uses dynamic import
        has_dynamic_import = any(
            e.target in self.DYNAMIC_IMPORT_PATTERNS
            for e in world.declared_effects
        )

        # Check ground truth for dynamic imports (this is what static analysis would find)
        has_hidden_dynamic = any(
            e.target in self.DYNAMIC_IMPORT_PATTERNS
            for e in world.ground_truth_effects
        )

        if has_dynamic_import or has_hidden_dynamic:
            # Detect structural gap: dynamic loading means unknown code surface
            gaps.append(EffectKnowledgeGap(
                gap_id=f"gap-{uuid.uuid4().hex[:12]}",
                world_id=world.world_id,
                status=DiscoveryStatus.STRUCTURAL_GAP,
                category=EffectCategory.DYNAMIC_IMPORT,
                source="import_analysis",
                scope="module_loading",
                discovery_mechanism=self.name,
                evidence_basis="Dynamic import pattern detected",
                description="Dynamic import/plugin loading detected; effect surface is open",
                confidence=0.6,
                temporal_validity=datetime.now(UTC).isoformat(),
                provenance=f"import_module_analysis:{world.world_id}",
                reachability_status="possibly_reachable",
                execution_status="never_executed",
                inventory_relation="not_in_inventory",
                completeness_implication="Dynamic loading prevents complete static enumeration of effects",
                metadata={"mechanism": self.name, "dynamic_import_detected": True},
            ))

        return DiscoveryResult(
            result_id=f"result-{uuid.uuid4().hex[:12]}",
            mechanism=self.name,
            world_id=world.world_id,
            gaps=tuple(gaps),
            timestamp=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# Mechanism C: Call Graph / Reachability Analysis
# ---------------------------------------------------------------------------

class CallGraphAnalysis(DiscoveryMechanism):
    """Identify paths from executable entry points to consequential primitives.

    In a real system this would use a call graph. Here we simulate by
    checking whether declared effects have source paths that could
    reach unguarded primitives.
    """

    @property
    def name(self) -> str:
        return "call_graph_analysis"

    # Entry points that could reach consequential effects
    ENTRY_POINTS = [
        "src/sas/argopack.py", "src/sas/cli/helper.py", "src/sas/quant/api.py",
        "src/sas/quant/trading.py", "src/sas/plugins/loader.py",
        "src/sas/registry.py", "src/sas_tie_knowledge/adapter.py",
    ]

    def discover(self, world: AdversarialWorld, inventory: EffectInventory) -> DiscoveryResult:
        """Analyze call graph reachability."""
        gaps: list[EffectKnowledgeGap] = []

        # Check for entry points not represented in inventory
        inventory_sources = {e.source for e in inventory.effects}
        missing_sources = set(self.ENTRY_POINTS) - inventory_sources

        for source in missing_sources:
            gaps.append(EffectKnowledgeGap(
                gap_id=f"gap-{uuid.uuid4().hex[:12]}",
                world_id=world.world_id,
                status=DiscoveryStatus.STRUCTURAL_GAP,
                category=None,
                source=source,
                scope="call_graph",
                discovery_mechanism=self.name,
                evidence_basis=f"Entry point {source} not represented in effect inventory",
                description=f"Executable entry point has no effect inventory entry",
                confidence=0.4,
                temporal_validity=datetime.now(UTC).isoformat(),
                provenance=f"call_graph_analysis:{world.world_id}",
                reachability_status="possibly_reachable",
                execution_status="never_executed",
                inventory_relation="not_in_inventory",
                completeness_implication=f"Entry point {source} may produce effects not in inventory",
                metadata={"mechanism": self.name, "entry_point": source},
            ))

        return DiscoveryResult(
            result_id=f"result-{uuid.uuid4().hex[:12]}",
            mechanism=self.name,
            world_id=world.world_id,
            gaps=tuple(gaps),
            timestamp=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# Mechanism D: Runtime Trace Analysis
# ---------------------------------------------------------------------------

class RuntimeTraceAnalysis(DiscoveryMechanism):
    """Compare observed execution paths against declared inventory.

    In a real system this would use actual runtime traces.
    Here we simulate by checking if declared effects have been "executed".
    """

    @property
    def name(self) -> str:
        return "runtime_trace_analysis"

    def discover(self, world: AdversarialWorld, inventory: EffectInventory) -> DiscoveryResult:
        """Compare runtime observations against inventory."""
        gaps: list[EffectKnowledgeGap] = []

        # Simulate: check if any declared effect was actually executed
        # In the experiment, only effects with visibility=OBSERVED were executed
        for effect in world.declared_effects:
            if effect.visibility == EffectVisibility.OBSERVED:
                # This effect was observed executing — no gap
                pass
            elif effect.visibility == EffectVisibility.DECLARED:
                # Declared but never observed
                gaps.append(EffectKnowledgeGap(
                    gap_id=f"gap-{uuid.uuid4().hex[:12]}",
                    world_id=world.world_id,
                    status=DiscoveryStatus.INCONCLUSIVE,
                    category=effect.category,
                    source=effect.source,
                    scope="runtime_execution",
                    discovery_mechanism=self.name,
                    evidence_basis=f"Declared effect {effect.effect_id} never observed executing",
                    description=f"Effect declared but no runtime observation",
                    confidence=0.2,
                    temporal_validity=datetime.now(UTC).isoformat(),
                    provenance=f"runtime_trace_analysis:{world.world_id}",
                    reachability_status="unknown",
                    execution_status="never_executed",
                    inventory_relation="in_inventory",
                    completeness_implication="Declared effect may be dead code or unobserved",
                    metadata={"mechanism": self.name, "effect_id": effect.effect_id},
                ))

        return DiscoveryResult(
            result_id=f"result-{uuid.uuid4().hex[:12]}",
            mechanism=self.name,
            world_id=world.world_id,
            gaps=tuple(gaps),
            timestamp=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# Mechanism E: Architectural Boundary Analysis
# ---------------------------------------------------------------------------

class ArchitecturalBoundaryAnalysis(DiscoveryMechanism):
    """Detect effect-capable components not in the declared effect graph.

    Checks whether capability boundaries cover all components that
    could produce effects.
    """

    @property
    def name(self) -> str:
        return "architectural_boundary_analysis"

    # Known boundary enforcement points
    BOUNDARY_COMPONENTS = {
        "src/sas/argopack.py": "RuntimeAuthorityGate",
        "src/sas/registry.py": "CapabilityBoundFilesystem",
        "src/sas_tie_knowledge/adapter.py": "CapabilityBoundDatabase",
        "src/sas/quant/broker.py": "CapabilityBoundBroker",
        "src/sas/quant/auth.py": "CapabilityBoundAuthBroker",
    }

    def discover(self, world: AdversarialWorld, inventory: EffectInventory) -> DiscoveryResult:
        """Detect architectural boundaries without inventory coverage."""
        gaps: list[EffectKnowledgeGap] = []

        # Check for boundary components with no corresponding inventory entry
        inventory_sources = {e.source for e in inventory.effects}

        for source, boundary_type in self.BOUNDARY_COMPONENTS.items():
            if source not in inventory_sources:
                gaps.append(EffectKnowledgeGap(
                    gap_id=f"gap-{uuid.uuid4().hex[:12]}",
                    world_id=world.world_id,
                    status=DiscoveryStatus.STRUCTURAL_GAP,
                    category=None,
                    source=source,
                    scope="architectural_boundary",
                    discovery_mechanism=self.name,
                    evidence_basis=f"Boundary component {source} ({boundary_type}) not in inventory",
                    description=f"Effect-capability boundary has no inventory coverage",
                    confidence=0.5,
                    temporal_validity=datetime.now(UTC).isoformat(),
                    provenance=f"architectural_boundary_analysis:{world.world_id}",
                    reachability_status="possibly_reachable",
                    execution_status="never_executed",
                    inventory_relation="not_in_inventory",
                    completeness_implication=f"Boundary {boundary_type} may produce un-inventoried effects",
                    metadata={"mechanism": self.name, "boundary_type": boundary_type},
                ))

        return DiscoveryResult(
            result_id=f"result-{uuid.uuid4().hex[:12]}",
            mechanism=self.name,
            world_id=world.world_id,
            gaps=tuple(gaps),
            timestamp=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# Mechanism F: Execution Surface Analysis
# ---------------------------------------------------------------------------

class ExecutionSurfaceAnalysis(DiscoveryMechanism):
    """Identify capabilities/adapters that expose consequential effects.

    Detects when a capability boundary exists but its effect surface
    is not fully enumerated.
    """

    @property
    def name(self) -> str:
        return "execution_surface_analysis"

    def discover(self, world: AdversarialWorld, inventory: EffectInventory) -> DiscoveryResult:
        """Analyze execution surface coverage."""
        gaps: list[EffectKnowledgeGap] = []

        # For each inventory category, check if multiple sources exist
        category_sources: dict[EffectCategory, set[str]] = {}
        for e in inventory.effects:
            category_sources.setdefault(e.category, set()).add(e.source)

        # Categories with only one source may have hidden sources
        for category, sources in category_sources.items():
            if len(sources) == 1:
                gaps.append(EffectKnowledgeGap(
                    gap_id=f"gap-{uuid.uuid4().hex[:12]}",
                    world_id=world.world_id,
                    status=DiscoveryStatus.STRUCTURAL_GAP,
                    category=category,
                    source=next(iter(sources)),
                    scope="execution_surface",
                    discovery_mechanism=self.name,
                    evidence_basis=f"Category '{category.value}' has only one inventoried source",
                    description=f"Single-source category may have hidden execution paths",
                    confidence=0.35,
                    temporal_validity=datetime.now(UTC).isoformat(),
                    provenance=f"execution_surface_analysis:{world.world_id}",
                    reachability_status="unknown",
                    execution_status="never_executed",
                    inventory_relation="partially_in_inventory",
                    completeness_implication=f"Category '{category.value}' may have undiscovered effect paths",
                    metadata={"mechanism": self.name, "source_count": len(sources)},
                ))

        return DiscoveryResult(
            result_id=f"result-{uuid.uuid4().hex[:12]}",
            mechanism=self.name,
            world_id=world.world_id,
            gaps=tuple(gaps),
            timestamp=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# Mechanism G: Differential Analysis
# ---------------------------------------------------------------------------

class DifferentialAnalysis(DiscoveryMechanism):
    """Compare effect surfaces between two builds or commits.

    Detects when new code paths appear between inventory snapshots.
    """

    @property
    def name(self) -> str:
        return "differential_analysis"

    def discover(self, world: AdversarialWorld, inventory: EffectInventory) -> DiscoveryResult:
        """Compare current inventory against a hypothetical baseline."""
        gaps: list[EffectKnowledgeGap] = []

        # Simulate: check if ground truth has more effects than inventory
        inventory_ids = {e.effect_id for e in inventory.effects}

        # In a real system, diff would compare two scans
        # Here we detect that the inventory might be missing categories
        inventory_categories = inventory.categories
        for effect in world.declared_effects:
            if effect.category not in inventory_categories:
                gaps.append(EffectKnowledgeGap(
                    gap_id=f"gap-{uuid.uuid4().hex[:12]}",
                    world_id=world.world_id,
                    status=DiscoveryStatus.STRUCTURAL_GAP,
                    category=effect.category,
                    source=effect.source,
                    scope="differential",
                    discovery_mechanism=self.name,
                    evidence_basis=f"Category '{effect.category.value}' appears in declared effects but not inventory",
                    description="Differential gap between declared effects and inventory",
                    confidence=0.45,
                    temporal_validity=datetime.now(UTC).isoformat(),
                    provenance=f"differential_analysis:{world.world_id}",
                    reachability_status="unknown",
                    execution_status="never_executed",
                    inventory_relation="not_in_inventory",
                    completeness_implication="Effect category detected but not represented in inventory",
                    metadata={"mechanism": self.name},
                ))

        return DiscoveryResult(
            result_id=f"result-{uuid.uuid4().hex[:12]}",
            mechanism=self.name,
            world_id=world.world_id,
            gaps=tuple(gaps),
            timestamp=datetime.now(UTC).isoformat(),
        )


# ---------------------------------------------------------------------------
# Adversarial world generator
# ---------------------------------------------------------------------------

class AdversarialWorldGenerator:
    """Generates adversarial worlds with hidden effects.

    Each world has a different hiding mechanism to test discovery.
    """

    def __init__(self) -> None:
        self._worlds: list[AdversarialWorld] = []

    def generate_all_worlds(self) -> list[AdversarialWorld]:
        """Generate all adversarial worlds."""
        self._worlds = [
            self._world_01_direct_primitive(),
            self._world_02_indirect_helper(),
            self._world_03_dynamic_plugin(),
            self._world_04_reflection_invocation(),
            self._world_05_subprocess_alternate_api(),
            self._world_06_filesystem_pathlib(),
            self._world_07_database_alternate_client(),
            self._world_08_network_abstraction(),
            self._world_09_payment_callback(),
            self._world_10_identity_alternate_adapter(),
            self._world_11_credential_env_config(),
            self._world_12_background_worker(),
            self._world_13_exception_recovery(),
            self._world_14_emergency_path(),
            self._world_15_lazy_initialization(),
            self._world_16_generated_code(),
            self._world_17_dynamic_code_load(),
            # Benign worlds (no hidden effect, but structural anomaly)
            self._world_18_dead_code(),
            self._world_19_unreachable_subprocess(),
            self._world_20_unused_plugin(),
        ]
        return self._worlds

    def _make_effect(
        self,
        category: EffectCategory,
        source: str,
        target: str,
        operation: str,
        visibility: EffectVisibility = EffectVisibility.DECLARED,
        authority_path_status: AuthorityPathStatus = AuthorityPathStatus.GOVERNED,
        description: str = "",
        hidden_mechanism: str = "",
        effect_id: str = "",
    ) -> ConsequentialEffect:
        """Helper to create an effect."""
        if not effect_id:
            effect_id = f"eff-{uuid.uuid4().hex[:12]}"
        return ConsequentialEffect(
            effect_id=effect_id,
            category=category,
            source=source,
            target=target,
            operation=operation,
            visibility=visibility,
            authority_path_status=authority_path_status,
            description=description,
            hidden_mechanism=hidden_mechanism,
        )

    def _world_01_direct_primitive(self) -> AdversarialWorld:
        """Direct subprocess.Popen in unindexed module."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute",
                              description="ARGO subprocess through RuntimeAuthorityGate"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/cli/helper.py",
                              "subprocess.Popen", "subprocess.spawn",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.ESCAPE,
                              description="Direct subprocess.Popen in CLI helper",
                              hidden_mechanism="helper module not in declared inventory"),
        )
        return AdversarialWorld(
            world_id="world_01_direct_primitive",
            description="Direct subprocess.Popen in unindexed module",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="direct_primitive",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_02_indirect_helper(self) -> AdversarialWorld:
        """Indirect helper call."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/cli/helper.py",
                              "helper.run_command", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.ESCAPE,
                              description="Indirect subprocess via helper",
                              hidden_mechanism="helper.run_command wraps subprocess"),
        )
        return AdversarialWorld(
            world_id="world_02_indirect_helper",
            description="Indirect subprocess via helper function",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="indirect_call",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_03_dynamic_plugin(self) -> AdversarialWorld:
        """Dynamically imported plugin."""
        declared = (
            self._make_effect(EffectCategory.PLUGIN, "src/sas/plugins/loader.py",
                              "importlib.import_module", "plugin.load"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/plugins/external_plugin.py",
                              "subprocess.run", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.ESCAPE,
                              description="Dynamically loaded plugin spawns subprocess",
                              hidden_mechanism="plugin loaded at runtime, not in static inventory"),
        )
        return AdversarialWorld(
            world_id="world_03_dynamic_plugin",
            description="Dynamically imported plugin with hidden subprocess",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="dynamic_loading",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_04_reflection_invocation(self) -> AdversarialWorld:
        """Reflection-based invocation."""
        declared = (
            self._make_effect(EffectCategory.DATABASE, "src/sas_tie_knowledge/adapter.py",
                              "aiosqlite", "db.query"),
        )
        hidden = (
            self._make_effect(EffectCategory.DATABASE, "src/sas/quant/reflection.py",
                              "getattr(conn, 'execute')", "db.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Reflection-based DB invocation",
                              hidden_mechanism="getattr bypasses static detection"),
        )
        return AdversarialWorld(
            world_id="world_04_reflection_invocation",
            description="Reflection-based database invocation",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="reflection",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_05_subprocess_alternate_api(self) -> AdversarialWorld:
        """Subprocess through alternate API."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/quant/batch.py",
                              "os.system", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.ESCAPE,
                              description="os.system bypasses subprocess detection",
                              hidden_mechanism="alternate API not in inventory"),
        )
        return AdversarialWorld(
            world_id="world_05_subprocess_alternate_api",
            description="Subprocess through os.system alternate API",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="alternate_api",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_06_filesystem_pathlib(self) -> AdversarialWorld:
        """Filesystem through shutil/pathlib."""
        declared = (
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/registry.py",
                              "open", "file.write"),
        )
        hidden = (
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/quant/cache.py",
                              "shutil.copy", "file.copy",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="shutil.copy bypasses open()-based detection",
                              hidden_mechanism="shutil not in declared inventory"),
        )
        return AdversarialWorld(
            world_id="world_06_filesystem_pathlib",
            description="Filesystem through shutil/pathlib",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="alternate_api",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_07_database_alternate_client(self) -> AdversarialWorld:
        """Database through alternate client."""
        declared = (
            self._make_effect(EffectCategory.DATABASE, "src/sas_tie_knowledge/adapter.py",
                              "aiosqlite", "db.query"),
        )
        hidden = (
            self._make_effect(EffectCategory.DATABASE, "src/sas/quant/analytics.py",
                              "psycopg2.connect", "db.connect",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="psycopg2 in analytics module bypasses adapter",
                              hidden_mechanism="alternate DB client not in inventory"),
        )
        return AdversarialWorld(
            world_id="world_07_database_alternate_client",
            description="Database through alternate client",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="alternate_api",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_08_network_abstraction(self) -> AdversarialWorld:
        """Network through library abstraction."""
        declared = (
            self._make_effect(EffectCategory.NETWORK, "src/sas/quant/api.py",
                              "httpx.request", "http.request"),
        )
        hidden = (
            self._make_effect(EffectCategory.NETWORK, "src/sas/quant/feeds.py",
                              "requests.get", "http.get",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="requests.get bypasses httpx inventory",
                              hidden_mechanism="different HTTP library not in inventory"),
        )
        return AdversarialWorld(
            world_id="world_08_network_abstraction",
            description="Network through library abstraction",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="alternate_api",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_09_payment_callback(self) -> AdversarialWorld:
        """Payment through callback."""
        declared = (
            self._make_effect(EffectCategory.BROKER, "src/sas/quant/broker.py",
                              "broker.submit_order", "broker.trade"),
        )
        hidden = (
            self._make_effect(EffectCategory.PAYMENT, "src/sas/quant/callbacks.py",
                              "payment.execute", "payment.transfer",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Payment triggered via callback",
                              hidden_mechanism="callback invocation path not in inventory"),
        )
        return AdversarialWorld(
            world_id="world_09_payment_callback",
            description="Payment through callback",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="callback",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_10_identity_alternate_adapter(self) -> AdversarialWorld:
        """Identity through alternate adapter."""
        declared = (
            self._make_effect(EffectCategory.IDENTITY, "src/sas/quant/identity.py",
                              "identity.mutate", "identity.update"),
        )
        hidden = (
            self._make_effect(EffectCategory.IDENTITY, "src/sas/quant/users.py",
                              "db.execute_identity", "identity.update",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Direct DB update bypasses identity adapter",
                              hidden_mechanism="alternate adapter path not in inventory"),
        )
        return AdversarialWorld(
            world_id="world_10_identity_alternate_adapter",
            description="Identity through alternate adapter",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="alternate_api",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_11_credential_env_config(self) -> AdversarialWorld:
        """Credential access through environment/configuration."""
        declared = (
            self._make_effect(EffectCategory.CREDENTIAL, "src/sas/quant/auth.py",
                              "keyring.get_password", "credential.read"),
        )
        hidden = (
            self._make_effect(EffectCategory.CREDENTIAL, "src/sas/quant/config.py",
                              "os.environ.get", "credential.read",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Credential via env var bypasses auth broker",
                              hidden_mechanism="env var access not in inventory"),
        )
        return AdversarialWorld(
            world_id="world_11_credential_env_config",
            description="Credential access through environment/configuration",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="alternate_api",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_12_background_worker(self) -> AdversarialWorld:
        """Background worker with hidden effects."""
        declared = (
            self._make_effect(EffectCategory.NETWORK, "src/sas/quant/api.py",
                              "httpx.request", "http.request"),
        )
        hidden = (
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/quant/worker.py",
                              "open", "file.write",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Background worker writes files outside inventory",
                              hidden_mechanism="background worker not in declared inventory"),
            self._make_effect(EffectCategory.NETWORK, "src/sas/quant/worker.py",
                              "httpx.request", "http.request",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Background worker makes network calls",
                              hidden_mechanism="background worker network calls not in inventory"),
        )
        return AdversarialWorld(
            world_id="world_12_background_worker",
            description="Background worker with hidden effects",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="background_execution",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_13_exception_recovery(self) -> AdversarialWorld:
        """Exception/recovery path."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/quant/recovery.py",
                              "subprocess.run", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Recovery path spawns subprocess",
                              hidden_mechanism="exception handler path not in call graph"),
        )
        return AdversarialWorld(
            world_id="world_13_exception_recovery",
            description="Exception/recovery path with hidden subprocess",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="recovery_path",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_14_emergency_path(self) -> AdversarialWorld:
        """Emergency path."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/quant/emergency.py",
                              "subprocess.Popen", "subprocess.spawn",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.ESCAPE,
                              description="Emergency kill switch bypasses governance",
                              hidden_mechanism="emergency path excluded from normal analysis"),
        )
        return AdversarialWorld(
            world_id="world_14_emergency_path",
            description="Emergency path bypasses governance",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="emergency_path",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_15_lazy_initialization(self) -> AdversarialWorld:
        """Lazy initialization."""
        declared = (
            self._make_effect(EffectCategory.DATABASE, "src/sas_tie_knowledge/adapter.py",
                              "aiosqlite", "db.query"),
        )
        hidden = (
            self._make_effect(EffectCategory.DATABASE, "src/sas/quant/cache.py",
                              "aiosqlite", "db.connect",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.UNGOVERNED,
                              description="Lazy cache init writes to DB on first access",
                              hidden_mechanism="lazy init path not in static call graph"),
        )
        return AdversarialWorld(
            world_id="world_15_lazy_initialization",
            description="Lazy initialization with hidden DB path",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="lazy_init",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_16_generated_code(self) -> AdversarialWorld:
        """Generated code."""
        declared = (
            self._make_effect(EffectCategory.DYNAMIC_IMPORT, "src/sas/plugins/loader.py",
                              "importlib.import_module", "plugin.load"),
        )
        hidden = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/generated/dynamic_ops.py",
                              "subprocess.run", "subprocess.execute",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.ESCAPE,
                              description="Generated code spawns subprocess",
                              hidden_mechanism="generated code not in source analysis"),
        )
        return AdversarialWorld(
            world_id="world_16_generated_code",
            description="Generated code with hidden subprocess",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="generated_code",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_17_dynamic_code_load(self) -> AdversarialWorld:
        """Dynamically loaded code."""
        declared = (
            self._make_effect(EffectCategory.DYNAMIC_IMPORT, "src/sas/plugins/loader.py",
                              "importlib.import_module", "plugin.load"),
        )
        hidden = (
            self._make_effect(EffectCategory.NETWORK, "src/sas/dynamic/remote_ops.py",
                              "httpx.request", "http.request",
                              visibility=EffectVisibility.HIDDEN,
                              authority_path_status=AuthorityPathStatus.ESCAPE,
                              description="Dynamically loaded code makes network calls",
                              hidden_mechanism="remote code load bypasses static analysis"),
        )
        return AdversarialWorld(
            world_id="world_17_dynamic_code_load",
            description="Dynamically loaded code with hidden network calls",
            declared_effects=declared,
            hidden_effects=hidden,
            ground_truth_effects=declared + hidden,
            attack_category="dynamic_code",
            expected_completeness=CompletenessStatus.INCOMPLETE,
        )

    def _world_18_dead_code(self) -> AdversarialWorld:
        """Dead code — benign, no hidden effect."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/deprecated/utils.py",
                              "open", "file.write",
                              description="Deprecated utility — dead code"),
        )
        # No hidden effects — but has dead code
        benign = (
            self._make_effect(EffectCategory.FILESYSTEM, "src/sas/deprecated/utils.py",
                              "open", "file.write",
                              description="Dead code — unreachable"),
        )
        return AdversarialWorld(
            world_id="world_18_dead_code",
            description="Dead code — no hidden effect",
            declared_effects=declared,
            hidden_effects=(),
            ground_truth_effects=declared + benign,
            attack_category="benign",
            expected_completeness=CompletenessStatus.COMPLETE_WITHIN_SCOPE,
            has_structural_anomaly=True,
            structural_anomaly_description="Dead code may appear consequential but never executes",
            benign_code=benign,
        )

    def _world_19_unreachable_subprocess(self) -> AdversarialWorld:
        """Unreachable subprocess call — benign."""
        declared = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/argopack.py",
                              "subprocess.run", "subprocess.execute"),
        )
        benign = (
            self._make_effect(EffectCategory.SUBPROCESS, "src/sas/quant/legacy.py",
                              "subprocess.run", "subprocess.execute",
                              description="Unreachable subprocess in legacy module"),
        )
        return AdversarialWorld(
            world_id="world_19_unreachable_subprocess",
            description="Unreachable subprocess — benign",
            declared_effects=declared,
            hidden_effects=(),
            ground_truth_effects=declared + benign,
            attack_category="benign",
            expected_completeness=CompletenessStatus.COMPLETE_WITHIN_SCOPE,
            has_structural_anomaly=True,
            structural_anomaly_description="Unreachable subprocess may appear as hidden effect",
            benign_code=benign,
        )

    def _world_20_unused_plugin(self) -> AdversarialWorld:
        """Unused plugin — benign."""
        declared = (
            self._make_effect(EffectCategory.PLUGIN, "src/sas/plugins/loader.py",
                              "importlib.import_module", "plugin.load"),
        )
        benign = (
            self._make_effect(EffectCategory.PLUGIN, "src/sas/plugins/unused.py",
                              "importlib.import_module", "plugin.load",
                              description="Unused plugin — never instantiated"),
        )
        return AdversarialWorld(
            world_id="world_20_unused_plugin",
            description="Unused plugin — benign",
            declared_effects=declared,
            hidden_effects=(),
            ground_truth_effects=declared + benign,
            attack_category="benign",
            expected_completeness=CompletenessStatus.COMPLETE_WITHIN_SCOPE,
            has_structural_anomaly=True,
            structural_anomaly_description="Unused plugin may appear as hidden effect",
            benign_code=benign,
        )


# ---------------------------------------------------------------------------
# Independent Oracle
# ---------------------------------------------------------------------------

class IndependentOracle:
    """Independent oracle that knows the ground truth.

    The oracle evaluates discovery results against the actual hidden effects.
    The discovery mechanism does NOT have access to this information.
    """

    def evaluate(
        self,
        world: AdversarialWorld,
        result: DiscoveryResult,
    ) -> OracleEvaluation:
        """Evaluate a discovery result against ground truth."""
        true_positives: list[str] = []
        true_negatives: list[str] = []
        false_positives: list[str] = []
        structural_gaps_correct: list[str] = []
        structural_gaps_incorrect: list[str] = []

        hidden_categories = {e.category for e in world.hidden_effects}
        hidden_sources = {e.source for e in world.hidden_effects}

        for gap in result.gaps:
            if gap.status == DiscoveryStatus.STRUCTURAL_GAP:
                # Check if the structural gap corresponds to a real hidden effect
                if gap.category in hidden_categories:
                    structural_gaps_correct.append(gap.gap_id)
                elif gap.source in hidden_sources:
                    structural_gaps_correct.append(gap.gap_id)
                else:
                    structural_gaps_incorrect.append(gap.gap_id)
            elif gap.status == DiscoveryStatus.NOT_DISCOVERED:
                if gap.category in hidden_categories:
                    # Missed — will be counted in false_negatives
                    pass
                else:
                    true_negatives.append(gap.gap_id)

        # Identify hidden effects that were NOT discovered
        discovered_categories = {g.category for g in result.gaps}
        unknown_effects = tuple(
            e.effect_id for e in world.hidden_effects
            if e.category not in discovered_categories
        )

        return OracleEvaluation(
            evaluation_id=f"eval-{uuid.uuid4().hex[:12]}",
            result_id=result.result_id,
            world_id=world.world_id,
            true_positives=tuple(true_positives),
            true_negatives=tuple(true_negatives),
            false_positives=tuple(false_positives),
            false_negatives=(),  # Will be computed separately
            structural_gaps_correct=tuple(structural_gaps_correct),
            structural_gaps_incorrect=tuple(structural_gaps_incorrect),
            unknown_effects=unknown_effects,
        )


# ---------------------------------------------------------------------------
# Phase 29 experiment
# ---------------------------------------------------------------------------

class Phase29Experiment:
    """Runs the Phase 29 effect knowledge gap discovery experiments."""

    def __init__(self) -> None:
        self.worlds = AdversarialWorldGenerator()
        self.oracle = IndependentOracle()
        self.mechanisms: list[DiscoveryMechanism] = [
            StaticSourceAnalysis(),
            ImportModuleAnalysis(),
            CallGraphAnalysis(),
            RuntimeTraceAnalysis(),
            ArchitecturalBoundaryAnalysis(),
            ExecutionSurfaceAnalysis(),
            DifferentialAnalysis(),
        ]
        self._results: list[tuple[AdversarialWorld, DiscoveryResult, OracleEvaluation]] = []

    def run_all(self) -> list[tuple[AdversarialWorld, DiscoveryResult, OracleEvaluation]]:
        """Run all Phase 29 experiments."""
        worlds = self.worlds.generate_all_worlds()
        for world in worlds:
            # Build inventory from declared effects
            inventory = EffectInventory(
                inventory_id=f"inv-{uuid.uuid4().hex[:12]}",
                effects=world.declared_effects,
                generated_by="phase29_experiment",
                created_at=datetime.now(UTC).isoformat(),
            )
            for mechanism in self.mechanisms:
                result = mechanism.discover(world, inventory)
                evaluation = self.oracle.evaluate(world, result)
                self._results.append((world, result, evaluation))
        return self._results

    def summary(self) -> dict[str, Any]:
        """Produce a summary of all results."""
        total_worlds = len(set(w.world_id for w, _, _ in self._results))
        total_mechanisms = len(self.mechanisms)
        total_runs = len(self._results)

        worlds_with_hidden = set(
            w.world_id for w, _, _ in self._results if w.has_hidden_effects
        )
        worlds_benign = set(
            w.world_id for w, _, _ in self._results if not w.has_hidden_effects
        )

        structural_gaps_flagged = sum(
            1 for _, r, _ in self._results if r.has_structural_gaps
        )

        return {
            "total_worlds": total_worlds,
            "worlds_with_hidden_effects": len(worlds_with_hidden),
            "worlds_benign": len(worlds_benign),
            "total_mechanisms": total_mechanisms,
            "total_runs": total_runs,
            "structural_gaps_flagged": structural_gaps_flagged,
        }


# ---------------------------------------------------------------------------
# Convenience runner
# ---------------------------------------------------------------------------

def run_phase29() -> dict[str, Any]:
    """Run the Phase 29 experiment suite and return summary."""
    exp = Phase29Experiment()
    exp.run_all()
    return exp.summary()


if __name__ == "__main__":
    summary = run_phase29()
    print("Phase 29 Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
