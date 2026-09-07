"""Compute substrate — where the agent runs and what it can touch.

Full desktop environment, not just a browser tab. Local Docker container.
The agent drives it via screenshots + mouse/keyboard events.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Protocol


@dataclass
class Machine:
    """A compute machine."""
    id: str
    template: str
    status: str  # "running", "stopped", "booting"
    created_at: str
    resources: dict | None = None


@dataclass
class Screenshot:
    """A screenshot of a machine."""
    machine_id: str
    data: bytes
    width: int
    height: int


@dataclass
class Output:
    """Output from a command."""
    stdout: str
    stderr: str
    exit_code: int


class SubstrateError(Exception):
    """Error from substrate operations."""


class ComputeSubstrate(Protocol):
    """Protocol for compute substrate implementations."""
    def boot(self, template: str) -> Machine: ...
    def capture(self, machine: Machine) -> Screenshot: ...
    def click(self, machine: Machine, x: int, y: int) -> None: ...
    def type(self, machine: Machine, text: str) -> None: ...
    def execute(self, machine: Machine, command: str) -> Output: ...
    def destroy(self, machine: Machine) -> None: ...
    def list_machines(self) -> list[Machine]: ...


class LocalDockerSubstrate:
    """Local Docker-based compute substrate.

    Manages Docker containers with desktop environments.
    Supports boot, capture, click, type, execute, destroy.
    """

    def __init__(
        self,
        default_resources: dict | None = None,
        idle_timeout: int = 300,
    ) -> None:
        self.default_resources = default_resources or {"cpu": 4, "memory": "8Gi"}
        self.idle_timeout = idle_timeout
        self._machines: dict[str, Machine] = {}
        self._last_active: dict[str, float] = {}

    def boot(self, template: str) -> Machine:
        """Boot a new machine from a template."""
        machine_id = f"machine_{uuid.uuid4().hex[:8]}"
        machine = Machine(
            id=machine_id,
            template=template,
            status="running",
            created_at=time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            resources=dict(self.default_resources),
        )

        # In production: docker run -d --name {machine_id} ...
        # For now, we simulate
        self._machines[machine_id] = machine
        self._last_active[machine_id] = time.time()

        return machine

    def capture(self, machine: Machine) -> Screenshot:
        """Capture a screenshot of a machine."""
        self._ensure_running(machine)
        # In production: docker exec {machine_id} import -window root ...
        # For now, return a placeholder screenshot
        return Screenshot(
            machine_id=machine.id,
            data=b"PNG_PLACEHOLDER",
            width=1920,
            height=1080,
        )

    def click(self, machine: Machine, x: int, y: int) -> None:
        """Click at coordinates on a machine."""
        self._ensure_running(machine)
        # In production: docker exec {machine_id} xdotool mousemove {x} {y} click 1
        self._last_active[machine.id] = time.time()

    def type(self, machine: Machine, text: str) -> None:
        """Type text on a machine."""
        self._ensure_running(machine)
        # In production: docker exec {machine_id} xdotool type '{text}'
        self._last_active[machine.id] = time.time()

    def execute(self, machine: Machine, command: str) -> Output:
        """Execute a command on a machine."""
        self._ensure_running(machine)
        # In production: docker exec {machine_id} sh -c '{command}'
        # For now, simulate
        self._last_active[machine.id] = time.time()

        if command.startswith("echo "):
            return Output(
                stdout=command[5:] + "\n",
                stderr="",
                exit_code=0,
            )

        return Output(
            stdout="",
            stderr="",
            exit_code=0,
        )

    def destroy(self, machine: Machine) -> None:
        """Destroy a machine."""
        machine.status = "stopped"
        # In production: docker stop {machine_id} && docker rm {machine_id}
        self._last_active.pop(machine.id, None)

    def list_machines(self) -> list[Machine]:
        """List all machines."""
        return list(self._machines.values())

    def _ensure_running(self, machine: Machine) -> None:
        """Ensure a machine is running."""
        if machine.status != "running":
            raise SubstrateError(
                f"Machine {machine.id} is not running (status: {machine.status})"
            )

    def _auto_destroy_idle(self) -> None:
        """Auto-destroy machines that have been idle."""
        now = time.time()
        to_destroy = [
            m for m in self._machines.values()
            if m.status == "running" and now - self._last_active.get(m.id, 0) > self.idle_timeout
        ]
        for machine in to_destroy:
            self.destroy(machine)
