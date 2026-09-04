"""Tests for Rust bridge modules."""
from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock

from sas.rust_bridge import (
    ExecutionContext,
    AgentStateMachine,
    StateTransition,
    CapabilityRegistry,
    PolicyEnforcer,
    SovereigntyAsserter,
)


class TestExecutionContext:
    """Tests for Python ExecutionContext wrapper."""
    
    def test_new_context_has_no_capabilities(self):
        ctx = ExecutionContext()
        assert not ctx.can_read_filesystem
        assert not ctx.can_write_filesystem
        assert not ctx.can_dispatch_network
        assert not ctx.can_execute_commands
        assert not ctx.can_process_payments
    
    def test_builder_pattern_grants_capabilities(self):
        ctx = ExecutionContext()
        ctx = ctx.with_read_filesystem().with_dispatch_network()
        assert ctx.can_read_filesystem
        assert ctx.can_dispatch_network
        assert not ctx.can_write_filesystem
    
    def test_builder_pattern_returns_new_instance(self):
        ctx1 = ExecutionContext()
        ctx2 = ctx1.with_read_filesystem()
        assert not ctx1.can_read_filesystem  # Original unchanged
        assert ctx2.can_read_filesystem  # New instance has it


class TestAgentStateMachine:
    """Tests for Python AgentStateMachine wrapper."""
    
    def test_new_is_idle(self):
        sm = AgentStateMachine()
        assert sm.current == "Idle"
    
    def test_idle_to_executing(self):
        sm = AgentStateMachine()
        sm.transition("Executing")
        assert sm.current == "Executing"
    
    def test_executing_to_completed(self):
        sm = AgentStateMachine()
        sm.transition("Executing")
        sm.transition("Verifying")
        sm.transition("Completed")
        assert sm.current == "Completed"
    
    def test_invalid_transition_raises(self):
        sm = AgentStateMachine()
        with pytest.raises(ValueError):
            sm.transition("Completed")  # Can't go Idle -> Completed
    
    def test_history_tracks_transitions(self):
        sm = AgentStateMachine()
        sm.transition("Executing")
        sm.transition("Verifying")
        history = sm.history
        assert len(history) == 2
        assert history[0].from_state == "Idle"
        assert history[0].to_state == "Executing"


class TestCapabilityRegistry:
    """Tests for Python CapabilityRegistry wrapper."""
    
    def test_new_registry_has_no_capabilities(self):
        reg = CapabilityRegistry()
        assert not reg.is_granted("read_filesystem")
    
    def test_grant_and_check(self):
        reg = CapabilityRegistry()
        reg.grant("read_filesystem")
        assert reg.is_granted("read_filesystem")
        assert not reg.is_granted("write_filesystem")
    
    def test_require_raises_when_missing(self):
        reg = CapabilityRegistry()
        with pytest.raises(PermissionError):
            reg.require("read_filesystem")
    
    def test_require_passes_when_granted(self):
        reg = CapabilityRegistry()
        reg.grant("read_filesystem")
        reg.require("read_filesystem")  # Should not raise


class TestPolicyEnforcer:
    """Tests for Python PolicyEnforcer wrapper."""
    
    def test_allow_mode_permits(self):
        enforcer = PolicyEnforcer("allow")
        assert enforcer.check_write("/tmp/test.txt", b"data")
        assert enforcer.check_exec("ls", ["-la"])
        assert enforcer.check_dispatch("https://example.com")
        assert enforcer.check_payment(100.0, "USD", "recipient")
    
    def test_deny_mode_blocks(self):
        enforcer = PolicyEnforcer("deny")
        with pytest.raises(PermissionError):
            enforcer.check_write("/tmp/test.txt", b"data")
        with pytest.raises(PermissionError):
            enforcer.check_exec("ls", ["-la"])
        with pytest.raises(PermissionError):
            enforcer.check_dispatch("https://example.com")
        with pytest.raises(PermissionError):
            enforcer.check_payment(100.0, "USD", "recipient")


class TestSovereigntyAsserter:
    """Tests for Python SovereigntyAsserter wrapper."""
    
    def test_empty_score_is_zero(self):
        asserter = SovereigntyAsserter()
        assert asserter.score == 0.0
    
    def test_all_owned_score_is_one(self):
        asserter = SovereigntyAsserter()
        for layer in SovereigntyAsserter.LAYERS:
            asserter.with_layer(layer, "owned")
        assert asserter.score == 1.0
        assert asserter.owned_count == len(SovereigntyAsserter.LAYERS)
    
    def test_mixed_ownership(self):
        asserter = SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("compute", "rented")
        assert asserter.owned_count == 1
        assert asserter.total_count == 2
        assert asserter.score == 0.5
    
    def test_assert_all_owned_passes_when_all_owned(self):
        asserter = SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("harness", "owned")
        assert asserter.assert_all_owned()
    
    def test_assert_all_owned_fails_when_not_all_owned(self):
        asserter = SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("compute", "rented")
        with pytest.raises(ValueError):
            asserter.assert_all_owned()
    
    def test_assert_score_above(self):
        asserter = SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("harness", "owned")
        asserter.with_layer("compute", "rented")
        asserter.with_layer("identity", "rented")
        # Score is 0.5
        assert asserter.assert_score_above(0.4)
        with pytest.raises(ValueError):
            asserter.assert_score_above(0.6)
    
    def test_verdict(self):
        asserter = SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("harness", "owned")
        asserter.with_layer("compute", "owned")
        asserter.with_layer("identity", "owned")
        asserter.with_layer("short_term_memory", "owned")
        asserter.with_layer("long_term_knowledge", "rented")
        asserter.with_layer("auth", "rented")
        asserter.with_layer("payments", "rented")
        # Score is 0.625
        assert asserter.verdict == "Sovereign (target)"


class TestStateTransition:
    """Tests for StateTransition class."""
    
    def test_from_string(self):
        t = StateTransition.from_string("Idle -> Executing (2024-01-01T00:00:00Z)")
        assert t.from_state == "Idle"
        assert t.to_state == "Executing"
        assert t.timestamp == "2024-01-01T00:00:00Z"
    
    def test_repr(self):
        t = StateTransition("Idle", "Executing", "2024-01-01T00:00:00Z", None)
        assert repr(t) == "StateTransition(Idle -> Executing)"
