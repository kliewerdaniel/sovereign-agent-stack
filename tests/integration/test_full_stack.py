# — Full Stack Integration Test (Phase 7) —
# Exercises all 8 layers together through the CLI and Python API.

import pytest
from pathlib import Path
import tempfile
import json

from sas.core.config import parse_sas_yaml
from sas.layers import LayerRegistry
from sas.layers.knowledge import CompileTimeKnowledge
from sas.layers.auth import LocalAuthBroker, Credentials
from sas.layers.payments import VirtualCardAdapter, MPPAdapter, PaymentRequirement, SpendingLimit
from sas.layers.substrate import LocalDockerSubstrate
from sas.layers.identity import MockEmailAdapter, MockPhoneAdapter, Email


class TestFullStackIntegration:
    """End-to-end test: all 8 layers working together."""

    def test_layer_registry_with_real_config(self):
        """LayerRegistry computes sovereignty score from a real sas.yaml."""
        config_path = Path("examples/agency-worker/sas.yaml")
        config = parse_sas_yaml(config_path)
        registry = LayerRegistry(config)
        owned, total, score = registry.sovereignty_score()
        assert owned == 6
        assert total == 6
        assert score == 1.0

    def test_knowledge_graph_compile_and_query(self):
        """Knowledge layer: compile markdown, query graph."""
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "agent.md"
            md.write_text("# Agent Design\n\nUses [[local-first]] architecture.")
            ctk = CompileTimeKnowledge(store_path=":memory:")
            graph = ctk.compile(md)
            assert len(graph.nodes) == 2
            results = ctk.query(graph, "local")
            assert len(results) >= 1

    def test_auth_broker_register_and_call(self):
        """Auth layer: register tool, make a call with credential injection."""
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(
            tool_name="github", auth_type="oauth", token="test-token-123"
        ))
        captured = {}

        def mock_http(request):
            captured["auth"] = request.headers.get("Authorization", "")
            from sas.layers.auth import Response
            return Response(200, {}, b"ok")

        from sas.layers.auth import Request
        req = Request(tool_name="github", method="GET", path="/repos", headers={})
        broker.call(req, mock_http)
        assert captured["auth"] == "Bearer test-token-123"

    def test_payments_virtual_card(self):
        """Payments layer: virtual card payment within limits."""
        adapter = VirtualCardAdapter(limit=SpendingLimit(daily=100, per_transaction=50, currency="USD"))
        receipt = adapter.pay(PaymentRequirement(
            resource="api", price=25.0, currency="USD",
            methods=["card"], cadence="one_shot", metadata={}
        ))
        assert receipt.status == "completed"
        assert receipt.amount == 25.0

    def test_payments_mpp(self):
        """Payments layer: MPP stablecoin payment."""
        adapter = MPPAdapter(settlement="stablecoin",
                             limit=SpendingLimit(daily=1000, per_transaction=100, currency="USD"))
        receipt = adapter.pay(PaymentRequirement(
            resource="compute", price=10.0, currency="USD",
            methods=["stablecoin"], cadence="one_shot", metadata={}
        ))
        assert receipt.method == "stablecoin"

    def test_substrate_lifecycle(self):
        """Substrate layer: boot, execute, destroy."""
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        assert m.status == "running"
        output = sub.execute(m, "echo integration-test")
        assert "integration-test" in output.stdout
        sub.destroy(m)
        assert m.status == "stopped"

    def test_identity_email(self):
        """Identity layer: provision email, send message."""
        adapter = MockEmailAdapter()
        inbox = adapter.provision("agent", "agentmail.to")
        adapter.send(inbox, Email(
            from_="agent@agentmail.to",
            to="client@example.com",
            subject="Test",
            body="Integration test"
        ))
        sent = adapter.watch(inbox)
        assert len(sent) == 1

    def test_identity_phone(self):
        """Identity layer: provision phone, send SMS."""
        adapter = MockPhoneAdapter()
        phone = adapter.provision("US")
        adapter.sms(phone, "Integration test")
        assert len(adapter.get_sent_messages(phone)) == 1

    def test_full_pipeline_sovereignty_to_payment(self):
        """Full pipeline: sovereignty check → knowledge query → payment."""
        # 1. Check sovereignty
        config = parse_sas_yaml(Path("examples/agency-worker/sas.yaml"))
        registry = LayerRegistry(config)
        owned, total, score = registry.sovereignty_score()
        assert score == 1.0

        # 2. Query knowledge
        with tempfile.TemporaryDirectory() as tmpdir:
            md = Path(tmpdir) / "payments.md"
            md.write_text("# Payments\n\nSupports [[virtual card]] and [[MPP]].")
            ctk = CompileTimeKnowledge(store_path=":memory:")
            graph = ctk.compile(md)
            results = ctk.query(graph, "virtual")
            assert len(results) >= 1

        # 3. Make payment
        adapter = VirtualCardAdapter()
        receipt = adapter.pay(PaymentRequirement(
            resource="api", price=10.0, currency="USD",
            methods=["card"], cadence="one_shot", metadata={}
        ))
        assert receipt.status == "completed"

    def test_auth_audit_trail_across_layers(self):
        """Auth audit trail captures calls from multiple layers."""
        broker = LocalAuthBroker(store_path=":memory:")
        broker.register_tool("github", Credentials(tool_name="github", auth_type="oauth", token="t1"))
        broker.register_tool("stripe", Credentials(tool_name="stripe", auth_type="api_key", token="t2"))

        from sas.layers.auth import Request, Response

        def mock_http(request):
            return Response(200, {}, b"ok")

        broker.call(Request("github", "GET", "/repos", {}), mock_http)
        broker.call(Request("stripe", "POST", "/charges", {}), mock_http)

        trail = broker.audit()
        assert len(trail.entries) == 2
        tools = {e.tool_name for e in trail.entries}
        assert tools == {"github", "stripe"}

    def test_substrate_idle_auto_destroy(self):
        """Substrate auto-destroys idle machines."""
        import time
        sub = LocalDockerSubstrate(idle_timeout=0)
        m = sub.boot("xfce")
        time.sleep(0.1)
        sub._auto_destroy_idle()
        assert m.status == "stopped"

    def test_payments_spending_limit_enforcement(self):
        """Payments enforces daily spending limits."""
        adapter = VirtualCardAdapter(limit=SpendingLimit(daily=50, per_transaction=50, currency="USD"))
        adapter.pay(PaymentRequirement("r1", 30.0, "USD", ["card"], "one_shot", {}))
        with pytest.raises(ValueError, match="Daily limit exceeded"):
            adapter.pay(PaymentRequirement("r2", 30.0, "USD", ["card"], "one_shot", {}))


class TestCLIIntegration:
    """Test CLI commands work end-to-end."""


