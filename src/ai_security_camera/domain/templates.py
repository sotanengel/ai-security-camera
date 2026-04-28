"""Use-case templates loaded from YAML (requirements P-001, §4.2)."""

from __future__ import annotations

import importlib.resources
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class NotificationHints(BaseModel):
    """Template-level notification hints (subset of §4.2)."""

    interest_classes: list[str] = Field(default_factory=list)
    min_confidence: float = Field(default=0.4, ge=0.0, le=1.0)
    dwell_alert_seconds: int | None = None


class UseCaseTemplate(BaseModel):
    """Bundle of prompts and detector hints for one use case (UC-xx)."""

    id: str
    name: str
    location_description: str = Field(description="Context for the VLM about where the camera is.")
    detector_classes: list[str] = Field(
        default_factory=list,
        description="YOLO / lightweight detector class names of interest.",
    )
    vlm_system_prompt: str
    vlm_user_prompt_template: str = Field(
        default="{scene_context}",
        description="Template string; may reference scene_context, detector_summary, custom_rules.",
    )
    notification: NotificationHints = Field(default_factory=NotificationHints)
    recording_retention_days: int = 7
    snapshot_retention_days: int = 30


def load_template_from_mapping(data: dict[str, Any]) -> UseCaseTemplate:
    return UseCaseTemplate.model_validate(data)


def load_template_from_yaml(text: str) -> UseCaseTemplate:
    raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        msg = "YAML root must be a mapping"
        raise ValueError(msg)
    return load_template_from_mapping(raw)


def load_builtin_template(template_id: str) -> UseCaseTemplate:
    """Load packaged YAML from ai_security_camera.data.templates."""
    pkg = "ai_security_camera.data.templates"
    filename = f"{template_id}.yaml"
    try:
        traversable = importlib.resources.files(pkg).joinpath(filename)
    except (ModuleNotFoundError, FileNotFoundError) as e:
        msg = f"Unknown template package or missing file: {filename}"
        raise FileNotFoundError(msg) from e
    if not traversable.is_file():
        msg = f"Template not found: {template_id}"
        raise FileNotFoundError(msg)
    text = traversable.read_text(encoding="utf-8")
    return load_template_from_yaml(text)


def load_template_from_path(path: Path) -> UseCaseTemplate:
    return load_template_from_yaml(path.read_text(encoding="utf-8"))


def list_builtin_template_ids() -> list[str]:
    """Return stem names of packaged templates."""
    pkg = importlib.resources.files("ai_security_camera.data.templates")
    return sorted(p.stem for p in pkg.iterdir() if p.suffix == ".yaml")
