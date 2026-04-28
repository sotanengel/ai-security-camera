"""API request/response models."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel


class EventCreate(BaseModel):
    template_id: str
    detector_summary: str
    vlm: dict[str, Any] | None = None
    media_uri: str | None = None


class EventOut(BaseModel):
    id: str
    created_at: datetime
    template_id: str
    detector_summary: str
    vlm_json: dict[str, Any] | None
    media_uri: str | None = None


def utc_now() -> datetime:
    return datetime.now(UTC)
