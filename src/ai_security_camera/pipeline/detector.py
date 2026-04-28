"""Stage-1 lightweight detector protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float


@dataclass(frozen=True)
class DetectorResult:
    detections: list[Detection]

    @property
    def triggered(self) -> bool:
        return len(self.detections) > 0

    def summary(self, classes_of_interest: set[str] | None = None) -> str:
        if not self.detections:
            return "no detections"
        parts: list[str] = []
        for d in self.detections:
            if classes_of_interest is not None and d.label not in classes_of_interest:
                continue
            parts.append(f"{d.label} {d.confidence:.2f}")
        return ", ".join(parts) if parts else "no detections in interest set"


@runtime_checkable
class ObjectDetector(Protocol):
    def infer(self, frame_id: int) -> DetectorResult:
        """Run lightweight inference on a frame (implementation-defined inputs)."""
        ...
