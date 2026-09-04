"""Tests for the compute substrate layer."""

import pytest

from sas.layers.substrate import (
    ComputeSubstrate,
    Machine,
    Screenshot,
    Output,
    LocalDockerSubstrate,
    SubstrateError,
)


class TestMachine:
    """Tests for the Machine dataclass."""

    def test_create_machine(self) -> None:
        """Machine has expected attributes."""
        machine = Machine(
            id="m1",
            template="sas-desktop:latest",
            status="running",
            created_at="2026-09-04T12:00:00",
        )
        assert machine.id == "m1"
        assert machine.template == "sas-desktop:latest"
        assert machine.status == "running"


class TestLocalDockerSubstrate:
    """Tests for the local Docker substrate."""

    def test_boot_creates_machine(self) -> None:
        """Booting creates a machine with running status."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("sas-desktop:latest")
        assert machine.status == "running"
        assert machine.template == "sas-desktop:latest"
        assert machine.id is not None

    def test_capture_returns_screenshot(self) -> None:
        """Capturing returns a screenshot."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("sas-desktop:latest")
        screenshot = substrate.capture(machine)
        assert isinstance(screenshot, Screenshot)
        assert screenshot.machine_id == machine.id

    def test_click_does_not_raise(self) -> None:
        """Clicking does not raise for a running machine."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("sas-desktop:latest")
        substrate.click(machine, x=100, y=200)
        # No exception = pass

    def test_type_does_not_raise(self) -> None:
        """Typing does not raise for a running machine."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("sas-desktop:latest")
        substrate.type(machine, text="hello world")

    def test_execute_returns_output(self) -> None:
        """Executing a command returns output."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("sas-desktop:latest")
        output = substrate.execute(machine, "echo hello")
        assert isinstance(output, Output)
        assert "hello" in output.stdout

    def test_destroy_stops_machine(self) -> None:
        """Destroying a machine changes its status."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("sas-desktop:latest")
        substrate.destroy(machine)
        assert machine.status == "stopped"

    def test_operations_on_stopped_machine_raise(self) -> None:
        """Operations on a stopped machine raise SubstrateError."""
        substrate = LocalDockerSubstrate()
        machine = substrate.boot("sas-desktop:latest")
        substrate.destroy(machine)

        with pytest.raises(SubstrateError):
            substrate.capture(machine)

        with pytest.raises(SubstrateError):
            substrate.click(machine, x=100, y=200)

        with pytest.raises(SubstrateError):
            substrate.type(machine, text="hello")

        with pytest.raises(SubstrateError):
            substrate.execute(machine, "echo hello")

    def test_boot_with_custom_resources(self) -> None:
        """Booting with custom resource limits."""
        substrate = LocalDockerSubstrate(
            default_resources={"cpu": 2, "memory": "4Gi"},
        )
        machine = substrate.boot("sas-desktop:latest")
        assert machine.status == "running"

    def test_list_machines(self) -> None:
        """List machines returns all booted machines."""
        substrate = LocalDockerSubstrate()
        m1 = substrate.boot("template1")
        m2 = substrate.boot("template2")
        machines = substrate.list_machines()
        assert len(machines) == 2
        ids = {m.id for m in machines}
        assert m1.id in ids
        assert m2.id in ids

    def test_auto_destroy_on_idle(self) -> None:
        """Machine is destroyed after idle timeout."""
        import time
        substrate = LocalDockerSubstrate(idle_timeout=1)
        machine = substrate.boot("sas-desktop:latest")

        # Simulate idle time by manipulating last active timestamp
        substrate._last_active[machine.id] = time.time() - 2

        # Trigger auto-destroy check
        substrate._auto_destroy_idle()

        # Machine should be destroyed
        assert machine.status == "stopped"


class TestSubstrateError:
    """Tests for substrate errors."""

    def test_error_message(self) -> None:
        """Error has a message."""
        err = SubstrateError("test error")
        assert str(err) == "test error"
