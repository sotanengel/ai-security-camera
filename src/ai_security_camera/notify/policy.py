"""Notification policy (requirements §17.5: high → push, medium/low → UI)."""

from __future__ import annotations

from ai_security_camera.domain.vlm_schema import Severity, VlmStructuredResponse


def should_send_push(vlm: VlmStructuredResponse) -> bool:
    """Mobile push for high severity only; other severities are UI-only in the PoC."""
    return vlm.severity == Severity.high and vlm.should_notify


def should_send_topic_message(vlm: VlmStructuredResponse) -> bool:
    """
    ntfy topic: notify on any should_notify with at least medium severity
    (adjust per deployment; PoC default aligns with 'alert' channel).
    """
    if not vlm.should_notify:
        return False
    return vlm.severity in (Severity.medium, Severity.high)
