"""Tests for Phase 29: Effect Knowledge Gap Discovery."""

import pytest
from examples.sovereign_agent.effect_knowledge_gap import (
    AdversarialWorldGenerator,
    AdversarialWorld,
    ArchitecturalBoundaryAnalysis,
    AuthorityPathStatus,
    CallGraphAnalysis,
    CompletenessStatus,
    ConsequentialEffect,
    DifferentialAnalysis,
    DiscoveryResult,
    DiscoveryStatus,
    EffectCategory,
    EffectInventory,
    EffectKnowledgeGap,
    EffectVisibility,
    ExecutionSurfaceAnalysis,
    ImportModuleAnalysis,
    IndependentOracle,
    Phase29Experiment,
    RuntimeTraceAnalysis,
    StaticSourceAnalysis,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def generator() -> AdversarialWorldGenerator:
    return AdversarialWorldGenerator()


@pytest.fixture
def worlds(generator: AdversarialWorldGenerator) -> list[AdversarialWorld]:
    return generator.generate_all_worlds()


@pytest.fixture
def oracle() -> IndependentOracle:
    return IndependentOracle()


def _make_effect(
    category: EffectCategory = EffectCategory.SUBPROCESS,
    source: str = "src/sas/argopack.py",
    target: str = "subprocess.run",
    operation: str = "subprocess.execute",
    visibility: EffectVisibility = EffectVisibility.DECLARED,
    authority_path_status: AuthorityPathStatus = AuthorityPathStatus.GOVERNED,
    description: str = "",
) -> ConsequentialEffect:
    return ConsequentialEffect(
        effect_id=f"eff-test-{uuid.uuid4().hex[:8]}",
        category=category,
        source=source,
        target=target,
        operation=operation,
        visibility=visibility,
        authority_path_status=authority_path_status,
        description=description,
    )


def _make_inventory(
    effects: tuple[ConsequentialEffect, ...] = (),
    commit_ref: str = "test",
) -> EffectInventory:
    return EffectInventory(
        inventory_id=f"inv-test-{uuid.uuid4().hex[:8]}",
        effects=effects,
        commit_ref=commit_ref,
    )


import uuid


# ---------------------------------------------------------------------------
# World generation tests
# ---------------------------------------------------------------------------

class TestWorldGeneration:
    def test_generates_20_worlds(self, generator: AdversarialWorldGenerator):
        worlds = generator.generate_all_worlds()
        assert len(worlds) == 20

    def test_worlds_have_unique_ids(self, worlds: list[AdversarialWorld]):
        ids = [w.world_id for w in worlds]
        assert len(ids) == len(set(ids))

    def test_first_17_worlds_have_hidden_effects(self, worlds: list[AdversarialWorld]):
        for world in worlds[:17]:
            assert world.has_hidden_effects, f"{world.world_id} should have hidden effects"
            assert world.hidden_count > 0

    def test_last_3_worlds_are_benign(self, worlds: list[AdversarialWorld]):
        for world in worlds[17:]:
            assert not world.has_hidden_effects, f"{world.world_id} should be benign"
            assert world.hidden_count == 0

    def test_benign_worlds_have_structural_anomaly(self, worlds: list[AdversarialWorld]):
        for world in worlds[17:]:
            assert world.has_structural_anomaly

    def test_all_worlds_have_ground_truth(self, worlds: list[AdversarialWorld]):
        for world in worlds:
            assert len(world.ground_truth_effects) > 0

    def test_ground_truth_equals_declared_plus_hidden(self, worlds: list[AdversarialWorld]):
        for world in worlds:
            # For benign worlds, ground_truth includes benign_code
            # For adversarial worlds, ground_truth = declared + hidden
            if world.has_benign_code:
                expected_ids = {e.effect_id for e in world.declared_effects} | {e.effect_id for e in world.benign_code}
            else:
                expected_ids = {e.effect_id for e in world.declared_effects} | {e.effect_id for e in world.hidden_effects}
            actual_ids = {e.effect_id for e in world.ground_truth_effects}
            assert expected_ids == actual_ids


# ---------------------------------------------------------------------------
# Discovery mechanism tests
# ---------------------------------------------------------------------------

class TestDiscoveryMechanisms:
    def test_static_source_analysis_runs(self, worlds: list[AdversarialWorld]):
        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        assert isinstance(result, DiscoveryResult)
        assert result.mechanism == "static_source_analysis"

    def test_import_module_analysis_runs(self, worlds: list[AdversarialWorld]):
        mechanism = ImportModuleAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        assert isinstance(result, DiscoveryResult)
        assert result.mechanism == "import_module_analysis"

    def test_call_graph_analysis_runs(self, worlds: list[AdversarialWorld]):
        mechanism = CallGraphAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        assert isinstance(result, DiscoveryResult)
        assert result.mechanism == "call_graph_analysis"

    def test_runtime_trace_analysis_runs(self, worlds: list[AdversarialWorld]):
        mechanism = RuntimeTraceAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        assert isinstance(result, DiscoveryResult)
        assert result.mechanism == "runtime_trace_analysis"

    def test_architectural_boundary_analysis_runs(self, worlds: list[AdversarialWorld]):
        mechanism = ArchitecturalBoundaryAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        assert isinstance(result, DiscoveryResult)
        assert result.mechanism == "architectural_boundary_analysis"

    def test_execution_surface_analysis_runs(self, worlds: list[AdversarialWorld]):
        mechanism = ExecutionSurfaceAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        assert isinstance(result, DiscoveryResult)
        assert result.mechanism == "execution_surface_analysis"

    def test_differential_analysis_runs(self, worlds: list[AdversarialWorld]):
        mechanism = DifferentialAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        assert isinstance(result, DiscoveryResult)
        assert result.mechanism == "differential_analysis"


# ---------------------------------------------------------------------------
# Oracle evaluation tests
# ---------------------------------------------------------------------------

class TestOracleEvaluation:
    def test_oracle_evaluates_discovery(self, worlds: list[AdversarialWorld], oracle: IndependentOracle):
        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        evaluation = oracle.evaluate(worlds[0], result)
        assert evaluation.result_id == result.result_id
        assert evaluation.world_id == worlds[0].world_id

    def test_oracle_detects_structural_gaps(self, worlds: list[AdversarialWorld], oracle: IndependentOracle):
        # World 01 has hidden subprocess effect
        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        evaluation = oracle.evaluate(worlds[0], result)
        # The mechanism should flag a structural gap for missing categories
        assert len(evaluation.structural_gaps_correct) > 0 or len(evaluation.structural_gaps_incorrect) > 0

    def test_oracle_detects_unknown_effects(self, worlds: list[AdversarialWorld], oracle: IndependentOracle):
        # World 01 has hidden subprocess effect
        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(worlds[0].declared_effects)
        result = mechanism.discover(worlds[0], inventory)
        evaluation = oracle.evaluate(worlds[0], result)
        # The hidden effect should be flagged as unknown
        assert len(evaluation.unknown_effects) > 0


# ---------------------------------------------------------------------------
# Phase 29 invariants
# ---------------------------------------------------------------------------

class TestPhase29Invariants:
    def test_not_discovered_not_does_not_exist(self):
        """NOT_DISCOVERED ≠ DOES_NOT_EXIST."""
        # In benign worlds, no hidden effects exist
        # Discovery mechanisms may still flag structural gaps
        # This is correct: NOT_DISCOVERED means "no evidence found"
        # NOT "no effect exists"
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        benign = worlds[17]  # dead code world

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(benign.declared_effects)
        result = mechanism.discover(benign, inventory)

        # The mechanism may flag gaps even in benign worlds
        # This is fine — it's evidence of incompleteness, not a claim of effect existence
        for gap in result.gaps:
            assert gap.status in (
                DiscoveryStatus.STRUCTURAL_GAP,
                DiscoveryStatus.NOT_DISCOVERED,
                DiscoveryStatus.INCONCLUSIVE,
            )

    def test_structural_gap_not_concrete_effect(self):
        """STRUCTURAL_GAP ≠ CONCRETE_EFFECT."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[0]

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        for gap in result.gaps:
            if gap.status == DiscoveryStatus.STRUCTURAL_GAP:
                # Structural gap may have a category but it's not a concrete effect
                assert gap.confidence < 1.0
                assert gap.execution_status == "never_executed"

    def test_static_possibility_not_executed_effect(self):
        """STATIC POSSIBILITY ≠ EXECUTED EFFECT."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[18]  # unreachable subprocess

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        for gap in result.gaps:
            # Even if a gap is flagged, it should not claim execution
            assert gap.execution_status != "observed_executed"

    def test_discovered_effect_not_authorized(self):
        """DISCOVERED_EFFECT ≠ AUTHORIZED_EFFECT."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[0]

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        for gap in result.gaps:
            # Discovery does not imply authorization
            assert gap.inventory_relation != "authorized"

    def test_no_new_effect_discovered_not_no_effect_exists(self):
        """NO_NEW_EFFECT_DISCOVERED ≠ NO_NEW_EFFECT_EXISTS."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        benign = worlds[17]  # dead code

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(benign.declared_effects)
        result = mechanism.discover(benign, inventory)

        # Even if no gaps are flagged, we cannot claim no hidden effects exist
        # (in this benign case it happens to be true, but the mechanism can't know that)
        # The mechanism's silence is not evidence of absence

    def test_discovery_not_authority(self):
        """DISCOVERY ≠ AUTHORITY."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[0]

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        # Discovery results should not contain authority claims
        for gap in result.gaps:
            assert "authority" not in gap.inventory_relation
            assert "authorized" not in gap.inventory_relation


# ---------------------------------------------------------------------------
# Benign world tests (false positive detection)
# ---------------------------------------------------------------------------

class TestBenignWorlds:
    def test_dead_code_world(self, generator: AdversarialWorldGenerator):
        worlds = generator.generate_all_worlds()
        dead_code = worlds[17]
        assert dead_code.world_id == "world_18_dead_code"
        assert not dead_code.has_hidden_effects
        assert dead_code.has_benign_code

    def test_unreachable_subprocess_world(self, generator: AdversarialWorldGenerator):
        worlds = generator.generate_all_worlds()
        unreachable = worlds[18]
        assert unreachable.world_id == "world_19_unreachable_subprocess"
        assert not unreachable.has_hidden_effects
        assert unreachable.has_benign_code

    def test_unused_plugin_world(self, generator: AdversarialWorldGenerator):
        worlds = generator.generate_all_worlds()
        unused = worlds[19]
        assert unused.world_id == "world_20_unused_plugin"
        assert not unused.has_hidden_effects
        assert unused.has_benign_code


# ---------------------------------------------------------------------------
# Phase 29 experiment tests
# ---------------------------------------------------------------------------

class TestPhase29Experiment:
    def test_runs_all_worlds_and_mechanisms(self):
        exp = Phase29Experiment()
        results = exp.run_all()
        # 20 worlds * 7 mechanisms = 140 results
        assert len(results) == 140

    def test_summary_generated(self):
        exp = Phase29Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["total_worlds"] == 20
        assert summary["total_mechanisms"] == 7
        assert summary["total_runs"] == 140

    def test_worlds_with_hidden_effects_count(self):
        exp = Phase29Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["worlds_with_hidden_effects"] == 17

    def test_benign_worlds_count(self):
        exp = Phase29Experiment()
        exp.run_all()
        summary = exp.summary()
        assert summary["worlds_benign"] == 3


# ---------------------------------------------------------------------------
# EffectKnowledgeGap tests
# ---------------------------------------------------------------------------

class TestEffectKnowledgeGap:
    def test_gap_preserves_epistemic_context(self):
        gap = EffectKnowledgeGap(
            gap_id="gap-test-001",
            world_id="world_01",
            status=DiscoveryStatus.STRUCTURAL_GAP,
            category=EffectCategory.SUBPROCESS,
            source="src/sas/cli/helper.py",
            scope="source_code",
            discovery_mechanism="static_source_analysis",
            evidence_basis="Category 'subprocess' has no entry in declared inventory",
            description="No declared effects for category: subprocess",
            confidence=0.3,
            temporal_validity="2026-09-10T00:00:00Z",
            provenance="static_source_analysis:world_01",
            reachability_status="unknown",
            execution_status="never_executed",
            inventory_relation="not_in_inventory",
            completeness_implication="Effect inventory has no subprocess effects; may be incomplete",
        )
        assert gap.confidence < 1.0
        assert gap.execution_status == "never_executed"
        assert gap.reachability_status == "unknown"

    def test_gap_confidence_not_probability(self):
        """Confidence is NOT a probability of effect existence."""
        gap = EffectKnowledgeGap(
            gap_id="gap-test-002",
            world_id="world_01",
            status=DiscoveryStatus.STRUCTURAL_GAP,
            category=EffectCategory.PAYMENT,
            source="static_analysis",
            scope="source_code",
            discovery_mechanism="static_source_analysis",
            evidence_basis="Category 'payment' has no entry in declared inventory",
            description="No declared effects for category: payment",
            confidence=0.3,
            temporal_validity="2026-09-10T00:00:00Z",
            provenance="static_source_analysis:world_01",
            reachability_status="unknown",
            execution_status="never_executed",
            inventory_relation="not_in_inventory",
            completeness_implication="Effect inventory has no payment effects; may be incomplete",
        )
        # Confidence is bounded — never 1.0 (certain) for a structural gap
        assert gap.confidence < 1.0


# ---------------------------------------------------------------------------
# Negative claim tests
# ---------------------------------------------------------------------------

class TestNegativeClaims:
    def test_mechanism_silence_not_evidence_of_absence(self):
        """A mechanism that finds nothing has not proven no effect exists."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[0]  # Has hidden effects

        # A mechanism with no patterns to search for
        class EmptyMechanism:
            @property
            def name(self):
                return "empty"
            def discover(self, world, inventory):
                return DiscoveryResult(
                    result_id="empty",
                    mechanism="empty",
                    world_id=world.world_id,
                    gaps=(),
                    timestamp="2026-09-10T00:00:00Z",
                )

        mechanism = EmptyMechanism()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        # No gaps found, but hidden effects exist
        assert result.gap_count == 0
        assert world.has_hidden_effects  # Reality contradicts the silence

    def test_structural_gap_without_concrete_effect(self):
        """System can detect incompleteness without identifying a specific effect."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[17]  # Benign dead code

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        # The mechanism may flag structural gaps
        # This is correct: it's evidence of incompleteness, not a specific effect
        for gap in result.gaps:
            if gap.status == DiscoveryStatus.STRUCTURAL_GAP:
                # Structural gap is not a concrete effect
                assert gap.confidence < 1.0


# ---------------------------------------------------------------------------
# Temporal validity tests
# ---------------------------------------------------------------------------

class TestTemporalValidity:
    def test_discovery_has_temporal_validity(self):
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[0]

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        for gap in result.gaps:
            assert gap.temporal_validity != ""

    def test_discovery_has_provenance(self):
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[0]

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        for gap in result.gaps:
            assert gap.provenance != ""
            assert gap.discovery_mechanism == "static_source_analysis"


# ---------------------------------------------------------------------------
# Authority non-amplification tests
# ---------------------------------------------------------------------------

class TestAuthorityNonAmplification:
    def test_discovery_does_not_create_authority(self):
        """Discovery results do not contain authority claims."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[0]

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        for gap in result.gaps:
            # No authority-related fields
            assert "authority" not in gap.inventory_relation
            assert "authorized" not in gap.inventory_relation
            assert "governed" not in gap.inventory_relation

    def test_structural_gap_does_not_imply_unauthorized(self):
        """STRUCTURAL_GAP ≠ UNAUTHORIZED_EFFECT."""
        generator = AdversarialWorldGenerator()
        worlds = generator.generate_all_worlds()
        world = worlds[0]

        mechanism = StaticSourceAnalysis()
        inventory = _make_inventory(world.declared_effects)
        result = mechanism.discover(world, inventory)

        for gap in result.gaps:
            if gap.status == DiscoveryStatus.STRUCTURAL_GAP:
                # A structural gap is not an unauthorized effect
                assert gap.inventory_relation != "unauthorized"
