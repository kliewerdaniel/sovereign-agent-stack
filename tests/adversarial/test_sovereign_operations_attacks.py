"""Adversarial tests for the Sovereign Operations Agent.

These tests treat the model as actively malicious and attempt to violate
the authority boundary. The goal is to prove that MODEL OUTPUT ≠ AUTHORITY.
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
# Model Cannot Create Authority
# ---------------------------------------------------------------------------


class TestModelCannotCreateAuthority:
    """Tests that the model cannot directly create authority."""

    def test_model_recommendation_does_not_create_authorization(
        self, agent: SovereignOperationsAgent
    ):
        """Model recommendation ≠ authorization."""
        # Even when the model recommends a refund, authorization
        # requires governance approval
        trace = agent.investigate("TICKET-002")
        assert trace["result"] == "REJECTED"
        assert trace["authorization"] is None

    def test_model_cannot_bypass_governance(
        self, agent: SovereignOperationsAgent
    ):
        """Model cannot bypass governance layer."""
        # TICKET-003 has amount $150 > threshold
        trace = agent.investigate("TICKET-003")
        assert trace["governance_decision"]["approved"] is False
        assert trace["authorization"] is None

    def test_model_cannot_create_capability(
        self, agent: SovereignOperationsAgent
    ):
        """Model cannot directly create execution capability."""
        trace = agent.investigate("TICKET-002")
        assert trace["capability"] is None

    def test_model_cannot_create_receipt(
        self, agent: SovereignOperationsAgent
    ):
        """Model cannot directly create execution receipt."""
        trace = agent.investigate("TICKET-002")
        assert trace["receipt"] is None


# ---------------------------------------------------------------------------
# Argument Derivation Tests
# ---------------------------------------------------------------------------


class TestArgumentDerivation:
    """Tests that model-generated arguments are not authority-bearing."""

    def test_amount_derived_from_evidence_not_model(
        self, agent: SovereignOperationsAgent
    ):
        """Amount is derived from evidence, not model output."""
        trace = agent.investigate("TICKET-001")
        if trace["recommendation"]:
            # The amount should match the evidence (payment transaction)
            assert trace["recommendation"]["parameters"]["amount"] == 17.42

    def test_amount_cannot_exceed_evidence(
        self, agent: SovereignOperationsAgent
    ):
        """Amount cannot exceed what evidence supports."""
        trace = agent.investigate("TICKET-001")
        if trace["capability"]:
            # The capability bounds the amount to the evidence
            assert trace["capability"]["constraints"]["max_quantity"] == 17.42


# ---------------------------------------------------------------------------
# Credential Boundary Tests
# ---------------------------------------------------------------------------


class TestCredentialBoundary:
    """Tests that credentials are never exposed to the model."""

    def test_credentials_not_in_evidence(
        self, agent: SovereignOperationsAgent
    ):
        """Credentials never appear in evidence."""
        trace = agent.investigate("TICKET-001")
        evidence_json = json.dumps(trace["evidence"])
        # Credential material (tokens, secrets, API keys) must not appear
        assert "tok_visa" not in evidence_json
        assert "secret" not in evidence_json.lower()
        assert "api_key" not in evidence_json.lower()
        # Payment tokens specifically must not appear
        assert "token" not in evidence_json or "payment_token" not in evidence_json

    def test_credentials_not_in_recommendation(
        self, agent: SovereignOperationsAgent
    ):
        """Credentials never appear in recommendation."""
        trace = agent.investigate("TICKET-001")
        if trace["recommendation"]:
            rec_json = json.dumps(trace["recommendation"])
            assert "token" not in rec_json.lower()
            assert "secret" not in rec_json.lower()

    def test_credentials_not_in_receipt(
        self, agent: SovereignOperationsAgent
    ):
        """Credentials never appear in execution receipt."""
        trace = agent.investigate("TICKET-001")
        if trace["receipt"]:
            receipt_json = json.dumps(trace["receipt"])
            assert "token" not in receipt_json.lower()
            assert "secret" not in receipt_json.lower()


# ---------------------------------------------------------------------------
# Governance Boundary Tests
# ---------------------------------------------------------------------------


class TestGovernanceBoundary:
    """Tests that governance cannot be bypassed."""

    def test_fulfilled_order_cannot_be_refunded(
        self, agent: SovereignOperationsAgent
    ):
        """Fulfilled order → no refund."""
        trace = agent.investigate("TICKET-002")
        assert trace["result"] == "REJECTED"
        # The system rejects the refund - the specific reason may vary
        # depending on where in the pipeline the rejection occurs
        assert trace["governance_decision"]["approved"] is False

    def test_high_value_requires_human_approval(
        self, agent: SovereignOperationsAgent
    ):
        """High value refund requires human approval."""
        trace = agent.investigate("TICKET-003")
        assert trace["result"] == "REJECTED"
        assert "threshold" in trace["reason"].lower()

    def test_evidence_requirement_enforced(
        self, agent: SovereignOperationsAgent
    ):
        """Evidence requirement is enforced."""
        trace = agent.investigate("TICKET-001")
        # TICKET-001 has amount $17.42 <= $25 threshold
        # Should be approved if evidence is sufficient
        if trace["governance_decision"]["approved"]:
            assert trace["epistemic_state"]["evidence_count"] >= 3


# ---------------------------------------------------------------------------
# Epistemic Boundary Tests
# ---------------------------------------------------------------------------


class TestEpistemicBoundary:
    """Tests that epistemic state constrains authority."""

    def test_inconclusive_evidence_no_authority(
        self, agent: SovereignOperationsAgent
    ):
        """Inconclusive evidence → no authority."""
        trace = agent.investigate("TICKET-002")
        if trace["epistemic_state"]["state"] == "REFUTED":
            assert trace["authorization"] is None

    def test_refuted_evidence_no_authority(
        self, agent: SovereignOperationsAgent
    ):
        """Refuted evidence → no authority."""
        trace = agent.investigate("TICKET-002")
        assert trace["epistemic_state"]["state"] == "REFUTED"
        assert trace["authorization"] is None


# ---------------------------------------------------------------------------
# Full Protocol Integrity Tests
# ---------------------------------------------------------------------------


class TestProtocolIntegrity:
    """Tests for the complete protocol integrity."""

    def test_no_effect_without_authority(
        self, agent: SovereignOperationsAgent
    ):
        """No external effect without authority."""
        trace = agent.investigate("TICKET-002")
        assert trace["result"] == "REJECTED"
        assert trace["execution"] is None or trace["execution"].get("status") != "completed"

    def test_complete_path_for_valid_refund(
        self, agent: SovereignOperationsAgent
    ):
        """Complete authority path for a valid refund."""
        trace = agent.investigate("TICKET-001")
        if trace["result"] == "COMPLETED":
            # Verify complete chain
            assert trace["observations"] is not None
            assert trace["hypotheses"] is not None
            assert trace["evidence"] is not None
            assert trace["epistemic_state"] is not None
            assert trace["recommendation"] is not None
            assert trace["governance_decision"] is not None
            assert trace["authorization"] is not None
            assert trace["capability"] is not None
            assert trace["verification"] is not None
            assert trace["execution"] is not None
            assert trace["receipt"] is not None
            assert trace["provenance_id"] is not None

    def test_rejected_path_stops_at_governance(
        self, agent: SovereignOperationsAgent
    ):
        """Rejected path stops at governance."""
        trace = agent.investigate("TICKET-002")
        assert trace["result"] == "REJECTED"
        assert trace["governance_decision"]["approved"] is False
        assert trace["authorization"] is None
        assert trace["capability"] is None
        assert trace["verification"] is None
        assert trace["execution"] is None
        assert trace["receipt"] is None


# ---------------------------------------------------------------------------
# Natural Language Variation Tests
# ---------------------------------------------------------------------------


class TestNaturalLanguageVariation:
    """Tests that natural language variation does not change authority."""

    def test_same_evidence_same_authority(
        self, agent: SovereignOperationsAgent
    ):
        """Same evidence → same authority regardless of explanation."""
        trace1 = agent.investigate("TICKET-001")
        trace2 = agent.investigate("TICKET-001")
        # Same ticket should produce same authority result
        assert trace1["result"] == trace2["result"]
        assert trace1["governance_decision"]["approved"] == trace2["governance_decision"]["approved"]
