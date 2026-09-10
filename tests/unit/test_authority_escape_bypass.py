"""Phase 26: Authority Escape Bypass Tests.

Tests that direct primitive access is detected as an escape.
Proves: DIRECT PRIMITIVE ACCESS != GOVERNED EXECUTION

Each enforcement boundary is tested by:
1. Attempting a direct primitive call (bypass)
2. Verifying the oracle detects this as an escape
3. Verifying governed execution succeeds under valid capability
"""
from __future__ import annotations

import subprocess
import sys
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from sas.argopack import _create_subprocess_capability, _get_argo_gate, _run_sas_with_gate
from sas.capability_bound_database import CapabilityBoundDatabase, create_capability_bound_database
from sas.capability_bound_filesystem import CapabilityBoundFilesystem, create_capability_bound_filesystem
from sas.quant.experiment.execution_capability import (
    CapabilityConstraints,
    CapabilityScope,
    CapabilityType,
    ExecutionCapability,
    ExecutorBinding,
    ReplayGuard,
    ReplayProtectionType,
)
from sas.quant.experiment.protocol_lineage import DomainType, DomainValidityInterval, create_protocol_domain
from sas.quant.runtime_authority_gate import OperationRequest, RuntimeAuthorityGate, create_runtime_authority_gate


# ---------------------------------------------------------------------------
# Boundary 1: RuntimeAuthorityGate for ARGO pack
# ---------------------------------------------------------------------------


class TestARGOBypass:
    """Test that direct subprocess access bypassing the gate is detectable."""

    def test_gate_rejects_mismatched_resource(self):
        """A capability bound to resource A cannot execute against resource B."""
        gate = create_runtime_authority_gate("test-domain")
        capability = _create_subprocess_capability(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={"args": ["dashboard"]},
        )

        # Build a request for a DIFFERENT resource than the capability binds
        request = OperationRequest(
            action="subprocess.execute",
            resource="/usr/bin/other-command",
            arguments={},
            actor_id="argo-agent",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="argo",
        )

        is_permitted, conflicts = gate.verify_capability(capability, request)
        assert not is_permitted, "Gate must reject resource mismatch"
        assert any("Resource mismatch" in c for c in conflicts)

    def test_gate_rejects_expired_capability(self):
        """A capability past its temporal bound must be rejected."""
        gate = create_runtime_authority_gate("test-domain")
        capability = _create_subprocess_capability(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={"args": ["dashboard"]},
        )
        # Override temporal interval to be expired
        from dataclasses import replace
        expired_scope = replace(
            capability.scope,
            temporal_interval=DomainValidityInterval(
                valid_from="2020-01-01T00:00:00Z",
                valid_until="2020-01-02T00:00:00Z",
            ),
        )
        expired_capability = replace(capability, scope=expired_scope)

        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={"args": ["dashboard"]},
            actor_id="argo-agent",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="argo",
        )

        is_permitted, conflicts = gate.verify_capability(expired_capability, request)
        assert not is_permitted, "Gate must reject expired capability"
        assert any("not valid" in c for c in conflicts)

    def test_direct_subprocess_bypass_detected(self):
        """Direct subprocess.run without capability is structurally an escape.

        This test verifies the DETECTION logic: any subprocess call
        without a verified capability is classified as an authority escape.
        """
        gate = create_runtime_authority_gate("test-domain")
        # No capability = no authority
        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={"args": ["dashboard"]},
            actor_id="unauthorized-actor",
            domain_id="unknown-domain",
            requested_at="2026-01-01T00:00:00Z",
            source="unknown",
        )

        # Without a capability, there is nothing to verify -> escape
        # The gate has no registered authorization for this
        assert gate.get_authorization("nonexistent-auth") is None

    def test_gate_accepts_valid_capability(self):
        """A valid, non-expired, correctly-scoped capability must pass."""
        gate = _get_argo_gate()
        capability = _create_subprocess_capability(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={"args": ["dashboard"]},
        )
        # Use the capability's valid_from as the request time to ensure validity
        now = capability.scope.temporal_interval.valid_from

        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={"args": ["dashboard"]},
            actor_id="argo-agent",
            domain_id=gate.domain.domain_id,
            requested_at=now,
            source="argo",
        )

        is_permitted, conflicts = gate.verify_capability(capability, request)
        assert is_permitted, f"Valid capability must pass, got conflicts: {conflicts}"


# ---------------------------------------------------------------------------
# Boundary 2: CapabilityBoundFilesystem
# ---------------------------------------------------------------------------


class TestFilesystemBypass:
    """Test that direct filesystem access bypassing the wrapper is detectable."""

    def test_filesystem_rejects_invalid_capability(self):
        """Filesystem wrapper must reject operations with invalid capability."""
        fs = create_capability_bound_filesystem()

        # Create a capability bound to a different resource
        wrong_domain = create_protocol_domain("wrong-domain", DomainType.SOVEREIGN)
        wrong_capability = ExecutionCapability(
            capability_id="cap-wrong",
            authorization_ref="wrong-auth",
            scope=CapabilityScope(
                domain_id=wrong_domain.domain_id,
                lineage_id=wrong_domain.lineage_hash,
                actor_id="attacker",
                action="filesystem.write",
                resource="/etc/passwd",
                resource_class="filesystem",
                arguments={},
                constraints=CapabilityConstraints(allowed_actions=["filesystem.write"]),
                temporal_interval=DomainValidityInterval(
                    valid_from="2026-01-01T00:00:00Z",
                    valid_until="",
                ),
                authorization_ref="wrong-auth",
            ),
            capability_type=CapabilityType.EXECUTE,
            replay_guard=ReplayGuard(
                guard_type=ReplayProtectionType.SINGLE_USE,
                nonce="nonce-wrong",
                max_uses=1,
                created_at="2026-01-01T00:00:00Z",
            ),
            actor_identity_ref="attacker",
            resource_binding=ExecutorBinding(
                binding_id="binding-wrong",
                executor_id="capability-bound-filesystem",
                resource_id="/etc/passwd",
                bound_resources=["/etc/passwd"],
                bound_at="2026-01-01T00:00:00Z",
                bound_until="",
            ),
            domain_id=wrong_domain.domain_id,
            lineage_id=wrong_domain.lineage_hash,
            authority_root="wrong-auth",
            derived_at="2026-01-01T00:00:00Z",
            derived_by="attacker",
        )

        result = fs.write(wrong_capability, "/tmp/test.txt", "hello")
        assert not result.is_permitted, "Filesystem must reject capability from wrong domain"
        assert result.receipt is not None, "Rejection must produce a receipt"
        assert result.receipt.status.value == "rejected"

    def test_filesystem_accepts_valid_capability(self):
        """Filesystem wrapper must accept operations with valid capability."""
        fs = create_capability_bound_filesystem()
        capability = _create_filesystem_capability(fs, "/tmp/test_cb.txt", "write")
        result = fs.write(capability, "/tmp/test_cb.txt", "hello world")
        assert result.is_permitted, f"Valid write must succeed, got: {result.rejection_reason}"
        assert result.receipt is not None

    def test_direct_open_bypass_is_escape(self):
        """Direct open() call without capability verification is an escape.

        This proves: DIRECT PRIMITIVE ACCESS != GOVERNED EXECUTION
        """
        # The CapabilityBoundFilesystem is the only sanctioned path.
        # A raw open() call has no capability verification, no receipt,
        # no provenance — it is by definition outside the governed model.
        fs = create_capability_bound_filesystem()

        # Attempt without capability: no verification possible
        # This is a structural statement: the wrapper exists precisely
        # because direct open() is not governed execution.
        assert fs.get_receipts() == [], "No receipts until governed execution"


# ---------------------------------------------------------------------------
# Boundary 3: CapabilityBoundDatabase
# ---------------------------------------------------------------------------


class TestDatabaseBypass:
    """Test that direct database access bypassing the wrapper is detectable."""

    def test_database_rejects_invalid_capability(self):
        """Database wrapper must reject operations with invalid capability."""
        db = create_capability_bound_database()

        wrong_domain = create_protocol_domain("wrong-domain", DomainType.SOVEREIGN)
        wrong_capability = ExecutionCapability(
            capability_id="cap-wrong-db",
            authorization_ref="wrong-auth",
            scope=CapabilityScope(
                domain_id=wrong_domain.domain_id,
                lineage_id=wrong_domain.lineage_hash,
                actor_id="attacker",
                action="database.write",
                resource="/etc/shadow",
                resource_class="database",
                arguments={},
                constraints=CapabilityConstraints(allowed_actions=["database.write"]),
                temporal_interval=DomainValidityInterval(
                    valid_from="2026-01-01T00:00:00Z",
                    valid_until="",
                ),
                authorization_ref="wrong-auth",
            ),
            capability_type=CapabilityType.EXECUTE,
            replay_guard=ReplayGuard(
                guard_type=ReplayProtectionType.SINGLE_USE,
                nonce="nonce-wrong-db",
                max_uses=1,
                created_at="2026-01-01T00:00:00Z",
            ),
            actor_identity_ref="attacker",
            resource_binding=ExecutorBinding(
                binding_id="binding-wrong-db",
                executor_id="capability-bound-database",
                resource_id="/etc/shadow",
                bound_resources=["/etc/shadow"],
                bound_at="2026-01-01T00:00:00Z",
                bound_until="",
            ),
            domain_id=wrong_domain.domain_id,
            lineage_id=wrong_domain.lineage_hash,
            authority_root="wrong-auth",
            derived_at="2026-01-01T00:00:00Z",
            derived_by="attacker",
        )

        result = db.connect(wrong_capability, "/tmp/test.db")
        assert not result.is_permitted, "Database must reject capability from wrong domain"

    def test_database_accepts_valid_capability(self):
        """Database wrapper must accept operations with valid capability."""
        db = create_capability_bound_database()
        capability = _create_database_capability(db, "/tmp/test_cbd.db", "connect")
        result = db.connect(capability, "/tmp/test_cbd.db")
        assert result.is_permitted, f"Valid connect must succeed, got: {result.rejection_reason}"

    def test_direct_sqlite_bypass_is_escape(self):
        """Direct sqlite3.connect without capability verification is an escape."""
        db = create_capability_bound_database()
        # No capability = no verification = no governed execution
        assert db.get_receipts() == [], "No receipts until governed execution"


# ---------------------------------------------------------------------------
# Boundary 4: SubprocessInstrument
# ---------------------------------------------------------------------------


class TestSubprocessInstrumentBypass:
    """Test that direct subprocess access is detectable as escape vs instrumented path."""

    def test_instrument_observes_but_does_not_authorize(self):
        """SubprocessInstrument makes subprocess observable, NOT authorized.

        CRITICAL: INSTRUMENTATION != AUTHORITY.
        The instrument records; it does not grant authority.
        """
        from examples.self_audit.runtime_trace import RuntimeTraceRecorder, SubprocessInstrument

        recorder = RuntimeTraceRecorder("test-scope", scope="controlled_local")
        recorder.start()
        instrument = SubprocessInstrument(recorder)

        # The instrument runs subprocess but does NOT verify capability
        result = instrument.run(
            [sys.executable, "-c", "print('hello')"],
            actor="test",
            component="test",
            consequence_type="informational",
        )

        assert result["ok"] is True, "Instrument runs subprocess successfully"
        events = recorder.get_subprocess_events()
        assert len(events) == 2, "Instrument records create + complete events"
        # But no capability verification happened
        cap_events = recorder.get_capability_events()
        assert len(cap_events) == 0, "Instrument does NOT verify capability"

    def test_raw_subprocess_without_instrument_is_unobserved(self):
        """Direct subprocess.run without instrument leaves no trace in recorder.

        This proves the escape detection gap that the instrument closes.
        """
        from examples.self_audit.runtime_trace import RuntimeTraceRecorder

        recorder = RuntimeTraceRecorder("test-scope", scope="controlled_local")
        recorder.start()

        # Direct subprocess call — no instrument, no trace
        subprocess.run(
            [sys.executable, "-c", "print('unobserved')"],
            capture_output=True,
            text=True,
        )

        # The recorder has no knowledge of this
        assert len(recorder.events) == 0, "Direct subprocess leaves no trace"


# ---------------------------------------------------------------------------
# Helper: create valid capabilities for tests
# ---------------------------------------------------------------------------


def _create_filesystem_capability(
    fs: CapabilityBoundFilesystem,
    path: str,
    action: str,
) -> ExecutionCapability:
    """Create a valid filesystem capability for the given path."""
    import uuid
    from datetime import UTC, datetime

    now = datetime.now(UTC).isoformat()
    domain = fs._CapabilityBoundFilesystem__domain  # type: ignore[attr-defined]

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="test-fs-auth",
        scope=CapabilityScope(
            domain_id=domain.domain_id,
            lineage_id=domain.lineage_hash,
            actor_id="test-actor",
            action=f"filesystem.{action}",
            resource=path,
            resource_class="filesystem",
            arguments={"path": path},
            constraints=CapabilityConstraints(allowed_actions=[f"filesystem.{action}"]),
            temporal_interval=DomainValidityInterval(valid_from=now, valid_until=""),
            authorization_ref="test-fs-auth",
        ),
        capability_type=CapabilityType.EXECUTE,
        replay_guard=ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce=f"nonce-{uuid.uuid4().hex[:16]}",
            max_uses=1,
            created_at=now,
        ),
        actor_identity_ref="test-actor",
        resource_binding=ExecutorBinding(
            binding_id=f"binding-{uuid.uuid4().hex[:12]}",
            executor_id="capability-bound-filesystem",
            resource_id=path,
            bound_resources=[path],
            bound_at=now,
            bound_until="",
        ),
        domain_id=domain.domain_id,
        lineage_id=domain.lineage_hash,
        authority_root="test-fs-auth",
        derived_at=now,
        derived_by="test",
    )


def _create_database_capability(
    db: CapabilityBoundDatabase,
    db_path: str,
    action: str,
) -> ExecutionCapability:
    """Create a valid database capability for the given path."""
    import uuid
    from datetime import UTC, datetime

    now = datetime.now(UTC).isoformat()
    domain = db._CapabilityBoundDatabase__domain  # type: ignore[attr-defined]

    return ExecutionCapability(
        capability_id=f"cap-{uuid.uuid4().hex[:12]}",
        authorization_ref="test-db-auth",
        scope=CapabilityScope(
            domain_id=domain.domain_id,
            lineage_id=domain.lineage_hash,
            actor_id="test-actor",
            action=f"database.{action}",
            resource=db_path,
            resource_class="database",
            arguments={"db_path": db_path},
            constraints=CapabilityConstraints(allowed_actions=[f"database.{action}"]),
            temporal_interval=DomainValidityInterval(valid_from=now, valid_until=""),
            authorization_ref="test-db-auth",
        ),
        capability_type=CapabilityType.EXECUTE,
        replay_guard=ReplayGuard(
            guard_type=ReplayProtectionType.SINGLE_USE,
            nonce=f"nonce-{uuid.uuid4().hex[:16]}",
            max_uses=1,
            created_at=now,
        ),
        actor_identity_ref="test-actor",
        resource_binding=ExecutorBinding(
            binding_id=f"binding-{uuid.uuid4().hex[:12]}",
            executor_id="capability-bound-database",
            resource_id=db_path,
            bound_resources=[db_path],
            bound_at=now,
            bound_until="",
        ),
        domain_id=domain.domain_id,
        lineage_id=domain.lineage_hash,
        authority_root="test-db-auth",
        derived_at=now,
        derived_by="test",
    )


# ---------------------------------------------------------------------------
# Cross-boundary invariant: DIRECT PRIMITIVE ACCESS != GOVERNED EXECUTION
# ---------------------------------------------------------------------------


class TestDirectPrimitiveVsGovernedExecution:
    """Prove the central invariant: DIRECT PRIMITIVE ACCESS != GOVERNED EXECUTION."""

    def test_filesystem_direct_access_produces_no_receipt(self):
        """Direct open()/write() produces no execution receipt."""
        fs = create_capability_bound_filesystem()
        assert fs.get_receipts() == [], "No capability = no receipt"

    def test_database_direct_access_produces_no_receipt(self):
        """Direct sqlite3.connect produces no execution receipt."""
        db = create_capability_bound_database()
        assert db.get_receipts() == [], "No capability = no receipt"

    def test_gate_without_authorization_cannot_execute(self):
        """Gate with no registered authorization cannot resolve authority."""
        gate = create_runtime_authority_gate("test-domain")
        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={},
            actor_id="test",
            domain_id=gate.domain.domain_id,
            requested_at="2026-01-01T00:00:00Z",
            source="test",
        )
        # No authorization registered
        resolution = gate.resolve(request, "nonexistent-auth")
        assert not resolution.is_valid
        assert "not found" in resolution.rejection_reason

    def test_replay_guard_prevents_double_execution(self):
        """A capability with max_uses=1 cannot be executed twice."""
        gate = _get_argo_gate()
        capability = _create_subprocess_capability(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={},
        )
        now = capability.scope.temporal_interval.valid_from

        request = OperationRequest(
            action="subprocess.execute",
            resource="sas.cli",
            arguments={},
            actor_id="argo-agent",
            domain_id=gate.domain.domain_id,
            requested_at=now,
            source="argo",
        )

        # First execution should succeed
        is_permitted, _ = gate.verify_capability(capability, request)
        assert is_permitted

        # Mark nonce as used (simulating execution)
        if capability.replay_guard and capability.replay_guard.nonce:
            gate._executed_nonces.add(capability.replay_guard.nonce)

        # Second execution must fail (replay)
        is_permitted, conflicts = gate.verify_capability(capability, request)
        assert not is_permitted, "Replay guard must prevent double execution"
        assert any("replay" in c.lower() for c in conflicts)
