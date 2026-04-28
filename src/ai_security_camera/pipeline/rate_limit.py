"""VLM call rate limiting (requirements VLM-003)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class VlmRateLimiter:
    """Allow at most one VLM call per `min_interval_seconds` per scene key."""

    min_interval_seconds: float = 10.0
    _last: dict[str, float] = field(default_factory=dict)

    def allow(self, scene_key: str, now: float | None = None) -> bool:
        t = now if now is not None else time.monotonic()
        last = self._last.get(scene_key)
        if last is None or t - last >= self.min_interval_seconds:
            self._last[scene_key] = t
            return True
        return False
