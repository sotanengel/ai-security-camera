"""Tests for VLM structured JSON schema (VLM-021 / VLM-022)."""

import pytest
from pydantic import ValidationError

from ai_security_camera.domain.vlm_schema import (
    Severity,
    VlmStructuredResponse,
    validate_vlm_payload,
)


def test_valid_payload_roundtrip() -> None:
    raw = {
        "event_type": "delivery",
        "confidence": 0.82,
        "description": "荷物を置いた人物がいる",
        "objects": ["person", "box"],
        "should_notify": True,
        "severity": "medium",
    }
    m = VlmStructuredResponse.model_validate(raw)
    assert m.severity == Severity.medium
    assert m.objects == ["person", "box"]


def test_invalid_payload_returns_none() -> None:
    bad = {"confidence": 2.0}  # out of range
    assert validate_vlm_payload(bad) is None


def test_validate_vlm_payload_accepts_good_dict() -> None:
    good = {
        "event_type": "unknown",
        "confidence": 0.1,
        "description": "不明",
        "objects": [],
        "should_notify": False,
        "severity": "low",
    }
    out = validate_vlm_payload(good)
    assert out is not None
    assert out.event_type == "unknown"


@pytest.mark.parametrize(
    "missing_key",
    ["event_type", "confidence", "description", "should_notify", "severity"],
)
def test_missing_required_field_invalid(missing_key: str) -> None:
    base = {
        "event_type": "normal",
        "confidence": 0.5,
        "description": "ok",
        "objects": [],
        "should_notify": False,
        "severity": "low",
    }
    del base[missing_key]
    with pytest.raises(ValidationError):
        VlmStructuredResponse.model_validate(base)
