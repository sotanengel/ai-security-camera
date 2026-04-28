"""Two-stage pipeline: detector trigger -> optional VLM (requirements VLM-002, VLM-003)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ai_security_camera.domain.rules import render_vlm_user_prompt
from ai_security_camera.domain.templates import UseCaseTemplate
from ai_security_camera.domain.vlm_schema import VlmStructuredResponse
from ai_security_camera.pipeline.detector import ObjectDetector
from ai_security_camera.pipeline.ollama_client import OllamaClient, OllamaError
from ai_security_camera.pipeline.rate_limit import VlmRateLimiter


@dataclass
class PipelineDecision:
    """Outcome of processing one logical frame."""

    ran_vlm: bool
    skipped_reason: str | None
    vlm_result: VlmStructuredResponse | None
    detector_summary: str


class PipelineOrchestrator:
    def __init__(
        self,
        *,
        template: UseCaseTemplate,
        detector: ObjectDetector,
        ollama: OllamaClient,
        rate_limiter: VlmRateLimiter,
        scene_key: str = "default",
        custom_rules: list[str] | None = None,
        interest_classes: set[str] | None = None,
    ) -> None:
        self.template = template
        self.detector = detector
        self.ollama = ollama
        self.rate_limiter = rate_limiter
        self.scene_key = scene_key
        self.custom_rules = custom_rules or []
        self.interest_classes = interest_classes

    def process_frame(self, frame_id: int, *, now: float | None = None) -> PipelineDecision:
        """
        VLM-002: no VLM when stage-1 does not trigger.
        VLM-003: rate limit per scene_key.
        """
        det = self.detector.infer(frame_id)
        classes = self.interest_classes
        if classes is None:
            classes = set(self.template.detector_classes)
        summary = det.summary(classes_of_interest=classes if classes else None)

        if not det.triggered:
            return PipelineDecision(
                ran_vlm=False,
                skipped_reason="no_detection",
                vlm_result=None,
                detector_summary=summary,
            )

        if not self.rate_limiter.allow(self.scene_key, now=now):
            return PipelineDecision(
                ran_vlm=False,
                skipped_reason="rate_limited",
                vlm_result=None,
                detector_summary=summary,
            )

        user_prompt = render_vlm_user_prompt(
            self.template,
            detector_summary=summary,
            custom_rules_lines=self.custom_rules,
        )
        try:
            vlm = self.ollama.complete_vlm(
                system=self.template.vlm_system_prompt,
                user=user_prompt,
                images=None,
            )
        except OllamaError:
            return PipelineDecision(
                ran_vlm=True,
                skipped_reason="vlm_error",
                vlm_result=None,
                detector_summary=summary,
            )

        return PipelineDecision(
            ran_vlm=True,
            skipped_reason=None if vlm else "invalid_json",
            vlm_result=vlm,
            detector_summary=summary,
        )


def run_fallback_on_vlm_down(
    orchestrator: PipelineOrchestrator,
    frame_id: int,
    *,
    now: float | None = None,
) -> tuple[PipelineDecision, dict[str, Any]]:
    """
    NF-012: on VLM failure, continue with detection-only metadata for logging/alert policy.
    Returns (decision, extra) where extra includes fallback=True when VLM missing after trigger.
    """
    d = orchestrator.process_frame(frame_id, now=now)
    extra: dict[str, Any] = {}
    if d.ran_vlm and d.vlm_result is None:
        extra["fallback_detection_only"] = True
    return d, extra
