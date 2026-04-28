"""Deterministic fake detector for tests (no CV dependency)."""

from __future__ import annotations

from ai_security_camera.pipeline.detector import Detection, DetectorResult, ObjectDetector


class FakeYoloDetector(ObjectDetector):
    """Returns scripted detections per frame id."""

    def __init__(
        self,
        *,
        trigger_on_frames: set[int] | None = None,
        label: str = "person",
        confidence: float = 0.91,
    ) -> None:
        self.trigger_on_frames = trigger_on_frames or set()
        self.label = label
        self.confidence = confidence

    def infer(self, frame_id: int) -> DetectorResult:
        if frame_id not in self.trigger_on_frames:
            return DetectorResult(detections=[])
        return DetectorResult(
            detections=[Detection(label=self.label, confidence=self.confidence)],
        )
