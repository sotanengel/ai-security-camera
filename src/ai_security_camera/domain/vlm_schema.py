"""VLM structured output (requirements VLM-021)."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class Severity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class VlmStructuredResponse(BaseModel):
    """Standard JSON contract for VLM stage-2 output."""

    event_type: str = Field(
        ...,
        description="Predefined category: intrusion, delivery, fall, animal, normal, unknown, etc.",
    )
    confidence: float = Field(..., ge=0.0, le=1.0)
    description: str = Field(..., description="Natural language situation description (ja/en).")
    objects: list[str] = Field(default_factory=list, description="Primary detected object labels.")
    should_notify: bool
    severity: Severity

    @field_validator("event_type", "description", mode="before")
    @classmethod
    def strip_strings(cls, v: Any) -> Any:
        if isinstance(v, str):
            return v.strip()
        return v

    @classmethod
    def parse_from_json_dict(cls, data: dict[str, Any]) -> "VlmStructuredResponse":
        """Validate and return model; raises ValidationError on schema violation."""
        return cls.model_validate(data)


def validate_vlm_payload(raw: dict[str, Any]) -> VlmStructuredResponse | None:
    """
    Return validated model or None if invalid (VLM-022: discard invalid responses).

    Callers may retry generation when None.
    """
    try:
        return VlmStructuredResponse.model_validate(raw)
    except Exception:
        return None
