"""User custom rules merged with templates (requirements §12.2)."""

from __future__ import annotations

from typing import Any

import yaml
from pydantic import BaseModel, Field

from ai_security_camera.domain.templates import UseCaseTemplate


class UserRuleConfig(BaseModel):
    """Subset of §12.2 YAML shape."""

    template: str = Field(description="Builtin template id, e.g. uc_01")
    custom_rules: list[str] = Field(default_factory=list)
    notification: dict[str, Any] = Field(default_factory=dict)


def parse_user_rules_yaml(text: str) -> UserRuleConfig:
    raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        msg = "Rules YAML root must be a mapping"
        raise ValueError(msg)
    return UserRuleConfig.model_validate(raw)


def render_vlm_user_prompt(
    template: UseCaseTemplate,
    *,
    detector_summary: str,
    custom_rules_lines: list[str] | None = None,
) -> str:
    """Fill template placeholders including merged natural-language rules."""
    custom_rules = "\n".join(f"- {r}" for r in (custom_rules_lines or []))
    if not custom_rules:
        custom_rules = "(なし)"
    base = template.vlm_user_prompt_template
    return base.format(
        location_description=template.location_description,
        scene_context=template.location_description,
        detector_summary=detector_summary,
        custom_rules=custom_rules,
    )


def merge_template_with_mapping(
    base: UseCaseTemplate,
    overlay: dict[str, Any],
) -> UseCaseTemplate:
    """Shallow-merge YAML overlay onto a loaded template (for advanced users)."""
    merged = base.model_dump()
    merged.update({k: v for k, v in overlay.items() if k in merged and v is not None})
    return UseCaseTemplate.model_validate(merged)


def load_template_for_user_config(
    cfg: UserRuleConfig,
    *,
    builtins: dict[str, UseCaseTemplate],
) -> UseCaseTemplate:
    """Resolve template id from user config against pre-loaded builtins."""
    tid = cfg.template
    if tid not in builtins:
        msg = f"Unknown template id: {tid}"
        raise KeyError(msg)
    return builtins[tid]
