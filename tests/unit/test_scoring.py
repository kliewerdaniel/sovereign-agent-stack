"""Tests for sovereignty scoring engine."""

import pytest

from sas.core.config import (
    AuthBroker,
    LongTermProvider,
    MemoryProvider,
    ModelConfig,
    Ownership,
    SASConfig,
    SubstrateType,
)
from sas.core.scoring import (
    LayerID,
    compute_score,
    generate_report,
    score_config,
)


class TestScoreConfig:
    """Tests for the layer scoring function."""

    def test_fully_sovereign_config(self) -> None:
        """A fully sovereign config scores 6/8."""
        config = SASConfig(
            model_primary=ModelConfig(provider="ollama", name="llama3.1:8b", location="local"),
            substrate=SubstrateType.LOCAL_DOCKER,
            memory_short_term=MemoryProvider.LOCAL_RAG,
            memory_long_term=LongTermProvider.COMPILE_TIME_GRAPH,
            auth_broker=AuthBroker.LOCAL_MCP_GATEWAY,
        )
        layers = score_config(config)

        # Exclude identity and payments (unavoidable)
        scorable = [l for l in layers if not l.unavoidable_rental]
        owned = [l for l in scorable if l.scored_as == Ownership.OWNED]

        assert len(owned) == 6
        assert len(scorable) == 6

    def test_rented_config(self) -> None:
        """A fully rented config scores lower."""
        config = SASConfig(
            model_primary=None,
            substrate=SubstrateType.ORGO_CLOUD,
            memory_short_term=MemoryProvider.HONCHO_CLOUD,
            memory_long_term=LongTermProvider.RETRIEVAL_ONLY,
            auth_broker=AuthBroker.COMPOSIO,
        )
        layers = score_config(config)

        scorable = [l for l in layers if not l.unavoidable_rental]
        owned = [l for l in scorable if l.scored_as == Ownership.OWNED]

        # Harness is always owned (ARGO), everything else rented
        assert len(owned) == 1

    def test_manual_override(self) -> None:
        """Manual overrides should be respected."""
        config = SASConfig(
            memory_short_term=MemoryProvider.HONCHO_CLOUD,  # Would be rented
            overrides={"layer_5": Ownership.OWNED},  # Override to owned
        )
        layers = score_config(config)

        layer_5 = next(l for l in layers if l.layer_id == LayerID.SHORT_TERM_MEMORY)
        assert layer_5.scored_as == Ownership.OWNED
        assert "MANUAL OVERRIDE" in layer_5.reasoning

    def test_unavoidable_rentals_flagged(self) -> None:
        """Identity and payments should be flagged as unavoidable."""
        config = SASConfig()
        layers = score_config(config)

        identity = next(l for l in layers if l.layer_id == LayerID.IDENTITY)
        payments = next(l for l in layers if l.layer_id == LayerID.PAYMENTS)

        assert identity.unavoidable_rental is True
        assert payments.unavoidable_rental is True


class TestComputeScore:
    """Tests for the score computation."""

    def test_full_score(self) -> None:
        """All layers owned = 1.0."""
        from sas.core.scoring import LayerScore
        layers = [
            LayerScore(
                layer_id=LayerID.MODEL,
                name="Model",
                ownership=Ownership.OWNED,
                scored_as=Ownership.OWNED,
                reasoning="test",
            ),
            LayerScore(
                layer_id=LayerID.COMPUTE,
                name="Compute",
                ownership=Ownership.OWNED,
                scored_as=Ownership.OWNED,
                reasoning="test",
            ),
        ]
        owned, total, score = compute_score(layers)
        assert score == 1.0

    def test_half_score(self) -> None:
        """Half owned = 0.5."""
        from sas.core.scoring import LayerScore
        layers = [
            LayerScore(
                layer_id=LayerID.MODEL,
                name="Model",
                ownership=Ownership.OWNED,
                scored_as=Ownership.OWNED,
                reasoning="test",
            ),
            LayerScore(
                layer_id=LayerID.COMPUTE,
                name="Compute",
                ownership=Ownership.RENTED,
                scored_as=Ownership.RENTED,
                reasoning="test",
            ),
        ]
        owned, total, score = compute_score(layers)
        assert score == 0.5

    def test_unavoidable_excluded(self) -> None:
        """Unavoidable rentals are excluded from score."""
        from sas.core.scoring import LayerScore
        layers = [
            LayerScore(
                layer_id=LayerID.MODEL,
                name="Model",
                ownership=Ownership.OWNED,
                scored_as=Ownership.OWNED,
                reasoning="test",
            ),
            LayerScore(
                layer_id=LayerID.IDENTITY,
                name="Identity",
                ownership=Ownership.RENTED,
                scored_as=Ownership.RENTED,
                reasoning="test",
                unavoidable_rental=True,
            ),
        ]
        owned, total, score = compute_score(layers)
        assert total == 1  # Identity excluded
        assert score == 1.0


class TestGenerateReport:
    """Tests for the full report generation."""

    def test_report_structure(self) -> None:
        """Report should have all expected fields."""
        config = SASConfig()
        report = generate_report(config)

        assert report.timestamp is not None
        assert len(report.layers) == 8
        assert report.score >= 0.0
        assert report.score <= 1.0
        assert report.verdict in ["Fully sovereign", "Sovereign (target)", "Partially sovereign", "Rented"]

    def test_report_with_previous_score(self) -> None:
        """Report should compute drift when previous score is provided."""
        config = SASConfig()
        report = generate_report(config, previous_score=0.5)

        assert report.previous_score == 0.5
        assert report.drift is not None
        assert report.drift == report.score - 0.5

    def test_sovereign_verdict(self) -> None:
        """A config with all layers owned should have 'Sovereign' verdict."""
        config = SASConfig(
            model_primary=ModelConfig(provider="ollama", name="llama3.1:8b", location="local"),
            substrate=SubstrateType.LOCAL_DOCKER,
            memory_short_term=MemoryProvider.LOCAL_RAG,
            memory_long_term=LongTermProvider.COMPILE_TIME_GRAPH,
            auth_broker=AuthBroker.LOCAL_MCP_GATEWAY,
        )
        report = generate_report(config)
        assert "Sovereign" in report.verdict or "sovereign" in report.verdict
