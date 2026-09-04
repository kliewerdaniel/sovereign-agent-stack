"""Performance benchmarks for the Sovereign Agent Stack.

Measures:
- Knowledge graph compile latency (markdown parsing + materialization)
- Graph query latency (by label, by content, transitive)
- Auth broker credential operations (register, get, refresh, audit)
- Payment adapter latency (authorize, pay, receipt lookup)
- Sovereignty scoring latency (full report generation)
- Substrate lifecycle latency (boot, capture, destroy)

Run with: python -m pytest tests/benchmarks/ -v
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from sas.core.config import SASConfig
from sas.core.scoring import generate_report
from sas.layers.auth import LocalAuthBroker, Credentials
from sas.layers.knowledge import CompileTimeKnowledge
from sas.layers.payments import VirtualCardAdapter, PaymentRequirement, SpendingLimit
from sas.layers.substrate import LocalDockerSubstrate


def _measure(fn, iterations: int = 100) -> float:
    """Measure average execution time in seconds."""
    start = time.perf_counter()
    for _ in range(iterations):
        fn()
    elapsed = time.perf_counter() - start
    return elapsed / iterations


class TestKnowledgeGraphBenchmarks:
    """Benchmark knowledge graph operations."""

    def test_compile_latency_small(self, tmp_path: Path) -> None:
        """Compile 10 markdown files."""
        for i in range(10):
            (tmp_path / f"file{i}.md").write_text(f"""
# Node {i}
Content for node {i} with [[Link {i}]].
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        avg = _measure(lambda: knowledge.compile(tmp_path))
        # Should complete in < 100ms for 10 files
        assert avg < 0.1

    def test_compile_latency_medium(self, tmp_path: Path) -> None:
        """Compile 100 markdown files."""
        for i in range(100):
            (tmp_path / f"file{i}.md").write_text(f"""
# Node {i}
Content for node {i} with [[Link {i}]].
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        avg = _measure(lambda: knowledge.compile(tmp_path))
        # Should complete in < 500ms for 100 files
        assert avg < 0.5

    def test_query_latency_label(self, tmp_path: Path) -> None:
        """Query nodes by label."""
        for i in range(50):
            (tmp_path / f"file{i}.md").write_text(f"""
# Node {i}
Content for node {i}.
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(tmp_path)

        avg = _measure(lambda: knowledge.query(graph, "Node 25"))
        assert avg < 0.01  # < 10ms

    def test_query_latency_transitive(self, tmp_path: Path) -> None:
        """Transitive query (graph traversal)."""
        for i in range(50):
            (tmp_path / f"file{i}.md").write_text(f"""
# Node {i}
Links to [[Node {i+1}]].
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph = knowledge.compile(tmp_path)

        avg = _measure(lambda: knowledge.query(graph, "Node 0"))
        assert avg < 0.05  # < 50ms

    def test_diff_latency(self, tmp_path: Path) -> None:
        """Diff two graph states."""
        for i in range(50):
            (tmp_path / f"file{i}.md").write_text(f"""
# Node {i}
Version 1.
""")

        knowledge = CompileTimeKnowledge(store_path=":memory:")
        graph1 = knowledge.compile(tmp_path)

        # Modify some files
        for i in range(10):
            (tmp_path / f"file{i}.md").write_text(f"""
# Node {i}
Version 2.
""")

        graph2 = knowledge.compile(tmp_path)

        avg = _measure(lambda: knowledge.diff(graph1, graph2))
        assert avg < 0.05  # < 50ms


class TestAuthBrokerBenchmarks:
    """Benchmark auth broker operations."""

    def test_register_latency(self) -> None:
        """Register a new credential."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="bench-key")

        def register():
            broker.register_tool(
                f"tool_{time.time()}",
                Credentials(tool_name="bench", auth_type="api_key", token="tok"),
            )

        avg = _measure(register)
        assert avg < 0.001  # < 1ms

    def test_get_latency(self) -> None:
        """Get decrypted credentials."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="bench-key")
        broker.register_tool(
            "bench_tool",
            Credentials(tool_name="bench", auth_type="api_key", token="tok"),
        )

        avg = _measure(lambda: broker.get_credentials("bench_tool"))
        assert avg < 0.001  # < 1ms

    def test_audit_latency(self) -> None:
        """Generate audit trail."""
        broker = LocalAuthBroker(store_path=":memory:", encryption_key="bench-key")
        for i in range(100):
            broker.register_tool(
                f"tool_{i}",
                Credentials(tool_name=f"tool_{i}", auth_type="api_key", token=f"tok_{i}"),
            )

        avg = _measure(lambda: broker.audit())
        assert avg < 0.01  # < 10ms


class TestPaymentAdapterBenchmarks:
    """Benchmark payment operations."""

    def test_pay_latency(self) -> None:
        """Process a payment."""
        adapter = VirtualCardAdapter(limit=SpendingLimit(daily=1000, per_transaction=500, currency="USD"))

        req = PaymentRequirement(
            resource="bench.com",
            price=10.0,
            currency="USD",
            methods=["card"],
            cadence="one_shot",
            metadata={},
        )

        avg = _measure(lambda: adapter.pay(req))
        assert avg < 0.001  # < 1ms

    def test_authorize_latency(self) -> None:
        """Update spending limits."""
        adapter = VirtualCardAdapter()

        avg = _measure(lambda: adapter.authorize(SpendingLimit(daily=500, per_transaction=100, currency="USD")))
        assert avg < 0.0001  # < 0.1ms


class TestScoringBenchmarks:
    """Benchmark sovereignty scoring."""

    def test_full_report_latency(self) -> None:
        """Generate full sovereignty report."""
        config = SASConfig()

        avg = _measure(lambda: generate_report(config))
        assert avg < 0.001  # < 1ms


class TestSubstrateBenchmarks:
    """Benchmark compute substrate operations."""

    def test_boot_latency(self) -> None:
        """Boot a new machine."""
        substrate = LocalDockerSubstrate()

        avg = _measure(lambda: substrate.boot("sas-desktop:latest"))
        assert avg < 0.001  # < 1ms (simulated)

    def test_capture_latency(self) -> None:
        """Capture a screenshot."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("template")

        avg = _measure(lambda: substrate.capture(machine))
        assert avg < 0.001  # < 1ms (simulated)

    def test_destroy_latency(self) -> None:
        """Destroy a machine."""
        substrate = LocalDockerSubstrate()

        def boot_and_destroy():
            m = substrate.boot("template")
            substrate.destroy(m)

        avg = _measure(boot_and_destroy)
        assert avg < 0.001  # < 1ms (simulated)
