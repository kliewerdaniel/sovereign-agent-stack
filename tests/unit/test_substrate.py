# — Unit tests for the Compute Substrate (Phase 5) —

import time
import pytest

from sas.layers.substrate import (
    ComputeSubstrate,
    LocalDockerSubstrate,
    Machine,
    Output,
    Screenshot,
    SubstrateError,
)


# ── Machine / Screenshot / Output dataclasses ───────────────────────────────────

class TestMachine:
    def test_create_machine(self):
        m = Machine(
            id="test_001",
            template="xfce",
            status="running",
            created_at="2024-01-01T00:00:00Z",
        )
        assert m.id == "test_001"
        assert m.template == "xfce"
        assert m.resources is None

    def test_create_machine_with_resources(self):
        m = Machine(
            id="test_001",
            template="xfce",
            status="running",
            created_at="2024-01-01T00:00:00Z",
            resources={"cpu": 4, "memory": "8Gi"},
        )
        assert m.resources["cpu"] == 4


class TestScreenshot:
    def test_create_screenshot(self):
        s = Screenshot(machine_id="m1", data=b"PNG", width=1920, height=1080)
        assert s.machine_id == "m1"
        assert s.data == b"PNG"
        assert s.width == 1920
        assert s.height == 1080


class TestOutput:
    def test_create_output(self):
        o = Output(stdout="hello\n", stderr="", exit_code=0)
        assert o.stdout == "hello\n"
        assert o.exit_code == 0


class TestSubstrateError:
    def test_raise_error(self):
        with pytest.raises(SubstrateError, match="test error"):
            raise SubstrateError("test error")


# ── LocalDockerSubstrate ────────────────────────────────────────────────────────

class TestLocalDockerSubstrate:
    def test_boot(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        assert m.id.startswith("machine_")
        assert m.template == "xfce"
        assert m.status == "running"
        assert m.resources == {"cpu": 4, "memory": "8Gi"}

    def test_list_machines(self):
        sub = LocalDockerSubstrate()
        m1 = sub.boot("xfce")
        m2 = sub.boot("lxde")
        machines = sub.list_machines()
        assert len(machines) == 2
        ids = {m.id for m in machines}
        assert m1.id in ids
        assert m2.id in ids

    def test_capture(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        screenshot = sub.capture(m)
        assert screenshot.machine_id == m.id
        assert screenshot.width == 1920
        assert screenshot.height == 1080

    def test_click(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        sub.click(m, 100, 200)
        # Should not raise

    def test_type(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        sub.type(m, "hello world")
        # Should not raise

    def test_execute_echo(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        output = sub.execute(m, "echo hello")
        assert output.stdout == "hello\n"
        assert output.exit_code == 0

    def test_execute_other(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        output = sub.execute(m, "ls -la")
        assert output.exit_code == 0

    def test_destroy(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        sub.destroy(m)
        assert m.status == "stopped"

    def test_destroy_removes_from_list(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        sub.destroy(m)
        # list_machines still returns it, but status is stopped
        machines = sub.list_machines()
        assert len(machines) == 1
        assert machines[0].status == "stopped"

    def test_operations_on_stopped_machine_raise(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        sub.destroy(m)
        with pytest.raises(SubstrateError, match="not running"):
            sub.capture(m)
        with pytest.raises(SubstrateError, match="not running"):
            sub.click(m, 0, 0)
        with pytest.raises(SubstrateError, match="not running"):
            sub.type(m, "test")
        with pytest.raises(SubstrateError, match="not running"):
            sub.execute(m, "test")

    def test_default_resources(self):
        sub = LocalDockerSubstrate()
        m = sub.boot("xfce")
        assert m.resources == {"cpu": 4, "memory": "8Gi"}

    def test_custom_resources(self):
        sub = LocalDockerSubstrate(default_resources={"cpu": 8, "memory": "16Gi"})
        m = sub.boot("xfce")
        assert m.resources == {"cpu": 8, "memory": "16Gi"}

    def test_idle_timeout(self):
        sub = LocalDockerSubstrate(idle_timeout=60)
        assert sub.idle_timeout == 60

    def test_auto_destroy_idle(self):
        sub = LocalDockerSubstrate(idle_timeout=0)
        m = sub.boot("xfce")
        time.sleep(0.1)
        sub._auto_destroy_idle()
        assert m.status == "stopped"

    def test_auto_destroy_does_not_destroy_active(self):
        sub = LocalDockerSubstrate(idle_timeout=300)
        m = sub.boot("xfce")
        sub._auto_destroy_idle()
        assert m.status == "running"

    def test_multiple_machines_independent(self):
        sub = LocalDockerSubstrate()
        m1 = sub.boot("xfce")
        m2 = sub.boot("lxde")
        sub.destroy(m1)
        assert m1.status == "stopped"
        assert m2.status == "running"
