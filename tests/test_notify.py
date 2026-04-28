"""ntfy adapter and severity policy tests."""

import httpx
import pytest

from ai_security_camera.domain.vlm_schema import Severity, VlmStructuredResponse
from ai_security_camera.notify.ntfy import NtfyNotifier
from ai_security_camera.notify.policy import should_send_push, should_send_topic_message


def _sample_vlm(**kwargs: object) -> VlmStructuredResponse:
    base = {
        "event_type": "intrusion",
        "confidence": 0.9,
        "description": "テスト",
        "objects": ["person"],
        "should_notify": True,
        "severity": "high",
    }
    base.update(kwargs)
    return VlmStructuredResponse.model_validate(base)


def test_push_only_high() -> None:
    assert should_send_push(_sample_vlm(severity=Severity.high, should_notify=True)) is True
    assert should_send_push(_sample_vlm(severity=Severity.medium, should_notify=True)) is False


def test_topic_message_medium_and_high() -> None:
    low = _sample_vlm(severity=Severity.low, should_notify=True)
    med = _sample_vlm(severity=Severity.medium, should_notify=True)
    assert should_send_topic_message(low) is False
    assert should_send_topic_message(med) is True


def test_ntfy_publish_uses_post() -> None:
    seen: dict[str, object] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["body"] = request.content
        return httpx.Response(200)

    transport = httpx.MockTransport(handle)
    with httpx.Client(transport=transport) as hc:
        n = NtfyNotifier("https://ntfy.example/mytopic", client=hc)
        n.publish_text("タイトル", "本文テスト")
    assert seen["method"] == "POST"
    assert isinstance(seen["body"], bytes)
    assert "本文テスト".encode() in seen["body"]


def test_publish_vlm_summary_sends_description() -> None:
    captured: dict[str, bytes] = {}

    def handle(request: httpx.Request) -> httpx.Response:
        captured["raw"] = request.content
        return httpx.Response(200)

    transport = httpx.MockTransport(handle)
    vlm = _sample_vlm(description="玄関に人物")
    with httpx.Client(transport=transport) as hc:
        n = NtfyNotifier("https://ntfy.example/t", client=hc)
        n.publish_vlm_summary(vlm)
    assert "玄関に人物".encode() in captured["raw"]


def test_ntfy_missing_url_errors() -> None:
    n = NtfyNotifier(None)
    with pytest.raises(ValueError, match="not configured"):
        n.publish_text("a", "b")
