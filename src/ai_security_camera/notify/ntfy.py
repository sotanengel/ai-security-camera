"""ntfy.sh / self-hosted ntfy HTTP publisher."""

from __future__ import annotations

import httpx

from ai_security_camera.domain.vlm_schema import Severity, VlmStructuredResponse


def _ascii_http_header_value(value: str, *, fallback: str = "notification") -> str:
    """HTTP headers must be latin-1; replace non-ASCII titles for client compatibility."""
    try:
        value.encode("latin-1")
    except UnicodeEncodeError:
        return fallback
    return value


class NtfyNotifier:
    def __init__(
        self,
        topic_url: str | None,
        *,
        client: httpx.Client | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.topic_url = topic_url.rstrip("/") if topic_url else None
        self._own = client is None
        self._client = client or httpx.Client(timeout=timeout)

    def close(self) -> None:
        if self._own:
            self._client.close()

    def publish_text(self, title: str, message: str, priority: int | None = None) -> None:
        if not self.topic_url:
            msg = "ASC_NTFY_TOPIC_URL / topic_url is not configured"
            raise ValueError(msg)
        headers: dict[str, str] = {}
        if title:
            headers["Title"] = _ascii_http_header_value(title)
        if priority is not None:
            headers["Priority"] = str(priority)
        r = self._client.post(
            self.topic_url,
            content=message.encode("utf-8"),
            headers=headers,
        )
        r.raise_for_status()

    def publish_vlm_summary(
        self,
        vlm: VlmStructuredResponse,
        *,
        title: str = "Camera",
        priority_from_severity: bool = True,
    ) -> None:
        """Send human-readable VLM description as notification body (requirements F-041)."""
        prio: int | None = None
        if priority_from_severity:
            prio = {Severity.low: 3, Severity.medium: 4, Severity.high: 5}.get(vlm.severity, 3)
        lines = [
            f"type: {vlm.event_type}",
            f"severity: {vlm.severity}",
            f"confidence: {vlm.confidence:.2f}",
            "",
            vlm.description,
        ]
        self.publish_text(title, "\n".join(lines), priority=prio)
