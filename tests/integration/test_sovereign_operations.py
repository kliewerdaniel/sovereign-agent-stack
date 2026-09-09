"""Integration tests for the Sovereign Operations Agent.

Tests the complete protocol loop:
    Observation → Hypothesis → Evidence → Epistemic Evaluation →
    Recommendation → Governance → Authorization → Capability →
    Verification → Execution → Receipt → Provenance
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from examples.sovereign_operations.agent import SovereignOperationsAgent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def ops_dir() -> Path:
    """Get the sovereign operations directory."""
    return Path(__file__).resolve().parent.parent.parent / "examples" / "sovereign_operations"


@pytest.fixture
def data_dir(ops_dir: Path) -> Path:
    return ops_dir / "data"


@pytest.fixture
def knowledge_dir(ops_dir: Path) -> Path:
    return ops_dir / "knowledge"


@pytest.fixture
def policy_path(ops_dir: Path) -> Path:
    return ops_dir / "policies" / "governance.json"


@pytest.fixture
def agent(data_dir: Path, knowledge_dir: Path, policy_path: Path) -> SovereignOperationsAgent:
    return SovereignOperationsAgent(
        data_dir=data_dir,
        knowledge_dir=knowledge_dir,
        policy_path=policy_path,
    )


# ---------------------------------------------------------------------------
# Epistemic Tests
# ---------------------------------------------------------------------------


class TestEpistemic:
    """Tests for epistemic evaluation."""

    def test_supported_evidence(self, agent: SovereignOperationsAgent):
        """Supported evidence → SUPPORTED state."""
        trace = agent.investigate("TICKET-001")
        assert trace["epistemic_state"]["state"] == "SUPPORTED"

    def test_refuted_evidence(self, agent: SovereignOperationsAgent):
        """Fulfilled order → REFUTED state."""
        trace = agent.investigate("TICKET-002")
        assert trace["epistemic_state"]["state"] == "REFUTED"

    def test_evidence_gathering(self, agent: SovereignOperationsAgent):
        """Evidence is gathered from multiple sources."""
        trace = agent.investigate("TICKET-001")
        evidence_types = [e["evidence_type"] for e in trace["evidence"]]
        assert "payment_transaction" in evidence_types
        assert "order_record" in evidence_types
        assert "fulfillment_record" in evidence_types
        assert "customer_record" in evidence_types


# ---------------------------------------------------------------------------
# Governance Tests
# ---------------------------------------------------------------------------


class TestGovernance:
    """Tests for governance evaluation."""

    def test_policy_satisfied(self, agent: SovereignOperationsAgent):
        """Policy satisfied → approved."""
        trace = agent.investigate("TICKET-001")
        assert trace["governance_decision"]["approved"] is True

    def test_policy_violated_fulfilled(self, agent: SovereignOperationsAgent):
        """Fulfilled order → rejected."""
        trace = agent.investigate("TICKET-002")
        assert trace["governance_decision"]["approved"] is False

    def test_threshold_exceeded(self, agent: SovereignOperationsAgent):
        """Amount > threshold → rejected."""
        trace = agent.investigate("TICKET-003")
        assert trace["governance_decision"]["approved"] is False
        assert "threshold" in trace["governance_decision"]["reason"].lower()


# ---------------------------------------------------------------------------
# Authorization Tests
# ---------------------------------------------------------------------------


class TestAuthorization:
    """Tests for authorization derivation."""

    def test_authorization_derived(self, agent: SovereignOperationsAgent):
        """Authorization is derived from governance decision."""
        trace = agent.investigate("TICKET-001")
        if trace["governance_decision"]["approved"]:
            assert trace["authorization"] is not None
            assert "authorization_id" in trace["authorization"]

    def test_no_authorization_when_rejected(self, agent: SovereignOperationsAgent):
        """No authorization when governance rejects."""
        trace = agent.investigate("TICKET-002")
        assert trace["authorization"] is None


# ---------------------------------------------------------------------------
# Capability Tests
# ---------------------------------------------------------------------------


class TestCapability:
    """Tests for capability materialization."""

    def test_capability_materialized(self, agent: SovereignOperationsAgent):
        """Capability is materialized from authorization."""
        trace = agent.investigate("TICKET-001")
        if trace["authorization"]:
            assert trace["capability"] is not None
            assert "capability_id" in trace["capability"]

    def test_capability_bounds_amount(self, agent: SovereignOperationsAgent):
        """Capability bounds the refund amount."""
        trace = agent.investigate("TICKET-001")
        if trace["capability"]:
            assert trace["capability"]["constraints"]["max_quantity"] == 17.42


# ---------------------------------------------------------------------------
# Execution Tests
# ---------------------------------------------------------------------------


class TestExecution:
    """Tests for execution."""

    def test_refund_executed(self, agent: SovereignOperationsAgent):
        """Refund is executed when authorized."""
        trace = agent.investigate("TICKET-001")
        if trace["result"] == "COMPLETED":
            assert trace["execution"]["status"] == "completed"
            assert trace["receipt"] is not None

    def test_no_execution_when_rejected(self, agent: SovereignOperationsAgent):
        """No execution when governance rejects."""
        trace = agent.investigate("TICKET-002")
        assert trace["result"] == "REJECTED"
        assert "execution" not in trace or trace["execution"] is None


# ---------------------------------------------------------------------------
# Provenance Tests
# ---------------------------------------------------------------------------


class TestProvenance:
    """Tests for provenance recording."""

    def test_provenance_recorded(self, agent: SovereignOperationsAgent):
        """Provenance is recorded for every investigation."""
        trace = agent.investigate("TICKET-001")
        assert "provenance_id" in trace

    def test_provenance_contains_trace(self, agent: SovereignOperationsAgent):
        """Provenance contains the complete trace."""
        trace = agent.investigate("TICKET-001")
        provenance = agent.get_provenance()
        assert len(provenance) > 0
        assert provenance[-1]["trace"]["ticket_id"] == "TICKET-001"


# ---------------------------------------------------------------------------
# Full Protocol Tests
# ---------------------------------------------------------------------------


class TestFullProtocol:
    """Tests for the complete protocol loop."""

    def test_complete_loop(self, agent: SovereignOperationsAgent):
        """Complete protocol loop for a valid refund."""
        trace = agent.investigate("TICKET-001")

        # Verify all steps are present
        assert "observations" in trace
        assert "hypotheses" in trace
        assert "evidence" in trace
        assert "epistemic_state" in trace
        assert "recommendation" in trace
        assert "governance_decision" in trace
        assert "authorization" in trace
        assert "capability" in trace
        assert "verification" in trace
        assert "execution" in trace
        assert "receipt" in trace
        assert "provenance_id" in trace

    def test_rejected_loop(self, agent: SovereignOperationsAgent):
        """Rejected protocol loop for an invalid refund."""
        trace = agent.investigate("TICKET-002")

        # Verify rejection path
        assert trace["result"] == "REJECTED"
        assert trace["governance_decision"]["approved"] is False
        assert trace["authorization"] is None
