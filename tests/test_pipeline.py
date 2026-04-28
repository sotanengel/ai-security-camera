"""Pipeline: detector, rate limit, Ollama client, orchestrator."""

import json
from typing import Any

import httpx
import pytest

from ai_security_camera.domain.templates import load_builtin_template
from ai_security_camera.pipeline.fake_yolo import FakeYoloDetector
from ai_security_camera.pipeline.ollama_client import OllamaClient, OllamaError
from ai_security_camera.pipeline.orchestrator import (
    PipelineOrchestrator,
    run_fallback_on_vlm_down,
)
from ai_security_camera.pipeline.rate_limit import VlmRateLimiter
from ai_security_camera.pipeline.sampler import FrameSampler


def test_sampler_stride() -> None:
    s = FrameSampler(stride=5)
    assert s.should_process(0)
    assert not s.should_process(1)
    assert s.should_process(5)


def test_rate_limiter_spacing() -> None:
    r = VlmRateLimiter(min_interval_seconds=10.0)
    assert r.allow("cam1", now=0.0)
    assert not r.allow("cam1", now=5.0)
    assert r.allow("cam1", now=10.0)


def test_fake_yolo_trigger_only_on_frames() -> None:
    det = FakeYoloDetector(trigger_on_frames={1, 3})
    assert not det.infer(0).triggered
    assert det.infer(1).triggered


def _chat_handler_good_json(request: httpx.Request) -> httpx.Response:
    body = json.loads(request.content.decode())
    assert body.get("format") == "json"
    payload = {
        "message": {
            "role": "assistant",
            "content": json.dumps(
                {
                    "event_type": "normal",
                    "confidence": 0.5,
                    "description": "問題なし",
                    "objects": ["person"],
                    "should_notify": False,
                    "severity": "low",
                },
            ),
        },
    }
    return httpx.Response(200, json=payload)


def test_ollama_client_parses_json() -> None:
    transport = httpx.MockTransport(_chat_handler_good_json)
    with httpx.Client(transport=transport) as hc:
        c = OllamaClient("http://x", "m", client=hc)
        out = c.chat_json(
            [{"role": "user", "content": "hi"}],
        )
        assert out["event_type"] == "normal"


def test_ollama_complete_vlm_validates_schema() -> None:
    transport = httpx.MockTransport(_chat_handler_good_json)
    with httpx.Client(transport=transport) as hc:
        c = OllamaClient("http://x", "m", client=hc)
        v = c.complete_vlm(system="s", user="u")
        assert v is not None
        assert v.should_notify is False


def test_orchestrator_skips_vlm_without_detection() -> None:
    template = load_builtin_template("uc_01")
    det = FakeYoloDetector(trigger_on_frames=set())
    transport = httpx.MockTransport(_chat_handler_good_json)
    with httpx.Client(transport=transport) as hc:
        ollama = OllamaClient("http://x", "m", client=hc)
        orch = PipelineOrchestrator(
            template=template,
            detector=det,
            ollama=ollama,
            rate_limiter=VlmRateLimiter(min_interval_seconds=0.0),
        )
        d = orch.process_frame(0, now=0.0)
        assert d.ran_vlm is False
        assert d.skipped_reason == "no_detection"


def test_orchestrator_calls_vlm_when_triggered() -> None:
    template = load_builtin_template("uc_01")
    det = FakeYoloDetector(trigger_on_frames={0})
    called: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        called["yes"] = True
        return _chat_handler_good_json(request)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as hc:
        ollama = OllamaClient("http://x", "m", client=hc)
        orch = PipelineOrchestrator(
            template=template,
            detector=det,
            ollama=ollama,
            rate_limiter=VlmRateLimiter(min_interval_seconds=0.0),
        )
        d = orch.process_frame(0, now=0.0)
        assert d.ran_vlm is True
        assert d.vlm_result is not None
        assert "yes" in called


def test_orchestrator_rate_limits_vlm() -> None:
    template = load_builtin_template("uc_01")
    det = FakeYoloDetector(trigger_on_frames={0, 1})
    transport = httpx.MockTransport(_chat_handler_good_json)
    with httpx.Client(transport=transport) as hc:
        ollama = OllamaClient("http://x", "m", client=hc)
        rl = VlmRateLimiter(min_interval_seconds=100.0)
        orch = PipelineOrchestrator(
            template=template,
            detector=det,
            ollama=ollama,
            rate_limiter=rl,
            scene_key="s",
        )
        d0 = orch.process_frame(0, now=0.0)
        d1 = orch.process_frame(1, now=1.0)
        assert d0.ran_vlm is True
        assert d1.skipped_reason == "rate_limited"


def test_fallback_flag_when_vlm_invalid_after_trigger() -> None:
    template = load_builtin_template("uc_01")
    det = FakeYoloDetector(trigger_on_frames={0})

    def bad_schema(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "message": {
                    "role": "assistant",
                    "content": json.dumps({"event_type": "x"}),  # incomplete schema
                },
            },
        )

    transport = httpx.MockTransport(bad_schema)
    with httpx.Client(transport=transport) as hc:
        ollama = OllamaClient("http://x", "m", client=hc)
        orch = PipelineOrchestrator(
            template=template,
            detector=det,
            ollama=ollama,
            rate_limiter=VlmRateLimiter(min_interval_seconds=0.0),
        )
        _d, extra = run_fallback_on_vlm_down(orch, 0, now=0.0)
        assert extra.get("fallback_detection_only") is True


def test_invalid_json_from_ollama_raises_on_chat_json() -> None:
    def bad(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"message": {"role": "assistant", "content": "not json"}},
        )

    transport = httpx.MockTransport(bad)
    with httpx.Client(transport=transport) as hc:
        c = OllamaClient("http://x", "m", client=hc)
        with pytest.raises(OllamaError):
            c.chat_json([{"role": "user", "content": "x"}])
