"""Frame index sampling (FPS / stride control)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FrameSampler:
    """Emit frame indices at most every `stride` steps (simulated clock)."""

    stride: int = 1

    def __post_init__(self) -> None:
        if self.stride < 1:
            msg = "stride must be >= 1"
            raise ValueError(msg)

    def should_process(self, tick: int) -> bool:
        return tick % self.stride == 0
