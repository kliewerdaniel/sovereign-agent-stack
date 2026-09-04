"""Tests for Rust extension module (sas_core_py)."""
from __future__ import annotations

import json
import pytest

import sas_core_py as sas


class TestToolRegistry:
    """Tests for Rust ToolRegistry."""
    
    def test_new_registry_empty(self):
        reg = sas.ToolRegistry()
        assert reg.list() == []
        assert not reg.has("anything")
    
    def test_register_and_get(self):
        reg = sas.ToolRegistry()
        schema = json.dumps({
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["query"]
        })
        reg.register("my_tool", "A test tool", schema, ["read_filesystem"])
        assert reg.has("my_tool")
        assert "my_tool" in reg.list()
    
    def test_validate_valid_input(self):
        reg = sas.ToolRegistry()
        schema = json.dumps({
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["query"]
        })
        reg.register("my_tool", "A test tool", schema, [])
        assert reg.validate("my_tool", json.dumps({"query": "test", "limit": 5}))
    
    def test_validate_missing_required(self):
        reg = sas.ToolRegistry()
        schema = json.dumps({
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "limit": {"type": "integer"}
            },
            "required": ["query"]
        })
        reg.register("my_tool", "A test tool", schema, [])
        with pytest.raises(ValueError, match="Missing required field"):
            reg.validate("my_tool", json.dumps({"limit": 5}))
    
    def test_validate_invalid_type(self):
        reg = sas.ToolRegistry()
        schema = json.dumps({
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        })
        reg.register("my_tool", "A test tool", schema, [])
        with pytest.raises(ValueError, match="invalid type"):
            reg.validate("my_tool", json.dumps({"query": 123}))
    
    def test_unregister(self):
        reg = sas.ToolRegistry()
        schema = json.dumps({"type": "object", "properties": {}})
        reg.register("my_tool", "A test tool", schema, [])
        assert reg.has("my_tool")
        assert reg.unregister("my_tool")
        assert not reg.has("my_tool")


class TestSovereigntyAsserter:
    """Tests for Rust SovereigntyAsserter."""
    
    def test_empty_score_is_zero(self):
        asserter = sas.SovereigntyAsserter()
        assert asserter.calculate_score() == 0.0
        assert asserter.owned_count() == 0
        assert asserter.total_count() == 0
    
    def test_all_owned(self):
        asserter = sas.SovereigntyAsserter()
        for layer in ["model", "harness", "compute", "identity", 
                       "short_term_memory", "long_term_knowledge", "auth", "payments"]:
            asserter.with_layer(layer, "owned")
        assert asserter.calculate_score() == 1.0
        assert asserter.owned_count() == 8
        assert asserter.total_count() == 8
    
    def test_mixed_ownership(self):
        asserter = sas.SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("harness", "owned")
        asserter.with_layer("compute", "rented")
        asserter.with_layer("identity", "rented")
        assert asserter.calculate_score() == 0.5
        assert asserter.owned_count() == 2
        assert asserter.total_count() == 4
    
    def test_assert_all_owned_success(self):
        asserter = sas.SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("harness", "owned")
        assert asserter.assert_all_owned()
    
    def test_assert_all_owned_failure(self):
        asserter = sas.SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("compute", "rented")
        with pytest.raises(ValueError):
            asserter.assert_all_owned()
    
    def test_assert_score_above_success(self):
        asserter = sas.SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("harness", "owned")
        asserter.with_layer("compute", "rented")
        asserter.with_layer("identity", "rented")
        assert asserter.assert_score_above(0.4)
    
    def test_assert_score_above_failure(self):
        asserter = sas.SovereigntyAsserter()
        asserter.with_layer("model", "owned")
        asserter.with_layer("compute", "rented")
        with pytest.raises(ValueError):
            asserter.assert_score_above(0.6)


class TestPolicyEnforcer:
    """Tests for Rust PolicyEnforcer."""
    
    def test_allow_mode(self):
        enforcer = sas.PolicyEnforcer("allow")
        assert enforcer.check_write("/tmp/test.txt", b"data")
        assert enforcer.check_exec("ls", ["-la"])
        assert enforcer.check_dispatch("https://example.com", "GET")
        assert enforcer.check_payment(100.0, "USD", "recipient")
    
    def test_deny_mode(self):
        enforcer = sas.PolicyEnforcer("deny")
        with pytest.raises(PermissionError):
            enforcer.check_write("/tmp/test.txt", b"data")
        with pytest.raises(PermissionError):
            enforcer.check_exec("ls", ["-la"])
        with pytest.raises(PermissionError):
            enforcer.check_dispatch("https://example.com", "GET")
        with pytest.raises(PermissionError):
            enforcer.check_payment(100.0, "USD", "recipient")


class TestCapabilityRegistry:
    """Tests for Rust CapabilityRegistry."""
    
    def test_new_registry_empty(self):
        reg = sas.CapabilityRegistry()
        assert not reg.is_granted("read_filesystem")
        assert not reg.is_granted("write_filesystem")
    
    def test_grant_and_check(self):
        reg = sas.CapabilityRegistry()
        reg.grant("read_filesystem")
        assert reg.is_granted("read_filesystem")
        assert not reg.is_granted("write_filesystem")
    
    def test_require_success(self):
        reg = sas.CapabilityRegistry()
        reg.grant("read_filesystem")
        assert reg.require("read_filesystem")
    
    def test_require_failure(self):
        reg = sas.CapabilityRegistry()
        with pytest.raises(BaseException):  # PanicException from unwrap
            reg.require("read_filesystem")


class TestExecutionContext:
    """Tests for Rust ExecutionContext."""
    
    def test_new_context_no_capabilities(self):
        ctx = sas.ExecutionContext()
        assert not ctx.can_read_filesystem
        assert not ctx.can_write_filesystem
        assert not ctx.can_dispatch_network
        assert not ctx.can_execute_commands
        assert not ctx.can_process_payments
    
    def test_with_capabilities(self):
        ctx = sas.ExecutionContext()
        ctx = ctx.with_read_filesystem().with_write_filesystem()
        assert ctx.can_read_filesystem
        assert ctx.can_write_filesystem
        assert not ctx.can_dispatch_network


class TestAgentStateMachine:
    """Tests for Rust AgentStateMachine."""
    
    def test_new_is_idle(self):
        sm = sas.AgentStateMachine()
        assert sm.current == "Idle"
    
    def test_transitions(self):
        sm = sas.AgentStateMachine()
        sm.transition("Executing", None)
        assert sm.current == "Executing"
        sm.transition("Verifying", None)
        assert sm.current == "Verifying"
        sm.transition("Completed", None)
        assert sm.current == "Completed"
    
    def test_invalid_transition(self):
        sm = sas.AgentStateMachine()
        with pytest.raises(ValueError):
            sm.transition("Completed", None)
    
    def test_history(self):
        sm = sas.AgentStateMachine()
        sm.transition("Executing", None)
        sm.transition("Verifying", None)
        history = sm.history
        assert len(history) == 2
