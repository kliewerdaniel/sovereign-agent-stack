"""Layer 3: Compute Substrate — Where the agent runs and what it can touch.

Full desktop environment, not just a browser tab. Local Docker container or VM.
The agent drives it via screenshots + mouse/keyboard events.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass
class Machine:
    id: str
    template: str
    status: str  # "running", "stopped", "booting"
    created_at: str


@dataclass
class Screenshot:
    machine_id: str
    data: bytes
    width: int
    height: int


@dataclass
class Output:
    stdout: str
    stderr: str
    exit_code: int


class ComputeSubstrate(Protocol):
    async def boot(self, template: str) -> Machine: ...
    async def capture(self, machine: Machine) -> Screenshot: ...
    async def click(self, machine: Machine, x: int, y: int) -> None: ...
    async def type(self, machine: Machine, text: str) -> None: ...
    async def execute(self, machine: Machine, command: str) -> Output: ...
    async def destroy(self, machine: Machine) -> None: ...
