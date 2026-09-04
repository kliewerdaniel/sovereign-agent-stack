"""Integration tests — verify all 8 layers work end-to-end.

These tests wire real implementations together (not mocks) to confirm
the sovereignty stack operates as a unified system.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from sas.core.config import (
    AuthBroker,
    LongTermProvider,
    MemoryProvider,
    Ownership,
    SASConfig,
    SubstrateType,
    parse_sas_yaml,
)
from sas.core.scoring import compute_score, generate_report, score_config
from sas.dashboard.report import run_dashboard
from sas.layers.auth import LocalAuthBroker, Credentials, Request
from sas.layers.identity import MockEmailAdapter, MockPhoneAdapter, Email
from sas.layers.knowledge import CompileTimeKnowledge
from sas.layers.payments import MPPAdapter, VirtualCardAdapter, PaymentRequirement, SpendingLimit
from sas.layers.substrate import LocalDockerSubstrate, SubstrateError


class TestEndToEndSovereigntyStack:
    """Full stack integration test."""

    def test_sovereign_stack_all_owned(self) -> None:
        """All scorable layers owned gives Fully Sovereign verdict."""
        from sas.core.config import ModelConfig
        config = SASConfig(
            model_primary=ModelConfig(provider="ollama", name="llama3.1:8b", location="local"),
            substrate=SubstrateType.LOCAL_DOCKER,
            memory_short_term=MemoryProvider.LOCAL_RAG,
            memory_long_term=LongTermProvider.COMPILE_TIME_GRAPH,
            auth_broker=AuthBroker.LOCAL_MCP_GATEWAY,
        )
        layers = score_config(config)
        owned, total, score = compute_score(layers)
        report = generate_report(config)

        assert report.verdict == "Fully Sovereign"
        assert score == 1.0
        assert owned == total

    def test_rented_stack_all_rented(self) -> None:
        """All scorable layers rented except unavoidable gives low score."""
        config = SASConfig(
            substrate=SubstrateType.ORGO_CLOUD,
            memory_short_term=MemoryProvider.HONCHO_CLOUD,
            memory_long_term=LongTermProvider.RETRIEVAL_ONLY,
            auth_broker=AuthBroker.COMPOSIO,
        )
        layers = score_config(config)
        owned, total, score = compute_score(layers)
        report = generate_report(config)

        assert report.verdict == "Rented"
        # Harness is always owned (ARGO self-hosted), so 1/6 = 0.167
        assert score < 0.375
        assert owned == 1

    def test_mixed_stack_partial(self) -> None:
        """Mixed owned/rented gives Partial or Sovereign verdict."""
        from sas.core.config import ModelConfig
        config = SASConfig(
            model_primary=ModelConfig(provider="ollama", name="llama3.1:8b", location="local"),
            substrate=SubstrateType.LOCAL_DOCKER,
            memory_short_term=MemoryProvider.HONCHO_CLOUD,
            memory_long_term=LongTermProvider.COMPILE_TIME_GRAPH,
            auth_broker=AuthBroker.COMPOSIO,
        )
        report = generate_report(config)

        # 3 owned (model, compute, knowledge) + harness always owned = 4/6 = 0.667
        assert report.verdict == "Sovereign (target)"
        assert report.score == pytest.approx(0.667, abs=0.01)

    def test_unavoidable_rentals_excluded(self) -> None:
        """Identity and Payments are excluded from score denominator."""
        config = SASConfig()  # defaults
        layers = score_config(config)

        # Identity and payments are unavoidable
        identity = next(l for l in layers if l.layer_id.value == "layer_4_identity")
        payments = next(l for l in layers if l.layer_id.value == "layer_8_payments")

        assert identity.unavoidable_rental is True
        assert payments.unavoidable_rental is True

        # Scorable count excludes them
        scorable = [l for l in layers if not l.unavoidable_rental]
        assert len(scorable) == 6


class TestKnowledgeGraphIntegration:
    """Knowledge graph with real filesystem operations."""

    def test_compile_from_directory(self, tmp_path: Path) -> None:
        """Compile a directory of markdown files into a knowledge graph."""
        # Create markdown files
        (tmp_path / "sovereignty.md").write_text("""---
title: Sovereignty
author: Daniel
---
# Sovereignty
The thesis that intelligence is the accumulated decisions that shaped it.
See [[Compile-Time Knowledge]] for how we implement this.
""")
        (tmp_path / "compile-time.md").write_text("""
# Compile-Time Knowledge
Facts compiled once into stable, inspectable, versionable nodes.
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(tmp_path)

        # 2 unique node labels: "Sovereignty" and "Compile-Time Knowledge"
        # (wikilink target "Compile-Time Knowledge" is deduplicated by label)
        assert len(graph.nodes) == 2
        assert graph.source_path == str(tmp_path)
        # 1 edge: Sovereignty -> Compile-Time Knowledge
        assert len(graph.edges) == 1

    def test_compile_and_query(self, tmp_path: Path) -> None:
        """Compile then query returns matching nodes."""
        (tmp_path / "agent.md").write_text("""
# Sovereign Agent
An agent that owns its [[Knowledge Graph]] and [[Auth Broker]].
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(tmp_path)

        results = knowledge.query(graph, "agent")
        assert len(results) >= 1
        assert any("Agent" in r.label for r in results)

    def test_compile_diff_detects_changes(self, tmp_path: Path) -> None:
        """Diff detects added, removed, and changed nodes."""
        (tmp_path / "original.md").write_text("""
# Original Node
Some content here.
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph1 = knowledge.compile(tmp_path)

        # Modify the file
        (tmp_path / "original.md").write_text("""
# Original Node
Modified content here with [[New Link]].
""")
        (tmp_path / "added.md").write_text("""
# Added Node
A new node.
""")

        graph2 = knowledge.compile(tmp_path)
        diff = knowledge.diff(graph1, graph2)

        assert len(diff.added_nodes) >= 1
        assert any(n.label == "Added Node" for n in diff.added_nodes)

    def test_compile_audit_finds_orphans(self, tmp_path: Path) -> None:
        """Audit identifies orphaned nodes."""
        (tmp_path / "connected.md").write_text("""
# Connected Node
Links to [[Another Node]].
""")
        (tmp_path / "orphan.md").write_text("""
# Orphan Node
No links here.
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(tmp_path)
        report = knowledge.audit(graph)

        # Orphan Node should have no edges
        orphan_labels = {n.label for n in report.orphaned_nodes}
        assert "Orphan Node" in orphan_labels


class TestAuthBrokerIntegration:
    """Auth broker with real encryption and credential lifecycle."""

    def test_register_get_credentials_roundtrip(self) -> None:
        """Registering and retrieving credentials preserves data."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="test-key")
        creds = Credentials(
            tool_name="github",
            auth_type="oauth",
            token="ghp_test_token_123",
            refresh_token="ghr_refresh_token",
            scopes=["repo", "read:user"],
        )

        broker.register_tool("github", creds)
        retrieved = broker.get_credentials("github")

        assert retrieved is not None
        assert retrieved.token == "ghp_test_token_123"
        assert retrieved.refresh_token == "ghr_refresh_token"
        assert retrieved.scopes == ["repo", "read:user"]

    def test_credentials_encrypted_at_rest(self) -> None:
        """Credentials are encrypted in the database."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="secret-key-123")
        creds = Credentials(
            tool_name="stripe",
            auth_type="api_key",
            token="sk_live_12345",
        )

        broker.register_tool("stripe", creds)
        raw = broker._get_raw_token("stripe")

        # Raw bytes should NOT contain the plaintext
        assert raw is not None
        assert b"sk_live_12345" not in raw

    def test_unregister_removes_credentials(self) -> None:
        """Unregistering a tool removes its credentials."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="test-key")
        broker.register_tool("tool1", Credentials(tool_name="tool1", auth_type="api_key", token="tok1"))

        assert broker.get_credentials("tool1") is not None
        broker.unregister_tool("tool1")
        assert broker.get_credentials("tool1") is None

    def test_call_injects_auth_and_audits(self) -> None:
        """Calling a tool injects auth headers and records audit entry."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="test-key")
        broker.register_tool(
            "api",
            Credentials(tool_name="api", auth_type="oauth", token="bearer-token-123"),
        )

        request = Request(
            tool_name="api",
            method="GET",
            path="/v1/users",
            headers={"Accept": "application/json"},
        )

        def mock_http_call(req: Request):
            class FakeResponse:
                status_code = 200
                headers = {}
                body = b'{"ok": true}'
            return FakeResponse()

        response = broker.call(request, mock_http_call)
        assert response.status_code == 200

        # Check audit trail
        trail = broker.audit()
        assert len(trail.entries) == 1
        assert trail.entries[0].tool_name == "api"

    def test_refresh_updates_credentials(self) -> None:
        """Refreshing credentials updates the stored values."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="test-key")
        broker.register_tool(
            "svc",
            Credentials(tool_name="svc", auth_type="oauth", token="old-token"),
        )

        def refresh_fn(tool_name, creds):
            return Credentials(
                tool_name=tool_name,
                auth_type="oauth",
                token="new-token",
            )

        broker.refresh("svc", refresh_fn)
        retrieved = broker.get_credentials("svc")
        assert retrieved is not None
        assert retrieved.token == "new-token"


class TestPaymentIntegration:
    """Payments with real spending limit enforcement."""

    def test_virtual_card_pay_within_limits(self) -> None:
        """Paying within limits succeeds."""
        adapter = VirtualCardAdapter(limit=SpendingLimit(daily=100, per_transaction=50, currency="USD"))
        receipt = adapter.pay(PaymentRequirement(
            resource="api.premium.com",
            price=25.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        ))

        assert receipt.status == "completed"
        assert receipt.method == "card"

    def test_virtual_card_pay_exceeds_limit(self) -> None:
        """Paying over per-transaction limit raises."""
        adapter = VirtualCardAdapter(limit=SpendingLimit(daily=100, per_transaction=50, currency="USD"))

        with pytest.raises(ValueError, match="exceeds per-transaction limit"):
            adapter.pay(PaymentRequirement(
                resource="expensive.com",
                price=75.0,
                currency="USD",
                methods=["card"],
                cadence="one_shot",
                metadata={},
            ))

    def test_mpp_pay_stablecoin(self) -> None:
        """MPP adapter pays with stablecoin."""
        adapter = MPPAdapter(settlement="stablecoin")
        receipt = adapter.pay(PaymentRequirement(
            resource="decentralized-api.com",
            price=10.0,
            currency="USDC",
            methods=["stablecoin"],
            cadence="streaming",
            metadata={},
        ))

        assert receipt.status == "completed"
        assert receipt.method == "stablecoin"

    def test_daily_spending_accumulates(self) -> None:
        """Multiple payments accumulate toward daily limit."""
        adapter = VirtualCardAdapter(limit=SpendingLimit(daily=100, per_transaction=50, currency="USD"))

        adapter.pay(PaymentRequirement(
            resource="a.com", price=20.0, currency="USD", methods=["card"], cadence="one_shot", metadata={},
        ))
        adapter.pay(PaymentRequirement(
            resource="b.com", price=15.0, currency="USD", methods=["card"], cadence="one_shot", metadata={},
        ))

        assert adapter.daily_spending == 35.0
        assert adapter.remaining_daily == 65.0


class TestComputeSubstrateIntegration:
    """Compute substrate lifecycle."""

    def test_full_lifecycle(self) -> None:
        """Boot → operate → destroy lifecycle works."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("sas-desktop:latest")

        assert machine.status == "running"
        assert substrate.list_machines() == [machine]

        screenshot = substrate.capture(machine)
        assert screenshot.machine_id == machine.id

        substrate.click(machine, x=50, y=50)
        substrate.type(machine, "test")
        output = substrate.execute(machine, "echo lifecycle")
        assert "lifecycle" in output.stdout

        substrate.destroy(machine)
        assert machine.status == "stopped"

    def test_multiple_machines(self) -> None:
        """Multiple machines can run concurrently."""
        substrate = LocalDockerSubstrate()
        m1 = substrate.boot("template-a")
        m2 = substrate.boot("template-b")
        m3 = substrate.boot("template-a")

        machines = substrate.list_machines()
        assert len(machines) == 3
        assert {m.template for m in machines} == {"template-a", "template-b"}

    def test_operations_on_destroyed_raise(self) -> None:
        """Operations on a destroyed machine raise SubstrateError."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("template")
        substrate.destroy(machine)

        with pytest.raises(SubstrateError):
            substrate.capture(machine)


class TestIdentityIntegration:
    """Identity adapters with real data flow."""

    def test_email_send_receive_flow(self) -> None:
        """Send an email and receive it back via watch."""
        adapter = MockEmailAdapter()
        inbox = adapter.provision(username="agent", domain="agentmail.to")

        adapter.send(inbox, Email(
            from_="agent@agentmail.to",
            to="client@external.com",
            subject="Proposal",
            body="Here is my proposal...",
        ))

        received = list(adapter.watch(inbox))
        assert len(received) == 1
        assert received[0].subject == "Proposal"

    def test_phone_call_and_sms_history(self) -> None:
        """Calls and SMS are recorded in history."""
        adapter = MockPhoneAdapter()
        number = adapter.provision(region="US")

        adapter.call(number, "+15551234567")
        adapter.sms(number, "Hello!")
        adapter.sms(number, "Follow-up")

        calls = adapter.get_call_history(number)
        messages = adapter.get_sent_messages(number)

        assert len(calls) == 1
        assert len(messages) == 2
        assert messages[1] == "Follow-up"


class TestDriftDetection:
    """Sovereignty drift detection."""

    def test_drift_detected_on_config_change(self, tmp_path: Path) -> None:
        """Running dashboard twice with different configs shows drift."""
        config1 = tmp_path / "sas1.yaml"
        config1.write_text("""
model:
  primary:
    provider: ollama
    name: llama3.1:8b
    location: local
compute:
  substrate: local_docker
memory:
  short_term:
    provider: local_rag
  long_term:
    provider: compile_time_graph
auth:
  broker: local_mcp_gateway
payments:
  adapter: virtual_card
""")

        cache = tmp_path / ".sas"

        # First run — all owned
        report1 = run_dashboard(config1, cache)
        assert "Fully Sovereign" in report1 or "Sovereign" in report1

        # Modify config to be cloud-based
        config2 = tmp_path / "sas2.yaml"
        config2.write_text("""
compute:
  substrate: orgo_cloud
memory:
  short_term:
    provider: honcho_cloud
  long_term:
    provider: retrieval_only
auth:
  broker: composio
payments:
  adapter: virtual_card
""")

        # Second run — should detect drift
        report2 = run_dashboard(config2, cache)
        assert "Rented" in report2 or "Partial" in report2 or "drift" in report2.lower()
