"""Tests for the ARGO skill pack."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from sas.argopack import ARGO_SAS_SKILL, invoke, ARGO_SKILL_META


class TestARGOSkillMeta:
    """Test ARGO skill metadata."""

    def test_meta_structure(self):
        assert ARGO_SKILL_META["name"] == "sovereign-agent-stack"
        assert "version" in ARGO_SKILL_META
        assert "parameters" in ARGO_SKILL_META

    def test_meta_parameters_schema(self):
        params = ARGO_SKILL_META["parameters"]
        assert params["type"] == "object"
        assert "action" in params["properties"]
        assert "config" in params["properties"]

    def test_meta_action_enum(self):
        action_prop = ARGO_SKILL_META["properties"]["action"] if "properties" in ARGO_SKILL_META else ARGO_SKILL_META["parameters"]["properties"]["action"]
        assert "sovereignty_check" in action_prop["enum"]
        assert "compile_knowledge" in action_prop["enum"]


class TestARGOInvoke:
    """Test ARGO skill invocation."""

    def test_unknown_action(self):
        result = invoke({"action": "nonexistent"})
        assert result["ok"] is False
        assert "Unknown action" in result.get("error", "")

    def test_sovereignty_check(self):
        with patch("sas.argopack._run_sas") as mock_run:
            mock_run.return_value = {"ok": True, "stdout": '{"score": 1.0}', "stderr": ""}
            result = invoke({"action": "sovereignty_check"})
            assert result["ok"] is True
            mock_run.assert_called_once()

    def test_compile_knowledge_missing_source(self):
        result = invoke({"action": "compile_knowledge"})
        assert result["ok"] is False
        assert "source" in result.get("error", "")

    def test_compile_knowledge(self):
        with patch("sas.argopack._run_sas") as mock_run:
            mock_run.return_value = {"ok": True, "stdout": "Compiled", "stderr": ""}
            result = invoke({"action": "compile_knowledge", "source": "/tmp/notes"})
            assert result["ok"] is True

    def test_query_knowledge_missing_query(self):
        result = invoke({"action": "query_knowledge"})
        assert result["ok"] is False
        assert "query" in result.get("error", "")

    def test_register_credential_missing_params(self):
        result = invoke({"action": "register_credential", "tool_name": "github"})
        assert result["ok"] is False
        assert "token" in result.get("error", "")

    def test_payments_pay_missing_params(self):
        result = invoke({"action": "payments_pay", "resource": "api"})
        assert result["ok"] is False
        assert "price" in result.get("error", "")

    def test_substrate_destroy_missing_id(self):
        result = invoke({"action": "substrate_destroy"})
        assert result["ok"] is False
        assert "machine_id" in result.get("error", "")


class TestRunSas:
    """Test _run_sas helper."""

    def test_timeout(self):
        with patch("sas.argopack.subprocess.run", side_effect=__import__('subprocess').TimeoutExpired(cmd="sas", timeout=30)):
            from sas.argopack import _run_sas
            result = _run_sas(["dashboard"])
            assert result["ok"] is False
            assert "timed out" in result.get("error", "")

    def test_module_not_found(self):
        with patch("sas.argopack.subprocess.run", side_effect=FileNotFoundError):
            from sas.argopack import _run_sas
            result = _run_sas(["dashboard"])
            assert result["ok"] is False
            assert "not found" in result.get("error", "")
